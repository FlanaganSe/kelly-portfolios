"""Structural and tax-aware edges: the contractual class, sized from stated rates.

This module is the executable record behind
``docs/research/structural-and-tax-edges.md``. It contains no market data, no
forecast and no randomness. Every number it produces is a function of a *stated tax
regime* and a *stated portfolio assumption*, both of which are arguments rather than
constants, because tax law is jurisdiction-specific and dated and the framework
requires it to be modelled as an input.

**Why this class of edge is different.** The edge budget in
:mod:`portfolio_edge.studies.outperformance_horizon` separates *deterministic* lines —
an identity or a contract — from *probabilistic* ones. Everything here is in the first
class. A withholding tax that cannot be credited is not a bet on a market; it is a
subtraction that happens with certainty given the account, the domicile and the rate.
The uncertainty in these figures lives entirely in the **inputs** (which bracket, which
yield, which holding period), never in the **sign** of the outcome.

**The one identity that organises the whole module.** Consider a dollar compounding at
log growth ``g`` for ``H`` years. Tax reaches it through exactly three doors:

1. **A recurring levy on distributed income** — dividends, interest, capital-gain
   distributions, foreign withholding. Charged annually on a base the investor does not
   choose, it reduces the compounding rate itself and so costs ``rate x yield`` per year,
   compounded.
2. **A realisation levy on gains the investor chooses to realise.** Deferrable. Its cost
   is not the tax but the *loss of the interest-free loan* the deferred liability
   represents, which is why turnover, not the rate, is the decision variable.
3. **A terminal levy at disposal**, which is the full rate on liquidation, and **zero**
   under a basis step-up at death (26 U.S.C. §1014) or an outright charitable gift of
   appreciated long-term property (§170).

:func:`after_tax_path` implements all three in one loop, and every other function in the
module is a special case of it or a closed form checked against it. That is deliberate:
the failure mode of tax arithmetic is that each lever is computed with its own private
convention and the totals then do not add up.

**Scope.** US federal, individual investor, ``as of 2026-08-12``. State income tax is
excluded and is additive where it exists. Non-US investors face materially different
answers on every line — most sharply on the foreign tax credit, where a jurisdiction
without a credit mechanism converts §1 below from a location question into a pure cost.
Nothing here is personalised advice; it is a sizing exercise for a class of edge.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from portfolio_edge.studies.outperformance_horizon import (
    BASIS_POINT,
    Benchmark,
    Certainty,
)

AS_OF = "2026-08-12"
"""Every rate, threshold and yield in this module is stated as of this date."""

JURISDICTION = "US federal"
"""Rates below carry no state income tax. Nine US states levy none; the rest are
additive to every drag computed here, and two (California, New Jersey) additionally tax
health savings account earnings that are exempt federally."""


# --------------------------------------------------------------------------------------
# The tax regime: an argument, never a constant
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TaxRegime:
    """A dated, jurisdiction-stamped set of marginal rates.

    The framework's requirement is verbatim that tax law *"must be a dated
    jurisdiction-specific input, never a hardcoded financial truth"*. This dataclass is
    that input. Rates are marginal and expressed as decimals.

    ``net_investment_income`` is the US §1411 surtax, which applies on top of both the
    ordinary and the long-term rate above a modified-AGI threshold that is **not**
    inflation indexed, so the fraction of investors paying it rises every year by
    construction.
    """

    label: str
    jurisdiction: str
    as_of: str
    ordinary_income: float
    long_term_capital_gain: float
    net_investment_income: float

    def __post_init__(self) -> None:
        for name in (
            "ordinary_income",
            "long_term_capital_gain",
            "net_investment_income",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value < 1.0:
                raise ValueError(f"{self.label}: {name} must lie in [0, 1), got {value}")
        if self.long_term_capital_gain > self.ordinary_income:
            raise ValueError(
                f"{self.label}: a long-term rate above the ordinary rate inverts every "
                "conclusion in this module; state it deliberately in a new regime if a "
                "jurisdiction really does that"
            )
        if not self.as_of.strip() or not self.jurisdiction.strip():
            raise ValueError(f"{self.label}: a regime without a date and a jurisdiction is a trap")

    @property
    def ordinary(self) -> float:
        """All-in marginal rate on ordinary income, including the §1411 surtax."""
        return self.ordinary_income + self.net_investment_income

    @property
    def capital_gain(self) -> float:
        """All-in marginal rate on long-term capital gain, including the §1411 surtax."""
        return self.long_term_capital_gain + self.net_investment_income

    @property
    def qualified_dividend(self) -> float:
        """Qualified dividends are taxed at the long-term rate (26 U.S.C. §1(h)(11)).

        Conditional on the §1(h)(11)(B)(iii) holding period — more than 60 days within
        the 121-day window around the ex-dividend date — and on the payer being a US
        corporation or a qualified foreign corporation. A fund that fails the test on
        part of its book reports the shortfall as ordinary income, which is
        :meth:`ordinary` and not this rate.
        """
        return self.capital_gain

    @property
    def section_1256_blended(self) -> float:
        """``0.6 x long-term + 0.4 x ordinary``: 26 U.S.C. §1256(a)(3).

        The statute assigns the split *"without regard to the period for which the
        taxpayer has held such contract"*, so it is available on a position held for a
        single day. It is a rate reduction against ordinary treatment and a rate
        *increase* against deferred long-term treatment, and §1256(a)(1) forces annual
        mark-to-market, which removes deferral entirely. Both halves are priced in
        :func:`section_1256_comparison`.
        """
        return 0.6 * self.capital_gain + 0.4 * self.ordinary


TOP_BRACKET = TaxRegime(
    label="US top marginal bracket",
    jurisdiction=JURISDICTION,
    as_of=AS_OF,
    ordinary_income=0.37,
    long_term_capital_gain=0.20,
    net_investment_income=0.038,
)
"""37% ordinary / 20% long-term, both plus the 3.8% §1411 surtax: 40.8% and 23.8%.

