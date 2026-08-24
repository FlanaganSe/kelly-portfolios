"""Corrections for search: family-wise error, false discovery rate, and data snooping.

Four procedures, in increasing order of what they assume and what they buy:

* :func:`holm_bonferroni` — family-wise error rate, valid under arbitrary dependence.
* :func:`benjamini_hochberg` — false discovery rate, valid under independence or positive
  regression dependence.
* :func:`reality_check` — White's (2000) bootstrap Reality Check for the best of ``M``
  strategies, which respects the cross-sectional dependence between strategies because it
  resamples the *same* time index for all of them.
* :func:`spa_test` — Hansen's (2005) Superior Predictive Ability test, a studentised
  Reality Check with recentring that stops poor strategies from inflating the null.

The two bootstrap tests resample with the stationary bootstrap from
:mod:`portfolio_edge.inference.bootstrap`, so serial dependence in the performance series
survives the resample.

References
----------
White, H. (2000). "A Reality Check for Data Snooping." *Econometrica* 68(5), 1097-1126.
Hansen, P. R. (2005). "A Test for Superior Predictive Ability." *JBES* 23(4), 365-380.
Holm, S. (1979). *Scandinavian Journal of Statistics* 6(2), 65-70.
Benjamini, Y. and Y. Hochberg (1995). *JRSS B* 57(1), 289-300.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.inference.bootstrap import optimal_block_length, stationary_bootstrap_indices

__all__ = [
    "MultipleTestingResult",
    "RealityCheckResult",
    "Recentring",
    "benjamini_hochberg",
    "holm_bonferroni",
    "reality_check",
    "spa_test",
]

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]

Recentring = Literal["consistent", "lower", "upper"]


@dataclass(frozen=True)
class MultipleTestingResult:
    """Adjusted p-values and rejection flags, in the caller's original ordering."""

    p_values: FloatArray
    adjusted_p_values: FloatArray
    rejected: BoolArray
    alpha: float
    method: str

    @property
    def n_rejected(self) -> int:
        return int(np.count_nonzero(self.rejected))


def _as_p_values(p_values: NDArray[np.floating] | list[float]) -> FloatArray:
    values = np.asarray(p_values, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"p_values must be one-dimensional, got shape {values.shape}")
    if values.size == 0:
        raise ValueError("p_values must not be empty")
    if not np.all(np.isfinite(values)):
        raise ValueError("p_values contains non-finite values")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("p_values must lie in [0, 1]")
    return values


def _check_alpha(alpha: float) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie in (0, 1), got {alpha}")


def holm_bonferroni(
    p_values: NDArray[np.floating] | list[float], *, alpha: float = 0.05
) -> MultipleTestingResult:
    """Holm's step-down family-wise error rate correction.

    Sort ascending; the adjusted p-value of the ``i``-th smallest (1-based) is the running
    maximum of ``(M - i + 1) * p_(i)``, capped at 1. Rejection at level ``alpha`` is
    ``adjusted <= alpha``, which is equivalent to the sequential stopping rule and enforces
    the step-down monotonicity that a raw Bonferroni comparison would violate.

    Uniformly more powerful than Bonferroni and valid under arbitrary dependence between
    the tests, which is the property that matters when strategies share data.
    """
    _check_alpha(alpha)
    values = _as_p_values(p_values)
    m = values.size
    order = np.argsort(values, kind="stable")
    sorted_p = values[order]
    multipliers = np.arange(m, 0, -1, dtype=np.float64)
    adjusted_sorted = np.clip(np.maximum.accumulate(sorted_p * multipliers), 0.0, 1.0)
    adjusted = np.empty(m, dtype=np.float64)
    adjusted[order] = adjusted_sorted
    return MultipleTestingResult(
        p_values=values,
        adjusted_p_values=adjusted,
        rejected=adjusted <= alpha,
        alpha=alpha,
        method="holm-bonferroni",
    )


