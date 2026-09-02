"""Regenerates every table behind ``docs/research/trend-weight-under-uncertainty.md``.

Kept separate from :mod:`portfolio_edge.studies.trend_weight_regret` so the study itself
stays pure and testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.trend_weight_regret

**The panel is the construction tournament's own window**, 1990-11..2026-05, on the same
two series — Ken French ``Mkt-RF`` for equity and AQR's ``TSMOM`` for trend — so that this
page's disagreement with
``docs/research/construction-tournament.md`` is a disagreement about a prior and never
about a sample. The first thing printed is that window's moments, which reproduce the
tournament's 10.98 pp/yr and the three-era decay quoted in
``docs/research/live-managed-futures.md`` exactly.

**Nothing here downloads.** A missing cache entry raises, so a table can never be the thing
that silently pulls a new vintage of a vendor series that is rebuilt on every update.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import aqr, french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_011_overlay_stack import minimum_detectable_effect
from portfolio_edge.studies.notional_budget import horizon_outcomes
from portfolio_edge.studies.trend_weight_regret import (
    Benchmark,
    OverlayGrowthModel,
    PremiumPrior,
    PremiumScenario,
    abandonment_adjusted_gap,
    conditional_decade_gaps,
    minimax_regret_weight,
    regret_from_gaps,
    regret_surface,
    restate_annual_mean,
    robust_range,
    years_to_resolve,
)

FloatArray = NDArray[np.float64]

SEED: Final = 20260822
RESAMPLES: Final = 4_000
BLOCK_MONTHS: Final = 24

#: The tournament's window, chosen by the data rather than by anyone: AQR's TSMOM ends
#: 2026-05 and Ken French's developed ex-US momentum factor starts 1990-11.
WINDOW: Final = ("1990-11", "2026-05")

#: The action space the investor is actually choosing from. 40% is a ceiling, not a
#: measurement, and section 3 of the page reports how much of the answer it decides.
WEIGHT_GRID: Final = tuple(round(0.02 * i, 2) for i in range(21))
HEADLINE_WEIGHTS: Final = (0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40)
#: The margin inside which two weights are not distinguishable as decisions. Ten basis
#: points a year is most of the prize at every premium below the prior's mean, which is
#: what makes it a decision tolerance rather than an arbitrary rounding.
TOLERANCE: Final = 0.0010
#: The prior with the full-window realisation removed and the rest renormalised: the view
#: that a 1990-2026 backtest mean is not a forward estimate for a strategy published in 2012.
DECAY_WEIGHTS: Final = (0.17, 0.11, 0.17, 0.16, 0.11, 0.11, 0.17, 0.0)
#: A coarser grid for the simulated arm, which costs a bootstrap per cell.
HOLDABILITY_WEIGHTS: Final = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)
#: The contribution stream the recommendation cites as the reason a position survives a
#: drought: 5-15% of starting capital a year, paid monthly to BOTH arms. Zero is the row
#: every other table on the page is built on. Two bases bracket the effect: a fixed
#: nominal instalment, and one that keeps pace with the benchmark portfolio's wealth.
CONTRIBUTION_RATES: Final = (0.0, 0.05, 0.10, 0.15)
CONTRIBUTION_WEIGHTS: Final = (0.25, 0.30)

#: All-in retail cost per unit of trend notional obtained through the candidate's wrapper:
#: 99 bp of RSST fee plus 20.5 bp of equity-index-futures basis on the 0.331 of financed
#: notional it carries, less VTI's 3 bp, measured in
#: docs/research/leverage-and-the-notional-budget.md section 4.
WRAPPER_COST: Final = 0.01165
#: The same figure in a taxable account: plus RSST's 32 bp/yr of distribution drag per
#: dollar of trend notional, the only measured after-tax figure on the trend shelf
#: (docs/research/trend-marginal-value.md, consequence list).
WRAPPER_COST_TAXABLE: Final = 0.01485
#: The sibling page's own lower cost convention, 96 bp charged on trend notional, kept as a
#: sensitivity so the two pages' difference is visible rather than silent.
WRAPPER_COST_LOW: Final = 0.0096

#: Equity-index-futures basis over 3-month Term SOFR, ten rolls Dec-2022..Mar-2025
#: (docs/research/structural-and-tax-edges.md). Charged to the leverage-matched control on
#: exactly the same terms as to the overlay.
EQUITY_FINANCING_SPREAD: Final = 0.0062

#: Three forward equity premia, every one sourced rather than invented. The leverage-matched
#: control's break-even is dominated by this input, so it is swept and never defaulted.
EQUITY_PREMIA: Final[tuple[tuple[str, float], ...]] = (
    ("realised on this panel", math.nan),  # filled in from the data
    ("decision 0004's working figure", 0.0500),
    ("valuation-proxy mapping, notional budget section 2", 0.0150),
)

#: Sharpe ratios of the live managed-futures evidence, from Experiment 012's own table
#: (docs/research/live-managed-futures.md section 2). Net of every fund's fee, trading cost
#: and slippage; flattered by two survivorship holes that both remove funds that failed.
LIVE_SHARPE_HEADLINE: Final = 0.329
LIVE_SHARPE_EX_VENDOR: Final = 0.230
#: DBMF's fee, the median of Experiment 008's five-fund shelf, added back so that a fund's
#: own fee is not charged twice once the wrapper's fee is charged.
LIVE_FUND_FEE: Final = 0.0085

#: Two independent trend constructions from docs/research/adversarial-review.md section 1,
#: built on this repository's own frozen ``time_series_momentum`` over data the vendor never
#: touched. Held as SHARPE RATIOS, because the rescaling to this panel's trend volatility is
#: then explicit in the code rather than transcribed as a level.
OWN_BOOK_SHARPE: Final = 0.58
OWN_BOOK_SHARPE_CHARGED: Final = 0.50
JST_BOOK_SHARPE: Final = 0.43

#: Experiment 004's stated management fee, which is the fee that was subtracted a second time
#: inside the 1.80 pp/yr convention. Used only to reconstruct that figure in section 1.1.
EXP_004_FEE: Final = 0.0150
#: The convention itself, reconstructed rather than consumed.
PUBLISHED_CONVENTION: Final = 0.0180

#: The named episodes this panel can price, from docs/research/evidence-base.md.
CRISIS_WINDOWS: Final[Mapping[str, tuple[str, str]]] = {
    "2000-02 dotcom": ("2000-04", "2002-09"),
    "2007-09 GFC": ("2007-11", "2009-02"),
    "2020 Q1 covid": ("2020-02", "2020-03"),
    "2022 inflation": ("2022-01", "2022-10"),
}

#: Relative-drawdown triggers for the capitulation arm. The sibling page's corrected
#: central-case worst relative run at a 30% weight is -15.7% (its first version read -21.3%
#: off the retracted 1.80% row), so a -20% trigger sits four points beyond the central case
#: and is a pessimistic input rather than a central one.
TRIGGERS: Final = (-0.15, -0.20, -0.30)

#: Experiment 012's own window, so that the scenario built from it is the scenario that
#: page measured and not a longer one this panel happens to reach.
EXP_012_WINDOW: Final = ("2019-07", "2025-12")
#: Experiment 004's frozen post-publication era, ending where that experiment ended.
POST_PUBLICATION_WINDOW: Final = ("2012-01", "2025-12")
#: The pre-publication era, which starts before this panel does; the decay table therefore
#: reads it from the whole TSMOM file rather than from the window.
PRE_PUBLICATION_WINDOW: Final = ("1985-01", "2011-12")


# --------------------------------------------------------------------------------
# Panel
# --------------------------------------------------------------------------------


def _full_trend() -> tuple[tuple[str, ...], FloatArray]:
    """The whole TSMOM file, because the pre-publication era starts before the panel."""
    cache = RawCache()
    dataset = aqr.get_dataset("aqr_tsmom_factors")
    _, parsed, _ = aqr.load(cache, dataset)
    pairs = [
        (p, v)
        for p, v in zip(parsed.table.periods, parsed.table.column("TSMOM"), strict=True)
        if v is not None
    ]
    pairs.sort()
    return tuple(p for p, _ in pairs), np.array([v for _, v in pairs], dtype=np.float64)


def _panel() -> tuple[tuple[str, ...], FloatArray, FloatArray, FloatArray]:
    """Equity excess, trend excess and cash on the tournament's window."""
    cache = RawCache()

    trend_dataset = aqr.get_dataset("aqr_tsmom_factors")
    _, parsed, _ = aqr.load(cache, trend_dataset)
    trend = {
        p: v
        for p, v in zip(parsed.table.periods, parsed.table.column("TSMOM"), strict=True)
        if v is not None
    }

    french_dataset = french.get_dataset("french_us_ff3")
    entry = cache.entry_for(french_dataset.url)
    if entry is None:
        raise RuntimeError(
            "the Ken French three-factor file is not cached. This module never downloads, "
            "so a table can never be the thing that pulls a new vintage."
        )
    monthly = french.parse(cache, entry, dataset=french_dataset).table("monthly")
    market = {
        p: v
        for p, v in zip(monthly.periods, monthly.column("Mkt-RF"), strict=True)
        if v is not None
    }
    riskfree = {
        p: v for p, v in zip(monthly.periods, monthly.column("RF"), strict=True) if v is not None
    }

    start, end = WINDOW
    periods = tuple(
        p
        for p in sorted(set(trend) & set(market) & set(riskfree))
        if start <= p <= end
    )
    return (
        periods,
        np.array([market[p] for p in periods], dtype=np.float64),
        np.array([trend[p] for p in periods], dtype=np.float64),
        np.array([riskfree[p] for p in periods], dtype=np.float64),
    )


