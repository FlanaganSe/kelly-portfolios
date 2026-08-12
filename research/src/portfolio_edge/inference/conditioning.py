"""Covariance and correlation conditioning.

Three independent problems, three tools:

* **Inconsistency.** A hand-specified correlation matrix need not be positive semi-definite,
  because pairwise values chosen one at a time need not be jointly realisable. The fix is
  Higham's (2002) alternating projections *with Dykstra's correction* —
  :func:`nearest_correlation_matrix`. Dropping the correction is not a harmless
  simplification: it converges to a measurably suboptimal point.
* **Noise.** The sample covariance matrix has rank at most ``min(T-1, N)``, so its smallest
  eigenvalues are noise and an inverse-covariance optimiser loads maximally on exactly those
  directions. Marchenko-Pastur bounds the noise spectrum —
  :func:`marchenko_pastur_bounds`, :func:`fit_marchenko_pastur_bulk`.
* **Instability.** Linear shrinkage toward a structured target trades a little bias for a
  large variance reduction — :func:`ledoit_wolf_shrinkage`.

References
----------
Higham, N. J. (2002). "Computing the nearest correlation matrix - a problem from finance."
*IMA Journal of Numerical Analysis* 22(3), 329-343. Algorithm 3.3.
Laloux, L. et al. (1999). "Noise dressing of financial correlation matrices."
*Physical Review Letters* 83, 1467. https://arxiv.org/pdf/cond-mat/9810255
Ledoit, O. and M. Wolf (2004). "Honey, I shrunk the sample covariance matrix."
*Journal of Portfolio Management* 30(4), 110-119. https://ledoit.net/honey.pdf
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "LedoitWolfResult",
    "MarchenkoPasturBounds",
    "MarchenkoPasturBulk",
    "NearestCorrelationResult",
    "fit_marchenko_pastur_bulk",
    "ledoit_wolf_shrinkage",
    "marchenko_pastur_bounds",
    "nearest_correlation_matrix",
    "ridge_and_renormalise",
]

FloatArray = NDArray[np.float64]


def _as_square_symmetric(a: NDArray[np.floating], name: str = "matrix") -> FloatArray:
    matrix = np.asarray(a, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"{name} must be square, got shape {matrix.shape}")
    if matrix.shape[0] < 1:
        raise ValueError(f"{name} must be non-empty")
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} contains non-finite values")
    if not np.allclose(matrix, matrix.T, atol=1e-12, rtol=0.0):
        raise ValueError(f"{name} must be symmetric")
    return 0.5 * (matrix + matrix.T)


def _project_psd(a: FloatArray) -> FloatArray:
    """``P_S``: project onto the positive semi-definite cone by clipping eigenvalues at 0."""
    eigenvalues, eigenvectors = np.linalg.eigh(a)
    clipped = np.clip(eigenvalues, 0.0, None)
    return (eigenvectors * clipped) @ eigenvectors.T


def _project_unit_diagonal(a: FloatArray) -> FloatArray:
    """``P_U``: project onto the set of symmetric matrices with unit diagonal."""
    out = a.copy()
    np.fill_diagonal(out, 1.0)
    return out


@dataclass(frozen=True)
class NearestCorrelationResult:
    """Nearest correlation matrix and the evidence that it converged."""

    matrix: FloatArray
    iterations: int
    converged: bool
    frobenius_distance: float
    """``||A - X||_F`` — the quantity the projection minimises."""
    min_eigenvalue: float
    """Smallest eigenvalue of the result. It is ~0, not positive: the answer is positive
    *semi*-definite, so :func:`ridge_and_renormalise` is required before any Cholesky."""
    used_dykstra: bool


def nearest_correlation_matrix(
    a: NDArray[np.floating],
    *,
    max_iterations: int = 200,
    tolerance: float = 1e-12,
    use_dykstra: bool = True,
) -> NearestCorrelationResult:
    """Nearest correlation matrix in the Frobenius norm — Higham (2002), Algorithm 3.3.

    The iteration, exactly as specified::

        dS = 0; Y = A
        repeat
            R  = Y - dS            # Dykstra's correction - not optional
            X  = P_S(R)            # clip eigenvalues at zero
            dS = X - R
            Y  = P_U(X)            # set unit diagonal

    ``use_dykstra=False`` runs the naive alternating projection ``Y <- P_U(P_S(Y))``. It is
    exposed only so that a test can show it converging to a *worse* point; never use it in
    production. On Higham's own example the naive iteration lands at Frobenius distance
    0.52791114 against 0.52779046 with the correction.

    The result is positive **semi**-definite — its smallest eigenvalue is zero to machine
    precision on inconsistent inputs — so pass it through :func:`ridge_and_renormalise`
    before any Cholesky factorisation.
    """
    matrix = _as_square_symmetric(a, "correlation matrix")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")

    delta_s = np.zeros_like(matrix)
    y = matrix.copy()
    x = matrix.copy()
    converged = False
    iterations = 0

    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        y_previous = y
        if use_dykstra:
            r = y - delta_s
            x = _project_psd(r)
            delta_s = x - r
        else:
            x = _project_psd(y)
        y = _project_unit_diagonal(x)
        if float(np.linalg.norm(y - y_previous, "fro")) <= tolerance:
            converged = True
            break

    eigenvalues = np.linalg.eigvalsh(y)
    return NearestCorrelationResult(
        matrix=y,
        iterations=iterations,
        converged=converged,
        frobenius_distance=float(np.linalg.norm(matrix - y, "fro")),
        min_eigenvalue=float(eigenvalues.min()),
        used_dykstra=use_dykstra,
    )


def ridge_and_renormalise(a: NDArray[np.floating], *, ridge: float = 1e-8) -> FloatArray:
    """Make a positive semi-definite correlation matrix strictly positive definite.

    Adds ``ridge * I`` and rescales to a unit diagonal via ``D^-1/2 C D^-1/2``. The result
    is a correlation matrix whose smallest eigenvalue is at least ``ridge / (1 + ridge)``,
    which is what a Cholesky factorisation needs. The distortion is ``O(ridge)``, so keep
    ``ridge`` at the smallest value that makes the factorisation succeed rather than
    treating it as a tuning knob.
    """
    matrix = _as_square_symmetric(a, "correlation matrix")
    if ridge <= 0.0:
        raise ValueError("ridge must be positive")
    ridged = matrix + ridge * np.eye(matrix.shape[0])
    scale = np.sqrt(np.diag(ridged))
    renormalised: FloatArray = ridged / np.outer(scale, scale)
    return renormalised


@dataclass(frozen=True)
class MarchenkoPasturBounds:
    """Edges of the Marchenko-Pastur noise band."""

    upper: float
    lower: float
    sigma_squared: float
    n_assets: int
    n_observations: int


def marchenko_pastur_bounds(
    n_assets: int, n_observations: int, *, sigma_squared: float = 1.0
) -> MarchenkoPasturBounds:
    """Noise-band edges ``lambda_pm = sigma^2 (1 +- sqrt(N/T))^2``.

    Applies to the **correlation** matrix, not the covariance matrix: the derivation
    assumes unit-variance entries. Eigenvalues inside ``[lambda_-, lambda_+]`` are
    indistinguishable from those of a pure-noise matrix of the same shape.

    ``sigma_squared`` should be *refitted on the bulk* rather than assumed to be 1, because
    the market mode absorbs variance that then does not appear in the noise band — the
    original Laloux calibration used 0.85. See :func:`fit_marchenko_pastur_bulk`.
    """
    if n_assets < 1 or n_observations < 1:
        raise ValueError("n_assets and n_observations must be positive")
    if sigma_squared <= 0.0:
        raise ValueError("sigma_squared must be positive")
    q = math.sqrt(n_assets / n_observations)
    return MarchenkoPasturBounds(
        upper=sigma_squared * (1.0 + q) ** 2,
        lower=sigma_squared * (1.0 - q) ** 2,
        sigma_squared=sigma_squared,
        n_assets=n_assets,
        n_observations=n_observations,
    )


@dataclass(frozen=True)
class MarchenkoPasturBulk:
    """Noise band with ``sigma^2`` refitted on the bulk of the observed spectrum."""

    bounds: MarchenkoPasturBounds
    eigenvalues: FloatArray
    """Eigenvalues of the correlation matrix, ascending."""
    n_above_upper: int
    """Count of eigenvalues above the upper edge — the informative directions."""
    iterations: int
    converged: bool


def fit_marchenko_pastur_bulk(
    correlation: NDArray[np.floating],
    n_observations: int,
    *,
    max_iterations: int = 100,
    tolerance: float = 1e-10,
) -> MarchenkoPasturBulk:
    """Refit ``sigma^2`` on the bulk of a correlation matrix's spectrum.

    The trace of a correlation matrix is exactly ``N``, so assuming ``sigma^2 = 1`` charges
    the whole variance to noise even though the market mode holds a large share of it. The
    fixed point implemented here is the standard remedy: iterate

    1. compute the band at the current ``sigma^2``;
    2. drop the eigenvalues above the upper edge (the market and sector modes);
    3. set ``sigma^2`` to the mean of the surviving eigenvalues;

    until ``sigma^2`` stops moving. On a strongly single-factor correlation matrix this
    lands near the Laloux calibration of 0.85; the exact value is data-dependent and must
    not be hardcoded.
    """
    matrix = _as_square_symmetric(correlation, "correlation matrix")
    n = matrix.shape[0]
    if n_observations < 1:
        raise ValueError("n_observations must be positive")
    if not np.allclose(np.diag(matrix), 1.0, atol=1e-8):
        raise ValueError("expected a correlation matrix with a unit diagonal")

    eigenvalues = np.linalg.eigvalsh(matrix)
    sigma_squared = 1.0
    converged = False
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        bounds = marchenko_pastur_bounds(n, n_observations, sigma_squared=sigma_squared)
        bulk = eigenvalues[eigenvalues <= bounds.upper]
        if bulk.size == 0:
            break
        updated = float(bulk.mean())
        if abs(updated - sigma_squared) <= tolerance:
            sigma_squared = updated
            converged = True
            break
        sigma_squared = updated

    bounds = marchenko_pastur_bounds(n, n_observations, sigma_squared=sigma_squared)
    return MarchenkoPasturBulk(
        bounds=bounds,
        eigenvalues=eigenvalues,
        n_above_upper=int(np.count_nonzero(eigenvalues > bounds.upper)),
        iterations=iterations,
        converged=converged,
    )


@dataclass(frozen=True)
class LedoitWolfResult:
    """Linear shrinkage ``Sigma_delta = (1 - delta) S + delta F``."""

    covariance: FloatArray
    shrinkage: float
    """``delta``, in ``[0, 1]``, learned inside the training window."""
    sample_covariance: FloatArray
    target: FloatArray
    """``F``, the constant-correlation target."""
    mean_correlation: float
    n_observations: int
    n_assets: int


def ledoit_wolf_shrinkage(
    returns: NDArray[np.floating], *, shrinkage: float | None = None
) -> LedoitWolfResult:
    """Ledoit-Wolf linear shrinkage toward a constant-correlation target.

    ``Sigma_delta = (1 - delta) S + delta F`` where ``S`` is the maximum-likelihood sample
    covariance (``1/T`` divisor, as the derivation requires) and ``F`` keeps every sample
    variance but replaces every correlation with the average sample correlation.

    ``delta`` is estimated from the data by the optimal-shrinkage formula
    ``delta = max(0, min(1, (pi - rho) / gamma / T))`` of Ledoit and Wolf (2004). Crucially
    it must be **learned inside the training window**: estimating it on data that includes
    the evaluation period leaks the answer into the estimator. This function therefore
    takes only one block of returns, and callers must pass the training slice.

    ``shrinkage`` overrides the estimate, which is useful for a fixed-delta comparison.
    """
    data = np.asarray(returns, dtype=np.float64)
    if data.ndim != 2:
        raise ValueError(f"returns must be T x N, got shape {data.shape}")
    t, n = data.shape
    if t < 2:
        raise ValueError("need at least two observations")
    if not np.all(np.isfinite(data)):
        raise ValueError("returns contains non-finite values")

    centred = data - data.mean(axis=0)
    sample = centred.T @ centred / t
    variances = np.diag(sample).copy()
    if np.any(variances <= 0.0):
        raise ValueError("an asset has zero sample variance")
    std = np.sqrt(variances)
    outer_std = np.outer(std, std)

    correlations = sample / outer_std
    mean_correlation = (float(correlations.sum()) - n) / (n * (n - 1)) if n > 1 else 1.0
    target = mean_correlation * outer_std
    np.fill_diagonal(target, variances)

    if shrinkage is None:
        squared = centred**2
        phi_matrix = squared.T @ squared / t - sample**2
        pi_hat = float(phi_matrix.sum())

        # theta[i, j] = (1/T) sum_t (x_it^2 - s_ii)(x_it x_jt - s_ij), which expands to
        # ((x^3)'x / T)_ij - s_ii s_ij. Ledoit's published Matlab writes this as
        # term1 - term2 - term3 + term4 where term3 and term4 are identical and cancel;
        # the two-term form below is the same quantity.
        term1 = (centred**3).T @ centred / t
        theta = term1 - variances[:, None] * sample
        np.fill_diagonal(theta, 0.0)
        rho_hat = float(np.trace(phi_matrix)) + mean_correlation * float(
            ((1.0 / std)[:, None] * std[None, :] * theta).sum()
        )

        gamma_hat = float(np.linalg.norm(sample - target, "fro") ** 2)
        if gamma_hat <= 0.0:
            delta = 0.0
        else:
            delta = float(min(1.0, max(0.0, (pi_hat - rho_hat) / gamma_hat / t)))
    else:
        if not 0.0 <= shrinkage <= 1.0:
            raise ValueError(f"shrinkage must lie in [0, 1], got {shrinkage}")
        delta = float(shrinkage)

    covariance = (1.0 - delta) * sample + delta * target
    covariance = 0.5 * (covariance + covariance.T)

    return LedoitWolfResult(
        covariance=covariance,
        shrinkage=delta,
        sample_covariance=sample,
        target=target,
        mean_correlation=mean_correlation,
        n_observations=t,
        n_assets=n,
    )
