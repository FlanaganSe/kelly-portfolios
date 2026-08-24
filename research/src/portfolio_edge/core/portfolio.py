"""Weights, weight drift, risk contributions, and equal-risk-contribution solving.

Risk contributions follow the definition used throughout the research framework,
``RC_i = w_i (Sigma w)_i / sqrt(w' Sigma w)``, which is Euler's decomposition of a
homogeneous-of-degree-one risk measure: the contributions sum *exactly* to
portfolio volatility. That identity is a property of the definition, not of any
particular portfolio, so it is the right invariant to assert in tests.

Equal risk contribution is a construction, not an edge. Three of its properties are
proved rather than empirical and are asserted in the tests: the solution is unique
for positive-definite ``Sigma``; for two assets it reduces exactly to
inverse-volatility weighting *independent of correlation*; and it is ordered
``sigma_MV <= sigma_ERC <= sigma_1/N``
(Maillard, Roncalli and Teiletche 2010, SSRN 1271972).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize

from ._types import FloatArray, FloatMatrix, FloatVector, as_float_array, as_square_matrix

DEFAULT_WEIGHT_TOLERANCE = 1e-9
"""Declared tolerance for the "weights sum to one" invariant."""


class WeightNormalisationError(ValueError):
    """Raised when a weight vector does not sum to one within the declared tolerance."""

    def __init__(self, total: float, tolerance: float) -> None:
        self.total = total
        self.tolerance = tolerance
        super().__init__(
            f"weights sum to {total!r}, which is outside 1 +/- {tolerance!r}"
        )


class NotPositiveDefiniteError(ValueError):
    """Raised when a covariance matrix is not symmetric positive definite."""


def equal_weights(n_assets: int) -> FloatArray:
    """The ``1/N`` portfolio."""
    if n_assets < 1:
        raise ValueError(f"n_assets must be positive, got {n_assets}")
    return np.full(n_assets, 1.0 / n_assets, dtype=np.float64)


def weights_sum(weights: FloatVector) -> float:
    """Sum of a weight vector."""
    return float(np.sum(as_float_array(weights, name="weights")))


def check_weights_sum_to_one(
    weights: FloatVector,
    *,
    tolerance: float = DEFAULT_WEIGHT_TOLERANCE,
) -> None:
    """Raise :class:`WeightNormalisationError` unless the weights sum to one."""
    if tolerance < 0.0:
        raise ValueError("tolerance cannot be negative")
    total = weights_sum(weights)
    if abs(total - 1.0) > tolerance:
        raise WeightNormalisationError(total, tolerance)


def normalise_weights(
    weights: FloatVector,
    *,
    tolerance: float = DEFAULT_WEIGHT_TOLERANCE,
) -> FloatArray:
    """Rescale weights to sum to one.

    ``tolerance`` guards the divisor, not the result: a vector summing to within
    ``tolerance`` of zero cannot be normalised at all and raises.
    """
    array = as_float_array(weights, name="weights")
    total = float(np.sum(array))
    if abs(total) <= max(tolerance, 0.0):
        raise WeightNormalisationError(total, tolerance)
    return np.asarray(array / total, dtype=np.float64)


def drift_weights(weights: FloatVector, asset_returns: FloatVector) -> FloatArray:
    """Weights after one period of buy-and-hold drift.

    ``w_i (1 + r_i) / sum_j w_j (1 + r_j)``. This is what "no rebalancing" means at
    the weight level, and the drifting buy-and-hold portfolio is a mandatory
    baseline in the framework's construction tournament.
    """
    w = as_float_array(weights, name="weights")
    r = as_float_array(asset_returns, name="asset_returns")
    if w.shape != r.shape:
        raise ValueError("weights and asset_returns must have the same length")
    grown = w * (1.0 + r)
    total = float(np.sum(grown))
    if total <= 0.0:
        raise ValueError(
            f"buy-and-hold drift produced a non-positive portfolio value {total!r}"
        )
    return np.asarray(grown / total, dtype=np.float64)


def validate_covariance(
    covariance: FloatMatrix, *, symmetry_tolerance: float = 1e-12
) -> FloatArray:
    """Return the matrix as float64 after checking symmetry and positive definiteness."""
    matrix = as_square_matrix(covariance, name="covariance")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=symmetry_tolerance):
        raise NotPositiveDefiniteError("covariance matrix is not symmetric")
    try:
        np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError as error:
        raise NotPositiveDefiniteError(
            "covariance matrix is not positive definite"
        ) from error
    return matrix


def portfolio_variance(weights: FloatVector, covariance: FloatMatrix) -> float:
    """``w' Sigma w``."""
    w = as_float_array(weights, name="weights")
    matrix = as_square_matrix(covariance, name="covariance")
    if matrix.shape[0] != w.size:
        raise ValueError("weights and covariance must have matching dimensions")
    return float(w @ matrix @ w)


def portfolio_volatility(weights: FloatVector, covariance: FloatMatrix) -> float:
    """``sqrt(w' Sigma w)``."""
    variance = portfolio_variance(weights, covariance)
    if variance < 0.0:
        raise NotPositiveDefiniteError(
            f"portfolio variance is negative ({variance!r}); the covariance matrix "
            "is not positive semi-definite"
        )
    return math.sqrt(variance)


