"""Arithmetic for the adversarial review of the 2026-08 construction session.

Five checks recur across
[the adversarial review](../../../../docs/research/adversarial-review.md), and each of
them is a small closed-form calculation that belongs in code rather than in prose.

**1. Restating a premium on a like-for-like basis.** A break-even haircut computed
against an *arithmetic, gross* mean cannot be compared with a *geometric, net-of-fee*
forecast. The two differ by ``sigma**2 / 2`` plus whatever fee the forecast already
carries, and if the simulation charges that fee separately the comparison also
double-counts it. :func:`restate_to_arithmetic_gross` puts a stated forecast back on
the basis the break-even was computed on and reports each correction separately.

**2. A sub-period's own detection floor.** A minimum detectable effect scales as
``1/sqrt(n)``; the difference between two disjoint sub-periods has twice the full
sample's standard error. :func:`subperiod_floor` and :func:`difference_floor` are the
two lines that let an era table be read against its own resolution rather than against
zero. Both assume the gap's volatility is the same in the sub-period as in the whole,
which is why they are stated as scalings of a measured floor and never as a measurement.

**3. Charging a fitted alpha.** Charging only those alphas whose point estimate exceeds
their own detection floor conditions on the estimator's variance: it charges whatever
was measured precisely and forgives whatever was not. :func:`empirical_bayes_alphas`
is the standard alternative — shrink every estimate toward the common prior by
``tau**2 / (tau**2 + s_i**2)``, with ``tau**2`` estimated by moments from the
cross-section. It charges every fund and charges none of them at face value.

**4. Restating a Sharpe ratio at another volatility.** A trend book built on four
instruments and a vendor's book built on fifty-eight are not comparable in level. Their
Sharpe ratios are, and :func:`premium_at_volatility` converts one into a premium at the
other's volatility so that a break-even stated in pp/yr can be applied to it.

**5. What an edge is worth against a savings rate.** :func:`contribution_equivalent`
answers the question nobody in the session asked: how much extra monthly contribution
buys the same terminal wealth as ``edge`` percentage points a year of extra growth. For
an accumulating investor this is the comparator every sleeve decision should be scored
against, because it is the one lever with no tracking error and no detection floor.

Nothing here reads data. Every function takes numbers a caller measured elsewhere, so
the same arithmetic runs on a fixture, on a published table, or on a fresh run.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from portfolio_edge.core._types import FloatArray

__all__ = [
    "BasisRestatement",
    "EmpiricalBayesAlphas",
    "contribution_equivalent",
    "difference_floor",
    "empirical_bayes_alphas",
    "premium_at_volatility",
    "restate_to_arithmetic_gross",
    "subperiod_floor",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class BasisRestatement:
    """A forecast put back on an arithmetic, gross-of-the-named-fee basis.

    ``stated`` is what the source published. ``arithmetic_gross`` is the same forecast
    with the variance drag and the fee added back. ``implied_haircut`` is the haircut
    from ``realised`` that the restated forecast actually represents, which is the
    number a break-even computed on arithmetic means may be compared with.
    """

    stated: float
    volatility: float
    fee_added_back: float
    variance_drag_added_back: float
    arithmetic_gross: float
    realised: float
    implied_haircut: float
    stated_haircut: float

    @property
    def haircut_overstatement(self) -> float:
        """How much larger the naive haircut is than the like-for-like one."""
        return self.stated_haircut - self.implied_haircut


def restate_to_arithmetic_gross(
    *,
    stated_geometric_net: float,
    volatility: float,
    fee: float,
    realised_arithmetic_gross: float,
) -> BasisRestatement:
    """Put a geometric, net-of-``fee`` forecast on an arithmetic gross basis.

    All arguments are in the same units (percentage points per year is the natural
    one here). The variance drag uses the second-order approximation
    ``arithmetic ~ geometric + sigma**2 / 2``, which is the one implied by taking a
    log growth rate as the geometric mean.

    Raises ``ValueError`` on a negative volatility or fee, because both would make the
    correction move the wrong way and neither is a quantity that can be negative.
    """
    if volatility < 0.0:
        raise ValueError(f"volatility must not be negative, got {volatility}")
    if fee < 0.0:
        raise ValueError(f"fee must not be negative, got {fee}")
    drag = 0.5 * volatility * volatility / 100.0
    arithmetic = stated_geometric_net + fee + drag
    return BasisRestatement(
        stated=stated_geometric_net,
        volatility=volatility,
        fee_added_back=fee,
        variance_drag_added_back=drag,
        arithmetic_gross=arithmetic,
        realised=realised_arithmetic_gross,
        implied_haircut=realised_arithmetic_gross - arithmetic,
        stated_haircut=realised_arithmetic_gross - stated_geometric_net,
    )


def subperiod_floor(full_floor: float, *, full_months: int, subperiod_months: int) -> float:
    """A sub-period's detection floor, scaled from the full sample's by ``1/sqrt(n)``.

    This is an approximation and its one assumption is stated in the module docstring:
    the gap's volatility in the sub-period equals its volatility over the whole sample.
    Where that fails the true sub-period floor is larger in the volatile era and
    smaller in the quiet one, and the direction is knowable from the era's own
    volatility if a caller has it.
    """
    if full_floor < 0.0:
        raise ValueError(f"full_floor must not be negative, got {full_floor}")
    if full_months < 1 or subperiod_months < 1:
        raise ValueError("month counts must be positive")
    if subperiod_months > full_months:
        raise ValueError(
            f"subperiod {subperiod_months} exceeds the full sample {full_months}"
        )
    return full_floor * math.sqrt(full_months / subperiod_months)


def difference_floor(full_floor: float) -> float:
    """The floor on the *difference* between two halves of a sample.

    Each half has ``sqrt(2)`` times the full sample's standard error, and the
    difference of two independent halves has ``sqrt(2)`` times that again — so the
    floor on a first-half-minus-second-half difference is exactly twice the full
    sample's floor, with no dependence on the split point beyond its being a halving.

    This is the line an era table needs and rarely carries. "The effect was +4.80 in
    the first half and -0.30 in the second" is a claim about a difference of 5.10, and
    5.10 against a floor of 6.66 is not a finding.
    """
    if full_floor < 0.0:
        raise ValueError(f"full_floor must not be negative, got {full_floor}")
    return 2.0 * full_floor


@dataclass(frozen=True, slots=True, kw_only=True)
class EmpiricalBayesAlphas:
    """Shrunk alpha estimates and the weight each one kept."""

    estimates: FloatArray
    standard_errors: FloatArray
    prior_variance: float
    shrinkage: FloatArray
    shrunk: FloatArray

    def portfolio_charge(self, weights: Sequence[float]) -> float:
        """The weighted charge these shrunk alphas imply, in the alphas' own units."""
        w = np.asarray(weights, dtype=np.float64)
        if w.shape != self.shrunk.shape:
            raise ValueError(
                f"weights has shape {w.shape}, alphas have shape {self.shrunk.shape}"
            )
        return float(np.dot(w, self.shrunk))


