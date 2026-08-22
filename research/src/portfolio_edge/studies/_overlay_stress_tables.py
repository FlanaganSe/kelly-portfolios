"""Regenerates the stress tables behind ``docs/research/capital-efficiency-and-breadth.md``.

Kept separate from :mod:`portfolio_edge.studies.overlay_stress` so the study itself stays
pure and testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.overlay_stress

**What this reproduces before it attacks anything.** §7's ladder was produced by a
scoping script that was never committed, so the first thing printed is that ladder
recomputed from the pinned sources. It reproduces the published geometric returns,
maximum drawdowns and times under water to the printed precision at every weight, which
is the check that licenses reading the rest. It does **not** reproduce the published
volatilities and Sharpe ratios exactly: every volatility here is about 0.3% *relative*
higher than the published one (15.859% against 15.81% at the unlevered base, and the same
ratio at every rung), which moves each Sharpe ratio by roughly 0.002. The geometric
returns and drawdowns — the quantities §7's argument actually rests on — agree exactly.
The residual is recorded rather than reconciled, because the script that produced the
published figures does not exist to compare against.

**Three data notes that decide how far the output may be trusted.**

*The panel is the one Experiment 011 pins, minus its vendor trend leg.* US equity is Ken
French ``Mkt-RF``; treasury and credit are Goyal-Welch ``ltr`` and ``corpr`` less
``Rfree``; the commodity leg is AQR's ``Commodities for the Long Run`` equal-weight
excess return, used here as an *instrument* rather than as a strategy. Cash is
Goyal-Welch ``Rfree``.

*The trend leg is built here*, by :mod:`portfolio_edge.studies.time_series_momentum` on
those four instruments — the standard Moskowitz-Ooi-Pedersen construction with a 12-month
signal, a 36-month trailing volatility window, a 10% per-position target and a 2x cap —
then scaled to a 12% target on a **trailing** 60-month window and charged 95 bp/yr. That
matches the settings that reproduce §7 exactly, and the borrow spread §7 charged is
**zero**, which is itself worth saying out loud: the published ladder finances 2.00x
gross notional free.

*The 1,091-month window starts in 1934-07, and that is a finding rather than a detail.*
The trend leg's 36-month signal burn-in plus its 60-month volatility-target window
consume the first 96 months of a panel that begins 1926-07. **So §7's flat-drawdown
result is measured on a sample from which 1929-32 has been removed by construction**, and
the -50.3% it anchors on is not US equity's worst drawdown; §2 of the same page puts that
at -83.7%. The extended arm below drops the outer volatility target, which moves the
trend leg's start to 1929-07 and lets the 1929-32 window be priced at all.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import aqr, french, goyal_welch
from portfolio_edge.data.cache import RawCache
from portfolio_edge.studies.overlay_growth import OverlayInputs
from portfolio_edge.studies.overlay_stress import (
    ADVERSE_COPULA,
    INDEPENDENT_COPULA,
    DrawdownRung,
    JointPrior,
    Scaling,
    abandonment_cost,
    closure_hazard,
    drawdown_ladder,
    drought_probability,
    forced_deleveraging,
    gap_pair,
    joint_loss_frequency,
    leave_out_gaps,
    matched_volatility_gap,
    overlay_total_returns,
    paired_drawdown_bootstrap,
    sample_joint_prior,
    stress_crisis_correlation,
    stress_surface,
    tolerable_financing_spread,
)
from portfolio_edge.studies.time_series_momentum import (
    TimeSeriesMomentumSpec,
    time_series_momentum,
    volatility_targeted,
)

FloatArray = np.typing.NDArray[np.float64]

SEED: Final = 20260816
DRAWS: Final = 40_000
RESAMPLES: Final = 4_000
BLOCK_MONTHS: Final = 24

#: The settings that reproduce §7's ladder exactly. Not tuned here: found by matching the
#: published geometric returns and drawdowns and then frozen in this file.
TREND_TARGET_VOLATILITY: Final = 0.12
TREND_TARGET_WINDOW: Final = 60
TREND_FEE: Final = 0.0095
#: §7's ladder charges no borrow spread. The stress arms below charge 60 bp, which is the
#: repository's own assumed spread, and the difference is reported rather than merged.
PUBLISHED_BORROW_SPREAD: Final = 0.0
STRESS_BORROW_SPREAD: Final = 0.0060

LADDER: Final = (0.0, 0.25, 0.30, 0.50, 1.00, 2.00)

#: The two controls, never combined into one row. Typed so mypy holds the caller to the
#: two the study defines rather than to any string.
SCALINGS: Final[tuple[Scaling, ...]] = ("leverage_matched", "unlevered")

#: The recommendation under attack: 100% global equity plus a 30% financed trend overlay.
RECOMMENDED_WEIGHT: Final = 0.30

#: The named stress episodes (docs/research/evidence-base.md), every one for which this panel
#: could in principle hold data. 1998 is included because the plan names it.
CRISIS_WINDOWS: Final[Mapping[str, tuple[str, str]]] = {
    "1929-32 great crash": ("1929-09", "1932-06"),
    "1937-38": ("1937-03", "1938-03"),
    "1973-74": ("1973-01", "1974-12"),
    "late-1970s inflation": ("1977-01", "1980-03"),
    "1987": ("1987-08", "1987-12"),
    "1998": ("1998-07", "1998-10"),
    "2000-02 dotcom": ("2000-04", "2002-09"),
    "2008-09 GFC": ("2007-11", "2009-02"),
    "2020 Q1 covid": ("2020-01", "2020-03"),
    "2022 inflation": ("2022-01", "2022-12"),
}

#: §5a's base, unchanged, so the joint surface and the univariate table share their inputs.
BASE_EXCESS_RETURN: Final = 0.050
BASE_VOLATILITY: Final = 0.155
OVERLAY_FEE: Final = 0.0086

#: The prior. Every number here was **chosen**, not measured, and the page must say so.
#: The centres are the three instruments' own figures: a 4.0% gross excess return is
#: §5a's already-two-thirds-haircut central case, -0.08 is the correlation all three
#: instruments agree on, 12.6% is the vendor series' volatility and 59 bp is the measured
#: Fleckenstein-Longstaff funding basis. The scales are wider than estimation error alone
#: would justify, because the forward uncertainty that matters here is regime rather than
#: sampling: a 4.0 pp scale on the mean puts about 16% of mass below zero, which is
#: roughly what the post-2012 drought looks like on all three instruments.
PRIOR_CENTRES: Final = {
    "excess_centre": 0.040,
    "excess_scale": 0.040,
    "correlation_centre": -0.08,
    "correlation_scale": 0.20,
    "volatility_centre": 0.126,
    "volatility_log_scale": 0.25,
    "spread_centre": 0.0059,
    "spread_log_scale": 0.80,
}


# --------------------------------------------------------------------------------
# The panel
# --------------------------------------------------------------------------------


def _panel() -> tuple[tuple[str, ...], dict[str, FloatArray]]:
    """The four instruments, the cash rate, intersected on months all five exist."""
    cache = RawCache()

    french_dataset = french.get_dataset("french_us_ff3")
    french_entry = cache.entry_for(french_dataset.url)
    goyal_dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    goyal_entry = cache.entry_for(goyal_dataset.url)
    aqr_dataset = aqr.get_dataset("aqr_commodities_long_run")
    aqr_entry = cache.entry_for(aqr_dataset.url)
    if french_entry is None or goyal_entry is None or aqr_entry is None:
        raise RuntimeError(
            "one of the three sources is not cached. This module never downloads, so a "
            "stress table can never be the thing that silently pulls a new vintage."
        )

    market = french.parse(cache, french_entry, dataset=french_dataset).table("monthly")
    equity = _column(market.periods, market.column("Mkt-RF"))

    goyal_file = goyal_welch.parse(cache, goyal_entry, dataset=goyal_dataset)
    monthly = next(table for table in goyal_file.tables if table.table_id == "monthly")
    long_treasury = _column(monthly.periods, monthly.column("ltr"))
    corporate = _column(monthly.periods, monthly.column("corpr"))
    cash = _column(monthly.periods, monthly.column("Rfree"))

    commodity_table = aqr.parse(cache, aqr_entry, dataset=aqr_dataset).table
    commodity = _column(
        commodity_table.periods,
        commodity_table.column("Excess return of equal-weight commodities portfolio"),
    )

    periods = tuple(
        sorted(set(equity) & set(long_treasury) & set(corporate) & set(cash) & set(commodity))
    )
    columns = {
        "equity": np.array([equity[p] for p in periods]),
        "treasury": np.array([long_treasury[p] - cash[p] for p in periods]),
        "credit": np.array([corporate[p] - cash[p] for p in periods]),
        "commodity": np.array([commodity[p] for p in periods]),
        "cash": np.array([cash[p] for p in periods]),
    }
    return periods, columns


def _column(periods: Sequence[str], values: Sequence[float | None]) -> dict[str, float]:
    return {p: v for p, v in zip(periods, values, strict=True) if v is not None}


def _trend_legs(columns: Mapping[str, FloatArray]) -> tuple[FloatArray, FloatArray]:
    """The published trend leg (volatility-targeted) and the extended one (raw).

    The published leg costs 96 months of burn-in and starts in 1934-07. The extended leg
    drops only the outer volatility target — the per-position inverse-volatility sizing is
    still there — and starts in 1929-07, which is what makes 1929-32 priceable.
    """
    instruments = np.column_stack(
        [columns["equity"], columns["treasury"], columns["credit"], columns["commodity"]]
    )
    raw = time_series_momentum(instruments, spec=TimeSeriesMomentumSpec())
    targeted = volatility_targeted(
        raw, window=TREND_TARGET_WINDOW, target=TREND_TARGET_VOLATILITY
    )
    return targeted, raw


def _finite(*series: FloatArray) -> np.typing.NDArray[np.bool_]:
    mask = np.ones(series[0].size, dtype=bool)
    for item in series:
        mask &= np.isfinite(item)
    return mask


def _annualised_volatility(values: FloatArray) -> float:
    return float(np.std(values, ddof=1)) * math.sqrt(12.0)


# --------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------


def _drawdown_and_growth(
    base: FloatArray,
    sleeve: FloatArray,
    cash: FloatArray,
    *,
    weights: Sequence[float],
) -> list[tuple[float, float]]:
    """``(max drawdown, geometric return)`` at each weight, on one supplied sleeve path."""
    out: list[tuple[float, float]] = []
    for weight in weights:
        total = overlay_total_returns(
            base,
            sleeve,
            cash,
            weight=weight,
            fee=TREND_FEE,
            borrow_spread=STRESS_BORROW_SPREAD,
        )
        curve = np.cumprod(1.0 + total)
        out.append(
            (
                drawdown_summary(curve).max_drawdown,
                float(curve[-1]) ** (12 / total.size) - 1.0,
            )
        )
    return out


def _print_ladder(title: str, rungs: Sequence[DrawdownRung]) -> None:
    print(f"\n== {title}")
    print("   w    gross   geometric   volatility   Sharpe    max DD   under water")
    for rung in rungs:
        print(
            f"  {rung.weight:4.2f}  {rung.gross_notional:5.2f}x    "
            f"{rung.geometric_return:7.2%}      {rung.volatility:6.2%}   "
            f"{rung.sharpe:5.3f}   {rung.max_drawdown:7.2%}   "
            f"{rung.months_under_water:4d} mo"
        )


def main() -> None:
    periods, columns = _panel()
    print(f"panel intersection {periods[0]}..{periods[-1]}, {len(periods)} months")

    targeted, raw = _trend_legs(columns)
    published = _finite(targeted)
    extended = _finite(raw)
    labels = np.array(periods)
    print(
        f"published trend leg: {labels[published][0]}..{labels[published][-1]}, "
        f"{int(published.sum())} months, volatility "
        f"{_annualised_volatility(targeted[published]):.2%}"
    )
    print(
        f"extended trend leg:  {labels[extended][0]}..{labels[extended][-1]}, "
        f"{int(extended.sum())} months, volatility "
        f"{_annualised_volatility(raw[extended]):.2%}"
    )

    equity = columns["equity"]
    cash = columns["cash"]

    # ---------------------------------------------------------------- 1. reproduction
    rungs = drawdown_ladder(
        equity[published],
        targeted[published],
        cash[published],
        weights=LADDER,
        fee=TREND_FEE,
        borrow_spread=PUBLISHED_BORROW_SPREAD,
    )
    _print_ladder("§7 reproduced, published settings (no borrow spread charged)", rungs)

    charged = drawdown_ladder(
        equity[published],
        targeted[published],
        cash[published],
        weights=LADDER,
        fee=TREND_FEE,
        borrow_spread=STRESS_BORROW_SPREAD,
    )
    _print_ladder("the same ladder charging the repository's own 60 bp borrow spread", charged)

    # ---------------------------------------------------------------- 2. joint surface
    print("\n== joint stress surface, 30% overlay, 40,000 draws")
    print(
        "   prior: a_d ~ N(4.0%, 4.0%), rho ~ N(-0.08, 0.20), sigma_d ~ 12.6%*exp(0.25 z), "
        "s ~ 59bp*exp(0.80 z)"
    )
    print(
        "   copula          P(gap<0 | levered)  P(gap<0 | unlevered)  mean gap   p05 gap"
        "   ES(gap<0)"
    )
    surfaces = {}
    for name, copula in (
        ("independent", INDEPENDENT_COPULA),
        ("half adverse", _blend(INDEPENDENT_COPULA, ADVERSE_COPULA, 0.5)),
        ("adverse", ADVERSE_COPULA),
    ):
        prior = JointPrior(copula=copula, **PRIOR_CENTRES)
        surface = stress_surface(
            prior,
            base_excess_return=BASE_EXCESS_RETURN,
            base_volatility=BASE_VOLATILITY,
            fee=OVERLAY_FEE,
            weight=RECOMMENDED_WEIGHT,
            draws=DRAWS,
            rng=np.random.default_rng(SEED),
        )
        surfaces[name] = surface
        print(
            f"   {name:<14}  {surface.probability_negative_leverage_matched:17.1%}  "
            f"{surface.probability_negative_unlevered:19.1%}  "
            f"{surface.mean_leverage_matched * 100:+8.2f}  "
            f"{surface.quantiles_leverage_matched['p5'] * 100:+8.2f}  "
            f"{surface.conditional_shortfall * 100:+8.2f}"
        )
    worst = surfaces["adverse"].univariate_worst
    print(
        f"\n   worst single univariate cell (one axis at its own p01): "
        f"{worst * 100:+.2f} pp/yr"
    )
    for name, surface in surfaces.items():
        print(
            f"   P(joint gap worse than that single cell), {name}: "
            f"{surface.probability_worse_than_univariate_worst:.1%}"
        )
    print(
        "\n   prior mass below §5a's own worst printed cell (-1.26 pp/yr, the one joint "
        "row it contains):"
    )
    for name, copula in (
        ("independent", INDEPENDENT_COPULA),
        ("adverse", ADVERSE_COPULA),
    ):
        prior = JointPrior(copula=copula, **PRIOR_CENTRES)
        drawn = sample_joint_prior(prior, draws=DRAWS, rng=np.random.default_rng(SEED))
        gaps = np.array(
            [
                gap_pair(
                    OverlayInputs(
                        base_excess_return=BASE_EXCESS_RETURN,
                        base_volatility=BASE_VOLATILITY,
                        diversifier_excess_return=float(drawn["diversifier_excess_return"][i]),
                        diversifier_volatility=float(drawn["diversifier_volatility"][i]),
                        correlation=float(drawn["correlation"][i]),
                        financing_spread=float(drawn["financing_spread"][i]),
                        fee=OVERLAY_FEE,
                    ),
                    weight=RECOMMENDED_WEIGHT,
                ).versus_leverage_matched
                for i in range(DRAWS)
            ]
        )
        print(f"     {name:<14} {float(np.mean(gaps < -0.0126)):.1%}")

    print("\n   the same failure probability by overlay weight, adverse copula:")
    print("   weight   P(gap<0)   mean gap   p05 gap")
    for weight in (0.15, 0.25, 0.30, 0.50, 1.00):
        arm = stress_surface(
            JointPrior(copula=ADVERSE_COPULA, **PRIOR_CENTRES),
            base_excess_return=BASE_EXCESS_RETURN,
            base_volatility=BASE_VOLATILITY,
            fee=OVERLAY_FEE,
            weight=weight,
            draws=DRAWS,
            rng=np.random.default_rng(SEED),
        )
        print(
            f"   {weight:6.2f}   {arm.probability_negative_leverage_matched:8.1%}   "
            f"{arm.mean_leverage_matched * 100:+8.2f}   "
            f"{arm.quantiles_leverage_matched['p5'] * 100:+7.2f}"
        )
    print("\n   among failing draws, share with the axis beyond its own median (adverse copula):")
    for axis, share in surfaces["adverse"].driver_shares.items():
        print(f"     {axis:<28} {share:.1%}")

    # ---------------------------------------------------------------- 3. the boundary
    print("\n== prior-free boundary: financing spread the 30% overlay can absorb, pp/yr")
    print("   rows: gross trend excess return; columns: correlation to equity")
    correlations = (-0.20, -0.08, 0.00, 0.20, 0.30, 0.50)
    print("   a_d      " + "".join(f"{c:+8.2f}" for c in correlations))
    for a_d in (0.00, 0.02, 0.04, 0.06, 0.08, 0.12):
        spreads = [
            tolerable_financing_spread(
                base_excess_return=BASE_EXCESS_RETURN,
                base_volatility=BASE_VOLATILITY,
                diversifier_excess_return=a_d,
                diversifier_volatility=0.126,
                correlation=c,
                fee=OVERLAY_FEE,
                weight=RECOMMENDED_WEIGHT,
            )
            for c in correlations
        ]
        print(f"   {a_d:6.2%}  " + "".join(f"{v * 100:+8.2f}" for v in spreads))

    # ---------------------------------------------------------------- 4. drawdown attack
    print("\n== the flat-drawdown claim, resampled")
    print(
        f"   circular block bootstrap, {BLOCK_MONTHS}-month blocks, {RESAMPLES} paired "
        "resamples, seed fixed"
    )
    print("   w     observed  mean    95% interval on mdd(w)-mdd(0)   P(overlay deeper)")
    for weight in (0.25, 0.30, 0.50, 1.00, 2.00):
        interval = paired_drawdown_bootstrap(
            equity[published],
            targeted[published],
            cash[published],
            weight=weight,
            resamples=RESAMPLES,
            block_length=BLOCK_MONTHS,
            rng=np.random.default_rng(SEED + 1),
            fee=TREND_FEE,
            borrow_spread=STRESS_BORROW_SPREAD,
        )
        print(
            f"  {weight:4.2f}   {interval.observed_difference:+7.2%}  "
            f"{interval.mean_difference:+7.2%}   "
            f"[{interval.interval[0]:+7.2%}, {interval.interval[1]:+7.2%}]      "
            f"{interval.probability_deeper:6.1%}"
        )

    # ---------------------------------------------------------------- 5. crisis windows
    print("\n== crisis windows, peak-to-trough of the stacked portfolio")
    print("   window                    n    w=0.00    w=0.30    w=1.00    covered?")
    for name, (start, end) in CRISIS_WINDOWS.items():
        keep = [i for i, p in enumerate(periods) if start <= p <= end]
        covered = [i for i in keep if published[i]]
        if not covered:
            extended_only = [i for i in keep if extended[i]]
            marker = "extended arm only" if extended_only else "NOT IN PANEL"
            print(f"   {name:<24} {len(keep):3d}       --        --        --    {marker}")
            continue
        take = np.array(covered, dtype=np.intp)
        cells = []
        for weight in (0.0, RECOMMENDED_WEIGHT, 1.0):
            total = overlay_total_returns(
                equity[take],
                targeted[take],
                cash[take],
                weight=weight,
                fee=TREND_FEE,
                borrow_spread=STRESS_BORROW_SPREAD,
            )
            cells.append(drawdown_summary(np.cumprod(1.0 + total)).max_drawdown)
        flag = "yes" if len(covered) == len(keep) else f"partial {len(covered)}/{len(keep)}"
        print(
            f"   {name:<24} {len(covered):3d}  " + "".join(f"{c:+8.2%}  " for c in cells) + flag
        )

    # ---------------------------------------------------------------- 6. the 1929 arm
    print("\n== the extended arm: the same ladder on a window that contains 1929-32")
    scale = _annualised_volatility(targeted[published]) / _annualised_volatility(raw[extended])
    print(
        f"   the raw leg carries {_annualised_volatility(raw[extended]):.2%} volatility "
        f"against the published leg's {_annualised_volatility(targeted[published]):.2%}, so "
        f"weights are multiplied by {scale:.2f} to match the risk contribution."
    )
    print(
        "   That scale factor is a single full-sample constant and is therefore look-ahead "
        "in LEVEL. It changes no sign and no date, so it cannot manufacture a drawdown "
        "result; it is stated because a reader must not quote the growth figures as "
        "out-of-sample."
    )
    extended_rungs = drawdown_ladder(
        equity[extended],
        raw[extended] * scale,
        cash[extended],
        weights=LADDER,
        fee=TREND_FEE,
        borrow_spread=STRESS_BORROW_SPREAD,
    )
    _print_ladder(
        f"extended ladder, {labels[extended][0]}..{labels[extended][-1]}, "
        f"{int(extended.sum())} months",
        extended_rungs,
    )
    for name in ("1929-32 great crash", "1937-38"):
        start, end = CRISIS_WINDOWS[name]
        rows = np.array(
            [i for i, p in enumerate(periods) if start <= p <= end and extended[i]], dtype=np.intp
        )
        if rows.size == 0:
            continue
        depths: list[float] = []
        for weight in (0.0, RECOMMENDED_WEIGHT, 1.0, 2.0):
            total = overlay_total_returns(
                equity[rows],
                raw[rows] * scale,
                cash[rows],
                weight=weight,
                fee=TREND_FEE,
                borrow_spread=STRESS_BORROW_SPREAD,
            )
            depths.append(drawdown_summary(np.cumprod(1.0 + total)).max_drawdown)
        print(
            f"   {name:<24} {rows.size:3d} mo   " + "".join(f"{c:+9.2%}" for c in depths)
            + "   (w = 0.00, 0.30, 1.00, 2.00)"
        )

    # ---------------------------------------------------------------- 7. stressed rho
    print("\n== correlation forced positive inside equity drawdowns only")
    print(
        "   the crisis-window mean and volatility of the trend leg are preserved exactly; "
        "only its co-movement with equity changes."
    )
    print("   target rho   crisis n   full-sample rho   w=0.30 max DD   w=1.00 max DD   w=0.30 geo")
    for target in (-0.20, 0.00, 0.30, 0.60, 0.90):
        stressed = stress_crisis_correlation(
            equity[published],
            targeted[published],
            target_correlation=target,
            drawdown_threshold=0.10,
        )
        pairs = _drawdown_and_growth(
            equity[published], stressed.stressed, cash[published], weights=(RECOMMENDED_WEIGHT, 1.0)
        )
        print(
            f"   {target:+8.2f}   {stressed.crisis_months:8d}   "
            f"{stressed.full_sample_correlation_after:+15.3f}   "
            f"{pairs[0][0]:+13.2%}   {pairs[1][0]:+13.2%}   {pairs[0][1]:10.2%}"
        )

    print("\n   the same, with the trend leg additionally earning ZERO inside those months")
    print("   (the plan's 'simultaneous loss in both sides of a return stack')")
    print("   target rho   w=0.30 max DD   w=1.00 max DD   w=0.30 geo   w=0.00 geo")
    baseline_total = overlay_total_returns(
        equity[published], targeted[published], cash[published], weight=0.0
    )
    baseline_growth = float(np.prod(1.0 + baseline_total)) ** (12 / baseline_total.size) - 1.0
    for target in (0.00, 0.30, 0.60, 0.90):
        stressed = stress_crisis_correlation(
            equity[published],
            targeted[published],
            target_correlation=target,
            drawdown_threshold=0.10,
            crisis_mean=0.0,
        )
        pairs = _drawdown_and_growth(
            equity[published], stressed.stressed, cash[published], weights=(RECOMMENDED_WEIGHT, 1.0)
        )
        print(
            f"   {target:+8.2f}   {pairs[0][0]:+13.2%}   {pairs[1][0]:+13.2%}   "
            f"{pairs[0][1]:10.2%}   {baseline_growth:10.2%}"
        )

    # ---------------------------------------------------------------- 8. failure modes
    print("\n== forced deleveraging inside the stacked fund")
    print("   trigger  restore   months cut   geometric   max DD    growth cost   DD change")
    for trigger, restore in ((0.15, 1.00), (0.20, 1.00), (0.20, 0.90), (0.30, 1.00)):
        outcome = forced_deleveraging(
            equity[published],
            targeted[published],
            cash[published],
            weight=RECOMMENDED_WEIGHT,
            trigger=trigger,
            reduced_weight=0.0,
            restore_fraction=restore,
            fee=TREND_FEE,
            borrow_spread=STRESS_BORROW_SPREAD,
        )
        print(
            f"   {trigger:6.0%}   {restore:6.0%}   {outcome.months_deleveraged:10d}   "
            f"{outcome.geometric_return:9.2%}   {outcome.max_drawdown:+7.2%}   "
            f"{outcome.geometric_cost_versus_unconstrained * 100:+11.2f}   "
            f"{outcome.drawdown_change_versus_unconstrained * 100:+9.2f}"
        )

    print("\n== simultaneous loss in both stacked legs")
    joint = joint_loss_frequency(equity[published], targeted[published])
    print(f"   months                                    {joint.months}")
    print(f"   P(equity loses)                           {joint.probability_base_loses:.3f}")
    print(f"   P(trend loses)                            {joint.probability_diversifier_loses:.3f}")
    print(f"   P(both lose)                              {joint.probability_both_lose:.3f}")
    print(f"   independence benchmark                    {joint.independence_benchmark:.3f}")
    print(f"   Gaussian-copula benchmark                 {joint.gaussian_benchmark:.3f}")
    print(f"   lift over independence                    {joint.lift_over_independence:.3f}x")
    print(
        f"   P(trend loses | equity in worst decile)   "
        f"{joint.probability_both_lose_given_base_tail:.3f}"
    )
    print(f"   worst single month, both legs summed      {joint.worst_joint_month:.2%}")

    print("\n== fund closure, from the only cohort this repository has measured")
    hazard = closure_hazard(cohort=25, deaths=13, years_observed=6.5, hold_years=20.0)
    print(
        "   13 of 25 managed-futures funds filing at 2019-07 had stopped by 2025-12 "
        "(Experiment 012)"
    )
    print(
        f"   annual hazard {hazard.annual_hazard:.1%} "
        f"[{hazard.annual_hazard_interval[0]:.1%}, {hazard.annual_hazard_interval[1]:.1%}]"
    )
    for years in (5.0, 10.0, 20.0):
        at_horizon = closure_hazard(cohort=25, deaths=13, years_observed=6.5, hold_years=years)
        print(
            f"   P(the specific fund held closes within {years:4.0f} years) "
            f"{at_horizon.probability_of_closure_within_hold:.1%} "
            f"[{at_horizon.probability_interval_within_hold[0]:.1%}, "
            f"{at_horizon.probability_interval_within_hold[1]:.1%}]"
        )

    overlay_excess = (
        overlay_total_returns(
            equity[published],
            targeted[published],
            cash[published],
            weight=RECOMMENDED_WEIGHT,
            fee=TREND_FEE,
            borrow_spread=STRESS_BORROW_SPREAD,
        )
        - cash[published]
    )

    print("\n== what the 30% overlay is worth on this panel, beside its resolution floor")
    for scaling in SCALINGS:
        gap, mde = matched_volatility_gap(overlay_excess, equity[published], scaling=scaling)
        verdict = "resolved" if abs(gap) >= mde else "BELOW THE FLOOR"
        print(
            f"   versus {scaling:<17} gap {gap * 100:+6.2f} pp/yr   "
            f"MDE(80%) {mde * 100:5.2f}   {verdict}"
        )
    print(
        "   The two rows are two different claims and are never added. The unlevered row "
        "is the arithmetic\n   excess difference, not a growth difference, and is the "
        "smaller question."
    )

    print("\n== removing the strongest episodes, on the leverage-matched gap")
    groups: dict[str, list[int]] = {}
    for name, (start, end) in CRISIS_WINDOWS.items():
        window_rows = [i for i, p in enumerate(labels[published]) if start <= p <= end]
        if window_rows:
            groups[f"drop {name}"] = window_rows
    decade_labels = sorted({str(p)[:3] + "0s" for p in labels[published]})
    for decade in decade_labels:
        groups[f"drop the {decade}"] = [
            i for i, p in enumerate(labels[published]) if str(p)[:3] + "0s" == decade
        ]
    removals = leave_out_gaps(
        overlay_excess, equity[published], scaling="leverage_matched", groups=groups
    )
    ranked = sorted(removals, key=lambda row: row.change_from_full_sample)
    print("   removed                          n     gap      change")
    for row in ranked[:6]:
        print(
            f"   {row.removed:<30} {row.months_removed:4d}  {row.gap * 100:+6.2f}  "
            f"{row.change_from_full_sample * 100:+7.2f}"
        )
    print("   ...")
    for row in ranked[-2:]:
        print(
            f"   {row.removed:<30} {row.months_removed:4d}  {row.gap * 100:+6.2f}  "
            f"{row.change_from_full_sample * 100:+7.2f}"
        )

    print("\n== five-year manager underperformance")
    print("   horizon   P(gap<0)   median gap   worst gap   MDE at that horizon")
    for scaling in SCALINGS:
        print(f"   against the {scaling} control:")
        for horizon in (3, 5, 10):
            estimate = drought_probability(
                overlay_excess,
                equity[published],
                scaling=scaling,
                horizon_months=horizon * 12,
                resamples=RESAMPLES,
                block_length=BLOCK_MONTHS,
                rng=np.random.default_rng(SEED + 2),
            )
            print(
                f"     {horizon:2d}y       {estimate.probability_negative_gap:6.1%}   "
                f"{estimate.median_gap * 100:+10.2f}   {estimate.worst_gap * 100:+9.2f}   "
                f"{estimate.minimum_detectable_effect * 100:9.2f}"
            )
    print(
        "   The leverage-matched gap is invariant to any constant rescaling of the "
        "benchmark, so passing\n   equity levered 1.30x gives the identical row. It is one "
        "observation, not two."
    )

    print("\n== a five-year review, and whether it predicts anything")
    cost = abandonment_cost(
        overlay_excess,
        equity[published],
        scaling="leverage_matched",
        review_years=5,
        subsequent_years=5,
    )
    print(f"   overlapping 5-year windows                {cost.windows}")
    print(
        "   P(a review shows the overlay behind)      "
        f"{cost.probability_review_shows_a_loss:.1%}"
    )
    print(
        f"   mean next-5-year gap after a bad review   "
        f"{cost.mean_subsequent_gap_after_a_bad_review * 100:+.2f} pp/yr"
    )
    print(
        f"   mean next-5-year gap after a good review  "
        f"{cost.mean_subsequent_gap_after_a_good_review * 100:+.2f} pp/yr"
    )
    print(
        "   MDE on the full monthly paired difference "
        f"{cost.minimum_detectable_effect * 100:.2f}"
    )

    print(
        "\n== NOT ESTIMATED, and why\n"
        "   Methodology change inside a live fund produces no observable event in any\n"
        "   census this repository holds: N-PORT records returns and net assets, not\n"
        "   prospectus amendments, and the closure hazard above prices only the funds that\n"
        "   stopped filing. Thirteen capital-efficient series exist and none is six years\n"
        "   old, so there is no cohort to measure a methodology-change rate on at all. The\n"
        "   probability is not small and it is not estimable here; it is a reason to prefer\n"
        "   a monitorable rule to a point estimate."
    )


def _blend(
    left: tuple[tuple[float, ...], ...], right: tuple[tuple[float, ...], ...], weight: float
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple((1.0 - weight) * a + weight * b for a, b in zip(row_l, row_r, strict=True))
        for row_l, row_r in zip(left, right, strict=True)
    )


if __name__ == "__main__":  # pragma: no cover - a report, not a library entry point
    main()