The 37% top ordinary rate and the 20% top long-term rate were made permanent by the
2025 reconciliation act rather than expiring after 2025 as previously scheduled.
"""

UPPER_MIDDLE_BRACKET = TaxRegime(
    label="US upper-middle bracket",
    jurisdiction=JURISDICTION,
    as_of=AS_OF,
    ordinary_income=0.24,
    long_term_capital_gain=0.15,
    net_investment_income=0.0,
)
"""24% ordinary / 15% long-term, below the §1411 threshold. The modal affluent saver."""

ZERO_RATE_BRACKET = TaxRegime(
    label="US zero long-term-rate bracket",
    jurisdiction=JURISDICTION,
    as_of=AS_OF,
    ordinary_income=0.12,
    long_term_capital_gain=0.0,
    net_investment_income=0.0,
)
"""12% ordinary / 0% long-term. The bracket in which several conclusions invert, and
the one in which tax-gain harvesting is a real lever rather than a curiosity."""

REGIMES: tuple[TaxRegime, ...] = (TOP_BRACKET, UPPER_MIDDLE_BRACKET, ZERO_RATE_BRACKET)


# --------------------------------------------------------------------------------------
# Accounts
# --------------------------------------------------------------------------------------


class Account(Enum):
    """Where a dollar sits. The distinctions that matter are structural, not nominal."""

    TAXABLE = "taxable"
    """Annual tax on distributions; deferral on unrealised gain; basis step-up at death;
    losses are usable; foreign tax is creditable."""

    TAX_DEFERRED = "tax_deferred"
    """Traditional IRA / 401(k). No internal tax at all, and no credit for foreign tax
    withheld. Withdrawals are ordinary income, and the government owns a fixed share of
    the balance from the outset."""

    TAX_EXEMPT = "tax_exempt"
    """Roth IRA / Roth 401(k). No internal tax and no withdrawal tax, and — identically
    to the traditional account — no credit for foreign tax withheld."""

    HEALTH_SAVINGS = "health_savings"
    """Deductible in, untaxed inside, untaxed out for qualified medical expense. The
    only US account with no tax at any of the three points, and the only account choice
    in this module that is a structural edge rather than a rate forecast."""


SHELTERED_ACCOUNTS: frozenset[Account] = frozenset(
    {Account.TAX_DEFERRED, Account.TAX_EXEMPT, Account.HEALTH_SAVINGS}
)
"""Accounts inside which no US tax is levied — and therefore inside which no foreign
tax credit can arise, because §901 credits a foreign tax only against a US tax."""


def traditional_and_roth_are_equivalent(
    *,
    pretax_contribution: float,
    pretax_log_growth: float,
    years: float,
    rate_at_contribution: float,
    rate_at_withdrawal: float,
) -> tuple[float, float]:
    """After-tax terminal wealth of a traditional and a Roth contribution.

    The algebra is a one-liner and it is the reason account *type* is not on the
    structural ledger. Contribute ``C`` pre-tax dollars:

    * traditional — ``C e**(gH) (1 - t_withdrawal)``
    * Roth — ``C (1 - t_contribution) e**(gH)``

    Multiplication commutes, so the two are **identical whenever the two rates are
    equal**, and the entire difference is ``(t_contribution - t_withdrawal)``. Choosing
    between them is a forecast of one's own future marginal rate, which is
    probabilistic, and it therefore does not belong in a contractual budget.

    What *is* structural, and follows directly, is that a tax-deferred balance is not
    the investor's money: at ``t_withdrawal``, a fraction ``t_withdrawal`` of every
    traditional dollar belongs to the government. An asset allocation stated on nominal
    balances therefore misstates the investor's true equity exposure, and an asset
    *location* comparison run on nominal rather than after-tax dollars is wrong for the
    same reason.
    """
    if pretax_contribution < 0.0:
        raise ValueError("pretax_contribution cannot be negative")
    if years < 0.0:
        raise ValueError("years cannot be negative")
    for rate in (rate_at_contribution, rate_at_withdrawal):
        if not 0.0 <= rate < 1.0:
            raise ValueError(f"rates must lie in [0, 1), got {rate}")
    growth = math.exp(pretax_log_growth * years)
    traditional = pretax_contribution * growth * (1.0 - rate_at_withdrawal)
    roth = pretax_contribution * (1.0 - rate_at_contribution) * growth
    return traditional, roth


# --------------------------------------------------------------------------------------
# The one simulator every other number is a special case of
# --------------------------------------------------------------------------------------


class Disposal(Enum):
    """What happens to the unrealised gain at the end of the horizon."""

    LIQUIDATE = "liquidate"
    """Sell everything and pay capital-gains tax on the whole remaining gain. The
    conservative assumption, and the one Chaudhuri, Burnham and Lo use, which is why
    their harvesting alpha is already net of the "it is only deferral" objection."""

    STEP_UP = "step_up"
    """Die holding it. 26 U.S.C. §1014 resets basis to fair market value, so the entire
    deferred liability is extinguished. This is not a trick; it is the largest single
    tax fact in US personal investing, and it is the reason turnover in a taxable
    account is expensive in a way no expense ratio captures."""

    CHARITABLE_GIFT = "charitable_gift"
    """Give the appreciated long-term shares to a public charity. §170 allows a
    deduction at fair market value and §170(e) does not claw back the appreciation, so
    the gain is never taxed to anyone. Arithmetically identical to :attr:`STEP_UP` for
    the portfolio, and additionally worth the deduction, which is outside this model."""


@dataclass(frozen=True)
class AfterTaxPath:
    """Terminal state of one dollar after a stated tax treatment."""

    terminal_wealth: float
    terminal_basis: float
    cumulative_tax_paid: float
    annualised_log_growth: float
    years: float

    def drag_bp_against(self, other: AfterTaxPath) -> float:
        """Annualised log-growth shortfall of ``self`` against ``other``, in bp/yr.

        Positive means ``self`` is *behind*. Log growth is used rather than a wealth
        ratio because it is the only difference measure that adds across years, which
        is what makes an annual "bp/yr" statement meaningful at all.
        """
        if self.years != other.years:
            raise ValueError("cannot compare paths of different length")
        return (other.annualised_log_growth - self.annualised_log_growth) / BASIS_POINT


def after_tax_path(
    *,
    regime: TaxRegime,
    account: Account,
    pretax_log_growth: float,
    years: int,
    dividend_yield: float = 0.0,
    dividend_qualified_fraction: float = 1.0,
    foreign_withholding_rate: float = 0.0,
    foreign_credit_utilisation: float = 1.0,
    capital_gain_distribution_yield: float = 0.0,
    realised_gain_fraction: float = 0.0,
    section_1256_fraction: float = 0.0,
    expense_ratio: float = 0.0,
    disposal: Disposal = Disposal.LIQUIDATE,
) -> AfterTaxPath:
    """Compound one dollar for ``years`` under a fully stated tax treatment.

    Convention, stated because it is where these calculations usually diverge:

    * ``pretax_log_growth`` is **total** pre-fee, pre-tax log growth, dividends
      included. Fees and taxes are then subtracted from it, so raising
      ``dividend_yield`` moves return from the deferred bucket into the taxed bucket
      without changing the pre-tax total. That is the correct comparative static and it
      is the one that makes a high-yield asset tax-disadvantaged.
    * Tax is paid **out of the account**, not from an external wallet. Paying it
      externally is a disguised extra contribution and flatters every deferral figure.
      Selling shares to pay it reduces wealth and basis by the same amount, because the
      shares sold are the ones whose basis was just stepped up by the distribution.
    * Distributions are reinvested and raise basis by the amount actually reinvested;
      that basis relief is exactly why the cost of a capital-gain distribution is far
      below its headline tax. The bookkeeping invariant this enforces is that
      distributing ``D`` of gain reduces standing unrealised gain by exactly ``D``.
    * In a sheltered account the only tax that is levied at all is foreign withholding,
      because a foreign government withholds at source regardless of the US wrapper. The
      account's own withdrawal tax is deliberately **not** applied here: by
      :func:`traditional_and_roth_are_equivalent` it is a constant multiplier that
      cancels out of every comparison this module makes.

    ``foreign_credit_utilisation`` is the fraction of foreign tax the investor actually
    converts into a credit. It is 1.0 only for a taxable investor with enough US tax on
    foreign-source income to absorb it; the §904 limitation drives it towards zero in a
    low bracket, and it is structurally zero in every sheltered account.
    """
    if years <= 0:
        raise ValueError(f"years must be a positive whole number, got {years}")
    for name, value in (
        ("dividend_yield", dividend_yield),
        ("capital_gain_distribution_yield", capital_gain_distribution_yield),
        ("expense_ratio", expense_ratio),
    ):
        if value < 0.0:
            raise ValueError(f"{name} cannot be negative, got {value}")
    for name, value in (
        ("dividend_qualified_fraction", dividend_qualified_fraction),
        ("foreign_withholding_rate", foreign_withholding_rate),
        ("foreign_credit_utilisation", foreign_credit_utilisation),
        ("realised_gain_fraction", realised_gain_fraction),
        ("section_1256_fraction", section_1256_fraction),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must lie in [0, 1], got {value}")

    sheltered = account in SHELTERED_ACCOUNTS
    utilisation = 0.0 if sheltered else foreign_credit_utilisation
    gross = math.exp(pretax_log_growth)

    wealth = 1.0
    basis = 1.0
    tax_paid = 0.0

    for _ in range(years):
        wealth *= gross
        wealth *= 1.0 - expense_ratio

        # 1. Foreign withholding, levied at source on the gross dividend. It is charged
        #    in every account; it is *creditable* only where a US tax exists to credit
        #    it against.
        dividend = dividend_yield * wealth
        foreign_tax = foreign_withholding_rate * dividend
        credit = utilisation * foreign_tax

        # 2. US tax on the dividend, computed on the *gross* amount, then reduced by the
        #    credit actually usable. Netting a fully usable credit against the gross US
        #    liability is what makes a creditable foreign tax cost the investor nothing.
        if sheltered:
            dividend_tax_net = 0.0
        else:
            qualified = dividend_qualified_fraction * dividend
            dividend_tax_net = max(
                regime.qualified_dividend * qualified
                + regime.ordinary * (dividend - qualified)
                - credit,
                0.0,
            )
        wealth -= foreign_tax + dividend_tax_net
        tax_paid += foreign_tax + dividend_tax_net
        # The net-of-withholding dividend is reinvested and raises basis; the US tax is
        # met by selling shares, which removes the same amount of basis again.
        basis += (dividend - foreign_tax) - dividend_tax_net

        if not sheltered:
            # 3. Capital-gain distributions: taxed now, but they raise basis, so the
            #    cost is the lost deferral rather than the tax.
            unrealised = max(wealth - basis, 0.0)
            distribution = min(capital_gain_distribution_yield * wealth, unrealised)
            distribution_tax = regime.capital_gain * distribution
            wealth -= distribution_tax
            tax_paid += distribution_tax
            basis += distribution - distribution_tax

            # 4. Gains the investor chooses to realise, plus any §1256 position forced
            #    to mark to market at the blended rate.
            unrealised = max(wealth - basis, 0.0)
            realised = realised_gain_fraction * unrealised
            ordinary_share = section_1256_fraction * realised
            realisation_tax = (
                regime.section_1256_blended * ordinary_share
                + regime.capital_gain * (realised - ordinary_share)
            )
            wealth -= realisation_tax
            tax_paid += realisation_tax
            basis += realised - realisation_tax
        else:
            basis = wealth

    if not sheltered and disposal is Disposal.LIQUIDATE:
        terminal_tax = regime.capital_gain * max(wealth - basis, 0.0)
        wealth -= terminal_tax
        tax_paid += terminal_tax
        basis = wealth

    return AfterTaxPath(
        terminal_wealth=wealth,
        terminal_basis=basis,
        cumulative_tax_paid=tax_paid,
        annualised_log_growth=math.log(wealth) / years,
        years=float(years),
    )


# --------------------------------------------------------------------------------------
# 1. Foreign tax credit forfeiture
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ForeignSleeve:
    """A stated international equity sleeve. Yields are gross of withholding."""

    label: str
    dividend_yield: float
    withholding_rate: float
    source: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.dividend_yield < 1.0:
            raise ValueError(f"{self.label}: dividend_yield must lie in [0, 1)")
        if not 0.0 <= self.withholding_rate < 1.0:
            raise ValueError(f"{self.label}: withholding_rate must lie in [0, 1)")
        if not self.source.strip():
            raise ValueError(f"{self.label}: a sleeve without a source is not evidence")

    @property
    def forfeited_bp(self) -> float:
        """``yield x withholding rate``, in bp/yr: the cost of sheltering this sleeve.

        This is the whole of the foreign tax credit forfeiture. It is exact, it is
        annual, it is permanent, and it applies identically to a traditional account and
        a Roth account, because §901 credits a foreign tax against a *US* tax and a
        sheltered account generates none.
        """
        return self.dividend_yield * self.withholding_rate / BASIS_POINT


@dataclass(frozen=True)
class LocationComparison:
    """Two placements of the same two assets, and the winner."""

    international_in_taxable_bp: float
    international_sheltered_bp: float

    @property
    def advantage_of_sheltering_international_bp(self) -> float:
        """Positive means the conventional "shelter the high-yield asset" rule holds."""
        return self.international_in_taxable_bp - self.international_sheltered_bp


def location_comparison(
    *,
    regime: TaxRegime,
    international: ForeignSleeve,
    domestic_dividend_yield: float,
    foreign_credit_utilisation: float = 1.0,
) -> LocationComparison:
    """Annual tax drag of the two ways to place an international and a domestic sleeve.

    One dollar of each asset, one dollar of shelter capacity. Only the *recurring* levy
    differs between the placements — the deferred gain is the same asset in both — so the
    comparison is closed form and needs no simulation:

    * international taxable, domestic sheltered:
      ``w y_i + max(q y_i - u w y_i, 0)`` — the foreign tax is paid at source in every
      case, and the US tax on the same dividend is then reduced by whatever credit the
      investor can actually use. The ``max`` is not decoration: an unused credit is
      **not refundable**, it carries back one year and forward ten (§904(c)), and in a
      0% bracket it usually expires.
    * international sheltered, domestic taxable: ``w y_i + q y_d`` — the foreign tax,
      now irrecoverable, plus US tax on the domestic dividend.

    Setting the two equal gives the break-even marginal dividend rate in
    :func:`location_breakeven_rate`, which is the decision-relevant output: below it the
    international sleeve belongs in the taxable account and above it in the shelter. The
    conventional advice states one side of that inequality as though it were universal.
    """
    if not 0.0 <= domestic_dividend_yield < 1.0:
        raise ValueError("domestic_dividend_yield must lie in [0, 1)")
    if not 0.0 <= foreign_credit_utilisation <= 1.0:
        raise ValueError("foreign_credit_utilisation must lie in [0, 1]")
    q = regime.qualified_dividend
    y_i = international.dividend_yield
    w = international.withholding_rate
    taxable = w * y_i + max(q * y_i - foreign_credit_utilisation * w * y_i, 0.0)
    sheltered = w * y_i + q * domestic_dividend_yield
    return LocationComparison(
        international_in_taxable_bp=taxable / BASIS_POINT,
        international_sheltered_bp=sheltered / BASIS_POINT,
    )


def location_breakeven_rate(
    *,
    international: ForeignSleeve,
    domestic_dividend_yield: float,
    foreign_credit_utilisation: float = 1.0,
) -> float:
    """The marginal qualified-dividend rate at which the two placements tie.

    From :func:`location_comparison`, equality is
    ``q y_i (1 - u w / q ... )`` — expanded cleanly:

        q y_i + (1 - u) w y_i  =  w y_i + q y_d
        q (y_i - y_d)          =  u w y_i
        q*                     =  u w y_i / (y_i - y_d).

    Read it as the sentence it is: **the international sleeve belongs in the taxable
    account whenever the investor's dividend rate is below the withholding rate scaled
    by the ratio of the international yield to the yield *gap*.** The rule flips on the
    investor's bracket, not on any property of the funds.

    Raises when the international yield does not exceed the domestic one, because then
    the shelter should hold the domestic asset for reasons that have nothing to do with
    the credit.
    """
    if not 0.0 <= foreign_credit_utilisation <= 1.0:
        raise ValueError("foreign_credit_utilisation must lie in [0, 1]")
    gap = international.dividend_yield - domestic_dividend_yield
    if gap <= 0.0:
        raise ValueError(
            "the international yield must exceed the domestic yield for this comparison "
            "to be about the credit at all"
        )
    return foreign_credit_utilisation * international.withholding_rate * (
        international.dividend_yield / gap
    )


DEVELOPED_EX_US = ForeignSleeve(
    label="Developed ex-US equity",
    dividend_yield=0.0260,
    withholding_rate=0.06068,
    source=(
        "Yield: MSCI EAFE index factsheet, dividend yield 2.60% as of 2026-07-31. "
        "Withholding: Vanguard '2025 Foreign tax credit information' worksheet "
        "(FTCWS 012026), VEA column 3 = 6.46% of ordinary cash dividends, which is "
        "6.46 / 106.46 = 6.068% of the grossed-up Box 1a amount the shareholder reports."
    ),
)
"""VEA-shaped developed-market sleeve. Forfeits 15.8 bp/yr inside any shelter."""

EMERGING_MARKETS = ForeignSleeve(
    label="Emerging-market equity",
    dividend_yield=0.0203,
    withholding_rate=0.09853,
    source=(
        "Yield: MSCI Emerging Markets index factsheet, dividend yield 2.03% as of "
        "2026-07-31. Withholding: Vanguard FTCWS 012026, VWO column 3 = 10.93% of "
        "ordinary cash dividends = 9.853% of the grossed-up amount."
    ),
)
"""VWO-shaped emerging sleeve. Forfeits 20.0 bp/yr inside any shelter — more than
developed markets despite the lower yield, because the withholding rate is higher."""


@dataclass(frozen=True)
class ShelterCandidate:
    """An asset competing for a dollar of tax-advantaged shelter capacity."""

    label: str
    dividend_yield: float
    qualified_fraction: float
    foreign_withholding_rate: float
    source: str

    def __post_init__(self) -> None:
        for name in ("dividend_yield", "qualified_fraction", "foreign_withholding_rate"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{self.label}: {name} must lie in [0, 1], got {value}")
        if not self.source.strip():
            raise ValueError(f"{self.label}: a candidate without a source is not evidence")

    def taxable_cost_bp(
        self, regime: TaxRegime, *, foreign_credit_utilisation: float = 1.0
    ) -> float:
        """Annual recurring tax if this asset sits in the taxable account, in bp/yr."""
        gross = self.dividend_yield
        foreign_tax = self.foreign_withholding_rate * gross
        us_tax = (
            regime.qualified_dividend * self.qualified_fraction * gross
            + regime.ordinary * (1.0 - self.qualified_fraction) * gross
        )
        credit = min(foreign_credit_utilisation * foreign_tax, us_tax)
        return (foreign_tax + us_tax - credit) / BASIS_POINT

    def sheltered_cost_bp(self) -> float:
        """Annual recurring tax if this asset sits inside a shelter, in bp/yr.

        Zero for everything except an asset subject to foreign withholding, which leaks
        ``w y`` a year in **every** account type. This asymmetry is the entire mechanism
        of §1 and it is the reason a location ranking computed on taxable cost alone —
        which is what the standard rule is — is not the right ranking.
        """
        return self.foreign_withholding_rate * self.dividend_yield / BASIS_POINT


def shelter_priority_bp(
    candidates: Sequence[ShelterCandidate],
    *,
    regime: TaxRegime,
    foreign_credit_utilisation: float = 1.0,
) -> list[tuple[str, float]]:
    """Rank assets by what a dollar of shelter capacity saves, highest first.

    The saving from moving an asset into a shelter is its taxable cost **less** the cost
    it still incurs inside the shelter:

        priority = (taxable recurring tax) - (irrecoverable foreign withholding).

    For every asset except a foreign one the second term is zero and the rule collapses
    to the familiar "shelter the heaviest recurring tax burden". For a foreign equity
    sleeve it does not, and the correction is exactly the forfeited credit. This is the
    honest form of the asset-location question, and it is the form in which the credit's
    effect on the ranking can be read off rather than asserted.

    Ties are broken by label so the ordering is deterministic.
    """
    scored = [
        (
            candidate.label,
            candidate.taxable_cost_bp(
                regime, foreign_credit_utilisation=foreign_credit_utilisation
            )
            - candidate.sheltered_cost_bp(),
        )
        for candidate in candidates
    ]
    return sorted(scored, key=lambda item: (-item[1], item[0]))


SHELTER_CANDIDATES: tuple[ShelterCandidate, ...] = (
    ShelterCandidate(
        label="Taxable investment-grade bonds",
        dividend_yield=0.0465,
        qualified_fraction=0.0,
        foreign_withholding_rate=0.0,
        source=(
            "Vanguard Total Bond Market ETF (BND) SEC 30-day yield 4.65% as of "
            "2026-08-10, from investor.vanguard.com's published fund-yield endpoint. "
            "Interest is ordinary income in full."
        ),
    ),
    ShelterCandidate(
        label=DEVELOPED_EX_US.label,
        dividend_yield=DEVELOPED_EX_US.dividend_yield,
        qualified_fraction=1.0,
        foreign_withholding_rate=DEVELOPED_EX_US.withholding_rate,
        source=DEVELOPED_EX_US.source,
    ),
    ShelterCandidate(
        label=EMERGING_MARKETS.label,
        dividend_yield=EMERGING_MARKETS.dividend_yield,
        qualified_fraction=1.0,
        foreign_withholding_rate=EMERGING_MARKETS.withholding_rate,
        source=EMERGING_MARKETS.source,
    ),
    ShelterCandidate(
        label="US equity",
        dividend_yield=0.0110,
        qualified_fraction=1.0,
        foreign_withholding_rate=0.0,
        source=(
            "Vanguard's published forecast dividend yield for VTI, 1.063% as of "
            "2026-06-30, cross-checked against MSCI World 1.53% and MSCI EAFE 2.60% at "
            "2026-07-31, which imply about 1.1% for the US at plausible weights. The "
            "12-month trailing figure on the same endpoint carries a stale effective "
            "date and is not used."
        ),
    ),
)
"""The four assets competing for shelter capacity. Deliberately excludes REITs and
high-yield credit: both belong at the top of the ranking, neither changes the finding,
and neither is in the repository's cheap broad-market control."""


