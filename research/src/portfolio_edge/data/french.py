"""Ken French Data Library reader: direct zip download and first-party parsing.

Deliberately not ``pandas_datareader``. A third-party reader hides the raw bytes,
the response headers and the file's own prose header, and it silently absorbs
layout changes at the source. All three are the provenance this package exists to
record, so the zip is fetched into the raw cache and parsed here.

What these files actually look like
-----------------------------------
Each zip holds one CSV that is not a CSV in the usual sense. It contains a
multi-line prose header, then *several* tables stacked in one file, separated by
blank lines and a free-text banner ("Annual Factors: January-December", "Average
Equal Weighted Returns -- Monthly", "Number of Firms in Portfolios"). Date keys
are ``YYYYMM``, ``YYYY`` or ``YYYYMMDD`` depending on the table. Values are in
percent, which the file never states. Missing values are the sentinels ``-99.99``
and ``-999``, which the file states only in prose.

Consequences this parser takes seriously:

* Table boundaries are found structurally — runs of rows whose first field is a
  date key, split whenever the key width changes — never by line number. Ken
  French appends rows monthly and edits the prose header, so any hardcoded offset
  is wrong by construction.
* The banner and the file preamble are preserved and carried into the manifest
  warnings, because for several of these tables the prose is the *only* statement
  of what the numbers mean.
* Percent to decimal is an explicit, recorded transform, applied only to tables
  the parser has classified as returns. "Number of Firms" and "Average Market
  Cap" are not returns and are left untouched; their unit is recorded as unknown
  rather than guessed.
* Sentinels become missing values and are counted in the warnings. They are never
  allowed through as data, and never quietly dropped either.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import Frequency, ParsedTable

__all__ = [
    "DATASETS",
    "FRENCH_SENTINELS",
    "LICENSE_OR_TERMS_URL",
    "PARSER_VERSION",
    "FrenchDataset",
    "FrenchFile",
    "FrenchParseError",
    "build_manifests",
    "download",
    "get_dataset",
    "parse",
]

#: Bump on any change to parsing behaviour: boundary detection, unit inference,
#: sentinel handling, column naming, or period labelling. Manifests record it so
#: a table built by an older parser is identifiable without re-running anything.
PARSER_VERSION: Final = "french/1.0.0"

LICENSE_OR_TERMS_URL: Final = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
)

#: Declared in the prose header of several files as "Missing data are indicated
#: by -99.99 or -999". Nothing machine-readable declares them.
FRENCH_SENTINELS: Final = (-99.99, -999.0)

_BASE_URL: Final = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"

_DATE_KEY = re.compile(r"^\d{4}(?:\d{2})?(?:\d{2})?$")
_SLUG_STRIP = re.compile(r"[^a-z0-9]+")

_AVAILABILITY_MONTHLY: Final = (
    "Rebuilt from a CRSP vintage after month end and posted without a published "
    "release timestamp. The HTTP Last-Modified header of the zip is the only "
    "upper bound this code can observe on when a row became available; the row "
    "for month M was certainly not available during month M. Treat every "
    "observation as unavailable until at least the month after its period, and "
    "do not treat Last-Modified as the availability date of older rows."
)

_REVISION_POLICY: Final = (
    "Not point-in-time. The entire history is recomputed from the current source "
    "vintage on every rebuild, so observations from the 1920s can and do change "
    "between downloads. Ken French publishes no vintage archive, so a value here "
    "cannot be assumed equal to the value published at any earlier date. A "
    "sha256 identifies the file used; it does not establish what was historically "
    "available."
)

_REVISION_POLICY_INTERNATIONAL: Final = (
    _REVISION_POLICY
    + " The international files are built from a Bloomberg vintage rather than "
    "CRSP, and early history is sparse: RMW and CMA carry the -99.99 sentinel "
    "for the first years of the emerging-markets sample."
)

_REVISION_POLICY_INTERNATIONAL_MOMENTUM: Final = (
    _REVISION_POLICY
    + " The international files are built from a Bloomberg vintage rather than "
    "CRSP. A momentum factor needs twelve months of prior returns before it can "
    "be formed, so each regional momentum file begins later than the "
    "five-factor file for the same region."
)


class FrenchParseError(ValueError):
    """Raised when a French artifact does not have the expected shape at all."""


@dataclass(frozen=True)
class FrenchDataset:
    """A file in the Ken French Data Library, with its provenance policies.

    ``default_source_units`` is the units declaration this repository is willing
    to make about a table the file itself does not describe. The factor files
    contain nothing but returns, so ``"percent"`` is a defensible default for an
    unlabelled table in them. The 25-portfolio file mixes returns, firm counts,
    market caps and accounting ratios, so it declares nothing and every table in
    it must be classified from its own banner or left as unknown.
    """

    dataset_id: str
    filename: str
    description: str
    availability_policy: str
    revision_policy: str
    default_source_units: str | None = None

    @property
    def url(self) -> str:
        return f"{_BASE_URL}/{self.filename}"


DATASETS: Final[dict[str, FrenchDataset]] = {
    dataset.dataset_id: dataset
    for dataset in (
        FrenchDataset(
            dataset_id="french_us_ff5",
            filename="F-F_Research_Data_5_Factors_2x3_CSV.zip",
            description=(
                "Fama-French five factors (Mkt-RF, SMB, HML, RMW, CMA) and the "
                "one-month Treasury bill rate, US, 2x3 sorts."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_us_momentum",
            filename="F-F_Momentum_Factor_CSV.zip",
            description=(
                "Momentum factor (Mom) from six value-weight portfolios on size "
                "and prior 12-2 return, US."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_developed_ff5",
            filename="Developed_5_Factors_CSV.zip",
            description=(
                "Fama-French five factors, developed markets INCLUDING the United "
                "States. This file is not an ex-US series: regressing its Mkt-RF on "
                "the US and Developed ex-US Mkt-RF over 1990-07..2026-06 gives "
                "weights 0.460 and 0.549 summing to 1.009, so the US is roughly "
                "half of it. Use french_developed_ex_us_ff5 for a sleeve that must "
                "not overlap a US sleeve."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_developed_ex_us_ff5",
            filename="Developed_ex_US_5_Factors_CSV.zip",
            description=(
                "Fama-French five factors, developed markets excluding the United "
                "States. The non-overlapping complement of the US file, and the "
                "series a two-region portfolio needs."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_emerging_ff5",
            filename="Emerging_5_Factors_CSV.zip",
            description="Fama-French five factors, emerging markets.",
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_developed_momentum",
            filename="Developed_Mom_Factor_CSV.zip",
            description=(
                "Momentum factor (WML) from six value-weight portfolios on size "
                "and prior 2-12 return, developed markets INCLUDING the United "
                "States. Registered as the momentum counterpart of "
                "french_developed_ff5 and excluded from any pool that also holds "
                "the US file, for the same reason: it is not an ex-US series. "
                "The column is called WML here and Mom in the US file; both are "
                "the same 30/70 prior-return spread."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL_MOMENTUM,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_developed_ex_us_momentum",
            filename="Developed_ex_US_Mom_Factor_CSV.zip",
            description=(
                "Momentum factor (WML), developed markets excluding the United "
                "States. The non-overlapping complement of french_us_momentum "
                "and the series a two-region momentum comparison needs."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL_MOMENTUM,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_emerging_momentum",
            filename="Emerging_MOM_Factor_CSV.zip",
            description="Momentum factor (WML), emerging markets.",
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL_MOMENTUM,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_us_25_portfolios_5x5",
            filename="25_Portfolios_5x5_CSV.zip",
            description=(
                "25 portfolios formed on size and book-to-market, US: value- and "
                "equal-weighted returns, firm counts, average market cap and "
                "average BE/ME."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
        ),
        FrenchDataset(
            dataset_id="french_us_ff3",
            filename="F-F_Research_Data_Factors_CSV.zip",
            description=(
                "Fama-French three factors (Mkt-RF, SMB, HML) and the one-month "
                "Treasury bill rate, US, from 1926-07. The three-factor file is "
                "NOT a prefix of the five-factor one: its SMB is built from the "
                "six size x book-to-market portfolios alone, whereas the "
                "five-factor file's SMB averages the size legs of the "
                "book-to-market, profitability and investment sorts. Use this "
                "file, and not french_us_ff5, whenever an SMB is to be "
                "reconciled against 6_Portfolios_2x3, and whenever a market "
                "return is needed before 1963-07."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
            default_source_units="percent",
        ),
        FrenchDataset(
            dataset_id="french_us_6_portfolios_2x3",
            filename="6_Portfolios_2x3_CSV.zip",
            description=(
                "Six portfolios formed on size and book-to-market, US, 2x3 sorts: "
                "SMALL LoBM, ME1 BM2, SMALL HiBM, BIG LoBM, ME2 BM2, BIG HiBM. "
                "These are the LONG-ONLY building blocks HML is assembled from, "
                "which is what makes them the only public series that can price a "
                "long-only tilt against the long-short factor built out of it."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
        ),
        FrenchDataset(
            dataset_id="french_us_6_portfolios_me_prior_12_2",
            filename="6_Portfolios_ME_Prior_12_2_CSV.zip",
            description=(
                "Six portfolios formed on size and prior 2-12 month return, US, "
                "2x3 sorts. The long-only building blocks of the momentum factor. "
                "Constructed MONTHLY, unlike the annually rebalanced "
                "book-to-market sorts, so the two are not comparable on turnover."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
        ),
        FrenchDataset(
            dataset_id="french_us_portfolios_formed_on_me",
            filename="Portfolios_Formed_on_ME_CSV.zip",
            description=(
                "Portfolios formed on market equity alone, US: a negative-ME "
                "bucket that the file itself marks 'not used', 30/40/30 splits, "
                "quintiles and deciles, value- and equal-weighted, with firm "
                "counts and average firm size."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY,
        ),
        FrenchDataset(
            dataset_id="french_developed_ex_us_6_portfolios_2x3",
            filename="Developed_ex_US_6_Portfolios_ME_BE-ME_CSV.zip",
            description=(
                "Six portfolios formed on size and book-to-market, developed "
                "markets EXCLUDING the United States, 2x3 sorts. The regional "
                "analogue of french_us_6_portfolios_2x3. Developed_6_Portfolios "
                "is deliberately not registered: like Developed_5_Factors it "
                "INCLUDES the United States, so it cannot be an ex-US check."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL,
        ),
        FrenchDataset(
            dataset_id="french_emerging_6_portfolios_2x3",
            filename="Emerging_Markets_6_Portfolios_ME_BE-ME_CSV.zip",
            description=(
                "Six portfolios formed on size and book-to-market, emerging "
                "markets, 2x3 sorts. Note the filename: the emerging portfolio "
                "sorts are published under 'Emerging_Markets_', not the "
                "'Emerging_' prefix the emerging FACTOR files use, and there is "
                "no 25-portfolio emerging file at all. Emerging markets are "
                "distributed as 2x3 sixes and 2x2 fours only, so no emerging "
                "small-value CORNER exists in this library."
            ),
            availability_policy=_AVAILABILITY_MONTHLY,
            revision_policy=_REVISION_POLICY_INTERNATIONAL,
        ),
    )
}


def get_dataset(dataset_id: str) -> FrenchDataset:
    """Look up a registered dataset, or raise ``KeyError`` naming the choices."""
    try:
        return DATASETS[dataset_id]
    except KeyError:
        raise KeyError(
            f"unknown French dataset {dataset_id!r}; known: {sorted(DATASETS)}"
        ) from None


@dataclass(frozen=True)
class FrenchFile:
    """Everything parsed out of one French artifact.

    Attributes:
        member_name: The CSV inside the zip that was parsed.
        preamble: The file's prose header, verbatim. Preserved because it carries
            the source vintage ("created using the 202606 CRSP database"), the
            sentinel declaration, and construction notes that appear nowhere in
            machine-readable form.
        tables: One entry per table found, each with its own frequency and units.
        warnings: File-level problems, as opposed to per-table ones.
    """

    member_name: str
    preamble: str
    tables: tuple[ParsedTable, ...]
    warnings: tuple[str, ...]

    def table(self, table_id: str) -> ParsedTable:
        for candidate in self.tables:
            if candidate.table_id == table_id:
                return candidate
        raise KeyError(
            f"no table {table_id!r}; found {[t.table_id for t in self.tables]}"
        )


def download(
    cache: RawCache,
    dataset: FrenchDataset,
    *,
    force: bool = False,
    timeout: float = 60.0,
) -> CacheEntry:
    """Fetch the dataset zip into ``cache``, reusing the cached bytes unless forced.

    No ``User-Agent`` override is set. The Dartmouth host serves the zips to any
    client, and inventing an agent string only adds a way for the request to
    start failing later.
    """
    return cache.fetch(dataset.url, force=force, timeout=timeout)


def parse(
    cache: RawCache, entry: CacheEntry, *, dataset: FrenchDataset | None = None
) -> FrenchFile:
    """Parse a cached French artifact.

    Reads exclusively from the cache, so parsing without a stored raw artifact is
    impossible: :meth:`RawCache.read` raises ``RawArtifactMissing``.

    Passing ``dataset`` supplies the registry's units declaration for tables the
    file does not label. Omitting it is safe but conservative: an unlabelled table
    then comes back with unknown units and untransformed values rather than being
    divided by 100 on an assumption the caller never made.
    """
    raw = cache.read(entry)
    member_name, csv_bytes, warnings = _extract_member(raw)
    text, decode_warnings = _decode(csv_bytes)
    return _parse_text(
        text,
        member_name,
        (*warnings, *decode_warnings),
        default_source_units=dataset.default_source_units if dataset else None,
    )


def load(
    cache: RawCache, dataset: FrenchDataset, *, force: bool = False
) -> tuple[CacheEntry, FrenchFile, tuple[DatasetManifest, ...]]:
    """Download if needed, parse, and build manifests, in one call."""
    entry = download(cache, dataset, force=force)
    parsed = parse(cache, entry, dataset=dataset)
    return (entry, parsed, build_manifests(dataset, entry, parsed))


def build_manifests(
    dataset: FrenchDataset, entry: CacheEntry, parsed: FrenchFile
) -> tuple[DatasetManifest, ...]:
    """Build one manifest per table in the file.

    The file preamble is folded into every manifest's warnings. It is the source's
    only statement of its own vintage and sentinel convention, and a manifest that
    dropped it would understate what a reader must know to use the numbers.
    """
    preamble_note = (
        "source file preamble (verbatim, the only place the file describes "
        f"itself): {parsed.preamble.strip()!r}"
    )
    manifests: list[DatasetManifest] = []
    for table in parsed.tables:
        banner_note = (
            f"source table banner (verbatim): {table.banner.strip()!r}"
            if table.banner.strip()
            else "source table banner: none; this table is unlabelled in the file"
        )
        manifests.append(
            manifest_from_table(
                dataset_id=f"{dataset.dataset_id}_{table.table_id}",
                entry=entry,
                table=table,
                parser_version=PARSER_VERSION,
                availability_policy=dataset.availability_policy,
                revision_policy=dataset.revision_policy,
                license_or_terms_url=LICENSE_OR_TERMS_URL,
                extra_warnings=(
                    f"member parsed from zip: {parsed.member_name}",
                    banner_note,
                    preamble_note,
                    *parsed.warnings,
                ),
            )
        )
    return tuple(manifests)


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


def _extract_member(raw: bytes) -> tuple[str, bytes, tuple[str, ...]]:
    """Return the CSV member of a zip, or the bytes themselves if not a zip.

    Plain-CSV input is accepted so that committed fixtures can stay readable text
    in Git while exercising the identical code path as a downloaded zip.
    """
    if not raw.startswith(b"PK\x03\x04"):
        return ("<uncompressed>", raw, ())
    warnings: list[str] = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir() and not info.filename.startswith("__MACOSX/")
        ]
        if not names:
            raise FrenchParseError("zip archive contains no files")
        candidates = [n for n in names if n.lower().endswith((".csv", ".txt"))] or names
        if len(names) > 1:
            warnings.append(
                f"zip contains {len(names)} members {sorted(names)}; "
                f"parsed {sorted(candidates)[0]!r} only"
            )
        member = sorted(candidates)[0]
        return (member, archive.read(member), tuple(warnings))


def _decode(data: bytes) -> tuple[str, tuple[str, ...]]:
    try:
        return (data.decode("utf-8"), ())
    except UnicodeDecodeError:
        return (
            data.decode("latin-1"),
            (
                "raw bytes are not valid UTF-8; decoded as latin-1. Non-ASCII "
                "bytes in a Ken French file usually mean the prose header "
                "changed, so re-read the preamble before trusting column names.",
            ),
        )


# --------------------------------------------------------------------------- #
# Structural parsing
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _Block:
    header_index: int
    banner_start: int
    start: int
    end: int  # exclusive
    key_width: int


def _is_data_row(line: str) -> bool:
    if "," not in line:
        return False
    return bool(_DATE_KEY.match(line.split(",", 1)[0].strip()))


def _find_blocks(lines: Sequence[str]) -> list[_Block]:
    """Locate every table by structure, never by line number.

    A block is a maximal run of consecutive lines whose first field is a date key
    of constant width. Requiring constant width splits a monthly table from an
    annual one even when the source omits the blank line between them.
    """
    runs: list[tuple[int, int, int]] = []
    index = 0
    total = len(lines)
    while index < total:
        if not _is_data_row(lines[index]):
            index += 1
            continue
        width = len(lines[index].split(",", 1)[0].strip())
        end = index + 1
        while (
            end < total
            and _is_data_row(lines[end])
            and len(lines[end].split(",", 1)[0].strip()) == width
        ):
            end += 1
        runs.append((index, end, width))
        index = end

    blocks: list[_Block] = []
    for start, end, width in runs:
        header_index = start - 1
        while header_index >= 0 and not lines[header_index].strip():
            header_index -= 1
        banner_start = header_index
        while banner_start - 1 >= 0 and lines[banner_start - 1].strip():
            banner_start -= 1
        blocks.append(
            _Block(
                header_index=header_index,
                banner_start=max(banner_start, 0),
                start=start,
                end=end,
                key_width=width,
            )
        )
    return blocks


def _slug(text: str) -> str:
    return _SLUG_STRIP.sub("_", text.lower()).strip("_")[:80]


def _frequency_for(width: int) -> Frequency:
    mapping: dict[int, Frequency] = {4: "annual", 6: "monthly", 8: "daily"}
    return mapping.get(width, "unknown")


def _period_label(key: str) -> str:
    if len(key) == 4:
        return key
    if len(key) == 6:
        return f"{key[:4]}-{key[4:]}"
    if len(key) == 8:
        return f"{key[:4]}-{key[4:6]}-{key[6:]}"
    return key


def _infer_units(
    banner: str, preamble: str, default_source_units: str | None
) -> tuple[str, str, str, tuple[str, ...]]:
    """Classify a table's units from the only place the source states them: prose.

    Returns ``(source_units, units, unit_transform, warnings)``.

    The rules are ordered and every branch records how it decided, because a
    wrong unit is the failure mode that survives every downstream check: a factor
    premium a hundred times too large still passes a duplicate-date test. A table
    the rules cannot classify comes back as ``unknown`` and untransformed. That is
    a deliberate refusal — "probably percent" is exactly the assumption that turns
    the 25-portfolio file's firm counts and BE/ME averages into nonsense.
    """
    lowered = banner.lower()
    if "number of firms" in lowered:
        return (
            "count",
            "count",
            "identity",
            (
                "classified as firm counts from the banner "
                f"{banner.strip()!r}; no unit conversion applied.",
            ),
        )
    if "market cap" in lowered:
        return (
            "unknown",
            "unknown",
            "identity",
            (
                "classified as average market cap from the banner "
                f"{banner.strip()!r}. The file states neither currency nor "
                "scale, so the values are left untransformed and the unit is "
                "recorded as unknown. Do not assume dollars or millions without "
                "checking the data library page.",
            ),
        )
    if "average of" in lowered or "sum[" in lowered or "be/me" in lowered:
        return (
            "ratio",
            "ratio",
            "identity",
            (
                "classified as a value-weighted accounting characteristic, not a "
                "return, from the banner "
                f"{banner.strip()!r}. No percent conversion was applied. The "
                "banner is the only definition of this quantity that the file "
                "provides; read it before using the numbers.",
            ),
        )
    if "return" in lowered or "factor" in lowered:
        return (
            "percent",
            "decimal",
            "value / 100",
            (
                "classified as returns from the banner "
                f"{banner.strip()!r}. The file never declares its units in "
                "machine-readable form; percent is the Ken French Data Library "
                "convention and was divided by 100 to give decimals. If the "
                "source ever changes convention this parser is silently wrong, "
                "so validation.validate_table's plausibility check is not "
                "optional.",
            ),
        )
    if default_source_units == "percent":
        checked_against = (
            "the prose header" if "percent" in preamble.lower() else "the data library page"
        )
        return (
            "percent",
            "decimal",
            "value / 100",
            (
                "this table is unlabelled in the file. Percent was taken from "
                "the dataset registry's declaration for this file, not from "
                "anything the file itself says, and divided by 100 to give "
                "decimals. The registry declaration is a claim this repository "
                "makes about the source and is only as good as the last time "
                f"someone checked it against {checked_against}.",
            ),
        )
    return (
        "unknown",
        "unknown",
        "identity",
        (
            f"units could not be classified. Banner: {banner.strip()!r}. No "
            "conversion was applied and the values are exactly as the file "
            "wrote them. Classify this table explicitly before using it in any "
            "calculation.",
        ),
    )


def _parse_columns(header_line: str, field_count: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    warnings: list[str] = []
    fields = [cell.strip() for cell in header_line.split(",")]
    if fields and fields[0] == "":
        columns = fields[1:]
    else:
        columns = fields
        warnings.append(
            f"header row {header_line.strip()!r} does not begin with an empty "
            "date cell; every field was treated as a data column."
        )
    expected = field_count - 1
    if len(columns) < expected:
        warnings.append(
            f"header declares {len(columns)} columns but rows carry {expected}; "
            "the surplus columns were named unnamed_N. Column-name drift at the "
            "source is the usual cause."
        )
        columns = [*columns, *(f"unnamed_{i}" for i in range(len(columns) + 1, expected + 1))]
    elif len(columns) > expected:
        warnings.append(
            f"header declares {len(columns)} columns but rows carry {expected}; "
            f"the trailing header names {columns[expected:]!r} were dropped."
        )
        columns = columns[:expected]
    return (tuple(columns), tuple(warnings))


def _is_sentinel(value: float) -> bool:
    return any(abs(value - sentinel) < 1e-9 for sentinel in FRENCH_SENTINELS)


def _parse_block(
    lines: Sequence[str],
    block: _Block,
    preamble: str,
    used_ids: set[str],
    *,
    default_source_units: str | None,
    frequency_is_unique: bool,
) -> ParsedTable:
    if block.header_index >= 0:
        header_line = lines[block.header_index]
        banner = "\n".join(
            line.strip()
            for line in lines[block.banner_start : block.header_index]
            if line.strip()
        )
    else:
        header_line = ""
        banner = ""

    rows_raw = [lines[i] for i in range(block.start, block.end)]
    field_count = max(len(row.split(",")) for row in rows_raw)
    warnings: list[str] = []
    if header_line and "," in header_line and not _is_data_row(header_line):
        columns, column_warnings = _parse_columns(header_line, field_count)
        warnings.extend(column_warnings)
    else:
        columns = tuple(f"unnamed_{i}" for i in range(1, field_count))
        warnings.append(
            "no header row was found above this table; columns were named "
            "unnamed_N. Do not join this table to anything by position."
        )

    source_units, units, transform, unit_warnings = _infer_units(
        banner, preamble, default_source_units
    )
    warnings.extend(unit_warnings)
    scale = 0.01 if transform == "value / 100" else 1.0

    periods: list[str] = []
    values: list[tuple[float | None, ...]] = []
    sentinel_hits: list[str] = []
    blank_hits: list[str] = []
    unparsed_hits: list[str] = []
    ragged_rows: list[str] = []

    for line in rows_raw:
        cells = [cell.strip() for cell in line.split(",")]
        key = cells[0]
        label = _period_label(key)
        payload = cells[1:]
        if len(payload) != len(columns):
            ragged_rows.append(label)
            payload = [*payload, *([""] * len(columns))][: len(columns)]
        row: list[float | None] = []
        for column, cell in zip(columns, payload, strict=True):
            if cell == "":
                blank_hits.append(f"{label}/{column}")
                row.append(None)
                continue
            try:
                number = float(cell)
            except ValueError:
                unparsed_hits.append(f"{label}/{column}={cell!r}")
                row.append(None)
                continue
            if _is_sentinel(number):
                sentinel_hits.append(f"{label}/{column}")
                row.append(None)
                continue
            row.append(number * scale)
        periods.append(label)
        values.append(tuple(row))

    if sentinel_hits:
        warnings.append(
            f"{len(sentinel_hits)} cells held the declared missing-data sentinels "
            f"{list(FRENCH_SENTINELS)} and were converted to missing, not to "
            f"data. First: {sentinel_hits[:4]}; last: {sentinel_hits[-1]}."
        )
    if blank_hits:
        warnings.append(
            f"{len(blank_hits)} cells were empty in the source: {blank_hits[:4]}"
        )
    if unparsed_hits:
        warnings.append(
            f"{len(unparsed_hits)} cells were not numeric and became missing: "
            f"{unparsed_hits[:4]}"
        )
    if ragged_rows:
        warnings.append(
            f"{len(ragged_rows)} rows did not carry {len(columns)} value fields "
            f"and were padded with missing values: {ragged_rows[:4]}"
        )

    frequency = _frequency_for(block.key_width)
    if frequency == "unknown":
        warnings.append(
            f"date keys are {block.key_width} characters wide, which matches "
            "none of YYYY, YYYYMM or YYYYMMDD; the frequency is recorded as "
            "unknown rather than guessed."
        )

    table_id = _table_id(
        banner, frequency, used_ids, frequency_is_unique=frequency_is_unique
    )
    used_ids.add(table_id)
    return ParsedTable(
        table_id=table_id,
        banner=banner,
        columns=columns,
        periods=tuple(periods),
        values=tuple(values),
        frequency=frequency,
        source_units=source_units,
        units=units,
        unit_transform=transform,
        warnings=tuple(warnings),
    )


def _table_id(
    banner: str, frequency: str, used: Iterable[str], *, frequency_is_unique: bool
) -> str:
    """Name a table by what the source calls it, falling back to its frequency.

    When a file holds exactly one table at a given frequency, the frequency alone
    is the clearest name and matches the plan's own example
    (``french_us_ff5_monthly``). When it does not — the 25-portfolio file has six
    monthly tables — the banner slug is the only thing that distinguishes them, so
    it is used in full and, if two banners still collide after truncation, a short
    digest of the whole banner is appended. The digest is deterministic, so table
    ids do not move when a table is added ahead of another one.
    """
    taken = set(used)
    slug = _slug(banner.replace("\n", " "))
    if not slug or frequency_is_unique:
        candidate = frequency
    elif slug.endswith(f"_{frequency}") or slug == frequency:
        candidate = slug
    else:
        candidate = f"{slug}_{frequency}"
    if candidate not in taken:
        return candidate
    digest = hashlib.sha256(banner.encode("utf-8")).hexdigest()[:8]
    return f"{candidate}_{digest}"


def _parse_text(
    text: str,
    member_name: str,
    warnings: Sequence[str],
    *,
    default_source_units: str | None = None,
) -> FrenchFile:
    lines = text.splitlines()
    blocks = _find_blocks(lines)
    if not blocks:
        raise FrenchParseError(
            f"{member_name}: found no rows keyed by YYYY, YYYYMM or YYYYMMDD. "
            "The source layout has changed; do not work around this."
        )
    preamble = "\n".join(lines[: blocks[0].banner_start])
    file_warnings = list(warnings)

    frequency_counts = Counter(_frequency_for(block.key_width) for block in blocks)
    used_ids: set[str] = set()
    tables = tuple(
        _parse_block(
            lines,
            block,
            preamble,
            used_ids,
            default_source_units=default_source_units,
            frequency_is_unique=frequency_counts[_frequency_for(block.key_width)] == 1,
        )
        for block in blocks
    )

    trailing = [
        line.strip()
        for line in lines[blocks[-1].end :]
        if line.strip() and not _is_data_row(line)
    ]
    if trailing:
        file_warnings.append(f"trailing non-data lines after the last table: {trailing}")
    if len(tables) > 1:
        file_warnings.append(
            f"{len(tables)} separate tables were found in one file: "
            f"{[t.table_id for t in tables]}. Tables in one Ken French file "
            "differ in frequency and can differ in units. Never concatenate "
            "them and never assume the first one is the one you want."
        )
    return FrenchFile(
        member_name=member_name,
        preamble=preamble,
        tables=tables,
        warnings=tuple(file_warnings),
    )
