"""The current-pricing arithmetic, against fixtures computed independently of it.

Every expectation below is worked out without calling the function under test: the
percentile by counting, the value spread from ``math.log`` on paper, the minimum
detectable slope from the two normal quantiles it is defined by, and the out-of-sample
``R**2`` from a two-origin case small enough to write down. A fixture that disagrees with
the implementation is a finding, not a tolerance to loosen.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies._current_pricing_tables import (
    _forward_log_returns,
    _out_of_sample_r2,
)
from portfolio_edge.studies.current_pricing import (
    PricedLevel,
    classify_evidence,
    expanding_percentile_rank,
    fisher_real_rate,
    log_value_spread,
    mark_to_market_log_spread,
    minimum_detectable_slope,
    percentile_rank,
    simple_real_rate,
)

# --------------------------------------------------------------------------------------
# Percentiles
# --------------------------------------------------------------------------------------


def test_percentile_rank_counts_strictly_below() -> None:
    """Three of the five entries are below 4.0, so the rank is 0.6 exactly."""
    assert percentile_rank([1.0, 2.0, 3.0, 4.0, 9.0], 4.0) == pytest.approx(0.6)


def test_percentile_rank_of_an_all_time_high_is_one_minus_one_over_n() -> None:
    """The strict-below convention makes a record read 0.99, never 1.00."""
    history = list(range(100))
    assert percentile_rank(history, 99.0) == pytest.approx(0.99)


def test_percentile_rank_rejects_an_empty_history() -> None:
    with pytest.raises(ValueError, match="empty"):
        percentile_rank([], 1.0)


def test_percentile_rank_rejects_a_non_finite_history() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        percentile_rank([1.0, float("nan")], 1.0)


def test_expanding_percentile_never_sees_the_future() -> None:
    """A series that rises monotonically is at its own record in every window."""
    values = np.arange(10.0)
    out = expanding_percentile_rank(values, burn_in=1)
    assert np.isnan(out[0])
    for index in range(1, 10):
        assert out[index] == pytest.approx(index / (index + 1))


def test_expanding_percentile_ignores_later_extremes() -> None:
    """The rank at index 2 is unchanged by a spike at index 5."""
    base = expanding_percentile_rank([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], burn_in=1)
    spiked = expanding_percentile_rank([1.0, 2.0, 3.0, 4.0, 5.0, 600.0], burn_in=1)
    assert base[2] == pytest.approx(spiked[2])


def test_expanding_percentile_rejects_a_zero_burn_in() -> None:
    with pytest.raises(ValueError, match="burn_in"):
        expanding_percentile_rank([1.0, 2.0], burn_in=0)


# --------------------------------------------------------------------------------------
# Levels
# --------------------------------------------------------------------------------------


def test_priced_level_rejects_a_percentile_outside_the_unit_interval() -> None:
    with pytest.raises(ValueError, match="percentile"):
        PricedLevel(
            name="x", value=1.0, units="pp", as_of="2026-08-20", percentile=1.4,
            window=("a", "b"), n_observations=10, source="s",
        )


def test_priced_level_rejects_an_empty_history() -> None:
    with pytest.raises(ValueError, match="n_observations"):
        PricedLevel(
            name="x", value=1.0, units="pp", as_of="2026-08-20", percentile=0.5,
            window=("a", "b"), n_observations=0, source="s",
        )


def test_real_rate_conventions_differ_by_the_cross_term() -> None:
    """At 3.73% nominal and 3.54% inflation the two conventions differ by 6.6 bp."""
    simple = simple_real_rate(3.73, 3.54)
    fisher = fisher_real_rate(3.73, 3.54)
    assert simple == pytest.approx(0.19)
    assert fisher == pytest.approx(100.0 * (1.0373 / 1.0354 - 1.0))
    assert simple - fisher == pytest.approx(0.0065, abs=5e-4)


def test_fisher_real_rate_rejects_total_deflation() -> None:
    with pytest.raises(ValueError, match="Fisher"):
        fisher_real_rate(1.0, -100.0)


# --------------------------------------------------------------------------------------
# The value spread
# --------------------------------------------------------------------------------------


def test_log_value_spread_against_hand_arithmetic() -> None:
    """French's 2026-06 big-cap pair: BE/ME 0.9479 against 0.0909."""
    assert log_value_spread(0.9479, 0.0909) == pytest.approx(
        math.log(0.9479) - math.log(0.0909)
    )
    assert log_value_spread(0.9479, 0.0909) == pytest.approx(2.34449, abs=1e-5)


