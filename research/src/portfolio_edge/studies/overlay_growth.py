"""What a diversifying sleeve is worth depends on what you sell to buy it.

Every marginal-sleeve result in this repository was produced by *selling something*
to fund the sleeve. Experiment 010 sold the base portfolio pro rata. Experiment 004
sold a 60/40 equity/cash base pro rata. Neither tested the rule a capital-efficient
fund actually uses, which is to sell nothing and finance the notional. This module
derives the exact size of that difference, and it is large.

**What this module does not claim.** It does *not* explain why Experiment 004
measured +1.312 pp/yr for a 15% trend sleeve and Experiment 010b measured +0.258 for
a 10% one. Checked rather than assumed: the funding-rule term accounts for
**+0.25 pp/yr of a +2.15 pp/yr per-unit-weight difference, about 12%.** The rest is
period, base composition, comparator and realised returns. Those two numbers are not
a worked example of anything here.

Notation throughout, all arithmetic and all in excess of cash. The base is whatever
portfolio the sleeve is being added to — 100% equity, a 60/40, anything — and every
result below is stated in its terms rather than equity's, because the funding rule is
a question about the thing being sold:

===================  ==========================================================
``a_p``, ``sigma_p``  the base portfolio's arithmetic excess return, and its volatility
``a_d``, ``sigma_d``  the diversifier's, **gross** of financing and fee
``rho``               their correlation; ``beta = rho sigma_d / sigma_p``
``s``                 the financing spread paid over cash to obtain notional
``phi``               the fee charged on notional
``a_net``             ``a_d - s - phi``, what a unit of notional actually earns
===================  ==========================================================

Growth is ``g = r + A - V/2`` throughout, with ``A`` the portfolio's arithmetic
excess return and ``V`` its variance. That is the lognormal approximation, exact in
continuous time, and it is the same objective decision 0008 makes deciding.

**The two funding rules.**

*Overlay.* Hold one unit of the base and add ``w`` units of diversifier notional,
financed. ``A(w) = a_p + w a_net`` and
``V(w) = sigma_p**2 + 2 w rho sigma_p sigma_d + w**2 sigma_d**2``, so

    dg/dw at w=0  =  a_net - rho sigma_p sigma_d.                            (1)

*Pro rata.* Hold ``1 - w`` units of the base and ``w`` of diversifier, selling the
base to fund it. ``A(w) = (1-w) a_p + w a_net`` and
``V(w) = (1-w)**2 sigma_p**2 + 2 w (1-w) rho sigma_p sigma_d + w**2 sigma_d**2``, so

    dg/dw at w=0  =  (a_net - a_p) + sigma_p**2 (1 - beta).                  (2)

Expression (2) is Experiment 010's diversification credit, re-derived. Subtracting
(1) from (2), **every term involving the diversifier cancels**:

    pro-rata bar  -  overlay bar  =  a_p - sigma_p**2
                                  =  sigma_p**2 (L_p* - 1),                  (3)

where ``L_p* = a_p / sigma_p**2`` is the base portfolio's own growth-optimal
leverage. This is the central result of the module and it is worth stating in words:

    **The funding rule changes the hurdle a diversifier must clear by an amount
    that depends on nothing about the diversifier — only on how far the base
    portfolio's own growth-optimal exposure sits above 1. The two rules agree
    exactly when ``L_p* = 1``, that is, precisely when the zero-leverage constraint
    does not bind.**

At ``a_p = 5.0%`` and ``sigma_p = 16%`` the gap is **2.44 pp/yr** and ``L_p* = 1.95``.
For the 60/40 equity/cash base Experiment 004 used it is **2.08 pp/yr**. So the
repository's zero-leverage rule is not a neutral simplification that lowers returns a
little. It raises the bar every candidate diversifier has been judged against by more
than two percentage points a year, which is larger than any premium this repository
has attempted to measure. The corner solution in
``docs/research/setting-the-equity-share.md`` §1.1 and the null result in Experiment
010 are two readings of the same constraint.

**The general form.** With the base held at exposure ``L`` rather than 1, (1) becomes
``a_net - L rho sigma_p sigma_d > 0``, or dividing by ``sigma_d``,

    S_d  >  L rho sigma_p.                                                   (4)

At ``L = L_p*`` this is the textbook tangency condition ``S_d > rho S_p``: an asset
belongs in the growth-optimal portfolio iff its Sharpe ratio exceeds its correlation
times the incumbent's. **At negative correlation the threshold is negative**, so a
diversifier with a small negative expected excess return can still raise growth. That
is not a loophole; it is the same statement as (3) seen from the other side.

**Two ways to misuse this module, both found in review rather than in theory.**

*First, (4) silently mis-scores a high-correlation sleeve.* Applied mechanically to a
covered-call or put-writing index at ``rho = 0.86``, the bar is about 0.20 and the
sleeve's standalone Sharpe of 0.55 clears it — yet its measured CAPM alpha is
**-0.09%/yr** and its Sharpe is *below the market's* over the same window. The
threshold is a **first-order** condition at ``w = 0``: at high correlation almost all
of the marginal contribution is alpha, the first-order term is a small difference of
large numbers, and the estimate is swamped. **Do not read (4) as an admission test
above roughly ``|rho| = 0.5``**; there, compute the alpha and its standard error
instead. The condition is exact for the model and useless as a decision rule where the
sleeve is mostly the base in disguise.

*Second, (3) is a forecast and it changes sign.* The gap ``a_p - sigma_p**2`` is zero
at ``a_p = sigma_p**2`` — **2.56%/yr at a 16% volatility** — and **negative below it**,
where selling the base to fund a sleeve is *better* than financing it. It is stated
above as "+2.44 pp/yr" using ``a_p = 5.0%``, which is an assumed forward equity
premium and not a measurement. A CAPE-implied forward premium sits below 2.56%, so the
sign of this module's central result is live rather than settled. **Anything quoting
the gap must quote the ``a_p`` that produced it.**

**The honest control, and it is unforgiving.** None of the above establishes that an
overlay beats simply levering the base to the same risk. At matched volatility
``sigma_total``, the levered base grows at
``r + sigma_total S_p - sigma_total**2 / 2`` and the overlay portfolio at
``r + A - sigma_total**2 / 2``. The variance terms are identical by construction, so

    **at matched volatility the higher Sharpe ratio wins, and nothing else
    matters.**                                                               (5)

Every figure this module produces must be read through (5). An overlay that raises
growth over the *unlevered* base while lowering the portfolio's Sharpe ratio has
bought its gain with leverage, and the charter requires that be labelled leveraged
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
    "MultiOverlay",
    "OverlayInputs",
    "OverlaySizing",
    "effective_breadth",
    "funding_rule_gap",
    "growth_optimal_overlay_vector",
    "growth_optimal_overlay_weight",
    "marginal_growth",
    "matched_volatility_verdict",
    "multi_overlay_growth_gain",
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
    """One diversifier bolted onto one base portfolio, all figures annual.

    Returns are **arithmetic excesses over cash**, not geometric and not total. The
    financing spread and fee are charged on notional, which is what a return-stacked
    fund actually does, and they are separate arguments because they move for
    different reasons: the spread is a market price and the fee is a contract.
    """

    base_excess_return: float
    base_volatility: float
    diversifier_excess_return: float
    diversifier_volatility: float
    correlation: float
    financing_spread: float = 0.0
    fee: float = 0.0

    def __post_init__(self) -> None:
        if self.base_volatility <= 0.0:
            raise ValueError(
                f"base volatility must be positive, got {self.base_volatility}"
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
        """``beta = rho sigma_d / sigma_p``, the diversifier's beta on the base."""
        return self.correlation * self.diversifier_volatility / self.base_volatility

    @property
    def covariance(self) -> float:
        """``rho sigma_p sigma_d``, the term that decides every bar in this module."""
        return (
            self.correlation * self.base_volatility * self.diversifier_volatility
        )

    @property
    def base_kelly_leverage(self) -> float:
        """``L_p* = a_p / sigma_p**2``, the base portfolio's growth-optimal exposure.

        The single number that decides whether the funding rule matters at all: by
        (3), the two bars coincide iff this equals 1.
        """
        return self.base_excess_return / self.base_volatility**2

    @property
    def base_sharpe(self) -> float:
        return self.base_excess_return / self.base_volatility

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


