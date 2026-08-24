"""Wealth paths: equity curves, terminal wealth, and external cash flows.

The one rule this module enforces without exception is that wealth must stay
strictly positive. A path that reaches zero or below is not a small number to be
carried forward as a ``NaN``; it is insolvency, and every statistic computed after
it is meaningless. :class:`NonPositiveWealthError` names the period it happened in.

Cash-flow timing is declared, never inferred. A contribution made *before* the
period's return earns that return; one made *after* it does not, and the terminal
difference over a long accumulation is large.
"""

from __future__ import annotations

from enum import Enum

import numpy as np

from ._types import FloatArray, FloatVector, as_float_array


class NonPositiveWealthError(ValueError):
    """Raised when a wealth path reaches or crosses zero."""

    def __init__(self, index: int, wealth: float) -> None:
        self.index = index
        self.wealth = wealth
        super().__init__(
            f"wealth reached {wealth!r} at index {index}; the path is insolvent and "
            "cannot be continued"
        )


class CashFlowTiming(Enum):
    """When an external cash flow is applied relative to the period's return.

    ``BEGINNING``  the flow is added before the return, so it earns that return.
    ``END``        the flow is added after the return, so it does not.
    """

    BEGINNING = "beginning"
    END = "end"


def equity_curve(returns: FloatVector, *, initial_wealth: float = 1.0) -> FloatArray:
    """Wealth path implied by ``returns``, length ``len(returns) + 1``.

    Element 0 is ``initial_wealth``; element ``t + 1`` is wealth after return ``t``.
    """
    array = as_float_array(returns, name="returns")
    if initial_wealth <= 0.0:
        raise NonPositiveWealthError(0, initial_wealth)
    curve = np.empty(array.size + 1, dtype=np.float64)
    curve[0] = initial_wealth
    wealth = initial_wealth
    for index, period_return in enumerate(array):
        wealth *= 1.0 + float(period_return)
        if wealth <= 0.0:
            raise NonPositiveWealthError(index + 1, wealth)
        curve[index + 1] = wealth
    return curve


def terminal_wealth(returns: FloatVector, *, initial_wealth: float = 1.0) -> float:
    """Wealth after compounding every return in ``returns``."""
    return float(equity_curve(returns, initial_wealth=initial_wealth)[-1])


def equity_curve_with_cash_flows(
    returns: FloatVector,
    cash_flows: FloatVector,
    *,
    initial_wealth: float = 1.0,
    timing: CashFlowTiming = CashFlowTiming.BEGINNING,
) -> FloatArray:
    """Wealth path with an external contribution or withdrawal in each period.

    ``cash_flows[t]`` is signed: positive contributes, negative withdraws. It must
    be the same length as ``returns``. The returned curve has length
    ``len(returns) + 1`` and records wealth *after* both the return and the flow
    of each period, whichever order ``timing`` declares.
    """
    array = as_float_array(returns, name="returns")
    flows = as_float_array(cash_flows, name="cash_flows")
    if flows.shape != array.shape:
        raise ValueError(
            f"cash_flows must be the same length as returns ({array.size}), "
            f"got {flows.size}"
        )
    if initial_wealth <= 0.0:
        raise NonPositiveWealthError(0, initial_wealth)

    curve = np.empty(array.size + 1, dtype=np.float64)
    curve[0] = initial_wealth
    wealth = initial_wealth
    for index in range(array.size):
        if timing is CashFlowTiming.BEGINNING:
            wealth += float(flows[index])
            if wealth <= 0.0:
                raise NonPositiveWealthError(index + 1, wealth)
            wealth *= 1.0 + float(array[index])
        else:
            wealth *= 1.0 + float(array[index])
            if wealth <= 0.0:
                raise NonPositiveWealthError(index + 1, wealth)
            wealth += float(flows[index])
        if wealth <= 0.0:
            raise NonPositiveWealthError(index + 1, wealth)
        curve[index + 1] = wealth
    return curve


def returns_from_equity_curve(equity: FloatVector) -> FloatArray:
    """Simple returns implied by a wealth path with no external cash flows.

    Applying this to a curve that had contributions or withdrawals produces
    money-weighted nonsense; use the return series that generated the curve.
    """
    curve = as_float_array(equity, name="equity")
    if curve.size < 2:
        raise ValueError("an equity curve needs at least two points to imply a return")
    if np.any(curve <= 0.0):
        index = int(np.argmax(curve <= 0.0))
        raise NonPositiveWealthError(index, float(curve[index]))
    return np.asarray(curve[1:] / curve[:-1] - 1.0, dtype=np.float64)


def log_returns_from_equity_curve(equity: FloatVector) -> FloatArray:
    """Log returns implied by a wealth path, ``ln(W_t / W_{t-1})``."""
    curve = as_float_array(equity, name="equity")
    if curve.size < 2:
        raise ValueError("an equity curve needs at least two points to imply a return")
    if np.any(curve <= 0.0):
        index = int(np.argmax(curve <= 0.0))
        raise NonPositiveWealthError(index, float(curve[index]))
    return np.asarray(np.log(curve[1:]) - np.log(curve[:-1]), dtype=np.float64)