def test_log_value_spread_is_the_log_of_the_ratio() -> None:
    assert log_value_spread(1.0, 0.2) == pytest.approx(math.log(5.0))


def test_log_value_spread_rejects_a_non_positive_ratio() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        log_value_spread(1.0, 0.0)


def test_mark_to_market_is_a_no_op_when_both_sides_moved_together() -> None:
    """Equal returns cancel exactly, which is the identity the adjustment must hold."""
    assert mark_to_market_log_spread(
        2.0, growth_cumulative_return=1.37, value_cumulative_return=1.37
    ) == pytest.approx(2.0)


def test_mark_to_market_narrows_the_spread_when_the_cheap_side_outperforms() -> None:
    """Big-cap value +62.3% against big-cap growth +24.1% narrows it by 0.269 log."""
    adjusted = mark_to_market_log_spread(
        2.286, growth_cumulative_return=1.241, value_cumulative_return=1.623
    )
    assert adjusted == pytest.approx(2.286 + math.log(1.241 / 1.623), abs=1e-9)
    assert adjusted - 2.286 == pytest.approx(-0.2680, abs=1e-3)


def test_mark_to_market_rejects_a_non_positive_multiple() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        mark_to_market_log_spread(1.0, growth_cumulative_return=0.0, value_cumulative_return=1.0)


# --------------------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------------------


def test_minimum_detectable_slope_is_the_two_quantile_sum() -> None:
    """1.959964 + 0.841621 = 2.801585, times the standard error."""
    assert minimum_detectable_slope(1.0) == pytest.approx(2.801585, abs=1e-5)
    assert minimum_detectable_slope(0.5) == pytest.approx(1.400793, abs=1e-5)


def test_minimum_detectable_slope_at_fifty_percent_power_is_the_critical_value() -> None:
    """At 50% power the second quantile vanishes and only the size term survives."""
    assert minimum_detectable_slope(1.0, power=0.5) == pytest.approx(1.959964, abs=1e-5)


def test_minimum_detectable_slope_rejects_a_zero_standard_error() -> None:
    with pytest.raises(ValueError, match="standard_error"):
        minimum_detectable_slope(0.0)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1])
def test_minimum_detectable_slope_rejects_a_degenerate_power(bad: float) -> None:
    with pytest.raises(ValueError, match="power"):
        minimum_detectable_slope(1.0, power=bad)


# --------------------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------------------


def test_a_large_t_with_a_negative_out_of_sample_r2_is_unresolved() -> None:
    """The CAPE signature: Hodrick t of 2.47 and an out-of-sample R**2 of -0.44."""
    assert classify_evidence(
        t_hodrick_1b=2.47,
        r_squared_out_of_sample=-0.44,
        slope_per_sd=3.0,
        minimum_detectable_per_sd=1.0,
    ) == "unresolved"


def test_both_legs_are_needed_for_supported() -> None:
    assert classify_evidence(
        t_hodrick_1b=3.14,
        r_squared_out_of_sample=0.127,
        slope_per_sd=3.18,
        minimum_detectable_per_sd=2.84,
    ) == "supported"


def test_a_slope_below_its_own_resolution_is_never_supported() -> None:
    """Same statistics, but the estimate is smaller than the design could detect."""
    assert classify_evidence(
        t_hodrick_1b=3.14,
        r_squared_out_of_sample=0.127,
        slope_per_sd=1.0,
        minimum_detectable_per_sd=2.84,
    ) == "suggestive"