def _annualised_volatility(values: FloatArray) -> float:
    return float(np.std(values, ddof=1)) * math.sqrt(12.0)


def _candidate(
    equity: FloatArray, trend_net: FloatArray, cash: FloatArray, *, weight: float
) -> FloatArray:
    """Base at 1.0 plus ``weight`` of trend notional, financed, costs already inside."""
    return np.asarray(equity + weight * trend_net + cash, dtype=np.float64)


def _levered_control(
    equity: FloatArray, cash: FloatArray, *, weight: float, spread: float
) -> FloatArray:
    """The cheap index levered to the overlay's gross notional and charged the basis."""
    return np.asarray((1.0 + weight) * equity - weight * spread / 12.0 + cash, dtype=np.float64)


def _era(periods: Sequence[str], values: FloatArray, start: str, end: str) -> FloatArray:
    mask = np.array([start <= p <= end for p in periods], dtype=bool)
    return np.asarray(values[mask], dtype=np.float64)


# --------------------------------------------------------------------------------
# The prior
# --------------------------------------------------------------------------------


def build_prior(*, trend_volatility: float, realised: float, cost: float) -> PremiumPrior:
    """Eight forward views on **one stated basis**, each traced to a page and a window.

    **The basis is gross arithmetic excess over cash, per unit of trend notional, at this
    panel's trend volatility.** That is what the growth model consumes, and stating it is not
    a formality: the previous version of this prior entered the repository's 1.80 pp/yr
    convention on this axis when that figure is a *geometric* mean *net of a 1.50% fee* that
    the cost term already charges separately. Section 1.1 reconstructs it and shows that,
    restated, it is the post-publication-era scenario below and not a separate one.

    Two rescalings are used and both are explicit. A Sharpe ratio measured at some other
    volatility is multiplied by ``trend_volatility``, which preserves the Sharpe — the right
    invariant when the volatility of the delivered exposure is being changed. A fund's own
    fee is added back before the wrapper's fee is charged, so that no fee is counted twice.

    What is *not* a judgement is the labelling: three of these come from a vendor's own
    reconstruction of its own strategy, two are independent constructions on data that vendor
    never touched, two are the only retail-net evidence that exists, and one is a forecast.
    """
    scenarios = (
        PremiumScenario(
            label="premium gone",
            gross_premium=0.0,
            prior_weight=0.15,
            provenance=(
                "A forecast, not a measurement. Exp 004's post-publication sleeve is "
                "+0.883 pp/yr, 95% [-0.175, +2.165], failing Holm; the standalone Sharpe "
                "fell 1.34 -> 0.18; clause (d)'s static + vol-scaled replica reproduces "
                "43.7% of the benefit for no fee. Weighted DOWN from an earlier 0.25 "
                "because the adversarial review reproduces the post-2008 decay on two "
                "independent books and also shows a 0.07 Sharpe decade in the 1960s "
                "followed by an 0.80 one"
            ),
            vendor_authored=False,
        ),
        PremiumScenario(
            label="vendor, most recent 78 months",
            gross_premium=0.0,  # placeholder, filled from the panel
            prior_weight=0.10,
            provenance=(
                "AQR TSMOM 2019-07..2025-12, Sharpe 0.141, Sharpe-preserving rescale to this "
                "panel's trend volatility. Gross arithmetic; gross of the vendor's own "
                "trading costs by omission"
            ),
            vendor_authored=True,
        ),
        PremiumScenario(
            label="live funds ex vendor-run, net of fees",
            gross_premium=LIVE_SHARPE_EX_VENDOR * trend_volatility + LIVE_FUND_FEE,
            prior_weight=0.15,
            provenance=(
                "Exp 012's 41-fund arm after removing the five the vendor itself runs, "
                "+1.99%/yr at 8.68% volatility, Sharpe-preserving rescale, with the median "
                "shelf fee of 85 bp added back so the wrapper's fee is not charged twice. "
                "Arithmetic. Flattered by two survivorship holes"
            ),
            vendor_authored=False,
        ),
        PremiumScenario(
            label="vendor post-publication era = the restated convention",
            gross_premium=0.0,  # placeholder, filled from the panel
            prior_weight=0.15,
            provenance=(
                "AQR TSMOM 2012-01..2025-12, Sharpe 0.315, Sharpe-preserving rescale. This is "
                "ALSO decision 0004's 1.80 pp/yr convention once its geometric basis and its "
                "double-charged fee are undone (section 1.1), so the two are one scenario and "
                "are not counted twice"
            ),
            vendor_authored=True,
        ),
        PremiumScenario(
            label="live funds, headline index",
            gross_premium=LIVE_SHARPE_HEADLINE * trend_volatility + LIVE_FUND_FEE,
            prior_weight=0.10,
            provenance=(
                "Exp 012's 46-fund equal-weight index, +2.84%/yr at 8.64% volatility, same "
                "rescaling and fee add-back. Five of the 46 are run by the vendor that "
                "authors the comparator series"
            ),
            vendor_authored=False,
        ),
        PremiumScenario(
            label="independent 36-leg JST book, 1880-2020",
            gross_premium=JST_BOOK_SHARPE * trend_volatility,
            prior_weight=0.10,
            provenance=(
                "Adversarial review section 1: 18 JST countries, equity and bonds, 141 annual "
                "observations, Sharpe 0.43, t = 6.59, built on this repository's frozen "
                "time_series_momentum. Independent of the vendor and of the window. Annual "
                "data with a one-year lookback is a coarser signal than monthly, and no "
                "trading cost is charged"
            ),
            vendor_authored=False,
        ),
        PremiumScenario(
            label="independent 4-asset book, 1929-2025",
            gross_premium=OWN_BOOK_SHARPE * trend_volatility,
            prior_weight=0.15,
            provenance=(
                "Adversarial review section 1: US equity, long government, corporate and "
                "commodities, 1,157 months, Sharpe 0.58, t = 5.48 — and 0.58 in BOTH halves, "
                "1929-1990 and 1990-2025, so the tournament's window is representative. The "
                "single strongest out-of-window evidence in the prior. Charging 20 bp one-way "
                "against its 262% turnover takes the Sharpe to 0.50 and this row to "
                f"{OWN_BOOK_SHARPE_CHARGED * trend_volatility * 100:.2f}%, the only "
                "trading-cost estimate anywhere in this prior; the uncharged figure is used "
                "so that every row shares one basis"
            ),
            vendor_authored=False,
        ),
        PremiumScenario(
            label="full-window realisation",
            gross_premium=realised,
            prior_weight=0.10,
            provenance=(
                "AQR TSMOM 1990-11..2026-05, the number every trend figure in the tournament "
                "rests on. It requires believing there was no post-publication decay, against "
                "which three constructions on three sources agree there was"
            ),
            vendor_authored=True,
        ),
    )
    return PremiumPrior(scenarios=scenarios, cost_per_unit_notional=cost)


