"""Descriptive statistics, Sharpe inference, and tail risk.

Three things here are deliberately awkward to use, because each has a failure mode
that otherwise returns a plausible number instead of an error:

* **Annualising a Sharpe ratio.** ``sqrt(q)`` is wrong under autocorrelation. The
  Lo (2002) factor is provided and must be passed the autocorrelations actually
  estimated; it must never be applied to a Sharpe already built from overlapping
  q-period returns.
* **Expected shortfall.** With fewer than about ten observations in the tail it is
  unestimable. This module raises and surfaces the effective tail count rather
  than printing a mean of three numbers.
* **Cornish-Fisher VaR.** The expansion is a valid quantile transform only where
  it is monotone in ``z``. Outside that region it still returns a finite number.
  This module evaluates the derivative across the queried range and refuses.

Sources: ``docs/research/portfolio-engine-specification.md`` Layers 1 and 2;
Lo (2002) as restated verbatim in Getmansky, Lo and Makarov (2004), eqs. 79-81.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy.stats import norm

from ._types import FloatArray, FloatVector, as_float_array, require_non_empty
from .returns import (
    Compounding,
    ExcessMethod,
    Frequency,
    RateBasis,
    excess_returns,
)

MIN_TAIL_OBSERVATIONS = 10
"""Minimum tail sample below which expected shortfall is refused.

