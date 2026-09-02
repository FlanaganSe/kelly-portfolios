"""What leverage the investor is already taking, and what leverage the objective wants.

An investor who says *"I am okay with leverage but it absolutely must be with purpose
and must understand market conditions"* has stated two requirements. This module makes
both computable and refuses to answer either with a point estimate.

Five separable pieces.

**1. Exposure arithmetic** (:func:`portfolio_exposure`). A stacked wrapper delivers more
notional than the capital spent on it, so a portfolio holding one has a gross notional
above 1.0 whether or not its holder has computed it. The arithmetic is a sum, it needs no
forecast, and it is the only part of this module that is not a scenario. It is deliberately
kept separate from every growth calculation below so that a reader can check it against
their own holdings without accepting any of the modelling.

**2. Where the leverage recommendation changes sign** (:func:`premium_for_leverage`,
:func:`kinked_growth_optimal_leverage`). The much-repeated ``L* = (mu - r) / sigma**2``
inverts to ``mu - r = L sigma**2``, so the premium at which an exposure of exactly 1.0 is
growth-optimal is ``sigma**2`` — the *same quantity* that
:mod:`portfolio_edge.studies.overlay_growth` calls the funding-rule gap ``a_p -
sigma_p**2``. Below that premium the growth objective wants **less** than a fully invested
portfolio and a levered one is overbetting; above it, more. The sign of the whole
recommendation therefore turns on a forecast, and :func:`kinked_growth_optimal_leverage`
adds the two frictions that move it: a borrow spread charged only above 1.0, and a fee
charged on notional. Both push the optimum down, and between the two branches sits a flat
region in which the optimum is exactly 1.0 — a *kink*, not a point, so a range of premium
forecasts all imply "hold what you have".

**3. Two assets, financed separately** (:func:`growth_optimal_pair`). A stacked fund is not
levered equity. With ``Sigma`` the 2x2 covariance of the base and the diversifier and
``mu_net`` their net-of-cost excess returns, the growth-optimal notional pair is
``Sigma^-1 mu_net``, and the diversifier leg is close to ``mu_d / sigma_d**2`` whenever the
correlation is near zero. The two legs answer separately, which is exactly why gross
notional cannot score the portfolio: 1.3x gross as 1.0 equity plus 0.3 trend and 1.3x gross
as 1.3 equity are different portfolios with different optima and different drawdowns.

**4. Sizing by drawdown instead** (:func:`notional_for_drawdown`,
:func:`gross_notional_ladder`). If the growth optimum is not identifiable — and §2's
sensitivity is how you find out whether it is — the operational question is the largest
exposure whose measured drawdown the investor would have sat through. That inverts a
measured ladder rather than a model, so it inherits one sample's limitations and no
forecast at all.

**5. Conditioning on market conditions** (:func:`volatility_targeted_leverage`,
:func:`apply_leverage`, :func:`leverage_turnover`). Volatility is far more forecastable
than return, which is the whole case for scaling exposure by a trailing volatility
estimate. The rule here is executable: the estimate ends at ``t-1``, the leverage is capped
and floored, the borrow spread is charged on the financed part, and every change in
leverage is charged a round-trip trading cost inside the path. A vol-targeting result
reported gross of turnover is not a result.

**What this module is not.** It reads no market data — the caller supplies arrays — and it
recommends nothing. Every function taking an ``excess_return`` takes a forecast, and
``docs/decisions/0004-no-sleeve-promoted.md``'s non-promotion and zero-leverage default for
*recommendations* are untouched by anything computed here;
``docs/decisions/0009-blocks-lifted-and-closures-rescoped.md`` clause 3 unblocks the
measurement alone.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary

__all__ = [
    "EQUITY_KINDS",
    "MONTHS_PER_YEAR",
    "ExposureSummary",
    "FinancingLeg",
    "FinancingStack",
    "GrossNotionalRung",
    "Holding",
    "HorizonOutcome",
    "LeverageInterval",
    "LeveragePathResult",
    "NotionalLeg",
    "PairOptimum",
    "apply_leverage",
    "financing_stack",
    "gross_notional_ladder",
    "growth_optimal_pair",
    "horizon_outcomes",
    "kinked_growth_optimal_leverage",
    "leverage_confidence_interval",
    "leverage_turnover",
    "notional_for_drawdown",
    "portfolio_exposure",
    "premium_for_leverage",
    "volatility_targeted_leverage",
]

MONTHS_PER_YEAR: Final = 12

FloatArray = NDArray[np.float64]

#: Notional kinds that are equity beta. Membership is a judgement about what the exposure
#: *is*, and it is held in one place so that a caller cannot quietly reclassify a leg to
#: make an equity share look smaller. Global and US equity are both equity beta for this
#: purpose; whether they are the same *benchmark* is a separate question this module does
#: not answer (``docs/research/capital-efficiency-and-breadth.md``, "Global versus US").
EQUITY_KINDS: Final[frozenset[str]] = frozenset(
    {"us-equity", "global-equity", "equity"}
)


# --------------------------------------------------------------------------------
# 1. Exposure arithmetic. No forecast anywhere in this section.
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NotionalLeg:
    """One exposure a fund delivers, per dollar of capital placed in that fund.

    ``per_dollar_of_capital`` is read from a holdings filing, not from marketing copy:
    1.072 means 107.2% of net assets. It is a gross notional, so it says what the position
    is, never that the strategy inside delivers anything.
    """

    kind: str
    per_dollar_of_capital: float


@dataclass(frozen=True, slots=True)
class Holding:
    """One line of a portfolio: a share of capital and what that share delivers."""

    label: str
    weight: float
    legs: tuple[NotionalLeg, ...]


@dataclass(frozen=True, slots=True)
class ExposureSummary:
    """What a portfolio actually holds, per dollar of capital.

    ``financed_notional`` is ``gross_notional - 1``: the notional the investor did not pay
    for, which is the honest definition of the leverage being taken. It is zero for any
    fully invested unlevered portfolio and negative for one holding cash.
    """

    capital_deployed: float
    cash_weight: float
    by_kind: Mapping[str, float]
    gross_notional: float
    equity_notional: float
    non_equity_notional: float
    financed_notional: float
    effective_equity_share: float


def portfolio_exposure(
    holdings: Sequence[Holding], *, equity_kinds: frozenset[str] = EQUITY_KINDS
) -> ExposureSummary:
    """Sum a portfolio's notional legs, per dollar of capital.

    ``effective_equity_share`` is the equity notional expressed against a nominal
    100%-equity portfolio, so 1.0216 means the portfolio carries 2.16% more equity beta
    than an all-equity one — not that it is 102.16% invested.

    Raises if the weights exceed one dollar of capital: a portfolio cannot deploy capital
    it does not have, and the leverage in a stacked fund arrives as notional rather than as
    a weight above 1.0. A shortfall is treated as cash and reported.
    """
    weights = [holding.weight for holding in holdings]
    if any(weight < 0.0 for weight in weights):
        raise ValueError(
            "a holding weight cannot be negative; short positions are not modelled here"
        )
    deployed = float(sum(weights))
    if deployed > 1.0 + 1e-12:
        raise ValueError(
            f"holdings deploy {deployed!r} of capital. Weights are shares of capital, and "
            "leverage enters through a leg's notional per dollar, never through a weight "
            "above one"
        )
    by_kind: dict[str, float] = {}
    for holding in holdings:
        for leg in holding.legs:
            by_kind[leg.kind] = (
                by_kind.get(leg.kind, 0.0) + holding.weight * leg.per_dollar_of_capital
            )
    gross = float(sum(by_kind.values()))
    equity = float(sum(value for kind, value in by_kind.items() if kind in equity_kinds))
    return ExposureSummary(
        capital_deployed=deployed,
        cash_weight=1.0 - deployed,
        by_kind=dict(sorted(by_kind.items())),
        gross_notional=gross,
        equity_notional=equity,
        non_equity_notional=gross - equity,
        financed_notional=gross - 1.0,
        effective_equity_share=equity,
    )


# --------------------------------------------------------------------------------
# 2. Where the leverage recommendation changes sign
# --------------------------------------------------------------------------------


def premium_for_leverage(*, leverage: float, volatility: float) -> float:
    """``mu - r = L sigma**2``: the arithmetic excess return at which ``L`` is optimal.

    The inverse of :func:`portfolio_edge.core.kelly.kelly_leverage`, and the honest
    direction to read it in: rather than assert a premium and derive an exposure, state the
    premium the exposure you hold is implicitly forecasting. At ``L = 1`` it returns
    ``sigma**2``, which is the same quantity as
    :mod:`portfolio_edge.studies.overlay_growth`'s funding-rule gap ``a_p - sigma_p**2``
    written as a break-even rather than as a difference.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    if leverage < 0.0:
        raise ValueError(f"leverage cannot be negative, got {leverage}")
    return leverage * volatility**2


