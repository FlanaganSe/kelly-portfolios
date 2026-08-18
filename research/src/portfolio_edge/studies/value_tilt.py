"""What a long-only value tilt is worth, and the double count that made it look smaller.

Why this module exists
----------------------
``docs/research/portfolio-recommendation.md`` §5 valued a 20%-of-portfolio small-value
tilt with the chain ``weight x loading x capture x premium - cost``. Three of those four
terms are measured quantities. The product of the middle two is **not a quantity at
all**, because ``loading`` and ``capture`` are two estimators of the same thing, and
multiplying them applies the long-only discount twice.

The identity, which is exact
----------------------------
Let ``L`` be a long-only portfolio and ``B`` a benchmark, both total returns on the same
months. Experiment 007 defines the capture fraction as

    c  =  mean(L - B) / mean(HML).

Regress the same spread ``L - B`` on the same factors::

    L - B  =  a  +  h * HML  +  sum_{k != HML} b_k * f_k  +  e,

with ``mean(e) = 0`` by construction. Taking means and dividing by ``mean(HML)``,

    c  =  h  +  ( a + sum_{k != HML} b_k * mean(f_k) ) / mean(HML).          (C)

**The capture fraction is the HML loading plus a residue.** It is not a multiplier that
converts a loading into a delivered exposure; it is a second, noisier measurement of the
same exposure, carrying every other factor's contribution and the spread's alpha in its
numerator. :func:`capture_from_regression` computes (C) and
``_value_tilt_tables`` verifies it against Ken French's own six portfolios, where it
holds to machine precision.

The consequence for any budget
------------------------------
A fund's HML regression coefficient is estimated on that fund's realised excess return.
A long-only fund cannot load 1.0 on a long-short factor, and its coefficient already says
so: AVUV's +0.537 *is* its delivered exposure, not a gross exposure awaiting a haircut.
So

    edge  =  weight * (h_fund - h_benchmark) * premium  -  weight * cost

and there is no capture term. :func:`sleeve_edge` refuses a capture argument outright
rather than accepting one and warning, in the tradition of
``studies/outperformance_horizon.aggregate()`` raising rather than summing across
benchmarks.

What the loading form also fixes
--------------------------------
Experiment 007's central finding is that five defensible benchmarks give capture
fractions spanning 0.846, so no page may quote one without its benchmark. That
dispersion is a property of the *ratio*, not of the exposure. Regress the same long-only
value halves against the market instead of against the size-neutral six and the HML
coefficient moves from +0.489 to +0.699 while an **SMB** coefficient of +0.452 appears —
the "size premium wearing a value label" the capture ratio silently books as value. A
loading is taken against a factor, so the only benchmark choice left is which fund is
sold to buy the sleeve, and that enters as ``h_benchmark``, a small measured number.

What this module is not
-----------------------
It is arithmetic over stated inputs and contains no market data and no cache access, in
the tradition of :mod:`overlay_growth` and :mod:`equity_share`.
:mod:`portfolio_edge.studies._value_tilt_tables` is the one file that reads the cache.
Nothing here promotes any product: decision 0002 caps every product result at
``exploratory``, and a premium that is not reliably signed makes every net figure below a
conditional statement about a premium rather than a measurement of a tilt.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

__all__ = [
    "CaptureDecomposition",
    "CaptureDoubleCountError",
    "TiltInputs",
    "TiltVerdict",
    "capture_from_regression",
    "certainty_equivalent_contribution",
    "marginal_growth_contribution",
    "portfolio_tracking_error",
    "sleeve_edge",
    "substitution_variance_change",
    "terminal_wealth_multiple",
    "tilt_verdict",
    "turnover_cost_percent",
    "variance_drag",
]

PERCENT_PER_BASIS_POINT: Final = 0.01
"""One basis point in the percent-per-year units every figure here is stated in."""

PERCENT_PER_UNIT: Final = 100.0
"""The conversion every variance term here needs, and the one easy to forget.

