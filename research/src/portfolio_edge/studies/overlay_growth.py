"""What a diversifying sleeve is worth depends on what you sell to buy it.

This repository has measured the same sleeve against two funding rules and reported
two different answers without naming the reason. Experiment 004 added a 15% trend
sleeve to a 60/40 equity/cash portfolio against a risk-matched cash comparator and
measured **+1.312 pp/yr** of growth. Experiment 010b added a 10% trend sleeve to a
fully invested global equity core, funded pro rata, and measured **+0.258 pp/yr**
against a 0.30 threshold. Both are correct. The gap is not evidence, sample or
weight: it is the funding rule, and this module derives its exact size.

Notation throughout, all arithmetic and all in excess of cash:

===================  ==========================================================
``a_e``, ``sigma_e``  equity's arithmetic excess return over cash, and its volatility
``a_d``, ``sigma_d``  the diversifier's, **gross** of financing and fee
``rho``               their correlation; ``beta = rho sigma_d / sigma_e``
``s``                 the financing spread paid over cash to obtain notional
``phi``               the fee charged on notional
``a_net``             ``a_d - s - phi``, what a unit of notional actually earns
===================  ==========================================================

Growth is ``g = r + A - V/2`` throughout, with ``A`` the portfolio's arithmetic
excess return and ``V`` its variance. That is the lognormal approximation, exact in
continuous time, and it is the same objective decision 0008 makes deciding.

**The two funding rules.**

*Overlay.* Hold one unit of equity and add ``w`` units of diversifier notional,
financed. ``A(w) = a_e + w a_net`` and
``V(w) = sigma_e**2 + 2 w rho sigma_e sigma_d + w**2 sigma_d**2``, so

    dg/dw at w=0  =  a_net - rho sigma_e sigma_d.                            (1)

*Pro rata.* Hold ``1 - w`` units of equity and ``w`` of diversifier, selling equity
to fund it. ``A(w) = (1-w) a_e + w a_net`` and
``V(w) = (1-w)**2 sigma_e**2 + 2 w (1-w) rho sigma_e sigma_d + w**2 sigma_d**2``, so

    dg/dw at w=0  =  (a_net - a_e) + sigma_e**2 (1 - beta).                  (2)

Expression (2) is Experiment 010's diversification credit, re-derived. Subtracting
(1) from (2), **every term involving the diversifier cancels**:

    pro-rata bar  -  overlay bar  =  a_e - sigma_e**2
                                  =  sigma_e**2 (L_e* - 1),                  (3)

where ``L_e* = a_e / sigma_e**2`` is equity's own growth-optimal leverage. This is
the central result of the module and it is worth stating in words:

    **The funding rule changes the hurdle a diversifier must clear by an amount
    that depends on nothing about the diversifier — only on how far equity's own
    growth-optimal exposure sits above 1. The two rules agree exactly when
    ``L_e* = 1``, that is, precisely when the zero-leverage constraint does not
    bind.**

At ``a_e = 5.5%`` and ``sigma_e = 16%`` the gap is 2.94 pp/yr, and ``L_e* = 2.15``.
So the repository's zero-leverage rule is not a neutral simplification that lowers
returns a little. It raises the bar every candidate diversifier has been judged
against by nearly three percentage points a year, which is larger than any premium
this repository has ever attempted to measure. The corner solution in
``docs/research/setting-the-equity-share.md`` §1.1 and the null result in Experiment
010 are two readings of the same constraint.

**The general form.** With equity held at exposure ``L`` rather than 1, (1) becomes
``a_net - L rho sigma_e sigma_d > 0``, or dividing by ``sigma_d``,

    S_d  >  L rho sigma_e.                                                   (4)

At ``L = L_e*`` this is the textbook tangency condition ``S_d > rho S_e``: an asset
belongs in the growth-optimal portfolio iff its Sharpe ratio exceeds its correlation
times the incumbent's. **At negative correlation the threshold is negative**, so a
diversifier with a small negative expected excess return can still raise growth. That
is not a loophole; it is the same statement as (3) seen from the other side.

**The honest control, and it is unforgiving.** None of the above establishes that an
overlay beats simply levering equity to the same risk. At matched volatility
``sigma_p``, levered equity grows at ``r + sigma_p S_e - sigma_p**2 / 2`` and the
overlay portfolio at ``r + A - sigma_p**2 / 2``. The variance terms are identical by
construction, so

    **at matched volatility the higher Sharpe ratio wins, and nothing else
    matters.**                                                               (5)

Every figure this module produces must be read through (5). An overlay that raises
growth over *unlevered* equity while lowering the portfolio's Sharpe ratio has bought
its gain with leverage, and ``docs/the-plan.md`` requires that be labelled leveraged
beta rather than alpha.

**What this module is not.** It is algebra about a stated model, in the tradition of
:mod:`volatility_harvesting` and :mod:`equity_share`, and it contains no market data
and no claim that any diversifier clears any bar. The inputs it takes are forecasts.
It fixes ``sigma_d`` and ``rho`` as known, which flatters the overlay, because the
estimation error priced in section 5 is on the mean alone; and it assumes the
financing spread ``s`` is constant, which
``docs/research/structural-and-tax-edges.md`` §3 shows it is not — the measured
Fleckenstein-Longstaff funding basis of 58.70 bp is an average over 28 years, not a
guarantee.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from portfolio_edge.studies.equity_share import optimal_kelly_shrinkage

__all__ = [
    "FundingRule",
    "OverlayInputs",
    "OverlaySizing",
    "funding_rule_gap",
    "growth_optimal_overlay_weight",
    "marginal_growth",
    "matched_volatility_verdict",
    "overlay_growth_gain",
    "required_net_excess_return",
    "sharpe_admission_threshold",
    "shrunk_overlay_weight",
]


# --------------------------------------------------------------------------------
# 1. Inputs
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class OverlayInputs:
    """One diversifier bolted onto one equity position, all figures annual.

    Returns are **arithmetic excesses over cash**, not geometric and not total. The
    financing spread and fee are charged on notional, which is what a return-stacked
    fund actually does, and they are separate arguments because they move for
    different reasons: the spread is a market price and the fee is a contract.
    """

    equity_excess_return: float
    equity_volatility: float
    diversifier_excess_return: float
    diversifier_volatility: float
    correlation: float
    financing_spread: float = 0.0
    fee: float = 0.0

    def __post_init__(self) -> None:
        if self.equity_volatility <= 0.0:
            raise ValueError(
                f"equity volatility must be positive, got {self.equity_volatility}"
            )
        if self.diversifier_volatility <= 0.0:
            raise ValueError(
                "diversifier volatility must be positive, "
                f"got {self.diversifier_volatility}"
            )
        if not -1.0 <= self.correlation <= 1.0:
            raise ValueError(f"correlation must lie in [-1, 1], got {self.correlation}")

    @property
    def net_excess_return(self) -> float:
        """``a_net = a_d - s - phi``: what one unit of notional earns over cash.

        The fee and the financing spread enter identically here, which is why a
        cheap fund financing badly and an expensive fund financing well are the same
        portfolio. Only the sum is decision-relevant.
        """
        return self.diversifier_excess_return - self.financing_spread - self.fee

    @property
    def beta(self) -> float:
        """``beta = rho sigma_d / sigma_e``, the diversifier's beta on equity."""
        return self.correlation * self.diversifier_volatility / self.equity_volatility

    @property
    def covariance(self) -> float:
        """``rho sigma_e sigma_d``, the term that decides every bar in this module."""
        return (
            self.correlation * self.equity_volatility * self.diversifier_volatility
        )

    @property
    def equity_kelly_leverage(self) -> float:
        """``L_e* = a_e / sigma_e**2``, equity's own growth-optimal exposure.

        The single number that decides whether the funding rule matters at all: by
        (3), the two bars coincide iff this equals 1.
        """
        return self.equity_excess_return / self.equity_volatility**2

    @property
    def equity_sharpe(self) -> float:
        return self.equity_excess_return / self.equity_volatility

    @property
    def diversifier_sharpe(self) -> float:
        """Sharpe of the diversifier **net** of financing and fee."""
        return self.net_excess_return / self.diversifier_volatility