def kinked_growth_optimal_leverage(
    *,
    excess_return: float,
    volatility: float,
    borrow_spread: float = 0.0,
    cost_on_notional: float = 0.0,
) -> float:
    """Growth-optimal exposure when borrowing costs more than lending.

    Maximises :func:`portfolio_edge.core.kelly.kinked_growth_rate` with a linear cost
    ``C(L) = c L``. The objective is concave and piecewise quadratic with a kink at
    ``L = 1``, so the optimum is one of three things:

    * ``(mu - r - c) / sigma**2`` if that is at most 1 — the lending branch, where no
      spread is paid;
    * ``(mu - r - s - c) / sigma**2`` if that is at least 1 — the borrowing branch;
    * exactly ``1.0`` otherwise, at the kink.

    The third case is the one worth naming: a *range* of premium forecasts, of width
    ``s`` in excess-return units, all imply holding exactly what you have. A spread of
    60 bp on a 15.9%-volatility base makes that range 60 bp wide in the premium, which is
    a quarter of the whole distance between "hold nothing extra" and "hold a third more".

    Returns a non-negative exposure; a premium below the cost gives 0.0 rather than a short.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    if borrow_spread < 0.0:
        raise ValueError(f"borrow_spread cannot be negative, got {borrow_spread}")
    variance = volatility**2
    lending = (excess_return - cost_on_notional) / variance
    borrowing = (excess_return - cost_on_notional - borrow_spread) / variance
    if lending <= 1.0:
        return max(lending, 0.0)
    if borrowing >= 1.0:
        return borrowing
    return 1.0


@dataclass(frozen=True, slots=True)
class LeverageInterval:
    """A sampling interval on the plug-in growth-optimal exposure.

    ``point`` is the plug-in ``(muhat - r) / sigma**2``. ``lower`` and ``upper`` come from
    ``SE(Lhat*) = 1 / (sigma sqrt(T))`` with ``sigma`` treated as known, which is the
    *narrow* case: estimating ``sigma`` too widens it and also biases the plug-in upward by
    :func:`portfolio_edge.studies.equity_share.inverse_variance_bias_factor`.
    """

    point: float
    standard_error: float
    lower: float
    upper: float
    years: float
    confidence_level: float


def leverage_confidence_interval(
    *, excess_return: float, volatility: float, years: float, confidence_level: float = 0.95
) -> LeverageInterval:
    """Interval on ``Lhat*`` from the sampling error in the mean alone.

    This is the quantity that decides whether a leverage recommendation is identifiable.
    ``SE(Lhat*) = 1 / (sigma sqrt(T))`` contains no ``mu``: the precision of the exposure
    estimate depends only on the volatility and the **calendar span** of the sample, so
    sampling more finely inside a window buys nothing (Merton 1980). An interval that spans
    1.0 means the data cannot say whether to lever at all.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    if years <= 0.0:
        raise ValueError(f"years must be positive, got {years}")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(f"confidence_level must lie in (0, 1), got {confidence_level}")
    # Two-sided normal quantile without a scipy import: the study modules keep scipy in the
    # table layer. math.erfinv does not exist, so use the inverse-erf identity via erfc is
    # not available either; a small rational approximation would be a second definition of
    # a standard quantile. Import scipy locally instead, which costs nothing at call time.
    from scipy.stats import norm

    z = float(norm.ppf(0.5 + confidence_level / 2.0))
    point = excess_return / volatility**2
    standard_error = 1.0 / (volatility * math.sqrt(years))
    return LeverageInterval(
        point=point,
        standard_error=standard_error,
        lower=point - z * standard_error,
        upper=point + z * standard_error,
        years=years,
        confidence_level=confidence_level,
    )


