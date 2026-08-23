"""Regenerates every measured table in ``docs/research/currency-and-the-international-sleeve.md``.

Run it with::

    uv run python -m portfolio_edge.studies._currency_hedging_tables

Kept separate from :mod:`portfolio_edge.studies.currency_hedging` so that module stays
pure and testable and only this file touches the cache, the same split
:mod:`portfolio_edge.studies._stress_dependence_tables` uses.

**Everything here is `exploratory`.** No specification was frozen before the numbers
were seen, no experiment is registered, and the stress windows were chosen by eye from
history by an earlier page. Nothing below may support a promoted claim.

The four panels, and why there are four
----------------------------------------
No single free panel answers the currency question, because the three sub-questions have
different data needs and different resolution.

``JST`` — **1871-2020, annual, 15 countries.** Jordà-Schularick-Taylor local-currency
equity total returns, bill rates and ``xrusd``. The only source in this repository that
can measure a currency excess return over more than one monetary regime. Its point is
comparative: pre-1914 gold standard, interwar catastrophe, Bretton Woods peg and
post-1973 float are four different objects, and quoting a full-sample currency figure
across them would average a war with a floating rate.

``M1`` — **monthly, developed, spot and carry.** Ken French's developed-ex-US market
return (which is published **in dollars**), a cap-weighted currency basket built from
H.10 noon rates, and the OECD three-month interbank differential. The primary panel for
the hedged-versus-unhedged comparison. It starts in 2002-04 and ends 2026-01 because
Japan's interbank series starts there and the UK's ends there — a constraint of the
statistical programme, not of the market.

``M2`` — **monthly, developed, spot only, 1999-02 onward.** The same thing without the
carry leg, which buys back the three years the Japanese rate costs. A "hedge" here
earns no interest differential, so when US rates exceed foreign ones it **understates**
the hedged return. It is a cross-check on M1's spot term, not a substitute for it.

``DOLLAR`` — **the Fed's own trade-weighted indices**, ``DTWEXM`` 1973-2019 and
``DTWEXAFEGS`` 2006-2026. Official weights, no basket construction by this module, and
the longest monthly currency history available free. Trade weights are not equity
weights, so this panel is a cross-check on the *shape* of the basket result and never a
substitute for it.

Traps that decide whether a number here is right
-------------------------------------------------
*The H.10 quotes some pairs each way round.* ``DEXJPUS`` is yen per dollar and
``DEXUSUK`` is dollars per pound. Every level in this module goes through
:func:`portfolio_edge.data.fred.foreign_currency_return`, which reads the registry's
typed quote convention; no ratio is written by hand anywhere below.

*Month-end, never monthly-average.* The daily H.10 series are sampled at the last
business day with a print in each calendar month.
[The evidence base](../../../../docs/research/evidence-base.md) records what a
monthly-averaged series does to any result that depends on serial correlation, and the
monthly ``EX*`` twins of these series are exactly that.

*Covered interest parity is assumed, not measured.* The hedged leg prices the forward at
``S (1 + i_USD) / (1 + i_foreign)``. Since 2008 a cross-currency basis has driven a
wedge into that, and **its sign favours a dollar-based investor**: the basis is quoted on
the non-dollar leg and is negative because dollars are scarce, so the party that supplies
dollars to the swap market — which is what a USD investor hedging foreign assets is
doing — receives slightly *more* than plain CIP implies. Every hedged return computed
here is therefore a mild **under**statement, not an overstatement, by the size of the
basis. The magnitude is small and shrinking: the BIS puts the turnover-weighted
three-month basis at about -9 bp in October 2025 against about -59 bp in October 2022,
and it widens predictably each autumn as three-month contracts begin to span the
year-end. None of that is observable in the series this module reads, so it is stated
here and quantified only from the published source.

*The interest differential must be interbank on both sides.* A forward is priced off the
money-market curve. Differencing a foreign interbank rate against a US Treasury bill
rate would import the US bill-to-interbank spread into the answer, which is why
``IR3TIB01USM156N`` and not ``TB3MS`` is the domestic leg here.

*The currency basket is not the fund's basket.* Weights are equity-market weights read
from a published fund document, applied as constants for the whole window. A fund's
weights move; a currency basket built from seven currencies is missing the small
markets; and no free source publishes a point-in-time currency weight history. The
:data:`DOLLAR` panel exists so that a reader can see how much of the answer survives a
completely different weighting scheme.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import fred, french, macrohistory
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.studies._stress_dependence_tables import STRESS_WINDOWS
from portfolio_edge.studies.currency_hedging import (
    HEDGE_RATIO_GRID,
    PERCENT,
    CurrencyPanel,
    HedgeComparison,
    effective_sample_size,
    hedge_comparison,
    hedge_give_up,
    hedge_ratio_grid,
    weighted_basket,
)
from portfolio_edge.studies.stress_dependence import episode_returns, tail_dependence

#: Developed-market currencies, mapped to their H.10 spot series and OECD interbank rate.
#: Seven currencies, chosen because they are the only developed ones with **both** a
#: daily spot rate and a comparable three-month interbank rate in this repository.
DEVELOPED_SPOT: Final[Mapping[str, str]] = {
    "EUR": "DEXUSEU",
    "JPY": "DEXJPUS",
    "GBP": "DEXUSUK",
    "CAD": "DEXCAUS",
    "KRW": "DEXKOUS",
    "CHF": "DEXSZUS",
    "AUD": "DEXUSAL",
    "SEK": "DEXSDUS",
}

DEVELOPED_INTERBANK: Final[Mapping[str, str]] = {
    "EUR": "IR3TIB01DEM156N",
    "JPY": "IR3TIB01JPM156N",
    "GBP": "IR3TIB01GBM156N",
    "CAD": "IR3TIB01CAM156N",
    "KRW": "IR3TIB01KRM156N",
    "CHF": "IR3TIB01CHM156N",
    "AUD": "IR3TIB01AUM156N",
    "SEK": "IR3TIB01SEM156N",
}

#: The US leg of every differential. Interbank on both sides, deliberately; see the
#: module docstring.
USD_INTERBANK: Final = "IR3TIB01USM156N"

#: Currency weights for the developed sleeve, from **VEA's** own published market
#: allocation — the fund the investor actually holds — read 2026-08-22 from
#: https://investor.vanguard.com/vmf/api/vea/diversification (Vanguard states the
#: allocation as of 2026-07-31). Country weights are assigned to currencies (France,
#: Germany, the Netherlands, Spain, Italy, Belgium, Finland, Austria, Ireland and
#: Portugal all to the euro, 26.0% together) and the eight currencies below are
#: renormalised to one from the **93.1%** of the fund they cover.
#:
#: **VEA is not EAFE, and the difference is the whole implementation problem.** VEA
#: tracks FTSE Developed All Cap ex US, which includes **Canada at 10.9%** and **Korea
#: at 8.0%**; MSCI EAFE, which every large hedged product tracks, excludes both. So
#: nineteen per cent of this investor's developed currency exposure is in currencies no
#: hedged EAFE fund touches. :data:`EAFE_WEIGHTS` is measured beside this one so the
#: gap is a number rather than an assertion.
#:
#: Hong Kong, Denmark, Singapore, Israel, Norway, Poland and New Zealand — 6.9% between
#: them — are dropped for want of a registered spot rate or a comparable interbank rate.
#: The Hong Kong dollar is pegged and the Singapore dollar is managed against a basket,
#: so dropping those two removes near-zero-variance legs and if anything **raises** the
#: measured volatility of the basket rather than lowering it.
#:
#: The weights are a constant applied to the whole window. A fund's weights move —
#: Vanguard's own endpoint shows Korea going 4.6% to 8.0% in twelve months — and no free
#: source publishes a point-in-time currency weight history. The Fed's trade-weighted
#: indices are reported beside every basket result precisely so a reader can see how much
#: of the answer survives an entirely different weighting scheme.
DEVELOPED_WEIGHTS: Final[Mapping[str, float]] = {
    "EUR": 26.0 / 93.1,
    "JPY": 20.9 / 93.1,
    "GBP": 11.6 / 93.1,
    "CAD": 10.9 / 93.1,
    "KRW": 8.0 / 93.1,
    "CHF": 7.1 / 93.1,
    "AUD": 5.8 / 93.1,
    "SEK": 2.8 / 93.1,
}

#: The same construction on **IEFA's** country allocation, read 2026-08-22 from
#: https://www.ishares.com/us/products/244049/ishares-core-msci-eafe-etf and stated as of
#: 2026-08-20, renormalised from the 90.29% of that fund these six currencies cover.
#: This is the basket a currency-hedged **EAFE** product removes. Measuring both is how
#: the page answers "what would the available product actually hedge?" rather than
#: assuming the product hedges what the investor holds.
EAFE_WEIGHTS: Final[Mapping[str, float]] = {
    "EUR": 31.54 / 90.29,
    "JPY": 25.07 / 90.29,
    "GBP": 14.22 / 90.29,
    "CHF": 8.65 / 90.29,
    "AUD": 7.14 / 90.29,
    "SEK": 3.67 / 90.29,
}

#: Emerging-market currencies with an H.10 spot rate, and the four that also have a
#: comparable OECD three-month interbank rate. Brazil and India have **no** interbank
#: series on this feed — FRED serves only discount rates for them and India's ends in
#: 2022 — so an emerging carry basket built here covers four currencies, not seven, and
#: every table using it says which three are missing.
EMERGING_SPOT: Final[Mapping[str, str]] = {
    "CNY": "DEXCHUS",
    "INR": "DEXINUS",
    "TWD": "DEXTAUS",
    "KRW": "DEXKOUS",
    "BRL": "DEXBZUS",
    "ZAR": "DEXSFUS",
    "MXN": "DEXMXUS",
}

EMERGING_INTERBANK: Final[Mapping[str, str]] = {
    "CNY": "IR3TIB01CNM156N",
    "KRW": "IR3TIB01KRM156N",
    "ZAR": "IR3TIB01ZAM156N",
    "MXN": "IR3TIB01MXM156N",
}

#: Emerging-market currency weights from **IEMG's** published country allocation, read
#: 2026-08-22 from
#: https://www.ishares.com/us/products/244050/ishares-core-msci-emerging-markets-etf and
#: stated by the issuer as of 2026-08-20, renormalised from the 87.50% of the fund these
#: seven currencies cover. Saudi Arabia and the United Arab Emirates are dropped and
#: both are **pegged to the dollar**, so their exclusion removes near-zero-variance
#: legs; Poland, Malaysia and Thailand are dropped for want of an H.10 series.
EMERGING_WEIGHTS: Final[Mapping[str, float]] = {
    "TWD": 26.77 / 87.50,
    "KRW": 20.13 / 87.50,
    "CNY": 19.41 / 87.50,
    "INR": 12.53 / 87.50,
    "BRL": 3.70 / 87.50,
    "ZAR": 3.30 / 87.50,
    "MXN": 1.66 / 87.50,
}

#: Countries in the JST panel that adopted the euro. From 1999 they are one currency,
#: and the composite folds them into a single bloc so that an equal-weighted basket of
#: fifteen countries does not silently become 53% euro.
JST_EURO_BLOC: Final[tuple[str, ...]] = (
    "BEL",
    "DEU",
    "ESP",
    "FIN",
    "FRA",
    "ITA",
    "NLD",
    "PRT",
)

JST_EURO_FROM: Final = 1999

#: Germany is dropped for these years. The JST ``xrusd`` column is chained through the
#: 1923 hyperinflation and the 1948 currency reform in units of the surviving currency,
#: so a "currency return" computed across them is redenomination arithmetic: 1923 reads
#: -100.0% and 1949 reads +238.8%, neither of which any investor experienced. This is a
#: **documented, pre-stated exclusion on source grounds**, not a filter on the values.
JST_GERMANY_EXCLUDED: Final[tuple[int, int]] = (1914, 1950)

#: The minimum number of currencies a JST composite year must contain before it is used.
#: Below this the "basket" is two or three countries and its volatility is a fact about
#: coverage rather than about currencies.
JST_MINIMUM_CURRENCIES: Final = 5

#: The three JST windows, and what each one is for. They are monetary regimes, not
#: round numbers: a currency result that pools a gold-standard peg with a post-1973
#: float has averaged two different data-generating processes.
JST_WINDOWS: Final[tuple[tuple[str, int, int], ...]] = (
    ("1871-2020 all regimes", 1871, 2020),
    ("1951-2020 post-war", 1951, 2020),
    ("1974-2020 floating", 1974, 2020),
)

#: Calendar slices reported on the developed basket, so that the recent years everyone
#: argues about are visible beside the full window rather than replacing it.
RECENT_SLICES: Final[tuple[tuple[str, str, str], ...]] = (
    ("2010-2024", "2010-01", "2024-12"),
    ("2023", "2023-01", "2023-12"),
    ("2024", "2024-01", "2024-12"),
    ("2025", "2025-01", "2025-12"),
    ("2026 H1", "2026-01", "2026-06"),
)

#: Two equity drawdowns that postdate the canonical :data:`STRESS_WINDOWS` list and that
#: this question cannot skip, because the claim under test — that the dollar rises when
#: equity falls — is exactly what 2025 is said to have broken.
#:
#: The dates are **read off the panel, not chosen**: they are the peak-to-trough months
#: of Ken French's US market total return since 2024-06. February to April 2025 is a
#: -8.5% US equity drawdown and February to March 2026 a -5.7% one. Two episodes cannot
#: settle whether a relationship has changed and this table does not claim they can;
#: they are printed so that the recent counter-example is visible next to the older
#: episodes rather than argued about in prose.
RECENT_EPISODES: Final[dict[str, tuple[str, str]]] = {
    "2025 Feb-Apr drawdown": ("2025-02", "2025-04"),
    "2026 Feb-Mar drawdown": ("2026-02", "2026-03"),
}

MONTHS_PER_YEAR: Final = 12


def _require(cache: RawCache, url: str, label: str) -> CacheEntry:
    entry = cache.entry_for(url)
    if entry is None:
        raise RuntimeError(
            f"{label} is not cached. This module never downloads, so a currency table "
            f"can never be the thing that silently pulls a new vintage."
        )
    return entry


def _month_end_levels(
    cache: RawCache, series_id: str
) -> tuple[fred.FredSeries, dict[str, float], str]:
    """The last daily print in each calendar month, as ``{YYYY-MM: level}``.

    Last *print*, not last calendar day: the H.10 skips US holidays and weekends, so the
    sample date drifts within the month. That is the correct sample for a return series
    and it is not the same as the monthly-average ``EX*`` twins, which must not be used
    here.
    """
    series = fred.get_series(series_id)
    entry = _require(cache, series.url, f"FRED {series_id}")
    table = fred.parse(cache, entry, series_id)
    levels: dict[str, float] = {}
    for period, row in zip(table.periods, table.values, strict=True):
        value = row[0]
        if value is not None:
            levels[period[:7]] = float(value)
    return series, levels, entry.sha256


def _monthly_rate(cache: RawCache, series_id: str) -> tuple[dict[str, float], str]:
    """A monthly interest-rate series as ``{YYYY-MM: annual decimal rate}``."""
    series = fred.get_series(series_id)
    entry = _require(cache, series.url, f"FRED {series_id}")
    table = fred.parse(cache, entry, series_id)
    values = {
        period[:7]: float(row[0])
        for period, row in zip(table.periods, table.values, strict=True)
        if row[0] is not None
    }
    return values, entry.sha256


def _spot_returns(
    cache: RawCache, mapping: Mapping[str, str]
) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    """Per-currency monthly returns to a USD investor holding one unit of the currency."""
    returns: dict[str, dict[str, float]] = {}
    digests: dict[str, str] = {}
    for currency, series_id in mapping.items():
        series, levels, digest = _month_end_levels(cache, series_id)
        digests[series_id] = digest
        months = sorted(levels)
        returns[currency] = {
            later: fred.foreign_currency_return(series, levels[earlier], levels[later])
            for earlier, later in itertools.pairwise(months)
        }
    return returns, digests


def _french_total_return(cache: RawCache, dataset_id: str) -> tuple[dict[str, float], str]:
    """``Mkt-RF + RF``: the region's market **total** return in US dollars.

    Ken French publishes the international factors in dollars and publishes no
    local-currency series, which is the whole reason this module has to construct a
    currency basket rather than read a local return off a file.
    """
    dataset = french.get_dataset(dataset_id)
    entry = _require(cache, dataset.url, f"Ken French {dataset_id}")
    table = french.parse(cache, entry, dataset=dataset).table("monthly")
    market = table.column("Mkt-RF")
    cash = table.column("RF")
    values: dict[str, float] = {}
    for period, excess, rf in zip(table.periods, market, cash, strict=True):
        if excess is not None and rf is not None:
            values[period] = float(excess) + float(rf)
    return values, entry.sha256


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionPanel:
    """One region's aligned monthly panel, plus the pieces the tables need separately."""

    label: str
    months: tuple[str, ...]
    unhedged: FloatArray
    currency_excess: FloatArray
    spot: FloatArray
    us_equity: FloatArray
    per_currency_spot: Mapping[str, FloatArray]
    carry_included: bool

    def panel(self) -> CurrencyPanel:
        return CurrencyPanel(
            label=self.label,
            periods=self.months,
            periods_per_year=MONTHS_PER_YEAR,
            unhedged=self.unhedged,
            currency_excess=self.currency_excess,
        )


