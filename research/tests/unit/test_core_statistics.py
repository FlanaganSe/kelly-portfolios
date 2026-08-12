"""Tests for :mod:`portfolio_edge.core.statistics`.

Every fixture is cited to ``docs/research/portfolio-engine-specification.md`` and
re-derived here from its stated inputs.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.stats import norm

from portfolio_edge.core.returns import Frequency, RateBasis
from portfolio_edge.core.statistics import (
    MIN_TAIL_OBSERVATIONS,
    InsufficientTailDataError,
    NonMonotoneExpansionError,
    QuantileRule,
    ar1_autocorrelations,
    cornish_fisher_derivative,
    cornish_fisher_value_at_risk,
    cornish_fisher_z,
    effective_tail_count,
    gaussian_expected_shortfall,
    gaussian_value_at_risk,
    historical_expected_shortfall,
    historical_value_at_risk,
    is_cornish_fisher_monotone,
    lo_annualisation_factor,
    max_admissible_skewness,
    mean_return,
    sharpe_ratio,
    sharpe_standard_error,
    volatility,
)

# --------------------------------------------------------------------------------------
# Moments and Sharpe
# --------------------------------------------------------------------------------------


def test_mean_and_volatility_use_the_stated_degrees_of_freedom() -> None:
    sample = [0.01, 0.03, -0.02, 0.04]
    assert mean_return(sample) == pytest.approx(sum(sample) / 4.0, rel=1e-15, abs=0.0)
    centred = [x - sum(sample) / 4.0 for x in sample]
    assert volatility(sample, ddof=1) == pytest.approx(
        math.sqrt(sum(x * x for x in centred) / 3.0), rel=1e-14, abs=0.0
    )
    assert volatility(sample, ddof=0) == pytest.approx(
        math.sqrt(sum(x * x for x in centred) / 4.0), rel=1e-14, abs=0.0
    )


def test_sharpe_ratio_is_the_excess_mean_over_the_excess_volatility() -> None:
    returns = [0.02, -0.01, 0.03, 0.00, 0.015]
    risk_free = 0.002
    excess = [r - risk_free for r in returns]
    mean = sum(excess) / len(excess)
    centred = [x - mean for x in excess]
    sigma = math.sqrt(sum(x * x for x in centred) / (len(excess) - 1))

    result = sharpe_ratio(returns, frequency=Frequency.MONTHLY, risk_free=risk_free)
    assert result.sharpe_per_period == pytest.approx(mean / sigma, rel=1e-14, abs=0.0)
    assert result.annualisation_factor == pytest.approx(math.sqrt(12.0), rel=1e-15, abs=0.0)
    assert result.annualised_sharpe == pytest.approx(
        mean / sigma * math.sqrt(12.0), rel=1e-14, abs=0.0
    )
    assert "arithmetic" in result.risk_free_treatment
    assert "monthly" in result.risk_free_treatment


def test_an_annualised_risk_free_rate_is_deannualised_before_subtraction() -> None:
    returns = [0.02, -0.01, 0.03, 0.00, 0.015]
    monthly_cash = 1.05 ** (1.0 / 12.0) - 1.0
    from_annual = sharpe_ratio(
        returns,
        frequency=Frequency.MONTHLY,
        risk_free=0.05,
        risk_free_basis=RateBasis.ANNUALISED,
    )
    from_monthly = sharpe_ratio(returns, frequency=Frequency.MONTHLY, risk_free=monthly_cash)
    assert from_annual.sharpe_per_period == pytest.approx(
        from_monthly.sharpe_per_period, rel=1e-14, abs=0.0
    )


@pytest.mark.parametrize(
    ("sharpe", "observations", "expected"),
    [(0.5, 60, 0.1369306394), (1.0, 120, 0.1118033989)],
)
def test_sharpe_standard_error_fixtures(
    sharpe: float, observations: int, expected: float
) -> None:
    """docs/research/portfolio-engine-specification.md, "Sharpe ratio inference".

    SE = sqrt((1 + SR^2 / 2) / T), re-derived from the stated inputs on both sides.
    """
    derived = math.sqrt((1.0 + sharpe**2 / 2.0) / observations)
    assert derived == pytest.approx(expected, rel=0.0, abs=5e-11)
    assert sharpe_standard_error(sharpe, observations) == pytest.approx(
        derived, rel=1e-15, abs=0.0
    )


def test_sharpe_standard_error_falls_with_the_square_root_of_sample_length() -> None:
    assert sharpe_standard_error(1.0, 480) == pytest.approx(
        sharpe_standard_error(1.0, 120) / 2.0, rel=1e-14, abs=0.0
    )


# --------------------------------------------------------------------------------------
# Lo (2002) autocorrelation-corrected annualisation
# --------------------------------------------------------------------------------------


def test_eta_reduces_to_sqrt_q_with_no_autocorrelation() -> None:
    factor = lo_annualisation_factor(12, [0.0] * 11)
    assert factor == pytest.approx(math.sqrt(12.0), rel=1e-15, abs=0.0)


@pytest.mark.parametrize(
    ("rho", "expected_eta", "expected_overstatement"),
    [
        (0.0, 3.464102, 0.0000),
        (0.1, 3.160111, 0.0962),
        (0.2, 2.878849, 0.2033),
        (0.3, 2.614806, 0.3248),
        (0.5, 2.121288, 0.6330),
        (-0.2, 4.170848, -0.1694),
    ],
)
def test_lo_eta_table_for_ar1_returns(
    rho: float, expected_eta: float, expected_overstatement: float
) -> None:
    """docs/research/portfolio-engine-specification.md, "Sharpe ratio inference".

    eta(q) = q / sqrt(q + 2 * sum_{k=1}^{q-1} (q - k) rho_k), with the AR(1)
    autocorrelation function rho_k = rho^k re-derived here from rho alone.
    Published to six decimals, so the tolerance is the rounding half-width.
    """
    rho_k = [rho**k for k in range(1, 12)]
    denominator = 12.0 + 2.0 * sum((12 - k) * rho_k[k - 1] for k in range(1, 12))
    derived = 12.0 / math.sqrt(denominator)
    assert derived == pytest.approx(expected_eta, rel=0.0, abs=5e-7)

    factor = lo_annualisation_factor(12, ar1_autocorrelations(rho, 11))
    assert factor == pytest.approx(derived, rel=1e-14, abs=0.0)
    assert math.sqrt(12.0) / factor - 1.0 == pytest.approx(
        expected_overstatement, rel=0.0, abs=5e-5
    )


def test_lo_eta_for_a_non_ar1_autocorrelation_function() -> None:
    """Engine specification: rho = [0.3, 0.2, 0.1, 0, ...] gives eta(12) = 2.429329."""
    rho = [0.3, 0.2, 0.1] + [0.0] * 8
    denominator = 12.0 + 2.0 * ((12 - 1) * 0.3 + (12 - 2) * 0.2 + (12 - 3) * 0.1)
    derived = 12.0 / math.sqrt(denominator)
    assert derived == pytest.approx(2.429329, rel=0.0, abs=5e-7)
    assert lo_annualisation_factor(12, rho) == pytest.approx(derived, rel=1e-14, abs=0.0)


def test_lo_eta_at_q_three() -> None:
    """Engine specification: q = 3 with rho = [0.5, 0.25] gives 1.279204."""
    denominator = 3.0 + 2.0 * ((3 - 1) * 0.5 + (3 - 2) * 0.25)
    derived = 3.0 / math.sqrt(denominator)
    assert derived == pytest.approx(1.279204, rel=0.0, abs=5e-7)
    assert lo_annualisation_factor(3, [0.5, 0.25]) == pytest.approx(
        derived, rel=1e-14, abs=0.0
    )


def test_negative_autocorrelation_makes_eta_exceed_sqrt_q() -> None:
    """sqrt(q) is an upper bound only under *positive* autocorrelation."""
    assert lo_annualisation_factor(12, ar1_autocorrelations(-0.2, 11)) > math.sqrt(12.0)
    assert lo_annualisation_factor(12, ar1_autocorrelations(0.2, 11)) < math.sqrt(12.0)


def test_eta_requires_q_minus_one_autocorrelations() -> None:
    with pytest.raises(ValueError, match="needs 11 autocorrelations"):
        lo_annualisation_factor(12, [0.1] * 5)


def test_eta_rejects_autocorrelations_implying_a_non_positive_variance() -> None:
    with pytest.raises(ValueError, match="not consistent with a positive"):
        lo_annualisation_factor(3, [-0.9, -0.9])


def test_sharpe_can_be_annualised_with_the_lo_factor() -> None:
    returns = [0.02, -0.01, 0.03, 0.00, 0.015, 0.005]
    factor = lo_annualisation_factor(12, ar1_autocorrelations(0.3, 11))
    result = sharpe_ratio(returns, frequency=Frequency.MONTHLY, annualisation_factor=factor)
    assert result.annualisation_factor == pytest.approx(factor, rel=1e-15, abs=0.0)
    assert result.annualised_sharpe == pytest.approx(
        result.sharpe_per_period * factor, rel=1e-14, abs=0.0
    )


# --------------------------------------------------------------------------------------
# Tail risk
# --------------------------------------------------------------------------------------


def test_historical_var_uses_the_documented_linear_interpolation_rule() -> None:
    """Hyndman-Fan type 7: h = (n - 1) alpha, interpolate between order statistics."""
    sample = [float(x) for x in range(-10, 10)]  # n = 20, sorted ascending
    alpha = 0.10
    h = (len(sample) - 1) * alpha  # 1.9
    lower = sample[1]
    upper = sample[2]
    expected = lower + (h - math.floor(h)) * (upper - lower)
    assert historical_value_at_risk(sample, alpha=alpha) == pytest.approx(
        -expected, rel=1e-14, abs=0.0
    )


def test_the_lower_rule_returns_an_actually_observed_loss() -> None:
    sample = [float(x) for x in range(-10, 10)]
    var = historical_value_at_risk(sample, alpha=0.10, rule=QuantileRule.LOWER)
    assert -var in sample
    # ceil(0.10 * 20) = 2, so the second-smallest observation.
    assert -var == pytest.approx(sorted(sample)[1], rel=0.0, abs=1e-15)


def test_the_lower_rule_is_weakly_more_conservative() -> None:
    rng = np.random.default_rng(20260811)
    sample = rng.normal(0.0, 0.02, size=250)
    linear = historical_value_at_risk(sample, alpha=0.05)
    lower = historical_value_at_risk(sample, alpha=0.05, rule=QuantileRule.LOWER)
    assert lower >= linear - 1e-12


def test_expected_shortfall_refuses_a_thin_tail_and_surfaces_the_count() -> None:
    """Engine specification: expected shortfall with fewer than about ten tail
    observations is unestimable, so surface the effective tail count."""
    rng = np.random.default_rng(1)
    sample = rng.normal(0.0, 0.02, size=60)  # 5% of 60 is 3 observations
    assert effective_tail_count(60, 0.05) == 3
    with pytest.raises(InsufficientTailDataError) as info:
        historical_expected_shortfall(sample, alpha=0.05)
    assert info.value.tail_observations < MIN_TAIL_OBSERVATIONS
    assert info.value.required == MIN_TAIL_OBSERVATIONS
    assert info.value.sample == 60
    assert "tail observation" in str(info.value)


def test_expected_shortfall_is_returned_once_the_tail_is_deep_enough() -> None:
    rng = np.random.default_rng(2)
    sample = rng.normal(0.0, 0.02, size=1000)
    result = historical_expected_shortfall(sample, alpha=0.05)
    assert result.tail_observations >= MIN_TAIL_OBSERVATIONS
    assert result.expected_shortfall > result.value_at_risk
    tail = np.sort(sample)[: result.tail_observations]
    assert result.expected_shortfall == pytest.approx(
        -float(np.mean(tail)), rel=1e-12, abs=0.0
    )


def test_effective_tail_count_scales_with_the_sample() -> None:
    assert effective_tail_count(200, 0.05) == 10
    assert effective_tail_count(199, 0.05) == 9


def test_gaussian_var_and_expected_shortfall_match_their_closed_forms() -> None:
    mean, sigma, alpha = 0.005, 0.04, 0.05
    z = float(norm.ppf(alpha))
    assert gaussian_value_at_risk(mean, sigma, alpha=alpha) == pytest.approx(
        -(mean + sigma * z), rel=1e-14, abs=0.0
    )
    assert gaussian_expected_shortfall(mean, sigma, alpha=alpha) == pytest.approx(
        -(mean - sigma * float(norm.pdf(z)) / alpha), rel=1e-14, abs=0.0
    )
    assert gaussian_expected_shortfall(mean, sigma, alpha=alpha) > gaussian_value_at_risk(
        mean, sigma, alpha=alpha
    )


# --------------------------------------------------------------------------------------
# Cornish-Fisher
# --------------------------------------------------------------------------------------


def test_cornish_fisher_reduces_to_z_for_a_normal_distribution() -> None:
    for z in (-2.0, -1.0, 0.0, 1.0, 2.0):
        assert cornish_fisher_z(z, 0.0, 0.0) == pytest.approx(z, rel=0.0, abs=1e-15)
        assert cornish_fisher_derivative(z, 0.0, 0.0) == pytest.approx(
            1.0, rel=0.0, abs=1e-15
        )


def test_cornish_fisher_derivative_matches_a_numerical_derivative() -> None:
    skew, kurtosis, step = -0.3, 2.0, 1e-6
    for z in (-2.5, -1.0, 0.5, 2.0):
        numerical = (
            cornish_fisher_z(z + step, skew, kurtosis)
            - cornish_fisher_z(z - step, skew, kurtosis)
        ) / (2.0 * step)
        assert cornish_fisher_derivative(z, skew, kurtosis) == pytest.approx(
            numerical, rel=1e-7, abs=0.0
        )


@pytest.mark.parametrize(
    ("excess_kurtosis", "published_bound"),
    [(0.0, 0.418), (1.0, 0.834), (3.0, 1.376), (6.0, 1.921)],
)
def test_admissible_skew_bounds_by_kurtosis(
    excess_kurtosis: float, published_bound: float
) -> None:
    """docs/research/portfolio-engine-specification.md, "Tail risk".

    Scanning z in [-4, 4] gives |S| < 0.418 at K=0, 0.834 at K=1, 1.376 at K=3,
    1.921 at K=6. The published figures are truncated to three decimals, so the
    bound must lie in [published, published + 0.001).
    """
    bound = max_admissible_skewness(excess_kurtosis, grid_points=8001, tolerance=1e-7)
    assert published_bound <= bound < published_bound + 1e-3
    assert is_cornish_fisher_monotone(
        bound - 1e-4, excess_kurtosis, grid_points=8001
    )
    assert not is_cornish_fisher_monotone(
        bound + 1e-3, excess_kurtosis, grid_points=8001
    )


def test_the_expansion_returns_a_plausible_number_where_it_is_invalid() -> None:
    """Engine specification: at alpha=0.05, S=-2.0, K=1 the formula returns -2.118056
    and is non-monotone, so the value is meaningless. The raw transform is exposed so
    that this failure mode is testable, but the VaR wrapper must refuse it."""
    z = float(norm.ppf(0.05))
    assert cornish_fisher_z(z, -2.0, 1.0) == pytest.approx(-2.118056, rel=0.0, abs=5e-7)
    assert not is_cornish_fisher_monotone(-2.0, 1.0)


def test_cornish_fisher_var_raises_when_the_derivative_changes_sign() -> None:
    with pytest.raises(NonMonotoneExpansionError) as info:
        cornish_fisher_value_at_risk(
            mean=0.0, sigma=1.0, skewness=-2.0, excess_kurtosis=1.0, alpha=0.05
        )
    assert info.value.derivative <= 0.0
    assert -4.0 <= info.value.z <= 4.0


def test_cornish_fisher_var_returns_a_value_inside_the_admissible_region() -> None:
    mean, sigma, skew, kurtosis, alpha = 0.004, 0.045, -0.3, 1.0, 0.05
    z = float(norm.ppf(alpha))
    expected = -(mean + sigma * cornish_fisher_z(z, skew, kurtosis))
    assert cornish_fisher_value_at_risk(
        mean=mean, sigma=sigma, skewness=skew, excess_kurtosis=kurtosis, alpha=alpha
    ) == pytest.approx(expected, rel=1e-14, abs=0.0)


def test_negative_skew_raises_cornish_fisher_var_above_the_gaussian_one() -> None:
    mean, sigma, alpha = 0.0, 0.04, 0.05
    adjusted = cornish_fisher_value_at_risk(
        mean=mean, sigma=sigma, skewness=-0.3, excess_kurtosis=1.0, alpha=alpha
    )
    assert adjusted > gaussian_value_at_risk(mean, sigma, alpha=alpha)
