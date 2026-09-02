"""Tests for :mod:`portfolio_edge.studies.global_split_regret`.

The load-bearing checks do not reuse the implementation's algebra: the return identity is
worked with literal numbers, the regret table is rebuilt by hand for two splits and two
scenarios, the minimax split is checked against a brute-force scan, and the closed-form
minimum-variance split is checked against a numerical minimum. The rest is contracts,
units and numerical edges.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.global_split_regret import (
    CURRENCY_LEGS,
    EQUAL_PRIOR,
    GROWTH_DIFFERENTIALS,
    RERATING_STATES,
    REVERSION_PRIOR,
    SPLITS,
    Reading,
    Readings,
    RelativeMoments,
    ReratingPrior,
    Scenario,
    bayes_split_sweep,
    expected_differential,
    growth_optimal_split,
    implied_differential,
    regret_table,
    reversion_sweep_prior,
    scenario_grid,
    sleeve_log_growth,
    tracking_error,
    years_to_reach,
)


def _reading(value: float) -> Reading:
    return Reading(value=value, as_of="fixture", source="fixture")


READINGS = Readings(
    us_dividend_yield=_reading(0.01088),
    ex_us_dividend_yield=_reading(0.0250),
    relative_cape=_reading(1.704),
    long_run_log_median=_reading(-0.015),
    log_spread_sd=_reading(0.317),
    cap_weight_us=_reading(0.64),
)

MOMENTS = RelativeMoments(
    us_volatility=0.15,
    ex_us_volatility=0.16,
    correlation=0.75,
    first_month="1990-07",
    last_month="2026-06",
    months=432,
)


# --------------------------------------------------------------------------------
# The identity
# --------------------------------------------------------------------------------


def test_identity_matches_an_independently_computed_fixture() -> None:
    """``(y_US - y_X) + g + delta / T - c`` with every term written out by hand.

    Half reversion at ten years, a +1 pp growth edge and a currency leg of -1 pp:
    log(1.704) = 0.532978; gap to the median -0.015 - 0.532978 = -0.547978; half of it
    over ten years is -0.0273989 a year; yields -0.01412; so d = -0.01412 + 0.01
    - 0.0273989 + 0.01 = -0.0215189.
    """
    scenario = Scenario(rerating="half", growth_differential=0.01, currency_leg=-0.01)
    assert implied_differential(READINGS, scenario, horizon_years=10) == pytest.approx(
        -0.0215189, abs=1e-7
    )


def test_identity_terms_enter_with_the_stated_signs() -> None:
    hold = Scenario(rerating="hold", growth_differential=0.0, currency_leg=0.0)
    base = implied_differential(READINGS, hold, horizon_years=10)
    assert base == pytest.approx(0.01088 - 0.0250)
    growth = Scenario(rerating="hold", growth_differential=0.01, currency_leg=0.0)
    assert implied_differential(READINGS, growth, horizon_years=10) == pytest.approx(base + 0.01)
    currency = Scenario(rerating="hold", growth_differential=0.0, currency_leg=0.01)
    assert implied_differential(READINGS, currency, horizon_years=10) == pytest.approx(
        base - 0.01
    )
    further = Scenario(rerating="further", growth_differential=0.0, currency_leg=0.0)
    assert implied_differential(READINGS, further, horizon_years=10) == pytest.approx(
        base + 0.317 / 10
    )


def test_rerating_spreads_over_the_horizon() -> None:
    full = Scenario(rerating="full", growth_differential=0.0, currency_leg=0.0)
    ten = implied_differential(READINGS, full, horizon_years=10) - READINGS.yield_differential
    thirty = implied_differential(READINGS, full, horizon_years=30) - READINGS.yield_differential
    assert ten == pytest.approx(3.0 * thirty)
    assert READINGS.rerating_log_change("full") == pytest.approx(
        2.0 * READINGS.rerating_log_change("half")
    )


def test_identity_rejects_a_non_positive_horizon() -> None:
    scenario = Scenario(rerating="hold", growth_differential=0.0, currency_leg=0.0)
    with pytest.raises(ValueError):
        implied_differential(READINGS, scenario, horizon_years=0.0)


def test_readings_reject_impossible_inputs() -> None:
    with pytest.raises(ValueError):
        Readings(
            us_dividend_yield=_reading(0.01),
            ex_us_dividend_yield=_reading(0.02),
            relative_cape=_reading(0.0),
            long_run_log_median=_reading(0.0),
            log_spread_sd=_reading(0.3),
            cap_weight_us=_reading(0.64),
        )
    with pytest.raises(ValueError):
        Readings(
            us_dividend_yield=_reading(0.01),
            ex_us_dividend_yield=_reading(0.02),
            relative_cape=_reading(1.5),
            long_run_log_median=_reading(0.0),
            log_spread_sd=_reading(0.3),
            cap_weight_us=_reading(1.0),
        )


def test_scenario_grid_is_the_full_predeclared_product() -> None:
    grid = scenario_grid()
    assert len(grid) == len(RERATING_STATES) * len(GROWTH_DIFFERENTIALS) * len(CURRENCY_LEGS)
    assert len(set(grid)) == len(grid)
    assert grid[0].rerating == "hold"
    assert grid[-1].rerating == "further"


# --------------------------------------------------------------------------------
# Growth, variance and tracking error
# --------------------------------------------------------------------------------


def test_minimum_variance_split_matches_a_numerical_minimum() -> None:
    fine = np.linspace(0.0, 1.0, 100_001)
    variances = [MOMENTS.sleeve_variance(float(s)) for s in fine]
    numerical = float(fine[int(np.argmin(variances))])
    assert MOMENTS.minimum_variance_split == pytest.approx(numerical, abs=1e-4)
    # The closed form, by hand: (0.16**2 - 0.75 * 0.15 * 0.16) / (0.15**2 + 0.16**2 - 2 * 0.018).
    assert MOMENTS.minimum_variance_split == pytest.approx((0.0256 - 0.018) / 0.0121)


def test_tracking_error_is_zero_at_cap_weight_and_linear_away_from_it() -> None:
    assert tracking_error(0.64, MOMENTS, cap_weight_us=0.64) == 0.0
    ten_points = tracking_error(0.54, MOMENTS, cap_weight_us=0.64)
    assert ten_points == pytest.approx(0.10 * math.sqrt(0.0121))
    assert tracking_error(0.74, MOMENTS, cap_weight_us=0.64) == pytest.approx(ten_points)
    assert tracking_error(0.44, MOMENTS, cap_weight_us=0.64) == pytest.approx(2.0 * ten_points)


def test_growth_optimal_split_has_the_stated_slope() -> None:
    at_zero = growth_optimal_split(0.0, MOMENTS)
    assert at_zero == pytest.approx(MOMENTS.minimum_variance_split)
    assert growth_optimal_split(0.01, MOMENTS) - at_zero == pytest.approx(0.01 / 0.0121)


def test_sleeve_log_growth_rejects_a_split_outside_the_unit_interval() -> None:
    with pytest.raises(ValueError):
        sleeve_log_growth(1.2, 0.0, MOMENTS)


# --------------------------------------------------------------------------------
# The regret table
# --------------------------------------------------------------------------------


def test_regret_table_matches_an_independently_computed_fixture() -> None:
    """Two splits, two scenarios, ten years, every number worked by hand.

    var(0.8) = 0.64 * 0.0225 + 0.04 * 0.0256 + 2 * 0.8 * 0.2 * 0.018 = 0.021184
    var(0.4) = 0.16 * 0.0225 + 0.36 * 0.0256 + 2 * 0.4 * 0.6 * 0.018 = 0.021456
    d = +0.02: g(0.8) = 0.016 - 0.010592 = 0.005408; g(0.4) = 0.008 - 0.010728 = -0.002728
    d = -0.03: g(0.8) = -0.024 - 0.010592 = -0.034592; g(0.4) = -0.012 - 0.010728 = -0.022728
    regret(0.4 | +0.02) = 10 * (0.005408 + 0.002728) = 0.08136
    regret(0.8 | -0.03) = 10 * (0.034592 - 0.022728) = 0.11864
    """
    readings = Readings(
        us_dividend_yield=_reading(0.02),
        ex_us_dividend_yield=_reading(0.0),
        relative_cape=_reading(1.0),
        long_run_log_median=_reading(-0.5),
        log_spread_sd=_reading(0.0),
        cap_weight_us=_reading(0.64),
    )
    up = Scenario(rerating="hold", growth_differential=0.0, currency_leg=0.0)  # d = +0.02
    down = Scenario(rerating="full", growth_differential=0.0, currency_leg=0.0)  # d = -0.03
    table = regret_table(
        readings, MOMENTS, horizon_years=10, splits=(0.8, 0.4), scenarios=(up, down)
    )
    assert table.differentials == pytest.approx((0.02, -0.03))
    assert table.regret_at(0.4, up) == pytest.approx(0.08136, abs=1e-9)
    assert table.regret_at(0.8, up) == 0.0
    assert table.regret_at(0.8, down) == pytest.approx(0.11864, abs=1e-9)
    assert table.regret_at(0.4, down) == 0.0
    assert table.best_split == (0.8, 0.4)
    assert table.max_regret == pytest.approx((0.11864, 0.08136), abs=1e-9)
    assert table.minimax_split == 0.4
    assert table.minimax_regret == pytest.approx(0.08136, abs=1e-9)
    assert table.tracking_error == pytest.approx(
        (0.16 * math.sqrt(0.0121), 0.24 * math.sqrt(0.0121))
    )


def test_regret_is_non_negative_and_zero_at_the_best_split() -> None:
    table = regret_table(READINGS, MOMENTS, horizon_years=10)
    for j, scenario in enumerate(table.scenarios):
        column = [table.regret[i][j] for i in range(len(table.splits))]
        assert min(column) == 0.0
        assert table.regret_at(table.best_split[j], scenario) == 0.0


def test_minimax_split_agrees_with_a_brute_force_scan() -> None:
    table = regret_table(READINGS, MOMENTS, horizon_years=30)
    brute = min(table.splits, key=lambda s: max(table.regret[table.row(s)]))
    assert table.minimax_split == brute
    assert table.minimax_regret == pytest.approx(max(table.regret[table.row(brute)]))


def test_regret_scales_with_the_horizon_when_the_rerating_is_held_fixed_per_year() -> None:
    """With no re-rating the differential is horizon-free, so regret is linear in T."""
    hold = tuple(s for s in scenario_grid() if s.rerating == "hold")
    ten = regret_table(READINGS, MOMENTS, horizon_years=10, scenarios=hold)
    thirty = regret_table(READINGS, MOMENTS, horizon_years=30, scenarios=hold)
    assert np.asarray(thirty.regret) == pytest.approx(3.0 * np.asarray(ten.regret))


def test_regret_table_rejects_bad_grids() -> None:
    with pytest.raises(ValueError):
        regret_table(READINGS, MOMENTS, horizon_years=10, splits=())
    with pytest.raises(ValueError):
        regret_table(READINGS, MOMENTS, horizon_years=10, splits=(0.6, 0.6))
    with pytest.raises(ValueError):
        regret_table(READINGS, MOMENTS, horizon_years=10, scenarios=())


# --------------------------------------------------------------------------------
# Priors
# --------------------------------------------------------------------------------


def test_priors_sum_to_one_and_spread_evenly_within_a_state() -> None:
    grid = scenario_grid()
    for prior in (EQUAL_PRIOR, REVERSION_PRIOR, reversion_sweep_prior(0.3)):
        weights = prior.scenario_weights(grid)
        assert sum(weights) == pytest.approx(1.0)
        hold = [w for w, s in zip(weights, grid, strict=True) if s.rerating == "hold"]
        assert hold == pytest.approx([prior.weights["hold"] / 9] * 9)
    assert reversion_sweep_prior(0.3).reversion_weight == pytest.approx(0.3)
    assert REVERSION_PRIOR.reversion_weight == pytest.approx(0.70)


def test_prior_contracts() -> None:
    with pytest.raises(ValueError):
        ReratingPrior(label="short", weights={"hold": 1.0})
    with pytest.raises(ValueError):
        ReratingPrior(
            label="over", weights={"hold": 0.5, "half": 0.5, "full": 0.5, "further": 0.0}
        )
    with pytest.raises(ValueError):
        reversion_sweep_prior(1.5)


def test_expected_differential_is_the_prior_weighted_mean() -> None:
    grid = scenario_grid()
    weights = EQUAL_PRIOR.scenario_weights(grid)
    by_hand = sum(
        w * implied_differential(READINGS, s, horizon_years=10)
        for w, s in zip(weights, grid, strict=True)
    )
    assert expected_differential(READINGS, EQUAL_PRIOR, horizon_years=10) == pytest.approx(by_hand)


def test_bayes_split_minimises_expected_regret_and_the_sweep_is_monotone() -> None:
    table = regret_table(READINGS, MOMENTS, horizon_years=10)
    expected = table.expected_regret(EQUAL_PRIOR)
    assert table.bayes_split(EQUAL_PRIOR) == table.splits[int(np.argmin(expected))]
    points = bayes_split_sweep(table, READINGS, MOMENTS, reversion_weights=(0.0, 0.5, 1.0))
    differentials = [p.expected_differential for p in points]
    assert differentials == sorted(differentials, reverse=True)
    unconstrained = [p.unconstrained_split for p in points]
    assert unconstrained == sorted(unconstrained, reverse=True)
    assert all(p.bayes_split in SPLITS for p in points)


# --------------------------------------------------------------------------------
# Contributions
# --------------------------------------------------------------------------------


def test_years_to_reach_matches_hand_arithmetic() -> None:
    # 64/36 to 60/40 at 10%: k = (0.40 - 0.36) / 0.60 = 0.0667 of the balance.
    assert years_to_reach(
        current_us_share=0.64, target_us_share=0.60, contribution_rate=0.10
    ) == pytest.approx(2.0 / 3.0)
    # To 50/50: k = 0.14 / 0.5 = 0.28; 2.8 years at 10%, 5.6 at 5%, 4.0 with 70% of it.
    assert years_to_reach(
        current_us_share=0.64, target_us_share=0.50, contribution_rate=0.10
    ) == pytest.approx(2.8)
    assert years_to_reach(
        current_us_share=0.64, target_us_share=0.50, contribution_rate=0.05
    ) == pytest.approx(5.6)
    assert years_to_reach(
        current_us_share=0.64,
        target_us_share=0.50,
        contribution_rate=0.10,
        share_of_contributions=0.7,
    ) == pytest.approx(4.0)
    # Upward, to 70/30: US is the under-weight side; k = 0.06 / 0.30 = 0.2.
    assert years_to_reach(
        current_us_share=0.64, target_us_share=0.70, contribution_rate=0.10
    ) == pytest.approx(2.0)
    assert years_to_reach(current_us_share=0.64, target_us_share=0.64, contribution_rate=0.1) == 0.0


def test_years_to_reach_lands_exactly_on_the_target() -> None:
    years = years_to_reach(current_us_share=0.64, target_us_share=0.55, contribution_rate=0.10)
    added = 0.10 * years
    assert 0.64 / (1.0 + added) == pytest.approx(0.55)


def test_years_to_reach_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        years_to_reach(current_us_share=0.0, target_us_share=0.5, contribution_rate=0.1)
    with pytest.raises(ValueError):
        years_to_reach(current_us_share=0.6, target_us_share=0.5, contribution_rate=0.0)