def benjamini_hochberg(
    p_values: NDArray[np.floating] | list[float], *, alpha: float = 0.05
) -> MultipleTestingResult:
    """Benjamini-Hochberg false discovery rate control.

    Sort ascending; the adjusted p-value of the ``i``-th smallest (1-based) is the running
    minimum, taken from the largest downwards, of ``(M / i) * p_(i)``, capped at 1.

    Controls the expected proportion of false discoveries among rejections, not the
    probability of any false discovery, so it rejects more than Holm and promises less.
    Valid under independence and under positive regression dependence; for arbitrary
    dependence the Benjamini-Yekutieli ``log`` penalty would be required and is not
    implemented here.
    """
    _check_alpha(alpha)
    values = _as_p_values(p_values)
    m = values.size
    order = np.argsort(values, kind="stable")
    sorted_p = values[order]
    ranks = np.arange(1, m + 1, dtype=np.float64)
    scaled = sorted_p * m / ranks
    adjusted_sorted = np.minimum.accumulate(scaled[::-1])[::-1]
    adjusted_sorted = np.clip(adjusted_sorted, 0.0, 1.0)
    adjusted = np.empty(m, dtype=np.float64)
    adjusted[order] = adjusted_sorted
    return MultipleTestingResult(
        p_values=values,
        adjusted_p_values=adjusted,
        rejected=adjusted <= alpha,
        alpha=alpha,
        method="benjamini-hochberg",
    )


def _as_performance(performance: NDArray[np.floating]) -> FloatArray:
    matrix = np.asarray(performance, dtype=np.float64)
    if matrix.ndim == 1:
        matrix = matrix[:, None]
    if matrix.ndim != 2:
        raise ValueError(f"performance must be T x M, got shape {matrix.shape}")
    if matrix.shape[0] < 4:
        raise ValueError("need at least four periods to bootstrap")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("performance contains non-finite values")
    return matrix


def _resolve_block_length(matrix: FloatArray, block_length: float | None) -> float:
    """Block length for a panel: the largest per-strategy stationary length.

    Taking the maximum rather than the mean is deliberate — under-blocking is the failure
    that produces optimistic p-values, so the panel inherits the most persistent column.
    """
    if block_length is not None:
        if not math.isfinite(block_length) or block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}")
        return block_length
    lengths = []
    for column in matrix.T:
        if float(np.var(column)) <= 0.0:
            continue
        lengths.append(optimal_block_length(column).stationary)
    return max(lengths) if lengths else 1.0


@dataclass(frozen=True)
class RealityCheckResult:
    """Outcome of a bootstrap data-snooping test over ``M`` strategies."""

    statistic: float
    p_value: float
    best_index: int
    best_mean_performance: float
    bootstrap_statistics: FloatArray
    block_length: float
    n_resamples: int
    n_observations: int
    n_strategies: int
    method: str


def reality_check(
    performance: NDArray[np.floating],
    *,
    rng: np.random.Generator,
    block_length: float | None = None,
    n_resamples: int = 1000,
) -> RealityCheckResult:
    """White's Reality Check for the best of ``M`` strategies.

    ``performance`` is a ``T x M`` matrix of per-period performance **relative to the
    benchmark** (positive means the strategy beat the benchmark that period). The null is
    that no strategy beats the benchmark: ``max_k E[f_k] <= 0``.

    The statistic is ``V = max_k sqrt(T) * mean(f_k)``. Each bootstrap replicate uses one
    stationary-bootstrap index draw applied to *every* column, which is what preserves the
    cross-sectional dependence between strategies, and is recentred on the sample means:
    ``V*_b = max_k sqrt(T) (mean(f*_k) - mean(f_k))``. The p-value is the fraction of
    replicates exceeding ``V``, computed with the usual ``(count + 1) / (B + 1)``
    convention so that it is never exactly zero.

    White's null is least favourable — every strategy is assumed to sit exactly at the
    benchmark — so poor strategies inflate the critical value and the test loses power.
    :func:`spa_test` is the fix.
    """
    matrix = _as_performance(performance)
    t, m = matrix.shape
    resolved_block = _resolve_block_length(matrix, block_length)
    means = matrix.mean(axis=0)
    scale = math.sqrt(t)
    statistic = float(np.max(means) * scale)
    best_index = int(np.argmax(means))

    indices = stationary_bootstrap_indices(t, resolved_block, n_resamples, rng)
    replicates = np.empty(n_resamples, dtype=np.float64)
    for b in range(n_resamples):
        resampled_means = matrix[indices[b]].mean(axis=0)
        replicates[b] = float(np.max((resampled_means - means) * scale))

    exceedances = int(np.count_nonzero(replicates >= statistic))
    p_value = (exceedances + 1.0) / (n_resamples + 1.0)

    return RealityCheckResult(
        statistic=statistic,
        p_value=p_value,
        best_index=best_index,
        best_mean_performance=float(means[best_index]),
        bootstrap_statistics=replicates,
        block_length=resolved_block,
        n_resamples=n_resamples,
        n_observations=t,
        n_strategies=m,
        method="white-reality-check",
    )


