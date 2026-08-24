"""Asset location for one stated investor: the plan, not the maxim.

This module is the executable record behind the investor-specific section of
``docs/research/structural-and-tax-edges.md``. It applies the ranking machinery in
:mod:`portfolio_edge.studies.tax_structure` to **named funds with filed tax
characteristics**, rather than to the four generic sleeves that module carries.

Why the fund level changes the answer. ``tax_structure``'s sleeve table assumes every
equity sleeve is **100% qualified**, so its priority for a foreign sleeve collapses to
``(q - w) y``. Three sponsors' own filings say otherwise, and the correction is not
small: Vanguard's 2025 foreign tax credit worksheet reports qualified foreign dividend
income of **66.27% of Box 1a for VEA** and **34.63% for VWO**; iShares designates
**34.82% for IEMG**; Avantis **44.48% for AVES**; Invesco **25% for IDMO**. The
non-qualified remainder is taxed at the *ordinary* rate, which is 17 pp higher at the
top bracket. Restoring the filed fraction reverses ``tax_structure``'s headline: the
emerging-market inversion disappears and **both emerging funds outrank US equity for
shelter capacity at every live US rate**.

**One denominator, stated once, because it is the trap.** Every yield here is a
**Box 1a yield**: the fund's ordinary dividend distribution as a fraction of net
assets, *grossed up* for the creditable foreign tax the §853 election makes the
shareholder report. Vanguard's worksheet defines Box 1a in exactly those terms —
"ordinary cash dividends paid by the Fund, short-term capital gains paid by the Fund,
and foreign taxes paid". A sponsor's filed ``foreign taxes / foreign source income``
ratio has a **different, smaller denominator** (foreign source income is 77-100% of
Box 1a), and multiplying a fund's total yield by it overstates the withholding. VEA
reconciles the two exactly: 6.068% of Box 1a divided by 79.6488% foreign source income
is 7.618%, which is the ratio VEA's own N-CSR files. They are the same fact in two
denominators, not two disagreeing measurements.

**Scope.** US federal, individual, ``as of 2026-08-22``. State income tax is excluded
and additive. This is a sizing exercise for one stated portfolio, not personalised
advice. No market data, no randomness, no forecast: every number is a function of a
stated regime and a filed fund characteristic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from portfolio_edge.studies.outperformance_horizon import (
    BASIS_POINT,
    Benchmark,
    Certainty,
    EdgeComponent,
)
from portfolio_edge.studies.tax_structure import TaxRegime

AS_OF = "2026-08-22"
"""Every fund characteristic below is stated as of this date."""


# --------------------------------------------------------------------------------------
# Regimes: the plausible federal range, not one silently selected bracket
# --------------------------------------------------------------------------------------


TOP_BRACKET = TaxRegime(
    label="US top marginal bracket",
    jurisdiction="US federal",
    as_of=AS_OF,
    ordinary_income=0.37,
    long_term_capital_gain=0.20,
    net_investment_income=0.038,
)
"""23.8% qualified / 40.8% ordinary.

Rev. Proc. 2025-32 §3.03 puts the 20% long-term rate above **$613,700** of taxable
income filing jointly and **$545,500** filing single for 2026, while the §1411
threshold is an unindexed $250,000 / $200,000 of modified AGI. **A taxpayer at the 20%
rate is therefore always past the surtax threshold**, which is why 20% without the
surtax is not a column anywhere in this module.
"""

UPPER_WITH_SURTAX = TaxRegime(
    label="US 15% long-term rate plus the §1411 surtax",
    jurisdiction="US federal",
    as_of=AS_OF,
    ordinary_income=0.32,
    long_term_capital_gain=0.15,
    net_investment_income=0.038,
)
"""18.8% qualified / 35.8% ordinary — the 2026 joint band from $403,550 to $512,450 of
taxable income, above the $250,000 surtax threshold. This is the bracket the emerging
inversion in ``tax_structure`` §1 straddles, and the reason it is stated separately."""

UPPER_MIDDLE = TaxRegime(
    label="US upper-middle bracket",
    jurisdiction="US federal",
    as_of=AS_OF,
    ordinary_income=0.24,
    long_term_capital_gain=0.15,
    net_investment_income=0.0,
)
"""15% qualified / 24% ordinary, below the surtax threshold."""

PLAUSIBLE_RANGE: tuple[TaxRegime, ...] = (TOP_BRACKET, UPPER_WITH_SURTAX, UPPER_MIDDLE)
"""The three regimes every result in this module is reported across.

