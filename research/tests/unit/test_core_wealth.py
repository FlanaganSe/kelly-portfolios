"""Tests for :mod:`portfolio_edge.core.wealth`."""

from __future__ import annotations

import math

import pytest

from portfolio_edge.core.wealth import (
    CashFlowTiming,
    NonPositiveWealthError,
    equity_curve,
    equity_curve_with_cash_flows,
    log_returns_from_equity_curve,
    returns_from_equity_curve,
    terminal_wealth,
)


def test_equity_curve_has_one_more_point_than_returns() -> None:
    curve = equity_curve([0.1, -0.1, 0.2], initial_wealth=100.0)
    assert curve.size == 4
    assert float(curve[0]) == 100.0


def test_simple_returns_compound_to_the_expected_terminal_wealth() -> None:
    returns = [0.10, -0.05, 0.08, -0.02]
    expected = 1000.0 * math.prod(1.0 + r for r in returns)
    assert terminal_wealth(returns, initial_wealth=1000.0) == pytest.approx(
        expected, rel=1e-14, abs=0.0
    )


def test_equity_curve_round_trips_through_implied_returns() -> None:
    returns = [0.10, -0.05, 0.08]
    curve = equity_curve(returns, initial_wealth=250.0)
    assert returns_from_equity_curve(curve) == pytest.approx(returns, rel=1e-14, abs=0.0)


def test_log_returns_from_equity_curve_sum_to_total_log_growth() -> None:
    curve = equity_curve([0.10, -0.05, 0.08], initial_wealth=250.0)
    total = float(sum(log_returns_from_equity_curve(curve)))
    assert total == pytest.approx(
        math.log(float(curve[-1]) / float(curve[0])), rel=1e-14, abs=0.0
    )


def test_wealth_reaching_zero_raises_rather_than_producing_nan() -> None:
    with pytest.raises(NonPositiveWealthError) as info:
        equity_curve([0.1, -1.0, 0.5])
    assert info.value.index == 2
    assert info.value.wealth == pytest.approx(0.0, rel=0.0, abs=1e-15)


def test_wealth_going_negative_raises() -> None:
    with pytest.raises(NonPositiveWealthError):
        equity_curve([-1.5])


def test_non_positive_initial_wealth_is_rejected() -> None:
    with pytest.raises(NonPositiveWealthError):
        equity_curve([0.1], initial_wealth=0.0)


def test_beginning_of_period_contributions_earn_that_period_return() -> None:
    curve = equity_curve_with_cash_flows(
        [0.10], [100.0], initial_wealth=1000.0, timing=CashFlowTiming.BEGINNING
    )
    assert float(curve[-1]) == pytest.approx(1100.0 * 1.10, rel=1e-14, abs=0.0)


def test_end_of_period_contributions_do_not_earn_that_period_return() -> None:
    curve = equity_curve_with_cash_flows(
        [0.10], [100.0], initial_wealth=1000.0, timing=CashFlowTiming.END
    )
    assert float(curve[-1]) == pytest.approx(1000.0 * 1.10 + 100.0, rel=1e-14, abs=0.0)


def test_the_two_timings_differ_by_the_flow_times_the_period_return() -> None:
    beginning = equity_curve_with_cash_flows(
        [0.10], [100.0], initial_wealth=1000.0, timing=CashFlowTiming.BEGINNING
    )
    end = equity_curve_with_cash_flows(
        [0.10], [100.0], initial_wealth=1000.0, timing=CashFlowTiming.END
    )
    assert float(beginning[-1]) - float(end[-1]) == pytest.approx(
        100.0 * 0.10, rel=1e-13, abs=0.0
    )


def test_a_withdrawal_larger_than_wealth_is_rejected() -> None:
    with pytest.raises(NonPositiveWealthError):
        equity_curve_with_cash_flows([0.0], [-1500.0], initial_wealth=1000.0)


def test_cash_flows_must_match_the_return_series_length() -> None:
    with pytest.raises(ValueError, match="same length as returns"):
        equity_curve_with_cash_flows([0.1, 0.2], [10.0])


def test_permuting_returns_leaves_terminal_wealth_unchanged_without_cash_flows() -> None:
    """Sequence risk is a cash-flow interaction, not a separate premium.

    docs/research/portfolio-edge-research-framework.md: "Without external cash flows,
    permuting returns leaves terminal wealth unchanged; contributions and withdrawals
    break that identity."
    """
    returns = [0.20, -0.15, 0.08, -0.03]
    reversed_returns = list(reversed(returns))
    assert terminal_wealth(returns) == pytest.approx(
        terminal_wealth(reversed_returns), rel=1e-14, abs=0.0
    )

    with_flows = equity_curve_with_cash_flows(returns, [100.0] * 4, initial_wealth=1000.0)
    reversed_with_flows = equity_curve_with_cash_flows(
        reversed_returns, [100.0] * 4, initial_wealth=1000.0
    )
    assert float(with_flows[-1]) != pytest.approx(
        float(reversed_with_flows[-1]), rel=1e-9, abs=0.0
    )