# --------------------------------------------------------------------------------
# 3. Two assets, financed separately
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PairOptimum:
    """The growth-optimal notional in each of two legs, and the gross that implies."""

    base_notional: float
    diversifier_notional: float
    gross_notional: float
    peak_growth_over_cash: float


def growth_optimal_pair(
    *,
    base_excess_return: float,
    base_volatility: float,
    diversifier_excess_return: float,
    diversifier_volatility: float,
    correlation: float,
) -> PairOptimum:
    """``Sigma^-1 mu``: growth-optimal notional in each leg, neither clipped.

    Both excess returns must already be **net of everything charged on that leg's
    notional** — fee, financing spread, roll — because the objective cannot tell a cost
    from a lower premium and the caller must not be able to forget one. Both are forecasts.

    Nothing is clipped and nothing is capped: the point of this function is to show how far
    above any feasible exposure the unconstrained optimum sits, which is
    ``docs/research/capital-efficiency-and-breadth.md``'s finding that "feasible exposure is
    set by drawdown, liquidity, withdrawal, and holdability constraints before an estimated
    growth optimum binds."
    """
    if base_volatility <= 0.0 or diversifier_volatility <= 0.0:
        raise ValueError("both volatilities must be positive")
    if not -1.0 < correlation < 1.0:
        raise ValueError(f"correlation must lie strictly in (-1, 1), got {correlation}")
    covariance = correlation * base_volatility * diversifier_volatility
    sigma = np.array(
        [
            [base_volatility**2, covariance],
            [covariance, diversifier_volatility**2],
        ],
        dtype=np.float64,
    )
    mu = np.array([base_excess_return, diversifier_excess_return], dtype=np.float64)
    weights = np.linalg.solve(sigma, mu)
    return PairOptimum(
        base_notional=float(weights[0]),
        diversifier_notional=float(weights[1]),
        gross_notional=float(abs(weights[0]) + abs(weights[1])),
        peak_growth_over_cash=float(0.5 * mu @ weights),
    )