``docs/charter.md`` requires that a result depending on a missing input show the
dependency rather than silently select a value. The investor's bracket is that input.
"""


# --------------------------------------------------------------------------------------
# A holding, characterised by what its own filings say it distributes
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Holding:
    """One named fund, with the three yields that decide where it belongs.

    All three are fractions of the fund's net assets, per year. They are kept apart
    rather than folded into a single "dividend yield and qualified fraction" because a
    fund can distribute a short-term capital gain (ordinary), a long-term capital gain
    (capital-gain rate) and a dividend of mixed character in the same year, and
    collapsing them loses exactly the information that decides the ranking.

    ``creditable_foreign_tax_yield`` is the amount the §853 election passes through, not
    the amount withheld at source. The two differ: a fund that fails the §901(k)
    fifteen-day holding-period test on part of its book, or whose reclaims are pending,
    passes through less than it paid, and **the shortfall is lost in every account
    including the taxable one**.
    """

    ticker: str
    name: str
    weight: float
    expense_ratio: float
    ordinary_yield: float
    capital_gain_rate_yield: float
    creditable_foreign_tax_yield: float
    source: str
    as_of: str

    def __post_init__(self) -> None:
        for name in (
            "weight",
            "expense_ratio",
            "ordinary_yield",
            "capital_gain_rate_yield",
            "creditable_foreign_tax_yield",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{self.ticker}: {name} must lie in [0, 1], got {value}")
        if not self.source.strip():
            raise ValueError(f"{self.ticker}: a holding without a source is not evidence")
        if not self.as_of.strip():
            raise ValueError(f"{self.ticker}: a fund characteristic without a date is a trap")

    @property
    def box_1a_yield(self) -> float:
        """Ordinary dividends as the shareholder reports them, gross of foreign tax."""
        return self.ordinary_yield + self.capital_gain_rate_yield

    def us_tax_bp(self, regime: TaxRegime) -> float:
        """US tax on this year's distributions, before any foreign tax credit, bp/yr."""
        gross = (
            regime.ordinary * self.ordinary_yield
            + regime.capital_gain * self.capital_gain_rate_yield
        )
        return gross / BASIS_POINT

    def sheltered_cost_bp(self, regime: TaxRegime) -> float:
        """Recurring cost inside a shelter, bp/yr — the forfeited credit and nothing else.

        Identical in a traditional account and a Roth, because §901 credits a foreign tax
        against a *US* tax and neither account generates one. This is why the Roth-versus-
        traditional choice cannot be made on the drag: for every holding it is the same
        number in both.
        """
        del regime  # a shelter's cost does not depend on the investor's bracket
        return self.creditable_foreign_tax_yield / BASIS_POINT

    def taxable_cost_bp(self, regime: TaxRegime) -> float:
        """Recurring cost in the taxable account, bp/yr.

        The foreign tax is paid at source either way; the US tax on the same income is
        then reduced by the credit, capped at the US tax because an unused §901 credit is
        not refundable.
        """
        foreign = self.creditable_foreign_tax_yield / BASIS_POINT
        us = self.us_tax_bp(regime)
        return foreign + us - min(foreign, us)

    def priority_bp(self, regime: TaxRegime) -> float:
        """``taxable cost - sheltered cost``: what a dollar of shelter saves, bp/yr."""
        return self.taxable_cost_bp(regime) - self.sheltered_cost_bp(regime)


# --------------------------------------------------------------------------------------
# The stated portfolio
# --------------------------------------------------------------------------------------


_TIDAL = (
    "Tidal Trust II Form N-CSR for the fiscal year ended 2026-01-31, filed 2026-04-09, "
    "accession 0001999371-26-008023."
)

VTI = Holding(
    ticker="VTI",
    name="Vanguard Morningstar Total Stock Market ETF",
    weight=0.20,
    expense_ratio=0.0003,
    ordinary_yield=0.0,
    capital_gain_rate_yield=0.01067,
    creditable_foreign_tax_yield=0.0,
    source=(
        "Vanguard's published fund-yield endpoint for portfolio 0970: SEC 30-day yield "
        "1.03% and forecast dividend yield 1.0670%, both effective 2026-07-31; expense "
        "ratio 0.03%. The fund was renamed from 'Vanguard Total Stock Market ETF' and "
        "its benchmark rebranded from CRSP to Morningstar US Total Market effective "
        "2026-07-29; objective and management are unchanged. The qualified fraction is "
        "taken as 1.00 and is an ASSUMPTION: no Vanguard QDI percentage was retrieved "
        "for VTI, whose table is rendered client-side."
    ),
    as_of="2026-07-31",
)

AVLV = Holding(
    ticker="AVLV",
    name="Avantis U.S. Large Cap Value ETF",
    weight=0.15,
    expense_ratio=0.0015,
    ordinary_yield=0.0,
    capital_gain_rate_yield=0.0177,
    creditable_foreign_tax_yield=0.0,
    source=(
        "American Century ETF Trust Form N-CSR for the fiscal year ended 2025-08-31, "
        "accession 0001710607-25-000307: ratio of net investment income to average net "
        "assets 1.77%, expense ratio 0.15% gross = net with no waiver, portfolio "
        "turnover 7%, and no capital-gain distribution in any of the four years filed. "
        "Actively managed. The qualified fraction is taken as 1.00 and is an ASSUMPTION: "
        "Avantis publishes a QDI percentage per fund and AVLV's was not retrieved."
    ),
    as_of="2025-08-31",
)

DFIV = Holding(
    ticker="DFIV",
    name="Dimensional International Value ETF",
    weight=0.10,
    expense_ratio=0.0027,
    ordinary_yield=0.0,
    capital_gain_rate_yield=0.04033,
    creditable_foreign_tax_yield=0.003226,
    source=(
        "Dimensional ETF Trust Form N-CSR for the fiscal year ended 2025-10-31, "
        "accession 0001133228-26-000245: ratio of net investment income to average net "
        "assets 3.71%, expense ratio 0.27%, turnover 6%, and zero capital-gain "
        "distribution in all five years filed. Its tax note designates, as percentages "
        "of investment company taxable income, Qualifying Dividend Income 100%, Foreign "
        "Source Income 100% and Foreign Tax Credit 8% under §853. Box 1a yield is "
        "3.71%/(1-0.08) = 4.033% and the credit is 8% of that. Both filed percentages "
        "are rounded to a whole point, which is the coarsest input in this table."
    ),
    as_of="2025-10-31",
)

