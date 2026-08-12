"""Experiment 010: marginal sleeve value inside a real portfolio.

Every sleeve this repository has judged except trend was judged by a STANDALONE
chain -- ``premium x delivered loading x capture - cost``. That chain contains no
covariance term at all: it asks whether an asset beats the market on its own. The
portfolio question is different. Funding weight ``w`` of sleeve ``i`` out of
funding leg ``f`` inside portfolio ``p``, the derivative of the portfolio's
geometric growth rate at zero weight is exactly

    dg/dw|_{w=0} = E[(r_i - r_f) / (1 + r_p)]

and, to second order in the moments,

    dg/dw|_{w=0} = (mu_i - mu_f) - (sigma_ip - sigma_fp).

The first term is the standalone alpha the existing chain already measures. The
second is a DIVERSIFICATION CREDIT the chain omits. With ``f = p`` it collapses to
``sigma_p^2 (1 - beta_ip)``, the same excess-growth algebra this repository proved
in :mod:`portfolio_edge.studies.volatility_harvesting` and measured on real data
in exp_003.

Three things this module refuses to do
--------------------------------------
* **It does not read the derivative at zero and stop.** The derivative at zero
  favours any low-beta asset by construction and overstates the case at any
  weight an investor would hold. The reported figure is the certainty-equivalent
  gain at a FROZEN reference weight, with a constrained optimum over
  ``[0, cap]`` reported beside it -- together with how flat the surface is at
  that optimum, because a large "optimal" weight on a flat surface is not
  evidence about the weight.
* **It does not leave the funding source implicit.** "The marginal value of
  adding sleeve i" is undefined until the funding leg is named: funding pro rata
  from the whole portfolio, out of a specific leg, or out of cash are three
  different questions with three different covariances and possibly three
  different signs. All three are reported for every sleeve.
* **It does not assume the credit is positive.** ``beta_ip = rho_ip sigma_i /
  sigma_p``, so an equity sleeve's higher volatility can more than offset its
  correlation being below one, and the credit can be NEGATIVE. If it is, the
  portfolio-level view is HARSHER than the standalone view rather than kinder,
  and the existing dismissal stands strengthened. The prediction was frozen in
  ``parameters.predeclared_prediction`` before any number was computed, so the
  data is allowed to contradict it.

What this experiment is
-----------------------
A **public-series evaluation**. Ken French's research portfolios and factor files
are paper portfolios rebuilt from the current vintage on every release, with no
trading cost, no borrow and no capacity limit. The AQR trend series is a vendor
series whose cost basis exp_004 established to be UNSTATED. The long-duration
Treasury sleeve is a MODELLED PROXY reconstructed from a yield and is forced to
``unresolved`` by the frozen falsifier whatever it measures. Gold, the other asset
with a plausibly low equity beta, is NOT TESTED at all: no research-grade series
is reachable and decision record 0002 forbids substituting a free price feed.

Run it::

    uv run python -m portfolio_edge.experiments.exp_010_marginal_sleeve_value --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.data import aqr, fred, french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_count, month_index, shift_period
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.runner import RunOutcome, run_experiment
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.multiple_testing import MultipleTestingResult, holm_bonferroni

__all__ = [
    "ASSET_NAMES",
    "BASE_PORTFOLIO_IDS",
    "ENTRY_POINT",
    "FUNDING_LEG_IDS",
    "MONTHS_PER_YEAR",
    "ClosedFormOptimum",
    "Decomposition",
    "FeeTier",
    "MarginalSleeveValueError",
    "MonthlySeries",
    "PanelInputs",
    "Sleeve",
    "WeightSurface",
    "bond_total_return_from_yield",
    "build_registry",
    "certainty_equivalent_annual",
    "closed_form_optimum",
    "default_specification_path",
    "exact_growth_derivative",
    "high_water_mark_performance_fee",
    "main",
    "minimum_detectable_effect",
    "moment_growth_decomposition",
    "optimal_long_only_weight",
    "par_bond_risk",
    "run",
    "run_constant_weights",
]

ENTRY_POINT: Final = "exp_010_marginal_sleeve_value"

MONTHS_PER_YEAR: Final = 12

#: Asset ordering inside every weight vector. The sleeve is always last.
ASSET_NAMES: Final = (
    "us_equity",
    "dev_ex_us_equity",
    "emerging_equity",
    "cash",
    "sleeve",
)

BASE_PORTFOLIO_IDS: Final = ("global_equity_core", "balanced_60_40")

#: The three funding conventions. ``pro_rata`` carries the primary inference; the
#: other two exist because the funding source decides which covariance enters the
#: credit and can flip its sign.
FUNDING_LEG_IDS: Final = ("pro_rata", "named_leg", "cash")

#: One-sided alpha 0.05 and power 0.80: ``Phi^-1(0.95) + Phi^-1(0.80)``.
_Z_ALPHA_ONE_SIDED_05: Final = 1.6448536269514722
_Z_POWER_80: Final = 0.8416212335729143

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]

_GAIN_AT_OPTIMUM_KEY: Final = "certainty_equivalent_gain_at_optimum_pp_per_year"


class MarginalSleeveValueError(RuntimeError):
    """The experiment could not be attempted against the declared vintages."""


def _json_float(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``."""
    return None if math.isnan(value) or math.isinf(value) else value


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise MarginalSleeveValueError(
            f"{where} must be a mapping, got {type(value).__name__}"
        )
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise MarginalSleeveValueError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise MarginalSleeveValueError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise MarginalSleeveValueError(
            f"{where}.{key} must be a non-empty string, got {value!r}"
        )
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise MarginalSleeveValueError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str):
            raise MarginalSleeveValueError(
                f"{where}.{key}[{index}] must be a string, got {item!r}"
            )
        out.append(item)
    return tuple(out)


# --------------------------------------------------------------------------- #
# Statistics this experiment adds, each with its own unit test
# --------------------------------------------------------------------------- #


