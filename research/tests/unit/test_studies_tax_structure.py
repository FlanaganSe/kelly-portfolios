"""Tests for :mod:`portfolio_edge.studies.tax_structure`.

Every number in ``docs/research/structural-and-tax-edges.md`` is pinned here. The
module has no data dependency and no randomness, so a failure is always either a
changed assumption or a bug, never noise.

Three kinds of test, kept visibly apart because the repository's methodology note
records that verification killed *framing* more often than arithmetic:

* **Closed forms computed independently of the implementation.** The simulator in
  ``after_tax_path`` is a loop; several of its outputs have exact algebraic solutions
  derived here from scratch. Where the loop and the algebra agree to machine precision
  the loop is doing what it claims.
* **Invariants.** Monotonicity, conservation of basis, the refusal to aggregate across
  benchmarks, and the guards that stop a lever being booked twice.
* **Pinned figures.** The numbers that appear in the synthesis, with the inputs that
  produce them stated in the test rather than in a fixture file.
"""

from __future__ import annotations

import math

import pytest

from portfolio_edge.studies.outperformance_horizon import (
    ASSET_LOCATION,
    TAX_LOSS_HARVESTING,
    Benchmark,
    Certainty,
    budget_for,
    horizon_for_confidence,
)
from portfolio_edge.studies.tax_structure import (
    AS_OF,
    BOOKED_COUNTERFACTUAL_BUDGET_BP,
    DEVELOPED_EX_US,
    DIRECT_INDEXING_FEES_BP,
    EMERGING_MARKETS,
    EQUITY_FUTURES_ROLL_RICHNESS_BP,
    HARVESTING_NO_FLOW_LONG_TERM,
    HARVESTING_NO_FLOW_SHORT_TERM,
    HARVESTING_WITH_CONTRIBUTIONS,
    MUNICIPAL_CURVE,
    NTSX,
    REFERENCE_INVESTOR,
    SECURITIES_LENDING_BY_ASSET_CLASS,
    SHELTER_CANDIDATES,
    STRUCTURAL_LEDGER,
    TOP_BRACKET,
    TREASURY_FUTURES_FUNDING_BASIS_BP,
    UPPER_MIDDLE_BRACKET,
    ZERO_RATE_BRACKET,
    Account,
    Additivity,
    CapitalEfficiency,
    Disposal,
    HarvestingProfile,
    StructuralLever,
    TaxRegime,
    additive_total,
    after_tax_path,
    capital_gain_distribution_drag_bp,
    deferral_value,
    form_1116_threshold_assets,
    harvested_loss_value_bp,
    location_breakeven_rate,
    location_comparison,
    lot_selection_comparison,
    municipal_breakeven_rate,
    net_unrealised_appreciation_benefit_bp,
    qualified_dividend_shortfall_bp,
    revised_counterfactual_budget_bp,
    section_1256_comparison,
    shelter_priority_bp,
    tax_equivalent_yield,
    tax_gain_harvest_value_bp,
    traditional_and_roth_are_equivalent,
    wash_sale_across_accounts_cost_bp,
)

NO_TAX = TaxRegime(
    label="no tax at all",
    jurisdiction="test",
    as_of=AS_OF,
    ordinary_income=0.0,
    long_term_capital_gain=0.0,
    net_investment_income=0.0,
)


# --------------------------------------------------------------------------------------
# The regime is an input, and it validates itself
# --------------------------------------------------------------------------------------


def test_the_three_committed_regimes_carry_the_rates_the_synthesis_quotes() -> None:
    """40.8% / 23.8% at the top, 24% / 15% in the middle, 12% / 0% at the bottom."""
    assert TOP_BRACKET.ordinary == pytest.approx(0.408)
    assert TOP_BRACKET.capital_gain == pytest.approx(0.238)
    assert UPPER_MIDDLE_BRACKET.ordinary == pytest.approx(0.24)
    assert UPPER_MIDDLE_BRACKET.capital_gain == pytest.approx(0.15)
    assert ZERO_RATE_BRACKET.capital_gain == pytest.approx(0.0)
    for regime in (TOP_BRACKET, UPPER_MIDDLE_BRACKET, ZERO_RATE_BRACKET):
        assert regime.as_of == AS_OF
        assert regime.jurisdiction == "US federal"


def test_a_regime_without_a_date_or_a_jurisdiction_is_refused() -> None:
    """Tax law that is not stamped is the failure mode the framework names by hand."""
    with pytest.raises(ValueError, match="trap"):
        TaxRegime(
            label="undated",
            jurisdiction="US federal",
            as_of="   ",
            ordinary_income=0.37,
            long_term_capital_gain=0.20,
            net_investment_income=0.038,
        )


def test_a_long_term_rate_above_the_ordinary_rate_is_refused() -> None:
    with pytest.raises(ValueError, match="inverts every conclusion"):
        TaxRegime(
            label="inverted",
            jurisdiction="nowhere",
            as_of=AS_OF,
            ordinary_income=0.20,
            long_term_capital_gain=0.37,
            net_investment_income=0.0,
        )


def test_section_1256_blend_is_sixty_forty_of_the_all_in_rates() -> None:
    """``0.6 x 23.8 + 0.4 x 40.8 = 30.6%``, computed by hand, not by the property."""
    assert TOP_BRACKET.section_1256_blended == pytest.approx(0.6 * 0.238 + 0.4 * 0.408)
    assert TOP_BRACKET.section_1256_blended == pytest.approx(0.306)
    # It sits strictly between the two rates it blends, by construction.
    assert TOP_BRACKET.capital_gain < TOP_BRACKET.section_1256_blended < TOP_BRACKET.ordinary


# --------------------------------------------------------------------------------------
# The simulator, checked against algebra derived from scratch
# --------------------------------------------------------------------------------------


def test_a_zero_tax_regime_reproduces_pure_compounding_exactly() -> None:
    """The most basic sanity check: with no rates, the loop must be the identity."""
    path = after_tax_path(
        regime=NO_TAX,
        account=Account.TAXABLE,
        pretax_log_growth=0.07,
        years=30,
        dividend_yield=0.02,
        capital_gain_distribution_yield=0.05,
        realised_gain_fraction=0.3,
    )
    assert path.terminal_wealth == pytest.approx(math.exp(0.07 * 30), rel=1e-12)
    assert path.annualised_log_growth == pytest.approx(0.07, rel=1e-12)
    assert path.cumulative_tax_paid == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("account", [Account.TAX_DEFERRED, Account.TAX_EXEMPT])
