"""The funding rule is not a modelling choice. It is a property of the fund you buy.

:mod:`portfolio_edge.studies.overlay_growth` derives the gap between the two funding
rules and finds it is ``a_p - sigma_p**2``, an expression containing nothing about the
sleeve. It states the two rules as a dichotomy: *overlay*, where nothing is sold, and
*pro rata*, where the base is sold to fund the sleeve.

**Real wrappers are not a dichotomy, and reading them as one gets NTSX wrong.** A
90/60 efficient-core fund is neither. Buying a dollar of it costs a dollar of base
equity and returns ninety cents of equity plus sixty cents of Treasury notional, so
ten cents of equity are sold per sixty cents of overlay obtained. This module places
every wrapper on the continuum between the two rules with one number, and shows that
the continuum has an exact closed form.

Notation extends :mod:`overlay_growth`. A wrapper is two numbers per dollar of
capital:

===========  ===============================================================
``b``        dollars of **base** exposure delivered per dollar of capital
``d``        dollars of **diversifier** notional delivered per dollar of capital
===========  ===============================================================

``b + d`` is the wrapper's **gross notional per dollar**, the quantity a fact sheet
calls "capital efficiency". It is *not* the quantity that decides anything, and the
central point of this module is that two wrappers at identical gross notional can sit
at opposite ends of the funding rule.

**The derivation.** Hold ``1 - x`` of the base directly and put ``x`` into the
wrapper. Base exposure is ``B = 1 - x + x b = 1 - x (1 - b)`` and diversifier notional
is ``D = x d``. Solving ``w = x d`` for the diversifier notional the investor wants,

    B(w) = 1 - w delta,     delta = (1 - b) / d.                             (6)

``delta`` is **the base sold per unit of diversifier notional obtained**. With
``A(w) = B a_p + w a_net`` and
``V(w) = B**2 sigma_p**2 + 2 B w rho sigma_p sigma_d + w**2 sigma_d**2``, and
``g = A - V/2``,

    dg/dw at w=0  =  (a_net - rho sigma_p sigma_d)  -  delta (a_p - sigma_p**2).  (7)

**The wrapper's structure enters exactly once, as a multiplier on the funding-rule
gap.** Equation (7) reduces to :mod:`overlay_growth`'s equation (1) at ``delta = 0``
and to its equation (2) at ``delta = 1``, and both reductions are pinned by tests. So:

======================  ========  =========================================
Wrapper                 ``delta``  Reading
======================  ========  =========================================
100 equity / 100 trend   0.00      pure overlay. Nothing is sold
90 equity / 60 bonds     0.167     keeps 83.3% of the funding-rule benefit
100% trend, standalone   1.00      pure pro rata. The full gap is paid
50 equity / 50 trend     1.00      **also** pure pro rata, at half the notional
40 equity / 30 trend     2.00      **worse than selling equity outright**
======================  ========  =========================================

The fourth row is the one worth staring at. A 50/50 fund is marketed as capital
efficient and is arithmetically indistinguishable, at the margin, from selling equity
to buy a standalone product. Its gross notional of 1.0x is the tell, and gross
notional is the number this module asks for first.

**Cost is charged in the wrong units by every fact sheet.** An expense ratio is quoted
on capital; the sleeve's hurdle in :mod:`overlay_growth` is stated per unit of
*notional*. The conversion is ``fee / d``, and it is not a rounding adjustment: a
0.20% fee on a wrapper delivering 0.60 of notional is **0.333% per unit of notional**,
and a 1.03% fee on a wrapper delivering 1.00 is 1.03%. Comparing the two expense
ratios directly compares different things.

**What this module is not.** It is algebra over stated structural facts, in the
tradition of :mod:`overlay_growth`. It reads no market data, promotes nothing, and
takes ``a_p``, ``sigma_p``, ``a_d``, ``sigma_d`` and ``rho`` as forecasts supplied by
the caller. In particular ``a_p - sigma_p**2`` changes sign at ``a_p = sigma_p**2``,
so every figure it produces inherits :mod:`overlay_growth`'s warning that the
funding-rule gap is a forecast rather than a measurement, and **anything quoting a
penalty must quote the ``a_p`` that produced it.**

It also assumes the wrapper's two legs are the base and the diversifier the caller
named. A wrapper stacking a *third* exposure — global equity where the investor holds
US, say — is not described by ``b`` alone, and :func:`base_substitution_note` exists
to make that refusal explicit rather than silent.
"""

