"""Tax-loss harvesting and direct indexing, modelled rather than quoted.

This module is the executable record behind
``docs/research/harvesting-and-direct-indexing.md``. It exists because the
harvesting line in :mod:`portfolio_edge.studies.tax_structure` is a *lookup* — a
published vendor-adjacent decay profile, taken on trust — and a lookup cannot answer
the two questions that decide the case for a specific investor:

1. **How much loss is actually harvestable**, given the volatility of the holdings,
   the dispersion *within* the index, the contribution rate and the elapsed time.
2. **How much of that loss can be used**, given that 26 U.S.C. §1211(b) caps the
   deduction of net capital loss against ordinary income at $3,000 a year and
   §1212(b) merely carries the rest forward.

The two are separated on purpose, in two functions with no shared state.
:func:`simulate_harvest_yield` is a market model and contains no tax law.
:func:`value_harvesting` is tax law and contains no market model. Conflating them is
how a harvesting figure gets quoted at its gross yield.

The identity that organises the valuation
-----------------------------------------
Write ``H`` for the losses harvested over a lifetime, ``U`` for the part of ``H``
actually *used* against gains or against ordinary income before disposal, and ``C =
H - U`` for the capital-loss carryforward standing at the end. Harvesting reduces the
account's aggregate basis by exactly ``H``. Therefore, against an identical
never-selling fund position:

* **On liquidation**, the extra gain realised is ``H``, the carryforward absorbs
  ``C`` of it, and the residue taxed is exactly ``U``. So harvesting costs
  ``capital-gain rate x U`` at the end and saved ``rate-at-use x U`` along the way.
  **The whole permanent benefit is the rate difference on ``U``**, plus the time
  value of the deferral. Every dollar of ``H`` that is never used is worth zero.
* **On a §1014 step-up at death, or an outright gift of the appreciated shares under
  §170**, the terminal gain is never taxed, so the ``capital-gain rate x U`` clawback
  never happens and the early saving is permanent. But the carryforward ``C`` is
  destroyed: IRS Publication 559 states that a decedent's capital losses "including
  capital loss carryovers) can be deducted only on the decedent's final income tax
  return" and that "you can't deduct any unused NOL or capital loss on the estate's
  income tax return".

So under **every** disposal path the answer turns on ``U`` and not on ``H``, and ``U``
is capped by the investor's own realised gains plus $3,000 a year. That is the finding
this module exists to make computable, and it is the reason a harvesting figure is not
a property of a strategy but of a taxpayer.

Scope and honesty
-----------------
US federal individual investor, ``as of 2026-08-23``. State income tax is excluded and
additive. Nothing here is personalised advice. The market model is a **forecast**: a
lognormal factor model whose parameters are arguments, two of which
(:mod:`portfolio_edge.studies._tax_loss_harvesting_tables`) are estimated from the
committed Ken French files and one of which — the drift — is an assumption carried over
from ``tax_structure`` for comparability. The tax arithmetic is **deterministic** given
the rates. Keep the two classes apart when quoting anything from here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.studies.tax_structure import TaxRegime

FloatArray = NDArray[np.float64]

AS_OF: Final = "2026-08-23"
"""Every rate, threshold, fee and statutory citation in this module is as of this date."""

JURISDICTION: Final = "US federal"

ORDINARY_OFFSET_CAP: Final = 3_000.0
"""26 U.S.C. §1211(b)(1): $3,000, or $1,500 for a married individual filing separately.

Last amended by Pub. L. 99-514 in 1986; the $3,000 figure itself dates from the 1976
and 1977 amendments and has never been indexed. Its real value has fallen by roughly
the whole of the intervening inflation, which is why a lever that looked material to a
1978 taxpayer is a rounding error on a seven-figure account today.
"""

WASH_SALE_WINDOW_DAYS: Final = 30
"""26 U.S.C. §1091(a): 30 days before or after the sale, "substantially identical"."""

MIDDLE_BRACKET: Final = TaxRegime(
    label="US 32% ordinary / 15% long-term bracket, above the §1411 threshold",
    jurisdiction=JURISDICTION,
    as_of=AS_OF,
    ordinary_income=0.32,
    long_term_capital_gain=0.15,
    net_investment_income=0.038,
)
"""35.8% / 18.8%.