``g = A - V / 2`` holds with ``A`` and ``V`` in the same *decimal* units. Everything in
this module is in percent, and a variance stated in percent-squared is 100 times too
large for that formula: ``g_pct = A_pct - sigma_pct**2 / 200``. Dropping the 100 makes a
21 bp growth contribution read as -21 pp/yr, which is how this was caught.
"""


class CaptureDoubleCountError(ValueError):
    """Raised when a caller multiplies a regression loading by a capture fraction.

    The two measure the same quantity — see identity (C) in the module docstring — so
    their product is not a delivered exposure. This is the error
    ``portfolio-recommendation.md`` §5 made, and it cost a factor of about two.
    """


# --------------------------------------------------------------------------------
# 1. The identity: a capture fraction is a loading plus a residue
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CaptureDecomposition:
    """Identity (C), with each term kept so a caller cannot quote the ratio alone."""

    capture: float
    """``mean(L - B) / mean(HML)``: the ratio Experiment 007 measures."""

    hml_loading: float
    """``h``: the same spread's HML regression coefficient. The exposure."""

    residue: float
    """``capture - hml_loading``: everything the ratio books as value and is not."""

    alpha_contribution: float
    """``a / mean(HML)``: the part of the residue that is the spread's own alpha."""

    other_factor_contribution: float
    """``sum_{k != HML} b_k mean(f_k) / mean(HML)``: the part that is other factors."""

    long_only_excess: float
    """``mean(L - B)``, in the units the factor means were supplied in."""

    def share_that_is_exposure(self) -> float:
        """``h / capture``: how much of the ratio is the thing it is taken to measure."""
        if self.capture == 0.0:
            raise ZeroDivisionError("capture is zero; the share is undefined")
        return self.hml_loading / self.capture


def capture_from_regression(
    *,
    hml_loading: float,
    alpha: float,
    other_loadings: Mapping[str, float],
    factor_means: Mapping[str, float],
    hml_premium: float,
) -> CaptureDecomposition:
    """Identity (C): rebuild a capture fraction from the regression that explains it.

    ``alpha`` and every mean are in the same units per period (this repository states
    both in percent per year). ``other_loadings`` must not contain ``HML``, and every
    key in it must have a mean in ``factor_means``; a missing mean is a silently
    dropped term, which is exactly how the residue would go unnoticed.

    Raises ``ZeroDivisionError`` when ``hml_premium`` is zero — a capture fraction is
    undefined when its denominator is, which is why Experiment 007 marks every era whose
    premium is not reliably signed UNSTABLE.
    """
    if "HML" in other_loadings:
        raise ValueError("other_loadings carries HML; pass it as hml_loading instead")
    missing = sorted(set(other_loadings) - set(factor_means))
    if missing:
        raise ValueError(f"no mean supplied for {', '.join(missing)}")
    if hml_premium == 0.0:
        raise ZeroDivisionError(
            "the HML premium is zero, so a capture fraction has no value; report the "
            "long-only excess in percent per year instead"
        )
    other = sum(loading * factor_means[name] for name, loading in other_loadings.items())
    alpha_share = alpha / hml_premium
    other_share = other / hml_premium
    long_only_excess = alpha + hml_loading * hml_premium + other
    return CaptureDecomposition(
        capture=long_only_excess / hml_premium,
        hml_loading=hml_loading,
        residue=alpha_share + other_share,
        alpha_contribution=alpha_share,
        other_factor_contribution=other_share,
        long_only_excess=long_only_excess,
    )


# --------------------------------------------------------------------------------
# 2. The tilt itself
# --------------------------------------------------------------------------------


def turnover_cost_percent(
    *, one_sided_turnover_percent: float, coefficient: float
) -> float:
    """``k * turnover`` basis points, returned in percent per year.

    The calibration is :mod:`portfolio_edge.core.costs`: ``cost_bp ~= k * turnover_pct``
    over the same period, with ``k`` from 1.0 (patient limit orders in liquid names) to
    1.7 (market orders, full universe). The turnover a fund files under Item 3 of Form
    N-1A is ``min(purchases, sales) / average net assets``, which is the one-sided
    measure this rule wants, and it **excludes an ETF's in-kind creations and
    redemptions** — the part of an ETF's rotation that costs the fund nothing.
    """
    if one_sided_turnover_percent < 0.0:
        raise ValueError(f"turnover cannot be negative, got {one_sided_turnover_percent}")
    if coefficient < 0.0:
        raise ValueError(f"the turnover coefficient cannot be negative, got {coefficient}")
    return coefficient * one_sided_turnover_percent * PERCENT_PER_BASIS_POINT