def _with_era_premia(
    prior: PremiumPrior, *, recent: float, post_publication: float
) -> PremiumPrior:
    """Fill the two placeholder scenarios from the panel rather than from a docstring."""
    filled = []
    for scenario in prior.scenarios:
        gross = scenario.gross_premium
        if scenario.label == "vendor, most recent 78 months":
            gross = recent
        elif scenario.label == "vendor post-publication era = the restated convention":
            gross = post_publication
        filled.append(
            PremiumScenario(
                label=scenario.label,
                gross_premium=gross,
                prior_weight=scenario.prior_weight,
                provenance=scenario.provenance,
                vendor_authored=scenario.vendor_authored,
            )
        )
    return PremiumPrior(
        scenarios=tuple(filled), cost_per_unit_notional=prior.cost_per_unit_notional
    )


# --------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------


def _print_panel(
    periods: Sequence[str],
    equity: FloatArray,
    trend: FloatArray,
    cash: FloatArray,
    full: tuple[tuple[str, ...], FloatArray],
) -> None:
    print("== 0. the panel, which is the construction tournament's own window ==\n")
    print(f"  {periods[0]}..{periods[-1]}  {len(periods)} months  ({len(periods) / 12:.1f} years)")
    print(
        f"  equity Mkt-RF   excess {np.mean(equity) * 1200:6.2f}%/yr  "
        f"vol {_annualised_volatility(equity) * 100:5.2f}%"
    )
    print(
        f"  trend  TSMOM    excess {np.mean(trend) * 1200:6.2f}%/yr  "
        f"vol {_annualised_volatility(trend) * 100:5.2f}%"
    )
    print(f"  correlation {np.corrcoef(equity, trend)[0, 1]:+.4f}")
    print(f"  mean cash rate {np.mean(cash) * 1200:.2f}%/yr\n")
    print("  the decay, reproduced from the same file rather than quoted:")
    full_periods, full_trend = full
    for label, (start, end) in (
        ("1985-2011 (pre/at publication)", PRE_PUBLICATION_WINDOW),
        ("2012-2025 (post-publication)", POST_PUBLICATION_WINDOW),
        ("2019-07..2025-12 (live-fund overlap)", EXP_012_WINDOW),
    ):
        era = _era(full_periods, full_trend, start, end)
        if era.size == 0:
            print(f"    {label:38} outside this panel's window")
            continue
        vol = _annualised_volatility(era)
        print(
            f"    {label:38} n={era.size:3d}  {np.mean(era) * 1200:6.2f}%/yr  "
            f"vol {vol * 100:5.2f}%  Sharpe {np.mean(era) * 12 / vol:5.3f}"
        )
    print()