VEA = Holding(
    ticker="VEA",
    name="Vanguard FTSE Developed Markets ETF",
    weight=0.10,
    expense_ratio=0.0003,
    ordinary_yield=0.008050372,
    capital_gain_rate_yield=0.015819628,
    creditable_foreign_tax_yield=0.001448432,
    source=(
        "Vanguard's 2025 foreign tax credit worksheet (FTCWS 012026): foreign source "
        "income 79.6488% of Box 1a, qualified foreign dividend income 66.2741% of "
        "Box 1a, foreign tax paid 6.46% of ordinary cash dividends, which is 6.068% of "
        "Box 1a. Yield is Vanguard's forecast dividend yield of 2.387% for portfolio "
        "0936 effective 2026-07-31 — a FORECAST, not a realised distribution, and "
        "Vanguard publishes no SEC yield for VEA. Vanguard's own FY2025 N-CSR "
        "designates foreign source income of $7,075,442,000 and foreign taxes of "
        "$538,664,000, a ratio of 7.613% on the foreign-source denominator, which "
        "reconciles with 6.068%/79.6488% = 7.618%. No capital-gain distribution "
        "2021-2025."
    ),
    as_of="2026-07-31",
)

IDMO = Holding(
    ticker="IDMO",
    name="Invesco S&P International Developed Momentum ETF",
    weight=0.05,
    expense_ratio=0.0025,
    ordinary_yield=0.032773,
    capital_gain_rate_yield=0.011258,
    creditable_foreign_tax_yield=0.001229,
    source=(
        "Invesco Exchange-Traded Fund Trust II Form N-CSR for the fiscal year ended "
        "2025-10-31, accession 0001193125-26-001460. Ratio of net investment income to "
        "average net assets 2.14%, expense ratio 0.25% unitary, PORTFOLIO TURNOVER 105%. "
        "Its tax note designates QUALIFIED DIVIDEND INCOME OF 25% of ordinary income "
        "dividends, and passes through foreign taxes of $0.0317 against foreign source "
        "income of $0.5841 per share, a rate of 5.43%; Box 1a yield is "
        "2.14%/(1-0.0543) = 2.263%. The fund's own statement of operations shows "
        "$2,049,253 of foreign tax WITHHELD against roughly $1.23m passed through as "
        "creditable, consistent with §901(k) disallowance at this turnover. Tax "
        "components of net assets at 2025-10-31 carried $32,959,121 of undistributed "
        "ordinary income and $11,582,181 of undistributed long-term capital gain on "
        "$2,081,578,000 of net assets, which the 2025-12-22 distribution then paid out "
        "as $0.68417 of short-term gain and $0.27579 of long-term gain per share. Those "
        "are carried here as 1.58% and 0.56% of net assets. ONE FISCAL YEAR, and the "
        "capital-gain line is the least durable number in this table."
    ),
    as_of="2025-10-31",
)

IEMG = Holding(
    ticker="IEMG",
    name="iShares Core MSCI Emerging Markets ETF",
    weight=0.05,
    expense_ratio=0.0009,
    ordinary_yield=0.016588,
    capital_gain_rate_yield=0.008862,
    creditable_foreign_tax_yield=0.002450,
    source=(
        "iShares 2025 Distribution Summary: Box 1a $2.045531 per share against "
        "$1.848602 of cash distributions and $0.196929 of foreign tax, so Box 1a is "
        "exactly gross of the tax and the credit is 9.627% of it; foreign source income "
        "76.99% of Box 1a; Box 2a zero. iShares 2025 QDI Summary: QUALIFIED DIVIDEND "
        "INCOME 34.82%. Yield is the 12-month trailing yield of 2.30% published on the "
        "fund page effective 2026-07-31, grossed to Box 1a at 2.545%; the 30-day SEC "
        "yield on the same date is 1.76% and is a one-month snapshot of a fund whose "
        "dividends are concentrated in the first half of the year. Expense ratio 0.09%, "
        "contractually capped through 2030-12-31 with no recoupment. No capital-gain "
        "distribution FY2021-FY2025."
    ),
    as_of="2026-07-31",
)

AVES = Holding(
    ticker="AVES",
    name="Avantis Emerging Markets Value ETF",
    weight=0.05,
    expense_ratio=0.0036,
    ordinary_yield=0.021709,
    capital_gain_rate_yield=0.017391,
    creditable_foreign_tax_yield=0.004598,
    source=(
        "Avantis 2025 tax centre: QUALIFIED DIVIDEND INCOME 44.48%, foreign source "
        "income 92.34% of Box 1a; its 2025 ICI file gives Box 1a $2.094150712 per share "
        "against $1.8479 of cash and $0.246250712 of foreign tax, so the credit is "
        "11.759% of Box 1a and Box 1a is gross of the tax. Yield is the fiscal-2025 "
        "ratio of net investment income to average net assets of 3.45% from American "
        "Century ETF Trust's N-CSR, grossed to Box 1a at 3.910%; that N-CSR's own tax "
        "note gives foreign tax $3,511,553 against foreign source income $24,403,526, a "
        "rate of 14.39% on the foreign-source denominator. Expense ratio 0.36% gross = "
        "net, no waiver. No capital-gain distribution since inception 2021-09-28. The "
        "yield mixes a fiscal-year numerator with a calendar-year character; both "
        "windows are stated."
    ),
    as_of="2025-08-31",
)

