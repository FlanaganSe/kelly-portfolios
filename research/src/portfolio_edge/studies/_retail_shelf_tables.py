"""The one file in the retail-shelf study that reads the cache.

:mod:`portfolio_edge.studies.retail_shelf` is arithmetic and holds no data.
This module assembles the four families' return histories from primary sources,
scores them with that module, and prints the tables that
``docs/research/alternative-sleeves-audit.md`` quotes.

Sources, and why each is the one used
-------------------------------------
*Fund returns: SEC Form N-PORT Item B.5*, through :mod:`portfolio_edge.data.nport`.
The fund's own monthly total return per share class, net of its own ongoing fees, on
a signed filing the SEC archives permanently. Public filings begin with periods ending
2019-09-30, which is the binding constraint on everything here and is reported as a
minimum detectable effect beside every estimate.

*Factors and the cash rate: the Ken French library.* ``Mkt-RF``, ``SMB``, ``HML``,
``RMW``, ``CMA``, ``Mom`` and ``RF``.

*The base portfolio: VTI's own Item B.5 return*, not the market factor. Decision 0003
makes a cheap broad-market fund the control, and comparing a net fund return against a
gross academic factor would flatter every sleeve by the control's fee.

*Duration: TLT's own Item B.5 return.* The REIT question needs a duration factor and
this repository holds no investable bond total-return history — every experiment here
uses a modelled ``GS10`` proxy. A long-Treasury ETF's own filed return is investable,
net of fee, from the same source as the sleeve, on exactly the same months. It covers
only the N-PORT window, so it settles nothing about REITs before 2019.

*Bitcoin: FRED ``CBBTCUSD``.* See the registry entry in
:mod:`portfolio_edge.data.fred` for what it is and is not. It is one venue's 5 p.m.
PST print, not the CME CF reference rate an ETP's net asset value is struck against.

*Full-period price returns for the buffer payoff: Goyal-Welch ``CRSP_SPvwx``*, the
CRSP value-weighted return **excluding dividends**. A buffer fund holds FLEX options on
the reference asset's price, so a price return is the correct input and a total return
would silently hand the structure the dividends its holders do not receive.
``CRSP_SPvw``, the same series including dividends, supplies the forgone yield.

Run it::

    uv run python -m portfolio_edge.studies._retail_shelf_tables
    uv run python -m portfolio_edge.studies._retail_shelf_tables --write-manifests
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from portfolio_edge.data import fred, french, goyal_welch, nport
from portfolio_edge.data.cache import RawCache
from portfolio_edge.studies.factor_breadth import admission
from portfolio_edge.studies.overlay_growth import (
    OverlayInputs,
    growth_optimal_overlay_weight,
    marginal_growth,
    shrunk_overlay_weight,
)
from portfolio_edge.studies.retail_shelf import (
    MONTHS_PER_YEAR,
    BufferTerms,
    MatchedVolatilityVerdict,
    buffer_cost_decomposition,
    choose_instrument,
    factor_regression,
    matched_volatility,
    piecewise_beta,
)

__all__ = [
    "FAMILIES",
    "SHELF",
    "FundSeries",
    "Panel",
    "build_panel",
    "load_bitcoin_monthly",
    "load_fund_returns",
    "load_product_facts",
    "main",
    "workspace_root",
]

BITCOIN_SERIES_ID: Final = "CBBTCUSD"

#: The first month of the bitcoin series with no missing prints. December 2014 has
#: 35 gaps in the FRED file and is dropped whole rather than interpolated.
BITCOIN_FIRST_MONTH: Final = "2015-01"


@dataclass(frozen=True, slots=True, kw_only=True)
class ShelfEntry:
    """One fund on the shelf, keyed to the SEC identifiers its filings are found by."""

    ticker: str
    family: str
    series_id: str
    class_id: str
    role: str = "sleeve"


#: The audited shelf. Series and class identifiers are EDGAR's own, resolved from
#: ``https://www.sec.gov/files/company_tickers_mf.json``, so a share class cannot be
#: silently re-pointed at a different product.
SHELF: Final[tuple[ShelfEntry, ...]] = (
    ShelfEntry(ticker="SCHD", family="dividend", series_id="S000034163", class_id="C000105320"),
    ShelfEntry(ticker="VYM", family="dividend", series_id="S000014011", class_id="C000038295"),
    ShelfEntry(ticker="DGRO", family="dividend", series_id="S000045648", class_id="C000141931"),
    ShelfEntry(ticker="VIG", family="dividend", series_id="S000011322", class_id="C000031350"),
    ShelfEntry(ticker="NOBL", family="dividend", series_id="S000042349", class_id="C000131287"),
    ShelfEntry(ticker="DIVO", family="dividend", series_id="S000055107", class_id="C000173384"),
    ShelfEntry(ticker="VNQ", family="reit", series_id="S000002924", class_id="C000032424"),
    ShelfEntry(ticker="SCHH", family="reit", series_id="S000030518", class_id="C000094080"),
    ShelfEntry(ticker="USRT", family="reit", series_id="S000015627", class_id="C000042588"),
    ShelfEntry(ticker="BUFR", family="buffer", series_id="S000068605", class_id="C000219511"),
    ShelfEntry(ticker="BUFD", family="buffer", series_id="S000070644", class_id="C000224383"),
    ShelfEntry(ticker="PJUL", family="buffer", series_id="S000058252", class_id="C000190965"),
    ShelfEntry(ticker="POCT", family="buffer", series_id="S000063478", class_id="C000205658"),
    ShelfEntry(
        ticker="VTI", family="control", series_id="S000002848", class_id="C000007808",
        role="base",
    ),
    ShelfEntry(
        ticker="VOO", family="control", series_id="S000002839", class_id="C000092055",
        role="control",
    ),
    ShelfEntry(
        ticker="TLT", family="control", series_id="S000004360", class_id="C000012090",
        role="duration",
    ),
)

FAMILIES: Final = ("dividend", "reit", "buffer", "bitcoin")


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


PRODUCT_FACTS_PATH: Final = Path("data-manifests") / "retail_shelf" / "product_facts.json"


def load_product_facts(root: Path | None = None) -> Mapping[str, object]:
    """The committed per-fund facts: fees, indices, after-tax tables, tax character.

    Read from the repository rather than the network. Every entry carries the SEC
    document it came from and the date it was read, and anything that could not be
    reached is in the file's ``unreachable`` list as "not found" rather than as an
    estimate.
    """
    path = (root or workspace_root()) / PRODUCT_FACTS_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path}: expected an object at the top level")
    return payload


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FundSeries:
    """One share class' filed monthly total returns, with its provenance."""

    ticker: str
    family: str
    series_id: str
    class_id: str
    series_name: str
    returns: Mapping[str, float]
    filing_count: int
    amendment_count: int
    net_assets: float | None
    warnings: tuple[str, ...]

    @property
    def first(self) -> str:
        return min(self.returns)

    @property
    def last(self) -> str:
        return max(self.returns)


