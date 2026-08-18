"""Whether a loading is worth buying, and which fund buys it most cheaply.

Why this module exists
----------------------
:mod:`portfolio_edge.studies.value_tilt` prices **one** exposure: it multiplies a
delivered HML loading by an HML premium and subtracts the incremental cost. It is silent
on the two questions that actually decided the US shelf, and that decide the ex-US one:

1. **Is the premium behind a loading signable at all?** A fund that buys HML also buys
   SMB, RMW and CMA, and an exposure whose premium this repository cannot sign is
   variance with no priced expectation — pure drag on the geometric term. The US answer
   was that a small-value fund's ``SMB ~ +0.85`` is exactly that. Whether the same holds
   on the developed-ex-US panel is a **measurement**, not a transfer, because
   Experiment 005 found HML three times larger outside the United States, and nothing
   says SMB behaves the same way.
2. **How much tracking error does a unit of exposure cost?** Two funds buying the same
   HML at different tracking errors are not the same purchase, and the ratio is what
   ranks a shelf.

Both are arithmetic over stated inputs. Neither reads market data;
:mod:`portfolio_edge.studies._exus_value_tilt_tables` is the one file that touches the
cache, in the same split :mod:`portfolio_edge.studies.value_tilt` uses.

What "signable" means here, precisely
-------------------------------------
It is the conjunction this repository has already been applying in prose:

* the interval excludes zero, **and**
* the point estimate is at least as large as the smallest effect its own window could
  detect at 80% power.

The second clause is the one that does the work and the one a *p*-value cannot supply.
``docs/research/evidence-base.md`` exists because a null from an instrument whose floor
exceeds the effect carries almost no information — so **"not signable" never means "the
premium is zero"**, and :attr:`Signability.reason` says which clause failed so a caller
cannot quote the verdict without it.

Materiality (2.0 pp/yr, the repository's threshold) is reported separately and is not
part of the verdict, because a premium can be signable and too small to matter.

The alpha charge
----------------
:func:`alpha_charged_edge` implements the rule ``docs/research/portfolio-recommendation.md``
§5 applied to DFLV by hand: the tilt chain prices an exposure and **assumes alpha is
zero**, so a fund whose own raw alpha exceeds what its window could detect is being
flattered by every figure in its row. The charge is applied **only** when the alpha is
measurable, and always net of the comparator's own model-misfit pedestal — every alpha
here is a distance from that pedestal, never from zero
([factor products, conclusion 4](../../../docs/research/factor-products.md)). Crediting an
unmeasurable *positive* alpha would be the same error with the sign flipped, and is
refused for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from portfolio_edge.studies.value_tilt import (
    PERCENT_PER_BASIS_POINT,
    TiltInputs,
    TiltVerdict,
)

__all__ = [
    "MATERIALITY_PERCENT",
    "PremiumEvidence",
    "Signability",
    "alpha_charged_edge",
    "growth_per_unit_tracking_error",
    "signability",
    "tracking_error_per_unit_exposure",
]

MATERIALITY_PERCENT: Final = 2.0
"""The repository's materiality threshold in percentage points per year.