WRAPPER_DISTRIBUTED = Holding(
    ticker="RSST",
    name="Return Stacked U.S. Stocks & Managed Futures ETF, distributed basis",
    weight=0.30,
    expense_ratio=0.0099,
    ordinary_yield=0.001843,
    capital_gain_rate_yield=0.011007,
    creditable_foreign_tax_yield=0.0,
    source=(
        _TIDAL + " Distributions paid in the year were $915,484 of ordinary income and "
        "$2,648,642 of long-term capital gain, $0.32 per share against a beginning net "
        "asset value of $24.91, so 1.285% of net assets, 74.32% of it long-term. The "
        "trust designates 44.14% of the ordinary portion as qualified dividend income "
        "and 0.04% for the corporate dividends-received deduction. The fund's own "
        "prospectus of 2026-04-27 reports 17.17% a year before tax against 16.85% after "
        "taxes on distributions since inception on 2023-09-05 — a 32 bp/yr gap, which "
        "is this reading measured independently."
    ),
    as_of="2026-01-31",
)

WRAPPER_RECOGNISED = Holding(
    ticker="RSST",
    name="Return Stacked U.S. Stocks & Managed Futures ETF, recognised basis",
    weight=0.30,
    expense_ratio=0.0099,
    ordinary_yield=0.082990,
    capital_gain_rate_yield=0.009740,
    creditable_foreign_tax_yield=0.0,
    source=(
        _TIDAL + " Undistributed ordinary income on a tax basis was $29,468,239 at "
        "2026-01-31 against $3,964,528 a year earlier, on net assets of $344,251,000 "
        "and $282,674,000 — so the queue went from 1.40% to 8.56% of net assets while "
        "the fund distributed $915,484 of ordinary income. Ordinary income RECOGNISED "
        "in the year is therefore about $26.42m, or 8.43% of mean net assets, against "
        "0.85% of long-term gain distributed. The mechanism is in the trust's own note: "
        "'As wholly-owned controlled foreign corporations, the Subsidiaries' net income "
        "and capital gains, if any, will be included each year in the Funds' investment "
        "company taxable income.' Whether and when the queue is distributed is NOT "
        "settled here; the same note reserves the right to 'retain income or capital "
        "gains and pay excise tax'. FY2026 was a 19.94% total-return year."
    ),
    as_of="2026-01-31",
)

EQUITY_HOLDINGS: tuple[Holding, ...] = (VTI, AVLV, DFIV, VEA, IDMO, IEMG, AVES)
"""The seven long-only funds. Their weights sum to 0.70; the wrapper is the other 0.30."""


def portfolio(*, wrapper: Holding) -> tuple[Holding, ...]:
    """The eight-line portfolio, with the wrapper priced on the stated basis."""
    return (wrapper, *EQUITY_HOLDINGS)


# --------------------------------------------------------------------------------------
# The investor's accounts
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Accounts:
    """Three accounts of stated NOMINAL size. The distinction matters below."""

    roth: float
    traditional: float
    taxable: float

    def __post_init__(self) -> None:
        total = self.roth + self.traditional + self.taxable
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"account shares must sum to 1, got {total}")

    @property
    def shelter_capacity(self) -> float:
        """Roth plus traditional. The priority ranking cannot tell them apart."""
        return self.roth + self.traditional

    def after_tax_shelter_capacity(self, *, withdrawal_rate: float) -> float:
        """Shelter capacity in the investor's own money rather than in nominal balances.

        A traditional balance is not the investor's money: at a withdrawal rate ``t``,
        ``$1`` of traditional is ``$(1 - t)`` of investor wealth and ``$t`` of government
        wealth. Stating an allocation on nominal balances overstates true exposure, and
        the difference ``roth - traditional (1 - t)`` is the entire arithmetic content of
        the Roth-versus-traditional placement question — see
        :func:`roth_versus_traditional_bp`.
        """
        if not 0.0 <= withdrawal_rate < 1.0:
            raise ValueError("withdrawal_rate must lie in [0, 1)")
        return self.roth + self.traditional * (1.0 - withdrawal_rate)


THIRDS = Accounts(roth=1.0 / 3.0, traditional=1.0 / 3.0, taxable=1.0 / 3.0)
"""The stated investor: roughly equal thirds, long horizon, no near-term withdrawal."""


# --------------------------------------------------------------------------------------
# The plan
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Placement:
    """One holding, split between the shelter and the taxable account."""

    ticker: str
    priority_bp: float
    sheltered_weight: float
    taxable_weight: float

    @property
    def weight(self) -> float:
        return self.sheltered_weight + self.taxable_weight


