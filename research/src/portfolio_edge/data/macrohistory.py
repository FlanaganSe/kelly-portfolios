"""Jordà-Schularick-Taylor Macrohistory Database reader (release R6).

What this source is, and why it was acquired
--------------------------------------------
Every drawdown, equity-share and diversification figure this repository has
produced came from a single country. The JST Macrohistory Database is the
cheapest free correction available: annual total returns on equity, housing,
long-term government bonds and bills, plus consumer prices, for **18 advanced
economies from 1870**. The returns half is the data behind Jordà, Knoll,
Kuvshinov, Schularick and Taylor, *The Rate of Return on Everything, 1870-2015*
(QJE 2019), extended to 2020 by the R6 release.

Retrieved 2026-08-16 from https://www.macrohistory.net/database/. Licensed
CC BY-NC-SA 4.0 with a required citation, which is recorded in every manifest.

What the numbers are
--------------------
The R6 documentation defines them exactly, and this module repeats the
definitions rather than paraphrasing them:

    eq_tr       Equity total return, nominal.  r[t] = ((p[t] + d[t]) / p[t-1]) - 1
    eq_capgain  Equity capital gain, nominal.  cg[t] = (p[t] / p[t-1]) - 1
    eq_dp       Equity dividend yield.         dp[t] = dividend[t] / p[t]
    bond_tr     Government bond total return, nominal
    bill_rate   Bill rate, nominal
    housing_tr  Housing total return, nominal
    cpi         Consumer prices (index, 1990 = 100)

**Every return here is nominal and in local currency**, annual, and measured
year-end to year-end. Real returns are obtained by deflating with ``cpi``; see
:func:`real_total_return`, which is the only transformation this module offers
and which exists so that the deflation is written down once instead of at each
call site. The file also carries ``xrusd`` (local currency per USD). It is
deliberately **not** landed: this repository has not verified its direction
against an independent source, and a currency conversion applied in the wrong
direction is invisible in the output.

Known biases, from the source's own documentation
-------------------------------------------------
These are not caveats invented here. They are in the RORE data documentation and
they land on precisely the observations that dominate a drawdown ladder, so they
are attached to the manifests as warnings and repeated here:

* **Annual frequency understates drawdown.** A year-end series cannot see an
  intra-year peak or trough. A maximum drawdown computed from it is a lower
  bound on the loss an investor experienced, and is not comparable with a
  monthly figure. It is also not comparable across countries with different
  sample lengths, because maximum drawdown deepens mechanically with ``T``.
* **Canada and Ireland have no return data at all** in R6 — no equity, bond,
  bill or housing series. They appear in the macro half only. The returns panel
  is 16 countries, not 18.
* **Exchange closures are interpolated, and the file says which.**
  ``eq_tr_interp = 1`` marks Portugal 1975-1977 and Spain 1937-1940. For
  Portugal the documentation states the Lisbon exchange closed after the 1974
  Carnation Revolution, that no dividends were assumed to have been paid, and
  that prices were interpolated between firms listed before and after; the
  published ``eq_tr`` is then *identical* in 1975 and 1976 and nearly identical
  in 1977, which is a fill rather than a measurement. For Spain the Madrid
  exchange closed for the Civil War years 1937-1939 and returns were computed
  from shares listed both before and after, again with no dividends.
* **Gaps are not always flagged.** Japan has no equity return for **1946-1947**
  ("Stock exchange closed; no data"), which is the middle of the worst episode in
  the panel: 1945 alone is -90% in real terms and 1946-1947 inflation was +91%
  and +125%. Any Japanese drawdown computed from this file either stops at 1945
  or silently bridges two of the worst years with nothing.
* **A one-year return can span more than a year.** The Netherlands' 1945 return
  covers August 1944 to April 1946, and Switzerland's 1915 return covers July
  1914 to July 1916, because the exchanges were shut.
* **The German 1922-1923 rows are hyperinflation arithmetic.** ``eq_tr`` for 1923
  is 2.6e9 against consumer-price inflation of 1.06e9. The ratio of two
  astronomical annual numbers is not a return an investor could have realised at
  any point inside the year, and the 1948 currency reform then appears as a
  -88% nominal equity return. Bond returns have no data at all for 1923-1925.
* **The index behind a country changes.** The documentation's own coverage table
  moves between "all share", "broad", "blue chip" and "selected stocks", and
  between market-cap, book-cap, transaction-volume and equal weighting. France is
  blue chip for the whole sample (a CAC-40-like top-40 index); Germany is blue
  chip 1914-1959; the UK is blue chip 1929-1963.
* **Bills are often not bills.** "Much of our bill rate data before the 1960s
  actually consist of deposit rates" or money-market rates.

None of this is investable. There are no fees, no spreads, no taxes and no
withholding, and several series are reconstructions from newspapers, yearbooks
and company reports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.workbook import (
    SheetRows,
    WorkbookParseError,
    load_xlsx_sheets,
)

__all__ = [
    "CITATION",
    "DATASETS",
    "LICENSE_OR_TERMS_URL",
    "PARSER_VERSION",
    "RETURN_COUNTRIES",
    "JstDataset",
    "JstFile",
    "JstParseError",
    "JstVariable",
    "build_manifests",
    "download",
    "get_dataset",
    "load",
    "parse",
    "parse_bytes",
    "parse_sheets",
    "real_total_return",
]

#: Bump on any change to parsing behaviour: sheet selection, panel pivoting,
#: period labelling, unit handling or missing-value treatment.
PARSER_VERSION: Final = "macrohistory/1.0.0"

LICENSE_OR_TERMS_URL: Final = "https://creativecommons.org/licenses/by-nc-sa/4.0/"

CITATION: Final = (
    "Jordà, Òscar, Katharina Knoll, Dmitry Kuvshinov, Moritz Schularick and Alan "
    "M. Taylor. 2019. 'The Rate of Return on Everything, 1870-2015.' Quarterly "
    "Journal of Economics 134(3): 1225-1298. Macro series: Jordà, Schularick and "
    "Taylor. 2017. 'Macrofinancial History and the New Business Cycle Facts.' "
    "NBER Macroeconomics Annual 31. Licence CC BY-NC-SA 4.0; citation is a "
    "condition of use."
)

#: The 16 countries that carry return series in R6. Canada and Ireland are in the
#: file and in the macro half, and have no equity, bond, bill or housing returns
#: at all — a fact worth stating in code, because a reader who counts "18
#: countries" from the landing page will overstate the panel by two.
RETURN_COUNTRIES: Final = (
    "AUS",
    "BEL",
    "CHE",
    "DEU",
    "DNK",
    "ESP",
    "FIN",
    "FRA",
    "GBR",
    "ITA",
    "JPN",
    "NLD",
    "NOR",
    "PRT",
    "SWE",
    "USA",
)

_AVAILABILITY: Final = (
    "Annual observations published in an academic release, years after the fact. "
    "Release R6 was posted in 2022 and covers through 2020; the HTTP "
    "Last-Modified header of the workbook is the only upper bound this code can "
    "observe on when any row became available, and it bounds the whole file "
    "rather than any row. No observation here was available in its own year, and "
    "many were first published decades later from newspapers, statistical "
    "yearbooks and company reports."
)

_REVISION: Final = (
    "Not point-in-time. Each JST release rebuilds and revises the full history: "
    "R6 revised GDP and related series, replaced discontinued IMF interest-rate, "
    "narrow-money and broad-money sources, and added Ireland. Prior releases "
    "(R1-R5) are not served from the current download links, so this code cannot "
    "read a vintage. A sha256 here identifies the file downloaded and nothing "
    "about what any earlier release said."
)


class JstParseError(ValueError):
    """Raised when the JST workbook does not have the expected shape."""


@dataclass(frozen=True)
class JstVariable:
    """One column of the JST panel, with what it is stated to be.

    Attributes:
        column: The column name in the source sheet, verbatim.
        definition: The R6 documentation's own definition, quoted.
        source_units: Units in the file.
        units: Units of the derived table. No conversion is applied to any JST
            variable, so these are equal for every entry; the pair is kept
            because the manifest schema requires both and because a future
            variable that does need converting must not be able to hide it.
        notes: Everything a user of this column has to know before quoting a
            number from it.
    """

    column: str
    table_id: str
    definition: str
    source_units: str
    units: str
    unit_transform: str
    notes: tuple[str, ...] = ()


_LOCAL_CURRENCY: Final = (
    "NOMINAL and in LOCAL CURRENCY. Deflate with the cpi table for a real "
    "return; there is no USD-converted series in this repository."
)

_ANNUAL_DRAWDOWN: Final = (
    "ANNUAL, year-end to year-end. A drawdown computed from this series cannot "
    "see an intra-year peak or trough and is a LOWER BOUND on the realised loss. "
    "It is not comparable with a monthly drawdown, and maximum drawdown deepens "
    "mechanically with sample length, so it is not comparable across countries "
    "with unequal samples either."
)

_NOT_INVESTABLE: Final = (
    "NOT INVESTABLE. No fee, spread, tax, withholding or capacity is deducted "
    "anywhere, and much of the pre-1950 history is reconstructed from newspapers, "
    "statistical yearbooks and company reports."
)

_EQUITY_INDEX_DRIFT: Final = (
    "The index behind a country is not constant. The RORE documentation's "
    "coverage table moves between 'all share', 'broad', 'blue chip' and 'selected "
    "stocks', and between market-cap, book-cap, transaction-volume and equal "
    "weighting. France is blue chip (top-40, CAC-40 methodology) for the whole "
    "sample; Germany is blue chip 1914-1959; the UK is blue chip 1929-1963."
)

_EQUITY_CLOSURES: Final = (
    "EXCHANGE CLOSURES ARE FILLED. eq_tr_interp = 1 in the source marks Portugal "
    "1975-1977 and Spain 1937-1940. Portugal's published eq_tr is identical in "
    "1975 and 1976 and nearly identical in 1977, which is a fill and not a "
    "measurement. Japan has NO equity return for 1946-1947 ('Stock exchange "
    "closed; no data') and that hole sits in the middle of the largest loss in "
    "the panel. The Netherlands' 1945 return covers August 1944 to April 1946 "
    "and Switzerland's 1915 return covers July 1914 to July 1916."
)

_GERMAN_HYPERINFLATION: Final = (
    "GERMANY 1922-1923 IS HYPERINFLATION ARITHMETIC. eq_tr for 1923 is 2.6e9 "
    "against consumer-price inflation of 1.06e9; the ratio of two astronomical "
    "annual numbers is not a return anyone realised inside that year. The 1948 "
    "currency reform then appears as a -88% nominal equity return. Bond returns "
    "have no data for 1923-1925."
)

_CANADA_IRELAND: Final = (
    "Canada and Ireland carry NO return data in R6. They are in the file for "
    "their macro series only, so the returns panel is 16 countries, not the 18 "
    "the landing page advertises."
)

_VARIABLES: Final = (
    JstVariable(
        column="eq_tr",
        table_id="equity_total_return",
        definition="Equity total return, nominal. r[t] = ((p[t] + d[t]) / p[t-1]) - 1",
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        notes=(
            _LOCAL_CURRENCY,
            _EQUITY_CLOSURES,
            _GERMAN_HYPERINFLATION,
            _EQUITY_INDEX_DRIFT,
            _NOT_INVESTABLE,
        ),
    ),
    JstVariable(
        column="eq_capgain",
        table_id="equity_capital_gain",
        definition="Equity capital gain, nominal. cg[t] = (p[t] / p[t-1]) - 1",
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        notes=(
            _LOCAL_CURRENCY,
            "This is the PRICE return. eq_tr minus eq_capgain is the dividend "
            "contribution; do not use this series where a total return is meant.",
            _EQUITY_CLOSURES,
            _NOT_INVESTABLE,
        ),
    ),
    JstVariable(
        column="eq_dp",
        table_id="equity_dividend_yield",
        definition="Equity dividend yield. dp[t] = dividend[t] / p[t]",
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        notes=(
            "A YIELD, not a return: the denominator is the end-of-period price. "
            "The source publishes eq_div_rtn separately for the dividend return "
            "on the lagged price; this repository has not landed it.",
            "eq_dp_interp = 1 in the source marks dividends interpolated or "
            "ASSUMED ZERO to cover an exchange closure.",
        ),
    ),
    JstVariable(
        column="bond_tr",
        table_id="bond_total_return",
        definition=(
            "Government bond total return, nominal. "
            "r[t] = ((p[t] + coupon[t]) / p[t-1]) - 1"
        ),
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        notes=(
            _LOCAL_CURRENCY,
            "Long-term central government bonds listed and traded on the LOCAL "
            "exchange, targeting roughly 10-year maturity. Before WW2 several "
            "countries are represented by perpetuals (the British consol, the "
            "French rente), whose duration is nothing like ten years.",
            "Germany has no bond return for the 1923-1925 hyperinflation period.",
            _NOT_INVESTABLE,
        ),
    ),
    JstVariable(
        column="bill_rate",
        table_id="bill_rate",
        definition="Bill rate, nominal. r[t] = coupon[t] / p[t-1]",
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        notes=(
            _LOCAL_CURRENCY,
            "OFTEN NOT A BILL. The documentation states that 'much of our bill "
            "rate data before the 1960s actually consist of deposit rates', with "
            "money-market and deposit rates substituted wherever Treasury bill "
            "data were unavailable. It is a cash proxy, not a risk-free rate with "
            "a stated instrument.",
        ),
    ),
    JstVariable(
        column="housing_tr",
        table_id="housing_total_return",
        definition=(
            "Housing total return, nominal. r[t] = ((p[t] + d[t]) / p[t-1]) - 1"
        ),
        source_units="decimal",
        units="decimal",
        unit_transform="identity",
        notes=(
            _LOCAL_CURRENCY,
            "A MODELLED aggregate, not a traded return. Capital gains come from "
            "national house price indices and the income leg from a benchmark net "
            "rent-price ratio in 2012-2014 extrapolated backwards by rent and "
            "price indices. It includes imputed rents on owner-occupied housing, "
            "deducts an estimate of running costs and depreciation, and carries "
            "no transaction cost, vacancy, leverage or illiquidity.",
            "rent_ipolated = 1 marks 29 observations whose rental yield was "
            "interpolated, typically under wartime rent controls; "
            "housing_capgain_ipolated = 1 marks 5 more.",
            _NOT_INVESTABLE,
        ),
    ),
    JstVariable(
        column="cpi",
        table_id="consumer_prices",
        definition="Consumer prices (index, 1990 = 100)",
        source_units="index_1990_eq_100",
        units="index_1990_eq_100",
        unit_transform="identity",
        notes=(
            "An INDEX LEVEL, not an inflation rate. Rebased so that 1990 = 100 in "
            "every country, so levels are not comparable across countries and "
            "only ratios within a country mean anything.",
            "Spliced from national sources across currency reforms, occupations "
            "and hyperinflations. German 1923 and Japanese 1946-1947 year-on-year "
            "changes are 1.06e9 and +125%; an annual index cannot represent what "
            "prices did inside those years.",
            "Ireland has no CPI before 1922.",
        ),
    ),
)

_ANNUAL_TABLE_NOTE: Final = (
    "Columns are ISO-3 country codes. A missing cell is a country-year the source "
    "does not publish and is None, never zero."
)


@dataclass(frozen=True)
class JstDataset:
    """One JST release, with its download URL and its policies."""

    dataset_id: str
    release: str
    url: str
    data_sheet: str
    variables: tuple[JstVariable, ...]
    availability_policy: str = _AVAILABILITY
    revision_policy: str = _REVISION


DATASETS: Final[dict[str, JstDataset]] = {
    dataset.dataset_id: dataset
    for dataset in (
        JstDataset(
            dataset_id="jst_macrohistory_r6",
            release="R6 (2022 release, coverage 1870-2020)",
            # The query string is the site's own cache-busting token and is part
            # of the URL the download page publishes. It has changed before and
            # will change again; when it does, re-read
            # https://www.macrohistory.net/database/ rather than guessing.
            url=(
                "https://www.macrohistory.net/app/download/9834512569/"
                "JSTdatasetR6.xlsx?t=1763503850"
            ),
            data_sheet="Sheet1",
            variables=_VARIABLES,
        ),
    )
}


def get_dataset(dataset_id: str) -> JstDataset:
    """Look up a registered release, or raise ``KeyError`` naming the choices."""
    try:
        return DATASETS[dataset_id]
    except KeyError:
        raise KeyError(
            f"unknown JST dataset {dataset_id!r}; known: {sorted(DATASETS)}"
        ) from None


@dataclass(frozen=True)
class JstFile:
    """Everything parsed out of one JST workbook.

    Attributes:
        countries: ISO-3 codes found in the file, sorted. The column order of
            every table.
        tables: One table per registered variable, in registry order.
        interpolated: ``(variable, country, year)`` for every observation the
            source flags as interpolated to cover an exchange closure.
        warnings: File-level problems, as opposed to per-table ones.
    """

    sheet_names: tuple[str, ...]
    countries: tuple[str, ...]
    tables: tuple[ParsedTable, ...]
    interpolated: tuple[tuple[str, str, str], ...]
    warnings: tuple[str, ...]

    def table(self, table_id: str) -> ParsedTable:
        for candidate in self.tables:
            if candidate.table_id == table_id:
                return candidate
        raise KeyError(
            f"no table {table_id!r}; parsed: {[t.table_id for t in self.tables]}"
        )


def download(
    cache: RawCache, dataset: JstDataset, *, force: bool = False, timeout: float = 120.0
) -> CacheEntry:
    """Fetch the workbook into ``cache``, reusing cached bytes unless forced.

    No ``User-Agent`` override. Verified on 2026-08-16: macrohistory.net serves
    the workbook to the default ``requests`` agent with HTTP 200 after one
    redirect. Note that the *documentation* PDFs on the same host answer 403 to
    some clients while the data files do not, so a 403 on a PDF is not evidence
    that the data are unavailable.
    """
    return cache.fetch(dataset.url, force=force, timeout=timeout)


def parse(cache: RawCache, entry: CacheEntry, *, dataset: JstDataset) -> JstFile:
    """Parse a cached JST workbook. Reads only from the cache."""
    return parse_bytes(cache.read(entry), dataset=dataset)


def parse_bytes(raw: bytes, *, dataset: JstDataset) -> JstFile:
    """Parse workbook bytes into one panel table per registered variable."""
    try:
        sheets = load_xlsx_sheets(raw, source=dataset.dataset_id)
    except WorkbookParseError as exc:
        raise JstParseError(str(exc)) from exc
    return parse_sheets(sheets, dataset=dataset)


def parse_sheets(sheets: Mapping[str, SheetRows], *, dataset: JstDataset) -> JstFile:
    """Build the tables from already-read sheet rows.

    Split out from :func:`parse_bytes` so that the whole pivot, missing-value and
    interpolation-flag path can be exercised offline against a small frozen slice
    of the real workbook, without committing a megabyte of raw data to Git.
    """
    sheet_names = tuple(sheets)
    if dataset.data_sheet not in sheets:
        raise JstParseError(
            f"{dataset.dataset_id}: the declared data sheet "
            f"{dataset.data_sheet!r} is not in this workbook. Sheets found: "
            f"{list(sheet_names)}. Freeze a new dataset entry against the new "
            "name rather than letting the parser pick a different sheet."
        )

    rows = sheets[dataset.data_sheet]
    if not rows:
        raise JstParseError(f"{dataset.dataset_id}: sheet {dataset.data_sheet!r} is empty")

    header = [("" if cell is None else str(cell)).strip() for cell in rows[0]]
    position = {name: index for index, name in enumerate(header) if name}
    for required in ("year", "iso", *(variable.column for variable in dataset.variables)):
        if required not in position:
            raise JstParseError(
                f"{dataset.dataset_id}: column {required!r} is not in the sheet "
                f"header {header}. The release layout has changed; register the "
                "new release rather than renaming a column here."
            )

    warnings: list[str] = []
    panel: dict[str, dict[tuple[str, str], float | None]] = {
        variable.column: {} for variable in dataset.variables
    }
    interpolated: list[tuple[str, str, str]] = []
    years: set[int] = set()
    countries: set[str] = set()
    interp_flags = {
        "eq_tr": "eq_tr_interp",
        "eq_capgain": "eq_capgain_interp",
        "eq_dp": "eq_dp_interp",
        "housing_tr": "housing_capgain_ipolated",
    }
    skipped = 0

    for row in rows[1:]:
        raw_year = row[position["year"]] if position["year"] < len(row) else None
        raw_iso = row[position["iso"]] if position["iso"] < len(row) else None
        year = _as_year(raw_year)
        iso = str(raw_iso).strip() if raw_iso is not None else ""
        if year is None or not iso:
            skipped += 1
            continue
        years.add(year)
        countries.add(iso)
        key = (str(year), iso)
        for variable in dataset.variables:
            index = position[variable.column]
            panel[variable.column][key] = (
                _as_number(row[index]) if index < len(row) else None
            )
            flag = interp_flags.get(variable.column)
            if flag is not None and flag in position:
                flag_index = position[flag]
                flag_value = _as_number(row[flag_index]) if flag_index < len(row) else None
                if flag_value == 1.0:
                    interpolated.append((variable.column, iso, str(year)))

    if skipped:
        warnings.append(
            f"{skipped} rows had no parseable year or ISO code and were skipped."
        )
    if not years or not countries:
        raise JstParseError(f"{dataset.dataset_id}: no country-year rows were found")

    ordered_countries = tuple(sorted(countries))
    missing_returns = tuple(
        iso for iso in ordered_countries if iso not in RETURN_COUNTRIES
    )
    if missing_returns:
        warnings.append(
            f"{list(missing_returns)} appear in the file but carry no equity, "
            "bond, bill or housing return series in this release. " + _CANADA_IRELAND
        )
    if set(RETURN_COUNTRIES) - countries:
        warnings.append(
            "expected return countries are absent from the file: "
            f"{sorted(set(RETURN_COUNTRIES) - countries)}. The release composition "
            "has changed."
        )
    if interpolated:
        warnings.append(
            "the source flags these observations as interpolated to cover an "
            f"exchange closure: {sorted(interpolated)}. They are kept in the "
            "tables, because dropping them silently would be worse, and they are "
            "listed here so that a result which depends on them can be identified."
        )

    ordered_years = tuple(str(year) for year in sorted(years))
    tables = tuple(
        _build_table(variable, ordered_years, ordered_countries, panel[variable.column])
        for variable in dataset.variables
    )
    return JstFile(
        sheet_names=sheet_names,
        countries=ordered_countries,
        tables=tables,
        interpolated=tuple(sorted(interpolated)),
        warnings=tuple(warnings),
    )


def _build_table(
    variable: JstVariable,
    years: tuple[str, ...],
    countries: tuple[str, ...],
    cells: dict[tuple[str, str], float | None],
) -> ParsedTable:
    values = tuple(
        tuple(cells.get((year, iso)) for iso in countries) for year in years
    )
    present = {
        iso
        for index, iso in enumerate(countries)
        if any(row[index] is not None for row in values)
    }
    empty = tuple(iso for iso in countries if iso not in present)
    missing = sum(1 for row in values for value in row if value is None)
    warnings = [
        f"definition, verbatim from the R6 documentation: {variable.definition}",
        _ANNUAL_TABLE_NOTE,
        _ANNUAL_DRAWDOWN,
        f"{missing} of {len(values) * len(countries)} country-year cells are "
        "missing and are None, not zero.",
        *variable.notes,
    ]
    if empty:
        warnings.append(
            f"these countries carry no observation of this variable at all: "
            f"{list(empty)}."
        )
    return ParsedTable(
        table_id=variable.table_id,
        banner=(
            "Jorda-Schularick-Taylor Macrohistory Database, column "
            f"{variable.column!r}: {variable.definition}"
        ),
        columns=countries,
        periods=years,
        values=values,
        frequency="annual",
        source_units=variable.source_units,
        units=variable.units,
        unit_transform=variable.unit_transform,
        warnings=tuple(warnings),
    )


def _as_year(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        year = int(value)
        return year if 1500 <= year <= 2200 else None
    text = str(value).strip()
    if not text.isdigit():
        return None
    year = int(text)
    return year if 1500 <= year <= 2200 else None


def _as_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        number = float(value)
        return None if number != number else number
    text = str(value).strip()
    if text in {"", "NA", "na", "NaN", "nan", "."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load(
    cache: RawCache, dataset: JstDataset, *, force: bool = False
) -> tuple[CacheEntry, JstFile, tuple[DatasetManifest, ...]]:
    """Download if needed, parse, and build one manifest per table."""
    entry = download(cache, dataset, force=force)
    parsed = parse(cache, entry, dataset=dataset)
    return (entry, parsed, build_manifests(dataset, entry, parsed))


def build_manifests(
    dataset: JstDataset, entry: CacheEntry, parsed: JstFile
) -> tuple[DatasetManifest, ...]:
    """Build one manifest per derived table.

    The sheet actually read and the release are recorded as warnings. The
    manifest schema has no field for either and adding one would invalidate every
    manifest already committed under schema version 1, so they are pinned where a
    reader cannot miss them.
    """
    return tuple(
        manifest_from_table(
            dataset_id=f"{dataset.dataset_id}_{table.table_id}_annual",
            entry=entry,
            table=table,
            parser_version=PARSER_VERSION,
            availability_policy=dataset.availability_policy,
            revision_policy=dataset.revision_policy,
            license_or_terms_url=LICENSE_OR_TERMS_URL,
            extra_warnings=(
                f"RELEASE PINNED: {dataset.release}. "
                f"SHEET PINNED: {dataset.data_sheet!r}, of sheets "
                f"{list(parsed.sheet_names)}.",
                f"required citation: {CITATION}",
                f"countries, in column order: {list(parsed.countries)}",
                *parsed.warnings,
            ),
        )
        for table in parsed.tables
    )


def real_total_return(
    nominal: Sequence[float | None], price_index: Sequence[float | None]
) -> tuple[float | None, ...]:
    """Deflate a nominal return series by a price index, period by period.

    ``real[t] = (1 + nominal[t]) * index[t-1] / index[t] - 1``.

    Both sequences must be the same length and aligned on the same periods; the
    first element is always ``None`` because a real return needs two consecutive
    index observations. Any period whose nominal return or either index level is
    missing, or whose lagged index is not strictly positive, is ``None`` — the
    hole is propagated rather than bridged, because bridging a gap in this data
    would silently assume zero real return across exactly the episodes (Japan
    1946-47, Germany 1923) where that assumption is worst.

    This is a unit transformation, not an analysis. It lives here so that the
    deflation is written down once, next to the statement that every JST return
    is nominal, instead of being re-derived at each call site.
    """
    if len(nominal) != len(price_index):
        raise ValueError(
            f"nominal has {len(nominal)} observations and price_index has "
            f"{len(price_index)}; they must be aligned on the same periods"
        )
    out: list[float | None] = [None] * len(nominal)
    for index in range(1, len(nominal)):
        value = nominal[index]
        previous_level = price_index[index - 1]
        level = price_index[index]
        if value is None or previous_level is None or level is None:
            continue
        if previous_level <= 0.0 or level <= 0.0:
            continue
        out[index] = (1.0 + value) * previous_level / level - 1.0
    return tuple(out)