def marginal_risk_contributions(weights: FloatVector, covariance: FloatMatrix) -> FloatArray:
    """``(Sigma w)_i / sqrt(w' Sigma w)`` — the derivative of volatility in ``w_i``."""
    w = as_float_array(weights, name="weights")
    matrix = as_square_matrix(covariance, name="covariance")
    sigma = portfolio_volatility(w, matrix)
    if sigma <= 0.0:
        raise ValueError("risk contributions are undefined at zero portfolio volatility")
    return np.asarray((matrix @ w) / sigma, dtype=np.float64)


def risk_contributions(weights: FloatVector, covariance: FloatMatrix) -> FloatArray:
    """``RC_i = w_i (Sigma w)_i / sqrt(w' Sigma w)``, summing to portfolio volatility."""
    w = as_float_array(weights, name="weights")
    return np.asarray(w * marginal_risk_contributions(w, covariance), dtype=np.float64)


def relative_risk_contributions(weights: FloatVector, covariance: FloatMatrix) -> FloatArray:
    """Risk contributions as fractions of portfolio volatility; they sum to one."""
    contributions = risk_contributions(weights, covariance)
    return np.asarray(contributions / float(np.sum(contributions)), dtype=np.float64)


def inverse_volatility_weights(covariance: FloatMatrix) -> FloatArray:
    """Weights proportional to ``1 / sigma_i``, ignoring correlation entirely."""
    matrix = validate_covariance(covariance)
    sigmas = np.sqrt(np.diag(matrix))
    return normalise_weights(1.0 / sigmas)


def equal_risk_contribution_weights(
    covariance: FloatMatrix,
    *,
    tolerance: float = 1e-12,
    max_iterations: int = 200,
) -> FloatArray:
    """Long-only weights equalising ``RC_i``, by Newton descent on the log barrier.

    The ERC portfolio is the normalised minimiser of the strictly convex
    ``f(x) = 0.5 x' Sigma x - sum(ln x_i)`` on ``x > 0``: its stationarity condition
    ``(Sigma x)_i = 1 / x_i`` makes every ``x_i (Sigma x)_i`` equal, which is exactly
    equal risk contribution after normalising. Strict convexity for positive-definite
    ``Sigma`` is why the solution is unique.
    """
    matrix = validate_covariance(covariance)
    n = matrix.shape[0]
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")

    sigmas = np.sqrt(np.diag(matrix))
    x = np.asarray(1.0 / (sigmas * n), dtype=np.float64)

    def objective(vector: FloatArray) -> float:
        return float(0.5 * vector @ matrix @ vector - np.sum(np.log(vector)))

    value = objective(x)
    for _ in range(max_iterations):
        gradient = matrix @ x - 1.0 / x
        if float(np.max(np.abs(gradient))) <= tolerance:
            break
        hessian = matrix + np.diag(1.0 / x**2)
        step = np.linalg.solve(hessian, -gradient)
        scale = 1.0
        while np.any(x + scale * step <= 0.0):
            scale *= 0.5
            if scale < 1e-18:
                raise RuntimeError("ERC line search collapsed; covariance may be ill-conditioned")
        candidate = x + scale * step
        candidate_value = objective(candidate)
        while candidate_value > value + 1e-4 * scale * float(gradient @ step):
            scale *= 0.5
            if scale < 1e-18:
                break
            candidate = x + scale * step
            candidate_value = objective(candidate)
        x, value = candidate, candidate_value
    else:
        raise RuntimeError(
            f"equal risk contribution did not converge in {max_iterations} iterations"
        )
    return normalise_weights(x)


def minimum_variance_weights(
    covariance: FloatMatrix,
    *,
    long_only: bool = True,
) -> FloatArray:
    """Minimum-variance weights, fully invested.

    Unconstrained, this is the closed form ``Sigma^-1 1 / (1' Sigma^-1 1)``. Long-only
    it is a small convex QP solved with SLSQP; the no-short constraint doubles as
    implicit covariance shrinkage (Jagannathan and Ma 2003).
    """
    matrix = validate_covariance(covariance)
    n = matrix.shape[0]
    ones = np.ones(n, dtype=np.float64)
    inverse_times_ones = np.linalg.solve(matrix, ones)
    unconstrained = np.asarray(
        inverse_times_ones / float(ones @ inverse_times_ones), dtype=np.float64
    )
    if not long_only:
        return unconstrained
    if np.all(unconstrained >= 0.0):
        return unconstrained

    start = equal_weights(n)
    result = minimize(
        lambda w: float(w @ matrix @ w),
        start,
        jac=lambda w: np.asarray(2.0 * matrix @ w, dtype=np.float64),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}],
        options={"maxiter": 500, "ftol": 1e-14},
    )
    if not result.success:
        raise RuntimeError(f"long-only minimum variance failed: {result.message}")
    return normalise_weights(np.asarray(result.x, dtype=np.float64))


def excess_growth_rate(weights: FloatVector, covariance: FloatMatrix) -> float:
    """``0.5 * (sum_i w_i sigma_i**2 - sigma_p**2)`` — the excess-growth term.

    Non-negative for long-only weights. It compares a rebalanced portfolio with the
    *weighted log growth of its components*, which is not the return of any portfolio
    one can hold; it is therefore not evidence that rebalancing beats buy-and-hold.
    """
    w = as_float_array(weights, name="weights")
    matrix = as_square_matrix(covariance, name="covariance")
    if matrix.shape[0] != w.size:
        raise ValueError("weights and covariance must have matching dimensions")
    weighted_variance = float(w @ np.diag(matrix))
    return 0.5 * (weighted_variance - portfolio_variance(w, matrix))