def rank(holdings: Sequence[Holding], *, regime: TaxRegime) -> list[tuple[str, float]]:
    """Rank holdings by priority, highest first, ties broken by ticker."""
    scored = [(h.ticker, h.priority_bp(regime)) for h in holdings]
    return sorted(scored, key=lambda item: (-item[1], item[0]))


def plan(
    holdings: Sequence[Holding], *, regime: TaxRegime, capacity: float
) -> list[Placement]:
    """Fill ``capacity`` of shelter highest-priority-first and return the whole plan.

    Weights and ``capacity`` are fractions of the same base, so the saving this plan
    produces is in bp/yr **of that base**.
    """
    if not 0.0 <= capacity <= 1.0:
        raise ValueError(f"capacity must lie in [0, 1], got {capacity}")
    ordered = sorted(holdings, key=lambda h: (-h.priority_bp(regime), h.ticker))
    remaining = capacity
    placements: list[Placement] = []
    for holding in ordered:
        sheltered = min(holding.weight, max(remaining, 0.0))
        remaining -= sheltered
        placements.append(
            Placement(
                ticker=holding.ticker,
                priority_bp=holding.priority_bp(regime),
                sheltered_weight=sheltered,
                taxable_weight=holding.weight - sheltered,
            )
        )
    return placements


def saving_bp(placements: Sequence[Placement]) -> float:
    """Annual saving a plan delivers, bp/yr of the portfolio."""
    return sum(p.sheltered_weight * p.priority_bp for p in placements)


def pro_rata_saving_bp(
    holdings: Sequence[Holding], *, regime: TaxRegime, capacity: float
) -> float:
    """What an investor who never thinks about location gets.

    Every fund held in the same proportion in every account. This is the honest control
    for "what is placement worth", because the alternative to a plan is not the worst
    plan; it is no plan.
    """
    return capacity * sum(h.weight * h.priority_bp(regime) for h in holdings)


def worst_saving_bp(
    holdings: Sequence[Holding], *, regime: TaxRegime, capacity: float
) -> float:
    """What an investor who gets the ranking exactly backwards gets."""
    reversed_priority = sorted(holdings, key=lambda h: (h.priority_bp(regime), h.ticker))
    remaining, saving = capacity, 0.0
    for holding in reversed_priority:
        placed = min(holding.weight, max(remaining, 0.0))
        saving += placed * holding.priority_bp(regime)
        remaining -= placed
    return saving


def forfeited_credit_bp(placements: Sequence[Placement], holdings: Sequence[Holding]) -> float:
    """Foreign tax credit destroyed by this plan, bp/yr of the portfolio.

    The price of sheltering the international sleeve. It is permanent, it is identical
    in a Roth and a traditional account, and it is the term the conventional rule
    "hold international in taxable to capture the credit" is built on — so it should be
    reported next to the saving rather than buried inside it.
    """
    by_ticker = {h.ticker: h for h in holdings}
    return sum(
        p.sheltered_weight * by_ticker[p.ticker].creditable_foreign_tax_yield / BASIS_POINT
        for p in placements
    )


# --------------------------------------------------------------------------------------
# Roth versus traditional, which the priority ranking cannot answer
# --------------------------------------------------------------------------------------


def roth_versus_traditional_bp(
    *,
    accounts: Accounts,
    withdrawal_rate: float,
    swapped_weight: float,
    high_growth: float,
    low_growth: float,
    years: int,
) -> float:
    """Value of putting the higher-growth sleeve in the Roth, in bp/yr of log growth.

    **The drag cannot decide this.** :meth:`Holding.sheltered_cost_bp` is the same
    number in both accounts for every holding, so the whole of the location ranking is
    silent between them. What is not silent is that a Roth dollar and a traditional
    dollar are not the same dollar. Writing ``R`` and ``T`` for the nominal balances and
    ``t`` for the withdrawal rate, terminal after-tax wealth from putting growth factor
    ``A`` in the Roth and ``B`` in the traditional is ``R A + T (1 - t) B``; swapping
    them gives ``R B + T (1 - t) A``, and the difference is exactly

        ``(R - T (1 - t)) (A - B)``.

    So the gain is the *after-tax size gap between the accounts* times the *growth gap
    between the sleeves*, and it is zero when ``R = T (1 - t)``. Two consequences worth
    stating plainly: at equal nominal thirds the Roth is the larger after-tax account by
    ``T t``, so the higher-growth sleeve does belong there; and the result is a
    **forecast**, because it needs both a future withdrawal rate and a return
    difference, neither of which is contractual.

    A third reading is the honest one. Holding the same after-tax allocation, this
    "gain" is not free: it raises the investor's share of the sleeve's dispersion by the
    same factor it raises the mean. The traditional account makes the government a
    ``t``-share partner in the outcome. Putting the least-established sleeve there is a
    risk decision, not an edge.
    """
    if years <= 0:
        raise ValueError("years must be positive")
    if not 0.0 <= swapped_weight <= 1.0:
        raise ValueError("swapped_weight must lie in [0, 1]")
    size_gap = accounts.roth - accounts.traditional * (1.0 - withdrawal_rate)
    growth_gap = (1.0 + high_growth) ** years - (1.0 + low_growth) ** years
    gain = swapped_weight * size_gap * growth_gap
    base = (1.0 + high_growth) ** years
    if gain <= -base:
        raise ValueError("the stated inputs destroy the whole portfolio; check them")
    from math import log

    return log(1.0 + gain / base) / years / BASIS_POINT


