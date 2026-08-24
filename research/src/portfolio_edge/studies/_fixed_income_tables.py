"""The one file in the fixed-income study that reads the cache.

:mod:`portfolio_edge.studies.fixed_income_shelf` is arithmetic and holds no data. This
module assembles the bond and TIPS histories from primary sources, scores them with
that module and :mod:`portfolio_edge.studies.retail_shelf`, and prints the tables
``docs/research/marginal-sleeve-value.md``, ``docs/research/setting-the-equity-share.md``
and ``docs/research/evidence-base.md`` quote.

Sources, and why each is the one used
-------------------------------------
*Fund returns: SEC Form N-PORT Item B.5*, through :mod:`portfolio_edge.data.nport`. The
fund's own monthly total return per share class, net of its own ongoing fees, on a
signed filing the SEC archives permanently. Public filings begin with periods ending
2019-09-30, which is the binding constraint on every investable figure here and is
reported as a minimum detectable effect beside every estimate.

*Fund costs: Form N-CEN*, through :mod:`portfolio_edge.data.ncen` and the shelf
machinery in :mod:`portfolio_edge.studies.core_beta_shelf`, which this module reuses
rather than copies. Securities-lending income accruing to shareholders (Item C.6),
expense-limitation and recoupment flags (Item C.8), and the tracking difference against
the fund's own index (Item C.3.b) -- the last of which may only be compared **within**
an index, never across.

*Expense ratios and waivers: the funds' own Form 497K fee tables*, read by hand into
``data-manifests/fixed_income_shelf/product_facts.json`` with the accession number and
the prospectus date beside every figure. Anything that could not be reached is in that
file's ``unreachable`` list as "not found" rather than as an estimate.

*The long measured bond leg: Goyal-Welch ``ltr`` and ``corpr``*, monthly total returns
on long-term US government and long-term investment-grade corporate bonds, 1926-01
onward, excess of the same file's ``Rfree``. Not investable and gross of any fee. This
is the series that replaces the modelled ``GS10`` proxy as a *measurement*; the funds
replace it as an *investable* series; neither replaces it as both.

*The real yield curve: FRED ``FII10``*, the ten-year real constant-maturity Treasury
yield, monthly from 2003-01, with ``CPIAUCNS`` supplying the reference index. Used only
where a TIPS history longer than the funds' six years is needed, and always labelled
modelled.

*The base portfolio: VTI's own Item B.5 return* on the investable window and Ken
French's regional market returns on the long one. Decision 0003 makes a cheap
broad-market fund the control.

Run it::

    uv run python -m portfolio_edge.studies._fixed_income_tables
    uv run python -m portfolio_edge.studies._fixed_income_tables --build-ncen
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from portfolio_edge.data import fred, french, goyal_welch, nport
from portfolio_edge.data.cache import RawCache, default_cache_root
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.studies.core_beta_shelf import (
    ShelfFund,
    build_ncen_manifest,
    summarise,
)
from portfolio_edge.studies.factor_breadth import admission, minimum_detectable_effect
from portfolio_edge.studies.fixed_income_shelf import (
    FIXED_INCOME_SHELF,
    ShelfEntry,
    annualised,
    correlation_stability,
    correlation_standard_error,
    par_bond_total_returns,
    tips_nominal_total_return,
)
from portfolio_edge.studies.overlay_growth import (
    FundingRule,
    OverlayInputs,
    marginal_growth,
    matched_volatility_verdict,
)
from portfolio_edge.studies.retail_shelf import (
    MONTHS_PER_YEAR,
    choose_instrument,
    matched_volatility,
)

__all__ = [
    "NCEN_MANIFEST_PATH",
    "PRODUCT_FACTS_PATH",
    "Panel",
    "build_panel",
    "load_fund_returns",
    "load_product_facts",
    "main",
    "workspace_root",
]

NCEN_MANIFEST_PATH: Final = Path("data-manifests") / "fixed_income_shelf" / "ncen_costs.json"
PRODUCT_FACTS_PATH: Final = Path("data-manifests") / "fixed_income_shelf" / "product_facts.json"

#: Experiment 010's sample, so the bond leg is checked on the window whose result it
#: would change rather than on a window chosen here.
EXP_010_WINDOW: Final = ("1991-01", "2025-12")

#: The borrow spread charged on financed notional, matching the levered ladder in
#: ``docs/research/capital-efficiency-and-breadth.md`` §2.
BORROW_SPREAD: Final = 0.0060

#: A representative bond-ETF fee charged on overlay notional. The measured shelf runs
#: 0.03%-0.15%; the higher end is used so the overlay column is not flattered.
BOND_FUND_FEE: Final = 0.0015

#: The date §7c splits on. Chosen by eye from the block table and reported as such; the
#: blocks are the pre-specified statistic and this is a compact restatement of them.
ERA_BREAK: Final = "1998-07"

#: The block length for every correlation-stability table. Five years, fixed before the
#: series were seen, and stated in every table that reports one.
BLOCK_MONTHS: Final = 60


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FundSeries:
    """One share class' filed monthly total returns, with its provenance."""

    ticker: str
    family: str
    series_name: str
    returns: Mapping[str, float]
    filing_count: int
    amendment_count: int
    net_assets: float | None
    warnings: tuple[str, ...]


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