def _print_prior(prior: PremiumPrior) -> None:
    print("== 1. the prior, on ONE stated basis, before any weight is computed ==\n")
    print(
        "  BASIS: gross arithmetic excess over cash, per unit of trend notional, at this\n"
        "  panel's trend volatility. Every row is on that basis and every row says so. The\n"
        "  previous version of this table entered a NET GEOMETRIC figure on this axis; the\n"
        "  labels below exist because that error was invisible without them.\n"
    )
    print(
        f"  cost charged per unit of trend notional: {prior.cost_per_unit_notional * 100:.3f}%/yr"
    )
    print("  net premium m = gross - cost; every gap depends on the two only through m.\n")
    print(f"  {'scenario':46} {'gross':>7} {'net m':>7} {'weight':>7}  vendor  basis")
    for scenario, net in zip(prior.scenarios, prior.net_premia, strict=True):
        print(
            f"  {scenario.label:46} {scenario.gross_premium * 100:6.2f}% "
            f"{net * 100:6.2f}% {scenario.prior_weight:7.2f}  "
            f"{'yes   ' if scenario.vendor_authored else 'no    '}  gross arithmetic"
        )
    lo, hi = prior.support
    print(
        f"\n  mean {prior.mean * 100:+.2f}%   median {prior.median * 100:+.2f}%   "
        f"support [{lo * 100:+.2f}%, {hi * 100:+.2f}%]   "
        f"P(m < 0) = {prior.probability_below(0.0):.2f}\n"
    )


def _print_convention_reconstruction(
    periods: Sequence[str], trend: FloatArray, trend_volatility: float
) -> None:
    """Section 1.1: rebuild decision 0004's 1.80 pp/yr and show what basis it is on."""
    era = _era(periods, trend, *POST_PUBLICATION_WINDOW)
    arithmetic = float(np.mean(era)) * 12.0
    vol = _annualised_volatility(era)
    geometric = float(np.expm1(np.mean(np.log1p(era)) * 12.0))
    print("== 1.1 where 1.80 pp/yr came from, reconstructed ==\n")
    print(
        f"  AQR TSMOM {POST_PUBLICATION_WINDOW[0]}..{POST_PUBLICATION_WINDOW[1]}, "
        f"{era.size} months:"
    )
    print(f"    arithmetic excess          {arithmetic * 100:6.2f}%/yr")
    print(f"    volatility                 {vol * 100:6.2f}%/yr")
    print(f"    geometric excess           {geometric * 100:6.2f}%/yr")
    print(
        f"    less Exp 004's {EXP_004_FEE * 100:.2f}% fee   "
        f"{(geometric - EXP_004_FEE) * 100:6.2f}%/yr   <- decision 0004 records "
        f"{PUBLISHED_CONVENTION * 100:.2f}%"
    )
    print(
        f"\n  Undoing both steps returns the era's own arithmetic mean exactly:\n"
        f"    {PUBLISHED_CONVENTION * 100:.2f} + {EXP_004_FEE * 100:.2f} "
        f"+ 0.5 x {vol * 100:.2f}^2/100 = "
        f"{(PUBLISHED_CONVENTION + EXP_004_FEE + 0.5 * vol**2) * 100:.2f}%/yr, "
        f"against the measured {arithmetic * 100:.2f}%"
    )
    print(
        f"  Sharpe-preserving rescale to this panel's {trend_volatility * 100:.2f}% "
        f"volatility: {arithmetic / vol * trend_volatility * 100:.2f}%/yr.\n"
    )
    print(
        "  So the convention IS the post-publication era, twice transformed. Two errors\n"
        "  followed from entering it raw on a gross arithmetic axis: a geometric figure was\n"
        "  compared with an arithmetic break-even, and a 1.50% fee was subtracted a second\n"
        "  time when the cost term already charges the wrapper's 99 bp. The subsample's own\n"
        "  95% interval is [-2.67, +11.00] and therefore contains the 10.98 it was being\n"
        "  used to overturn (docs/research/adversarial-review.md section 1).\n"
    )


def _report_surface(
    model: OverlayGrowthModel,
    prior: PremiumPrior,
    *,
    benchmark: Benchmark,
    label: str,
) -> None:
    surface = regret_surface(
        model, weights=WEIGHT_GRID, prior=prior, benchmark=benchmark
    )
    closed_form = minimax_regret_weight(
        model, weights=WEIGHT_GRID, support=prior.support, benchmark=benchmark
    )
    print(f"  benchmark: {label}")
    print(
        f"  {'w':>6} {'E[growth]':>10} {'max regret':>11} {'E[regret]':>10}   "
        + "  ".join(f"{m * 100:+5.1f}%" for m in prior.net_premia)
    )
    for i, w in enumerate(surface.weights):
        if w not in HEADLINE_WEIGHTS:
            continue
        cells = "  ".join(f"{g * 1e4:+6.0f}" for g in surface.growth[i])
        print(
            f"  {w:6.2f} {surface.expected_growth[i] * 1e4:9.0f}b "
            f"{surface.max_regret[i] * 1e4:10.0f}b {surface.expected_regret[i] * 1e4:9.0f}b   "
            f"{cells}"
        )
    print(
        f"  minimax-regret weight {surface.minimax_weight:.2f} on the grid, "
        f"{closed_form:.3f} in closed form; max regret "
        f"{surface.minimax_regret * 1e4:.0f} bp/yr"
    )
    low, high = robust_range(surface, tolerance=TOLERANCE)
    print(
        f"  minimum-expected-regret weight {surface.bayes_weight:.2f}, "
        f"expected regret {surface.bayes_expected_regret * 1e4:.0f} bp/yr"
    )
    print(
        f"  weights within {TOLERANCE * 1e4:.0f} bp/yr of the minimax weight's own max "
        f"regret: {low:.2f} to {high:.2f}"
    )
    try:
        marginal = model.break_even_net_premium(weight=0.30, benchmark=benchmark)
        print(
            f"  break-even net premium at w = 0.30: {marginal * 100:+.2f}%  "
            f"(gross {(marginal + prior.cost_per_unit_notional) * 100:+.2f}%)"
        )
    except ValueError:  # pragma: no cover - weight is non-zero by construction
        pass
    print()