def test_a_sheltered_account_leaks_exactly_the_foreign_withholding_and_nothing_else(
    account: Account,
) -> None:
    """Closed form: ``W_H = (e**g (1 - w y))**H``, derived independently of the loop.

    Inside the shelter the only charge that survives is the tax a foreign government
    takes at source, because §901 credits a foreign tax against a **US** tax and a
    sheltered account generates none. Both sheltered account types leak the identical
    amount, which is the whole finding of §1 of the synthesis: the forfeiture is a
    property of the wrapper, not of whether the wrapper is Roth or traditional.
    """
    g, years, yield_, withholding = 0.07, 30, 0.032, 0.075
    path = after_tax_path(
        regime=TOP_BRACKET,
        account=account,
        pretax_log_growth=g,
        years=years,
        dividend_yield=yield_,
        foreign_withholding_rate=withholding,
    )
    expected = (math.exp(g) * (1.0 - withholding * yield_)) ** years
    assert path.terminal_wealth == pytest.approx(expected, rel=1e-12)
    # The annual leak is exactly -log(1 - w y), which for small w y is w y = 24.0 bp.
    leak_bp = -math.log(1.0 - withholding * yield_) / 1e-4
    assert (0.07 - path.annualised_log_growth) / 1e-4 == pytest.approx(leak_bp, rel=1e-12)
    assert leak_bp == pytest.approx(24.02, abs=0.01)


def test_a_fully_credited_foreign_tax_costs_a_taxable_investor_nothing() -> None:
    """The credit, when usable, makes the withholding invisible. This is the mechanism.

    Two taxable paths differing only in whether a foreign government withholds 15% of
    the dividend must end at the same wealth, because the credit offsets the US tax
    dollar for dollar up to the US tax on that income.
    """
    withheld = after_tax_path(
        regime=TOP_BRACKET,
        account=Account.TAXABLE,
        pretax_log_growth=0.07,
        years=30,
        dividend_yield=0.032,
        foreign_withholding_rate=0.15,
        foreign_credit_utilisation=1.0,
    )
    clean = after_tax_path(
        regime=TOP_BRACKET,
        account=Account.TAXABLE,
        pretax_log_growth=0.07,
        years=30,
        dividend_yield=0.032,
        foreign_withholding_rate=0.0,
    )
    assert withheld.terminal_wealth == pytest.approx(clean.terminal_wealth, rel=1e-12)


def test_the_credit_stops_helping_once_it_exceeds_the_us_tax_on_that_income() -> None:
    """§904 in miniature: an unused credit is not refundable, it carries or expires.

    A 35% Swiss statutory withholding against a 15% US qualified-dividend rate leaves
    20 points with nowhere to go, so the excess is a real cost even in a taxable account.
    """
    heavy = after_tax_path(
        regime=UPPER_MIDDLE_BRACKET,
        account=Account.TAXABLE,
        pretax_log_growth=0.07,
        years=30,
        dividend_yield=0.032,
        disposal=Disposal.STEP_UP,
        foreign_withholding_rate=0.35,
    )
    light = after_tax_path(
        regime=UPPER_MIDDLE_BRACKET,
        account=Account.TAXABLE,
        pretax_log_growth=0.07,
        years=30,
        dividend_yield=0.032,
        disposal=Disposal.STEP_UP,
        foreign_withholding_rate=0.10,
    )
    assert heavy.terminal_wealth < light.terminal_wealth
    # Closed form, derived by hand. At w = 35% against a 15% US rate the credit is capped
    # by the US tax and the annual charge is the full 35% of the dividend; at w = 10% the
    # credit is fully usable and the annual charge is the 15% US rate. Disposal is a
    # step-up so the two paths' differing bases cannot contaminate the comparison.
    heavy_multiplier = math.log(1.0 - 0.35 * 0.032)
    light_multiplier = math.log(1.0 - 0.15 * 0.032)
    assert heavy.annualised_log_growth - light.annualised_log_growth == pytest.approx(
        heavy_multiplier - light_multiplier, rel=1e-12
    )


def test_realising_every_gain_annually_has_an_exact_closed_form() -> None:
    """``W_{t+1} = W_t (e**g (1 - q) + q)``, so the annualised rate is horizon-free."""
    g, q, years = 0.07, TOP_BRACKET.capital_gain, 30
    path = after_tax_path(
        regime=TOP_BRACKET,
        account=Account.TAXABLE,
        pretax_log_growth=g,
        years=years,
        realised_gain_fraction=1.0,
    )
    per_year = math.exp(g) * (1.0 - q) + q
    assert path.terminal_wealth == pytest.approx(per_year**years, rel=1e-12)
    assert path.terminal_basis == pytest.approx(path.terminal_wealth, rel=1e-12)


def test_basis_never_exceeds_wealth_in_a_growing_taxable_account() -> None:
    """The bookkeeping invariant the first draft of the simulator broke.

    Paying tax out of the account means selling shares whose basis was just stepped up,
    so wealth and basis fall together. Getting this wrong manufactures a phantom shelter
    that grows every year and understates every tax drag on the page.
    """
    for fraction in (0.0, 0.25, 0.5, 1.0):
        path = after_tax_path(
            regime=TOP_BRACKET,
            account=Account.TAXABLE,
            pretax_log_growth=0.07,
            years=40,
            capital_gain_distribution_yield=0.05,
            realised_gain_fraction=fraction,
            disposal=Disposal.STEP_UP,
        )
        assert path.terminal_basis <= path.terminal_wealth + 1e-12


def test_after_tax_path_rejects_impossible_inputs() -> None:
    with pytest.raises(ValueError, match="years must be"):
        after_tax_path(regime=TOP_BRACKET, account=Account.TAXABLE, pretax_log_growth=0.07, years=0)
    with pytest.raises(ValueError, match="dividend_yield cannot be negative"):
        after_tax_path(
            regime=TOP_BRACKET,
            account=Account.TAXABLE,
            pretax_log_growth=0.07,
            years=10,
            dividend_yield=-0.01,
        )
    with pytest.raises(ValueError, match="realised_gain_fraction must lie"):
        after_tax_path(
            regime=TOP_BRACKET,
            account=Account.TAXABLE,
            pretax_log_growth=0.07,
            years=10,
            realised_gain_fraction=1.5,
        )


def test_paths_of_different_length_cannot_be_compared() -> None:
    short = after_tax_path(
        regime=TOP_BRACKET, account=Account.TAXABLE, pretax_log_growth=0.07, years=10
    )
    long = after_tax_path(
        regime=TOP_BRACKET, account=Account.TAXABLE, pretax_log_growth=0.07, years=30
    )
    with pytest.raises(ValueError, match="different length"):
        short.drag_bp_against(long)


# --------------------------------------------------------------------------------------
# 1. Foreign tax credit forfeiture
# --------------------------------------------------------------------------------------


US_EQUITY_YIELD = 0.0110