def load_product_facts(root: Path | None = None) -> Mapping[str, object]:
    """The committed per-fund fee facts, read from the repository rather than the network."""
    path = (root or workspace_root()) / PRODUCT_FACTS_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path}: expected an object at the top level")
    return payload


def _french_monthly(cache: RawCache, dataset_id: str) -> tuple[dict[str, dict[str, float]], str]:
    entry, parsed, _ = french.load(cache, french.get_dataset(dataset_id))
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
    raise RuntimeError(f"{dataset_id}: no monthly table in the file")


def _goyal_welch_monthly(cache: RawCache) -> tuple[dict[str, dict[str, float]], str]:
    entry, parsed, _ = goyal_welch.load(cache, goyal_welch.get_dataset("goyal_welch_predictors"))
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


def _fred_monthly(cache: RawCache, series_id: str) -> tuple[dict[str, float], str, str]:
    """Monthly observations by ``YYYY-MM``, plus the digest and the last observation date."""
    entry = fred.download(cache, series_id)
    table = fred.parse(cache, entry, series_id)
    out: dict[str, float] = {}
    last = ""
    for period, values in zip(table.periods, table.values, strict=True):
        if values[0] is None:
            continue
        out[period[:7]] = float(values[0])
        last = period
    return out, entry.sha256, last


def _fred_last_daily(cache: RawCache, series_id: str) -> tuple[str, float, str]:
    """The most recent non-missing daily print, its date, and the file digest."""
    entry = fred.download(cache, series_id)
    table = fred.parse(cache, entry, series_id)
    latest = ("", 0.0)
    for period, values in zip(table.periods, table.values, strict=True):
        if values[0] is None:
            continue
        latest = (period, float(values[0]))
    return latest[0], latest[1], entry.sha256


@dataclass(frozen=True, slots=True, kw_only=True)
class Panel:
    """Everything the tables read, assembled once."""

    funds: Mapping[str, FundSeries]
    us: Mapping[str, Mapping[str, float]]
    developed_ex_us: Mapping[str, Mapping[str, float]]
    emerging: Mapping[str, Mapping[str, float]]
    goyal_welch: Mapping[str, Mapping[str, float]]
    nominal_yield: Mapping[str, float]
    real_yield: Mapping[str, float]
    consumer_prices: Mapping[str, float]
    breakeven: tuple[str, float]
    nominal_ten_year: tuple[str, float]
    real_ten_year_daily: tuple[str, float]
    digests: Mapping[str, str]

    def fund_excess(self, ticker: str, months: Sequence[str]) -> np.ndarray:
        series = self.funds[ticker].returns
        return np.array(
            [series[month] - self.us[month]["RF"] for month in months], dtype=np.float64
        )

    def fund_window(self, tickers: Sequence[str]) -> tuple[str, ...]:
        shared = set(self.us)
        for ticker in tickers:
            shared &= set(self.funds[ticker].returns)
        return tuple(sorted(shared))


def build_panel(cache: RawCache) -> Panel:
    """Load every input. Network on first run, cache-only afterwards."""
    funds = {entry.ticker: load_fund_returns(cache, entry) for entry in FIXED_INCOME_SHELF}
    us, us_digest = _french_monthly(cache, "french_us_ff5")
    dev, dev_digest = _french_monthly(cache, "french_developed_ex_us_ff5")
    emerging, em_digest = _french_monthly(cache, "french_emerging_ff5")
    gw, gw_digest = _goyal_welch_monthly(cache)
    gs10, gs10_digest, _ = _fred_monthly(cache, "GS10")
    fii10, fii10_digest, fii10_last = _fred_monthly(cache, "FII10")
    cpi, cpi_digest, _ = _fred_monthly(cache, "CPIAUCNS")
    breakeven_date, breakeven, be_digest = _fred_last_daily(cache, "T10YIE")
    return Panel(
        funds=funds,
        us=us,
        developed_ex_us=dev,
        emerging=emerging,
        goyal_welch=gw,
        nominal_yield=gs10,
        real_yield=fii10,
        consumer_prices=cpi,
        breakeven=(breakeven_date, breakeven),
        nominal_ten_year=(max(gs10), gs10[max(gs10)]),
        real_ten_year_daily=(fii10_last, fii10[max(fii10)]),
        digests={
            "french_us_ff5": us_digest,
            "french_developed_ex_us_ff5": dev_digest,
            "french_emerging_ff5": em_digest,
            "goyal_welch_predictors": gw_digest,
            "fred_gs10": gs10_digest,
            "fred_fii10": fii10_digest,
            "fred_cpiaucns": cpi_digest,
            "fred_t10yie": be_digest,
        },
    )


# --------------------------------------------------------------------------- #
# Derived series
# --------------------------------------------------------------------------- #


def long_treasury_excess(panel: Panel) -> dict[str, float]:
    """Goyal-Welch ``ltr`` less ``Rfree``: long-term US government bonds, measured."""
    return {
        month: row["ltr"] - row["Rfree"]
        for month, row in panel.goyal_welch.items()
        if "ltr" in row and "Rfree" in row
    }


