"""Crisis-conditional breadth: how many independent bets the active legs make when equity falls.

Why this module exists
----------------------
``docs/research/stacking-and-effective-breadth.md`` counts the candidate's five active
legs as ``1' R^-1 1 = 3.71`` effective bets and then lists, as its second open question,
that every correlation behind that number is unconditional: *"3.71 effective bets is an
all-months figure and the tail number is smaller."* This module measures the tail number.

It takes an aligned panel of active-leg returns and a boolean mask selecting the months of
interest, and reports three things inside the mask:

* the pairwise correlation matrix and its ``1' R^-1 1``, with a bootstrap interval;
* each leg's mean active return, with a Newey-West interval and the effective number of
  observations behind it;
* each tilt's correlation with the trend leg specifically, because the page flags IDMO's
  unconditional +0.331 with trend as the pairing most likely to worsen in a crash.

Four masks are supplied by the functions here and the caller chooses which to apply:
:func:`worst_quantile_mask` (the worst decile of some base series),
:func:`window_mask` (a union of named calendar windows), and
:func:`trailing_negative_mask` (months whose trailing twelve-month base return is
negative). The all-true mask reproduces the unconditional figures, and the tables twin
checks that it does before printing anything conditional.

What this module does not do
-----------------------------
It holds **no market data and no cache access**, in the tradition of
:mod:`portfolio_edge.studies.stress_dependence`;
:mod:`portfolio_edge.studies._conditional_breadth_tables` is the one file that reads the
cache and reuses :mod:`portfolio_edge.studies._stacking_tables`' leg construction so the
unconditional numbers are the page's numbers. It estimates no premium and tests no
hypothesis. Every quantity is a descriptive statistic on a supplied series inside a
supplied set of months, and a set of months chosen after seeing history is exploratory by
construction.

Three traps, and the shape of the code that answers them
--------------------------------------------------------
*A conditional correlation is not the unconditional one truncated.* Conditioning on a
third series (equity) rather than on the legs themselves does not impose the
variance-truncation bias :class:`portfolio_edge.studies.stress_dependence.TailDependence`
warns about, but the legs carry no market beta by construction, so what moves inside the
mask is their factor co-movement and nothing else. Read a conditional matrix beside the
unconditional one from the same design.

*A tail sample is small and clustered.* Crisis months arrive in runs, so the number of
months overstates the information. Each leg's mean carries a Newey-West standard error
and the effective observation count ``n * s^2 / S`` it implies, and the bootstrap on the
matrix resamples months independently, which ignores that clustering and makes its
interval optimistic. Both limits are stated in the result rather than in prose.

*A conditional mean is not a rate.* Means are per month and never annualised, because the
mask is not a calendar.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core._types import FloatArray
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.studies.factor_breadth import correlation_matrix, exact_effective_breadth

__all__ = [
    "MINIMUM_CONDITION_MONTHS",
    "ConditionalBreadth",
    "LegConditional",
    "TrendPair",
    "conditional_breadth",
    "effective_observations",
    "trailing_negative_mask",
    "window_mask",
    "worst_quantile_mask",
]

BoolArray = NDArray[np.bool_]

#: The smallest conditional sample this module will describe. A five-leg correlation
#: matrix estimated from fewer months than this is not a matrix, and inverting it is
#: not a breadth count. The floor is deliberately above the five-month floor of
#: :mod:`portfolio_edge.studies.stress_dependence`, which describes one series at a time.
MINIMUM_CONDITION_MONTHS: Final = 24

#: Eigenvalue below which a bootstrap replicate's correlation matrix is treated as
#: singular and the replicate dropped rather than inverted. Matches the tolerance
#: :func:`portfolio_edge.studies.factor_breadth.exact_effective_breadth` raises at.
_SINGULAR_EIGENVALUE: Final = 1e-10

_NORMAL_975: Final = 1.959963984540054


# --------------------------------------------------------------------------- masks


def _base(values: Sequence[float] | FloatArray, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains a non-finite value; drop or repair it upstream")
    return array


def worst_quantile_mask(
    base: Sequence[float] | FloatArray, *, quantile: float = 0.10
) -> BoolArray:
    """True on the ``floor(quantile * n)`` months with the lowest ``base`` return.

    The split is on the base series alone, so the same months are selected for every
    leg measured against it. Ties are broken by position, which cannot matter on a
    return series quoted to more than a handful of decimals.
    """
    b = _base(base, name="base")
    if not 0.0 < quantile < 0.5:
        raise ValueError(f"quantile must lie in (0, 0.5), got {quantile}")
    count = math.floor(quantile * b.size)
    mask = np.zeros(b.size, dtype=bool)
    mask[np.argsort(b, kind="stable")[:count]] = True
    return mask


def window_mask(
    periods: Sequence[str], windows: Mapping[str, tuple[str, str]]
) -> BoolArray:
    """True on every month inside any of the named ``YYYY-MM`` windows, inclusive.

    The comparison is lexicographic, which is correct for zero-padded ISO months and for
    nothing else. A window the panel does not cover contributes no months and is not an
    error here; the caller reports coverage, as
    :func:`portfolio_edge.studies.stress_dependence.episode_returns` does.
    """
    labels = list(periods)
    mask = np.zeros(len(labels), dtype=bool)
    for name, (start, end) in windows.items():
        if start > end:
            raise ValueError(f"window {name!r} runs backwards: {start} to {end}")
        for index, period in enumerate(labels):
            if start <= period <= end:
                mask[index] = True
    return mask


def trailing_negative_mask(
    total_return: Sequence[float] | FloatArray, *, months: int = 12
) -> BoolArray:
    """True where the compounded return over the trailing ``months`` months, ending at
    and **including** the month itself, is negative.

    ``total_return`` is a decimal monthly return, ``0.01`` for one percent. The first
    ``months - 1`` rows cannot be evaluated and are False, so the condition's month count
    is at most ``n - months + 1``. Including the current month makes this a contemporaneous
    regime label, the same convention as the worst-decile mask, rather than a signal
    knowable in advance; a rule that trades on it would use the window ending one month
    earlier.
    """
    r = _base(total_return, name="total_return")
    if months < 1:
        raise ValueError(f"months must be at least 1, got {months}")
    growth = np.cumprod(1.0 + r)
    mask = np.zeros(r.size, dtype=bool)
    for index in range(months - 1, r.size):
        start = growth[index - months] if index >= months else 1.0
        mask[index] = growth[index] / start < 1.0
    return mask


# --------------------------------------------------------------------------- results


@dataclass(frozen=True, slots=True, kw_only=True)
class LegConditional:
    """One leg's mean active return inside the condition, per month, with its interval.

    ``standard_error`` is Newey-West on the time-ordered conditional subsequence, and
    ``effective_months`` is the observation count that error implies: ``n * s^2 / S``
    with ``s^2`` the sample variance and ``S`` the long-run variance, capped at ``n``.
    ``hit_rate`` is the fraction of conditional months with a positive return, so a leg
    that pays on average because of one enormous month is distinguishable from one that
    pays reliably.
    """

    label: str
    months: int
    effective_months: float
    mean: float
    standard_error: float
    lower: float
    upper: float
    hit_rate: float
    worst: float


@dataclass(frozen=True, slots=True, kw_only=True)
class TrendPair:
    """One tilt's correlation with the trend leg inside the condition, with its interval."""

    label: str
    correlation: float
    lower: float
    upper: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ConditionalBreadth:
    """Everything one condition produces, so a caller cannot quote half of it.

    ``effective_bets`` is ``1' R^-1 1`` on the conditional correlation matrix, and the
    interval around it is an iid percentile bootstrap over the conditional months.
    ``resamples_kept`` counts the replicates whose matrix was invertible; a count well
    below ``n_resamples`` is itself evidence that the condition is too thin to invert.
    """

    name: str
    months: int
    share_of_panel: float
    labels: tuple[str, ...]
    correlation: tuple[tuple[float, ...], ...]
    effective_bets: float
    effective_bets_lower: float
    effective_bets_upper: float
    resamples_kept: int
    n_resamples: int
    trend_pairs: tuple[TrendPair, ...]
    legs: tuple[LegConditional, ...]


