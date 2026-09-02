"""Regenerates the tables in ``docs/research/leverage-and-the-notional-budget.md``.

Kept separate from :mod:`portfolio_edge.studies.notional_budget` so the study itself stays
pure and testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.notional_budget

**The panel is not built here.** It is imported from
:mod:`portfolio_edge.studies._overlay_stress_tables`, which owns it, so that this page and
``docs/research/capital-efficiency-and-breadth.md`` cannot drift apart on the instrument.
That panel is US equity (Ken French ``Mkt-RF``), long Treasury and corporate excess returns
(Goyal-Welch ``ltr``, ``corpr`` less ``Rfree``), an AQR equal-weight commodity excess
return, and Goyal-Welch ``Rfree`` as cash; the trend leg is the Moskowitz-Ooi-Pedersen
construction run on those four instruments, volatility-targeted on a trailing 60-month
window and charged 95 bp/yr. It runs 1934-07 to 2025-05, 1,091 months, and **1929-32 is
absent by construction** because the trend leg's burn-in consumes it.

**Three things this file does that the panel does not licence.**

*The trend leg is an index-like construction, not RSST.* Every figure below that involves
the trend leg is a figure about *the exposure*, and the fund delivers less of it than one
for one: RSST's loading on the AQR index, measured from its own Form N-PORT returns, is
+0.681 [+0.406, +0.955] over 31 months to 2026-04
(``docs/research/loading-comparability-and-wrapper-exposure.md``). Reading a figure here as
a figure about the fund therefore overstates the trend leg by roughly a third, and the
31-month interval is wide enough that the size of that overstatement is itself uncertain.

*The exposure arithmetic is the only forecast-free section.* §1 sums filed notionals. Every
growth number below §1 takes a premium forecast, and the tables print the whole surface
rather than one cell precisely because the answer's sign turns on it.

*The financing spreads are borrowed, not measured here.* No fund on the shelf discloses one.
Their sources are printed beside each number in §4 and are canonical in
``docs/research/structural-and-tax-edges.md``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Final

import numpy as np

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.kelly import kelly_leverage
from portfolio_edge.experiments.exp_011_overlay_stack import minimum_detectable_effect
from portfolio_edge.inference.deflated_sharpe import (
    deflated_sharpe_ratio,
    effective_number_of_trials,
    mean_off_diagonal_correlation,
    trial_dispersion_from_sharpes,
)
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni
from portfolio_edge.studies._overlay_stress_tables import (
    BLOCK_MONTHS,
    CRISIS_WINDOWS,
    RESAMPLES,
    SEED,
    TREND_FEE,
    _finite,
    _panel,
    _trend_legs,
)
from portfolio_edge.studies.equity_share import (
    growth_retained_fraction,
    optimal_kelly_shrinkage,
    plug_in_growth_cost,
)
from portfolio_edge.studies.notional_budget import (
    FinancingLeg,
    Holding,
    LeveragePathResult,
    NotionalLeg,
    apply_leverage,
    financing_stack,
    gross_notional_ladder,
    growth_optimal_pair,
    horizon_outcomes,
    kinked_growth_optimal_leverage,
    leverage_confidence_interval,
    notional_for_drawdown,
    portfolio_exposure,
    premium_for_leverage,
    relative_run_outcomes,
    volatility_targeted_leverage,
)
from portfolio_edge.studies.outperformance_horizon import horizon_for_confidence
from portfolio_edge.studies.overlay_stress import (
    forced_deleveraging,
    paired_drawdown_bootstrap,
)

FloatArray = np.typing.NDArray[np.float64]

# --------------------------------------------------------------------------------
# The candidate portfolio, from filings. Sources are in src/content/shelf.ts.
# --------------------------------------------------------------------------------

#: The share of capital the investor proposes to put in the stacked fund.
STACKED_WEIGHT: Final = 0.30

#: RSST, N-PORT 2026-04-30: 74.09% of net assets in a physical S&P 500 fund plus 33.1% of
#: E-mini futures notional is 107.2% equity; the managed-futures book runs ~294% gross
#: notional to deliver ~100% of risk exposure.
RSST_LEGS: Final = (
    NotionalLeg("us-equity", 1.072),
    NotionalLeg("trend", 1.000),
)
#: RSSB, N-PORT 2026-04-30. RSSB's base leg is *global* equity where this reader's
#: incumbent is US, which is why no single displacement scores it.
RSSB_LEGS: Final = (
    NotionalLeg("global-equity", 1.0007),
    NotionalLeg("treasury-futures", 1.0033),
)
#: NTSX, N-PORT 2026-03-31.
NTSX_LEGS: Final = (
    NotionalLeg("us-equity", 0.9083),
    NotionalLeg("treasury-futures", 0.6350),
)
#: MATE, N-PORT 2026-02-28: an S&P 500 ETF at 49.8% of net assets **plus a long E-mini
#: S&P 500 future at 61.8%**, so the base leg is 111.6%, not 49.8%. At 2026-05-31 the two
#: read 50.30% and 65.57% for a base leg of 115.87%. Reading the ETF line alone put MATE in
#: the range where a wrapper is worse than selling equity outright, and it is not there.
#: The trend leg here is the PROSPECTUS TARGET of 100%, not a filed number: the index
#: future is not separable into base completion and the trend book's own equity position,
#: because both sleeves trade equity-index futures and no filing tags a contract by sleeve
#: (docs/research/capital-efficiency-and-breadth.md).
MATE_MAY_LEGS: Final = (NotionalLeg("us-equity", 1.1587), NotionalLeg("trend", 1.000))
MATE_FEB_LEGS: Final = (NotionalLeg("us-equity", 1.1156), NotionalLeg("trend", 1.000))
#: JPFP is NOT given a notional profile. It commenced operations 2026-05-27, its series
#: S000101300 appears in none of its trust's 24 N-PORT filings for the 2026-05-31 period,
#: and its first holdings filing is due 2026-08-29 or 2026-09-29. Until one exists there is
#: no base leg, no diversifier leg and no gross notional. A prospectus sentence
#: ("aggregate notional exposure will exceed its net assets") is not a number, and putting
#: an assumed 1.0 + 1.0 in a table would manufacture the very figure this page exists to
#: compute. `not filed`, with a date attached, is the finding.
JPFP_STATUS: Final = (
    "NOT FILED. No Form N-PORT exists (series S000101300, checked 2026-08-22); first due "
    "2026-08-29 or 2026-09-29. No base leg, no diversifier leg, no gross notional. The "
    "only established facts are a 59 bp unitary fee with no waiver and $17.07m of net "
    "assets. This row is deliberately empty."
)

#: The incumbent the stacked fund's capital is taken from.
VTI_FEE: Final = 0.0003
RSST_FEE: Final = 0.0099
NTSX_FEE: Final = 0.0020
RSSB_FEE: Final = 0.0039

#: Financing spreads, none of them measured in this repository and none disclosed by any
#: fund. Canonical in docs/research/structural-and-tax-edges.md.
EQUITY_FUTURES_SPREAD: Final = 0.0062
TREASURY_FUTURES_SPREAD: Final = 0.0015
TREND_BOOK_SPREAD: Final = 0.0000
TREND_BOOK_SPREAD_STRESS: Final = 0.0025

# --------------------------------------------------------------------------------
# Grids. Every one is declared here rather than chosen after seeing a result.
# --------------------------------------------------------------------------------

PREMIUM_GRID: Final = (0.01, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06)
VOLATILITY_GRID: Final = (0.13, 0.155, 0.18, 0.22)
KELLY_FRACTIONS: Final = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
HORIZONS: Final = (10.0, 20.0, 30.0)
#: The vol-targeting family. One declared target, five windows: the Sharpe ratio of a
#: volatility-scaled series is near-invariant to the target level, so varying the window is
#: the search that could actually find something and varying the target is not.
VOL_TARGET: Final = 0.15
VOL_WINDOWS: Final = (3, 6, 12, 24, 36)
VOL_CAP: Final = 2.0
VOL_FLOOR: Final = 0.0
#: Round-trip cost per unit of notional traded. A retail investor moving between a core ETF
#: and a stacked one pays a spread on both sides; 10 bp is the central assumption and 5 and
#: 20 bp bracket it.
ROUND_TRIP_COSTS: Final = (0.0005, 0.0010, 0.0020)
CENTRAL_ROUND_TRIP: Final = 0.0010

#: Drawdown tolerances a reader might state. Depth only; the ladder prints months too.
DRAWDOWN_TOLERANCES: Final = (-0.30, -0.40, -0.50, -0.60)

#: The valuation-conditioned drawdown pair, measured in this session and canonical in the
#: valuation page: entries above CAPE 30 ran a median -51.8% REAL drawdown over the next
#: fifteen years against -36.7% for entries below CAPE 20. US CAPE is 41.18 at 2026-08-01.
#: The pair is used here only as a RATIO, because the ladder below is nominal and those two
#: figures are real, and a ratio of two real drawdowns is the part that transfers.
CAPE_CONDITIONED_DRAWDOWN: Final = -0.518
CAPE_UNCONDITIONED_DRAWDOWN: Final = -0.367

#: The overlay-weight grid for the cliff scan, deliberately fine through the region
#: decision 0009 names so that a claimed doubling can be located rather than assumed.
CLIFF_GRID: Final = (0.10, 0.25, 0.30, 0.40, 0.50, 0.56, 0.58, 0.59, 0.60, 0.62, 0.70, 1.00, 2.00)
#: Four seeds, because a jump that moves with the seed is a resampling artefact.
CLIFF_SEEDS: Final = (SEED + 1, 12345, 999983, 20260822)
#: Where the identity of the worst drawdown episode is checked on the actual path.
EPISODE_SCAN: Final = (0.0, 0.05, 0.10, 0.30, 0.58, 0.59, 0.60, 1.00)

#: Forward GROSS trend excess returns to restate every measured row at. The panel's own
#: realised figure is far above anything this repository can sign forward. Zero is
#: included because a forecast of zero is admissible and the sleeve still has to be
#: scored at it. The three other rows, and their status:
#:
#: * 1.80% is decision 0004's convention and is RETRACTED as a gross figure. The
#:   adversarial review (docs/research/adversarial-review.md section 1) traced it to AQR
#:   TSMOM 2012-01..2025-12 taken geometrically and net of a 1.50% fee the wrapper's cost
#:   term already charges. It is kept so every table that was built on it can be read
#:   against its corrected value, and it must not be read as a central case.
#: * 3.90% is the trend-weight page's prior median, +2.73% net of the wrapper's 1.165%
#:   all-in cost, put back on this table's gross axis: 2.73 + 1.165 = 3.895. This table
#:   then charges its own 96 bp convention, so the same row reads 2.94% net here; the two
#:   pages' cost conventions differ by 21 bp and that difference is stated rather than
#:   merged. Both figures are at the tournament panel's 12.38% trend volatility; this
#:   panel's leg runs 12.46%, and a Sharpe-preserving rescale would move the row by
#:   +0.03 pp, inside the rounding.
#: * 4.07% is the same 1.80 restated to one basis by the review: 1.80 + 1.50 of fee
#:   + 0.77 of variance drag at 12.38% volatility. It is the corrected central case.
FORWARD_TREND_PREMIA: Final = (0.000, 0.018, 0.037, 0.039, 0.0407)
#: The rows of the section 6a weight ladder, in the order the page reads them.
HOLDABILITY_PREMIA: Final = (0.0407, 0.039, 0.018, 0.000)
#: Capital in the wrapper for the section 6a weight ladder. Each row's equity notional
#: follows the filing (1.072 of equity per dollar of RSST) rather than being held at 1.0.
HOLDABILITY_WEIGHTS: Final = (0.15, 0.20, 0.25, 0.30, 0.35)
#: The relative-drawdown trigger the trend-weight page's capitulation arm uses, so the
#: probabilities in section 6a and the abandonment probabilities there are one quantity.
RELATIVE_RUN_TRIGGER: Final = -0.20


# --------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------


def _two_leg_total(
    base_excess: FloatArray,
    sleeve_excess: FloatArray,
    cash: FloatArray,
    *,
    base_notional: float,
    sleeve_notional: float,
    cost: float,
    periods_per_year: int = 12,
) -> FloatArray:
    """One month-by-month total return of a two-leg financed portfolio."""
    return np.asarray(
        base_notional * base_excess
        + sleeve_notional * sleeve_excess
        - cost / periods_per_year
        + cash,
        dtype=np.float64,
    )


def _restate_mean(
    series: FloatArray, *, annual_mean: float, periods_per_year: int = 12
) -> FloatArray:
    """Shift a series to a stated annual mean, leaving volatility and every correlation
    with any other series exactly unchanged. A level shift is the only honest way to ask
    "what if the forward premium is lower", because it changes the one moment that is a
    forecast and touches none of the moments the sample can actually estimate."""
    values = np.asarray(series, dtype=np.float64)
    return np.asarray(
        values - float(np.mean(values)) + annual_mean / periods_per_year, dtype=np.float64
    )


def _window_mask(periods: Sequence[str], start: str, end: str) -> np.typing.NDArray[np.bool_]:
    return np.array([start <= period <= end for period in periods], dtype=bool)


def _peak_to_trough(total: FloatArray) -> float:
    return drawdown_summary(np.cumprod(1.0 + total)).max_drawdown


def _print_exposure(label: str, holdings: Sequence[Holding], note: str = "") -> None:
    summary = portfolio_exposure(holdings)
    legs = "  ".join(f"{kind} {value:+.4f}" for kind, value in summary.by_kind.items())
    print(
        f"  {label:<34} gross {summary.gross_notional:6.4f}  "
        f"equity {summary.equity_notional:6.4f}  "
        f"financed {summary.financed_notional:+7.4f}  cash {summary.cash_weight:5.2f}"
    )
    print(f"     legs: {legs}")
    if note:
        print(f"     {note}")


# --------------------------------------------------------------------------------
# The report
# --------------------------------------------------------------------------------


def main() -> None:
    periods, columns = _panel()
    targeted, _raw = _trend_legs(columns)
    mask = _finite(columns["equity"], columns["cash"], targeted)
    equity = columns["equity"][mask]
    cash = columns["cash"][mask]
    trend = targeted[mask]
    window = np.array(periods)[mask]
    months = int(equity.size)

    equity_volatility = float(np.std(equity, ddof=1)) * math.sqrt(12.0)
    equity_premium = float(np.mean(equity)) * 12.0
    trend_volatility = float(np.std(trend, ddof=1)) * math.sqrt(12.0)
    trend_premium = float(np.mean(trend)) * 12.0
    correlation = float(np.corrcoef(equity, trend)[0, 1])
    years = months / 12.0

    print(
        f"panel {window[0]}..{window[-1]}  {months} months  ({years:.1f} years)\n"
        f"  equity excess {equity_premium * 100:.2f}%/yr at {equity_volatility * 100:.2f}% vol\n"
        f"  trend  excess {trend_premium * 100:.2f}%/yr at {trend_volatility * 100:.2f}% vol"
        f"  (net of the {TREND_FEE * 100:.2f}% construction fee)\n"
        f"  equity/trend correlation {correlation:+.4f}\n"
        f"  mean cash rate {float(np.mean(cash)) * 100 * 12:.2f}%/yr\n"
    )

    # ----------------------------------------------------------------------------
    print("== 1. exposure arithmetic: no forecast anywhere in this section ==")
    core = Holding("core US equity", 1.0 - STACKED_WEIGHT, (NotionalLeg("us-equity", 1.0),))
    _print_exposure(
        f"{STACKED_WEIGHT:.0%} RSST + core",
        [core, Holding("RSST", STACKED_WEIGHT, RSST_LEGS)],
        "RSST N-PORT 2026-04-30; 74.09% physical S&P 500 + 33.1% E-mini = 107.2% equity",
    )
    _print_exposure(
        f"{STACKED_WEIGHT:.0%} RSSB + core",
        [core, Holding("RSSB", STACKED_WEIGHT, RSSB_LEGS)],
        "base leg is GLOBAL equity where the incumbent is US: two decisions, not one",
    )
    _print_exposure(
        f"{STACKED_WEIGHT:.0%} NTSX + core",
        [core, Holding("NTSX", STACKED_WEIGHT, NTSX_LEGS)],
        "NTSX N-PORT 2026-03-31",
    )
    _print_exposure(
        f"{STACKED_WEIGHT:.0%} MATE + core (2026-05-31)",
        [core, Holding("MATE", STACKED_WEIGHT, MATE_MAY_LEGS)],
        "base leg 50.30% IVV + 65.57% E-mini = 115.87%; trend leg is the prospectus's "
        "100% target, because the E-mini line is not separable between the two sleeves",
    )
    _print_exposure(
        f"{STACKED_WEIGHT:.0%} MATE + core (2026-02-28)",
        [core, Holding("MATE", STACKED_WEIGHT, MATE_FEB_LEGS)],
        "the earlier filing reads the same way at 111.56% equity",
    )
    print(f"  {'30% JPFP + core':<34} {'-- no figure --':>60}")
    print(f"     {JPFP_STATUS}")
    print(
        "\n  A DERIVATIVE BOOK IS NOT AN EXPOSURE, AND THE TWO MUST NOT BE SUMMED.\n"
        "  Every figure above is NET ECONOMIC EXPOSURE per dollar of capital: the\n"
        "  directional risk the holder carries. It is not the funds' gross derivative\n"
        "  book, which is much larger and measures the number of contracts rather than the\n"
        "  amount of risk:\n"
        "    RSST   trend book ~294% of net assets  ->  ~100% of trend RISK\n"
        "           exposure\n"
        "    MATE   derivative book 404.5% of net assets at 2026-05-31\n"
        "           (284.2% futures + 120.3% FX forwards)  ->  100% trend target\n"
        "  A long/short trend book is long some contracts and short others, so its legs\n"
        "  offset; a 120.3% FX-forward book is not 120.3% of directional risk, and on a\n"
        "  volatility-targeted book the gross figure is an artefact of the risk target\n"
        "  rather than an exposure. MATE's book moved from 339% to 404.5% of net assets\n"
        "  between two filings while its stated targets did not move at all, which is the\n"
        "  clearest possible demonstration that the gross derivative number is not the\n"
        "  quantity a portfolio is sized on. Summing derivative notionals across the two\n"
        "  funds would put the candidate at roughly 2.0x 'gross' on RSST and 2.2x on MATE,\n"
        "  and both numbers would be meaningless.\n"
        "\n  the same NET gross notional reached two ways, which is the point of the section:"
    )
    _print_exposure(
        "levered equity at matched gross",
        [Holding("levered equity", 1.0, (NotionalLeg("us-equity", 1.0216),))],
        "gross 1.0216 of equity beta alone is NOT the same risk as 1.0216 + 0.30 trend",
    )

    candidate = portfolio_exposure([core, Holding("RSST", STACKED_WEIGHT, RSST_LEGS)])
    base_notional = candidate.equity_notional
    sleeve_notional = candidate.non_equity_notional
    gross = candidate.gross_notional

    # ----------------------------------------------------------------------------
    print("\n== 2. where the leverage recommendation changes sign ==")
    print(
        "  the premium at which each exposure is growth-optimal, mu-r = L sigma**2.\n"
        "  read it backwards: the exposure you hold IS a premium forecast.\n"
    )
    print("   sigma  " + "".join(f"  L={lev:5.2f}" for lev in (0.8, 1.0, gross, 1.5, 2.0)))
    for volatility in VOLATILITY_GRID:
        cells = "".join(
            f"  {premium_for_leverage(leverage=lev, volatility=volatility) * 100:6.2f}%"
            for lev in (0.8, 1.0, gross, 1.5, 2.0)
        )
        print(f"  {volatility * 100:5.1f}%{cells}")
    print(
        f"\n  the sign flip: at sigma = {equity_volatility * 100:.2f}% the growth-optimal "
        f"exposure is exactly 1.0 at a premium of {equity_volatility ** 2 * 100:.2f}%/yr.\n"
        "  BELOW that premium the growth objective wants LESS than a fully invested\n"
        "  portfolio and any leverage at all is overbetting. This is the same quantity as\n"
        "  the funding-rule gap a_p - sigma_p**2, written as a break-even.\n"
    )

    print("  growth-optimal exposure on a premium x volatility grid (frictionless):")
    print("   mu-r    " + "".join(f"  sig={v * 100:4.1f}%" for v in VOLATILITY_GRID))
    for premium in PREMIUM_GRID:
        cells = "".join(
            f"  {kelly_leverage(excess_return=premium, volatility=v):9.2f}"
            for v in VOLATILITY_GRID
        )
        print(f"  {premium * 100:5.2f}%{cells}")

    wrapper_spread = STACKED_WEIGHT * (RSST_FEE - VTI_FEE) / candidate.financed_notional
    print(
        f"\n  the same grid with a spread charged only on the FINANCED part, which is what\n"
        "  an investor actually faces. Three spreads: 0 bp, the repository's assumed 60 bp\n"
        f"  futures financing, and {wrapper_spread * 1e4:.0f} bp — the candidate's\n"
        "  own incremental\n"
        f"  wrapper fee ({STACKED_WEIGHT * (RSST_FEE - VTI_FEE) * 1e4:.1f} bp of"
        "  portfolio) divided by the\n"
        f"  {candidate.financed_notional:.4f} of financed notional it buys. The flat"
        "  1.00 band is the\n"
        "  kink, not a rounding artefact: a whole RANGE of premium forecasts implies\n"
        "  holding exactly what you have, and the range is as wide as the spread."
    )
    for spread in (0.0, 0.0060, wrapper_spread):
        print(f"\n   borrow spread {spread * 1e4:5.1f} bp")
        print("   mu-r    " + "".join(f"  sig={v * 100:4.1f}%" for v in VOLATILITY_GRID))
        for premium in PREMIUM_GRID:
            cells = "".join(
                "  "
                + f"{kinked_growth_optimal_leverage(excess_return=premium, volatility=v, borrow_spread=spread):9.2f}"  # noqa: E501
                for v in VOLATILITY_GRID
            )
            print(f"  {premium * 100:5.2f}%{cells}")

    print(
        "\n  WHERE TODAY'S PREMIUM PROXY LANDS ON THAT GRID. The TIPS-based excess CAPE\n"
        "  yield is at the 0th percentile of the entire 2003-2026 TIPS record, +0.02 to\n"
        "  +0.08 pp, with the 10-year real yield at 2.35% (measured this session; canonical\n"
        "  in the valuation page). An excess CAPE yield near zero is a GEOMETRIC real\n"
        "  premium over long TIPS; the Kelly numerator wants an ARITHMETIC excess over\n"
        "  cash, which adds roughly sigma**2/2 and then subtracts a term premium. That\n"
        "  lands somewhere near the 1.00% to 2.00% rows above, where the growth-optimal\n"
        "  exposure is 0.21 to 1.18 and the FRICTIONLESS answer is already below 1.0 at\n"
        "  every volatility of 15.5% or more. It is NOT a timing signal — conditioning on\n"
        "  it fails out of sample and after tax — but a leverage recommendation derived\n"
        "  from a historical premium at a moment when the premium proxy is at a record low\n"
        "  is exactly the failure this repository exists to prevent."
    )

    print("\n  and whether the data can identify it at all:")
    print("   sample   L*(sample premium)   SE      95% interval        spans 1.0?")
    for span in (10.0, 20.0, 30.0, years):
        interval = leverage_confidence_interval(
            excess_return=equity_premium, volatility=equity_volatility, years=span
        )
        spans = interval.lower <= 1.0 <= interval.upper
        print(
            f"   {span:5.1f}y   {interval.point:16.2f}   {interval.standard_error:5.2f}   "
            f"[{interval.lower:+6.2f}, {interval.upper:+6.2f}]   {'YES' if spans else 'no'}"
        )
    print(
        "   SE(L*) = 1/(sigma sqrt(T)) contains no mu: precision comes from the calendar\n"
        "   span alone, so sampling more finely inside a window buys nothing (Merton 1980)."
    )

    print("\n  fractional Kelly, and what it costs to be at a fraction of the optimum:")
    print("   f      growth retained of peak excess")
    for fraction in KELLY_FRACTIONS:
        print(f"   {fraction:4.2f}   {growth_retained_fraction(fraction):+7.3f}")
    sharpe = equity_premium / equity_volatility
    print(f"\n   sample Sharpe of the base {sharpe:.4f}")
    print("   believed years of stationarity | growth cost 1/(2T) | growth-max shrinkage f*")
    for span in (10.0, 20.0, 30.0, years):
        print(
            f"   {span:29.1f} | {plug_in_growth_cost(span) * 100:16.2f}% | "
            f"{optimal_kelly_shrinkage(sharpe_ratio=sharpe, years=span):22.3f}"
        )
    print(
        "   The estimation-error argument, run correctly, does NOT support half Kelly:\n"
        "   with sigma known the plug-in optimum is unbiased and noisy, and what the noise\n"
        "   damages is achieved growth, not the estimate. Half Kelly is a claim about\n"
        "   non-stationarity and has to be argued as one\n"
        "   (docs/research/setting-the-equity-share.md §2.1)."
    )

    print("\n  the two legs answer separately. Sigma^-1 mu at the sample moments:")
    net_trend = trend_premium - (RSST_FEE - VTI_FEE)
    pair = growth_optimal_pair(
        base_excess_return=equity_premium,
        base_volatility=equity_volatility,
        diversifier_excess_return=net_trend,
        diversifier_volatility=trend_volatility,
        correlation=correlation,
    )
    print(
        f"   at the SAMPLE premia (an illustration, not a forecast):"
        f" base {pair.base_notional:.2f}, trend {pair.diversifier_notional:.2f},"
        f" gross {pair.gross_notional:.2f}"
    )
    for premium in (0.02, 0.03, 0.04, 0.05):
        for sleeve in (0.005, 0.018, 0.030):
            forward = growth_optimal_pair(
                base_excess_return=premium,
                base_volatility=equity_volatility,
                diversifier_excess_return=sleeve - (RSST_FEE - VTI_FEE),
                diversifier_volatility=trend_volatility,
                correlation=correlation,
            )
            print(
                f"   equity {premium * 100:4.1f}%  trend gross {sleeve * 100:4.1f}%  ->"
                f"  base {forward.base_notional:5.2f}  trend {forward.diversifier_notional:6.2f}"
                f"  gross {forward.gross_notional:5.2f}"
            )

    # ----------------------------------------------------------------------------
    print("\n== 3. what it looks like on the record, measured ==")
    incremental_cost = STACKED_WEIGHT * (RSST_FEE - VTI_FEE)
    print(
        f"  every rung below charges {incremental_cost * 1e4:.1f} bp/yr on the portfolio,\n"
        "  the incremental fee of the stacked wrapper over the core it displaces.\n"
    )
    rungs = gross_notional_ladder(
        equity,
        trend,
        cash,
        rungs=tuple((1.0, w) for w in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0)),
        diversifier_cost=RSST_FEE - VTI_FEE,
    )
    print("  A. base held at 1.00, trend notional varied (the stacked-fund shape)")
    print("    trend  gross    geo%    vol%   Sharpe    MDD%   TUW")
    for rung in rungs:
        print(
            f"    {rung.diversifier_notional:5.2f}  {rung.gross_notional:5.2f}  "
            f"{rung.geometric_return * 100:6.2f}  {rung.volatility * 100:6.2f}  "
            f"{rung.sharpe:6.3f}  {rung.max_drawdown * 100:6.1f}  "
            f"{rung.months_under_water:4d}"
        )

    levered = gross_notional_ladder(
        equity,
        trend,
        cash,
        rungs=tuple((b, 0.0) for b in (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0)),
        borrow_spread=0.0060,
    )
    print("\n  B. the SAME gross notional taken as levered equity, at a 60 bp spread")
    print("    base   gross    geo%    vol%   Sharpe    MDD%   TUW")
    for rung in levered:
        print(
            f"    {rung.base_notional:5.2f}  {rung.gross_notional:5.2f}  "
            f"{rung.geometric_return * 100:6.2f}  {rung.volatility * 100:6.2f}  "
            f"{rung.sharpe:6.3f}  {rung.max_drawdown * 100:6.1f}  "
            f"{rung.months_under_water:4d}"
        )
    print(
        "\n  Compare the two ladders at matched gross. They are not the same portfolio and\n"
        "  a gross-notional figure cannot tell them apart, which is why no wrapper may be\n"
        "  scored from its gross notional."
    )

    print("\n  C. the candidate exactly as filed, against three controls")
    candidate_rung = gross_notional_ladder(
        equity,
        trend,
        cash,
        rungs=((base_notional, sleeve_notional),),
        diversifier_cost=RSST_FEE - VTI_FEE,
    )[0]
    control_rung = gross_notional_ladder(equity, trend, cash, rungs=((1.0, 0.0),))[0]
    matched_rung = gross_notional_ladder(
        equity, trend, cash, rungs=((gross, 0.0),), borrow_spread=0.0060
    )[0]
    for label, rung in (
        ("candidate 1.0216 eq + 0.30 trend", candidate_rung),
        ("control 1.00 equity", control_rung),
        (f"levered equity {gross:.4f}x", matched_rung),
    ):
        print(
            f"    {label:<34} geo {rung.geometric_return * 100:5.2f}%  "
            f"vol {rung.volatility * 100:5.2f}%  Sharpe {rung.sharpe:5.3f}  "
            f"MDD {rung.max_drawdown * 100:6.1f}%  TUW {rung.months_under_water:3d}"
        )

    print("\n  D. sizing by drawdown tolerance, which is the only sizing that needs no forecast")
    print(
        "    The base notional is varied from 0.30 upward, because the tolerances a reader\n"
        "    is likely to state are BELOW the drawdown of an unlevered equity portfolio and\n"
        "    a ladder that starts at 1.0 cannot answer them. Two columns: the base alone at\n"
        "    a 60 bp financing spread, and the base with the candidate's 0.30 of trend\n"
        "    notional beside it. The gap between them is what the overlay buys."
    )
    base_grid = tuple(round(0.30 + 0.02 * step, 2) for step in range(0, 86))
    base_only = list(
        gross_notional_ladder(
            equity, trend, cash, rungs=tuple((b, 0.0) for b in base_grid), borrow_spread=0.0060
        )
    )
    with_overlay = list(
        gross_notional_ladder(
            equity,
            trend,
            cash,
            rungs=tuple((b, sleeve_notional) for b in base_grid),
            diversifier_cost=RSST_FEE - VTI_FEE,
            borrow_spread=0.0060,
        )
    )
    print("\n    tolerance   base alone: max base   with 0.30 trend: max base   extra base bought")
    for tolerance in DRAWDOWN_TOLERANCES:
        alone = notional_for_drawdown(base_only, tolerance=tolerance)
        stacked_gross = notional_for_drawdown(with_overlay, tolerance=tolerance)
        stacked_base = stacked_gross - sleeve_notional
        extra = stacked_base - alone
        print(
            f"    {tolerance * 100:8.0f}%   {alone:20.3f}   {stacked_base:25.3f}   {extra:17.3f}"
        )
    print(
        "    Read the last column. At every tolerance tested the overlay lets the investor\n"
        "    hold MORE equity beta for the same drawdown they would have sat through. That\n"
        "    is what the sleeve is for, and it is a statement about one panel's episodes."
    )

    print("\n    the same rows as a drawdown ladder, for a reader who wants to pick one:")
    print("     base   +0.30 trend gross   MDD alone   MDD with trend   geo alone   geo with")
    for target_base in (0.5, 0.7, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5):
        index = min(
            range(len(base_grid)), key=lambda i: abs(base_grid[i] - target_base)
        )
        print(
            f"     {base_grid[index]:5.2f}  {with_overlay[index].gross_notional:17.3f}   "
            f"{base_only[index].max_drawdown * 100:9.1f}%   "
            f"{with_overlay[index].max_drawdown * 100:14.1f}%   "
            f"{base_only[index].geometric_return * 100:9.2f}%  "
            f"{with_overlay[index].geometric_return * 100:8.2f}%"
        )

    print(
        "\n  E. THE SAME LADDER UNDER THE VALUATION-CONDITIONED DRAWDOWN ASSUMPTION\n"
        f"    Entries above CAPE 30 ran a median {CAPE_CONDITIONED_DRAWDOWN * 100:.1f}%"
        " real drawdown over\n"
        "    the following fifteen years against "
        f"{CAPE_UNCONDITIONED_DRAWDOWN * 100:.1f}% for entries below CAPE 20, and US\n"
        "    CAPE is 41.18 at 2026-08-01 — a level equalled or exceeded in 19 of the 1,748\n"
        "    months since 1881, 18 of them between March 1999 and September 2000.\n"
        "    THOSE TWO FIGURES ARE REAL AND THIS LADDER IS NOMINAL, so only their RATIO is\n"
        "    transferred: "
        f"{CAPE_CONDITIONED_DRAWDOWN / CAPE_UNCONDITIONED_DRAWDOWN:.3f}x."
        " Applying it to the ladder is the same as\n    asking\n"
        "    for a tolerance that much tighter, which is the honest way to read it."
    )
    multiplier = CAPE_CONDITIONED_DRAWDOWN / CAPE_UNCONDITIONED_DRAWDOWN
    print(
        "\n    stated tolerance   max base, panel as measured   max base, CAPE-conditioned"
        "   change"
    )
    for tolerance in DRAWDOWN_TOLERANCES:
        plain = notional_for_drawdown(base_only, tolerance=tolerance)
        conditioned = notional_for_drawdown(base_only, tolerance=tolerance / multiplier)
        change = conditioned - plain
        print(
            f"    {tolerance * 100:14.0f}%   {plain:27.3f}   {conditioned:26.3f}"
            f"   {change:+7.3f}"
        )
    print(
        "    The equity notional is what moves. A tolerance of -50% supports a base of\n"
        "    0.992 on the panel as measured and 0.651 once the ratio is applied: the SAME\n"
        "    investor, the same stated tolerance, a THIRD LESS EQUITY."
    )
    print(
        "\n    and what that does to the trend notional, holding the overlay at a constant\n"
        "    share of the equity exposure (the candidate's own ratio, "
        f"{sleeve_notional / base_notional:.3f}):"
    )
    print(
        "    stated tolerance   base   trend notional   capital in the wrapper   gross"
    )
    for tolerance in DRAWDOWN_TOLERANCES:
        conditioned = notional_for_drawdown(base_only, tolerance=tolerance / multiplier)
        if not math.isfinite(conditioned):
            print(f"    {tolerance * 100:14.0f}%   {'not reachable on this ladder':>60}")
            continue
        implied_trend = conditioned * sleeve_notional / base_notional
        # A dollar of RSST delivers 1.072 of equity and 1.000 of trend, so the capital
        # needed for `implied_trend` of trend notional is `implied_trend / 1.000`.
        capital = implied_trend / RSST_LEGS[1].per_dollar_of_capital
        print(
            f"    {tolerance * 100:14.0f}%   {conditioned:5.3f}   {implied_trend:14.3f}"
            f"   {capital:22.1%}   {conditioned + implied_trend:5.3f}"
        )
    print(
        "    Read the 'capital in the wrapper' column against the 30% proposed. Under the\n"
        "    CAPE-conditioned assumption a -50% tolerance supports about 20% and a -40%\n"
        "    tolerance about 15%, BEFORE any of the tracking-error argument in section 6a."
    )

    # ----------------------------------------------------------------------------
    print("\n== 3a. the drawdown cliff, resampled ==")
    print(
        f"  circular block bootstrap, {BLOCK_MONTHS}-month blocks, {RESAMPLES} paired\n"
        "  resamples, both arms drawn on the same history. P(deeper) is the share of\n"
        "  resamples in which the overlay's max drawdown is WORSE than the unlevered base's.\n"
        f"  Settings are the published ones: a {TREND_FEE * 100:.2f}% fee on trend"
        "  notional and the two\n"
        "  borrow-spread assumptions the owning page reports separately."
    )
    for spread, spread_label in ((0.0060, "60 bp spread"), (0.0, "no spread")):
        print(f"\n   {spread_label}")
        print("   trend w   gross   observed mdd(w)-mdd(0)   95% interval        P(deeper)")
        for weight in CLIFF_GRID:
            paired = paired_drawdown_bootstrap(
                equity,
                trend,
                cash,
                weight=weight,
                resamples=RESAMPLES,
                block_length=BLOCK_MONTHS,
                rng=np.random.default_rng(SEED + 1),
                fee=TREND_FEE,
                borrow_spread=spread,
            )
            print(
                f"   {weight:7.2f}  {1.0 + weight:6.3f}   "
                f"{paired.observed_difference * 100:+20.2f}   "
                f"[{paired.interval[0] * 100:+6.2f}, {paired.interval[1] * 100:+6.2f}]   "
                f"{paired.probability_deeper:8.1%}"
            )
    print(
        "\n   THE CLIFF IS REAL, IT IS SEED-STABLE, AND IT IS NOT A RISK GRADIENT.\n"
        "   Across four independent seeds it sits between w = 0.58 and w = 0.59:"
    )
    for seed in CLIFF_SEEDS:
        seed_cells: list[str] = []
        for weight in (0.56, 0.58, 0.59, 0.60, 0.65):
            seeded = paired_drawdown_bootstrap(
                equity,
                trend,
                cash,
                weight=weight,
                resamples=RESAMPLES,
                block_length=BLOCK_MONTHS,
                rng=np.random.default_rng(seed),
                fee=TREND_FEE,
                borrow_spread=0.0060,
            )
            seed_cells.append(f"{weight:.2f}:{seeded.probability_deeper:6.1%}")
        print(f"     seed {seed:<10} " + "  ".join(seed_cells))
    print(
        "\n   And it VANISHES without the financing spread — the 'no spread' block above\n"
        "   ramps smoothly through the same region. The mechanism is not a smoothly rising\n"
        "   risk: it is that the IDENTITY of the worst drawdown episode switches, and it\n"
        "   switches at nearly the same w in a large block of resampled histories at once."
    )
    print("\n   which episode is the worst drawdown, on the actual path:")
    print("    w      max drawdown   peak      trough")
    for weight in EPISODE_SCAN:
        path = (
            equity
            + weight * trend
            - (TREND_FEE * weight + 0.0060 * weight) / 12.0
            + cash
        )
        summary = drawdown_summary(np.cumprod(1.0 + path))
        print(
            f"    {weight:5.2f}  {summary.max_drawdown * 100:12.2f}%   "
            f"{window[summary.peak_index]}   {window[summary.trough_index]}"
        )
    print(
        "    The overlay's worst episode moves off the GFC — where trend paid — and onto\n"
        "    1937-38, where it did not, as soon as any overlay is held at all. P(deeper)\n"
        "    is then a step function of which of two episodes happens to be deeper in THIS\n"
        "    panel, which is a much weaker basis for a ceiling than a smooth risk curve.\n"
        f"    The candidate sits at w = {sleeve_notional:.2f}, roughly half the step."
    )

    # ----------------------------------------------------------------------------
    print("\n== 4. the financing cost, honestly ==")
    print(
        "  Embedded leverage is not free, and no fund on this shelf discloses what it\n"
        "  pays. RSST files 0.00% of interest expense like every fund in its family:\n"
        "  that is a disclosure ARTEFACT of the instrument, not a measurement of zero.\n"
        "  A futures position borrows nothing, so there is no interest expense line to\n"
        "  report; the financing is embedded in the futures price as a basis over the\n"
        "  rate the collateral earns, and it never appears in an expense ratio.\n"
    )
    print(
        "  as of 2026-08-22, from research/cache: effective fed funds 3.63% (2026-08-20),\n"
        "  3-month constant-maturity Treasury 3.87% (2026-08-20), 3-month bill 3.73%\n"
        "  (2026-07). The LEVEL of the collateral rate nets out of a futures position and\n"
        "  only the basis remains, which is why the stack below is a spread table.\n"
    )
    stacks = (
        financing_stack(
            label="RSST at 30% of capital",
            portfolio_weight=STACKED_WEIGHT,
            fee_on_capital=RSST_FEE,
            legs=(
                FinancingLeg(
                    "E-mini equity futures",
                    0.331,
                    EQUITY_FUTURES_SPREAD,
                    "equity index futures over 3m Term SOFR, +62 bp, ten rolls "
                    "Dec-2022 to Mar-2025",
                ),
                FinancingLeg(
                    "diversified trend book",
                    1.000,
                    TREND_BOOK_SPREAD,
                    "Hazelkorn, Moskowitz and Vasudevan 2023: signed basis -0.83 bp mean "
                    "across 18 index futures 2000-2017; a long/short book takes both sides",
                ),
            ),
            displaced_fee=VTI_FEE,
            diversifier_notional=1.000,
        ),
        financing_stack(
            label="RSST, trend book at +25 bp",
            portfolio_weight=STACKED_WEIGHT,
            fee_on_capital=RSST_FEE,
            legs=(
                FinancingLeg("E-mini equity futures", 0.331, EQUITY_FUTURES_SPREAD, "as above"),
                FinancingLeg(
                    "diversified trend book",
                    1.000,
                    TREND_BOOK_SPREAD_STRESS,
                    "stress: a quarter of the mean ABSOLUTE basis, applied as a drag "
                    "against the authors' own warning",
                ),
            ),
            displaced_fee=VTI_FEE,
            diversifier_notional=1.000,
        ),
        financing_stack(
            label="NTSX at 30% of capital",
            portfolio_weight=STACKED_WEIGHT,
            fee_on_capital=NTSX_FEE,
            legs=(
                FinancingLeg(
                    "Treasury futures",
                    0.635,
                    TREASURY_FUTURES_SPREAD,
                    "maturity-matched OIS, 12-18 bp, Siriwardane Sunderam Wallen",
                ),
            ),
            displaced_fee=VTI_FEE,
            diversifier_notional=0.635,
        ),
        financing_stack(
            label="RSSB at 30% of capital",
            portfolio_weight=STACKED_WEIGHT,
            fee_on_capital=RSSB_FEE,
            legs=(
                FinancingLeg("Treasury futures", 1.0033, TREASURY_FUTURES_SPREAD, "as above"),
            ),
            displaced_fee=VTI_FEE,
            diversifier_notional=1.0033,
        ),
    )
    print(
        "   wrapper                         fee    financing   all-in    portfolio   "
        "incremental   per unit notional"
    )
    for stack in stacks:
        print(
            f"   {stack.label:<28} {stack.fee_on_capital * 1e4:6.1f}"
            f" {stack.financing_cost_in_wrapper * 1e4:11.1f}"
            f" {stack.total_cost_in_wrapper * 1e4:8.1f} {stack.total_cost_in_portfolio * 1e4:11.1f}"
            f" {stack.incremental_cost_in_portfolio * 1e4:13.1f}"
            f" {stack.incremental_cost_per_unit_notional * 1e4:18.1f}"
        )
    print("   (all figures bp/yr; 'portfolio' and 'incremental' are per dollar of PORTFOLIO)")
    print("\n   leg detail for the central RSST row:")
    for leg in stacks[0].legs:
        print(
            f"     {leg.label:<24} financed {leg.financed_notional:5.3f} x "
            f"{leg.spread * 1e4:5.1f} bp = {leg.cost * 1e4:5.1f} bp   [{leg.source}]"
        )
    covariance_hurdle = correlation * equity_volatility * trend_volatility
    hurdle = stacks[0].incremental_cost_per_unit_notional + covariance_hurdle
    print(
        f"\n   the overlay hurdle: rho sigma_p sigma_d + cost per unit notional\n"
        f"   = {covariance_hurdle * 1e4:.1f} + "
        f"{stacks[0].incremental_cost_per_unit_notional * 1e4:.1f} = "
        f"{hurdle * 1e4:.1f} bp/yr of GROSS\n"
        "   trend excess return before the first dollar of overlay adds any growth."
    )
    print(
        "\n   SENSITIVITY, because this estimate is load-bearing. No fund on this shelf\n"
        "   discloses a financing cost and none can: a unitary fee excludes interest\n"
        "   expense, futures financing sits in the basis, and MATE's Other Expenses line is\n"
        "   0.00% and estimated. Every fee table on the shelf therefore compares everything\n"
        "   EXCEPT the cost of the leverage, and the grid below is the whole of what is\n"
        "   left. Rows: the equity-futures basis charged on RSST's 0.331 of E-mini notional.\n"
        "   Columns: a drag charged on the trend book's notional, which the signed evidence\n"
        "   says should be zero and which is varied anyway."
    )
    equity_basis_grid = (0.0, 0.0031, 0.0062, 0.0100)
    trend_basis_grid = (0.0, 0.0025, 0.0050, 0.0100)
    print(
        "\n   incremental portfolio cost, bp/yr        trend-book drag ->\n"
        "   equity basis  " + "".join(f"{v * 1e4:9.0f} bp" for v in trend_basis_grid)
    )
    for equity_basis in equity_basis_grid:
        grid_cells: list[str] = []
        for trend_basis in trend_basis_grid:
            stack = financing_stack(
                label="grid",
                portfolio_weight=STACKED_WEIGHT,
                fee_on_capital=RSST_FEE,
                legs=(
                    FinancingLeg("equity futures", 0.331, equity_basis, "grid"),
                    FinancingLeg("trend book", 1.000, trend_basis, "grid"),
                ),
                displaced_fee=VTI_FEE,
                diversifier_notional=1.000,
            )
            grid_cells.append(f"{stack.incremental_cost_in_portfolio * 1e4:9.1f}   ")
        print(f"   {equity_basis * 1e4:9.0f} bp  " + "".join(grid_cells))
    print(
        "\n   the same grid as the GROSS trend excess return needed to break even,\n"
        "   rho sigma_p sigma_d + cost per unit of trend notional, %/yr\n"
        "   equity basis  " + "".join(f"{v * 1e4:9.0f} bp" for v in trend_basis_grid)
    )
    for equity_basis in equity_basis_grid:
        hurdle_cells: list[str] = []
        for trend_basis in trend_basis_grid:
            stack = financing_stack(
                label="grid",
                portfolio_weight=STACKED_WEIGHT,
                fee_on_capital=RSST_FEE,
                legs=(
                    FinancingLeg("equity futures", 0.331, equity_basis, "grid"),
                    FinancingLeg("trend book", 1.000, trend_basis, "grid"),
                ),
                displaced_fee=VTI_FEE,
                diversifier_notional=1.000,
            )
            hurdle_cells.append(
                f"{(stack.incremental_cost_per_unit_notional + covariance_hurdle) * 100:9.2f}   "
            )
        print(f"   {equity_basis * 1e4:9.0f} bp  " + "".join(hurdle_cells))
    print(
        "   The whole grid spans 0.99% to 2.24%/yr of gross trend excess. The repository's\n"
        "   own post-publication trend estimate is roughly 1.80%/yr, which sits INSIDE that\n"
        "   range. So the sign of the overlay's contribution is decided by a financing\n"
        "   spread that nobody discloses and this repository has not measured — and the fee\n"
        "   is the larger part of it in every cell."
    )

    # ----------------------------------------------------------------------------
    print("\n== 4a. every measured row restated at a forward trend premium ==")
    print(
        f"  The panel's realised gross trend excess is {trend_premium * 100:.2f}%/yr."
        " Nothing in this\n"
        "  repository signs a forward number anywhere near it: decision 0004 records a\n"
        "  post-publication trend excess of roughly 1.8 pp/yr and Experiment 010b's\n"
        "  marginal figure sits inside its own detection floor. Every row below shifts the\n"
        "  trend leg's MEAN to a stated forward premium and leaves its volatility and its\n"
        "  correlation with equity exactly unchanged."
    )
    print(
        "\n   gross trend   net of 96 bp   candidate geo%   control geo%   edge pp/yr"
        "   candidate MDD%   Sharpe"
    )
    restated: dict[float, FloatArray] = {}
    for forward_premium in (*FORWARD_TREND_PREMIA, trend_premium):
        shifted = _restate_mean(trend, annual_mean=forward_premium)
        restated[forward_premium] = shifted
        forward_rung = gross_notional_ladder(
            equity,
            shifted,
            cash,
            rungs=((base_notional, sleeve_notional),),
            diversifier_cost=RSST_FEE - VTI_FEE,
        )[0]
        print(
            f"   {forward_premium * 100:10.2f}%   "
            f"{(forward_premium - (RSST_FEE - VTI_FEE)) * 100:11.2f}%   "
            f"{forward_rung.geometric_return * 100:13.2f}   "
            f"{control_rung.geometric_return * 100:12.2f}   "
            f"{(forward_rung.geometric_return - control_rung.geometric_return) * 100:+10.2f}"
            f"   {forward_rung.max_drawdown * 100:14.1f}   {forward_rung.sharpe:6.3f}"
        )
    print(
        "\n   the growth-optimal trend notional at each forward premium, Sigma^-1 mu:"
    )
    for forward_premium in (*FORWARD_TREND_PREMIA, trend_premium):
        forward_pair = growth_optimal_pair(
            base_excess_return=equity_premium,
            base_volatility=equity_volatility,
            diversifier_excess_return=forward_premium - (RSST_FEE - VTI_FEE),
            diversifier_volatility=trend_volatility,
            correlation=correlation,
        )
        print(
            f"     gross trend {forward_premium * 100:5.2f}%  ->  trend notional "
            f"{forward_pair.diversifier_notional:+6.2f}"
            f"  (base {forward_pair.base_notional:.2f})"
        )
    # Solve Sigma^-1 mu = (base, 0.30) for the diversifier premium directly rather than by
    # search: with the base leg free, the second row of Sigma w = mu gives
    # mu_d = rho sigma_p sigma_d L_base + sigma_d**2 * 0.30, and L_base is itself the
    # solution at that mu_d. The correlation here is +0.011, so the coupling is negligible
    # and the one-step value below is reported with the coupling included.
    coupled_base = (equity_premium - covariance_hurdle * sleeve_notional) / (
        equity_volatility**2 * (1.0 - correlation**2)
    )
    net_at_030 = (
        covariance_hurdle * coupled_base + trend_volatility**2 * sleeve_notional
    )
    gross_at_030 = net_at_030 + (RSST_FEE - VTI_FEE)
    print(
        f"\n   INVERTED: 0.30 of trend notional is exactly growth-optimal at a GROSS forward\n"
        f"   trend excess of {gross_at_030 * 100:.2f}%/yr ({net_at_030 * 100:.2f}%"
        " net of the 96 bp incremental fee).\n"
        f"   The repository's own post-publication figure is roughly 1.80%/yr, at which the\n"
        f"   growth-optimal notional is 0.49 — so 30% is about "
        f"{sleeve_notional / 0.49:.0%} of the growth optimum at\n"
        "   the best forward number this repository has, which is a fractional-Kelly\n"
        "   position arrived at by accident rather than by design."
    )
    print(
        f"   The break-even hurdle from section 4 is {hurdle * 1e4:.0f} bp of GROSS"
        " trend excess. Below\n"
        "   it the growth-optimal trend notional is NEGATIVE and any overlay at all is\n"
        "   overbetting a sleeve with no expected return. The window in which 0.30 is a\n"
        f"   sensible size is therefore narrow — {hurdle * 100:.2f}% to about 3%/yr"
        " of gross trend excess —\n"
        "   and the growth optimum leaves that window in both directions faster than any\n"
        "   forecast this repository can make distinguishes its endpoints."
    )

    print(
        "\n   THE SIZE OF THE PRIZE, which is the number the whole decision turns on.\n"
        "   Peak excess growth from the trend leg alone is a_net**2 / (2 sigma_d**2) at\n"
        "   notional a_net / sigma_d**2, and growth at any other notional is that peak\n"
        "   times 1 - (1 - f)**2 with f the fraction of the optimum held. Tracking error\n"
        "   against 100% equity is w sigma_d. Years to 90% confidence is (z s / e)**2."
    )
    print(
        "\n    gross   optimal w   peak growth   |   w=0.15    w=0.20    w=0.25    w=0.30"
        "   |  TE at 0.30   90% conf"
    )
    for forward_premium in (*FORWARD_TREND_PREMIA, trend_premium):
        net = forward_premium - (RSST_FEE - VTI_FEE)
        optimal_w = net / trend_volatility**2
        peak = net**2 / (2.0 * trend_volatility**2)
        prize_cells: list[str] = []
        for weight in (0.15, 0.20, 0.25, 0.30):
            fraction = weight / optimal_w if optimal_w != 0.0 else math.nan
            prize_cells.append(f"{peak * growth_retained_fraction(fraction) * 1e4:8.1f}")
        te_at_030 = 0.30 * trend_volatility
        edge_at_030 = peak * growth_retained_fraction(0.30 / optimal_w)
        confidence_years = (
            horizon_for_confidence(
                edge_bp=edge_at_030 * 1e4, tracking_error_bp=te_at_030 * 1e4, confidence=0.90
            )
            if edge_at_030 > 0.0
            else math.inf
        )
        print(
            f"    {forward_premium * 100:5.2f}%   {optimal_w:9.2f}   {peak * 1e4:8.1f} bp   |"
            + "  ".join(prize_cells)
            + f"   |  {te_at_030 * 100:8.2f}%   "
            + ("   never" if not math.isfinite(confidence_years) else f"{confidence_years:7.0f}y")
        )
    print(
        "    (growth figures are bp/yr of the PORTFOLIO's growth rate, from the trend leg\n"
        "     alone, on the lognormal model rather than on the realised path)\n"
        "    At the repository's own 1.80% forward premium the ENTIRE trend overlay is\n"
        "    worth at most ~23 bp/yr of growth and carries 3.7 pp/yr of tracking error.\n"
        "    Moving from 0.30 to 0.20 of notional gives up a handful of basis points and\n"
        "    removes a third of the benchmark-relative risk. That trade is the\n"
        "    recommendation, and it does not depend on which side of the break-even the\n"
        "    forward premium turns out to be."
    )

    # ----------------------------------------------------------------------------
    print("\n== 5. the outcome distribution, which is what the charter asks for ==")
    print(
        "  P5 and P1 of the resampled maximum-drawdown distribution are reported rather\n"
        "  than the worst resample: a minimum over resamples is an extreme order statistic\n"
        "  and it moves by several points with the seed."
    )
    control_total = _two_leg_total(
        equity, trend, cash, base_notional=1.0, sleeve_notional=0.0, cost=0.0
    )
    matched_total = _two_leg_total(
        equity, trend, cash, base_notional=gross, sleeve_notional=0.0, cost=0.0060 * (gross - 1.0)
    )
    for forward_label, sleeve_series in (
        (f"realised {trend_premium * 100:.2f}%", trend),
        ("forward 1.80%", restated[0.018]),
        ("forward 0.00%", restated[0.000]),
    ):
        arm = _two_leg_total(
            equity,
            sleeve_series,
            cash,
            base_notional=base_notional,
            sleeve_notional=sleeve_notional,
            cost=(RSST_FEE - VTI_FEE) * sleeve_notional,
        )
        for control_label, control in (
            ("100% equity", control_total),
            (f"levered equity {gross:.4f}x", matched_total),
        ):
            print(
                f"\n  trend at {forward_label}, against {control_label}"
                f" ({RESAMPLES} joint {BLOCK_MONTHS}-month block resamples)"
            )
            print(
                "   horizon  P(underperform)   relative wealth p5 / median / p95"
                "   median MDD   p5 MDD   p1 MDD"
            )
            for horizon in HORIZONS:
                outcome = horizon_outcomes(
                    arm,
                    control,
                    horizon_years=horizon,
                    resamples=RESAMPLES,
                    block_length=BLOCK_MONTHS,
                    rng=np.random.default_rng(SEED + 3),
                )
                print(
                    f"   {horizon:5.0f}y  {outcome.probability_underperform:15.1%}   "
                    f"{outcome.relative_wealth_quantiles['p5']:6.3f} / "
                    f"{outcome.median_relative_wealth:6.3f} / "
                    f"{outcome.relative_wealth_quantiles['p95']:6.3f}   "
                    f"{outcome.median_max_drawdown * 100:9.1f}%   "
                    f"{outcome.drawdown_quantiles['p5'] * 100:6.1f}%  "
                    f"{outcome.drawdown_quantiles['p1'] * 100:6.1f}%"
                )
    print(
        "\n   The resampling imposes a block-stationary null: dependence survives to 24\n"
        "   months and is destroyed beyond, so a 30-year row is an extrapolation of that\n"
        "   null rather than a measurement of a 30-year holding period."
    )

    # ----------------------------------------------------------------------------
    candidate_total = _two_leg_total(
        equity,
        trend,
        cash,
        base_notional=base_notional,
        sleeve_notional=sleeve_notional,
        cost=(RSST_FEE - VTI_FEE) * sleeve_notional,
    )
    print("\n== 6. 'understand market conditions': does vol-targeting survive? ==")
    print(
        f"  rule: leverage_t = clip({VOL_TARGET:.0%} / trailing vol(t-w..t-1), "
        f"{VOL_FLOOR:.1f}, {VOL_CAP:.1f}), applied to the CANDIDATE's excess return.\n"
        f"  {len(VOL_WINDOWS)} arms, one declared target, windows {VOL_WINDOWS}.\n"
        f"  every arm charges {CENTRAL_ROUND_TRIP * 1e4:.0f} bp round trip per unit of "
        "notional traded and a 60 bp spread above 1.0x, inside the path.\n"
    )
    candidate_excess = candidate_total - cash
    arms: list[tuple[int, LeveragePathResult]] = []
    active_series: list[FloatArray] = []
    active_sharpes: list[float] = []
    p_values: list[float] = []
    print(
        "   window   months   mean L   max L   turnover/yr   geo%    vol%   Sharpe    MDD%"
        "   cost bp   active pp/yr   MDE80   HAC t   p"
    )
    for vol_window in VOL_WINDOWS:
        path = volatility_targeted_leverage(
            candidate_excess,
            window=vol_window,
            target=VOL_TARGET,
            cap=VOL_CAP,
            floor=VOL_FLOOR,
        )
        result = apply_leverage(
            candidate_excess,
            cash,
            path,
            borrow_spread=0.0060,
            round_trip_cost=CENTRAL_ROUND_TRIP,
        )
        # The comparator is the same portfolio at CONSTANT leverage equal to the rule's own
        # mean, over the same months, so the comparison is a timing comparison and not a
        # leverage comparison wearing a timing comparison's clothes.
        constant = np.full(candidate_excess.size, np.nan, dtype=np.float64)
        constant[vol_window:] = result.mean_leverage
        control_arm = apply_leverage(
            candidate_excess, cash, constant, borrow_spread=0.0060, round_trip_cost=0.0
        )
        # THE ACTIVE SERIES. Scale the timed arm to the control's realised volatility
        # before differencing, so what is tested is the timing and not the risk level.
        # Everything downstream — the Sharpe deflated, the correlations that set the
        # effective trial count, the p-values corrected — uses THIS series and never the
        # arm's own Sharpe. Deflating a raw levered-portfolio Sharpe would be deflating the
        # equity premium, which passes by construction and measures nothing.
        scale = control_arm.volatility / result.volatility
        active = np.asarray(
            scale * result.excess_returns - control_arm.excess_returns, dtype=np.float64
        )
        hac = hac_mean(active)
        floor_effect = minimum_detectable_effect(active)
        arms.append((vol_window, result))
        active_series.append(active)
        active_sharpes.append(
            float(np.mean(active)) / float(np.std(active, ddof=1))
        )
        p_values.append(hac.p_value)
        print(
            f"   {vol_window:6d}   {result.months:6d}   {result.mean_leverage:6.3f}  "
            f"{result.max_leverage:6.3f}   {result.turnover_per_year:11.3f}   "
            f"{result.geometric_return * 100:5.2f}  {result.volatility * 100:6.2f}  "
            f"{result.sharpe:6.3f}  {result.max_drawdown * 100:6.1f}   "
            f"{result.trading_cost_charged * 1e4:7.1f}   "
            f"{float(np.mean(active)) * 1200:+12.2f}   {floor_effect * 100:6.2f}   "
            f"{hac.t_statistic:+5.2f}  {hac.p_value:.3f}"
        )

    shortest = min(series.size for series in active_series)
    trial_matrix = np.column_stack([series[-shortest:] for series in active_series])
    mean_correlation = mean_off_diagonal_correlation(trial_matrix)
    effective_trials = effective_number_of_trials(len(VOL_WINDOWS), mean_correlation)
    dispersion = trial_dispersion_from_sharpes(np.asarray(active_sharpes, dtype=np.float64))
    best_index = int(np.argmax(active_sharpes))
    best_window, best_result = arms[best_index]
    best_active = active_series[best_index]
    standardised = (best_active - best_active.mean()) / best_active.std(ddof=0)
    skew = float(np.mean(standardised**3))
    kurt = float(np.mean(standardised**4))
    deflated = deflated_sharpe_ratio(
        active_sharpes[best_index],
        trial_dispersion=dispersion,
        n_trials=effective_trials,
        n_observations=best_active.size,
        skewness=skew,
        kurtosis=kurt,
    )
    print(
        "\n   DEFLATION IS RUN ON THE ACTIVE SERIES, NEVER ON THE ARM'S OWN SHARPE.\n"
        "   Every arm here is long the candidate portfolio all of the time, so its raw\n"
        "   Sharpe contains the equity premium and deflating it would return a pass by\n"
        "   construction. What is deflated below is the volatility-matched difference\n"
        "   between the timed arm and a constant-leverage arm at the same mean exposure."
    )
    print(
        f"\n   best arm by ACTIVE Sharpe: {best_window}-month window, monthly active SR "
        f"{active_sharpes[best_index]:+.4f}"
    )
    print(
        f"   (its raw levered Sharpe is {best_result.sharpe:.3f}, which is NOT the number"
        " deflated)"
    )
    print(
        f"   mean off-diagonal correlation across the {len(VOL_WINDOWS)} active series"
        f"  {mean_correlation:.4f}"
    )
    print(f"   effective independent trials               {effective_trials:.2f}")
    print(f"   trial dispersion sqrt(V[SR])               {dispersion:.4f}")
    print(f"   deflated null threshold SR*                {deflated.sharpe_threshold:.4f}")
    print(
        "   DEFLATED SIGNIFICANCE P[SR_true > SR*]     "
        f"{deflated.deflated_significance:.4f}"
    )
    for assumed in (14.8, 100.0, 10_000.0):
        harsher = deflated_sharpe_ratio(
            active_sharpes[best_index],
            trial_dispersion=dispersion,
            n_trials=assumed,
            n_observations=best_active.size,
            skewness=skew,
            kurtosis=kurt,
        )
        print(
            f"     at {assumed:>8.1f} assumed independent trials  DSR "
            f"{harsher.deflated_significance:.4f}"
        )
    print(
        "   The deflation family is these five arms ONLY. It does not correct for the\n"
        "   choice of target, cap, floor, cost assumption, base panel or the decision to\n"
        "   test vol-targeting at all, so the true trial count is larger and the deflated\n"
        "   significance above is an upper bound on the evidence."
    )
    bh = benjamini_hochberg(np.asarray(p_values, dtype=np.float64))
    holm = holm_bonferroni(np.asarray(p_values, dtype=np.float64))
    print(
        "\n   paired HAC test of the volatility-matched timing difference, corrected:\n"
        "   window   raw p    BH adj    BH rejects   Holm adj   Holm rejects"
    )
    for index, vol_window in enumerate(VOL_WINDOWS):
        print(
            f"   {vol_window:6d}   {p_values[index]:.3f}   {bh.adjusted_p_values[index]:.3f}"
            f"   {'yes' if bh.rejected[index] else 'no':>10}   "
            f"{holm.adjusted_p_values[index]:.3f}   {'yes' if holm.rejected[index] else 'no':>12}"
        )

    print("\n   sensitivity to the trading-cost assumption, at the best arm's window:")
    print("    round trip   geo%    Sharpe   cost charged bp/yr")
    for cost in ROUND_TRIP_COSTS:
        path = volatility_targeted_leverage(
            candidate_excess, window=best_window, target=VOL_TARGET, cap=VOL_CAP, floor=VOL_FLOOR
        )
        priced = apply_leverage(
            candidate_excess, cash, path, borrow_spread=0.0060, round_trip_cost=cost
        )
        print(
            f"    {cost * 1e4:8.0f} bp   {priced.geometric_return * 100:5.2f}   "
            f"{priced.sharpe:6.3f}   {priced.trading_cost_charged * 1e4:17.1f}"
        )
    print(
        "   And the tax the panel cannot price: every leverage change in a taxable\n"
        "   account is a realisation. Turnover above is in units of NOTIONAL a year, and\n"
        "   at the investor's marginal rate a short-term realisation of that size is the\n"
        "   largest single term in the rule and it is NOT charged in any row above."
    )

    # ----------------------------------------------------------------------------
    print("\n== 6a. the tracking error, and what it means for the stretch to sit through ==")
    relative = (1.0 + candidate_total) / (1.0 + control_total) - 1.0
    tracking_error = float(np.std(relative, ddof=1)) * math.sqrt(12.0)
    trend_only = sleeve_notional * trend_volatility
    beta_only = (base_notional - 1.0) * equity_volatility
    print(
        "   tracking error of the candidate against 100% equity  "
        f" {tracking_error * 100:6.2f}%/yr\n"
        f"     of which the trend overlay alone (w x sigma_d)      {trend_only * 100:6.2f}%/yr\n"
        f"     of which the extra equity beta alone                {beta_only * 100:6.2f}%/yr\n"
        "   The overlay is essentially the whole benchmark-relative risk budget. The extra\n"
        "   equity beta contributes about a tenth as much, which is why the 1.0216 is a\n"
        "   rounding detail and the 0.30 is the decision."
    )
    relative_curve = np.cumprod(1.0 + relative)
    relative_drawdown = drawdown_summary(relative_curve)
    print(
        f"\n   worst run of RELATIVE underperformance on the actual path"
        f"   {relative_drawdown.max_drawdown * 100:6.1f}%\n"
        f"   longest run below the previous relative high water mark   "
        f"{relative_drawdown.max_time_under_water:4d} months\n"
        f"   peak {window[relative_drawdown.peak_index]}  trough "
        f"{window[relative_drawdown.trough_index]}\n"
        "   THIS is the number a tracking-error figure is a proxy for: the investor does\n"
        "   not experience an annualised standard deviation, they experience this stretch."
    )
    print("\n   the same statistic at each forward trend premium, and resampled:")
    print(
        "    gross trend   worst relative run   months under   p5 of resampled worst run"
    )
    for forward_premium in (*FORWARD_TREND_PREMIA, trend_premium):
        arm = _two_leg_total(
            equity,
            restated[forward_premium],
            cash,
            base_notional=base_notional,
            sleeve_notional=sleeve_notional,
            cost=(RSST_FEE - VTI_FEE) * sleeve_notional,
        )
        arm_relative = (1.0 + arm) / (1.0 + control_total) - 1.0
        summary = drawdown_summary(np.cumprod(1.0 + arm_relative))
        rng = np.random.default_rng(SEED + 5)
        blocks = math.ceil(arm_relative.size / BLOCK_MONTHS)
        starts = rng.integers(0, arm_relative.size, size=(RESAMPLES, blocks))
        offsets = np.arange(BLOCK_MONTHS, dtype=np.intp)
        drawn = (starts[:, :, None] + offsets[None, None, :]) % arm_relative.size
        indices = drawn.reshape(RESAMPLES, -1)[:, : arm_relative.size]
        wealth = np.cumprod(1.0 + arm_relative[indices], axis=1)
        peaks = np.maximum.accumulate(wealth, axis=1)
        worst = np.min(wealth / peaks - 1.0, axis=1)
        print(
            f"    {forward_premium * 100:10.2f}%   {summary.max_drawdown * 100:17.1f}%   "
            f"{summary.max_time_under_water:12d}   {float(np.quantile(worst, 0.05)) * 100:24.1f}%"
        )
    print(
        "   1.80% is the RETRACTED convention, kept for comparison only: the review restated\n"
        "   it to 4.07% gross on this axis, and the trend-weight page's prior median is 3.90%\n"
        "   gross (2.73% net of the wrapper's 1.165%). The central case is the 4.07% row."
    )

    print(
        "\n   the same, across the capital weight the investor is choosing between, with the\n"
        f"   probability that relative wealth sits {RELATIVE_RUN_TRIGGER:.0%} below its running"
        " peak within\n"
        f"   10, 20 and 30 years ({RESAMPLES} joint {BLOCK_MONTHS}-month block resamples,"
        " nested):"
    )
    print(
        "    gross trend   w      base    worst run   months   p5 resampled"
        "   P(-20% run) 10y   20y   30y"
    )
    for forward_premium in HOLDABILITY_PREMIA:
        for weight in HOLDABILITY_WEIGHTS:
            exposure = portfolio_exposure(
                [
                    Holding("core US equity", 1.0 - weight, (NotionalLeg("us-equity", 1.0),)),
                    Holding("RSST", weight, RSST_LEGS),
                ]
            )
            arm = _two_leg_total(
                equity,
                restated[forward_premium],
                cash,
                base_notional=exposure.equity_notional,
                sleeve_notional=exposure.non_equity_notional,
                cost=(RSST_FEE - VTI_FEE) * exposure.non_equity_notional,
            )
            arm_relative = (1.0 + arm) / (1.0 + control_total) - 1.0
            summary = drawdown_summary(np.cumprod(1.0 + arm_relative))
            rng = np.random.default_rng(SEED + 5)
            blocks = math.ceil(arm_relative.size / BLOCK_MONTHS)
            starts = rng.integers(0, arm_relative.size, size=(RESAMPLES, blocks))
            offsets = np.arange(BLOCK_MONTHS, dtype=np.intp)
            drawn = (starts[:, :, None] + offsets[None, None, :]) % arm_relative.size
            indices = drawn.reshape(RESAMPLES, -1)[:, : arm_relative.size]
            wealth = np.cumprod(1.0 + arm_relative[indices], axis=1)
            peaks = np.maximum.accumulate(wealth, axis=1)
            worst = np.min(wealth / peaks - 1.0, axis=1)
            runs = relative_run_outcomes(
                arm,
                control_total,
                trigger=RELATIVE_RUN_TRIGGER,
                horizons_years=HORIZONS,
                resamples=RESAMPLES,
                block_length=BLOCK_MONTHS,
                rng=np.random.default_rng(SEED + 7),
            )
            breach = runs.breach_probability_by_horizon
            p5 = float(np.quantile(worst, 0.05))
            print(
                f"    {forward_premium * 100:10.2f}%   {weight:4.2f}  "
                f"{exposure.equity_notional:6.4f}   {summary.max_drawdown * 100:8.1f}%   "
                f"{summary.max_time_under_water:6d}   {p5 * 100:11.1f}%"
                f"   {breach[10.0]:15.1%} {breach[20.0]:5.1%} {breach[30.0]:5.1%}"
            )
    print(
        "   The worst run and months under water are the ACTUAL path, restated to the row's\n"
        "   premium; the resampled columns impose the block-stationary null. The 30-year\n"
        "   probability is the trend-weight page's abandonment probability measured on this\n"
        "   panel: same trigger, same rule, different trend leg and window."
    )

    # ----------------------------------------------------------------------------
    print("\n== 7. the specific danger: leverage, a volatility spike, forced deleveraging ==")
    print("  the named episodes (docs/research/evidence-base.md), peak-to-trough inside each")
    print("   episode                        months   control   candidate   levered eq")
    for name, (start, end) in CRISIS_WINDOWS.items():
        inside = _window_mask(window.tolist(), start, end)
        if not inside.any():
            print(f"   {name:<30}   {'absent from the panel':>38}")
            continue
        print(
            f"   {name:<30} {int(inside.sum()):6d}   "
            f"{_peak_to_trough(control_total[inside]) * 100:6.1f}%   "
            f"{_peak_to_trough(candidate_total[inside]) * 100:8.1f}%   "
            f"{_peak_to_trough(matched_total[inside]) * 100:9.1f}%"
        )
    print(
        "   1929-32 is ABSENT: the trend leg's 36-month signal plus 60-month volatility\n"
        "   window consume the first 96 months of the panel, so the deepest US equity\n"
        "   drawdown on record is removed by construction and every drawdown above is\n"
        "   measured on a sample that excludes it."
    )

    print(
        "\n  forced deleveraging: the wrapper's own risk control cuts the overlay after a\n"
        "  loss and restores it only at a new high-water mark, so the sleeve is absent for\n"
        "  exactly the part of the path where it would have paid."
    )
    print("   trigger   months cut   geo%    MDD%    cost vs unconstrained   MDD change")
    for trigger in (0.10, 0.15, 0.20, 0.30):
        cut = forced_deleveraging(
            equity,
            trend,
            cash,
            weight=sleeve_notional,
            trigger=trigger,
            reduced_weight=0.0,
            restore_fraction=1.0,
            fee=RSST_FEE - VTI_FEE,
        )
        print(
            f"   {trigger:7.0%}   {cut.months_deleveraged:10d}   "
            f"{cut.geometric_return * 100:5.2f}  {cut.max_drawdown * 100:6.1f}   "
            f"{cut.geometric_cost_versus_unconstrained * 100:+21.2f}   "
            f"{cut.drawdown_change_versus_unconstrained * 100:+9.2f}"
        )
    print(
        "   The mechanism that turns a drawdown into a permanent loss is not a margin call\n"
        "   — a return-stacked ETF cannot margin-call its holders — it is the same\n"
        "   arithmetic seen from inside the fund, or from the investor selling at the\n"
        "   bottom. The rows above price the fund's version. The investor's version is\n"
        "   larger and is not estimable from any series held here."
    )

    # ----------------------------------------------------------------------------
    print("\n== 8. three answers to 'how much trend', each optimising something else ==")
    print(
        "  These are not competing estimates of one quantity. They are the optima of three\n"
        "  different objectives, and an investor should pick the objective first."
    )
    variance_minimising = -base_notional * correlation * equity_volatility / trend_volatility
    print(
        "\n   objective                         optimal trend notional   what it ignores"
    )
    print(
        f"   minimum portfolio variance        {variance_minimising:21.3f}   expected return"
    )
    print(
        f"   maximum growth at 1.80% gross     {0.49:21.3f}   drawdown and holdability"
    )
    print(
        f"   maximum growth at 0.00% gross     {-0.67:21.3f}   drawdown and holdability"
    )
    print(
        f"   drawdown tolerance (any tested)   {'not binding':>21}   return entirely"
    )
    print(f"   the investor proposes             {sleeve_notional:21.3f}")
    print(
        "\n   THE VARIANCE-MINIMISING POINT IS ENTIRELY A CORRELATION ESTIMATE.\n"
        "   With the base held at b, portfolio variance is minimised at\n"
        "     w* = -b rho sigma_e / sigma_d,\n"
        f"   which on THIS panel is {variance_minimising:+.3f}, because the measured equity/trend\n"
        f"   correlation over {months} months is {correlation:+.4f} — statistically\n"
        "   indistinguishable from zero.\n"
        "   An independent measurement in this session puts the\n"
        "   variance-minimising notional at 0.216. Inverting the same identity, 0.216\n"
        "   requires rho = "
        f"{-0.216 * trend_volatility / (base_notional * equity_volatility):+.3f}.\n"
        "   THE TWO RESULTS DO NOT DISAGREE ABOUT METHOD. They disagree about one\n"
        "   correlation, measured on different instruments and different windows, and the\n"
        "   difference between +0.011 and about -0.17 is the whole gap. Neither is\n"
        "   resolvable against the other from anything held here, and\n"
        "   docs/charter.md's rule applies: a low average correlation is incomplete\n"
        "   evidence about crisis dependence, and this identity uses the average one."
    )
    print(
        "\n   sensitivity of the variance-minimising notional to the correlation:"
    )
    for assumed_correlation in (-0.30, -0.20, -0.17, -0.10, 0.0, correlation, 0.10):
        print(
            f"     rho {assumed_correlation:+6.3f}  ->  w* "
            f"{-base_notional * assumed_correlation * equity_volatility / trend_volatility:+6.3f}"
        )

    print(
        "\n  and if the objective is drawdown control, four ways to buy it, ranked by what\n"
        "  they cost. Every row is measured on this panel, matched to the candidate's own\n"
        f"  {candidate_rung.max_drawdown * 100:.1f}% maximum drawdown where it can be:"
    )
    print("    route                              MDD%    geo%    turnover/yr   cost bp/yr")
    print(
        f"    hold less equity (base 0.90)      "
        f"{base_only[30].max_drawdown * 100:6.1f}  {base_only[30].geometric_return * 100:6.2f}"
        f"   {0.0:11.3f}   {0.0:10.1f}"
    )
    print(
        f"    the 0.30 trend overlay            "
        f"{candidate_rung.max_drawdown * 100:6.1f}  "
        f"{candidate_rung.geometric_return * 100:6.2f}   {0.0:11.3f}   "
        f"{STACKED_WEIGHT * (RSST_FEE - VTI_FEE) * 1e4:10.1f}"
    )
    print(
        f"    vol-target the whole portfolio    "
        f"{best_result.max_drawdown * 100:6.1f}  {best_result.geometric_return * 100:6.2f}"
        f"   {best_result.turnover_per_year:11.3f}   "
        f"{best_result.trading_cost_charged * 1e4:10.1f}"
    )
    print(
        "    a return-timing rule              see docs/research/ for the timing verdict:"
        " unresolved,\n"
        "                                      +0.74 pp/yr against an MDE80 of 3.03 pp/yr"
    )
    print(
        "\n   Read the first row against the second. Holding 0.90 of equity and nothing\n"
        "   else buys a drawdown 3.9 points shallower than 1.00 of equity, for nothing, in\n"
        "   one trade, with no wrapper, no financing, no Cayman subsidiary and no forecast.\n"
        "   That is the honest control the overlay has to beat, and on this panel the\n"
        "   overlay's drawdown reduction at 0.30 is under one percentage point. THE\n"
        "   OVERLAY IS NOT A DRAWDOWN INSTRUMENT AT THIS SIZE. It is a return bet, and it\n"
        "   must be argued as one."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