def load_region(
    cache: RawCache,
    *,
    label: str,
    equity_dataset: str,
    spot_series: Mapping[str, str],
    interbank_series: Mapping[str, str],
    weights: Mapping[str, float],
    carry: bool,
) -> tuple[RegionPanel, dict[str, str]]:
    """Build one region's monthly panel by intersecting every input's own coverage.

    Intersecting is the only honest option and it is expensive: the panel is as short as
    its shortest series, and which series that is changes with ``carry``. Both windows
    are printed so a reader can see the price of the carry leg.
    """
    spot_returns, digests = _spot_returns(cache, spot_series)
    equity, equity_digest = _french_total_return(cache, equity_dataset)
    us_equity, us_digest = _french_total_return(cache, "french_us_ff5")
    digests[equity_dataset] = equity_digest
    digests["french_us_ff5"] = us_digest

    coverage = [set(spot_returns[currency]) for currency in weights]
    rates: dict[str, dict[str, float]] = {}
    domestic: dict[str, float] = {}
    if carry:
        domestic, usd_digest = _monthly_rate(cache, USD_INTERBANK)
        digests[USD_INTERBANK] = usd_digest
        for currency in weights:
            series_id = interbank_series[currency]
            values, digest = _monthly_rate(cache, series_id)
            digests[series_id] = digest
            rates[currency] = values
            coverage.append(set(values))
        coverage.append(set(domestic))

    common: set[str] = set(equity) & set(us_equity)
    for available in coverage:
        common &= available
    months = tuple(sorted(common))
    if not months:
        raise RuntimeError(f"{label}: the inputs do not overlap at all")

    spot = {
        currency: np.asarray([spot_returns[currency][m] for m in months], dtype=np.float64)
        for currency in weights
    }
    basket_spot = weighted_basket(weights, spot)
    if carry:
        excess = {}
        for currency in weights:
            foreign = np.asarray(
                [rates[currency][m] / MONTHS_PER_YEAR for m in months], dtype=np.float64
            )
            home = np.asarray(
                [domestic[m] / MONTHS_PER_YEAR for m in months], dtype=np.float64
            )
            excess[currency] = hedge_give_up(spot[currency], foreign, home)
        basket_excess = weighted_basket(weights, excess)
    else:
        basket_excess = basket_spot

    return (
        RegionPanel(
            label=label,
            months=months,
            unhedged=np.asarray([equity[m] for m in months], dtype=np.float64),
            currency_excess=basket_excess,
            spot=basket_spot,
            us_equity=np.asarray([us_equity[m] for m in months], dtype=np.float64),
            per_currency_spot=spot,
            carry_included=carry,
        ),
        digests,
    )


