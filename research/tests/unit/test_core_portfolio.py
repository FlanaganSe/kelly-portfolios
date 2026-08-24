"""Tests for :mod:`portfolio_edge.core.portfolio`."""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.portfolio import (
    DEFAULT_WEIGHT_TOLERANCE,
    NotPositiveDefiniteError,
    WeightNormalisationError,
    check_weights_sum_to_one,
    drift_weights,
    equal_risk_contribution_weights,
    equal_weights,
    excess_growth_rate,
    inverse_volatility_weights,
    marginal_risk_contributions,
    minimum_variance_weights,
    normalise_weights,
    portfolio_volatility,
    relative_risk_contributions,
    risk_contributions,
    validate_covariance,
)

# ERC fixture, docs/research/portfolio-edge-research-framework.md "Numerical fixtures":
# sigma_e = 16%, sigma_b = 6%, rho = 0.
SIGMA_EQUITY = 0.16
SIGMA_BOND = 0.06


def covariance_two_asset(rho: float) -> list[list[float]]:
    """Two-asset covariance matrix from the fixture volatilities and a correlation."""
    off = rho * SIGMA_EQUITY * SIGMA_BOND
    return [[SIGMA_EQUITY**2, off], [off, SIGMA_BOND**2]]


# --------------------------------------------------------------------------------------
# Weights
# --------------------------------------------------------------------------------------


def test_equal_weights_sum_to_one() -> None:
    check_weights_sum_to_one(equal_weights(7))


def test_normalise_weights_rescales_to_one() -> None:
    normalised = normalise_weights([2.0, 3.0, 5.0])
    assert normalised == pytest.approx([0.2, 0.3, 0.5], rel=0.0, abs=1e-15)
    check_weights_sum_to_one(normalised)


def test_weight_check_uses_the_declared_tolerance() -> None:
    almost = [0.5, 0.5 + DEFAULT_WEIGHT_TOLERANCE / 2.0]
    check_weights_sum_to_one(almost)
    with pytest.raises(WeightNormalisationError):
        check_weights_sum_to_one([0.5, 0.5 + 1e-6])
    check_weights_sum_to_one([0.5, 0.5 + 1e-6], tolerance=1e-5)


def test_weights_summing_to_zero_cannot_be_normalised() -> None:
    with pytest.raises(WeightNormalisationError):
        normalise_weights([1.0, -1.0])


def test_buy_and_hold_drift_moves_weight_towards_the_winner() -> None:
    drifted = drift_weights([0.5, 0.5], [0.20, -0.10])
    expected_first = 0.5 * 1.20 / (0.5 * 1.20 + 0.5 * 0.90)
    assert float(drifted[0]) == pytest.approx(expected_first, rel=1e-15, abs=0.0)
    assert float(drifted[0]) > 0.5
    check_weights_sum_to_one(drifted)


def test_drift_is_the_identity_when_returns_are_equal() -> None:
    drifted = drift_weights([0.3, 0.7], [0.05, 0.05])
    assert drifted == pytest.approx([0.3, 0.7], rel=1e-15, abs=0.0)


# --------------------------------------------------------------------------------------
# Risk contributions
# --------------------------------------------------------------------------------------


def test_risk_contributions_sum_to_portfolio_volatility_euler_property() -> None:
    rng = np.random.default_rng(20260811)
    factor = rng.normal(size=(6, 12))
    covariance = factor @ factor.T / 12.0 + np.eye(6) * 1e-3
    weights = normalise_weights(rng.uniform(0.05, 1.0, size=6))
    contributions = risk_contributions(weights, covariance)
    assert float(np.sum(contributions)) == pytest.approx(
        portfolio_volatility(weights, covariance), rel=1e-13, abs=0.0
    )
    assert float(np.sum(relative_risk_contributions(weights, covariance))) == pytest.approx(
        1.0, rel=1e-13, abs=0.0
    )


def test_marginal_risk_contribution_matches_a_numerical_derivative() -> None:
    covariance = covariance_two_asset(0.3)
    weights = np.array([0.4, 0.6])
    step = 1e-7
    for i in range(2):
        bumped_up = weights.copy()
        bumped_up[i] += step
        bumped_down = weights.copy()
        bumped_down[i] -= step
        numerical = (
            portfolio_volatility(bumped_up, covariance)
            - portfolio_volatility(bumped_down, covariance)
        ) / (2.0 * step)
        assert float(marginal_risk_contributions(weights, covariance)[i]) == pytest.approx(
            numerical, rel=1e-6, abs=0.0
        )