# --------------------------------------------------------------------------------------
# The employer plan: a shelter with a menu
# --------------------------------------------------------------------------------------


INDEX_MENU: frozenset[str] = frozenset({"VTI", "VEA", "IEMG"})
"""What a typical employer 401(k)/403(b) lineup can hold from this portfolio.

A plain, broad, low-cost index fund in each of US total market, developed ex-US and
emerging markets, or a close equivalent. **No employer plan offers a return-stacked ETF, a
Dimensional or Avantis systematic fund, or a single-factor momentum ETF**, so the other
five holdings are unreachable inside it. This is a menu constraint, not a tax fact, and it
turns out to bind harder than anything in the tax code.
"""


def open_menu_capacity(*, accounts: Accounts, open_menu_fraction: float) -> float:
    """Shelter capacity that can hold anything: the Roth plus the rollover IRA.

    ``open_menu_fraction`` is the share of the tax-deferred third that sits in a rollover
    IRA rather than in an employer plan. It is an investor input nobody has measured, so
    every result below is reported across its range rather than at a selected value.
    """
    if not 0.0 <= open_menu_fraction <= 1.0:
        raise ValueError(f"open_menu_fraction must lie in [0, 1], got {open_menu_fraction}")
    return accounts.roth + accounts.traditional * open_menu_fraction


def restricted_menu_capacity(*, accounts: Accounts, open_menu_fraction: float) -> float:
    """Shelter capacity that can hold only :data:`INDEX_MENU`. It must still be filled."""
    if not 0.0 <= open_menu_fraction <= 1.0:
        raise ValueError(f"open_menu_fraction must lie in [0, 1], got {open_menu_fraction}")
    return accounts.traditional * (1.0 - open_menu_fraction)


def menu_constrained_plan(
    holdings: Sequence[Holding],
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
    shelter_wrapper_first: bool = True,
    wrapper_ticker: str = "RSST",
) -> dict[str, float]:
    """Sheltered weight per ticker, subject to the employer plan's index-only menu.

    Three claims on the same capacity, resolved in this order:

    1. **The employer plan must be filled**, because the balance exists whatever is in it,
       and it can only be filled from :data:`INDEX_MENU`. Filling it with the *highest*
       priority index fund available is the best that can be done with a captive account.
    2. **The wrapper takes open-menu capacity next** when ``shelter_wrapper_first``. This
       is not the greedy choice on every input — see :func:`wrapper_regret_bp`, which is
       why it is a flag rather than an assumption.
    3. **Everything else fills the remainder by priority.**

    Raises if the employer plan cannot be filled from the index menu at all, which would
    mean the stated allocation is infeasible rather than merely expensive.
    """
    restricted = restricted_menu_capacity(
        accounts=accounts, open_menu_fraction=open_menu_fraction
    )
    open_capacity = open_menu_capacity(
        accounts=accounts, open_menu_fraction=open_menu_fraction
    )
    placed = {h.ticker: 0.0 for h in holdings}

    if shelter_wrapper_first and wrapper_ticker in placed:
        wrapper = next(h for h in holdings if h.ticker == wrapper_ticker)
        placed[wrapper_ticker] = min(wrapper.weight, open_capacity)
        open_capacity -= placed[wrapper_ticker]

    remaining = restricted
    for holding in sorted(
        (h for h in holdings if h.ticker in INDEX_MENU),
        key=lambda h: (-h.priority_bp(regime), h.ticker),
    ):
        take = min(holding.weight - placed[holding.ticker], max(remaining, 0.0))
        placed[holding.ticker] += take
        remaining -= take
    if remaining > 1e-9:
        raise ValueError(
            "the employer plan cannot be filled from the index menu: "
            f"{remaining:.4f} of capacity has nothing eligible to hold"
        )

    remaining = open_capacity
    for holding in sorted(holdings, key=lambda h: (-h.priority_bp(regime), h.ticker)):
        if shelter_wrapper_first and holding.ticker == wrapper_ticker:
            continue
        take = min(holding.weight - placed[holding.ticker], max(remaining, 0.0))
        placed[holding.ticker] += take
        remaining -= take
    return placed


def plan_value_bp(
    placed: dict[str, float], holdings: Sequence[Holding], *, regime: TaxRegime
) -> float:
    """Value a placement under a stated set of holdings, bp/yr of the portfolio.

    Kept separate from :func:`menu_constrained_plan` on purpose: the same *placement* has
    to be priceable under both wrapper readings, which is what makes
    :func:`wrapper_regret_bp` possible.
    """
    by_ticker = {h.ticker: h for h in holdings}
    return sum(weight * by_ticker[t].priority_bp(regime) for t, weight in placed.items())


def menu_binding_fraction(*, accounts: Accounts = THIRDS) -> float:
    """The ``open_menu_fraction`` below which the employer plan starts costing something.

    The unconstrained plan already shelters some index funds. While the employer plan is
    no larger than that, it can be filled with exactly those and the constraint is free.
    Below it, the plan is forced to shelter a fund it would rather hold in taxable.
    """
    index_sheltered = sum(
        h.weight for h in EQUITY_HOLDINGS if h.ticker in INDEX_MENU and h.ticker != "VTI"
    )
    if accounts.traditional <= 0.0:
        return 0.0
    return max(0.0, 1.0 - index_sheltered / accounts.traditional)