def fill_shelter_bp(
    sleeves: Sequence[tuple[str, float, float]],
    *,
    capacity: float,
) -> float:
    """Fill a shelter of size ``capacity`` highest-priority-first, and return the saving.

    ``sleeves`` are ``(label, weight, priority_bp)``. Weights and ``capacity`` are
    fractions of the same base, so the result is in bp/yr **of that base**. Ties break
    by label, matching :func:`shelter_priority_bp`.

    A ranking is not an answer on its own: what a placement is worth depends on how much
    shelter there is. Below the first sleeve's weight the ranking's top line is all that
    matters; once capacity covers everything, placement is worth nothing at all, because
    every dollar is sheltered either way.
    """
    if capacity < 0.0:
        raise ValueError("capacity must be non-negative")
    for label, weight, _ in sleeves:
        if weight < 0.0:
            raise ValueError(f"{label}: weight must be non-negative")
    remaining, saving = capacity, 0.0
    for _, weight, priority in sorted(sleeves, key=lambda s: (-s[2], s[0])):
        placed = min(weight, remaining)
        saving += placed * priority
        remaining -= placed
        if remaining <= 0.0:
            break
    return saving


@dataclass(frozen=True)
class SplitVersusSingleFund:
    """Holding developed and emerging separately, against one total-international fund.

    Both figures are in bp/yr of the **equity sleeve**, at a stated shelter capacity
    also expressed as a fraction of the equity sleeve and taken to be what is left
    *after* bonds, which outrank every equity line by a factor of four.
    """

    capacity: float
    split_saving_bp: float
    single_fund_saving_bp: float

    @property
    def gain_bp(self) -> float:
        """What splitting the international sleeve is worth, in bp/yr of equity.

        Never negative: the split's fill order is available to the blended holder only
        by coincidence, so the split weakly dominates on placement alone. Every cost of
        splitting — two fees rather than one, two spreads, a second line to rebalance —
        sits outside this number and must be subtracted separately.
        """
        return self.split_saving_bp - self.single_fund_saving_bp


def _blended_international(
    *,
    developed: ShelterCandidate,
    emerging: ShelterCandidate,
    developed_weight: float,
    emerging_weight: float,
) -> ShelterCandidate:
    """The single total-international fund the two sleeves would collapse into.

    Yield blends by weight and the **withheld tax** blends by weight, so the blended
    withholding *rate* is a yield-weighted average rather than a weight-weighted one.
    Taking the plain average of the two rates would misprice the fund, because emerging
    markets withholds at a higher rate on a lower yield.
    """
    total = developed_weight + emerging_weight
    if total <= 0.0:
        raise ValueError("the international sleeve must carry positive weight")
    blended_yield = (
        developed_weight * developed.dividend_yield
        + emerging_weight * emerging.dividend_yield
    ) / total
    blended_foreign_tax = (
        developed_weight * developed.dividend_yield * developed.foreign_withholding_rate
        + emerging_weight * emerging.dividend_yield * emerging.foreign_withholding_rate
    ) / total
    return ShelterCandidate(
        label="Total international equity, one fund",
        dividend_yield=blended_yield,
        qualified_fraction=1.0,
        foreign_withholding_rate=blended_foreign_tax / blended_yield,
        source=(
            "Derived from the developed and emerging sleeves at the stated weights. "
            "Cross-checked against Vanguard's own 2025 foreign tax credit worksheet, "
            "which gives VXUS 7.11% of ordinary dividends against VEA 6.46% and VWO "
            "10.93%."
        ),
    )