def empirical_bayes_alphas(
    estimates: Sequence[float], standard_errors: Sequence[float]
) -> EmpiricalBayesAlphas:
    """Shrink a cross-section of fitted alphas toward zero by their own precision.

    The prior variance is estimated by moments: ``E[a**2] = tau**2 + s**2``, so
    ``tau**2 = mean(a**2) - mean(s**2)``, floored at zero. Each estimate then keeps
    ``tau**2 / (tau**2 + s_i**2)`` of itself.

    The prior is centred on **zero**, not on the sample mean of the alphas, because
    zero is what the headline arms of the design under review assume and because a
    fund's expected alpha before measurement is its fee, not its peers' average
    shortfall. Shrinking toward the sample mean would be defensible too and would move
    a single large negative estimate less; the choice is stated rather than tuned.

    A noiseless estimate (``s_i = 0``) keeps all of itself, and an estimate whose
    standard error swamps the cross-sectional spread keeps almost none. That is the
    property a threshold rule lacks: a threshold charges an estimate at face value the
    moment it crosses, and forgives it entirely one basis point below.
    """
    a = np.asarray(estimates, dtype=np.float64)
    s = np.asarray(standard_errors, dtype=np.float64)
    if a.ndim != 1:
        raise ValueError(f"estimates must be one-dimensional, got shape {a.shape}")
    if a.shape != s.shape:
        raise ValueError(f"shape mismatch: estimates {a.shape}, errors {s.shape}")
    if a.size == 0:
        raise ValueError("estimates is empty")
    if not np.isfinite(a).all() or not np.isfinite(s).all():
        raise ValueError("estimates and standard errors must all be finite")
    if np.any(s < 0.0):
        raise ValueError("standard errors must not be negative")
    tau_squared = max(float(np.mean(a * a) - np.mean(s * s)), 0.0)
    denominator = tau_squared + s * s
    safe = np.where(denominator > 0.0, denominator, 1.0)
    shrinkage = np.where(denominator > 0.0, tau_squared / safe, 0.0)
    return EmpiricalBayesAlphas(
        estimates=a,
        standard_errors=s,
        prior_variance=tau_squared,
        shrinkage=np.asarray(shrinkage, dtype=np.float64),
        shrunk=np.asarray(a * shrinkage, dtype=np.float64),
    )


def premium_at_volatility(sharpe: float, volatility: float) -> float:
    """The premium a Sharpe ratio implies at ``volatility``, in the same units.

    Used to put a narrow, independently constructed trend book and a wide vendor book
    on one scale. It assumes the two books differ in leverage and breadth but not in
    the *shape* of their return distribution, which is the assumption a Sharpe ratio
    already makes and is why the result is a bracket rather than an estimate.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    return sharpe * volatility


def contribution_equivalent(
    *, edge_pp_yr: float, growth_pp_yr: float, months: int
) -> float:
    """Monthly contribution, as a fraction of the starting balance, worth ``edge``.

    Solves for the constant monthly contribution ``c`` such that a portfolio growing at
    ``growth_pp_yr`` with contributions reaches the same terminal wealth as one
    growing at ``growth_pp_yr + edge_pp_yr`` with none. Both legs start from one unit.
    The contribution arrives at the **end** of each month and so earns no return in the
    month it is paid — an ordinary annuity, matching the month-by-month recursion
    ``w <- w * base + c`` that the test simulates.

    The answer depends on the balance the contributions are measured against, which is
    the whole point: an edge is a rate on capital and a contribution is a flow, so the
    two are only comparable once a horizon and a starting balance are named. For an
    accumulating investor early in a career the flow dominates by an order of
    magnitude; near the end it does not.
    """
    if months < 1:
        raise ValueError(f"months must be positive, got {months}")
    base = (1.0 + growth_pp_yr / 100.0) ** (1.0 / 12.0)
    fast = (1.0 + (growth_pp_yr + edge_pp_yr) / 100.0) ** (1.0 / 12.0)
    if base <= 0.0 or fast <= 0.0:
        raise ValueError("growth rates imply a non-positive monthly factor")
    target = fast**months
    lump = base**months
    annuity = (
        float(months)
        if math.isclose(base, 1.0)
        else (base**months - 1.0) / (base - 1.0)
    )
    if annuity <= 0.0:
        raise ValueError("degenerate annuity factor")
    return float((target - lump) / annuity)
