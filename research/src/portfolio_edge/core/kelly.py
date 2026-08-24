"""Growth-rate algebra for leveraged and multi-asset log-wealth objectives.

This module computes growth rates. It does **not** recommend an allocation, and no
function here returns anything labelled optimal for an investor. The reasons are
recorded in ``docs/research/portfolio-edge-research-framework.md`` and are worth
restating because they bound what the numbers below may be used for:

* ``L* = (mu - r) / sigma**2`` is the growth-optimal exposure of an *idealised
  one-risky-asset diffusion* with known parameters, continuous rebalancing, zero
  costs and a single financing rate. Its numerator is an estimated expected return,
  and at ``sigma = 18%`` over 20 years ``SE(L*) ~= 1.24`` exposure units before any
  allowance for volatility error, non-stationarity, tails, or costs.
* The much-repeated ``L* ~= 1.54`` is not a measured S&P quantity. It comes from the
  stylised illustrative parameters ``mu - r = 5%``, ``sigma = 18%`` used in the
  fixtures below.
* Growth falls back to exactly the risk-free rate at ``2 L*`` by the symmetry of the
  parabola, and turns negative at the positive root of
  ``L**2 - 2 L* L - 2 r / sigma**2 = 0``. Neither is a ruin boundary, a margin limit,
  or a universal leverage ceiling. Continuous GBM never reaches zero in finite time;
  real ruin comes from jumps, discrete trading, liabilities and forced liquidation,
  none of which this algebra contains.
* Maximising time-average growth and maximising expected log utility are the same
  optimisation, and both are the ``gamma = 1`` case of Merton's
  ``L* = (mu - r) / (gamma sigma**2)``. Attribute the algebra to Ito, Kelly, Latane
  and Merton.

For discrete multi-asset returns the actual problem is
``max_w E[log(1 + w' R_net)]`` subject to ``1 + w' R_net > 0`` almost surely. A
Gaussian model of simple returns has unbounded losses and therefore makes expected
log wealth undefined for every nonzero unconstrained exposure, so
:func:`expected_log_wealth` refuses any scenario set that breaches the constraint.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from ._types import FloatArray, FloatMatrix, FloatVector, as_float_array, as_float_matrix


class NonPositiveWealthScenarioError(ValueError):
    """Raised when a scenario set implies ``1 + w' R <= 0`` for some scenario."""

    def __init__(
        self,
        scenario_index: int,
        wealth_relative: float,
        asset_index: int | None = None,
    ) -> None:
        self.scenario_index = scenario_index
        self.wealth_relative = wealth_relative
        self.asset_index = asset_index
        where = (
            f"scenario {scenario_index}"
            if asset_index is None
            else f"asset {asset_index} in scenario {scenario_index}"
        )
        super().__init__(
            f"{where} implies a wealth relative of {wealth_relative!r}; "
            "expected log wealth is undefined and this allocation is rejected"
        )


@dataclass(frozen=True)
class GrowthCurve:
    """The closed-form landmarks of the stylised one-asset growth parabola."""

    optimal_leverage: float
    peak_growth: float
    risk_free_rate: float
    cash_equivalent_leverage: float
    zero_growth_leverage: float


