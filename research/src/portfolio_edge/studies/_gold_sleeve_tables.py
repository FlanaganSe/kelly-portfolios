"""Regenerates the gold tables in ``docs/research/marginal-sleeve-value.md`` and
``docs/research/capital-efficiency-and-breadth.md`` §3.

Kept separate from :mod:`portfolio_edge.studies.gold_sleeve` so the study stays pure and
testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.gold_sleeve

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen, the gold leg comes from a benchmark price rather than a research-grade total
return (see :mod:`portfolio_edge.data.lbma` for the argument about why that is a weaker
objection for gold than for a fund), and the carry cost is an assumption.

Two gold instruments, and neither is quoted alone
--------------------------------------------------
*Primary:* the **World Bank Pink Sheet** gold series, monthly, USD per troy ounce, 1960
onward, CC BY 4.0 and therefore redistributable. Its own definition says it is the London
afternoon fixing, **averaged over the daily rates in each month**, until June 2025.

*Cross-check:* the **LBMA Gold Price PM** month-end fix, daily from 1968, licence-
restricted (see :mod:`portfolio_edge.data.lbma`).

They are the same benchmark sampled two different ways, and the difference is not
cosmetic: differencing period *averages* induces positive autocorrelation and understates
volatility, so the Pink Sheet's Sharpe ratio is biased **upward**. Every table below
reports both, and where they disagree the **less favourable** figure is the one the
documentation quotes — which is this repository's net-pessimistic convention applied to a
sampling choice rather than to a cost.

The panel
---------
*US equity* is Ken French ``Mkt-RF + RF``; *cash* is the same file's ``RF``. Using one
file for both legs avoids the cash-series substitution :mod:`portfolio_edge.data.fred`
exists to block.

*The global equity core* is Experiment 010's, 60/30/10 US / developed ex-US / emerging,
monthly rebalanced, and it exists only from 1991-01, so it is the short arm rather than
the headline.

The windows, and why 1971 decides them
---------------------------------------
Before 1971-08-15 the US dollar gold price was an administered peg. A monthly "return"
inside that window records the 1972 and 1973 devaluations — two policy decisions — and a
US person could not legally own bullion until 1974-12-31 in any case. So:

* **1971-09 onward is the headline**, the first full month after convertibility ended.
* **the pegged window is reported and excluded**, so the reader can see what excluding it
  did rather than take the exclusion on trust.
* **1975-01 onward** is the arm in which the asset was actually holdable by the investor
  this repository models.
* **1985-01…2025-05** is reported because it is exactly the window
  ``docs/research/capital-efficiency-and-breadth.md`` §3 compares every other candidate
  engine on, and a gold row measured on a different window could not be read beside them.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Final, Literal

import numpy as np

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import french, lbma, worldbank
from portfolio_edge.data.cache import RawCache
from portfolio_edge.inference.bootstrap import bootstrap_confidence_interval
from portfolio_edge.studies.gold_sleeve import (
    MONTHS_PER_YEAR,
    GoldCarry,
    admission,
    conditional_correlation,
    geometric_growth,
    pro_rata_marginal_value,
    sleeve_moments,
    total_returns_from_levels,
)
from portfolio_edge.studies.overlay_growth import (
    FundingRule,
    MultiOverlay,
    OverlayInputs,
    effective_breadth,
    funding_rule_gap,
    growth_optimal_overlay_vector,
    marginal_growth,
    multi_overlay_growth_gain,
)
from portfolio_edge.studies.overlay_stress import matched_volatility_gap

FloatArray = np.typing.NDArray[np.float64]

Source = Literal["worldbank", "lbma"]

#: Primary first. Every table iterates this tuple; nothing quotes one source alone.
SOURCES: Final[tuple[Source, ...]] = ("worldbank", "lbma")

SEED: Final = 20260817
RESAMPLES: Final = 10_000
BLOCK_MONTHS: Final = 12.0

#: One-sided alpha 0.05 and power 0.80, matching every other MDE in this repository.
_Z_SUM: Final = 1.6448536269514722 + 0.8416212335729143

#: Experiment 010's frozen reference weight and cap, reused so the gold row can be read
#: beside its sleeve table rather than beside nothing.
REFERENCE_WEIGHT: Final = 0.10
WEIGHT_CAP: Final = 0.20

#: Experiment 010's frozen materiality bar, in pp/yr.
MATERIALITY_BAR: Final = 0.30

#: The month after which the US dollar gold price is a market price rather than a peg.
FIRST_FLOATING_MONTH: Final = "1971-09"
FIRST_LEGAL_MONTH: Final = "1975-01"

#: The carry tiers. **Every one of these is an assumption about what a holder pays**, and
#: each states where its number came from. The ETF tiers are the sponsors' fees as stated
#: in their own SEC filings, which are stronger sources than the marketing pages and were
#: used because two of the issuer pages could not be reached. The zero tier is not a
#: holdable arrangement and exists only to show how much of the result the cost
#: assumption is carrying.
CARRY_TIERS: Final[tuple[GoldCarry, ...]] = (
    GoldCarry(
        annual_cost=0.0,
        label="none (not holdable)",
        source="not a vehicle; a sensitivity arm isolating the cost assumption",
    ),
    GoldCarry(
        annual_cost=0.0010,
        label="GLDM 0.10%",
        source=(
            "World Gold Trust Form 10-K, FY ended 2025-09-30, filed 2025-11-25: "
            '"GLDM\'s only ordinary recurring operating expense is the Sponsor\'s '
            'annual fee of 0.10% of the NAV of GLDM." Retrieved 2026-08-17 from '
            "sec.gov/Archives/edgar/data/1618181/000143774925036313/gldm20250930_10k.htm"
        ),
    ),
    GoldCarry(
        annual_cost=0.0017,
        label="SGOL 0.17%",
        source=(
            'abrdn Gold ETF Trust Form 10-K, FY2025, filed 2026-03-02: "The '
            "Sponsor's Fee accrues daily at an annualized rate equal to 0.17% of the "
            'ANAV of the Trust." Retrieved 2026-08-17 from '
            "sec.gov/Archives/edgar/data/1450923/000199937126004879/sgol-10k_123125.htm"
        ),
    ),
    GoldCarry(
        annual_cost=0.0025,
        label="IAU 0.25%",
        source=(
            "iShares Gold Trust Form 10-K, FY2025, filed 2026-02-27: \"the Sponsor's "
            'fees is accrued daily at an annualized rate equal to 0.25% of the net '
            'asset value of the Trust". Retrieved 2026-08-17 from '
            "sec.gov/Archives/edgar/data/1278680/000143774926006055/iau20251231_10k.htm"
        ),
    ),
    GoldCarry(
        annual_cost=0.0040,
        label="GLD 0.40%",
        source=(
            'SPDR Gold Trust Form 10-K, FY ended 2025-09-30, filed 2025-11-25: "The '
            "Trust's only recurring fixed expense is the Sponsor's fee which accrues "
            'daily at an annual rate equal to 0.40% of the daily NAV." Retrieved '
            "2026-08-17 from "
            "sec.gov/Archives/edgar/data/1222333/000143774925036305/gld20250930_10k.htm"
        ),
    ),
    GoldCarry(
        annual_cost=0.0119,
        label="UGL 1.19% (2x, K-1)",
        source=(
            "ProShares Trust II prospectus 424(b)(3) filed 2026-03-26, Breakeven "
            "Table for ProShares Ultra Gold: management fee 0.95%, brokerage 0.24%, "
            "total 1.19%. NOT A GOLD SLEEVE — it is 2x geared and mixes non-1256 "
            "swaps with futures; listed only to price the futures route. Retrieved "
            "2026-08-17 from "
            "sec.gov/Archives/edgar/data/1415311/000119312526126553/d86378d424b3.htm"
        ),
    ),
)

#: The tier the headline uses. The cheapest *bullion-backed* vehicle, not the zero tier.
HEADLINE_CARRY: Final = CARRY_TIERS[1]

#: Drawdown depths at which the conditional correlation is measured. ``0.10`` is the
#: depth ``docs/research/capital-efficiency-and-breadth.md`` §9.3 uses, so the gold figure
#: is directly comparable to trend's.
CRISIS_THRESHOLDS: Final = (0.05, 0.10, 0.20)

#: The named stress episodes (docs/research/evidence-base.md) this panel can reach.
CRISIS_WINDOWS: Final[Mapping[str, tuple[str, str]]] = {
    "1973-74": ("1973-01", "1974-12"),
    "late-1970s inflation": ("1977-01", "1980-03"),
    "1987": ("1987-08", "1987-12"),
    "1998": ("1998-07", "1998-10"),
    "2000-02 dotcom": ("2000-04", "2002-09"),
    "2008-09 GFC": ("2007-11", "2009-02"),
    "2020 Q1 covid": ("2020-01", "2020-03"),
    "2022 inflation": ("2022-01", "2022-12"),
}

#: The eras. ``(label, first month, last month or None for "to the end")``.
ERAS: Final = (
    ("pegged window, EXCLUDED", None, "1971-08"),
    ("1971-09…end (headline)", FIRST_FLOATING_MONTH, None),
    ("1975-01…end (legal to own)", FIRST_LEGAL_MONTH, None),
    ("1971-09…1974-12 (repricing)", FIRST_FLOATING_MONTH, "1974-12"),
    ("1975-01…1984-12", FIRST_LEGAL_MONTH, "1984-12"),
    ("1985-01…2025-05 (§3's window)", "1985-01", "2025-05"),
    ("1985-01…end", "1985-01", None),
)

#: Experiment 010's frozen sample and base weights, so the gold row can be dropped into
#: its sleeve table rather than reported beside it in a different window.
EXP_010_FIRST: Final = "1991-01"
EXP_010_LAST: Final = "2025-12"
GLOBAL_CORE_WEIGHTS: Final = {"us": 0.60, "dev_ex_us": 0.30, "emerging": 0.10}
BALANCED_CASH_WEIGHT: Final = 0.40


# --------------------------------------------------------------------------------
# The panel
# --------------------------------------------------------------------------------


def _gold_levels(source: Source) -> tuple[tuple[str, float], ...]:
    """Monthly USD gold levels from one source. Never downloads."""
    cache = RawCache()
    if source == "lbma":
        dataset = lbma.get_dataset("lbma_gold_pm")
        entry = cache.entry_for(dataset.url)
        if entry is None:
            raise RuntimeError("the LBMA gold price is not cached")
        return lbma.month_end_usd(lbma.parse(cache, entry, dataset=dataset))
    pink = worldbank.get_dataset("worldbank_pinksheet_gold_monthly")
    entry = cache.entry_for(pink.url)
    if entry is None:
        raise RuntimeError("the World Bank Pink Sheet is not cached")
    return worldbank.monthly_series(
        worldbank.parse(cache, entry, dataset=pink), "Gold"
    )


def _gold_returns(source: Source, carry: GoldCarry) -> dict[str, float]:
    """Monthly gold total returns keyed by the month the return belongs to.

    A return dated M is the change from M-1's level to M's, so it belongs to M. The
    first month of the level series therefore has no return, by construction.
    """
    levels = _gold_levels(source)
    months = tuple(month for month, _ in levels)
    values = total_returns_from_levels([price for _, price in levels], carry=carry)
    return dict(zip(months[1:], values, strict=True))


def _equity_and_cash() -> tuple[dict[str, float], dict[str, float]]:
    cache = RawCache()
    dataset = french.get_dataset("french_us_ff3")
    entry = cache.entry_for(dataset.url)
    if entry is None:
        raise RuntimeError("the Ken French file is not cached")
    table = french.parse(cache, entry, dataset=dataset).table("monthly")
    return (
        _column(table.periods, table.column("Mkt-RF")),
        _column(table.periods, table.column("RF")),
    )


def _panel(
    source: Source, carry: GoldCarry
) -> tuple[tuple[str, ...], dict[str, FloatArray]]:
    """Gold, US equity and cash, intersected on the months all three exist.

    Never downloads. A table that silently pulled a new vintage would be the one thing
    that could change a published figure without a commit.
    """
    gold = _gold_returns(source, carry)
    excess, cash = _equity_and_cash()
    periods = tuple(sorted(set(gold) & set(excess) & set(cash)))
    columns = {
        "gold_excess": np.array([gold[p] - cash[p] for p in periods]),
        "gold_total": np.array([gold[p] for p in periods]),
        "equity_excess": np.array([excess[p] for p in periods]),
        "equity_total": np.array([excess[p] + cash[p] for p in periods]),
        "cash": np.array([cash[p] for p in periods]),
    }
    return periods, columns


def _column(
    periods: Sequence[str], values: Sequence[float | None]
) -> dict[str, float]:
    return {p: v for p, v in zip(periods, values, strict=True) if v is not None}


def _slice(
    periods: Sequence[str],
    columns: Mapping[str, FloatArray],
    *,
    first: str | None,
    last: str | None,
) -> tuple[tuple[str, ...], dict[str, FloatArray]]:
    keep = np.array(
        [
            (first is None or first <= p) and (last is None or p <= last)
            for p in periods
        ],
        dtype=bool,
    )
    return tuple(p for p, k in zip(periods, keep, strict=True) if k), {
        name: values[keep] for name, values in columns.items()
    }


# --------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------


def _rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def _provenance() -> None:
    cache = RawCache()
    _rule("Provenance")
    pink = worldbank.get_dataset("worldbank_pinksheet_gold_monthly")
    entry = cache.entry_for(pink.url)
    if entry is None:
        print("  worldbank_pinksheet_gold_monthly: NOT CACHED")
    else:
        table = worldbank.parse(cache, entry, dataset=pink)
        print(
            f"  worldbank_pinksheet_gold_monthly (PRIMARY, CC BY 4.0): {table.rows} "
            f"months {table.first_observation}…{table.last_observation}, retrieved "
            f"{entry.retrieved_utc}"
        )
        print(f"    sha256_raw        {entry.sha256}")
        print(f"    sha256_normalized {table.sha256_normalized()}")
        print(f"    release           {table.banner}")
    for dataset_id in ("lbma_gold_pm", "lbma_gold_am"):
        dataset = lbma.get_dataset(dataset_id)
        entry = cache.entry_for(dataset.url)
        if entry is None:
            print(f"  {dataset_id}: NOT CACHED")
            continue
        table = lbma.parse(cache, entry, dataset=dataset)
        print(
            f"  {dataset_id} (CROSS-CHECK, LICENCE-RESTRICTED): {table.rows} daily rows "
            f"{table.first_observation}…{table.last_observation}, retrieved "
            f"{entry.retrieved_utc}"
        )
        print(f"    sha256_raw        {entry.sha256}")
        print(f"    sha256_normalized {table.sha256_normalized()}")
    print(f"  research_grade={lbma.RESEARCH_GRADE} on both; methodology {lbma.METHODOLOGY_URL}")


def _source_comparison() -> None:
    _rule("The two instruments against each other, on the months both exist")
    frames = {source: _panel(source, HEADLINE_CARRY) for source in SOURCES}
    common = set(frames["worldbank"][0]) & set(frames["lbma"][0])
    window = tuple(sorted(p for p in common if p >= FIRST_FLOATING_MONTH))
    print(f"  {len(window)} common months {window[0]}…{window[-1]}")
    print(
        f"  {'source':12s} {'geo':>8s} {'excess':>8s} {'vol':>8s} {'Sharpe':>8s} "
        f"{'rho':>8s} {'AC(1)':>8s}"
    )
    series: dict[str, FloatArray] = {}
    for source in SOURCES:
        periods, columns = frames[source]
        index = np.array([p in common and p >= FIRST_FLOATING_MONTH for p in periods])
        sliced = {name: values[index] for name, values in columns.items()}
        moments = sleeve_moments(sliced["gold_excess"], sliced["equity_excess"])
        gold = sliced["gold_excess"]
        autocorrelation = float(
            np.corrcoef(gold[:-1], gold[1:])[0, 1]
        )
        series[source] = sliced["gold_total"]
        print(
            f"  {source:12s} {100 * geometric_growth(sliced['gold_total']):7.2f}% "
            f"{100 * moments.arithmetic_excess:7.2f}% "
            f"{100 * moments.volatility:7.2f}% {moments.sharpe:8.3f} "
            f"{moments.correlation:+8.3f} {autocorrelation:+8.3f}"
        )
    correlation = float(np.corrcoef(series["worldbank"], series["lbma"])[0, 1])
    print(f"  correlation between the two return series: {correlation:+.4f}")
    print(
        "  the Pink Sheet is a monthly AVERAGE, so its positive AC(1) and lower "
        "volatility are the Working effect, and its Sharpe is biased upward."
    )


def _eras(source: Source) -> None:
    periods, columns = _panel(source, HEADLINE_CARRY)
    _rule(f"Gold by era, net of {HEADLINE_CARRY.label}, against US equity [{source}]")
    print(
        f"  {'era':32s} {'n':>5s} {'geo':>8s} {'excess':>8s} {'vol':>8s} "
        f"{'Sharpe':>8s} {'rho':>8s} {'beta':>8s} | {'eq geo':>8s} {'eq S':>7s}"
    )
    for label, first, last in ERAS:
        window, sliced = _slice(periods, columns, first=first, last=last)
        if len(window) < 12:
            print(f"  {label:32s} {len(window):5d}   too few months")
            continue
        moments = sleeve_moments(sliced["gold_excess"], sliced["equity_excess"])
        print(
            f"  {label:32s} {moments.months:5d} "
            f"{100 * geometric_growth(sliced['gold_total']):7.2f}% "
            f"{100 * moments.arithmetic_excess:7.2f}% "
            f"{100 * moments.volatility:7.2f}% "
            f"{moments.sharpe:8.3f} {moments.correlation:+8.3f} {moments.beta:+8.3f} | "
            f"{100 * geometric_growth(sliced['equity_total']):7.2f}% "
            f"{moments.base_sharpe:7.3f}"
        )
    print(f"  (the pegged window is {periods[0]}…1971-08 on this source)")


def _carry_sensitivity(source: Source) -> None:
    _rule(f"How much the carry assumption is carrying, 1971-09 onward [{source}]")
    print(f"  {'tier':22s} {'excess':>8s} {'Sharpe':>8s} {'margin at L=1':>14s}")
    for tier in CARRY_TIERS:
        periods, columns = _panel(source, tier)
        _, sliced = _slice(periods, columns, first=FIRST_FLOATING_MONTH, last=None)
        moments = sleeve_moments(sliced["gold_excess"], sliced["equity_excess"])
        print(
            f"  {tier.label:22s} {100 * moments.arithmetic_excess:7.2f}% "
            f"{moments.sharpe:8.3f} {admission(moments).margin:14.3f}"
        )


#: The two windows every decision-relevant table is reported on. The first is the
#: headline; the second is the only one in which a US person could legally have held the
#: asset, and the gap between them is the single most important number on this page.
DECISION_WINDOWS: Final = (
    ("1971-09…end", FIRST_FLOATING_MONTH),
    ("1975-01…end (holdable)", FIRST_LEGAL_MONTH),
)


def _admission(source: Source, label: str, first: str) -> None:
    periods, columns = _panel(source, HEADLINE_CARRY)
    _rule(f"Admission: does gold's net Sharpe clear L·rho·sigma_p? [{source}, {label}]")
    window, sliced = _slice(periods, columns, first=first, last=None)
    moments = sleeve_moments(sliced["gold_excess"], sliced["equity_excess"])
    inputs = OverlayInputs(
        base_excess_return=moments.base_arithmetic_excess,
        base_volatility=moments.base_volatility,
        diversifier_excess_return=moments.arithmetic_excess,
        diversifier_volatility=moments.volatility,
        correlation=moments.correlation,
    )
    print(f"  months {moments.months} ({window[0]}…{window[-1]})")
    print(
        f"  gold  S_d={moments.sharpe:.3f}  sigma_d={100 * moments.volatility:.2f}%  "
        f"rho={moments.correlation:+.3f}  beta={moments.beta:+.3f}"
    )
    print(
        f"  base  S_p={moments.base_sharpe:.3f}  "
        f"a_p={100 * moments.base_arithmetic_excess:.2f}%  "
        f"sigma_p={100 * moments.base_volatility:.2f}%  "
        f"L_p*={inputs.base_kelly_leverage:.2f}"
    )
    print(f"  {'base exposure L':>18s} {'threshold':>10s} {'margin':>10s} {'verdict':>10s}")
    for exposure in (1.0, 1.5, inputs.base_kelly_leverage):
        verdict = admission(moments, base_exposure=exposure)
        print(
            f"  {exposure:18.3f} {verdict.threshold:10.4f} {verdict.margin:+10.4f} "
            f"{'ADMITTED' if verdict.admitted else 'refused':>10s}"
        )
    print(
        f"  equation (4) valid at this correlation: "
        f"{admission(moments).within_equation_4_range} "
        f"(|rho| <= 0.5 required; |rho| = {abs(moments.correlation):.3f})"
    )
    gap = funding_rule_gap(
        base_excess_return=moments.base_arithmetic_excess,
        base_volatility=moments.base_volatility,
    )
    print(
        f"  the pro-rata bar sits {100 * gap:.2f} pp/yr above the overlay bar "
        "(a_p - sigma_p**2, nothing about gold in it)"
    )


def _conditional(source: Source, label: str, first: str) -> None:
    periods, columns = _panel(source, HEADLINE_CARRY)
    _rule(f"Crisis-conditional correlation to equity [{source}, {label}]")
    _, sliced = _slice(periods, columns, first=first, last=None)
    print(
        f"  {'depth':>7s} {'n in':>6s} {'n out':>6s} {'rho in':>8s} {'rho out':>9s} "
        f"{'gap':>8s} {'gold %/mo in':>13s} {'eq %/mo in':>11s}"
    )
    for threshold in CRISIS_THRESHOLDS:
        result = conditional_correlation(
            sliced["equity_excess"], sliced["gold_excess"], threshold=threshold
        )
        print(
            f"  {threshold:6.0%}  {result.months_in:6d} {result.months_out:6d} "
            f"{result.correlation_in:+8.3f} {result.correlation_out:+9.3f} "
            f"{result.gap:+8.3f} {100 * result.sleeve_mean_in:12.2f}% "
            f"{100 * result.base_mean_in:10.2f}%"
        )
    full = float(np.corrcoef(sliced["equity_excess"], sliced["gold_excess"])[0, 1])
    print(f"  full-sample rho {full:+.3f}")

    if first != FIRST_FLOATING_MONTH:
        return
    _rule(f"Inside each named episode [{source}]")
    print(f"  {'window':26s} {'n':>4s} {'equity':>9s} {'gold':>9s} {'rho':>8s}")
    for label, (first, last) in CRISIS_WINDOWS.items():
        window, sub = _slice(periods, columns, first=first, last=last)
        if len(window) < 3:
            print(f"  {label:26s} {len(window):4d}   not in the panel")
            continue
        equity = float(np.prod(1.0 + sub["equity_total"]) - 1.0)
        gold = float(np.prod(1.0 + sub["gold_total"]) - 1.0)
        rho = float(np.corrcoef(sub["equity_excess"], sub["gold_excess"])[0, 1])
        print(
            f"  {label:26s} {len(window):4d} {100 * equity:8.1f}% {100 * gold:8.1f}% "
            f"{rho:+8.3f}"
        )


def _marginal(source: Source, label: str, first: str) -> None:
    periods, columns = _panel(source, HEADLINE_CARRY)
    _rule(f"Experiment 010's construction, pro rata, US equity base [{source}, {label}]")
    window, sliced = _slice(periods, columns, first=first, last=None)
    print(
        f"  {'w':>6s} {'base g':>9s} {'blend g':>9s} {'marginal':>9s} {'alpha':>9s} "
        f"{'credit@w':>9s} {'ceiling@w':>10s} {'1st order':>10s}"
    )
    for weight in (REFERENCE_WEIGHT, WEIGHT_CAP):
        value = pro_rata_marginal_value(
            sliced["equity_total"], sliced["gold_total"], sliced["cash"], weight=weight
        )
        print(
            f"  {weight:6.2f} {100 * value.base_growth:8.2f}% "
            f"{100 * value.blended_growth:8.2f}% "
            f"{100 * value.realised_marginal_growth:+8.3f} "
            f"{100 * value.standalone_alpha:+8.2f} "
            f"{100 * value.credit_at_weight:+8.3f} "
            f"{100 * value.credit_ceiling_at_weight:9.3f} "
            f"{100 * value.first_order_marginal:+9.3f}"
        )
    reference = pro_rata_marginal_value(
        sliced["equity_total"],
        sliced["gold_total"],
        sliced["cash"],
        weight=REFERENCE_WEIGHT,
    )
    print(
        f"  beta to base {reference.beta:+.3f}; credit per unit weight "
        f"{100 * reference.credit_per_unit_weight:+.3f} pp/yr; frozen bar "
        f"{MATERIALITY_BAR:.2f} pp/yr"
    )

    rng = np.random.default_rng(SEED)
    difference = REFERENCE_WEIGHT * (sliced["gold_total"] - sliced["equity_total"])
    interval = bootstrap_confidence_interval(
        difference,
        lambda x: float(np.mean(x)) * MONTHS_PER_YEAR,
        rng=rng,
        method="stationary",
        block_length=BLOCK_MONTHS,
        n_resamples=RESAMPLES,
    )
    print(
        f"  arithmetic marginal at w={REFERENCE_WEIGHT:.2f}: "
        f"{100 * interval.point_estimate:+.3f} pp/yr, 95% "
        f"[{100 * interval.lower:+.3f}, {100 * interval.upper:+.3f}], MDE(80%) "
        f"{100 * _Z_SUM * interval.standard_error:.3f} pp/yr, n={len(window)}"
    )
    print(
        "  (the interval is on the ARITHMETIC first-order difference; the deciding "
        "figure above is the realised geometric finite difference)"
    )


def _weight_ladder(source: Source) -> None:
    periods, columns = _panel(source, HEADLINE_CARRY)
    _rule(f"The realised growth surface in the weight, 1971-09 onward [{source}]")
    _, sliced = _slice(periods, columns, first=FIRST_FLOATING_MONTH, last=None)
    base = geometric_growth(sliced["equity_total"])
    print(f"  {'w':>6s} {'geometric':>11s} {'vs base':>9s} {'volatility':>11s}")
    for weight in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50):
        blended = (1.0 - weight) * sliced["equity_total"] + weight * sliced["gold_total"]
        volatility = float(np.std(blended, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
        print(
            f"  {weight:6.2f} {100 * geometric_growth(blended):10.2f}% "
            f"{100 * (geometric_growth(blended) - base):+8.3f} "
            f"{100 * volatility:10.2f}%"
        )
    del periods


def _exp_010_arm(source: Source) -> None:
    """Gold through Experiment 010's own base portfolios, sample and reference weight.

    The base portfolios are rebuilt here rather than imported because that experiment
    reads a frozen specification and re-running it would require amending a file written
    before its result was examined. The weights, the sample and the reference weight are
    copied from it and are stated as module constants so the copy is checkable.
    """
    cache = RawCache()
    gold = _gold_returns(source, HEADLINE_CARRY)

    regions: dict[str, dict[str, float]] = {}
    cash: dict[str, float] = {}
    for key, dataset_id in (
        ("us", "french_us_ff3"),
        ("dev_ex_us", "french_developed_ex_us_ff5"),
        ("emerging", "french_emerging_ff5"),
    ):
        dataset = french.get_dataset(dataset_id)
        entry = cache.entry_for(dataset.url)
        if entry is None:
            raise RuntimeError(f"{dataset_id} is not cached")
        table = french.parse(cache, entry, dataset=dataset).table("monthly")
        excess = _column(table.periods, table.column("Mkt-RF"))
        free = _column(table.periods, table.column("RF"))
        regions[key] = {p: excess[p] + free[p] for p in excess if p in free}
        if key == "us":
            cash = free

    common = set(cash) & set(gold)
    for values in regions.values():
        common &= set(values)
    periods = tuple(p for p in sorted(common) if EXP_010_FIRST <= p <= EXP_010_LAST)
    core = np.array(
        [sum(GLOBAL_CORE_WEIGHTS[k] * regions[k][p] for k in regions) for p in periods]
    )
    cash_leg = np.array([cash[p] for p in periods])
    balanced = (1.0 - BALANCED_CASH_WEIGHT) * core + BALANCED_CASH_WEIGHT * cash_leg
    sleeve = np.array([gold[p] for p in periods])

    _rule(
        f"Experiment 010's bases and sample, {len(periods)} months "
        f"{periods[0]}…{periods[-1]} [{source}]"
    )
    print(
        f"  {'base':20s} {'w':>5s} {'marginal':>9s} {'alpha':>8s} {'credit/unit':>12s} "
        f"{'credit@w':>9s} {'ceiling@w':>10s} {'beta':>8s}"
    )
    for name, base in (("global_equity_core", core), ("balanced_60_40", balanced)):
        for weight in (REFERENCE_WEIGHT, WEIGHT_CAP):
            value = pro_rata_marginal_value(base, sleeve, cash_leg, weight=weight)
            print(
                f"  {name:20s} {weight:5.2f} "
                f"{100 * value.realised_marginal_growth:+8.3f} "
                f"{100 * value.standalone_alpha:+7.2f} "
                f"{100 * value.credit_per_unit_weight:+11.3f} "
                f"{100 * value.credit_at_weight:+8.3f} "
                f"{100 * value.credit_ceiling_at_weight:9.3f} "
                f"{value.beta:+8.3f}"
            )
    moments = sleeve_moments(sleeve - cash_leg, core - cash_leg)
    print(
        f"  gold on exp_010's sample: Sharpe {moments.sharpe:.3f}, rho to core "
        f"{moments.correlation:+.3f}, vol {100 * moments.volatility:.2f}%, excess "
        f"{100 * moments.arithmetic_excess:.2f}%"
    )
    print(
        f"  frozen bar {MATERIALITY_BAR:.2f} pp/yr at the frozen "
        f"{REFERENCE_WEIGHT:.2f} reference weight"
    )


# --------------------------------------------------------------------------------
# The funding rule, which is the question the pro-rata tables above do not answer
# --------------------------------------------------------------------------------

#: GDE's structure, measured from its own Form N-PORT for 2026-02-28 and recorded in
#: ``docs/research/capital-efficiency-and-breadth.md`` §6a.2: 84.80% of net assets in
#: equity and 83.63% in gold-futures notional.
GDE_BASE_LEG: Final = 0.8480
GDE_OVERLAY_LEG: Final = 0.8363

#: Equation (7) of §6a.1: ``delta = (1 - b) / d`` is the base sold per unit of
#: diversifier notional obtained, and the wrapper's structure enters the hurdle exactly
#: once, as a multiplier on §1's funding-rule gap. **GDE is not a pure overlay**: it
#: forfeits 18.2% of the gap because its equity leg is 84.8% rather than 100%.
GDE_DELTA: Final = (1.0 - GDE_BASE_LEG) / GDE_OVERLAY_LEG

#: GDE's total expense ratio from its own SEC-filed fee table, on **capital**. The hurdle
#: is stated per unit of **notional**, so the conversion is ``fee / d``.
GDE_FEE_ON_CAPITAL: Final = 0.0020
GDE_FEE_PER_NOTIONAL: Final = GDE_FEE_ON_CAPITAL / GDE_OVERLAY_LEG

#: The financing embedded in a long gold-futures position, from
#: ``docs/research/structural-and-tax-edges.md`` §3: <=40 bp over the Treasury curve, and
#: an **upper bound** — the same 40 bp appears in SPX option boxes over the same window,
#: so it is the Treasury convenience yield rather than anything gold-specific. **It is a
#: transfer from published research on the contracts, not a reading of any GDE filing.**
GOLD_FUTURES_BASIS: Final = 0.0040

#: GDE's SEC-standardised after-tax return drag at the highest individual federal rates,
#: since inception 2022-03-17, from §6a.4: 18.63% before tax against 17.10% after tax on
#: distributions. **On capital, not on notional.** Gold futures are Section 1256 contracts
#: marked to market every 31 December, so there is nothing to defer.
GDE_TAX_DRAG_ON_CAPITAL: Final = 0.0153


def _overlay_funding(source: Source, label: str, first: str) -> None:
    """What gold is worth when the sleeve is financed rather than funded by a sale.

    Every table above uses **pro-rata** funding, which is Experiment 010's rule and the
    rule a physical gold ETF imposes. It is also the rule
    ``docs/research/capital-efficiency-and-breadth.md`` §1 shows costs
    ``a_p - sigma_p**2`` — an amount containing nothing about the sleeve — and §6a shows
    is a property of the ticker rather than of the analysis. **A verdict quoted from the
    pro-rata tables alone is a verdict about GLDM, not about gold.**

    Three bars are reported and they are not interchangeable:

    * **pure overlay**, equation (1): ``a_net - L rho sigma_p sigma_d``;
    * **GDE as measured**, equation (7): the overlay bar less ``delta`` times the
      funding-rule gap, because GDE's equity leg is 84.8% rather than 100%;
    * **pro rata**, equation (2), repeated so the three sit in one place.
    """
    periods, columns = _panel(source, CARRY_TIERS[0])  # gross: futures pay no storage
    window, sliced = _slice(periods, columns, first=first, last=None)
    moments = sleeve_moments(sliced["gold_excess"], sliced["equity_excess"])

    inputs = OverlayInputs(
        base_excess_return=moments.base_arithmetic_excess,
        base_volatility=moments.base_volatility,
        diversifier_excess_return=moments.arithmetic_excess,
        diversifier_volatility=moments.volatility,
        correlation=moments.correlation,
        financing_spread=GOLD_FUTURES_BASIS,
        fee=GDE_FEE_PER_NOTIONAL,
    )
    gap = funding_rule_gap(
        base_excess_return=moments.base_arithmetic_excess,
        base_volatility=moments.base_volatility,
    )
    overlay = marginal_growth(inputs, rule=FundingRule.OVERLAY)
    wrapper = overlay - GDE_DELTA * gap
    pro_rata = marginal_growth(inputs, rule=FundingRule.PRO_RATA)

    _rule(f"Funding rule: the three bars, per unit of gold notional [{source}, {label}]")
    print(f"  months {moments.months} ({window[0]}…{window[-1]})")
    print(
        f"  gross a_d {100 * moments.arithmetic_excess:.2f}%, less {100 * GOLD_FUTURES_BASIS:.2f}% "
        f"financing and {100 * GDE_FEE_PER_NOTIONAL:.3f}% fee = a_net "
        f"{100 * inputs.net_excess_return:.2f}%"
    )
    print(f"  funding-rule gap a_p - sigma_p**2 = {100 * gap:+.2f} pp/yr")
    print(f"  GDE delta = {GDE_DELTA:.4f}, so it keeps {100 * (1 - GDE_DELTA):.1f}% of that gap")
    print(f"  {'rule':28s} {'dg/dw per unit notional':>24s}")
    for name, value in (
        ("pure overlay (1)", overlay),
        ("GDE as measured (7)", wrapper),
        ("pro rata (2)", pro_rata),
    ):
        print(f"  {name:28s} {100 * value:+23.3f}")
    print(f"  {'weight w':>10s} {'pure overlay':>14s} {'GDE (7)':>10s} {'pro rata':>10s}")
    for weight in (REFERENCE_WEIGHT, GDE_OVERLAY_LEG):
        print(
            f"  {weight:10.4f} {100 * weight * overlay:+14.3f} "
            f"{100 * weight * wrapper:+10.3f} {100 * weight * pro_rata:+10.3f}"
        )
    print(f"  frozen bar {MATERIALITY_BAR:.2f} pp/yr")


def _gde_realised(source: Source, label: str, first: str) -> None:
    """The GDE-implied portfolio path, against the two controls that decide.

    ``r = b r_eq + (1 - b) r_cash + d (r_gold - r_cash - s) - fee``, monthly, with ``b``
    and ``d`` GDE's measured legs. This is not a backtest of GDE — the fund began in
    2022-03 and this window starts decades earlier — it is **what GDE's structure would
    have delivered on this history**, which is the only thing a 658-month panel can say.

    Equation (5) decides: at matched volatility the higher Sharpe ratio wins and nothing
    else matters, so the leverage-matched control is reported beside the unlevered one and
    the unlevered comparison is never quoted alone.
    """
    periods, columns = _panel(source, CARRY_TIERS[0])
    window, sliced = _slice(periods, columns, first=first, last=None)
    equity = sliced["equity_total"]
    cash = sliced["cash"]
    gold_excess = sliced["gold_total"] - cash

    gde = (
        GDE_BASE_LEG * equity
        + (1.0 - GDE_BASE_LEG) * cash
        + GDE_OVERLAY_LEG * (gold_excess - GOLD_FUTURES_BASIS / MONTHS_PER_YEAR)
        - GDE_FEE_ON_CAPITAL / MONTHS_PER_YEAR
    )
    pure = equity + GDE_OVERLAY_LEG * (
        gold_excess - (GOLD_FUTURES_BASIS + GDE_FEE_PER_NOTIONAL) / MONTHS_PER_YEAR
    )
    small = equity + REFERENCE_WEIGHT * (
        gold_excess - (GOLD_FUTURES_BASIS + GDE_FEE_PER_NOTIONAL) / MONTHS_PER_YEAR
    )

    _rule(f"The GDE-implied path against its controls [{source}, {label}]")
    print(f"  {len(window)} months {window[0]}…{window[-1]}")
    print(
        f"  {'portfolio':34s} {'geometric':>10s} {'vol':>8s} {'Sharpe':>8s} "
        f"{'vs unlev':>9s} {'vs matched':>11s} {'MDE':>7s}"
    )
    base_sharpe = float(np.mean(equity - cash)) / float(np.std(equity - cash, ddof=1))
    for name, path in (
        ("equity only, 1.00x", equity),
        (f"pure overlay, w={REFERENCE_WEIGHT:.2f}", small),
        (f"pure overlay, w={GDE_OVERLAY_LEG:.4f}", pure),
        ("GDE as measured", gde),
    ):
        excess = path - cash
        volatility = float(np.std(excess, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
        sharpe = float(np.mean(excess)) / float(np.std(excess, ddof=1))
        levered = volatility / (
            float(np.std(equity - cash, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
        )
        control = levered * (equity - cash)
        gap, mde = matched_volatility_gap(excess, control, scaling="unlevered")
        unlevered_gap = geometric_growth(path) - geometric_growth(equity)
        print(
            f"  {name:34s} {100 * geometric_growth(path):9.2f}% "
            f"{100 * volatility:7.2f}% {sharpe * math.sqrt(MONTHS_PER_YEAR):8.3f} "
            f"{100 * unlevered_gap:+8.3f} {100 * gap:+10.3f} {100 * mde:6.2f}"
        )
    print(
        f"  base Sharpe {base_sharpe * math.sqrt(MONTHS_PER_YEAR):.3f}; equation (5) says "
        "the matched column decides and the unlevered one does not"
    )
    print(
        f"  in a TAXABLE account subtract GDE's measured {100 * GDE_TAX_DRAG_ON_CAPITAL:.2f} "
        "pp/yr distribution drag from the GDE row: Section 1256 marks to market annually"
    )


# --------------------------------------------------------------------------------
# Breadth: does gold ADD to trend, or substitute for it?
# --------------------------------------------------------------------------------

#: The trend overlay weight ``docs/research/portfolio-recommendation.md`` recommends.
RECOMMENDED_TREND_WEIGHT: Final = 0.30

#: Trend's all-in cost on notional and the borrow spread, both as
#: ``_overlay_stress_tables`` charges them, so the joint arm is priced the same way §7's
#: ladder is rather than on a fresh set of assumptions.
TREND_FEE: Final = 0.0095
BORROW_SPREAD: Final = 0.0060


def _trend_and_gold(source: Source) -> None:
    """Gold beside the trend leg this repository builds itself, never a vendor series.

    The trend leg is :mod:`portfolio_edge.studies._overlay_stress_tables`'s **published**
    arm — the same Moskowitz-Ooi-Pedersen construction on four instruments, 12-month
    signal, 36-month volatility window, scaled to a 12% target on a trailing 60-month
    window — imported rather than rebuilt so this section cannot silently diverge from
    the ladder §7 publishes. It reads the cache through that module and downloads
    nothing.

    **One inconsistency is inherited and stated rather than fixed here.** That panel's
    cash leg is Goyal-Welch ``Rfree`` while every other table in this module uses Ken
    French's ``RF``. They are close and they are not the same series, and reconciling
    them would change §7's published figures, so this section uses the trend panel's own
    cash throughout and the correlation it reports is between two excess series measured
    against the same rate.
    """
    from portfolio_edge.studies._overlay_stress_tables import _panel as stress_panel
    from portfolio_edge.studies._overlay_stress_tables import _trend_legs

    stress_periods, stress_columns = stress_panel()
    targeted, _raw = _trend_legs(stress_columns)
    gold = _gold_returns(source, CARRY_TIERS[0])

    keep = [
        i
        for i, period in enumerate(stress_periods)
        if np.isfinite(targeted[i]) and period in gold and period >= FIRST_LEGAL_MONTH
    ]
    if len(keep) < 60:
        raise RuntimeError(f"only {len(keep)} joint months; the panel did not align")
    index = np.array(keep)
    months = [stress_periods[i] for i in keep]
    equity = stress_columns["equity"][index]
    cash = stress_columns["cash"][index]
    trend = targeted[index] - TREND_FEE / MONTHS_PER_YEAR
    gold_excess = np.array([gold[m] for m in months]) - cash - (
        (GOLD_FUTURES_BASIS + GDE_FEE_PER_NOTIONAL) / MONTHS_PER_YEAR
    )

    def annual_mean(x: FloatArray) -> float:
        return float(np.mean(x)) * MONTHS_PER_YEAR

    def annual_vol(x: FloatArray) -> float:
        return float(np.std(x, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)

    _rule(f"Gold beside the trend leg built here, holdable window [{source}]")
    print(f"  {len(months)} joint months {months[0]}…{months[-1]}")
    print(f"  {'leg':10s} {'excess':>8s} {'vol':>8s} {'Sharpe':>8s} {'rho to equity':>14s}")
    for name, leg in (("equity", equity), ("trend", trend), ("gold", gold_excess)):
        print(
            f"  {name:10s} {100 * annual_mean(leg):7.2f}% {100 * annual_vol(leg):7.2f}% "
            f"{annual_mean(leg) / annual_vol(leg):8.3f} "
            f"{float(np.corrcoef(leg, equity)[0, 1]):+14.3f}"
        )
    mutual = float(np.corrcoef(trend, gold_excess)[0, 1])
    print(f"  **correlation between trend and gold: {mutual:+.4f}**")
    alone = effective_breadth(count=1, mutual_correlation=0.0)
    pair = effective_breadth(count=2, mutual_correlation=mutual)
    print(
        f"  effective breadth: trend alone {alone:.2f}; trend + gold {pair:.2f}; "
        "trend + BAB + STR + accruals (page §3) 4.06"
    )

    overlays = MultiOverlay(
        net_excess_returns=(annual_mean(trend), annual_mean(gold_excess)),
        covariance_with_base=(
            float(np.cov(trend, equity, ddof=1)[0, 1]) * MONTHS_PER_YEAR,
            float(np.cov(gold_excess, equity, ddof=1)[0, 1]) * MONTHS_PER_YEAR,
        ),
        covariance=tuple(
            tuple(float(v) * MONTHS_PER_YEAR for v in row)
            for row in np.cov(np.vstack([trend, gold_excess]), ddof=1)
        ),
    )
    star = growth_optimal_overlay_vector(overlays)
    print(
        f"  unshrunk growth-optimal notional: trend {star[0]:.3f}, gold {star[1]:.3f} "
        "— a plug-in optimum from forecasts, never a recommendation"
    )
    print(
        f"  {'weights (trend, gold)':>26s} {'joint gain pp/yr':>17s}"
    )
    for weights in (
        (RECOMMENDED_TREND_WEIGHT, 0.0),
        (0.0, REFERENCE_WEIGHT),
        (RECOMMENDED_TREND_WEIGHT, REFERENCE_WEIGHT),
        (RECOMMENDED_TREND_WEIGHT, RECOMMENDED_TREND_WEIGHT),
    ):
        gain = multi_overlay_growth_gain(overlays, weights=weights)
        print(f"  {weights!s:>26s} {100 * gain:+16.3f}")

    _rule(f"The joint overlay, realised, against the control that decides [{source}]")
    print(
        f"  {'portfolio':32s} {'geometric':>10s} {'vol':>8s} {'Sharpe':>8s} "
        f"{'vs matched':>11s} {'MDE':>7s} {'max DD':>8s}"
    )
    for name, trend_w, gold_w in (
        ("equity only", 0.0, 0.0),
        ("+ 30% trend", RECOMMENDED_TREND_WEIGHT, 0.0),
        ("+ 10% gold", 0.0, REFERENCE_WEIGHT),
        ("+ 30% trend + 10% gold", RECOMMENDED_TREND_WEIGHT, REFERENCE_WEIGHT),
        ("+ 30% trend + 30% gold", RECOMMENDED_TREND_WEIGHT, RECOMMENDED_TREND_WEIGHT),
    ):
        gross_above_one = max(0.0, trend_w + gold_w)
        excess = (
            equity
            + trend_w * trend
            + gold_w * gold_excess
            - BORROW_SPREAD * gross_above_one / MONTHS_PER_YEAR
        )
        volatility = annual_vol(excess)
        levered = volatility / annual_vol(equity)
        gap, mde = matched_volatility_gap(
            excess, levered * equity, scaling="unlevered"
        )
        curve = np.cumprod(1.0 + excess + cash)
        print(
            f"  {name:32s} "
            f"{100 * geometric_growth(excess + cash):9.2f}% "
            f"{100 * volatility:7.2f}% {annual_mean(excess) / volatility:8.3f} "
            f"{100 * gap:+10.3f} {100 * mde:6.2f} "
            f"{100 * drawdown_summary(curve).max_drawdown:7.1f}%"
        )
    crisis = conditional_correlation(equity, gold_excess, threshold=0.10)
    crisis_trend = conditional_correlation(equity, trend, threshold=0.10)
    print(
        f"  crisis-conditional rho to equity at 10% depth, {crisis.months_in} months: "
        f"gold {crisis.correlation_in:+.3f}, trend {crisis_trend.correlation_in:+.3f}; "
        "the falsifier is +0.20"
    )


def main() -> None:
    _provenance()
    _source_comparison()
    for source in SOURCES:
        _eras(source)
    _carry_sensitivity(SOURCES[0])
    _carry_sensitivity(SOURCES[1])
    for label, first in DECISION_WINDOWS:
        for source in SOURCES:
            _admission(source, label, first)
    for label, first in DECISION_WINDOWS:
        for source in SOURCES:
            _conditional(source, label, first)
    for label, first in DECISION_WINDOWS:
        for source in SOURCES:
            _marginal(source, label, first)
    for label, first in DECISION_WINDOWS:
        for source in SOURCES:
            _overlay_funding(source, label, first)
    for label, first in DECISION_WINDOWS:
        for source in SOURCES:
            _gde_realised(source, label, first)
    for source in SOURCES:
        _trend_and_gold(source)
    for source in SOURCES:
        _weight_ladder(source)
    for source in SOURCES:
        _exp_010_arm(source)


if __name__ == "__main__":  # pragma: no cover - a reporting entry point
    main()