def test_the_two_committed_sleeves_forfeit_the_figures_the_synthesis_quotes() -> None:
    """15.78 bp/yr developed, 20.00 bp/yr emerging, and both are exact products.

    Emerging markets forfeits *more* despite yielding *less*, because its effective
    withholding rate is 62% higher. That reversal is the reason the two sleeves have to
    be sized separately rather than as one "international" line.
    """
    assert DEVELOPED_EX_US.forfeited_bp == pytest.approx(0.06068 * 0.0260 / 1e-4, rel=1e-12)
    assert DEVELOPED_EX_US.forfeited_bp == pytest.approx(15.78, abs=0.01)
    assert EMERGING_MARKETS.forfeited_bp == pytest.approx(0.09853 * 0.0203 / 1e-4, rel=1e-12)
    assert EMERGING_MARKETS.forfeited_bp == pytest.approx(20.00, abs=0.01)
    assert EMERGING_MARKETS.dividend_yield < DEVELOPED_EX_US.dividend_yield
    assert EMERGING_MARKETS.forfeited_bp > DEVELOPED_EX_US.forfeited_bp


def test_a_seventy_thirty_international_sleeve_forfeits_seventeen_basis_points() -> None:
    """17.04 bp/yr on the sleeve; 5.11 bp on a portfolio 30% in international."""
    blended = 0.70 * DEVELOPED_EX_US.forfeited_bp + 0.30 * EMERGING_MARKETS.forfeited_bp
    assert blended == pytest.approx(17.04, abs=0.01)
    assert 0.30 * blended == pytest.approx(5.11, abs=0.01)


def test_the_conventional_location_rule_survives_for_developed_markets() -> None:
    """Sheltering developed ex-US still wins at the top bracket, by 19.9 bp of 61.9.

    Developed international taxable costs ``q y_i`` = 23.8% x 2.60% = 61.9 bp, the
    foreign tax having been fully restored by the credit.
    Sheltered it costs ``w y_i + q y_d`` = 15.8 + 23.8% x 1.10% = 42.0 bp. The naive
    "hold international in taxable to capture the credit" argument reads the 15.8 bp in
    isolation and never compares it against the 61.9 bp it displaces.
    """
    comparison = location_comparison(
        regime=TOP_BRACKET,
        international=DEVELOPED_EX_US,
        domestic_dividend_yield=US_EQUITY_YIELD,
    )
    assert comparison.international_in_taxable_bp == pytest.approx(61.88, abs=0.01)
    assert comparison.international_sheltered_bp == pytest.approx(41.96, abs=0.01)
    assert comparison.advantage_of_sheltering_international_bp == pytest.approx(19.92, abs=0.01)


@pytest.mark.parametrize(
    ("sleeve_name", "breakeven"),
    [("developed", 0.10518), ("emerging", 0.21507)],
)
def test_the_break_even_dividend_rate_straddles_the_us_rate_schedule(
    sleeve_name: str, breakeven: float
) -> None:
    """10.52% for developed markets, **21.51%** for emerging. The gap is the finding.

    ``q* = u w y_i / (y_i - y_d)``, derived by hand in the module docstring. The US
    qualified-dividend schedule offers only 0%, 15%, 18.8% and 23.8%, so:

    * developed markets' 10.52% break-even sits **below every positive rate**, and the
      conventional "shelter the higher-yielding foreign sleeve" rule survives intact;
    * emerging markets' 21.51% break-even sits **between 18.8% and 23.8%**, so an
      investor at 15% or 18.8% should do the opposite of the conventional advice and
      hold emerging-market equity in the taxable account.

    That is the whole inversion, and it is a bracket-dependent fact rather than a
    universal rule — which is exactly what the framework says tax law must be treated as.
    """
    sleeve = DEVELOPED_EX_US if sleeve_name == "developed" else EMERGING_MARKETS
    computed = location_breakeven_rate(
        international=sleeve, domestic_dividend_yield=US_EQUITY_YIELD
    )
    assert computed == pytest.approx(
        sleeve.withholding_rate * sleeve.dividend_yield / (sleeve.dividend_yield - US_EQUITY_YIELD),
        rel=1e-12,
    )
    assert computed == pytest.approx(breakeven, abs=1e-5)
    # And it is a genuine break-even: at exactly q* the two placements tie.
    tied = TaxRegime(
        label="at the break-even",
        jurisdiction="US federal",
        as_of=AS_OF,
        ordinary_income=0.37,
        long_term_capital_gain=computed,
        net_investment_income=0.0,
    )
    comparison = location_comparison(
        regime=tied, international=sleeve, domestic_dividend_yield=US_EQUITY_YIELD
    )
    assert comparison.advantage_of_sheltering_international_bp == pytest.approx(0.0, abs=1e-9)


def test_an_unusable_credit_removes_the_taxable_account_advantage_entirely() -> None:
    """With ``u = 0`` the break-even rate is 0: the shelter always wins.

    This is the 0%-bracket case stated properly, and it is the trap in the naive
    argument. Such an investor cannot use the credit in *either* location, because §904
    limits it to the US tax on foreign-source income and there is none — so the credit
    stops being an argument for the taxable account at exactly the bracket where the
    arithmetic would otherwise have favoured it.
    """
    assert location_breakeven_rate(
        international=EMERGING_MARKETS,
        domestic_dividend_yield=US_EQUITY_YIELD,
        foreign_credit_utilisation=0.0,
    ) == pytest.approx(0.0)


def test_the_break_even_needs_the_international_yield_to_be_the_higher_one() -> None:
    with pytest.raises(ValueError, match="must exceed the domestic yield"):
        location_breakeven_rate(international=DEVELOPED_EX_US, domestic_dividend_yield=0.05)


@pytest.mark.parametrize(
    ("regime", "expected_order"),
    [
        (
            TOP_BRACKET,
            (
                "Taxable investment-grade bonds",
                "Developed ex-US equity",
                "Emerging-market equity",
                "US equity",
            ),
        ),
        (
            UPPER_MIDDLE_BRACKET,
            (
                "Taxable investment-grade bonds",
                "Developed ex-US equity",
                "US equity",
                "Emerging-market equity",
            ),
        ),
    ],
)
def test_the_shelter_ranking_inverts_between_brackets(
    regime: TaxRegime, expected_order: tuple[str, ...]
) -> None:
    """Emerging-market equity falls **below** US equity at 15%, and rises above it at 23.8%.

    Ranking by ``taxable cost - irrecoverable withholding``. Bonds dominate everywhere by
    a factor of four, which is the part of the conventional rule that is not in doubt.
    The contested part — where foreign equity sits — reverses inside the US rate
    schedule, which no source read for this page states.
    """
    ranking = shelter_priority_bp(SHELTER_CANDIDATES, regime=regime)
    assert tuple(label for label, _ in ranking) == expected_order


