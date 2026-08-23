"""Pricing a tilt candidate against the portfolio that already exists.

Why this module exists
----------------------
A fund shelf invites the wrong question. It lists products side by side with a loading
and a fee, and the reader picks the best-looking row. But a portfolio is not a shelf: a
tilt that duplicates an exposure already held adds nothing however good it looks alone,
and a tilt whose cost is paid in turnover rather than in fee looks cheap on the row and
is not. This module is the arithmetic for the question the shelf cannot ask — *what does
this candidate add, given what is already owned, after everything it actually costs?*

Three guards, and they are the reason this is a module rather than four lines in a table
script.

**A capture fraction may not multiply a loading.** Reused wholesale from
:mod:`portfolio_edge.studies.value_tilt`, which owns the identity: a regression loading
already contains the long-only discount, so a capture fraction beside it discounts twice.
:func:`sleeve_edge` refuses the argument rather than documenting the trap.

**A fee is not a net cost.** Cost is ``fee - securities lending``, and several funds on
this repository's shelf have no lending figure at all. :attr:`FundCost.net_cost_bp`
therefore *raises* where the lending income was never read, and
:meth:`FundCost.cost_bracket_bp` returns a low-high pair instead — so a caller who has
only a fee reports a range with the fee at one end, and never a net cost it does not have.

**Two after-tax figures from different calendar periods do not subtract.** Form N-1A's
standardised after-tax table is dated, and funds update on their own fiscal calendars, so
one fund's ten years to 2024-12 and another's to 2025-12 are different questions.
:func:`incremental_distribution_tax_drag` raises on mismatched periods, in the tradition
of ``studies.outperformance_horizon.aggregate()`` refusing to add results measured against
different benchmarks.

What this module is not
-----------------------
It estimates nothing. Every loading, premium, correlation and tracking error is supplied
by the caller; :mod:`portfolio_edge.studies._untested_tilts_tables` is the half that reads
filings and fits regressions. Everything it computes is `exploratory`: the delivered
exposures behind any real use of it come from six-year windows, which is shorter than one
value cycle.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from portfolio_edge.studies.stacking import (
    MDE_TO_STANDARD_ERROR,
    MarginalVerdict,
    Sleeve,
    marginal_contribution,
)
from portfolio_edge.studies.value_tilt import CaptureDoubleCountError, turnover_cost_percent

__all__ = [
    "TURNOVER_COEFFICIENT_HIGH",
    "TURNOVER_COEFFICIENT_LOW",
    "AfterTaxReturns",
    "FundCost",
    "MismatchedTaxPeriodError",
    "UnmeasuredCostError",
    "UnpricedFactorError",
    "annualise_monthly",
    "edge_standard_error",
    "effective_bets_of_pair",
    "incremental_cost_bracket",
    "incremental_distribution_tax_drag",
    "marginal_tilt",
    "portfolio_return_change",
    "sleeve_edge",
    "tracking_error_from_monthly",
]

#: The calibration bracket ``portfolio_edge.core.costs`` supplies for turning a filed
#: portfolio turnover rate into a trading cost: 1.0 for patient limit orders in liquid
#: names, 1.7 for market orders across a full universe. Both ends are reported everywhere
#: this module is used, because on a fund turning over more than once a year the choice
#: between them is larger than the whole edge being measured.
TURNOVER_COEFFICIENT_LOW: Final = 1.0
TURNOVER_COEFFICIENT_HIGH: Final = 1.7

_BASIS_POINTS_PER_PERCENT: Final = 100.0


class UnmeasuredCostError(ValueError):
    """A net cost was requested for a fund whose securities lending was never read."""


class UnpricedFactorError(ValueError):
    """A delivered exposure was supplied for a factor with no premium beside it."""


class MismatchedTaxPeriodError(ValueError):
    """Two standardised after-tax tables covering different periods were about to subtract."""


@dataclass(frozen=True, slots=True, kw_only=True)
class FundCost:
    """What one fund costs to hold, from its own filings and never from memory.

    ``fee_bp`` is total annual fund operating expenses from the fee table.
    ``securities_lending_bp`` is net lending income from Form N-CEN, and ``None`` means
    nobody read it — not that it is zero. ``turnover_percent`` is Item 3 of Form N-1A,
    which is ``min(purchases, sales) / average net assets`` and already excludes an ETF's
    in-kind creations and redemptions.
    """

    ticker: str
    fee_bp: float
    securities_lending_bp: float | None
    turnover_percent: float | None

    def __post_init__(self) -> None:
        if self.fee_bp < 0.0:
            raise ValueError(f"{self.ticker}: a fee cannot be negative, got {self.fee_bp}")
        if self.turnover_percent is not None and self.turnover_percent < 0.0:
            raise ValueError(
                f"{self.ticker}: turnover cannot be negative, got {self.turnover_percent}"
            )

    @property
    def net_cost_bp(self) -> float:
        """``fee - securities lending``, or a refusal.

        Raises rather than falling back to the fee. A fee quoted where a net cost belongs
        is a different number wearing the same units, and the funds it is quoted for are
        exactly the ones whose lending income was never measured.
        """
        if self.securities_lending_bp is None:
            raise UnmeasuredCostError(
                f"{self.ticker}: no securities-lending income was read for this fund, so "
                "its net cost is unknown. Use cost_bracket_bp() and report a range with "
                f"the {self.fee_bp:.2f} bp fee at one end, or read Form N-CEN."
            )
        return self.fee_bp - self.securities_lending_bp

    def cost_bracket_bp(self) -> tuple[float, float]:
        """``(low, high)`` cost in basis points a year.

        The high end is always the fee, which is an upper bound on holding cost because
        securities lending can only reduce it. The low end is the measured net cost where
        Form N-CEN was read and the fee again where it was not, so an unmeasured fund
        carries a collapsed bracket sitting at its own upper bound. That is the direction
        that cannot flatter a candidate.
        """
        if self.securities_lending_bp is None:
            return self.fee_bp, self.fee_bp
        return self.net_cost_bp, self.fee_bp

    @property
    def lending_was_read(self) -> bool:
        """Whether a net cost exists for this fund at all."""
        return self.securities_lending_bp is not None


@dataclass(frozen=True, slots=True, kw_only=True)
class AfterTaxReturns:
    """One row of Form N-1A's standardised after-tax table, with the period it covers.

    ``period`` is the table's own heading, e.g. ``"10 years to 2024-12"``. It is carried
    because the whole point of :func:`incremental_distribution_tax_drag` is that two rows
    from different periods are not comparable, and a period that lives in a comment cannot
    be checked.
    """

    ticker: str
    period: str
    before_tax: float
    after_tax_on_distributions: float

    @property
    def distribution_drag(self) -> float:
        """``before tax - after taxes on distributions``, percentage points a year.

        This is what the fund's own distributions cost a taxable holder at the highest
        historical individual federal rates, which is the assumption Form N-1A fixes. It
        is *not* the tax cost of eventually selling, and it says nothing about a holder in
        a sheltered account.
        """
        return self.before_tax - self.after_tax_on_distributions


def incremental_distribution_tax_drag(
    *, fund: AfterTaxReturns, incumbent: AfterTaxReturns
) -> float:
    """How much more the candidate's distributions cost than the incumbent's, pp/yr.

    Negative means the candidate is the more tax-efficient of the two. Raises when the two
    tables cover different periods, because a fund's fiscal calendar decides when its table
    is refreshed and subtracting across that boundary measures the market, not the funds.
    """
    if fund.period != incumbent.period:
        raise MismatchedTaxPeriodError(
            f"{fund.ticker} reports {fund.period!r} and {incumbent.ticker} reports "
            f"{incumbent.period!r}. Standardised after-tax returns from different periods "
            "do not subtract; find both funds' tables for one period first."
        )
    return fund.distribution_drag - incumbent.distribution_drag


def incremental_cost_bracket(
    *,
    fund: FundCost,
    incumbent: FundCost,
    turnover_coefficient_low: float = TURNOVER_COEFFICIENT_LOW,
    turnover_coefficient_high: float = TURNOVER_COEFFICIENT_HIGH,
) -> tuple[float, float]:
    """``(low, high)`` incremental holding cost over the incumbent, percent a year.

    Two sources of width, kept together because a reader who sees only one will mistake it
    for the whole uncertainty: the trading-cost coefficient's own 1.0-to-1.7 calibration
    range, and the fee-versus-net-cost gap wherever a fund's securities lending is unread.

    Turnover is charged only on the excess over the incumbent, and never negatively: a
    candidate that trades *less* than what it replaces gets no credit here, which is the
    conservative direction.
    """
    fund_low, fund_high = fund.cost_bracket_bp()
    incumbent_low, incumbent_high = incumbent.cost_bracket_bp()
    fee_low = (fund_low - incumbent_high) / _BASIS_POINTS_PER_PERCENT
    fee_high = (fund_high - incumbent_low) / _BASIS_POINTS_PER_PERCENT
    if fund.turnover_percent is None:
        raise UnmeasuredCostError(
            f"{fund.ticker}: no portfolio turnover was read, so its trading cost cannot "
            "be charged. Read Item 3 of the summary prospectus; a factor product's "
            "turnover has decided a verdict on this shelf before."
        )
    incumbent_turnover = incumbent.turnover_percent or 0.0
    excess = max(fund.turnover_percent - incumbent_turnover, 0.0)
    trading_low = turnover_cost_percent(
        one_sided_turnover_percent=excess, coefficient=turnover_coefficient_low
    )
    trading_high = turnover_cost_percent(
        one_sided_turnover_percent=excess, coefficient=turnover_coefficient_high
    )
    return fee_low + trading_low, fee_high + trading_high


def sleeve_edge(
    *,
    delivered: Mapping[str, float],
    premia: Mapping[str, float],
    incremental_cost: float,
    capture: float | None = None,
) -> float:
    """``sum_k (h_fund,k - h_incumbent,k) * premium_k - cost``, per dollar of sleeve.

    ``delivered`` is already the *difference* between the candidate's loading and the
    incumbent's, on one panel and one window. ``premia`` must price every factor in it:
    a missing entry raises rather than defaulting to zero, because a silent zero is a
    premium assumption made by an omission.

    ``capture`` exists only to be refused; see :class:`CaptureDoubleCountError`.
    """
    if capture is not None:
        raise CaptureDoubleCountError(
            "a capture fraction may not multiply a regression loading: the loading "
            "already contains the long-only discount, so the product applies it twice. "
            f"Drop the capture of {capture} and use the loading alone."
        )
    missing = sorted(set(delivered) - set(premia))
    if missing:
        raise UnpricedFactorError(
            f"no premium was supplied for {missing}. A factor left out of the premium map "
            "is charged at zero, which is an assumption; state it explicitly."
        )
    gross = sum(loading * premia[factor] for factor, loading in delivered.items())
    return gross - incremental_cost


def edge_standard_error(
    *, delivered: Mapping[str, float], minimum_detectable_premia: Mapping[str, float]
) -> float:
    """The standard error on :func:`sleeve_edge`, from the premia's own published floors.

    ``minimum_detectable_premia`` are MDE80 figures in percentage points a year; dividing
    by :data:`stacking.MDE_TO_STANDARD_ERROR` recovers the standard error behind each.
    The terms are summed rather than added in quadrature, which is the *perfectly
    correlated* bound and therefore the widest of the two defensible readings. It is the
    right default here: the premia are estimated on overlapping months of the same files,
    so treating their errors as independent would flatter every candidate.

    Only premium uncertainty enters. The loadings have sampling error too, and the cost
    bracket has its own width; both are reported separately rather than folded in.
    """
    missing = sorted(set(delivered) - set(minimum_detectable_premia))
    if missing:
        raise UnpricedFactorError(f"no minimum detectable premium was supplied for {missing}")
    return sum(
        abs(loading) * minimum_detectable_premia[factor] / MDE_TO_STANDARD_ERROR
        for factor, loading in delivered.items()
    )


def portfolio_return_change(*, weight: float, edge: float) -> float:
    """``weight * edge``: what a sleeve at ``weight`` does to the whole portfolio's return.

    The one conversion between "per dollar of sleeve" and "per year of portfolio", kept as
    a named function because every headline number in the owning page is this product and
    quoting a sleeve edge as a portfolio figure overstates it by ``1 / weight``.
    """
    if not 0.0 <= weight <= 1.0:
        raise ValueError(f"weight must lie in [0, 1], got {weight}")
    return weight * edge


def marginal_tilt(
    *,
    ticker: str,
    weight: float,
    candidate_edge: float,
    candidate_tracking_error: float,
    held_edge: float,
    held_tracking_error: float,
    correlation_to_held: float,
) -> MarginalVerdict:
    """What the candidate adds *given what is already owned*.

    Delegates to :func:`stacking.marginal_contribution` so the repository keeps one
    definition of ``alpha_k / omega_k``. ``candidate_edge`` and
    ``candidate_tracking_error`` are per dollar of the candidate sleeve; ``held_edge`` and
    ``held_tracking_error`` describe the *whole* existing active position at its actual
    weights. ``MarginalVerdict.alpha`` is then the candidate's edge net of what the
    portfolio already supplies, and it is the number a weight should be sized from.
    """
    return marginal_contribution(
        label=ticker,
        candidate=Sleeve(
            label=ticker,
            weight=weight,
            edge=candidate_edge,
            tracking_error=candidate_tracking_error,
        ),
        held_edge=held_edge,
        held_tracking_error=held_tracking_error,
        correlation_to_held=correlation_to_held,
    )


def effective_bets_of_pair(correlation: float) -> float:
    """``2 / (1 + rho)``: how many independent bets two equal sleeves are worth.

    The two-sleeve case of ``k / (1 + (k-1) rho)``, which
    ``studies.overlay_growth.effective_breadth`` defines in general. Written out here
    because the momentum question this module was built for is exactly a two-sleeve
    question: US momentum beside developed-ex-US momentum is 2 tickers and, at the
    correlation measured between them, fewer than 2 bets.
    """
    if not -1.0 < correlation <= 1.0:
        raise ValueError(f"correlation must lie in (-1, 1], got {correlation}")
    return 2.0 / (1.0 + correlation)


def annualise_monthly(value: float) -> float:
    """A monthly figure in decimals to percentage points a year, arithmetically.

    ``value * 1200``. Arithmetic rather than geometric because every regression intercept
    and factor premium in this repository is an arithmetic monthly mean, and compounding
    one of them silently changes the estimand.
    """
    return value * 1200.0


def tracking_error_from_monthly(monthly_standard_deviation: float) -> float:
    """A monthly standard deviation in decimals to percentage points a year."""
    if monthly_standard_deviation < 0.0:
        raise ValueError("a standard deviation cannot be negative")
    return monthly_standard_deviation * math.sqrt(12.0) * 100.0


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._untested_tilts_tables import main

    main()
