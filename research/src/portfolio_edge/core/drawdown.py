"""Maximum drawdown and time under water, in one pass over the equity curve.

Both statistics are properties of the *wealth path*, not of the return series, and
computing them from returns invites an off-by-one on the running peak. The
algorithm below is the one specified in
``docs/research/portfolio-engine-specification.md``, Layer 1:

    peak = equity[0]; mdd = 0; run = 0; tuw = 0
    for v in equity:
        if v >= peak: peak = v; tuw = max(tuw, run); run = 0
        else:         run += 1; mdd = min(mdd, v / peak - 1)
    tuw = max(tuw, run)          # a drawdown still open at the end must count

Maximum drawdown is not scale-free in sample length: it deepens mechanically with
``T``, so it must never be compared across unequal sample lengths.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ._types import FloatArray, FloatVector, as_float_array
from .wealth import NonPositiveWealthError


@dataclass(frozen=True)
class DrawdownSummary:
    """Result of a single pass over an equity curve.

    ``max_drawdown`` is signed and non-positive: ``-0.25`` means a 25% peak-to-trough
    loss. ``max_time_under_water`` counts observations strictly below the running
    peak, including a run still open at the final observation.
    """

    max_drawdown: float
    max_time_under_water: int
    peak_index: int
    trough_index: int
    final_time_under_water: int
    open_at_end: bool
    observations: int


def drawdown_summary(equity: FloatVector) -> DrawdownSummary:
    """Compute maximum drawdown and maximum time under water in O(n)."""
    curve = as_float_array(equity, name="equity")
    if curve.size == 0:
        raise ValueError("equity must contain at least one observation")
    if np.any(curve <= 0.0):
        index = int(np.argmax(curve <= 0.0))
        raise NonPositiveWealthError(index, float(curve[index]))

    peak = float(curve[0])
    peak_index = 0
    max_drawdown = 0.0
    worst_peak_index = 0
    trough_index = 0
    run = 0
    max_run = 0

    for index in range(curve.size):
        value = float(curve[index])
        if value >= peak:
            peak = value
            peak_index = index
            max_run = max(max_run, run)
            run = 0
        else:
            run += 1
            drawdown = value / peak - 1.0
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                trough_index = index
                worst_peak_index = peak_index
    max_run = max(max_run, run)

    return DrawdownSummary(
        max_drawdown=max_drawdown,
        max_time_under_water=max_run,
        peak_index=worst_peak_index,
        trough_index=trough_index,
        final_time_under_water=run,
        open_at_end=run > 0,
        observations=int(curve.size),
    )


def drawdown_series(equity: FloatVector) -> FloatArray:
    """Drawdown at every point, ``equity / running_peak - 1`` (non-positive)."""
    curve = as_float_array(equity, name="equity")
    if curve.size == 0:
        raise ValueError("equity must contain at least one observation")
    if np.any(curve <= 0.0):
        index = int(np.argmax(curve <= 0.0))
        raise NonPositiveWealthError(index, float(curve[index]))
    running_peak = np.maximum.accumulate(curve)
    return np.asarray(curve / running_peak - 1.0, dtype=np.float64)


def max_drawdown(equity: FloatVector) -> float:
    """Maximum peak-to-trough loss as a signed, non-positive fraction."""
    return drawdown_summary(equity).max_drawdown


def time_under_water(equity: FloatVector) -> int:
    """Longest run of observations strictly below the running peak."""
    return drawdown_summary(equity).max_time_under_water