def test_the_credit_costs_the_ranking_its_margin_not_its_order_at_the_top() -> None:
    """At 23.8% the credit cuts developed markets from 61.9 to 46.1 bp of priority.

    Emerging markets is cut from 48.3 to 28.3, which leaves it only 2.1 bp above US
    equity — a margin far inside the uncertainty in either yield. The honest reading is
    that at the top bracket the credit makes the emerging/US shelter choice a **tie**,
    not that it reverses it.
    """
    ranking = dict(shelter_priority_bp(SHELTER_CANDIDATES, regime=TOP_BRACKET))
    assert ranking["Taxable investment-grade bonds"] == pytest.approx(189.72, abs=0.01)
    assert ranking["Developed ex-US equity"] == pytest.approx(46.10, abs=0.01)
    assert ranking["Emerging-market equity"] == pytest.approx(28.31, abs=0.01)
    assert ranking["US equity"] == pytest.approx(26.18, abs=0.01)
    assert ranking["Emerging-market equity"] - ranking["US equity"] < 3.0
    # Without the forfeiture the margin would be more than ten times larger.
    emerging = next(c for c in SHELTER_CANDIDATES if c.label == "Emerging-market equity")
    assert emerging.taxable_cost_bp(TOP_BRACKET) == pytest.approx(48.31, abs=0.01)
    assert emerging.taxable_cost_bp(TOP_BRACKET) - ranking["US equity"] > 20.0


def test_nothing_is_worth_sheltering_at_a_zero_dividend_rate_except_bonds() -> None:
    """In the 0% long-term bracket every equity sleeve scores exactly zero priority."""
    ranking = dict(shelter_priority_bp(SHELTER_CANDIDATES, regime=ZERO_RATE_BRACKET))
    assert ranking["Taxable investment-grade bonds"] == pytest.approx(0.12 * 0.0465 / 1e-4)
    for label in ("Developed ex-US equity", "Emerging-market equity", "US equity"):
        assert ranking[label] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize(("limit", "assets"), [(300.0, 190_153.0), (600.0, 380_305.0)])
def test_form_1116_thresholds_translate_into_sleeve_sizes(limit: float, assets: float) -> None:
    """$300 single / $600 joint of foreign tax is $190k / $380k of the developed sleeve.

    Below it the credit is claimed on Schedule 3 without Form 1116 and without the §904
    limitation. Above it the limitation binds, which is exactly where
    ``foreign_credit_utilisation`` stops being 1.0. Both thresholds are nominal and have
    never been indexed, so the fraction of investors above them rises mechanically.
    """
    assert form_1116_threshold_assets(
        foreign_tax_limit=limit, sleeve=DEVELOPED_EX_US
    ) == pytest.approx(assets, abs=1.0)


# --------------------------------------------------------------------------------------
# 2. Capital-gain distributions
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("distribution_yield", "liquidate_bp", "step_up_bp"),
    [(0.02, 25.69, 47.71), (0.05, 62.97, 119.71), (0.07, 84.12, 162.21)],
)
def test_distribution_drag_is_far_below_its_headline_tax(
    distribution_yield: float, liquidate_bp: float, step_up_bp: float
) -> None:
    """A 5%-of-NAV distribution costs 63 bp/yr, not the 119 bp of tax it triggers.

    The headline tax at the top bracket is ``23.8% x 5% = 119 bp``. Almost half of that
    comes back through the basis step the distribution creates, so the true cost is the
    lost deferral. Quoting the headline is the standard overstatement, and quoting the
    ``STEP_UP`` figure as though it applied to a liquidating investor is the standard
    understatement running the other way.
    """
    assert capital_gain_distribution_drag_bp(
        regime=TOP_BRACKET,
        pretax_log_growth=0.07,
        years=30,
        distribution_yield=distribution_yield,
    ) == pytest.approx(liquidate_bp, abs=0.01)
    assert capital_gain_distribution_drag_bp(
        regime=TOP_BRACKET,
        pretax_log_growth=0.07,
        years=30,
        distribution_yield=distribution_yield,
        disposal=Disposal.STEP_UP,
    ) == pytest.approx(step_up_bp, abs=0.01)


def test_distribution_drag_is_zero_in_a_sheltered_account_by_construction() -> None:
    """The whole ETF-versus-mutual-fund argument is a taxable-account argument."""
    sheltered = after_tax_path(
        regime=TOP_BRACKET,
        account=Account.TAX_DEFERRED,
        pretax_log_growth=0.07,
        years=30,
        capital_gain_distribution_yield=0.07,
    )
    clean = after_tax_path(
        regime=TOP_BRACKET,
        account=Account.TAX_DEFERRED,
        pretax_log_growth=0.07,
        years=30,
        capital_gain_distribution_yield=0.0,
    )
    assert sheltered.terminal_wealth == pytest.approx(clean.terminal_wealth, rel=1e-12)


def test_distribution_drag_is_monotone_in_the_distribution_rate() -> None:
    drags = [
        capital_gain_distribution_drag_bp(
            regime=TOP_BRACKET, pretax_log_growth=0.07, years=30, distribution_yield=d
        )
        for d in (0.0, 0.01, 0.03, 0.05, 0.08)
    ]
    assert drags == sorted(drags)
    assert drags[0] == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------------------
# 3. Section 1256
# --------------------------------------------------------------------------------------


def test_section_1256_saves_ten_point_two_points_of_rate_and_destroys_deferral() -> None:
    """51 bp/yr saved on a 5% return, against 82 bp/yr of deferral destroyed.

    The rate arbitrage is ``(40.8% - 30.6%) x 5% = 51 bp``. The deferral cost compares
    annual mark-to-market at 30.6% against never realising until liquidation at 23.8%
    over thirty years. §1256 is therefore a large win against ordinary annual income and
    a clear loss against a buy-and-hold equity position — and which of those is the
    counterfactual is the whole question.
    """
    comparison = section_1256_comparison(
        regime=TOP_BRACKET, annual_return=0.05, pretax_log_growth=0.05, years=30
    )
    assert comparison.blended_rate == pytest.approx(0.306)
    assert comparison.saving_against_ordinary_bp == pytest.approx(
        (0.408 - 0.306) * 0.05 / 1e-4, rel=1e-12
    )
    assert comparison.saving_against_ordinary_bp == pytest.approx(51.0, abs=0.01)
    assert comparison.cost_against_deferred_capital_gain_bp == pytest.approx(82.22, abs=0.01)
    assert comparison.net_bp == pytest.approx(-31.22, abs=0.01)


def test_section_1256_has_no_deferral_cost_at_a_zero_capital_gains_rate() -> None:
    """In the 0% long-term bracket the blend is a pure tax **increase**: 0.4 x 12% = 4.8%."""
    assert ZERO_RATE_BRACKET.section_1256_blended == pytest.approx(0.048)
    comparison = section_1256_comparison(
        regime=ZERO_RATE_BRACKET, annual_return=0.05, pretax_log_growth=0.05, years=30
    )
    assert comparison.saving_against_ordinary_bp == pytest.approx(
        (0.12 - 0.048) * 0.05 / 1e-4, rel=1e-12
    )