``tax_structure`` carries the 23.8% and 15% columns but not this one, and
``structural-and-tax-edges.md`` §8.1 shows it is the *third* live combination for a US
investor: the §1411 threshold is an unindexed $250,000 of modified AGI while the 20%
long-term rate starts above $613,700, so 18.8% is reachable and "20% without 3.8%" is
not. A harvesting answer that omits it omits the bracket most likely to hold here.
"""


# --------------------------------------------------------------------------------------
# The market model: how much loss is harvestable
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MarketAssumptions:
    """A lognormal one-factor model for the holdings of a taxable equity account.

    Every field is an argument because every one of them is either an estimate with a
    stated resolution or an outright forecast. ``annual_idiosyncratic_volatility`` is
    the parameter the whole answer is most sensitive to and the one this repository can
    only bound: see
    :func:`portfolio_edge.studies._tax_loss_harvesting_tables.idiosyncratic_volatility`.

    Setting ``annual_idiosyncratic_volatility`` to zero turns the direct index into a
    single fund and the model into the *fund-level* harvesting case, where the only
    harvestable losses are market-wide ones. That is not a special case bolted on; it
    is the same model at the boundary, and it is how the two routes are compared on
    like terms.
    """

    annual_total_log_drift: float
    annual_market_volatility: float
    annual_idiosyncratic_volatility: float
    dividend_yield: float

    def __post_init__(self) -> None:
        if self.annual_market_volatility <= 0.0:
            raise ValueError("annual_market_volatility must be positive")
        if self.annual_idiosyncratic_volatility < 0.0:
            raise ValueError("annual_idiosyncratic_volatility cannot be negative")
        if not 0.0 <= self.dividend_yield < 1.0:
            raise ValueError("dividend_yield must lie in [0, 1)")

    @property
    def annual_price_log_drift(self) -> float:
        """Total return less the dividend yield: the drift of the *price*, which is what
        a cost basis is compared against."""
        return self.annual_total_log_drift - self.dividend_yield


@dataclass(frozen=True)
class HarvestRule:
    """The operating rule of the account, separately from the tax treatment of it."""

    years: int
    harvest_threshold: float
    contribution_rate: float
    lots_per_month: int
    paths: int
    seed: int
    reinvest_dividends: bool = True

    def __post_init__(self) -> None:
        if self.years < 1:
            raise ValueError("years must be at least 1")
        if not 0.0 < self.harvest_threshold < 1.0:
            raise ValueError("harvest_threshold must lie in (0, 1)")
        if self.contribution_rate < 0.0:
            raise ValueError("contribution_rate cannot be negative")
        if self.lots_per_month < 1:
            raise ValueError("lots_per_month must be at least 1")
        if self.paths < 1:
            raise ValueError("paths must be at least 1")


@dataclass(frozen=True)
class HarvestYieldPaths:
    """Per-path, per-year output of the market model. No tax law has touched this.

    All loss and value figures are expressed **as a fraction of the account's own mean
    value in that year**, which is the only normalisation under which a "bp/yr" claim
    means anything when the account is growing and receiving contributions.

    Attributes:
        short_term_loss: ``(paths, years)`` losses realised on lots held 12 months or
            less. 26 U.S.C. §1222(1).
        long_term_loss: ``(paths, years)`` losses realised on lots held more than 12
            months. §1222(3).
        harvest_turnover: ``(paths, years)`` proceeds sold as a fraction of mean account
            value, which is what a bid-ask spread is charged on.
        mean_account_value: ``(paths, years)`` account value, indexed to 1.0 at outset.
        terminal_value: ``(paths,)`` account value at the horizon.
        terminal_basis_harvested: ``(paths,)`` aggregate cost basis at the horizon in
            the harvested account.
        terminal_basis_held: ``(paths,)`` aggregate cost basis at the horizon in an
            otherwise identical account that never sold. The difference between the two
            is the lifetime harvested loss, which :func:`value_harvesting` checks.
        embedded_gain_fraction: ``(paths,)`` unrealised gain as a fraction of terminal
            value in the harvested account. This is the lock-in number: it is what a
            later decision to leave the strategy would have to realise.
    """

    short_term_loss: FloatArray
    long_term_loss: FloatArray
    harvest_turnover: FloatArray
    mean_account_value: FloatArray
    terminal_value: FloatArray
    terminal_basis_harvested: FloatArray
    terminal_basis_held: FloatArray
    embedded_gain_fraction: FloatArray
    assumptions: MarketAssumptions
    rule: HarvestRule

    @property
    def total_loss(self) -> FloatArray:
        """Harvested loss per year as a fraction of that year's mean account value."""
        return self.short_term_loss + self.long_term_loss

    def decay_curve(self, quantile: float = 50.0) -> FloatArray:
        """The gross harvest yield by year, at a chosen quantile across market paths.

        This is the curve a headline "1% a year" hides. It is steeply front-loaded and,
        without new money, it approaches zero: the mechanism is that loss lots are
        systematically sold and gain lots systematically retained, so the account's
        basis falls towards its market value and stops producing losses.
        """
        return np.asarray(
            np.percentile(self.total_loss, quantile, axis=0), dtype=np.float64
        )


