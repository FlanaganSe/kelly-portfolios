"""Tests for correlation/covariance conditioning.

Fixture sources are cited beside each assertion; all come from
``docs/research/portfolio-engine-specification.md``, "Covariance conditioning", which in
turn cites Higham (2002) and Laloux et al. (1999). Every one was recomputed here from the
algorithm and the closed form before being asserted.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.inference.conditioning import (
    fit_marchenko_pastur_bulk,
    ledoit_wolf_shrinkage,
    marchenko_pastur_bounds,
    nearest_correlation_matrix,
    ridge_and_renormalise,
)

# Fixture (a): the inconsistent triple. rho_12 = rho_13 = 0.9, rho_23 = -0.9.
# Source: docs/research/portfolio-engine-specification.md, "Covariance conditioning".
INCONSISTENT_TRIPLE = np.array(
    [
        [1.0, 0.9, 0.9],
        [0.9, 1.0, -0.9],
        [0.9, -0.9, 1.0],
    ]
)

# Fixture (b): Higham's own example, [[1,1,0],[1,1,1],[0,1,1]].
# Source: same page; Higham (2002), https://eprints.maths.manchester.ac.uk/232/1/paper.pdf
HIGHAM_EXAMPLE = np.array(
    [
        [1.0, 1.0, 0.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]
)


# --------------------------------------------------------------------------------------
# Higham (2002) Algorithm 3.3 with Dykstra's correction
# --------------------------------------------------------------------------------------


def test_inconsistent_triple_has_the_published_spectrum() -> None:
    """Eigenvalues (-0.8, 1.9, 1.9): the matrix is not positive semi-definite."""
    assert np.linalg.eigvalsh(INCONSISTENT_TRIPLE) == pytest.approx([-0.8, 1.9, 1.9])


def test_inconsistent_triple_projects_to_the_published_answer() -> None:
    """Projects to rho_12 = rho_13 = 0.5, rho_23 = -0.5, eigenvalues (0, 1.5, 1.5)."""
    result = nearest_correlation_matrix(INCONSISTENT_TRIPLE)
    assert result.converged
    expected = np.array([[1.0, 0.5, 0.5], [0.5, 1.0, -0.5], [0.5, -0.5, 1.0]])
    assert result.matrix == pytest.approx(expected, abs=1e-9)
    assert np.linalg.eigvalsh(result.matrix) == pytest.approx([0.0, 1.5, 1.5], abs=1e-9)


def test_higham_example_has_the_published_spectrum() -> None:
    """Eigenvalues (1 - sqrt 2, 1, 1 + sqrt 2)."""
    assert np.linalg.eigvalsh(HIGHAM_EXAMPLE) == pytest.approx(
        [1.0 - math.sqrt(2.0), 1.0, 1.0 + math.sqrt(2.0)]
    )


def test_higham_example_converges_to_the_published_answer() -> None:
    """Off-diagonals 0.760690 and 0.157298, eigenvalues (0, 0.84270189, 2.15729811).

    The paper itself publishes 0.7607 and 0.1573; the six-decimal figures are from the
    specification page and are reproduced here to 1e-7.
    """
    result = nearest_correlation_matrix(HIGHAM_EXAMPLE)
    assert result.converged
    matrix = result.matrix
    assert matrix[0, 1] == pytest.approx(0.760690, abs=5e-7)
    assert matrix[1, 2] == pytest.approx(0.760690, abs=5e-7)
    assert matrix[0, 2] == pytest.approx(0.157298, abs=5e-7)
    assert np.linalg.eigvalsh(matrix) == pytest.approx([0.0, 0.84270189, 2.15729811], abs=1e-7)
    assert np.diag(matrix) == pytest.approx([1.0, 1.0, 1.0])


def test_dropping_dykstras_correction_converges_to_a_worse_point() -> None:
    """Frobenius distance 0.52791114 (naive) against 0.52779046 (Dykstra) on fixture (b).

    Source: docs/research/portfolio-engine-specification.md, "Covariance conditioning".
    This is the assertion that makes Dykstra's correction non-optional: the naive
    alternating projection still lands on a correlation matrix, just not the nearest one.
    """
    dykstra = nearest_correlation_matrix(HIGHAM_EXAMPLE, use_dykstra=True)
    naive = nearest_correlation_matrix(HIGHAM_EXAMPLE, use_dykstra=False, max_iterations=5000)
    assert dykstra.frobenius_distance == pytest.approx(0.52779046, abs=5e-9)
    assert naive.frobenius_distance == pytest.approx(0.52791114, abs=5e-9)
    assert naive.frobenius_distance > dykstra.frobenius_distance
    # The naive fixed point is a genuinely different matrix, not a convergence artefact.
    assert naive.matrix[0, 1] == pytest.approx(0.76300194, abs=1e-7)
    assert naive.matrix[0, 2] == pytest.approx(0.16434392, abs=1e-7)


def test_a_valid_correlation_matrix_is_returned_unchanged() -> None:
    valid = np.array([[1.0, 0.3, 0.1], [0.3, 1.0, -0.2], [0.1, -0.2, 1.0]])
    result = nearest_correlation_matrix(valid)
    assert result.matrix == pytest.approx(valid, abs=1e-12)
    assert result.frobenius_distance == pytest.approx(0.0, abs=1e-12)


def test_the_projection_result_is_only_positive_semi_definite() -> None:
    """Which is why a ridge is required before any Cholesky factorisation."""
    result = nearest_correlation_matrix(INCONSISTENT_TRIPLE)
    assert result.min_eigenvalue == pytest.approx(0.0, abs=1e-9)
    with pytest.raises(np.linalg.LinAlgError):
        np.linalg.cholesky(result.matrix - 1e-12 * np.eye(3))


def test_ridge_and_renormalise_makes_the_result_factorisable() -> None:
    result = nearest_correlation_matrix(INCONSISTENT_TRIPLE)
    conditioned = ridge_and_renormalise(result.matrix, ridge=1e-8)
    assert np.diag(conditioned) == pytest.approx([1.0, 1.0, 1.0])
    assert float(np.linalg.eigvalsh(conditioned).min()) > 0.0
    np.linalg.cholesky(conditioned)  # must not raise
    # The distortion is O(ridge).
    assert conditioned == pytest.approx(result.matrix, abs=1e-7)


def test_nearest_correlation_matrix_rejects_asymmetric_input() -> None:
    with pytest.raises(ValueError, match="symmetric"):
        nearest_correlation_matrix(np.array([[1.0, 0.5], [0.2, 1.0]]))
    with pytest.raises(ValueError, match="square"):
        nearest_correlation_matrix(np.ones((2, 3)))


# --------------------------------------------------------------------------------------
# Marchenko-Pastur
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n_assets", "n_observations", "upper", "lower"),
    [
        # Source: docs/research/portfolio-engine-specification.md, "Covariance conditioning",
        # citing Laloux et al. (1999), https://arxiv.org/pdf/cond-mat/9810255
        (50, 100, 2.914214, 0.085786),
        (100, 1000, 1.732456, 0.467544),
        (500, 500, 4.0, 0.0),
    ],
)
def test_marchenko_pastur_bounds_reproduce_the_published_fixtures(
    n_assets: int, n_observations: int, upper: float, lower: float
) -> None:
    bounds = marchenko_pastur_bounds(n_assets, n_observations)
    assert bounds.upper == pytest.approx(upper, abs=5e-7)
    assert bounds.lower == pytest.approx(lower, abs=5e-7)


def test_marchenko_pastur_scales_linearly_in_sigma_squared() -> None:
    """The original Laloux calibration used sigma^2 = 0.85 rather than 1."""
    unit = marchenko_pastur_bounds(50, 100)
    calibrated = marchenko_pastur_bounds(50, 100, sigma_squared=0.85)
    assert calibrated.upper == pytest.approx(0.85 * unit.upper)
    assert calibrated.lower == pytest.approx(0.85 * unit.lower)
    assert calibrated.sigma_squared == 0.85


def test_pure_noise_correlation_eigenvalues_sit_inside_the_band() -> None:
    """Sanity check on the band itself, using a correlation matrix of independent columns."""
    rng = np.random.default_rng(5)
    n, t = 40, 400
    data = rng.standard_normal((t, n))
    correlation = np.asarray(np.corrcoef(data, rowvar=False), dtype=float)
    bounds = marchenko_pastur_bounds(n, t)
    eigenvalues = np.linalg.eigvalsh(correlation)
    assert float(eigenvalues.max()) < bounds.upper * 1.15
    assert int(np.count_nonzero(eigenvalues > bounds.upper)) <= 2


def test_bulk_refit_lowers_sigma_squared_when_a_market_mode_is_present() -> None:
    """The market mode absorbs variance, so assuming sigma^2 = 1 overstates the band.

    One common factor holding 30% of each asset's variance plus idiosyncratic noise. The
    refitted sigma^2 must fall well below 1 and the fitted band must isolate the single
    market eigenvalue.
    """
    rng = np.random.default_rng(6)
    n, t, w = 60, 600, 0.30
    factor = rng.standard_normal((t, 1))
    data = math.sqrt(w) * factor + math.sqrt(1.0 - w) * rng.standard_normal((t, n))
    correlation = np.asarray(np.corrcoef(data, rowvar=False), dtype=float)

    fitted = fit_marchenko_pastur_bulk(correlation, t)
    assert fitted.converged
    assert 0.5 < fitted.bounds.sigma_squared < 0.95
    assert fitted.bounds.upper < marchenko_pastur_bounds(n, t).upper
    assert fitted.n_above_upper == 1  # the market mode alone
    assert fitted.eigenvalues.size == n


def test_bulk_refit_leaves_sigma_squared_near_one_for_pure_noise() -> None:
    rng = np.random.default_rng(7)
    n, t = 50, 1000
    correlation = np.asarray(np.corrcoef(rng.standard_normal((t, n)), rowvar=False), dtype=float)
    fitted = fit_marchenko_pastur_bulk(correlation, t)
    assert fitted.bounds.sigma_squared == pytest.approx(1.0, abs=0.12)


def test_bulk_refit_requires_a_correlation_matrix() -> None:
    covariance = np.diag([4.0, 9.0, 1.0])
    with pytest.raises(ValueError, match="unit diagonal"):
        fit_marchenko_pastur_bulk(covariance, 100)


# --------------------------------------------------------------------------------------
# Ledoit-Wolf linear shrinkage
# --------------------------------------------------------------------------------------


def test_shrinkage_is_the_stated_convex_combination() -> None:
    """Sigma_delta = (1 - delta) S + delta F, checked at an explicit delta."""
    rng = np.random.default_rng(8)
    data = rng.standard_normal((200, 6))
    result = ledoit_wolf_shrinkage(data, shrinkage=0.4)
    expected = 0.6 * result.sample_covariance + 0.4 * result.target
    assert result.covariance == pytest.approx(expected)
    assert result.shrinkage == 0.4


def test_the_target_keeps_variances_and_averages_correlations() -> None:
    rng = np.random.default_rng(9)
    data = rng.standard_normal((300, 5))
    result = ledoit_wolf_shrinkage(data)
    assert np.diag(result.target) == pytest.approx(np.diag(result.sample_covariance))
    std = np.sqrt(np.diag(result.sample_covariance))
    implied = result.target / np.outer(std, std)
    off_diagonal = implied[~np.eye(5, dtype=bool)]
    assert off_diagonal == pytest.approx(np.full(20, result.mean_correlation))


def _factor_returns(n_observations: int, n_assets: int, seed: int) -> np.ndarray:
    """Three-factor returns with dispersed loadings and volatilities.

    A structured covariance is required here: on i.i.d. unit-variance data the sample
    covariance and the constant-correlation target are both essentially the identity, so
    the optimal shrinkage saturates at 1 and carries no information.
    """
    rng = np.random.default_rng(seed)
    factors = rng.standard_normal((n_observations, 3))
    loadings = rng.uniform(0.3, 1.0, size=(3, n_assets))
    volatilities = rng.uniform(0.5, 2.0, size=n_assets)
    idiosyncratic = rng.standard_normal((n_observations, n_assets))
    return (factors @ loadings + idiosyncratic) * volatilities


def test_learned_shrinkage_is_a_valid_intensity_and_rises_as_t_falls() -> None:
    """delta is learned inside the window; a shorter window needs more shrinkage."""
    data = _factor_returns(2000, 30, seed=10)
    long_delta = ledoit_wolf_shrinkage(data).shrinkage
    medium_delta = ledoit_wolf_shrinkage(data[:100]).shrinkage
    short_delta = ledoit_wolf_shrinkage(data[:60]).shrinkage
    assert 0.0 <= long_delta <= 1.0
    assert 0.0 <= short_delta <= 1.0
    assert long_delta < medium_delta < short_delta


def test_shrinkage_improves_conditioning_when_assets_outnumber_observations() -> None:
    """T <= N makes the sample covariance exactly singular; shrinkage repairs the rank."""
    data = _factor_returns(50, 60, seed=11)
    result = ledoit_wolf_shrinkage(data)
    sample_eigenvalues = np.linalg.eigvalsh(result.sample_covariance)
    shrunk_eigenvalues = np.linalg.eigvalsh(result.covariance)
    assert float(sample_eigenvalues.min()) < 1e-8
    assert float(shrunk_eigenvalues.min()) > 1e-3
    assert result.shrinkage > 0.0
    np.linalg.cholesky(result.covariance)  # must not raise


def test_shrunk_covariance_is_symmetric_and_reports_its_window() -> None:
    rng = np.random.default_rng(12)
    data = rng.standard_normal((120, 8))
    result = ledoit_wolf_shrinkage(data)
    assert result.covariance == pytest.approx(result.covariance.T)
    assert result.n_observations == 120
    assert result.n_assets == 8


def test_shrinkage_rejects_bad_input() -> None:
    rng = np.random.default_rng(13)
    with pytest.raises(ValueError, match="T x N"):
        ledoit_wolf_shrinkage(rng.standard_normal(50))
    with pytest.raises(ValueError, match="shrinkage"):
        ledoit_wolf_shrinkage(rng.standard_normal((50, 3)), shrinkage=1.5)
    with pytest.raises(ValueError, match="zero sample variance"):
        ledoit_wolf_shrinkage(np.column_stack([np.ones(50), rng.standard_normal(50)]))
