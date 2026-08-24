"""Robert Shiller's ``ie_data`` workbook: US monthly stock data since 1871.

Where it actually lives
-----------------------
The URL this repository previously recorded, ``econ.yale.edu/~shiller/data/
ie_data.xls``, is still reachable but **stale**: on 2026-08-16 it returned a file
whose ``Last-Modified`` was 2023-10-17. The maintained copy is served from
https://shillerdata.com/, and its download link is a hashed content URL on
``img1.wsimg.com`` — the site is built on a hosting platform that serves assets
from a CDN. That link carries a ``?ver=`` token which changes when the file is
updated, so it is pinned in the registry and must be re-read from
https://shillerdata.com/ rather than guessed at when it stops working.

Retrieved 2026-08-16: HTTP 200, ``application/vnd.ms-excel``, ``Last-Modified:
Tue, 04 Aug 2026 15:29:32 GMT``, 1,673,216 bytes, last observation 2026-08.

What the workbook is
--------------------
A legacy OLE2 ``.xls`` — the same file Shiller has published since 2000 — with a
``Disclaimer`` sheet and a ``Data`` sheet. The ``Data`` sheet has an eight-row
stacked header whose column names are spread vertically across rows, then one row
per month from 1871-01, then a trailing footnote row. Only the last header row is
machine-usable, so this module declares the column names it expects and
cross-checks them against that row rather than trying to reassemble the stack.

Dates are floats of the form ``YYYY.MM``: ``1871.01`` is January and ``1871.1``
is October. That is the one place this file will silently produce a wrong answer,
and it is handled by rounding ``(value - year) * 100`` rather than by parsing the
text after the decimal point.

What the numbers are, and what they are not
-------------------------------------------
* **The price is not an end-of-month price.** Shiller's ``P`` is the *monthly
  average* of daily closes, except for the final row, whose footnote on
  2026-08-16 read "Aug price is Aug 1st close". Averaging suppresses volatility
  and moves a drawdown; this series must not be used where a month-end
  observation is meant.
* **Dividends and earnings are interpolated.** ``D`` and ``E`` are twelve-month
  trailing totals, published quarterly or annually by S&P and interpolated to
  monthly by Shiller. The last months of ``E`` are typically blank because the
  data are not in yet.
* **The CPI tail is estimated.** The footnote on 2026-08-16 read "Oct '25/July/
  Aug CPI estimated".
* **CAPE begins in 1881**, ten years after the price series, and is ``NA`` before
  then. ``NA`` is the workbook's own missing marker and becomes ``None`` here,
  never zero.
* **Two columns are index levels that start at 1**: the real total return price
  and the real total bond return. They are wealth indices, not returns.
* **One column is a gross monthly factor**, ``Monthly Total Bond Returns``, whose
  values sit around 1.00. A reader who treats it as a return is out by 100
  percentage points a month.
* Two columns in the sheet are entirely blank spacers and are dropped, with the
  drop recorded as a warning.

Not point-in-time. Shiller rebuilds and re-estimates the whole file on each
update — the CPI tail is revised, the S&P earnings are restated — and publishes
no vintage archive.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.workbook import (
    SheetRows,
    WorkbookParseError,
    column_unit_string,
    load_xls_sheets,
)

__all__ = [
    "COLUMN_UNITS",
    "DATASETS",
    "LICENSE_OR_TERMS_URL",
    "PARSER_VERSION",
    "ShillerDataset",
    "ShillerFile",
    "ShillerParseError",
    "build_manifests",
    "download",
    "get_dataset",
    "load",
    "parse",
    "parse_bytes",
    "parse_sheets",
]

#: Bump on any change to parsing behaviour: header detection, date decoding,
#: column naming, missing-value treatment.
PARSER_VERSION: Final = "shiller/1.0.0"

LICENSE_OR_TERMS_URL: Final = "https://shillerdata.com/"

#: The workbook's own missing marker, written as text in numeric columns.
MISSING_TOKENS: Final = frozenset({"", "NA", "N/A", "na", "nan", "NaN"})

#: What each column is. Declared here rather than inferred from magnitudes, and
#: rendered into ``units`` per column because this sheet mixes index levels,
#: per-share currency amounts, ratios, annualised percentages, decimal returns
#: and one gross return factor in adjacent columns.
COLUMN_UNITS: Final[dict[str, str]] = {
    "P": "index_level",
    "D": "currency_per_index_share_trailing_12m",
    "E": "currency_per_index_share_trailing_12m",
    "CPI": "index_1982_1984_eq_100",
    "Date_Fraction": "decimal_year",
    "Long_Interest_Rate_GS10": "percent_per_year",
    "Real_Price": "index_level_constant_currency",
    "Real_Dividend": "currency_per_index_share_trailing_12m_constant_currency",
    "Real_Total_Return_Price": "wealth_index_constant_currency",
    "Real_Earnings": "currency_per_index_share_trailing_12m_constant_currency",
    "Real_TR_Scaled_Earnings": "currency_per_index_share_trailing_12m_constant_currency",
    "CAPE": "ratio",
    "TR_CAPE": "ratio",
    "Excess_CAPE_Yield": "decimal_per_year",
    "Monthly_Total_Bond_Returns": "gross_return_factor",
    "Real_Total_Bond_Returns": "wealth_index_constant_currency",
    "Ten_Year_Annualized_Stock_Real_Return": "decimal_per_year",
    "Ten_Year_Annualized_Bond_Real_Return": "decimal_per_year",
    "Real_Ten_Year_Excess_Annualized_Return": "decimal_per_year",
}

#: Column names this repository assigns, in sheet order, ``None`` for a blank
#: spacer column that is dropped. The workbook's own header is stacked across
#: eight rows and cannot be read as a single row, so the names are declared and
#: the *last* header row is cross-checked against ``_HEADER_TOKENS`` below.
_COLUMNS: Final[tuple[str | None, ...]] = (
    None,  # the date column, consumed as the period label
    "P",
    "D",
    "E",
    "CPI",
    "Date_Fraction",
    "Long_Interest_Rate_GS10",
    "Real_Price",
    "Real_Dividend",
    "Real_Total_Return_Price",
    "Real_Earnings",
    "Real_TR_Scaled_Earnings",
    "CAPE",
    None,  # blank spacer
    "TR_CAPE",
    None,  # blank spacer
    "Excess_CAPE_Yield",
    "Monthly_Total_Bond_Returns",
    "Real_Total_Bond_Returns",
    "Ten_Year_Annualized_Stock_Real_Return",
    "Ten_Year_Annualized_Bond_Real_Return",
    "Real_Ten_Year_Excess_Annualized_Return",
)

#: Tokens expected in the workbook's final header row, at the same positions as
#: ``_COLUMNS``. A mismatch is a warning rather than an error: Shiller edits the
#: header wording, and refusing to parse over a changed adjective would be worse
#: than recording that it changed.
_HEADER_TOKENS: Final[tuple[str, ...]] = (
    "Date",
    "P",
    "D",
    "E",
    "CPI",
    "Fraction",
    "Rate GS10",
    "Price",
    "Dividend",
    "Price",
    "Earnings",
    "Earnings",
    "P/E10 or",
    "",
    "TR P/E10 or",
    "",
    "Yield",
    "Returns",
    "Returns",
    "Real Return",
    "Real Return",
    "Returns",
)


class ShillerParseError(ValueError):
    """Raised when the ie_data workbook does not have the expected shape."""


@dataclass(frozen=True)
class ShillerDataset:
    """One Shiller workbook, with its download URL and its policies."""

    dataset_id: str
    url: str
    data_sheet: str
    description: str
    availability_policy: str
    revision_policy: str


_AVAILABILITY: Final = (
    "Monthly observations posted to shillerdata.com without a per-row as-of date. "
    "The HTTP Last-Modified header of the workbook bounds the whole file and no "
    "individual row. The row for month M was not available during month M: the "
    "price is a monthly average of daily closes, earnings are published on S&P's "
    "quarterly schedule and interpolated, and the workbook's own footnotes state "
    "which of the most recent CPI observations are estimates rather than "
    "releases."
)

_REVISION: Final = (
    "Not point-in-time. The whole file is rebuilt on each update: the CPI tail is "
    "replaced as estimates become releases, S&P earnings are restated, and the "
    "final price row is a partial-month close that becomes a monthly average in "
    "the next release. No vintage archive is published, so a sha256 here "
    "identifies the file downloaded and says nothing about what the series looked "
    "like at any earlier date."
)

DATASETS: Final[dict[str, ShillerDataset]] = {
    dataset.dataset_id: dataset
    for dataset in (
        ShillerDataset(
            dataset_id="shiller_ie_data",
            # Read from https://shillerdata.com/ on 2026-08-16. The ?ver= token
            # changes when the file is updated; re-read the landing page rather
            # than guessing a new one. The older econ.yale.edu path still
            # answers but served a 2023 file on the same date.
            url=(
                "https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/"
                "downloads/e27e58c1-8ae0-488c-a976-a298708c7175/ie_data.xls"
                "?ver=1785857394436"
            ),
            data_sheet="Data",
            description=(
                "Monthly US stock price, dividend and earnings data with the "
                "consumer price index and the long government bond yield, from "
                "1871-01, together with the cyclically adjusted price-earnings "
                "ratio (CAPE), its total-return variant, and the excess CAPE "
                "yield. The dataset behind Shiller, Irrational Exuberance "
                "(Princeton University Press, 2000, 2005, 2015), updated."
            ),
            availability_policy=_AVAILABILITY,
            revision_policy=_REVISION,
        ),
    )
}


def get_dataset(dataset_id: str) -> ShillerDataset:
    """Look up a registered dataset, or raise ``KeyError`` naming the choices."""
    try:
        return DATASETS[dataset_id]
    except KeyError:
        raise KeyError(
            f"unknown Shiller dataset {dataset_id!r}; known: {sorted(DATASETS)}"
        ) from None


@dataclass(frozen=True)
class ShillerFile:
    """Everything parsed out of one ie_data workbook.

    Attributes:
        disclaimer: The Disclaimer sheet's text, verbatim. It is the only place
            the workbook states what it warrants, which is nothing.
        footnotes: Text found below the last data row. These carry the "Aug price
            is Aug 1st close" and "CPI estimated" statements, which change from
            release to release and are the only per-row availability information
            in the file.
    """

    sheet_names: tuple[str, ...]
    table: ParsedTable
    disclaimer: str
    footnotes: tuple[str, ...]
    warnings: tuple[str, ...]


def download(
    cache: RawCache,
    dataset: ShillerDataset,
    *,
    force: bool = False,
    timeout: float = 120.0,
) -> CacheEntry:
    """Fetch the workbook into ``cache``, reusing cached bytes unless forced.

    No ``User-Agent`` override. Verified on 2026-08-16: the CDN serves the file to
    the default ``requests`` agent with HTTP 200 and a ``Last-Modified`` header.
    """
    return cache.fetch(dataset.url, force=force, timeout=timeout)


def parse(cache: RawCache, entry: CacheEntry, *, dataset: ShillerDataset) -> ShillerFile:
    """Parse a cached ie_data workbook. Reads only from the cache."""
    return parse_bytes(cache.read(entry), dataset=dataset)


def parse_bytes(raw: bytes, *, dataset: ShillerDataset) -> ShillerFile:
    """Parse workbook bytes into one monthly table."""
    try:
        sheets = load_xls_sheets(raw, source=dataset.dataset_id)
    except WorkbookParseError as exc:
        raise ShillerParseError(str(exc)) from exc
    return parse_sheets(sheets, dataset=dataset)


def parse_sheets(
    sheets: Mapping[str, SheetRows], *, dataset: ShillerDataset
) -> ShillerFile:
    """Build the table from already-read sheet rows.

    Split out from :func:`parse_bytes` so that header detection, the YYYY.MM date
    decode, the NA handling and the footnote capture can all be exercised offline
    against a frozen slice of the real sheet. A legacy .xls cannot be truncated
    into a small fixture and no writer for the format is installed, so the slice
    is stored as rows rather than as bytes; :func:`load_xls_sheets` itself is
    covered by the container-rejection test and by the network test.
    """
    sheet_names = tuple(sheets)
    if dataset.data_sheet not in sheets:
        raise ShillerParseError(
            f"{dataset.dataset_id}: the declared data sheet "
            f"{dataset.data_sheet!r} is not in this workbook. Sheets found: "
            f"{list(sheet_names)}."
        )
    rows = sheets[dataset.data_sheet]
    if not rows:
        raise ShillerParseError(f"{dataset.dataset_id}: sheet {dataset.data_sheet!r} is empty")

    warnings: list[str] = []
    first_data = next(
        (index for index, row in enumerate(rows) if _period_label(row[0] if row else None)),
        None,
    )
    if first_data is None or first_data == 0:
        raise ShillerParseError(
            f"{dataset.dataset_id}: no row has a YYYY.MM date in its first "
            "column, so the data block could not be located. The workbook layout "
            "has changed."
        )
    header_row = [str(cell).strip() for cell in rows[first_data - 1]]
    for index, expected in enumerate(_HEADER_TOKENS):
        actual = header_row[index] if index < len(header_row) else ""
        if actual != expected:
            warnings.append(
                f"header cell {index} reads {actual!r}, not the expected "
                f"{expected!r}; the workbook's header wording has changed. The "
                "column names in this table are this repository's declaration, "
                "not the file's."
            )

    width = len(_COLUMNS)
    columns = tuple(name for name in _COLUMNS if name is not None)
    dropped = tuple(
        (index, header_row[index] if index < len(header_row) else "")
        for index, name in enumerate(_COLUMNS)
        if name is None and index > 0
    )
    if dropped:
        warnings.append(
            f"dropped {len(dropped)} blank spacer column(s) at sheet positions "
            f"{[index for index, _ in dropped]}; their header cells read "
            f"{[text for _, text in dropped]}."
        )

    periods: list[str] = []
    values: list[tuple[float | None, ...]] = []
    footnotes: list[str] = []
    text_cells = 0
    for row in rows[first_data:]:
        label = _period_label(row[0] if row else None)
        if label is None:
            note = " ".join(
                str(cell).strip() for cell in row if str(cell).strip()
            ).strip()
            if note:
                footnotes.append(note)
            continue
        cells: list[float | None] = []
        for index, name in enumerate(_COLUMNS):
            if name is None:
                continue
            raw_cell = row[index] if index < len(row) else None
            number = _as_number(raw_cell)
            if number is None and isinstance(raw_cell, str) and raw_cell.strip():
                text_cells += 1
            cells.append(number)
        periods.append(label)
        values.append(tuple(cells))

    if not periods:
        raise ShillerParseError(f"{dataset.dataset_id}: the data block held no rows")
    if len(rows[first_data]) < width:
        warnings.append(
            f"the first data row has {len(rows[first_data])} cells against the "
            f"{width} this parser expects; missing trailing cells became missing "
            "values, not zeros."
        )
    if text_cells:
        warnings.append(
            f"{text_cells} cells held text rather than a number and became "
            f"missing values, not zeros. The workbook writes {sorted(MISSING_TOKENS)} "
            "for a value it does not have; CAPE in particular is NA before 1881 "
            "because it needs ten prior years of earnings."
        )
    if footnotes:
        warnings.append(
            "footnote rows below the data block, verbatim — these state which of "
            "the most recent observations are estimates rather than releases and "
            f"they change with every update: {footnotes}"
        )

    unit_string = column_unit_string(columns, COLUMN_UNITS)
    undeclared = [name for name in columns if name not in COLUMN_UNITS]
    if undeclared:
        warnings.append(
            f"no unit is declared for {undeclared}; they are marked 'undeclared' "
            "in the units string rather than guessed from their magnitudes."
        )

    table = ParsedTable(
        table_id="monthly",
        banner=(
            "Robert J. Shiller, Stock Market Data Used in 'Irrational Exuberance', "
            "Princeton University Press, 2000, 2005, 2015, updated. Sheet 'Data'."
        ),
        columns=columns,
        periods=tuple(periods),
        values=tuple(values),
        frequency="monthly",
        source_units=unit_string,
        units=unit_string,
        unit_transform="identity",
        warnings=(
            "COLUMN NAMES ARE THIS REPOSITORY'S DECLARATION. The workbook's header "
            "is stacked across eight rows and no single row carries a usable name; "
            "the last header row is cross-checked and any difference is warned "
            "about above.",
            "UNITS ARE PER COLUMN and are in the units string, name=unit, in "
            "column order. No conversion was applied to any column: "
            "Long_Interest_Rate_GS10 is left as the published percent per year, "
            "Monthly_Total_Bond_Returns is a GROSS factor around 1.00 and not a "
            "return, and Real_Total_Return_Price and Real_Total_Bond_Returns are "
            "wealth index levels starting at 1, not returns.",
            "P IS A MONTHLY AVERAGE OF DAILY CLOSES, not a month-end price, except "
            "in the final row when the footnote says otherwise. Averaging "
            "suppresses volatility and moves any drawdown computed from it.",
            "D AND E ARE TRAILING TWELVE-MONTH TOTALS published quarterly or "
            "annually by S&P and INTERPOLATED to monthly frequency by the author.",
            *warnings,
        ),
    )
    disclaimer = "\n".join(
        " ".join(str(cell).strip() for cell in row if str(cell).strip())
        for name, sheet_rows in sheets.items()
        if name != dataset.data_sheet
        for row in sheet_rows
    ).strip()
    return ShillerFile(
        sheet_names=sheet_names,
        table=table,
        disclaimer=disclaimer,
        footnotes=tuple(footnotes),
        warnings=tuple(warnings),
    )


def _period_label(value: object) -> str | None:
    """Decode Shiller's ``YYYY.MM`` float into ``YYYY-MM``.

    ``1871.01`` is January and ``1871.1`` is October, which is why the month comes
    from rounding ``(value - year) * 100`` and never from the text after the
    decimal point.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
    elif isinstance(value, int | float):
        number = float(value)
    else:
        return None
    year = int(number)
    if not 1800 <= year <= 2200:
        return None
    month = round((number - year) * 100)
    if not 1 <= month <= 12:
        return None
    return f"{year:04d}-{month:02d}"


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
    cache: RawCache, dataset: ShillerDataset, *, force: bool = False
) -> tuple[CacheEntry, ShillerFile, tuple[DatasetManifest, ...]]:
    """Download if needed, parse, and build the manifest, in one call."""
    entry = download(cache, dataset, force=force)
    parsed = parse(cache, entry, dataset=dataset)
    return (entry, parsed, build_manifests(dataset, entry, parsed))


def build_manifests(
    dataset: ShillerDataset, entry: CacheEntry, parsed: ShillerFile
) -> tuple[DatasetManifest, ...]:
    """Build the manifest for the one table in the workbook."""
    return (
        manifest_from_table(
            dataset_id=f"{dataset.dataset_id}_{parsed.table.table_id}",
            entry=entry,
            table=parsed.table,
            parser_version=PARSER_VERSION,
            availability_policy=dataset.availability_policy,
            revision_policy=dataset.revision_policy,
            license_or_terms_url=LICENSE_OR_TERMS_URL,
            extra_warnings=(
                f"SHEET PINNED: {dataset.data_sheet!r}, of sheets "
                f"{list(parsed.sheet_names)}.",
                f"dataset description: {dataset.description}",
                (
                    "the workbook's Disclaimer sheet, verbatim: "
                    f"{parsed.disclaimer!r}"
                ),
                *parsed.warnings,
            ),
        ),
    )