def simulate_harvest_yield(
    assumptions: MarketAssumptions, rule: HarvestRule
) -> HarvestYieldPaths:
    """Simulate the losses a monthly-harvested taxable equity account can realise.

    Mechanics, stated because each is a modelling choice that moves the answer:

    * **Monthly steps.** The month is the natural grid: it is longer than the 30-day
      §1091 window, so a replacement bought at one month end and sold at the next never
      creates a wash sale within the account.
    * **A lot is a position.** Each lot receives an independent idiosyncratic shock, so
      the model assumes the account is broad enough that two lots are rarely the same
      security. That understates the co-movement of two vintages of the same holding
      and therefore slightly *overstates* how smooth the harvest yield is within a
      market path. It does not bias the mean, because the mean depends only on each
      lot's marginal distribution, and the market factor — the dominant source of
      covariance across lots — is retained exactly.
    * **Harvesting is a swap, not a withdrawal.** A lot trading below
      ``1 - harvest_threshold`` of its basis is sold and the proceeds are immediately
      reinvested at the current price, so the account's *value* is unchanged and its
      *basis* falls by the realised loss. This is what a direct-index manager does:
      sells the loser, buys a correlated name that is not substantially identical.
    * **Contributions and reinvested dividends create fresh lots**, at the current
      price, which is the whole reason a contributing investor's harvest yield does not
      decay to zero.
    What is deliberately **not** modelled is giving during life. An annual gift of the
    most-appreciated lots would remove exactly the ossified lots that no longer harvest,
    and so would slow the decay below. It is left out because the same gift is available
    to the fund holder and does the same job there, so including it would credit
    harvesting with a benefit that is not harvesting's. It runs in harvesting's favour
    and is unbooked.

    The one thing this function does **not** model is the wash-sale rule itself, in
    either direction. Within the account the monthly grid makes it inapplicable; across
    accounts it is a behavioural failure rather than a market outcome, and
    :func:`value_harvesting` prices it as a disallowance fraction instead.
    """
    months = rule.years * 12
    step = 1.0 / 12.0
    root = math.sqrt(step)
    market_variance = assumptions.annual_market_volatility**2
    market_drift = (assumptions.annual_price_log_drift - 0.5 * market_variance) * step
    market_sigma = assumptions.annual_market_volatility * root
    idio_drift = -0.5 * assumptions.annual_idiosyncratic_volatility**2 * step
    idio_sigma = assumptions.annual_idiosyncratic_volatility * root

    slots = months * rule.lots_per_month
    shape = (rule.paths, slots)
    basis = np.zeros(shape, dtype=np.float64)
    shares = np.zeros(shape, dtype=np.float64)
    log_price = np.zeros(shape, dtype=np.float64)
    live = np.zeros(shape, dtype=bool)
    age = np.zeros(shape, dtype=np.int32)

    short = np.zeros((rule.paths, rule.years), dtype=np.float64)
    long = np.zeros((rule.paths, rule.years), dtype=np.float64)
    turnover = np.zeros((rule.paths, rule.years), dtype=np.float64)
    value_sum = np.zeros((rule.paths, rule.years), dtype=np.float64)
    held_basis = np.zeros(rule.paths, dtype=np.float64)

    generator = np.random.default_rng(rule.seed)
    monthly_contribution = rule.contribution_rate / 12.0
    monthly_dividend = assumptions.dividend_yield / 12.0
    cursor = 0

    for month in range(months):
        year = month // 12
        if month > 0:
            market = market_drift + market_sigma * generator.standard_normal(rule.paths)
            idio = idio_drift + idio_sigma * generator.standard_normal(shape)
            log_price = np.where(live, log_price + market[:, None] + idio, log_price)
            age = age + live

        value = np.where(live, shares * np.exp(log_price), 0.0)
        account = value.sum(axis=1)

        if month == 0:
            new_money = np.ones(rule.paths, dtype=np.float64)
        else:
            new_money = monthly_contribution * account
            if rule.reinvest_dividends:
                new_money = new_money + monthly_dividend * account

        per_lot = new_money / rule.lots_per_month
        window = slice(cursor, cursor + rule.lots_per_month)
        basis[:, window] = per_lot[:, None]
        shares[:, window] = per_lot[:, None]
        log_price[:, window] = 0.0
        live[:, window] = True
        age[:, window] = 0
        cursor += rule.lots_per_month
        held_basis += new_money

        value = np.where(live, shares * np.exp(log_price), 0.0)
        value_sum[:, year] += value.sum(axis=1)

        harvestable = live & (value < basis * (1.0 - rule.harvest_threshold))
        loss = np.where(harvestable, basis - value, 0.0)
        is_long = harvestable & (age > 12)
        long[:, year] += np.where(is_long, loss, 0.0).sum(axis=1)
        short[:, year] += np.where(harvestable & ~is_long, loss, 0.0).sum(axis=1)
        turnover[:, year] += np.where(harvestable, value, 0.0).sum(axis=1)

        basis = np.where(harvestable, value, basis)
        shares = np.where(harvestable, value, shares)
        log_price = np.where(harvestable, 0.0, log_price)
        age = np.where(harvestable, 0, age)

    mean_value = value_sum / 12.0
    final_value = np.where(live, shares * np.exp(log_price), 0.0).sum(axis=1)
    final_basis = np.where(live, basis, 0.0).sum(axis=1)
    return HarvestYieldPaths(
        short_term_loss=short / mean_value,
        long_term_loss=long / mean_value,
        harvest_turnover=turnover / mean_value,
        mean_account_value=mean_value,
        terminal_value=final_value,
        terminal_basis_harvested=final_basis,
        terminal_basis_held=held_basis,
        embedded_gain_fraction=(final_value - final_basis) / final_value,
        assumptions=assumptions,
        rule=rule,
    )