def spa_test(
    performance: NDArray[np.floating],
    *,
    rng: np.random.Generator,
    block_length: float | None = None,
    n_resamples: int = 1000,
    recentring: Recentring = "consistent",
) -> RealityCheckResult:
    """Hansen's Superior Predictive Ability test.

    Same input and null as :func:`reality_check`, with two changes. Each strategy is
    studentised by its own bootstrap standard deviation ``omega_k``, so a high-variance
    strategy no longer dominates the maximum by variance alone; and the bootstrap null is
    recentred so that strategies which are clearly worse than the benchmark do not inflate
    the critical value.

    The statistic is ``T_SPA = max(0, max_k sqrt(T) mean(f_k) / omega_k)`` and the
    replicate is ``max(0, max_k sqrt(T) (mean(f*_k) - g_k) / omega_k)``. Recentring
    choices:

    * ``"consistent"`` (default, Hansen's ``SPA_c``) — ``g_k = mean(f_k)`` when
      ``sqrt(T) mean(f_k) >= -omega_k sqrt(2 log log T)``, else 0. This is the consistent
      estimate of the true null set.
    * ``"lower"`` — ``g_k = max(0, mean(f_k))``. Discards every inferior strategy from the
      null, giving Hansen's ``p_l``, a **lower bound** on the true p-value.
    * ``"upper"`` — ``g_k = mean(f_k)`` always. Keeps every strategy in the null, giving
      Hansen's ``p_u``, an **upper bound** on the true p-value and the studentised
      analogue of the Reality Check.

    Because ``g^upper <= g^consistent <= g^lower`` pointwise, the p-values are ordered
    ``p_lower <= p_consistent <= p_upper``.

    ``omega_k`` is estimated from the same bootstrap draws used for the null distribution,
    which is Hansen's own recommendation and keeps the two consistent with each other.
    """
    matrix = _as_performance(performance)
    t, m = matrix.shape
    resolved_block = _resolve_block_length(matrix, block_length)
    means = matrix.mean(axis=0)
    scale = math.sqrt(t)

    indices = stationary_bootstrap_indices(t, resolved_block, n_resamples, rng)
    resampled_means = np.empty((n_resamples, m), dtype=np.float64)
    for b in range(n_resamples):
        resampled_means[b] = matrix[indices[b]].mean(axis=0)

    omega = np.std((resampled_means - means) * scale, axis=0, ddof=1)
    # A degenerate column (zero bootstrap dispersion) must not divide by zero; it carries
    # no evidence either way, so give it an infinite scale and a zero studentised value.
    safe_omega = np.where(omega > 0.0, omega, np.inf)

    studentised = means * scale / safe_omega
    statistic = float(max(0.0, float(np.max(studentised))))
    best_index = int(np.argmax(studentised))

    if recentring == "upper":
        g = means.copy()
    elif recentring == "lower":
        g = np.maximum(means, 0.0)
    elif recentring == "consistent":
        threshold = -safe_omega * math.sqrt(2.0 * math.log(math.log(t))) / scale
        g = np.where(means >= threshold, means, 0.0)
    else:
        raise ValueError(f"unknown recentring {recentring!r}")

    replicate_matrix = (resampled_means - g) * scale / safe_omega
    replicates = np.maximum(replicate_matrix.max(axis=1), 0.0)

    exceedances = int(np.count_nonzero(replicates >= statistic))
    p_value = (exceedances + 1.0) / (n_resamples + 1.0)

    return RealityCheckResult(
        statistic=statistic,
        p_value=p_value,
        best_index=best_index,
        best_mean_performance=float(means[best_index]),
        bootstrap_statistics=replicates,
        block_length=resolved_block,
        n_resamples=n_resamples,
        n_observations=t,
        n_strategies=m,
        method=f"hansen-spa-{recentring}",
    )