from __future__ import annotations

from dataclasses import dataclass

from portfolio_edge.studies.overlay_growth import (
    FundingRule,
    OverlayInputs,
    funding_rule_gap,
    marginal_growth,
)

__all__ = [
    "Wrapper",
    "base_substitution_note",
    "capital_share_required",
    "cost_per_unit_notional",
    "displacement",
    "funding_capture",
    "funding_rule_penalty",
    "marginal_growth_through_wrapper",
    "required_net_excess_return_through_wrapper",
    "wrapper_funding_class",
]


@dataclass(frozen=True)
class Wrapper:
    """One fund, described by what a dollar of it delivers.

    ``base_notional`` and ``diversifier_notional`` are **gross notional exposures per
    dollar of capital**, as read from holdings and derivative notionals rather than
    from marketing copy. ``fee`` is the all-in expense charged on capital — the net
    expense ratio plus acquired fund fees, not the headline number.

    ``financing_spread`` is charged on the diversifier notional and defaults to zero
    because for most wrappers it is not disclosed. Zero is a stated absence, not a
    measurement, and a caller who leaves it there is asserting the wrapper finances
    at cash.
    """

    name: str
    base_notional: float
    diversifier_notional: float
    fee: float = 0.0
    financing_spread: float = 0.0

    def __post_init__(self) -> None:
        if self.diversifier_notional <= 0.0:
            raise ValueError(
                "diversifier notional must be positive — a wrapper delivering none "
                f"is not on this continuum at all, got {self.diversifier_notional}"
            )
        if self.base_notional < 0.0:
            raise ValueError(
                f"base notional may not be negative, got {self.base_notional}"
            )
        if self.fee < 0.0:
            raise ValueError(f"fee may not be negative, got {self.fee}")

    @property
    def gross_notional(self) -> float:
        """``b + d``: what a fact sheet calls capital efficiency.

        **It decides nothing on its own.** A 50/50 fund and a standalone product both
        show 1.0x here and both pay the full funding-rule gap; a 90/60 fund shows
        1.5x and pays a sixth of it. :func:`displacement` is the number that decides.
        """
        return self.base_notional + self.diversifier_notional


def displacement(wrapper: Wrapper) -> float:
    """``delta = (1 - b) / d``: base sold per unit of diversifier notional obtained.

    Equation (6). Zero for a pure overlay, one for a pure pro-rata vehicle, and
    **greater than one for a wrapper that dilutes the base faster than it adds
    notional** — a category that exists on the real shelf and has no name in the
    marketing vocabulary.

    Negative values are returned rather than refused: a wrapper delivering more base
    exposure than the dollar it consumed (``b > 1``) is levering the base as well, and
    the sign correctly says the funding rule is now working in the holder's favour.
    """
    return (1.0 - wrapper.base_notional) / wrapper.diversifier_notional


def funding_capture(wrapper: Wrapper) -> float:
    """``1 - delta``: the share of the funding-rule benefit the wrapper keeps.

    1.0 for a pure overlay, 0.0 for a pure pro-rata vehicle. Reported as a share
    because that is how the wrapper decision is actually made — the gap itself is a
    forecast and the share is a structural fact.
    """
    return 1.0 - displacement(wrapper)


def funding_rule_penalty(
    wrapper: Wrapper, *, base_excess_return: float, base_volatility: float
) -> float:
    """``delta (a_p - sigma_p**2)``: pp/yr of hurdle the wrapper's structure adds.

    The second term of equation (7). Zero for a pure overlay by construction, and
    equal to :func:`overlay_growth.funding_rule_gap` for a pure pro-rata vehicle.
    **It inherits that function's sign warning**: below ``a_p = sigma_p**2`` the gap
    is negative and a pro-rata vehicle is the better structure.
    """
    return displacement(wrapper) * funding_rule_gap(
        base_excess_return=base_excess_return, base_volatility=base_volatility
    )