def kelly_leverage(*, excess_return: float, volatility: float) -> float:
    """``L* = (mu - r) / sigma**2``.

    ``excess_return`` must be the arithmetic Ito drift in excess of cash and
    ``volatility`` the instantaneous volatility; substituting a CAGR or a coarsely
    sampled volatility gives the wrong answer.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    return excess_return / volatility**2


def growth_rate_quadratic(
    leverage: float,
    *,
    excess_return: float,
    volatility: float,
    risk_free_rate: float,
) -> float:
    """``g(L) = r + L (mu - r) - 0.5 L**2 sigma**2``, the stylised smooth model."""
    if volatility < 0.0:
        raise ValueError("volatility cannot be negative")
    return (
        risk_free_rate
        + leverage * excess_return
        - 0.5 * leverage**2 * volatility**2
    )


def growth_rate_vertex(
    leverage: float,
    *,
    excess_return: float,
    volatility: float,
    risk_free_rate: float,
) -> float:
    """``g(L) = r + 0.5 sigma**2 [(L*)**2 - (L - L*)**2]``.

    Algebraically identical to :func:`growth_rate_quadratic` but written about its
    vertex, which makes the symmetry ``g(0) = g(2 L*) = r`` visible without a
    separate derivation. Re-derived from Ito's lemma rather than copied.
    """
    optimal = kelly_leverage(excess_return=excess_return, volatility=volatility)
    return risk_free_rate + 0.5 * volatility**2 * (optimal**2 - (leverage - optimal) ** 2)


def peak_growth_rate(
    *, excess_return: float, volatility: float, risk_free_rate: float
) -> float:
    """``g(L*) = r + (mu - r)**2 / (2 sigma**2)``."""
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    return risk_free_rate + excess_return**2 / (2.0 * volatility**2)


def cash_equivalent_leverage(*, excess_return: float, volatility: float) -> float:
    """``2 L*``: the exposure at which modelled growth falls back to the cash rate.

    For an investor whose objective is this model's asymptotic log-growth rate this
    is the cash-relative model boundary. It is not a ruin boundary.
    """
    return 2.0 * kelly_leverage(excess_return=excess_return, volatility=volatility)


def zero_growth_leverage(
    *, excess_return: float, volatility: float, risk_free_rate: float
) -> float:
    """Positive root of ``L**2 - 2 L* L - 2 r / sigma**2 = 0``."""
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    optimal = kelly_leverage(excess_return=excess_return, volatility=volatility)
    discriminant = optimal**2 + 2.0 * risk_free_rate / volatility**2
    if discriminant < 0.0:
        raise ValueError(
            "no real zero-growth leverage exists for these parameters "
            f"(discriminant {discriminant!r})"
        )
    return optimal + math.sqrt(discriminant)


def growth_curve(
    *, excess_return: float, volatility: float, risk_free_rate: float
) -> GrowthCurve:
    """All four landmarks of the stylised growth parabola in one object."""
    return GrowthCurve(
        optimal_leverage=kelly_leverage(excess_return=excess_return, volatility=volatility),
        peak_growth=peak_growth_rate(
            excess_return=excess_return,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
        ),
        risk_free_rate=risk_free_rate,
        cash_equivalent_leverage=cash_equivalent_leverage(
            excess_return=excess_return, volatility=volatility
        ),
        zero_growth_leverage=zero_growth_leverage(
            excess_return=excess_return,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
        ),
    )


def kinked_growth_rate(
    leverage: float,
    *,
    mean_return: float,
    volatility: float,
    lending_rate: float,
    borrow_spread: float,
    instrument_cost: Callable[[float], float] | None = None,
) -> float:
    """``g(L) ~= r_l + L (mu - r_l) - s_b (L - 1)+ - C(L) - 0.5 L**2 sigma**2``.

    The stylised smooth model assumes one financing rate. This variant kinks at
    one-times exposure: borrowing above 1x pays ``borrow_spread`` on the borrowed
    portion. ``instrument_cost`` is ``C(L)``, an arbitrary non-negative cost of
    holding exposure ``L`` (ETF fees, roll cost, borrow); it defaults to zero.

    This is still an approximation, not an executable financing model: the optimum
    and the boundaries above do not survive unchanged when margin forces liquidation.
    """
    if volatility < 0.0:
        raise ValueError("volatility cannot be negative")
    if borrow_spread < 0.0:
        raise ValueError("borrow_spread cannot be negative")
    cost = 0.0 if instrument_cost is None else instrument_cost(leverage)
    if cost < 0.0:
        raise ValueError(f"instrument_cost returned a negative cost {cost!r}")
    borrowed = max(leverage - 1.0, 0.0)
    return (
        lending_rate
        + leverage * (mean_return - lending_rate)
        - borrow_spread * borrowed
        - cost
        - 0.5 * leverage**2 * volatility**2
    )


def leverage_financing_cost(
    *, target_volatility: float, portfolio_volatility: float, borrow_spread: float
) -> float:
    """Annual financing drag of levering a portfolio to a target volatility.

    ``L = target / portfolio``, borrowing ``L - 1`` of NAV, so the drag is
    ``(L - 1) * spread``. This is the arithmetic behind the framework's finding that
    a 6.17%-volatility parity portfolio needs 2.59x leverage to reach 16%, making
    every 100 bp of spread cost about 159 bp per year.
    """
    if portfolio_volatility <= 0.0:
        raise ValueError("portfolio_volatility must be positive")
    if target_volatility < 0.0:
        raise ValueError("target_volatility cannot be negative")
    leverage = target_volatility / portfolio_volatility
    return max(leverage - 1.0, 0.0) * borrow_spread


def wealth_relatives(weights: FloatVector, scenario_returns: FloatMatrix) -> FloatArray:
    """``1 + w' R`` for every scenario row of ``scenario_returns``."""
    w = as_float_array(weights, name="weights")
    scenarios = as_float_matrix(scenario_returns, name="scenario_returns")
    if scenarios.shape[1] != w.size:
        raise ValueError(
            "scenario_returns must have one column per asset "
            f"({w.size}), got {scenarios.shape[1]}"
        )
    return np.asarray(1.0 + scenarios @ w, dtype=np.float64)