# --------------------------------------------------------------------------------------
# The tax model: how much of it can be used
# --------------------------------------------------------------------------------------


class Disposal(Enum):
    """What eventually happens to the position. This decides the sign of the reversal."""

    LIQUIDATE = "liquidate"
    """Sold at the horizon and the gain taxed. Harvesting's basis reduction is clawed
    back in full, so only the rate difference and the time value survive."""

    STEP_UP = "step_up"
    """Held until death. 26 U.S.C. §1014 resets basis to fair market value, so the
    clawback never happens — but any unused capital-loss carryforward dies with the
    taxpayer (IRS Publication 559)."""

    GIFT = "gift"
    """Given to charity. §170 allows a fair-market-value deduction for long-term
    publicly traded stock and the gain is never recognised, so the basis reduction is
    forgiven exactly as under §1014. The carryforward dies just the same, and the §170
    percentage limits bind on the deduction rather than on this comparison."""


@dataclass(frozen=True)
class LossUsage:
    """The taxpayer's own capacity to absorb a realised loss.

    This is investor data, not market data, and it is the input the vendor figures
    assume away. Every field except the cap is a property of the person.

    Attributes:
        account_value: Dollar value of the taxable account at the outset. The $3,000
            cap is a nominal amount, so its basis-point value is inversely proportional
            to this and to nothing else.
        annual_long_term_gain_fraction: Long-term capital gain the investor realises
            each year from any source — rebalancing, a concentrated position, a fund's
            own distributions — as a fraction of the account.
        annual_short_term_gain_fraction: The same for short-term gain, which is taxed
            at the ordinary rate and is therefore worth far more to shelter.
        ordinary_offset_cap: §1211(b). An argument only so a married-filing-separately
            taxpayer can state $1,500.
        marginal_ordinary_rate_on_wages: The rate the $3,000 deduction is worth. This is
            deliberately **not** ``regime.ordinary``: the §1411 surtax reaches net
            investment income, not wages, so applying the all-in investment rate to a
            deduction against salary overstates it. Where the loss also reduces net
            investment income the deduction is worth up to 3.8 points more, which this
            module reports as a sensitivity rather than booking.
        wash_sale_disallowed_fraction: The fraction of harvested losses destroyed
            outright because a substantially identical security was bought inside an
            IRA within the §1091 window. Revenue Ruling 2008-5 disallows the loss and
            denies the §1091(d) basis increase to the IRA, so this is the one error in
            harvesting whose cost is permanent rather than timing.
    """

    account_value: float
    annual_long_term_gain_fraction: float = 0.0
    annual_short_term_gain_fraction: float = 0.0
    ordinary_offset_cap: float = ORDINARY_OFFSET_CAP
    marginal_ordinary_rate_on_wages: float = 0.37
    wash_sale_disallowed_fraction: float = 0.0

    def __post_init__(self) -> None:
        if self.account_value <= 0.0:
            raise ValueError("account_value must be positive")
        for name in (
            "annual_long_term_gain_fraction",
            "annual_short_term_gain_fraction",
            "wash_sale_disallowed_fraction",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.ordinary_offset_cap < 0.0:
            raise ValueError("ordinary_offset_cap cannot be negative")
        if not 0.0 <= self.marginal_ordinary_rate_on_wages < 1.0:
            raise ValueError("marginal_ordinary_rate_on_wages must lie in [0, 1)")


@dataclass(frozen=True)
class HarvestingValue:
    """What harvesting was worth, per market path, with its working shown.

    ``benefit_bp`` is the annualised difference in after-tax log terminal wealth against
    an otherwise identical account holding a fund and never selling, in basis points a
    year. It is net of the fee difference and of trading costs, and it is a
    **distribution**: quote :meth:`quantile`, not the mean alone.

    The other four arrays are in units of the account's own initial value, one per
    market path, summed over the whole horizon: ``gross_harvested`` is every loss
    realised, ``used`` is the part that produced a tax saving, ``unused_carryforward``
    is what stood at the horizon under §1212(b), and ``ordinary_offset`` is the part of
    ``used`` that went against ordinary income under §1211(b).
    """

    benefit_bp: FloatArray
    gross_harvested: FloatArray
    used: FloatArray
    unused_carryforward: FloatArray
    ordinary_offset: FloatArray
    disposal: Disposal
    regime: TaxRegime
    usage: LossUsage

    def quantile(self, q: float) -> float:
        return float(np.percentile(self.benefit_bp, q))

    @property
    def median_bp(self) -> float:
        return self.quantile(50.0)

    @property
    def probability_negative(self) -> float:
        return float(np.mean(self.benefit_bp < 0.0))

    @property
    def usable_share(self) -> float:
        """Fraction of harvested losses that ever produced a tax saving.

        The single most informative diagnostic in this module. A vendor figure is
        implicitly quoting the case where this is 1.0.
        """
        gross = float(np.sum(self.gross_harvested))
        if gross <= 0.0:
            return 0.0
        return float(np.sum(self.used)) / gross


def value_harvesting(
    paths: HarvestYieldPaths,
    *,
    regime: TaxRegime,
    usage: LossUsage,
    disposal: Disposal,
    direct_index_fee: float,
    replaced_fund_cost: float,
    round_trip_cost: float = 0.0004,
    reinvestment_log_growth: float | None = None,
) -> HarvestingValue:
    """Value a harvest-yield simulation under one bracket, one taxpayer and one exit.

    The comparison is against **the same account holding the fund it replaced and never
    selling**, which is the investor's own counterfactual and not a cheap index. Both
    arms receive the same contributions and hold the same pre-tax exposure, so their
    pre-tax values are equal by construction and the whole difference is:

    ``benefit = future value of the tax saved along the way``
    ``        - the extra tax paid at disposal``
    ``        - the fee difference``
    ``        - the trading cost of harvesting``

    Ordering follows §1222 and §1212(b): short-term losses meet short-term gains and
    long-term losses meet long-term gains, the excess of either crosses over, and only
    then does §1211(b) allow up to $3,000 against ordinary income, short-term first.
    Whatever is left carries forward with its character and waits.

    ``round_trip_cost`` is the round-trip spread and commission charged on harvested
    proceeds. It defaults to 4 bp, which is the order of a large-cap US equity spread;
    it is an assumption, and a small-cap direct index would pay several times it.

    ``reinvestment_log_growth`` is the rate at which a tax saving compounds once it is
    put back into the account. It defaults to the market's total log drift less the tax
    on its dividend, which is the correct rate for a dollar going into the same taxable
    account under a deferral policy. It is **not** the pre-tax drift; using that would
    credit the saving with growth it never gets.

    A loss destroyed by a cross-account wash sale still reduces basis. Revenue Ruling
    2008-5 disallows the deduction and denies the IRA the §1091(d) basis increase, but
    the taxable account bought its replacement with the sale proceeds either way. So
    ``wash_sale_disallowed_fraction`` scales the deductible loss and deliberately does
    **not** scale the basis reduction: the taxpayer keeps the harm and loses the good.
    """
    if direct_index_fee < 0.0 or replaced_fund_cost < 0.0:
        raise ValueError("fees cannot be negative")
    if round_trip_cost < 0.0:
        raise ValueError("round_trip_cost cannot be negative")

    years = paths.rule.years
    allowed = 1.0 - usage.wash_sale_disallowed_fraction
    short = paths.short_term_loss * allowed
    long = paths.long_term_loss * allowed

    if reinvestment_log_growth is None:
        reinvestment_log_growth = (
            paths.assumptions.annual_total_log_drift
            - paths.assumptions.dividend_yield * regime.capital_gain
        )
    growth = math.exp(reinvestment_log_growth)
    short_gain = usage.annual_short_term_gain_fraction
    long_gain = usage.annual_long_term_gain_fraction
    # The simulation is indexed to 1.0 at the outset, so one simulation unit is
    # ``usage.account_value`` dollars and the nominal §1211(b) cap has to be put on
    # that scale before it can be compared with anything.
    cap = usage.ordinary_offset_cap / usage.account_value

    n = short.shape[0]
    carry_short = np.zeros(n, dtype=np.float64)
    carry_long = np.zeros(n, dtype=np.float64)
    saved_future_value = np.zeros(n, dtype=np.float64)
    used_total = np.zeros(n, dtype=np.float64)
    ordinary_used_total = np.zeros(n, dtype=np.float64)

    for year in range(years):
        scale = paths.mean_account_value[:, year]
        # Carryforwards are dollar amounts; the loss arrays are fractions of that
        # year's mean account value, so put everything on the account's own scale.
        st = short[:, year] * scale + carry_short
        lt = long[:, year] * scale + carry_long
        st_gain = short_gain * scale
        lt_gain = long_gain * scale

        used_st_against_st = np.minimum(st, st_gain)
        st -= used_st_against_st
        used_lt_against_lt = np.minimum(lt, lt_gain)
        lt -= used_lt_against_lt
        used_st_against_lt = np.minimum(st, lt_gain - used_lt_against_lt)
        st -= used_st_against_lt
        used_lt_against_st = np.minimum(lt, st_gain - used_st_against_st)
        lt -= used_lt_against_st

        ordinary_from_short = np.minimum(st, cap)
        st -= ordinary_from_short
        ordinary_from_long = np.minimum(lt, cap - ordinary_from_short)
        lt -= ordinary_from_long

        saving = (
            (used_st_against_st + used_lt_against_st) * regime.ordinary
            + (used_lt_against_lt + used_st_against_lt) * regime.capital_gain
            + (ordinary_from_short + ordinary_from_long)
            * usage.marginal_ordinary_rate_on_wages
        )
        saved_future_value += saving * growth ** (years - year - 1)
        used_total += (
            used_st_against_st
            + used_lt_against_lt
            + used_st_against_lt
            + used_lt_against_st
            + ordinary_from_short
            + ordinary_from_long
        )
        ordinary_used_total += ordinary_from_short + ordinary_from_long
        carry_short = st
        carry_long = lt

    gross_total = ((short + long) * paths.mean_account_value).sum(axis=1)
    carryforward = carry_short + carry_long

    held_value = paths.terminal_value
    if disposal is Disposal.LIQUIDATE:
        # Both arms sell at the horizon. The harvested arm's basis is lower by exactly
        # the lifetime harvested loss, and its carryforward absorbs part of the extra
        # gain; §1211(b) still caps whatever the gain cannot absorb, which is why this
        # is computed rather than netted.
        held_gain = held_value - paths.terminal_basis_held
        harvested_gain = held_value - paths.terminal_basis_harvested
        absorbed = np.minimum(carryforward, np.maximum(harvested_gain, 0.0))
        residual_relief = np.minimum(carryforward - absorbed, cap)
        held_after_tax = held_value - regime.capital_gain * np.maximum(held_gain, 0.0)
        terminal_tax = regime.capital_gain * np.maximum(
            harvested_gain - absorbed, 0.0
        ) - residual_relief * usage.marginal_ordinary_rate_on_wages
        harvested_after_tax = held_value - terminal_tax + saved_future_value
    else:
        # §1014 and §170 both forgive the gain outright, so the basis reduction is never
        # reversed. The carryforward, however, dies with the taxpayer (Publication 559).
        held_after_tax = held_value
        harvested_after_tax = held_value + saved_future_value

    # Fee and spread are recurring costs, so they belong in the log drag rather than as
    # a one-off subtraction from terminal wealth. The fee difference is what the direct
    # index charges less what the fund it replaced cost to own, which on this
    # repository's own audit is a *net* cost after securities lending, not a fee.
    turnover_per_year = paths.harvest_turnover.sum(axis=1) / years
    cost_bp = (
        direct_index_fee - replaced_fund_cost + round_trip_cost * turnover_per_year
    ) * 1e4
    benefit = (
        np.log(np.maximum(harvested_after_tax, 1e-12) / held_after_tax) / years * 1e4
        - cost_bp
    )
    return HarvestingValue(
        benefit_bp=benefit,
        gross_harvested=gross_total,
        used=used_total,
        unused_carryforward=carryforward,
        ordinary_offset=ordinary_used_total,
        disposal=disposal,
        regime=regime,
        usage=usage,
    )


# --------------------------------------------------------------------------------------
# Closed forms that do not need a simulation
# --------------------------------------------------------------------------------------


def ordinary_offset_ceiling_bp(
    *, account_value: float, marginal_ordinary_rate: float, cap: float = ORDINARY_OFFSET_CAP
) -> float:
    """The most harvesting can be worth to an investor with no realised gains at all.

    ``cap x rate / account value``, in basis points a year. It is a **ceiling**, reached
    only while the account is still producing at least $3,000 of losses a year, and it
    falls with account size because the cap is nominal. This one line explains most of
    the distance between a vendor headline and a real answer, and it needs no model.
    """
    if account_value <= 0.0:
        raise ValueError("account_value must be positive")
    if not 0.0 <= marginal_ordinary_rate < 1.0:
        raise ValueError("marginal_ordinary_rate must lie in [0, 1)")
    return cap * marginal_ordinary_rate / account_value * 1e4


def lock_in_exit_cost_bp(
    *, embedded_gain_fraction: float, regime: TaxRegime, remaining_years: int
) -> float:
    """Annualised cost of abandoning a low-basis position, spread over the years left.

    Direct indexing is a one-way door: the account holds hundreds of individual lots
    whose basis harvesting has deliberately driven down, and the only ways out are to
    sell and pay, to gift, or to die holding it. This prices the first. It is the
    mirror image of the harvesting benefit and it uses the same rate, which is the point
    — a strategy whose benefit is measured in single-digit basis points can be undone by
    one exit decision costing hundreds.
    """
    if not 0.0 <= embedded_gain_fraction < 1.0:
        raise ValueError("embedded_gain_fraction must lie in [0, 1)")
    if remaining_years < 1:
        raise ValueError("remaining_years must be at least 1")
    survived = 1.0 - regime.capital_gain * embedded_gain_fraction
    return -math.log(survived) / remaining_years * 1e4


def active_risk_from_substitution(
    *,
    annual_idiosyncratic_volatility: float,
    substituted_fraction: float,
    substitute_positions: float,
    substitute_correlation: float,
) -> float:
    """Active risk created by holding substitutes for part of the index.

    Harvesting is a swap: the account sells a name and buys a different one that is not
    substantially identical. From then on the account is not the index. Write ``w`` for
    the fraction of the portfolio held in substitutes, spread over ``m`` of them, and
    ``rho`` for the idiosyncratic correlation between a substitute and the name it
    replaced. The active return is the weighted difference of two idiosyncratic
    components, whose variance is ``2 (1 - rho) sigma^2`` per pair, diversified across
    ``m`` independent pairs:

    ``active risk = (w / sqrt(m)) x sigma_idio x sqrt(2 (1 - rho))``

    This is an **assumption-driven bound, not a measurement**. Nothing in this
    repository holds a direct-index account's holdings file, so ``w``, ``m`` and ``rho``
    are the reader's inputs. The measured upper bound on a deliberately crude
    49-position proxy is in
    :mod:`portfolio_edge.studies._tax_loss_harvesting_tables`, and it is far larger.
    """
    if annual_idiosyncratic_volatility < 0.0:
        raise ValueError("annual_idiosyncratic_volatility cannot be negative")
    if not 0.0 <= substituted_fraction <= 1.0:
        raise ValueError("substituted_fraction must lie in [0, 1]")
    if substitute_positions <= 0.0:
        raise ValueError("substitute_positions must be positive")
    if not -1.0 <= substitute_correlation <= 1.0:
        raise ValueError("substitute_correlation must lie in [-1, 1]")
    pair = math.sqrt(2.0 * (1.0 - substitute_correlation))
    return (
        substituted_fraction
        / math.sqrt(substitute_positions)
        * annual_idiosyncratic_volatility
        * pair
    )


# --------------------------------------------------------------------------------------
# The routes, ranked on what they cost to run and what they cost to undo
# --------------------------------------------------------------------------------------


class Reversibility(Enum):
    """How hard it is to stop doing this."""

    FREE = "free"
    """Stop at any time at no tax cost."""

    CHEAP = "cheap"
    """One or two fund positions to unwind; a single embedded gain to manage."""

    ONE_WAY = "one_way"
    """Hundreds of low-basis lots. Leaving means realising the accumulated gain, or
    never leaving."""


@dataclass(frozen=True)
class Route:
    """One way of pursuing the tax edge in a taxable account."""

    name: str
    annual_fee_bp: float
    decisions_per_year: float
    reversibility: Reversibility
    note: str


def routes() -> tuple[Route, ...]:
    """The five routes compared in the synthesis, with their stated running costs.

    Fees are the *incremental* annual cost over holding the fund the sleeve already
    holds. ``decisions_per_year`` is an operating-burden proxy: the number of times a
    human must look at the account and act, which is the constraint
    ``portfolio-recommendation.md`` names as deciding whether a procedure survives
    thirty years.
    """
    return (
        Route(
            name="Hold and never sell",
            annual_fee_bp=0.0,
            decisions_per_year=0.0,
            reversibility=Reversibility.FREE,
            note=(
                "Collects the §1014 step-up in full and pays nothing. It is the "
                "baseline every other route is measured against, and the deferral it "
                "preserves is worth 84 bp/yr at thirty years."
            ),
        ),
        Route(
            name="Direct contributions to whatever is furthest below target",
            annual_fee_bp=0.0,
            decisions_per_year=4.0,
            reversibility=Reversibility.FREE,
            note=(
                "Already in the plan. Worth zero as a tax line and everything as an "
                "exposure-control line: it is what lets the taxable account never sell."
            ),
        ),
        Route(
            name="Gift appreciated lots to charity or a donor-advised fund",
            annual_fee_bp=0.0,
            decisions_per_year=1.0,
            reversibility=Reversibility.FREE,
            note=(
                "§170 gives a fair-market-value deduction for long-term publicly traded "
                "stock and the gain is never recognised. Only worth doing to the extent "
                "the investor was giving anyway; it is a way of giving, not a return."
            ),
        ),
        Route(
            name="Fund-level harvesting between two similar funds",
            annual_fee_bp=0.0,
            decisions_per_year=2.0,
            reversibility=Reversibility.CHEAP,
            note=(
                "Sell the total-market fund at a loss, buy a different sponsor's "
                "total-market fund tracking a different index. Captures market-wide "
                "losses only, so it fires in drawdowns and not otherwise. No fee, "
                "because the two funds cost the same to own."
            ),
        ),
        Route(
            name="Direct indexing the taxable US core",
            annual_fee_bp=9.0,
            decisions_per_year=0.0,
            reversibility=Reversibility.ONE_WAY,
            note=(
                "Captures dispersion within the index, which is the only thing a fund "
                "cannot pass through. Costs a fee that is not deductible under §67(h), "
                "forfeits the fund's securities-lending offset, and cannot be undone."
            ),
        ),
    )


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._tax_loss_harvesting_tables import main

    main()
