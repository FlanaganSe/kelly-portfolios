"""Rebalancing policies simulated from identical starting weights and cash flows.

Rebalancing is a portfolio-maintenance policy, not assumed alpha. Two results from
``docs/research/portfolio-edge-research-framework.md`` shape this module:

* **Diversification return is measured against a benchmark nobody can hold.** It is
  defined as ``g_p - sum_i w_i g_i``, and ``sum_i w_i g_i`` is not the growth rate of
  any investable portfolio (Willenbrock 2011). The investable comparison is
  buy-and-hold, whose geometric mean may be higher or lower.
* **A two-period rebalance is a short straddle on relative performance.** For two
  assets over two periods the identity is exact:
  ``R_REBAL - R_HOLD = -w_S w_B kappa_1 kappa_2`` with
  ``kappa_t = r_{S,t} - r_{B,t}`` (Rattray et al. 2020). Rebalancing therefore loses
  when relative performance trends and gains only on reversal.

Because of the second result, the correct diagnostic for whether rebalancing adds
value is the **serial dependence of kappa**, not the diversification-return
statistic. :func:`kappa_series` and :func:`kappa_autocorrelation` exist to make that
diagnostic the easy thing to compute.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

import numpy as np

from ._types import FloatArray, FloatMatrix, FloatVector, as_float_array, as_float_matrix
from .costs import CostModel, ProportionalCostModel, one_sided_turnover
from .portfolio import check_weights_sum_to_one, normalise_weights
from .wealth import CashFlowTiming, NonPositiveWealthError


@dataclass(frozen=True)
class BuyAndHold:
    """Never trade. Weights drift with relative performance; cash flows go pro rata."""


@dataclass(frozen=True)
class CalendarRebalance:
    """Restore target weights every ``interval`` periods, starting at period 0."""

    interval: int

    def __post_init__(self) -> None:
        if self.interval < 1:
            raise ValueError(f"interval must be at least 1, got {self.interval}")


@dataclass(frozen=True)
class RelativeThreshold:
    """Restore target weights when any weight drifts more than ``band`` *relatively*.

    The trigger is ``max_i |w_i / w_target_i - 1| > band``, so a band of 0.25 fires
    when a 40% target has become 50% or 30%. Relative bands are the form the
    framework names; absolute bands treat a 2% sleeve and a 60% sleeve identically.
    """

    band: float

    def __post_init__(self) -> None:
        if self.band <= 0.0:
            raise ValueError(f"band must be positive, got {self.band}")


@dataclass(frozen=True)
class CashFlowDirected:
    """Never trade discretionarily; steer with contributions and withdrawals only.

    Contributions buy the most underweight assets first; withdrawals sell the most
    overweight. Turnover beyond the cash flow itself is zero, which is why this is
    the cheapest policy and the one a taxable accumulating investor should be
    compared against.
    """


RebalancePolicy = BuyAndHold | CalendarRebalance | RelativeThreshold | CashFlowDirected


@dataclass(frozen=True, eq=False)
class RebalanceResult:
    """Full path of a simulated policy: wealth, weights, trades, turnover, costs."""

    equity_curve: FloatArray
    weights: FloatArray
    trades: FloatArray
    turnover: FloatArray
    costs: FloatArray
    cash_flows: FloatArray
    policy: RebalancePolicy

    @property
    def terminal_wealth(self) -> float:
        return float(self.equity_curve[-1])

    @property
    def total_turnover(self) -> float:
        return float(np.sum(self.turnover))

    @property
    def total_costs(self) -> float:
        return float(np.sum(self.costs))


def simulate(
    asset_returns: FloatMatrix,
    target_weights: FloatVector,
    policy: RebalancePolicy,
    *,
    initial_wealth: float = 1.0,
    cash_flows: FloatVector | None = None,
    cost_model: CostModel | None = None,
    cash_flow_timing: CashFlowTiming = CashFlowTiming.BEGINNING,
    weight_tolerance: float = 1e-9,
) -> RebalanceResult:
    """Run one rebalancing policy over a ``(T, N)`` matrix of simple asset returns.

    Order of operations within period ``t``, all declared rather than inferred:

    1. the cash flow is applied (``BEGINNING`` timing) and allocated per the policy;
    2. the policy decides whether to restore ``target_weights``, producing trades;
    3. costs are charged against the trades;
    4. asset returns for period ``t`` are applied;
    5. the cash flow is applied (``END`` timing), so it earns no return that period.

    Every policy sees identical starting weights, returns, and cash flows, which is
    the comparison the framework requires.
    """
    returns = as_float_matrix(asset_returns, name="asset_returns")
    periods, n_assets = returns.shape
    target = as_float_array(target_weights, name="target_weights")
    if target.size != n_assets:
        raise ValueError("target_weights length must match the number of assets")
    check_weights_sum_to_one(target, tolerance=weight_tolerance)
    if initial_wealth <= 0.0:
        raise NonPositiveWealthError(0, initial_wealth)
    flows = (
        np.zeros(periods, dtype=np.float64)
        if cash_flows is None
        else as_float_array(cash_flows, name="cash_flows")
    )
    if flows.size != periods:
        raise ValueError("cash_flows length must match the number of periods")
    model: CostModel = ProportionalCostModel() if cost_model is None else cost_model

    values = initial_wealth * target
    weights_path = np.empty((periods + 1, n_assets), dtype=np.float64)
    equity = np.empty(periods + 1, dtype=np.float64)
    trades = np.zeros((periods, n_assets), dtype=np.float64)
    turnover = np.zeros(periods, dtype=np.float64)
    costs = np.zeros(periods, dtype=np.float64)
    weights_path[0] = target
    equity[0] = initial_wealth

    for t in range(periods):
        if cash_flow_timing is CashFlowTiming.BEGINNING:
            values = _apply_cash_flow(values, float(flows[t]), target, policy)

        wealth = float(np.sum(values))
        if wealth <= 0.0:
            raise NonPositiveWealthError(t + 1, wealth)
        weights_before = values / wealth

        if _should_rebalance(policy, t, weights_before, target):
            desired = wealth * target
            period_trades = desired - values
            trades[t] = period_trades
            turnover[t] = one_sided_turnover(weights_before, target)
            cost = model.cost(period_trades, wealth)
            if cost < 0.0:
                raise ValueError(f"cost model returned a negative cost {cost!r}")
            costs[t] = cost
            if cost >= wealth:
                raise NonPositiveWealthError(t + 1, wealth - cost)
            values = desired * (1.0 - cost / wealth)

        values = values * (1.0 + returns[t])

        if cash_flow_timing is CashFlowTiming.END:
            values = _apply_cash_flow(values, float(flows[t]), target, policy)

        wealth = float(np.sum(values))
        if wealth <= 0.0:
            raise NonPositiveWealthError(t + 1, wealth)
        equity[t + 1] = wealth
        weights_path[t + 1] = values / wealth

    return RebalanceResult(
        equity_curve=equity,
        weights=weights_path,
        trades=trades,
        turnover=turnover,
        costs=costs,
        cash_flows=flows,
        policy=policy,
    )


def kappa_series(asset_returns: FloatMatrix) -> FloatArray:
    """``kappa_t = r_{0,t} - r_{1,t}``, the relative-performance difference.

    Defined for exactly two assets, which is the setting in which the exact
    rebalancing identity holds.
    """
    returns = as_float_matrix(asset_returns, name="asset_returns")
    if returns.shape[1] != 2:
        raise ValueError(
            f"kappa is defined for exactly two assets, got {returns.shape[1]}"
        )
    return np.asarray(returns[:, 0] - returns[:, 1], dtype=np.float64)


def kappa_autocorrelation(kappa: FloatVector, *, lag: int = 1) -> float:
    """Serial correlation of ``kappa`` at ``lag``.

    This, not the diversification-return statistic, is the diagnostic for whether
    rebalancing should be expected to add value: rebalancing is short relative-
    performance continuation, so positive autocorrelation in ``kappa`` predicts that
    rebalancing loses.
    """
    series = as_float_array(kappa, name="kappa")
    if lag < 1:
        raise ValueError(f"lag must be at least 1, got {lag}")
    if series.size <= lag + 1:
        raise ValueError(
            f"need more than {lag + 1} observations to estimate lag-{lag} autocorrelation"
        )
    centred = series - float(np.mean(series))
    denominator = float(np.dot(centred, centred))
    if denominator <= 0.0:
        raise ValueError("kappa has zero variance; its autocorrelation is undefined")
    return float(np.dot(centred[lag:], centred[:-lag]) / denominator)


def two_period_rebalance_advantage(first_weight: float, kappa_1: float, kappa_2: float) -> float:
    """``R_REBAL - R_HOLD = -w_S w_B kappa_1 kappa_2`` for two assets over two periods.

    Exact, not an approximation. ``first_weight`` is ``w_S``; ``w_B = 1 - w_S``.
    Source: Rattray, Granger, Harvey and Van Hemert (2020), "Strategic rebalancing".
    """
    return -first_weight * (1.0 - first_weight) * kappa_1 * kappa_2


def diversification_return(
    weights: FloatVector,
    component_growth_rates: FloatVector,
    portfolio_growth_rate: float,
) -> float:
    """``g_p - sum_i w_i g_i``.

    Positive by construction for a rebalanced long-only portfolio of assets that are
    not perfectly co-moving in log space. It is *not* an alpha: the subtrahend is the
    weighted growth of the components, which nobody can hold.
    """
    w = as_float_array(weights, name="weights")
    g = as_float_array(component_growth_rates, name="component_growth_rates")
    if w.shape != g.shape:
        raise ValueError("weights and component_growth_rates must have the same length")
    return portfolio_growth_rate - float(np.dot(w, g))


def _should_rebalance(
    policy: RebalancePolicy,
    period_index: int,
    weights: FloatArray,
    target: FloatArray,
) -> bool:
    if isinstance(policy, BuyAndHold | CashFlowDirected):
        return False
    if isinstance(policy, CalendarRebalance):
        return period_index % policy.interval == 0
    if isinstance(policy, RelativeThreshold):
        if np.any(target <= 0.0):
            raise ValueError("a relative threshold needs strictly positive target weights")
        return bool(np.max(np.abs(weights / target - 1.0)) > policy.band)
    assert_never(policy)


def _apply_cash_flow(
    values: FloatArray,
    cash_flow: float,
    target: FloatArray,
    policy: RebalancePolicy,
) -> FloatArray:
    """Allocate an external cash flow across assets under the policy's rule."""
    if cash_flow == 0.0:
        return values
    wealth = float(np.sum(values))
    if wealth <= 0.0:
        raise ValueError("cannot allocate a cash flow into a non-positive portfolio")
    if wealth + cash_flow <= 0.0:
        raise NonPositiveWealthError(0, wealth + cash_flow)

    if not isinstance(policy, CashFlowDirected):
        # Pro rata at current weights: no rebalancing effect, zero turnover.
        return np.asarray(values + cash_flow * (values / wealth), dtype=np.float64)

    desired = (wealth + cash_flow) * target
    if cash_flow > 0.0:
        deficits = np.maximum(desired - values, 0.0)
        total_deficit = float(np.sum(deficits))
        if total_deficit <= cash_flow:
            remainder = cash_flow - total_deficit
            return np.asarray(values + deficits + remainder * target, dtype=np.float64)
        return np.asarray(values + cash_flow * deficits / total_deficit, dtype=np.float64)

    withdrawal = -cash_flow
    surpluses = np.maximum(values - desired, 0.0)
    total_surplus = float(np.sum(surpluses))
    if total_surplus <= withdrawal:
        remainder = withdrawal - total_surplus
        reduced = values - surpluses
        residual_total = float(np.sum(reduced))
        if residual_total <= remainder:
            raise NonPositiveWealthError(0, residual_total - remainder)
        return np.asarray(
            reduced - remainder * (reduced / residual_total), dtype=np.float64
        )
    return np.asarray(values - withdrawal * surpluses / total_surplus, dtype=np.float64)


def buy_and_hold_weights(
    initial_weights: FloatVector,
    asset_returns: FloatMatrix,
) -> FloatArray:
    """Weight path of an untouched portfolio, shape ``(T + 1, N)``."""
    weights = normalise_weights(initial_weights)
    returns = as_float_matrix(asset_returns, name="asset_returns")
    if returns.shape[1] != weights.size:
        raise ValueError("initial_weights length must match the number of assets")
    path = np.empty((returns.shape[0] + 1, weights.size), dtype=np.float64)
    path[0] = weights
    for t in range(returns.shape[0]):
        grown = path[t] * (1.0 + returns[t])
        total = float(np.sum(grown))
        if total <= 0.0:
            raise NonPositiveWealthError(t + 1, total)
        path[t + 1] = grown / total
    return path