def international_split_versus_single_fund(
    *,
    regime: TaxRegime,
    capacity: float,
    us_weight: float = 0.60,
    developed_weight: float = 0.30,
    emerging_weight: float = 0.10,
    foreign_credit_utilisation: float = 1.0,
) -> SplitVersusSingleFund:
    """Price the choice between VEA + VWO and a single VXUS-shaped fund, on placement.

    The recommendation splits developed from emerging *because* splitting is what makes
    the location result available, and a total-international fund forecloses it. That is
    a claim about a quantity, so the quantity is computed here rather than asserted.

    Defaults are Experiment 003's declared equity composition, 60/30/10.
    """
    candidates = {c.label: c for c in SHELTER_CANDIDATES}
    developed, emerging, us = (
        candidates["Developed ex-US equity"],
        candidates["Emerging-market equity"],
        candidates["US equity"],
    )
    blended = _blended_international(
        developed=developed,
        emerging=emerging,
        developed_weight=developed_weight,
        emerging_weight=emerging_weight,
    )

    def priority(candidate: ShelterCandidate) -> float:
        return (
            candidate.taxable_cost_bp(
                regime, foreign_credit_utilisation=foreign_credit_utilisation
            )
            - candidate.sheltered_cost_bp()
        )

    split = (
        ("US equity", us_weight, priority(us)),
        ("Developed ex-US equity", developed_weight, priority(developed)),
        ("Emerging-market equity", emerging_weight, priority(emerging)),
    )
    single = (
        ("US equity", us_weight, priority(us)),
        (blended.label, developed_weight + emerging_weight, priority(blended)),
    )
    return SplitVersusSingleFund(
        capacity=capacity,
        split_saving_bp=fill_shelter_bp(split, capacity=capacity),
        single_fund_saving_bp=fill_shelter_bp(single, capacity=capacity),
    )


def international_split_best_case_bp(
    *,
    regime: TaxRegime,
    us_weight: float = 0.60,
    developed_weight: float = 0.30,
    emerging_weight: float = 0.10,
    foreign_credit_utilisation: float = 1.0,
) -> tuple[float, float]:
    """``(capacity, gain_bp)`` at the shelter capacity that most favours splitting.

    ``gain_bp`` is piecewise linear in capacity with kinks only where a sleeve is
    exhausted, so the maximum is attained at one of those breakpoints and searching them
    is exact rather than a grid.
    """
    weights = (us_weight, developed_weight, emerging_weight)
    breakpoints = {
        sum(w for w, take in zip(weights, mask, strict=True) if take)
        for mask in itertools.product((False, True), repeat=len(weights))
    }
    best = max(
        (
            international_split_versus_single_fund(
                regime=regime,
                capacity=capacity,
                us_weight=us_weight,
                developed_weight=developed_weight,
                emerging_weight=emerging_weight,
                foreign_credit_utilisation=foreign_credit_utilisation,
            )
            for capacity in sorted(breakpoints)
        ),
        key=lambda result: (result.gain_bp, -result.capacity),
    )
    return best.capacity, best.gain_bp


def form_1116_threshold_assets(
    *, foreign_tax_limit: float, sleeve: ForeignSleeve
) -> float:
    """Sleeve value at which foreign tax paid reaches the Form 1116 filing threshold.

    A taxpayer whose creditable foreign tax is at or below $300 (single) or $600 (joint)
    and whose foreign income is all qualified passive income may claim the credit
    directly, without Form 1116 and **without the §904 limitation calculation**. Above
    the threshold the limitation binds, which is precisely where
    ``foreign_credit_utilisation`` stops being 1.0.

    ``foreign_tax = assets x yield x withholding rate``, so the threshold in assets is
    ``limit / (yield x withholding rate)``.
    """
    if foreign_tax_limit <= 0.0:
        raise ValueError("foreign_tax_limit must be positive")
    per_dollar = sleeve.dividend_yield * sleeve.withholding_rate
    if per_dollar <= 0.0:
        raise ValueError("a sleeve with no withheld tax has no threshold")
    return foreign_tax_limit / per_dollar


# --------------------------------------------------------------------------------------
# 2. Fund structure: capital-gain distributions
# --------------------------------------------------------------------------------------


def capital_gain_distribution_drag_bp(
    *,
    regime: TaxRegime,
    pretax_log_growth: float,
    years: int,
    distribution_yield: float,
    disposal: Disposal = Disposal.LIQUIDATE,
) -> float:
    """Annualised cost of a fund that distributes ``distribution_yield`` of NAV a year.

    Measured against an otherwise identical fund that distributes **nothing**, which is
    what an equity index ETF approximates because 26 U.S.C. §852(b)(6) exempts a
    regulated investment company from recognising gain on a redemption in kind.

    The number that matters is far below the headline tax, and the reason is the
    third line of :func:`after_tax_path`: a distribution raises the shareholder's basis,
    so the tax is **accelerated, not created**. Under :attr:`Disposal.LIQUIDATE` the
    entire cost is the lost deferral. Under :attr:`Disposal.STEP_UP` the acceleration is
    permanent and the cost roughly doubles, because the deferred liability would
    otherwise have been extinguished.
    """
    if distribution_yield < 0.0:
        raise ValueError("distribution_yield cannot be negative")
    distributing = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        capital_gain_distribution_yield=distribution_yield,
        disposal=disposal,
    )
    clean = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        capital_gain_distribution_yield=0.0,
        disposal=disposal,
    )
    return distributing.drag_bp_against(clean)


# --------------------------------------------------------------------------------------
# 3. Section 1256
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Section1256Comparison:
    """§1256 treatment against the two things it is confused with."""

    blended_rate: float
    ordinary_rate: float
    capital_gain_rate: float
    saving_against_ordinary_bp: float
    cost_against_deferred_capital_gain_bp: float

    @property
    def net_bp(self) -> float:
        """Saving against ordinary treatment, net of the deferral it destroys."""
        return self.saving_against_ordinary_bp - self.cost_against_deferred_capital_gain_bp


def section_1256_comparison(
    *,
    regime: TaxRegime,
    annual_return: float,
    pretax_log_growth: float,
    years: int,
) -> Section1256Comparison:
    """Price both halves of §1256: the rate cut, and the deferral it forfeits.

    A regulated futures contract is marked to market at year end and the resulting gain
    is split 60% long-term / 40% short-term whatever the holding period. Against a
    strategy whose gains would otherwise be **ordinary and annual** — which is the true
    counterfactual for a managed-futures programme, whose positions turn over in weeks —
    the saving is a pure rate cut of ``(ordinary - blended) x annual return`` per year.

    Against a strategy whose gains would otherwise be **long-term and deferred** — which
    is the true counterfactual for a buy-and-hold equity holding — §1256 is strictly
    worse on both counts, and the second figure prices the deferral half by comparing
    annual mark-to-market at the blended rate against full deferral at the long-term
    rate.
    """
    if annual_return < 0.0:
        raise ValueError("annual_return cannot be negative; the loss case is symmetric")
    saving = (regime.ordinary - regime.section_1256_blended) * annual_return / BASIS_POINT
    marked = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        realised_gain_fraction=1.0,
        section_1256_fraction=1.0,
    )
    deferred = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        realised_gain_fraction=0.0,
    )
    return Section1256Comparison(
        blended_rate=regime.section_1256_blended,
        ordinary_rate=regime.ordinary,
        capital_gain_rate=regime.capital_gain,
        saving_against_ordinary_bp=saving,
        cost_against_deferred_capital_gain_bp=marked.drag_bp_against(deferred),
    )


# --------------------------------------------------------------------------------------
# 4. Deferred unrealised gain
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DeferralValue:
    """What an unrealised gain is worth, decomposed into its two halves."""

    years: int
    realised_gain_fraction: float
    deferral_bp: float
    step_up_bp: float

    @property
    def total_bp(self) -> float:
        """Full value of never realising, against realising at the stated rate."""
        return self.deferral_bp + self.step_up_bp


def deferral_value(
    *,
    regime: TaxRegime,
    pretax_log_growth: float,
    years: int,
    realised_gain_fraction: float = 1.0,
) -> DeferralValue:
    """The interest-free loan, sized, and the step-up that can forgive it.

    ``deferral_bp`` compares full deferral-then-liquidation against realising
    ``realised_gain_fraction`` of the standing unrealised gain every year and
    liquidating the rest. ``step_up_bp`` is the further gain from never liquidating at
    all (26 U.S.C. §1014).

    Both grow with the horizon and with the growth rate, and both are **larger than
    every other line in this module** at long horizons. That is the quantitative form of
    the argument against high-turnover strategies in a taxable account: a strategy must
    out-earn not only its fee and its spread but the deferral it destroys, and at a 7%
    growth rate over thirty years that hurdle alone is worth more than the entire
    89 bp/yr contractual budget the repository has already booked.
    """
    realising = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        realised_gain_fraction=realised_gain_fraction,
    )
    deferring = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        realised_gain_fraction=0.0,
    )
    stepped = after_tax_path(
        regime=regime,
        account=Account.TAXABLE,
        pretax_log_growth=pretax_log_growth,
        years=years,
        realised_gain_fraction=0.0,
        disposal=Disposal.STEP_UP,
    )
    return DeferralValue(
        years=years,
        realised_gain_fraction=realised_gain_fraction,
        deferral_bp=realising.drag_bp_against(deferring),
        step_up_bp=deferring.drag_bp_against(stepped),
    )