# --------------------------------------------------------------------------------------
# Equal risk contribution fixtures
# --------------------------------------------------------------------------------------


def test_two_asset_erc_equals_inverse_volatility_exactly() -> None:
    """Fixture: sigma_e = 16%, sigma_b = 6%, rho = 0 -> w = (3/11, 8/11) exactly.

    Re-derived: inverse-volatility weights are (1/0.16, 1/0.06) normalised. Scaling
    both by 0.48 gives (3, 8), so w = (3/11, 8/11). Source:
    docs/research/portfolio-edge-research-framework.md, "Numerical fixtures"; the
    two-asset reduction is proved in Maillard, Roncalli and Teiletche (2010).
    """
    assert pytest.approx(3.0, rel=1e-15, abs=0.0) == (1.0 / SIGMA_EQUITY) * 0.48
    assert pytest.approx(8.0, rel=1e-15, abs=0.0) == (1.0 / SIGMA_BOND) * 0.48

    weights = equal_risk_contribution_weights(covariance_two_asset(0.0))
    assert weights == pytest.approx([3.0 / 11.0, 8.0 / 11.0], rel=1e-12, abs=0.0)
    assert weights == pytest.approx(
        inverse_volatility_weights(covariance_two_asset(0.0)), rel=1e-12, abs=0.0
    )


@pytest.mark.parametrize("rho", [-0.9, -0.5, -0.2, 0.0, 0.2, 0.5, 0.9])
def test_two_asset_erc_is_independent_of_correlation(rho: float) -> None:
    """Proved, not empirical: for two assets ERC reduces exactly to inverse
    volatility independent of rho (Maillard, Roncalli and Teiletche 2010)."""
    weights = equal_risk_contribution_weights(covariance_two_asset(rho))
    assert weights == pytest.approx([3.0 / 11.0, 8.0 / 11.0], rel=1e-11, abs=0.0)


def test_two_asset_erc_portfolio_volatility_and_risk_contributions() -> None:
    """Fixture: sigma_p^2 = 288/75625, sigma_p = 0.06171113727,
    RC_e = RC_b = 0.030855568634, summing to sigma_p by Euler.

    Re-derived: with rho = 0, sigma_p^2 = (3/11)^2 (0.16)^2 + (8/11)^2 (0.06)^2
    = (9 * 0.0256 + 64 * 0.0036) / 121 = 0.4608 / 121 = 288 / 75625.
    """
    derived_variance = (9.0 * SIGMA_EQUITY**2 + 64.0 * SIGMA_BOND**2) / 121.0
    assert derived_variance == pytest.approx(288.0 / 75625.0, rel=1e-15, abs=0.0)
    assert math.sqrt(derived_variance) == pytest.approx(0.06171113727, rel=0.0, abs=5e-11)

    covariance = covariance_two_asset(0.0)
    weights = equal_risk_contribution_weights(covariance)
    sigma_p = portfolio_volatility(weights, covariance)
    assert sigma_p == pytest.approx(math.sqrt(derived_variance), rel=1e-12, abs=0.0)

    contributions = risk_contributions(weights, covariance)
    assert contributions == pytest.approx(
        [0.030855568634, 0.030855568634], rel=0.0, abs=5e-12
    )
    assert float(np.sum(contributions)) == pytest.approx(sigma_p, rel=1e-13, abs=0.0)
    assert float(contributions[0]) == pytest.approx(sigma_p / 2.0, rel=1e-13, abs=0.0)


def test_erc_equalises_risk_contributions_for_many_assets() -> None:
    rng = np.random.default_rng(7)
    factor = rng.normal(size=(8, 40))
    covariance = factor @ factor.T / 40.0 + np.eye(8) * 1e-2
    weights = equal_risk_contribution_weights(covariance)
    contributions = risk_contributions(weights, covariance)
    assert float(np.max(contributions) - np.min(contributions)) < 1e-12
    assert np.all(weights > 0.0)
    check_weights_sum_to_one(weights, tolerance=1e-12)


def test_erc_is_not_inverse_volatility_for_more_than_two_assets() -> None:
    """The two-asset reduction holds for n > 2 only under constant correlation."""
    covariance = np.array(
        [
            [0.04, 0.012, 0.000],
            [0.012, 0.09, 0.030],
            [0.000, 0.030, 0.16],
        ]
    )
    erc = equal_risk_contribution_weights(covariance)
    inverse_vol = inverse_volatility_weights(covariance)
    assert float(np.max(np.abs(erc - inverse_vol))) > 1e-3