def certainty_equivalent_annual(annual_gross_returns: FloatArray, *, gamma: float) -> float:
    """The constant annual return whose CRRA utility equals the sample's mean utility.

    ``u(x) = x**(1 - gamma) / (1 - gamma)`` for ``gamma != 1``, so
    ``CE = (mean_y G_y**(1 - gamma))**(1 / (1 - gamma)) - 1``. ``gamma = 1`` is the
    geometric mean minus one.

    Inputs are wealth relatives over a whole year, not returns, and must be
    strictly positive: CRRA utility is undefined at zero wealth for ``gamma >= 1``,
    and a portfolio that reaches it is insolvent rather than unlucky. The same
    definition is used by exp_003 and exp_004; it is restated here so that the
    experiments do not import each other's internals.
    """
    values = np.asarray(annual_gross_returns, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("annual_gross_returns must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(values)):
        raise ValueError("annual_gross_returns contains non-finite values")
    if np.any(values <= 0.0):
        raise ValueError(
            "CRRA utility is undefined at non-positive wealth; a gross return of "
            f"{float(np.min(values))!r} is insolvency, not a low return"
        )
    if math.isclose(gamma, 1.0):
        return float(np.exp(np.mean(np.log(values)))) - 1.0
    power = 1.0 - gamma
    return float(np.mean(values**power) ** (1.0 / power)) - 1.0


def _annual_gross_matrix(monthly: FloatArray) -> FloatArray:
    """Compound ``(..., 12 * Y)`` monthly returns into ``(..., Y)`` annual relatives."""
    values = np.asarray(monthly, dtype=np.float64)
    if values.shape[-1] % MONTHS_PER_YEAR != 0:
        raise ValueError(f"need a whole number of 12-month blocks, got {values.shape[-1]} months")
    shaped = values.reshape(*values.shape[:-1], -1, MONTHS_PER_YEAR)
    return np.asarray(np.prod(1.0 + shaped, axis=-1), dtype=np.float64)


def _certainty_equivalent_rows(monthly: FloatArray, *, gamma: float) -> FloatArray:
    """Vectorised certainty equivalent for every row of a ``(R, T)`` return matrix."""
    annual = _annual_gross_matrix(monthly)
    if np.any(annual <= 0.0):
        raise ValueError("a resampled path reached non-positive wealth over a calendar year")
    if math.isclose(gamma, 1.0):
        return np.asarray(np.exp(np.mean(np.log(annual), axis=-1)) - 1.0, dtype=np.float64)
    power = 1.0 - gamma
    return np.asarray(np.mean(annual**power, axis=-1) ** (1.0 / power) - 1.0, dtype=np.float64)


@dataclass(frozen=True, slots=True, kw_only=True)
class Decomposition:
    """The first-order marginal effect of a sleeve, split into its two terms.

    Every field is an ANNUALISED decimal rate per unit of sleeve weight. Multiply
    by 100 for percentage points and by the weight for the effect at that weight.
    """

    alpha_term: float
    """``periods_per_year * (mu_i - mu_f)``. What the standalone chain measures."""
    credit_term: float
    """``periods_per_year * gamma * (sigma_fp - sigma_ip)``. What it omits."""
    moment_total: float
    gamma: float
    beta_sleeve_to_portfolio: float
    beta_funding_to_portfolio: float
    correlation_sleeve_to_portfolio: float
    sleeve_volatility: float
    portfolio_volatility: float
    credit_derivative_per_correlation: float
    """``-periods_per_year * gamma * sigma_i * sigma_p``: how far the credit moves
    when the correlation moves by one, holding the volatilities fixed."""


def moment_growth_decomposition(
    *,
    mean_sleeve: float,
    mean_funding: float,
    cov_sleeve_portfolio: float,
    cov_funding_portfolio: float,
    variance_sleeve: float,
    variance_portfolio: float,
    gamma: float = 1.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> Decomposition:
    """Split ``dg/dw|_{w=0}`` into a standalone term and a diversification credit.

    All six inputs are per-period moments in decimal units -- monthly means,
    monthly covariances -- and every output is annualised by ``periods_per_year``.
    That is the only unit convention in this function and it is asserted by a test:
    passing annual moments and expecting annual outputs would multiply by twelve
    twice.

    The identity, for portfolio ``p``, sleeve ``i`` and funding leg ``f``::

        dCE/dw|_{w=0} = (mu_i - mu_f) - gamma * (sigma_ip - sigma_fp)

    ``gamma = 1`` is the geometric growth rate; ``gamma = 3`` is the CRRA investor
    the primary metric uses. With ``f = p`` the credit becomes
    ``gamma * sigma_p^2 (1 - beta_ip)``, which is negative whenever
    ``beta_ip > 1`` -- the case the frozen prediction expects for every equity
    sleeve, and the case in which the portfolio-level view is HARSHER than the
    standalone chain rather than kinder.

    A closed form derived independently of this implementation takes precedence
    over it. If the two disagree, that is a finding, not a tolerance to loosen.
    """
    if variance_sleeve < 0.0 or variance_portfolio < 0.0:
        raise ValueError(
            f"variances must be non-negative, got sleeve={variance_sleeve!r} "
            f"portfolio={variance_portfolio!r}"
        )
    if periods_per_year <= 0:
        raise ValueError(f"periods_per_year must be positive, got {periods_per_year}")
    alpha = periods_per_year * (mean_sleeve - mean_funding)
    credit = periods_per_year * gamma * (cov_funding_portfolio - cov_sleeve_portfolio)
    sleeve_volatility = math.sqrt(variance_sleeve * periods_per_year)
    portfolio_volatility = math.sqrt(variance_portfolio * periods_per_year)
    beta_sleeve = (
        cov_sleeve_portfolio / variance_portfolio if variance_portfolio > 0.0 else math.nan
    )
    beta_funding = (
        cov_funding_portfolio / variance_portfolio if variance_portfolio > 0.0 else math.nan
    )
    denominator = math.sqrt(variance_sleeve * variance_portfolio)
    correlation = cov_sleeve_portfolio / denominator if denominator > 0.0 else math.nan
    return Decomposition(
        alpha_term=alpha,
        credit_term=credit,
        moment_total=alpha + credit,
        gamma=gamma,
        beta_sleeve_to_portfolio=beta_sleeve,
        beta_funding_to_portfolio=beta_funding,
        correlation_sleeve_to_portfolio=correlation,
        sleeve_volatility=sleeve_volatility,
        portfolio_volatility=portfolio_volatility,
        credit_derivative_per_correlation=(
            -gamma * sleeve_volatility * portfolio_volatility
        ),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ClosedFormOptimum:
    """The analytic interior optimum of the quadratic growth curve, and its gain.

    In the continuous (Ito) convention the growth rate of the mix is EXACTLY
    quadratic in the sleeve weight::

        g(w) = g(0) + w D - 0.5 w^2 tau^2,   tau^2 = Var(r_i - r_f)

    so ``w* = D / tau^2`` and ``g(w*) - g(0) = D^2 / (2 tau^2)``, with ``D`` the
    first-order marginal growth rate that
    :func:`moment_growth_decomposition` splits into its two terms.

    This is reported BESIDE the numerical certainty-equivalent optimum, never
    instead of it. The two answer different questions -- one is the analytic
    optimum of a second-moment model of the growth rate, the other is the realised
    optimum of an exact CRRA utility over the actual cost-charged path -- and a
    large gap between them is informative rather than a defect.

    ``tau_squared = 0`` means the sleeve is a pathwise clone of the funding leg.
    Then ``D`` is zero too, the curve is flat, and the optimum is ``0/0``: a
    genuine degeneracy, which this refuses rather than answering.
    """

    marginal_growth: float
    """``D``, annualised, per unit weight."""
    relative_variance: float
    """``tau^2 = Var(r_i - r_f)``, annualised."""
    interior_weight: float
    interior_gain: float
    constrained_weight: float
    constrained_gain: float
    cap: float
    degenerate: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "marginal_growth_per_unit_weight": self.marginal_growth,
            "relative_variance_tau_squared": self.relative_variance,
            "interior_optimal_weight": _json_float(self.interior_weight),
            "interior_gain_pp_per_year": _json_float(100.0 * self.interior_gain),
            "constrained_optimal_weight": self.constrained_weight,
            "constrained_gain_pp_per_year": 100.0 * self.constrained_gain,
            "weight_cap": self.cap,
            "degenerate_clone_of_the_funding_leg": self.degenerate,
        }


def closed_form_optimum(
    marginal_growth: float, relative_variance: float, *, cap: float
) -> ClosedFormOptimum:
    """``w* = D / tau^2`` projected onto ``[0, cap]``, with the gain at both weights."""
    if relative_variance < 0.0:
        raise ValueError(f"tau^2 must be non-negative, got {relative_variance}")
    if cap <= 0.0:
        raise ValueError(f"cap must be positive, got {cap}")
    if relative_variance == 0.0:
        return ClosedFormOptimum(
            marginal_growth=marginal_growth,
            relative_variance=0.0,
            interior_weight=math.nan,
            interior_gain=math.nan,
            constrained_weight=0.0,
            constrained_gain=0.0,
            cap=cap,
            degenerate=True,
        )
    interior = marginal_growth / relative_variance
    constrained = min(max(interior, 0.0), cap)
    return ClosedFormOptimum(
        marginal_growth=marginal_growth,
        relative_variance=relative_variance,
        interior_weight=interior,
        interior_gain=marginal_growth**2 / (2.0 * relative_variance),
        constrained_weight=constrained,
        constrained_gain=(
            constrained * marginal_growth - 0.5 * constrained**2 * relative_variance
        ),
        cap=cap,
        degenerate=False,
    )


def exact_growth_derivative(
    sleeve: FloatArray,
    funding: FloatArray,
    portfolio: FloatArray,
    *,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> float:
    """``periods_per_year * mean((r_i - r_f) / (1 + r_p))``.

    The exact derivative of the realised annualised LOG growth rate with respect
    to the sleeve weight at zero weight, with no distributional assumption and no
    truncation at two moments. Differentiating
    ``(1/T) sum_t log(1 + r_p,t + w (r_i,t - r_f,t))`` at ``w = 0`` gives it
    directly.

    Reported beside :func:`moment_growth_decomposition` so that the approximation
    error of the two-moment split is visible rather than assumed away. The unit is
    annualised log growth per unit weight, which is not the same unit as an annual
    simple return; the two agree to first order and the difference is second order
    in the growth rate itself.
    """
    a = np.asarray(sleeve, dtype=np.float64)
    b = np.asarray(funding, dtype=np.float64)
    c = np.asarray(portfolio, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or a.shape != c.shape:
        raise ValueError("sleeve, funding and portfolio must be one-dimensional and aligned")
    if a.size == 0:
        raise ValueError("the series must not be empty")
    if np.any(c <= -1.0):
        raise ValueError(
            "the portfolio reached non-positive wealth, so its log growth rate and "
            "therefore this derivative do not exist"
        )
    return float(periods_per_year * np.mean((a - b) / (1.0 + c)))


def minimum_detectable_effect(
    standard_error: float,
    *,
    z_alpha: float = _Z_ALPHA_ONE_SIDED_05,
    z_power: float = _Z_POWER_80,
) -> float:
    """``(z_{1-alpha} + z_{power}) * standard_error``.

    The smallest true effect a one-sided test of size ``alpha`` rejects the null
    for with probability ``power``. Identical in form to exp_001 and exp_005, so
    the figures are directly comparable to their grids; the only difference is
    that this experiment feeds it a bootstrap standard error as well as the
    ``sigma / sqrt(T)`` one, because the certainty equivalent is not a mean and
    the monthly panel is serially dependent.
    """
    if standard_error < 0.0:
        raise ValueError(f"standard_error must be non-negative, got {standard_error}")
    return (z_alpha + z_power) * standard_error


def high_water_mark_performance_fee(
    returns: FloatArray, *, rate: float
) -> tuple[FloatArray, float]:
    """Charge a performance fee on gains above a high-water mark, month by month.

    A high-water mark is the standard contract and is strictly more favourable to
    the strategy than charging on every up month, which would take a fee twice for
    recovering the same ground. The favourable convention is chosen deliberately:
    the conclusion must not depend on an unnecessarily harsh fee model. Identical
    in form to exp_004, restated so the two experiments do not import each other.
    """
    if not 0.0 <= rate < 1.0:
        raise ValueError(f"rate must lie in [0, 1), got {rate}")
    values = np.asarray(returns, dtype=np.float64)
    net = np.empty(values.size, dtype=np.float64)
    nav = 1.0
    high_water = 1.0
    total_fee = 0.0
    for index, gross in enumerate(values):
        before = nav * (1.0 + float(gross))
        fee = rate * max(before - high_water, 0.0)
        after = before - fee
        total_fee += fee
        net[index] = after / nav - 1.0
        nav = after
        high_water = max(high_water, after)
    return net, total_fee


def par_bond_risk(annual_yield: float, *, periods: float) -> tuple[float, float]:
    """Modified duration and convexity, in years and years squared, of a par bond.

    For a semi-annual par bond priced at 1 with ``n`` periods and per-period yield
    ``i``, the coupon equals the yield, so with the coupon held fixed
    ``P'(i) = -(1 - v^n)/i`` with ``v = 1/(1+i)``. Differentiating once more gives

        P''(i) = 2 [ (1 - v^n)/i^2 - n v^(n+1)/i ].

    Dividing by 2 and by 4 converts the per-period derivatives to annual ones,
    since ``di/dy = 1/2``.

    At a 4% yield and ten years this returns 8.1757 and 78.8979. Both are checked
    in the tests by numerically differentiating the exact price function, not
    against this function's own output.

    FINDING, since REPAIRED: the same helper in ``exp_004_trend_marginal_value``
    omitted the factor of 2 in ``P''(i)`` and therefore reported HALF the true
    convexity, 39.4490 instead of 78.8979, behind a unit test that asserted the
    implementation's own output and so pinned the error rather than catching it.
    This module surfaced it and carried the corrected form without touching the
    ledgered experiment; exp_004 was then re-run against its unchanged frozen
    specification and exactly one figure moved, its bond-leg robustness arm's
    marginal, by -0.000585 pp/yr. A test now holds the two copies against each
    other at three yields so they cannot diverge again.
    """
    if annual_yield <= 0.0:
        raise ValueError(f"a par-bond yield must be positive, got {annual_yield}")
    if periods <= 0.0:
        raise ValueError(f"periods must be positive, got {periods}")
    half = annual_yield / 2.0
    discount = (1.0 + half) ** -periods
    modified = (1.0 - discount) / (2.0 * half)
    convexity = ((1.0 - discount) / half**2 - periods * discount / (half * (1.0 + half))) / 2.0
    return modified, convexity


def bond_total_return_from_yield(
    yields_annual: FloatArray, *, maturity_years: float = 10.0
) -> FloatArray:
    """A par-bond total return reconstructed from a constant-maturity yield.

    THIS IS A MODELLED SERIES AND IS A PROXY, not an investable total-return
    history. It has no documented total-return contract, no coupon reinvestment
    convention and no transaction costs. It exists here because omitting the one
    asset class with a plausibly negative equity beta would bias the whole
    experiment toward the conclusion that no diversification credit exists
    anywhere. The frozen falsifier forces any sleeve built from it to
    ``unresolved`` whatever it measures. The first element is ``NaN``.
    """
    y = np.asarray(yields_annual, dtype=np.float64)
    if y.ndim != 1 or y.size < 2:
        raise ValueError("yields_annual must be one-dimensional with at least two entries")
    out = np.full(y.size, np.nan, dtype=np.float64)
    periods = 2.0 * maturity_years
    for index in range(1, y.size):
        previous = float(y[index - 1])
        change = float(y[index]) - previous
        if previous <= 0.0:
            continue
        modified, convexity = par_bond_risk(previous, periods=periods)
        out[index] = previous / MONTHS_PER_YEAR - modified * change + 0.5 * convexity * change**2
    return out


def run_constant_weights(
    target: FloatArray, asset_returns: FloatArray, *, one_way_bps: float
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Realise a CONSTANT target weight vector, charging spread on each trade.

    ``target`` is held through every month and the portfolio is rebalanced back to
    it at every month end, so the trade at ``t`` is the distance from the weights
    the previous month drifted to::

        drifted_t = target * (1 + r_{t-1}) / (target . (1 + r_{t-1}))

    which depends only on the previous month's returns and the constant target,
    and therefore needs no loop. The initial purchase is not charged: every
    comparison in this experiment starts from the same cash, and an identical
    entry cost charged to both sides cannot change a difference between them.

    Returns ``(portfolio_returns, one_sided_turnover, trading_cost)``.
    """
    weights = np.asarray(target, dtype=np.float64)
    returns = np.asarray(asset_returns, dtype=np.float64)
    if weights.ndim != 1 or returns.ndim != 2 or returns.shape[1] != weights.size:
        raise ValueError(
            f"target must be one-dimensional and match asset_returns' columns; got "
            f"{weights.shape} and {returns.shape}"
        )
    if one_way_bps < 0.0:
        raise ValueError(f"one_way_bps must be non-negative, got {one_way_bps}")
    periods = returns.shape[0]
    grown = weights[None, :] * (1.0 + returns)
    totals = grown.sum(axis=1)
    drifted = np.empty_like(grown)
    drifted[0] = weights
    with np.errstate(divide="ignore", invalid="ignore"):
        normalised = grown / totals[:, None]
    # A month that wipes out the portfolio has no meaningful drifted weights; hold
    # the target rather than inventing one, and let the return series say so.
    normalised = np.where(np.isfinite(normalised), normalised, weights[None, :])
    if periods > 1:
        drifted[1:] = np.where(
            (totals[:-1] > 0.0)[:, None], normalised[:-1], weights[None, :]
        )
    traded = np.abs(weights[None, :] - drifted).sum(axis=1)
    turnover = 0.5 * traded
    cost = traded * one_way_bps / 1e4
    portfolio = returns @ weights - cost
    return portfolio, turnover, cost


@dataclass(frozen=True, slots=True, kw_only=True)
class WeightSurface:
    """The certainty-equivalent gain over a long-only weight grid, and its shape.

    ``gains`` are in percentage points per year relative to the base portfolio at
    zero sleeve weight. Every flatness statistic is reported together with the
    optimum, because an optimum without them says nothing about whether the data
    can locate a weight.
    """

    weights: tuple[float, ...]
    gains: tuple[float, ...]
    optimal_weight: float
    optimal_gain: float
    gain_at_cap: float
    cap: float
    at_lower_boundary: bool
    at_upper_boundary: bool
    plateau_low: float
    plateau_high: float
    plateau_width: float
    material_low: float
    material_high: float
    material_width: float
    curvature: float
    """Second difference of the gain at the optimum, per unit weight squared. Near
    zero means a flat surface: the optimum is not located by the data."""
    max_deviation_from_linear: float
    """Largest absolute distance, in percentage points per year, between the gain
    curve and the straight line joining zero weight to the cap. A small value means
    the surface is essentially LINEAR in the weight, so there is no interior
    optimum at all and the reported optimal weight is decided entirely by the
    frozen cap rather than by the data."""

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "optimal_weight": self.optimal_weight,
            "certainty_equivalent_gain_at_optimum_pp_per_year": self.optimal_gain,
            "certainty_equivalent_gain_at_cap_pp_per_year": self.gain_at_cap,
            "weight_cap": self.cap,
            "optimum_at_long_only_boundary": self.at_lower_boundary,
            "optimum_at_weight_cap": self.at_upper_boundary,
            "plateau_within_90_percent_of_peak": [self.plateau_low, self.plateau_high],
            "plateau_width": self.plateau_width,
            "region_above_materiality": [self.material_low, self.material_high],
            "region_above_materiality_width": self.material_width,
            "curvature_at_optimum_per_unit_weight_squared": _json_float(self.curvature),
            "max_deviation_from_a_straight_line_pp_per_year": self.max_deviation_from_linear,
            "surface_is_effectively_linear": (
                abs(self.gain_at_cap) > 0.0
                and self.max_deviation_from_linear < 0.10 * abs(self.gain_at_cap)
            ),
            "grid": list(self.weights),
            "gains_pp_per_year": list(self.gains),
        }


def optimal_long_only_weight(
    weights: Sequence[float],
    gains: Sequence[float],
    *,
    cap: float,
    materiality: float,
) -> WeightSurface:
    """Locate the constrained optimum on a long-only grid and describe its shape.

    ``weights`` must be increasing and start at zero; ``gains[k]`` is the
    certainty-equivalent gain in percentage points per year at ``weights[k]``. The
    long-only constraint is enforced by the grid: nothing below zero is offered,
    so a sleeve whose gain is decreasing everywhere returns weight zero at the
    boundary, which is falsifier clause (c).

    Three flatness statistics accompany the optimum:

    * the contiguous plateau around the optimum on which the gain is at least 90%
      of its maximum;
    * the contiguous region on which the gain exceeds the materiality threshold;
    * the second difference of the gain at the optimum.
    """
    w = np.asarray(weights, dtype=np.float64)
    g = np.asarray(gains, dtype=np.float64)
    if w.ndim != 1 or w.shape != g.shape or w.size < 3:
        raise ValueError("weights and gains must be aligned one-dimensional grids of size >= 3")
    if not np.all(np.diff(w) > 0.0):
        raise ValueError("weights must be strictly increasing")
    if not math.isclose(float(w[0]), 0.0, abs_tol=1e-12):
        raise ValueError(f"the grid must start at zero weight, got {float(w[0])!r}")
    if not np.all(np.isfinite(g)):
        raise ValueError("gains contains non-finite values")

    best = int(np.argmax(g))
    optimal_gain = float(g[best])
    optimal_weight = float(w[best])

    def contiguous(threshold: float) -> tuple[float, float]:
        low = best
        while low > 0 and g[low - 1] >= threshold:
            low -= 1
        high = best
        while high + 1 < g.size and g[high + 1] >= threshold:
            high += 1
        return float(w[low]), float(w[high])

    plateau_threshold = 0.9 * optimal_gain if optimal_gain > 0.0 else math.inf
    plateau_low, plateau_high = (
        contiguous(plateau_threshold)
        if math.isfinite(plateau_threshold)
        else (optimal_weight, optimal_weight)
    )
    material_low, material_high = (
        contiguous(materiality) if optimal_gain >= materiality else (0.0, 0.0)
    )

    if 0 < best < g.size - 1:
        step = float(w[best + 1] - w[best])
        curvature = float(g[best - 1] - 2.0 * g[best] + g[best + 1]) / (step * step)
    else:
        curvature = math.nan

    straight_line = g[0] + (g[-1] - g[0]) * (w - w[0]) / (w[-1] - w[0])
    max_deviation = float(np.max(np.abs(g - straight_line)))

    return WeightSurface(
        weights=tuple(float(value) for value in w),
        gains=tuple(float(value) for value in g),
        optimal_weight=optimal_weight,
        optimal_gain=optimal_gain,
        gain_at_cap=float(g[-1]),
        cap=cap,
        at_lower_boundary=best == 0,
        at_upper_boundary=best == g.size - 1,
        plateau_low=plateau_low,
        plateau_high=plateau_high,
        plateau_width=plateau_high - plateau_low,
        material_low=material_low,
        material_high=material_high,
        material_width=material_high - material_low,
        curvature=curvature,
        max_deviation_from_linear=max_deviation,
    )


# --------------------------------------------------------------------------- #
# Series and alignment
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class MonthlySeries:
    """One monthly series in decimal units, with its period labels."""

    name: str
    periods: tuple[str, ...]
    values: FloatArray
    source: str

    def __post_init__(self) -> None:
        if len(self.periods) != self.values.size:
            raise MarginalSleeveValueError(
                f"series {self.name!r} has {len(self.periods)} labels and "
                f"{self.values.size} values"
            )

    def as_map(self) -> dict[str, float]:
        return dict(zip(self.periods, (float(v) for v in self.values), strict=True))


def _series_from_table(
    table: ParsedTable, column: str, *, name: str, source: str
) -> MonthlySeries:
    if column not in table.columns:
        raise MarginalSleeveValueError(
            f"column {column!r} is absent from table {table.table_id!r} of {source}; "
            f"found {list(table.columns)}"
        )
    periods: list[str] = []
    values: list[float] = []
    for period, value in zip(table.periods, table.column(column), strict=True):
        if value is None:
            continue
        periods.append(period[:7])
        values.append(value)
    return MonthlySeries(
        name=name, periods=tuple(periods), values=np.asarray(values, dtype=np.float64),
        source=source,
    )


def _aligned(
    series: Mapping[str, MonthlySeries], *, start: str, end: str
) -> tuple[tuple[str, ...], dict[str, FloatArray], tuple[str, ...]]:
    """Intersect every series onto one contiguous monthly grid, reporting shortfalls.

    Nothing is forward-filled. A month that any series lacks is dropped from all of
    them and the drop is reported, because a hole silently patched is a hole that
    reappears later as an unexplained number.
    """
    maps = {name: item.as_map() for name, item in series.items()}
    first, last = month_index(start), month_index(end)
    grid = [shift_period(start, offset) for offset in range(max(0, last - first + 1))]
    findings: list[str] = []
    keep = [period for period in grid if all(period in table for table in maps.values())]
    if len(keep) != len(grid):
        missing = [period for period in grid if period not in keep]
        findings.append(
            f"{len(missing)} of {len(grid)} months in {start}..{end} are absent from at "
            f"least one input series and were dropped from all of them: {missing[:6]}"
        )
    for name, table in maps.items():
        available = sorted(table)
        if available and available[0] > start:
            findings.append(f"{name} begins at {available[0]}, after the requested {start}")
        if available and available[-1] < end:
            findings.append(f"{name} ends at {available[-1]}, before the requested {end}")
    columns = {
        name: np.asarray([maps[name][period] for period in keep], dtype=np.float64)
        for name in maps
    }
    return (tuple(keep), columns, tuple(findings))


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PanelInputs:
    """Every monthly input on one aligned grid, plus a one-month lead.

    ``lead_months`` months sit before the frozen sample start and are NEVER
    reported. They exist only because the modelled long-duration proxy is a
    difference of consecutive yields and so has no value in its first month; a
    lead of one supplies that month rather than leaving a hole or inventing a
    value. Every other series ignores the lead entirely.
    """

    periods: tuple[str, ...]
    columns: Mapping[str, FloatArray]
    lead_months: int
    findings: tuple[str, ...]
    provenance: tuple[JsonValue, ...]
    source_last_observations: tuple[tuple[str, str], ...]
    """Each input's own last month, BEFORE alignment clipped it to the holdout."""

    @property
    def reported_periods(self) -> tuple[str, ...]:
        return self.periods[self.lead_months :]

    @property
    def reported_columns(self) -> dict[str, FloatArray]:
        return {name: values[self.lead_months :] for name, values in self.columns.items()}


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _manifest_hash(data: Mapping[str, JsonValue], key: str) -> str | None:
    location = data.get(key)
    if not isinstance(location, str):
        return None
    path = _workspace_root() / location
    if not path.is_file():
        return None
    return read_manifest(path).sha256_manifest()


#: Which raw column of which pinned table becomes which internal series name.
_FRENCH_COLUMNS: Final[dict[str, tuple[str, str]]] = {
    "french_us_ff5": ("Mkt-RF", "us_market_excess"),
    "french_developed_ex_us_ff5": ("Mkt-RF", "dev_ex_us_market_excess"),
    "french_emerging_ff5": ("Mkt-RF", "emerging_market_excess"),
    "french_us_momentum": ("Mom", "us_momentum_factor"),
    "french_developed_ex_us_momentum": ("WML", "dev_ex_us_momentum_factor"),
    "french_emerging_momentum": ("WML", "emerging_momentum_factor"),
    "french_us_6_portfolios_2x3": ("SMALL HiBM", "us_small_value_total"),
    "french_developed_ex_us_6_portfolios_2x3": ("SMALL HiBM", "dev_ex_us_small_value_total"),
    "french_emerging_6_portfolios_2x3": ("SMALL HiBM", "emerging_small_value_total"),
    "french_us_6_portfolios_me_prior_12_2": ("BIG HiPRIOR", "us_momentum_long_only_total"),
}

#: The extra column each five-factor file also supplies: its own risk-free rate,
#: which is the only sum that turns ``Mkt-RF`` into a total return.
_FRENCH_RISK_FREE: Final[dict[str, str]] = {
    "french_us_ff5": "us_risk_free",
    "french_developed_ex_us_ff5": "dev_ex_us_risk_free",
    "french_emerging_ff5": "emerging_risk_free",
}

_FF5_COLUMNS: Final = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
_BOOK_TO_MARKET_SIX: Final = (
    "SMALL LoBM",
    "ME1 BM2",
    "SMALL HiBM",
    "BIG LoBM",
    "ME2 BM2",
    "BIG HiBM",
)
_PRIOR_RETURN_SIX: Final = (
    "SMALL LoPRIOR",
    "ME1 PRIOR2",
    "SMALL HiPRIOR",
    "BIG LoPRIOR",
    "ME2 PRIOR2",
    "BIG HiPRIOR",
)

#: The WHOLE schema each pinned table must present, in order. Validating against
#: the full tuple rather than the columns actually read is what turns a silent
#: source rename or reordering into an error instead of a wrong number.
_FRENCH_SCHEMA: Final[dict[str, tuple[str, ...]]] = {
    "french_us_ff5": _FF5_COLUMNS,
    "french_developed_ex_us_ff5": _FF5_COLUMNS,
    "french_emerging_ff5": _FF5_COLUMNS,
    "french_us_momentum": ("Mom",),
    "french_developed_ex_us_momentum": ("WML",),
    "french_emerging_momentum": ("WML",),
    "french_us_6_portfolios_2x3": _BOOK_TO_MARKET_SIX,
    "french_developed_ex_us_6_portfolios_2x3": _BOOK_TO_MARKET_SIX,
    "french_emerging_6_portfolios_2x3": _BOOK_TO_MARKET_SIX,
    "french_us_6_portfolios_me_prior_12_2": _PRIOR_RETURN_SIX,
}


def _load_inputs(specification: Specification) -> PanelInputs:
    """Fetch, pin, parse and validate every input, then align them.

    A raw-hash mismatch on Ken French or AQR ABORTS. Both rebuild their entire
    history in place on every update, so an unrecognised hash is a new vintage
    rather than a corrupted download, and a marginal figure computed from an
    unrecognised file looks exactly like a good one. FRED appends rather than
    rewrites, so its hash is reported without aborting.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    cache = RawCache()
    provenance: list[JsonValue] = []
    raw_series: dict[str, MonthlySeries] = {}

    for index, item in enumerate(
        _sequence(_at(pin, "french", where="source_pin"), where="source_pin.french")
    ):
        where = f"source_pin.french[{index}]"
        entry_spec = _mapping(item, where=where)
        dataset_id = _text(entry_spec, "dataset_id", where=where)
        table_id = _text(entry_spec, "table_id", where=where)
        dataset = french.get_dataset(dataset_id)
        cached = french.download(cache, dataset)
        expected_raw = _text(entry_spec, "expected_sha256_raw", where=where)
        if cached.sha256 != expected_raw:
            raise MarginalSleeveValueError(
                f"the file at {dataset.url} now hashes to {cached.sha256}, but this "
                f"specification is frozen against {expected_raw}. Ken French rebuilds "
                "the whole history from each new vintage, so this is a new vintage, "
                "not a corrupted download. Freeze a new specification against it "
                "rather than reporting marginal value from an unrecognised file."
            )
        parsed = french.parse(cache, cached, dataset=dataset)
        table = parsed.table(table_id)
        expected_columns = _strings(entry_spec, "columns", where=where)
        report = validate_table(
            table,
            dataset_id=f"{dataset_id}_{table_id}",
            expected_columns=_FRENCH_SCHEMA[dataset_id],
            expected_frequency="monthly",
        )
        if not report.ok:
            raise MarginalSleeveValueError(
                f"the {dataset_id}/{table_id} table failed validation before any "
                "statistic was computed: " + "; ".join(report.summary())
            )
        expected_normalised = _text(entry_spec, "expected_sha256_normalized", where=where)
        if table.sha256_normalized() != expected_normalised:
            raise MarginalSleeveValueError(
                f"the derived {dataset_id}/{table_id} table hashes to "
                f"{table.sha256_normalized()}, but the specification pins "
                f"{expected_normalised}. The raw bytes matched, so the parser changed "
                "behaviour. That is a finding, not a hash to update."
            )
        column, name = _FRENCH_COLUMNS[dataset_id]
        if column not in expected_columns:
            raise MarginalSleeveValueError(
                f"{where}.columns is {list(expected_columns)} but this module reads "
                f"{column!r} from {dataset_id}"
            )
        raw_series[name] = _series_from_table(table, column, name=name, source=dataset_id)
        if dataset_id in _FRENCH_RISK_FREE:
            risk_free_name = _FRENCH_RISK_FREE[dataset_id]
            raw_series[risk_free_name] = _series_from_table(
                table, "RF", name=risk_free_name, source=dataset_id
            )
        provenance.append(
            {
                "dataset_id": dataset_id,
                "table_id": table_id,
                "source_url": cached.url,
                "columns_used": [column, *(["RF"] if dataset_id in _FRENCH_RISK_FREE else [])],
                "sha256_raw": cached.sha256,
                "sha256_normalized": table.sha256_normalized(),
                "retrieved_utc": cached.retrieved_utc,
                "source_last_modified": cached.last_modified,
                "parser_version": french.PARSER_VERSION,
                "rows_in_file": table.rows,
                "first_observation": table.first_observation,
                "last_observation": table.last_observation,
                "units": table.units,
                "validation_findings": list(report.summary()),
                "committed_manifest_sha256": _manifest_hash(entry_spec, "committed_manifest"),
            }
        )

    # --- AQR trend sleeve ---------------------------------------------------
    aqr_pin = _mapping(_at(pin, "aqr", where="source_pin"), where="source_pin.aqr")
    aqr_dataset = aqr.get_dataset(_text(aqr_pin, "dataset_id", where="source_pin.aqr"))
    aqr_entry = aqr.download(cache, aqr_dataset)
    expected_aqr = _text(aqr_pin, "expected_sha256_raw", where="source_pin.aqr")
    if aqr_entry.sha256 != expected_aqr:
        raise MarginalSleeveValueError(
            f"the workbook at {aqr_dataset.url} now hashes to {aqr_entry.sha256}, but "
            f"this specification is frozen against {expected_aqr}. AQR reconstructs the "
            "full history each time the returns are updated, so this is a new vintage."
        )
    aqr_file = aqr.parse(cache, aqr_entry, dataset=aqr_dataset)
    sheet = _text(aqr_pin, "sheet", where="source_pin.aqr")
    if aqr_file.data_sheet != sheet:
        raise MarginalSleeveValueError(
            f"the specification pins sheet {sheet!r} but the parser read "
            f"{aqr_file.data_sheet!r}"
        )
    aqr_report = validate_table(
        aqr_file.table,
        dataset_id="aqr_tsmom_factors_monthly",
        expected_columns=aqr_dataset.expected_columns,
        expected_frequency="monthly",
    )
    if not aqr_report.ok:
        raise MarginalSleeveValueError(
            "the AQR table failed validation: " + "; ".join(aqr_report.summary())
        )
    expected_aqr_normalised = _text(aqr_pin, "expected_sha256_normalized", where="source_pin.aqr")
    if aqr_file.table.sha256_normalized() != expected_aqr_normalised:
        raise MarginalSleeveValueError(
            f"the derived AQR table hashes to {aqr_file.table.sha256_normalized()}, but "
            f"the specification pins {expected_aqr_normalised}."
        )
    aqr_column = _text(aqr_pin, "column", where="source_pin.aqr")
    raw_series["trend_factor"] = _series_from_table(
        aqr_file.table, aqr_column, name="trend_factor", source=aqr_dataset.dataset_id
    )
    provenance.append(
        {
            "dataset_id": aqr_dataset.dataset_id,
            "source_url": aqr_entry.url,
            "workbook_sheet": aqr_file.data_sheet,
            "column": aqr_column,
            "sha256_raw": aqr_entry.sha256,
            "sha256_normalized": aqr_file.table.sha256_normalized(),
            "retrieved_utc": aqr_entry.retrieved_utc,
            "parser_version": aqr.PARSER_VERSION,
            "first_observation": aqr_file.table.first_observation,
            "last_observation": aqr_file.table.last_observation,
            "validation_findings": list(aqr_report.summary()),
            "committed_manifest_sha256": _manifest_hash(aqr_pin, "committed_manifest"),
            "vendor_note": (
                "Vendor series, maintained by a firm that sells the strategy. exp_004 "
                "established that the archived workbook states NO fee, transaction-cost, "
                "slippage or financing basis anywhere, so it is treated as gross of every "
                "cost by omission."
            ),
        }
    )

    # --- FRED cash and the modelled long-duration proxy ---------------------
    for item in _sequence(_at(pin, "fred", where="source_pin"), where="source_pin.fred"):
        entry_spec = _mapping(item, where="source_pin.fred[]")
        series_id = _text(entry_spec, "series_id", where="source_pin.fred[]")
        cached_fred = fred.download(cache, series_id)
        table = fred.parse(cache, cached_fred, series_id)
        report = validate_table(
            table, dataset_id=f"fred_{series_id.lower()}", expected_columns=(series_id,)
        )
        if not report.ok:
            raise MarginalSleeveValueError(
                f"the FRED {series_id} table failed validation: " + "; ".join(report.summary())
            )
        raw_series[f"fred_{series_id.lower()}"] = _series_from_table(
            table, series_id, name=f"fred_{series_id.lower()}", source="FRED"
        )
        expected_fred = _text(entry_spec, "expected_sha256_raw", where="source_pin.fred[]")
        provenance.append(
            {
                "dataset_id": f"fred_{series_id.lower()}",
                "source_url": cached_fred.url,
                "sha256_raw": cached_fred.sha256,
                "sha256_raw_pinned": expected_fred,
                "sha256_matches_pin": cached_fred.sha256 == expected_fred,
                "abort_on_mismatch": False,
                "why_no_abort": (
                    "FRED appends observations rather than rewriting history, so the "
                    "file hash changes on every release. Only the two sources that "
                    "rebuild their history in place abort on a mismatch."
                ),
                "sha256_normalized": table.sha256_normalized(),
                "retrieved_utc": cached_fred.retrieved_utc,
                "parser_version": fred.PARSER_VERSION,
                "first_observation": table.first_observation,
                "last_observation": table.last_observation,
                "units": table.units,
                "validation_findings": list(report.summary()),
                "committed_manifest_sha256": _manifest_hash(entry_spec, "committed_manifest"),
            }
        )

    start = specification.sample_policy.start
    end = specification.sample_policy.end
    lead = 1
    periods, columns, findings = _aligned(
        raw_series, start=shift_period(start, -lead), end=end
    )
    expected_months = month_count(start, end)
    if len(periods) != expected_months + lead:
        raise MarginalSleeveValueError(
            f"the frozen sample {start}..{end} is {expected_months} months, plus "
            f"{lead} lead month for the modelled proxy, but only {len(periods)} "
            "survive alignment. A marginal figure computed on a shortened window is "
            "not the figure the specification froze."
        )
    if expected_months % MONTHS_PER_YEAR != 0:
        raise MarginalSleeveValueError(
            f"the frozen sample is {expected_months} months, not a whole number of "
            "calendar years, so the certainty equivalent cannot be computed without "
            "silently dropping months"
        )
    return PanelInputs(
        periods=periods,
        columns=columns,
        lead_months=lead,
        findings=findings,
        provenance=tuple(provenance),
        source_last_observations=tuple(
            (name, item.periods[-1] if item.periods else "")
            for name, item in sorted(raw_series.items())
        ),
    )


# --------------------------------------------------------------------------- #
# Sleeves, fee tiers and base portfolios
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FeeTier:
    """One frozen fee assumption, in decimal annual terms."""

    tier_id: str
    management_fee_annual: float
    performance_fee_rate: float

    def apply(self, gross_total: FloatArray) -> FloatArray:
        after_management = gross_total - self.management_fee_annual / MONTHS_PER_YEAR
        if self.performance_fee_rate <= 0.0:
            return after_management
        net, _ = high_water_mark_performance_fee(
            after_management, rate=self.performance_fee_rate
        )
        return net


@dataclass(frozen=True, slots=True, kw_only=True)
class CostColumn:
    """One frozen cost basis, applied identically to every portfolio.

    ``basis_key`` selects which column of ``cost_model.fee_tiers`` supplies the
    fund fee; the sleeve's own ``cost_tier`` selects the row. A long-only index
    fund and a long-short overlay pay very different fees, and collapsing them to
    one number would decide the experiment by assumption.
    """

    basis: CostBasis
    basis_key: str
    one_way_bps: float


@dataclass(frozen=True, slots=True, kw_only=True)
class Sleeve:
    """One candidate sleeve: a funded monthly total return and how it is judged."""

    sleeve_id: str
    kind: str
    cost_tier: str
    named_funding_leg: str
    gross_total_return: FloatArray
    in_holm_family: bool
    """Whether the sleeve belongs to the family of ten the frozen specification
    corrects across. The modelled proxy is excluded because the frozen text names
    ten, and adding it would only HARDEN the correction; nothing survives Holm at
    ten either way, so the choice is immaterial and is recorded rather than
    argued."""
    is_control: bool
    is_proxy: bool
    proxy_for: str
    description: str


def _fee_tiers(specification: Specification) -> dict[str, dict[str, FeeTier]]:
    """``{cost basis key: {tier id: FeeTier}}`` from the frozen cost model."""
    model = _mapping(specification.cost_model, where="cost_model")
    raw = _mapping(_at(model, "fee_tiers", where="cost_model"), where="cost_model.fee_tiers")
    out: dict[str, dict[str, FeeTier]] = {"gross": {}, "optimistic": {}, "pessimistic": {}}
    for tier_id, item in raw.items():
        entry = _mapping(item, where=f"fee_tiers.{tier_id}")
        optimistic = (
            _number(entry, "net_optimistic_management_fee_annual_percent", where=tier_id) / 100.0
        )
        pessimistic = (
            _number(entry, "net_pessimistic_management_fee_annual_percent", where=tier_id) / 100.0
        )
        performance = _number(entry, "performance_fee_percent_of_gains", where=tier_id) / 100.0
        out["gross"][tier_id] = FeeTier(
            tier_id=tier_id, management_fee_annual=0.0, performance_fee_rate=0.0
        )
        out["optimistic"][tier_id] = FeeTier(
            tier_id=tier_id, management_fee_annual=optimistic, performance_fee_rate=0.0
        )
        out["pessimistic"][tier_id] = FeeTier(
            tier_id=tier_id,
            management_fee_annual=pessimistic,
            performance_fee_rate=performance,
        )
    return out


def _cost_columns(specification: Specification) -> tuple[CostColumn, ...]:
    model = _mapping(specification.cost_model, where="cost_model")
    spread = _mapping(
        _at(model, "spread_and_commission", where="cost_model"), where="spread_and_commission"
    )
    optimistic_bps = _number(
        _mapping(_at(spread, "net_optimistic", where="spread"), where="spread.net_optimistic"),
        "one_way_bps",
        where="spread.net_optimistic",
    )
    pessimistic_bps = _number(
        _mapping(_at(spread, "net_pessimistic", where="spread"), where="spread.net_pessimistic"),
        "one_way_bps",
        where="spread.net_pessimistic",
    )
    return (
        CostColumn(basis=CostBasis.GROSS, basis_key="gross", one_way_bps=0.0),
        CostColumn(
            basis=CostBasis.NET_OPTIMISTIC,
            basis_key="optimistic",
            one_way_bps=optimistic_bps,
        ),
        CostColumn(
            basis=CostBasis.NET_PESSIMISTIC,
            basis_key="pessimistic",
            one_way_bps=pessimistic_bps,
        ),
    )


def _build_sleeves(inputs: PanelInputs, specification: Specification) -> tuple[Sleeve, ...]:
    """Assemble every candidate sleeve as a FUNDED monthly total return.

    A long-only research portfolio is already a funded total return. A long-short
    factor is not: it is self-financing, so cash is added to make it a funded
    position comparable with the others, exactly as exp_004 does for the vendor
    trend series. Which of the two a sleeve is is recorded on the sleeve and
    printed beside every figure, because the two have very different betas to an
    equity core and beta is the whole question here.
    """
    column = inputs.reported_columns
    cash = column["fred_tb3ms"] / MONTHS_PER_YEAR
    universe = _mapping(specification.universe, where="universe")
    declared = {
        _text(_mapping(item, where="universe.sleeves[]"), "id", where="universe.sleeves[]"): (
            _mapping(item, where="universe.sleeves[]")
        )
        for item in _sequence(_at(universe, "sleeves", where="universe"), where="universe.sleeves")
    }
    proxies = {
        _text(_mapping(item, where="universe.proxy_sleeves[]"), "id", where="proxy"): (
            _mapping(item, where="universe.proxy_sleeves[]")
        )
        for item in _sequence(
            _at(universe, "proxy_sleeves", where="universe"), where="universe.proxy_sleeves"
        )
    }
    control = {
        _text(_mapping(item, where="universe.calibration_control[]"), "id", where="control"): (
            _mapping(item, where="universe.calibration_control[]")
        )
        for item in _sequence(
            _at(universe, "calibration_control", where="universe"),
            where="universe.calibration_control",
        )
    }

    def total(name: str) -> FloatArray:
        return np.asarray(column[name], dtype=np.float64)

    def overlay(name: str) -> FloatArray:
        """A self-financing long-short factor made into a funded position by cash."""
        return total(name) + cash

    raw: dict[str, FloatArray] = {
        "us_small_value": total("us_small_value_total"),
        "dev_ex_us_small_value": total("dev_ex_us_small_value_total"),
        "emerging_small_value": total("emerging_small_value_total"),
        "dev_ex_us_equity": total("dev_ex_us_market_excess") + total("dev_ex_us_risk_free"),
        "emerging_equity": total("emerging_market_excess") + total("emerging_risk_free"),
        "us_momentum_overlay": overlay("us_momentum_factor"),
        "dev_ex_us_momentum_overlay": overlay("dev_ex_us_momentum_factor"),
        "emerging_momentum_overlay": overlay("emerging_momentum_factor"),
        "us_momentum_long_only": total("us_momentum_long_only_total"),
        "trend_aqr": overlay("trend_factor"),
    }

    sleeves: list[Sleeve] = []
    for sleeve_id, entry in declared.items():
        if sleeve_id not in raw:
            raise MarginalSleeveValueError(
                f"the specification declares sleeve {sleeve_id!r} but this module builds "
                f"{sorted(raw)}"
            )
        sleeves.append(
            Sleeve(
                sleeve_id=sleeve_id,
                kind=_text(entry, "kind", where=f"universe.sleeves.{sleeve_id}"),
                cost_tier=_text(entry, "cost_tier", where=f"universe.sleeves.{sleeve_id}"),
                named_funding_leg=_text(
                    entry, "funding_leg", where=f"universe.sleeves.{sleeve_id}"
                ),
                gross_total_return=raw[sleeve_id],
                in_holm_family=True,
                is_control=False,
                is_proxy=False,
                proxy_for="",
                description=_text(entry, "series", where=f"universe.sleeves.{sleeve_id}"),
            )
        )

    # The modelled long-duration proxy. Its first month is NaN by construction, so
    # the sample must already start after it; the check is explicit rather than a
    # silent nan_to_num.
    for sleeve_id, entry in proxies.items():
        # The FRED parser already divides the published percent by 100, so the
        # yield arrives here as a decimal per year, which is what the par-bond
        # approximation expects. The UNSLICED yield is used so that the lead month
        # supplies the first difference; the result is then sliced to the reported
        # window, which is why no month of the frozen sample is missing.
        modelled = bond_total_return_from_yield(inputs.columns["fred_gs10"])[
            inputs.lead_months :
        ]
        if not np.all(np.isfinite(modelled)):
            missing = int(np.count_nonzero(~np.isfinite(modelled)))
            raise MarginalSleeveValueError(
                f"the modelled long-duration proxy is missing in {missing} of "
                f"{modelled.size} months of the frozen sample. A proxy with holes is "
                "not a series; extend the alignment window rather than filling them."
            )
        sleeves.append(
            Sleeve(
                sleeve_id=sleeve_id,
                kind=_text(entry, "kind", where=f"universe.proxy_sleeves.{sleeve_id}"),
                cost_tier=_text(entry, "cost_tier", where=f"universe.proxy_sleeves.{sleeve_id}"),
                named_funding_leg=_text(
                    entry, "funding_leg", where=f"universe.proxy_sleeves.{sleeve_id}"
                ),
                gross_total_return=modelled,
                in_holm_family=False,
                is_control=False,
                is_proxy=True,
                proxy_for=_text(entry, "proxy_for", where=f"universe.proxy_sleeves.{sleeve_id}"),
                description="MODELLED PROXY reconstructed from FRED GS10; not investable",
            )
        )

    for sleeve_id, entry in control.items():
        sleeves.append(
            Sleeve(
                sleeve_id=sleeve_id,
                kind=_text(entry, "kind", where=f"universe.calibration_control.{sleeve_id}"),
                cost_tier="calibration_control",
                named_funding_leg="us_equity",
                gross_total_return=cash.copy(),
                in_holm_family=False,
                is_control=True,
                is_proxy=False,
                proxy_for="",
                description="cash, the null sleeve; a machine check, not a hypothesis",
            )
        )
    return tuple(sleeves)


def _asset_matrix(inputs: PanelInputs) -> FloatArray:
    """The four base assets in :data:`ASSET_NAMES` order, sleeve column excluded."""
    column = inputs.reported_columns
    return np.column_stack(
        [
            column["us_market_excess"] + column["us_risk_free"],
            column["dev_ex_us_market_excess"] + column["dev_ex_us_risk_free"],
            column["emerging_market_excess"] + column["emerging_risk_free"],
            column["fred_tb3ms"] / MONTHS_PER_YEAR,
        ]
    )


def _base_weights(specification: Specification) -> dict[str, FloatArray]:
    parameters = _mapping(specification.parameters, where="parameters")
    weights = _mapping(_at(parameters, "base_weights", where="parameters"), where="base_weights")
    us = _number(weights, "us", where="base_weights")
    developed = _number(weights, "developed_ex_us", where="base_weights")
    emerging = _number(weights, "emerging", where="base_weights")
    equity_share = _number(parameters, "balanced_equity_share", where="parameters")
    core = np.array([us, developed, emerging, 0.0], dtype=np.float64)
    if not math.isclose(float(core.sum()), 1.0, abs_tol=1e-12):
        raise MarginalSleeveValueError(
            f"the frozen base weights sum to {float(core.sum())!r}, not 1.0"
        )
    return {
        "global_equity_core": core,
        "balanced_60_40": np.array(
            [
                equity_share * us,
                equity_share * developed,
                equity_share * emerging,
                1.0 - equity_share,
            ],
            dtype=np.float64,
        ),
    }


def _weights_for(
    base: FloatArray, *, sleeve_weight: float, leg: str, named_leg: str
) -> tuple[FloatArray, bool]:
    """The five-asset target at ``sleeve_weight``, and whether it needs borrowing.

    ``pro_rata`` scales every base asset by ``1 - w``. A named leg or cash takes
    the whole weight out of one asset, which is only feasible while that asset
    holds at least ``w``; beyond that the target goes short, which is reported as
    levered rather than silently clipped.
    """
    target = np.zeros(len(ASSET_NAMES), dtype=np.float64)
    if leg == "pro_rata":
        target[:4] = base * (1.0 - sleeve_weight)
    else:
        asset = "cash" if leg == "cash" else named_leg
        if asset not in ASSET_NAMES[:4]:
            raise MarginalSleeveValueError(
                f"funding leg {asset!r} is not one of {ASSET_NAMES[:4]}"
            )
        index = ASSET_NAMES.index(asset)
        target[:4] = base
        target[index] -= sleeve_weight
    target[4] = sleeve_weight
    return target, bool(np.any(target < -1e-12))


# --------------------------------------------------------------------------- #
# Marginal results and their uncertainty
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class MarginalResult:
    """One sleeve, one base portfolio, one funding leg, one cost basis."""

    sleeve_id: str
    base_portfolio: str
    funding_leg: str
    basis: CostBasis
    window: str
    observations: int
    reference_weight: float
    deciding_basis: str
    marginal_percent: float
    """The paired difference on the DECIDING basis. Every interval, p-value and
    falsifier clause on this row reads this number and no other."""
    marginal_growth_percent: float
    """The same paired difference on the GEOMETRIC GROWTH basis, gamma = 1."""
    marginal_crra_percent: float
    """The same paired difference on the reported CRRA basis. One of these two is
    the deciding figure and the other is its companion; which is which is stated
    by ``deciding_basis`` rather than left to the reader. The gap between them IS
    the de-risking component that a risk-averse utility rewards and a growth rate
    does not, and decision record 0008 is the record of why it may not decide."""
    lower_95: float
    upper_95: float
    standard_error: float
    one_sided_p_value: float
    mde_bootstrap: float
    mde_normal: float
    block_length: float
    levered: bool
    neighbours: tuple[tuple[float, float, float], ...]

    @property
    def multiple_of_mde(self) -> float:
        return (
            self.marginal_percent / self.mde_bootstrap if self.mde_bootstrap > 0.0 else math.nan
        )

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "sleeve": self.sleeve_id,
            "base_portfolio": self.base_portfolio,
            "funding_leg": self.funding_leg,
            "cost_basis": self.basis.value,
            "window": self.window,
            "observations": self.observations,
            "effective_independent_blocks_at_12m": self.observations / self.block_length,
            "reference_weight": self.reference_weight,
            "deciding_basis": self.deciding_basis,
            "marginal_on_the_deciding_basis_pp_per_year": self.marginal_percent,
            "marginal_certainty_equivalent_pp_per_year": self.marginal_crra_percent,
            "marginal_geometric_growth_pp_per_year": self.marginal_growth_percent,
            "de_risking_component_pp_per_year": (
                self.marginal_crra_percent - self.marginal_growth_percent
            ),
            "two_sided_95": [self.lower_95, self.upper_95],
            "bootstrap_standard_error": self.standard_error,
            "one_sided_p_value_marginal_is_positive": self.one_sided_p_value,
            "minimum_detectable_effect_80_power_bootstrap": self.mde_bootstrap,
            "minimum_detectable_effect_80_power_sigma_over_sqrt_t": self.mde_normal,
            "marginal_as_multiple_of_its_own_mde": _json_float(self.multiple_of_mde),
            "block_length_months": self.block_length,
            "requires_borrowing": self.levered,
            "neighbour_block_intervals": [
                {"block_length": length, "two_sided_95": [low, high]}
                for length, low, high in self.neighbours
            ],
        }


def _paired_replicates(
    treatment: FloatArray,
    comparator: FloatArray,
    *,
    rng: np.random.Generator,
    block_length: float,
    n_resamples: int,
    gamma: float,
    chunk: int = 2000,
) -> FloatArray:
    """Resample the joint panel and recompute the paired difference on every draw.

    The two series are resampled with the SAME indices. Resampling them
    independently would destroy the pairing and produce an interval for the
    difference of two unrelated portfolios, which is a much wider and entirely
    different statement.
    """
    n = treatment.size
    replicates = np.empty(n_resamples, dtype=np.float64)
    done = 0
    while done < n_resamples:
        size = min(chunk, n_resamples - done)
        indices = stationary_bootstrap_indices(n, block_length, size, rng)
        left = _certainty_equivalent_rows(treatment[indices], gamma=gamma)
        right = _certainty_equivalent_rows(comparator[indices], gamma=gamma)
        replicates[done : done + size] = 100.0 * (left - right)
        done += size
    return replicates


def _marginal(
    treatment: FloatArray,
    comparator: FloatArray,
    *,
    sleeve_id: str,
    base_portfolio: str,
    funding_leg: str,
    basis: CostBasis,
    window: str,
    reference_weight: float,
    levered: bool,
    rng: np.random.Generator,
    settings: Settings,
    block_length: float,
    neighbours: Sequence[float],
    n_resamples: int,
) -> MarginalResult:
    gamma = settings.decision_gamma

    def paired(at_gamma: float) -> float:
        return 100.0 * (
            certainty_equivalent_annual(_annual_gross_matrix(treatment), gamma=at_gamma)
            - certainty_equivalent_annual(_annual_gross_matrix(comparator), gamma=at_gamma)
        )

    point = paired(gamma)
    growth_point = paired(1.0)
    crra_point = paired(settings.report_gamma)
    replicates = _paired_replicates(
        treatment,
        comparator,
        rng=rng,
        block_length=block_length,
        n_resamples=n_resamples,
        gamma=gamma,
    )
    low, high = np.quantile(replicates, [0.025, 0.975])
    standard_error = float(np.std(replicates, ddof=1))
    difference = treatment - comparator
    normal_error = (
        100.0
        * MONTHS_PER_YEAR
        * float(np.std(difference, ddof=1))
        / math.sqrt(float(difference.size))
    )
    neighbour_intervals: list[tuple[float, float, float]] = []
    for length in neighbours:
        draws = _paired_replicates(
            treatment,
            comparator,
            rng=rng,
            block_length=length,
            n_resamples=max(2000, n_resamples // 5),
            gamma=gamma,
        )
        neighbour_low, neighbour_high = np.quantile(draws, [0.025, 0.975])
        neighbour_intervals.append((float(length), float(neighbour_low), float(neighbour_high)))
    return MarginalResult(
        sleeve_id=sleeve_id,
        base_portfolio=base_portfolio,
        funding_leg=funding_leg,
        basis=basis,
        window=window,
        observations=treatment.size,
        reference_weight=reference_weight,
        deciding_basis=settings.deciding_basis,
        marginal_percent=point,
        marginal_growth_percent=growth_point,
        marginal_crra_percent=crra_point,
        lower_95=float(low),
        upper_95=float(high),
        standard_error=standard_error,
        one_sided_p_value=float(np.mean(replicates <= 0.0)),
        mde_bootstrap=minimum_detectable_effect(standard_error),
        mde_normal=minimum_detectable_effect(normal_error),
        block_length=block_length,
        levered=levered,
        neighbours=tuple(neighbour_intervals),
    )


def _reselected_optimum_interval(
    increments: FloatArray,
    base_returns: FloatArray,
    grid: FloatArray,
    *,
    rng: np.random.Generator,
    block_length: float,
    n_resamples: int,
    gamma: float,
    chunk: int = 2000,
) -> dict[str, JsonValue]:
    """Re-choose the optimal weight INSIDE every bootstrap replicate.

    ``increments`` is ``(T, G)``: the cost-charged monthly return of the portfolio
    at each grid weight minus the base portfolio's. The optimum is chosen from the
    same sample it is evaluated on, so an interval computed at the in-sample
    optimum is too narrow. Re-selecting inside each replicate makes the selection
    effect part of the interval instead of hiding it.
    """
    n = base_returns.size
    best_gains = np.empty(n_resamples, dtype=np.float64)
    best_weights = np.empty(n_resamples, dtype=np.float64)
    done = 0
    while done < n_resamples:
        size = min(chunk, n_resamples - done)
        indices = stationary_bootstrap_indices(n, block_length, size, rng)
        base = _certainty_equivalent_rows(base_returns[indices], gamma=gamma)
        gains = np.empty((size, grid.size), dtype=np.float64)
        for k in range(grid.size):
            path = base_returns[indices] + increments[:, k][indices]
            gains[:, k] = 100.0 * (_certainty_equivalent_rows(path, gamma=gamma) - base)
        chosen = np.argmax(gains, axis=1)
        best_gains[done : done + size] = gains[np.arange(size), chosen]
        best_weights[done : done + size] = grid[chosen]
        done += size
    low, high = np.quantile(best_gains, [0.025, 0.975])
    return {
        "note": (
            "The optimal weight is re-chosen inside every bootstrap replicate, so this "
            "interval carries the selection effect that an interval computed at the "
            "in-sample optimum does not. It is an interval for 'the gain a searcher "
            "who optimises in sample would report', which is why its lower end can sit "
            "above zero even when the sleeve adds nothing: the maximum of a noisy "
            "surface is positive by construction."
        ),
        "grid": [float(value) for value in grid],
        "reselected_gain_two_sided_95": [float(low), float(high)],
        "reselected_gain_median": float(np.median(best_gains)),
        "reselected_weight_median": float(np.median(best_weights)),
        "reselected_weight_two_sided_95": [
            float(value) for value in np.quantile(best_weights, [0.025, 0.975])
        ],
        "share_of_replicates_choosing_zero_weight": float(np.mean(best_weights <= 0.0)),
        "resamples": n_resamples,
    }


def _correlation_interval(
    sleeve: FloatArray,
    portfolio: FloatArray,
    *,
    rng: np.random.Generator,
    block_length: float,
    n_resamples: int,
    chunk: int = 2000,
) -> tuple[float, float]:
    """A paired block-bootstrap interval for the sleeve-to-portfolio correlation."""
    n = sleeve.size
    draws = np.empty(n_resamples, dtype=np.float64)
    done = 0
    while done < n_resamples:
        size = min(chunk, n_resamples - done)
        indices = stationary_bootstrap_indices(n, block_length, size, rng)
        a = sleeve[indices]
        b = portfolio[indices]
        a = a - a.mean(axis=1, keepdims=True)
        b = b - b.mean(axis=1, keepdims=True)
        numerator = np.sum(a * b, axis=1)
        denominator = np.sqrt(np.sum(a * a, axis=1) * np.sum(b * b, axis=1))
        with np.errstate(divide="ignore", invalid="ignore"):
            draws[done : done + size] = np.where(denominator > 0.0, numerator / denominator, 0.0)
        done += size
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(low), float(high)


# --------------------------------------------------------------------------- #
# Windows
# --------------------------------------------------------------------------- #


def _mask_for(periods: Sequence[str], start: str, end: str) -> BoolArray:
    low, high = month_index(start), month_index(end)
    return np.asarray([low <= month_index(period) <= high for period in periods], dtype=bool)


def _whole_year_mask(periods: Sequence[str], start: str, end: str) -> BoolArray:
    """A window mask a calendar-year certainty equivalent can consume, or all false."""
    mask = _mask_for(periods, start, end)
    count = int(np.count_nonzero(mask))
    aligned = start.endswith("-01") and end.endswith("-12")
    if aligned and count % MONTHS_PER_YEAR == 0 and count > 0:
        return mask
    return np.zeros(len(periods), dtype=bool)


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Settings:
    """Everything the frozen specification says about how to run this."""

    decision_gamma: float
    """The risk aversion whose metric DECIDES every threshold and every falsifier
    clause. Decision record 0008 sets it to 1 -- geometric growth -- for any
    specification frozen after that record, because the exact CRRA certainty
    equivalent over 35 calendar years rewards de-risking: this experiment's own
    cash control, which supplies zero alpha and zero diversification credit by
    construction, scores +0.166 pp/yr at gamma = 3 while LOSING 0.643 pp/yr of
    growth. A specification that does not name one falls back to
    :attr:`report_gamma`, which is what every specification frozen before that
    record meant."""
    report_gamma: float
    """The CRRA risk aversion reported BESIDE the deciding figure. Never alone and
    never as the deciding number, which is the whole content of decision 0008."""
    materiality: float
    reference_weight: float
    weight_cap: float
    weight_cap_half: float
    grid_step: float
    bootstrap_grid_step: float
    block_length: float
    neighbours: tuple[float, ...]
    resamples: int

    @property
    def deciding_basis(self) -> str:
        """A stable identifier for the basis, written beside every deciding figure."""
        if math.isclose(self.decision_gamma, 1.0):
            return "geometric_growth_gamma_1"
        return f"crra_certainty_equivalent_gamma_{self.decision_gamma:g}"

    @property
    def deciding_metric_name(self) -> str:
        """How the deciding figure is named in prose, in the falsifier's own words."""
        if math.isclose(self.decision_gamma, 1.0):
            return "marginal geometric growth rate"
        return "marginal certainty equivalent"

    @property
    def decides_on_growth(self) -> bool:
        return math.isclose(self.decision_gamma, 1.0)


def _settings(specification: Specification) -> Settings:
    parameters = _mapping(specification.parameters, where="parameters")
    report_gamma = _number(parameters, "crra_gamma", where="parameters")
    decision_gamma = (
        _number(parameters, "decision_gamma", where="parameters")
        if "decision_gamma" in parameters
        else report_gamma
    )
    return Settings(
        decision_gamma=decision_gamma,
        report_gamma=report_gamma,
        materiality=_number(
            parameters, "materiality_threshold_annual_percent", where="parameters"
        ),
        reference_weight=_number(parameters, "reference_weight", where="parameters"),
        weight_cap=_number(parameters, "weight_cap", where="parameters"),
        weight_cap_half=_number(parameters, "weight_cap_half", where="parameters"),
        grid_step=_number(parameters, "weight_grid_step", where="parameters"),
        bootstrap_grid_step=_number(parameters, "bootstrap_weight_grid_step", where="parameters"),
        block_length=12.0,
        neighbours=(6.0, 24.0),
        resamples=specification.inference.resamples,
    )


def _grid(cap: float, step: float) -> FloatArray:
    count = round(cap / step)
    if count < 2 or not math.isclose(count * step, cap, rel_tol=1e-9, abs_tol=1e-12):
        raise MarginalSleeveValueError(
            f"the weight cap {cap} is not a whole number of steps of {step}"
        )
    return np.linspace(0.0, cap, count + 1)


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class _Paths:
    """Cost-charged monthly returns for one sleeve on one grid, plus the base."""

    grid: FloatArray
    returns: FloatArray
    """``(T, G)``: the portfolio return at each grid weight."""
    base: FloatArray
    levered: tuple[bool, ...]


def _paths_for(
    *,
    assets: FloatArray,
    sleeve_net: FloatArray,
    base: FloatArray,
    leg: str,
    named_leg: str,
    grid: FloatArray,
    one_way_bps: float,
) -> _Paths:
    matrix = np.column_stack([assets, sleeve_net])
    columns: list[FloatArray] = []
    levered: list[bool] = []
    for weight in grid:
        target, needs_borrowing = _weights_for(
            base, sleeve_weight=float(weight), leg=leg, named_leg=named_leg
        )
        realised, _, _ = run_constant_weights(target, matrix, one_way_bps=one_way_bps)
        columns.append(realised)
        levered.append(needs_borrowing)
    stacked = np.column_stack(columns)
    return _Paths(grid=grid, returns=stacked, base=stacked[:, 0], levered=tuple(levered))


def _index_of(grid: FloatArray, weight: float) -> int:
    matches = np.flatnonzero(np.isclose(grid, weight, rtol=0.0, atol=1e-12))
    if matches.size != 1:
        raise MarginalSleeveValueError(
            f"the reference weight {weight} is not a point of the frozen grid"
        )
    return int(matches[0])


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 010."""
    settings = _settings(specification)
    rng = context.rng
    inputs = _load_inputs(specification)
    periods = inputs.reported_periods
    assets = _asset_matrix(inputs)
    sleeves = _build_sleeves(inputs, specification)
    tiers = _fee_tiers(specification)
    columns = _cost_columns(specification)
    default_column = columns[-1]
    bases = _base_weights(specification)
    fine_grid = _grid(settings.weight_cap, settings.grid_step)
    coarse_grid = _grid(settings.weight_cap, settings.bootstrap_grid_step)
    reference_index = _index_of(fine_grid, settings.reference_weight)

    full_mask = _whole_year_mask(
        periods, specification.sample_policy.start, specification.sample_policy.end
    )
    if not bool(full_mask.any()):
        raise MarginalSleeveValueError(
            "the frozen sample is not a whole number of calendar years, so the "
            "certainty equivalent cannot be computed without dropping months"
        )
    era_masks = {
        era.name: _whole_year_mask(periods, era.start, era.end)
        for era in specification.sample_policy.eras
    }

    marginals: list[MarginalResult] = []
    decompositions: list[JsonValue] = []
    surfaces: list[JsonValue] = []
    hostile_rows: list[JsonValue] = []
    reselected: list[JsonValue] = []
    primary: dict[str, MarginalResult] = {}
    sleeve_index = {sleeve.sleeve_id: sleeve for sleeve in sleeves}

    # Which (cost column, base portfolio, funding leg) cells are computed. The
    # net-pessimistic column is the decision column and is run against both base
    # portfolios and all three funding legs; the gross and net-optimistic columns
    # exist to size the cost gap and are run on the primary cell only. Enumerating
    # the cells here, rather than deciding inside the loop, is what keeps the
    # search countable.
    cells: list[tuple[CostColumn, str, str]] = []
    for column in columns:
        for base_id in BASE_PORTFOLIO_IDS:
            for leg in FUNDING_LEG_IDS:
                if column.basis is default_column.basis or (
                    base_id == BASE_PORTFOLIO_IDS[0] and leg == "pro_rata"
                ):
                    cells.append((column, base_id, leg))

    for sleeve in sleeves:
        for column, base_id, leg in cells:
            tier = tiers[column.basis_key][sleeve.cost_tier]
            sleeve_net = tier.apply(sleeve.gross_total_return)
            base = bases[base_id]
            is_primary_cell = (
                column.basis is default_column.basis
                and base_id == BASE_PORTFOLIO_IDS[0]
                and leg == "pro_rata"
            )
            paths = _paths_for(
                assets=assets,
                sleeve_net=sleeve_net,
                base=base,
                leg=leg,
                named_leg=sleeve.named_funding_leg,
                grid=fine_grid,
                one_way_bps=column.one_way_bps,
            )
            treatment = paths.returns[:, reference_index][full_mask]
            comparator = paths.base[full_mask]
            result = _marginal(
                treatment,
                comparator,
                sleeve_id=sleeve.sleeve_id,
                base_portfolio=base_id,
                funding_leg=leg,
                basis=column.basis,
                window="full_period",
                reference_weight=settings.reference_weight,
                levered=paths.levered[reference_index],
                rng=rng,
                settings=settings,
                block_length=settings.block_length,
                neighbours=settings.neighbours if is_primary_cell else (),
                n_resamples=settings.resamples,
            )
            marginals.append(result)
            if is_primary_cell:
                primary[sleeve.sleeve_id] = result

            # --- the decomposition and the weight surface -------------
            base_returns = paths.base[full_mask]
            funding_returns = _funding_returns(
                assets=assets,
                base=base,
                portfolio=base_returns,
                leg=leg,
                named_leg=sleeve.named_funding_leg,
                mask=full_mask,
            )
            decompositions.append(
                _decomposition_row(
                    sleeve=sleeve,
                    sleeve_net=sleeve_net[full_mask],
                    funding=funding_returns,
                    portfolio=base_returns,
                    base_portfolio=base_id,
                    funding_leg=leg,
                    basis=column.basis,
                    settings=settings,
                    rng=rng,
                    n_resamples=settings.resamples,
                    with_interval=is_primary_cell,
                    realised_growth_marginal=result.marginal_growth_percent,
                )
            )
            gains = _gain_curve(paths, full_mask, gamma=settings.decision_gamma)
            surface = optimal_long_only_weight(
                [float(value) for value in fine_grid],
                [float(value) for value in gains],
                cap=settings.weight_cap,
                materiality=settings.materiality,
            )
            half = _index_of(fine_grid, settings.weight_cap_half)
            half_surface = optimal_long_only_weight(
                [float(value) for value in fine_grid[: half + 1]],
                [float(value) for value in gains[: half + 1]],
                cap=settings.weight_cap_half,
                materiality=settings.materiality,
            )
            surfaces.append(
                {
                    "sleeve": sleeve.sleeve_id,
                    "base_portfolio": base_id,
                    "funding_leg": leg,
                    "cost_basis": column.basis.value,
                    "is_proxy": sleeve.is_proxy,
                    **surface.to_json(),
                    "halved_cap": {
                        "cap": settings.weight_cap_half,
                        "optimal_weight": half_surface.optimal_weight,
                        "gain_at_optimum_pp_per_year": half_surface.optimal_gain,
                    },
                }
            )
            if is_primary_cell:
                coarse = _paths_for(
                    assets=assets,
                    sleeve_net=sleeve_net,
                    base=base,
                    leg=leg,
                    named_leg=sleeve.named_funding_leg,
                    grid=coarse_grid,
                    one_way_bps=column.one_way_bps,
                )
                increments = coarse.returns[full_mask] - coarse.base[full_mask][:, None]
                reselected.append(
                    {
                        "sleeve": sleeve.sleeve_id,
                        **_reselected_optimum_interval(
                            increments,
                            coarse.base[full_mask],
                            coarse_grid,
                            rng=rng,
                            block_length=settings.block_length,
                            n_resamples=settings.resamples,
                            gamma=settings.decision_gamma,
                        ),
                    }
                )
                hostile_rows.append(
                    _hostile_row(
                        sleeve=sleeve,
                        assets=assets,
                        base=base,
                        base_id=base_id,
                        leg=leg,
                        tier=tier,
                        column=column,
                        grid=fine_grid,
                        reference_index=reference_index,
                        full_mask=full_mask,
                        era_masks=era_masks,
                        settings=settings,
                        periods=periods,
                    )
                )

    family = [
        result
        for sleeve_id, result in sorted(primary.items())
        if sleeve_index[sleeve_id].in_holm_family
    ]
    holm = holm_bonferroni([item.one_sided_p_value for item in family], alpha=0.05)

    control_check = _calibration_control(marginals, settings)

    verdicts = _apply_rejection_rule(
        primary=primary,
        sleeves=sleeve_index,
        decompositions=decompositions,
        surfaces=surfaces,
        marginals=marginals,
        holm=holm,
        family=family,
        settings=settings,
    )

    diagnostics: dict[str, JsonValue] = {
        "deciding_metric": {
            "basis": settings.deciding_basis,
            "gamma": settings.decision_gamma,
            "name": settings.deciding_metric_name,
            "reported_beside_it": {
                "geometric_growth_gamma_1": True,
                "crra_certainty_equivalent_gamma": settings.report_gamma,
            },
            "decision_record": "docs/decisions/0008-growth-decides-crra-reports.md",
            "why": (
                "Geometric growth decides because the exact CRRA certainty equivalent "
                "over 35 calendar-year returns pays a sleeve for reducing risk, and "
                "any investor obtains that reduction free by holding less equity. The "
                "cash calibration control in this same experiment measures the size of "
                "the payment: it supplies no alpha and no diversification credit and "
                "still scores positively at gamma = 3. The certainty equivalent stays "
                "reported beside the growth figure because the gap between them IS "
                "that de-risking component, and hiding it would be the opposite error."
            ),
        },
        "evaluation_disclosure": _at(
            _mapping(specification.parameters, where="parameters"),
            "evaluation_disclosure",
            where="parameters",
        ),
        "sources": list(inputs.provenance),
        "alignment_findings": list(inputs.findings),
        "sample": {
            "lead_month_never_reported": inputs.periods[0],
            "first_month": periods[0],
            "last_month": periods[-1],
            "months": len(periods),
            "whole_calendar_years": len(periods) // MONTHS_PER_YEAR,
            "effective_independent_blocks_at_12m": len(periods) / settings.block_length,
            "months_beyond_the_holdout_by_source": {
                name: max(0, month_count(specification.sample_policy.end, last) - 1)
                for name, last in inputs.source_last_observations
                if last
            },
        },
        "sleeves_tested": [
            {
                "sleeve": sleeve.sleeve_id,
                "kind": sleeve.kind,
                "series": sleeve.description,
                "cost_tier": sleeve.cost_tier,
                "named_funding_leg": sleeve.named_funding_leg,
                "in_holm_family": sleeve.in_holm_family,
                "is_calibration_control": sleeve.is_control,
                "is_proxy": sleeve.is_proxy,
                "proxy_for": sleeve.proxy_for,
            }
            for sleeve in sleeves
        ],
        "sleeves_not_tested": _at(
            _mapping(specification.parameters, where="parameters"),
            "sleeves_not_tested",
            where="parameters",
        ),
        "gold_statement": (
            "GOLD WAS NOT TESTED. It is one of only two candidate assets with a "
            "plausibly low equity beta, and therefore one of the two most likely to "
            "earn a real diversification credit. No research-grade gold price or "
            "total-return series is reachable from this repository; decision record "
            "0002 establishes that no free price source carries a documented "
            "total-return or corporate-action contract, and no gold series is "
            "registered in portfolio_edge.data.fred. Its absence biases this "
            "experiment TOWARD the finding that no credit exists anywhere, and that "
            "direction is stated here rather than left for a reader to infer."
        ),
        "marginal_results": [item.to_json() for item in marginals],
        "decompositions": decompositions,
        "weight_surfaces": surfaces,
        "reselected_optima": reselected,
        "hostile_tests": hostile_rows,
        "multiple_testing": {
            "method": holm.method,
            "alpha": holm.alpha,
            "family_size": len(family),
            "sleeves_tested_total": len(sleeves),
            "rows": [
                {
                    "sleeve": item.sleeve_id,
                    "p_uncorrected": item.one_sided_p_value,
                    "holm_adjusted_p": float(adjusted),
                    "holm_rejected": bool(rejected),
                }
                for item, adjusted, rejected in zip(
                    family, holm.adjusted_p_values, holm.rejected, strict=True
                )
            ],
            "sleeves_outside_the_family": (
                "The modelled long-duration proxy and the cash calibration control are "
                "tested but excluded from the family of ten the frozen specification "
                "names. Including the proxy would only HARDEN the correction and no "
                "sleeve survives Holm at ten either way, so the exclusion cannot "
                "flatter anything; the control is a machine check, not a hypothesis."
            ),
            "trial_count_note": (
                f"This experiment tested {len(family)} sleeves in its Holm family plus "
                "a modelled proxy and a calibration control, on one base portfolio, one "
                "funding leg and one cost column. That number is a LOWER bound on the "
                "correction the "
                "whole search requires: it counts neither the three funding legs, the "
                "two base portfolios, the three cost columns, the two eras, nor the "
                "twelve distinct specifications this repository had already frozen "
                "before this one. Any later deflated-Sharpe trial count must start "
                f"from thirteen specifications and add these {len(family)} sleeves."
            ),
            "dependence_warning": (
                "Every sleeve here is measured against the same base portfolio over "
                "the same 420 months, and eight of the ten are equity claims that "
                "share the global equity factor. The tests are strongly dependent. "
                "Holm is valid under arbitrary dependence, which is why it was chosen "
                "over Benjamini-Hochberg."
            ),
        },
        "predeclared_prediction_scorecard": _score_prediction(decompositions, sleeve_index),
        "calibration_control": control_check,
        "credit_ceiling": _credit_ceiling(decompositions, settings),
        "verdicts": verdicts,
    }

    status, summary = _experiment_status(verdicts, primary, control_check, settings)
    return ExperimentResult(
        status=status,
        summary=summary,
        estimates=_estimates(primary, decompositions, surfaces, settings, sleeve_index),
        diagnostics=diagnostics,
        caveats=_caveats(settings),
        frames=_frames(marginals, decompositions, surfaces),
    )


def _funding_returns(
    *,
    assets: FloatArray,
    base: FloatArray,
    portfolio: FloatArray,
    leg: str,
    named_leg: str,
    mask: BoolArray,
) -> FloatArray:
    """The monthly return of whatever the sleeve is funded out of.

    Under ``pro_rata`` that is the REALISED base portfolio, costs and all, which is
    what an investor actually sells and what makes the credit collapse exactly to
    ``gamma sigma_p^2 (1 - beta_ip)``. Using the uncosted weighted average instead
    would leave a small residual in that identity and hide it inside the
    decomposition. Under a named leg or cash it is that single asset, and the
    credit becomes ``sigma_fp - sigma_ip``, a different quantity that can carry the
    opposite sign.
    """
    del base
    if leg == "pro_rata":
        return portfolio
    asset = "cash" if leg == "cash" else named_leg
    return assets[:, ASSET_NAMES.index(asset)][mask]


def _gain_curve(paths: _Paths, mask: BoolArray, *, gamma: float) -> FloatArray:
    base = certainty_equivalent_annual(_annual_gross_matrix(paths.base[mask]), gamma=gamma)
    return np.asarray(
        [
            100.0
            * (
                certainty_equivalent_annual(
                    _annual_gross_matrix(paths.returns[:, k][mask]), gamma=gamma
                )
                - base
            )
            for k in range(paths.grid.size)
        ],
        dtype=np.float64,
    )


def _decomposition_row(
    *,
    sleeve: Sleeve,
    sleeve_net: FloatArray,
    funding: FloatArray,
    portfolio: FloatArray,
    base_portfolio: str,
    funding_leg: str,
    basis: CostBasis,
    settings: Settings,
    rng: np.random.Generator,
    n_resamples: int,
    with_interval: bool,
    realised_growth_marginal: float,
) -> JsonValue:
    """The alpha/credit split at gamma = 1 and at the frozen gamma, plus sensitivity.

    ``realised_growth_marginal`` is the actual cost-charged growth difference at the
    reference weight. Reporting the first-order prediction beside it is the check
    that the decomposition describes the portfolio that was really built, and not a
    portfolio the algebra imagined.
    """
    covariance = np.cov(np.column_stack([sleeve_net, funding, portfolio]), rowvar=False, ddof=1)
    growth = moment_growth_decomposition(
        mean_sleeve=float(np.mean(sleeve_net)),
        mean_funding=float(np.mean(funding)),
        cov_sleeve_portfolio=float(covariance[0, 2]),
        cov_funding_portfolio=float(covariance[1, 2]),
        variance_sleeve=float(covariance[0, 0]),
        variance_portfolio=float(covariance[2, 2]),
        gamma=1.0,
    )
    crra = moment_growth_decomposition(
        mean_sleeve=float(np.mean(sleeve_net)),
        mean_funding=float(np.mean(funding)),
        cov_sleeve_portfolio=float(covariance[0, 2]),
        cov_funding_portfolio=float(covariance[1, 2]),
        variance_sleeve=float(covariance[0, 0]),
        variance_portfolio=float(covariance[2, 2]),
        gamma=settings.report_gamma,
    )
    deciding = growth if settings.decides_on_growth else crra
    exact = exact_growth_derivative(sleeve_net, funding, portfolio)
    relative_variance = MONTHS_PER_YEAR * float(np.var(sleeve_net - funding, ddof=1))
    analytic = closed_form_optimum(
        growth.moment_total, relative_variance, cap=settings.weight_cap
    )
    correlation_low = correlation_high = math.nan
    credit_low = credit_high = math.nan
    if with_interval:
        correlation_low, correlation_high = _correlation_interval(
            sleeve_net,
            portfolio,
            rng=rng,
            block_length=settings.block_length,
            n_resamples=n_resamples,
        )
        # Hold the volatilities at their point estimates and move only rho, which is
        # the sensitivity the frozen specification asks for. Annualising the
        # covariance by 12 and multiplying the two ANNUALISED volatilities are the
        # same operation, so no factor of 12 appears twice here.
        scale = growth.sleeve_volatility * growth.portfolio_volatility
        annual_funding_covariance = MONTHS_PER_YEAR * float(covariance[1, 2])

        def credit_at(rho: float) -> float:
            return annual_funding_covariance - rho * scale

        credit_low = 100.0 * credit_at(correlation_high)
        credit_high = 100.0 * credit_at(correlation_low)
    return {
        "sleeve": sleeve.sleeve_id,
        "base_portfolio": base_portfolio,
        "funding_leg": funding_leg,
        "cost_basis": basis.value,
        "is_proxy": sleeve.is_proxy,
        "proxy_for": sleeve.proxy_for,
        "growth_gamma_1": {
            "alpha_term_pp_per_year_per_unit_weight": 100.0 * growth.alpha_term,
            "diversification_credit_pp_per_year_per_unit_weight": 100.0 * growth.credit_term,
            "moment_total_pp_per_year_per_unit_weight": 100.0 * growth.moment_total,
            "exact_derivative_pp_per_year_per_unit_weight": 100.0 * exact,
            "higher_moment_residual_pp_per_year_per_unit_weight": 100.0
            * (exact - growth.moment_total),
            "predicted_growth_marginal_at_the_reference_weight_pp_per_year": (
                100.0 * settings.reference_weight * growth.moment_total
            ),
            "realised_growth_marginal_at_the_reference_weight_pp_per_year": (
                realised_growth_marginal
            ),
            "reconciliation_gap_pp_per_year": (
                realised_growth_marginal - 100.0 * settings.reference_weight * growth.moment_total
            ),
            "reconciliation_note": (
                "The prediction is first order in the weight and second order in the "
                "moments, and it ignores the trading cost the realised path pays. The "
                "gap between the two is therefore expected to be small and non-zero; a "
                "LARGE gap would mean the decomposition is not describing the portfolio "
                "that was actually built."
            ),
        },
        "crra_gamma": {
            "gamma": settings.report_gamma,
            "alpha_term_pp_per_year_per_unit_weight": 100.0 * crra.alpha_term,
            "diversification_credit_pp_per_year_per_unit_weight": 100.0 * crra.credit_term,
            "moment_total_pp_per_year_per_unit_weight": 100.0 * crra.moment_total,
        },
        "deciding_basis": settings.deciding_basis,
        "at_the_reference_weight": {
            "reference_weight": settings.reference_weight,
            "alpha_term_pp_per_year": 100.0 * settings.reference_weight * crra.alpha_term,
            "diversification_credit_pp_per_year": (
                100.0 * settings.reference_weight * crra.credit_term
            ),
            "on_the_deciding_basis": {
                "basis": settings.deciding_basis,
                "gamma": settings.decision_gamma,
                "alpha_term_pp_per_year": (
                    100.0 * settings.reference_weight * deciding.alpha_term
                ),
                "diversification_credit_pp_per_year": (
                    100.0 * settings.reference_weight * deciding.credit_term
                ),
                "note": (
                    "The alpha term does not depend on gamma at all; only the credit "
                    "is scaled by it. A basis that scales the credit by three is "
                    "therefore paying three times over for the same covariance, which "
                    "is the second-moment shadow of the de-risking reward decision "
                    "record 0008 removes from the deciding metric."
                ),
            },
        },
        "closed_form_growth_optimum": {
            **analytic.to_json(),
            "note": (
                "The analytic optimum of the quadratic growth curve, w* = D / tau^2. "
                "It answers a different question from the numerical certainty-equivalent "
                "optimum reported in weight_surfaces: this one optimises a second-moment "
                "model of the GROWTH rate with no costs, that one optimises an exact "
                "CRRA utility over the realised cost-charged path. Both are reported."
            ),
        },
        "beta_sleeve_to_portfolio": _json_float(growth.beta_sleeve_to_portfolio),
        "beta_funding_to_portfolio": _json_float(growth.beta_funding_to_portfolio),
        "correlation_sleeve_to_portfolio": _json_float(
            growth.correlation_sleeve_to_portfolio
        ),
        "correlation_two_sided_95": [
            _json_float(correlation_low),
            _json_float(correlation_high),
        ],
        "sleeve_annualised_volatility_percent": 100.0 * growth.sleeve_volatility,
        "portfolio_annualised_volatility_percent": 100.0 * growth.portfolio_volatility,
        "credit_change_per_0.10_of_correlation_pp_per_year": (
            100.0 * 0.10 * growth.credit_derivative_per_correlation
        ),
        "credit_at_the_correlation_interval_bounds_pp_per_year": [
            _json_float(credit_low),
            _json_float(credit_high),
        ],
        "credit_sensitivity_band_spans_zero": bool(
            math.isfinite(credit_low)
            and math.isfinite(credit_high)
            and credit_low <= 0.0 <= credit_high
        ),
    }


def _hostile_row(
    *,
    sleeve: Sleeve,
    assets: FloatArray,
    base: FloatArray,
    base_id: str,
    leg: str,
    tier: FeeTier,
    column: CostColumn,
    grid: FloatArray,
    reference_index: int,
    full_mask: BoolArray,
    era_masks: Mapping[str, BoolArray],
    settings: Settings,
    periods: Sequence[str],
) -> JsonValue:
    """Every hostile test the frozen specification demands, favourable or not."""
    gamma = settings.decision_gamma

    def marginal_point(sleeve_gross: FloatArray, *, bps: float, fee: FeeTier) -> float:
        paths = _paths_for(
            assets=assets,
            sleeve_net=fee.apply(sleeve_gross),
            base=base,
            leg=leg,
            named_leg=sleeve.named_funding_leg,
            grid=grid,
            one_way_bps=bps,
        )
        treatment = paths.returns[:, reference_index][full_mask]
        comparator = paths.base[full_mask]
        return 100.0 * (
            certainty_equivalent_annual(_annual_gross_matrix(treatment), gamma=gamma)
            - certainty_equivalent_annual(_annual_gross_matrix(comparator), gamma=gamma)
        )

    baseline = marginal_point(sleeve.gross_total_return, bps=column.one_way_bps, fee=tier)

    doubled_fee = FeeTier(
        tier_id=f"{tier.tier_id}x2",
        management_fee_annual=2.0 * tier.management_fee_annual,
        performance_fee_rate=min(2.0 * tier.performance_fee_rate, 0.99),
    )
    delayed = np.concatenate(([sleeve.gross_total_return[0]], sleeve.gross_total_return[:-1]))

    # Drop the sleeve's single best calendar year: replace it with the funding leg's
    # own return so the weight still exists but earns nothing distinctive.
    everything = np.ones(len(periods), dtype=bool)
    funding = _funding_returns(
        assets=assets,
        base=base,
        portfolio=assets @ base,
        leg=leg,
        named_leg=sleeve.named_funding_leg,
        mask=everything,
    )
    yearly = (sleeve.gross_total_return - funding).reshape(-1, MONTHS_PER_YEAR).sum(axis=1)
    best_year = int(np.argmax(yearly))
    without_best = sleeve.gross_total_return.copy()
    slice_start = best_year * MONTHS_PER_YEAR
    without_best[slice_start : slice_start + MONTHS_PER_YEAR] = funding[
        slice_start : slice_start + MONTHS_PER_YEAR
    ]

    era_rows: dict[str, JsonValue] = {}
    for name, mask in era_masks.items():
        if not bool(mask.any()) or name == "full_period":
            continue
        paths = _paths_for(
            assets=assets,
            sleeve_net=tier.apply(sleeve.gross_total_return),
            base=base,
            leg=leg,
            named_leg=sleeve.named_funding_leg,
            grid=grid,
            one_way_bps=column.one_way_bps,
        )
        era_rows[name] = 100.0 * (
            certainty_equivalent_annual(
                _annual_gross_matrix(paths.returns[:, reference_index][mask]), gamma=gamma
            )
            - certainty_equivalent_annual(_annual_gross_matrix(paths.base[mask]), gamma=gamma)
        )

    return {
        "sleeve": sleeve.sleeve_id,
        "base_portfolio": base_id,
        "funding_leg": leg,
        "cost_basis": column.basis.value,
        "baseline_marginal_pp_per_year": baseline,
        "doubled_costs_marginal_pp_per_year": marginal_point(
            sleeve.gross_total_return, bps=2.0 * column.one_way_bps, fee=doubled_fee
        ),
        "delayed_one_month_marginal_pp_per_year": marginal_point(
            delayed, bps=column.one_way_bps, fee=tier
        ),
        "best_year_removed": {
            "calendar_year": periods[slice_start][:4],
            "marginal_pp_per_year": marginal_point(
                without_best, bps=column.one_way_bps, fee=tier
            ),
        },
        "by_era_pp_per_year": era_rows,
    }


def _score_prediction(
    decompositions: Sequence[JsonValue], sleeves: Mapping[str, Sleeve]
) -> JsonValue:
    """Score the frozen prediction that equity sleeves carry a non-positive credit."""
    equity_kinds = {"long-only"}
    rows: list[JsonValue] = []
    agree = 0
    total = 0
    for item in decompositions:
        if not isinstance(item, Mapping):
            continue
        if item.get("funding_leg") != "pro_rata" or item.get("cost_basis") != "net-pessimistic":
            continue
        if item.get("base_portfolio") != BASE_PORTFOLIO_IDS[0]:
            continue
        sleeve_id = str(item.get("sleeve"))
        sleeve = sleeves.get(sleeve_id)
        if sleeve is None or sleeve.is_control:
            continue
        growth = item.get("growth_gamma_1")
        if not isinstance(growth, Mapping):
            continue
        credit = float(
            str(growth.get("diversification_credit_pp_per_year_per_unit_weight"))
        )
        beta = item.get("beta_sleeve_to_portfolio")
        predicted = "non-positive" if sleeve.kind in equity_kinds else "positive"
        realised = "positive" if credit > 0.0 else "non-positive"
        total += 1
        if predicted == realised:
            agree += 1
        rows.append(
            {
                "sleeve": sleeve_id,
                "kind": sleeve.kind,
                "predicted_credit_sign": predicted,
                "realised_credit_sign": realised,
                "credit_pp_per_year_per_unit_weight": credit,
                "beta_to_portfolio": beta,
                "prediction_held": predicted == realised,
            }
        )
    return {
        "prediction": (
            "Every long-only equity sleeve carries a beta at or above one to the "
            "equity core and therefore a credit at or below zero; only trend and the "
            "long-duration proxy carry a positive credit."
        ),
        "frozen_before_any_result": True,
        "rows": rows,
        "sleeves_scored": total,
        "sleeves_matching_the_prediction": agree,
        "note": (
            "A contradiction of this prediction is the more interesting outcome and is "
            "reported here as prominently as a confirmation. The prediction is about "
            "the SIGN of the credit under pro-rata funding, not its size."
        ),
    }


# --------------------------------------------------------------------------- #
# The frozen rejection rule
# --------------------------------------------------------------------------- #


def _apply_rejection_rule(
    *,
    primary: Mapping[str, MarginalResult],
    sleeves: Mapping[str, Sleeve],
    decompositions: Sequence[JsonValue],
    surfaces: Sequence[JsonValue],
    marginals: Sequence[MarginalResult],
    holm: MultipleTestingResult,
    family: Sequence[MarginalResult],
    settings: Settings,
) -> JsonValue:
    """Apply the frozen falsifier clause by clause, per sleeve."""
    holm_rejected = {
        item.sleeve_id: bool(flag)
        for item, flag in zip(family, holm.rejected, strict=True)
    }
    holm_adjusted = {
        item.sleeve_id: float(value)
        for item, value in zip(family, holm.adjusted_p_values, strict=True)
    }

    def primary_decomposition(sleeve_id: str) -> Mapping[str, JsonValue] | None:
        for item in decompositions:
            if (
                isinstance(item, Mapping)
                and item.get("sleeve") == sleeve_id
                and item.get("funding_leg") == "pro_rata"
                and item.get("cost_basis") == "net-pessimistic"
                and item.get("base_portfolio") == BASE_PORTFOLIO_IDS[0]
            ):
                return item
        return None

    def primary_surface(sleeve_id: str) -> Mapping[str, JsonValue] | None:
        for item in surfaces:
            if (
                isinstance(item, Mapping)
                and item.get("sleeve") == sleeve_id
                and item.get("funding_leg") == "pro_rata"
                and item.get("cost_basis") == "net-pessimistic"
                and item.get("base_portfolio") == BASE_PORTFOLIO_IDS[0]
            ):
                return item
        return None

    def named_leg_marginal(sleeve_id: str) -> float | None:
        for item in marginals:
            if (
                item.sleeve_id == sleeve_id
                and item.funding_leg == "named_leg"
                and item.basis is CostBasis.NET_PESSIMISTIC
                and item.base_portfolio == BASE_PORTFOLIO_IDS[0]
            ):
                return item.marginal_percent
        return None

    rows: list[JsonValue] = []
    for sleeve_id, result in sorted(primary.items()):
        sleeve = sleeves[sleeve_id]
        decomposition = primary_decomposition(sleeve_id)
        surface = primary_surface(sleeve_id)
        fired: list[str] = []
        unresolved: list[str] = []

        if result.marginal_percent < settings.materiality:
            fired.append(
                f"(a) the {settings.deciding_metric_name} at the reference weight is "
                f"{result.marginal_percent:+.3f} pp/yr, below the frozen materiality "
                f"threshold of {settings.materiality:.2f}"
                + (
                    f" (the CRRA gamma={settings.report_gamma:g} companion is "
                    f"{result.marginal_crra_percent:+.3f}, which would NOT have fired "
                    "this clause; decision record 0008 is why the growth figure "
                    "decides and the companion does not)"
                    if settings.decides_on_growth
                    and result.marginal_crra_percent >= settings.materiality
                    else ""
                )
            )
        credit = math.nan
        if decomposition is not None:
            growth = decomposition.get("growth_gamma_1")
            if isinstance(growth, Mapping):
                credit = float(
                    str(growth.get("diversification_credit_pp_per_year_per_unit_weight"))
                )
        if math.isfinite(credit) and credit <= 0.0:
            fired.append(
                f"(b) the diversification credit is {credit:+.3f} pp/yr per unit weight, "
                "zero or negative, so the portfolio-level view supplies no credit the "
                "standalone chain omitted and the existing standalone dismissal stands "
                "unaltered -- indeed strengthened"
            )
        if surface is not None and bool(surface.get("optimum_at_long_only_boundary")):
            fired.append("(c) the constrained optimum is zero weight at the long-only boundary")
        if sleeve.in_holm_family and not holm_rejected.get(sleeve_id, False):
            fired.append(
                f"(d) the sleeve does not survive Holm at 0.05 across the family of "
                f"{len(family)}; adjusted p = {holm_adjusted.get(sleeve_id, 1.0):.4f}"
            )

        if result.lower_95 <= 0.0 <= result.upper_95:
            unresolved.append(
                f"(u1) the 95% interval [{result.lower_95:+.3f}, {result.upper_95:+.3f}] "
                "contains zero"
            )
        if abs(result.marginal_percent) < result.mde_bootstrap:
            unresolved.append(
                f"(u2) the marginal figure on the deciding basis "
                f"{result.marginal_percent:+.3f} is smaller than "
                f"its own minimum detectable effect at 80% power, {result.mde_bootstrap:.3f}"
            )
        named = named_leg_marginal(sleeve_id)
        if named is not None and named * result.marginal_percent < 0.0:
            unresolved.append(
                f"(u3) the sign flips between funding legs: {result.marginal_percent:+.3f} "
                f"pro rata against {named:+.3f} from the named leg"
            )
        if decomposition is not None and bool(
            decomposition.get("credit_sensitivity_band_spans_zero")
        ):
            unresolved.append(
                "(u4) the credit evaluated at the two ends of the correlation's own 95% "
                "interval spans zero"
            )
        if sleeve.is_proxy:
            unresolved.append(
                "(u5) the sleeve is a declared PROXY series, so it may not resolve "
                "anything whatever it measures"
            )

        if fired:
            status = ResultStatus.REJECTED
        elif unresolved:
            status = ResultStatus.UNRESOLVED
        else:
            status = ResultStatus.EXPLORATORY
        proxy_note = ""
        if sleeve.is_proxy:
            proxy_note = (
                "PROXY. Whatever status this row carries is a statement about the "
                "MODELLED series and never about the thing it stands in for, which is: "
                f"{sleeve.proxy_for.strip()} "
                "The frozen falsifier orders the rejection clauses ahead of the "
                "`unresolved` triggers, so clause (u5) -- 'a modelled series may never "
                "resolve anything' -- reaches this row only when no rejection clause "
                "fires. That ordering is applied as frozen rather than reinterpreted "
                "after the fact, and this note carries the consequence instead."
            )
        rows.append(
            {
                "sleeve": sleeve_id,
                "in_holm_family": sleeve.in_holm_family,
                "is_calibration_control": sleeve.is_control,
                "is_proxy": sleeve.is_proxy,
                "proxy_note": proxy_note,
                "status": status.value,
                "marginal_pp_per_year": result.marginal_percent,
                "marginal_geometric_growth_pp_per_year": result.marginal_growth_percent,
                "marginal_certainty_equivalent_pp_per_year": result.marginal_crra_percent,
                "de_risking_component_pp_per_year": (
                    result.marginal_crra_percent - result.marginal_growth_percent
                ),
                "two_sided_95": [result.lower_95, result.upper_95],
                "minimum_detectable_effect": result.mde_bootstrap,
                "diversification_credit_pp_per_year_per_unit_weight": _json_float(credit),
                "holm_adjusted_p": holm_adjusted.get(sleeve_id),
                "falsifier_clauses_fired": fired,
                "unresolved_triggers": unresolved,
            }
        )
    return {
        "materiality_threshold_annual_percent": settings.materiality,
        "reference_weight": settings.reference_weight,
        "deciding_basis": settings.deciding_basis,
        "deciding_gamma": settings.decision_gamma,
        "primary_cell": (
            f"{BASE_PORTFOLIO_IDS[0]}, pro-rata funding, net-pessimistic costs, "
            "full period"
        ),
        "per_sleeve": rows,
    }


def _credit_ceiling(decompositions: Sequence[JsonValue], settings: Settings) -> JsonValue:
    """How large the diversification credit could be at BEST, and what that implies.

    Under pro-rata funding the credit is ``gamma * sigma_p^2 (1 - beta_ip)``, so a
    beta of zero -- the most any real asset can hope for against an equity core --
    caps it at ``gamma * sigma_p^2``. That ceiling is a property of the base
    portfolio alone: it does not depend on which sleeve is proposed, it cannot be
    improved by finding a better sleeve, and it is the single number that decides
    whether the portfolio-level view can rescue anything the standalone chain
    dismissed. It is computed here from the cash calibration control, whose beta to
    the portfolio is zero by construction, so the arithmetic is checkable against
    the reported volatility rather than asserted.
    """
    rows = [
        item
        for item in decompositions
        if isinstance(item, Mapping)
        and item.get("funding_leg") == "pro_rata"
        and item.get("cost_basis") == "net-pessimistic"
        and item.get("base_portfolio") == BASE_PORTFOLIO_IDS[0]
    ]
    out: list[JsonValue] = []
    for item in rows:
        if item.get("sleeve") != "cash_control":
            continue
        volatility = float(str(item.get("portfolio_annualised_volatility_percent"))) / 100.0
        growth_ceiling = 100.0 * volatility**2
        out.append(
            {
                "base_portfolio": BASE_PORTFOLIO_IDS[0],
                "portfolio_annualised_volatility_percent": 100.0 * volatility,
                "maximum_credit_growth_basis_pp_per_year_per_unit_weight": growth_ceiling,
                "maximum_credit_growth_basis_at_the_reference_weight_pp_per_year": (
                    settings.reference_weight * growth_ceiling
                ),
                "maximum_credit_crra_basis_pp_per_year_per_unit_weight": (
                    settings.report_gamma * growth_ceiling
                ),
                "deciding_basis": settings.deciding_basis,
                "materiality_threshold_annual_percent": settings.materiality,
                "reading": (
                    f"On the growth basis the diversification credit cannot exceed "
                    f"{settings.reference_weight * growth_ceiling:.3f} pp/yr at the "
                    f"frozen {settings.reference_weight:.0%} weight, against a frozen "
                    f"materiality threshold of {settings.materiality:.2f} pp/yr. That "
                    "ceiling is reached only by an asset with ZERO beta to the equity "
                    "core, and it is a fact about the base portfolio's variance rather "
                    "than about any sleeve: no sleeve can be found that beats it."
                ),
            }
        )
    return out


def _calibration_control(
    marginals: Sequence[MarginalResult], settings: Settings
) -> JsonValue:
    """Evaluate the frozen machine check on BOTH readings, and name which decides.

    The frozen hostile test reads: "Cash added to an equity core and funded from US
    equity MUST show a materially negative marginal certainty equivalent. If it
    does not, the machinery is wrong and no other figure may be read."

    That sentence admits two readings and both are reported, because a rule that
    only fires on the reading its author preferred after seeing the answer is not a
    rule.

    * On the CERTAINTY-EQUIVALENT reading it was written for, the check can fail
      for a reason that has nothing to do with the machinery: a CRRA investor at
      gamma = 3 holding a portfolio that is 100% equity genuinely prefers a tenth
      of it in cash, because the utility function rewards the risk reduction more
      than it penalises the lost premium. That is a property of the METRIC.
    * On the GEOMETRIC GROWTH reading, gamma = 1, no preference term exists and
      cash must lose. That is the reading that actually tests the machinery, and it
      is the one this module treats as decisive.

    This control is what CALIBRATED the choice. It supplies zero alpha and zero
    diversification credit by construction, so anything it scores is measurement
    error in the metric rather than value in the sleeve, and the size of what it
    scores is the size of the reward the metric hands out for de-risking. Decision
    record 0008 turned that reading from this module's own preference into the
    repository's rule.

    The resolution is outcome-neutral: it cannot promote any sleeve, because the
    control is excluded from the Holm family and its own status is decided by the
    same clauses as everything else.
    """
    rows = [
        item
        for item in marginals
        if item.sleeve_id == "cash_control"
        and item.basis is CostBasis.NET_PESSIMISTIC
        and item.base_portfolio == BASE_PORTFOLIO_IDS[0]
    ]
    by_leg = {item.funding_leg: item for item in rows}
    frozen_reading = by_leg.get("named_leg")
    growth_values = [item.marginal_growth_percent for item in rows]
    machinery_ok = bool(growth_values) and all(value < 0.0 for value in growth_values)
    return {
        "deciding_basis_of_this_specification": settings.deciding_basis,
        "de_risking_reward_measured_by_this_control_pp_per_year": {
            leg: item.marginal_crra_percent - item.marginal_growth_percent
            for leg, item in sorted(by_leg.items())
        },
        "why_this_control_calibrates_the_metric": (
            "Cash funded out of the equity core supplies NO alpha and NO "
            "diversification credit by construction. Any positive score it records "
            "is therefore a property of the metric and not of the sleeve, and its "
            "size is the size of the reward that metric pays for de-risking. Every "
            "certainty-equivalent figure in this experiment contains a component of "
            "that kind, which is why decision record 0008 forbids the certainty "
            "equivalent from deciding a threshold on its own."
        ),
        "frozen_text": (
            "Cash added to an equity core and funded from US equity MUST show a "
            "materially negative marginal certainty equivalent. If it does not, the "
            "machinery is wrong and no other figure may be read."
        ),
        "readings": {
            "certainty_equivalent_gamma_3": {
                "per_funding_leg_pp_per_year": {
                    leg: item.marginal_percent for leg, item in sorted(by_leg.items())
                },
                "check_passes": (
                    frozen_reading is not None and frozen_reading.marginal_percent < 0.0
                ),
                "why_it_can_fail_without_the_machinery_being_wrong": (
                    "A CRRA investor at gamma = 3 holding a 100% equity portfolio "
                    "genuinely prefers a tenth of it in cash: the exact utility over "
                    "calendar-year returns penalises the realised left tail far more "
                    "than the quadratic approximation does, so de-risking pays. The "
                    "metric therefore CONFOUNDS 'this sleeve adds growth' with 'this "
                    "sleeve reduces risk', which is exactly why the alpha/credit "
                    "decomposition and the growth-basis marginal are reported beside "
                    "every certainty-equivalent figure rather than instead of them."
                ),
            },
            "geometric_growth_gamma_1": {
                "per_funding_leg_pp_per_year": {
                    leg: item.marginal_growth_percent for leg, item in sorted(by_leg.items())
                },
                "check_passes": machinery_ok,
                "what_it_tests": (
                    "With no preference term, cash added to an equity core must lower "
                    "the growth rate. This is the reading that tests the machinery, "
                    "and it is the one treated as decisive."
                ),
            },
        },
        "reading_that_decides": "geometric_growth_gamma_1",
        "machinery_validated": machinery_ok,
        "what_a_reader_who_prefers_the_other_reading_concludes": (
            "That the experiment is void and no figure may be read. That reader "
            "reaches the same decision about every sleeve as this module does, "
            "because every sleeve is rejected on the frozen falsifier either way, so "
            "the choice of reading cannot promote anything."
        ),
    }


def _experiment_status(
    verdicts: JsonValue,
    primary: Mapping[str, MarginalResult],
    control_check: JsonValue,
    settings: Settings,
) -> tuple[ResultStatus, str]:
    rows = verdicts.get("per_sleeve") if isinstance(verdicts, Mapping) else None
    statuses: list[tuple[str, str]] = []
    if isinstance(rows, Sequence):
        statuses = [
            (str(item.get("sleeve")), str(item.get("status")))
            for item in rows
            if isinstance(item, Mapping) and not bool(item.get("is_calibration_control"))
        ]
    survivors = [name for name, value in statuses if value == ResultStatus.EXPLORATORY.value]
    validated = isinstance(control_check, Mapping) and bool(
        control_check.get("machinery_validated")
    )
    control = primary.get("cash_control")
    if not validated:
        return (
            ResultStatus.UNRESOLVED,
            (
                "MACHINE CHECK FAILED ON THE READING THAT DECIDES. Cash added to an "
                "equity core did not lower the portfolio's geometric growth rate, "
                "which it must. The machinery is wrong and no other figure in this "
                "experiment may be read."
            ),
        )
    values = [value for _, value in statuses]
    rejected = values.count(ResultStatus.REJECTED.value)
    unresolved = values.count(ResultStatus.UNRESOLVED.value)
    if survivors:
        status = ResultStatus.EXPLORATORY
        headline = f"{len(survivors)} of {len(statuses)} sleeves cleared every frozen clause"
    elif unresolved:
        status = ResultStatus.UNRESOLVED
        headline = (
            f"no sleeve cleared every frozen clause; {rejected} rejected and "
            f"{unresolved} unresolved"
        )
    else:
        status = ResultStatus.REJECTED
        headline = f"all {len(statuses)} sleeves were rejected by the frozen falsifier"
    control_note = (
        f"The cash calibration control loses {control.marginal_growth_percent:+.3f} pp/yr "
        f"of growth, as the machine check requires, while GAINING "
        f"{control.marginal_crra_percent:+.3f} pp/yr of certainty equivalent at "
        f"gamma={settings.report_gamma:g} -- a de-risking reward of "
        f"{control.marginal_crra_percent - control.marginal_growth_percent:+.3f} pp/yr "
        "bought by a sleeve that supplies no alpha and no credit at all"
        if control is not None
        else "The cash calibration control was not computed"
    )
    summary = (
        "Public-series evaluation of MARGINAL sleeve value inside a portfolio, "
        "decomposed into a standalone alpha term and a diversification credit. "
        f"Every threshold and every falsifier clause is decided on the "
        f"{settings.deciding_basis} basis (decision record 0008); the CRRA "
        f"gamma={settings.report_gamma:g} certainty equivalent is reported beside it "
        f"and decides nothing. {headline}. {control_note}. Gold was not tested: no "
        f"research-grade series is reachable. Status: {status.value}."
    )
    return status, summary


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def _estimates(
    primary: Mapping[str, MarginalResult],
    decompositions: Sequence[JsonValue],
    surfaces: Sequence[JsonValue],
    settings: Settings,
    sleeves: Mapping[str, Sleeve],
) -> tuple[Estimate, ...]:
    out: list[Estimate] = []
    for sleeve_id, result in sorted(primary.items()):
        label = "PROXY " if sleeves[sleeve_id].is_proxy else ""
        out.append(
            Estimate(
                name=f"{label}{settings.deciding_metric_name}, {sleeve_id}",
                value=result.marginal_percent,
                units="percentage points per year",
                interval=(result.lower_95, result.upper_95),
                interval_method=(
                    f"paired stationary block bootstrap, two-sided 95%, mean block "
                    f"{result.block_length:.0f}m, {settings.resamples} resamples, "
                    "resampling the joint monthly panel so the pairing is preserved"
                ),
                cost_basis=CostBasis.NET_PESSIMISTIC,
                n_obs=result.observations,
                notes=(
                    f"weight {result.reference_weight:.2f} funded pro rata from "
                    f"{result.base_portfolio}, deciding basis {settings.deciding_basis} "
                    f"(gamma={settings.decision_gamma:g}); the CRRA "
                    f"gamma={settings.report_gamma:g} companion is "
                    f"{result.marginal_crra_percent:+.3f} and the geometric-growth "
                    f"companion {result.marginal_growth_percent:+.3f} pp/yr; MDE at 80% "
                    f"power {result.mde_bootstrap:.3f} pp/yr"
                    + (
                        f"; PROXY for {sleeves[sleeve_id].proxy_for}"
                        if sleeves[sleeve_id].is_proxy
                        else ""
                    )
                ),
            )
        )
    for item in decompositions:
        if not isinstance(item, Mapping):
            continue
        if (
            item.get("funding_leg") != "pro_rata"
            or item.get("cost_basis") != "net-pessimistic"
            or item.get("base_portfolio") != BASE_PORTFOLIO_IDS[0]
        ):
            continue
        growth = item.get("growth_gamma_1")
        if not isinstance(growth, Mapping):
            continue
        sleeve_id = str(item.get("sleeve"))
        bounds = item.get("credit_at_the_correlation_interval_bounds_pp_per_year")
        interval: tuple[float, float] | None = None
        if isinstance(bounds, Sequence) and len(bounds) == 2:
            low, high = bounds[0], bounds[1]
            if isinstance(low, int | float) and isinstance(high, int | float):
                interval = (float(low), float(high))
        out.append(
            Estimate(
                name=f"diversification credit, {sleeve_id}",
                value=float(
                    str(growth.get("diversification_credit_pp_per_year_per_unit_weight"))
                ),
                units="percentage points per year per unit of sleeve weight",
                interval=interval,
                interval_method=(
                    "credit re-evaluated at the two ends of the correlation's paired "
                    "block-bootstrap 95% interval, volatilities held at their point "
                    "estimates"
                )
                if interval is not None
                else "",
                cost_basis=CostBasis.NET_PESSIMISTIC,
                uncertainty_unavailable_reason=(
                    "" if interval is not None else "no correlation interval was computed"
                ),
                notes=(
                    f"alpha term "
                    f"{float(str(growth.get('alpha_term_pp_per_year_per_unit_weight'))):+.3f}; "
                    f"beta to the portfolio {item.get('beta_sleeve_to_portfolio')}"
                ),
            )
        )
    for item in surfaces:
        if not isinstance(item, Mapping):
            continue
        if (
            item.get("funding_leg") != "pro_rata"
            or item.get("cost_basis") != "net-pessimistic"
            or item.get("base_portfolio") != BASE_PORTFOLIO_IDS[0]
        ):
            continue
        out.append(
            Estimate(
                name=f"constrained optimal weight, {item.get('sleeve')}",
                value=float(str(item.get("optimal_weight"))),
                units="fraction of portfolio value",
                cost_basis=CostBasis.NET_PESSIMISTIC,
                uncertainty_unavailable_reason=(
                    "an in-sample selected maximum; its interval is reported separately "
                    "by re-selecting the weight inside every bootstrap replicate, which "
                    "is the only version that carries the selection effect"
                ),
                notes=(
                    f"gain {float(str(item.get(_GAIN_AT_OPTIMUM_KEY))):+.3f} pp/yr; "
                    f"plateau width {float(str(item.get('plateau_width'))):.3f}"
                ),
            )
        )
    return tuple(out)


def _caveats(settings: Settings) -> tuple[str, ...]:
    basis = (
        "EVERY THRESHOLD AND EVERY FALSIFIER CLAUSE HERE IS DECIDED ON THE GEOMETRIC "
        "GROWTH RATE, gamma = 1, and the CRRA certainty equivalent is reported beside "
        "it and decides nothing. Decision record 0008 records why: the exact CRRA "
        "utility over only 35 calendar-year returns REWARDS DE-RISKING, and this "
        "experiment's own cash control measures the reward. Cash funded out of the "
        "equity core supplies zero alpha and zero diversification credit by "
        "construction, yet scores positively at gamma = 3 while losing growth. Any "
        "investor obtains that component free by holding less equity, so a sleeve "
        "scoring on it has been paid for something it did not supply."
        if settings.decides_on_growth
        else (
            f"EVERY THRESHOLD AND EVERY FALSIFIER CLAUSE HERE IS DECIDED ON THE CRRA "
            f"CERTAINTY EQUIVALENT AT gamma = {settings.decision_gamma:g}. Decision "
            "record 0008 forbids that for any specification frozen after it, because "
            "the exact CRRA utility over 35 calendar-year returns rewards de-risking: "
            "this experiment's own cash control, which supplies zero alpha and zero "
            "diversification credit by construction, scores positively on it while "
            "losing growth. The geometric-growth figure is reported beside every "
            "certainty-equivalent figure in this result and is the one to read."
        )
    )
    return (
        basis,
        "THIS IS A PUBLIC-SERIES EVALUATION, NOT AN INVESTABLE BACKTEST. Ken French's "
        "research portfolios and factor files are paper portfolios rebuilt from the "
        "current CRSP or Bloomberg vintage on every release, with no trading cost, no "
        "borrow, no capacity limit and no rebalancing friction inside the portfolio. "
        "The fee tiers charged here are this repository's assumptions about an "
        "accessible implementation, not any provider's disclosure.",
        "GOLD WAS NOT TESTED. It is one of only two candidate assets with a plausibly "
        "low equity beta and no research-grade series is reachable; decision record "
        "0002 forbids substituting a free price feed. Its absence biases this "
        "experiment toward finding no diversification credit anywhere.",
        "The long-duration Treasury sleeve is a MODELLED PROXY reconstructed from FRED "
        "GS10 by a duration-and-convexity approximation. It has no total-return "
        "contract, no coupon reinvestment convention and no transaction costs. It is a "
        "proxy for the long-duration Treasury sleeve this repository cannot source, and "
        "whatever status it carries is a statement about the model, never about a real "
        "Treasury sleeve. The frozen falsifier orders its rejection clauses ahead of "
        "clause (u5), so the proxy reaches `unresolved` only when no rejection clause "
        "fires; that ordering is applied as frozen rather than reinterpreted.",
        "FINDING SURFACED BY THIS EXPERIMENT, not by its data, and SINCE REPAIRED: the "
        "par-bond convexity helper in exp_004 dropped a factor of two in the second "
        "derivative and therefore returned half the true convexity, 39.4490 against "
        "78.8979 for a ten-year 4% par bond, behind a unit test that asserted the "
        "implementation's own output. This module carried the corrected form and a test "
        "that differentiates the exact price function instead. exp_004 has since been "
        "re-run against its unchanged frozen specification: exactly one figure moved, "
        "its declared research-grade-false bond-leg robustness arm, by -0.000585 pp/yr, "
        "and its headline, all five falsifier clauses and its status are unmoved.",
        "The trend sleeve is AQR's published vendor series, maintained by a firm that "
        "sells the strategy, whose fee and transaction-cost basis exp_004 established "
        "to be UNSTATED in the archived workbook. Its figures here are NOT comparable "
        "with exp_004's headline: that experiment measured a 15% sleeve against a "
        "RISK-MATCHED CASH comparator, and this one measures a 10% sleeve against the "
        "same portfolio without it. The two answer different questions.",
        "The constrained optimal weight is chosen from the same sample it is evaluated "
        "on. Its naive gain is a selected maximum and is positive by construction on a "
        "noisy surface. Only the interval that re-selects the weight inside every "
        "bootstrap replicate carries that selection effect, and the gap between the two "
        "is reported rather than resolved.",
        "The diversification credit is a difference of two covariances estimated from "
        "420 months. Its sensitivity to the correlation is reported beside it: a credit "
        "that moves by more than itself when the correlation moves by 0.10 is not a "
        "finding, and several of these do.",
        "Every sleeve is measured against the same base portfolio over the same months, "
        "and eight of the ten share the global equity factor. The Holm correction is "
        "valid under that dependence but the family of ten is a LOWER bound on the "
        "correction the whole search requires; it counts neither the funding legs, the "
        "base portfolios, the cost columns, the eras, nor the specifications this "
        "repository froze before this one, which the append-only ledger counts.",
        "Long-short sleeves are made funded by adding cash to a self-financing factor "
        "return. That is the only way to compare them with a long-only holding, and it "
        "understates their cost: the Ken French factor files contain no shorting cost, "
        "no borrow and no capacity limit at all.",
    )


def _frames(
    marginals: Sequence[MarginalResult],
    decompositions: Sequence[JsonValue],
    surfaces: Sequence[JsonValue],
) -> dict[str, pd.DataFrame]:
    def flat(rows: Sequence[JsonValue]) -> list[dict[str, JsonValue]]:
        return [dict(item) for item in rows if isinstance(item, Mapping)]

    return {
        "marginal_results": pd.DataFrame([item.to_json() for item in marginals]),
        "decompositions": pd.json_normalize(flat(decompositions)),
        "weight_surfaces": pd.json_normalize(flat(surfaces)),
    }


def build_registry() -> ExperimentRegistry:
    """A registry holding exactly this experiment."""
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return _workspace_root() / "experiments" / "exp_010_marginal_sleeve_value.yaml"


def _manifest_hashes(specification: Specification) -> tuple[str, ...]:
    parameters = specification.parameters
    if not isinstance(parameters, Mapping):
        return ()
    pin = parameters.get("source_pin")
    if not isinstance(pin, Mapping):
        return ()
    hashes: list[str] = []
    for group in pin.values():
        entries = group if isinstance(group, Sequence) and not isinstance(group, str) else [group]
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            location = entry.get("committed_manifest")
            if isinstance(location, str):
                path = _workspace_root() / location
                if path.is_file():
                    hashes.append(read_manifest(path).sha256_manifest())
    return tuple(hashes)


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    lines = [result.summary, ""]
    verdicts = result.diagnostics.get("verdicts")
    decompositions = result.diagnostics.get("decompositions")
    credits: dict[str, tuple[float, float, float]] = {}
    if isinstance(decompositions, Sequence):
        for item in decompositions:
            if not isinstance(item, Mapping):
                continue
            if (
                item.get("funding_leg") != "pro_rata"
                or item.get("cost_basis") != "net-pessimistic"
                or item.get("base_portfolio") != BASE_PORTFOLIO_IDS[0]
            ):
                continue
            growth = item.get("growth_gamma_1")
            if not isinstance(growth, Mapping):
                continue
            credits[str(item.get("sleeve"))] = (
                float(str(growth.get("alpha_term_pp_per_year_per_unit_weight"))),
                float(str(growth.get("diversification_credit_pp_per_year_per_unit_weight"))),
                float(str(item.get("beta_sleeve_to_portfolio"))),
            )
    basis = "?"
    if isinstance(verdicts, Mapping):
        basis = str(verdicts.get("deciding_basis", "?"))
    lines.append(f"deciding basis: {basis}   (marg is on that basis)")
    lines.append(
        f"{'sleeve':<30}{'marg':>8}{'growth':>8}{'CE':>8}{'95% low':>9}{'95% hi':>9}"
        f"{'MDE':>8}{'alpha':>9}{'credit':>9}{'beta':>7}{'holm p':>9}  status"
    )
    if isinstance(verdicts, Mapping):
        rows = verdicts.get("per_sleeve")
        if isinstance(rows, Sequence):
            for item in rows:
                if not isinstance(item, Mapping):
                    continue
                name = str(item.get("sleeve"))
                alpha, credit, beta = credits.get(name, (math.nan, math.nan, math.nan))
                holm_p = item.get("holm_adjusted_p")
                interval = item.get("two_sided_95")
                low = high = math.nan
                if isinstance(interval, Sequence) and len(interval) == 2:
                    low, high = float(str(interval[0])), float(str(interval[1]))
                lines.append(
                    f"{name[:29]:<30}"
                    f"{float(str(item.get('marginal_pp_per_year'))):>8.3f}"
                    f"{float(str(item.get('marginal_geometric_growth_pp_per_year'))):>8.3f}"
                    f"{float(str(item.get('marginal_certainty_equivalent_pp_per_year'))):>8.3f}"
                    f"{low:>9.3f}{high:>9.3f}"
                    f"{float(str(item.get('minimum_detectable_effect'))):>8.3f}"
                    f"{alpha:>9.3f}{credit:>9.3f}{beta:>7.2f}"
                    f"{float(str(holm_p)) if holm_p is not None else math.nan:>9.4f}"
                    f"  {item.get('status')}"
                )
    lines.append("")
    scorecard = result.diagnostics.get("predeclared_prediction_scorecard")
    if isinstance(scorecard, Mapping):
        lines.append(
            f"predeclared prediction held for "
            f"{scorecard.get('sleeves_matching_the_prediction')} of "
            f"{scorecard.get('sleeves_scored')} sleeves"
        )
    lines.append("")
    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 010 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_010_marginal_sleeve_value",
        description=(
            "Measure the marginal contribution of each candidate sleeve to a realistic "
            "portfolio's certainty equivalent, split into a standalone alpha term and a "
            "diversification credit, writing a ledger entry for the attempt."
        ),
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument(
        "--view-results",
        action="store_true",
        help=(
            "print the computed numbers AND append a results_viewed entry to the "
            "ledger. Looking is an event with consequences, so it is recorded."
        ),
    )
    arguments = parser.parse_args(argv)

    specification = load_specification(arguments.specification)
    ledger = Ledger(arguments.ledger)
    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=_manifest_hashes(specification),
    )

    print(f"run_id       {outcome.run_id}")
    print(f"spec_hash    {outcome.spec_hash}")
    print(f"status       {outcome.status.value}")
    print(f"result       {outcome.result.status.value if outcome.result else 'none'}")
    print(f"git_commit   {outcome.git_state.commit} (dirty={outcome.git_state.dirty})")
    for record in outcome.artifacts:
        print(f"artifact     {record.path}  {record.sha256}  {record.size_bytes}B")

    if arguments.view_results:
        print()
        print(_render_console_report(outcome))
        ledger.record_results_viewed(
            outcome.run_id,
            origin=Origin(arguments.origin),
            notes=(
                "numbers printed to the console by the --view-results flag of "
                "exp_010_marginal_sleeve_value"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
