"""Block bootstrap resampling for serially dependent series.

An i.i.d. bootstrap destroys serial dependence and therefore biases the sampling
distribution of every statistic that depends on it — long-horizon variance, drawdown,
autocorrelation-adjusted Sharpe — generally *too narrow*. This module provides the two
resamplers that preserve short-range dependence, plus automatic block-length selection.

* **Circular block bootstrap** — fixed-length blocks drawn from the series wrapped end to
  start, so every observation is equally likely to appear (Politis and Romano 1992).
* **Stationary bootstrap** — geometrically distributed block lengths, producing a strictly
  stationary resample at the cost of extra variance from the randomised length
  (Politis and Romano 1994).

Block-length selection follows Politis and White (2004) **with the Patton, Politis and
White (2009) correction**: Nordman found an error in the underlying stationary-bootstrap
variance, so the correct constant is ``D_SB = 2 * g(0)^2`` rather than the pre-2009 value.
The consequence is that the stationary bootstrap's optimal block is smaller than
previously published and its asymptotic relative efficiency against the circular block
bootstrap is ``(2/3)**(2/3) ~= 0.7631428`` — see :data:`STATIONARY_TO_CIRCULAR_ARE`.

Every resampling function takes an explicit :class:`numpy.random.Generator`; there is no
module-level generator and no global state, so results are exactly reproducible.

References
----------
Politis, D. N. and H. White (2004). "Automatic block-length selection for the dependent
bootstrap." *Econometric Reviews* 23.
Patton, A., D. N. Politis and H. White (2009). "Correction to 'Automatic block-length
selection for the dependent bootstrap'." *Econometric Reviews* 28(4), 372-375.
Reference implementation cross-checked against http://www.math.ucsd.edu/~politis/SOFT/ppwR.txt
(retrieved 2026-08-11; ``$Id: ppw.R,v 1.47 2008/12/12$``).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "STATIONARY_TO_CIRCULAR_ARE",
    "BlockLengthSelection",
    "BootstrapInterval",
    "BootstrapMethod",
    "IntervalKind",
    "autocorrelation",
    "autocovariance",
    "bootstrap_confidence_interval",
    "circular_block_indices",
    "iid_bootstrap_indices",
    "optimal_block_length",
    "stationary_bootstrap_indices",
]

FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]

BootstrapMethod = Literal["circular", "stationary", "iid"]
IntervalKind = Literal["percentile", "basic"]

#: Asymptotic relative efficiency of the stationary bootstrap against the circular block
#: bootstrap under the Patton-Politis-White (2009) correction.
#:
#: The minimised mean squared error of the block-length-optimal variance estimator is
#: proportional to ``D**(2/3)``, so the efficiency ratio is ``(D_CB / D_SB)**(2/3)``.
#: With the corrected ``D_SB = 2 g(0)**2`` and ``D_CB = (4/3) g(0)**2`` this is
#: ``((4/3) / 2)**(2/3) = (2/3)**(2/3) = 0.7631428...``. The pre-2009 constant is still
#: circulating in older ports of the rule, so verify any library compared against this.
STATIONARY_TO_CIRCULAR_ARE: Final[float] = (2.0 / 3.0) ** (2.0 / 3.0)

#: Coefficient on ``g(0)**2`` in the stationary-bootstrap variance term, post-correction.
_D_SB_COEFFICIENT: Final[float] = 2.0
#: Coefficient on ``g(0)**2`` in the circular-block-bootstrap variance term.
_D_CB_COEFFICIENT: Final[float] = 4.0 / 3.0

#: Two-sided 97.5% normal quantile, the default critical multiplier in ppwR.txt.
_DEFAULT_CRITICAL_MULTIPLIER: Final[float] = 1.959963984540054


def _as_series(x: NDArray[np.floating] | list[float]) -> FloatArray:
    """Validate and coerce a one-dimensional real series."""
    series = np.asarray(x, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"expected a one-dimensional series, got shape {series.shape}")
    if series.size < 2:
        raise ValueError("a bootstrap needs at least two observations")
    if not np.all(np.isfinite(series)):
        raise ValueError("series contains non-finite values")
    return series


def autocovariance(x: NDArray[np.floating] | list[float], max_lag: int) -> FloatArray:
    """Sample autocovariance ``R_hat(k)`` for ``k = 0 .. max_lag``.

    Uses the ``1/n`` divisor at every lag, matching R's ``acf(type="covariance")`` and
    therefore the ``ppwR.txt`` reference implementation. This is the *auto-covariance*
    used by the block-length formula — distinct from :func:`autocorrelation`, which is
    what the lag-selection step consumes. Conflating the two is a common porting bug.
    """
    series = _as_series(x)
    n = series.size
    if not 0 <= max_lag < n:
        raise ValueError(f"max_lag must lie in [0, {n - 1}], got {max_lag}")
    centred = series - series.mean()
    out = np.empty(max_lag + 1, dtype=np.float64)
    for k in range(max_lag + 1):
        out[k] = float(np.dot(centred[: n - k], centred[k:]) / n)
    return out


def autocorrelation(x: NDArray[np.floating] | list[float], max_lag: int) -> FloatArray:
    """Sample autocorrelation ``rho_hat(k)`` for ``k = 0 .. max_lag``.

    This is ``R_hat(k) / R_hat(0)``. The lag-selection step of the Politis-White rule uses
    *this* quantity; the block-length formula itself uses the raw autocovariance.
    """
    gamma = autocovariance(x, max_lag)
    if gamma[0] <= 0.0:
        raise ValueError("series has zero variance; autocorrelation is undefined")
    normalised: FloatArray = gamma / float(gamma[0])
    return normalised


def _flat_top_lag_window(s: FloatArray) -> FloatArray:
    """Politis-Romano (1995) flat-top lag window.

    ``lam(s) = 1`` for ``|s| < 1/2``, ``2 (1 - |s|)`` for ``1/2 <= |s| <= 1``, else 0.
    """
    a = np.abs(s)
    return np.where(a < 0.5, 1.0, np.where(a <= 1.0, 2.0 * (1.0 - a), 0.0))


def _select_lag(rho: FloatArray, n: int, k_n: int, critical_multiplier: float) -> int:
    """Politis-White footnote (c) selection of ``m_hat`` from autocorrelations.

    ``rho`` holds ``rho_hat(1) .. rho_hat(m_max)``. Take the smallest lag after which
    ``k_n`` consecutive autocorrelations are all insignificant; failing that, the largest
    significant lag (or the sole one); failing that, 1.
    """
    m_max = rho.size
    threshold = critical_multiplier * math.sqrt(math.log10(n) / n)
    insignificant = np.abs(rho) < threshold
    if m_max >= k_n:
        # Rolling count of insignificant autocorrelations in each window of length k_n.
        cumulative = np.concatenate(([0], np.cumsum(insignificant.astype(np.int64))))
        counts = cumulative[k_n:] - cumulative[: m_max - k_n + 1]
        runs = np.flatnonzero(counts == k_n)
        if runs.size > 0:
            return int(runs[0]) + 1
    significant = np.flatnonzero(~insignificant)
    if significant.size == 1:
        return int(significant[0]) + 1
    if significant.size > 1:
        return int(significant.max()) + 1
    return 1


@dataclass(frozen=True)
class BlockLengthSelection:
    """Outcome of the corrected Politis-White automatic block-length rule."""

    stationary: float
    """Optimal expected block length for the stationary bootstrap (``b*_SB``)."""
    circular: float
    """Optimal fixed block length for the circular block bootstrap (``b*_CB``)."""
    m_hat: int
    """Selected autocorrelation cut-off lag."""
    m: int
    """Bandwidth ``M = min(2 * m_hat, m_max)`` used in the spectral sums."""
    g_hat: float
    """``G_hat = sum_k lam(k/M) |k| R_hat(k)``, using the auto*covariance*."""
    g_zero: float
    """``g_hat(0) = sum_k lam(k/M) R_hat(k)``, using the auto*covariance*."""
    d_sb: float
    """``D_SB = 2 g_hat(0)^2`` — the Patton-Politis-White (2009) corrected constant."""
    d_cb: float
    """``D_CB = (4/3) g_hat(0)^2``."""
    n_observations: int
    k_n: int
    m_max: int
    b_max: float


def optimal_block_length(
    x: NDArray[np.floating] | list[float],
    *,
    k_n: int | None = None,
    m_max: int | None = None,
    b_max: float | None = None,
    critical_multiplier: float = _DEFAULT_CRITICAL_MULTIPLIER,
) -> BlockLengthSelection:
    """Automatic block length by Politis-White (2004) with the 2009 correction.

    Defaults follow ``ppwR.txt`` exactly: ``k_n = max(5, ceil(log10(n)))``,
    ``m_max = ceil(sqrt(n)) + k_n``, ``b_max = ceil(min(3 sqrt(n), n/3))`` and a critical
    multiplier of ``Phi^-1(0.975)``.

    Note the two different second moments the rule uses. Lag selection thresholds the
    **autocorrelation** ``rho_hat(k)`` against ``c sqrt(log10(n)/n)``; the block-length
    formula then sums the **autocovariance** ``R_hat(k)`` against a flat-top window.

    Returns both block lengths unrounded (but clipped to ``[1, b_max]``). Callers that
    need integers should round the stationary length and take the ceiling of the circular
    one, as the reference implementation does.
    """
    series = _as_series(x)
    n = series.size
    resolved_k_n = max(5, math.ceil(math.log10(n))) if k_n is None else k_n
    resolved_m_max = math.ceil(math.sqrt(n)) + resolved_k_n if m_max is None else m_max
    resolved_m_max = min(resolved_m_max, n - 1)
    resolved_b_max = math.ceil(min(3.0 * math.sqrt(n), n / 3.0)) if b_max is None else b_max
    if resolved_k_n < 1 or resolved_m_max < 1:
        raise ValueError("k_n and m_max must be positive")

    rho = autocorrelation(series, resolved_m_max)[1:]
    m_hat = _select_lag(rho, n, resolved_k_n, critical_multiplier)
    m = resolved_m_max if 2 * m_hat > resolved_m_max else 2 * m_hat

    lags = np.arange(-m, m + 1)
    gamma = autocovariance(series, m)
    r_k = gamma[np.abs(lags)]
    window = _flat_top_lag_window(lags / m)
    g_hat = float(np.sum(window * np.abs(lags) * r_k))
    g_zero = float(np.sum(window * r_k))

    d_sb = _D_SB_COEFFICIENT * g_zero**2
    d_cb = _D_CB_COEFFICIENT * g_zero**2

    if d_sb <= 0.0 or g_hat == 0.0:
        # No detectable dependence: fall back to single-observation blocks.
        stationary = 1.0
        circular = 1.0
    else:
        scale = float(n) ** (1.0 / 3.0)
        stationary = (2.0 * g_hat**2 / d_sb) ** (1.0 / 3.0) * scale
        circular = (2.0 * g_hat**2 / d_cb) ** (1.0 / 3.0) * scale

    return BlockLengthSelection(
        stationary=float(min(max(stationary, 1.0), resolved_b_max)),
        circular=float(min(max(circular, 1.0), resolved_b_max)),
        m_hat=m_hat,
        m=m,
        g_hat=g_hat,
        g_zero=g_zero,
        d_sb=d_sb,
        d_cb=d_cb,
        n_observations=n,
        k_n=resolved_k_n,
        m_max=resolved_m_max,
        b_max=float(resolved_b_max),
    )


def _check_resample_shape(n_observations: int, n_resamples: int) -> None:
    if n_observations < 1:
        raise ValueError("n_observations must be positive")
    if n_resamples < 1:
        raise ValueError("n_resamples must be positive")


def iid_bootstrap_indices(
    n_observations: int, n_resamples: int, rng: np.random.Generator
) -> IndexArray:
    """Draw ``(n_resamples, n_observations)`` i.i.d. resampling indices.

    Provided for comparison only. It destroys serial dependence and gives materially
    narrower intervals than a block bootstrap on a dependent series.
    """
    _check_resample_shape(n_observations, n_resamples)
    return rng.integers(0, n_observations, size=(n_resamples, n_observations)).astype(np.intp)


def circular_block_indices(
    n_observations: int,
    block_length: float,
    n_resamples: int,
    rng: np.random.Generator,
) -> IndexArray:
    """Circular block bootstrap indices, shape ``(n_resamples, n_observations)``.

    The series is wrapped end to start, so block starts are uniform on ``0..n-1`` and
    every observation appears in exactly ``block_length`` blocks. That is what makes each
    observation equally likely, unlike the non-circular moving-block bootstrap which
    under-samples the two ends.

    ``block_length`` is rounded up to an integer, matching the reference implementation's
    treatment of ``BstarCB``.
    """
    _check_resample_shape(n_observations, n_resamples)
    if not math.isfinite(block_length) or block_length <= 0:
        raise ValueError(f"block_length must be a positive finite number, got {block_length!r}")
    b = min(math.ceil(block_length), n_observations)
    n_blocks = math.ceil(n_observations / b)
    starts = rng.integers(0, n_observations, size=(n_resamples, n_blocks))
    offsets = np.arange(b)
    indices = (starts[:, :, None] + offsets[None, None, :]) % n_observations
    return indices.reshape(n_resamples, n_blocks * b)[:, :n_observations].astype(np.intp)


def stationary_bootstrap_indices(
    n_observations: int,
    mean_block_length: float,
    n_resamples: int,
    rng: np.random.Generator,
) -> IndexArray:
    """Stationary bootstrap indices, shape ``(n_resamples, n_observations)``.

    Blocks have geometric lengths with mean ``mean_block_length`` (restart probability
    ``p = 1 / mean_block_length``) and wrap circularly. The resample is strictly
    stationary; the price is extra variance from the randomised block length.
    """
    _check_resample_shape(n_observations, n_resamples)
    if not math.isfinite(mean_block_length) or mean_block_length < 1.0:
        raise ValueError(f"mean_block_length must be >= 1, got {mean_block_length!r}")
    p = 1.0 / mean_block_length
    starts = rng.integers(0, n_observations, size=(n_resamples, n_observations))
    restart = rng.random((n_resamples, n_observations)) < p
    restart[:, 0] = True
    positions = np.broadcast_to(np.arange(n_observations), (n_resamples, n_observations))
    # Index of the most recent restart at or before each position.
    last_restart = np.maximum.accumulate(np.where(restart, positions, -1), axis=1)
    block_start = np.take_along_axis(starts, last_restart, axis=1)
    indices = (block_start + (positions - last_restart)) % n_observations
    return indices.astype(np.intp)


def _draw_indices(
    method: BootstrapMethod,
    n_observations: int,
    block_length: float,
    n_resamples: int,
    rng: np.random.Generator,
) -> IndexArray:
    if method == "iid":
        return iid_bootstrap_indices(n_observations, n_resamples, rng)
    if method == "circular":
        return circular_block_indices(n_observations, block_length, n_resamples, rng)
    if method == "stationary":
        return stationary_bootstrap_indices(n_observations, block_length, n_resamples, rng)
    raise ValueError(f"unknown bootstrap method {method!r}")


@dataclass(frozen=True)
class BootstrapInterval:
    """A bootstrap confidence interval for an arbitrary statistic."""

    point_estimate: float
    lower: float
    upper: float
    standard_error: float
    confidence_level: float
    method: BootstrapMethod
    interval: IntervalKind
    block_length: float
    n_resamples: int
    replicates: FloatArray

    @property
    def width(self) -> float:
        """Width of the interval — the quantity that a block bootstrap widens."""
        return self.upper - self.lower


def bootstrap_confidence_interval(
    x: NDArray[np.floating] | list[float],
    statistic: Callable[[FloatArray], float],
    *,
    rng: np.random.Generator,
    method: BootstrapMethod = "circular",
    block_length: float | None = None,
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    interval: IntervalKind = "percentile",
) -> BootstrapInterval:
    """Bootstrap a confidence interval for ``statistic`` applied to ``x``.

    ``statistic`` must map a one-dimensional series to a scalar — a Sharpe ratio, a mean,
    a maximum drawdown. It is applied to the original series for the point estimate and to
    each resample for the replicate distribution.

    ``block_length`` defaults to the automatic Politis-White length appropriate to
    ``method`` (:func:`optimal_block_length`), and is ignored for ``method="iid"``.

    Two interval kinds are offered, both documented rather than implicit:

    * ``"percentile"`` — the ``alpha/2`` and ``1 - alpha/2`` quantiles of the replicates.
    * ``"basic"`` — the reflected interval ``2*theta_hat - q_{1-alpha/2}``,
      ``2*theta_hat - q_{alpha/2}``, which corrects first-order median bias.

    Neither is bias-corrected-and-accelerated; BCa is deliberately out of scope because its
    jackknife acceleration term is not well defined for path-dependent statistics such as
    drawdown.
    """
    series = _as_series(x)
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(f"confidence_level must lie in (0, 1), got {confidence_level}")
    if n_resamples < 2:
        raise ValueError("n_resamples must be at least 2")

    if method == "iid":
        resolved_block = 1.0
    elif block_length is None:
        selection = optimal_block_length(series)
        resolved_block = selection.circular if method == "circular" else selection.stationary
    else:
        resolved_block = block_length

    indices = _draw_indices(method, series.size, resolved_block, n_resamples, rng)
    replicates = np.array(
        [statistic(series[row]) for row in indices],
        dtype=np.float64,
    )

    point = float(statistic(series))
    alpha = 1.0 - confidence_level
    low_q, high_q = np.quantile(replicates, [alpha / 2.0, 1.0 - alpha / 2.0])
    if interval == "percentile":
        lower, upper = float(low_q), float(high_q)
    elif interval == "basic":
        lower, upper = 2.0 * point - float(high_q), 2.0 * point - float(low_q)
    else:
        raise ValueError(f"unknown interval kind {interval!r}")

    return BootstrapInterval(
        point_estimate=point,
        lower=lower,
        upper=upper,
        standard_error=float(np.std(replicates, ddof=1)),
        confidence_level=confidence_level,
        method=method,
        interval=interval,
        block_length=resolved_block,
        n_resamples=n_resamples,
        replicates=replicates,
    )
