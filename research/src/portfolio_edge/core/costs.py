"""Transaction costs, charged against trades rather than against results.

The rule this module exists to enforce: *costs must alter the trading rule, not
appear as a constant haircut after the backtest*
(``docs/research/portfolio-edge-research-framework.md``, "Factors and manager
alpha"). Every function here takes a trade, not a return series.

Two calibrations are carried, both with their units stated because both are easy
to misread by two orders of magnitude:

* **Cost by turnover.** ``cost_bp_per_month ~= k * one_sided_turnover_pct``, fitted
  to the Novy-Marx and Velikov (2016) tier means. ``k`` runs 1.57-1.71 across
  tiers; use ``K_FLOOR = 1.0`` for the optimistic column (patient limit orders,
  liquid large caps) and ``K_PESSIMISTIC = 1.7`` for the default. Turnover is in
  *percent*, cost in *basis points*.
* **Square-root impact.** ``bp ~= c * sqrt(|Q / V|)`` with ``c ~= 11`` for US
  stocks and the exponent treated as ``0.5 +/- 0.1`` because Almgren et al. (2005)
  prefer 3/5. ``Q / V`` is participation in *percent of daily volume*: at 10% of
  daily volume ``11 * sqrt(10) = 34.8`` bp, consistent with the 32-43 bp reported
  in the framework, whereas reading ``Q / V`` as a fraction would give 3.5 bp.

At retail scale trade/ADV is far below 0.1%, so the impact term all but vanishes
and the spread term binds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from ._types import FloatArray, FloatVector, as_float_array

K_FLOOR = 1.0
"""Conservative floor for the cost-by-turnover coefficient (optimistic column)."""

K_PESSIMISTIC = 1.7
"""Default cost-by-turnover coefficient: market orders, full universe."""

IMPACT_COEFFICIENT_US_STOCKS_BP = 11.0
"""``c`` in ``bp = c * sqrt(participation_pct)`` for US stocks."""

IMPACT_EXPONENT = 0.5
"""Nominal square-root exponent. Almgren et al. (2005) prefer 3/5; treat as 0.5 +/- 0.1."""

MAX_RETAIL_MONTHLY_TURNOVER_PCT = 50.0
"""Above this one-sided monthly turnover, treat a strategy as not retail-implementable."""


class NegativeWealthAfterCostsError(ValueError):
    """Raised when charging a trade's cost would drive wealth to zero or below."""

    def __init__(self, wealth: float, cost: float) -> None:
        self.wealth = wealth
        self.cost = cost
        super().__init__(
            f"cost {cost!r} would reduce wealth {wealth!r} to {wealth - cost!r}; "
            "the position is not fundable"
        )


class CostModel(Protocol):
    """A model that prices a vector of signed trade notionals."""

    def cost(self, trade_notional: FloatVector, portfolio_value: float) -> float:
        """Return the non-negative cash cost of executing ``trade_notional``."""


@dataclass(frozen=True)
class ProportionalCostModel:
    """A flat cost in basis points of traded notional, applied to each side.

    This is the spread-plus-commission model appropriate at retail scale, where
    market impact is negligible.
    """

    cost_bp: float = 0.0

    def __post_init__(self) -> None:
        if self.cost_bp < 0.0:
            raise ValueError(f"cost_bp cannot be negative, got {self.cost_bp}")

    def cost(self, trade_notional: FloatVector, portfolio_value: float) -> float:
        traded = _traded_notional(trade_notional, portfolio_value)
        return traded * self.cost_bp / 1e4


@dataclass(frozen=True)
class TurnoverCostModel:
    """``cost_bp = k * one_sided_turnover_pct``, the Novy-Marx-Velikov fit.

    ``k`` defaults to the pessimistic 1.7. The relationship is linear in turnover,
    so the resulting cash cost is exactly proportional to traded notional; the
    turnover framing is kept because that is the form the published table supports
    and the form in which the retail-implementability limit is stated.
    """

    k: float = K_PESSIMISTIC

    def __post_init__(self) -> None:
        if self.k < 0.0:
            raise ValueError(f"k cannot be negative, got {self.k}")

    def cost_bp_per_period(self, one_sided_turnover_pct: float) -> float:
        """Cost in basis points for a period with the given one-sided turnover (%)."""
        if one_sided_turnover_pct < 0.0:
            raise ValueError("turnover cannot be negative")
        return self.k * one_sided_turnover_pct

    def cost(self, trade_notional: FloatVector, portfolio_value: float) -> float:
        traded = _traded_notional(trade_notional, portfolio_value)
        if portfolio_value <= 0.0:
            raise ValueError(f"portfolio_value must be positive, got {portfolio_value}")
        turnover_pct = 100.0 * 0.5 * traded / portfolio_value
        return portfolio_value * self.cost_bp_per_period(turnover_pct) / 1e4