def long_corporate_excess(panel: Panel) -> dict[str, float]:
    """Goyal-Welch ``corpr`` less ``Rfree``: long-term US IG corporates, measured."""
    return {
        month: row["corpr"] - row["Rfree"]
        for month, row in panel.goyal_welch.items()
        if "corpr" in row and "Rfree" in row
    }


def standalone_credit(panel: Panel) -> dict[str, float]:
    """``corpr - ltr``: the credit leg with the duration taken out.

    A long corporate index and a long government index are not duration-matched, so
    this difference still carries a small duration residual. It is the closest thing to
    a standalone credit return this repository holds and it is labelled that way.
    """
    return {
        month: row["corpr"] - row["ltr"]
        for month, row in panel.goyal_welch.items()
        if "corpr" in row and "ltr" in row
    }


def modelled_nominal_excess(panel: Panel, *, maturity_years: float = 10.0) -> dict[str, float]:
    """The ``GS10`` par-bond proxy every existing bond result in this repository uses."""
    returns = par_bond_total_returns(panel.nominal_yield, maturity_years=maturity_years)
    return {
        month: value - panel.us[month]["RF"]
        for month, value in returns.items()
        if month in panel.us and "RF" in panel.us[month]
    }


def modelled_tips_excess(
    panel: Panel, *, maturity_years: float = 10.0, lag_months: int = 3
) -> dict[str, float]:
    """A modelled ten-year TIPS total return in nominal terms, excess of cash."""
    real = par_bond_total_returns(panel.real_yield, maturity_years=maturity_years)
    nominal = tips_nominal_total_return(real, panel.consumer_prices, lag_months=lag_months)
    return {
        month: value - panel.us[month]["RF"]
        for month, value in nominal.items()
        if month in panel.us and "RF" in panel.us[month]
    }


def global_equity_core(panel: Panel) -> dict[str, float]:
    """Experiment 010's base portfolio: 60/30/10 US / developed ex-US / emerging, excess.

    Monthly rebalanced, from the three regional market factors. Reproducing it here is
    the check that licenses comparing a bond leg against Experiment 010's published
    cells at all: its realised ``sigma_p**2`` must come back as the 2.171 pp/yr credit
    ceiling that experiment printed.
    """
    shared = set(panel.us) & set(panel.developed_ex_us) & set(panel.emerging)
    return {
        month: 0.6 * panel.us[month]["Mkt-RF"]
        + 0.3 * panel.developed_ex_us[month]["Mkt-RF"]
        + 0.1 * panel.emerging[month]["Mkt-RF"]
        for month in shared
        if "Mkt-RF" in panel.us[month]
        and "Mkt-RF" in panel.developed_ex_us[month]
        and "Mkt-RF" in panel.emerging[month]
    }


def _window(*series: Mapping[str, float], first: str = "", last: str = "zzzz") -> tuple[str, ...]:
    shared: set[str] | None = None
    for item in series:
        shared = set(item) if shared is None else shared & set(item)
    assert shared is not None
    return tuple(sorted(month for month in shared if first <= month <= last))


def _pct(value: float, places: int = 2) -> str:
    return f"{100.0 * value:.{places}f}"


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #


def table_shelf(panel: Panel) -> str:
    lines = [
        "## 1. The shelf, from the filings",
        "",
        "| ticker | family | exposure | net assets ($m) | filings | window | months |",
        "| --- | --- | --- | ---: | ---: | --- | ---: |",
    ]
    for entry in FIXED_INCOME_SHELF:
        fund = panel.funds[entry.ticker]
        months = sorted(fund.returns)
        assets = "not found" if fund.net_assets is None else f"{fund.net_assets / 1e6:,.0f}"
        lines.append(
            f"| {entry.ticker} | {entry.family} | {entry.exposure} | {assets} | "
            f"{fund.filing_count} | {months[0]}..{months[-1]} | {len(months)} |"
        )
    return "\n".join(lines)