JstWindowResult = tuple[tuple[str, ...], FloatArray, FloatArray, FloatArray]


def load_jst(cache: RawCache) -> tuple[dict[str, JstWindowResult], str]:
    """The JST composite for each window in :data:`JST_WINDOWS`.

    Each year's composite is an **equal-weighted** average across the countries that
    have a complete ``(xrusd, bill_rate, eq_tr)`` triple that year, with the euro members
    folded into one bloc from 1999. Equal weighting is a choice: JST publishes no market
    capitalisation, so the alternative would be to weight by nominal GDP, which is not
    what an equity investor holds either. The choice is stated rather than optimised.
    """
    dataset = macrohistory.get_dataset("jst_macrohistory_r6")
    entry = _require(cache, dataset.url, "the JST R6 workbook")
    parsed = macrohistory.parse(cache, entry, dataset=dataset)

    def cells(table_id: str) -> dict[tuple[str, str], float | None]:
        table = parsed.table(table_id)
        return {
            (year, country): table.values[row][column]
            for row, year in enumerate(table.periods)
            for column, country in enumerate(table.columns)
        }

    fx = cells("exchange_rate_usd")
    equity = cells("equity_total_return")
    bills = cells("bill_rate")
    years = parsed.table("exchange_rate_usd").periods
    foreign = [c for c in macrohistory.RETURN_COUNTRIES if c != "USA"]

    yearly: dict[str, tuple[dict[str, tuple[float, float, float]], float]] = {}
    low, high = JST_GERMANY_EXCLUDED
    for index in range(1, len(years)):
        previous, current = years[index - 1], years[index]
        domestic = bills.get((current, "USA"))
        if domestic is None:
            continue
        row: dict[str, tuple[float, float, float]] = {}
        for country in foreign:
            if country == "DEU" and low <= int(current) <= high:
                continue
            start, end = fx.get((previous, country)), fx.get((current, country))
            rate, total = bills.get((current, country)), equity.get((current, country))
            if start is None or end is None or rate is None or total is None:
                continue
            if start <= 0.0 or end <= 0.0:
                continue
            row[country] = (start / end - 1.0, float(rate), float(total))
        if row:
            yearly[current] = (row, float(domestic))

    results: dict[str, JstWindowResult] = {}
    for label, first, last in JST_WINDOWS:
        periods: list[str] = []
        unhedged: list[float] = []
        excess: list[float] = []
        spot: list[float] = []
        for year in sorted(yearly):
            if not first <= int(year) <= last:
                continue
            row, domestic = yearly[year]
            blocs: dict[str, list[tuple[float, float, float]]] = {}
            for country, value in row.items():
                key = (
                    "EUR"
                    if int(year) >= JST_EURO_FROM and country in JST_EURO_BLOC
                    else country
                )
                blocs.setdefault(key, []).append(value)
            if len(blocs) < JST_MINIMUM_CURRENCIES:
                continue
            legs_u, legs_x, legs_s = [], [], []
            for values in blocs.values():
                move = float(np.mean([v[0] for v in values]))
                rate = float(np.mean([v[1] for v in values]))
                total = float(np.mean([v[2] for v in values]))
                legs_u.append((1.0 + total) * (1.0 + move) - 1.0)
                legs_x.append(float(hedge_give_up([move], [rate], [domestic])[0]))
                legs_s.append(move)
            periods.append(year)
            unhedged.append(float(np.mean(legs_u)))
            excess.append(float(np.mean(legs_x)))
            spot.append(float(np.mean(legs_s)))
        results[label] = (
            tuple(periods),
            np.asarray(unhedged, dtype=np.float64),
            np.asarray(excess, dtype=np.float64),
            np.asarray(spot, dtype=np.float64),
        )
    return results, entry.sha256


