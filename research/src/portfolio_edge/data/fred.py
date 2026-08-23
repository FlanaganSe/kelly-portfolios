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
    "QuoteConvention",
    "SeriesNotInterchangeableError",
    "UnknownSeriesError",
    "build_manifest",
    "check_interchangeable",
    "download",
    "foreign_currency_return",
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

#: Which way round an exchange rate is quoted. There is no convention that holds
#: across the H.10 release — ``DEXJPUS`` is yen per dollar and ``DEXUSUK`` is
#: dollars per pound — and a single inverted series flips the sign of a currency
#: result without changing anything a reader would notice. So the direction is a
#: typed field on the series rather than a comment, and
#: :func:`foreign_currency_return` is the only supported way to turn a level into
#: a return.
QuoteConvention = Literal["foreign_per_usd", "usd_per_foreign"]

Construction = Literal[
    "secondary_market_discount_rate",
    "constant_maturity_yield",
    "overnight_effective_rate",
    "market_yield_at_constant_maturity",
    "index_level",
    "exchange_reference_price",
    "noon_buying_rate",
    "trade_weighted_index",
    "interbank_offered_rate",
    "real_yield_at_constant_maturity",
    "breakeven_inflation_spread",
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
        currency: The currency the measurement belongs to, ISO 4217. Defaults to
            ``USD`` because every series registered before 2026-08 was a US one.
            Foreign interest rates entered the registry with the currency
            question, and without this field a three-month euro-area interbank
            rate and a three-month US one differ in no attribute the registry
            records — which is exactly the silent substitution the rest of this
            module exists to prevent.
        quote_convention: For an exchange rate only, which way round it is
            quoted. ``None`` for everything that is not a rate of exchange.
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
    currency: str = "USD"
    quote_convention: QuoteConvention | None = None

    @property
    def url(self) -> str:
        return series_url(self.series_id)


def series_url(series_id: str) -> str:
    return f"{CSV_ENDPOINT}?id={series_id}"


_PERCENT_TO_DECIMAL: Final = "value / 100"

_H10_AVAILABILITY: Final = (
    "H.10 noon buying rates are certified by the Federal Reserve Bank of New "
    "York for customs purposes and published the following business day. A "
    "month-end observation is the last BUSINESS day of the month, not the last "
    "calendar day, and a US holiday that is not a foreign one leaves a gap."
)

_H10_REVISION: Final = (
    "Not point-in-time. The H.10 release republishes its full history and FRED "
    "serves the current vintage only; corrections overwrite in place. Rates are "
    "rarely revised in practice."
)

_H10_NOON_RATE: Final = (
    "A NOON BUYING RATE IN NEW YORK, one quote a day for cable transfers, not a "
    "traded close and not a WM/Reuters 4pm London fix. An index or a fund prices "
    "against the 4pm London fix; the two differ by hours of trading, so a "
    "currency return computed here is close to but not identical with the one "
    "inside any product's NAV."
)

_OECD_INTERBANK_DEFINITION: Final = (
    "OECD Main Economic Indicators, three-month or ninety-day interbank offered "
    "rate, monthly, as redistributed by FRED. Registered because the cost of "
    "hedging a currency is the INTERBANK differential, not the Treasury-bill "
    "differential: a currency forward is priced off the money-market curve, and "
    "substituting a bill rate on one side of the difference imports that "
    "country's bill-to-interbank spread into the answer. Every rate in this "
    "family is the same measurement in a different currency, which is why they "
    "may be differenced against IR3TIB01USM156N and against nothing else."
)

_OECD_INTERBANK_AVAILABILITY: Final = (
    "A monthly average of daily fixings, published by the OECD with a lag of a "
    "month or more. The value for month M is not available during month M, and "
    "the OECD's own publication lag is longer than FRED's."
)

_OECD_INTERBANK_REVISION: Final = (
    "Not point-in-time. The OECD rebuilds the Main Economic Indicators database "
    "on each release and FRED serves the current vintage; several members of "
    "this family also END EARLY because the underlying national fixing was "
    "discontinued or the OECD stopped collecting it, so a coverage end date "
    "here is a fact about the statistical programme rather than about the "
    "market."
)


#: How each quote convention reads in prose, so the direction appears in the definition
#: text a reader sees and not only in a typed field they might not look at.
_DIRECTION_PROSE: Final[dict[str, str]] = {
    "foreign_per_usd": "FOREIGN CURRENCY PER US DOLLAR",
    "usd_per_foreign": "US DOLLARS PER UNIT OF FOREIGN CURRENCY",
}


def _spot_rate(
    series_id: str,
    *,
    title: str,
    currency: str,
    quote_convention: QuoteConvention,
    coverage: str,
    notes: str = "",
) -> FredSeries:
    """One H.10 bilateral spot rate.

    A factory rather than twenty-six literals because these are genuinely one
    measurement repeated in different currencies, and the two things that vary
    between them and can silently corrupt a result — the quote direction and the
    coverage window — are the two arguments the caller must supply.
    """
    return FredSeries(
        series_id=series_id,
        title=title,
        definition=(
            f"{title}. Federal Reserve H.10, noon buying rate in New York City "
            f"for cable transfers. {coverage} {_H10_NOON_RATE} "
            f"QUOTED AS {_DIRECTION_PROSE[quote_convention]}"
            f" — the H.10 has no single convention and this family contains both. "
            f"{notes}"
        ).strip(),
        frequency="daily",
        source_units=(
            f"{currency.lower()}_per_usd"
            if quote_convention == "foreign_per_usd"
            else f"usd_per_{currency.lower()}"
        ),
        units=(
            f"{currency.lower()}_per_usd"
            if quote_convention == "foreign_per_usd"
            else f"usd_per_{currency.lower()}"
        ),
        unit_transform="identity",
        transformation="none (rate of exchange, as published)",
        maturity_months=None,
        construction="noon_buying_rate",
        day_count="not applicable (a rate of exchange, not an interest rate)",
        seasonal_adjustment="not seasonally adjusted",
        release_timing=_H10_AVAILABILITY,
        revision_behavior=_H10_REVISION,
        currency=currency,
        quote_convention=quote_convention,
    )


def _oecd_interbank_rate(
    series_id: str, *, country: str, currency: str, coverage: str
) -> FredSeries:
    """One country's three-month interbank offered rate, monthly."""
    return FredSeries(
        series_id=series_id,
        title=(
            "Interest Rates: 3-Month or 90-Day Rates and Yields: Interbank "
            f"Rates: Total for {country}"
        ),
        definition=f"{_OECD_INTERBANK_DEFINITION} Measured 2026-08-22: {coverage}",
        frequency="monthly",
        source_units="percent_per_year",
        units="decimal_per_year",
        unit_transform=_PERCENT_TO_DECIMAL,
        transformation="none (level, as published)",
        maturity_months=3.0,
        construction="interbank_offered_rate",
        day_count="money-market basis, which is actual/360 in every currency "
        "here except GBP, where it is actual/365",
        seasonal_adjustment="not seasonally adjusted",
        release_timing=_OECD_INTERBANK_AVAILABILITY,
        revision_behavior=_OECD_INTERBANK_REVISION,
        currency=currency,
    )


def foreign_currency_return(
    series: FredSeries, previous_level: float, current_level: float
) -> float:
    """The return, to a US dollar investor, of holding one unit of the foreign currency.

    The one function in this module that reads a quote convention, and the only
    supported way to turn two exchange-rate levels into a return. Written here
    rather than at each call site because the H.10 quotes some pairs each way
    round, and an inverted ratio changes the sign of every currency result while
    changing nothing a reader would notice.
    """
    if series.quote_convention is None:
        raise ValueError(
            f"{series.series_id} is not an exchange rate; it has no quote convention"
        )
    if previous_level <= 0.0 or current_level <= 0.0:
        raise ValueError(
            f"{series.series_id}: an exchange rate of {previous_level} -> "
            f"{current_level} is not a rate; check for a missing observation"
        )
    if series.quote_convention == "foreign_per_usd":
        return previous_level / current_level - 1.0
    return current_level / previous_level - 1.0


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
            series_id="FII10",
            title=(
                "Market Yield on U.S. Treasury Securities at 10-Year Constant "
                "Maturity, Quoted on an Investment Basis, Inflation-Indexed"
            ),
            definition=(
                "Monthly average of the daily ten-year REAL constant-maturity "
                "Treasury yield. The Treasury's own definition, from "
                "https://home.treasury.gov/resource-center/data-chart-center/"
                "interest-rates/TextView?type=daily_treasury_real_yield_curve "
                "read 2026-08-17: 'Par real yields on Treasury Inflation "
                "Protected Securities (TIPS) at \"constant maturity\" are "
                "interpolated by the U.S. Treasury from Treasury's daily par "
                "real yield curve. These par real yields are calculated from "
                "indicative secondary market quotations obtained by the Federal "
                "Reserve Bank of New York.' NOT interchangeable with GS10: that "
                "is a nominal yield and this is a real one, and the difference "
                "between them is a breakeven inflation rate, not a spread. "
                "Measured 2026-08-17: 283 monthly observations, 2003-01 to "
                "2026-07. THE SERIES CARRIES A DOCUMENTED METHODOLOGY BREAK the "
                "same page states: 'Starting 12/01/2008, the TIPS yield curve "
                "began using the most recently auctioned TIPS as knot points "
                "rather than all securities. The reported values from September "
                "2 to November 28, 2008, utilize the old methodology and remain "
                "official.' A study that splits this series at a date near 2008 "
                "is splitting on a construction change as well as on an era."
            ),
            frequency="monthly",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=120.0,
            construction="real_yield_at_constant_maturity",
            day_count="bond-equivalent, investment basis, on an inflation-indexed principal",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Monthly average published early in the following month.",
            revision_behavior="Rarely revised; corrections are possible.",
        ),
        FredSeries(
            series_id="T10YIE",
            title="10-Year Breakeven Inflation Rate",
            definition=(
                "The daily difference between the ten-year nominal and ten-year "
                "real constant-maturity Treasury yields. It is a MARKET-IMPLIED "
                "BREAKEVEN, not an inflation forecast and not an expectation: it "
                "contains an inflation risk premium and a TIPS liquidity premium "
                "of unknown and time-varying sign, so quoting it as 'expected "
                "inflation' overstates what it measures. Registered here for one "
                "purpose only -- to state what real return a TIPS holder is "
                "buying against what a nominal Treasury holder is buying on a "
                "given date -- and never as a predictor. Measured 2026-08-17: "
                "daily from 2003-01-02."
            ),
            frequency="daily",
            source_units="percent_per_year",
            units="decimal_per_year",
            unit_transform=_PERCENT_TO_DECIMAL,
            transformation="none (level, as published)",
            maturity_months=120.0,
            construction="breakeven_inflation_spread",
            day_count="not applicable (a difference of two quoted yields)",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Next business day.",
            revision_behavior=(
                "Revised whenever either input yield curve is revised, and it "
                "inherits the TIPS curve's 2008-12-01 methodology break."
            ),
        ),
        FredSeries(
            series_id="BAMLCC0A0CMTRIV",
            title="ICE BofA US Corporate Index Total Return Index Value",
            definition=(
                "TRUNCATED TO THREE YEARS AND THEREFORE USELESS FOR RESEARCH — "
                "registered so that this is not rediscovered. A genuine "
                "total-return index level for US dollar investment-grade "
                "corporate debt, coupons reinvested, minimum $250m outstanding, "
                "over one year to maturity. Measured on 2026-08-16: the CSV "
                "endpoint returns exactly 795 daily observations, 2023-08-15 to "
                "2026-08-13. The series notes state 'Starting in April 2026, "
                "this series will only include 3 years of observations. For more "
                "data, go to the source.' Thirty-six monthly returns cannot "
                "answer a diversification or rebalancing question. The notes "
                "also state 'Reproduction of this data in any form is prohibited "
                "except with the prior written permission of ICE Data Indices', "
                "so the bytes stay in the uncommitted cache and only hashes are "
                "manifested. Every sibling in the BAML family is capped "
                "identically: BAMLCC1A013YTRIV, BAMLCC2A035YTRIV, "
                "BAMLCC3A057YTRIV, BAMLCC4A0710YTRIV, BAMLCC7A01015YTRIV, "
                "BAMLCC8A015PYTRIV, BAMLHYH0A1BBTRIV, BAMLHYH0A2BTRIV, "
                "BAMLHYH0A3CMTRIV and BAMLEMCBPITRIV were each measured at 795 "
                "rows over the same dates. For long corporate-bond history use "
                "portfolio_edge.data.goyal_welch instead."
            ),
            frequency="daily",
            source_units="index_level",
            units="index_level",
            unit_transform="identity",
            transformation="none (index level, as published)",
            maturity_months=None,
            construction="index_level",
            day_count="not applicable (an index level, not a rate)",
            seasonal_adjustment="not seasonally adjusted",
            release_timing=(
                "Next business day. Month-end levels jump on accrued-interest "
                "adjustments, which the source's own notes call out."
            ),
            revision_behavior=(
                "Rarely revised, but the observation WINDOW moves: the trailing "
                "three-year cap means observations silently leave the series as "
                "time passes. A download taken a year from now will not contain "
                "the rows this one does, and no archive of the dropped rows is "
                "published anywhere this code can read."
            ),
        ),
        FredSeries(
            series_id="BAMLHYH0A0HYM2TRIV",
            title="ICE BofA US High Yield Index Total Return Index Value",
            definition=(
                "TRUNCATED TO THREE YEARS AND THEREFORE USELESS FOR RESEARCH — "
                "see BAMLCC0A0CMTRIV for the full measurement and the licence "
                "note; both were taken on 2026-08-16 and both returned exactly "
                "795 daily rows, 2023-08-15 to 2026-08-13. A genuine total-return "
                "index level for US dollar below-investment-grade corporate "
                "debt. This repository holds NO usable high-yield total-return "
                "history: goyal_welch covers long-term INVESTMENT GRADE "
                "corporates only, and high yield is not a substitute for it."
            ),
            frequency="daily",
            source_units="index_level",
            units="index_level",
            unit_transform="identity",
            transformation="none (index level, as published)",
            maturity_months=None,
            construction="index_level",
            day_count="not applicable (an index level, not a rate)",
            seasonal_adjustment="not seasonally adjusted",
            release_timing="Next business day.",
            revision_behavior=(
                "Rarely revised, but the observation WINDOW moves; see "
                "BAMLCC0A0CMTRIV."
            ),
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
        FredSeries(
            series_id="CPIAUCNS",
            title="Consumer Price Index for All Urban Consumers: All Items (NSA)",
            definition=(
                "The NOT seasonally adjusted CPI-U index level. Registered "
                "because it, and not CPIAUCSL, is the reference index a Treasury "
                "Inflation-Protected Security's principal is indexed to: 31 CFR "
                "356.2 defines the Index Ratio from the non-seasonally-adjusted "
                "CPI-U, applied with a THREE-MONTH LAG and interpolated within "
                "the month. Anything that models a TIPS return with the "
                "seasonally adjusted series is using a series the security does "
                "not reference. Measured 2026-08-17: monthly from 1913-01."
            ),
            frequency="monthly",
            source_units="index_1982_1984_eq_100",
            units="index_1982_1984_eq_100",
            unit_transform="identity",
            transformation="none (index level, as published)",
            maturity_months=None,
            construction="index_level",
            day_count="not applicable",
            seasonal_adjustment="not seasonally adjusted",
            release_timing=(
                "Roughly mid-month for the prior month, on the BLS schedule. "
                "Unlike the seasonally adjusted series this one is essentially "
                "final on first publication, which is why the indexed security "
                "references it."
            ),
            revision_behavior=(
                "The published NSA index is not revised in the ordinary course; "
                "the seasonally adjusted twin is rewritten every year. That "
                "asymmetry is the reason 31 CFR 356 names this one."
            ),
        ),
        FredSeries(
            series_id="CBBTCUSD",
            title="Coinbase Bitcoin",
            definition=(
                "One venue's US dollar price of one bitcoin, published by "
                "Coinbase and redistributed by FRED. The only bitcoin price "
                "series this repository holds. Measured 2026-08-17: 2014-12-01 "
                "to 2026-08-16, daily including weekends, U.S. Dollars, not "
                "seasonally adjusted. The series notes state, in full, 'All data "
                "is as of 5 PM PST.' — so an observation is a snapshot at a "
                "stated wall-clock time on one exchange, NOT a settled close and "
                "NOT a multi-venue reference rate. It is therefore not the index "
                "any US spot bitcoin ETP prices its net asset value against, and "
                "the two largest do not even use the same one: IBIT's 10-K names "
                "the CME CF Bitcoin Reference Rate - New York Variant, a 3-4 "
                "p.m. New York volume-weighted median across eight venues "
                "administered by CF Benchmarks Ltd., while FBTC's names the "
                "Fidelity Bitcoin Reference Rate, whose methodology is written "
                "by an affiliate of its own sponsor. Neither is published here. "
                "Reaching for this series where an ETP's own index is meant is a "
                "substitution, and the difference is an unmeasured basis. "
                "Decision 0002 does not forbid it: that decision bans free PRICE "
                "feeds because they drop distributions and mishandle corporate "
                "actions, and bitcoin pays no distribution and has no corporate "
                "action, which is the identical carve-out the World Bank gold "
                "series relies on. Everything else decision 0002 says still "
                "applies, so this is exploratory and may not support a "
                "confirmatory result."
            ),
            frequency="daily",
            source_units="usd_per_bitcoin",
            units="usd_per_bitcoin",
            unit_transform="identity",
            transformation="none (price level, as published)",
            maturity_months=None,
            construction="exchange_reference_price",
            day_count="not applicable (a price, not a rate)",
            seasonal_adjustment="not seasonally adjusted",
            release_timing=(
                "Daily, seven days a week, timestamped 5 p.m. PST on the day it "
                "describes. A month-end observation is the last calendar day of "
                "the month rather than the last business day, because the market "
                "does not close."
            ),
            revision_behavior=(
                "No series-specific revision policy is published. FRED's own "
                "panel says only 'All data are subject to revision'. Vintages do "
                "exist: ALFRED serves this series with release dates from "
                "2018-06-17, checked 2026-08-17, so a corrected print is "
                "recoverable there even though this module does not read it. "
                "The file also carries at least one bad print — 2015-01-14 reads "
                "120.00 between neighbours in the 260s — which month-end "
                "sampling happens to miss and daily use would not. "
                "The series carries a redistribution prohibition — "
                "'Copyright, 2018, Coinbase. Reproduction of Coinbase data in "
                "any form is prohibited except with the prior written permission "
                "of Coinbase.' — so its bytes stay in the uncommitted cache and "
                "only hashes are manifested, the same posture as the ICE BofA "
                "and LBMA series."
            ),
        ),
        # --- H.10 bilateral spot rates -------------------------------------
        # The developed-market currencies a US investor is long through VEA and
        # DFIV, and the emerging-market ones IEMG and AVES carry. Registered
        # 2026-08-22 for the currency-hedging question; coverage measured the
        # same day off the CSV endpoint.
        _spot_rate(
            "DEXJPUS",
            title="Japanese Yen to U.S. Dollar Spot Exchange Rate",
            currency="JPY",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1971-01-04 to 2026-08-14, 14,509 observations.",
        ),
        _spot_rate(
            "DEXUSUK",
            title="U.S. Dollars to U.K. Pound Sterling Spot Exchange Rate",
            currency="GBP",
            quote_convention="usd_per_foreign",
            coverage="Daily, 1971-01-04 to 2026-08-14, 14,509 observations.",
        ),
        _spot_rate(
            "DEXSZUS",
            title="Swiss Francs to U.S. Dollar Spot Exchange Rate",
            currency="CHF",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1971-01-04 to 2026-08-14, 14,509 observations.",
            notes=(
                "Carries the 2015-01-15 removal of the 1.20 EUR/CHF floor, a "
                "single day on which the franc moved about 20% against the "
                "dollar. Any volatility estimated through that date is a "
                "measurement of a policy break as much as of a market."
            ),
        ),
        _spot_rate(
            "DEXCAUS",
            title="Canadian Dollars to U.S. Dollar Spot Exchange Rate",
            currency="CAD",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1971-01-04 to 2026-08-14, 14,509 observations.",
        ),
        _spot_rate(
            "DEXUSAL",
            title="U.S. Dollars to Australian Dollar Spot Exchange Rate",
            currency="AUD",
            quote_convention="usd_per_foreign",
            coverage="Daily, 1971-01-04 to 2026-08-14, 14,509 observations.",
        ),
        _spot_rate(
            "DEXUSEU",
            title="U.S. Dollars to Euro Spot Exchange Rate",
            currency="EUR",
            quote_convention="usd_per_foreign",
            coverage="Daily, 1999-01-04 to 2026-08-14, 7,204 observations.",
            notes=(
                "STARTS AT THE EURO'S LAUNCH. There is no euro before "
                "1999-01-04 and this repository holds no legacy-currency splice, "
                "so a currency panel containing the euro cannot begin earlier "
                "without an analytical choice that is not made here."
            ),
        ),
        _spot_rate(
            "DEXSDUS",
            title="Swedish Kronor to U.S. Dollar Spot Exchange Rate",
            currency="SEK",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1971-01-04 to 2026-08-14, 14,509 observations.",
        ),
        _spot_rate(
            "DEXHKUS",
            title="Hong Kong Dollars to U.S. Dollar Spot Exchange Rate",
            currency="HKD",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1981-01-02 to 2026-08-14, 11,900 observations.",
            notes=(
                "PEGGED to the US dollar since 1983 inside a band the HKMA "
                "defends. Its currency return is near zero by construction and "
                "its volatility is not an estimate of anything a floating "
                "currency does; the hedging question does not arise for it."
            ),
        ),
        _spot_rate(
            "DEXSIUS",
            title="Singapore Dollars to U.S. Dollar Spot Exchange Rate",
            currency="SGD",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1981-01-02 to 2026-08-14, 11,900 observations.",
            notes=(
                "MANAGED against an undisclosed trade-weighted basket by the "
                "MAS, which runs monetary policy through the exchange rate "
                "rather than through an interest rate."
            ),
        ),
        _spot_rate(
            "DEXCHUS",
            title="Chinese Yuan Renminbi to U.S. Dollar Spot Exchange Rate",
            currency="CNY",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1981-01-02 to 2026-08-14, 11,900 observations.",
            notes=(
                "MANAGED, and for 1994-2005 and 2008-2010 effectively FIXED. A "
                "volatility or correlation estimated across those years measures "
                "a policy, and the onshore CNY quoted here is not the offshore "
                "CNH a foreign investor would actually transact or hedge in."
            ),
        ),
        _spot_rate(
            "DEXINUS",
            title="Indian Rupees to U.S. Dollar Spot Exchange Rate",
            currency="INR",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1973-01-02 to 2026-08-14, 13,988 observations.",
        ),
        _spot_rate(
            "DEXTAUS",
            title="Taiwan Dollars to U.S. Dollar Spot Exchange Rate",
            currency="TWD",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1983-10-03 to 2026-08-14, 11,184 observations.",
        ),
        _spot_rate(
            "DEXKOUS",
            title="South Korean Won to U.S. Dollar Spot Exchange Rate",
            currency="KRW",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1981-04-13 to 2026-08-14, 11,829 observations.",
        ),
        _spot_rate(
            "DEXBZUS",
            title="Brazilian Reals to U.S. Dollar Spot Exchange Rate",
            currency="BRL",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1995-01-02 to 2026-08-14, 8,249 observations.",
            notes=(
                "STARTS AT THE REAL'S INTRODUCTION in 1994 and therefore omits "
                "every earlier Brazilian currency and redenomination. The "
                "1999 float and the 2002 election crisis are both inside it."
            ),
        ),
        _spot_rate(
            "DEXSFUS",
            title="South African Rand to U.S. Dollar Spot Exchange Rate",
            currency="ZAR",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1980-01-02 to 2026-08-14, 12,162 observations.",
        ),
        _spot_rate(
            "DEXMXUS",
            title="Mexican Pesos to U.S. Dollar Spot Exchange Rate",
            currency="MXN",
            quote_convention="foreign_per_usd",
            coverage="Daily, 1993-11-08 to 2026-08-14, 8,549 observations.",
            notes=(
                "STARTS WEEKS BEFORE the December 1994 devaluation and inside "
                "the 1993 redenomination. The first fourteen months of this "
                "series are one of the largest currency losses in the panel."
            ),
        ),
        # --- Fed trade-weighted dollar indices ------------------------------
        FredSeries(
            series_id="DTWEXAFEGS",
            title="Nominal Advanced Foreign Economies U.S. Dollar Index",
            definition=(
                "The Federal Reserve's nominal trade-weighted index of the US "
                "dollar against a subset of advanced foreign economies, goods "
                "and services trade weights, published in the H.10 release. "
                "Measured 2026-08-22: daily, 2006-01-02 to 2026-08-14, 5,379 "
                "observations, index 2006-01-02 = 100. A RISE IS A STRONGER "
                "DOLLAR, so the return to holding the basket of foreign "
                "currencies is level[t-1] / level[t] - 1. "
                "REGISTERED AS A CROSS-CHECK ON A CAP-WEIGHTED BASKET, NOT AS A "
                "SUBSTITUTE FOR ONE: the weights are bilateral GOODS AND "
                "SERVICES TRADE shares, which is not how a developed-ex-US "
                "equity index is weighted. Canada is the United States' largest "
                "trading partner and a small share of developed-ex-US equity "
                "market capitalisation, and Japan is the reverse, so this index "
                "and an equity-weighted currency basket are different objects "
                "that happen to move together."
            ),
            frequency="daily",
            source_units="index_2006_01_02_eq_100",
            units="index_2006_01_02_eq_100",
            unit_transform="identity",
            transformation="none (index level, as published)",
            maturity_months=None,
            construction="trade_weighted_index",
            day_count="not applicable (an index level, not a rate)",
            seasonal_adjustment="not seasonally adjusted",
            release_timing=_H10_AVAILABILITY,
            revision_behavior=(
                "Not point-in-time, and the WEIGHTS ARE REVISED ANNUALLY from "
                "updated trade data, which rewrites recent history. The whole "
                "index family was restructured in January 2019, when the Board "
                "replaced the Major/OITP split with the Broad/AFE/EME split; "
                "this series is a product of that restructuring and its "
                "pre-2019 values are a backfill computed under the new scheme, "
                "not what anyone published at the time."
            ),
        ),
        FredSeries(
            series_id="DTWEXM",
            title=(
                "Nominal Major Currencies U.S. Dollar Index (Goods Only) "
                "(DISCONTINUED)"
            ),
            definition=(
                "The Federal Reserve's former nominal major-currencies dollar "
                "index, goods-only trade weights, DISCONTINUED at the January "
                "2019 restructuring and last published 2019-12-31. Measured "
                "2026-08-22: daily, 1973-01-02 to 2019-12-31, 12,260 "
                "observations, index March 1973 = 100. A RISE IS A STRONGER "
                "DOLLAR. Registered for one reason: it is the only free daily "
                "developed-currency series in this repository that reaches back "
                "to the collapse of Bretton Woods, and the currency question "
                "needs the longest window it can defend. It ENDS IN 2019 and so "
                "sees neither 2020 nor 2022 nor 2025; DTWEXAFEGS covers those "
                "and the two overlap 2006-2019 but are NOT the same index and "
                "must not be chained without saying so."
            ),
            frequency="daily",
            source_units="index_1973_03_eq_100",
            units="index_1973_03_eq_100",
            unit_transform="identity",
            transformation="none (index level, as published)",
            maturity_months=None,
            construction="trade_weighted_index",
            day_count="not applicable (an index level, not a rate)",
            seasonal_adjustment="not seasonally adjusted",
            release_timing=_H10_AVAILABILITY,
            revision_behavior=(
                "Discontinued, so the history no longer changes. While it was "
                "live its weights were revised annually and rewrote recent "
                "history in the same way DTWEXAFEGS's do."
            ),
        ),
        # --- OECD three-month interbank rates -------------------------------
        # The carry leg. These are differenced against IR3TIB01USM156N and
        # against nothing else; see _OECD_INTERBANK_DEFINITION.
        _oecd_interbank_rate(
            "IR3TIB01USM156N",
            country="United States",
            currency="USD",
            coverage="monthly, 1964-06 to 2026-06, 744 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01DEM156N",
            country="Germany",
            currency="EUR",
            coverage=(
                "monthly, 1960-01 to 2026-06, 797 observations. CURRENCY IS "
                "RECORDED AS EUR BECAUSE THAT IS WHAT IT IS AFTER 1999: the "
                "series is a Deutsche Mark interbank rate before 1999 and a "
                "euro one after, spliced by the source, and it is used here as "
                "the euro-area rate for the whole window."
            ),
        ),
        _oecd_interbank_rate(
            "IR3TIB01JPM156N",
            country="Japan",
            currency="JPY",
            coverage=(
                "monthly, 2002-04 to 2026-05, 289 observations. THE SHORTEST "
                "MEMBER OF THE FAMILY BY TWENTY YEARS, and it is the binding "
                "constraint on any panel that needs all of them at once."
            ),
        ),
        _oecd_interbank_rate(
            "IR3TIB01GBM156N",
            country="United Kingdom",
            currency="GBP",
            coverage=(
                "monthly, 1957-01 to 2026-01, 828 observations. ENDS 2026-01 "
                "while its siblings run to June; a panel that intersects on "
                "dates will lose five months to this series alone."
            ),
        ),
        _oecd_interbank_rate(
            "IR3TIB01CHM156N",
            country="Switzerland",
            currency="CHF",
            coverage="monthly, 1999-07 to 2026-06, 323 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01CAM156N",
            country="Canada",
            currency="CAD",
            coverage="monthly, 1956-01 to 2026-06, 845 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01AUM156N",
            country="Australia",
            currency="AUD",
            coverage="monthly, 1968-01 to 2026-06, 701 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01SEM156N",
            country="Sweden",
            currency="SEK",
            coverage="monthly, 1982-01 to 2026-06, 533 observations.",
        ),
        # The four emerging-market currencies for which the same OECD interbank
        # measurement exists. Brazil and India do NOT have one — FRED serves
        # only discount rates for them, and India's ends 2022-07 — so an
        # emerging-market carry basket built here is necessarily incomplete and
        # any page using it must say which currencies are missing from it.
        _oecd_interbank_rate(
            "IR3TIB01KRM156N",
            country="Korea",
            currency="KRW",
            coverage="monthly, 1991-01 to 2026-06, 425 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01MXM156N",
            country="Mexico",
            currency="MXN",
            coverage="monthly, 1997-01 to 2026-06, 353 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01ZAM156N",
            country="South Africa",
            currency="ZAR",
            coverage="monthly, 1980-12 to 2026-06, 546 observations.",
        ),
        _oecd_interbank_rate(
            "IR3TIB01CNM156N",
            country="China",
            currency="CNY",
            coverage=(
                "monthly, 1997-06 to 2026-05, 347 observations. AN ONSHORE "
                "ADMINISTERED RATE for most of its history, not a freely traded "
                "one, and it prices onshore CNY rather than the offshore CNH a "
                "foreign investor would hedge in."
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
    if left.currency != right.currency:
        differences.append(
            f"currency differs: {left.series_id}={left.currency}, "
            f"{right.series_id}={right.currency}"
        )
    if left.quote_convention != right.quote_convention:
        differences.append(
            f"quote convention differs: {left.series_id}={left.quote_convention}, "
            f"{right.series_id}={right.quote_convention}"
        )
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
    currency: str = "USD"


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
        and series.currency == requirement.currency
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
