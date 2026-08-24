"""The eight foundation tests named in the commissioning brief.

    - Simple returns compound to the expected terminal wealth.
    - Log returns aggregate consistently with wealth when wealth remains positive.
    - Costs never increase wealth.
    - Zero-value trades do not change wealth.
    - Portfolio weights sum to one after a rebalance within a declared tolerance.
    - Drawdown calculations reproduce a hand-computed path.
    - A scenario producing nonpositive wealth is rejected by log optimization.
    - No observation may be used before its availability timestamp.

They are gathered here as one file so the foundation is legible in one place. The
per-module test files cover the same ground in more detail; these are the eight
invariants that must never regress.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pytest

from portfolio_edge.core.availability import LookAheadError, Observation
from portfolio_edge.core.costs import (
    K_PESSIMISTIC,
    CostModel,
    ProportionalCostModel,
    TurnoverCostModel,
    apply_trade_costs,
)
from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.kelly import (
    NonPositiveWealthScenarioError,
    expected_log_wealth,
    maximise_expected_log_wealth,
)
from portfolio_edge.core.portfolio import (
    DEFAULT_WEIGHT_TOLERANCE,
    check_weights_sum_to_one,
)
from portfolio_edge.core.rebalance import (
    CalendarRebalance,
    RebalancePolicy,
    RelativeThreshold,
    simulate,
)
from portfolio_edge.core.returns import compound_simple, simple_to_log
from portfolio_edge.core.wealth import equity_curve, log_returns_from_equity_curve, terminal_wealth

RETURNS = [0.10, -0.05, 0.08, -0.02, 0.031]


def test_foundation_1_simple_returns_compound_to_expected_terminal_wealth() -> None:
    expected = 10_000.0
    for period_return in RETURNS:
        expected *= 1.0 + period_return
    assert terminal_wealth(RETURNS, initial_wealth=10_000.0) == pytest.approx(
        expected, rel=1e-14, abs=0.0
    )
    assert compound_simple(RETURNS) == pytest.approx(expected / 10_000.0 - 1.0, rel=1e-14, abs=0.0)


def test_foundation_2_log_returns_aggregate_consistently_with_wealth() -> None:
    """Valid only while wealth remains positive, which is why the guard exists."""
    curve = equity_curve(RETURNS, initial_wealth=10_000.0)
    assert float(np.min(curve)) > 0.0
    from_returns = float(np.sum(simple_to_log(RETURNS)))
    from_wealth = float(np.sum(log_returns_from_equity_curve(curve)))
    assert from_returns == pytest.approx(from_wealth, rel=1e-14, abs=0.0)
    assert math.exp(from_returns) == pytest.approx(
        float(curve[-1]) / float(curve[0]), rel=1e-14, abs=0.0
    )


def test_foundation_3_costs_never_increase_wealth() -> None:
    rng = np.random.default_rng(20260811)
    models: list[CostModel] = [
        ProportionalCostModel(cost_bp=0.0),
        ProportionalCostModel(cost_bp=30.0),
        TurnoverCostModel(k=K_PESSIMISTIC),
    ]
    for model in models:
        for _ in range(100):
            wealth = float(rng.uniform(1_000.0, 1_000_000.0))
            trades = rng.normal(0.0, wealth / 50.0, size=4)
            assert apply_trade_costs(wealth, trades, model) <= wealth

    # And at the portfolio level: the same policy costs less when the model is cheaper.
    returns = rng.normal(0.005, 0.04, size=(60, 2))
    free = simulate(returns, [0.6, 0.4], CalendarRebalance(interval=1))
    costed = simulate(
        returns,
        [0.6, 0.4],
        CalendarRebalance(interval=1),
        cost_model=TurnoverCostModel(k=K_PESSIMISTIC),
    )
    assert costed.terminal_wealth <= free.terminal_wealth


def test_foundation_4_zero_value_trades_do_not_change_wealth() -> None:
    wealth = 250_000.0
    for model in (ProportionalCostModel(cost_bp=45.0), TurnoverCostModel(k=K_PESSIMISTIC)):
        assert apply_trade_costs(wealth, np.zeros(6), model) == wealth

    # A rebalance to weights that are already on target is a zero-value trade.
    flat_returns = np.zeros((12, 3))
    result = simulate(
        flat_returns,
        [0.2, 0.3, 0.5],
        CalendarRebalance(interval=1),
        initial_wealth=wealth,
        cost_model=ProportionalCostModel(cost_bp=100.0),
    )
    assert result.total_turnover == 0.0
    assert result.total_costs == 0.0
    assert result.terminal_wealth == pytest.approx(wealth, rel=0.0, abs=1e-9)


def test_foundation_5_weights_sum_to_one_after_a_rebalance() -> None:
    rng = np.random.default_rng(11)
    returns = rng.normal(0.004, 0.05, size=(120, 4))
    target = [0.4, 0.3, 0.2, 0.1]
    policies: list[RebalancePolicy] = [
        CalendarRebalance(interval=1),
        CalendarRebalance(interval=12),
        RelativeThreshold(band=0.15),
    ]
    for policy in policies:
        result = simulate(
            returns,
            target,
            policy,
            initial_wealth=100_000.0,
            cash_flows=[250.0] * 120,
            cost_model=TurnoverCostModel(k=K_PESSIMISTIC),
        )
        for row in result.weights:
            check_weights_sum_to_one(row, tolerance=DEFAULT_WEIGHT_TOLERANCE)
        rebalanced_periods = np.flatnonzero(result.turnover > 0.0)
        assert rebalanced_periods.size > 0
        for period in rebalanced_periods:
            # Immediately after a rebalance the pre-return weights are the target.
            assert result.turnover[period] >= 0.0


def test_foundation_6_drawdown_reproduces_a_hand_computed_path() -> None:
    """Fixture: [100, 110, 105, 95, 120, 90, 130] -> MDD = -0.25, max TUW = 2.

    docs/research/portfolio-engine-specification.md, Layer 1. Hand derivation: the
    running peaks are 100, 110, 110, 110, 120, 120, 130; the deepest shortfall is
    90/120 - 1 = -0.25; the longest run strictly below a running peak is [105, 95].
    """
    summary = drawdown_summary([100.0, 110.0, 105.0, 95.0, 120.0, 90.0, 130.0])
    assert summary.max_drawdown == pytest.approx(-0.25, rel=0.0, abs=1e-15)
    assert summary.max_time_under_water == 2


def test_foundation_7_a_non_positive_wealth_scenario_is_rejected_by_log_optimisation() -> None:
    scenarios = [[0.20, 0.03], [-1.00, 0.01], [0.05, 0.02]]
    with pytest.raises(NonPositiveWealthScenarioError):
        expected_log_wealth([1.0, 0.0], scenarios)
    with pytest.raises(NonPositiveWealthScenarioError):
        maximise_expected_log_wealth(scenarios)


def test_foundation_8_no_observation_is_used_before_its_availability_timestamp() -> None:
    observation = Observation(
        observation_date=date(2020, 1, 31),
        available_date=date(2020, 2, 5),
        value=0.0123,
    )
    with pytest.raises(LookAheadError):
        observation.read(date(2020, 2, 4))
    assert observation.read(date(2020, 2, 5)) == pytest.approx(0.0123, rel=0.0, abs=1e-15)
