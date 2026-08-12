"""Unit tests for the statistics Experiment 004 adds.

Every expected value here is computed in this file, from first principles, never
by calling the function under test. Where a textbook figure exists — the modified
duration and convexity of a ten-year par bond — it is asserted directly.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from portfolio_edge.data import aqr
from portfolio_edge.experiments.exp_004_trend_marginal_value import (
    COMPARISON_IDS,
    ENTRY_POINT,
    Scenario,
    TrendMarginalValueError,
    _annual_gross_matrix,
    _attribute,
    _certainty_equivalent_rows,
    _crisis_union_mask,
    _mask_for,
    _run_weights,
    _share_lost,
    _whole_year_mask,
    bond_total_return_from_yield,
    build_registry,
    certainty_equivalent_annual,
    default_specification_path,
    ewma_annualised_covariance,
    ewma_annualised_volatility,
    expanding_annualised_volatility,
    high_water_mark_performance_fee,
    par_bond_risk,
)
from portfolio_edge.experiments.specification import JsonValue, load_specification

# --------------------------------------------------------------------------- #
# Certainty equivalent
# --------------------------------------------------------------------------- #


def test_certainty_equivalent_matches_an_independently_computed_value() -> None:
    """CRRA at gamma=3 inverts to ``(mean(G**-2))**(-1/2) - 1``."""
    gross = np.array([1.10, 0.90])
    expected = (0.5 * (1.10**-2 + 0.90**-2)) ** (-0.5) - 1.0
    assert certainty_equivalent_annual(gross, gamma=3.0) == pytest.approx(expected, rel=1e-12)
    # Risk aversion costs something: the certainty equivalent sits below both the
    # arithmetic mean and, at gamma > 1, the geometric mean.
    assert expected < math.sqrt(1.10 * 0.90) - 1.0 < 0.0


def test_certainty_equivalent_at_gamma_one_is_the_geometric_mean() -> None:
    gross = np.array([1.2, 0.9, 1.05])
    expected = (1.2 * 0.9 * 1.05) ** (1.0 / 3.0) - 1.0
    assert certainty_equivalent_annual(gross, gamma=1.0) == pytest.approx(expected, rel=1e-12)


def test_a_constant_path_has_a_certainty_equivalent_equal_to_its_return() -> None:
    gross = np.full(10, 1.07)
    assert certainty_equivalent_annual(gross, gamma=3.0) == pytest.approx(0.07, rel=1e-12)


def test_certainty_equivalent_refuses_insolvency_rather_than_returning_a_number() -> None:
    with pytest.raises(ValueError, match="insolvency"):
        certainty_equivalent_annual(np.array([1.1, 0.0]), gamma=3.0)


def test_certainty_equivalent_falls_as_risk_aversion_rises() -> None:
    gross = np.array([1.3, 0.8, 1.1, 0.95])
    values = [certainty_equivalent_annual(gross, gamma=g) for g in (1.0, 3.0, 5.0)]
    assert values[0] > values[1] > values[2]


def test_annual_blocks_compound_and_reject_a_partial_year() -> None:
    monthly = np.full(24, 0.01)
    annual = _annual_gross_matrix(monthly)
    assert annual.shape == (2,)
    assert annual[0] == pytest.approx(1.01**12, rel=1e-12)
    with pytest.raises(ValueError, match="whole number of 12-month blocks"):
        _annual_gross_matrix(np.full(13, 0.01))


def test_the_vectorised_certainty_equivalent_matches_the_scalar_one() -> None:
    rng = np.random.default_rng(7)
    panel = rng.normal(0.006, 0.03, size=(5, 36 * 12))
    rows = _certainty_equivalent_rows(panel, gamma=3.0)
    for index in range(panel.shape[0]):
        expected = certainty_equivalent_annual(
            _annual_gross_matrix(panel[index]), gamma=3.0
        )
        assert rows[index] == pytest.approx(expected, rel=1e-12)


# --------------------------------------------------------------------------- #
# The volatility estimator
# --------------------------------------------------------------------------- #


def test_ewma_volatility_matches_a_hand_computed_recursion() -> None:
    """Centre of mass 2 months gives ``delta = 2/3``; three steps by hand."""
    returns = np.array([0.01, -0.02, 0.03, 0.05])
    out = ewma_annualised_volatility(
        returns, centre_of_mass_months=2.0, minimum_observations=1
    )
    assert math.isnan(out[0])
    # After one observation the weighted variance is exactly zero.
    assert out[1] == pytest.approx(0.0, abs=1e-15)
    # After two: m = (1/3)(-0.02) + (2/3)(0.01) = 0; s = (1/3)(4e-4) + (2/3)(1e-4) = 2e-4.
    assert out[2] == pytest.approx(math.sqrt(2e-4 * 12.0), rel=1e-12)


def test_ewma_volatility_is_strictly_lagged() -> None:
    """The estimate at ``t`` may not move when the return at ``t`` changes."""
    returns = np.array([0.01, -0.02, 0.03, 0.05, -0.04, 0.02, 0.01, -0.01])
    baseline = ewma_annualised_volatility(
        returns, centre_of_mass_months=3.0, minimum_observations=2
    )
    tampered = returns.copy()
    tampered[5] = 0.99
    after = ewma_annualised_volatility(
        tampered, centre_of_mass_months=3.0, minimum_observations=2
    )
    np.testing.assert_allclose(baseline[:6], after[:6])
    assert after[6] != pytest.approx(baseline[6])


def test_ewma_volatility_is_missing_before_the_minimum_sample() -> None:
    returns = np.linspace(-0.02, 0.02, 30)
    out = ewma_annualised_volatility(returns, centre_of_mass_months=3.0, minimum_observations=24)
    assert np.all(np.isnan(out[:24]))
    assert np.all(np.isfinite(out[24:]))


def test_ewma_covariance_of_a_series_with_itself_is_its_variance() -> None:
    rng = np.random.default_rng(11)
    series = rng.normal(0.0, 0.04, size=60)
    volatility = ewma_annualised_volatility(series, centre_of_mass_months=2.857)
    covariance = ewma_annualised_covariance(series, series, centre_of_mass_months=2.857)
    np.testing.assert_allclose(covariance[30:], volatility[30:] ** 2, rtol=1e-10)


def test_ewma_covariance_of_independent_series_is_near_zero() -> None:
    rng = np.random.default_rng(13)
    left = rng.normal(0.0, 0.04, size=400)
    right = rng.normal(0.0, 0.04, size=400)
    covariance = ewma_annualised_covariance(left, right, centre_of_mass_months=12.0)
    assert abs(float(np.mean(covariance[100:]))) < 0.02


def test_expanding_volatility_uses_only_the_strict_prefix() -> None:
    rng = np.random.default_rng(3)
    series = rng.normal(0.005, 0.04, size=50)
    out = expanding_annualised_volatility(series, minimum_observations=24)
    assert math.isnan(out[23])
    for index in (24, 30, 49):
        expected = float(np.std(series[:index], ddof=1)) * math.sqrt(12.0)
        assert out[index] == pytest.approx(expected, rel=1e-12)


# --------------------------------------------------------------------------- #
# Fees
# --------------------------------------------------------------------------- #


def test_the_performance_fee_is_ten_percent_of_a_gain() -> None:
    net, total = high_water_mark_performance_fee(np.array([0.10]), rate=0.10)
    assert net[0] == pytest.approx(0.09, rel=1e-12)
    assert total == pytest.approx(0.01, rel=1e-12)


def test_recovering_ground_is_not_charged_twice() -> None:
    """The high-water mark is the whole point: a rebound to below the peak is free."""
    net, total = high_water_mark_performance_fee(
        np.array([0.10, -0.05, 0.05]), rate=0.10
    )
    assert net[0] == pytest.approx(0.09, rel=1e-12)
    assert net[1] == pytest.approx(-0.05, rel=1e-12)
    assert net[2] == pytest.approx(0.05, rel=1e-12)
    assert total == pytest.approx(0.01, rel=1e-12)


def test_a_performance_fee_never_increases_wealth() -> None:
    rng = np.random.default_rng(5)
    returns = rng.normal(0.004, 0.03, size=200)
    net, total = high_water_mark_performance_fee(returns, rate=0.20)
    assert total >= 0.0
    assert float(np.prod(1.0 + net)) <= float(np.prod(1.0 + returns)) + 1e-12
    assert np.all(net <= returns + 1e-15)


def test_a_zero_rate_charges_nothing() -> None:
    returns = np.array([0.1, -0.2, 0.3])
    net, total = high_water_mark_performance_fee(returns, rate=0.0)
    np.testing.assert_allclose(net, returns)
    assert total == 0.0


# --------------------------------------------------------------------------- #
# The modelled bond leg
# --------------------------------------------------------------------------- #


def test_par_bond_risk_matches_the_textbook_ten_year_figures() -> None:
    modified, convexity = par_bond_risk(0.04, periods=20)
    assert modified == pytest.approx(8.1757, abs=5e-4)
    assert convexity == pytest.approx(39.4490, abs=5e-3)


def test_a_flat_yield_earns_only_its_coupon() -> None:
    out = bond_total_return_from_yield(np.array([0.04, 0.04, 0.04]))
    assert math.isnan(out[0])
    assert out[1] == pytest.approx(0.04 / 12.0, rel=1e-12)
    assert out[2] == pytest.approx(0.04 / 12.0, rel=1e-12)


def test_a_rising_yield_loses_roughly_duration_times_the_change() -> None:
    out = bond_total_return_from_yield(np.array([0.04, 0.05]))
    price_change = float(out[1]) - 0.04 / 12.0
    implied_duration = -price_change / 0.01
    assert 7.5 < implied_duration < 8.5


def test_the_duration_approximation_is_close_to_an_exact_repricing() -> None:
    """A 100 bp shock is the largest this series sees; bound the error there."""

    def price(annual_yield: float, periods: int, coupon: float) -> float:
        rate = annual_yield / 2.0
        return sum(
            coupon / 2.0 / (1.0 + rate) ** period for period in range(1, periods + 1)
        ) + (1.0 + rate) ** -periods

    exact = price(0.05, 20, 0.04) - 1.0
    approximate = float(bond_total_return_from_yield(np.array([0.04, 0.05]))[1]) - 0.04 / 12.0
    assert abs(approximate - exact) < 0.002


def test_a_non_positive_yield_is_left_missing_rather_than_invented() -> None:
    out = bond_total_return_from_yield(np.array([0.0, 0.01, 0.02]))
    assert math.isnan(out[1])
    assert math.isfinite(out[2])


# --------------------------------------------------------------------------- #
# Weight paths and costs
# --------------------------------------------------------------------------- #


def test_a_constant_weight_path_reproduces_the_weighted_return() -> None:
    weights = np.tile(np.array([0.6, 0.4, 0.0]), (3, 1))
    returns = np.array([[0.02, 0.001, 0.0], [-0.01, 0.001, 0.0], [0.03, 0.001, 0.0]])
    portfolio, turnover, cost = _run_weights(weights, returns, one_way_bps=0.0)
    for index in range(3):
        assert portfolio[index] == pytest.approx(
            0.6 * returns[index, 0] + 0.4 * returns[index, 1]
        )
    assert cost.sum() == 0.0
    # The first month has no trade; later ones pay for correcting drift.
    assert turnover[0] == 0.0
    assert turnover[1] > 0.0


def test_a_path_that_never_drifts_never_trades() -> None:
    weights = np.tile(np.array([0.5, 0.5, 0.0]), (4, 1))
    returns = np.tile(np.array([0.01, 0.01, 0.01]), (4, 1))
    _, turnover, cost = _run_weights(weights, returns, one_way_bps=8.0)
    assert float(np.max(turnover)) == pytest.approx(0.0, abs=1e-15)
    assert float(np.max(cost)) == pytest.approx(0.0, abs=1e-15)


def test_costs_never_increase_wealth() -> None:
    rng = np.random.default_rng(19)
    weights = np.tile(np.array([0.6, 0.4, 0.0]), (60, 1))
    returns = np.column_stack(
        [rng.normal(0.006, 0.04, 60), np.full(60, 0.002), np.zeros(60)]
    )
    free, _, _ = _run_weights(weights, returns, one_way_bps=0.0)
    charged, _, cost = _run_weights(weights, returns, one_way_bps=8.0)
    assert float(np.prod(1.0 + charged)) < float(np.prod(1.0 + free))
    assert np.all(cost >= 0.0)
    np.testing.assert_allclose(charged, free - cost)


def test_the_cost_is_proportional_to_the_traded_notional() -> None:
    weights = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    returns = np.zeros((2, 3))
    _, turnover, cost = _run_weights(weights, returns, one_way_bps=10.0)
    # A complete switch trades 2.0 of notional, which is 1.0 of one-sided turnover.
    assert turnover[1] == pytest.approx(1.0)
    assert cost[1] == pytest.approx(2.0 * 10.0 / 1e4)


# --------------------------------------------------------------------------- #
# Windows
# --------------------------------------------------------------------------- #


def test_a_window_mask_selects_its_own_months_inclusively() -> None:
    periods = ("1999-11", "1999-12", "2000-01", "2000-02", "2000-03")
    mask = _mask_for(periods, "1999-12", "2000-02")
    assert list(mask) == [False, True, True, True, False]


def test_a_whole_year_mask_refuses_a_window_that_is_not_whole_years() -> None:
    """Chopping a partial year would silently drop months from the CE."""
    periods = (*(f"2001-{month:02d}" for month in range(1, 13)), "2002-01")
    assert int(_whole_year_mask(periods, "2001-01", "2001-12").sum()) == 12
    assert int(_whole_year_mask(periods, "2001-03", "2002-01").sum()) == 0


def test_the_crisis_union_is_the_union_of_the_frozen_windows() -> None:
    periods = tuple(f"2000-{month:02d}" for month in range(1, 13))
    windows = (("a", "2000-02", "2000-03"), ("b", "2000-09", "2000-10"))
    mask = _crisis_union_mask(periods, windows)
    assert [periods[i] for i in np.flatnonzero(mask)] == [
        "2000-02",
        "2000-03",
        "2000-09",
        "2000-10",
    ]


def test_share_lost_is_none_when_the_baseline_is_zero() -> None:
    assert _share_lost(0.0, 0.5) is None
    assert _share_lost(1.0, 0.4) == pytest.approx(0.6)
    # A stress that makes an already-negative baseline worse loses a positive share.
    assert _share_lost(-1.0, -2.0) == pytest.approx(1.0)
    # A stress that improves the result loses a negative share, and is reported, not hidden.
    assert _share_lost(1.0, 1.5) == pytest.approx(-0.5)


# --------------------------------------------------------------------------- #
# Attribution
# --------------------------------------------------------------------------- #


def test_a_sleeve_that_is_exactly_a_static_market_position_is_attributed_to_one() -> None:
    """If a static exposure IS the sleeve, the attribution must say so exactly."""
    rng = np.random.default_rng(23)
    equity = rng.normal(0.006, 0.04, size=300)
    exposure = np.clip(1.0 + 0.5 * rng.normal(size=300), 0.2, 2.0)
    scaled = exposure * equity
    sleeve = 0.7 * equity
    attribution = _attribute(sleeve, equity_excess=equity, scaled_equity_excess=scaled)
    assert attribution.r_squared == pytest.approx(1.0, abs=1e-8)
    assert attribution.annualised_alpha_percent == pytest.approx(0.0, abs=1e-8)
    assert attribution.coefficients[1] == pytest.approx(0.7, abs=1e-8)
    assert attribution.coefficients[2] == pytest.approx(0.0, abs=1e-8)


def test_a_collinear_design_is_refused_rather_than_producing_a_number() -> None:
    """A singular design would otherwise crash deep inside a linear-algebra call."""
    rng = np.random.default_rng(31)
    equity = rng.normal(0.006, 0.04, size=120)
    with pytest.raises(TrendMarginalValueError, match="collinear"):
        _attribute(equity, equity_excess=equity, scaled_equity_excess=0.5 * equity)


def test_a_sleeve_uncorrelated_with_the_market_leaves_its_mean_in_the_intercept() -> None:
    rng = np.random.default_rng(29)
    equity = rng.normal(0.006, 0.04, size=600)
    sleeve = rng.normal(0.004, 0.03, size=600)
    exposure = np.clip(1.0 + 0.5 * rng.normal(size=600), 0.2, 2.0)
    attribution = _attribute(
        sleeve, equity_excess=equity, scaled_equity_excess=exposure * equity
    )
    assert attribution.r_squared < 0.05
    assert attribution.annualised_alpha_percent == pytest.approx(
        100.0 * 12.0 * float(np.mean(sleeve[1:])), abs=0.6
    )


# --------------------------------------------------------------------------- #
# Wiring
# --------------------------------------------------------------------------- #


def test_the_registry_resolves_the_committed_entry_point() -> None:
    registry = build_registry()
    assert registry.names() == (ENTRY_POINT,)
    assert registry.resolve(ENTRY_POINT).__name__ == "run"


def _as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def _as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


def test_the_comparison_ids_match_the_frozen_specification() -> None:
    specification = load_specification(default_specification_path())
    comparison = _as_sequence(_as_mapping(specification.universe)["comparison_set"])
    assert tuple(str(_as_mapping(item)["id"]) for item in comparison) == COMPARISON_IDS


def test_the_specification_pins_the_workbook_sheet_this_module_reads() -> None:
    specification = load_specification(default_specification_path())
    pins = _as_mapping(_as_mapping(specification.parameters)["source_pin"])
    pin = _as_mapping(pins["aqr_tsmom"])
    dataset = aqr.get_dataset(str(pin["dataset_id"]))
    assert str(pin["sheet"]) == dataset.data_sheet
    assert str(pin["column"]) in dataset.expected_columns


def test_a_scenario_carries_everything_a_hostile_test_varies() -> None:
    """A hostile test must be a different Scenario, never a different code path."""
    scenario = Scenario(
        name="x",
        sleeve_excess=np.zeros(3),
        centre_of_mass_months=2.0,
        exposure_cap=1.5,
        sleeve_weight=0.15,
        equity_weight=0.6,
    )
    assert scenario.use_bond_leg is False
    with pytest.raises(FrozenInstanceError):
        scenario.sleeve_weight = 0.2  # type: ignore[misc]


def test_the_error_type_is_specific_enough_to_catch() -> None:
    assert issubclass(TrendMarginalValueError, RuntimeError)