# --------------------------------------------------------------------------------------
# 4. Deferral and the step-up
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("years", "deferral_bp", "step_up_bp"),
    [(10, 34.59, 127.62), (20, 63.41, 98.80), (30, 84.12, 78.09), (40, 98.96, 63.25)],
)
def test_deferral_grows_with_horizon_and_the_step_up_shrinks_to_meet_it(
    years: int, deferral_bp: float, step_up_bp: float
) -> None:
    """The two halves trade off exactly, and their sum is horizon-free at 162.21 bp/yr.

    That total is ``g - log(e**g (1 - q) + q)``, the gap between never realising and
    realising everything every year, which contains no ``H`` at all. So the *value of
    never paying* is a constant 162 bp/yr at these parameters; the horizon only decides
    how much of it is deferral and how much is forgiveness.
    """
    value = deferral_value(regime=TOP_BRACKET, pretax_log_growth=0.07, years=years)
    assert value.deferral_bp == pytest.approx(deferral_bp, abs=0.01)
    assert value.step_up_bp == pytest.approx(step_up_bp, abs=0.01)
    q = TOP_BRACKET.capital_gain
    horizon_free = (0.07 - math.log(math.exp(0.07) * (1.0 - q) + q)) / 1e-4
    assert value.total_bp == pytest.approx(horizon_free, rel=1e-9)
    assert value.total_bp == pytest.approx(162.21, abs=0.01)


def test_the_deferral_hurdle_exceeds_the_whole_booked_contractual_budget() -> None:
    """84 bp/yr at thirty years, against 89 bp/yr for the entire own-counterfactual budget.

    A high-turnover strategy in a taxable account must clear this before it clears its
    fee or its spread. It is the strongest quantitative argument on the page against
    turnover, and it is an argument the fee-focused version of the budget does not make.
    """
    hurdle = deferral_value(regime=TOP_BRACKET, pretax_log_growth=0.07, years=30).deferral_bp
    booked = budget_for(Benchmark.COUNTERFACTUAL_HOLDING).central_bp
    assert booked == pytest.approx(89.0, abs=0.01)
    assert hurdle == pytest.approx(84.12, abs=0.01)
    assert hurdle / booked > 0.9


@pytest.mark.parametrize(
    ("realised_fraction", "drag_bp"),
    [(0.10, 41.52), (0.25, 63.89), (0.50, 76.40), (1.00, 84.12)],
)
def test_the_deferral_penalty_is_sharply_concave_in_turnover(
    realised_fraction: float, drag_bp: float
) -> None:
    """Half the full penalty arrives in the first tenth of the turnover.

    Realising a tenth of standing gain each year costs 41.5 bp against the 84.1 bp of
    realising all of it. "Low turnover" is therefore not a defence: the marginal cost of
    the *first* unit of turnover is by far the largest, because it starts the basis
    ratchet that every later year inherits.
    """
    assert deferral_value(
        regime=TOP_BRACKET,
        pretax_log_growth=0.07,
        years=30,
        realised_gain_fraction=realised_fraction,
    ).deferral_bp == pytest.approx(drag_bp, abs=0.01)


def test_deferral_is_worth_nothing_at_a_zero_capital_gains_rate() -> None:
    value = deferral_value(regime=ZERO_RATE_BRACKET, pretax_log_growth=0.07, years=30)
    assert value.total_bp == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------------------
# 5. Harvesting decay
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("profile", "year_one", "average_30", "net_of_nine"),
    [
        (HARVESTING_NO_FLOW_LONG_TERM, 155.3, 5.57, -3.43),
        (HARVESTING_NO_FLOW_SHORT_TERM, 339.1, 36.22, 27.22),
        (HARVESTING_WITH_CONTRIBUTIONS, 164.3, 34.59, 25.59),
    ],
)
def test_the_horizon_average_is_an_order_below_the_year_one_headline(
    profile: HarvestingProfile, year_one: float, average_30: float, net_of_nine: float
) -> None:
    """155.3 bp in year one becomes 5.6 bp averaged over thirty years.

    Vendor headlines quote year one, which is the largest number any of these profiles
    ever takes. The 30-year average is what a "bp/yr" claim about a long-horizon holding
    actually means, and for the modal case — no new money, only long-term gains to offset
    — it is **negative once any fee is charged**.
    """
    assert profile.horizon_average_bp(1) == pytest.approx(year_one)
    assert profile.horizon_average_bp(30) == pytest.approx(average_30, abs=0.01)
    assert profile.net_of_fee_bp(years=30, fee_bp=9.0) == pytest.approx(net_of_nine, abs=0.01)


def test_the_static_investor_profile_goes_negative_in_year_seven() -> None:
    """The published table turns negative before year ten and settles at -4.3 bp."""
    benefits = [HARVESTING_NO_FLOW_LONG_TERM.benefit_bp(y) for y in range(1, 13)]
    assert benefits[6] < 0.0  # year 7
    assert benefits[-1] == pytest.approx(-4.3)
    # Strictly decaying over the nine explicit years.
    assert benefits[:9] == sorted(benefits[:9], reverse=True)


def test_no_profile_survives_a_forty_basis_point_fee_over_thirty_years() -> None:
    """The load-bearing fee finding, stated as an assertion over every measured scenario."""
    for profile in (
        HARVESTING_NO_FLOW_LONG_TERM,
        HARVESTING_NO_FLOW_SHORT_TERM,
        HARVESTING_WITH_CONTRIBUTIONS,
    ):
        assert profile.net_of_fee_bp(years=30, fee_bp=40.0) < 0.0
    # And the published fee schedule really does span the decisive range.
    fees = [fee for _, fee, _ in DIRECT_INDEXING_FEES_BP]
    assert min(fees) == pytest.approx(9.0)
    assert max(fees) == pytest.approx(40.0)


def test_a_decaying_profile_crosses_its_own_fee_at_a_computable_date() -> None:
    """At a 40 bp fee the contributing investor's average benefit falls below it in year 18."""
    assert HARVESTING_WITH_CONTRIBUTIONS.break_even_horizon(fee_bp=40.0) == 18
    assert HARVESTING_WITH_CONTRIBUTIONS.horizon_average_bp(17) > 40.0
    assert HARVESTING_WITH_CONTRIBUTIONS.horizon_average_bp(18) < 40.0
    # A fee below the terminal level is never crossed inside the window.
    assert HARVESTING_WITH_CONTRIBUTIONS.break_even_horizon(fee_bp=9.0, max_years=200) is None


