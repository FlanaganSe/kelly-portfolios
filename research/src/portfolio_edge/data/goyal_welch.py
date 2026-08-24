"""Goyal-Welch equity-premium predictor data, at its current location.

Where it actually lives
-----------------------
The URL this repository previously recorded returned HTTP 404, and the dataset
was written off as unreachable. It had moved, not disappeared. As of 2026-08-16
Amit Goyal publishes it from https://sites.google.com/view/agoyal145 with the
files themselves hosted on Google Drive:

* ``PredictorData2025.xlsx`` — the Welch and Goyal (2008) predictor set, updated
  annually. Human link
  ``https://docs.google.com/spreadsheets/d/1qwpl2R_DNujpU5YUkk8lacP1tTeMb9iJ/edit``;
  the machine path to the same object is that document's ``/export?format=xlsx``
  endpoint, which is what this module fetches.
* ``Data2025.xlsx`` — the superset behind Goyal, Welch and Zafirov, *A
  Comprehensive 2022 Look at the Empirical Performance of Equity Premium
  Prediction*, Review of Financial Studies 37(11), 2024. Fifty-six predictors
  rather than twenty, with a ``ReadMe`` sheet that names and dates every one.

Both were fetched on 2026-08-16 with HTTP 200 and the correct content type. The
Drive endpoint serves **no ``Last-Modified`` header**, so the file's only
observable availability bound is the retrieval timestamp — weaker than for every
other source in this repository, and recorded as such on the manifests. The
zipped-CSV and MATLAB copies on Goyal's page sit behind Drive's large-file
confirmation interstitial and are not fetched; the spreadsheet holds the same
data.

The two traps in this file
--------------------------
**Full-sample predictors are not point-in-time, and the source says which.** The
``ReadMe`` sheet of ``Data2025.xlsx`` marks ``cay``, ``pce``, ``ogap``, ``sntm``,
``fbm``, ``tchi`` and ``shtint`` with "Needs recomputation every period. Only
full-sample version here." Those columns were estimated once on the whole sample
and then written back over history. Using them in a predictive regression is
look-ahead by construction — not a subtle one, and not something a hash or an
availability timestamp can catch, because the *file* is honest and the *column*
is not.

**Nothing here is a vintage.** The whole history is rebuilt on every annual
update, and the ``ReadMe`` records source changes inside the history: "From 2022,
data on lty from FRED, data on ltr/corpr from Bloomberg indices". A ``lty``
observation for 2015 downloaded today may not be the number the 2008 paper used.

Units
-----
This workbook mixes an index level, dollar dividends and earnings, ratios,
annualised yields, period returns and a realised variance in adjacent columns, so
``units`` carries a per-column declaration rather than one word — see
:func:`portfolio_edge.data.workbook.column_unit_string`. Nothing is converted:
the numbers are already decimals, and a column this repository cannot defend a
unit for is declared ``undeclared`` rather than guessed at. That applies to most
of the predictors added by the 2024 extension, whose units the source does not
state anywhere machine-readable.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import Frequency, ParsedTable
from portfolio_edge.data.workbook import (
    SheetRows,
    WorkbookParseError,
    column_unit_string,
    load_xlsx_sheets,
)

__all__ = [
    "COLUMN_UNITS",
    "DATASETS",
    "FULL_SAMPLE_PREDICTORS",
    "LICENSE_OR_TERMS_URL",
    "PARSER_VERSION",
    "GoyalWelchDataset",
    "GoyalWelchFile",
    "GoyalWelchParseError",
    "build_manifests",
    "download",
    "get_dataset",
    "load",
    "parse",
    "parse_bytes",
    "parse_sheets",
]

#: Bump on any change to parsing behaviour: sheet selection, period decoding,
#: unit declaration, missing-value treatment.
PARSER_VERSION: Final = "goyal_welch/1.0.0"

LICENSE_OR_TERMS_URL: Final = "https://sites.google.com/view/agoyal145"

#: The workbook writes missing observations as the literal string ``NaN``.
MISSING_TOKENS: Final = frozenset({"", "NaN", "nan", "NA", "N/A", "."})

#: Columns the source itself marks as estimated once on the full sample and
#: written back over history. Predicting with any of them is look-ahead by
#: construction. Recorded here so the fact travels with the data rather than
#: living in a ReadMe sheet nobody opens.
FULL_SAMPLE_PREDICTORS: Final = (
    "cay",
    "pce",
    "ogap",
    "sntm",
    "fbm",
    "tchi",
    "shtint",
)

#: Units this repository is prepared to defend, keyed by the source's own column
#: name. Anything absent is rendered ``undeclared`` in the units string and named
#: in a warning. Magnitudes are never used to infer a unit.
COLUMN_UNITS: Final[dict[str, str]] = {
    # Levels and per-share amounts.
    "Index": "index_level",
    "price": "index_level",
    "D12": "currency_per_index_share_trailing_12m",
    "d12": "currency_per_index_share_trailing_12m",
    "E12": "currency_per_index_share_trailing_12m",
    "e12": "currency_per_index_share_trailing_12m",
    "D3": "currency_per_index_share_trailing_3m",
    "E3": "currency_per_index_share_trailing_3m",
    # Ratios.
    "b/m": "ratio",
    "d/p": "ratio",
    "d/y": "ratio",
    "e/p": "ratio",
    "d/e": "ratio",
    # Annualised yields and yield spreads.
    "tbl": "decimal_per_year",
    "AAA": "decimal_per_year",
    "BAA": "decimal_per_year",
    "lty": "decimal_per_year",
    "tms": "decimal_per_year",
    "dfy": "decimal_per_year",
    # Period returns, at the frequency of the sheet.
    "Rfree": "decimal_per_period",
    "infl": "decimal_per_period",
    "ltr": "decimal_per_period",
    "corpr": "decimal_per_period",
    "dfr": "decimal_per_period",
    "ret": "decimal_per_period",
    "retx": "decimal_per_period",
    "CRSP_SPvw": "decimal_per_period",
    "CRSP_SPvwx": "decimal_per_period",
    # Dimensionless constructed predictors whose definition the 2008 paper gives.
    "ntis": "decimal_ratio",
    "eqis": "decimal_ratio",
    "ik": "decimal_ratio",
    "i/k": "decimal_ratio",
    "cay": "decimal_ratio",
    "csp": "decimal_ratio",
    # Realised variance of daily returns within the period.
    "svar": "decimal_squared_return",
}

_AVAILABILITY: Final = (
    "Annual academic release. The Google Drive endpoint returns NO Last-Modified "
    "header, so the retrieval timestamp in this manifest is the only observable "
    "bound on when any row became available, and it bounds the whole file rather "
    "than any row. That is weaker than every other source in this repository. "
    "Several columns are also flagged by the source as full-sample estimates "
    "written back over history, which no availability timestamp can detect: see "
    "the full-sample-predictor warning."
)

_REVISION: Final = (
    "Not point-in-time. The full history is rebuilt on each annual update and the "
    "source records changes to its own inputs inside the history ('From 2022, "
    "data on lty from FRED, data on ltr/corpr from Bloomberg indices'). No "
    "vintage archive is published, so an observation downloaded today may not be "
    "the number any published paper used, and a sha256 here identifies the file "
    "downloaded and nothing more."
)


@dataclass(frozen=True)
class GoyalWelchSheet:
    """One sheet of a predictor workbook, and how its period column decodes.

    Attributes:
        period_column: The date column's name in the sheet, verbatim.
        period_format: ``yyyy``, ``yyyymm`` or ``yyyyq``.
        frequency: The ``ParsedTable`` frequency. Quarterly sheets are declared
            ``unknown`` because ``Frequency`` has no quarterly member and
            mislabelling a quarter as a month would be worse than declaring
            ignorance.
    """

    name: str
    period_column: str
    period_format: str
    frequency: Frequency


@dataclass(frozen=True)
class GoyalWelchDataset:
    """One predictor workbook, with its download URL and its policies."""

    dataset_id: str
    url: str
    vintage: str
    description: str
    sheets: tuple[GoyalWelchSheet, ...]
    readme_sheet: str | None = None
    availability_policy: str = _AVAILABILITY
    revision_policy: str = _REVISION


_SHEETS: Final = (
    GoyalWelchSheet(
        name="Monthly",
        period_column="yyyymm",
        period_format="yyyymm",
        frequency="monthly",
    ),
    GoyalWelchSheet(
        name="Quarterly",
        period_column="yyyyq",
        period_format="yyyyq",
        frequency="unknown",
    ),
    GoyalWelchSheet(
        name="Annual",
        period_column="yyyy",
        period_format="yyyy",
        frequency="annual",
    ),
)


def _drive_export(document_id: str) -> str:
    """The public export path for a Google Sheets document holding an upload."""
    return f"https://docs.google.com/spreadsheets/d/{document_id}/export?format=xlsx"


DATASETS: Final[dict[str, GoyalWelchDataset]] = {
    dataset.dataset_id: dataset
    for dataset in (
        GoyalWelchDataset(
            dataset_id="goyal_welch_predictors",
            url=_drive_export("1qwpl2R_DNujpU5YUkk8lacP1tTeMb9iJ"),
            vintage="PredictorData2025.xlsx, data through 2025",
            description=(
                "The predictor set of Welch, Ivo and Amit Goyal. 2008. 'A "
                "Comprehensive Look at the Empirical Performance of Equity "
                "Premium Prediction.' Review of Financial Studies 21(4): "
                "1455-1508, updated annually by the authors. Monthly from "
                "1871-01, quarterly from 1871Q1 and annual from 1871."
            ),
            sheets=_SHEETS,
        ),
        GoyalWelchDataset(
            dataset_id="goyal_welch_zafirov_predictors",
            url=_drive_export("17mw_IpaiLFDrGnrPRQ2o1ugV5nJsZuD1"),
            vintage="Data2025.xlsx, data through 2025",
            description=(
                "The extended predictor set of Goyal, Amit, Ivo Welch and "
                "Athanasse Zafirov. 2024. 'A Comprehensive 2022 Look at the "
                "Empirical Performance of Equity Premium Prediction.' Review of "
                "Financial Studies 37(11): 3490-3557. Fifty-six predictors "
                "including the twenty of the 2008 paper, with a ReadMe sheet "
                "naming and dating each one."
            ),
            sheets=_SHEETS,
            readme_sheet="ReadMe",
        ),
    )
}


class GoyalWelchParseError(ValueError):
    """Raised when a predictor workbook does not have the expected shape."""


def get_dataset(dataset_id: str) -> GoyalWelchDataset:
    """Look up a registered dataset, or raise ``KeyError`` naming the choices."""
    try:
        return DATASETS[dataset_id]
    except KeyError:
        raise KeyError(
            f"unknown Goyal-Welch dataset {dataset_id!r}; known: {sorted(DATASETS)}"
        ) from None


@dataclass(frozen=True)
class GoyalWelchFile:
    """Everything parsed out of one predictor workbook.

    Attributes:
        readme: The ReadMe sheet's rows rendered as text, verbatim, when the
            workbook has one. It is the only place the source names, dates and
            qualifies each predictor.
    """

    sheet_names: tuple[str, ...]
    tables: tuple[ParsedTable, ...]
    readme: str
    warnings: tuple[str, ...]

    def table(self, table_id: str) -> ParsedTable:
        for candidate in self.tables:
            if candidate.table_id == table_id:
                return candidate
        raise KeyError(
            f"no table {table_id!r}; parsed: {[t.table_id for t in self.tables]}"
        )


def download(
    cache: RawCache,
    dataset: GoyalWelchDataset,
    *,
    force: bool = False,
    timeout: float = 120.0,
) -> CacheEntry:
    """Fetch the workbook into ``cache``, reusing cached bytes unless forced.

    No ``User-Agent`` override. Verified on 2026-08-16: the Google Docs export
    endpoint serves the workbook to the default ``requests`` agent with HTTP 200
    after one redirect, and returns no ``Last-Modified``.
    """
    return cache.fetch(dataset.url, force=force, timeout=timeout)


def parse(
    cache: RawCache, entry: CacheEntry, *, dataset: GoyalWelchDataset
) -> GoyalWelchFile:
    """Parse a cached predictor workbook. Reads only from the cache."""
    return parse_bytes(cache.read(entry), dataset=dataset)


def parse_bytes(raw: bytes, *, dataset: GoyalWelchDataset) -> GoyalWelchFile:
    """Parse workbook bytes into one table per registered sheet."""
    try:
        sheets = load_xlsx_sheets(raw, source=dataset.dataset_id)
    except WorkbookParseError as exc:
        raise GoyalWelchParseError(str(exc)) from exc
    return parse_sheets(sheets, dataset=dataset)


def parse_sheets(
    sheets: Mapping[str, SheetRows], *, dataset: GoyalWelchDataset
) -> GoyalWelchFile:
    """Build the tables from already-read sheet rows.

    Split out from :func:`parse_bytes` so the period decoding, the unit
    declaration and the full-sample-predictor warning can be exercised offline
    against a frozen slice of the real workbook.
    """
    sheet_names = tuple(sheets)
    warnings: list[str] = []
    tables: list[ParsedTable] = []
    for declared in dataset.sheets:
        if declared.name not in sheets:
            raise GoyalWelchParseError(
                f"{dataset.dataset_id}: declared sheet {declared.name!r} is not "
                f"in this workbook. Sheets found: {list(sheet_names)}. Register "
                "the new layout rather than letting the parser pick another sheet."
            )
        tables.append(_build_table(sheets[declared.name], declared, dataset))

    readme = ""
    if dataset.readme_sheet is not None:
        if dataset.readme_sheet not in sheets:
            warnings.append(
                f"the declared ReadMe sheet {dataset.readme_sheet!r} is absent; "
                "the source's own variable dictionary was not captured."
            )
        else:
            readme = "\n".join(
                " | ".join(
                    "" if cell is None else str(cell).strip()
                    for cell in row
                ).strip(" |")
                for row in sheets[dataset.readme_sheet]
            ).strip()

    return GoyalWelchFile(
        sheet_names=sheet_names,
        tables=tuple(tables),
        readme=readme,
        warnings=tuple(warnings),
    )


def _build_table(
    rows: SheetRows, sheet: GoyalWelchSheet, dataset: GoyalWelchDataset
) -> ParsedTable:
    if not rows:
        raise GoyalWelchParseError(
            f"{dataset.dataset_id}: sheet {sheet.name!r} is empty"
        )
    header = [("" if cell is None else str(cell)).strip() for cell in rows[0]]
    if sheet.period_column not in header:
        raise GoyalWelchParseError(
            f"{dataset.dataset_id}: sheet {sheet.name!r} has no {sheet.period_column!r} "
            f"column; its header is {header}. The layout has changed."
        )
    period_index = header.index(sheet.period_column)
    keep = [
        index
        for index, name in enumerate(header)
        if name and index != period_index
    ]
    columns = tuple(header[index] for index in keep)

    warnings: list[str] = []
    blank = [index for index, name in enumerate(header) if not name]
    if blank:
        warnings.append(
            f"dropped {len(blank)} unnamed column(s) at sheet positions {blank}."
        )

    periods: list[str] = []
    values: list[tuple[float | None, ...]] = []
    text_cells = 0
    skipped = 0
    for row in rows[1:]:
        raw_period = row[period_index] if period_index < len(row) else None
        label = _period_label(raw_period, sheet.period_format)
        if label is None:
            if any(cell not in (None, "") for cell in row):
                skipped += 1
            continue
        cells: list[float | None] = []
        for index in keep:
            raw_cell = row[index] if index < len(row) else None
            number = _as_number(raw_cell)
            if number is None and isinstance(raw_cell, str) and raw_cell.strip():
                text_cells += 1
            cells.append(number)
        periods.append(label)
        values.append(tuple(cells))

    if not periods:
        raise GoyalWelchParseError(
            f"{dataset.dataset_id}: sheet {sheet.name!r} produced no rows"
        )
    if skipped:
        warnings.append(
            f"{skipped} non-empty rows had no parseable {sheet.period_column} and "
            "were skipped."
        )
    if text_cells:
        warnings.append(
            f"{text_cells} cells held text rather than a number and became "
            "missing values, not zeros. The workbook writes 'NaN' for a value it "
            "does not have."
        )

    undeclared = [name for name in columns if name not in COLUMN_UNITS]
    if undeclared:
        warnings.append(
            "no unit is declared for these columns and none is inferred from "
            f"their magnitudes: {undeclared}. They are marked 'undeclared' in the "
            "units string. The source states no units for the predictors added by "
            "the 2024 extension; read the ReadMe sheet and the paper before "
            "quoting any of them."
        )
    present_full_sample = [name for name in columns if name in FULL_SAMPLE_PREDICTORS]
    if present_full_sample:
        warnings.append(
            "FULL-SAMPLE PREDICTORS PRESENT: "
            f"{present_full_sample}. The source marks these 'Needs recomputation "
            "every period. Only full-sample version here.' — they were estimated "
            "once on the entire sample and written back over history, so using "
            "them in a predictive regression is look-ahead by construction. No "
            "hash and no availability timestamp can detect this; the file is "
            "honest and the column is not."
        )
    if sheet.period_format == "yyyyq":
        warnings.append(
            "QUARTERLY SHEET. Periods are labelled with the LAST month of each "
            "quarter, which was verified against the Monthly sheet rather than "
            "assumed: the quarterly Index for 1871Q1 equals the monthly Index for "
            "1871-03. Frequency is declared 'unknown' because ParsedTable has no "
            "quarterly member, so no gap check runs over this table."
        )

    unit_string = column_unit_string(columns, COLUMN_UNITS)
    return ParsedTable(
        table_id=sheet.name.lower(),
        banner=(
            f"Goyal-Welch equity premium predictor data, {dataset.vintage}, sheet "
            f"{sheet.name!r}."
        ),
        columns=columns,
        periods=tuple(periods),
        values=tuple(values),
        frequency=sheet.frequency,
        source_units=unit_string,
        units=unit_string,
        unit_transform="identity",
        warnings=(
            "UNITS ARE PER COLUMN and are in the units string, name=unit, in "
            "column order. Nothing was converted; the source publishes decimals, "
            "not percentages, for its rate and return columns.",
            *warnings,
        ),
    )


def _period_label(value: object, period_format: str) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    digits = str(int(value)) if isinstance(value, int | float) else str(value).strip()
    if not digits.isdigit():
        return None
    if period_format == "yyyy":
        if len(digits) != 4:
            return None
        return digits
    if period_format == "yyyymm":
        if len(digits) != 6:
            return None
        month = int(digits[4:])
        if not 1 <= month <= 12:
            return None
        return f"{digits[:4]}-{month:02d}"
    if period_format == "yyyyq":
        if len(digits) != 5:
            return None
        quarter = int(digits[4:])
        if not 1 <= quarter <= 4:
            return None
        return f"{digits[:4]}-{quarter * 3:02d}"
    raise ValueError(f"unrecognised period format {period_format!r}")


def _as_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        number = float(value)
        return None if number != number else number
    text = str(value).strip()
    if text in MISSING_TOKENS:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load(
    cache: RawCache, dataset: GoyalWelchDataset, *, force: bool = False
) -> tuple[CacheEntry, GoyalWelchFile, tuple[DatasetManifest, ...]]:
    """Download if needed, parse, and build one manifest per sheet."""
    entry = download(cache, dataset, force=force)
    parsed = parse(cache, entry, dataset=dataset)
    return (entry, parsed, build_manifests(dataset, entry, parsed))


def build_manifests(
    dataset: GoyalWelchDataset, entry: CacheEntry, parsed: GoyalWelchFile
) -> tuple[DatasetManifest, ...]:
    """Build one manifest per derived table."""
    readme_note = (
        (
            "the workbook's ReadMe sheet, verbatim — the source's only statement "
            f"of what each predictor is and over what sample: {parsed.readme!r}"
        )
        if parsed.readme
        else "this workbook carries no ReadMe sheet; the columns are documented "
        "only in Welch and Goyal (2008)."
    )
    return tuple(
        manifest_from_table(
            dataset_id=f"{dataset.dataset_id}_{table.table_id}",
            entry=entry,
            table=table,
            parser_version=PARSER_VERSION,
            availability_policy=dataset.availability_policy,
            revision_policy=dataset.revision_policy,
            license_or_terms_url=LICENSE_OR_TERMS_URL,
            extra_warnings=(
                f"VINTAGE PINNED: {dataset.vintage}. "
                f"SHEET PINNED: {table.table_id!r}, of sheets "
                f"{list(parsed.sheet_names)}.",
                f"dataset description: {dataset.description}",
                "SOURCE URL is the Google Docs export path for the document Amit "
                "Goyal links from https://sites.google.com/view/agoyal145. The "
                "document id is part of the data's identity; if the page starts "
                "linking a different id, that is a new dataset, not a refresh.",
                readme_note,
                *parsed.warnings,
            ),
        )
        for table in parsed.tables
    )
