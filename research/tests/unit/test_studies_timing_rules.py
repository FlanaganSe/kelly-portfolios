"""Tests for :mod:`portfolio_edge.studies.timing_rules`.

The three failure modes this file exists to catch are look-ahead in the signal, a cost
that is charged once when a whipsaw pays twice, and a tax simulation whose holding-period
boundary is off by one. Each has its own hand-computed fixture.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.timing_rules import (
    Disposal,
    RuleKind,
    TaxableAssumptions,
    TimingRuleSpec,
    episode_ledger,
    in_market,
    levels_from_returns,
    matched_exposure_active_returns,
    out_of_market_episodes,
    relative_drawdown,
    rule_excess_returns,
    rule_grid,
    sheltered_path,
    summarise,
    switch_count,
    taxable_path,
    time_in_market,
)

SMA_3 = TimingRuleSpec(kind=RuleKind.SMA, lookback=3)
MOM_3 = TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=3)


# --------------------------------------------------------------------------------------
# The specification
# --------------------------------------------------------------------------------------


def test_sma_rejects_a_degenerate_lookback() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        TimingRuleSpec(kind=RuleKind.SMA, lookback=1)


def test_absolute_momentum_admits_a_one_period_lookback() -> None:
    """Annual data cannot carry a ten-month average; a one-year lookback is the rule."""
    assert TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=1).burn_in == 2


def test_a_return_signal_costs_one_more_month_of_history_than_an_average() -> None:
    """A k-month return needs the close k months before the decision; an average does not.

    Without the extra month the first position is scored against ``levels[-1]`` through
    NumPy's negative indexing, which compares the start of the sample with its end.
    """
    assert TimingRuleSpec(kind=RuleKind.SMA, lookback=3).burn_in == 3
    assert TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=3).burn_in == 4
    levels = np.array([100.0, 90.0, 80.0, 101.0, 99.0], dtype=np.float64)
    assert np.isnan(in_market(levels, spec=MOM_3)[:4]).all()


def test_negative_execution_lag_is_rejected() -> None:
    with pytest.raises(ValueError, match="execution_lag"):
        TimingRuleSpec(kind=RuleKind.SMA, lookback=10, execution_lag=-1)


def test_burn_in_and_label() -> None:
    spec = TimingRuleSpec(kind=RuleKind.SMA, lookback=10, execution_lag=1)
    assert spec.burn_in == 11
    assert spec.label == "sma-10+1m"
    assert TimingRuleSpec(kind=RuleKind.SMA, lookback=10).label == "sma-10"


# --------------------------------------------------------------------------------------
# The signal, computed by hand
# --------------------------------------------------------------------------------------


def test_sma_signal_against_a_hand_computed_fixture() -> None:
    levels = np.array([100.0, 110.0, 90.0, 120.0, 80.0], dtype=np.float64)
    position = in_market(levels, spec=SMA_3)
    # burn-in is 3, so indices 0..2 are nan.
    assert np.isnan(position[:3]).all()
    # t = 3: decision at index 2, level 90 against mean(100, 110, 90) = 100 -> out.
    assert position[3] == 0.0
    # t = 4: decision at index 3, level 120 against mean(110, 90, 120) = 106.667 -> in.
    assert position[4] == 1.0


def test_absolute_momentum_against_a_benchmark() -> None:
    levels = np.array([100.0, 101.0, 102.0, 130.0, 104.0], dtype=np.float64)
    bills = np.array([100.0, 101.0, 102.0, 103.0, 104.0], dtype=np.float64)
    position = in_market(levels, spec=MOM_3, benchmark_levels=bills)
    assert np.isnan(position[:4]).all()
    # t = 4: decision at index 3, three months after index 0. 130/100 = 1.30 against the
    # bill's 103/100 = 1.03 -> in.
    assert position[4] == 1.0
    # The same months without the benchmark also read long, so the benchmark is what makes
    # the two rules differ rather than a coincidence of this fixture.
    higher = np.array([100.0, 101.0, 102.0, 103.5, 104.0], dtype=np.float64)
    assert in_market(higher, spec=MOM_3, benchmark_levels=bills)[4] == 1.0
    slower = np.array([100.0, 101.0, 102.0, 102.5, 104.0], dtype=np.float64)
    assert in_market(slower, spec=MOM_3, benchmark_levels=bills)[4] == 0.0


def test_absolute_momentum_without_a_benchmark_is_price_momentum() -> None:
    levels = np.array([100.0, 90.0, 80.0, 101.0, 99.0], dtype=np.float64)
    # t = 4: decision at index 3, three months after index 0: 101/100 = 1.01 > 1 -> in.
    assert in_market(levels, spec=MOM_3)[4] == 1.0
    falling = np.array([110.0, 90.0, 80.0, 101.0, 99.0], dtype=np.float64)
    # 101/110 = 0.918 < 1 -> out.
    assert in_market(falling, spec=MOM_3)[4] == 0.0


def test_a_moving_average_has_no_benchmark_form() -> None:
    levels = np.linspace(100.0, 120.0, 12)
    with pytest.raises(ValueError, match="no benchmark form"):
        in_market(levels, spec=SMA_3, benchmark_levels=levels)


def test_the_signal_cannot_see_the_return_it_earns() -> None:
    """Perturbing month t's level must not change the position held during month t."""
    rng = np.random.default_rng(11)
    levels = levels_from_returns(rng.normal(0.006, 0.04, 200))
    spec = TimingRuleSpec(kind=RuleKind.SMA, lookback=10)
    base = in_market(levels, spec=spec)
    for index in range(spec.burn_in, levels.size):
        perturbed = levels.copy()
        perturbed[index] *= 1.5
        assert in_market(perturbed, spec=spec)[index] == base[index], index