def test_harvested_losses_are_worth_almost_nothing_without_offsetting_gains() -> None:
    """§1211(b)'s $3,000 cap, unchanged since 1978 and unindexed, is the binding constraint.

    On a $1m portfolio harvesting 5% of value, the benefit falls from 119 bp with
    offsetting gains to **12.24 bp** without them, a ratio of nearly ten. Every vendor
    figure assumes the first case, and the assumption is rarely stated where the headline
    appears. At 40.8% the cap is worth at most $1,224 a year however large the portfolio,
    so the basis-point value falls with size.
    """
    with_gains = harvested_loss_value_bp(
        regime=TOP_BRACKET, harvested_loss_fraction=0.05, offsetting_gain_available=True
    )
    without = harvested_loss_value_bp(
        regime=TOP_BRACKET, harvested_loss_fraction=0.05, offsetting_gain_available=False
    )
    assert with_gains == pytest.approx(0.238 * 0.05 / 1e-4, rel=1e-12)
    assert with_gains == pytest.approx(119.0, abs=0.01)
    assert without == pytest.approx(0.408 * 3000.0 / 1_000_000.0 / 1e-4, rel=1e-12)
    assert without == pytest.approx(12.24, abs=0.01)
    assert with_gains / without == pytest.approx(9.72, abs=0.01)


def test_the_ordinary_offset_cap_shrinks_in_basis_points_as_the_portfolio_grows() -> None:
    """A nominal cap is a vanishing cap. $3,000 is 122 bp of $100k and 1.2 bp of $10m."""
    small = harvested_loss_value_bp(
        regime=TOP_BRACKET,
        harvested_loss_fraction=0.05,
        offsetting_gain_available=False,
        portfolio_value=100_000.0,
    )
    large = harvested_loss_value_bp(
        regime=TOP_BRACKET,
        harvested_loss_fraction=0.05,
        offsetting_gain_available=False,
        portfolio_value=10_000_000.0,
    )
    assert small == pytest.approx(122.4, abs=0.1)
    assert large == pytest.approx(1.224, abs=0.001)


# --------------------------------------------------------------------------------------
# 6. Account type, and the levers that are not material
# --------------------------------------------------------------------------------------


def test_traditional_and_roth_are_identical_when_the_two_rates_match() -> None:
    """Multiplication commutes. Account *type* is a rate forecast, not a structural edge."""
    traditional, roth = traditional_and_roth_are_equivalent(
        pretax_contribution=10_000.0,
        pretax_log_growth=0.07,
        years=30,
        rate_at_contribution=0.24,
        rate_at_withdrawal=0.24,
    )
    assert traditional == pytest.approx(roth, rel=1e-12)


def test_the_whole_difference_between_them_is_the_rate_change() -> None:
    """A saver falling from 32% to 22% gains exactly ``(0.32 - 0.22)/(1 - 0.32)`` = 14.7%."""
    traditional, roth = traditional_and_roth_are_equivalent(
        pretax_contribution=10_000.0,
        pretax_log_growth=0.07,
        years=30,
        rate_at_contribution=0.32,
        rate_at_withdrawal=0.22,
    )
    assert traditional / roth == pytest.approx((1.0 - 0.22) / (1.0 - 0.32), rel=1e-12)
    assert traditional / roth - 1.0 == pytest.approx(0.14706, abs=1e-5)


def test_specific_identification_defers_a_large_one_off_gain() -> None:
    """Twenty annual $10k purchases at 7%, selling a quarter: $51,215 of gain deferred.

    FIFO realises $83,159 of gain on $112,978 of proceeds; highest-in-first-out realises
    $31,944 on the same proceeds. At 23.8% that is $12,189 of tax deferred on a $268,000
    position — a real number, but a **timing** number, and one that shrinks every year as
    the high-basis lots age into the same low-basis condition.
    """
    selection = lot_selection_comparison(
        annual_purchase=10_000.0, purchases=20, pretax_log_growth=0.07, proceeds_fraction=0.25
    )
    assert selection.proceeds == pytest.approx(112_977.84, abs=0.01)
    assert selection.gain_first_in_first_out == pytest.approx(83_159.04, abs=0.01)
    assert selection.gain_highest_in_first_out == pytest.approx(31_943.67, abs=0.01)
    assert selection.deferred_gain == pytest.approx(51_215.37, abs=0.01)
    assert selection.gain_first_in_first_out > selection.gain_highest_in_first_out


def test_lot_selection_makes_no_difference_when_there_is_only_one_lot() -> None:
    selection = lot_selection_comparison(
        annual_purchase=10_000.0, purchases=1, pretax_log_growth=0.07, proceeds_fraction=1.0
    )
    assert selection.deferred_gain == pytest.approx(0.0, abs=1e-9)


def test_a_wash_sale_into_an_ira_destroys_the_deduction_outright() -> None:
    """Revenue Ruling 2008-5: no §1091(d) basis repair, so the loss is gone, not deferred."""
    assert wash_sale_across_accounts_cost_bp(
        regime=TOP_BRACKET, disallowed_loss_fraction=0.05
    ) == pytest.approx(0.238 * 0.05 / 1e-4, rel=1e-12)


@pytest.mark.parametrize(
    ("municipal", "taxable", "breakeven"),
    [(0.032, 0.040, 0.20), (0.026, 0.040, 0.35), (0.040, 0.040, 0.0)],
)
def test_the_municipal_break_even_is_one_minus_the_yield_ratio(
    municipal: float, taxable: float, breakeven: float
) -> None:
    """A muni/Treasury yield ratio of 0.80 implies a 20% break-even rate, exactly."""
    assert municipal_breakeven_rate(
        municipal_yield=municipal, taxable_yield=taxable
    ) == pytest.approx(breakeven, abs=1e-12)


def test_the_tax_equivalent_yield_inverts_the_break_even() -> None:
    """At the top bracket a 3.2% muni is worth a 5.41% taxable yield."""
    assert tax_equivalent_yield(
        municipal_yield=0.032, regime=TOP_BRACKET
    ) == pytest.approx(0.032 / (1.0 - 0.408), rel=1e-12)
    assert tax_equivalent_yield(municipal_yield=0.032, regime=TOP_BRACKET) == pytest.approx(
        0.05405, abs=1e-5
    )


def test_net_unrealised_appreciation_is_a_one_off_amortised_over_the_wait() -> None:
    """A 10% position at 20% basis, distributed in ten years: 15.3 bp/yr."""
    benefit = net_unrealised_appreciation_benefit_bp(
        regime=TOP_BRACKET,
        basis_fraction=0.20,
        employer_stock_fraction_of_portfolio=0.10,
        years_to_distribution=10,
    )
    assert benefit == pytest.approx((0.408 - 0.238) * 0.80 * 0.10 / 10 / 1e-4, rel=1e-12)
    assert benefit == pytest.approx(13.6, abs=0.01)


def test_a_non_qualified_dividend_costs_the_rate_gap_on_the_non_qualified_share() -> None:
    """A fund only 70% qualified on a 2% yield loses 10.2 bp/yr at the top bracket."""
    assert qualified_dividend_shortfall_bp(
        regime=TOP_BRACKET, dividend_yield=0.02, qualified_fraction=0.70
    ) == pytest.approx(0.30 * 0.02 * (0.408 - 0.238) / 1e-4, rel=1e-12)
    assert qualified_dividend_shortfall_bp(
        regime=TOP_BRACKET, dividend_yield=0.02, qualified_fraction=0.70
    ) == pytest.approx(10.2, abs=0.01)
    assert qualified_dividend_shortfall_bp(
        regime=TOP_BRACKET, dividend_yield=0.02, qualified_fraction=1.0
    ) == pytest.approx(0.0, abs=1e-12)