def wrapper_regret_bp(
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
) -> tuple[float, float]:
    """``(cost of sheltering the wrapper if wrong, cost of not sheltering it if wrong)``.

    The wrapper's priority is unresolved by a factor of ten — see
    :data:`WRAPPER_RECOGNISED` against :data:`WRAPPER_DISTRIBUTED` — and the honest
    response to an unresolved input is not to pick the flattering branch and book it. It
    is to ask whether the decision needs the input at all.

    It does not. The asymmetry is roughly ten to one at every ``open_menu_fraction``, so
    **sheltering the wrapper is the right decision under either reading** and the
    measurement can stay unresolved without stalling the plan. What the reading decides is
    only how much the plan is *worth*, which is why §8.7 reports that as a range and books
    the conservative end.
    """
    recognised = portfolio(wrapper=WRAPPER_RECOGNISED)
    distributed = portfolio(wrapper=WRAPPER_DISTRIBUTED)
    kwargs = {"regime": regime, "accounts": accounts, "open_menu_fraction": open_menu_fraction}
    sheltered = menu_constrained_plan(recognised, shelter_wrapper_first=True, **kwargs)  # type: ignore[arg-type]
    greedy_distributed = menu_constrained_plan(
        distributed, shelter_wrapper_first=False, **kwargs  # type: ignore[arg-type]
    )
    greedy_recognised = menu_constrained_plan(
        recognised, shelter_wrapper_first=False, **kwargs  # type: ignore[arg-type]
    )
    cost_if_distributed = plan_value_bp(
        greedy_distributed, distributed, regime=regime
    ) - plan_value_bp(sheltered, distributed, regime=regime)
    cost_if_recognised = plan_value_bp(
        greedy_recognised, recognised, regime=regime
    ) - plan_value_bp(greedy_distributed, recognised, regime=regime)
    return cost_if_distributed, cost_if_recognised


# --------------------------------------------------------------------------------------
# The budget, with every line against its own benchmark
# --------------------------------------------------------------------------------------


def location_edge_bp(
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
) -> float:
    """The plan's edge over pro-rata placement on the **audited distributed basis**, bp/yr.

    Signed, and it can be negative — see :func:`location_edge`, which refuses to publish a
    negative value as a budget line.
    """
    distributed = portfolio(wrapper=WRAPPER_DISTRIBUTED)
    placed = menu_constrained_plan(
        distributed,
        regime=regime,
        accounts=accounts,
        open_menu_fraction=open_menu_fraction,
        shelter_wrapper_first=True,
    )
    return plan_value_bp(placed, distributed, regime=regime) - pro_rata_saving_bp(
        distributed, regime=regime, capacity=accounts.shelter_capacity
    )


def location_edge(
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
) -> EdgeComponent:
    """The plan's edge over the investor's own pro-rata placement of the same funds.

    **Priced on the audited distributed basis**, which is what shareholders were actually
    taxed on. The recognised basis is a *conditional* addition reported beside it and
    deliberately not booked: crediting a budget with income that has been recognised
    inside a fund and not yet distributed to anybody is precisely the inflation
    :func:`portfolio_edge.studies.tax_structure.deferral_value` refuses to commit.

    The benchmark is :attr:`Benchmark.COUNTERFACTUAL_HOLDING` — the *same eight funds*,
    placed the way a default-choosing investor with the same accounts would place them
    (:func:`feasible_naive_saving_bp`). It is not a cheap index and not the average
    investor, and :func:`aggregate` will refuse to add it to a line measured against
    either.
    """
    edge = location_edge_versus_feasible_bp(
        regime=regime, accounts=accounts, open_menu_fraction=open_menu_fraction
    )
    if edge < 0.0:
        raise ValueError(
            "the plan loses to pro-rata placement on the audited basis at "
            f"open_menu_fraction={open_menu_fraction:.2f} (edge {edge:.2f} bp/yr). That is "
            "a real finding, not a budget line: below the binding fraction the employer "
            "plan forces low-priority index funds into the shelter and pushes DFIV and "
            "AVES out of it. Publish it as a cost, and justify the plan on "
            "wrapper_regret_bp instead."
        )
    return EdgeComponent(
        name="Asset location, eight named funds, three accounts",
        mechanism=(
            "priority = recurring tax if held in taxable - irrecoverable withholding if "
            "sheltered, filled highest-first against a captive employer-plan menu"
        ),
        benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
        certainty=Certainty.DETERMINISTIC,
        low_bp=edge,
        central_bp=edge,
        high_bp=edge,
        tracking_error_bp=0.0,
        conditions=(
            "Already net of the 8.81 bp/yr of foreign tax credit the plan forfeits by "
            "sheltering the international sleeve: the forfeiture is the second term of "
            "the priority expression and must not be booked again. Excludes the "
            "wrapper's undistributed CFC accrual, reported separately by "
            "conditional_wrapper_upside_bp and deliberately not booked. Holds only at "
            f"open_menu_fraction={open_menu_fraction:.2f}, which is an unmeasured "
            "investor input."
        ),
        falsifier=(
            "A filed qualified-dividend percentage for VTI or AVLV below about 0.54 "
            "reorders the queue; a change in the employer plan's menu changes the "
            "constraint; and any of the three assumed qualified fractions being wrong "
            "moves the fund it belongs to."
        ),
    )