# --------------------------------------------------------------------------------
# 4. Sizing by drawdown instead of by an estimated optimum
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GrossNotionalRung:
    """One rung of the gross-notional ladder, measured on one supplied path."""

    base_notional: float
    diversifier_notional: float
    gross_notional: float
    geometric_return: float
    volatility: float
    sharpe: float
    max_drawdown: float
    months_under_water: int


def gross_notional_ladder(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    cash: FloatArray,
    *,
    rungs: Sequence[tuple[float, float]],
    base_cost: float = 0.0,
    diversifier_cost: float = 0.0,
    borrow_spread: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> tuple[GrossNotionalRung, ...]:
    """Measure a two-leg financed portfolio at each ``(base, diversifier)`` notional pair.

    Unlike :func:`portfolio_edge.studies.overlay_stress.drawdown_ladder`, which holds the
    base at exactly 1.0 and varies the overlay, this varies both — which is what is needed
    to answer whether 1.3x gross as equity and 1.3x gross as equity-plus-trend are the same
    risk. They are not, and the whole point of the ladder is that the reader can see it.

    Costs are charged on each leg's own notional and the borrow spread on gross notional
    above 1.0, all inside the path, so the drawdown and time under water carry them.
    """
    base = np.asarray(base_excess, dtype=np.float64)
    sleeve = np.asarray(diversifier_excess, dtype=np.float64)
    funding = np.asarray(cash, dtype=np.float64)
    if base.shape != sleeve.shape or base.shape != funding.shape:
        raise ValueError("base, diversifier and cash must have the same shape")
    if base.ndim != 1:
        raise ValueError(f"returns must be one-dimensional, got shape {base.shape}")
    out: list[GrossNotionalRung] = []
    for base_notional, diversifier_notional in rungs:
        gross = abs(base_notional) + abs(diversifier_notional)
        charge = (
            base_cost * abs(base_notional)
            + diversifier_cost * abs(diversifier_notional)
            + borrow_spread * max(0.0, gross - 1.0)
        )
        excess = base_notional * base + diversifier_notional * sleeve - charge / periods_per_year
        total = excess + funding
        curve = np.cumprod(1.0 + total)
        summary = drawdown_summary(curve)
        volatility = float(np.std(excess, ddof=1)) * math.sqrt(periods_per_year)
        out.append(
            GrossNotionalRung(
                base_notional=float(base_notional),
                diversifier_notional=float(diversifier_notional),
                gross_notional=float(gross),
                geometric_return=float(curve[-1]) ** (periods_per_year / total.size) - 1.0,
                volatility=volatility,
                sharpe=float(np.mean(excess)) * periods_per_year / volatility,
                max_drawdown=summary.max_drawdown,
                months_under_water=summary.max_time_under_water,
            )
        )
    return tuple(out)


def notional_for_drawdown(
    rungs: Sequence[GrossNotionalRung], *, tolerance: float
) -> float:
    """Largest gross notional on the ladder whose measured drawdown is within ``tolerance``.

    ``tolerance`` is signed and non-positive, matching
    :class:`portfolio_edge.core.drawdown.DrawdownSummary`: ``-0.40`` means "I would have
    sat through a 40% fall". Interpolates linearly in gross notional between the last rung
    inside the tolerance and the first outside it, and returns ``nan`` if even the smallest
    rung breaches it.

    The rungs must be sorted by gross notional and must come from **one window**, because
    maximum drawdown deepens mechanically with sample length. This inverts a measurement,
    not a model, so the answer is only as good as the one path it is measured on.
    """
    if tolerance > 0.0:
        raise ValueError(
            f"tolerance is a signed drawdown and must be non-positive, got {tolerance}"
        )
    if not rungs:
        raise ValueError("rungs must not be empty")
    grosses = [rung.gross_notional for rung in rungs]
    if any(b <= a for a, b in itertools.pairwise(grosses)):
        raise ValueError("rungs must be strictly increasing in gross notional")
    if rungs[0].max_drawdown < tolerance:
        return math.nan
    last_ok = rungs[0]
    for rung in rungs[1:]:
        if rung.max_drawdown < tolerance:
            span = last_ok.max_drawdown - rung.max_drawdown
            if span <= 0.0:
                return last_ok.gross_notional
            share = (last_ok.max_drawdown - tolerance) / span
            return last_ok.gross_notional + share * (rung.gross_notional - last_ok.gross_notional)
        last_ok = rung
    return last_ok.gross_notional


# --------------------------------------------------------------------------------
# 4a. What the leverage costs, in the units the portfolio is measured in
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FinancingLeg:
    """One financed leg of a wrapper and the spread it pays over its collateral rate.

    ``financed_notional`` is per dollar of capital **in the wrapper**, and is the notional
    obtained without paying for it — a physically held index fund finances nothing and
    belongs here at zero. ``spread`` is the annual excess of the leg's implied financing
    rate over the rate the collateral earns, which is the only financing cost that is
    economically real: a futures holder forgoes the cash return on the notional and earns
    it on the collateral instead, so the *level* of rates nets out and only the basis
    remains.

    ``source`` is required and free-form. It exists because none of these spreads is
    disclosed by any fund on the shelf, so every one of them is a number taken from
    somewhere else and the reader is entitled to know from where.
    """

    label: str
    financed_notional: float
    spread: float
    source: str

    @property
    def cost(self) -> float:
        """Annual cost of this leg, per dollar of capital in the wrapper."""
        return self.financed_notional * self.spread


@dataclass(frozen=True, slots=True)
class FinancingStack:
    """The total annual drag of holding a wrapper, per dollar of *portfolio* capital."""

    label: str
    portfolio_weight: float
    fee_on_capital: float
    legs: tuple[FinancingLeg, ...]
    financing_cost_in_wrapper: float
    total_cost_in_wrapper: float
    total_cost_in_portfolio: float
    displaced_fee: float
    incremental_cost_in_portfolio: float
    diversifier_notional_obtained: float
    incremental_cost_per_unit_notional: float


def financing_stack(
    *,
    label: str,
    portfolio_weight: float,
    fee_on_capital: float,
    legs: Sequence[FinancingLeg],
    displaced_fee: float = 0.0,
    diversifier_notional: float = 0.0,
) -> FinancingStack:
    """Add a wrapper's fee and its legs' financing spreads into one portfolio-level drag.

    ``displaced_fee`` is the fee of whatever the wrapper's capital would otherwise have
    been in, so ``incremental_cost_in_portfolio`` is what the *decision* costs rather than
    what the fund costs. Quoting a wrapper's expense ratio without subtracting the
    incumbent's is the same error as quoting a distribution tax drag without subtracting
    the drag of the fund it displaces.

    ``incremental_cost_per_unit_notional`` restates that incremental cost per unit of
    diversifier notional obtained, which is the unit
    :mod:`portfolio_edge.studies.overlay_growth` states its hurdle in. Comparing a cost in
    capital units against a hurdle in notional units is the error
    :mod:`portfolio_edge.studies.wrapper_economics` exists to prevent.
    """
    if not 0.0 <= portfolio_weight <= 1.0:
        raise ValueError(f"portfolio_weight must lie in [0, 1], got {portfolio_weight}")
    if fee_on_capital < 0.0 or displaced_fee < 0.0:
        raise ValueError("fees cannot be negative")
    if diversifier_notional < 0.0:
        raise ValueError(f"diversifier_notional cannot be negative, got {diversifier_notional}")
    financing = float(sum(leg.cost for leg in legs))
    total_in_wrapper = fee_on_capital + financing
    total_in_portfolio = portfolio_weight * total_in_wrapper
    incremental = portfolio_weight * (total_in_wrapper - displaced_fee)
    obtained = portfolio_weight * diversifier_notional
    per_notional = incremental / obtained if obtained > 0.0 else math.nan
    return FinancingStack(
        label=label,
        portfolio_weight=portfolio_weight,
        fee_on_capital=fee_on_capital,
        legs=tuple(legs),
        financing_cost_in_wrapper=financing,
        total_cost_in_wrapper=total_in_wrapper,
        total_cost_in_portfolio=total_in_portfolio,
        displaced_fee=displaced_fee,
        incremental_cost_in_portfolio=incremental,
        diversifier_notional_obtained=obtained,
        incremental_cost_per_unit_notional=per_notional,
    )


# --------------------------------------------------------------------------------
# 5. Conditioning on market conditions
# --------------------------------------------------------------------------------


def volatility_targeted_leverage(
    returns: FloatArray,
    *,
    window: int,
    target: float,
    cap: float,
    floor: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> FloatArray:
    """Leverage path from a **trailing** volatility estimate ending at ``t-1``.

    ``leverage[t] = clip(target / vol(returns[t-window:t]), floor, cap)``, and ``nan``
    until the window exists. The estimate never touches period ``t``, which is the whole
    discipline: scaling by the full-sample or contemporaneous volatility is the easy
    look-ahead in this kind of work and it flatters every statistic that follows.

    This differs from :func:`portfolio_edge.studies.time_series_momentum.volatility_targeted`
    in returning the **leverage path** rather than the scaled series, because the path is
    what a turnover and a trading cost are computed from, and a vol-targeting result
    reported gross of turnover is not a result.
    """
    series = np.asarray(returns, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"returns must be one-dimensional, got shape {series.shape}")
    if window < 2:
        raise ValueError(f"window must be at least 2, got {window}")
    if target <= 0.0:
        raise ValueError(f"target must be positive, got {target}")
    if cap <= 0.0:
        raise ValueError(f"cap must be positive, got {cap}")
    if floor < 0.0 or floor > cap:
        raise ValueError(f"floor must lie in [0, cap], got {floor} against cap {cap}")
    out = np.full(series.size, np.nan, dtype=np.float64)
    for index in range(window, series.size):
        history = series[index - window : index]
        if not np.isfinite(history).all():
            continue
        volatility = float(np.std(history, ddof=1)) * math.sqrt(periods_per_year)
        if volatility <= 0.0:
            continue
        out[index] = min(max(target / volatility, floor), cap)
    return out


def leverage_turnover(
    leverage: FloatArray, *, periods_per_year: int = MONTHS_PER_YEAR
) -> float:
    """Mean absolute change in exposure per year, in units of notional.

    ``1.0`` means the rule trades one whole portfolio of notional a year. Non-finite
    leading entries are skipped rather than treated as zero, so a burn-in does not
    manufacture a first trade out of nothing.
    """
    series = np.asarray(leverage, dtype=np.float64)
    finite = np.flatnonzero(np.isfinite(series))
    if finite.size < 2:
        return 0.0
    active = series[finite[0] : finite[-1] + 1]
    changes = np.abs(np.diff(active))
    return float(np.nansum(changes)) * periods_per_year / float(active.size)


@dataclass(frozen=True, slots=True)
class LeveragePathResult:
    """A conditional-leverage rule, executed with its costs inside the path."""

    total_returns: FloatArray
    excess_returns: FloatArray
    months: int
    mean_leverage: float
    max_leverage: float
    turnover_per_year: float
    geometric_return: float
    volatility: float
    sharpe: float
    max_drawdown: float
    months_under_water: int
    trading_cost_charged: float
    """Annualised cost actually charged by the rule's own trading, in return units."""


def apply_leverage(
    base_excess: FloatArray,
    cash: FloatArray,
    leverage: FloatArray,
    *,
    borrow_spread: float = 0.0,
    cost_on_notional: float = 0.0,
    round_trip_cost: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> LeveragePathResult:
    """Run a leverage path over a base excess return, charging everything inside the path.

    Three charges, each in its own units and none of them optional to think about:

    * ``cost_on_notional`` — a fee, charged per year on the exposure actually held;
    * ``borrow_spread`` — charged per year on the financed part, ``max(L - 1, 0)``;
    * ``round_trip_cost`` — charged once per unit of notional traded, on ``|L_t - L_{t-1}|``.

    Periods where the leverage is not finite are dropped from both arms, so a burn-in costs
    observations rather than silently becoming an unlevered stretch.
    """
    base = np.asarray(base_excess, dtype=np.float64)
    funding = np.asarray(cash, dtype=np.float64)
    path = np.asarray(leverage, dtype=np.float64)
    if base.shape != funding.shape or base.shape != path.shape:
        raise ValueError("base, cash and leverage must have the same shape")
    if round_trip_cost < 0.0 or cost_on_notional < 0.0 or borrow_spread < 0.0:
        raise ValueError("costs cannot be negative")
    usable = np.isfinite(path) & np.isfinite(base) & np.isfinite(funding)
    if not usable.any():
        raise ValueError("no period has a finite leverage, base return and cash rate")
    first, last = int(np.argmax(usable)), int(usable.size - np.argmax(usable[::-1]) - 1)
    window = slice(first, last + 1)
    exposure = path[window]
    if not np.isfinite(exposure).all():
        raise ValueError("the leverage path has a gap after it starts; fill or trim it first")

    traded = np.abs(np.diff(exposure, prepend=exposure[0]))
    charge = (
        cost_on_notional * exposure / periods_per_year
        + borrow_spread * np.maximum(exposure - 1.0, 0.0) / periods_per_year
        + round_trip_cost * traded
    )
    excess = exposure * base[window] - charge
    total = excess + funding[window]
    curve = np.cumprod(1.0 + total)
    summary = drawdown_summary(curve)
    volatility = float(np.std(excess, ddof=1)) * math.sqrt(periods_per_year)
    return LeveragePathResult(
        total_returns=np.asarray(total, dtype=np.float64),
        excess_returns=np.asarray(excess, dtype=np.float64),
        months=int(exposure.size),
        mean_leverage=float(np.mean(exposure)),
        max_leverage=float(np.max(exposure)),
        turnover_per_year=leverage_turnover(exposure, periods_per_year=periods_per_year),
        geometric_return=float(curve[-1]) ** (periods_per_year / total.size) - 1.0,
        volatility=volatility,
        sharpe=float(np.mean(excess)) * periods_per_year / volatility,
        max_drawdown=summary.max_drawdown,
        months_under_water=summary.max_time_under_water,
        trading_cost_charged=float(np.sum(round_trip_cost * traded))
        * periods_per_year
        / float(exposure.size),
    )


# --------------------------------------------------------------------------------
# 6. The outcome distribution, which is what the charter asks for instead of an optimum
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HorizonOutcome:
    """The candidate against its control over one horizon, on block resamples."""

    horizon_years: float
    resamples: int
    block_length: int
    probability_underperform: float
    median_relative_wealth: float
    relative_wealth_quantiles: Mapping[str, float]
    median_max_drawdown: float
    worst_max_drawdown: float
    drawdown_quantiles: Mapping[str, float]
    median_control_max_drawdown: float


def horizon_outcomes(
    candidate_total: FloatArray,
    control_total: FloatArray,
    *,
    horizon_years: float,
    resamples: int,
    block_length: int,
    rng: np.random.Generator,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> HorizonOutcome:
    """Relative terminal wealth, drawdown and P(underperform) over resampled histories.

    The two arms are resampled **jointly** — the same block indices are applied to both —
    so every draw is one investor's two portfolios on one history rather than two
    independent histories. Comparing independently resampled arms would inflate the spread
    of the difference and understate the probability of underperformance.

    The resampling imposes a block-stationary null: it preserves dependence up to the block
    length and destroys it beyond, so it neither confirms nor denies multi-year mean
    reversion, and a horizon much longer than the sample is an extrapolation of that null
    rather than a measurement.
    """
    candidate = np.asarray(candidate_total, dtype=np.float64)
    control = np.asarray(control_total, dtype=np.float64)
    if candidate.shape != control.shape:
        raise ValueError("candidate and control must have the same shape")
    if candidate.ndim != 1:
        raise ValueError("returns must be one-dimensional")
    if block_length < 1:
        raise ValueError(f"block_length must be at least 1, got {block_length}")
    if resamples < 1:
        raise ValueError(f"resamples must be at least 1, got {resamples}")
    horizon = round(horizon_years * periods_per_year)
    if horizon < 1:
        raise ValueError(f"horizon_years must cover at least one period, got {horizon_years}")

    n = candidate.size
    blocks = math.ceil(horizon / block_length)
    starts = rng.integers(0, n, size=(resamples, blocks))
    offsets = np.arange(block_length, dtype=np.intp)
    drawn = (starts[:, :, None] + offsets[None, None, :]) % n
    indices = drawn.reshape(resamples, -1)[:, :horizon]

    candidate_paths = 1.0 + candidate[indices]
    control_paths = 1.0 + control[indices]
    candidate_wealth = np.cumprod(candidate_paths, axis=1)
    control_wealth = np.cumprod(control_paths, axis=1)
    relative = candidate_wealth[:, -1] / control_wealth[:, -1]

    candidate_peak = np.maximum.accumulate(candidate_wealth, axis=1)
    control_peak = np.maximum.accumulate(control_wealth, axis=1)
    candidate_drawdown = np.min(candidate_wealth / candidate_peak - 1.0, axis=1)
    control_drawdown = np.min(control_wealth / control_peak - 1.0, axis=1)

    levels = (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99)
    return HorizonOutcome(
        horizon_years=horizon_years,
        resamples=resamples,
        block_length=block_length,
        probability_underperform=float(np.mean(relative < 1.0)),
        median_relative_wealth=float(np.median(relative)),
        relative_wealth_quantiles={
            f"p{int(level * 100)}": float(np.quantile(relative, level)) for level in levels
        },
        median_max_drawdown=float(np.median(candidate_drawdown)),
        worst_max_drawdown=float(np.min(candidate_drawdown)),
        drawdown_quantiles={
            f"p{int(level * 100)}": float(np.quantile(candidate_drawdown, level))
            for level in levels
        },
        median_control_max_drawdown=float(np.median(control_drawdown)),
    )


# --------------------------------------------------------------------------------
# 6a. The stretch to sit through: how often a stated relative run arrives, by horizon
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class RelativeRunOutcome:
    """How often relative wealth falls a stated distance below its running peak."""

    trigger: float
    resamples: int
    block_length: int
    breach_probability_by_horizon: Mapping[float, float]
    median_worst_run_by_horizon: Mapping[float, float]


def relative_run_outcomes(
    candidate_total: FloatArray,
    control_total: FloatArray,
    *,
    trigger: float,
    horizons_years: Sequence[float],
    resamples: int,
    block_length: int,
    rng: np.random.Generator,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> RelativeRunOutcome:
    """P(relative wealth sits ``trigger`` below its peak within each horizon), resampled.

    One set of joint block resamples is drawn at the **longest** horizon and every shorter
    horizon is read off the same paths as a prefix, so the probabilities are nested by
    construction: a run that arrives inside ten years has arrived inside twenty. The
    relative path and its running peak are defined exactly as
    :func:`portfolio_edge.studies.trend_weight_regret.abandonment_adjusted_gap` defines
    them, so a probability here and an abandonment probability there are the same
    quantity measured on two panels.
    """
    if trigger >= 0.0:
        raise ValueError(f"trigger must be a negative relative drawdown, got {trigger}")
    candidate = np.asarray(candidate_total, dtype=np.float64)
    control = np.asarray(control_total, dtype=np.float64)
    if candidate.shape != control.shape or candidate.ndim != 1:
        raise ValueError("candidate and control must be one-dimensional and the same length")
    if block_length < 1 or resamples < 1:
        raise ValueError("block_length and resamples must both be at least one")
    if not horizons_years:
        raise ValueError("at least one horizon is required")
    horizons = [round(h * periods_per_year) for h in horizons_years]
    if min(horizons) < 1:
        raise ValueError("every horizon must cover at least one period")

    n = candidate.size
    longest = max(horizons)
    blocks = math.ceil(longest / block_length)
    starts = rng.integers(0, n, size=(resamples, blocks))
    offsets = np.arange(block_length, dtype=np.intp)
    drawn = (starts[:, :, None] + offsets[None, None, :]) % n
    indices = drawn.reshape(resamples, -1)[:, :longest]

    relative = np.cumprod((1.0 + candidate[indices]) / (1.0 + control[indices]), axis=1)
    peak = np.maximum.accumulate(relative, axis=1)
    drawdown = relative / peak - 1.0
    breach_by_horizon: dict[float, float] = {}
    worst_by_horizon: dict[float, float] = {}
    for years, months in zip(horizons_years, horizons, strict=True):
        prefix = drawdown[:, :months]
        breach_by_horizon[years] = float(np.mean((prefix <= trigger).any(axis=1)))
        worst_by_horizon[years] = float(np.median(np.min(prefix, axis=1)))
    return RelativeRunOutcome(
        trigger=trigger,
        resamples=resamples,
        block_length=block_length,
        breach_probability_by_horizon=breach_by_horizon,
        median_worst_run_by_horizon=worst_by_horizon,
    )


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._notional_budget_tables import main

    main()