def test_tax_gain_harvesting_is_worth_the_rate_spread_and_only_that() -> None:
    """Realising 20% of the portfolio as gain at 0%, against a later 23.8%: 47.6 bp/yr over ten."""
    value = tax_gain_harvest_value_bp(
        harvesting_regime=ZERO_RATE_BRACKET,
        future_regime=TOP_BRACKET,
        gain_realised_fraction=0.20,
        years_until_sale=10,
    )
    assert value == pytest.approx(0.238 * 0.20 / 10 / 1e-4, rel=1e-12)
    assert value == pytest.approx(47.6, abs=0.01)
    # Harvesting into a *higher* future rate is worth nothing, never negative.
    assert tax_gain_harvest_value_bp(
        harvesting_regime=TOP_BRACKET,
        future_regime=ZERO_RATE_BRACKET,
        gain_realised_fraction=0.20,
        years_until_sale=10,
    ) == pytest.approx(0.0)


# --------------------------------------------------------------------------------------
# 7. Capital efficiency
# --------------------------------------------------------------------------------------


def test_a_ninety_sixty_fund_needs_ninety_two_basis_points_of_term_premium() -> None:
    """``break-even = financing spread + fee / bond notional`` = 58.70 + 20/0.60 = 92.03 bp.

    That is the whole capital-efficiency argument reduced to one number. Against a
    measured Treasury-futures funding basis of 58.70 bp/yr and NTSX's 20 bp fee, the
    overlay contributes nothing until the Treasury excess return over cash exceeds
    92 bp/yr — a term premium no experiment in this repository has signed.
    """
    assert NTSX.gross_notional == pytest.approx(1.50)
    assert NTSX.break_even_excess_return_bp() == pytest.approx(
        TREASURY_FUTURES_FUNDING_BASIS_BP + 20.0 / 0.60, rel=1e-12
    )
    assert NTSX.break_even_excess_return_bp() == pytest.approx(92.03, abs=0.01)
    # At the null — term premium exactly equal to the financing spread — the fund is
    # behind by precisely its own fee.
    assert NTSX.net_of_financing_bp == pytest.approx(0.0, abs=1e-12)
    assert NTSX.net_contribution_bp == pytest.approx(-NTSX.expense_ratio_bp, rel=1e-12)


def test_the_measured_financing_basis_matches_the_spread_that_kills_risk_parity() -> None:
    """58.70 bp measured against the 62.3 bp LIBOR spread at which AFP's own t-stat fails.

    Asness, Frazzini and Pedersen defend levered risk parity with the assertion that
    futures finance below LIBOR. Fleckenstein and Longstaff measure the Treasury-futures
    funding basis at 58.70 bp, which is within 6% of the 62.3 bp LIBOR spread at which
    their own Appendix B shows the advantage losing significance. The equity-futures roll
    is if anything worse.
    """
    libor_spread_bp = 62.3
    assert pytest.approx(58.70) == TREASURY_FUTURES_FUNDING_BASIS_BP
    assert abs(TREASURY_FUTURES_FUNDING_BASIS_BP - libor_spread_bp) / libor_spread_bp < 0.06
    assert EQUITY_FUTURES_ROLL_RICHNESS_BP > TREASURY_FUTURES_FUNDING_BASIS_BP


@pytest.mark.parametrize(
    ("term_premium_bp", "net_bp"), [(0.0, -55.22), (50.0, -25.22), (92.03, 0.0), (150.0, 34.78)]
)
def test_the_sign_of_capital_efficiency_turns_entirely_on_a_forecast(
    term_premium_bp: float, net_bp: float
) -> None:
    """Move the term premium and the answer flips sign. That is what probabilistic means.

    Nothing about §1256, the fee, or the notional is in doubt; the only unknown is a
    premium, and it is the one thing this repository has no signed estimate of. That is
    why no figure from the capital-efficiency section enters the ledger.
    """
    fund = CapitalEfficiency(
        label="90/60 at a stated term premium",
        equity_notional=0.90,
        bond_notional=0.60,
        expense_ratio_bp=20.0,
        bond_excess_return_bp=term_premium_bp,
        implied_financing_spread_bp=TREASURY_FUTURES_FUNDING_BASIS_BP,
    )
    assert fund.net_contribution_bp == pytest.approx(net_bp, abs=0.01)


# --------------------------------------------------------------------------------------
# The ledger, and the double-count guards
# --------------------------------------------------------------------------------------


def test_every_ledger_line_carries_a_falsifier_and_a_double_count_verdict() -> None:
    assert STRUCTURAL_LEDGER
    for lever in STRUCTURAL_LEDGER:
        assert lever.falsifier.strip()
        assert lever.double_count_note.strip()
        assert lever.conditions.strip()
        assert lever.mechanism.strip()


def test_a_lever_without_a_falsifier_is_refused() -> None:
    with pytest.raises(ValueError, match="needs a falsifier"):
        StructuralLever(
            name="unfalsifiable",
            mechanism="m",
            benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
            certainty=Certainty.DETERMINISTIC,
            additivity=Additivity.ADDITIVE,
            low_bp=0.0,
            central_bp=1.0,
            high_bp=2.0,
            conditions="c",
            falsifier="  ",
            double_count_note="n",
        )


def test_an_additive_line_with_a_zero_central_estimate_is_refused() -> None:
    """If it does not carry a positive central estimate it is NOT_BOOKABLE, not additive."""
    with pytest.raises(ValueError, match="must carry a positive central"):
        StructuralLever(
            name="empty",
            mechanism="m",
            benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
            certainty=Certainty.DETERMINISTIC,
            additivity=Additivity.ADDITIVE,
            low_bp=-5.0,
            central_bp=0.0,
            high_bp=5.0,
            conditions="c",
            falsifier="f",
            double_count_note="n",
        )


def test_the_ledger_refuses_to_total_across_benchmarks() -> None:
    """The same guard ``aggregate`` carries, for the same reason."""
    mixed = (
        StructuralLever(
            name="a",
            mechanism="m",
            benchmark=Benchmark.COUNTERFACTUAL_HOLDING,
            certainty=Certainty.DETERMINISTIC,
            additivity=Additivity.ADDITIVE,
            low_bp=0.0,
            central_bp=10.0,
            high_bp=20.0,
            conditions="c",
            falsifier="f",
            double_count_note="n",
        ),
        StructuralLever(
            name="b",
            mechanism="m",
            benchmark=Benchmark.STATED_INDEX,
            certainty=Certainty.DETERMINISTIC,
            additivity=Additivity.ADDITIVE,
            low_bp=0.0,
            central_bp=10.0,
            high_bp=20.0,
            conditions="c",
            falsifier="f",
            double_count_note="n",
        ),
    )
    with pytest.raises(ValueError, match="must share one benchmark"):
        additive_total(mixed)