@dataclass(frozen=True, slots=True)
class TiltInputs:
    """One long-only factor tilt against one incumbent fund, all figures percent per year.

    ``weight`` is the fraction of the whole portfolio moved out of the incumbent and into
    the tilt product, so this is a **substitution** and never an overlay: nothing is
    financed and total exposure does not change.

    Every cost is charged **incrementally over the incumbent**, because the incumbent's
    own fee and turnover are paid either way. Charging the tilt's gross fee against a
    zero baseline is the same double count in a different place.
    """

    weight: float
    fund_hml_loading: float
    benchmark_hml_loading: float
    hml_premium: float
    fund_fee: float
    benchmark_fee: float
    fund_turnover_percent: float
    benchmark_turnover_percent: float
    turnover_coefficient: float
    fund_volatility: float
    benchmark_volatility: float
    correlation: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"weight must lie in [0, 1], got {self.weight}")
        if self.fund_volatility <= 0.0 or self.benchmark_volatility <= 0.0:
            raise ValueError("both volatilities must be positive")
        if not -1.0 <= self.correlation <= 1.0:
            raise ValueError(f"correlation must lie in [-1, 1], got {self.correlation}")

    @property
    def delivered_loading(self) -> float:
        """``h_fund - h_benchmark``: the exposure the swap actually buys.

        The incumbent is not exposure-free. VTI's own FF5+UMD HML loading over
        2020-01..2025-12 is +0.0247, small but measured, and subtracting it is the only
        benchmark choice this chain contains.
        """
        return self.fund_hml_loading - self.benchmark_hml_loading

    @property
    def incremental_cost(self) -> float:
        """Fee plus trading cost, both net of what the incumbent already charges."""
        fee = self.fund_fee - self.benchmark_fee
        trading = turnover_cost_percent(
            one_sided_turnover_percent=self.fund_turnover_percent,
            coefficient=self.turnover_coefficient,
        ) - turnover_cost_percent(
            one_sided_turnover_percent=self.benchmark_turnover_percent,
            coefficient=self.turnover_coefficient,
        )
        return fee + trading

    @property
    def sleeve_tracking_error(self) -> float:
        """``sd(fund - benchmark)``, from the two volatilities and their correlation."""
        variance = (
            self.fund_volatility**2
            + self.benchmark_volatility**2
            - 2.0 * self.correlation * self.fund_volatility * self.benchmark_volatility
        )
        return math.sqrt(max(variance, 0.0))


def sleeve_edge(inputs: TiltInputs, *, capture: float | None = None) -> float:
    """``(h_fund - h_benchmark) * premium - incremental cost``, per dollar of sleeve.

    ``capture`` exists only to be refused. A regression loading already contains the
    long-only discount, so multiplying by a capture fraction applies it twice; see
    identity (C). Pass nothing.
    """
    if capture is not None:
        raise CaptureDoubleCountError(
            "a capture fraction may not multiply a regression loading: identity (C) "
            "shows they measure the same exposure, so the product discounts it twice. "
            f"Drop the capture of {capture} and use the loading alone."
        )
    return inputs.delivered_loading * inputs.hml_premium - inputs.incremental_cost


def portfolio_tracking_error(inputs: TiltInputs) -> float:
    """``weight * sd(fund - benchmark)``: what the swap does to the whole portfolio.

    **Not** the tracking error of the fund against a fitted cheap replication, which is
    what Experiment 002 reports and what §5 previously borrowed. A replication basis is
    not what the investor sells.
    """
    return inputs.weight * inputs.sleeve_tracking_error


def substitution_variance_change(inputs: TiltInputs) -> float:
    """``V(w) - V(0)`` for holding ``1 - w`` of the incumbent and ``w`` of the fund.

    In **percent-squared per year**, because the volatilities are in percent. Exact, and
    independent of either expected return, which is why the growth contribution below
    needs no forecast of the equity premium.

    It is positive for any tilt into a more volatile fund at a correlation below one,
    and it is the term the old chain omitted entirely: a substitution that raises
    portfolio variance pays for its arithmetic edge out of its own geometric return.
    """
    weight = inputs.weight
    covariance = inputs.correlation * inputs.fund_volatility * inputs.benchmark_volatility
    tilted = (
        (1.0 - weight) ** 2 * inputs.benchmark_volatility**2
        + 2.0 * weight * (1.0 - weight) * covariance
        + weight**2 * inputs.fund_volatility**2
    )
    return tilted - inputs.benchmark_volatility**2