# --------------------------------------------------------------------------------------
# 5. Tax-loss harvesting decay
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class HarvestingProfile:
    """A decaying stream of harvesting benefit, and what it is worth net of its fee."""

    label: str
    annual_bp: tuple[float, ...]
    terminal_bp: float
    source: str

    def benefit_bp(self, year: int) -> float:
        """Benefit in year ``year`` (1-indexed); the terminal level thereafter."""
        if year < 1:
            raise ValueError("years are 1-indexed")
        if year <= len(self.annual_bp):
            return self.annual_bp[year - 1]
        return self.terminal_bp

    def horizon_average_bp(self, years: int) -> float:
        """Arithmetic mean benefit over ``years``, which is what a "bp/yr" claim means.

        Vendor headlines quote year one. Year one is the largest number the profile ever
        takes, and quoting it as an annual rate overstates a thirty-year holding by
        roughly an order of magnitude.
        """
        if years < 1:
            raise ValueError("years must be at least 1")
        return sum(self.benefit_bp(y) for y in range(1, years + 1)) / years

    def net_of_fee_bp(self, *, years: int, fee_bp: float) -> float:
        """Horizon-average benefit less the fee charged to obtain it."""
        if fee_bp < 0.0:
            raise ValueError("fee_bp cannot be negative")
        return self.horizon_average_bp(years) - fee_bp

    def break_even_horizon(self, *, fee_bp: float, max_years: int = 100) -> int | None:
        """First horizon at which the horizon-average benefit falls below the fee.

        Returns ``None`` if it never does within ``max_years``. This is the number a
        direct-indexing prospect actually needs: the benefit is front-loaded and the fee
        is not, so a decaying profile crosses its own fee at a computable date.
        """
        if fee_bp < 0.0:
            raise ValueError("fee_bp cannot be negative")
        for year in range(1, max_years + 1):
            if self.horizon_average_bp(year) < fee_bp:
                return year
        return None


HARVESTING_NO_FLOW_LONG_TERM = HarvestingProfile(
    label="No contributions, only long-term gains to offset",
    annual_bp=(155.3, 50.8, 25.7, 18.9, 8.0, 4.8, -0.5, -2.4, -3.1),
    terminal_bp=-4.3,
    source=(
        "Sosner, Gromis and Krasner, 'The Tax Benefits of Direct Indexing: Not a "
        "One-Size-Fits-All Formula', Journal of Beta Investment Strategies 13(2), Summer "
        "2022, Exhibit 1, year-dummy regression on 45 overlapping historical simulations "
        "1975-2019, S&P 500 universe, 2020 rates (40.8% short / 23.8% long), HIFO lots, "
        "wash-sale rule NOT modelled. AQR sells competing tax-aware long/short "
        "strategies, so the direction of its commercial bias is away from this result."
    ),
)
"""The modal retail case, and the one the vendor headline never shows. Turns negative
in year 7 and settles at -4.3 bp."""

HARVESTING_NO_FLOW_SHORT_TERM = HarvestingProfile(
    label="No contributions, short-term gains available to offset",
    annual_bp=(339.1, 114.0, 66.5, 52.2, 36.8, 30.1, 24.1, 21.8, 19.8),
    terminal_bp=18.2,
    source=HARVESTING_NO_FLOW_LONG_TERM.source,
)
"""Requires systematic short-term gains from elsewhere — hedge funds, derivatives. The
long-run 18.2 bp is almost entirely *character* benefit, the short/long rate spread,
not harvesting."""

HARVESTING_WITH_CONTRIBUTIONS = HarvestingProfile(
    label="1% monthly contributions, only long-term gains to offset",
    annual_bp=(164.3, 64.7, 47.3, 39.3, 32.8, 31.8, 28.7, 27.8, 25.7),
    terminal_bp=27.4,
    source=HARVESTING_NO_FLOW_LONG_TERM.source,
)
"""New money resets basis and defeats ossification. This is the profile the 30 bp line
already in the edge budget actually describes, and its 30-year average is 34.6 bp."""

DIRECT_INDEXING_FEES_BP: tuple[tuple[str, float, float], ...] = (
    ("Wealthfront S&P 500 Direct", 9.0, 5_000.0),
    ("Frec S&P 500 direct index", 9.0, 20_000.0),
    ("Wealthfront Nasdaq-100 Direct", 12.0, 5_000.0),
    ("Altruist US Large-Cap Direct Index (adviser channel)", 12.0, 2_000.0),
    ("Vanguard Personalized Indexing (sub-advisory tier)", 20.0, 250_000.0),
    ("Schwab Personalized Indexing (retail)", 40.0, 100_000.0),
    ("Fidelity Managed FidFolios (index strategies)", 40.0, 5_000.0),
)
"""``(provider, annual fee in bp, minimum in dollars)``, published schedules as of
2026-07/08. Retail direct indexing has bifurcated: automated providers charge 9-12 bp
and incumbent brokerages 40 bp. Against the profiles above, a 40 bp fee is negative
expected value in steady state and a 9 bp fee is marginal for a static investor."""


def harvested_loss_value_bp(
    *,
    regime: TaxRegime,
    harvested_loss_fraction: float,
    offsetting_gain_available: bool,
    ordinary_offset_cap: float = 3_000.0,
    portfolio_value: float = 1_000_000.0,
) -> float:
    """Value of realising losses equal to ``harvested_loss_fraction`` of the portfolio.

    Two regimes, and the second is the one the vendor studies quietly assume away.

    * **With offsetting realised gains**, the loss shelters gain dollar for dollar at
      the capital-gains rate, so the benefit is ``rate x loss``.
    * **Without them**, 26 U.S.C. §1211(b) caps the deduction against ordinary income at
      **$3,000 a year** — a nominal figure unchanged since 1978 and not indexed — with
      the excess carried forward under §1212(b). The benefit collapses to
      ``ordinary rate x min(loss, 3000)``, which on a seven-figure portfolio is a
      rounding error.

    The realised benefit is in both cases a *deferral*, because §1091(d) and the basis
    mechanics push the sheltered gain into the replacement lot; the permanent part is
    only the rate arbitrage and whatever the step-up eventually forgives.
    """
    if not 0.0 <= harvested_loss_fraction <= 1.0:
        raise ValueError("harvested_loss_fraction must lie in [0, 1]")
    if portfolio_value <= 0.0:
        raise ValueError("portfolio_value must be positive")
    loss = harvested_loss_fraction * portfolio_value
    if offsetting_gain_available:
        benefit = regime.capital_gain * loss
    else:
        benefit = regime.ordinary * min(loss, ordinary_offset_cap)
    return benefit / portfolio_value / BASIS_POINT


# --------------------------------------------------------------------------------------
# 6. Small levers, priced so they can be dismissed with a number
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class LotSelection:
    """Gain realised on the same sale under two identification methods."""

    gain_first_in_first_out: float
    gain_highest_in_first_out: float
    proceeds: float

    @property
    def deferred_gain(self) -> float:
        return self.gain_first_in_first_out - self.gain_highest_in_first_out


def lot_selection_comparison(
    *,
    annual_purchase: float,
    purchases: int,
    pretax_log_growth: float,
    proceeds_fraction: float,
) -> LotSelection:
    """Gain realised selling the same dollar amount, FIFO against highest-in-first-out.

    A deliberately transparent lot model: ``purchases`` equal contributions of
    ``annual_purchase``, one a year, into an asset compounding at ``pretax_log_growth``,
    then a sale of ``proceeds_fraction`` of the final value. Lot ``k`` bought at price
    ``e**(g k)`` is worth ``e**(g (n - k))`` per dollar invested at the sale date, so the
    oldest lot carries the largest embedded gain and FIFO realises the most.

    Treasury Regulation §1.1012-1(c) permits specific identification when the taxpayer
    adequately identifies the shares sold *at the time of the sale*, and §1.1012-1(e)
    makes first-in-first-out the default for stock held by a broker where no adequate
    identification is made. So the choice is free, it must be made contemporaneously,
    and its whole value is the deferral on ``deferred_gain`` — a timing benefit, not a
    permanent one, except to the extent a later step-up forgives it.
    """
    if purchases < 1:
        raise ValueError("purchases must be at least 1")
    if annual_purchase <= 0.0:
        raise ValueError("annual_purchase must be positive")
    if not 0.0 < proceeds_fraction <= 1.0:
        raise ValueError("proceeds_fraction must lie in (0, 1]")

    growth_per_year = math.exp(pretax_log_growth)
    # (basis, current value) per lot, oldest first.
    lots = [
        (annual_purchase, annual_purchase * growth_per_year ** (purchases - k))
        for k in range(purchases)
    ]
    total_value = sum(value for _, value in lots)
    target = proceeds_fraction * total_value

    def realise(order: Sequence[tuple[float, float]]) -> float:
        remaining = target
        gain = 0.0
        for lot_basis, lot_value in order:
            if remaining <= 0.0:
                break
            taken = min(lot_value, remaining)
            share = taken / lot_value
            gain += taken - share * lot_basis
            remaining -= taken
        return gain

    oldest_first = list(lots)
    highest_basis_first = sorted(lots, key=lambda lot: lot[1] / lot[0])
    return LotSelection(
        gain_first_in_first_out=realise(oldest_first),
        gain_highest_in_first_out=realise(highest_basis_first),
        proceeds=target,
    )


def wash_sale_across_accounts_cost_bp(
    *, regime: TaxRegime, disallowed_loss_fraction: float
) -> float:
    """Cost of triggering a wash sale whose replacement shares are bought in an IRA.

    26 U.S.C. §1091(a) disallows a loss where substantially identical stock is acquired
    within 30 days either side of the sale, and §1091(d) normally repairs the damage by
    adding the disallowed loss to the basis of the replacement shares — so an ordinary
    wash sale is a **deferral**, not a loss.

    Revenue Ruling 2008-5 removes that repair when the replacement is bought inside the
    taxpayer's IRA: the loss is disallowed under §1091(a) and the IRA's basis is **not**
    increased, so the deduction is destroyed outright. This is the only tax-loss
    harvesting error in this module whose cost is permanent rather than timing, which is
    why it earns a line despite being an avoidance rather than an edge. The same logic
    reaches a spouse's IRA and, on the same reasoning, a Roth.
    """
    if not 0.0 <= disallowed_loss_fraction <= 1.0:
        raise ValueError("disallowed_loss_fraction must lie in [0, 1]")
    return regime.capital_gain * disallowed_loss_fraction / BASIS_POINT


def tax_equivalent_yield(*, municipal_yield: float, regime: TaxRegime) -> float:
    """``municipal yield / (1 - ordinary rate)``: what a taxable bond must yield to match.

    §103 exempts state and local bond interest from federal gross income, and the §1411
    surtax does not reach it either, so the divisor is the full all-in ordinary rate.
    """
    return municipal_yield / (1.0 - regime.ordinary)