class FundingRule:
    """Namespace for the two rules, kept as constants so specifications can name them."""

    OVERLAY = "overlay"
    PRO_RATA = "pro_rata"


# --------------------------------------------------------------------------------
# 2. The two bars, and the gap between them
# --------------------------------------------------------------------------------


def marginal_growth(inputs: OverlayInputs, *, rule: str, equity_exposure: float = 1.0) -> float:
    """``dg/dw`` at ``w = 0``: growth added per unit of the first sleeve dollar.

    ``rule`` selects (1) or (2) from the module docstring. ``equity_exposure``
    generalises the overlay rule to equity held at ``L`` rather than 1 and is
    ignored under pro rata, where the equity weight is what is being traded away.

    Positive means the first dollar of the sleeve raises growth. It says nothing
    about how much of it to hold — that is :func:`growth_optimal_overlay_weight` —
    and nothing about whether levering equity would have done better, which is
    :func:`matched_volatility_verdict` and is the question that decides.
    """
    if rule == FundingRule.OVERLAY:
        return inputs.net_excess_return - equity_exposure * inputs.covariance
    if rule == FundingRule.PRO_RATA:
        return (
            inputs.net_excess_return
            - inputs.equity_excess_return
            + inputs.equity_volatility**2 * (1.0 - inputs.beta)
        )
    raise ValueError(f"unknown funding rule {rule!r}")