def marginal_growth(inputs: OverlayInputs, *, rule: str, base_exposure: float = 1.0) -> float:
    """``dg/dw`` at ``w = 0``: growth added per unit of the first sleeve dollar.

    ``rule`` selects (1) or (2) from the module docstring. ``base_exposure``
    generalises the overlay rule to the base held at ``L`` rather than 1 and is
    ignored under pro rata, where the base weight is what is being traded away.

    Positive means the first dollar of the sleeve raises growth. It says nothing
    about how much of it to hold — that is :func:`growth_optimal_overlay_weight` —
    and nothing about whether levering the base would have done better, which is
    :func:`matched_volatility_verdict` and is the question that decides.
    """
    if rule == FundingRule.OVERLAY:
        return inputs.net_excess_return - base_exposure * inputs.covariance
    if rule == FundingRule.PRO_RATA:
        return (
            inputs.net_excess_return
            - inputs.base_excess_return
            + inputs.base_volatility**2 * (1.0 - inputs.beta)
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
        return inputs.base_excess_return - inputs.base_volatility**2 * (
            1.0 - inputs.beta
        )
    raise ValueError(f"unknown funding rule {rule!r}")


def funding_rule_gap(*, base_excess_return: float, base_volatility: float) -> float:
    """``a_e - sigma_e**2 = sigma_e**2 (L_e* - 1)``: how much harder pro rata is.

    Equation (3). **It takes no diversifier argument, and that is the finding** — the
    penalty the zero-leverage rule imposes on every candidate sleeve is a property of
    the base position alone. It is positive iff the base's growth-optimal leverage
    exceeds 1, zero iff the constraint does not bind, and negative for a base already
    levered past its own optimum, where selling it to buy anything is an
    improvement.
    """
    if base_volatility <= 0.0:
        raise ValueError(
            f"base volatility must be positive, got {base_volatility}"
        )
    return base_excess_return - base_volatility**2


def sharpe_admission_threshold(
    inputs: OverlayInputs, *, base_exposure: float = 1.0
) -> float:
    """``L rho sigma_e``: the Sharpe ratio a diversifier must beat, equation (4).

    At ``base_exposure = inputs.base_kelly_leverage`` this returns
    ``rho * S_e``, the textbook tangency condition, and the two statements are the
    same statement. Below negative correlation it is negative, so a sleeve with a
    negative net expected excess return can still raise growth — a fact that should
    make any reader suspicious of the inputs rather than pleased with the result.
    """
    return base_exposure * inputs.correlation * inputs.base_volatility


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
    base_sharpe: float
    leverage_matched_growth_gain: float
    beats_leverage_matched_base: bool


def _portfolio_volatility(inputs: OverlayInputs, weight: float) -> float:
    variance = (
        inputs.base_volatility**2
        + 2.0 * weight * inputs.covariance
        + weight**2 * inputs.diversifier_volatility**2
    )
    if variance <= 0.0:
        raise ValueError("portfolio variance is non-positive; inputs are inconsistent")
    return math.sqrt(variance)


def matched_volatility_verdict(inputs: OverlayInputs, *, weight: float) -> OverlaySizing:
    """The overlay against the base levered to the same volatility — equation (5).

    This is the control the charter makes mandatory: *"A strategy that beats
    VTI only by taking more equity beta must be labelled as leveraged beta, not
    alpha."* Because both portfolios are held at the same variance, the ``-V/2`` term
    is common and the comparison collapses to Sharpe ratios. ``growth_gain`` is
    measured against the **unlevered** base and ``leverage_matched_growth_gain``
    against the base levered to ``sigma_total / sigma_p``; the second is the honest
    one and is the smaller of the two whenever the overlay's own Sharpe is lower.
    """
    volatility = _portfolio_volatility(inputs, weight)
    excess = inputs.base_excess_return + weight * inputs.net_excess_return
    portfolio_sharpe = excess / volatility
    levered_excess = volatility * inputs.base_sharpe
    return OverlaySizing(
        weight=weight,
        growth_gain=overlay_growth_gain(inputs, weight=weight),
        portfolio_volatility=volatility,
        portfolio_sharpe=portfolio_sharpe,
        base_sharpe=inputs.base_sharpe,
        leverage_matched_growth_gain=excess - levered_excess,
        beats_leverage_matched_base=portfolio_sharpe > inputs.base_sharpe,
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
    exactly as it does for the base. Use
    :func:`portfolio_edge.studies.equity_share.plug_in_growth_cost` for it.

    **The Sharpe ratio that governs the shrinkage is the marginal one**,
    ``(a_net - rho sigma_p sigma_d) / sigma_d``, not the diversifier's standalone
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


# --------------------------------------------------------------------------------
# 5. Many overlays at once, which is where breadth is actually earned
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class MultiOverlay:
    """``k`` financed overlays on one base, with a full covariance matrix.

    The single-sleeve results above generalise exactly. Write ``e`` for the vector of
    marginal edges ``a_net_i - cov(d_i, base)`` and ``Sigma`` for the overlays'
    covariance matrix among themselves. Growth added by a notional vector ``w`` is

        g(w) - g(0)  =  w'e - w' Sigma w / 2,

    maximised at ``w* = Sigma^-1 e`` with peak value ``e' Sigma^-1 e / 2``. Both are
    the one-sleeve formulas with the scalar division replaced by a solve.

    **Why breadth pays, stated exactly.** Take ``k`` overlays with identical edge
    ``e``, identical volatility ``sigma_d`` and mutual correlation ``rho_dd``. Then
    ``Sigma = sigma_d**2 [(1 - rho_dd) I + rho_dd J]`` and the peak gain is

        k e**2 / (2 sigma_d**2 (1 + (k - 1) rho_dd)).

    At ``rho_dd = 0`` this is **``k`` times the single-sleeve peak**: the optimal
    total notional grows with ``k``, and so does the growth it buys, because the
    variance penalty per unit of total notional falls as ``1/k``. At ``rho_dd = 1``
    the bracket is ``k``, the expression collapses to the single-sleeve value, and
    ``k`` copies of one strategy are one strategy.

    The denominator's ``1 + (k - 1) rho_dd`` is why the charter insists on
    *effective* breadth rather than a count of tickers, and it is unforgiving: at
    ``rho_dd = 0.3``, ten sleeves buy ``10 / 3.7 = 2.7`` times one sleeve, not ten.
    **Correlation among the diversifiers, not their number, is what is being
    bought**, and it is the input estimated worst.

    Nothing here weakens the honest control. ``Sigma`` and ``e`` are forecasts, the
    solve amplifies error in ``Sigma`` without limit as it approaches singularity,
    and the matched-volatility comparison of equation (5) still decides.
    """

    net_excess_returns: tuple[float, ...]
    covariance_with_base: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        size = len(self.net_excess_returns)
        if size == 0:
            raise ValueError("need at least one overlay")
        if len(self.covariance_with_base) != size:
            raise ValueError("covariance_with_base must match net_excess_returns")
        if len(self.covariance) != size or any(
            len(row) != size for row in self.covariance
        ):
            raise ValueError(f"covariance must be {size} by {size}")
        for i in range(size):
            for j in range(size):
                if self.covariance[i][j] != self.covariance[j][i]:
                    raise ValueError("covariance must be symmetric")

    @property
    def marginal_edges(self) -> tuple[float, ...]:
        """``e_i = a_net_i - cov(d_i, base)``: equation (1), one entry per overlay."""
        return tuple(
            net - cov
            for net, cov in zip(
                self.net_excess_returns, self.covariance_with_base, strict=True
            )
        )


def _solve(
    matrix: tuple[tuple[float, ...], ...], vector: tuple[float, ...]
) -> list[float]:
    """Gauss-Jordan with partial pivoting, kept explicit and dependency-free."""
    size = len(vector)
    augmented = [
        [*row, value] for row, value in zip(matrix, vector, strict=True)
    ]
    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(augmented[r][column]))
        if abs(augmented[pivot][column]) < 1e-14:
            raise ValueError("covariance matrix is singular to working precision")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column] / augmented[column][column]
            for k in range(column, size + 1):
                augmented[row][k] -= factor * augmented[column][k]
    return [augmented[i][size] / augmented[i][i] for i in range(size)]