MUNICIPAL_CURVE: tuple[tuple[str, float, float], ...] = (
    ("2 year", 0.0254, 0.0422),
    ("5 year", 0.0284, 0.0437),
    ("10 year", 0.0324, 0.0467),
    ("30 year", 0.0439, 0.0520),
)
"""``(term, AAA general-obligation municipal yield, Treasury par yield)`` at 2026-07-29.

Municipal yields are the Municipal Market Data AAA GO curve as republished by Invesco's
municipal desk; Treasury yields are the official daily par yield curve. The pair is
struck on the same date deliberately: a break-even computed from yields a week apart is
the commonest error in this comparison, and at these levels a 10 bp curve move shifts
the break-even rate by about two percentage points.
"""


def municipal_breakeven_rate(*, municipal_yield: float, taxable_yield: float) -> float:
    """Marginal ordinary rate above which the municipal bond wins: ``1 - m / t``.

    Below it the taxable bond wins, and the municipal market prices itself so that this
    break-even sits near the top bracket — which is the point. A municipal yield ratio
    of 0.80 implies a break-even of exactly 20%, and one of 0.65 implies 35%.
    """
    if taxable_yield <= 0.0:
        raise ValueError("taxable_yield must be positive")
    return 1.0 - municipal_yield / taxable_yield


def net_unrealised_appreciation_benefit_bp(
    *,
    regime: TaxRegime,
    basis_fraction: float,
    employer_stock_fraction_of_portfolio: float,
    years_to_distribution: int,
) -> float:
    """Annualised value of the §402(e)(4) net-unrealised-appreciation election.

    Distribute employer securities in kind from a qualified plan: ordinary tax applies
    only to the plan's **basis**, and the appreciation is taxed at the long-term rate on
    later sale rather than as ordinary income on withdrawal. The saving is
    ``(ordinary - capital gain) x (1 - basis fraction)`` of the position, taken once and
    amortised over the years to that distribution.

    This is a genuine rate arbitrage and it is also the single most concentrated
    position most employees will ever hold, so sizing it is not the same as recommending
    it. It exists only for employer securities inside a qualified plan and is
    unavailable to an IRA-only saver.
    """
    if not 0.0 <= basis_fraction <= 1.0:
        raise ValueError("basis_fraction must lie in [0, 1]")
    if not 0.0 <= employer_stock_fraction_of_portfolio <= 1.0:
        raise ValueError("employer_stock_fraction_of_portfolio must lie in [0, 1]")
    if years_to_distribution < 1:
        raise ValueError("years_to_distribution must be at least 1")
    one_off = (
        (regime.ordinary - regime.capital_gain)
        * (1.0 - basis_fraction)
        * employer_stock_fraction_of_portfolio
    )
    return one_off / years_to_distribution / BASIS_POINT


def qualified_dividend_shortfall_bp(
    *, regime: TaxRegime, dividend_yield: float, qualified_fraction: float
) -> float:
    """Cost of the non-qualified share of a fund's dividend, in bp/yr.

    ``(1 - qualified fraction) x yield x (ordinary - long-term rate)``. It is listed
    because it is the mechanism by which two funds with identical expense ratios and
    identical gross returns deliver different after-tax returns, and because a fund that
    lends securities aggressively converts part of its dividend into substitute payments
    that are **not** qualified.
    """
    if not 0.0 <= qualified_fraction <= 1.0:
        raise ValueError("qualified_fraction must lie in [0, 1]")
    if dividend_yield < 0.0:
        raise ValueError("dividend_yield cannot be negative")
    return (
        (1.0 - qualified_fraction)
        * dividend_yield
        * (regime.ordinary - regime.capital_gain)
        / BASIS_POINT
    )


def tax_gain_harvest_value_bp(
    *,
    harvesting_regime: TaxRegime,
    future_regime: TaxRegime,
    gain_realised_fraction: float,
    years_until_sale: int,
) -> float:
    """Annualised value of realising gain at a 0% rate that would later be taxed.

    Selling and immediately repurchasing resets basis upward at whatever rate applies
    today; the wash-sale rule does not reach gains (§1091 is written for losses only),
    so the round trip is legal and costs only the spread. The benefit is
    ``(future rate - today's rate) x gain realised``, amortised over the years until the
    sale it displaces.
    """
    if not 0.0 <= gain_realised_fraction <= 1.0:
        raise ValueError("gain_realised_fraction must lie in [0, 1]")
    if years_until_sale < 1:
        raise ValueError("years_until_sale must be at least 1")
    spread = future_regime.capital_gain - harvesting_regime.capital_gain
    return max(spread, 0.0) * gain_realised_fraction / years_until_sale / BASIS_POINT


# --------------------------------------------------------------------------------------
# 7. Capital efficiency, analysed and not recommended
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CapitalEfficiency:
    """A return-stacked fund's arithmetic, with its financing cost made explicit."""

    label: str
    equity_notional: float
    bond_notional: float
    expense_ratio_bp: float
    bond_excess_return_bp: float
    implied_financing_spread_bp: float

    @property
    def gross_notional(self) -> float:
        return self.equity_notional + self.bond_notional

    @property
    def overlay_contribution_bp(self) -> float:
        """What the futures overlay adds before its own costs, in bp/yr of NAV."""
        return self.bond_notional * self.bond_excess_return_bp

    @property
    def financing_cost_bp(self) -> float:
        """The spread the overlay pays over the investor's own cash rate."""
        return self.bond_notional * self.implied_financing_spread_bp

    @property
    def net_contribution_bp(self) -> float:
        """Overlay contribution less financing and less the fund's fee.

        The whole question is the sign of this number, and **both of its inputs are
        forecasts**: the bond excess return over cash is a term premium, and the
        financing spread is a market price that moves. That is why capital efficiency
        cannot enter a contractual budget, however attractive its mechanism.
        """
        return self.overlay_contribution_bp - self.financing_cost_bp - self.expense_ratio_bp

    @property
    def net_of_financing_bp(self) -> float:
        """Overlay contribution less financing, before the fund's own fee."""
        return self.overlay_contribution_bp - self.financing_cost_bp

    def break_even_excess_return_bp(self) -> float:
        """Bond excess return over cash at which the overlay just pays for itself."""
        if self.bond_notional <= 0.0:
            raise ValueError("no overlay to break even on")
        return self.implied_financing_spread_bp + self.expense_ratio_bp / self.bond_notional


TREASURY_FUTURES_FUNDING_BASIS_BP = 58.70
"""Average implied-repo-minus-repo funding basis on CME 5-year Treasury note futures.

Fleckenstein and Longstaff, "Renting Balance Sheet Space", *Review of Financial Studies*
33(11), 2020: 6,943 daily observations, 1991-06-03 to 2018-12-31. Verbatim: *"The average
funding basis is 58.70 basis points, but reached levels of 200 basis points or more"* in
1998, 2000-2002 and 2008. It is 58.79 bp pre-crisis and 58.56 bp post-crisis and positive
in **all 28 years** — a remarkably stable cost, not a crisis artefact.

Its significance is that it is almost exactly the 62.3 bp LIBOR-over-T-bill spread at
which Asness, Frazzini and Pedersen's own Appendix B shows risk parity's advantage over
the market losing significance. Their defence — *"leverage can be achieved by using
futures contracts at an implicit cost that is lower than LIBOR"* — is not supported by
the one measurement of that implicit cost retrieved for this page.
"""

EQUITY_FUTURES_ROLL_RICHNESS_BP = 62.0
"""Average E-mini S&P 500 implied financing over the 3-month SOFR forward curve.

CME Group, "Quantifying and Hedging Equity Financing Risk" (2025): ten quarterly rolls,
December 2022 to March 2025, 916 days, averaging *"62bps rich"*, with individual rolls
from 20.1 bp to 141.9 bp. The sign is not constant — CME measured **-27 bp** against
LIBOR at the September 2011 roll — so this is a regime-dependent price, not a constant.
"""

NTSX = CapitalEfficiency(
    label="NTSX-shaped 90/60 equity and Treasury futures",
    equity_notional=0.90,
    bond_notional=0.60,
    expense_ratio_bp=20.0,
    bond_excess_return_bp=TREASURY_FUTURES_FUNDING_BASIS_BP,
    implied_financing_spread_bp=TREASURY_FUTURES_FUNDING_BASIS_BP,
)
"""The most substantive structural candidate on the page, and the one this repository
cannot sign.

Structure and fee from the WisdomTree U.S. Efficient Core Fund prospectus dated
2025-11-01: *"approximately 90% of its net assets in U.S. equity securities"* with
Treasury futures at *"approximately 60% of the Fund's net assets"*, total expenses 0.20%,
inception 2018-08-02.

``bond_excess_return_bp`` is deliberately set **equal to the financing spread**, which is
the null: it says the term premium exactly pays for the cost of renting the balance
sheet, and the fund is then behind by its own fee. Substitute a real term-premium
estimate to move it — but that estimate is a forecast, which is the whole point.
"""


# --------------------------------------------------------------------------------------
# The ledger
# --------------------------------------------------------------------------------------


class Additivity(Enum):
    """Whether a lever adds to the 89 bp/yr own-counterfactual budget already booked."""

    ADDITIVE = "additive"
    """A distinct mechanism against a distinct base. Adds."""

    ALREADY_COUNTED = "already_counted"
    """The same dollars as an existing line. Booking it again is a double count."""

    NOT_BOOKABLE = "not_bookable"
    """Real, but probabilistic, conditional on a forecast, or a one-off in dollars
    rather than a rate on the portfolio. Reported and deliberately not booked."""


@dataclass(frozen=True)
class StructuralLever:
    """One line of the structural ledger, with everything needed to audit or reject it."""

    name: str
    mechanism: str
    benchmark: Benchmark
    certainty: Certainty
    additivity: Additivity
    low_bp: float
    central_bp: float
    high_bp: float
    conditions: str
    falsifier: str
    double_count_note: str

    def __post_init__(self) -> None:
        if not self.low_bp <= self.central_bp <= self.high_bp:
            raise ValueError(
                f"{self.name}: require low <= central <= high, got "
                f"{self.low_bp}, {self.central_bp}, {self.high_bp}"
            )
        for field, label in (
            (self.falsifier, "falsifier"),
            (self.double_count_note, "double-count note"),
            (self.mechanism, "mechanism"),
            (self.conditions, "conditions"),
        ):
            if not field.strip():
                raise ValueError(f"{self.name}: every lever needs a {label}")
        if self.additivity is Additivity.ADDITIVE and self.central_bp <= 0.0:
            raise ValueError(
                f"{self.name}: a lever booked as additive must carry a positive central "
                "estimate; if it does not, it is NOT_BOOKABLE"
            )