def test_only_the_additive_lines_reach_the_total() -> None:
    total = additive_total(STRUCTURAL_LEDGER)
    additive = [
        lever for lever in STRUCTURAL_LEDGER if lever.additivity is Additivity.ADDITIVE
    ]
    assert total.lines == len(additive)
    assert total.central_bp == pytest.approx(sum(lever.central_bp for lever in additive))
    assert total.low_bp <= total.central_bp <= total.high_bp
    # Everything that is not additive must say why, and there must be some of each.
    assert any(lever.additivity is Additivity.ALREADY_COUNTED for lever in STRUCTURAL_LEDGER)
    assert any(lever.additivity is Additivity.NOT_BOOKABLE for lever in STRUCTURAL_LEDGER)


def test_the_two_lines_this_page_corrects_are_the_ones_already_in_the_budget() -> None:
    """The existing tax lines are 30 bp and 10 bp; this page revises both downward.

    Stated as a test so the correction cannot drift apart from the page that makes it.
    """
    assert TAX_LOSS_HARVESTING.central_bp == pytest.approx(30.0)
    assert ASSET_LOCATION.central_bp == pytest.approx(10.0)
    assert TAX_LOSS_HARVESTING.benchmark is Benchmark.COUNTERFACTUAL_HOLDING
    assert ASSET_LOCATION.benchmark is Benchmark.COUNTERFACTUAL_HOLDING
    # And the corrections this page books are exactly the size of those revisions.
    assert HARVESTING_WITH_CONTRIBUTIONS.net_of_fee_bp(
        years=30, fee_bp=9.0
    ) - TAX_LOSS_HARVESTING.central_bp == pytest.approx(-4.41, abs=0.01)
    forfeited = 0.14 * DEVELOPED_EX_US.forfeited_bp + 0.06 * EMERGING_MARKETS.forfeited_bp
    assert -forfeited == pytest.approx(-3.41, abs=0.01)


def test_the_two_additive_lines_are_the_only_ones_that_reach_the_total() -> None:
    """+23 bp of fund structure and +5 bp of lot selection; nothing else is additive.

    Every other lever on the page is a correction to an existing line, a hurdle, a
    circumstance, or an avoided error. Pinning that here is the whole point of the
    additivity classification: the count is the claim.
    """
    total = additive_total(STRUCTURAL_LEDGER)
    assert total.lines == 2
    assert total.central_bp == pytest.approx(28.0)
    assert total.low_bp == pytest.approx(0.0)
    assert total.high_bp == pytest.approx(94.0)
    names = {
        lever.name for lever in STRUCTURAL_LEDGER if lever.additivity is Additivity.ADDITIVE
    }
    assert names == {
        "Fund structure: capital-gain distributions avoided",
        "Specific identification of tax lots",
    }


def test_the_revised_budget_is_about_a_fifth_larger_than_the_one_it_replaces() -> None:
    """89 bp + 28 bp additive - 7.8 bp of corrections = 109.2 bp.

    The corrections are counted because they carry a negative central estimate and are
    marked ALREADY_COUNTED; the securities-lending revision is excluded from this total
    because it is measured against the *stated index*, not the counterfactual, and the
    budget never aggregates across benchmarks.
    """
    assert pytest.approx(89.0) == BOOKED_COUNTERFACTUAL_BUDGET_BP
    assert revised_counterfactual_budget_bp() == pytest.approx(109.2, abs=0.01)
    assert revised_counterfactual_budget_bp() / BOOKED_COUNTERFACTUAL_BUDGET_BP == pytest.approx(
        1.227, abs=0.001
    )
    # The stated-index line must not have leaked into a counterfactual total.
    assert SECURITIES_LENDING_BY_ASSET_CLASS.benchmark is Benchmark.STATED_INDEX


def test_a_fifth_more_edge_buys_about_two_months_of_confidence() -> None:
    """The point of the whole exercise, and the one that is easy to overstate.

    At 89 bp against 41 bp of tracking error, 99% confidence takes 13.8 months. At
    109.2 bp against a combined 46.3 bp it takes 11.7. Certainty is a property of the
    pairing, not of the edge's size, exactly as the edge decomposition already argues.
    """
    combined_te_bp = math.sqrt(41.0**2 + 20.0**2 + 8.0**2)
    assert combined_te_bp == pytest.approx(46.31, abs=0.01)
    before = horizon_for_confidence(edge_bp=89.0, tracking_error_bp=41.0, confidence=0.99) * 12.0
    after = (
        horizon_for_confidence(
            edge_bp=revised_counterfactual_budget_bp(),
            tracking_error_bp=combined_te_bp,
            confidence=0.99,
        )
        * 12.0
    )
    assert before == pytest.approx(13.8, abs=0.1)
    assert after == pytest.approx(11.7, abs=0.1)
    assert before - after < 3.0


def test_the_reference_investor_is_stated_and_its_weights_sum_to_one() -> None:
    """A portfolio-level figure without a stated portfolio is the commonest inflation."""
    assert "60% US equity" in REFERENCE_INVESTOR
    assert pytest.approx(1.0) == 0.60 + 0.14 + 0.06 + 0.20


@pytest.mark.parametrize(
    ("term", "breakeven", "pickup_bp"),
    [("2 year", 0.3981, 7.0), ("5 year", 0.3501, 43.0), ("10 year", 0.3062, 80.0),
     ("30 year", 0.1558, 222.0)],
)
def test_the_municipal_break_even_falls_from_forty_percent_to_sixteen(
    term: str, breakeven: float, pickup_bp: float
) -> None:
    """The maturity dependence that makes "municipals for taxable accounts" wrong as a rule.

    At two years a top-bracket investor gains 7 bp; at thirty, 222 bp. A scalar rule
    cannot express that, and the break-even marginal rate crosses the top bracket
    somewhere between two and five years.
    """
    municipal, taxable = next((m, t) for label, m, t in MUNICIPAL_CURVE if label == term)
    assert municipal_breakeven_rate(
        municipal_yield=municipal, taxable_yield=taxable
    ) == pytest.approx(breakeven, abs=1e-4)
    pickup = (
        tax_equivalent_yield(municipal_yield=municipal, regime=TOP_BRACKET) - taxable
    ) / 1e-4
    assert pickup == pytest.approx(pickup_bp, abs=0.5)


def test_the_shortest_municipal_maturity_is_the_one_a_top_bracket_investor_should_skip() -> None:
    """Its break-even of 39.81% sits *above* the 40.8% top rate by less than a point."""
    _, municipal, taxable = MUNICIPAL_CURVE[0]
    breakeven = municipal_breakeven_rate(municipal_yield=municipal, taxable_yield=taxable)
    assert breakeven < TOP_BRACKET.ordinary
    assert TOP_BRACKET.ordinary - breakeven < 0.01
