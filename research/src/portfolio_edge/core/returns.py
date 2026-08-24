"""Return primitives: simple/log conversion, aggregation, excess returns, growth.

Two contracts are made explicit here because both are routinely left implicit and
both change the answer:

* **Frequency.** Every annualisation or de-annualisation names the observation
  frequency and the compounding convention it uses. A cash rate is never assumed
  to be per-period or annualised; the caller states which via :class:`RateBasis`.
* **Growth.** ``g = mu - sigma**2 / 2`` is a second-order expansion, exact only in
  continuous time or for log returns. The exact lognormal simple-return growth
  rate is provided alongside it so the approximation error is measurable rather
  than assumed small. See ``docs/research/portfolio-engine-specification.md``,
  "Geometric versus arithmetic mean".
"""

from __future__ import annotations

import math
from enum import Enum

import numpy as np

from ._types import FloatArray, FloatVector, as_float_array, require_non_empty


class Frequency(Enum):
    """Observation frequency, carrying the periods-per-year used to annualise.

    ``DAILY`` uses 252 trading days, the convention for equity return series. A
    calendar-day series must not use it.
    """

    DAILY = 252
    WEEKLY = 52
    MONTHLY = 12
    QUARTERLY = 4
    ANNUAL = 1

    @property
    def periods_per_year(self) -> int:
        return int(self.value)


class Compounding(Enum):
    """How an annual rate is spread across the periods of a year.

    ``GEOMETRIC``  ``(1 + a) ** (1 / n) - 1`` — compounds to exactly ``a``.
    ``SIMPLE``     ``a / n`` — the money-market convention used by most quoted
    bill yields and by Ken French's ``RF`` column, which is already a monthly rate.
    """

    GEOMETRIC = "geometric"
    SIMPLE = "simple"


class RateBasis(Enum):
    """Whether a supplied rate is stated per period or per annum."""

    PER_PERIOD = "per_period"
    ANNUALISED = "annualised"


class ExcessMethod(Enum):
    """How an excess return is formed from a total return and a cash rate.

    ``ARITHMETIC``  ``r - r_f``. The Fama-French convention and the one implied by
    any regression whose dependent variable is a published excess return.
    ``GEOMETRIC``   ``(1 + r) / (1 + r_f) - 1``. The exact wealth-relative ratio;
    differs from the arithmetic form at second order in ``r_f``.
    """

    ARITHMETIC = "arithmetic"
    GEOMETRIC = "geometric"


def simple_to_log(returns: FloatVector) -> FloatArray:
    """Convert simple returns to log returns, ``ln(1 + r)``.

    Raises on ``1 + r <= 0``: total loss has no finite log return and the wealth
    path is not continuable.
    """
    array = as_float_array(returns, name="returns")
    relatives = 1.0 + array
    if np.any(relatives <= 0.0):
        index = int(np.argmax(relatives <= 0.0))
        raise ValueError(
            f"simple return {array[index]!r} at index {index} implies a non-positive "
            "wealth relative and has no log return"
        )
    return np.log(relatives)


def log_to_simple(log_returns: FloatVector) -> FloatArray:
    """Convert log returns to simple returns, ``exp(x) - 1``."""
    return np.expm1(as_float_array(log_returns, name="log_returns"))


def compound_simple(returns: FloatVector) -> float:
    """Total simple return over the whole sample, ``prod(1 + r) - 1``."""
    array = as_float_array(returns, name="returns")
    if array.size == 0:
        return 0.0
    return float(np.prod(1.0 + array) - 1.0)


def aggregate_log(log_returns: FloatVector) -> float:
    """Total log return over the whole sample. Log returns add; simple ones do not."""
    return float(np.sum(as_float_array(log_returns, name="log_returns")))


def aggregate_simple_over(returns: FloatVector, periods: int) -> FloatArray:
    """Compound ``returns`` into non-overlapping blocks of ``periods`` observations.

    A trailing partial block is dropped rather than annualised from a short window.
    Overlapping aggregation is deliberately not offered: it induces exactly the
    serial dependence that invalidates the Lo autocorrelation correction downstream.
    """
    array = as_float_array(returns, name="returns")
    if periods < 1:
        raise ValueError(f"periods must be at least 1, got {periods}")
    blocks = array.size // periods
    if blocks == 0:
        raise ValueError(
            f"cannot aggregate {array.size} observations into blocks of {periods}"
        )
    trimmed = array[: blocks * periods].reshape(blocks, periods)
    return np.asarray(np.prod(1.0 + trimmed, axis=1) - 1.0, dtype=np.float64)


def deannualise(
    annual_rate: FloatVector | float,
    *,
    frequency: Frequency,
    compounding: Compounding = Compounding.GEOMETRIC,
) -> FloatArray:
    """Convert an annual rate to a per-period rate under a stated convention."""
    array = np.atleast_1d(np.asarray(annual_rate, dtype=np.float64))
    periods = frequency.periods_per_year
    if compounding is Compounding.SIMPLE:
        return np.asarray(array / periods, dtype=np.float64)
    if np.any(1.0 + array <= 0.0):
        raise ValueError("geometric de-annualisation requires 1 + annual_rate > 0")
    return np.asarray(np.power(1.0 + array, 1.0 / periods) - 1.0, dtype=np.float64)