def test_a_weak_t_with_a_positive_out_of_sample_record_is_suggestive() -> None:
    assert classify_evidence(
        t_hodrick_1b=1.35,
        r_squared_out_of_sample=0.117,
        slope_per_sd=0.47,
        minimum_detectable_per_sd=0.97,
    ) == "suggestive"


def test_the_value_spread_grades_unresolved_on_its_own_numbers() -> None:
    """Positive out of sample, but a Hodrick t of 1.01 clears no threshold."""
    assert classify_evidence(
        t_hodrick_1b=1.014,
        r_squared_out_of_sample=0.033,
        slope_per_sd=2.599,
        minimum_detectable_per_sd=7.179,
    ) == "unresolved"


# --------------------------------------------------------------------------------------
# The regression plumbing
# --------------------------------------------------------------------------------------


def test_forward_log_returns_start_one_period_after_the_origin() -> None:
    """Element 0 must be the return realised *after* the origin, never during it."""
    returns = np.array([0.10, 0.20, 0.30, 0.40])
    out = _forward_log_returns(returns, horizon=1, periods_per_year=1)
    assert out.size == 3
    assert out[0] == pytest.approx(math.log(1.20))
    assert out[2] == pytest.approx(math.log(1.40))


def test_forward_log_returns_annualise_a_multi_period_window() -> None:
    returns = np.array([0.0, 0.10, 0.20, 0.30])
    out = _forward_log_returns(returns, horizon=2, periods_per_year=1)
    assert out[0] == pytest.approx((math.log(1.10) + math.log(1.20)) / 2.0)


def test_out_of_sample_r2_is_zero_when_the_predictor_carries_nothing() -> None:
    """A constant predictor fits the training mean, so the model *is* the benchmark."""
    rng = np.random.default_rng(20260823)
    returns = rng.normal(0.01, 0.05, 400)
    predictor = np.zeros(400)
    assert _out_of_sample_r2(
        predictor, returns, horizon=1, periods_per_year=1, minimum_training=20
    ) == pytest.approx(0.0, abs=1e-9)


def test_out_of_sample_r2_is_positive_on_a_genuinely_predictive_series() -> None:
    """Next period's return is the predictor plus small noise; the model must win."""
    rng = np.random.default_rng(20260823)
    predictor = rng.normal(0.0, 0.05, 400)
    returns = np.empty(400)
    returns[0] = 0.0
    returns[1:] = predictor[:-1] + rng.normal(0.0, 0.005, 399)
    score = _out_of_sample_r2(
        predictor, returns, horizon=1, periods_per_year=1, minimum_training=20
    )
    assert score > 0.9


def test_out_of_sample_r2_matches_hand_arithmetic_on_a_two_origin_case() -> None:
    """Two forecasts, both fitted here by ``numpy.linalg.lstsq`` rather than by the module.

    The training rule under test is that an origin at ``i`` may use rows up to
    ``i - horizon`` and no further, because the outcome for row ``i - horizon + 1`` has
    not finished being realised at ``i``. Transcribing that rule by hand is the point:
    an off-by-one here is exactly the leak the rule exists to prevent.
    """
    predictor = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    returns = np.array([0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
    forward = _forward_log_returns(returns, horizon=1, periods_per_year=1)
    expected_errors = []
    expected_base = []
    for index in (4, 5):
        train = index - 1
        design = np.column_stack([np.ones(train), predictor[:train]])
        beta = np.linalg.lstsq(design, forward[:train], rcond=None)[0]
        expected_errors.append(forward[index] - (beta[0] + beta[1] * predictor[index]))
        expected_base.append(forward[index] - forward[:train].mean())
    expected = 1.0 - float(np.sum(np.square(expected_errors))) / float(
        np.sum(np.square(expected_base))
    )
    assert _out_of_sample_r2(
        predictor, returns, horizon=1, periods_per_year=1, minimum_training=3
    ) == pytest.approx(expected)