``docs/research/portfolio-engine-specification.md``: "expected shortfall with fewer
than about ten observations in the tail is unestimable, so surface the effective
tail count rather than printing a number".
"""


class InsufficientTailDataError(ValueError):
    """Raised when a tail statistic is requested from too few tail observations."""

    def __init__(self, tail_observations: int, required: int, alpha: float, sample: int) -> None:
        self.tail_observations = tail_observations
        self.required = required
        self.alpha = alpha
        self.sample = sample
        super().__init__(
            f"expected shortfall at alpha={alpha} has only {tail_observations} tail "
            f"observation(s) from a sample of {sample}; at least {required} are needed. "
            f"A sample of {math.ceil(required / alpha)} observations would supply them."
        )


class NonMonotoneExpansionError(ValueError):
    """Raised when the Cornish-Fisher transform is not monotone over the query range."""

    def __init__(
        self, z: float, derivative: float, skewness: float, excess_kurtosis: float
    ) -> None:
        self.z = z
        self.derivative = derivative
        self.skewness = skewness
        self.excess_kurtosis = excess_kurtosis
        super().__init__(
            f"Cornish-Fisher expansion is not monotone at z={z:.6f} "
            f"(dz_cf/dz = {derivative:.6f}) for skewness={skewness} and "
            f"excess kurtosis={excess_kurtosis}; the quantile it returns is meaningless"
        )


class QuantileRule(Enum):
    """Interpolation rule used to read a quantile off the order statistics.

    ``LINEAR``  Hyndman-Fan type 7, NumPy's default. With ``x`` sorted ascending and
    ``h = (n - 1) * alpha``, the quantile is
    ``x[floor(h)] + (h - floor(h)) * (x[floor(h) + 1] - x[floor(h)])``.
    ``LOWER``   the ``ceil(alpha * n)``-th smallest observation (1-indexed), i.e. an
    actually-observed loss, never interpolated. Weakly more conservative and the
    right choice when the VaR must correspond to a realised outcome.
    """

    LINEAR = "linear"
    LOWER = "lower"


@dataclass(frozen=True)
class SharpeResult:
    """A Sharpe ratio with its risk-free treatment and annualisation stated."""

    sharpe_per_period: float
    annualised_sharpe: float
    annualisation_factor: float
    observations: int
    mean_excess_return: float
    excess_volatility: float
    standard_error_per_period: float
    risk_free_treatment: str


@dataclass(frozen=True)
class ExpectedShortfallResult:
    """Historical expected shortfall together with the tail sample it rests on."""

    expected_shortfall: float
    value_at_risk: float
    tail_observations: int
    observations: int
    alpha: float


def mean_return(returns: FloatVector) -> float:
    """Sample arithmetic mean."""
    array = require_non_empty(as_float_array(returns, name="returns"), name="returns")
    return float(np.mean(array))


def volatility(returns: FloatVector, *, ddof: int = 1) -> float:
    """Sample standard deviation. ``ddof=1`` is the unbiased-variance default."""
    array = require_non_empty(as_float_array(returns, name="returns"), name="returns")
    if array.size <= ddof:
        raise ValueError(
            f"need more than ddof={ddof} observations to estimate volatility, "
            f"got {array.size}"
        )
    return float(np.std(array, ddof=ddof))


def sharpe_ratio(
    returns: FloatVector,
    *,
    frequency: Frequency,
    risk_free: FloatVector | float = 0.0,
    risk_free_basis: RateBasis = RateBasis.PER_PERIOD,
    compounding: Compounding = Compounding.GEOMETRIC,
    excess_method: ExcessMethod = ExcessMethod.ARITHMETIC,
    ddof: int = 1,
    annualisation_factor: float | None = None,
) -> SharpeResult:
    """Sharpe ratio with an explicit risk-free treatment and stated annualisation.

    ``annualisation_factor`` defaults to ``sqrt(periods_per_year)``, which assumes
    serially independent returns. Pass :func:`lo_annualisation_factor` when the
    returns are autocorrelated.
    """
    excess = excess_returns(
        returns,
        risk_free,
        frequency=frequency,
        cash_rate_basis=risk_free_basis,
        compounding=compounding,
        method=excess_method,
    )
    mean = mean_return(excess)
    sigma = volatility(excess, ddof=ddof)
    if sigma <= 0.0:
        raise ValueError("Sharpe ratio is undefined for a zero-volatility series")
    per_period = mean / sigma
    factor = (
        math.sqrt(frequency.periods_per_year)
        if annualisation_factor is None
        else annualisation_factor
    )
    treatment = (
        f"excess = {excess_method.value} vs risk_free stated {risk_free_basis.value}"
        f" ({compounding.value} de-annualisation), frequency={frequency.name.lower()},"
        f" ddof={ddof}"
    )
    return SharpeResult(
        sharpe_per_period=per_period,
        annualised_sharpe=per_period * factor,
        annualisation_factor=factor,
        observations=int(excess.size),
        mean_excess_return=mean,
        excess_volatility=sigma,
        standard_error_per_period=sharpe_standard_error(per_period, int(excess.size)),
        risk_free_treatment=treatment,
    )


def sharpe_standard_error(sharpe: float, observations: int) -> float:
    """``sqrt((1 + SR**2 / 2) / T)`` under i.i.d. normality.

    Source: ``docs/research/portfolio-engine-specification.md``, "Sharpe ratio
    inference". Both ``SR`` and ``T`` must be on the same frequency; annualising the
    Sharpe without annualising ``T`` is the standard way to get this wrong.
    """
    if observations < 2:
        raise ValueError(f"need at least 2 observations, got {observations}")
    return math.sqrt((1.0 + sharpe**2 / 2.0) / observations)


def ar1_autocorrelations(rho: float, lags: int) -> FloatArray:
    """``[rho, rho**2, ..., rho**lags]`` — the autocorrelation function of an AR(1)."""
    if lags < 0:
        raise ValueError(f"lags must be non-negative, got {lags}")
    if abs(rho) >= 1.0:
        raise ValueError(f"an AR(1) requires |rho| < 1, got {rho}")
    return np.asarray([rho ** (k + 1) for k in range(lags)], dtype=np.float64)


def lo_annualisation_factor(q: int, autocorrelations: FloatVector) -> float:
    """The Lo (2002) autocorrelation-corrected Sharpe annualisation factor.

    ``eta(q) = q / sqrt(q + 2 * sum_{k=1}^{q-1} (q - k) * rho_k)``.

    ``autocorrelations[k - 1]`` is ``rho_k``; at least ``q - 1`` lags are required and
    any beyond that are ignored. Three traps, per the engine specification:
    ``sqrt(q)`` is an upper bound only under *positive* autocorrelation; the sum
    reaches ``rho_{q-1}``, estimated from very few pairs in short samples, so taper
    or truncate and disclose it; and never apply ``eta`` to a Sharpe already built
    from overlapping q-period returns.
    """
    if q < 1:
        raise ValueError(f"q must be at least 1, got {q}")
    rho = as_float_array(autocorrelations, name="autocorrelations")
    if rho.size < q - 1:
        raise ValueError(
            f"eta(q={q}) needs {q - 1} autocorrelations, got {rho.size}"
        )
    weights = np.asarray([q - k for k in range(1, q)], dtype=np.float64)
    total = float(q + 2.0 * float(np.dot(weights, rho[: q - 1])))
    if total <= 0.0:
        raise ValueError(
            f"the Lo variance ratio denominator is {total!r}; the supplied "
            "autocorrelations are not consistent with a positive q-period variance"
        )
    return q / math.sqrt(total)


def historical_value_at_risk(
    returns: FloatVector,
    *,
    alpha: float = 0.05,
    rule: QuantileRule = QuantileRule.LINEAR,
) -> float:
    """Historical VaR at level ``alpha``, reported as a positive loss.

    The quantile-interpolation rule is explicit and part of the contract; see
    :class:`QuantileRule`. A return of ``-0.03`` at the 5% quantile gives a VaR of
    ``+0.03``.
    """
    array = require_non_empty(as_float_array(returns, name="returns"), name="returns")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie strictly in (0, 1), got {alpha}")
    if rule is QuantileRule.LINEAR:
        quantile = float(np.quantile(array, alpha, method="linear"))
    else:
        ordered = np.sort(array)
        index = max(math.ceil(alpha * array.size), 1) - 1
        quantile = float(ordered[index])
    return -quantile


def effective_tail_count(observations: int, alpha: float) -> int:
    """Number of observations at or below the ``alpha`` quantile of a sample.

    Reported instead of an expected shortfall when the tail is too thin.
    """
    if observations < 1:
        raise ValueError("observations must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie strictly in (0, 1), got {alpha}")
    return math.floor(alpha * observations)


def historical_expected_shortfall(
    returns: FloatVector,
    *,
    alpha: float = 0.05,
    rule: QuantileRule = QuantileRule.LINEAR,
    min_tail_observations: int = MIN_TAIL_OBSERVATIONS,
) -> ExpectedShortfallResult:
    """Mean loss conditional on breaching the historical VaR, as a positive number.

    Raises :class:`InsufficientTailDataError` — carrying the effective tail count —
    rather than averaging a handful of observations.
    """
    array = require_non_empty(as_float_array(returns, name="returns"), name="returns")
    value_at_risk = historical_value_at_risk(array, alpha=alpha, rule=rule)
    threshold = -value_at_risk
    tail = array[array <= threshold]
    if tail.size < min_tail_observations:
        raise InsufficientTailDataError(
            tail_observations=int(tail.size),
            required=min_tail_observations,
            alpha=alpha,
            sample=int(array.size),
        )
    return ExpectedShortfallResult(
        expected_shortfall=-float(np.mean(tail)),
        value_at_risk=value_at_risk,
        tail_observations=int(tail.size),
        observations=int(array.size),
        alpha=alpha,
    )


def gaussian_value_at_risk(mean: float, sigma: float, *, alpha: float = 0.05) -> float:
    """``VaR = -(mu + sigma * z_alpha)``, reported as a positive loss."""
    if sigma < 0.0:
        raise ValueError("sigma cannot be negative")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie strictly in (0, 1), got {alpha}")
    return -(mean + sigma * float(norm.ppf(alpha)))


def gaussian_expected_shortfall(mean: float, sigma: float, *, alpha: float = 0.05) -> float:
    """``ES = -(mu - sigma * phi(z_alpha) / alpha)``, reported as a positive loss."""
    if sigma < 0.0:
        raise ValueError("sigma cannot be negative")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie strictly in (0, 1), got {alpha}")
    z = float(norm.ppf(alpha))
    return -(mean - sigma * float(norm.pdf(z)) / alpha)


def cornish_fisher_z(z: float, skewness: float, excess_kurtosis: float) -> float:
    """The Cornish-Fisher adjusted standard normal quantile.

    ``z_cf = z + (z**2 - 1) S / 6 + (z**3 - 3z) K / 24 - (2 z**3 - 5 z) S**2 / 36``
    with ``S`` skewness and ``K`` *excess* kurtosis (0 for a normal).
    """
    return (
        z
        + (z**2 - 1.0) * skewness / 6.0
        + (z**3 - 3.0 * z) * excess_kurtosis / 24.0
        - (2.0 * z**3 - 5.0 * z) * skewness**2 / 36.0
    )


def cornish_fisher_derivative(z: float, skewness: float, excess_kurtosis: float) -> float:
    """``dz_cf/dz``. The expansion is a valid quantile transform only where this is > 0."""
    return (
        1.0
        + z * skewness / 3.0
        + (3.0 * z**2 - 3.0) * excess_kurtosis / 24.0
        - (6.0 * z**2 - 5.0) * skewness**2 / 36.0
    )


def is_cornish_fisher_monotone(
    skewness: float,
    excess_kurtosis: float,
    *,
    z_range: tuple[float, float] = (-4.0, 4.0),
    grid_points: int = 4001,
) -> bool:
    """Whether ``dz_cf/dz > 0`` everywhere on ``z_range``, checked on a grid."""
    return _first_non_monotone_z(skewness, excess_kurtosis, z_range, grid_points) is None


def cornish_fisher_value_at_risk(
    *,
    mean: float,
    sigma: float,
    skewness: float,
    excess_kurtosis: float,
    alpha: float = 0.05,
    z_range: tuple[float, float] = (-4.0, 4.0),
    grid_points: int = 4001,
) -> float:
    """Cornish-Fisher VaR, reported as a positive loss.

    Raises :class:`NonMonotoneExpansionError` if ``dz_cf/dz`` changes sign anywhere on
    ``z_range``, which must cover every quantile the caller intends to query. At
    ``alpha=0.05, S=-2.0, K=1`` the formula returns a finite -2.118056 and is
    non-monotone; the value is meaningless and this function refuses it.
    """
    if sigma < 0.0:
        raise ValueError("sigma cannot be negative")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie strictly in (0, 1), got {alpha}")
    failure = _first_non_monotone_z(skewness, excess_kurtosis, z_range, grid_points)
    if failure is not None:
        z_bad, derivative = failure
        raise NonMonotoneExpansionError(z_bad, derivative, skewness, excess_kurtosis)
    z = float(norm.ppf(alpha))
    if not z_range[0] <= z <= z_range[1]:
        raise ValueError(
            f"alpha={alpha} implies z={z:.6f}, outside the checked range {z_range}"
        )
    return -(mean + sigma * cornish_fisher_z(z, skewness, excess_kurtosis))


def max_admissible_skewness(
    excess_kurtosis: float,
    *,
    z_range: tuple[float, float] = (-4.0, 4.0),
    grid_points: int = 4001,
    tolerance: float = 1e-6,
    upper_bound: float = 10.0,
) -> float:
    """Largest ``|S|`` for which Cornish-Fisher stays monotone on ``z_range``.

    Found by bisection on the monotonicity predicate. The engine specification
    reports 0.418 at K=0, 0.834 at K=1, 1.376 at K=3 and 1.921 at K=6, derived this
    way because the published validity domain (Maillard, SSRN 1997178) was not
    retrievable.
    """
    if not is_cornish_fisher_monotone(
        0.0, excess_kurtosis, z_range=z_range, grid_points=grid_points
    ):
        raise ValueError(
            f"the expansion is already non-monotone at zero skew for "
            f"excess kurtosis {excess_kurtosis}"
        )
    low, high = 0.0, upper_bound
    while high - low > tolerance:
        mid = 0.5 * (low + high)
        if is_cornish_fisher_monotone(
            mid, excess_kurtosis, z_range=z_range, grid_points=grid_points
        ):
            low = mid
        else:
            high = mid
    return low


def _first_non_monotone_z(
    skewness: float,
    excess_kurtosis: float,
    z_range: tuple[float, float],
    grid_points: int,
) -> tuple[float, float] | None:
    """Return the first grid point where ``dz_cf/dz <= 0``, or ``None``."""
    low, high = z_range
    if not high > low:
        raise ValueError(f"z_range must be increasing, got {z_range}")
    if grid_points < 2:
        raise ValueError(f"grid_points must be at least 2, got {grid_points}")
    grid = np.linspace(low, high, grid_points, dtype=np.float64)
    derivatives = (
        1.0
        + grid * skewness / 3.0
        + (3.0 * grid**2 - 3.0) * excess_kurtosis / 24.0
        - (6.0 * grid**2 - 5.0) * skewness**2 / 36.0
    )
    breaches = np.flatnonzero(derivatives <= 0.0)
    if breaches.size == 0:
        return None
    index = int(breaches[0])
    return float(grid[index]), float(derivatives[index])