def marginal_growth_through_wrapper(
    wrapper: Wrapper, inputs: OverlayInputs
) -> float:
    """Equation (7): ``dg/dw`` at ``w = 0`` for a sleeve obtained through this wrapper.

    ``inputs.fee`` and ``inputs.financing_spread`` are taken as the costs charged per
    unit of **notional**; :func:`cost_per_unit_notional` converts a wrapper's
    capital-denominated expense ratio into that unit, and the caller is responsible
    for having done so. Mixing the units is the error this module exists to prevent
    and it cannot be detected from the numbers.
    """
    return marginal_growth(
        inputs, rule=FundingRule.OVERLAY
    ) - funding_rule_penalty(
        wrapper,
        base_excess_return=inputs.base_excess_return,
        base_volatility=inputs.base_volatility,
    )


def required_net_excess_return_through_wrapper(
    wrapper: Wrapper, inputs: OverlayInputs
) -> float:
    """The ``a_net`` at which the first sleeve dollar breaks even through this wrapper.

    ``rho sigma_p sigma_d + delta (a_p - sigma_p**2)``. Negative at negative
    correlation and small ``delta``, which is the whole reason a diversifier with no
    expected excess return at all can still raise growth inside an overlay wrapper and
    cannot inside a pro-rata one.
    """
    return inputs.covariance + funding_rule_penalty(
        wrapper,
        base_excess_return=inputs.base_excess_return,
        base_volatility=inputs.base_volatility,
    )


def cost_per_unit_notional(wrapper: Wrapper) -> float:
    """``(fee / d) + financing_spread``: the wrapper's cost in the sleeve's own units.

    The fee is charged on capital and divided by the notional it buys; the financing
    spread is already charged on notional and is not rescaled. **A cheap wrapper that
    delivers little notional is not cheap**, and this is the only place in the
    repository that says so in the units the hurdle is stated in.
    """
    return wrapper.fee / wrapper.diversifier_notional + wrapper.financing_spread


def capital_share_required(wrapper: Wrapper, *, diversifier_weight: float) -> float:
    """``w / d``: share of the portfolio that must sit in the wrapper to obtain ``w``.

    Also the share of **tax shelter** consumed, which is the constraint
    ``docs/research/capital-efficiency-and-breadth.md`` §7 finds binding. A wrapper
    delivering ``d = 0.5`` of trend notional needs twice the sheltered capital of one
    delivering ``d = 1.0`` for the same sleeve, whatever their expense ratios say.
    """
    if diversifier_weight < 0.0:
        raise ValueError(
            f"diversifier weight may not be negative, got {diversifier_weight}"
        )
    return diversifier_weight / wrapper.diversifier_notional


def wrapper_funding_class(wrapper: Wrapper, *, tolerance: float = 1e-9) -> str:
    """Name the wrapper's position on the continuum, for a table column.

    ``"overlay"``, ``"partial-overlay"``, ``"pro-rata"``, ``"worse-than-pro-rata"`` or
    ``"levered-base"``. The boundaries are exact rather than judgemental: they are
    ``delta = 0`` and ``delta = 1``, the two points at which equation (7) collapses to
    one of :mod:`overlay_growth`'s two rules.
    """
    delta = displacement(wrapper)
    if delta < -tolerance:
        return "levered-base"
    if abs(delta) <= tolerance:
        return "overlay"
    if abs(delta - 1.0) <= tolerance:
        return "pro-rata"
    if delta < 1.0:
        return "partial-overlay"
    return "worse-than-pro-rata"


def base_substitution_note(wrapper: Wrapper, *, base_is_substitutable: bool) -> str:
    """Refuse, in words, to score a wrapper whose base leg is not the reader's base.

    Equation (7) assumes the ``b`` the wrapper delivers is the *same exposure* the
    investor was already holding. For RSSB — global equity stacked on bonds — held by
    an investor whose base is US equity, it is not: the wrapper changes the equity
    composition **and** adds an overlay, and those are two decisions this module
    cannot separate. Returning a sentence rather than a number is deliberate.
    """
    if base_is_substitutable:
        return (
            f"{wrapper.name}: base leg substitutes for the incumbent, "
            f"delta = {displacement(wrapper):.4f} applies."
        )
    return (
        f"{wrapper.name}: base leg is NOT the incumbent exposure. Equation (7) does "
        "not apply — the wrapper changes the base composition and adds an overlay, "
        "and no single delta separates those two decisions."
    )