def main() -> None:
    periods, equity, trend, cash = _panel()
    _print_panel(periods, equity, trend, cash, _full_trend())

    equity_premium = float(np.mean(equity)) * 12.0
    equity_volatility = _annualised_volatility(equity)
    trend_volatility = _annualised_volatility(trend)
    realised_trend = float(np.mean(trend)) * 12.0
    correlation = float(np.corrcoef(equity, trend)[0, 1])

    recent = _era(periods, trend, *EXP_012_WINDOW)
    post = _era(periods, trend, *POST_PUBLICATION_WINDOW)
    recent_premium = (
        float(np.mean(recent)) * 12.0 / _annualised_volatility(recent) * trend_volatility
    )
    post_premium = (
        float(np.mean(post)) * 12.0 / _annualised_volatility(post) * trend_volatility
    )

    prior = _with_era_premia(
        build_prior(
            trend_volatility=trend_volatility, realised=realised_trend, cost=WRAPPER_COST
        ),
        recent=recent_premium,
        post_publication=post_premium,
    )
    _print_prior(prior)
    _print_convention_reconstruction(periods, trend, trend_volatility)

    model = OverlayGrowthModel(
        equity_excess_return=equity_premium,
        equity_volatility=equity_volatility,
        trend_volatility=trend_volatility,
        correlation=correlation,
        equity_financing_spread=EQUITY_FINANCING_SPREAD,
    )

    print("== 2. the regret surface, cells in bp/yr of after-cost log growth ==\n")
    _report_surface(
        model, prior, benchmark="cheap_index", label="the investor's own unlevered portfolio"
    )
    _report_surface(
        model,
        prior,
        benchmark="leverage_matched",
        label=f"cheap index levered to 1+w, financed at {EQUITY_FINANCING_SPREAD * 100:.2f}% "
        f"(decision 0009 clause 3), equity premium held at this panel's realised "
        f"{equity_premium * 100:.2f}%",
    )

    print("== 2a. the leverage-matched verdict is mostly a statement about EQUITY ==\n")
    print(
        f"  {'forward equity premium':52} {'break-even m at w=0.30':>23} "
        f"{'minimax w':>10}"
    )
    for label, premium in (
        (f"realised on this panel ({equity_premium * 100:.2f}%)", equity_premium),
        ("decision 0004's working figure (5.00%)", 0.0500),
        ("valuation-proxy mapping, notional budget s2 (1.50%)", 0.0150),
    ):
        arm = OverlayGrowthModel(
            equity_excess_return=premium,
            equity_volatility=equity_volatility,
            trend_volatility=trend_volatility,
            correlation=correlation,
            equity_financing_spread=EQUITY_FINANCING_SPREAD,
        )
        break_even = arm.break_even_net_premium(weight=0.30, benchmark="leverage_matched")
        weight = minimax_regret_weight(
            arm, weights=WEIGHT_GRID, support=prior.support, benchmark="leverage_matched"
        )
        print(f"  {label:52} {break_even * 100:22.2f}% {weight:10.3f}")
    print(
        "\n  Haircutting the trend leg to a forward mean while holding the equity leg at its\n"
        "  realised one is not a consistent comparison, and the row order shows what it is\n"
        "  worth: the whole leverage-matched verdict moves with the equity input.\n"
    )

    print("== 2b. what the endpoints and the ceiling decide ==\n")
    lo, hi = prior.support
    by_label = {
        scenario.label: net
        for scenario, net in zip(prior.scenarios, prior.net_premia, strict=True)
    }
    for name, support in (
        ("full support", (lo, hi)),
        (
            "excluding the full-window realisation",
            (lo, by_label["independent 4-asset book, 1929-2025"]),
        ),
        (
            "excluding the independent constructions too",
            (lo, by_label["live funds, headline index"]),
        ),
        (
            "vendor evidence removed entirely",
            (lo, by_label["independent 4-asset book, 1929-2025"]),
        ),
        ("zero floor rather than a negative one", (0.0, hi)),
        (
            "independent constructions only",
            (
                by_label["independent 36-leg JST book, 1880-2020"],
                by_label["independent 4-asset book, 1929-2025"],
            ),
        ),
    ):
        index_weight = minimax_regret_weight(
            model, weights=WEIGHT_GRID, support=support, benchmark="cheap_index"
        )
        matched_weight = minimax_regret_weight(
            model, weights=WEIGHT_GRID, support=support, benchmark="leverage_matched"
        )
        print(
            f"  {name:42} m in [{support[0] * 100:+6.2f}%, {support[1] * 100:+6.2f}%]  "
            f"cheap index {index_weight:.3f}   leverage-matched {matched_weight:.3f}"
        )
    print()
    for ceiling in (0.30, 0.40, 0.60, 1.00):
        grid = tuple(round(0.02 * i, 2) for i in range(round(ceiling / 0.02) + 1))
        indexed = minimax_regret_weight(
            model, weights=grid, support=(lo, hi), benchmark="cheap_index"
        )
        matched = minimax_regret_weight(
            model, weights=grid, support=(lo, hi), benchmark="leverage_matched"
        )
        print(
            f"  action-space ceiling {ceiling:.2f}:  cheap index {indexed:.3f}"
            f"   leverage-matched {matched:.3f}"
        )
    print(
        "\n  Against a cheap index the minimax weight tracks the ceiling almost one for one:\n"
        "  it is reporting the grid, not the data. Against a leverage-matched control it does\n"
        "  not, because most of the premium range puts the optimum at zero.\n"
    )

    print("== 2c. the prior's weights, swept ==\n")
    alternatives = {
        "as stated": prior.weights,
        "all mass on decay (zero, recent vendor, post-pub)": (
            0.45, 0.25, 0.0, 0.30, 0.0, 0.0, 0.0, 0.0
        ),
        "no weight on the full-window realisation": DECAY_WEIGHTS,
        "uniform over the eight": tuple([0.125] * 8),
        "vendor evidence removed entirely": (0.23, 0.0, 0.23, 0.0, 0.15, 0.15, 0.24, 0.0),
        "independent constructions only": (0.0, 0.0, 0.0, 0.0, 0.0, 0.40, 0.60, 0.0),
        "all mass on the live-fund evidence": (0.0, 0.0, 0.50, 0.0, 0.50, 0.0, 0.0, 0.0),
    }
    print(
        f"  {'weighting':46} {'E[m]':>7} {'support':>18} "
        f"{'cheap idx':>20} {'lev-matched':>20}"
    )
    print(f"  {'':46} {'':>7} {'':>18} {'minimax / Bayes':>20} {'minimax / Bayes':>20}")
    for name, weights in alternatives.items():
        alt = prior.reweighted(weights)
        cheap_surface = regret_surface(
            model, weights=WEIGHT_GRID, prior=alt, benchmark="cheap_index"
        )
        matched_surface = regret_surface(
            model, weights=WEIGHT_GRID, prior=alt, benchmark="leverage_matched"
        )
        lo_alt, hi_alt = alt.support
        print(
            f"  {name:46} {alt.mean * 100:6.2f}% "
            f"[{lo_alt * 100:+6.2f}%,{hi_alt * 100:+6.2f}%] "
            f"{cheap_surface.minimax_weight:11.2f} / {cheap_surface.bayes_weight:.2f} "
            f"{matched_surface.minimax_weight:14.2f} / {matched_surface.bayes_weight:.2f}"
        )
    print(
        "\n  Minimum-expected-regret is bang-bang under every weighting tried: the expected\n"
        "  growth gap is linear in E[m] plus a fixed variance drag, so a Bayes rule on growth\n"
        "  alone returns a corner too. Neither decision rule produces an interior weight from\n"
        "  the growth arithmetic. Section 4 is where an interior answer comes from.\n"
    )

    print("== 3. resolution: what this instrument could see ==\n")
    window_years = len(periods) / 12.0
    print(f"  {'w':>5} {'m':>7} {'gap vs index':>13} {'MDE80':>8} {'years':>8}")
    for weight in (0.20, 0.30):
        for net in (prior.median, prior.mean, prior.support[1]):
            trend_net = restate_annual_mean(trend, annual_mean=net)
            candidate = _candidate(equity, trend_net, cash, weight=weight)
            control = np.asarray(equity + cash, dtype=np.float64)
            difference = candidate - control
            gap = model.growth_gap(
                weight=weight, net_premium=net, benchmark="cheap_index"
            )
            mde = minimum_detectable_effect(difference)
            years = years_to_resolve(
                gap=gap, minimum_detectable_effect=mde, window_years=window_years
            )
            print(
                f"  {weight:5.2f} {net * 100:6.2f}% {gap * 100:12.2f}% "
                f"{mde * 100:7.2f}% {years:8.0f}"
            )
    print(
        f"\n  Effective sample size: {len(periods)} months at a {BLOCK_MONTHS}-month block is "
        f"about {len(periods) / BLOCK_MONTHS:.0f}\n"
        "  independent observations, and the decade table below has about "
        f"{len(periods) / 120:.0f} distinct decades in it.\n"
    )

    print("== 4. the asymmetry, arm one: the position ends before the premium arrives ==\n")
    print(
        f"  Capitulation rule: sell the sleeve the first month relative wealth sits a stated\n"
        f"  distance below its own running peak, then hold the control for good. {RESAMPLES}\n"
        f"  joint {BLOCK_MONTHS}-month block resamples, 30-year horizon. The trigger is an INPUT.\n"
    )
    cheap_control = np.asarray(equity + cash, dtype=np.float64)
    print(
        f"  {'w':>5} {'m':>7} {'P(quit)':>8} {'median yr':>10} "
        f"{'held':>8} {'after quitting':>15} {'cost':>8} {'P(lose)':>8}"
    )
    for weight in HOLDABILITY_WEIGHTS:
        for net in (prior.support[0], prior.median, prior.mean):
            trend_net = restate_annual_mean(trend, annual_mean=net)
            outcome = abandonment_adjusted_gap(
                _candidate(equity, trend_net, cash, weight=weight),
                cheap_control,
                weight=weight,
                net_premium=net,
                trigger=-0.20,
                horizon_years=30.0,
                resamples=RESAMPLES,
                block_length=BLOCK_MONTHS,
                rng=np.random.default_rng(SEED),
            )
            months = outcome.median_months_to_abandonment
            print(
                f"  {weight:5.2f} {net * 100:6.2f}% "
                f"{outcome.probability_abandoned:8.1%} "
                f"{months / 12.0 if math.isfinite(months) else float('nan'):10.1f} "
                f"{outcome.gap_if_held * 1e4:7.0f}b "
                f"{outcome.gap_with_abandonment * 1e4:14.0f}b "
                f"{outcome.capitulation_cost * 1e4:7.0f}b "
                f"{outcome.probability_underperform_with_abandonment:8.1%}"
            )
    print(
        "\n  Quitting truncates both tails and it truncates the good one hardest: at a\n"
        "  negative premium abandonment SAVES money, at a positive one it costs. That is what\n"
        "  makes the two errors asymmetric and it is why a growth-only surface cannot see it.\n"
    )

    print("== 4c. the same rule with a contribution stream inside the path ==\n")
    print(
        "  The same resamples, the same -20% trigger, and the same dollars paid into BOTH\n"
        "  arms every month: a fixed instalment of the stated share of starting capital a\n"
        "  year, or the same share of the benchmark portfolio's wealth so the stream keeps\n"
        "  pace with it. Relative wealth is the ratio of the two pots INCLUDING the new\n"
        "  money, which is what a statement shows; the held and after-quitting columns are\n"
        "  then the terminal wealth ratio per year, money-weighted, not a return gap.\n"
    )
    print(
        f"  {'w':>5} {'m':>7} {'contrib':>8} {'basis':>16} {'P(quit)':>8} {'median yr':>10} "
        f"{'held':>8} {'after quitting':>15} {'P(lose)':>8}"
    )
    for weight in CONTRIBUTION_WEIGHTS:
        for net in (prior.support[0], prior.median):
            trend_net = restate_annual_mean(trend, annual_mean=net)
            candidate = _candidate(equity, trend_net, cash, weight=weight)
            for basis in ("starting_capital", "control_wealth"):
                for rate in CONTRIBUTION_RATES:
                    if rate == 0.0 and basis == "control_wealth":
                        continue
                    outcome = abandonment_adjusted_gap(
                        candidate,
                        cheap_control,
                        weight=weight,
                        net_premium=net,
                        trigger=-0.20,
                        horizon_years=30.0,
                        resamples=RESAMPLES,
                        block_length=BLOCK_MONTHS,
                        rng=np.random.default_rng(SEED),
                        contribution_rate=rate,
                        contribution_basis=basis,
                    )
                    months = outcome.median_months_to_abandonment
                    print(
                        f"  {weight:5.2f} {net * 100:6.2f}% {rate:8.0%} {basis:>16} "
                        f"{outcome.probability_abandoned:8.1%} "
                        f"{months / 12.0 if math.isfinite(months) else float('nan'):10.1f} "
                        f"{outcome.gap_if_held * 1e4:7.0f}b "
                        f"{outcome.gap_with_abandonment * 1e4:14.0f}b "
                        f"{outcome.probability_underperform_with_abandonment:8.1%}"
                    )
    print(
        "\n  A contribution stream dilutes an accumulated relative deficit with money that has\n"
        "  not yet had time to fall behind. Whether that moves the -20% trigger materially\n"
        "  is what the rows above measure; the zero-contribution rows reproduce section 4.\n"
    )

    print("== 4a. the regret surface once capitulation is inside the path ==\n")
    decayed = prior.reweighted(DECAY_WEIGHTS)

    def control_for(benchmark: Benchmark, overlay: float) -> FloatArray:
        if benchmark == "cheap_index":
            return cheap_control
        return _levered_control(
            equity, cash, weight=overlay, spread=EQUITY_FINANCING_SPREAD
        )

    benchmarks: tuple[Benchmark, ...] = ("cheap_index", "leverage_matched")
    for trigger in TRIGGERS:
        for benchmark in benchmarks:
            gaps = [
                [
                    abandonment_adjusted_gap(
                        _candidate(
                            equity,
                            restate_annual_mean(trend, annual_mean=net),
                            cash,
                            weight=weight,
                        ),
                        control_for(benchmark, weight),
                        weight=weight,
                        net_premium=net,
                        trigger=trigger,
                        horizon_years=30.0,
                        resamples=RESAMPLES,
                        block_length=BLOCK_MONTHS,
                        rng=np.random.default_rng(SEED),
                    ).gap_with_abandonment
                    for net in prior.net_premia
                ]
                for weight in HOLDABILITY_WEIGHTS
            ]
            full = regret_from_gaps(
                gaps, weights=HOLDABILITY_WEIGHTS, prior=prior, benchmark=benchmark
            )
            narrow = regret_from_gaps(
                gaps, weights=HOLDABILITY_WEIGHTS, prior=decayed, benchmark=benchmark
            )
            full_lo, full_hi = robust_range(full, tolerance=TOLERANCE)
            narrow_lo, narrow_hi = robust_range(narrow, tolerance=TOLERANCE)
            print(
                f"  trigger {trigger * 100:.0f}%, {benchmark:16}  full support: minimax "
                f"{full.minimax_weight:.2f} (robust {full_lo:.2f}-{full_hi:.2f}), Bayes "
                f"{full.bayes_weight:.2f}   |   decay-only support: minimax "
                f"{narrow.minimax_weight:.2f} (robust {narrow_lo:.2f}-{narrow_hi:.2f}), "
                f"Bayes {narrow.bayes_weight:.2f}"
            )
            if trigger == -0.20 and benchmark == "cheap_index":
                print(
                    f"    {'w':>6} {'E[growth]':>10} {'max regret':>11} {'E[regret]':>10}   "
                    + "  ".join(f"{m * 100:+5.1f}%" for m in prior.net_premia)
                )
                for i, w in enumerate(full.weights):
                    cells = "  ".join(f"{g * 1e4:+6.0f}" for g in full.growth[i])
                    print(
                        f"    {w:6.2f} {full.expected_growth[i] * 1e4:9.0f}b "
                        f"{full.max_regret[i] * 1e4:10.0f}b "
                        f"{full.expected_regret[i] * 1e4:9.0f}b   {cells}"
                    )
    print(
        "\n  Read the two halves of each line against each other. Under the full support the\n"
        "  capitulation surface runs to the ceiling, because minimax reads ONLY the endpoints\n"
        "  and the correction to the prior's basis moved its MIDDLE, not its ends. Dropping\n"
        "  the full-window scenario leaves the cheap-index answer at 0.35-0.40 and the\n"
        "  leverage-matched answer at zero. No decision rule built out of growth alone, with\n"
        "  or without capitulation inside the path, returns a weight below 0.28 against the\n"
        "  investor's own portfolio under any reweighting tried, and none returns one above\n"
        "  0.12 against a leverage-matched control at this panel's realised equity premium.\n"
        "  That gap is the whole disagreement and it is a choice of comparator.\n"
    )

    print("== 4b. the marginal trade, which is where an interior answer actually comes from ==\n")
    print(
        "  Each step up the ladder, priced twice: the expected growth it buys under the\n"
        "  prior with capitulation inside the path, and the abandonment probability it buys.\n"
        f"  Trigger -20%, benchmark: the investor's own portfolio. {RESAMPLES} resamples.\n"
    )
    ladder_growth: list[float] = []
    ladder_quit: list[float] = []
    for weight in HOLDABILITY_WEIGHTS:
        outcomes = [
            abandonment_adjusted_gap(
                _candidate(
                    equity, restate_annual_mean(trend, annual_mean=net), cash, weight=weight
                ),
                cheap_control,
                weight=weight,
                net_premium=net,
                trigger=-0.20,
                horizon_years=30.0,
                resamples=RESAMPLES,
                block_length=BLOCK_MONTHS,
                rng=np.random.default_rng(SEED),
            )
            for net in prior.net_premia
        ]
        ladder_growth.append(
            float(np.dot([o.gap_with_abandonment for o in outcomes], prior.weights))
        )
        ladder_quit.append(
            float(np.dot([o.probability_abandoned for o in outcomes], prior.weights))
        )
    print(
        f"  {'step':>13} {'E[growth]':>11} {'d growth':>10} {'P(quit)':>9} {'d P(quit)':>10} "
        f"{'bp per point':>13}"
    )
    for i in range(1, len(HOLDABILITY_WEIGHTS)):
        d_growth = (ladder_growth[i] - ladder_growth[i - 1]) * 1e4
        d_quit = (ladder_quit[i] - ladder_quit[i - 1]) * 100.0
        rate = d_growth / d_quit if d_quit > 1e-9 else float("inf")
        print(
            f"  {HOLDABILITY_WEIGHTS[i - 1]:5.2f} -> {HOLDABILITY_WEIGHTS[i]:4.2f} "
            f"{ladder_growth[i] * 1e4:10.0f}b {d_growth:9.1f}b "
            f"{ladder_quit[i]:8.1%} {d_quit:9.1f}pp {rate:12.2f}"
        )
    print(
        "\n  The exchange rate is the last column. It falls steeply through 0.05-0.15 and then\n"
        "  FLATTENS: on the corrected basis every step from 0.15 to 0.40 still buys more than\n"
        "  one basis point a year per percentage point of abandonment risk. On the previous,\n"
        "  understated basis the same column fell below 1.0 by 0.20 and was read as an elbow.\n"
        "  IT NO LONGER IDENTIFIES A CUT-OFF BELOW 0.30, and that is the largest single\n"
        "  consequence of the basis correction for this page's recommendation. It rests on a\n"
        "  trigger nobody has estimated, which is stated in the page.\n"
    )

    print("== 5. the asymmetry, arm two: the decade the sleeve exists for ==\n")
    print(
        f"  {'w':>5} {'m':>7} {'worst equity decade':>22} {'equity':>8} {'candidate':>10} "
        f"{'worst decile':>13} {'elsewhere':>10}"
    )
    for weight in (0.20, 0.30):
        for net in (prior.support[0], prior.median, prior.mean):
            trend_net = restate_annual_mean(trend, annual_mean=net)
            candidate = _candidate(equity, trend_net, cash, weight=weight)
            control = np.asarray(equity + cash, dtype=np.float64)
            decade = conditional_decade_gaps(
                periods, candidate, control, weight=weight, net_premium=net
            )
            window = f"{decade.worst_window[0]}..{decade.worst_window[1]}"
            print(
                f"  {weight:5.2f} {net * 100:6.2f}% {window:>22} "
                f"{decade.worst_equity_growth * 100:7.2f}% "
                f"{decade.worst_candidate_growth * 100:9.2f}% "
                f"{decade.mean_gap_in_worst_decile * 100:12.2f}% "
                f"{decade.mean_gap_elsewhere * 100:9.2f}%"
            )
    print()
    print("  the named episodes, compounded peak to trough over the stated months:\n")
    print(f"  {'episode':20} {'months':>7} {'equity':>9} " + "  ".join(
        f"{f'w={w:.2f}':>9}" for w in (0.20, 0.30)
    ))
    for episode, (start, end) in CRISIS_WINDOWS.items():
        mask = np.array([start <= p <= end for p in periods], dtype=bool)
        if not mask.any():
            continue
        episode_control = np.asarray(equity + cash, dtype=np.float64)[mask]
        episode_cells: list[str] = []
        for weight in (0.20, 0.30):
            trend_net = restate_annual_mean(trend, annual_mean=prior.median)
            candidate = _candidate(equity, trend_net, cash, weight=weight)[mask]
            episode_cells.append(
                f"{drawdown_summary(np.cumprod(1.0 + candidate)).max_drawdown * 100:8.1f}%"
            )
        print(
            f"  {episode:20} {int(mask.sum()):7d} "
            f"{drawdown_summary(np.cumprod(1.0 + episode_control)).max_drawdown * 100:8.1f}%  "
            + "  ".join(episode_cells)
        )
    print(
        "\n  Trend legs are restated to the prior's median so that this table prices the\n"
        "  correlation rather than the realised mean. The mean is a forecast; the shape is\n"
        "  what the sleeve is bought for.\n"
    )

    print("== 6. the outcome distribution at the candidate weights ==\n")
    for weight in (0.20, 0.30):
        trend_net = restate_annual_mean(trend, annual_mean=prior.median)
        candidate = _candidate(equity, trend_net, cash, weight=weight)
        for control_name, benchmark_series in (
            ("cheap index", np.asarray(equity + cash, dtype=np.float64)),
            (
                "leverage-matched",
                _levered_control(equity, cash, weight=weight, spread=EQUITY_FINANCING_SPREAD),
            ),
        ):
            print(
                f"  w = {weight:.2f} against {control_name}, at m = {prior.median * 100:+.2f}%  "
                f"(tracking error {weight * trend_volatility * 100:.2f}%/yr)"
            )
            print(
                f"    {'horizon':>8} {'P(underperform)':>16} {'p5':>7} {'median':>8} {'p95':>7} "
                f"{'median DD':>10} {'p5 DD':>8}"
            )
            for horizon in (10.0, 20.0, 30.0):
                distribution = horizon_outcomes(
                    candidate,
                    benchmark_series,
                    horizon_years=horizon,
                    resamples=RESAMPLES,
                    block_length=BLOCK_MONTHS,
                    rng=np.random.default_rng(SEED),
                )
                print(
                    f"    {horizon:7.0f}y {distribution.probability_underperform:15.1%} "
                    f"{distribution.relative_wealth_quantiles['p5']:7.3f} "
                    f"{distribution.median_relative_wealth:8.3f} "
                    f"{distribution.relative_wealth_quantiles['p95']:7.3f} "
                    f"{distribution.median_max_drawdown * 100:9.1f}% "
                    f"{distribution.drawdown_quantiles['p5'] * 100:7.1f}%"
                )
            print()

    print("== 7. the cost sweep, which is a translation of the premium axis ==\n")
    print(f"  {'cost per unit of trend notional':46} {'shifts every m by':>18}")
    for label, cost in (
        ("sheltered, wrapper all-in (this page's central case)", WRAPPER_COST),
        ("the sibling page's 96 bp convention", WRAPPER_COST_LOW),
        ("taxable, plus RSST's 32 bp of distribution drag", WRAPPER_COST_TAXABLE),
    ):
        print(f"  {label:46} {(WRAPPER_COST - cost) * 100:+17.2f}%")
    print(
        "\n  A 32 bp tax difference moves the whole surface by 32 bp of net premium and moves\n"
        "  no minimax weight by more than the grid spacing. Cost is not what decides this.\n"
    )


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    main()
