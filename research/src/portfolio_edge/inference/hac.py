"""Heteroskedasticity- and autocorrelation-consistent (HAC) standard errors.

Return series are autocorrelated, fat-tailed and heteroskedastic, so an i.i.d. standard
error understates uncertainty for a mean and for regression coefficients alike. This
module implements the Newey-West (1987) Bartlett-kernel sandwich estimator for both.

Bandwidth rule
--------------
Unless a lag count is passed explicitly, the bandwidth is the Newey-West (1994)
rule of thumb ``L = floor(4 * (T / 100) ** (2/9))`` — see :func:`newey_west_lag_count`.
It is deterministic in the sample size only, which is its virtue (nothing is tuned on the
data being tested) and its limitation (it ignores the observed persistence). Pass
``n_lags`` when the persistence is known: for monthly returns with a documented AR(1)
coefficient, ``L`` should be at least the horizon over which that dependence matters, and
for overlapping ``q``-period returns ``L >= q - 1`` is mandatory.

The Bartlett kernel weight is ``w_j = 1 - j / (L + 1)`` for ``j = 1..L``, which guarantees
a positive semi-definite long-run variance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

__all__ = [
    "HacMeanResult",
    "HacOlsResult",
    "bartlett_weights",
    "hac_mean",
    "hac_ols",
    "long_run_variance",
    "newey_west_lag_count",
]

FloatArray = NDArray[np.float64]


def newey_west_lag_count(n_observations: int) -> int:
    """Newey-West (1994) automatic bandwidth ``floor(4 * (T / 100) ** (2/9))``.

    Returned value is clipped to ``[0, T - 1]``. At ``T = 100`` this is 4; at ``T = 1000``
    it is 6; at ``T = 12`` it is 2.
    """
    if n_observations < 1:
        raise ValueError("n_observations must be positive")
    raw = math.floor(4.0 * (n_observations / 100.0) ** (2.0 / 9.0))
    return int(min(max(raw, 0), n_observations - 1))


def bartlett_weights(n_lags: int) -> FloatArray:
    """Bartlett kernel weights ``w_j = 1 - j / (L + 1)`` for ``j = 1 .. L``."""
    if n_lags < 0:
        raise ValueError("n_lags must be non-negative")
    lags = np.arange(1, n_lags + 1, dtype=np.float64)
    return 1.0 - lags / (n_lags + 1.0)


def _as_series(x: NDArray[np.floating] | list[float]) -> FloatArray:
    series = np.asarray(x, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"expected a one-dimensional series, got shape {series.shape}")
    if series.size < 2:
        raise ValueError("need at least two observations")
    if not np.all(np.isfinite(series)):
        raise ValueError("series contains non-finite values")
    return series


def long_run_variance(u: NDArray[np.floating] | list[float], *, n_lags: int | None = None) -> float:
    """Newey-West long-run variance ``S = gamma_0 + 2 sum_j w_j gamma_j``.

    ``u`` is used as supplied — it is *not* demeaned here, because for a regression score
    the mean is already zero by construction and subtracting a sample mean would be wrong.
    Use :func:`hac_mean` for the mean of a series, which demeans first.
    """
    series = _as_series(u)
    t = series.size
    lags = newey_west_lag_count(t) if n_lags is None else n_lags
    if not 0 <= lags < t:
        raise ValueError(f"n_lags must lie in [0, {t - 1}], got {lags}")
    total = float(np.dot(series, series) / t)
    for j, weight in enumerate(bartlett_weights(lags), start=1):
        gamma_j = float(np.dot(series[j:], series[:-j]) / t)
        total += 2.0 * float(weight) * gamma_j
    return total


@dataclass(frozen=True)
class HacMeanResult:
    """HAC inference for the mean of a single series."""

    mean: float
    standard_error: float
    t_statistic: float
    p_value: float
    long_run_variance: float
    n_lags: int
    n_observations: int


def hac_mean(x: NDArray[np.floating] | list[float], *, n_lags: int | None = None) -> HacMeanResult:
    """HAC standard error for a sample mean.

    ``SE = sqrt(S / T)`` where ``S`` is the Newey-West long-run variance of the demeaned
    series. Under no autocorrelation this collapses to the usual ``sd / sqrt(T)`` up to the
    ``1/T`` versus ``1/(T-1)`` divisor.

    The reported p-value is two-sided and normal, not Student-t: the HAC sandwich has no
    exact finite-sample distribution, so a t reference would be false precision.
    """
    series = _as_series(x)
    t = series.size
    lags = newey_west_lag_count(t) if n_lags is None else n_lags
    centred = series - series.mean()
    s = long_run_variance(centred, n_lags=lags)
    variance = max(s, 0.0) / t
    se = math.sqrt(variance)
    mean = float(series.mean())
    t_stat = mean / se if se > 0.0 else math.nan
    p_value = float(2.0 * norm.sf(abs(t_stat))) if math.isfinite(t_stat) else math.nan
    return HacMeanResult(
        mean=mean,
        standard_error=se,
        t_statistic=t_stat,
        p_value=p_value,
        long_run_variance=s,
        n_lags=lags,
        n_observations=t,
    )


@dataclass(frozen=True)
class HacOlsResult:
    """OLS coefficients with a Newey-West HAC covariance matrix."""

    coefficients: FloatArray
    covariance: FloatArray
    standard_errors: FloatArray
    t_statistics: FloatArray
    p_values: FloatArray
    residuals: FloatArray
    n_lags: int
    n_observations: int
    n_parameters: int
    dof_correction: bool


def hac_ols(
    y: NDArray[np.floating] | list[float],
    x: NDArray[np.floating],
    *,
    n_lags: int | None = None,
    add_constant: bool = True,
    dof_correction: bool = False,
) -> HacOlsResult:
    """OLS with Newey-West HAC standard errors.

    The sandwich is ``(X'X)^-1 S (X'X)^-1`` with

    ``S = sum_t x_t u_t u_t x_t' + sum_{j=1..L} w_j (Gamma_j + Gamma_j')``,
    ``Gamma_j = sum_t x_t u_t u_{t-j} x_{t-j}'``.

    ``dof_correction=True`` multiplies the covariance by ``T / (T - k)``. It is off by
    default because the asymptotic theory does not call for it; it is offered only because
    some libraries apply it and comparisons otherwise appear to disagree.

    Rows must be in chronological order. Shuffling them silently destroys the estimator.
    """
    response = _as_series(y)
    design = np.asarray(x, dtype=np.float64)
    if design.ndim == 1:
        design = design[:, None]
    if design.ndim != 2:
        raise ValueError(f"design matrix must be 1- or 2-dimensional, got shape {design.shape}")
    if design.shape[0] != response.size:
        raise ValueError(
            f"design has {design.shape[0]} rows but response has {response.size} observations"
        )
    if not np.all(np.isfinite(design)):
        raise ValueError("design matrix contains non-finite values")
    if add_constant:
        design = np.column_stack([np.ones(response.size), design])

    t, k = design.shape
    if t <= k:
        raise ValueError(f"need more observations ({t}) than parameters ({k})")
    lags = newey_west_lag_count(t) if n_lags is None else n_lags
    if not 0 <= lags < t:
        raise ValueError(f"n_lags must lie in [0, {t - 1}], got {lags}")

    xtx = design.T @ design
    xtx_inv = np.linalg.inv(xtx)
    beta = xtx_inv @ (design.T @ response)
    residuals = response - design @ beta

    scores = design * residuals[:, None]
    s_matrix = scores.T @ scores
    for j, weight in enumerate(bartlett_weights(lags), start=1):
        gamma_j = scores[j:].T @ scores[:-j]
        s_matrix = s_matrix + float(weight) * (gamma_j + gamma_j.T)

    covariance = xtx_inv @ s_matrix @ xtx_inv
    if dof_correction:
        covariance = covariance * (t / (t - k))
    covariance = 0.5 * (covariance + covariance.T)

    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_stats = np.where(standard_errors > 0.0, beta / standard_errors, np.nan)
    p_values = 2.0 * np.asarray(norm.sf(np.abs(t_stats)), dtype=np.float64)

    return HacOlsResult(
        coefficients=beta,
        covariance=covariance,
        standard_errors=standard_errors,
        t_statistics=t_stats,
        p_values=p_values,
        residuals=residuals,
        n_lags=lags,
        n_observations=t,
        n_parameters=k,
        dof_correction=dof_correction,
    )