def table_moments(panel: Panel) -> str:
    tickers = [entry.ticker for entry in FIXED_INCOME_SHELF if entry.role != "base"]
    months = panel.fund_window([*tickers, "VTI"])
    base = panel.fund_excess("VTI", months)
    base_mean, base_volatility = annualised(base)
    lines = [
        "## 2. Moments and the instrument, investable window",
        "",
        f"{len(months)} months, {months[0]}..{months[-1]}, every fund on the same months.",
        "Excess of Ken French `RF`. The instrument column is",
        "`retail_shelf.choose_instrument`'s, from the measured correlation, never by hand.",
        "",
        "| ticker | family | excess %/yr | vol %/yr | Sharpe | rho to VTI | SE(rho) | "
        "instrument | eq (4) margin |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for entry in FIXED_INCOME_SHELF:
        if entry.role == "base":
            continue
        sleeve = panel.fund_excess(entry.ticker, months)
        mean, volatility = annualised(sleeve)
        correlation = float(np.corrcoef(sleeve, base)[0, 1])
        choice = choose_instrument(label=entry.ticker, correlation=correlation)
        verdict = admission(
            label=entry.ticker,
            sharpe=mean / volatility,
            correlation=correlation,
            base_volatility=base_volatility,
            base_exposure=1.0,
        )
        lines.append(
            f"| {entry.ticker} | {entry.family} | {_pct(mean)} | {_pct(volatility)} | "
            f"{mean / volatility:.3f} | {correlation:+.3f} | "
            f"{correlation_standard_error(correlation, len(months)):.3f} | "
            f"{'(4)' if choice.first_order_admission_is_usable else '**(5)**'} | "
            f"{verdict.margin:+.3f}"
            f"{'' if choice.first_order_admission_is_usable else ' *(not a verdict)*'} |"
        )
    lines += [
        f"| *VTI, the base* | control | {_pct(base_mean)} | {_pct(base_volatility)} | "
        f"{base_mean / base_volatility:.3f} | +1.000 | — | — | — |",
        "",
        "**The shelf straddles the 0.5 first-order limit and the split is by family, not by",
        "sponsor.** Every nominal Treasury fund sits below it and equation (4) is usable;",
        "every TIPS fund sits above it and equation (4) is not. A study that had assumed one",
        "instrument for \"bonds\" would have mis-scored half of this shelf.",
    ]
    return "\n".join(lines)


def table_matched_volatility(panel: Panel) -> str:
    tickers = [entry.ticker for entry in FIXED_INCOME_SHELF if entry.role != "base"]
    months = panel.fund_window([*tickers, "VTI"])
    base = panel.fund_excess("VTI", months)
    lines = [
        "## 3. Equation (5): the sleeve against VTI at matched volatility",
        "",
        "Substitution, not addition: would holding this instead of VTI, levered to VTI's",
        "risk, have raised growth. `resolved` is the field to read before the sign.",
        "",
        "| ticker | growth gap pp/yr | HAC t | 95% interval | MDE80 | resolved |",
        "| --- | ---: | ---: | --- | ---: | --- |",
    ]
    for entry in FIXED_INCOME_SHELF:
        if entry.role == "base":
            continue
        verdict = matched_volatility(
            panel.fund_excess(entry.ticker, months), base, label=entry.ticker
        )
        lines.append(
            f"| {entry.ticker} | {_pct(verdict.growth_gap)} | {verdict.t_statistic:+.2f} | "
            f"`[{_pct(verdict.interval_low)}, {_pct(verdict.interval_high)}]` | "
            f"{_pct(verdict.mde_80)} | {'yes' if verdict.resolved else '**no**'} |"
        )
    return "\n".join(lines)


def table_engines(panel: Panel) -> str:
    order = [entry.ticker for entry in FIXED_INCOME_SHELF if entry.role != "base"]
    months = panel.fund_window([*order, "VTI"])
    matrix = np.array([panel.fund_excess(ticker, months) for ticker in order])
    correlations = np.corrcoef(matrix)
    lines = [
        "## 4. How many engines is this shelf?",
        "",
        f"Excess returns, {len(months)} months, {months[0]}..{months[-1]}.",
        "",
        "| | " + " | ".join(order) + " |",
        "| --- |" + " ---: |" * len(order),
    ]
    for row, ticker in enumerate(order):
        lines.append(
            f"| **{ticker}** | "
            + " | ".join(f"{correlations[row, column]:+.2f}" for column in range(len(order)))
            + " |"
        )
    pairs = [
        ("SCHP", "TIP"), ("SCHP", "GOVT"), ("SCHP", "BND"), ("SCHP", "VGIT"),
        ("SCHP", "TLT"), ("VTIP", "SCHO"), ("LTPZ", "VGLT"), ("LQD", "VGIT"),
        ("BND", "AGG"),
    ]
    lines += ["", "| pair | rho | reading |", "| --- | ---: | --- |"]
    index = {ticker: position for position, ticker in enumerate(order)}
    for left, right in pairs:
        value = correlations[index[left], index[right]]
        lines.append(
            f"| {left} / {right} | {value:+.3f} | "
            f"{'one engine' if abs(value) > 0.75 else 'partly distinct'} |"
        )
    return "\n".join(lines)


def table_long_bond_leg(panel: Panel) -> str:
    treasury = long_treasury_excess(panel)
    corporate = long_corporate_excess(panel)
    credit = standalone_credit(panel)
    proxy = modelled_nominal_excess(panel)
    lines = [
        "## 5. The long measured bond leg, and what the modelled proxy got wrong",
        "",
        "| series | source | months | window | excess %/yr | vol %/yr | Sharpe |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    named = (
        ("long Treasury `ltr`", "Goyal-Welch, measured", treasury),
        ("long IG corporate `corpr`", "Goyal-Welch, measured", corporate),
        ("credit `corpr - ltr`", "Goyal-Welch, measured", credit),
        ("10y par bond", "**modelled** from FRED `GS10`", proxy),
    )
    for label, source, series in named:
        months = sorted(series)
        mean, volatility = annualised([series[month] for month in months])
        lines.append(
            f"| {label} | {source} | {len(months)} | {months[0]}..{months[-1]} | "
            f"{_pct(mean)} | {_pct(volatility)} | {mean / volatility:.3f} |"
        )
    shared = _window(treasury, proxy)
    left = np.array([proxy[month] for month in shared])
    right = np.array([treasury[month] for month in shared])
    proxy_mean, proxy_volatility = annualised(left)
    measured_mean, measured_volatility = annualised(right)
    lines += [
        "",
        f"**On the {len(shared)} months both cover, {shared[0]}..{shared[-1]}, the modelled "
        f"proxy and the measured series correlate {float(np.corrcoef(left, right)[0, 1]):+.3f} "
        f"and are not the same exposure**: {_pct(proxy_volatility)}%/yr of volatility against "
        f"{_pct(measured_volatility)}%/yr, and {_pct(proxy_mean)}%/yr of excess return against "
        f"{_pct(measured_mean)}%/yr. `GS10` is a ten-year point and `ltr` is a roughly "
        "twenty-year index, so most of that gap is an exposure difference rather than an "
        "error in either. What it is not is interchangeable: a study that says \"bonds\" and "
        "means one of these has not said which.",
    ]
    return "\n".join(lines)


def table_exp_010_cells(panel: Panel) -> str:
    core = global_equity_core(panel)
    first, last = EXP_010_WINDOW
    candidates = {
        "**modelled** `GS10` 10y proxy — exp_010's own leg": modelled_nominal_excess(panel),
        "measured long Treasury `ltr`": long_treasury_excess(panel),
        "measured long IG corporate `corpr`": long_corporate_excess(panel),
        "measured standalone credit `corpr - ltr`": standalone_credit(panel),
    }
    months = _window(core, *candidates.values(), first=first, last=last)
    base = np.array([core[month] for month in months])
    base_mean, base_volatility = annualised(base)
    lines = [
        "## 6. Experiment 010's bond cell, recomputed on a measured series",
        "",
        f"`global_equity_core`, {len(months)} months {months[0]}..{months[-1]}, the sample",
        "Experiment 010 froze. Reproduction check: this pipeline puts the base at",
        f"`a_p` = {_pct(base_mean)}%/yr and `sigma_p` = {_pct(base_volatility)}%/yr, so the",
        f"credit ceiling `sigma_p**2` is **{_pct(base_volatility ** 2)} pp/yr per unit weight**",
        "against the +2.168 to +2.171 that experiment printed for its cash control and gold.",
        "",
        "First-order marginals at the 10% reference weight, without the block bootstrap the",
        "experiment ran, so these are a check on the leg and not a re-run of the experiment.",
        f"The financed column charges a {_pct(BORROW_SPREAD)}%/yr borrow spread -- the one",
        "`docs/research/capital-efficiency-and-breadth.md` uses -- plus a "
        f"{_pct(BOND_FUND_FEE)}%/yr fund fee on notional. The pro-rata column needs neither,",
        "because it sells the base rather than borrowing.",
        "",
        "| bond leg | excess %/yr | vol %/yr | beta to core | credit/unit | credit @10% | "
        "pro rata @10% | overlay @10%, free | overlay @10%, financed | MDE80 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, series in candidates.items():
        sleeve = np.array([series[month] for month in months])
        mean, volatility = annualised(sleeve)
        correlation = float(np.corrcoef(sleeve, base)[0, 1])
        inputs = OverlayInputs(
            base_excess_return=base_mean,
            base_volatility=base_volatility,
            diversifier_excess_return=mean,
            diversifier_volatility=volatility,
            correlation=correlation,
        )
        financed = OverlayInputs(
            base_excess_return=base_mean,
            base_volatility=base_volatility,
            diversifier_excess_return=mean,
            diversifier_volatility=volatility,
            correlation=correlation,
            financing_spread=BORROW_SPREAD,
            fee=BOND_FUND_FEE,
        )
        credit_per_unit = base_volatility**2 * (1.0 - inputs.beta)
        pro_rata = marginal_growth(inputs, rule=FundingRule.PRO_RATA) * 0.10
        overlay = marginal_growth(inputs, rule=FundingRule.OVERLAY) * 0.10
        overlay_net = marginal_growth(financed, rule=FundingRule.OVERLAY) * 0.10
        error = hac_mean(sleeve - base).standard_error * MONTHS_PER_YEAR
        lines.append(
            f"| {label} | {_pct(mean)} | {_pct(volatility)} | {inputs.beta:+.3f} | "
            f"{_pct(credit_per_unit, 3)} | {_pct(0.10 * credit_per_unit, 3)} | "
            f"{_pct(pro_rata, 3)} | {_pct(overlay, 3)} | {_pct(overlay_net, 3)} | "
            f"{_pct(minimum_detectable_effect(error) * 0.10, 3)} |"
        )
    lines += [
        "",
        "| bond leg | equation (5) at 10% overlay: portfolio Sharpe | base Sharpe | "
        "beats levered base |",
        "| --- | ---: | ---: | --- |",
    ]
    for label, series in candidates.items():
        sleeve = np.array([series[month] for month in months])
        mean, volatility = annualised(sleeve)
        inputs = OverlayInputs(
            base_excess_return=base_mean,
            base_volatility=base_volatility,
            diversifier_excess_return=mean,
            diversifier_volatility=volatility,
            correlation=float(np.corrcoef(sleeve, base)[0, 1]),
        )
        sizing = matched_volatility_verdict(inputs, weight=0.10)
        lines.append(
            f"| {label} | {sizing.portfolio_sharpe:.3f} | {sizing.base_sharpe:.3f} | "
            f"{'**yes**' if sizing.beats_leverage_matched_base else 'no'} |"
        )
    return "\n".join(lines)


def table_correlation_stability(panel: Panel) -> str:
    core_us = {
        month: row["Mkt-RF"] for month, row in panel.us.items() if "Mkt-RF" in row
    }
    series = {
        "long Treasury `ltr`, measured": long_treasury_excess(panel),
        "long IG corporate `corpr`, measured": long_corporate_excess(panel),
        "standalone credit `corpr - ltr`": standalone_credit(panel),
        "10y nominal par bond, **modelled** `GS10`": modelled_nominal_excess(panel),
        "10y TIPS, **modelled** `FII10`": modelled_tips_excess(panel),
    }
    lines = [
        "## 7. Is the correlation to equity stable? TIPS against nominal",
        "",
        f"US market excess return as the base. Non-overlapping {BLOCK_MONTHS}-month blocks,",
        "the length fixed before the series were seen. A trailing partial block is dropped.",
        "",
        "### 7a. Each series over its own full history",
        "",
        "| series | months | window | full-sample rho | blocks | span | sd | flips sign |",
        "| --- | ---: | --- | ---: | --- | ---: | ---: | --- |",
    ]
    for label, values in series.items():
        months = _window(values, core_us)
        stability = correlation_stability(
            values, core_us, months, label=label, block_months=BLOCK_MONTHS
        )
        lines.append(
            f"| {label} | {stability.months} | {months[0]}..{months[-1]} | "
            f"{stability.full_sample:+.3f} | "
            + " ".join(f"{value:+.2f}" for _, _, value in stability.blocks)
            + f" | {stability.span:.3f} | {stability.dispersion:.3f} | "
            f"{'**yes**' if stability.flips_sign else 'no'} |"
        )
    shared = _window(*series.values(), core_us)
    lines += [
        "",
        "### 7b. The only window in which TIPS and nominal both exist",
        "",
        f"{len(shared)} months, {shared[0]}..{shared[-1]}, identical months and identical",
        "block edges for every row, which is what makes the dispersion column comparable.",
        "",
        "| series | rho to equity | SE(rho) | blocks | span | sd |",
        "| --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for label, values in series.items():
        stability = correlation_stability(
            values, core_us, shared, label=label, block_months=BLOCK_MONTHS
        )
        lines.append(
            f"| {label} | {stability.full_sample:+.3f} | "
            f"{correlation_standard_error(stability.full_sample, len(shared)):.3f} | "
            + " ".join(f"{value:+.2f}" for _, _, value in stability.blocks)
            + f" | {stability.span:.3f} | {stability.dispersion:.3f} |"
        )
    tips = series["10y TIPS, **modelled** `FII10`"]
    nominal = series["10y nominal par bond, **modelled** `GS10`"]
    treasury = series["long Treasury `ltr`, measured"]
    left = np.array([tips[month] for month in shared])
    lines += [
        "",
        f"**TIPS against the nominal ten-year over the same months: rho = "
        f"{float(np.corrcoef(left, [nominal[m] for m in shared])[0, 1]):+.3f}.** Against the",
        "measured long Treasury: "
        f"{float(np.corrcoef(left, [treasury[m] for m in shared])[0, 1]):+.3f}.",
        "",
        "Sensitivity to the reference-CPI lag, which is the one modelling choice a TIPS",
        "return needs: at a zero-month lag instead of the statutory three, the correlation to",
        "equity reads "
        + f"{_lag_sensitivity(panel, core_us):+.3f}"
        + " on the months both variants cover.",
        "",
        "### 7c. The sign change, split at a date chosen by eye",
        "",
        f"**{ERA_BREAK} is not a pre-specified break.** It is where the block table above",
        "visibly changes sign, and a split chosen after looking at the blocks is a split",
        "chosen on the answer. The blocks are the statistic; this is the same thing said",
        "compactly, and it is reported as descriptive.",
        "",
        "| series | before | months | from | months |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, values in series.items():
        months = _window(values, core_us)
        before = [month for month in months if month < ERA_BREAK]
        after = [month for month in months if month >= ERA_BREAK]
        if len(before) < 4 or len(after) < 4:
            lines.append(f"| {label} | *no observation before {ERA_BREAK}* | 0 | — | — |")
            continue
        lines.append(
            f"| {label} | "
            f"{correlation_stability(values, core_us, before, label=label).full_sample:+.3f} | "
            f"{len(before)} | "
            f"{correlation_stability(values, core_us, after, label=label).full_sample:+.3f} | "
            f"{len(after)} |"
        )
    return "\n".join(lines)


def _lag_sensitivity(panel: Panel, base: Mapping[str, float]) -> float:
    zero_lag = modelled_tips_excess(panel, lag_months=0)
    months = _window(zero_lag, base)
    return float(
        np.corrcoef([zero_lag[month] for month in months], [base[month] for month in months])[0, 1]
    )


def table_investable_stability(panel: Panel) -> str:
    tickers = ["SCHP", "TIP", "VTIP", "GOVT", "VGIT", "TLT", "BND", "LQD"]
    months = panel.fund_window([*tickers, "VTI"])
    base = {
        month: value
        for month, value in zip(months, panel.fund_excess("VTI", months), strict=True)
    }
    lines = [
        "## 8. The same question on investable funds, where the window allows only halves",
        "",
        f"{len(months)} months, {months[0]}..{months[-1]}. Blocks of "
        f"{len(months) // 2} months, which is what the N-PORT window can carry; this is a",
        "consistency check on section 7 and not an independent era test.",
        "",
        "| ticker | rho to VTI | SE(rho) | first half | second half |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for ticker in tickers:
        values = {
            month: value
            for month, value in zip(months, panel.fund_excess(ticker, months), strict=True)
        }
        stability = correlation_stability(
            values, base, months, label=ticker, block_months=len(months) // 2
        )
        halves = [f"{value:+.3f}" for _, _, value in stability.blocks]
        lines.append(
            f"| {ticker} | {stability.full_sample:+.3f} | "
            f"{correlation_standard_error(stability.full_sample, len(months)):.3f} | "
            + " | ".join(halves)
            + " |"
        )
    return "\n".join(lines)


def table_breakeven(panel: Panel) -> str:
    breakeven_date, breakeven = panel.breakeven
    nominal_month, nominal = panel.nominal_ten_year
    real_month = max(panel.real_yield)
    real = panel.real_yield[real_month]
    return "\n".join(
        [
            "## 9. What a TIPS buyer is actually buying",
            "",
            "| quantity | value | as of | source |",
            "| --- | ---: | --- | --- |",
            f"| 10-year **real** constant-maturity yield | {_pct(real)}%/yr | {real_month} | "
            "FRED `FII10`, monthly average of Treasury's daily par real curve |",
            f"| 10-year **nominal** constant-maturity yield | {_pct(nominal)}%/yr | "
            f"{nominal_month} | FRED `GS10` |",
            f"| 10-year **breakeven** inflation | {_pct(breakeven)}%/yr | {breakeven_date} | "
            "FRED `T10YIE` |",
            f"| implied nominal return on the TIPS if inflation runs at the breakeven | "
            f"{_pct((1.0 + real) * (1.0 + breakeven) - 1.0)}%/yr | — | derived |",
            f"| the same breakeven from the two monthly averages, `GS10 - FII10` | "
            f"{_pct(nominal - real)}%/yr | {nominal_month} | derived |",
            "",
            "The two breakeven readings differ because they are taken on different dates and",
            "on different samplings -- `T10YIE` is a daily difference and the monthly series",
            "are averages of daily rates. Neither is corrected to the other.",
            "",
            "**The decision this makes explicit.** Buying the ten-year TIPS instead of the",
            "ten-year nominal note wins if and only if realised inflation exceeds",
            f"{_pct(breakeven)}%/yr over ten years. It is a **swap of one risk for another at a",
            "market-set price**, not a higher expected return: the breakeven already contains",
            "an inflation risk premium and a TIPS liquidity premium of unknown sign, so it is",
            "not a forecast and this table does not use it as one.",
        ]
    )


def table_costs(panel: Panel, root: Path) -> str:
    facts = load_product_facts(root)
    funds = facts.get("funds")
    if not isinstance(funds, dict):
        raise RuntimeError("product_facts.json carries no 'funds' object")
    manifest_file = root / NCEN_MANIFEST_PATH
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        shelf = tuple(
            ShelfFund(entry.ticker, entry.family, entry.registrant_cik)
            for entry in FIXED_INCOME_SHELF
        )
        lending = {row.ticker: row for row in summarise(manifest, shelf=shelf)}
    else:
        lending = {}
    lines = [
        "## 10. Total cost of ownership, not fee",
        "",
        "Expense ratios and waivers are from each fund's own Form 497K fee table, read by",
        "hand with the accession committed. Securities-lending income is Form N-CEN Item",
        "C.6.g over Item C.2's average net assets, in basis points a year, over every fiscal",
        "year on file. Net cost is the fee less the lending income; it can be negative.",
        "",
        "| ticker | gross fee bp | net fee bp | waiver | recoupable | lending bp (median) | "
        "net cost bp | prospectus |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for entry in FIXED_INCOME_SHELF:
        fact = funds.get(entry.ticker)
        if not isinstance(fact, dict):
            continue
        gross = fact.get("total_annual_operating_expenses_bp")
        net = fact.get("net_annual_operating_expenses_bp", gross)
        row = lending.get(entry.ticker)
        lend = row.lending_bp_median if row is not None else None
        if lend is not None:
            lending_cell = f"{lend:.2f}"
        elif row is not None:
            # The fund filed Item C.6.a "No" in every year on file. That is a
            # different fact from a missing filing and the table must not blur them.
            lending_cell = "does not lend"
        else:
            lending_cell = "not found"
        net_value = float(net) if isinstance(net, (int, float)) else None
        cost = None if net_value is None else net_value - (lend or 0.0)
        lines.append(
            f"| {entry.ticker} | {gross if gross is not None else 'not found'} | "
            f"{net if net is not None else 'not found'} | "
            f"{fact.get('waiver', 'not found')} | "
            f"{fact.get('recoupable', 'not found')} | "
            f"{lending_cell} | "
            f"{'not found' if cost is None else f'{cost:.2f}'} | "
            f"{fact.get('prospectus_date', 'not found')} |"
        )
    lines += [
        "",
        "### The exposure behind the wrapper",
        "",
        "A 3 bp fee is not the decision; what the fund is a claim on is. Index names and",
        "maturities are the prospectus's or the annual report's own words, and where the",
        "figure published is the **index's** rather than the fund's the row says so.",
        "",
        "| ticker | index | maturity or duration |",
        "| --- | --- | --- |",
    ]
    for entry in FIXED_INCOME_SHELF:
        fact = funds.get(entry.ticker)
        if not isinstance(fact, dict):
            continue
        index_name = str(fact.get("index", "not found"))
        if index_name == "not read":
            continue
        lines.append(
            f"| {entry.ticker} | {index_name} | {fact.get('maturity_or_duration', 'not found')} |"
        )
    unreachable = facts.get("unreachable")
    if isinstance(unreachable, list) and unreachable:
        lines += ["", "**Not found, recorded rather than estimated:**", ""]
        lines += [f"- {item}" for item in unreachable]
    return "\n".join(lines)


#: The FRED series this study added to the repository, with the warning each needs.
NEW_FRED_SERIES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "FII10",
        (
            "MODELLED USE ONLY. This is a yield, not a total return; the TIPS series in "
            "this study is a par bond priced off it and is labelled modelled wherever it "
            "appears.",
            "NOT INTERCHANGEABLE WITH GS10. One is real and one is nominal and their "
            "difference is a breakeven inflation rate, not a spread.",
            "The series is NEGATIVE in 45 of its 283 monthly observations, which is why "
            "portfolio_edge.studies.fixed_income_shelf.par_bond_risk exists beside the "
            "exp_010 copy that refuses a non-positive yield.",
            "DOCUMENTED METHODOLOGY BREAK at 2008-12-01: the Treasury's TIPS curve moved "
            "to the most recently auctioned issues as knot points. An era split near that "
            "date splits on a construction change as well as on an era.",
        ),
    ),
    (
        "T10YIE",
        (
            "A BREAKEVEN, NOT A FORECAST. It contains an inflation risk premium and a "
            "TIPS liquidity premium of unknown and time-varying sign. Nothing here "
            "predicts with it.",
        ),
    ),
    (
        "CPIAUCNS",
        (
            "This, not CPIAUCSL, is the index a TIPS principal references: 31 CFR 356.2 "
            "defines the CPI as the monthly non-seasonally adjusted CPI-U, and appendix B "
            "section I paragraph B applies it with a three-month lag.",
        ),
    ),
)


def write_manifests(cache: RawCache, root: Path) -> list[Path]:
    """Write the manifests for the datasets this study added."""
    directory = root / "data-manifests"
    written: list[Path] = []
    for series_id, warnings in NEW_FRED_SERIES:
        entry = fred.download(cache, series_id)
        table = fred.parse(cache, entry, series_id)
        written.append(
            fred.build_manifest(entry, table, series_id, extra_warnings=warnings).write(directory)
        )
    return written


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-ncen", action="store_true", help="refetch every N-CEN and rewrite the manifest"
    )
    parser.add_argument(
        "--write-manifests", action="store_true", help="write the manifests for the new datasets"
    )
    args = parser.parse_args(argv)
    root = workspace_root()
    cache = RawCache(default_cache_root())
    if args.build_ncen:
        shelf = tuple(
            ShelfFund(entry.ticker, entry.family, entry.registrant_cik)
            for entry in FIXED_INCOME_SHELF
        )
        manifest = build_ncen_manifest(
            cache,
            shelf=shelf,
            purpose=(
                "Provenance for the fixed-income shelf cost audit in "
                "docs/research/setting-the-equity-share.md. Form N-CEN Items C.3.b, C.6 "
                "and C.8, per series per fiscal year, as filed."
            ),
            regenerate=(
                "cd research && uv run python -m "
                "portfolio_edge.studies._fixed_income_tables --build-ncen"
            ),
        )
        path = root / NCEN_MANIFEST_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=1) + "\n")
        print(f"wrote {path}")
    if args.write_manifests:
        for written in write_manifests(cache, root):
            print(f"wrote {written}")
    panel = build_panel(cache)
    sections = [
        table_shelf(panel),
        table_moments(panel),
        table_matched_volatility(panel),
        table_engines(panel),
        table_long_bond_leg(panel),
        table_exp_010_cells(panel),
        table_correlation_stability(panel),
        table_investable_stability(panel),
        table_breakeven(panel),
    ]
    if (root / PRODUCT_FACTS_PATH).exists():
        sections.append(table_costs(panel, root))
    print("\n\n".join(sections))
    print("\n\n## Digests\n")
    for name, digest in sorted(panel.digests.items()):
        print(f"- `{name}` `{digest[:8]}`")


if __name__ == "__main__":
    main()