def required_net_excess_return(inputs: OverlayInputs, *, rule: str) -> float:
    """The smallest ``a_net`` at which the first sleeve dollar breaks even.

    Overlay: ``rho sigma_e sigma_d``, which is **negative whenever the correlation
    is**. Pro rata: ``a_e - sigma_e**2 (1 - beta)``. Their difference is
    :func:`funding_rule_gap` and involves no property of the diversifier.
    """
    if rule == FundingRule.OVERLAY:
        return inputs.covariance
    if rule == FundingRule.PRO_RATA:
        return inputs.equity_excess_return - inputs.equity_volatility**2 * (
            1.0 - inputs.beta
        )
    raise ValueError(f"unknown funding rule {rule!r}")


def funding_rule_gap(*, equity_excess_return: float, equity_volatility: float) -> float:
    """``a_e - sigma_e**2 = sigma_e**2 (L_e* - 1)``: how much harder pro rata is.

    Equation (3). **It takes no diversifier argument, and that is the finding** — the
    penalty the zero-leverage rule imposes on every candidate sleeve is a property of
    the equity position alone. It is positive iff equity's growth-optimal leverage
    exceeds 1, zero iff the constraint does not bind, and negative for an equity
    position already levered past its own optimum, where selling equity to buy
    anything is an improvement.
    """
    if equity_volatility <= 0.0:
        raise ValueError(
            f"equity volatility must be positive, got {equity_volatility}"
        )
    return equity_excess_return - equity_volatility**2


def sharpe_admission_threshold(
    inputs: OverlayInputs, *, equity_exposure: float = 1.0
) -> float:
    """``L rho sigma_e``: the Sharpe ratio a diversifier must beat, equation (4).

    At ``equity_exposure = inputs.equity_kelly_leverage`` this returns
    ``rho * S_e``, the textbook tangency condition, and the two statements are the
    same statement. Below negative correlation it is negative, so a sleeve with a
    negative net expected excess return can still raise growth — a fact that should
    make any reader suspicious of the inputs rather than pleased with the result.
    """
    return equity_exposure * inputs.correlation * inputs.equity_volatility


# --------------------------------------------------------------------------------
# 3. How much to hold, and what it is worth
# --------------------------------------------------------------------------------


def growth_optimal_overlay_weight(inputs: OverlayInputs) -> float:
    """``w* = (a_net - rho sigma_e sigma_d) / sigma_d**2``.

    The unconstrained growth-optimal overlay notional, obtained by setting
    ``dg/dw = a_net - rho sigma_e sigma_d - w sigma_d**2`` to zero. It is a plug-in
    optimum computed from forecasts and should never be used unshrunk; see
    :func:`shrunk_overlay_weight` and the ``1/(2T)`` result it rests on.
    """
    return (inputs.net_excess_return - inputs.covariance) / inputs.diversifier_volatility**2