def test_execution_lag_shifts_the_position_by_exactly_one_month() -> None:
    rng = np.random.default_rng(3)
    levels = levels_from_returns(rng.normal(0.006, 0.04, 120))
    prompt = in_market(levels, spec=TimingRuleSpec(kind=RuleKind.SMA, lookback=10))
    delayed = in_market(
        levels, spec=TimingRuleSpec(kind=RuleKind.SMA, lookback=10, execution_lag=1)
    )
    assert np.array_equal(prompt[10:-1], delayed[11:])


def test_levels_from_returns_round_trips() -> None:
    returns = np.array([0.10, -0.05, 0.02], dtype=np.float64)
    levels = levels_from_returns(returns)
    assert levels == pytest.approx([1.10, 1.045, 1.0659])
    assert np.diff(levels) / levels[:-1] == pytest.approx(returns[1:])


def test_levels_reject_a_wipeout() -> None:
    with pytest.raises(ValueError, match="reached zero"):
        levels_from_returns(np.array([-1.0, 0.5]))


# --------------------------------------------------------------------------------------
# Costs, exposure and the matched control
# --------------------------------------------------------------------------------------


def test_a_whipsaw_pays_the_cost_twice() -> None:
    excess = np.zeros(5)
    position = np.array([1.0, 0.0, 1.0, 1.0, 1.0])
    returns = rule_excess_returns(excess, position=position, one_way_cost=0.001)
    assert returns[0] == pytest.approx(0.0)  # the initial entry is free
    assert returns[1] == pytest.approx(-0.001)
    assert returns[2] == pytest.approx(-0.001)
    assert returns[3] == pytest.approx(0.0)
    assert float(np.nansum(returns)) == pytest.approx(-0.002)


def test_a_constant_position_has_no_active_return() -> None:
    rng = np.random.default_rng(7)
    excess = rng.normal(0.006, 0.04, 60)
    position = np.full(60, 0.7)
    active = matched_exposure_active_returns(excess, position=position, one_way_cost=0.001)
    assert np.allclose(active, 0.0)


def test_the_matched_control_is_the_rule_less_its_own_beta() -> None:
    rng = np.random.default_rng(9)
    excess = rng.normal(0.006, 0.04, 240)
    levels = levels_from_returns(excess + 0.002)
    position = in_market(levels, spec=TimingRuleSpec(kind=RuleKind.SMA, lookback=10))
    rule = rule_excess_returns(excess, position=position, one_way_cost=0.001)
    active = matched_exposure_active_returns(excess, position=position, one_way_cost=0.001)
    live = np.isfinite(rule)
    weight = time_in_market(position)
    assert np.allclose(active[live], rule[live] - weight * excess[live])
    assert weight == pytest.approx(float(np.mean(position[live])))


def test_switch_count_counts_both_legs_of_a_round_trip() -> None:
    assert switch_count(np.array([np.nan, 1.0, 0.0, 0.0, 1.0])) == 2