@dataclass(frozen=True)
class SquareRootImpactModel:
    """``bp = coefficient_bp * participation_pct ** exponent``.

    ``participation_pct`` is the order size as a *percentage* of daily volume. This
    is not a :class:`CostModel`: pricing impact needs a volume input that a weight
    vector does not carry.
    """

    coefficient_bp: float = IMPACT_COEFFICIENT_US_STOCKS_BP
    exponent: float = IMPACT_EXPONENT

    def __post_init__(self) -> None:
        if self.coefficient_bp < 0.0:
            raise ValueError("coefficient_bp cannot be negative")
        if not 0.0 < self.exponent <= 1.0:
            raise ValueError(f"exponent must lie in (0, 1], got {self.exponent}")

    def impact_bp(self, participation_pct: float) -> float:
        """Impact in basis points for an order at ``participation_pct`` of daily volume."""
        if participation_pct < 0.0:
            raise ValueError("participation cannot be negative")
        return float(self.coefficient_bp * participation_pct**self.exponent)

    def impact_cost(self, trade_notional: FloatVector, daily_volume: FloatVector) -> float:
        """Cash impact cost of a trade vector against per-asset daily volume (cash)."""
        trades = as_float_array(trade_notional, name="trade_notional")
        volume = as_float_array(daily_volume, name="daily_volume")
        if trades.shape != volume.shape:
            raise ValueError("trade_notional and daily_volume must have the same length")
        if np.any(volume <= 0.0):
            raise ValueError("daily_volume must be strictly positive")
        participation_pct = 100.0 * np.abs(trades) / volume
        impact = self.coefficient_bp * np.power(participation_pct, self.exponent)
        return float(np.sum(np.abs(trades) * impact / 1e4))


def one_sided_turnover(weights_before: FloatVector, weights_after: FloatVector) -> float:
    """``0.5 * sum |w_after - w_before|``, the Novy-Marx-Velikov convention.

    Returned as a fraction; multiply by 100 for the percent figure the cost-by-
    turnover rule expects.
    """
    before = as_float_array(weights_before, name="weights_before")
    after = as_float_array(weights_after, name="weights_after")
    if before.shape != after.shape:
        raise ValueError("weight vectors must have the same length")
    return 0.5 * float(np.sum(np.abs(after - before)))


def trades_from_weights(
    weights_before: FloatVector,
    weights_after: FloatVector,
    portfolio_value: float,
) -> FloatArray:
    """Signed cash trade per asset needed to move from one weight vector to another."""
    before = as_float_array(weights_before, name="weights_before")
    after = as_float_array(weights_after, name="weights_after")
    if before.shape != after.shape:
        raise ValueError("weight vectors must have the same length")
    if portfolio_value <= 0.0:
        raise ValueError(f"portfolio_value must be positive, got {portfolio_value}")
    return np.asarray((after - before) * portfolio_value, dtype=np.float64)


def apply_trade_costs(
    wealth: float,
    trade_notional: FloatVector,
    model: CostModel,
) -> float:
    """Charge ``model``'s cost for ``trade_notional`` against ``wealth``.

    Guarantees, and the reason this is a single chokepoint: the returned wealth is
    never greater than ``wealth``, and a trade vector of zeros leaves it unchanged.
    """
    if wealth <= 0.0:
        raise ValueError(f"wealth must be positive, got {wealth}")
    cost = model.cost(trade_notional, wealth)
    if cost < 0.0:
        raise ValueError(f"cost model returned a negative cost {cost!r}")
    if cost >= wealth:
        raise NegativeWealthAfterCostsError(wealth, cost)
    return wealth - cost


def implied_turnover_coefficient(cost_bp: float, one_sided_turnover_pct: float) -> float:
    """``k = cost_bp / turnover_pct`` — the fit behind the cost-by-turnover rule."""
    if one_sided_turnover_pct <= 0.0:
        raise ValueError("turnover must be positive to identify k")
    return cost_bp / one_sided_turnover_pct


def is_retail_implementable(one_sided_monthly_turnover_pct: float) -> bool:
    """Whether monthly one-sided turnover is inside the retail-implementable limit."""
    if one_sided_monthly_turnover_pct < 0.0:
        raise ValueError("turnover cannot be negative")
    return one_sided_monthly_turnover_pct <= MAX_RETAIL_MONTHLY_TURNOVER_PCT


def participation_from_notional(trade_notional: float, daily_volume: float) -> float:
    """Order size as a percentage of daily volume, the unit the impact law expects."""
    if daily_volume <= 0.0:
        raise ValueError("daily_volume must be strictly positive")
    return 100.0 * abs(trade_notional) / daily_volume


def _traded_notional(trade_notional: FloatVector, portfolio_value: float) -> float:
    trades = as_float_array(trade_notional, name="trade_notional")
    if not math.isfinite(portfolio_value):
        raise ValueError("portfolio_value must be finite")
    return float(np.sum(np.abs(trades)))