def check_scenarios_admissible(scenario_returns: FloatMatrix) -> FloatArray:
    """Reject a scenario set in which any single asset loses 100% or more.

    An optimiser searching the long-only simplex must be able to evaluate its
    objective at every vertex. If asset ``j`` returns ``-1`` or worse in any scenario,
    the objective is ``-inf`` at vertex ``j`` and the problem is not the one the caller
    thinks they posed: it is a bankruptcy model wearing a portfolio model's clothes.
    Rejecting the input is the honest response; the alternative is an optimiser that
    silently routes around the vertex and reports a finite optimum.
    """
    scenarios = as_float_matrix(scenario_returns, name="scenario_returns")
    breaches = np.argwhere(1.0 + scenarios <= 0.0)
    if breaches.size > 0:
        scenario_index, asset_index = (int(value) for value in breaches[0])
        raise NonPositiveWealthScenarioError(
            scenario_index,
            float(1.0 + scenarios[scenario_index, asset_index]),
            asset_index,
        )
    return scenarios


def expected_log_wealth(
    weights: FloatVector,
    scenario_returns: FloatMatrix,
    *,
    probabilities: FloatVector | None = None,
) -> float:
    """``E[log(1 + w' R)]`` over a discrete scenario set.

    Raises :class:`NonPositiveWealthScenarioError` if any scenario implies a wealth
    relative of zero or less. This is the constraint that makes the objective finite
    and it is checked, never assumed: a Gaussian model of simple returns violates it
    for every nonzero unconstrained exposure.
    """
    relatives = wealth_relatives(weights, scenario_returns)
    breaches = np.flatnonzero(relatives <= 0.0)
    if breaches.size > 0:
        index = int(breaches[0])
        raise NonPositiveWealthScenarioError(index, float(relatives[index]))
    probability = _normalised_probabilities(probabilities, relatives.size)
    return float(np.dot(probability, np.log(relatives)))


def maximise_expected_log_wealth(
    scenario_returns: FloatMatrix,
    *,
    probabilities: FloatVector | None = None,
    max_leverage: float = 1.0,
    tolerance: float = 1e-10,
    max_iterations: int = 500,
) -> FloatArray:
    """Weights maximising ``E[log(1 + w' R)]`` on the simplex scaled by ``max_leverage``.

    Long-only and fully invested at ``max_leverage``; solved by projected gradient
    ascent, which is adequate because the objective is concave on the feasible set.
    The scenario set is rejected outright by :func:`check_scenarios_admissible` if any
    asset loses 100% or more in any scenario, rather than searching for weights that
    route around the inadmissible vertex.
    """
    scenarios = check_scenarios_admissible(scenario_returns)
    n_assets = scenarios.shape[1]
    if max_leverage <= 0.0:
        raise ValueError("max_leverage must be positive")
    probability = _normalised_probabilities(probabilities, scenarios.shape[0])

    weights = np.full(n_assets, max_leverage / n_assets, dtype=np.float64)
    # Raises if the scenario set is inadmissible at the equally weighted start.
    value = expected_log_wealth(weights, scenarios, probabilities=probability)
    step = 1.0
    for _ in range(max_iterations):
        relatives = 1.0 + scenarios @ weights
        gradient = scenarios.T @ (probability / relatives)
        candidate = _project_to_simplex(weights + step * gradient, max_leverage)
        relatives_candidate = 1.0 + scenarios @ candidate
        if np.any(relatives_candidate <= 0.0):
            step *= 0.5
            continue
        candidate_value = float(np.dot(probability, np.log(relatives_candidate)))
        if candidate_value <= value:
            step *= 0.5
            if step < tolerance:
                break
            continue
        if candidate_value - value < tolerance:
            weights, value = candidate, candidate_value
            break
        weights, value = candidate, candidate_value
    return weights


def _normalised_probabilities(probabilities: FloatVector | None, size: int) -> FloatArray:
    if probabilities is None:
        return np.full(size, 1.0 / size, dtype=np.float64)
    array = as_float_array(probabilities, name="probabilities")
    if array.size != size:
        raise ValueError(f"probabilities must have {size} entries, got {array.size}")
    if np.any(array < 0.0):
        raise ValueError("probabilities cannot be negative")
    total = float(np.sum(array))
    if total <= 0.0:
        raise ValueError("probabilities must sum to a positive number")
    return np.asarray(array / total, dtype=np.float64)


def _project_to_simplex(vector: FloatArray, scale: float) -> FloatArray:
    """Euclidean projection onto ``{x >= 0, sum(x) = scale}``."""
    ordered = np.sort(vector)[::-1]
    cumulative = np.cumsum(ordered) - scale
    indices = np.arange(1, vector.size + 1, dtype=np.float64)
    condition = ordered - cumulative / indices > 0.0
    rho = int(np.flatnonzero(condition)[-1])
    theta = cumulative[rho] / (rho + 1.0)
    return np.asarray(np.maximum(vector - theta, 0.0), dtype=np.float64)