def test_a_gap_inside_the_live_window_is_refused() -> None:
    with pytest.raises(ValueError, match="gap inside"):
        rule_excess_returns(
            np.zeros(4), position=np.array([1.0, np.nan, 1.0, 1.0]), one_way_cost=0.0
        )


# --------------------------------------------------------------------------------------
# Summary statistics
# --------------------------------------------------------------------------------------


def test_summarise_against_an_independently_computed_fixture() -> None:
    excess = np.array([0.10, -0.05])
    cash = np.array([0.01, 0.01])
    summary = summarise(excess, cash=cash, label="fixture")
    assert summary.months == 2
    assert summary.geometric_total == pytest.approx((1.11 * 0.96) ** 6 - 1.0)
    assert summary.volatility == pytest.approx(0.10606601717798212 * math.sqrt(12))
    assert summary.sharpe == pytest.approx(0.025 / 0.10606601717798212 * math.sqrt(12))
    assert summary.max_drawdown == pytest.approx(1.11 * 0.96 / 1.11 - 1.0)
    assert math.isnan(summary.worst_twelve_months)


def test_summarise_ignores_months_the_rule_had_not_formed() -> None:
    excess = np.array([np.nan, 0.10, -0.05])
    cash = np.array([0.01, 0.01, 0.01])
    assert summarise(excess, cash=cash, label="x").months == 2


# --------------------------------------------------------------------------------------
# Episodes and holdability
# --------------------------------------------------------------------------------------


def test_episodes_score_only_the_exits_and_charge_the_round_trip() -> None:
    excess = np.array([0.0, 0.10, -0.20, 0.0, 0.05])
    position = np.array([1.0, 0.0, 0.0, 1.0, 0.0])
    episodes = out_of_market_episodes(excess, position=position, one_way_cost=0.001)
    assert len(episodes) == 2
    first = episodes[0]
    assert (first.start, first.end, first.months) == (1, 2, 2)
    # Missed 1.10 * 0.80 - 1 = -0.12, so sitting out was worth +0.12 less the round trip.
    assert first.avoided == pytest.approx(0.12 - 0.002)
    assert first.helped
    second = episodes[1]
    assert second.avoided == pytest.approx(-0.05 - 0.002)
    assert not second.helped


def test_the_ledger_finds_the_worst_run_of_consecutive_losing_exits() -> None:
    excess = np.array([0.0, 0.05, 0.0, 0.05, 0.0, 0.05, 0.0, -0.50, 0.0])
    position = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0])
    episodes = out_of_market_episodes(excess, position=position, one_way_cost=0.0)
    ledger = episode_ledger(episodes)
    assert ledger.episodes == 4
    assert ledger.hurt == 3
    assert ledger.helped == 1
    assert ledger.worst_losing_run == 3
    assert ledger.worst_losing_run_cost == pytest.approx(-0.15)
    assert ledger.worst_losing_run_span == (1, 5)
    assert ledger.best_three_total + ledger.remainder_total == pytest.approx(
        ledger.total_avoided
    )


def test_a_rule_that_never_leaves_has_no_ledger() -> None:
    with pytest.raises(ValueError, match="never left"):
        episode_ledger(out_of_market_episodes(np.zeros(3), position=np.ones(3), one_way_cost=0.0))


def test_relative_drawdown_reports_where_the_advantage_peaked() -> None:
    cash = np.zeros(4)
    rule = np.array([0.50, 0.0, 0.0, 0.0])
    control = np.array([0.0, 0.20, 0.20, 0.0])
    result = relative_drawdown(rule, control_excess=control, cash=cash)
    ratio = np.cumprod((1.0 + rule) / (1.0 + control))
    assert result.peak_index == 0
    assert result.trough_index == 2
    assert result.max_shortfall == pytest.approx(ratio[2] / ratio[0] - 1.0)
    assert result.max_months_behind == 3
    assert result.open_at_end


# --------------------------------------------------------------------------------------
# The grid that makes deflation possible
# --------------------------------------------------------------------------------------


def test_the_rule_grid_is_declared_and_has_no_duplicates() -> None:
    grid = rule_grid()
    assert len(grid) == 46
    assert len({spec.label for spec in grid}) == 46
    assert TimingRuleSpec(kind=RuleKind.SMA, lookback=10) in grid
    assert TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=12) in grid