def overlay_growth_gain(inputs: OverlayInputs, *, weight: float) -> float:
    """Growth added by an overlay of ``weight`` units of notional, exactly.

    ``w (a_net - rho sigma_e sigma_d) - w**2 sigma_d**2 / 2``. A downward parabola in
    ``w`` whose peak is at :func:`growth_optimal_overlay_weight` and whose value
    there is ``(a_net - rho sigma_e sigma_d)**2 / (2 sigma_d**2)``. It reaches zero
    again at twice the optimal weight, which is
    :func:`portfolio_edge.studies.equity_share.growth_retained_fraction`'s statement
    in a different coordinate.
    """
    edge = inputs.net_excess_return - inputs.covariance
    return weight * edge - 0.5 * weight**2 * inputs.diversifier_volatility**2


@dataclass(frozen=True)
class OverlaySizing:
    """Everything decided by one set of forecasts, so a caller cannot quote half."""

    weight: float
    growth_gain: float
    portfolio_volatility: float
    portfolio_sharpe: float
    equity_sharpe: float
    leverage_matched_growth_gain: float
    beats_leverage_matched_equity: bool


def _portfolio_volatility(inputs: OverlayInputs, weight: float) -> float:
    variance = (
        inputs.equity_volatility**2
        + 2.0 * weight * inputs.covariance
        + weight**2 * inputs.diversifier_volatility**2
    )
    if variance <= 0.0:
        raise ValueError("portfolio variance is non-positive; inputs are inconsistent")
    return math.sqrt(variance)


def matched_volatility_verdict(inputs: OverlayInputs, *, weight: float) -> OverlaySizing:
    """The overlay against equity levered to the same volatility — equation (5).

    This is the control ``docs/the-plan.md`` makes mandatory: *"A strategy that beats
    VTI only by taking more equity beta must be labelled as leveraged beta, not
    alpha."* Because both portfolios are held at the same variance, the ``-V/2`` term
    is common and the comparison collapses to Sharpe ratios. ``growth_gain`` is
    measured against **unlevered** equity and ``leverage_matched_growth_gain``
    against equity levered to ``sigma_p / sigma_e``; the second is the honest one and
    is the smaller of the two whenever the overlay's own Sharpe is the lower.
    """
    volatility = _portfolio_volatility(inputs, weight)
    excess = inputs.equity_excess_return + weight * inputs.net_excess_return
    portfolio_sharpe = excess / volatility
    levered_excess = volatility * inputs.equity_sharpe
    return OverlaySizing(
        weight=weight,
        growth_gain=overlay_growth_gain(inputs, weight=weight),
        portfolio_volatility=volatility,
        portfolio_sharpe=portfolio_sharpe,
        equity_sharpe=inputs.equity_sharpe,
        leverage_matched_growth_gain=excess - levered_excess,
        beats_leverage_matched_equity=portfolio_sharpe > inputs.equity_sharpe,
    )


# --------------------------------------------------------------------------------
# 4. Estimation error, which is where the argument is actually decided
# --------------------------------------------------------------------------------


def shrunk_overlay_weight(inputs: OverlayInputs, *, years: float) -> float:
    """The plug-in optimum shrunk by ``f* = S**2 T / (S**2 T + 1)``.

    The shrinkage argument transfers from :mod:`equity_share` unchanged, and so does
    the ``1/(2T)`` plug-in cost: the overlay weight's estimation variance is
    ``1 / (T sigma_d**2)`` and the growth loss is quadratic with curvature
    ``sigma_d**2``, so their product is ``1 / (2T)`` with ``sigma_d`` cancelling
    exactly as it does for equity. Use
    :func:`portfolio_edge.studies.equity_share.plug_in_growth_cost` for it.

    **The Sharpe ratio that governs the shrinkage is the marginal one**,
    ``(a_net - rho sigma_e sigma_d) / sigma_d``, not the diversifier's standalone
    Sharpe. For a negatively correlated sleeve the marginal Sharpe is the larger, so
    a diversifier is shrunk *less* than its own record would justify — which is the
    correct answer and an uncomfortable one, because it means the position size is
    most confident exactly where the correlation estimate is doing the work and the
    correlation is being treated as known.
    """
    marginal_sharpe = (
        inputs.net_excess_return - inputs.covariance
    ) / inputs.diversifier_volatility
    shrinkage = optimal_kelly_shrinkage(sharpe_ratio=marginal_sharpe, years=years)
    return shrinkage * growth_optimal_overlay_weight(inputs)
