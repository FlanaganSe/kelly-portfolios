"""World Bank Pink Sheet reader — the redistributable commodity price history.

Why this source rather than the benchmark it is built from
-----------------------------------------------------------
:mod:`portfolio_edge.data.lbma` reaches the LBMA Gold Price directly and at daily
frequency, and it cannot be the source a published figure rests on: IBA states in writing
that "none of IBA's benchmark and other information may be used without a written licence
from IBA", LBMA states that "a licence from IBA is required in order to obtain, use or
redistribute real-time or historical benchmark data", and in March 2025 IBA had the World
Gold Council remove its historical LBMA series (gold.org/goldhub/data/gold-prices, read
2026-08-17). That is not a hypothetical restriction.

The Pink Sheet carries the same underlying benchmark at monthly frequency under **CC BY
4.0**, which permits copying, modification and redistribution for any purpose with
attribution. Its own definition of the series says so:

    "Gold, spot average of daily rates, from June 2025; previously (UK), 99.5% fine,
    London afternoon fixing, average of daily rates"

So before June 2025 this *is* the LBMA PM auction, monthly-averaged. That makes it the
primary instrument here and makes LBMA the cross-check rather than the other way round.

Two properties that decide how a return may be built from it
-------------------------------------------------------------
**It is a monthly average of daily rates, not a month-end level.** This is the same trap
:mod:`portfolio_edge.data.shiller` carries on ``P``. Returns differenced from period
averages are the Working (1960) problem: averaging induces positive first-order
autocorrelation of about +0.25 in an otherwise serially independent return series and
**understates the volatility**, so a Sharpe ratio computed from them is biased *upward*.
A study quoting a Sharpe ratio from this file must either say so or check it against a
month-end series. :mod:`portfolio_edge.studies._gold_sleeve_tables` does the latter.

**There is a methodology break in June 2025**, from the London afternoon fixing to spot.
It is fourteen months at the end of a 799-month series and changes nothing here, but it
is recorded rather than discovered later.

Retrieval
---------
Landing page: https://www.worldbank.org/en/research/commodity-markets. The workbook URL
carries a release-specific path segment and **changes with every release**; the one
registered below was current on 2026-08-17 and its sheet is stamped "Updated on August
04, 2026". An older path (``…0050012025``, stamped January 2025) still answers HTTP 200
and is no longer linked from the landing page, so a stale URL fails silently by serving
a stale vintage rather than by 404ing. That is why the release stamp is parsed out of the
sheet and written into every manifest.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.workbook import SheetRows, WorkbookParseError, load_xlsx_sheets

__all__ = [
    "ATTRIBUTION",
    "DATASETS",
    "LANDING_PAGE",
    "LICENSE_OR_TERMS_URL",
    "PARSER_VERSION",
    "PinkSheetDataset",
    "PinkSheetParseError",
    "UnknownDatasetError",
    "build_manifest",
    "download",
    "get_dataset",
    "monthly_series",
    "parse",
    "parse_bytes",
]

PARSER_VERSION: Final = "worldbank_pinksheet/1.0.0"

LANDING_PAGE: Final = "https://www.worldbank.org/en/research/commodity-markets"
LICENSE_OR_TERMS_URL: Final = "https://datacatalog.worldbank.org/public-licenses"

#: CC BY 4.0 requires attribution and a statement of changes. Carried in every manifest
#: so the obligation travels with the data rather than living in a README.
ATTRIBUTION: Final = (
    "World Bank Commodity Price Data (The Pink Sheet), "
    "https://www.worldbank.org/en/research/commodity-markets, CC BY 4.0. Changes made: "
    "the 'Monthly Prices' sheet was reshaped into one column per commodity with "
    "YYYY-MM period labels; no value was altered."
)

_PRICES_SHEET: Final = "Monthly Prices"
_NAME_ROW: Final = 4
_UNIT_ROW: Final = 5
_FIRST_DATA_ROW: Final = 6
_STAMP_ROW: Final = 3


class UnknownDatasetError(KeyError):
    """Raised when a dataset id is not registered."""


class PinkSheetParseError(ValueError):
    """Raised when the workbook does not have the shape this parser was written for."""


@dataclass(frozen=True)
class PinkSheetDataset:
    """One landed slice of the Pink Sheet.

    Attributes:
        release: The exact "Updated on ..." stamp this URL's sheet carries, compared
            verbatim on every parse. The workbook URL is release-specific and a
            superseded path keeps answering HTTP 200 with an older vintage, so a stale
            URL fails by serving stale data. This field is the only thing that catches
            it.
        commodities: The exact column headers to land, as the sheet writes them.
            Naming them is the point: landing the whole 70-column sheet would let a
            later study reach for a series nobody has read the definition of.
        definitions: The source's own definition of each, verbatim from the
            ``Description`` sheet. A commodity price with no definition is not evidence.
    """

    dataset_id: str
    url: str
    release: str
    commodities: tuple[str, ...]
    definitions: Mapping[str, str]
    availability_policy: str
    revision_policy: str


_AVAILABILITY: Final = (
    "The Pink Sheet is published early in the month following the last observation; the "
    "release stamp parsed from the sheet is the only publication date the file itself "
    "carries. A monthly average for month M is not available during month M. The "
    "retrieval timestamp in this manifest bounds availability for the last observation "
    "only."
)

_REVISION: Final = (
    "Not point-in-time. The World Bank republishes the full history in each monthly "
    "release and publishes no vintage archive this code can read, so a revised month "
    "overwrites in place. The release URL itself changes each month and an older path "
    "keeps answering with an older vintage, so a stale URL fails by serving stale data "
    "rather than by erroring. The sha256 here identifies the file downloaded; it cannot "
    "establish what any earlier row read on any earlier date."
)

_GOLD_DEFINITION: Final = (
    "Gold, spot average of daily rates, from June 2025; previously (UK), 99.5% fine, "
    "London afternoon fixing, average of daily rates. Sources named by the World Bank: "
    "Bloomberg Finance L.P.; Kitco.com; International Monetary Fund, International "
    "Financial Statistics; London Bullion Market; Metals Week; Platts Metals Week; "
    "Shearson Lehman Brothers, Metal Market Weekly Review; Thomson Reuters Datastream; "
    "World Bank."
)

DATASETS: Final[dict[str, PinkSheetDataset]] = {
    dataset.dataset_id: dataset
    for dataset in (
        PinkSheetDataset(
            dataset_id="worldbank_pinksheet_gold_monthly",
            url=(
                "https://thedocs.worldbank.org/en/doc/"
                "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/"
                "CMO-Historical-Data-Monthly.xlsx"
            ),
            release="Updated on August 04, 2026",
            commodities=("Gold",),
            definitions={"Gold": _GOLD_DEFINITION},
            availability_policy=_AVAILABILITY,
            revision_policy=_REVISION,
        ),
    )
}


def get_dataset(dataset_id: str) -> PinkSheetDataset:
    """Look up a registered dataset, or raise :class:`UnknownDatasetError`."""
    try:
        return DATASETS[dataset_id]
    except KeyError:
        raise UnknownDatasetError(
            f"{dataset_id!r} is not registered. Registered: {sorted(DATASETS)}"
        ) from None


def download(
    cache: RawCache,
    dataset: PinkSheetDataset,
    *,
    force: bool = False,
    timeout: float = 120.0,
) -> CacheEntry:
    """Fetch the workbook into ``cache``, reusing cached bytes unless forced.

    No ``User-Agent`` override; verified 2026-08-17 that thedocs.worldbank.org serves the
    default ``requests`` agent HTTP 200 after redirects.
    """
    return cache.fetch(dataset.url, force=force, timeout=timeout)


def parse(
    cache: RawCache, entry: CacheEntry, *, dataset: PinkSheetDataset
) -> ParsedTable:
    """Parse a cached workbook. Reads only from the cache."""
    return parse_bytes(cache.read(entry), dataset=dataset)


def parse_bytes(raw: bytes, *, dataset: PinkSheetDataset) -> ParsedTable:
    """Parse workbook bytes into one monthly table of the named commodities."""
    try:
        sheets = load_xlsx_sheets(raw, source=dataset.dataset_id)
    except WorkbookParseError as exc:
        raise PinkSheetParseError(str(exc)) from exc
    if _PRICES_SHEET not in sheets:
        raise PinkSheetParseError(
            f"{dataset.dataset_id}: no {_PRICES_SHEET!r} sheet; found {list(sheets)}"
        )
    return parse_sheet(sheets[_PRICES_SHEET], dataset=dataset)


def parse_sheet(rows: SheetRows, *, dataset: PinkSheetDataset) -> ParsedTable:
    """Build the table from already-read sheet rows.

    Split out so the whole header-location, unit and period path can be exercised offline
    against a small frozen slice rather than against a half-megabyte workbook in Git.
    """
    if len(rows) <= _FIRST_DATA_ROW:
        raise PinkSheetParseError(
            f"{dataset.dataset_id}: sheet has {len(rows)} rows, too few to hold a header "
            f"at row {_NAME_ROW} and data from row {_FIRST_DATA_ROW}"
        )
    names = [str(cell).strip() if cell is not None else "" for cell in rows[_NAME_ROW]]
    units = [str(cell).strip() if cell is not None else "" for cell in rows[_UNIT_ROW]]

    indices: dict[str, int] = {}
    for wanted in dataset.commodities:
        matches = [i for i, name in enumerate(names) if name == wanted]
        if len(matches) != 1:
            raise PinkSheetParseError(
                f"{dataset.dataset_id}: expected exactly one column headed {wanted!r} in "
                f"row {_NAME_ROW}, found {len(matches)}. The sheet's layout has changed; "
                "do not work around it."
            )
        indices[wanted] = matches[0]

    warnings: list[str] = []
    stamp = _release_stamp(rows)
    if stamp is None:
        warnings.append(
            f"no 'Updated on ...' stamp found in row {_STAMP_ROW}; the release this file "
            "belongs to could not be read out of the file itself."
        )
    elif stamp != dataset.release:
        warnings.append(
            f"RELEASE MISMATCH: the registry pins {dataset.release!r} but the sheet is "
            f"stamped {stamp!r}. The URL is release-specific and an older path keeps "
            "serving an older vintage, so this is the check that catches a stale URL."
        )

    periods: list[str] = []
    values: list[tuple[float | None, ...]] = []
    missing = {name: 0 for name in dataset.commodities}
    for row in rows[_FIRST_DATA_ROW:]:
        if not row or row[0] is None:
            continue
        period = _month_label(str(row[0]).strip())
        if period is None:
            continue
        cells: list[float | None] = []
        for name in dataset.commodities:
            index = indices[name]
            cell = row[index] if index < len(row) else None
            number = _as_number(cell)
            if number is None:
                missing[name] += 1
            cells.append(number)
        periods.append(period)
        values.append(tuple(cells))

    if not periods:
        raise PinkSheetParseError(f"{dataset.dataset_id}: no monthly observations parsed")
    if sorted(periods) != periods:
        raise PinkSheetParseError(
            f"{dataset.dataset_id}: periods are not increasing; the parser relies on "
            "source order and will not sort silently"
        )

    for name, count in missing.items():
        if count:
            warnings.append(
                f"{name} is missing in {count} of {len(periods)} months and those became "
                "missing values, never zeros."
            )
    for name in dataset.commodities:
        warnings.append(f"source definition of {name!r}: {dataset.definitions[name]}")
        warnings.append(f"source units of {name!r}: {units[indices[name]]!r}")
    warnings.append(
        "THESE ARE MONTHLY AVERAGES OF DAILY RATES, NOT MONTH-END LEVELS. Differencing "
        "period averages induces positive first-order autocorrelation and understates "
        "volatility, so a Sharpe ratio built from this file is biased upward. Check it "
        "against a month-end series before quoting it."
    )
    warnings.append(f"CC BY 4.0 attribution required: {ATTRIBUTION}")

    return ParsedTable(
        table_id="monthly",
        banner=(
            f"World Bank Commodity Price Data (The Pink Sheet), {_PRICES_SHEET}, "
            f"release {stamp or dataset.release}, nominal US dollars"
        ),
        columns=dataset.commodities,
        periods=tuple(periods),
        values=tuple(values),
        frequency="monthly",
        source_units="nominal_usd_per_stated_unit",
        units="nominal_usd_per_stated_unit",
        unit_transform="identity",
        warnings=tuple(warnings),
    )


def monthly_series(table: ParsedTable, column: str) -> tuple[tuple[str, float], ...]:
    """``(("YYYY-MM", level), ...)`` for one column, dropping missing months."""
    values = table.column(column)
    return tuple(
        (period, value)
        for period, value in zip(table.periods, values, strict=True)
        if value is not None
    )


def _release_stamp(rows: SheetRows) -> str | None:
    for row in rows[: _FIRST_DATA_ROW + 1]:
        for cell in row:
            if isinstance(cell, str) and cell.strip().startswith("Updated on"):
                return cell.strip()
    return None


def _month_label(raw: str) -> str | None:
    """``"1960M01"`` becomes ``"1960-01"``. Anything else is not a period label."""
    if len(raw) != 7 or raw[4] != "M":
        return None
    year, month = raw[:4], raw[5:]
    if not (year.isdigit() and month.isdigit()):
        return None
    if not 1 <= int(month) <= 12:
        return None
    return f"{year}-{month}"


def _as_number(cell: object) -> float | None:
    if cell is None or isinstance(cell, bool):
        return None
    if isinstance(cell, int | float):
        return float(cell)
    if isinstance(cell, str):
        text = cell.strip().replace(",", "")
        if not text or text in {"..", "...", "n/a", "-"}:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def build_manifest(
    dataset: PinkSheetDataset,
    entry: CacheEntry,
    table: ParsedTable,
    *,
    extra_warnings: Sequence[str] = (),
) -> DatasetManifest:
    """Build the manifest for one landed Pink Sheet slice."""
    return manifest_from_table(
        dataset_id=dataset.dataset_id,
        entry=entry,
        table=table,
        parser_version=PARSER_VERSION,
        availability_policy=dataset.availability_policy,
        revision_policy=dataset.revision_policy,
        license_or_terms_url=LICENSE_OR_TERMS_URL,
        extra_warnings=(
            f"RELEASE PINNED: {dataset.release}. The workbook URL is release-specific "
            f"and changes monthly; landing page {LANDING_PAGE}.",
            "licence: CC BY 4.0, which permits redistribution with attribution. This is "
            "the reason this file rather than the LBMA benchmark it is built from is the "
            "primary gold instrument here; see portfolio_edge.data.lbma.",
            "methodology break: the gold series switches from the London afternoon "
            "fixing to spot in June 2025, per the source's own definition.",
            *extra_warnings,
        ),
    )