def test_the_rule_grid_can_be_narrowed_and_lagged() -> None:
    grid = rule_grid(lookbacks=(10, 12), execution_lag=1)
    assert [spec.label for spec in grid] == [
        "sma-10+1m",
        "sma-12+1m",
        "absolute_momentum-10+1m",
        "absolute_momentum-12+1m",
    ]


# --------------------------------------------------------------------------------------
# Tax, on the realised path
# --------------------------------------------------------------------------------------

TOP = TaxableAssumptions(ordinary_rate=0.408, long_term_rate=0.238, dividend_yield=0.0)


def test_a_short_term_exit_is_taxed_at_the_ordinary_rate() -> None:
    """Hand-computed: buy at 1, compound 1.10 and 1.10, sell at 1.21, gain 0.21."""
    outcome = taxable_path(
        label="fixture",
        position=np.array([1.0, 1.0, 0.0]),
        risky_total=np.array([0.10, 0.10, -0.50]),
        cash=np.zeros(3),
        assumptions=TaxableAssumptions(
            ordinary_rate=0.40, long_term_rate=0.20, dividend_yield=0.0
        ),
        one_way_cost=0.0,
    )
    assert outcome.realised_short_term_gain == pytest.approx(0.21)
    assert outcome.realised_long_term_gain == pytest.approx(0.0)
    assert outcome.cumulative_tax == pytest.approx(0.084)
    assert outcome.terminal_after_disposal == pytest.approx(1.126)
    assert outcome.annualised_after_tax_growth == pytest.approx(math.log(1.126) * 4.0)


def test_the_holding_period_boundary_is_more_than_twelve_months() -> None:
    """§1222: exactly twelve months is short-term; the thirteenth month is long-term."""
    for months, expect_long in ((12, False), (13, True)):
        position = np.concatenate([np.ones(months), np.zeros(1)])
        returns = np.concatenate([np.full(months, 0.01), np.zeros(1)])
        outcome = taxable_path(
            label=f"{months}",
            position=position,
            risky_total=returns,
            cash=np.zeros(months + 1),
            assumptions=TOP,
            one_way_cost=0.0,
        )
        assert (outcome.realised_long_term_gain > 0.0) is expect_long
        assert (outcome.realised_short_term_gain > 0.0) is not expect_long


def test_a_loss_carries_forward_against_a_later_gain() -> None:
    position = np.array([1.0, 0.0, 1.0, 0.0])
    returns = np.array([-0.50, 0.0, 1.00, 0.0])
    outcome = taxable_path(
        label="carryforward",
        position=position,
        risky_total=returns,
        cash=np.zeros(4),
        assumptions=TaxableAssumptions(
            ordinary_rate=0.40, long_term_rate=0.20, dividend_yield=0.0
        ),
        one_way_cost=0.0,
    )
    # Sells at 0.50 for a 0.50 loss, re-enters with 0.50, doubles to 1.00 for a 0.50 gain,
    # which the carried loss absorbs exactly. No tax is due on either leg.
    assert outcome.cumulative_tax == pytest.approx(0.0)
    assert outcome.terminal_after_disposal == pytest.approx(1.0)
    assert outcome.unused_loss_carryforward == pytest.approx(0.0)


def test_an_unused_loss_is_recorded_rather_than_credited() -> None:
    outcome = taxable_path(
        label="loss",
        position=np.array([1.0, 0.0]),
        risky_total=np.array([-0.50, 0.0]),
        cash=np.zeros(2),
        assumptions=TOP,
        one_way_cost=0.0,
    )
    assert outcome.unused_loss_carryforward == pytest.approx(0.50)
    assert outcome.cumulative_tax == pytest.approx(0.0)


def test_buy_and_hold_with_a_step_up_pays_no_tax_when_nothing_is_distributed() -> None:
    returns = np.array([0.10, -0.20, 0.30])
    outcome = taxable_path(
        label="hold",
        position=np.ones(3),
        risky_total=returns,
        cash=np.zeros(3),
        assumptions=TOP,
        one_way_cost=0.0,
        disposal=Disposal.STEP_UP,
    )
    assert outcome.cumulative_tax == pytest.approx(0.0)
    assert outcome.terminal_after_disposal == pytest.approx(float(np.prod(1.0 + returns)))