def test_erc_reduces_to_inverse_volatility_under_constant_correlation() -> None:
    sigmas = np.array([0.05, 0.10, 0.20, 0.35])
    rho = 0.4
    correlation = np.full((4, 4), rho)
    np.fill_diagonal(correlation, 1.0)
    covariance = np.outer(sigmas, sigmas) * correlation
    assert equal_risk_contribution_weights(covariance) == pytest.approx(
        inverse_volatility_weights(covariance), rel=1e-9, abs=0.0
    )


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_volatility_ordering_mv_le_erc_le_equal_weight(seed: int) -> None:
    """sigma_MV <= sigma_ERC <= sigma_1/N on a random positive-definite covariance.

    Proved rather than empirical (Maillard, Roncalli and Teiletche 2010), so a
    violation is a bug, not a sample. The matrix is built as W W' / T + ridge, which
    is positive definite by construction.
    """
    rng = np.random.default_rng(seed)
    n = 6
    factor = rng.normal(size=(n, 30))
    covariance = factor @ factor.T / 30.0 + np.eye(n) * 5e-3
    validate_covariance(covariance)

    sigma_mv = portfolio_volatility(minimum_variance_weights(covariance), covariance)
    sigma_erc = portfolio_volatility(equal_risk_contribution_weights(covariance), covariance)
    sigma_ew = portfolio_volatility(equal_weights(n), covariance)

    assert sigma_mv <= sigma_erc + 1e-10
    assert sigma_erc <= sigma_ew + 1e-10


def test_minimum_variance_is_long_only_by_default() -> None:
    # sigma = (10%, 30%), rho = 0.9. Sigma^-1 1 is proportional to
    # (0.09 - 0.027, 0.01 - 0.027) = (0.063, -0.017), so the unconstrained
    # minimum-variance portfolio shorts the high-volatility asset.
    covariance = np.array([[0.01, 0.027], [0.027, 0.09]])
    unconstrained = minimum_variance_weights(covariance, long_only=False)
    assert float(np.min(unconstrained)) < 0.0
    constrained = minimum_variance_weights(covariance, long_only=True)
    assert float(np.min(constrained)) >= -1e-12
    check_weights_sum_to_one(constrained, tolerance=1e-9)


def test_excess_growth_rate_is_non_negative_for_long_only_weights() -> None:
    covariance = covariance_two_asset(0.2)
    weights = [0.5, 0.5]
    derived = 0.5 * (
        0.5 * SIGMA_EQUITY**2
        + 0.5 * SIGMA_BOND**2
        - float(np.array(weights) @ np.array(covariance) @ np.array(weights))
    )
    assert excess_growth_rate(weights, covariance) == pytest.approx(
        derived, rel=1e-14, abs=0.0
    )
    assert excess_growth_rate(weights, covariance) >= 0.0


def test_excess_growth_rate_vanishes_for_a_single_asset_portfolio() -> None:
    covariance = covariance_two_asset(0.0)
    assert excess_growth_rate([1.0, 0.0], covariance) == pytest.approx(
        0.0, rel=0.0, abs=1e-15
    )


# --------------------------------------------------------------------------------------
# Covariance validation
# --------------------------------------------------------------------------------------


def test_an_asymmetric_matrix_is_rejected() -> None:
    with pytest.raises(NotPositiveDefiniteError, match="not symmetric"):
        validate_covariance([[1.0, 0.5], [0.4, 1.0]])


def test_an_inconsistent_correlation_triple_is_rejected() -> None:
    """rho_12 = rho_13 = 0.9, rho_23 = -0.9 has eigenvalues (-0.8, 1.9, 1.9).

    Fixture from docs/research/portfolio-engine-specification.md, "Covariance
    conditioning". Nothing in this module repairs such a matrix; it refuses it, and
    the Higham projection that repairs it belongs to the conditioning layer.
    """
    matrix = np.array([[1.0, 0.9, 0.9], [0.9, 1.0, -0.9], [0.9, -0.9, 1.0]])
    eigenvalues = np.sort(np.linalg.eigvalsh(matrix))
    assert eigenvalues == pytest.approx([-0.8, 1.9, 1.9], rel=0.0, abs=1e-12)
    with pytest.raises(NotPositiveDefiniteError, match="positive definite"):
        validate_covariance(matrix)
