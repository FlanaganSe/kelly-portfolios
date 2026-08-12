"""FRED CSV reader, with a typed registry that blocks silent series substitution.

FRED is a good source for cash rates and macro series and a bad source for
point-in-time research if used naively. Two properties drive everything here.

**FRED serves one vintage: the current one.** A series that is revised is revised
in place. Downloading ``CPIAUCSL`` today gives today's estimate of 1970, not the
number anyone saw in 1970. The vintages live in ALFRED, which this module does
not read, so every manifest written here states in ``revision_policy`` that the
data are not point-in-time. A sha256 pins which file was used; it cannot make a
revised series into a historical one.

**Cash rates are not fungible.** ``TB3MS``, ``DGS3MO`` and ``DFF`` are routinely
treated as "the risk-free rate" and they are three different things: a monthly
average of secondary-market three-month bill discount rates, a daily constant-
maturity three-month yield interpolated from the Treasury yield curve, and a
daily overnight effective federal funds rate. They differ in maturity, in
frequency, in construction and in day-count basis, and swapping one for another
moves a Sharpe ratio. Choosing whichever one improves a result is a search over
data definitions, and it is not recorded anywhere unless something makes it
explicit.

So this module refuses to let a caller ask for "the cash rate". A series is
fetched by id from :data:`SERIES`, and an experiment that wants a cash rate
declares a :class:`CashRateRequirement` — maturity, frequency, construction — and
gets the unique registered series that satisfies it, or an exception. Two series
can also be compared directly with :func:`check_interchangeable`, which returns
the reasons they are not.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import Frequency, ParsedTable

__all__ = [
    "CSV_ENDPOINT",
    "LICENSE_OR_TERMS_URL",
    "PARSER_VERSION",
    "SERIES",
    "CashRateRequirement",
    "Construction",
    "FredParseError",
    "FredSeries",
    "SeriesNotInterchangeableError",
    "UnknownSeriesError",
    "build_manifest",
    "check_interchangeable",
    "download",
    "get_series",
    "parse",
    "require_interchangeable",
    "resolve_cash_rate",
    "series_url",
]

#: Bump on any change to parsing behaviour.
PARSER_VERSION: Final = "fred/1.0.0"

CSV_ENDPOINT: Final = "https://fred.stlouisfed.org/graph/fredgraph.csv"
LICENSE_OR_TERMS_URL: Final = "https://fred.stlouisfed.org/legal/"

#: FRED writes missing observations as a bare full stop.
FRED_MISSING_TOKEN: Final = "."

Construction = Literal[
    "secondary_market_discount_rate",
    "constant_maturity_yield",
    "overnight_effective_rate",
    "market_yield_at_constant_maturity",
    "index_level",
]

_REVISION_NOT_POINT_IN_TIME: Final = (
    "Not point-in-time. FRED serves only the current vintage of a series; "
    "revisions overwrite history in place and this endpoint exposes no vintage. "
    "Historical vintages exist in ALFRED (https://alfred.stlouisfed.org) and are "
    "not read by this module. A sha256 here identifies the file downloaded, not "
    "what the series looked like on any earlier date."
)


class UnknownSeriesError(KeyError):
    """Raised when a series id is not in the registry.

    Unregistered ids are refused rather than fetched, because the point of the
    registry is that every series in use carries a written definition, frequency,
    construction and revision behaviour.
    """


class SeriesNotInterchangeableError(ValueError):
    """Raised when two series are used as if they were the same measurement."""


class FredParseError(ValueError):
    """Raised when a FRED CSV does not have the expected shape."""


@dataclass(frozen=True)
class FredSeries:
    """One FRED series and everything needed to use it without confusing it.

    Attributes:
        definition: What the number measures, in the source's own terms.
        maturity_months: Instrument maturity, ``None`` for overnight or non-rate
            series. The first thing that differs between "risk-free rates".
        construction: How the rate is produced. A discount-basis secondary-market
            rate and a constant-maturity interpolated yield are not the same
            number even at the same maturity.
        day_count: The basis on which the quoted rate is computed, which governs
            how it may be converted to a period return.
        release_timing: When an observation for a period becomes available. This,
            not the download time, bounds look-ahead.
        revision_behavior: Whether published values change afterwards.
    """

    series_id: str
    title: str
    definition: str
    frequency: Frequency
    source_units: str
    units: str
    unit_transform: str
    transformation: str
    maturity_months: float | None
    construction: Construction
    day_count: str
    seasonal_adjustment: str
    release_timing: str
    revision_behavior: str

    @property
    def url(self) -> str:
        return series_url(self.series_id)


def series_url(series_id: str) -> str:
    return f"{CSV_ENDPOINT}?id={series_id}"


_PERCENT_TO_DECIMAL: Final = "value / 100"

SERIES: Final[dict[str, FredSeries]] = {
    series.series_id: series
    for series in (
        FredSeries(
            series_id="TB3MS",
            title="3-Month Treasury Bill Secondary Market Rate, Discount Basis",
            definition=(
                "Monthly average of the secondary-market three-month Treasury "
                "bill rate quoted on a discount basis. The conventional monthly "
                "cash proxy in the US asset-pricing literature."
            ),
            frequency="monthly",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=3.0,
            construction="secondary_market_discount_rate",
            day_count="discount basis, actual/360",
            seasonal_adjustment="not seasonally adjusted",
            release_timing=(
                "Monthly average published in the first business days of the "
                "following month; the value for month M is not available during "
                "month M."
            ),
            revision_behavior=(
                "Underlying daily quotes are essentially final, but the monthly "
                "average can change if a daily quote is corrected."
            ),
        ),
        FredSeries(
            series_id="DTB3",
            title="3-Month Treasury Bill Secondary Market Rate, Discount Basis (Daily)",
            definition=(
                "Daily secondary-market three-month Treasury bill rate on a "
                "discount basis. The daily series TB3MS averages."
            ),
            frequency="daily",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=3.0,
            construction="secondary_market_discount_rate",
            day_count="discount basis, actual/360",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Next business day, on the Federal Reserve H.15 schedule.",
            revision_behavior="Rarely revised; corrections are possible.",
        ),
        FredSeries(
            series_id="DGS3MO",
            title="Market Yield on U.S. Treasury Securities at 3-Month Constant Maturity",
            definition=(
                "Daily constant-maturity three-month Treasury yield, interpolated "
                "by the Treasury from the daily yield curve. Same nominal "
                "maturity as TB3MS but a different construction, a different "
                "basis and a different frequency, so the two are not "
                "substitutable even after averaging."
            ),
            frequency="daily",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=3.0,
            construction="constant_maturity_yield",
            day_count="bond-equivalent, investment basis",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Next business day, on the Federal Reserve H.15 schedule.",
            revision_behavior="Rarely revised; corrections are possible.",
        ),
        FredSeries(
            series_id="DFF",
            title="Federal Funds Effective Rate (Daily)",
            definition=(
                "Daily volume-weighted median of overnight federal funds "
                "transactions between depository institutions. An overnight "
                "unsecured interbank rate, not a Treasury yield: it carries bank "
                "credit and settlement characteristics that a bill does not, and "
                "its maturity is one day, not three months."
            ),
            frequency="daily",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=None,
            construction="overnight_effective_rate",
            day_count="actual/360, overnight",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Next business day from the New York Fed.",
            revision_behavior=(
                "The effective rate is occasionally revised when reported "
                "transaction data are corrected."
            ),
        ),
        FredSeries(
            series_id="GS10",
            title="Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity",
            definition=(
                "Monthly average of the daily ten-year constant-maturity "
                "Treasury yield. A duration exposure, never a cash rate."
            ),
            frequency="monthly",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=120.0,
            construction="market_yield_at_constant_maturity",
            day_count="bond-equivalent, investment basis",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Monthly average published early in the following month.",
            revision_behavior="Rarely revised; corrections are possible.",
        ),
        FredSeries(
            series_id="CPIAUCSL",
            title="Consumer Price Index for All Urban Consumers: All Items (SA)",
            definition=(
                "Seasonally adjusted CPI-U index level. Included as the canonical "
                "example of a revised series: seasonal factors are re-estimated "
                "annually and rewrite published history."
            ),
            frequency="monthly",
            source_units="index_1982_1984_eq_100",
            units="index_1982_1984_eq_100",
            unit_transform="identity",
            transformation="none (index level, as published)",
            maturity_months=None,
            construction="index_level",
            day_count="not applicable",
            seasonal_adjustment="seasonally adjusted",
            release_timing=(
                "Roughly mid-month for the prior month, on the BLS schedule; the "
                "publication lag must be respected in any predictability test."
            ),
            revision_behavior=(
                "Seasonally adjusted history is revised every year when seasonal "
                "factors are re-estimated. Values downloaded today differ from "
                "values downloaded last year for the same months."
            ),
        ),
    )
}


def get_series(series_id: str) -> FredSeries:
    """Look up a registered series, or raise :class:`UnknownSeriesError`."""
    try:
        return SERIES[series_id]
    except KeyError:
        raise UnknownSeriesError(
            f"{series_id!r} is not registered. Add it to fred.SERIES with its "
            "definition, frequency, construction, release timing and revision "
            f"behaviour before using it. Registered: {sorted(SERIES)}"
        ) from None


def check_interchangeable(left_id: str, right_id: str) -> tuple[str, ...]:
    """Return the reasons two series are not the same measurement.

    An empty tuple means the registry records no difference, which is weaker than
    "they are the same series" and should still not be read as permission to swap
    them mid-experiment.
    """
    left = get_series(left_id)
    right = get_series(right_id)
    differences: list[str] = []
    if left.maturity_months != right.maturity_months:
        differences.append(
            f"maturity differs: {left.series_id}={left.maturity_months} months, "
            f"{right.series_id}={right.maturity_months} months"
        )
    if left.frequency != right.frequency:
        differences.append(
            f"frequency differs: {left.series_id}={left.frequency}, "
            f"{right.series_id}={right.frequency}"
        )
    if left.construction != right.construction:
        differences.append(
            f"construction differs: {left.series_id}={left.construction}, "
            f"{right.series_id}={right.construction}"
        )
    if left.day_count != right.day_count:
        differences.append(
            f"day-count basis differs: {left.series_id}={left.day_count!r}, "
            f"{right.series_id}={right.day_count!r}"
        )
    if left.seasonal_adjustment != right.seasonal_adjustment:
        differences.append(
            f"seasonal adjustment differs: {left.series_id}="
            f"{left.seasonal_adjustment}, {right.series_id}="
            f"{right.seasonal_adjustment}"
        )
    return tuple(differences)


def require_interchangeable(left_id: str, right_id: str) -> None:
    """Raise unless the registry records no difference between two series."""
    differences = check_interchangeable(left_id, right_id)
    if differences:
        raise SeriesNotInterchangeableError(
            f"{left_id} and {right_id} are not interchangeable: "
            + "; ".join(differences)
            + ". Pick one on economic grounds, declare it in the experiment "
            "specification, and do not change it after seeing a result."
        )


@dataclass(frozen=True)
class CashRateRequirement:
    """What an experiment says it needs from a cash rate, before it picks one.

    Written into the experiment specification and resolved by
    :func:`resolve_cash_rate`. Declaring the measurement first, and letting the
    registry find the series, is what stops "which cash series improves the
    Sharpe ratio" from becoming an unrecorded search.
    """

    maturity_months: float | None
    frequency: Frequency
    construction: Construction


def resolve_cash_rate(requirement: CashRateRequirement) -> FredSeries:
    """Return the one registered series matching ``requirement``, or raise.

    Raises:
        SeriesNotInterchangeableError: no registered series matches, or more than
            one does. Both are refusals: an ambiguous match means the requirement
            does not pin down the measurement.
    """
    matches = [
        series
        for series in SERIES.values()
        if series.maturity_months == requirement.maturity_months
        and series.frequency == requirement.frequency
        and series.construction == requirement.construction
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SeriesNotInterchangeableError(
            f"no registered FRED series matches {requirement}. Registered cash "
            "candidates: "
            + ", ".join(
                f"{s.series_id}(maturity={s.maturity_months}, freq={s.frequency}, "
                f"construction={s.construction})"
                for s in SERIES.values()
            )
        )
    raise SeriesNotInterchangeableError(
        f"{requirement} matches {[s.series_id for s in matches]}; the "
        "requirement does not identify a single measurement."
    )


def download(
    cache: RawCache, series_id: str, *, force: bool = False, timeout: float = 60.0
) -> CacheEntry:
    """Fetch a registered series' CSV into ``cache``.

    Deliberately sends no ``User-Agent`` override. Verified on 2026-08-12: the
    edge in front of ``fred.stlouisfed.org`` black-holes requests carrying a
    browser-shaped agent string, or an unfamiliar one, by accepting the
    connection and never responding — a read timeout rather than a status code.
    The default ``requests`` agent is served normally. Do not "fix" a timeout
    here by adding a browser user agent; that is what causes it.
    """
    series = get_series(series_id)
    return cache.fetch(series.url, force=force, timeout=timeout)


def parse(cache: RawCache, entry: CacheEntry, series_id: str) -> ParsedTable:
    """Parse a cached FRED CSV into a single-column table.

    Reads only from the cache, so parsing without a stored raw artifact raises
    ``RawArtifactMissing``.
    """
    series = get_series(series_id)
    text = cache.read(entry).decode("utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise FredParseError(f"{series_id}: empty CSV")

    warnings: list[str] = []
    header = [cell.strip() for cell in lines[0].split(",")]
    if len(header) != 2:
        raise FredParseError(
            f"{series_id}: expected a two-column CSV, got header {header!r}. "
            "The endpoint's shape has changed; do not work around it."
        )
    if header[0] not in {"observation_date", "DATE"}:
        warnings.append(
            f"date column is named {header[0]!r}, not 'observation_date' or "
            "'DATE'; the endpoint's header convention has changed."
        )
    if header[1] != series_id:
        warnings.append(
            f"value column is named {header[1]!r} but {series_id} was requested. "
            "FRED may have applied a transformation or redirected the id."
        )

    periods: list[str] = []
    values: list[tuple[float | None, ...]] = []
    missing: list[str] = []
    unparsed: list[str] = []
    for line in lines[1:]:
        cells = [cell.strip() for cell in line.split(",")]
        if len(cells) != 2:
            unparsed.append(line)
            continue
        period, raw_value = cells
        if raw_value == FRED_MISSING_TOKEN or raw_value == "":
            missing.append(period)
            periods.append(period)
            values.append((None,))
            continue
        try:
            number = float(raw_value)
        except ValueError:
            unparsed.append(line)
            periods.append(period)
            values.append((None,))
            continue
        scale = 0.01 if series.unit_transform == _PERCENT_TO_DECIMAL else 1.0
        periods.append(period)
        values.append((number * scale,))

    if missing:
        warnings.append(
            f"{len(missing)} observations were the FRED missing token "
            f"{FRED_MISSING_TOKEN!r} and became missing values, not zeros: "
            f"{missing[:6]}"
        )
    if unparsed:
        warnings.append(
            f"{len(unparsed)} lines were not a date/value pair: {unparsed[:4]}"
        )
    if series.frequency == "monthly" and any(
        not period.endswith("-01") for period in periods
    ):
        offenders = [p for p in periods if not p.endswith("-01")][:4]
        warnings.append(
            "the registry declares this series monthly but some observation "
            f"dates are not the first of a month: {offenders}. Check the "
            "registry entry before using the frequency for anything."
        )
    if series.unit_transform == _PERCENT_TO_DECIMAL:
        warnings.append(
            "values are an annualised rate expressed as a decimal after dividing "
            f"the published percent by 100, on a {series.day_count} basis. This "
            "is a rate, not a period return: converting it to a monthly or daily "
            "return requires an explicit, recorded compounding or day-count "
            "assumption that this parser does not make."
        )
    warnings.append(f"series definition: {series.definition}")
    warnings.append(f"release timing: {series.release_timing}")
    warnings.append(f"revision behaviour: {series.revision_behavior}")

    return ParsedTable(
        table_id=series_id.lower(),
        banner=series.title,
        columns=(series_id,),
        periods=tuple(periods),
        values=tuple(values),
        frequency=series.frequency,
        source_units=series.source_units,
        units=series.units,
        unit_transform=series.unit_transform,
        warnings=tuple(warnings),
    )


def build_manifest(
    entry: CacheEntry,
    table: ParsedTable,
    series_id: str,
    *,
    extra_warnings: Sequence[str] = (),
) -> DatasetManifest:
    """Build the manifest for one FRED series."""
    series = get_series(series_id)
    return manifest_from_table(
        dataset_id=f"fred_{series_id.lower()}",
        entry=entry,
        table=table,
        parser_version=PARSER_VERSION,
        availability_policy=(
            f"{series.release_timing} The retrieval timestamp in this manifest "
            "is when the file was downloaded, which is an upper bound on "
            "availability for the last observation and says nothing about when "
            "earlier observations became available."
        ),
        revision_policy=f"{series.revision_behavior} {_REVISION_NOT_POINT_IN_TIME}",
        license_or_terms_url=LICENSE_OR_TERMS_URL,
        extra_warnings=(
            f"transformation applied by the source: {series.transformation}",
            f"seasonal adjustment: {series.seasonal_adjustment}",
            f"maturity: {series.maturity_months} months "
            f"(construction: {series.construction}). TB3MS, DGS3MO and DFF are "
            "not interchangeable; see fred.check_interchangeable.",
            *extra_warnings,
        ),
    )
