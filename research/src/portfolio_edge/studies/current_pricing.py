"""Pricing the opportunity set as it stands, rather than on average.

Every other question in this repository asks whether an engine works *on average*.
This module asks a different one: **which of the engines this portfolio can reach is
cheap right now, and which is expensive**, and separately, **whether "cheap" has ever
predicted anything**.

Three rules hold the module together, and they are the whole point.

**A percentile is a measurement; an expected return is a forecast.** ``percentile_rank``
answers "where does today sit inside this series' own history". It is arithmetic on a
sample and it carries no claim about what happens next. Everything predictive lives in
:class:`PredictiveEvidence`, which refuses to report a slope without the smallest slope
its own design could have detected.

**The resolution belongs beside the estimate.** :func:`minimum_detectable_slope` returns
the slope a two-sided test at ``size`` would reject the null for with probability
``power``. An estimate below it is *unresolved*: the study could not have told that
effect apart from zero, so neither the sign nor the magnitude is evidence. Reporting a
point estimate without it is how a repository accumulates results it cannot defend.

**An out-of-sample record outranks an in-sample statistic.** Long-horizon overlapping
regressions on persistent, price-scaled predictors produce large ``t`` statistics from a
handful of independent observations. The valuation study measured the damage: a Newey-West
``t`` of 4.84 and a Hodrick 1B ``t`` of 2.47 on one coefficient, and an out-of-sample
``R**2`` of -0.44 on the same relation. :func:`classify_evidence` therefore requires both
a Hodrick statistic and a positive out-of-sample ``R**2`` before it will say anything
stronger than ``unresolved``.

The cache-touching companion is
:mod:`portfolio_edge.studies._current_pricing_tables`; this file stays pure so the
arithmetic can be tested against independently computed fixtures.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from portfolio_edge.core._types import FloatArray

__all__ = [
    "DEFAULT_POWER",
    "DEFAULT_SIZE",
    "EvidenceVerdict",
    "PredictiveEvidence",
    "PricedLevel",
    "classify_evidence",
    "expanding_percentile_rank",
    "fisher_real_rate",
    "log_value_spread",
    "mark_to_market_log_spread",
    "minimum_detectable_slope",
    "percentile_rank",
    "simple_real_rate",
]

#: Conventional two-sided size and power for :func:`minimum_detectable_slope`. Stated as
#: constants because a resolution figure quoted without them means nothing.
DEFAULT_SIZE: Final = 0.05
DEFAULT_POWER: Final = 0.80

EvidenceVerdict = Literal["supported", "suggestive", "unresolved"]


def percentile_rank(
    history: Sequence[float] | NDArray[np.floating[Any]], value: float
) -> float:
    """The share of ``history`` strictly below ``value``.

    Deliberately the strict-below convention rather than a midrank: it answers "how
    many months has this series spent cheaper than today", which is the sentence a
    reader will write, and it makes an all-time extreme read 0.0 or exactly
    ``1 - 1/n`` rather than something in between.

    Raises:
        ValueError: ``history`` is empty or contains a non-finite value.
    """
    array = np.asarray(history, dtype=np.float64)
    if array.size == 0:
        raise ValueError("history is empty")
    if not np.all(np.isfinite(array)):
        raise ValueError("history contains non-finite values")
    if not math.isfinite(value):
        raise ValueError(f"value must be finite, got {value}")
    return float(np.mean(array < value))


def expanding_percentile_rank(
    values: Sequence[float] | NDArray[np.floating[Any]], burn_in: int
) -> FloatArray:
    """:func:`percentile_rank` of each observation within the history ending at it.

    Strictly backward-looking. A percentile taken against the full sample hands the
    1955 investor a distribution containing 2026, which is the single easiest way to
    manufacture a conditioning rule that could never have been run.
    """
    array = np.asarray(values, dtype=np.float64)
    if burn_in < 1:
        raise ValueError(f"burn_in must be at least 1, got {burn_in}")
    out = np.full(array.size, np.nan)
    for index in range(burn_in, array.size):
        out[index] = float(np.mean(array[: index + 1] < array[index]))
    return out


@dataclass(frozen=True)
class PricedLevel:
    """One priced input, its percentile, and everything needed to audit both.

    Attributes:
        name: What is being measured, in the reader's language.
        value: The level, in ``units``.
        units: Units of ``value``, spelled out. ``pp`` is percentage points.
        as_of: The date the level describes, which is rarely the date it was read.
        percentile: :func:`percentile_rank` of ``value`` within its own history.
        window: ``(first, last)`` labels of the history the percentile is taken over.
        n_observations: Size of that history.
        source: Series identifier and provider.
    """

    name: str
    value: float
    units: str
    as_of: str
    percentile: float
    window: tuple[str, str]
    n_observations: int
    source: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.percentile <= 1.0:
            raise ValueError(f"percentile must lie in [0, 1], got {self.percentile}")
        if self.n_observations < 1:
            raise ValueError("n_observations must be positive")


def simple_real_rate(nominal_percent: float, inflation_percent: float) -> float:
    """``nominal - inflation``, in percentage points.

    The conventional ex-post real cash rate. It is an approximation to
    :func:`fisher_real_rate` and the two differ by about 13 bp at a 3.7% nominal rate
    and 3.5% inflation — immaterial here, but the exact form exists so that no page has
    to guess which one a number came from.
    """
    return nominal_percent - inflation_percent


def fisher_real_rate(nominal_percent: float, inflation_percent: float) -> float:
    """``(1 + n)/(1 + i) - 1``, in percentage points. The exact deflation."""
    if inflation_percent <= -100.0:
        raise ValueError("inflation of -100% or worse has no Fisher real rate")
    gross = (1.0 + nominal_percent / 100.0) / (1.0 + inflation_percent / 100.0)
    return 100.0 * (gross - 1.0)


def log_value_spread(
    high_book_to_market: float, low_book_to_market: float
) -> float:
    """``log(BE/ME of the cheap half) - log(BE/ME of the expensive half)``.

    The value spread: how much cheaper cheap stocks are than expensive ones, on the
    ratio scale, so that a reading of ``log 5`` means the cheap side trades at five
    times the book-to-market of the expensive side regardless of the era's price level.

    Book-to-market rather than price-to-book because the ratio is bounded below at zero
    on this orientation and a growth portfolio's ME can dwarf its BE without the log
    exploding.

    Raises:
        ValueError: Either input is not strictly positive.
    """
    if high_book_to_market <= 0.0 or low_book_to_market <= 0.0:
        raise ValueError(
            "book-to-market ratios must be strictly positive, got "
            f"{high_book_to_market} and {low_book_to_market}"
        )
    return math.log(high_book_to_market) - math.log(low_book_to_market)


def mark_to_market_log_spread(
    formation_log_spread: float,
    *,
    growth_cumulative_return: float,
    value_cumulative_return: float,
) -> float:
    """Move a formation-dated value spread forward to today's prices.

    Ken French's ``BE/ME`` is fixed at formation: book from the prior fiscal year over
    market equity at the prior December. By the time a reader sees it, the market
    equity in the denominator can be twenty months old, and twenty months is long
    enough for the spread to have closed or doubled. Scaling each side by its own
    cumulative return since the formation date restores the price leg.

    Args:
        formation_log_spread: :func:`log_value_spread` at formation.
        growth_cumulative_return: Gross cumulative return of the expensive side,
            formation to now, as a multiple (``1.24`` for +24%).
        value_cumulative_return: The same for the cheap side.

    Returns:
        The spread with both denominators updated.

    Note:
        Supplying **total** returns rather than price returns biases the result
        *downward*, because the cheap side pays the higher dividend and so has its ME
        over-grown by more. The bias is therefore against finding a wide spread, which
        is the direction an honest study wants it in.

    Raises:
        ValueError: Either cumulative return is not strictly positive.
    """
    if growth_cumulative_return <= 0.0 or value_cumulative_return <= 0.0:
        raise ValueError("cumulative returns must be strictly positive multiples")
    return (
        formation_log_spread
        + math.log(growth_cumulative_return)
        - math.log(value_cumulative_return)
    )


def minimum_detectable_slope(
    standard_error: float,
    *,
    power: float = DEFAULT_POWER,
    size: float = DEFAULT_SIZE,
) -> float:
    """The smallest true slope this design would detect, given its own standard error.

    ``(z_{1-size/2} + z_{power}) * se``. A fitted slope below this number is one the
    study could not have distinguished from zero at the stated power, so quoting it as
    a finding — in either direction — claims resolution the design does not have.

    At the conventional 5% two-sided size and 80% power the multiplier is 2.802.

    Raises:
        ValueError: ``standard_error`` is not positive, or ``power`` or ``size`` lies
            outside ``(0, 1)``.
    """
    if standard_error <= 0.0 or not math.isfinite(standard_error):
        raise ValueError(f"standard_error must be positive and finite, got {standard_error}")
    if not 0.0 < size < 1.0:
        raise ValueError(f"size must lie in (0, 1), got {size}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must lie in (0, 1), got {power}")
    multiplier = float(norm.ppf(1.0 - size / 2.0)) + float(norm.ppf(power))
    return multiplier * standard_error


@dataclass(frozen=True)
class PredictiveEvidence:
    """A conditioning variable's record, with the resolution beside the estimate.

    Attributes:
        predictor: The conditioning variable.
        response: What it is asked to predict.
        horizon_years: Forecast horizon.
        n_observations: Overlapping rows in the regression.
        independent_observations: ``n / horizon``, the honest count.
        slope_per_sd: Fitted response, in pp/yr, to a one-standard-deviation move in
            the predictor. Scale-free, so predictors in different units compare.
        minimum_detectable_per_sd: :func:`minimum_detectable_slope` on the same scale.
        t_newey_west: The optimistic statistic, kept so the gap is visible.
        t_hodrick_1b: The statistic whose estimated-quantity count does not grow with
            the horizon.
        r_squared: In-sample.
        r_squared_out_of_sample: Expanding-window, against an expanding-window mean.
        verdict: :func:`classify_evidence`.
    """

    predictor: str
    response: str
    horizon_years: float
    n_observations: int
    independent_observations: float
    slope_per_sd: float
    minimum_detectable_per_sd: float
    t_newey_west: float
    t_hodrick_1b: float
    r_squared: float
    r_squared_out_of_sample: float
    verdict: EvidenceVerdict


def classify_evidence(
    *,
    t_hodrick_1b: float,
    r_squared_out_of_sample: float,
    slope_per_sd: float,
    minimum_detectable_per_sd: float,
) -> EvidenceVerdict:
    """Grade a conditioning relation on inference *and* on its out-of-sample record.

    Three grades and both gates must clear for either of the top two:

    - ``supported``: ``|t| >= 2`` on Hodrick 1B **and** a positive out-of-sample
      ``R**2``. Not "true"; it means the relation survives the inference correction
      that kills most long-horizon results *and* beat a rolling mean on data the
      coefficients had not seen.
    - ``suggestive``: a positive out-of-sample ``R**2`` with ``|t| >= 1.3``, or
      ``|t| >= 2`` with an out-of-sample ``R**2`` at or above zero. One leg holds.
    - ``unresolved``: everything else, including every case where the fitted slope is
      smaller than the design's own minimum detectable slope.

    The thresholds are conventions, not derivations, and they are stated here so a
    reader can move them and see what changes. What is not a convention is the
    requirement that *both* legs be reported: a relation with a large ``t`` and a
    negative out-of-sample ``R**2`` is the exact signature of the CAPE regression, and
    grading it on the ``t`` alone is how that result got its reputation.
    """
    resolved = abs(slope_per_sd) >= minimum_detectable_per_sd
    strong_t = abs(t_hodrick_1b) >= 2.0
    weak_t = abs(t_hodrick_1b) >= 1.3
    if strong_t and r_squared_out_of_sample > 0.0 and resolved:
        return "supported"
    if r_squared_out_of_sample > 0.0 and weak_t:
        return "suggestive"
    if strong_t and r_squared_out_of_sample >= 0.0:
        return "suggestive"
    return "unresolved"