def conditional_wrapper_upside_bp(
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
) -> float:
    """What the plan gains **if** the wrapper's recognised income is distributed.

    Reported next to :func:`location_edge` and never added to it. It is contingent on an
    unresolved fact — whether the queue in :data:`WRAPPER_RECOGNISED` reaches
    shareholders — and a budget that books a contingency at its favourable branch is not
    a budget.
    """
    recognised = portfolio(wrapper=WRAPPER_RECOGNISED)
    placed = menu_constrained_plan(
        recognised,
        regime=regime,
        accounts=accounts,
        open_menu_fraction=open_menu_fraction,
        shelter_wrapper_first=True,
    )
    conditional = plan_value_bp(placed, recognised, regime=regime) - feasible_naive_saving_bp(
        recognised, regime=regime, accounts=accounts, open_menu_fraction=open_menu_fraction
    )
    return conditional - location_edge_versus_feasible_bp(
        regime=regime, accounts=accounts, open_menu_fraction=open_menu_fraction
    )


# --------------------------------------------------------------------------------------
# Contributions
# --------------------------------------------------------------------------------------


CONSTRAINED_ROTATION_PP = 2.0
"""Portfolio points a year of US-equity-to-international rotation that the plan cannot
execute inside the shelter, because only AVLV's sheltered remainder sits beside the
wrapper. Every other rebalancing direction is free."""


def contributions_cover_the_constrained_direction(*, contribution_rate: float) -> float:
    """How many times over new money covers the one constrained rebalancing direction.

    At or above 1.0 the taxable account never has to sell, so the deferral in
    ``tax_structure`` §4 is never broken. **That is a hurdle avoided, not a saving**, and
    it is reported as such: §4 is explicit that crediting yourself for not doing something
    nobody proposed is how these budgets get inflated.
    """
    if not 0.0 <= contribution_rate <= 1.0:
        raise ValueError(f"contribution_rate must lie in [0, 1], got {contribution_rate}")
    return contribution_rate * 100.0 / CONSTRAINED_ROTATION_PP


DEFAULT_EMPLOYER_ORDER: tuple[str, ...] = ("VTI", "VEA", "IEMG")
"""The order a default-choosing investor fills an employer plan in: the biggest, most
familiar index fund first. Not a priority ranking — the point of the control is that it
ignores priority."""


def feasible_naive_saving_bp(
    holdings: Sequence[Holding],
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
) -> float:
    """The control an investor with an employer plan can actually execute.

    :func:`pro_rata_saving_bp` is the right control when every account has an open menu.
    It is **infeasible** once part of the shelter is a captive employer plan, because the
    wrapper and the systematic funds cannot go in there at all, so measuring against it
    below ``open_menu_fraction = 1`` compares the plan with something nobody could have
    done. This control instead does what a default-choosing investor does: fill the
    employer plan from :data:`DEFAULT_EMPLOYER_ORDER`, then hold everything else pro rata
    across the open-menu accounts.
    """
    restricted = restricted_menu_capacity(
        accounts=accounts, open_menu_fraction=open_menu_fraction
    )
    open_capacity = open_menu_capacity(
        accounts=accounts, open_menu_fraction=open_menu_fraction
    )
    by_ticker = {h.ticker: h for h in holdings}
    placed = {h.ticker: 0.0 for h in holdings}

    remaining = restricted
    for ticker in DEFAULT_EMPLOYER_ORDER:
        if ticker not in by_ticker:
            continue
        take = min(by_ticker[ticker].weight, max(remaining, 0.0))
        placed[ticker] += take
        remaining -= take
    if remaining > 1e-9:
        raise ValueError("the employer plan cannot be filled from the default order")

    left = {t: by_ticker[t].weight - placed[t] for t in placed}
    total_left = sum(left.values())
    share = open_capacity / total_left if total_left > 0 else 0.0
    for ticker in placed:
        placed[ticker] += left[ticker] * share
    return plan_value_bp(placed, holdings, regime=regime)


def location_edge_versus_feasible_bp(
    *,
    regime: TaxRegime,
    accounts: Accounts = THIRDS,
    open_menu_fraction: float = 1.0,
) -> float:
    """The plan's edge over the *feasible* naive control, on the audited basis, bp/yr.

    This is the number §8.7 books. It is smaller than the edge over pro rata at
    ``open_menu_fraction = 1`` — where the two controls coincide — and **larger** below
    the binding fraction, because a captive employer plan hurts the naive investor more
    than it hurts a deliberate one.
    """
    distributed = portfolio(wrapper=WRAPPER_DISTRIBUTED)
    placed = menu_constrained_plan(
        distributed,
        regime=regime,
        accounts=accounts,
        open_menu_fraction=open_menu_fraction,
        shelter_wrapper_first=True,
    )
    return plan_value_bp(placed, distributed, regime=regime) - feasible_naive_saving_bp(
        distributed, regime=regime, accounts=accounts, open_menu_fraction=open_menu_fraction
    )