def annualise_simple_return(
    per_period_return: float,
    *,
    frequency: Frequency,
    compounding: Compounding = Compounding.GEOMETRIC,
) -> float:
    """Scale a per-period simple return up to a yearly figure."""
    periods = frequency.periods_per_year
    if compounding is Compounding.SIMPLE:
        return per_period_return * periods
    if 1.0 + per_period_return <= 0.0:
        raise ValueError("geometric annualisation requires 1 + per_period_return > 0")
    return float((1.0 + per_period_return) ** periods - 1.0)


def annualise_log_return(per_period_log_return: float, *, frequency: Frequency) -> float:
    """Log returns are additive, so annualising is multiplication by the period count."""
    return per_period_log_return * frequency.periods_per_year


def annualise_volatility(per_period_volatility: float, *, frequency: Frequency) -> float:
    """Square-root-of-time volatility scaling.

    Valid only for serially independent returns. Under autocorrelation use the Lo
    factor in :mod:`portfolio_edge.core.statistics` instead of this.
    """
    if per_period_volatility < 0.0:
        raise ValueError("volatility cannot be negative")
    return per_period_volatility * math.sqrt(frequency.periods_per_year)


def excess_returns(
    returns: FloatVector,
    cash_rate: FloatVector | float,
    *,
    frequency: Frequency,
    cash_rate_basis: RateBasis = RateBasis.PER_PERIOD,
    compounding: Compounding = Compounding.GEOMETRIC,
    method: ExcessMethod = ExcessMethod.ARITHMETIC,
) -> FloatArray:
    """Return ``returns`` net of a cash rate under an explicit frequency contract.

    ``frequency`` describes ``returns``. ``cash_rate_basis`` states whether
    ``cash_rate`` is already per-period or is quoted per annum; if annualised, it is
    de-annualised with ``compounding`` before subtraction. ``cash_rate`` may be a
    scalar (a constant rate) or a series of the same length as ``returns``.
    """
    array = as_float_array(returns, name="returns")
    rate = np.atleast_1d(np.asarray(cash_rate, dtype=np.float64))
    if not np.all(np.isfinite(rate)):
        raise ValueError("cash_rate contains non-finite entries")
    if cash_rate_basis is RateBasis.ANNUALISED:
        rate = deannualise(rate, frequency=frequency, compounding=compounding)
    if rate.size == 1:
        rate = np.full(array.shape, float(rate[0]), dtype=np.float64)
    if rate.shape != array.shape:
        raise ValueError(
            f"cash_rate must be scalar or the same length as returns "
            f"({array.size}), got {rate.size}"
        )
    if method is ExcessMethod.ARITHMETIC:
        return np.asarray(array - rate, dtype=np.float64)
    if np.any(1.0 + rate <= 0.0):
        raise ValueError("geometric excess returns require 1 + cash_rate > 0")
    return np.asarray((1.0 + array) / (1.0 + rate) - 1.0, dtype=np.float64)


def arithmetic_mean(returns: FloatVector) -> float:
    """Sample arithmetic mean of simple returns."""
    array = require_non_empty(as_float_array(returns, name="returns"), name="returns")
    return float(np.mean(array))


def geometric_mean(returns: FloatVector) -> float:
    """Per-period geometric mean, ``prod(1 + r) ** (1 / n) - 1``.

    This is the realised growth rate: the constant return that reproduces terminal
    wealth. It is always at most the arithmetic mean, with equality only when every
    observation is identical.
    """
    array = require_non_empty(as_float_array(returns, name="returns"), name="returns")
    relatives = 1.0 + array
    if np.any(relatives <= 0.0):
        raise ValueError("geometric mean is undefined once wealth reaches zero")
    return float(np.exp(np.mean(np.log(relatives))) - 1.0)


def lognormal_log_drift(mean_simple_return: float, volatility: float) -> float:
    """The log-return drift ``m`` implied by a lognormal simple-return model.

    ``m = ln((1 + mu)**2 / sqrt((1 + mu)**2 + sigma**2))``, where ``mu`` is the
    arithmetic mean simple return and ``sigma`` its standard deviation.
    Source: ``docs/research/portfolio-engine-specification.md``, Layer 1.
    """
    if volatility < 0.0:
        raise ValueError("volatility cannot be negative")
    base = (1.0 + mean_simple_return) ** 2
    if base <= 0.0:
        raise ValueError("lognormal model requires 1 + mean_simple_return != 0")
    return math.log(base / math.sqrt(base + volatility**2))


def lognormal_growth_rate(mean_simple_return: float, volatility: float) -> float:
    """Exact geometric growth rate ``g = exp(m) - 1`` under a lognormal model."""
    return math.exp(lognormal_log_drift(mean_simple_return, volatility)) - 1.0


def growth_rate_approximation(mean_simple_return: float, volatility: float) -> float:
    """The second-order approximation ``mu - sigma**2 / 2``.

    Kept as a named function precisely so that its error against
    :func:`lognormal_growth_rate` can be measured rather than assumed negligible.
    """
    if volatility < 0.0:
        raise ValueError("volatility cannot be negative")
    return mean_simple_return - volatility**2 / 2.0


def growth_rate_approximation_error(mean_simple_return: float, volatility: float) -> float:
    """``approximation - exact``. Negative means the approximation understates growth.

    The approximation overstates volatility drag as ``sigma`` grows and can wrongly
    predict negative growth; Kelly sizing runs directly on ``g``, so this error
    propagates straight into leverage.
    """
    return growth_rate_approximation(mean_simple_return, volatility) - lognormal_growth_rate(
        mean_simple_return, volatility
    )