def effective_observations(values: Sequence[float] | FloatArray) -> float:
    """``n * s^2 / S``, capped at ``n``: the iid-equivalent count behind a HAC mean.

    ``S`` is the Newey-West long-run variance :func:`portfolio_edge.inference.hac.hac_mean`
    uses, so this is exactly the deflation that its standard error applies, stated as a
    count rather than as a multiplier. Positive autocorrelation, the crisis case, lowers
    it; negative autocorrelation would raise it above ``n`` and is capped, because more
    information than the months contain is not a claim this module will print.
    """
    x = _base(values, name="values")
    if x.size < 2:
        return float(x.size)
    estimate = hac_mean(x)
    sample_variance = float(np.mean((x - x.mean()) ** 2))
    if sample_variance == 0.0 or estimate.long_run_variance <= 0.0:
        return float(x.size)
    return float(min(x.size, x.size * sample_variance / estimate.long_run_variance))


def conditional_breadth(
    labels: Sequence[str],
    panel: Sequence[Sequence[float]] | FloatArray,
    mask: Sequence[bool] | BoolArray,
    *,
    name: str,
    trend_label: str,
    rng: np.random.Generator,
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
) -> ConditionalBreadth:
    """Correlation, effective bets, trend pairs and leg means inside ``mask``.

    ``panel`` is ``(months, legs)`` in the caller's units, one column per label, in time
    order. ``mask`` is aligned with its rows. The all-true mask gives the unconditional
    figures, which is how a caller checks this function against
    :func:`portfolio_edge.studies.stacking.effective_bets` before trusting the rest.

    The bootstrap resamples the conditional **rows** independently and with replacement,
    keeping each month's five returns together so the resampled matrix is a real
    correlation matrix. It does not preserve serial dependence between months, which a
    crisis condition has by construction; the interval is therefore narrower than a block
    design would give, and the effective-observation counts on the leg means are the
    better guide to how much the condition really contains.
    """
    columns = tuple(labels)
    values = np.asarray(panel, dtype=np.float64)
    keep = np.asarray(mask, dtype=bool)
    if values.ndim != 2 or values.shape[1] != len(columns):
        raise ValueError(
            f"panel must be (months, {len(columns)}) to match the labels, got {values.shape}"
        )
    if keep.shape != (values.shape[0],):
        raise ValueError(
            f"mask must have one entry per panel row, got {keep.shape} for {values.shape[0]} rows"
        )
    if not np.all(np.isfinite(values)):
        raise ValueError("panel contains a non-finite value; align it upstream")
    if trend_label not in columns:
        raise ValueError(f"trend_label {trend_label!r} is not one of {columns}")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(f"confidence_level must lie in (0, 1), got {confidence_level}")
    if n_resamples < 2:
        raise ValueError("n_resamples must be at least 2")

    selected = values[keep]
    months = int(selected.shape[0])
    if months < MINIMUM_CONDITION_MONTHS:
        raise ValueError(
            f"condition {name!r} selects {months} months, below the "
            f"{MINIMUM_CONDITION_MONTHS}-month floor for a {len(columns)}-leg matrix; "
            "widen the condition or report the panel as unable to answer"
        )

    correlation = correlation_matrix([selected[:, j] for j in range(len(columns))])
    bets = exact_effective_breadth(correlation)
    trend_index = columns.index(trend_label)

    # One bootstrap loop serves both the breadth count and the trend pairs, so their
    # intervals come from the same replicates.
    draws = rng.integers(0, months, size=(n_resamples, months))
    bet_replicates: list[float] = []
    pair_replicates: dict[str, list[float]] = {c: [] for c in columns if c != trend_label}
    for row in draws:
        sample = selected[row]
        if np.any(np.std(sample, axis=0) == 0.0):
            continue
        matrix = np.corrcoef(sample, rowvar=False)
        if float(np.min(np.linalg.eigvalsh(matrix))) <= _SINGULAR_EIGENVALUE:
            continue
        ones = np.ones(len(columns))
        bet_replicates.append(float(ones @ np.linalg.solve(matrix, ones)))
        for j, column in enumerate(columns):
            if column != trend_label:
                pair_replicates[column].append(float(matrix[j, trend_index]))

    alpha = 1.0 - confidence_level
    quantiles = (alpha / 2.0, 1.0 - alpha / 2.0)

    def _interval(replicates: Sequence[float]) -> tuple[float, float]:
        if len(replicates) < 2:
            return (math.nan, math.nan)
        low, high = np.quantile(np.asarray(replicates, dtype=np.float64), quantiles)
        return (float(low), float(high))

    bets_low, bets_high = _interval(bet_replicates)
    pairs = tuple(
        TrendPair(
            label=column,
            correlation=correlation[j][trend_index],
            lower=_interval(pair_replicates[column])[0],
            upper=_interval(pair_replicates[column])[1],
        )
        for j, column in enumerate(columns)
        if column != trend_label
    )

    legs: list[LegConditional] = []
    for j, column in enumerate(columns):
        series = selected[:, j]
        estimate = hac_mean(series)
        half_width = _NORMAL_975 * estimate.standard_error
        legs.append(
            LegConditional(
                label=column,
                months=months,
                effective_months=effective_observations(series),
                mean=estimate.mean,
                standard_error=estimate.standard_error,
                lower=estimate.mean - half_width,
                upper=estimate.mean + half_width,
                hit_rate=float(np.mean(series > 0.0)),
                worst=float(np.min(series)),
            )
        )

    return ConditionalBreadth(
        name=name,
        months=months,
        share_of_panel=months / values.shape[0],
        labels=columns,
        correlation=correlation,
        effective_bets=bets,
        effective_bets_lower=bets_low,
        effective_bets_upper=bets_high,
        resamples_kept=len(bet_replicates),
        n_resamples=n_resamples,
        trend_pairs=pairs,
        legs=tuple(legs),
    )