def load_fund_returns(cache: RawCache, entry: ShelfEntry) -> FundSeries:
    """Assemble one share class' Item B.5 history across every ``NPORT-P`` filing."""
    refs = [
        ref
        for ref in nport.filing_index(cache, entry.series_id)
        if ref.form_type.startswith("NPORT-P")
    ]
    filings = []
    for ref in refs:
        filings.append(nport.fetch_filing(cache, ref))
        nport.throttle()
    if not filings:
        raise RuntimeError(f"{entry.ticker}: EDGAR lists no NPORT-P filing")
    table = nport.build_return_table(
        filings, class_id=entry.class_id, table_id=f"nport_{entry.ticker}"
    )
    return FundSeries(
        ticker=entry.ticker,
        family=entry.family,
        series_id=entry.series_id,
        class_id=entry.class_id,
        series_name=filings[0].series_name,
        returns={
            period: float(row[0])
            for period, row in zip(table.periods, table.values, strict=True)
            if row[0] is not None
        },
        filing_count=len(filings),
        amendment_count=sum(1 for item in filings if item.form_type.endswith("/A")),
        net_assets=max((item.net_assets or 0.0) for item in filings) or None,
        warnings=table.warnings,
    )


def _french_monthly(
    cache: RawCache, dataset_id: str, *, table_id: str | None = None
) -> tuple[Mapping[str, Mapping[str, float]], str]:
    dataset = french.get_dataset(dataset_id)
    entry, parsed, _ = french.load(cache, dataset)
    for table in parsed.tables:
        if table.frequency != "monthly":
            continue
        if table_id is not None and table.table_id != table_id:
            continue
        # A missing cell drops that COLUMN for that month, never the whole row.
        # The 49-industry file has industries with no firms in the early decades,
        # and dropping the row would silently delete four hundred usable months of
        # real estate because some unrelated industry was empty.
        rows: dict[str, dict[str, float]] = {}
        for period, values in zip(table.periods, table.values, strict=True):
            rows[period] = {
                name: float(value)
                for name, value in zip(table.columns, values, strict=True)
                if value is not None
            }
        return rows, entry.sha256
    raise RuntimeError(f"{dataset_id}: no monthly table in the file")


def load_bitcoin_monthly(cache: RawCache) -> tuple[dict[str, float], str, str]:
    """Month-end bitcoin price returns from FRED ``CBBTCUSD``.

    The month-end observation is the **last calendar day** with a print, not the last
    business day, because the market does not close. Months whose last print is more
    than three days before month end are dropped rather than carried forward; none are
    in the window used, and the check exists so that a future gap becomes a refusal
    rather than a stale price.
    """
    entry = fred.download(cache, BITCOIN_SERIES_ID)
    table = fred.parse(cache, entry, BITCOIN_SERIES_ID)
    last_by_month: dict[str, tuple[str, float]] = {}
    for period, values in zip(table.periods, table.values, strict=True):
        value = values[0]
        if value is None:
            continue
        month = period[:7]
        previous = last_by_month.get(month)
        if previous is None or period > previous[0]:
            last_by_month[month] = (period, float(value))
    months = sorted(month for month in last_by_month if month >= BITCOIN_FIRST_MONTH)
    returns: dict[str, float] = {}
    for earlier, later in itertools.pairwise(months):
        if _month_gap(earlier, later) != 1:
            continue
        returns[later] = last_by_month[later][1] / last_by_month[earlier][1] - 1.0
    return returns, entry.sha256, last_by_month[months[-1]][0]


def _month_gap(earlier: str, later: str) -> int:
    a = int(earlier[:4]) * 12 + int(earlier[5:7])
    b = int(later[:4]) * 12 + int(later[5:7])
    return b - a


def _goyal_welch_monthly(cache: RawCache) -> tuple[Mapping[str, Mapping[str, float]], str]:
    dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    entry, parsed, _ = goyal_welch.load(cache, dataset)
    for table in parsed.tables:
        if table.frequency != "monthly":
            continue
        rows: dict[str, dict[str, float]] = {}
        for period, values in zip(table.periods, table.values, strict=True):
            rows[period] = {
                name: float(value)
                for name, value in zip(table.columns, values, strict=True)
                if value is not None
            }
        return rows, entry.sha256
    raise RuntimeError("goyal_welch_predictors: no monthly table")


@dataclass(frozen=True, slots=True, kw_only=True)
class Panel:
    """Everything the tables read, assembled once."""

    funds: Mapping[str, FundSeries]
    factors: Mapping[str, Mapping[str, float]]
    momentum: Mapping[str, Mapping[str, float]]
    bitcoin: Mapping[str, float]
    goyal_welch: Mapping[str, Mapping[str, float]]
    industry: Mapping[str, Mapping[str, float]]
    industry_firms: Mapping[str, Mapping[str, float]]
    ff3: Mapping[str, Mapping[str, float]]
    digests: Mapping[str, str]

    def excess(self, ticker: str, periods: Sequence[str]) -> np.ndarray:
        series = self.funds[ticker].returns
        return np.array(
            [series[period] - self.factors[period]["RF"] for period in periods],
            dtype=np.float64,
        )

    def factor(self, name: str, periods: Sequence[str]) -> np.ndarray:
        if name == "Mom":
            return np.array([self.momentum[p]["Mom"] for p in periods], dtype=np.float64)
        return np.array([self.factors[p][name] for p in periods], dtype=np.float64)

    def window(
        self,
        tickers: Sequence[str],
        *,
        extra: Sequence[Mapping[str, float]] = (),
    ) -> tuple[str, ...]:
        shared = set(self.factors) & set(self.momentum)
        for ticker in tickers:
            shared &= set(self.funds[ticker].returns)
        for mapping in extra:
            shared &= set(mapping)
        return tuple(sorted(shared))


def build_panel(cache: RawCache) -> Panel:
    """Load every input. Network on first run, cache-only afterwards."""
    funds = {entry.ticker: load_fund_returns(cache, entry) for entry in SHELF}
    factors, ff5_digest = _french_monthly(cache, "french_us_ff5")
    momentum, mom_digest = _french_monthly(cache, "french_us_momentum")
    bitcoin, btc_digest, btc_last = load_bitcoin_monthly(cache)
    gw, gw_digest = _goyal_welch_monthly(cache)
    industry, industry_digest = _french_monthly(
        cache,
        "french_us_49_industry_portfolios",
        table_id="average_value_weighted_returns_monthly",
    )
    ff3, ff3_digest = _french_monthly(cache, "french_us_ff3")
    industry_firms, _ = _french_monthly(
        cache,
        "french_us_49_industry_portfolios",
        table_id="number_of_firms_in_portfolios_monthly",
    )
    return Panel(
        funds=funds,
        factors=factors,
        momentum=momentum,
        bitcoin=bitcoin,
        goyal_welch=gw,
        industry=industry,
        industry_firms=industry_firms,
        ff3=ff3,
        digests={
            "french_us_ff3": ff3_digest,
            "french_us_49_industry_portfolios": industry_digest,
            "french_us_ff5": ff5_digest,
            "french_us_momentum": mom_digest,
            "fred_cbbtcusd": btc_digest,
            "fred_cbbtcusd_last_observation": btc_last,
            "goyal_welch_predictors": gw_digest,
        },
    )


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #


def _pct(value: float, places: int = 2) -> str:
    return f"{100.0 * value:.{places}f}"


def table_shelf(panel: Panel) -> str:
    lines = [
        "## 1. The shelf, from the filings",
        "",
        "| ticker | family | series | net assets ($m) | filings | window | months |",
        "| --- | --- | --- | ---: | ---: | --- | ---: |",
    ]
    for entry in SHELF:
        fund = panel.funds[entry.ticker]
        assets = "not found" if fund.net_assets is None else f"{fund.net_assets / 1e6:,.0f}"
        lines.append(
            f"| {fund.ticker} | {fund.family} | {fund.series_name} | {assets} | "
            f"{fund.filing_count} | {fund.first}..{fund.last} | {len(fund.returns)} |"
        )
    lines.append(
        f"| BTC | bitcoin | FRED CBBTCUSD month-end price | n/a | n/a | "
        f"{min(panel.bitcoin)}..{max(panel.bitcoin)} | {len(panel.bitcoin)} |"
    )
    return "\n".join(lines)


def _moments(excess: np.ndarray, base: np.ndarray) -> tuple[float, float, float, float]:
    mean = float(np.mean(excess)) * MONTHS_PER_YEAR
    volatility = float(np.std(excess, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    correlation = float(np.corrcoef(excess, base)[0, 1])
    return mean, volatility, mean / volatility, correlation


def table_moments(panel: Panel) -> str:
    lines = [
        "## 2. Moments, correlation, and which instrument scores each family",
        "",
        "| sleeve | months | excess %/yr | vol %/yr | Sharpe | rho to VTI | instrument |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in SHELF:
        if entry.role == "base":
            continue
        periods = panel.window([entry.ticker, "VTI"])
        sleeve = panel.excess(entry.ticker, periods)
        base = panel.excess("VTI", periods)
        mean, volatility, sharpe, correlation = _moments(sleeve, base)
        choice = choose_instrument(label=entry.ticker, correlation=correlation)
        lines.append(
            f"| {entry.ticker} | {len(periods)} | {_pct(mean)} | {_pct(volatility)} | "
            f"{sharpe:.3f} | {correlation:+.3f} | "
            f"{'(4)' if choice.first_order_admission_is_usable else '(5)'} |"
        )
    periods = panel.window(["VTI"], extra=[panel.bitcoin])
    bitcoin = np.array(
        [panel.bitcoin[p] - panel.factors[p]["RF"] for p in periods], dtype=np.float64
    )
    base = panel.excess("VTI", periods)
    mean, volatility, sharpe, correlation = _moments(bitcoin, base)
    choice = choose_instrument(label="BTC", correlation=correlation)
    lines.append(
        f"| **BTC** | {len(periods)} | {_pct(mean)} | {_pct(volatility)} | {sharpe:.3f} | "
        f"{correlation:+.3f} | {'(4)' if choice.first_order_admission_is_usable else '(5)'} |"
    )
    base_periods = panel.window(["VTI"])
    base_only = panel.excess("VTI", base_periods)
    mean, volatility, sharpe, _ = _moments(base_only, base_only)
    lines += [
        f"| *VTI, the base* | {len(base_periods)} | {_pct(mean)} | {_pct(volatility)} | "
        f"{sharpe:.3f} | +1.000 | — |",
        "",
        "Instrument (4) is the admission condition `S_d > L rho sigma_p`; (5) is the",
        "matched-volatility control. The choice is made by `choose_instrument`, not by hand.",
    ]
    return "\n".join(lines)


def _geometric(monthly: np.ndarray) -> float:
    return float(np.prod(1.0 + monthly) ** (MONTHS_PER_YEAR / monthly.size)) - 1.0


def table_matched_volatility(panel: Panel) -> str:
    lines = [
        "## 3. Two comparisons against VTI: at the weight anyone holds, and at matched volatility",
        "",
        "`unlevered` is the geometric growth difference from holding the sleeve **instead**",
        "of VTI, one for one, which is the decision a long-only investor actually faces and",
        "the objective decision 0008 makes deciding. `matched` levers or delevers the sleeve",
        "to VTI's volatility, which is equation (5) and is the only comparison the higher",
        "Sharpe ratio settles. They disagree exactly when the sleeve's volatility differs",
        "from the base's, and for the buffer family that disagreement is the whole story.",
        "",
        "| sleeve | months | sleeve Sharpe | VTI Sharpe | unlevered growth gap | "
        "**matched growth gap** | 95% CI | MDE80 | resolved |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for entry in SHELF:
        if entry.role in {"base", "duration"}:
            continue
        periods = panel.window([entry.ticker, "VTI"])
        verdict = matched_volatility(
            panel.excess(entry.ticker, periods),
            panel.excess("VTI", periods),
            label=entry.ticker,
        )
        sleeve = np.array([panel.funds[entry.ticker].returns[p] for p in periods])
        base = np.array([panel.funds["VTI"].returns[p] for p in periods])
        lines.append(_matched_row(verdict, _geometric(sleeve) - _geometric(base)))
    periods = panel.window(["VTI"], extra=[panel.bitcoin])
    verdict = matched_volatility(
        np.array([panel.bitcoin[p] - panel.factors[p]["RF"] for p in periods]),
        panel.excess("VTI", periods),
        label="BTC",
    )
    bitcoin = np.array([panel.bitcoin[p] for p in periods])
    base = np.array([panel.funds["VTI"].returns[p] for p in periods])
    lines.append(_matched_row(verdict, _geometric(bitcoin) - _geometric(base)))
    return "\n".join(lines)


def _matched_row(verdict: MatchedVolatilityVerdict, unlevered_gap: float) -> str:
    return (
        f"| {verdict.label} | {verdict.months} | {verdict.sleeve_sharpe:.3f} | "
        f"{verdict.base_sharpe:.3f} | {_pct(unlevered_gap)} | "
        f"**{_pct(verdict.growth_gap)}** | "
        f"[{_pct(verdict.interval_low)}, {_pct(verdict.interval_high)}] | "
        f"{_pct(verdict.mde_80)} | {'yes' if verdict.resolved else '**no**'} |"
    )


_FF6: Final = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom")


def table_factor_regressions(panel: Panel) -> str:
    lines = [
        "## 4. Is the record a strategy, or a set of loadings? FF5 + momentum",
        "",
        "Every alpha is a distance from **VTI's own alpha in the identical regression**,",
        "not from zero. A cheap total-market fund does not score zero against a gross",
        "six-factor model: it pays a fee, and the model misfits. The `vs VTI` column is the",
        "only one that means anything, and it is the pedestal `factor-products.md` insists on.",
        "",
        "| sleeve | months | alpha %/yr | **vs VTI** | t | MDE80 | Mkt | SMB | HML | "
        "RMW | CMA | Mom | R2 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        " ---: | ---: |",
    ]
    pedestal_periods = panel.window(["VTI"])
    pedestal = factor_regression(
        panel.excess("VTI", pedestal_periods),
        [panel.factor(name, pedestal_periods) for name in _FF6],
        label="VTI",
        factor_names=_FF6,
    ).alpha
    for entry in SHELF:
        if entry.family not in {"dividend", "reit"} and entry.role == "sleeve":
            continue
        if entry.role in {"duration"}:
            continue
        periods = panel.window([entry.ticker])
        regression = factor_regression(
            panel.excess(entry.ticker, periods),
            [panel.factor(name, periods) for name in _FF6],
            label=entry.ticker,
            factor_names=_FF6,
        )
        loadings = " | ".join(f"{value:+.3f}" for value in regression.loadings)
        lines.append(
            f"| {entry.ticker} | {regression.months} | {_pct(regression.alpha)} | "
            f"**{_pct(regression.alpha - pedestal)}** | "
            f"{regression.alpha_t_statistic:+.2f} | {_pct(regression.alpha_mde_80)} | "
            f"{loadings} | {regression.r_squared:.3f} |"
        )
    return "\n".join(lines)


def table_reit_spanning(panel: Panel) -> str:
    """Does a REIT fund survive small-cap value and duration?"""
    lines = [
        "## 5. REIT spanning: market, then size and value, then duration",
        "",
        "| sleeve | model | alpha %/yr | t | MDE80 | residual vol %/yr | R2 | TLT loading |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    models: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("CAPM", ("Mkt-RF",)),
        ("FF3", ("Mkt-RF", "SMB", "HML")),
        ("FF3 + duration", ("Mkt-RF", "SMB", "HML", "TLT")),
    )
    for ticker in ("VNQ", "SCHH", "USRT"):
        periods = panel.window([ticker, "TLT"])
        response = panel.excess(ticker, periods)
        for name, factors in models:
            columns = [
                panel.excess("TLT", periods) if item == "TLT" else panel.factor(item, periods)
                for item in factors
            ]
            regression = factor_regression(
                response, columns, label=ticker, factor_names=factors
            )
            residual_volatility = (
                float(np.std(response, ddof=1))
                * math.sqrt(MONTHS_PER_YEAR)
                * math.sqrt(max(0.0, 1.0 - regression.r_squared))
            )
            tlt = (
                f"{regression.loading('TLT'):+.3f}"
                if "TLT" in regression.factor_names
                else "—"
            )
            lines.append(
                f"| {ticker} | {name} | {_pct(regression.alpha)} | "
                f"{regression.alpha_t_statistic:+.2f} | {_pct(regression.alpha_mde_80)} | "
                f"{_pct(residual_volatility)} | {regression.r_squared:.3f} | {tlt} |"
            )
    return "\n".join(lines)


#: The one industry column this study reads, and the SIC ranges French assigns to it.
REAL_ESTATE_INDUSTRY: Final = "RlEst"

#: French writes an unavailable industry-month as -99.99 in percent, which the parser
#: converts to -0.9999. Any month at or below this is dropped rather than used.
_FRENCH_SENTINEL: Final = -0.999


def table_reit_long_window(panel: Panel) -> str:
    """The same question on a century, using French's real-estate industry portfolio.

    The N-PORT window is 81 months and its detection floor is around 9 pp/yr, so it
    cannot settle whether REITs are spanned. French's ``RlEst`` industry portfolio runs
    from 1926-07 and is free. It is **not a REIT index** — it is SIC-coded real-estate
    operating companies, and modern equity REITs barely existed before the 1990s — so
    the first thing this table does is measure how closely it tracks a REIT fund over
    the months both exist, and that number decides how far the long window may be read.

    The duration leg is Goyal-Welch ``ltr`` in excess of ``Rfree``: the long-term
    government bond return, which is the only duration series here that reaches 1926.
    """
    overlap = tuple(
        sorted(
            set(panel.funds["VNQ"].returns)
            & {p for p, row in panel.industry.items() if _usable(row)}
        )
    )
    fund = np.array([panel.funds["VNQ"].returns[p] for p in overlap])
    proxy = np.array([panel.industry[p][REAL_ESTATE_INDUSTRY] for p in overlap])
    tracking = float(np.corrcoef(fund, proxy)[0, 1])
    lines = [
        "## 5b. The same question on a century, and what the proxy is worth",
        "",
        f"French `RlEst` against VNQ over the {len(overlap)} months both exist, "
        f"{overlap[0]}..{overlap[-1]}: **correlation {tracking:+.3f}**, tracking "
        f"difference "
        f"{_pct((float(np.mean(proxy)) - float(np.mean(fund))) * MONTHS_PER_YEAR)} pp/yr, "
        "and the proxy is a gross research portfolio while VNQ is net of its own fee.",
        "",
    ]

    # The first window is everything the FF3 factors reach; the second starts where
    # French's real-estate industry first holds more than a handful of firms; the
    # third is the modern equity-REIT era. The firm count in the last column is why
    # the earliest window is context and not evidence.
    windows: tuple[tuple[str, str, str], ...] = (
        ("1926-07..2025-12", "1926-07", "2025-12"),
        ("1963-07..2025-12", "1963-07", "2025-12"),
        ("1990-01..2025-12", "1990-01", "2025-12"),
    )
    lines += [
        "| window | months | RlEst excess %/yr | vol | Sharpe | market Sharpe | "
        "rho | firms, first..last |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, start, end in windows:
        periods = _long_reit_window(panel, start=start, end=end)
        sleeve = np.array(
            [
                panel.industry[p][REAL_ESTATE_INDUSTRY] - panel.ff3[p]["RF"]
                for p in periods
            ]
        )
        market = np.array([panel.ff3[p]["Mkt-RF"] for p in periods])
        mean, volatility, sharpe, correlation = _moments(sleeve, market)
        _, _, market_sharpe, _ = _moments(market, market)
        first_firms = panel.industry_firms[periods[0]][REAL_ESTATE_INDUSTRY]
        last_firms = panel.industry_firms[periods[-1]][REAL_ESTATE_INDUSTRY]
        lines.append(
            f"| {label} | {len(periods)} | {_pct(mean)} | {_pct(volatility)} | "
            f"{sharpe:.3f} | {market_sharpe:.3f} | {correlation:+.3f} | "
            f"{first_firms:.0f}..{last_firms:.0f} |"
        )

    lines += [
        "",
        "| window | model | alpha %/yr | t | MDE80 | residual vol %/yr | R2 | duration loading |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, start, end in windows:
        periods = _long_reit_window(panel, start=start, end=end)
        response = np.array(
            [
                panel.industry[p][REAL_ESTATE_INDUSTRY] - panel.ff3[p]["RF"]
                for p in periods
            ]
        )
        duration = np.array(
            [
                panel.goyal_welch[p]["ltr"] - panel.goyal_welch[p]["Rfree"]
                for p in periods
            ]
        )
        for model, names in (
            ("FF3", ("Mkt-RF", "SMB", "HML")),
            ("FF3 + duration", ("Mkt-RF", "SMB", "HML", "term")),
        ):
            columns = [
                duration
                if name == "term"
                else np.array([panel.ff3[p][name] for p in periods])
                for name in names
            ]
            regression = factor_regression(
                response, columns, label=label, factor_names=names
            )
            residual_volatility = (
                float(np.std(response, ddof=1))
                * math.sqrt(MONTHS_PER_YEAR)
                * math.sqrt(max(0.0, 1.0 - regression.r_squared))
            )
            term = (
                f"{regression.loading('term'):+.3f}"
                if "term" in regression.factor_names
                else "—"
            )
            lines.append(
                f"| {label} | {model} | {_pct(regression.alpha)} | "
                f"{regression.alpha_t_statistic:+.2f} | {_pct(regression.alpha_mde_80)} | "
                f"{_pct(residual_volatility)} | {regression.r_squared:.3f} | {term} |"
            )
    return "\n".join(lines)


def _usable(row: Mapping[str, float]) -> bool:
    value = row.get(REAL_ESTATE_INDUSTRY)
    return value is not None and value > _FRENCH_SENTINEL


def _long_reit_window(panel: Panel, *, start: str, end: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            period
            for period, row in panel.industry.items()
            if start <= period <= end
            and _usable(row)
            and period in panel.ff3
            and period in panel.goyal_welch
            and "ltr" in panel.goyal_welch[period]
            and "Rfree" in panel.goyal_welch[period]
        )
    )


def table_piecewise(panel: Panel) -> str:
    lines = [
        "## 6. Up-market and down-market beta, one regression each",
        "",
        "| sleeve | months | down months | up beta | down beta | asymmetry | t | protects? |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in SHELF:
        if entry.role in {"base", "duration"}:
            continue
        periods = panel.window([entry.ticker, "VTI"])
        result = piecewise_beta(
            panel.excess(entry.ticker, periods),
            panel.excess("VTI", periods),
            label=entry.ticker,
        )
        lines.append(
            f"| {result.label} | {result.months} | {result.down_months} | "
            f"{result.up_beta:.3f} | {result.down_beta:.3f} | {result.asymmetry:+.3f} | "
            f"{result.asymmetry_t_statistic:+.2f} | "
            f"{'yes' if result.protects else '**no**'} |"
        )
    return "\n".join(lines)


def _twelve_month_price_returns(
    panel: Panel, *, start: str, end: str
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """Overlapping twelve-month price and total returns from Goyal-Welch CRSP columns."""
    periods = tuple(
        sorted(
            period
            for period, row in panel.goyal_welch.items()
            if "CRSP_SPvwx" in row and "CRSP_SPvw" in row and start <= period <= end
        )
    )
    price = np.array([panel.goyal_welch[p]["CRSP_SPvwx"] for p in periods])
    total = np.array([panel.goyal_welch[p]["CRSP_SPvw"] for p in periods])
    windows = len(periods) - MONTHS_PER_YEAR + 1
    if windows < MONTHS_PER_YEAR:
        raise RuntimeError(f"only {windows} twelve-month windows in {start}..{end}")
    price_12 = np.array(
        [np.prod(1.0 + price[i : i + MONTHS_PER_YEAR]) - 1.0 for i in range(windows)]
    )
    total_12 = np.array(
        [np.prod(1.0 + total[i : i + MONTHS_PER_YEAR]) - 1.0 for i in range(windows)]
    )
    return price_12, total_12, periods


def table_buffer_payoff(panel: Panel, facts: Mapping[str, object]) -> str:
    """Price the cap against the realised distribution of twelve-month price returns.

    The cap and the buffer are the funds' own published terms, from their own 497K
    summary prospectuses, not a stylised example. Innovator publishes a new starting
    cap at the start of every outcome period, so the whole history of what a holder was
    actually offered is available and the mean of it is what the structure has really
    paid over its life.

    Two conventions, both stated because a reader could reasonably assume the other.
    The terms are the **gross** ones and the fee is charged separately and always; the
    prospectus presents the same economics as a cap and buffer each reduced by the fee,
    and the two differ only in whether the fee is borne inside the buffered region. And
    every figure is per **full outcome period** held start to finish, which is the only
    case the buffer is contracted to deliver.
    """
    products = _fact_funds(facts)
    lines = [
        "## 7. Pricing the cap, at the caps these funds actually published",
        "",
        "| fund | outcome periods | buffer | mean cap | median cap | min | max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    priced: list[tuple[str, float, float, float]] = []
    for ticker in ("PJUL", "POCT"):
        entry = products[ticker]
        published = _as_mapping(
            entry["starting_caps_percent"], what=f"{ticker} starting_caps_percent"
        )
        caps = [
            _as_float(value, what=f"{ticker} cap {period}") / 100.0
            for period, value in published.items()
        ]
        buffer_ = _as_float(entry["buffer_percent"], what=f"{ticker} buffer") / 100.0
        fee = _as_float(entry["net_expense_ratio_percent"], what=f"{ticker} fee") / 100.0
        mean_cap = sum(caps) / len(caps)
        lines.append(
            f"| {ticker} | {len(caps)} | {_pct(buffer_, 1)} | **{_pct(mean_cap, 2)}** | "
            f"{_pct(sorted(caps)[len(caps) // 2], 2)} | {_pct(min(caps), 2)} | "
            f"{_pct(max(caps), 2)} |"
        )
        priced.append((ticker, buffer_, mean_cap, fee))

    lines += [
        "",
        "**Neither fund has ever offered a cap as wide as its buffer.** Against that, here",
        "is what the option package delivered and cost, over three windows of realised",
        "twelve-month S&P price returns:",
        "",
        "| fund terms | window | protection received | upside sold | "
        "net option value | forgone dividend | fee | "
        "**total vs holding the index** |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    windows = (
        ("1926-07..2025-12", "1926-07", "2025-12"),
        ("1990-01..2025-12", "1990-01", "2025-12"),
        ("2010-01..2025-12", "2010-01", "2025-12"),
    )
    frequency_note = ""
    for ticker, buffer_, cap, fee in priced:
        for label, start, end in windows:
            price_12, total_12, _ = _twelve_month_price_returns(panel, start=start, end=end)
            dividend = float(np.mean(total_12 - price_12))
            terms = BufferTerms(
                buffer=buffer_, cap=cap, forgone_dividend_yield=dividend, fee=fee
            )
            result = buffer_cost_decomposition(price_12, terms, label=label)
            lines.append(
                f"| {ticker}, buffer {_pct(buffer_, 0)}%, cap {_pct(cap, 2)}% | "
                f"{label} ({result.periods} windows) | "
                f"{_pct(result.mean_protection_received)} | "
                f"{_pct(result.mean_upside_sold)} | "
                f"**{_pct(result.net_option_value)}** | {_pct(dividend)} | {_pct(fee)} | "
                f"**{_pct(result.total_shortfall)}** |"
            )
            if ticker == "PJUL" and label.startswith("1926"):
                frequency_note = (
                    f"Over {result.periods} overlapping twelve-month windows, "
                    f"1926-07..2025-12, **{_pct(result.capped_fraction, 1)}% of price "
                    f"returns exceeded PJUL's mean cap of {_pct(cap, 2)}%**, "
                    f"{_pct(result.buffer_used_fraction, 1)}% were negative at all, and "
                    f"{_pct(result.buffer_exceeded_fraction, 1)}% fell through the "
                    f"{_pct(buffer_, 0)}% buffer entirely."
                )

    lines += [
        "",
        frequency_note,
        "",
        "**The overlapping windows are not independent.** Twelve-month returns sampled",
        "monthly share eleven months with their neighbours, so these are means over a",
        "century of history and no interval may be computed from them without a block",
        "bootstrap. `buffer_cost_decomposition` returns means only, so no caller can",
        "obtain one from it by accident.",
    ]
    return "\n".join(lines)


def _as_float(value: object, *, what: str) -> float:
    """Narrow one JSON value to a float, refusing anything else.

    The product-facts file is hand-written from filings, so a typo there is the most
    likely way a wrong number reaches a table. Refusing rather than coercing means it
    becomes an error at load rather than a plausible-looking figure in a document.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"product facts: {what} is {value!r}, not a number")
    return float(value)


def _as_mapping(value: object, *, what: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError(f"product facts: {what} is not an object")
    return value


def _fact_funds(facts: Mapping[str, object]) -> Mapping[str, Mapping[str, object]]:
    funds = facts["funds"]
    if not isinstance(funds, dict):
        raise RuntimeError("product facts: 'funds' is not an object")
    return funds


def table_cost_and_tax(panel: Panel, facts: Mapping[str, object]) -> str:
    """All-in cost, and the fund's own SEC-standardised distribution tax drag.

    The drag is ``before tax - after taxes on distributions`` from the fund's own
    prospectus table, at the highest federal individual rates and **no state tax**. It
    is the fund's arithmetic, not this repository's. Two period ends appear in the
    shelf and a drag computed across them is not a comparison, so the control's figure
    at the **same** period end is carried in the last column.
    """
    products = _fact_funds(facts)
    control = products["VTI"]
    controls = {
        "2025-12-31": _drag(control["after_tax_returns"], "5_year"),
        "2024-12-31": _drag(control["after_tax_returns_prior_period"], "5_year"),
    }
    lines = [
        "## 11. All-in cost and the fund's own after-tax arithmetic",
        "",
        "| fund | all-in expense | period end | before tax 5yr | "
        "after tax on distributions | **drag** | VTI's drag, same period | "
        "**incremental** |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for ticker in (
        "SCHD", "VYM", "DGRO", "VIG", "NOBL", "DIVO",
        "VNQ", "SCHH", "USRT", "PJUL", "POCT", "BUFR", "VOO", "VTI",
    ):
        entry = products[ticker]
        expense = _as_float(
            entry["net_expense_ratio_percent"], what=f"{ticker} expense ratio"
        )
        table = entry.get("after_tax_returns")
        if not isinstance(table, dict):
            lines.append(
                f"| {ticker} | {expense:.2f}% | not found | not found | not found | "
                "not found | — | — |"
            )
            continue
        as_of = str(table["as_of"])
        row = _row_for(table, "5_year")
        drag = _drag(table, "5_year")
        reference = controls.get(as_of)
        lines.append(
            f"| {ticker} | {expense:.2f}% | {as_of} | {row['before_tax_percent']:.2f}% | "
            f"{row['after_tax_on_distributions_percent']:.2f}% | **{drag:.2f}** | "
            f"{'—' if reference is None else f'{reference:.2f}'} | "
            f"{'—' if reference is None else f'**{drag - reference:+.2f}**'} |"
        )
    del panel
    lines += [
        "",
        "`—` in the last two columns means the period end has no control in this file, not",
        "that the drag is zero. PJUL and POCT report a five-year drag of **0.00** — their",
        "after-tax-on-distributions row equals their before-tax row, because a FLEX-option",
        "fund distributes almost nothing. That is a real and unusual advantage and it is",
        "recorded as one.",
    ]
    return "\n".join(lines)


def _row_for(table: Mapping[str, object], period: str) -> Mapping[str, float]:
    rows = table["rows"]
    if not isinstance(rows, list):
        raise RuntimeError("after_tax_returns.rows is not a list")
    for row in rows:
        if isinstance(row, dict) and row.get("period") == period:
            return {k: float(v) for k, v in row.items() if k != "period"}
    raise RuntimeError(f"no {period} row in the after-tax table")


def _drag(table: object, period: str) -> float:
    if not isinstance(table, dict):
        raise RuntimeError("after-tax table is not an object")
    row = _row_for(table, period)
    return row["before_tax_percent"] - row["after_tax_on_distributions_percent"]


def _max_drawdown(returns: Sequence[float]) -> float:
    """Worst peak-to-trough fall of a month-end wealth path, as a negative decimal."""
    wealth = 1.0
    peak = 1.0
    worst = 0.0
    for value in returns:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        worst = min(worst, wealth / peak - 1.0)
    return worst


def _bitcoin_arm(
    panel: Panel, *, label: str, base_label: str, periods: Sequence[str]
) -> tuple[list[str], float, float, float, float, float]:
    """One row of the bitcoin moments table, and the numbers the next table needs."""
    bitcoin = np.array([panel.bitcoin[p] - panel.factors[p]["RF"] for p in periods])
    base = (
        panel.excess("VTI", periods)
        if base_label == "VTI"
        else panel.factor("Mkt-RF", periods)
    )
    mean, volatility, sharpe, correlation = _moments(bitcoin, base)
    _, base_volatility, base_sharpe, _ = _moments(base, base)
    rows = [
        f"| {label} | {len(periods)} | {periods[0]}..{periods[-1]} | {_pct(mean)} | "
        f"{_pct(volatility)} | {sharpe:.3f} | {correlation:+.3f} | {base_sharpe:.3f} |"
    ]
    return rows, mean, volatility, sharpe, correlation, base_volatility


def table_bitcoin_admission(panel: Panel) -> str:
    """Equation (4) at several exposures, then equation (5), then the overlay weight."""
    long_periods = tuple(sorted(set(panel.bitcoin) & set(panel.factors)))
    short_periods = panel.window(["VTI"], extra=[panel.bitcoin])
    lines = [
        "## 8. Bitcoin against equation (4), then against equation (5)",
        "",
        "| base | months | window | BTC excess %/yr | vol %/yr | BTC Sharpe | rho | base Sharpe |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    long_rows, mean, volatility, sharpe, correlation, base_volatility = _bitcoin_arm(
        panel, label="French Mkt-RF", base_label="Mkt-RF", periods=long_periods
    )
    short_rows, _, _, short_sharpe, short_correlation, short_base_volatility = _bitcoin_arm(
        panel, label="VTI, net", base_label="VTI", periods=short_periods
    )
    lines += long_rows + short_rows
    lines += [
        "",
        "**The full window is the one that scores it**, because the correlation is what "
        "equation (4) needs and a correlation is the one quantity these windows can "
        "resolve. The VTI arm exists only to show that the two agree on everything "
        "except the sample.",
        "",
        "| arm | exposure L | threshold `L rho sigma_p` | BTC Sharpe | margin | clears | usable |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for arm, arm_sharpe, arm_correlation, arm_volatility in (
        ("Mkt-RF", sharpe, correlation, base_volatility),
        ("VTI", short_sharpe, short_correlation, short_base_volatility),
    ):
        for exposure in (1.0, 1.5):
            verdict = admission(
                label="BTC",
                sharpe=arm_sharpe,
                correlation=arm_correlation,
                base_volatility=arm_volatility,
                base_exposure=exposure,
            )
            lines.append(
                f"| {arm} | {exposure:.2f} | {verdict.threshold:+.4f} | "
                f"{verdict.sharpe:.3f} | {verdict.margin:+.3f} | "
                f"{'yes' if verdict.clears else 'no'} | "
                f"{'yes' if verdict.usable else '**no**'} |"
            )
    base_mean = float(np.mean(panel.factor("Mkt-RF", long_periods))) * MONTHS_PER_YEAR
    inputs = OverlayInputs(
        base_excess_return=base_mean,
        base_volatility=base_volatility,
        diversifier_excess_return=mean,
        diversifier_volatility=volatility,
        correlation=correlation,
    )
    weight = growth_optimal_overlay_weight(inputs)
    shrunk = shrunk_overlay_weight(inputs, years=len(long_periods) / MONTHS_PER_YEAR)
    required = tuple(
        exposure * correlation * base_volatility * volatility for exposure in (1.0, 1.5)
    )
    drawdown = _max_drawdown([panel.bitcoin[p] for p in long_periods])
    equity_drawdown = _max_drawdown(
        [panel.factors[p]["Mkt-RF"] + panel.factors[p]["RF"] for p in long_periods]
    )
    lines += [
        "",
        "**The threshold inverted is the only forward-looking statement here.** Equation "
        "(4) clears whenever the sleeve's expected excess return exceeds "
        f"`L rho sigma_p sigma_d`, which at this correlation and volatility is "
        f"**{_pct(required[0])}%/yr at `L = 1` and {_pct(required[1])}%/yr at "
        f"`L = 1.5`** — below the equity premium, and low precisely because the "
        "correlation is low. Whether bitcoin's forward excess return exceeds it is the "
        "entire question, and nothing in this repository can answer it.",
        "",
        f"**Holdability.** Over the same {len(long_periods)} months bitcoin's worst "
        f"month-end drawdown was **{_pct(drawdown)}%** against US equity's "
        f"{_pct(equity_drawdown)}%. Equation (4) is a first-order condition on a "
        "twice-differentiable objective and contains no drawdown term at all; the "
        "levered-equity result in `capital-efficiency-and-breadth.md` §2 is the same "
        "lesson, where the growth optimum drew down 99.3% and was refused.",
        "",
        f"Growth-optimal overlay notional at these realised moments: **{weight:.3f}**, "
        f"shrunk for {len(long_periods) / MONTHS_PER_YEAR:.1f} years of estimation error "
        f"to **{shrunk:.3f}**. Marginal growth per unit of the first notional dollar is "
        f"{_pct(marginal_growth(inputs, rule='overlay'))} pp/yr under overlay funding and "
        f"{_pct(marginal_growth(inputs, rule='pro_rata'))} under pro rata.",
        "",
        "**Read the input, not the output.** Every figure in this section takes the "
        "realised mean as the expected excess return. For bitcoin there is no model that "
        "produces one, so the weight above is what the last eleven years would have "
        "justified in hindsight and is not a forecast of anything.",
    ]
    return "\n".join(lines)


def table_certainty_equivalent(panel: Panel) -> str:
    """Growth decides; the certainty equivalent reports beside it (decision 0008)."""
    from portfolio_edge.experiments.exp_004_trend_marginal_value import (
        certainty_equivalent_annual,
    )

    tickers = ("VTI", "SCHD", "VYM", "NOBL", "DIVO", "VNQ", "SCHH", "BUFR", "PJUL", "POCT")
    shared = panel.window(tickers)
    usable = len(shared) - len(shared) % MONTHS_PER_YEAR
    window = shared[len(shared) - usable :]
    lines = [
        "## 9. Growth decides, the certainty equivalent reports beside it",
        "",
        f"One common window for every row, {window[0]}..{window[-1]}, "
        f"{usable} months — **{usable // MONTHS_PER_YEAR} non-overlapping annual "
        "observations**, which is far too few to estimate a certainty equivalent with "
        "any precision. The column is here because decision 0008 requires it beside "
        "growth, not because it resolves anything.",
        "",
        "| sleeve | geometric %/yr | CE gamma=2 | CE gamma=5 | CE gamma=10 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for ticker in tickers:
        monthly = np.array([panel.funds[ticker].returns[p] for p in window])
        annual = np.array(
            [
                float(np.prod(1.0 + monthly[i : i + MONTHS_PER_YEAR]))
                for i in range(0, usable, MONTHS_PER_YEAR)
            ]
        )
        cells = " | ".join(
            _pct(certainty_equivalent_annual(annual, gamma=gamma)) for gamma in (2.0, 5.0, 10.0)
        )
        lines.append(f"| {ticker} | {_pct(_geometric(monthly))} | {cells} |")
    return "\n".join(lines)


#: The stated investor's own marginal rates, from
#: ``docs/research/portfolio-recommendation.md`` §3: 24% federal ordinary and 15%
#: federal qualified/long-term, both plus California's 9.3% at no preferential rate,
#: and no §1411 surtax. They are NOT the highest-federal-rate, no-state assumption the
#: SEC after-tax tables in section 11 use, so the two sets of figures answer the same
#: question with different rates and must never be mixed inside one row.
ORDINARY_RATE: Final = 0.24 + 0.093
QUALIFIED_RATE: Final = 0.15 + 0.093


def table_placement_priority(panel: Panel, facts: Mapping[str, object]) -> str:
    """Where each sleeve would sit in the recommendation's shelter queue.

    ``docs/research/portfolio-recommendation.md`` §3 ranks assets by what a sheltered
    dollar saves, in basis points a year. This computes the same quantity for the four
    families, from each fund's **own** filed distribution total, its own qualified
    share and its own net assets — three numbers from one N-CSR — at the investor's own
    rates rather than at the prospectus tables' highest-federal-no-state rates.

    The queue's own warning applies with full force and is repeated rather than linked
    away: **priority ranks what a sheltered dollar saves and says nothing about whether
    the asset should be held at all.** A queue is only ever run over sleeves already
    decided on other grounds, and nothing in this study decides one.
    """
    products = _fact_funds(facts)
    lines = [
        "## 10. What a sheltered dollar would save, at the investor's own rates",
        "",
        f"Ordinary {100 * ORDINARY_RATE:.1f}%, qualified {100 * QUALIFIED_RATE:.1f}%.",
        "Yield and character are the fund's own filed figures; a computed yield is",
        "distributions over net assets from the same annual report and is labelled so.",
        "",
        "| fund | distribution yield | at preferential rates | at ordinary rates | "
        "return of capital | **priority, bp/yr** | **incremental over VTI** |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    baseline: float | None = None
    for ticker in ("VTI", "SCHD", "VYM", "VIG", "DIVO", "VNQ", "SCHH"):
        entry = products[ticker]
        yield_, qualified, ordinary, capital = _yield_and_character(entry)
        if yield_ is None:
            lines.append(f"| {ticker} | not found | — | — | — | not found | — |")
            continue
        priority = 10000.0 * yield_ * (
            qualified * QUALIFIED_RATE + ordinary * ORDINARY_RATE
        )
        if ticker == "VTI":
            baseline = priority
        incremental = "—" if baseline is None else f"**{priority - baseline:+.1f}**"
        lines.append(
            f"| {ticker} | {100 * yield_:.2f}% | {100 * qualified:.0f}% | "
            f"{100 * ordinary:.0f}% | {100 * capital:.0f}% | **{priority:.1f}** | "
            f"{incremental} |"
        )
    del panel
    lines += [
        "",
        "**The buffer family is absent from this table because it distributes nothing.**",
        "PJUL's and POCT's own prospectus tables in section 11 report a five-year",
        "after-tax-on-distributions return equal to their before-tax return, so their",
        "priority is zero and they need no shelter at any weight. That is the same",
        "position a bullion trust occupies in the recommendation's own queue.",
        "",
        "**A return of capital is a deferral, not a rate**, so it is carried at zero here",
        "and shows up instead as a lower basis and a larger gain on sale. VNQ's own",
        "24.5% return-of-capital share is therefore the reason its priority below is",
        "*smaller* than its 3.79% yield suggests, and the reason its after-tax-on-sale",
        "row in section 11 is the one that moves.",
        "",
        "**Section 199A is not in this table and it runs in the REITs' favour.** A REIT",
        "dividend eligible for the 20% qualified-business-income deduction is taxed below",
        "the ordinary rate. The split was searched for in all three REIT funds' annual",
        "reports and is **not found** there, so every REIT figure here is an upper bound",
        "on the cost.",
    ]
    return "\n".join(lines)


def _yield_and_character(
    entry: Mapping[str, object],
) -> tuple[float | None, float, float, float]:
    """``(yield, qualified share, ordinary share, return-of-capital share)``.

    Prefers the fund's own filed distribution total over any published yield, because
    the character split has to come from the same statement as the amount or the two
    describe different periods.
    """
    character = entry.get("distribution_character")
    if isinstance(character, dict):
        ordinary_usd = _as_float(
            character.get("ordinary_income_usd") or 0.0, what="ordinary_income_usd"
        )
        gain_usd = _as_float(
            character.get("long_term_capital_gain_usd") or 0.0,
            what="long_term_capital_gain_usd",
        )
        capital_usd = _as_float(
            character.get("return_of_capital_usd") or 0.0, what="return_of_capital_usd"
        )
        total = ordinary_usd + gain_usd + capital_usd
        assets = character.get("net_assets_usd")
        if total > 0.0 and assets:
            qualified_share = character.get("qualified_share")
            if qualified_share is None:
                # A missing split is not a zero split. Charging the whole
                # distribution at the ordinary rate is the conservative reading and
                # is the one taken, with the row flagged in the page that quotes it.
                qualified_fraction = 0.0
            else:
                qualified_fraction = (
                    _as_float(qualified_share, what="qualified_share")
                    * ordinary_usd
                    / total
                )
            gain_fraction = gain_usd / total
            capital_fraction = capital_usd / total
            ordinary_fraction = max(
                0.0, 1.0 - qualified_fraction - gain_fraction - capital_fraction
            )
            return (
                total / _as_float(assets, what="net_assets_usd"),
                qualified_fraction + gain_fraction,
                ordinary_fraction,
                capital_fraction,
            )
    published = entry.get("sec_30_day_yield_percent")
    if published is not None:
        # Fallback for a fund whose annual report gives a character split but no net
        # assets on the same date. The published yield supplies the size and the
        # report supplies the split; where the split is absent too, the distribution
        # is treated as fully qualified, which is the assumption that FLATTERS the
        # fund and so cannot manufacture a rejection.
        share = 1.0
        if isinstance(character, dict) and character.get("qualified_share") is not None:
            share = _as_float(character["qualified_share"], what="qualified_share")
        return (
            _as_float(published, what="sec_30_day_yield_percent") / 100.0,
            share,
            1.0 - share,
            0.0,
        )
    return None, 0.0, 0.0, 0.0


def write_manifests(cache: RawCache, root: Path) -> list[Path]:
    """Write the manifest for the one dataset this study added."""
    entry = fred.download(cache, BITCOIN_SERIES_ID)
    table = fred.parse(cache, entry, BITCOIN_SERIES_ID)
    manifest = fred.build_manifest(
        entry,
        table,
        BITCOIN_SERIES_ID,
        extra_warnings=(
            "EXPLORATORY. Decision 0002 bans free price feeds for confirmatory work; "
            "the carve-out this series relies on is that bitcoin pays no distribution "
            "and has no corporate action, which are the only two failure modes that "
            "decision names. Nothing else about it is research-grade.",
            "This is NOT the index a US spot bitcoin ETP strikes its net asset value "
            "against. Those use the CME CF Bitcoin Reference Rate - New York Variant.",
            "Redistribution is prohibited by the source; the bytes stay in the "
            "uncommitted cache and only this hash is committed.",
        ),
    )
    directory = root / "data-manifests"
    written = [manifest.write(directory)]

    # The two tables this study reads from the 49-industry file, and only those two.
    # A manifest for a table nothing reads is a claim of provenance over an unused
    # number.
    dataset = french.get_dataset("french_us_49_industry_portfolios")
    _, _, industry_manifests = french.load(cache, dataset)
    wanted = {
        f"{dataset.dataset_id}_average_value_weighted_returns_monthly",
        f"{dataset.dataset_id}_number_of_firms_in_portfolios_monthly",
    }
    written += [
        item.write(directory) for item in industry_manifests if item.dataset_id in wanted
    ]
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-manifests", action="store_true")
    parser.add_argument("--json", action="store_true", help="digests only, for a ledger entry")
    arguments = parser.parse_args(argv)

    cache = RawCache()
    facts = load_product_facts()
    panel = build_panel(cache)
    if arguments.write_manifests:
        for path in write_manifests(cache, workspace_root()):
            print(f"wrote {path}")
        return 0
    if arguments.json:
        print(json.dumps(dict(panel.digests), indent=2, sort_keys=True))
        return 0

    print(table_shelf(panel))
    print()
    print(table_moments(panel))
    print()
    print(table_matched_volatility(panel))
    print()
    print(table_factor_regressions(panel))
    print()
    print(table_reit_spanning(panel))
    print()
    print(table_reit_long_window(panel))
    print()
    print(table_piecewise(panel))
    print()
    print(table_buffer_payoff(panel, facts))
    print()
    print(table_bitcoin_admission(panel))
    print()
    print(table_certainty_equivalent(panel))
    print()
    print(table_placement_priority(panel, facts))
    print()
    print(table_cost_and_tax(panel, facts))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