Frozen in Experiment 001's specification and reused unchanged by 005 and 006. Reported
beside a signability verdict and never part of it.
"""


# --------------------------------------------------------------------------------
# 1. Is the premium behind a loading signable?
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Signability:
    """The verdict and both clauses, so neither can be quoted without the other."""

    interval_excludes_zero: bool
    exceeds_detection_floor: bool
    material: bool
    reason: str

    @property
    def signable(self) -> bool:
        """Both clauses hold. Materiality is deliberately not part of this."""
        return self.interval_excludes_zero and self.exceeds_detection_floor


@dataclass(frozen=True, slots=True)
class PremiumEvidence:
    """One premium on one panel over one window, with everything needed to read it.

    ``panel`` and ``window`` are not decoration. Grading an ex-US fund on the US panel
    moves individual loadings by up to 0.480, so **an ex-US loading without its panel
    named is not a number** ([factor products, conclusion
    5](../../../docs/research/factor-products.md)); the same applies to the premium the
    loading is multiplied by.
    """

    label: str
    panel: str
    window: str
    months: int
    point: float
    low: float
    high: float
    mde80: float

    def __post_init__(self) -> None:
        if not self.panel.strip():
            raise ValueError("a premium must name the panel it was measured on")
        if self.low > self.high:
            raise ValueError(f"interval is inverted: [{self.low}, {self.high}]")
        if self.mde80 < 0.0:
            raise ValueError(f"a detection floor cannot be negative, got {self.mde80}")

    @property
    def verdict(self) -> Signability:
        return signability(point=self.point, low=self.low, high=self.high, mde80=self.mde80)


def signability(*, point: float, low: float, high: float, mde80: float) -> Signability:
    """Is this premium signable — interval away from zero **and** above its own floor?

    ``low`` and ``high`` bound the same interval the repository publishes beside the
    point estimate (a stationary block bootstrap at 90%, in every case reaching this
    function). ``mde80`` is the smallest true premium the window could reject a zero mean
    for at 80% power, in the same units.

    The two clauses fail for different reasons and the distinction is the whole point: an
    interval containing zero says *the sample could have come from nothing*; a point
    below the detection floor says *this window could not have found the effect even if
    it were there*. The second is a statement about the instrument, and it is why a
    failure here is never evidence of absence.
    """
    excludes_zero = (low > 0.0 and high > 0.0) or (low < 0.0 and high < 0.0)
    above_floor = abs(point) >= mde80
    material = abs(point) >= MATERIALITY_PERCENT
    if excludes_zero and above_floor:
        reason = "signable: the interval excludes zero and the point clears its own floor"
    elif not excludes_zero and not above_floor:
        reason = (
            f"not signable: the interval [{low:+.2f}, {high:+.2f}] contains zero and "
            f"{point:+.2f} is below this window's {mde80:.2f} detection floor"
        )
    elif not excludes_zero:
        reason = f"not signable: the interval [{low:+.2f}, {high:+.2f}] contains zero"
    else:
        reason = (
            f"not signable: {point:+.2f} is below this window's {mde80:.2f} "
            "detection floor, so the window could not have found it"
        )
    return Signability(
        interval_excludes_zero=excludes_zero,
        exceeds_detection_floor=above_floor,
        material=material,
        reason=reason,
    )


# --------------------------------------------------------------------------------
# 2. What a unit of exposure costs, and what a unit of tracking error buys
# --------------------------------------------------------------------------------


def tracking_error_per_unit_exposure(inputs: TiltInputs) -> float:
    """``sd(fund - benchmark) / (h_fund - h_benchmark)``: the price of the exposure.

    In percentage points of tracking error per unit of delivered HML loading, and
    independent of the weight, which cancels. This is the ratio that separated AVLV and
    DFUV from AVUV on the US shelf: three funds buying comparable value at very different
    tracking errors are not the same purchase.

    Raises rather than returning an infinity when the swap buys no exposure, because a
    ratio with a zero denominator is not a large number, it is an undefined one.
    """
    delivered = inputs.delivered_loading
    if delivered == 0.0:
        raise ZeroDivisionError(
            "the swap buys no exposure, so tracking error per unit of it is undefined; "
            "report the tracking error in percentage points instead"
        )
    return inputs.sleeve_tracking_error / delivered


def growth_per_unit_tracking_error(verdict: TiltVerdict) -> float:
    """Basis points of geometric growth per basis point of portfolio tracking error.

    Both terms are linear in the weight, so this ranks funds rather than sizes a bet —
    which is the same reason ``P(30 yr)`` does not vary with weight in
    ``portfolio-recommendation.md`` §5. It is the ranking metric that answers *"which
    single fund belongs at this weight"*, and it is **not** an information ratio: the
    numerator is a growth contribution after the ``V/2`` drag, not an arithmetic edge.
    """
    tracking_error = verdict.portfolio_tracking_error_basis_points
    if tracking_error <= 0.0:
        raise ZeroDivisionError("a swap with no tracking error has no ratio to report")
    return verdict.growth_contribution_percent * 100.0 / tracking_error


# --------------------------------------------------------------------------------
# 3. The alpha the chain assumes away
# --------------------------------------------------------------------------------


def alpha_charged_edge(
    *,
    weight: float,
    portfolio_edge_basis_points: float,
    fund_alpha: float,
    benchmark_alpha: float,
    alpha_mde80: float,
) -> float:
    """The portfolio edge with the fund's **measurable** alpha charged against it.

    ``fund_alpha`` and ``benchmark_alpha`` are raw annual alphas in percent from the same
    specification on the same panel; the difference is the fund's distance from the
    comparator's own model-misfit pedestal rather than from zero. ``alpha_mde80`` is what
    the fund's own window could detect at 80% power.

    **The charge applies in one direction only.** An alpha smaller than its detection
    floor is not a measurement, so it is neither charged nor credited; the returned edge
    is then the input unchanged. A positive alpha is never credited at all, because the
    chain's premise is that a product delivers exposure and no skill, and paying a fund
    for unmeasurable skill is how a shelf audit turns into a manager selection.
    """
    net = fund_alpha - benchmark_alpha
    if abs(fund_alpha) < alpha_mde80 or net >= 0.0:
        return portfolio_edge_basis_points
    return portfolio_edge_basis_points + weight * net / PERCENT_PER_BASIS_POINT
