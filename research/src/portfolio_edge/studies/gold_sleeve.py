"""Gold as a portfolio sleeve: the arithmetic, kept separate from the data that feeds it.

Why this module exists
----------------------
``docs/research/marginal-sleeve-value.md`` (Experiment 010) tested ten sleeves and
recorded, as an open question, that **gold was not tested and that its absence biases the
experiment toward finding no credit anywhere**. The bias direction is real: under pro-rata
funding the diversification credit is ``sigma_p**2 (1 - beta)`` per unit of sleeve weight,
so the credit is largest for the lowest-beta asset in the search, and every sleeve in that
search was an equity portfolio or a self-financing equity factor. Gold is the obvious
missing low-beta candidate. This module supplies the arithmetic to close that gap.

It contains **no market data and no cache access**, in the tradition of
:mod:`overlay_growth` and :mod:`equity_share`. :mod:`portfolio_edge.studies._gold_sleeve_tables`
is the one file that reads the cache.

The one assumption, named rather than buried
---------------------------------------------
Gold pays no distribution and has no corporate action, so for an unlevered holder

    total return  =  price return  -  carry cost,

exactly. The carry cost is a **vehicle fee** for an ETF holder and **storage plus
insurance** for a holder of metal, and it is the only free parameter in the identity. It
is therefore a required, non-defaulted argument everywhere it appears: see
:class:`GoldCarry`. A caller cannot obtain a gold return from this module without stating
what they assume it costs to hold, which is the whole point.

:func:`total_returns_from_levels` charges the annual cost as ``c / 12`` each month rather
than ``(1 + c)**(1/12) - 1``. The two differ by less than 0.1 bp/yr at every tier this
repository considers, and the simple-division form is what a fund's daily accrual actually
approximates. It is stated because a reader should not have to infer a compounding
convention.

What the three measurements are for
------------------------------------
*Unconditional moments* (:func:`sleeve_moments`) feed equation (4) of
:mod:`overlay_growth`, the admission threshold ``S_d > L rho sigma_p``. **Read that
module's first misuse warning before quoting the result**: equation (4) mis-scores any
sleeve above roughly ``|rho| = 0.5``, because there the first-order term is a small
difference of large numbers. Gold's correlation to equity is well inside the valid range,
and :func:`admission` checks rather than assumes it.

*The conditional correlation* (:func:`conditional_correlation`) is the axis that decides.
``docs/research/capital-efficiency-and-breadth.md`` (Capital efficiency §9.3) shows
that a diversifier's correlation **inside equity drawdowns** is what sets the portfolio's
drawdown, and that a full-sample correlation can be comfortably negative while the crisis
correlation is not. An unconditional correlation is not evidence about a hedge.

*The marginal value* (:func:`pro_rata_marginal_value`) is Experiment 010's construction
re-expressed: a standalone term plus a diversification credit capped by the base
portfolio's own variance. It is computed here as a **realised finite difference at the
reference weight**, matching that experiment's deciding clause (a), with the first-order
decomposition reported beside it rather than in place of it. The specification exp_010
froze explicitly rejects the derivative-at-zero, on the grounds that it "favours any
low-beta asset by construction" — which is precisely the direction a gold result would be
flattered in.

What this module cannot do
---------------------------
It cannot promote anything. Its inputs are an exploratory price benchmark
(:mod:`portfolio_edge.data.lbma`) and a stated carry assumption, and no specification was
frozen before its numbers were seen.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.studies.overlay_growth import (
    OverlayInputs,
    sharpe_admission_threshold,
)

__all__ = [
    "EQUATION_4_CORRELATION_LIMIT",
    "MONTHS_PER_YEAR",
    "Admission",
    "ConditionalCorrelation",
    "GoldCarry",
    "MarginalValue",
    "SleeveMoments",
    "admission",
    "conditional_correlation",
    "drawdown_mask",
    "geometric_growth",
    "pro_rata_marginal_value",
    "sleeve_moments",
    "total_returns_from_levels",
]

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]

MONTHS_PER_YEAR: Final = 12

#: Above this, :mod:`overlay_growth` equation (4) stops being an admission test and
#: :func:`admission` says so in its own output rather than leaving it to a reader.
EQUATION_4_CORRELATION_LIMIT: Final = 0.5


@dataclass(frozen=True)
class GoldCarry:
    """What it costs to hold an ounce for a year, and where that number came from.

    Attributes:
        annual_cost: Decimal per year, charged against the price return.
        label: The vehicle or arrangement this describes.
        source: Where the number was published. **An assumption states its own
            provenance or it is not usable**; a tier invented for a sensitivity arm
            should say so here in those words.
    """

    annual_cost: float
    label: str
    source: str

    def __post_init__(self) -> None:
        if self.annual_cost < 0.0:
            raise ValueError(f"annual_cost must be non-negative, got {self.annual_cost}")
        if not self.label.strip() or not self.source.strip():
            raise ValueError("a carry tier must carry a label and a source")


def total_returns_from_levels(
    levels: Sequence[float] | FloatArray, *, carry: GoldCarry
) -> FloatArray:
    """``r_t = P_t / P_{t-1} - 1 - c/12``, one shorter than ``levels``.

    The identity is exact for physical gold because there is no distribution to add and
    no corporate action to adjust for. ``carry`` is required, not defaulted: a price
    return quoted as a total return is the error this argument exists to prevent.
    """
    prices = np.asarray(levels, dtype=np.float64)
    if prices.ndim != 1 or prices.size < 2:
        raise ValueError("levels must be a one-dimensional series of at least two prices")
    if not np.all(np.isfinite(prices)) or np.any(prices <= 0.0):
        raise ValueError("levels must be finite and strictly positive")
    price_return: FloatArray = prices[1:] / prices[:-1] - 1.0
    return price_return - carry.annual_cost / MONTHS_PER_YEAR


def geometric_growth(returns: Sequence[float] | FloatArray) -> float:
    """Annualised geometric return of a monthly simple-return series, realised.

    The realised compounding of the actual path, not the lognormal approximation. The
    two are compared in :mod:`portfolio_edge.core.returns`; this module uses the realised
    figure everywhere a growth rate decides something, because
    ``docs/decisions/0008-growth-decides-crra-reports.md`` (decision 0008) makes
    growth the deciding metric and an approximation should not be what decides.
    """
    series = np.asarray(returns, dtype=np.float64)
    if series.ndim != 1 or series.size == 0:
        raise ValueError("returns must be a non-empty one-dimensional series")
    if np.any(series <= -1.0):
        raise ValueError(
            "the path reached non-positive wealth, so its geometric growth rate does "
            "not exist"
        )
    log_wealth = float(np.sum(np.log1p(series)))
    return math.expm1(log_wealth * MONTHS_PER_YEAR / series.size)


@dataclass(frozen=True)
class SleeveMoments:
    """Annualised moments of one sleeve against one base, on aligned monthly excesses.

    Every figure is **excess of cash** and annualised: means by 12, volatilities by
    ``sqrt(12)``. ``geometric_excess`` compounds the excess series itself, which is not
    the same as the difference of two geometric returns and is labelled so it cannot be
    mistaken for one.
    """

    months: int
    arithmetic_excess: float
    geometric_excess: float
    volatility: float
    sharpe: float
    correlation: float
    beta: float
    base_arithmetic_excess: float
    base_volatility: float
    base_sharpe: float


def sleeve_moments(
    sleeve_excess: Sequence[float] | FloatArray,
    base_excess: Sequence[float] | FloatArray,
) -> SleeveMoments:
    """Annualised moments of ``sleeve_excess`` and its relationship to ``base_excess``."""
    sleeve = _series(sleeve_excess, name="sleeve_excess")
    base = _series(base_excess, name="base_excess")
    if sleeve.shape != base.shape:
        raise ValueError(
            f"sleeve and base must be aligned; got {sleeve.size} and {base.size} months"
        )
    if sleeve.size < 3:
        raise ValueError("at least three months are needed for a volatility")
    sleeve_volatility = float(np.std(sleeve, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    base_volatility = float(np.std(base, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    if sleeve_volatility <= 0.0 or base_volatility <= 0.0:
        raise ValueError("a zero-variance series has no Sharpe ratio and no correlation")
    correlation = float(np.corrcoef(sleeve, base)[0, 1])
    arithmetic = float(np.mean(sleeve)) * MONTHS_PER_YEAR
    base_arithmetic = float(np.mean(base)) * MONTHS_PER_YEAR
    return SleeveMoments(
        months=int(sleeve.size),
        arithmetic_excess=arithmetic,
        geometric_excess=geometric_growth(sleeve),
        volatility=sleeve_volatility,
        sharpe=arithmetic / sleeve_volatility,
        correlation=correlation,
        beta=correlation * sleeve_volatility / base_volatility,
        base_arithmetic_excess=base_arithmetic,
        base_volatility=base_volatility,
        base_sharpe=base_arithmetic / base_volatility,
    )


@dataclass(frozen=True)
class Admission:
    """Equation (4) of :mod:`overlay_growth`, applied and then qualified.

    ``within_equation_4_range`` is part of the result rather than a note beside it,
    because that module's first documented misuse is quoting the verdict without it.
    """

    base_exposure: float
    sleeve_sharpe: float
    threshold: float
    margin: float
    admitted: bool
    correlation: float
    within_equation_4_range: bool


def admission(moments: SleeveMoments, *, base_exposure: float = 1.0) -> Admission:
    """Does the sleeve's net Sharpe ratio clear ``L rho sigma_p``?

    ``moments`` must already be net of carry — :func:`total_returns_from_levels` is the
    only way a gold return is built in this repository and it charges the carry there, so
    no cost is deducted a second time here.
    """
    inputs = OverlayInputs(
        base_excess_return=moments.base_arithmetic_excess,
        base_volatility=moments.base_volatility,
        diversifier_excess_return=moments.arithmetic_excess,
        diversifier_volatility=moments.volatility,
        correlation=moments.correlation,
    )
    threshold = sharpe_admission_threshold(inputs, base_exposure=base_exposure)
    return Admission(
        base_exposure=base_exposure,
        sleeve_sharpe=moments.sharpe,
        threshold=threshold,
        margin=moments.sharpe - threshold,
        admitted=moments.sharpe > threshold,
        correlation=moments.correlation,
        within_equation_4_range=abs(moments.correlation) <= EQUATION_4_CORRELATION_LIMIT,
    )


def drawdown_mask(
    base_excess: Sequence[float] | FloatArray, *, threshold: float
) -> BoolArray:
    """Months in which the base sits at least ``threshold`` below its running peak.

    The same definition ``docs/research/capital-efficiency-and-breadth.md`` §9.3 uses,
    restated here rather than imported so that a change to the stress machinery
    cannot silently redefine what "crisis" means in this study. ``threshold`` is a depth
    and must be non-negative; ``0.0`` selects every month not at a new high.
    """
    series = _series(base_excess, name="base_excess")
    if threshold < 0.0:
        raise ValueError(f"threshold is a depth and must be non-negative, got {threshold}")
    if np.any(series <= -1.0):
        raise ValueError("the base path reached non-positive wealth")
    curve = np.cumprod(1.0 + series)
    peak = np.maximum.accumulate(curve)
    mask: BoolArray = curve / peak - 1.0 <= -threshold
    return mask


@dataclass(frozen=True)
class ConditionalCorrelation:
    """Correlation to the base inside and outside its own drawdowns.

    Both halves are reported and neither is a subset statistic quoted alone. The
    difference between them is the finding whichever way it falls: a hedge that is only
    negatively correlated when it is not needed is not a hedge, and
    ``docs/research/portfolio-edge-research-framework.md`` (the framework)'s claim
    that "gold has been an average hedge" is a statement about exactly this pair.
    """

    threshold: float
    months_in: int
    months_out: int
    correlation_in: float
    correlation_out: float
    correlation_full: float
    sleeve_mean_in: float
    sleeve_mean_out: float
    base_mean_in: float

    @property
    def gap(self) -> float:
        """``correlation_in - correlation_out``. Positive means it correlates up in a
        crisis, which is the direction that breaks a diversification argument."""
        return self.correlation_in - self.correlation_out


def conditional_correlation(
    base_excess: Sequence[float] | FloatArray,
    sleeve_excess: Sequence[float] | FloatArray,
    *,
    threshold: float,
) -> ConditionalCorrelation:
    """Correlation of sleeve to base, split by whether the base is in drawdown.

    Means are reported **per month, not annualised**, because the conditioning set is
    not a calendar and annualising a conditional mean invites it to be read as a rate.
    """
    base = _series(base_excess, name="base_excess")
    sleeve = _series(sleeve_excess, name="sleeve_excess")
    if base.shape != sleeve.shape:
        raise ValueError("base and sleeve must be aligned")
    mask = drawdown_mask(base, threshold=threshold)
    inside = int(mask.sum())
    outside = int(mask.size - inside)
    if inside < 3 or outside < 3:
        raise ValueError(
            f"a conditional correlation needs at least three months on each side; got "
            f"{inside} inside and {outside} outside at a {threshold:.0%} threshold"
        )
    return ConditionalCorrelation(
        threshold=threshold,
        months_in=inside,
        months_out=outside,
        correlation_in=float(np.corrcoef(base[mask], sleeve[mask])[0, 1]),
        correlation_out=float(np.corrcoef(base[~mask], sleeve[~mask])[0, 1]),
        correlation_full=float(np.corrcoef(base, sleeve)[0, 1]),
        sleeve_mean_in=float(np.mean(sleeve[mask])),
        sleeve_mean_out=float(np.mean(sleeve[~mask])),
        base_mean_in=float(np.mean(base[mask])),
    )


@dataclass(frozen=True)
class MarginalValue:
    """Experiment 010's decomposition for one sleeve at one weight, in pp/yr.

    ``realised_marginal_growth`` is the **deciding** quantity: the finite difference in
    realised annualised geometric return between the blended path and the base path, at
    ``weight``, funded pro rata. ``first_order_*`` are the algebraic decomposition
    reported beside it. They will not agree exactly and are not meant to — the first
    order is a derivative at zero and the decider is a difference at ``w``.
    """

    weight: float
    base_growth: float
    blended_growth: float
    realised_marginal_growth: float
    standalone_alpha: float
    beta: float
    credit_per_unit_weight: float
    credit_at_weight: float
    credit_ceiling_at_weight: float
    first_order_marginal: float


def pro_rata_marginal_value(
    base_returns: Sequence[float] | FloatArray,
    sleeve_returns: Sequence[float] | FloatArray,
    cash_returns: Sequence[float] | FloatArray,
    *,
    weight: float,
) -> MarginalValue:
    """Blend ``weight`` of sleeve into the base pro rata and price the difference.

    All three inputs are **total** monthly returns; the cash series is used only to form
    the excesses the decomposition needs, never to fund anything — pro-rata funding sells
    the base, which is what makes it the least favourable rule for a diversifier and why
    Experiment 010 chose it as its headline.

    The blended path is ``(1 - w) * base + w * sleeve`` each month, which is a constant
    target rebalanced monthly. Trading cost is **not** charged here: it depends on the
    vehicle and the account, it is a per-caller assumption, and burying it in a study
    would repeat the mistake of a constant haircut. Charge it on the sleeve series before
    calling, which is what :func:`total_returns_from_levels` exists for.

    Returns the realised finite difference together with the first-order decomposition
    ``(mu_i - mu_p) + sigma_p**2 (1 - beta)``, whose second term is the diversification
    credit and whose ceiling at ``beta = 0`` is exactly ``sigma_p**2 * w``.
    """
    base = _series(base_returns, name="base_returns")
    sleeve = _series(sleeve_returns, name="sleeve_returns")
    cash = _series(cash_returns, name="cash_returns")
    if not base.shape == sleeve.shape == cash.shape:
        raise ValueError("base, sleeve and cash must be aligned")
    if not 0.0 <= weight <= 1.0:
        raise ValueError(f"weight must lie in [0, 1], got {weight}")

    blended = (1.0 - weight) * base + weight * sleeve
    base_growth = geometric_growth(base)
    blended_growth = geometric_growth(blended)

    base_excess = base - cash
    sleeve_excess = sleeve - cash
    base_variance = float(np.var(base_excess, ddof=1)) * MONTHS_PER_YEAR
    base_volatility = math.sqrt(base_variance)
    sleeve_volatility = float(np.std(sleeve_excess, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    if base_volatility <= 0.0 or sleeve_volatility <= 0.0:
        raise ValueError("a zero-variance leg has no beta")
    correlation = float(np.corrcoef(sleeve_excess, base_excess)[0, 1])
    beta = correlation * sleeve_volatility / base_volatility
    alpha = (
        float(np.mean(sleeve_excess)) - float(np.mean(base_excess))
    ) * MONTHS_PER_YEAR
    credit_per_unit = base_variance * (1.0 - beta)
    return MarginalValue(
        weight=weight,
        base_growth=base_growth,
        blended_growth=blended_growth,
        realised_marginal_growth=blended_growth - base_growth,
        standalone_alpha=alpha,
        beta=beta,
        credit_per_unit_weight=credit_per_unit,
        credit_at_weight=credit_per_unit * weight,
        credit_ceiling_at_weight=base_variance * weight,
        first_order_marginal=(alpha + credit_per_unit) * weight,
    )


def _series(values: Sequence[float] | FloatArray, *, name: str) -> FloatArray:
    series = np.asarray(values, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {series.shape}")
    if series.size == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.all(np.isfinite(series)):
        raise ValueError(f"{name} contains non-finite values")
    return series


if __name__ == "__main__":  # pragma: no cover - regenerates the published gold tables
    from portfolio_edge.studies._gold_sleeve_tables import main

    main()