def growth_optimal_overlay_vector(overlays: MultiOverlay) -> tuple[float, ...]:
    """``w* = Sigma^-1 e``, the unshrunk growth-optimal notional in each overlay.

    A plug-in optimum built from forecasts, and the matrix solve makes it more
    fragile than its scalar counterpart rather than less. Read a large entry as a
    statement about the covariance estimate, not about the strategy.
    """
    return tuple(_solve(overlays.covariance, overlays.marginal_edges))


def multi_overlay_growth_gain(
    overlays: MultiOverlay, *, weights: tuple[float, ...]
) -> float:
    """``w'e - w' Sigma w / 2``, exactly."""
    edges = overlays.marginal_edges
    if len(weights) != len(edges):
        raise ValueError("weights must match the number of overlays")
    linear = sum(w * e for w, e in zip(weights, edges, strict=True))
    quadratic = sum(
        weights[i] * overlays.covariance[i][j] * weights[j]
        for i in range(len(weights))
        for j in range(len(weights))
    )
    return linear - 0.5 * quadratic


def effective_breadth(*, count: int, mutual_correlation: float) -> float:
    """``k / (1 + (k - 1) rho_dd)``: how many independent sleeves ``k`` sleeves are.

    The multiplier on the single-sleeve peak growth gain when every overlay has the
    same edge, volatility and mutual correlation. It equals ``k`` at zero correlation
    and 1 at perfect correlation, and it is the quantity the charter means
    by effective breadth.

    It has no upper bound as ``rho_dd`` goes negative, which is a property of the
    equicorrelated model rather than of markets: ``rho_dd`` cannot fall below
    ``-1/(k-1)`` without the correlation matrix ceasing to be positive semi-definite,
    and the expression diverges exactly at that boundary. The function raises there
    rather than returning a number a reader could quote.
    """
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count}")
    if not -1.0 <= mutual_correlation <= 1.0:
        raise ValueError(f"correlation must lie in [-1, 1], got {mutual_correlation}")
    if count > 1 and mutual_correlation <= -1.0 / (count - 1):
        raise ValueError(
            f"mutual correlation {mutual_correlation} is at or below -1/(k-1) for "
            f"k={count}, where the correlation matrix is not positive semi-definite"
        )
    return count / (1.0 + (count - 1) * mutual_correlation)