def test_liquidation_taxes_the_whole_standing_gain() -> None:
    returns = np.array([0.10, 0.10])
    outcome = taxable_path(
        label="hold",
        position=np.ones(2),
        risky_total=returns,
        cash=np.zeros(2),
        assumptions=TaxableAssumptions(
            ordinary_rate=0.40, long_term_rate=0.20, dividend_yield=0.0
        ),
        one_way_cost=0.0,
        disposal=Disposal.LIQUIDATE,
    )
    # Two months is short-term, so the terminal levy is the ordinary rate.
    assert outcome.cumulative_tax == pytest.approx(0.40 * 0.21)
    assert outcome.terminal_after_disposal == pytest.approx(1.21 - 0.40 * 0.21)


def test_a_dividend_is_taxed_and_raises_basis_so_a_step_up_still_pays_nothing_more() -> None:
    assumptions = TaxableAssumptions(
        ordinary_rate=0.40, long_term_rate=0.20, dividend_yield=0.12
    )
    outcome = taxable_path(
        label="dividend",
        position=np.ones(1),
        risky_total=np.array([0.0]),
        cash=np.zeros(1),
        assumptions=assumptions,
        one_way_cost=0.0,
        disposal=Disposal.STEP_UP,
    )
    # A 12% annual yield is 1% for the month, taxed at 20%: 0.002 of wealth.
    assert outcome.cumulative_tax == pytest.approx(0.002)
    assert outcome.terminal_after_disposal == pytest.approx(0.998)


def test_cash_interest_is_taxed_at_the_ordinary_rate() -> None:
    outcome = taxable_path(
        label="bills",
        position=np.zeros(2),
        risky_total=np.zeros(2),
        cash=np.array([0.01, 0.01]),
        assumptions=TOP,
        one_way_cost=0.0,
    )
    net = 1.0 * (1.0 + 0.01 * (1.0 - 0.408)) ** 2
    assert outcome.terminal_after_disposal == pytest.approx(net)


def test_a_never_rebalanced_blend_does_not_trade_after_entry() -> None:
    position = np.full(24, 0.6)
    rng = np.random.default_rng(5)
    returns = rng.normal(0.008, 0.04, 24)
    banded = taxable_path(
        label="band",
        position=position,
        risky_total=returns,
        cash=np.full(24, 0.002),
        assumptions=TOP,
        one_way_cost=0.01,
        rebalance_band=1.0,
        disposal=Disposal.STEP_UP,
    )
    rebalanced = taxable_path(
        label="monthly",
        position=position,
        risky_total=returns,
        cash=np.full(24, 0.002),
        assumptions=TOP,
        one_way_cost=0.01,
        rebalance_band=0.0,
        disposal=Disposal.STEP_UP,
    )
    assert banded.turnover_cost_paid == pytest.approx(0.6 * 0.01)
    assert banded.realised_long_term_gain == pytest.approx(0.0)
    assert banded.realised_short_term_gain == pytest.approx(0.0)
    assert rebalanced.turnover_cost_paid > banded.turnover_cost_paid


def test_the_sheltered_path_is_the_pretax_path() -> None:
    rng = np.random.default_rng(2)
    returns = rng.normal(0.008, 0.04, 60)
    cash = np.full(60, 0.002)
    levels = levels_from_returns(returns)
    position = in_market(levels, spec=TimingRuleSpec(kind=RuleKind.SMA, lookback=10))
    outcome = sheltered_path(
        label="roth", position=position, risky_total=returns, cash=cash, one_way_cost=0.0
    )
    live = np.isfinite(position)
    expected = float(
        np.prod(1.0 + position[live] * returns[live] + (1.0 - position[live]) * cash[live])
    )
    assert outcome.cumulative_tax == pytest.approx(0.0)
    assert outcome.terminal_after_disposal == pytest.approx(expected)


def test_a_position_outside_the_unit_interval_is_refused() -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        taxable_path(
            label="levered",
            position=np.array([1.5, 1.5]),
            risky_total=np.zeros(2),
            cash=np.zeros(2),
            assumptions=TOP,
            one_way_cost=0.0,
        )


def test_a_long_term_rate_above_the_ordinary_rate_is_refused() -> None:
    with pytest.raises(ValueError, match="inverts"):
        TaxableAssumptions(ordinary_rate=0.10, long_term_rate=0.20, dividend_yield=0.0)
