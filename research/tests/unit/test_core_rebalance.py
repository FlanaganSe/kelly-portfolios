"""Tests for :mod:`portfolio_edge.core.rebalance`."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

from portfolio_edge.core.costs import ProportionalCostModel, TurnoverCostModel
from portfolio_edge.core.portfolio import check_weights_sum_to_one
from portfolio_edge.core.rebalance import (
    BuyAndHold,
    CalendarRebalance,
    CashFlowDirected,
    RebalancePolicy,
    RelativeThreshold,
    buy_and_hold_weights,
    diversification_return,
    kappa_autocorrelation,
    kappa_series,
    simulate,
    two_period_rebalance_advantage,
)
from portfolio_edge.core.returns import geometric_mean
from portfolio_edge.core.wealth import CashFlowTiming

EQUAL = [0.5, 0.5]


# --------------------------------------------------------------------------------------
# The exact two-period identity
# --------------------------------------------------------------------------------------


def test_two_period_identity_holds_for_arbitrary_returns() -> None:
    """R_REBAL - R_HOLD = -w_S w_B kappa_1 kappa_2, exactly.

    Re-derived algebraically: with a_t = 1 + r_S,t and b_t = 1 + r_B,t and u = w_S,
        REBAL - HOLD = u(u-1) a1 a2 + v(v-1) b1 b2 + uv(a1 b2 + a2 b1)
                     = -uv (a1 - b1)(a2 - b2) = -u v kappa_1 kappa_2.
    Source: Rattray, Granger, Harvey and Van Hemert (2020), via
    docs/research/portfolio-edge-research-framework.md, "Rebalancing".
    """
    rng = np.random.default_rng(20260811)
    for _ in range(50):
        w_s = float(rng.uniform(0.05, 0.95))
        returns = rng.normal(0.0, 0.10, size=(2, 2))
        weights = [w_s, 1.0 - w_s]

        rebalanced = simulate(returns, weights, CalendarRebalance(interval=1))
        held = simulate(returns, weights, BuyAndHold())
        difference = rebalanced.terminal_wealth - held.terminal_wealth

        kappa = kappa_series(returns)
        expected = two_period_rebalance_advantage(w_s, float(kappa[0]), float(kappa[1]))
        assert difference == pytest.approx(expected, rel=0.0, abs=1e-14)


def test_rebalance_identity_fixture_minus_384_basis_points() -> None:
    """Fixture: w_S = 0.6, w_B = 0.4, kappa_1 = kappa_2 = -40% -> -3.84 pp exactly.

    docs/research/portfolio-edge-research-framework.md, "Numerical fixtures".
    Re-derived from the stated inputs: the coefficient is -w_S w_B = -0.24 and the
    product of the two kappas is (-0.4)^2 = 0.16, so the difference is
    -0.24 * 0.16 = -0.0384. The figure is re-derived per parameterisation, never
    hardcoded: the framework explicitly names it as one of three constants that
    must not be.
    """
    w_s, w_b = 0.6, 0.4
    kappa_1 = kappa_2 = -0.40
    assert -w_s * w_b == pytest.approx(-0.24, rel=0.0, abs=1e-15)
    derived = -w_s * w_b * kappa_1 * kappa_2
    assert derived == pytest.approx(-0.0384, rel=0.0, abs=1e-15)
    assert two_period_rebalance_advantage(w_s, kappa_1, kappa_2) == pytest.approx(
        derived, rel=1e-15, abs=0.0
    )

    # Realised on an actual return path with those kappas: stocks flat, bonds +40%.
    returns = [[0.0, 0.40], [0.0, 0.40]]
    kappa = kappa_series(returns)
    assert kappa == pytest.approx([kappa_1, kappa_2], rel=0.0, abs=1e-15)
    rebalanced = simulate(returns, [w_s, w_b], CalendarRebalance(interval=1))
    held = simulate(returns, [w_s, w_b], BuyAndHold())
    assert rebalanced.terminal_wealth - held.terminal_wealth == pytest.approx(
        derived, rel=0.0, abs=1e-15
    )


def test_rebalancing_loses_when_relative_performance_trends_and_wins_on_reversal() -> None:
    """Rebalancing is short a straddle on relative performance."""
    trending = [[0.10, -0.10], [0.10, -0.10]]  # kappa positive twice
    reversing = [[0.10, -0.10], [-0.10, 0.10]]  # kappa changes sign
    for returns, expect_loss in ((trending, True), (reversing, False)):
        rebalanced = simulate(returns, EQUAL, CalendarRebalance(interval=1))
        held = simulate(returns, EQUAL, BuyAndHold())
        difference = rebalanced.terminal_wealth - held.terminal_wealth
        assert (difference < 0.0) is expect_loss


def test_kappa_autocorrelation_is_the_diagnostic_not_diversification_return() -> None:
    """A trending kappa has positive serial correlation; a reversing one negative."""
    trending = np.column_stack([np.full(20, 0.02), np.full(20, -0.02)])
    trending[:, 0] += np.linspace(0.0, 0.01, 20)
    reversing = np.column_stack(
        [np.array([0.05 if t % 2 == 0 else -0.05 for t in range(20)]), np.zeros(20)]
    )
    assert kappa_autocorrelation(kappa_series(trending)) > 0.0
    assert kappa_autocorrelation(kappa_series(reversing)) < 0.0


def test_kappa_requires_exactly_two_assets() -> None:
    with pytest.raises(ValueError, match="exactly two assets"):
        kappa_series([[0.1, 0.2, 0.3]])


# --------------------------------------------------------------------------------------
# Diversification return
# --------------------------------------------------------------------------------------


def test_diversification_return_fixture() -> None:
    """Fixture: two assets, equal weights, returns +25%/-10% and +50%/-20%, rho = 1
    -> g_A = 6.0660%, g_B = 9.5445%, sum w_i g_i = 7.8053%, g_p = 8.1087%,
    DR = +0.3035%.

    docs/research/portfolio-edge-research-framework.md, "Numerical fixtures".
    Everything below is re-derived from the four stated returns. The assets are
    perfectly correlated in sign (rho = 1 across the two states), which is exactly
    why the positive DR here is an accounting artefact of unequal volatilities
    rather than evidence of a diversification benefit.
    """
    asset_a = [0.25, -0.10]
    asset_b = [0.50, -0.20]

    g_a = math.sqrt(1.25 * 0.90) - 1.0
    g_b = math.sqrt(1.50 * 0.80) - 1.0
    assert g_a == pytest.approx(0.060660, rel=0.0, abs=5e-7)
    assert g_b == pytest.approx(0.095445, rel=0.0, abs=5e-7)
    assert geometric_mean(asset_a) == pytest.approx(g_a, rel=1e-14, abs=0.0)
    assert geometric_mean(asset_b) == pytest.approx(g_b, rel=1e-14, abs=0.0)

    weighted = 0.5 * g_a + 0.5 * g_b
    assert weighted == pytest.approx(0.078053, rel=0.0, abs=5e-7)

    returns = [[0.25, 0.50], [-0.10, -0.20]]
    rebalanced = simulate(returns, EQUAL, CalendarRebalance(interval=1))
    g_p = rebalanced.terminal_wealth ** (1.0 / 2.0) - 1.0
    assert g_p == pytest.approx(math.sqrt(1.375 * 0.85) - 1.0, rel=1e-14, abs=0.0)
    assert g_p == pytest.approx(0.081087, rel=0.0, abs=5e-7)

    assert diversification_return(EQUAL, [g_a, g_b], g_p) == pytest.approx(
        0.003035, rel=0.0, abs=5e-7
    )


def test_diversification_return_benchmark_is_not_investable() -> None:
    """sum_i w_i g_i is not the growth rate of any portfolio one can hold.

    The investable comparison is buy-and-hold, and whether rebalancing wins is
    decided by the sign of kappa_1 * kappa_2, not by the diversification return
    (Willenbrock 2011; Rattray et al. 2020). On this fixture the two kappas have
    opposite signs, so rebalancing gains -- but that is the identity talking, not
    the positive DR, and the companion test below shows a trending path where the
    DR is still positive while rebalancing loses.
    """
    returns = [[0.25, 0.50], [-0.10, -0.20]]
    rebalanced = simulate(returns, EQUAL, CalendarRebalance(interval=1))
    held = simulate(returns, EQUAL, BuyAndHold())
    kappa = kappa_series(returns)
    # kappa_1 = -0.25, kappa_2 = +0.10: opposite signs, so the identity predicts a gain.
    assert float(kappa[0]) * float(kappa[1]) < 0.0
    assert rebalanced.terminal_wealth > held.terminal_wealth


def test_a_positive_diversification_return_coexists_with_losing_to_buy_and_hold() -> None:
    """The decisive counterexample: DR > 0 while the rebalanced portfolio loses.

    Two assets whose relative performance trends in the same direction for two
    periods. The diversification return is positive by construction because the
    components' log growth is convex-penalised, yet the investable comparison goes
    the other way. A variance identity must never be reported as realised alpha.
    """
    returns = [[0.20, -0.10], [0.20, -0.10]]
    rebalanced = simulate(returns, EQUAL, CalendarRebalance(interval=1))
    held = simulate(returns, EQUAL, BuyAndHold())
    g_a = geometric_mean([0.20, 0.20])
    g_b = geometric_mean([-0.10, -0.10])
    g_p = rebalanced.terminal_wealth**0.5 - 1.0
    assert diversification_return(EQUAL, [g_a, g_b], g_p) > 0.0
    assert rebalanced.terminal_wealth < held.terminal_wealth


# --------------------------------------------------------------------------------------
# Zero expected profit
# --------------------------------------------------------------------------------------


def test_zero_expected_profit_over_sixteen_paths() -> None:
    """Fixture: two assets, i.i.d. +25%/-20% at p = 0.5, equal weights, two periods,
    16 paths -> E[W_T] = 1.050625 for BOTH strategies; the long-rebalanced /
    short-buy-and-hold trade has E[profit] = 0 and s.d. $0.02531.

    docs/research/portfolio-edge-research-framework.md, "Numerical fixtures", from
    Chambers and Zdanowicz (2014). Re-derived: E[1 + r] = 0.5(1.25) + 0.5(0.80) =
    1.025 per asset per period, and both strategies are linear in independent
    periods, so E[W_2] = 1.025^2 = 1.050625. The profit is -0.25 kappa_1 kappa_2 with
    E[kappa] = 0 and E[kappa^2] = 0.5 * 0.45^2 = 0.10125, so the standard deviation
    is 0.25 * 0.10125 = 0.0253125 exactly.
    """
    assert pytest.approx(1.025, rel=0.0, abs=1e-15) == 0.5 * 1.25 + 0.5 * 0.80
    assert pytest.approx(1.050625, rel=0.0, abs=1e-15) == 1.025**2

    outcomes = (0.25, -0.20)
    paths = list(itertools.product(outcomes, repeat=4))
    assert len(paths) == 16

    rebalanced_wealth: list[float] = []
    held_wealth: list[float] = []
    for s1, s2, b1, b2 in paths:
        returns = [[s1, b1], [s2, b2]]
        rebalanced_wealth.append(
            simulate(returns, EQUAL, CalendarRebalance(interval=1)).terminal_wealth
        )
        held_wealth.append(simulate(returns, EQUAL, BuyAndHold()).terminal_wealth)

    assert float(np.mean(rebalanced_wealth)) == pytest.approx(
        1.050625, rel=0.0, abs=1e-14
    )
    assert float(np.mean(held_wealth)) == pytest.approx(1.050625, rel=0.0, abs=1e-14)

    profits = np.array(rebalanced_wealth) - np.array(held_wealth)
    assert float(np.mean(profits)) == pytest.approx(0.0, rel=0.0, abs=1e-15)
    # Population standard deviation over the full 16-path enumeration, not a sample.
    expected_sd = 0.25 * (0.5 * 0.45**2)
    assert expected_sd == pytest.approx(0.0253125, rel=0.0, abs=1e-15)
    assert float(np.std(profits, ddof=0)) == pytest.approx(expected_sd, rel=1e-13, abs=0.0)


def test_the_rebalanced_portfolio_has_higher_expected_log_wealth() -> None:
    """The live objection recorded in the framework: Chambers and Zdanowicz's zero
    expected *wealth* profit coexists with higher expected *log* wealth, which they
    dismiss as "an arbitrary nonlinear transformation of wealth". That dismissal is
    a stance, not a theorem, and it is the premise a Kelly investor rejects.
    """
    outcomes = (0.25, -0.20)
    rebalanced_log: list[float] = []
    held_log: list[float] = []
    for s1, s2, b1, b2 in itertools.product(outcomes, repeat=4):
        returns = [[s1, b1], [s2, b2]]
        rebalanced_log.append(
            math.log(simulate(returns, EQUAL, CalendarRebalance(interval=1)).terminal_wealth)
        )
        held_log.append(math.log(simulate(returns, EQUAL, BuyAndHold()).terminal_wealth))
    assert float(np.mean(rebalanced_log)) > float(np.mean(held_log))


# --------------------------------------------------------------------------------------
# Policies
# --------------------------------------------------------------------------------------


def _drifting_returns(periods: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(loc=[0.006, 0.002], scale=[0.045, 0.012], size=(periods, 2))


def test_every_policy_starts_from_identical_weights_and_cash_flows() -> None:
    returns = _drifting_returns(60, 3)
    flows = [100.0] * 60
    target = [0.6, 0.4]
    policies: list[RebalancePolicy] = [
        BuyAndHold(),
        CalendarRebalance(interval=1),
        CalendarRebalance(interval=3),
        CalendarRebalance(interval=12),
        RelativeThreshold(band=0.20),
        CashFlowDirected(),
    ]
    results = [
        simulate(returns, target, policy, initial_wealth=10_000.0, cash_flows=flows)
        for policy in policies
    ]
    for result in results:
        assert result.weights[0] == pytest.approx(target, rel=0.0, abs=1e-15)
        assert result.cash_flows == pytest.approx(flows, rel=0.0, abs=1e-12)
        assert result.equity_curve.size == 61
        for row in result.weights:
            check_weights_sum_to_one(row, tolerance=1e-9)


def test_buy_and_hold_never_trades() -> None:
    returns = _drifting_returns(24, 4)
    result = simulate(returns, [0.6, 0.4], BuyAndHold())
    assert result.total_turnover == 0.0
    assert result.total_costs == 0.0
    assert float(np.max(np.abs(result.trades))) == 0.0


def test_buy_and_hold_weights_drift_away_from_the_target() -> None:
    returns = _drifting_returns(120, 5)
    result = simulate(returns, [0.6, 0.4], BuyAndHold())
    assert abs(float(result.weights[-1][0]) - 0.6) > 0.02
    path = buy_and_hold_weights([0.6, 0.4], returns)
    assert path[-1] == pytest.approx(result.weights[-1], rel=1e-12, abs=0.0)


def test_calendar_rebalancing_restores_the_target_on_its_schedule() -> None:
    returns = _drifting_returns(24, 6)
    result = simulate(returns, [0.6, 0.4], CalendarRebalance(interval=6))
    traded_periods = np.flatnonzero(result.turnover > 1e-15)
    # Period 0 starts on target, so the first non-zero trade is at period 6.
    assert traded_periods.tolist() == [6, 12, 18]


def test_monthly_rebalancing_turns_over_more_than_annual() -> None:
    returns = _drifting_returns(120, 7)
    monthly = simulate(returns, [0.6, 0.4], CalendarRebalance(interval=1))
    annual = simulate(returns, [0.6, 0.4], CalendarRebalance(interval=12))
    held = simulate(returns, [0.6, 0.4], BuyAndHold())
    assert monthly.total_turnover > annual.total_turnover > held.total_turnover


def test_a_relative_threshold_only_trades_once_the_band_is_breached() -> None:
    returns = _drifting_returns(120, 8)
    tight = simulate(returns, [0.6, 0.4], RelativeThreshold(band=0.02))
    loose = simulate(returns, [0.6, 0.4], RelativeThreshold(band=0.30))
    assert tight.total_turnover > loose.total_turnover
    assert float(np.count_nonzero(tight.turnover)) > float(np.count_nonzero(loose.turnover))


def test_a_relative_band_is_measured_against_the_target_weight() -> None:
    """The trigger is max_i |w_i / w_target_i - 1| > band, checked before the period's
    return, so a portfolio starting on target cannot fire in period 0.

    Hand-derived: 60/40 with returns +50%/-50% drifts to 0.9/1.1 and 0.2/1.1, i.e.
    weights 0.8182/0.1818. The relative deviations are +36.4% in equity and -54.5% in
    bonds, so a 25% band fires and a 60% band does not.
    """
    returns = [[0.50, -0.50], [0.0, 0.0]]
    result = simulate(returns, [0.6, 0.4], RelativeThreshold(band=0.25))
    assert float(result.weights[1][0]) == pytest.approx(0.9 / 1.1, rel=1e-14, abs=0.0)
    assert pytest.approx(0.363636, rel=0.0, abs=5e-7) == 0.9 / 1.1 / 0.6 - 1.0
    assert result.turnover[0] == 0.0
    assert float(result.turnover[1]) > 0.0

    wide = simulate(returns, [0.6, 0.4], RelativeThreshold(band=0.60))
    assert wide.total_turnover == 0.0


def test_cash_flow_directed_rebalancing_uses_contributions_and_never_trades() -> None:
    returns = _drifting_returns(60, 9)
    directed = simulate(
        returns, [0.6, 0.4], CashFlowDirected(), initial_wealth=10_000.0, cash_flows=[500.0] * 60
    )
    held = simulate(
        returns, [0.6, 0.4], BuyAndHold(), initial_wealth=10_000.0, cash_flows=[500.0] * 60
    )
    assert directed.total_turnover == 0.0
    assert directed.total_costs == 0.0
    # Directed flows keep the portfolio closer to target than pro-rata flows do.
    directed_drift = float(np.mean(np.abs(directed.weights[:, 0] - 0.6)))
    held_drift = float(np.mean(np.abs(held.weights[:, 0] - 0.6)))
    assert directed_drift < held_drift


def test_cash_flow_directed_withdrawals_sell_the_overweight_asset() -> None:
    returns = [[0.0, 0.0]]
    result = simulate(
        returns,
        [0.5, 0.5],
        CashFlowDirected(),
        initial_wealth=1000.0,
        cash_flows=[-100.0],
    )
    # From an on-target portfolio the withdrawal is spread and the target is kept.
    assert result.weights[-1] == pytest.approx([0.5, 0.5], rel=1e-12, abs=0.0)
    assert result.terminal_wealth == pytest.approx(900.0, rel=1e-12, abs=0.0)


def test_costs_are_charged_on_trades_and_reduce_terminal_wealth() -> None:
    returns = _drifting_returns(120, 10)
    free = simulate(returns, [0.6, 0.4], CalendarRebalance(interval=1))
    costed = simulate(
        returns,
        [0.6, 0.4],
        CalendarRebalance(interval=1),
        cost_model=TurnoverCostModel(k=1.7),
    )
    assert costed.total_costs > 0.0
    assert costed.terminal_wealth < free.terminal_wealth


def test_a_policy_that_never_trades_pays_no_costs_however_expensive_the_model() -> None:
    returns = _drifting_returns(60, 11)
    result = simulate(
        returns, [0.6, 0.4], BuyAndHold(), cost_model=ProportionalCostModel(cost_bp=500.0)
    )
    assert result.total_costs == 0.0


def test_cash_flow_timing_is_declared_and_changes_the_answer() -> None:
    returns = [[0.10, 0.10]]
    beginning = simulate(
        returns,
        EQUAL,
        BuyAndHold(),
        initial_wealth=1000.0,
        cash_flows=[100.0],
        cash_flow_timing=CashFlowTiming.BEGINNING,
    )
    end = simulate(
        returns,
        EQUAL,
        BuyAndHold(),
        initial_wealth=1000.0,
        cash_flows=[100.0],
        cash_flow_timing=CashFlowTiming.END,
    )
    assert beginning.terminal_wealth == pytest.approx(1100.0 * 1.10, rel=1e-13, abs=0.0)
    assert end.terminal_wealth == pytest.approx(1000.0 * 1.10 + 100.0, rel=1e-13, abs=0.0)


def test_target_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="outside 1"):
        simulate([[0.01, 0.01]], [0.6, 0.5], BuyAndHold())


def test_cash_flow_length_must_match_the_return_matrix() -> None:
    with pytest.raises(ValueError, match="cash_flows length"):
        simulate([[0.01, 0.01]], EQUAL, BuyAndHold(), cash_flows=[1.0, 2.0])