def load_dollar_index(cache: RawCache, series_id: str) -> tuple[tuple[str, ...], FloatArray, str]:
    """A Fed trade-weighted dollar index as a **foreign-currency** monthly return.

    The index rises when the dollar strengthens, so the return to holding the basket is
    ``level[t-1] / level[t] - 1``. Inverting this is the single easiest way to publish a
    currency result with the wrong sign.
    """
    _, levels, digest = _month_end_levels(cache, series_id)
    months = sorted(levels)
    values = [levels[a] / levels[b] - 1.0 for a, b in itertools.pairwise(months)]
    return tuple(months[1:]), np.asarray(values, dtype=np.float64), digest


def _pct(value: float) -> str:
    return f"{value * PERCENT:+.2f}" if math.isfinite(value) else "n/a"


def _plain(value: float) -> str:
    return f"{value * PERCENT:.2f}" if math.isfinite(value) else "n/a"


def _comparison_row(result: HedgeComparison) -> str:
    return (
        f"| {result.label} | {result.first_period}..{result.last_period} | "
        f"{result.n_periods} | {result.effective_n:.0f} | "
        f"{_pct(result.mean_unhedged)} | {_plain(result.volatility_unhedged)} | "
        f"{_pct(result.mean_hedged)} | {_plain(result.volatility_hedged)} | "
        f"{_pct(result.mean_difference)} | {_plain(result.mde_80)} | "
        f"{'yes' if result.mean_resolved else '**no**'} | "
        f"{result.volatility_reduction * PERCENT:.1f} | "
        f"{result.variance_minimising_ratio:.2f} |"
    )


