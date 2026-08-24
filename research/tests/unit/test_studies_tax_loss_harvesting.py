"""Harvesting and direct indexing: the arithmetic, and the two identities it rests on.

The identities are worth more than the figures. Harvesting reduces basis by exactly the
loss it realises, and on liquidation the carryforward absorbs exactly the part of that
extra gain that was never used. If either fails, every basis point on the page is wrong
in a way no sensitivity analysis would reveal.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.tax_loss_harvesting import (
    MIDDLE_BRACKET,
    ORDINARY_OFFSET_CAP,
    Disposal,
    HarvestingValue,
    HarvestRule,
    HarvestYieldPaths,
    LossUsage,
    MarketAssumptions,
    Reversibility,
    active_risk_from_substitution,
    lock_in_exit_cost_bp,
    ordinary_offset_ceiling_bp,
    routes,
    simulate_harvest_yield,
    value_harvesting,
)
from portfolio_edge.studies.tax_structure import TOP_BRACKET, UPPER_MIDDLE_BRACKET

MARKET = MarketAssumptions(
    annual_total_log_drift=0.07,
    annual_market_volatility=0.158,
    annual_idiosyncratic_volatility=0.35,
    dividend_yield=0.015,
)
FUND_ONLY = MarketAssumptions(
    annual_total_log_drift=0.07,
    annual_market_volatility=0.158,
    annual_idiosyncratic_volatility=0.0,
    dividend_yield=0.015,
)


def rule(**overrides: object) -> HarvestRule:
    """A small but honest configuration: short enough for a test, long enough to decay."""
    settings: dict[str, object] = {
        "years": 15,
        "harvest_threshold": 0.05,
        "contribution_rate": 0.10,
        "lots_per_month": 4,
        "paths": 60,
        "seed": 20260823,
    }
    settings.update(overrides)
    return HarvestRule(**settings)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# The two identities
# --------------------------------------------------------------------------------------


def test_harvesting_reduces_basis_by_exactly_the_loss_it_realises() -> None:
    """The whole valuation rests on this and nothing else checks it.

    A harvest sells a lot and reinvests the proceeds, so the account's value is
    unchanged and its basis falls by the realised loss. Summed over a lifetime, the
    difference between the never-selling account's basis and the harvested account's
    basis must equal every loss ever realised, to floating point.
    """
    paths = simulate_harvest_yield(MARKET, rule())
    realised = (paths.total_loss * paths.mean_account_value).sum(axis=1)
    difference = paths.terminal_basis_held - paths.terminal_basis_harvested
    assert np.allclose(difference, realised, rtol=0.0, atol=1e-9)


def test_liquidation_clawback_equals_the_capital_gain_rate_on_the_losses_used() -> None:
    """The second identity, checked against an independently computed hand fixture.

    Two years, one path, no growth, no dividend, a 10% short-term loss in year one and a
    10% long-term loss in year two, on a $100,000 account so the §1211(b) cap is 3% of
    it. By hand: $3,000 is deducted in each year at the 37% wage rate, so the saving is
    ``0.03 x 0.37`` twice; ``U = 0.06`` and the carryforward is 0.14. Liquidating a
    position worth 2.0 against a never-sold basis of 1.0 and a harvested basis of 0.8,
    the extra tax is ``0.238 x 0.06`` and the net gain is ``(0.37 - 0.238) x 0.06``.
    """
    paths = _hand_fixture()
    usage = LossUsage(account_value=100_000.0, marginal_ordinary_rate_on_wages=0.37)
    liquidated = value_harvesting(
        paths,
        regime=TOP_BRACKET,
        usage=usage,
        disposal=Disposal.LIQUIDATE,
        direct_index_fee=0.0,
        replaced_fund_cost=0.0,
    )
    stepped_up = value_harvesting(
        paths,
        regime=TOP_BRACKET,
        usage=usage,
        disposal=Disposal.STEP_UP,
        direct_index_fee=0.0,
        replaced_fund_cost=0.0,
    )

    assert liquidated.used[0] == pytest.approx(0.06)
    assert liquidated.unused_carryforward[0] == pytest.approx(0.14)
    assert liquidated.ordinary_offset[0] == pytest.approx(0.06)

    saving = 2.0 * 0.03 * 0.37
    held_after_tax = 2.0 - 0.238 * 1.0
    harvested_after_tax = held_after_tax + saving - 0.238 * 0.06
    expected = math.log(harvested_after_tax / held_after_tax) / 2.0 * 1e4
    assert liquidated.median_bp == pytest.approx(expected, rel=1e-9)
    assert harvested_after_tax - held_after_tax == pytest.approx((0.37 - 0.238) * 0.06)

    expected_step_up = math.log((2.0 + saving) / 2.0) / 2.0 * 1e4
    assert stepped_up.median_bp == pytest.approx(expected_step_up, rel=1e-9)


def _hand_fixture() -> HarvestYieldPaths:
    """A two-year, one-path panel written out by hand rather than simulated."""
    return HarvestYieldPaths(
        short_term_loss=np.array([[0.10, 0.0]]),
        long_term_loss=np.array([[0.0, 0.10]]),
        harvest_turnover=np.zeros((1, 2)),
        mean_account_value=np.ones((1, 2)),
        terminal_value=np.array([2.0]),
        terminal_basis_harvested=np.array([0.8]),
        terminal_basis_held=np.array([1.0]),
        embedded_gain_fraction=np.array([0.6]),
        assumptions=MarketAssumptions(
            annual_total_log_drift=0.0,
            annual_market_volatility=0.10,
            annual_idiosyncratic_volatility=0.0,
            dividend_yield=0.0,
        ),
        rule=HarvestRule(
            years=2, harvest_threshold=0.05, contribution_rate=0.0, lots_per_month=1,
            paths=1, seed=0,
        ),
    )


# --------------------------------------------------------------------------------------
# The decay curve, which is the thing vendor headlines hide
# --------------------------------------------------------------------------------------


def test_the_harvest_yield_decays_and_contributions_are_what_stop_it() -> None:
    """Ossification is self-inflicted: loss lots are sold and gain lots retained.

    Without new money the yield falls by more than an order of magnitude. With new money
    it settles at a level several times higher, because every contribution buys a lot
    whose basis is the current price.
    """
    static = simulate_harvest_yield(MARKET, rule(contribution_rate=0.0)).decay_curve()
    contributing = simulate_harvest_yield(MARKET, rule()).decay_curve()

    assert static[0] > 0.10
    assert static[-1] < static[0] / 10.0
    assert contributing[-1] > 2.0 * static[-1]
    assert contributing[-1] < contributing[0] / 3.0


def test_a_fund_harvests_a_fraction_of_what_the_securities_inside_it_harvest() -> None:
    """The whole case for direct indexing in one assertion.

    A fund passes through no security-level loss, so the only harvestable losses are
    market-wide ones. Setting idiosyncratic volatility to zero is exactly that case, and
    it is the same model at the boundary rather than a different one.
    """
    fund = simulate_harvest_yield(FUND_ONLY, rule()).decay_curve()
    direct = simulate_harvest_yield(MARKET, rule()).decay_curve()
    assert fund[-1] < direct[-1] / 4.0
    assert fund[0] < direct[0] / 2.0


def test_dispersion_raises_the_harvest_yield_monotonically() -> None:
    curves = [
        simulate_harvest_yield(
            MarketAssumptions(0.07, 0.158, sigma, 0.015), rule()
        ).decay_curve()[-1]
        for sigma in (0.0, 0.25, 0.35, 0.45)
    ]
    assert curves == sorted(curves)


# --------------------------------------------------------------------------------------
# Usage: the constraint the vendor figures assume away
# --------------------------------------------------------------------------------------


def _value(
    *,
    gains: float,
    disposal: Disposal,
    fee: float = 0.0009,
    account: float = 1_000_000.0,
    wash: float = 0.0,
) -> HarvestingValue:
    paths = simulate_harvest_yield(MARKET, rule())
    usage = LossUsage(
        account_value=account,
        annual_long_term_gain_fraction=gains,
        marginal_ordinary_rate_on_wages=0.37,
        wash_sale_disallowed_fraction=wash,
    )
    return value_harvesting(
        paths,
        regime=TOP_BRACKET,
        usage=usage,
        disposal=disposal,
        direct_index_fee=fee,
        replaced_fund_cost=0.000116,
    )


def test_without_offsetting_gains_almost_none_of_the_harvested_loss_is_ever_used() -> None:
    """§1211(b) caps the deduction at $3,000 and §1212(b) only defers the rest.

    On a seven-figure account harvesting several percent a year, the share of realised
    losses that ever produces a tax saving is a low single-digit percentage over the
    fifteen years tested here and falls further over thirty, because the cap is nominal
    while the account compounds. The remainder stands as a carryforward that a §1014
    step-up destroys.
    """
    value = _value(gains=0.0, disposal=Disposal.STEP_UP)
    assert value.usable_share < 0.02
    assert value.median_bp < 0.0
    assert value.probability_negative == pytest.approx(1.0)


def test_the_ordinary_offset_ceiling_falls_with_account_size_and_is_a_closed_form() -> None:
    assert ordinary_offset_ceiling_bp(
        account_value=1_000_000.0, marginal_ordinary_rate=0.37
    ) == pytest.approx(3_000.0 * 0.37 / 1_000_000.0 * 1e4)
    assert ordinary_offset_ceiling_bp(
        account_value=100_000.0, marginal_ordinary_rate=0.37
    ) == pytest.approx(111.0)
    small = ordinary_offset_ceiling_bp(account_value=100_000.0, marginal_ordinary_rate=0.37)
    large = ordinary_offset_ceiling_bp(account_value=3_000_000.0, marginal_ordinary_rate=0.37)
    assert small == pytest.approx(30.0 * large)


def test_a_stream_of_realised_gains_is_what_makes_direct_indexing_pay() -> None:
    with_gains = _value(gains=0.05, disposal=Disposal.STEP_UP)
    without = _value(gains=0.0, disposal=Disposal.STEP_UP)
    assert with_gains.usable_share > 0.5
    assert with_gains.median_bp > 0.0
    assert with_gains.median_bp - without.median_bp > 15.0


# --------------------------------------------------------------------------------------
# The disposal path, which is the whole decision
# --------------------------------------------------------------------------------------


def test_a_step_up_is_worth_strictly_more_than_a_liquidation_whenever_losses_are_used() -> None:
    """§1014 forgives the basis reduction; a sale reverses it at the capital-gain rate."""
    for gains in (0.01, 0.03, 0.05):
        step_up = _value(gains=gains, disposal=Disposal.STEP_UP).median_bp
        liquidate = _value(gains=gains, disposal=Disposal.LIQUIDATE).median_bp
        assert step_up > liquidate


def test_a_charitable_gift_and_a_step_up_do_the_same_thing_to_a_harvested_basis() -> None:
    """§170 and §1014 both forgive the gain outright, so the comparison cannot separate
    them. The difference between the two lives in the deduction and its percentage
    limits, which are a property of the gift and not of the harvesting."""
    gift = _value(gains=0.03, disposal=Disposal.GIFT)
    step_up = _value(gains=0.03, disposal=Disposal.STEP_UP)
    assert np.allclose(gift.benefit_bp, step_up.benefit_bp)


def test_the_wash_sale_trap_destroys_the_deduction_without_restoring_the_basis() -> None:
    """Revenue Ruling 2008-5: the loss is disallowed and the IRA gets no §1091(d) basis
    increase. The taxable account still bought its replacement out of the proceeds, so
    the harm is kept and the good is lost, and the benefit must fall strictly."""
    clean = _value(gains=0.05, disposal=Disposal.LIQUIDATE)
    trapped = _value(gains=0.05, disposal=Disposal.LIQUIDATE, wash=0.20)
    assert trapped.median_bp < clean.median_bp
    assert trapped.used.sum() < clean.used.sum()


def test_the_benefit_is_largest_in_the_paths_where_the_market_did_worst() -> None:
    """Harvesting is a hedge on the tax bill, not a return. It should be negatively
    correlated with terminal wealth, which is what makes a mean a poor summary of it."""
    paths = simulate_harvest_yield(MARKET, rule())
    usage = LossUsage(
        account_value=1_000_000.0,
        annual_long_term_gain_fraction=0.03,
        marginal_ordinary_rate_on_wages=0.37,
    )
    value = value_harvesting(
        paths,
        regime=TOP_BRACKET,
        usage=usage,
        disposal=Disposal.STEP_UP,
        direct_index_fee=0.0009,
        replaced_fund_cost=0.000116,
    )
    correlation = float(np.corrcoef(value.benefit_bp, np.log(paths.terminal_value))[0, 1])
    assert correlation < -0.3


# --------------------------------------------------------------------------------------
# Costs
# --------------------------------------------------------------------------------------


def test_the_fee_enters_one_for_one_and_a_forty_basis_point_fee_cannot_be_recovered() -> None:
    cheap = _value(gains=0.03, disposal=Disposal.STEP_UP, fee=0.0009)
    dear = _value(gains=0.03, disposal=Disposal.STEP_UP, fee=0.0040)
    assert cheap.median_bp - dear.median_bp == pytest.approx(31.0, abs=1e-6)
    # An investor with no gains to shelter pays the fee for nothing, and the 40 bp tier
    # is the one two incumbent brokerages charge.
    assert _value(gains=0.0, disposal=Disposal.STEP_UP, fee=0.0040).median_bp < -30.0


def test_the_lock_in_cost_of_leaving_is_an_independently_computed_fixture() -> None:
    """A 56%-embedded-gain account at the top rate, abandoned with ten years left:
    ``-ln(1 - 0.238 x 0.56) / 10`` in basis points."""
    expected = -math.log(1.0 - 0.238 * 0.56) / 10.0 * 1e4
    assert lock_in_exit_cost_bp(
        embedded_gain_fraction=0.56, regime=TOP_BRACKET, remaining_years=10
    ) == pytest.approx(expected)
    assert lock_in_exit_cost_bp(
        embedded_gain_fraction=0.56, regime=TOP_BRACKET, remaining_years=10
    ) > 140.0


def test_active_risk_from_substitution_is_the_stated_closed_form() -> None:
    value = active_risk_from_substitution(
        annual_idiosyncratic_volatility=0.35,
        substituted_fraction=0.10,
        substitute_positions=50.0,
        substitute_correlation=0.70,
    )
    assert value == pytest.approx(0.10 / math.sqrt(50.0) * 0.35 * math.sqrt(0.6))
    assert active_risk_from_substitution(
        annual_idiosyncratic_volatility=0.35,
        substituted_fraction=0.10,
        substitute_positions=50.0,
        substitute_correlation=1.0,
    ) == pytest.approx(0.0)


# --------------------------------------------------------------------------------------
# Inputs, regimes and guards
# --------------------------------------------------------------------------------------


def test_the_middle_bracket_is_the_third_live_us_combination() -> None:
    assert MIDDLE_BRACKET.capital_gain == pytest.approx(0.188)
    assert MIDDLE_BRACKET.ordinary == pytest.approx(0.358)
    assert MIDDLE_BRACKET.as_of == "2026-08-23"


def test_the_statutory_cap_is_the_unindexed_figure_and_not_a_guess() -> None:
    assert ORDINARY_OFFSET_CAP == 3_000.0


def test_the_simulation_is_deterministic_in_its_seed() -> None:
    first = simulate_harvest_yield(MARKET, rule())
    second = simulate_harvest_yield(MARKET, rule())
    third = simulate_harvest_yield(MARKET, rule(seed=1))
    assert np.array_equal(first.total_loss, second.total_loss)
    assert not np.array_equal(first.total_loss, third.total_loss)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"years": 0},
        {"harvest_threshold": 0.0},
        {"harvest_threshold": 1.0},
        {"contribution_rate": -0.01},
        {"lots_per_month": 0},
        {"paths": 0},
    ],
)
def test_a_nonsensical_rule_refuses_to_construct(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        rule(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"account_value": 0.0},
        {"annual_long_term_gain_fraction": -0.1},
        {"annual_short_term_gain_fraction": 1.5},
        {"wash_sale_disallowed_fraction": 2.0},
        {"marginal_ordinary_rate_on_wages": 1.0},
        {"ordinary_offset_cap": -1.0},
    ],
)
def test_a_nonsensical_taxpayer_refuses_to_construct(kwargs: dict[str, object]) -> None:
    settings: dict[str, object] = {"account_value": 1_000_000.0}
    settings.update(kwargs)
    with pytest.raises(ValueError):
        LossUsage(**settings)  # type: ignore[arg-type]


def test_market_assumptions_reject_impossible_inputs() -> None:
    with pytest.raises(ValueError):
        MarketAssumptions(0.07, 0.0, 0.35, 0.015)
    with pytest.raises(ValueError):
        MarketAssumptions(0.07, 0.158, -0.1, 0.015)
    with pytest.raises(ValueError):
        MarketAssumptions(0.07, 0.158, 0.35, 1.0)


def test_the_price_drift_is_the_total_return_less_the_dividend() -> None:
    assert MARKET.annual_price_log_drift == pytest.approx(0.07 - 0.015)


def test_negative_fees_and_impossible_lock_ins_are_refused() -> None:
    paths = _hand_fixture()
    usage = LossUsage(account_value=1_000_000.0)
    with pytest.raises(ValueError):
        value_harvesting(
            paths,
            regime=UPPER_MIDDLE_BRACKET,
            usage=usage,
            disposal=Disposal.STEP_UP,
            direct_index_fee=-0.001,
            replaced_fund_cost=0.0,
        )
    with pytest.raises(ValueError):
        lock_in_exit_cost_bp(
            embedded_gain_fraction=1.0, regime=TOP_BRACKET, remaining_years=10
        )
    with pytest.raises(ValueError):
        ordinary_offset_ceiling_bp(account_value=-1.0, marginal_ordinary_rate=0.37)


def test_the_route_table_is_ordered_from_free_to_one_way() -> None:
    """The ranking the synthesis reports: the cheapest routes are also the reversible
    ones, and the only route that cannot be undone is also the only one that charges a
    fee."""
    table = routes()
    assert [route.reversibility for route in table] == [
        Reversibility.FREE,
        Reversibility.FREE,
        Reversibility.FREE,
        Reversibility.CHEAP,
        Reversibility.ONE_WAY,
    ]
    paying = [route for route in table if route.annual_fee_bp > 0.0]
    assert len(paying) == 1
    assert paying[0].reversibility is Reversibility.ONE_WAY
