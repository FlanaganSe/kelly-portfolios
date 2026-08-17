"""Closed-form tests for :mod:`portfolio_edge.studies.factor_breadth`.

No market data. Every fixture is either an identity that can be checked by hand or a
value computed independently of the implementation under test — in particular the
exact effective breadth is checked against the equicorrelated closed form in
:mod:`portfolio_edge.studies.overlay_growth`, which shares no code with it.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.factor_breadth import (
    admission,
    average_pairwise_correlation,
    common_window,
    correlation_matrix,
    decile_spread,
    exact_effective_breadth,
    minimum_detectable_effect,
    normal_one_sided_p_value,
    premium,
)
from portfolio_edge.studies.overlay_growth import effective_breadth


def test_minimum_detectable_effect_is_the_two_quantile_sum() -> None:
    assert minimum_detectable_effect(1.0) == pytest.approx(1.6448536269514722 + 0.8416212335729143)
    assert minimum_detectable_effect(0.0) == 0.0
    with pytest.raises(ValueError, match="non-negative"):
        minimum_detectable_effect(-1e-9)


def test_the_one_sided_p_value_matches_the_standard_normal_at_known_points() -> None:
    assert normal_one_sided_p_value(0.0) == pytest.approx(0.5)
    assert normal_one_sided_p_value(1.6448536269514722) == pytest.approx(0.05, abs=1e-12)
    assert normal_one_sided_p_value(1.959963984540054) == pytest.approx(0.025, abs=1e-12)
    assert normal_one_sided_p_value(-1.6448536269514722) == pytest.approx(0.95, abs=1e-12)


def test_a_constant_series_annualises_exactly_and_has_no_dispersion() -> None:
    """Twelve identical monthly returns of 1% are a 12 pp/yr arithmetic premium."""
    estimate = premium([0.01] * 240, label="constant")
    assert estimate.months == 240
    assert estimate.annualised_premium == pytest.approx(0.12)
    assert estimate.annualised_volatility == pytest.approx(0.0)
    assert estimate.hac_standard_error == pytest.approx(0.0)
    assert estimate.mde_80 == pytest.approx(0.0)
    # A zero-dispersion series has no defined t statistic or Sharpe ratio; both
    # guards report zero rather than dividing. The premium is still resolved,
    # because a deterministic 12 pp/yr sits above a detection floor of zero.
    assert estimate.t_statistic == 0.0
    assert estimate.sharpe == 0.0
    assert estimate.resolved is True


def test_the_annualised_volatility_is_the_sample_sd_times_root_twelve() -> None:
    rng = np.random.default_rng(20260816)
    values = rng.normal(loc=0.005, scale=0.03, size=600)
    estimate = premium(values, label="gaussian")
    assert estimate.annualised_premium == pytest.approx(12.0 * float(np.mean(values)))
    assert estimate.annualised_volatility == pytest.approx(
        float(np.std(values, ddof=1)) * math.sqrt(12.0)
    )
    assert estimate.sharpe == pytest.approx(
        estimate.annualised_premium / estimate.annualised_volatility
    )
    assert estimate.interval_high - estimate.interval_low == pytest.approx(
        2.0 * 1.959963984540054 * estimate.hac_standard_error
    )


def test_a_premium_below_its_own_detection_floor_is_reported_unresolved() -> None:
    """The whole point of carrying an MDE beside a point estimate."""
    rng = np.random.default_rng(7)
    quiet = rng.normal(loc=0.0002, scale=0.04, size=120)
    estimate = premium(quiet, label="quiet")
    assert estimate.annualised_premium < estimate.mde_80
    assert estimate.resolved is False


def test_non_finite_and_ragged_input_is_refused_rather_than_filled() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        premium([0.01, float("nan"), 0.02], label="hole")
    with pytest.raises(ValueError, match="at least two observations"):
        premium([0.01], label="single")
    with pytest.raises(ValueError, match="different lengths"):
        correlation_matrix([[0.1, 0.2, 0.3], [0.1, 0.2]])


def test_exact_effective_breadth_reproduces_the_equicorrelated_closed_form() -> None:
    """``1' R^-1 1`` equals ``k / (1 + (k-1) rho)`` when ``R`` is equicorrelated.

    The two are computed by disjoint code — one solves a linear system, the other
    evaluates a scalar formula in a different module — so agreement to machine
    precision is a real check rather than a restatement.
    """
    for count in (2, 3, 5, 8):
        for rho in (-0.05, 0.0, 0.1, 0.3, 0.7):
            matrix = [
                [1.0 if i == j else rho for j in range(count)] for i in range(count)
            ]
            assert exact_effective_breadth(matrix) == pytest.approx(
                effective_breadth(count=count, mutual_correlation=rho), rel=1e-12
            )


def test_uncorrelated_sleeves_give_breadth_equal_to_their_count() -> None:
    identity = [[float(i == j) for j in range(4)] for i in range(4)]
    assert exact_effective_breadth(identity) == pytest.approx(4.0)


def test_the_exact_form_sees_a_hidden_pair_that_the_average_hides() -> None:
    """Three sleeves, two of which are nearly the same strategy.

    The average pairwise correlation is a mild 0.33 and the equicorrelated formula
    reports 1.81 effective sleeves. The exact figure is 2.005 — almost exactly the
    two engines that are really there, one of them held twice. The point is that
    they differ at all: an average over a matrix with one 0.99 entry and two zeros
    is describing a portfolio that does not exist.
    """
    matrix = [
        [1.00, 0.99, 0.00],
        [0.99, 1.00, 0.00],
        [0.00, 0.00, 1.00],
    ]
    average = average_pairwise_correlation(matrix)
    assert average == pytest.approx(0.33, abs=0.005)
    equicorrelated = effective_breadth(count=3, mutual_correlation=average)
    exact = exact_effective_breadth(matrix)
    assert equicorrelated == pytest.approx(1.8072, abs=0.001)
    assert exact == pytest.approx(2.005, abs=0.001)
    # Two near-identical sleeves plus one independent one is close to two engines.
    assert exact > equicorrelated


def test_two_identical_series_make_breadth_undefined_rather_than_infinite() -> None:
    with pytest.raises(ValueError, match="same series"):
        exact_effective_breadth([[1.0, 1.0], [1.0, 1.0]])


def test_admission_is_the_first_order_condition_and_withholds_above_half() -> None:
    verdict = admission(
        label="d", sharpe=0.5, correlation=-0.10, base_volatility=0.16, base_exposure=1.5
    )
    assert verdict.threshold == pytest.approx(1.5 * -0.10 * 0.16)
    assert verdict.margin == pytest.approx(0.5 - verdict.threshold)
    assert verdict.clears is True
    assert verdict.usable is True

    crowded = admission(
        label="d", sharpe=0.55, correlation=0.86, base_volatility=0.16, base_exposure=1.0
    )
    assert crowded.clears is True
    assert crowded.usable is False, (
        "at rho = 0.86 the first-order condition mis-scores a covered-call sleeve, "
        "which is the failure overlay_growth measured"
    )


def test_a_decile_spread_names_which_leg_is_long() -> None:
    spread = decile_spread([0.03, 0.01], [0.01, 0.02])
    assert list(spread) == pytest.approx([0.02, -0.01])
    with pytest.raises(ValueError, match="same length"):
        decile_spread([0.01, 0.02, 0.03], [0.01, 0.02])


def test_the_common_window_is_the_intersection_in_sorted_order() -> None:
    assert common_window(
        [("1990-01", "1990-02", "1990-03"), ("1990-02", "1990-03", "1990-04")]
    ) == ("1990-02", "1990-03")
    assert common_window([("1990-01",), ("1991-01",)]) == ()


def test_correlation_matrix_is_symmetric_with_a_unit_diagonal() -> None:
    rng = np.random.default_rng(11)
    series = [rng.normal(size=200) for _ in range(3)]
    matrix = correlation_matrix(series)
    for i in range(3):
        assert matrix[i][i] == pytest.approx(1.0)
        for j in range(3):
            assert matrix[i][j] == pytest.approx(matrix[j][i])


def test_average_pairwise_correlation_uses_only_the_upper_triangle() -> None:
    matrix = [[1.0, 0.2, 0.4], [0.2, 1.0, 0.6], [0.4, 0.6, 1.0]]
    assert average_pairwise_correlation(matrix) == pytest.approx((0.2 + 0.4 + 0.6) / 3.0)
    with pytest.raises(ValueError, match="at least two series"):
        average_pairwise_correlation([[1.0]])