REFERENCE_INVESTOR = (
    "US individual, top bracket (40.8% ordinary / 23.8% long-term), 30-year horizon, "
    "liquidation at the end. Portfolio: 60% US equity, 14% developed ex-US equity, "
    "6% emerging-market equity, 20% taxable investment-grade bonds. Accounts: 40% of "
    "the portfolio sits in tax-advantaged capacity and 60% in a taxable account, with "
    "assets located by the ranking in `shelter_priority_bp` — so the shelter holds the "
    "bonds and the whole international sleeve, and the taxable account holds US equity."
)
"""Every ``central_bp`` in the ledger is stated at portfolio level for this investor.

Stating it is not decoration. The single largest way a tax figure is inflated is to
quote a per-sleeve number as if it were a portfolio number, and every lever below has a
different base: fund structure applies to taxable equity, the foreign tax credit to the
sheltered international sleeve, municipal bonds to taxable bonds — of which this
investor has none, which is itself a finding.
"""


@dataclass(frozen=True)
class LedgerTotal:
    """Aggregate of the additive lines only."""

    lines: int
    low_bp: float
    central_bp: float
    high_bp: float


def additive_total(levers: Sequence[StructuralLever]) -> LedgerTotal:
    """Sum only the lines marked :attr:`Additivity.ADDITIVE`, within one benchmark.

    Raises on mixed benchmarks for the same reason
    :func:`portfolio_edge.studies.outperformance_horizon.aggregate` does: the standard
    way this argument is inflated is to add a saving against the investor's own
    counterfactual to a return against an index.
    """
    additive = [lever for lever in levers if lever.additivity is Additivity.ADDITIVE]
    if not additive:
        raise ValueError("no additive lines to total")
    benchmarks = {lever.benchmark for lever in additive}
    if len(benchmarks) != 1:
        raise ValueError(
            "additive lines must share one benchmark; got "
            + ", ".join(sorted(b.value for b in benchmarks))
        )
    return LedgerTotal(
        lines=len(additive),
        low_bp=sum(lever.low_bp for lever in additive),
        central_bp=sum(lever.central_bp for lever in additive),
        high_bp=sum(lever.high_bp for lever in additive),
    )


# --------------------------------------------------------------------------------------
# The committed ledger
# --------------------------------------------------------------------------------------
#
# Sizes are portfolio-level for REFERENCE_INVESTOR and are regenerated by the functions
# above from the inputs named in each `mechanism`. Nothing here is a forecast.