def variance_drag(inputs: TiltInputs, *, gamma: float) -> float:
    """``gamma (V(w) - V(0)) / 2``, converted from percent-squared into percent per year.

    At ``gamma = 1`` this is the geometric drag in ``g = A - V/2``; at ``gamma > 1`` it is
    the CRRA risk charge. Keeping one function for both is deliberate, because the only
    difference between the growth answer and the certainty-equivalent answer is this
    coefficient, and decision 0008 exists because that difference was being read as a
    result about a sleeve.
    """
    if gamma <= 0.0:
        raise ValueError(f"gamma must be positive, got {gamma}")
    return 0.5 * gamma * substitution_variance_change(inputs) / PERCENT_PER_UNIT


def marginal_growth_contribution(inputs: TiltInputs) -> float:
    """``w * edge - (V(w) - V(0)) / 200``: what the swap adds to geometric growth.

    ``g = r + A - V/2``, the lognormal approximation
    :mod:`portfolio_edge.studies.overlay_growth` uses and
    ``docs/decisions/0008-growth-decides-crra-reports.md`` makes deciding. Under a
    substitution the arithmetic-return change is exactly ``w * edge``, so the incumbent's
    own expected return cancels and does not have to be forecast.

    This is the **matched-volatility** reading of equation (5) rather than the admission
    rule of equation (4): a value tilt sits inside equity at a correlation around 0.85,
    far above the ``|rho| = 0.5`` at which ``overlay_growth`` says (4) stops being a
    decision rule.
    """
    return inputs.weight * sleeve_edge(inputs) - variance_drag(inputs, gamma=1.0)


def certainty_equivalent_contribution(inputs: TiltInputs, *, gamma: float) -> float:
    """``w * edge - gamma (V(w) - V(0)) / 200``: the CRRA certainty equivalent beside it.

    Decision 0008 requires this to be **reported** and not to decide, because on a
    certainty-equivalent metric a candidate is paid for reducing risk and the payment can
    exceed the materiality threshold on its own. At ``gamma = 1`` it is the growth rate.
    """
    return inputs.weight * sleeve_edge(inputs) - variance_drag(inputs, gamma=gamma)


def terminal_wealth_multiple(*, growth_contribution: float, years: float) -> float:
    """``exp(g * T)``: terminal wealth relative to holding the incumbent throughout.

    ``growth_contribution`` is in percent per year, as everything else here is.
    """
    if years < 0.0:
        raise ValueError(f"years cannot be negative, got {years}")
    return math.exp(growth_contribution / 100.0 * years)


# --------------------------------------------------------------------------------
# 3. Everything one set of inputs decides, so a caller cannot quote half
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TiltVerdict:
    """The growth answer and the demonstrability answer, side by side and labelled."""

    weight: float
    delivered_loading: float
    hml_premium: float
    incremental_cost: float
    sleeve_edge_percent: float
    portfolio_edge_basis_points: float
    portfolio_tracking_error_basis_points: float
    growth_contribution_percent: float
    certainty_equivalent_percent: float
    terminal_wealth_multiple_30y: float


def tilt_verdict(inputs: TiltInputs, *, gamma: float = 3.0, years: float = 30.0) -> TiltVerdict:
    """Every figure one set of tilt inputs produces.

    The edge and the tracking error answer *"can an investor ever show this worked"*.
    The growth contribution and the terminal wealth multiple answer *"did it help"*.
    They are different questions and a positive answer to the second is compatible with
    a negative answer to the first, which is the whole reason both are returned together.
    """
    edge = sleeve_edge(inputs)
    growth = marginal_growth_contribution(inputs)
    return TiltVerdict(
        weight=inputs.weight,
        delivered_loading=inputs.delivered_loading,
        hml_premium=inputs.hml_premium,
        incremental_cost=inputs.incremental_cost,
        sleeve_edge_percent=edge,
        portfolio_edge_basis_points=inputs.weight * edge / PERCENT_PER_BASIS_POINT,
        portfolio_tracking_error_basis_points=(
            portfolio_tracking_error(inputs) / PERCENT_PER_BASIS_POINT
        ),
        growth_contribution_percent=growth,
        certainty_equivalent_percent=certainty_equivalent_contribution(inputs, gamma=gamma),
        terminal_wealth_multiple_30y=terminal_wealth_multiple(
            growth_contribution=growth, years=years
        ),
    )


if __name__ == "__main__":  # pragma: no cover - regenerates the published tilt tables
    from portfolio_edge.studies._value_tilt_tables import main

    main()
