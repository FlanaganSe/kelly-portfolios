"""Financed gold and bitcoin on top of the construction: does the funding rule change the
crypto verdict?

Why this module exists
----------------------
``docs/research/alternative-sleeves-audit.md`` §3 sizes bitcoin at 0 to 2% of the portfolio,
labelled a speculation, and every number behind that verdict was measured on a pro-rata
construction in which bitcoin is bought by selling equity. Return Stacked's RSSX holds one
dollar of US equity plus about one dollar of a gold-and-bitcoin sleeve per dollar of capital,
so the sleeve is financed rather than funded, and §8 of the same page argues, for gold,
that a financed wrapper improves the hurdle without creating a premium. This module tests
that arithmetic on bitcoin instead of asserting it.

What it computes
----------------
* :func:`wrapper_excess` and :func:`portfolio_total`: the same wrapper algebra Experiment
  018 uses, ``sum(exposure * leg) - fee/12 - sum(financed * basis)/12`` per dollar of
  capital, combined at constant monthly-rebalanced capital weights on top of cash.
* :func:`compare`: one arm against the reference construction, on the arithmetic mean
  and on log growth, with a stationary block-bootstrap interval, the minimum detectable
  effect at 80% power from the paired difference series, maximum drawdown of both paths,
  the arm-minus-reference offset in the worst decile of equity months, and the
  up- and down-beta of that offset to equity.
* :func:`break_even_bitcoin_excess`: the arithmetic excess return bitcoin must earn for
  a financed stack to be worth holding against the core it displaces, as a closed form
  in the stack's exposures, fee and financing charges and the assumed gold premium; and
  :func:`growth_penalty_pp_yr`, the variance term that turns the arithmetic break-even
  into a log-growth one.
* :func:`track`: a realised fund series against its modelled exposure vector, so the
  assumed structure can be checked against the months the fund has actually printed.

What this module does not do
----------------------------
It holds **no market data and no cache access**, in the tradition of
:mod:`portfolio_edge.studies.conditional_breadth`;
:mod:`portfolio_edge.studies._financed_gold_bitcoin_tables` is the one file that reads the
cache. Nothing here is a frozen specification. The gold/bitcoin split, the bitcoin
financing basis, the window and the arms were all chosen after the audit's numbers had
been seen, which is why every result it produces is ``exploratory`` and why the tables
twin records its own run in the ledger.

Units
-----
Legs are **decimal monthly excess returns over cash**; ``cash`` is a decimal monthly total
return. Fees and financing rates are annual basis points. Reported gaps are percentage
points a year; conditional means are percentage points a month and are never annualised.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.core.drawdown import max_drawdown
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MONTHS_PER_YEAR,
    annualised_log_growth,
    minimum_detectable_effect,
)
from portfolio_edge.studies.stress_dependence import convexity, tail_dependence

__all__ = [
    "BASIS_POINTS",
    "PERCENT",
    "TAIL_QUANTILE",
    "Comparison",
    "TrackSummary",
    "Wrapper",
    "break_even_bitcoin_excess",
    "compare",
    "growth_penalty_pp_yr",
    "notional",
    "portfolio_total",
    "track",
    "wrapper_excess",
]

BASIS_POINTS: Final = 10_000.0
PERCENT: Final = 100.0

#: Fraction of months in the lower tail, the audit's convention.
TAIL_QUANTILE: Final = 0.10


@dataclass(frozen=True, slots=True, kw_only=True)
class Wrapper:
    """One holding: exposure per dollar of capital by leg, a fee, and the notional it
    finances at each leg's basis.

    A physical holding bought with capital carries no financing entry: the cash it
    displaces is already inside the leg's excess return. Only notional beyond the dollar
    of capital, obtained through futures, appears in ``financed``.
    """

    ticker: str
    exposures: Mapping[str, float]
    fee_bp: float
    financed: Mapping[str, float]
    note: str = ""


def _array(values: Sequence[float] | FloatArray, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains a non-finite value; align it upstream")
    return array


def wrapper_excess(
    legs: Mapping[str, Sequence[float] | FloatArray],
    wrapper: Wrapper,
    basis_bp: Mapping[str, float],
) -> FloatArray:
    """``sum(exposure * leg) - fee/12 - sum(financed * basis)/12``, decimal monthly.

    Identical in form to Experiment 018's ``wrapper_excess``, restated here so the legs
    can include bitcoin, which that experiment's leg list does not admit. A leg named
    in ``financed`` needs a basis in ``basis_bp``; a leg named only in ``exposures``
    does not.
    """
    columns = {name: _array(series, name=name) for name, series in legs.items()}
    lengths = {c.size for c in columns.values()}
    if len(lengths) != 1:
        raise ValueError(f"legs are not aligned: lengths {sorted(lengths)}")
    months = lengths.pop()
    total = np.zeros(months, dtype=np.float64)
    for leg, exposure in wrapper.exposures.items():
        if leg not in columns:
            raise ValueError(f"wrapper {wrapper.ticker} names leg {leg!r}, not supplied")
        total = total + exposure * columns[leg]
    annual = wrapper.fee_bp / BASIS_POINTS
    for leg, financed in wrapper.financed.items():
        if leg not in basis_bp:
            raise ValueError(f"wrapper {wrapper.ticker} finances {leg!r} with no basis given")
        annual += financed * basis_bp[leg] / BASIS_POINTS
    return np.asarray(total - annual / MONTHS_PER_YEAR, dtype=np.float64)


def portfolio_total(
    cash: Sequence[float] | FloatArray,
    weights: Mapping[str, float],
    excess: Mapping[str, Sequence[float] | FloatArray],
) -> FloatArray:
    """Funded monthly total return at constant capital weights rebalanced monthly.

    ``cash + sum(w_i * excess_i)``. Capital weights must sum to one: leverage lives
    inside a wrapper's exposures, never in the weights, exactly as Experiment 018 reads
    its arms. With a monthly rebalance to constant weights this is the exact path, not
    an approximation; the only thing Experiment 018's simulator adds is a 0.55 bp
    round-trip spread on rebalancing turnover, which is not charged here.
    """
    c = _array(cash, name="cash")
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError(f"capital weights sum to {sum(weights.values()):.6f}, not 1")
    total = c.copy()
    for ticker, weight in weights.items():
        if ticker not in excess:
            raise ValueError(f"no excess series for {ticker!r}")
        series = _array(excess[ticker], name=ticker)
        if series.size != c.size:
            raise ValueError(f"{ticker!r} has {series.size} months, cash has {c.size}")
        total = total + weight * series
    return np.asarray(total, dtype=np.float64)


def notional(weights: Mapping[str, float], wrappers: Mapping[str, Wrapper]) -> dict[str, float]:
    """Exposure per dollar of portfolio capital by leg, plus ``gross``."""
    by_leg: dict[str, float] = {}
    for ticker, weight in weights.items():
        for leg, exposure in wrappers[ticker].exposures.items():
            by_leg[leg] = by_leg.get(leg, 0.0) + weight * exposure
    by_leg["gross"] = sum(abs(v) for v in by_leg.values())
    return by_leg


# --------------------------------------------------------------------------- comparison


@dataclass(frozen=True, slots=True, kw_only=True)
class Comparison:
    """One arm against the reference, with everything a reader needs beside the gap.

    ``arithmetic_gap_pp_yr`` is ``1200 * mean(r_arm - r_ref)``; ``mde_pp_yr`` is the
    smallest gap this many months could have resolved at 80% power, from the paired
    difference series, and is the number to read before the point estimate.
    ``worst_decile_offset_pp_month`` is the mean of ``r_arm - r_ref`` in the worst
    decile of equity months, in percentage points a month.
    """

    name: str
    months: int
    arithmetic_gap_pp_yr: float
    arithmetic_interval: tuple[float, float]
    mde_pp_yr: float
    tracking_error_pct: float
    log_growth_gap_pp_yr: float
    log_growth_interval: tuple[float, float]
    arm_log_growth_pp_yr: float
    reference_log_growth_pp_yr: float
    arm_volatility_pct: float
    reference_volatility_pct: float
    arm_max_drawdown: float
    reference_max_drawdown: float
    worst_decile_months: int
    worst_decile_offset_pp_month: float
    worst_decile_hit_rate: float
    up_beta: float
    down_beta: float
    kappa: float
    kappa_t: float


def _wealth(total: FloatArray) -> FloatArray:
    return np.cumprod(1.0 + total)


def _volatility_pct(total: FloatArray) -> float:
    return float(np.std(total, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * PERCENT


def compare(
    name: str,
    arm_total: Sequence[float] | FloatArray,
    reference_total: Sequence[float] | FloatArray,
    *,
    equity_excess: Sequence[float] | FloatArray,
    indices: np.typing.NDArray[np.intp],
    confidence_level: float = 0.95,
) -> Comparison:
    """Score ``arm_total`` against ``reference_total`` on one aligned window.

    ``indices`` is a ``(n_resamples, months)`` array of bootstrap row indices, drawn
    once by the caller so every arm on a panel is scored on the same resamples. The
    conditional and convexity statistics use ``equity_excess`` as the base, so the
    worst decile is set by what equity did, never by what the arm did.
    """
    arm = _array(arm_total, name="arm_total")
    ref = _array(reference_total, name="reference_total")
    equity = _array(equity_excess, name="equity_excess")
    if arm.shape != ref.shape or arm.shape != equity.shape:
        raise ValueError("arm, reference and equity must cover the same months")
    if indices.ndim != 2 or indices.shape[1] != arm.size:
        raise ValueError(f"indices must be (n_resamples, {arm.size}), got {indices.shape}")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(f"confidence_level must lie in (0, 1), got {confidence_level}")

    difference = arm - ref
    gap = float(np.mean(difference)) * MONTHS_PER_YEAR * PERCENT
    resampled = difference[indices].mean(axis=1) * MONTHS_PER_YEAR * PERCENT
    tail = (1.0 - confidence_level) / 2.0
    low, high = np.quantile(resampled, [tail, 1.0 - tail])

    log_difference = np.log1p(arm) - np.log1p(ref)
    log_gap = float(np.mean(log_difference)) * MONTHS_PER_YEAR * PERCENT
    log_resampled = log_difference[indices].mean(axis=1) * MONTHS_PER_YEAR * PERCENT
    log_low, log_high = np.quantile(log_resampled, [tail, 1.0 - tail])

    dependence = tail_dependence(equity, difference, quantile=TAIL_QUANTILE)
    shape = convexity(equity, difference)

    return Comparison(
        name=name,
        months=int(arm.size),
        arithmetic_gap_pp_yr=gap,
        arithmetic_interval=(float(low), float(high)),
        mde_pp_yr=minimum_detectable_effect(difference),
        tracking_error_pct=_volatility_pct(difference),
        log_growth_gap_pp_yr=log_gap,
        log_growth_interval=(float(log_low), float(log_high)),
        arm_log_growth_pp_yr=annualised_log_growth(arm),
        reference_log_growth_pp_yr=annualised_log_growth(ref),
        arm_volatility_pct=_volatility_pct(arm),
        reference_volatility_pct=_volatility_pct(ref),
        arm_max_drawdown=max_drawdown(_wealth(arm)),
        reference_max_drawdown=max_drawdown(_wealth(ref)),
        worst_decile_months=dependence.months_low,
        worst_decile_offset_pp_month=dependence.mean_low * PERCENT,
        worst_decile_hit_rate=dependence.hit_rate_low,
        up_beta=shape.up_beta,
        down_beta=shape.down_beta,
        kappa=shape.kappa,
        kappa_t=shape.kappa_t,
    )


# --------------------------------------------------------------------------- break-even


def break_even_bitcoin_excess(
    stack: Wrapper,
    *,
    core_fee_bp: float,
    basis_bp: Mapping[str, float],
    gold_excess_pp_yr: float,
    equity_excess_pp_yr: float = 0.0,
    growth_penalty: float = 0.0,
) -> float:
    """The arithmetic bitcoin excess return, pp/yr, at which one dollar of ``stack``
    replacing one dollar of the equity core adds nothing.

    Per dollar of stack the expected gap over the core is::

        e_gold * mu_gold + e_btc * mu_btc + (e_equity - 1) * mu_equity
        - (fee - core_fee) - sum(financed * basis) - growth_penalty

    and setting it to zero gives ``mu_btc``. ``growth_penalty`` is zero for the
    arithmetic break-even and :func:`growth_penalty_pp_yr` for the log-growth one. All
    premia are in percentage points a year; fees and bases in basis points. The stack
    must carry a bitcoin exposure, or there is nothing to solve for.
    """
    e_btc = stack.exposures.get("bitcoin", 0.0)
    if e_btc <= 0.0:
        raise ValueError(f"{stack.ticker} has no bitcoin exposure; nothing to solve for")
    e_gold = stack.exposures.get("gold", 0.0)
    e_equity = stack.exposures.get("equity", 0.0)
    charges = (stack.fee_bp - core_fee_bp) / PERCENT
    for leg, financed in stack.financed.items():
        charges += financed * basis_bp[leg] / PERCENT
    covered = e_gold * gold_excess_pp_yr + (e_equity - 1.0) * equity_excess_pp_yr
    return (charges + growth_penalty - covered) / e_btc


def growth_penalty_pp_yr(
    reference_total: Sequence[float] | FloatArray,
    stack_over_core: Sequence[float] | FloatArray,
    *,
    weight: float,
) -> float:
    """The variance cost of adding ``weight`` of a stack to the reference, per unit of
    weight, in percentage points a year of log growth.

    ``g ~ mu - sigma^2 / 2``, so the growth gap is the arithmetic gap less
    ``(var(ref + w d) - var(ref)) / 2``, with ``d`` the stack's excess over the core it
    displaces. Divided by ``w`` it is the penalty per dollar of stack, in the same units
    as :func:`break_even_bitcoin_excess` takes. A second-order approximation, exact for
    lognormal returns and close for monthly ones.
    """
    ref = _array(reference_total, name="reference_total")
    d = _array(stack_over_core, name="stack_over_core")
    if ref.shape != d.shape:
        raise ValueError("reference and stack series must cover the same months")
    if weight <= 0.0:
        raise ValueError(f"weight must be positive, got {weight}")
    added = float(np.var(ref + weight * d, ddof=1) - np.var(ref, ddof=1))
    return 0.5 * added * MONTHS_PER_YEAR * PERCENT / weight


# --------------------------------------------------------------------------- tracking


@dataclass(frozen=True, slots=True, kw_only=True)
class TrackSummary:
    """A realised fund series beside its modelled exposure vector on the same months."""

    months: int
    fund_cumulative: float
    model_cumulative: float
    correlation: float
    mean_difference_pp_month: float
    difference_standard_error_pp_month: float
    tracking_error_pct: float


def track(
    fund_total: Sequence[float] | FloatArray, model_total: Sequence[float] | FloatArray
) -> TrackSummary:
    """Cumulative returns, correlation and the mean monthly gap of fund over model.

    The standard error is the plain iid one: a dozen months carry no usable
    autocorrelation estimate, and the point of the number is to say whether the gap is
    distinguishable from the fee, not to test anything.
    """
    fund = _array(fund_total, name="fund_total")
    model = _array(model_total, name="model_total")
    if fund.shape != model.shape:
        raise ValueError("fund and model must cover the same months")
    if fund.size < 3:
        raise ValueError("track needs at least three months")
    difference = fund - model
    return TrackSummary(
        months=int(fund.size),
        fund_cumulative=float(np.prod(1.0 + fund) - 1.0),
        model_cumulative=float(np.prod(1.0 + model) - 1.0),
        correlation=float(np.corrcoef(fund, model)[0, 1]),
        mean_difference_pp_month=float(np.mean(difference)) * PERCENT,
        difference_standard_error_pp_month=float(np.std(difference, ddof=1))
        / math.sqrt(fund.size)
        * PERCENT,
        tracking_error_pct=_volatility_pct(difference),
    )


if __name__ == "__main__":  # pragma: no cover - reporting entry point
    from portfolio_edge.studies._financed_gold_bitcoin_tables import main

    main()