FUND_STRUCTURE = StructuralLever(
    name="Fund structure: capital-gain distributions avoided",
    mechanism=(
        "26 U.S.C. §852(b)(6) disapplies §311(b) to a redemption in kind, so an ETF "
        "hands appreciated shares to an authorised participant without recognising "
        "gain, while an equivalent mutual fund sells and distributes. Sized as "
        "`capital_gain_distribution_drag_bp` at a 3%-of-NAV distribution over 30 years, "
        "38.3 bp on the taxable equity sleeve, times the 60% of the portfolio that "
        "sleeve occupies."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.ADDITIVE,
    low_bp=0.0,
    central_bp=23.0,
    high_bp=50.0,
    conditions=(
        "A taxable account, and a counterfactual that is an actively managed mutual "
        "fund without an ETF share class. Zero in any sheltered account and zero "
        "against a low-turnover index mutual fund: Poterba and Shoven (2002) found the "
        "Vanguard 500 index fund slightly *beat* SPY after tax over 1994-2000. The high "
        "figure is the 6.6-7.0%-of-NAV ten-year average distribution of the two largest "
        "active US equity funds, AGTHX and FCNTX, read from their N-CSR filings."
    ),
    falsifier=(
        "Broad adoption of ETF share classes by active mutual funds, which the SEC began "
        "permitting with its first multi-class order on 2025-11-17 and had extended to "
        "about fifty fund families by 2026-03-17; or repeal of §852(b)(6), proposed in "
        "the 2021 Senate Finance discussion draft and never enacted."
    ),
    double_count_note=(
        "ADDITIVE. The 49 bp fund-cost line in the edge budget is an expense-ratio gap "
        "and contains no tax at all, so this measures different dollars against the same "
        "benchmark. It does *not* overlap the tax-loss-harvesting line either: that is "
        "the investor realising losses, this is the fund realising gains."
    ),
)

LOT_SELECTION = StructuralLever(
    name="Specific identification of tax lots",
    mechanism=(
        "Treas. Reg. §1.1012-1(c) permits identifying the shares sold, and §1.1012-1(e) "
        "makes first-in-first-out the default when no identification is made. Selling "
        "the highest-basis lots defers gain that FIFO would realise. §1.1012-1(c)(8) "
        "accepts a standing instruction, and §1.1012-1(c)(10) says the choice is not a "
        "method of accounting, so switching costs nothing."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.ADDITIVE,
    low_bp=0.0,
    central_bp=5.0,
    high_bp=44.0,
    conditions=(
        "Requires sales — a pure buy-and-hold investor realises nothing and the lever is "
        "worth exactly zero until the first disposal. The high figure is Dickson, Shoven "
        "and Sialm's measured 73 bp/yr for HIFO against average cost in a no-cash-flow "
        "separate account over 1984-98, scaled to the taxable sleeve; that is a "
        "simulation over an unusually strong bull market and the central estimate is "
        "shrunk hard towards zero because no measurement exists for a retail investor."
    ),
    falsifier=(
        "A measurement on a low-turnover retail portfolio showing no material difference "
        "between HIFO and average cost, or a broker that does not support standing "
        "specific identification."
    ),
    double_count_note=(
        "PARTIALLY ADDITIVE, and booked at the part that is. Every tax-loss-harvesting "
        "study cited in the edge budget already assumes HIFO lot accounting, so the "
        "harvesting benefit and the lot-selection benefit overlap for an investor who "
        "harvests. What is booked here is the residual for an investor who merely "
        "rebalances or withdraws — which is why the central estimate is 5 bp and not 44."
    ),
)

FOREIGN_TAX_CREDIT = StructuralLever(
    name="Foreign tax credit forfeited inside a shelter",
    mechanism=(
        "§901(a) credits a foreign tax against a US tax; §408(e)(1) makes an IRA exempt "
        "from that tax and §904(a) makes the limitation zero, so withholding paid inside "
        "any shelter is lost. Sized as `ForeignSleeve.forfeited_bp`: 15.78 bp on the "
        "developed sleeve and 20.00 bp on emerging, at the 14% and 6% weights the "
        "reference investor shelters."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.ALREADY_COUNTED,
    low_bp=-6.0,
    central_bp=-3.4,
    high_bp=0.0,
    conditions=(
        "Applies to any internationally diversified portfolio with tax-advantaged "
        "capacity. Zero for an investor holding no foreign equity, and zero for one who "
        "holds it all in a taxable account with enough US tax on foreign-source income "
        "to absorb the credit."
    ),
    falsifier=(
        "Relief at source rather than reclaim, driving fund-reported foreign tax paid to "
        "zero; or a treaty extending the pension-fund exemption to pooled vehicles, which "
        "Art. 10(4) of both the US-UK and US-Japan conventions currently forecloses."
    ),
    double_count_note=(
        "NOT ADDITIVE — it is a **correction with the opposite sign** to the 10 bp asset "
        "location line already booked, whose sources (Shoven-Sialm, Dammon-Spatt-Zhang, "
        "Vanguard) model no foreign withholding at all. Booking it as a new positive "
        "line would be the most direct double count available."
    ),
)

HARVESTING_FEE = StructuralLever(
    name="Direct-indexing fee, netted against the harvesting line",
    mechanism=(
        "The 30 bp tax-loss-harvesting line already assumes direct security ownership, "
        "because a fund cannot pass security-level losses through. Obtaining that costs "
        "9-40 bp of published fee. Netting the fee and using the 30-year horizon average "
        "of the measured decay profile rather than the year-one figure gives 34.6 bp "
        "gross and 25.6 bp net for a contributing investor at a 9 bp fee."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.ALREADY_COUNTED,
    low_bp=-30.0,
    central_bp=-4.4,
    high_bp=6.0,
    conditions=(
        "The sign turns on contributions and on the provider. A static investor with only "
        "long-term gains averages 5.6 bp gross over 30 years and is negative at any fee; "
        "a contributing investor at 9 bp nets 25.6 bp; anyone at 40 bp is negative in "
        "every scenario measured."
    ),
    falsifier=(
        "A measured decay profile that does not decay — which would require harvesting "
        "not to ratchet basis downward — or a zero-fee direct-indexing provider."
    ),
    double_count_note=(
        "NOT ADDITIVE — it is a **correction** to the existing 30 bp line, moving it to "
        "about 25.6 bp for the reference investor. Direct indexing is the precondition "
        "for that line, never an addition to it."
    ),
)

SECURITIES_LENDING_BY_ASSET_CLASS = StructuralLever(
    name="Securities-lending revenue, verified by asset class",
    mechanism=(
        "Net securities-lending income as a fraction of average net assets, read from "
        "N-CSR Statements of Operations for fiscal years ending 2025-07 to 2025-12: "
        "IEFA 1.1 bp, VEA 3.0 bp, VXUS 3.4-3.6 bp, VWO 4.9-5.2 bp, IEMG 9.2-9.7 bp, "
        "VSS 13.0-13.4 bp, VB 3.0 bp. §851(b)(2)(A) lists lending payments as qualifying "
        "RIC income, so the revenue is structural rather than incidental."
    ),
    benchmark=Benchmark.STATED_INDEX,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.ALREADY_COUNTED,
    low_bp=0.0,
    central_bp=0.5,
    high_bp=2.0,
    conditions=(
        "The 1 bp already booked was computed on US total-market funds. International "
        "funds earn two to five times that and international small-cap about thirteen "
        "times, so a portfolio 20% international earns roughly 1.5 bp rather than 1.0. "
        "US small-cap does *not* show the premium (VB 3.0 bp), so this is an "
        "international and emerging-market lending-demand effect, not a size effect. Two "
        "same-asset-class funds differ threefold (IEFA 1.1 against VEA 3.0), so the "
        "sponsor matters more than the asset class."
    ),
    falsifier=(
        "A later fiscal year in which the international premium disappears, or a fund "
        "whose Statement of Operations shows the manager retaining the split."
    ),
    double_count_note=(
        "NOT ADDITIVE — the same line already in the edge budget at 1 bp, verified and "
        "revised up by about half a basis point for an internationally diversified "
        "portfolio. Immaterial either way, and recorded so the 1 bp is not re-derived."
    ),
)

DEFERRAL_HURDLE = StructuralLever(
    name="Deferred unrealised gain (a hurdle, not a saving)",
    mechanism=(
        "An unrealised gain is an interest-free loan whose principal compounds. §1014 "
        "extinguishes it at death. `deferral_value` prices the loan at 84.1 bp/yr over "
        "30 years and the forgiveness at a further 78.1 bp, summing to a horizon-free "
        "162.2 bp."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.NOT_BOOKABLE,
    low_bp=0.0,
    central_bp=84.1,
    high_bp=162.2,
    conditions=(
        "Taxable account and a positive long-term rate. Zero in the 0% bracket and in "
        "every shelter. The function is sharply concave in turnover: realising a tenth "
        "of standing gain each year already costs 41.5 bp of the 84.1."
    ),
    falsifier=(
        "Repeal of §1014 in favour of carryover or deemed-realisation basis, which "
        "removes the forgiveness half; or a jurisdiction taxing gains on accrual, which "
        "removes both."
    ),
    double_count_note=(
        "NOT BOOKABLE. It is the cost of a policy nobody proposed, so booking it as an "
        "edge would be claiming credit for not doing something. It belongs in the budget "
        "as a **hurdle** every future turnover-bearing sleeve must clear, and it is "
        "larger than every line in the current budget except fund cost."
    ),
)

MUNICIPAL_BONDS = StructuralLever(
    name="Municipal bonds for a taxable bond allocation",
    mechanism=(
        "§103(a) excludes state and local bond interest from gross income, and Treas. "
        "Reg. §1.1411-1(d)(4)(i) names it as excluded from net investment income too, so "
        "the tax-equivalent yield divides by the full 40.8%. At 2026-07-29 the pick-up "
        "over Treasuries runs 7 bp at two years, 43 at five, 80 at ten and 222 at thirty."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.NOT_BOOKABLE,
    low_bp=0.0,
    central_bp=0.0,
    high_bp=222.0,
    conditions=(
        "Requires a bond allocation held in a **taxable** account. The reference investor "
        "has none, because §1's ranking puts bonds first into the shelter by a factor of "
        "four over any equity sleeve — so this lever activates only once bond allocation "
        "exceeds shelter capacity. It is also strongly maturity-dependent: the break-even "
        "marginal rate falls from 39.8% at two years to 15.6% at thirty, so any rule of "
        "the form 'municipals for taxable accounts' is wrong at the short end."
    ),
    falsifier=(
        "A muni/Treasury yield ratio above one minus the investor's marginal rate at the "
        "maturity actually held; or default and call risk repricing the spread, which "
        "this comparison does not adjust for."
    ),
    double_count_note=(
        "NOT BOOKABLE for the reference investor, at zero, because shelter capacity "
        "covers the bond allocation. Sized so an investor whose does not can read it off."
    ),
)

SECTION_1256 = StructuralLever(
    name="Section 1256 60/40 treatment",
    mechanism=(
        "§1256(a)(3) splits gain on a regulated futures contract 60% long-term / 40% "
        "short-term regardless of holding period, and §1256(a)(1) marks it to market "
        "annually. The blended top rate is 30.6% against 40.8% ordinary and 23.8% "
        "long-term."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.NOT_BOOKABLE,
    low_bp=0.0,
    central_bp=0.0,
    high_bp=51.0,
    conditions=(
        "Requires a futures-based position, which the reference portfolio does not hold "
        "and which decision 0004 forbids while leverage stays at zero. The high figure is "
        "the rate saving on a 5%/yr return against ordinary annual treatment. Against a "
        "deferred long-only equity holding, §1256 is worse by 82 bp/yr over 30 years "
        "because mark-to-market destroys the deferral in the line above."
    ),
    falsifier=(
        "A flat rate schedule, which collapses the 60/40 blend to the same rate; or a "
        "strategy whose gains would have been long-term and deferred anyway, against "
        "which §1256 is a cost."
    ),
    double_count_note=(
        "NOT BOOKABLE. It is a property of an instrument this portfolio does not hold, "
        "and its benefit is inseparable from the leverage decision that decision 0004 "
        "settles. Reported so the capital-efficiency analysis in the synthesis has a "
        "number rather than an adjective."
    ),
)

ACCOUNT_TYPE = StructuralLever(
    name="Traditional against Roth, and the HSA",
    mechanism=(
        "`traditional_and_roth_are_equivalent`: the two wrappers are algebraically "
        "identical when the contribution and withdrawal rates match, so the whole "
        "difference is a forecast of one's own future marginal rate. The HSA is the one "
        "genuinely dominant wrapper — deductible in, untaxed inside, untaxed out for "
        "qualified medical expense, and FICA-free through payroll."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.PROBABILISTIC,
    additivity=Additivity.NOT_BOOKABLE,
    low_bp=0.0,
    central_bp=0.0,
    high_bp=0.0,
    conditions=(
        "The HSA's value is a dollar amount bounded by a contribution limit — $4,400 "
        "self-only and $8,750 family for 2026, plus a statutory $1,000 age-55 catch-up "
        "that is not indexed — not a rate on a portfolio of arbitrary size. California "
        "taxes HSA contributions, earnings as earned, and internal gains, removing the "
        "first two legs for residents."
    ),
    falsifier=(
        "A jurisdiction where the two wrappers are not algebraically equivalent at equal "
        "rates, which would mean a rule beyond the ones modelled here."
    ),
    double_count_note=(
        "NOT BOOKABLE. Choosing the wrapper is a rate forecast, so probabilistic; "
        "sequencing assets across wrappers is the asset-location line already booked; "
        "and the HSA is a dollar lever that does not express as bp on a portfolio."
    ),
)

CHARITABLE_AND_NUA = StructuralLever(
    name="Charitable gift of appreciated shares, NUA, tax-gain harvesting",
    mechanism=(
        "§170 allows a deduction at fair market value for long-term appreciated property "
        "with no §170(e) claw-back of the gain, so a gift converts deferral into "
        "forgiveness. §402(e)(4)(B) excludes net unrealised appreciation on employer "
        "securities from ordinary treatment: 13.6 bp/yr for a 10% position at 20% basis "
        "distributed in ten years. Realising gain inside the 0% bracket — $98,900 of "
        "taxable income joint, $49,450 single for 2026 — is worth 47.6 bp/yr on a fifth "
        "of the portfolio over ten years."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.NOT_BOOKABLE,
    low_bp=0.0,
    central_bp=0.0,
    high_bp=48.0,
    conditions=(
        "Each requires a circumstance rather than a decision: pre-existing charitable "
        "intent, employer securities inside a qualified plan, or a low-income year. The "
        "2025 act made the charitable arithmetic worse from 2026 — a new 0.5%-of-AGI "
        "floor under §170(b)(1)(I) that absorbs capital-gain property *first*, and a "
        "rewritten §68 capping the deduction's value at 37% x (1 - 2/37) = 35%. NUA is "
        "the one appreciated asset that does **not** get a §1014 step-up, being income "
        "in respect of a decedent."
    ),
    falsifier=(
        "For the charitable line, an investor with no giving: donating to capture a tax "
        "benefit is a transfer, not a return. For NUA, an employer without a stock plan."
    ),
    double_count_note=(
        "NOT BOOKABLE as portfolio return. A cheaper way to do something the investor "
        "was doing anyway is a real saving and not an edge, and counting it as one would "
        "let any spending decision become alpha."
    ),
)

AVOIDANCES = StructuralLever(
    name="Errors avoided: wash sales into an IRA, non-qualified dividends",
    mechanism=(
        "Revenue Ruling 2008-5 holds that a loss is disallowed under §1091(a) when the "
        "replacement is bought in the taxpayer's IRA and that **no** §1091(d) basis "
        "increase follows, so the deduction is destroyed rather than deferred: 119 bp on "
        "a 5%-of-portfolio disallowance. §1(h)(11)(B)(iii) requires more than 60 days of "
        "holding inside a 121-day window for a dividend to be qualified; a fund only 70% "
        "qualified on a 2% yield loses 10.2 bp/yr."
    ),
    benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
    certainty=Certainty.DETERMINISTIC,
    additivity=Additivity.NOT_BOOKABLE,
    low_bp=0.0,
    central_bp=0.0,
    high_bp=119.0,
    conditions=(
        "Avoiding an error is worth its cost only to an investor who would have made it. "
        "The engineering consequence is concrete: wash-sale scanning must be "
        "household-wide across IRAs and a spouse's accounts, because a same-account check "
        "converts a deferred loss into a destroyed one."
    ),
    falsifier=(
        "Withdrawal of Revenue Ruling 2008-5, or a §1091(d) amendment extending basis "
        "relief to retirement accounts."
    ),
    double_count_note=(
        "NOT BOOKABLE. An avoided mistake is not a return source, and booking it would "
        "let any arbitrary error become an edge by being large enough."
    ),
)

STRUCTURAL_LEDGER: tuple[StructuralLever, ...] = (
    FUND_STRUCTURE,
    LOT_SELECTION,
    FOREIGN_TAX_CREDIT,
    HARVESTING_FEE,
    SECURITIES_LENDING_BY_ASSET_CLASS,
    DEFERRAL_HURDLE,
    MUNICIPAL_BONDS,
    SECTION_1256,
    ACCOUNT_TYPE,
    CHARITABLE_AND_NUA,
    AVOIDANCES,
)
"""Every lever examined, sized, and classified. Add a line only with a primary source, a
condition, a falsifier, and an explicit verdict on whether it double-counts."""

BOOKED_COUNTERFACTUAL_BUDGET_BP = 89.0
"""The own-counterfactual total already committed in
:mod:`portfolio_edge.studies.outperformance_horizon`. Repeated here so
:func:`revised_counterfactual_budget_bp` cannot silently drift from it."""


def revised_counterfactual_budget_bp() -> float:
    """The 89 bp budget, plus the additive lines, plus the corrections.

    Corrections carry a negative ``central_bp`` and are marked ``ALREADY_COUNTED``, so
    they reduce the total rather than adding to it. That is the whole reason the ledger
    distinguishes three additivity classes instead of two.
    """
    additive = additive_total(STRUCTURAL_LEDGER).central_bp
    corrections = sum(
        lever.central_bp
        for lever in STRUCTURAL_LEDGER
        if lever.additivity is Additivity.ALREADY_COUNTED
        and lever.benchmark is Benchmark.COUNTERFACTUAL_HOLDING
    )
    return BOOKED_COUNTERFACTUAL_BUDGET_BP + additive + corrections
