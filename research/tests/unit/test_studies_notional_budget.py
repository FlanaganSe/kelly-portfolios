"""Tests for the notional-budget study.

Every fixture here is computed independently of the function under test: by hand, by a
grid search over the objective itself, by a second closed form, by a seeded simulation, or
by another module in this repository. Nothing is pinned to output the study produced.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.kelly import kelly_leverage, kinked_growth_rate
from portfolio_edge.studies.notional_budget import (
    EQUITY_KINDS,
    FinancingLeg,
    GrossNotionalRung,
    Holding,
    NotionalLeg,
    apply_leverage,
    financing_stack,
    gross_notional_ladder,
    growth_optimal_pair,
    horizon_outcomes,
    kinked_growth_optimal_leverage,
    leverage_confidence_interval,
    leverage_turnover,
    notional_for_drawdown,
    portfolio_exposure,
    premium_for_leverage,
    volatility_targeted_leverage,
)

# ---------------------------------------------------------------------------
# 1. Exposure arithmetic
# ---------------------------------------------------------------------------

#: The candidate portfolio, from filings. 70% of capital in a plain US equity fund and
#: 30% in RSST, whose 2026-04-30 N-PORT shows 107.2% equity and 100% trend notional.
CANDIDATE = (
    Holding("core", 0.70, (NotionalLeg("us-equity", 1.0),)),
    Holding("RSST", 0.30, (NotionalLeg("us-equity", 1.072), NotionalLeg("trend", 1.0))),
)


def test_candidate_exposure_matches_hand_arithmetic() -> None:
    summary = portfolio_exposure(CANDIDATE)
    # 0.70 * 1.0 + 0.30 * 1.072 = 0.70 + 0.3216
    assert summary.equity_notional == pytest.approx(1.0216, abs=1e-12)
    assert summary.by_kind["trend"] == pytest.approx(0.30, abs=1e-12)
    assert summary.gross_notional == pytest.approx(1.3216, abs=1e-12)
    assert summary.financed_notional == pytest.approx(0.3216, abs=1e-12)
    assert summary.non_equity_notional == pytest.approx(0.30, abs=1e-12)
    assert summary.capital_deployed == pytest.approx(1.0)
    assert summary.cash_weight == pytest.approx(0.0)
    # The effective equity share is against a nominal 100%-equity portfolio, so it is the
    # equity notional itself and NOT the fraction of capital deployed.
    assert summary.effective_equity_share == pytest.approx(1.0216, abs=1e-12)


def test_an_unlevered_portfolio_has_zero_financed_notional() -> None:
    summary = portfolio_exposure([Holding("all equity", 1.0, (NotionalLeg("equity", 1.0),))])
    assert summary.gross_notional == pytest.approx(1.0)
    assert summary.financed_notional == pytest.approx(0.0)


def test_holding_cash_gives_negative_financed_notional() -> None:
    summary = portfolio_exposure([Holding("equity", 0.6, (NotionalLeg("equity", 1.0),))])
    assert summary.cash_weight == pytest.approx(0.4)
    assert summary.financed_notional == pytest.approx(-0.4)


def test_weights_above_one_dollar_of_capital_are_refused() -> None:
    with pytest.raises(ValueError, match="deploy"):
        portfolio_exposure(
            [
                Holding("a", 0.7, (NotionalLeg("equity", 1.0),)),
                Holding("b", 0.7, (NotionalLeg("equity", 1.0),)),
            ]
        )


def test_a_negative_weight_is_refused() -> None:
    with pytest.raises(ValueError, match="negative"):
        portfolio_exposure([Holding("short", -0.1, (NotionalLeg("equity", 1.0),))])


def test_every_equity_kind_on_the_shelf_counts_as_equity_beta() -> None:
    assert {"us-equity", "global-equity", "equity"} == set(EQUITY_KINDS)
    mixed = portfolio_exposure(
        [
            Holding("us", 0.4, (NotionalLeg("us-equity", 1.0),)),
            Holding("global", 0.3, (NotionalLeg("global-equity", 1.0),)),
            Holding("wrapper", 0.3, (NotionalLeg("equity", 1.0), NotionalLeg("trend", 1.0))),
        ]
    )
    assert mixed.equity_notional == pytest.approx(1.0)
    assert mixed.non_equity_notional == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# 2. The premium a leverage implies, and the kink
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("leverage", [0.0, 0.5, 1.0, 1.3216, 2.0, 3.0])
@pytest.mark.parametrize("volatility", [0.10, 0.1586, 0.22])
def test_premium_for_leverage_inverts_kelly_leverage(leverage: float, volatility: float) -> None:
    premium = premium_for_leverage(leverage=leverage, volatility=volatility)
    assert kelly_leverage(excess_return=premium, volatility=volatility) == pytest.approx(
        leverage, abs=1e-12
    )


def test_unit_leverage_break_even_is_the_variance_and_the_funding_rule_gap() -> None:
    """The premium at which 1.0x is optimal is ``sigma**2``, which is the same quantity
    as ``a_p - sigma_p**2 = 0`` — the point at which the funding-rule gap changes sign."""
    volatility = 0.1586
    assert premium_for_leverage(leverage=1.0, volatility=volatility) == pytest.approx(
        volatility**2, abs=1e-15
    )


@pytest.mark.parametrize(
    ("premium", "spread", "cost"),
    [
        (0.01, 0.0000, 0.0),
        (0.02, 0.0060, 0.0),
        (0.03, 0.0060, 0.0),
        (0.04, 0.0060, 0.0),
        (0.05, 0.0200, 0.0),
        (0.06, 0.0060, 0.0096),
        (0.025, 0.0090, 0.0010),
    ],
)
def test_kinked_optimum_matches_a_grid_search_over_the_kinked_objective(
    premium: float, spread: float, cost: float
) -> None:
    """Independent check: maximise :func:`kinked_growth_rate` on a fine grid.

    ``kinked_growth_rate`` takes a *mean* return and a lending rate; with the lending rate
    at zero the mean return is the excess return, which is the parameterisation used here.
    """
    volatility = 0.1586
    grid = np.linspace(0.0, 5.0, 500_001)
    values = [
        kinked_growth_rate(
            float(leverage),
            mean_return=premium,
            volatility=volatility,
            lending_rate=0.0,
            borrow_spread=spread,
            instrument_cost=lambda level: cost * level,
        )
        for leverage in grid
    ]
    numerical = float(grid[int(np.argmax(values))])
    closed_form = kinked_growth_optimal_leverage(
        excess_return=premium,
        volatility=volatility,
        borrow_spread=spread,
        cost_on_notional=cost,
    )
    assert closed_form == pytest.approx(numerical, abs=1e-4)


def test_the_kink_is_a_flat_region_as_wide_as_the_spread() -> None:
    """A whole range of premium forecasts implies exactly 1.0x, and the range in
    excess-return units is the spread."""
    volatility = 0.16
    variance = volatility**2
    spread = 0.0060
    just_below = kinked_growth_optimal_leverage(
        excess_return=variance + 1e-6, volatility=volatility, borrow_spread=spread
    )
    just_above = kinked_growth_optimal_leverage(
        excess_return=variance + spread - 1e-6, volatility=volatility, borrow_spread=spread
    )
    assert just_below == pytest.approx(1.0)
    assert just_above == pytest.approx(1.0)
    outside = kinked_growth_optimal_leverage(
        excess_return=variance + spread + 1e-4, volatility=volatility, borrow_spread=spread
    )
    assert outside > 1.0


def test_zero_spread_and_zero_cost_reduce_to_plain_kelly() -> None:
    for premium in (0.005, 0.02, 0.05):
        assert kinked_growth_optimal_leverage(
            excess_return=premium, volatility=0.15
        ) == pytest.approx(kelly_leverage(excess_return=premium, volatility=0.15))


def test_a_premium_below_the_cost_gives_zero_rather_than_a_short() -> None:
    assert kinked_growth_optimal_leverage(
        excess_return=0.002, volatility=0.15, cost_on_notional=0.01
    ) == pytest.approx(0.0)


def test_leverage_interval_standard_error_is_free_of_the_premium() -> None:
    low = leverage_confidence_interval(excess_return=0.01, volatility=0.16, years=30.0)
    high = leverage_confidence_interval(excess_return=0.09, volatility=0.16, years=30.0)
    assert low.standard_error == pytest.approx(high.standard_error)
    assert low.standard_error == pytest.approx(1.0 / (0.16 * math.sqrt(30.0)))
    # And the interval is symmetric about the plug-in, with the 95% half-width at 1.96 SE.
    assert high.point - high.lower == pytest.approx(high.upper - high.point)
    assert (high.upper - high.point) / high.standard_error == pytest.approx(1.959964, abs=1e-5)


def test_the_standard_error_falls_with_the_square_root_of_calendar_span() -> None:
    ten = leverage_confidence_interval(excess_return=0.05, volatility=0.16, years=10.0)
    forty = leverage_confidence_interval(excess_return=0.05, volatility=0.16, years=40.0)
    assert ten.standard_error / forty.standard_error == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# 3. The two-asset optimum
# ---------------------------------------------------------------------------


def test_growth_optimal_pair_reduces_to_two_independent_kellys_at_zero_correlation() -> None:
    pair = growth_optimal_pair(
        base_excess_return=0.05,
        base_volatility=0.16,
        diversifier_excess_return=0.02,
        diversifier_volatility=0.12,
        correlation=0.0,
    )
    assert pair.base_notional == pytest.approx(0.05 / 0.16**2)
    assert pair.diversifier_notional == pytest.approx(0.02 / 0.12**2)


def test_growth_optimal_pair_matches_a_grid_search_on_the_quadratic_objective() -> None:
    mu = np.array([0.05, 0.02])
    volatilities = np.array([0.16, 0.12])
    correlation = -0.15
    covariance = correlation * volatilities[0] * volatilities[1]
    sigma = np.array(
        [[volatilities[0] ** 2, covariance], [covariance, volatilities[1] ** 2]]
    )
    axis = np.linspace(-2.0, 4.0, 1201)
    best_value, best = -np.inf, (math.nan, math.nan)
    for a in axis:
        for b in axis:
            w = np.array([a, b])
            value = float(mu @ w - 0.5 * w @ sigma @ w)
            if value > best_value:
                best_value, best = value, (float(a), float(b))
    pair = growth_optimal_pair(
        base_excess_return=0.05,
        base_volatility=0.16,
        diversifier_excess_return=0.02,
        diversifier_volatility=0.12,
        correlation=correlation,
    )
    assert pair.base_notional == pytest.approx(best[0], abs=6e-3)
    assert pair.diversifier_notional == pytest.approx(best[1], abs=6e-3)
    assert pair.peak_growth_over_cash == pytest.approx(best_value, abs=1e-4)


def test_a_diversifier_with_a_negative_net_return_is_shorted_not_clipped() -> None:
    pair = growth_optimal_pair(
        base_excess_return=0.05,
        base_volatility=0.16,
        diversifier_excess_return=-0.01,
        diversifier_volatility=0.12,
        correlation=0.0,
    )
    assert pair.diversifier_notional < 0.0


def test_a_degenerate_correlation_is_refused() -> None:
    with pytest.raises(ValueError, match="correlation"):
        growth_optimal_pair(
            base_excess_return=0.05,
            base_volatility=0.16,
            diversifier_excess_return=0.02,
            diversifier_volatility=0.12,
            correlation=1.0,
        )


# ---------------------------------------------------------------------------
# 4. Ladder and drawdown-tolerance sizing
# ---------------------------------------------------------------------------


def _fixture_panel() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260822)
    months = 480
    base = rng.normal(0.05 / 12.0, 0.16 / math.sqrt(12.0), months)
    sleeve = rng.normal(0.03 / 12.0, 0.12 / math.sqrt(12.0), months)
    cash = np.full(months, 0.03 / 12.0)
    return base, sleeve, cash


def test_gross_notional_ladder_reproduces_a_hand_built_path() -> None:
    base, sleeve, cash = _fixture_panel()
    rung = gross_notional_ladder(
        base,
        sleeve,
        cash,
        rungs=((1.2, 0.3),),
        base_cost=0.001,
        diversifier_cost=0.0096,
        borrow_spread=0.0060,
    )[0]
    charge = 0.001 * 1.2 + 0.0096 * 0.3 + 0.0060 * (1.5 - 1.0)
    expected_excess = 1.2 * base + 0.3 * sleeve - charge / 12.0
    expected_total = expected_excess + cash
    curve = np.cumprod(1.0 + expected_total)
    assert rung.gross_notional == pytest.approx(1.5)
    assert rung.geometric_return == pytest.approx(float(curve[-1]) ** (12.0 / base.size) - 1.0)
    assert rung.max_drawdown == pytest.approx(drawdown_summary(curve).max_drawdown)
    assert rung.volatility == pytest.approx(
        float(np.std(expected_excess, ddof=1)) * math.sqrt(12.0)
    )


def test_no_borrow_spread_is_charged_below_one_times_gross() -> None:
    base, sleeve, cash = _fixture_panel()
    with_spread = gross_notional_ladder(
        base, sleeve, cash, rungs=((0.6, 0.0),), borrow_spread=0.05
    )[0]
    without = gross_notional_ladder(base, sleeve, cash, rungs=((0.6, 0.0),))[0]
    assert with_spread.geometric_return == pytest.approx(without.geometric_return)


def _rung(gross: float, drawdown: float) -> GrossNotionalRung:
    return GrossNotionalRung(
        base_notional=gross,
        diversifier_notional=0.0,
        gross_notional=gross,
        geometric_return=0.0,
        volatility=0.0,
        sharpe=0.0,
        max_drawdown=drawdown,
        months_under_water=0,
    )


def test_notional_for_drawdown_interpolates_linearly() -> None:
    rungs = [_rung(1.0, -0.40), _rung(1.5, -0.60)]
    # -0.50 sits exactly halfway between -0.40 and -0.60, so the answer is 1.25.
    assert notional_for_drawdown(rungs, tolerance=-0.50) == pytest.approx(1.25)
    assert notional_for_drawdown(rungs, tolerance=-0.40) == pytest.approx(1.0)
    assert notional_for_drawdown(rungs, tolerance=-0.60) == pytest.approx(1.5)


def test_notional_for_drawdown_returns_nan_when_even_the_first_rung_breaches() -> None:
    rungs = [_rung(1.0, -0.55), _rung(1.5, -0.70)]
    assert math.isnan(notional_for_drawdown(rungs, tolerance=-0.30))


def test_notional_for_drawdown_returns_the_top_rung_when_nothing_breaches() -> None:
    rungs = [_rung(1.0, -0.20), _rung(1.5, -0.25)]
    assert notional_for_drawdown(rungs, tolerance=-0.90) == pytest.approx(1.5)


def test_notional_for_drawdown_refuses_a_positive_tolerance() -> None:
    with pytest.raises(ValueError, match="non-positive"):
        notional_for_drawdown([_rung(1.0, -0.2)], tolerance=0.3)


def test_notional_for_drawdown_refuses_unsorted_rungs() -> None:
    with pytest.raises(ValueError, match="increasing"):
        notional_for_drawdown([_rung(1.5, -0.2), _rung(1.0, -0.3)], tolerance=-0.5)


# ---------------------------------------------------------------------------
# 5. Financing
# ---------------------------------------------------------------------------


def test_financing_stack_matches_hand_arithmetic_for_the_candidate() -> None:
    """RSST at 30% of capital: 99 bp of fee on capital, plus a 62 bp equity-futures basis
    on 0.331 of financed E-mini notional, less a 3 bp incumbent fee."""
    stack = financing_stack(
        label="RSST",
        portfolio_weight=0.30,
        fee_on_capital=0.0099,
        legs=(
            FinancingLeg("E-mini", 0.331, 0.0062, "test"),
            FinancingLeg("trend book", 1.000, 0.0000, "test"),
        ),
        displaced_fee=0.0003,
        diversifier_notional=1.000,
    )
    assert stack.financing_cost_in_wrapper == pytest.approx(0.331 * 0.0062)
    assert stack.total_cost_in_wrapper == pytest.approx(0.0099 + 0.331 * 0.0062)
    assert stack.total_cost_in_portfolio == pytest.approx(0.30 * (0.0099 + 0.331 * 0.0062))
    assert stack.incremental_cost_in_portfolio == pytest.approx(
        0.30 * (0.0099 + 0.331 * 0.0062 - 0.0003)
    )
    assert stack.diversifier_notional_obtained == pytest.approx(0.30)
    # Per unit of notional obtained: the portfolio cost divided by 0.30 of trend notional.
    assert stack.incremental_cost_per_unit_notional == pytest.approx(
        0.0099 + 0.331 * 0.0062 - 0.0003
    )


def test_cost_per_unit_notional_is_nan_when_no_diversifier_notional_is_obtained() -> None:
    stack = financing_stack(
        label="levered equity",
        portfolio_weight=0.5,
        fee_on_capital=0.002,
        legs=(),
        displaced_fee=0.0003,
    )
    assert math.isnan(stack.incremental_cost_per_unit_notional)
    assert stack.financing_cost_in_wrapper == pytest.approx(0.0)


def test_a_physically_held_leg_finances_nothing() -> None:
    assert FinancingLeg("physical fund", 0.0, 0.0062, "test").cost == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 6. Volatility targeting
# ---------------------------------------------------------------------------


def test_volatility_targeted_leverage_uses_only_information_ending_at_t_minus_one() -> None:
    """Change a single future observation and no earlier leverage may move."""
    rng = np.random.default_rng(7)
    series = rng.normal(0.0, 0.04, 120)
    original = volatility_targeted_leverage(series, window=12, target=0.15, cap=3.0)
    perturbed_series = series.copy()
    perturbed_series[60] += 0.50
    perturbed = volatility_targeted_leverage(perturbed_series, window=12, target=0.15, cap=3.0)
    np.testing.assert_allclose(original[:61], perturbed[:61], equal_nan=True)
    assert not np.allclose(original[61:], perturbed[61:], equal_nan=True)


def test_volatility_targeted_leverage_matches_hand_arithmetic_at_one_index() -> None:
    rng = np.random.default_rng(11)
    series = rng.normal(0.0, 0.04, 60)
    path = volatility_targeted_leverage(series, window=24, target=0.15, cap=5.0)
    trailing = float(np.std(series[6:30], ddof=1)) * math.sqrt(12.0)
    assert path[30] == pytest.approx(0.15 / trailing)
    assert np.all(np.isnan(path[:24]))


def test_the_cap_and_floor_bind() -> None:
    quiet = np.full(60, 0.0001)
    quiet[::2] = -0.0001
    path = volatility_targeted_leverage(quiet, window=12, target=0.15, cap=2.0, floor=0.5)
    assert np.nanmax(path) == pytest.approx(2.0)
    loud = np.full(60, 0.30)
    loud[::2] = -0.30
    floored = volatility_targeted_leverage(loud, window=12, target=0.15, cap=2.0, floor=0.5)
    assert np.nanmin(floored) == pytest.approx(0.5)


def test_leverage_turnover_counts_notional_traded_per_year() -> None:
    # Alternating 1.0 and 1.5 over 12 months: 11 changes of 0.5 across 12 observations.
    path = np.array([1.0, 1.5] * 6)
    assert leverage_turnover(path) == pytest.approx(11 * 0.5 * 12.0 / 12.0)
    assert leverage_turnover(np.full(24, 1.3)) == pytest.approx(0.0)


def test_a_burn_in_does_not_manufacture_a_first_trade() -> None:
    path = np.array([np.nan, np.nan, 1.4, 1.4, 1.4])
    assert leverage_turnover(path) == pytest.approx(0.0)


def test_apply_leverage_charges_fee_spread_and_trading_inside_the_path() -> None:
    base = np.array([0.01, -0.02, 0.03, 0.00])
    cash = np.full(4, 0.002)
    path = np.array([1.0, 1.5, 1.5, 0.8])
    result = apply_leverage(
        base,
        cash,
        path,
        borrow_spread=0.012,
        cost_on_notional=0.006,
        round_trip_cost=0.0010,
        periods_per_year=12,
    )
    traded = np.array([0.0, 0.5, 0.0, 0.7])
    charge = (
        0.006 * path / 12.0 + 0.012 * np.maximum(path - 1.0, 0.0) / 12.0 + 0.0010 * traded
    )
    expected = path * base - charge
    np.testing.assert_allclose(result.excess_returns, expected, rtol=0, atol=1e-15)
    np.testing.assert_allclose(result.total_returns, expected + cash, rtol=0, atol=1e-15)
    assert result.turnover_per_year == pytest.approx(1.2 * 12.0 / 4.0)
    assert result.trading_cost_charged == pytest.approx(0.0010 * 1.2 * 12.0 / 4.0)
    assert result.mean_leverage == pytest.approx(1.2)
    assert result.max_leverage == pytest.approx(1.5)


def test_apply_leverage_trims_the_burn_in_rather_than_treating_it_as_unlevered() -> None:
    base = np.array([0.01, -0.02, 0.03, 0.00])
    cash = np.full(4, 0.0)
    path = np.array([np.nan, np.nan, 1.0, 1.0])
    result = apply_leverage(base, cash, path)
    assert result.months == 2
    np.testing.assert_allclose(result.excess_returns, base[2:])


def test_apply_leverage_refuses_a_gap_after_the_path_starts() -> None:
    with pytest.raises(ValueError, match="gap"):
        apply_leverage(
            np.array([0.01, 0.02, 0.03]),
            np.zeros(3),
            np.array([1.0, np.nan, 1.0]),
        )


# ---------------------------------------------------------------------------
# 7. The outcome distribution
# ---------------------------------------------------------------------------


def test_identical_arms_never_underperform_and_have_unit_relative_wealth() -> None:
    base, _sleeve, cash = _fixture_panel()
    arm = base + cash
    outcome = horizon_outcomes(
        arm,
        arm,
        horizon_years=10.0,
        resamples=200,
        block_length=24,
        rng=np.random.default_rng(3),
    )
    assert outcome.probability_underperform == pytest.approx(0.0)
    assert outcome.median_relative_wealth == pytest.approx(1.0, abs=1e-12)
    assert outcome.median_max_drawdown == pytest.approx(outcome.median_control_max_drawdown)


def test_a_uniformly_better_arm_never_underperforms() -> None:
    base, _sleeve, cash = _fixture_panel()
    control = base + cash
    candidate = control + 0.001
    outcome = horizon_outcomes(
        candidate,
        control,
        horizon_years=10.0,
        resamples=300,
        block_length=12,
        rng=np.random.default_rng(5),
    )
    assert outcome.probability_underperform == pytest.approx(0.0)
    assert outcome.median_relative_wealth > 1.0
    assert outcome.relative_wealth_quantiles["p5"] > 1.0


def test_the_arms_are_resampled_jointly_not_independently() -> None:
    """Paired resampling is what makes the difference one investor's two portfolios.

    A perfectly correlated pair differing by a constant has zero spread in its relative
    terminal wealth under joint resampling; under independent resampling it would not.
    """
    base, _sleeve, cash = _fixture_panel()
    control = base + cash
    candidate = 1.001 * (1.0 + control) - 1.0
    outcome = horizon_outcomes(
        candidate,
        control,
        horizon_years=10.0,
        resamples=400,
        block_length=24,
        rng=np.random.default_rng(9),
    )
    spread = (
        outcome.relative_wealth_quantiles["p95"] - outcome.relative_wealth_quantiles["p5"]
    )
    assert spread == pytest.approx(0.0, abs=1e-9)
    assert outcome.median_relative_wealth == pytest.approx(1.001**120, rel=1e-9)


def test_horizon_outcomes_rejects_mismatched_arms_and_bad_grids() -> None:
    base, _sleeve, _cash = _fixture_panel()
    with pytest.raises(ValueError, match="same shape"):
        horizon_outcomes(
            base,
            base[:-1],
            horizon_years=5.0,
            resamples=10,
            block_length=12,
            rng=np.random.default_rng(1),
        )
    with pytest.raises(ValueError, match="block_length"):
        horizon_outcomes(
            base,
            base,
            horizon_years=5.0,
            resamples=10,
            block_length=0,
            rng=np.random.default_rng(1),
        )