COMPARISON_HEADER: Final = (
    "| panel | window | n | eff n | unhedged pp/yr | vol % | hedged pp/yr | vol % | "
    "currency pp/yr | MDE80 | mean resolved | vol cut % | min-var h |\n"
    "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :-: | ---: | ---: |"
)


def _cumulative(values: Sequence[float] | FloatArray) -> float:
    return float(np.prod(1.0 + np.asarray(values, dtype=np.float64)) - 1.0)


def _slice(months: Sequence[str], values: FloatArray, first: str, last: str) -> FloatArray:
    keep = [i for i, m in enumerate(months) if first <= m <= last]
    return values[keep]


def main() -> None:  # pragma: no cover - a reporting entry point
    cache = RawCache()

    print("## 1. The long run: JST, annual, 15 countries\n")
    print(COMPARISON_HEADER)
    jst, jst_digest = load_jst(cache)
    jst_spot: dict[str, float] = {}
    for label, (periods, unhedged, excess, spot) in jst.items():
        panel = CurrencyPanel(
            label=label,
            periods=periods,
            periods_per_year=1,
            unhedged=unhedged,
            currency_excess=excess,
        )
        print(_comparison_row(hedge_comparison(panel)))
        jst_spot[label] = float(np.mean(spot))
    print()
    for label, mean in jst_spot.items():
        print(f"- {label}: spot leg alone {_pct(mean)} pp/yr")
    print(f"\nJST R6 workbook sha256 {jst_digest[:12]}\n")

    panels: dict[str, RegionPanel] = {}
    all_digests: dict[str, str] = {}
    for label, weights, carry in (
        ("M1 VEA basket, spot+carry", DEVELOPED_WEIGHTS, True),
        ("M2 VEA basket, spot only", DEVELOPED_WEIGHTS, False),
        ("M3 EAFE basket, spot+carry", EAFE_WEIGHTS, True),
    ):
        region, digests = load_region(
            cache,
            label=label,
            equity_dataset="french_developed_ex_us_ff5",
            spot_series=DEVELOPED_SPOT,
            interbank_series=DEVELOPED_INTERBANK,
            weights=weights,
            carry=carry,
        )
        panels[label] = region
        all_digests |= digests
    em_panel, em_digests = load_region(
        cache,
        label="EM, spot only",
        equity_dataset="french_emerging_ff5",
        spot_series=EMERGING_SPOT,
        interbank_series={},
        weights=EMERGING_WEIGHTS,
        carry=False,
    )
    panels["EM, spot only"] = em_panel
    all_digests |= em_digests
    em_carry, em_carry_digests = load_region(
        cache,
        label="EM, spot+carry (4 currencies)",
        equity_dataset="french_emerging_ff5",
        spot_series={c: EMERGING_SPOT[c] for c in EMERGING_INTERBANK},
        interbank_series=EMERGING_INTERBANK,
        weights={c: EMERGING_WEIGHTS[c] for c in EMERGING_INTERBANK},
        carry=True,
    )
    panels["EM, spot+carry (4 currencies)"] = em_carry
    all_digests |= em_carry_digests

    print("## 2. Hedged against unhedged, monthly\n")
    print(COMPARISON_HEADER)
    for region in panels.values():
        print(_comparison_row(hedge_comparison(region.panel())))
    print()

    print("## 3. The hedge-ratio frontier\n")
    print("| panel | h | mean pp/yr | vol % | worst month % | max drawdown % |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name in ("M1 VEA basket, spot+carry", "EM, spot only"):
        for point in hedge_ratio_grid(panels[name].panel(), ratios=HEDGE_RATIO_GRID):
            print(
                f"| {name} | {point.hedge_ratio:.2f} | {_pct(point.mean)} | "
                f"{_plain(point.volatility)} | {_pct(point.worst_period)} | "
                f"{_pct(point.max_drawdown)} |"
            )
    print()

    print("## 4. Crisis conditioning: the currency leg in the worst months\n")
    print(
        "| panel | conditioning base | tail months | base mean %/mo | currency mean %/mo | "
        "hit rate | worst %/mo | corr full | corr in tail |"
    )
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for name in ("M1 VEA basket, spot+carry", "EM, spot only"):
        region = panels[name]
        for base_label, base in (
            ("US equity", region.us_equity),
            ("the sleeve's own equity", region.unhedged),
        ):
            tail = tail_dependence(base, region.currency_excess, quantile=0.10)
            print(
                f"| {name} | {base_label} | {tail.months_low} | "
                f"{_pct(tail.base_mean_low)} | {_pct(tail.mean_low)} | "
                f"{tail.hit_rate_low:.0%} | {_pct(tail.worst_low)} | "
                f"{tail.correlation_full:+.2f} | {tail.correlation_low:+.2f} |"
            )
    print()

    print("### What the currency leg is correlated with\n")
    print(
        "| panel | corr with US equity | corr with the sleeve's own USD equity | "
        "corr with the implied local-currency leg |"
    )
    print("| --- | ---: | ---: | ---: |")
    for name in ("M1 VEA basket, spot+carry", "M3 EAFE basket, spot+carry", "EM, spot only"):
        region = panels[name]
        local = region.unhedged - region.currency_excess
        print(
            f"| {name} "
            f"| {float(np.corrcoef(region.currency_excess, region.us_equity)[0, 1]):+.2f} "
            f"| {float(np.corrcoef(region.currency_excess, region.unhedged)[0, 1]):+.2f} "
            f"| {float(np.corrcoef(region.currency_excess, local)[0, 1]):+.2f} |"
        )
    print(
        "\nThe third column is the one that decides the risk case. A currency leg "
        "*negatively* correlated with the local equity leg would be a hedge and would "
        "belong in the portfolio on risk grounds alone.\n"
    )

    print("### Named episodes, cumulative currency return\n")
    print("| episode | window | US equity | developed | emerging | DTWEXM | DTWEXAFEGS |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    dollar: dict[str, tuple[tuple[str, ...], FloatArray]] = {}
    for series_id in ("DTWEXM", "DTWEXAFEGS"):
        months, values, digest = load_dollar_index(cache, series_id)
        dollar[series_id] = (months, values)
        all_digests[series_id] = digest
    episode_rows: dict[str, dict[str, str]] = {}
    m2_spot_panel = panels["M2 VEA basket, spot only"]
    sources = {
        "US equity": (m2_spot_panel.months, m2_spot_panel.us_equity),
        "developed": (m2_spot_panel.months, m2_spot_panel.spot),
        "emerging": (em_panel.months, em_panel.spot),
        "DTWEXM": dollar["DTWEXM"],
        "DTWEXAFEGS": dollar["DTWEXAFEGS"],
    }
    for name, (episode_months, episode_values) in sources.items():
        for episode in episode_returns(
            episode_months, episode_values, windows={**STRESS_WINDOWS, **RECENT_EPISODES}
        ):
            cell = (
                "-"
                if not episode.covered
                else _pct(episode.cumulative_return) + ("*" if episode.partial else "")
            )
            episode_rows.setdefault(episode.window, {})[name] = cell
    for window, (first, last) in {**STRESS_WINDOWS, **RECENT_EPISODES}.items():
        cells = episode_rows.get(window, {})
        print(
            f"| {window} | {first}..{last} | {cells.get('US equity', '-')} | "
            f"{cells.get('developed', '-')} | {cells.get('emerging', '-')} | "
            f"{cells.get('DTWEXM', '-')} | {cells.get('DTWEXAFEGS', '-')} |"
        )
    print(
        "\n`*` the panel covers the window only in part. `-` means the panel does not "
        "reach the window at all, which is the most important thing a stress row can "
        "say: no free currency series in this repository sees 1929, 1937 or 1973.\n"
    )

    print("## 5. The currency leg by period\n")
    print("| slice | developed basket | DTWEXAFEGS | DTWEXM |")
    print("| --- | ---: | ---: | ---: |")
    m2 = panels["M2 VEA basket, spot only"]
    for label, first, last in RECENT_SLICES:
        columns = []
        for slice_months, slice_values in (
            (m2.months, m2.spot),
            dollar["DTWEXAFEGS"],
            dollar["DTWEXM"],
        ):
            take = _slice(slice_months, slice_values, first, last)
            columns.append(_pct(_cumulative(take)) if take.size else "-")
        print(f"| {label} cumulative | {columns[0]} | {columns[1]} | {columns[2]} |")
    print()
    print("| decade | developed basket pp/yr | DTWEXM pp/yr | DTWEXAFEGS pp/yr |")
    print("| --- | ---: | ---: | ---: |")
    for decade in range(1970, 2030, 10):
        first, last = f"{decade}-01", f"{decade + 9}-12"
        columns = []
        for slice_months, slice_values in (
            (m2.months, m2.spot),
            dollar["DTWEXM"],
            dollar["DTWEXAFEGS"],
        ):
            take = _slice(slice_months, slice_values, first, last)
            columns.append(
                _pct(float(np.mean(take)) * MONTHS_PER_YEAR) if take.size >= 24 else "-"
            )
        print(f"| {decade}s | {columns[0]} | {columns[1]} | {columns[2]} |")
    print()

    print("## 6. Per-currency spot, and today's interest differential\n")
    print(
        "| currency | basket weight | spot mean pp/yr | spot vol % | "
        "latest 3m interbank % | USD minus foreign pp |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    domestic, _ = _monthly_rate(cache, USD_INTERBANK)
    latest_usd_month = max(domestic)
    latest_usd = domestic[latest_usd_month]
    m2 = panels["M2 VEA basket, spot only"]
    latest_foreign: dict[str, tuple[str, float]] = {}
    for currency, series_id in DEVELOPED_INTERBANK.items():
        rates, _ = _monthly_rate(cache, series_id)
        month = max(rates)
        latest_foreign[currency] = (month, rates[month])
    for currency in DEVELOPED_WEIGHTS:
        series = m2.per_currency_spot.get(currency)
        month, rate = latest_foreign[currency]
        weight = DEVELOPED_WEIGHTS.get(currency)
        spot_mean = "-" if series is None else _pct(float(np.mean(series)) * MONTHS_PER_YEAR)
        spot_vol = (
            "-"
            if series is None
            else _plain(float(np.std(series, ddof=1)) * math.sqrt(MONTHS_PER_YEAR))
        )
        label = currency if weight is not None else f"{currency} (not in basket)"
        print(
            f"| {label} | {'-' if weight is None else f'{weight:.3f}'} | {spot_mean} | "
            f"{spot_vol} | {rate * PERCENT:.2f} ({month}) | "
            f"{(latest_usd - rate) * PERCENT:+.2f} |"
        )
    print(f"| USD | - | - | - | {latest_usd * PERCENT:.2f} ({latest_usd_month}) | - |")
    weighted = sum(
        weight * (latest_usd - latest_foreign[currency][1])
        for currency, weight in DEVELOPED_WEIGHTS.items()
    ) / sum(DEVELOPED_WEIGHTS.values())
    print(
        f"\nWeighted developed hedging carry, latest available month of each rate: "
        f"{_pct(weighted)} pp/yr **before** the cross-currency basis and before any "
        f"fund fee. A positive number means hedging currently pays.\n"
    )

    print(
        "| EM currency | spot mean pp/yr | spot vol % | latest 3m interbank % "
        "| USD minus foreign pp |"
    )
    print("| --- | ---: | ---: | ---: | ---: |")
    for currency in EMERGING_WEIGHTS:
        series = em_panel.per_currency_spot[currency]
        rate_cell, differential_cell = "-", "-"
        if currency in EMERGING_INTERBANK:
            rates, _ = _monthly_rate(cache, EMERGING_INTERBANK[currency])
            month = max(rates)
            rate_cell = f"{rates[month] * PERCENT:.2f} ({month})"
            differential_cell = f"{(latest_usd - rates[month]) * PERCENT:+.2f}"
        print(
            f"| {currency} | {_pct(float(np.mean(series)) * MONTHS_PER_YEAR)} | "
            f"{_plain(float(np.std(series, ddof=1)) * math.sqrt(MONTHS_PER_YEAR))} | "
            f"{rate_cell} | {differential_cell} |"
        )
    print()

    print("## 7. Effective sample size of the currency leg\n")
    print("| panel | n | effective n | ratio |")
    print("| --- | ---: | ---: | ---: |")
    for name, region in panels.items():
        n = region.currency_excess.size
        effective = effective_sample_size(region.currency_excess)
        print(f"| {name} | {n} | {effective:.0f} | {effective / n:.2f} |")
    print()

    print("## Source digests\n")
    for key in sorted(all_digests):
        print(f"- `{key}` sha256 `{all_digests[key][:16]}`")


if __name__ == "__main__":  # pragma: no cover
    main()
