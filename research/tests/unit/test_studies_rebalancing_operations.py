"""Tests for the operating study: units, account feasibility, and the executable rule."""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.notional_budget import NotionalLeg
from portfolio_edge.studies.rebalancing_operations import (
    BRACKETS,
    CANDIDATE_CAPITAL,
    FUND_TAX_PROFILE,
    Account,
    FundTaxProfile,
    Placement,
    RebalanceRule,
    TaxRegime,
    account_totals,
    after_tax_account_shares,
    capital_for_notional,
    check_placement,
    double_counted_capital,
    forced_realisation_cost,
    gain_fraction_after,
    gross_notional,
    headroom,
    implied_notional,
    max_achievable_headroom,
    min_drag_placement,
    minimum_detectable_effect,
    nearest_reachable,
    normalised_notional_capital,
    ordinary_rate_for,
    placement_costs_at,
    placement_drag_bp,
    placement_totals,
    portfolio_returns,
    relative_drift_to_infeasibility,
    simulate_operations,
    tracking_error,
    worst_relative_stretch,
)

TAXABLE_SHARE = 1.0 / 3.0


# --------------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------------


def test_candidate_capital_is_one_dollar_and_the_stated_regional_split() -> None:
    assert sum(CANDIDATE_CAPITAL.values()) == pytest.approx(1.0)
    assert CANDIDATE_CAPITAL["RSST"] + CANDIDATE_CAPITAL["VTI"] + CANDIDATE_CAPITAL[
        "AVLV"
    ] == pytest.approx(0.65)


def test_implied_notional_reproduces_the_published_exposure_table() -> None:
    """``src/content/portfolios.ts`` states 67.2 / 25 / 10 / 30 at 132% gross."""
    exposure = implied_notional(CANDIDATE_CAPITAL)
    assert exposure["us-equity"] == pytest.approx(0.6716)
    assert exposure["developed-ex-us-equity"] == pytest.approx(0.25)
    assert exposure["emerging-equity"] == pytest.approx(0.10)
    assert exposure["trend"] == pytest.approx(0.30)
    assert gross_notional(CANDIDATE_CAPITAL) == pytest.approx(1.3216)


def test_a_capital_weight_understates_the_stacks_equity_leg_by_a_known_amount() -> None:
    """30% of capital in RSST is 32.16 pp of US equity notional, not 30."""
    exposure = implied_notional({"RSST": 0.30})
    assert exposure["us-equity"] == pytest.approx(0.3216)
    assert exposure["trend"] == pytest.approx(0.30)


def test_capital_for_notional_hits_the_target_and_reports_the_shortfall() -> None:
    fixed = capital_for_notional(
        CANDIDATE_CAPITAL, kind="us-equity", target=0.65, adjust=["VTI", "AVLV"]
    )
    assert implied_notional(fixed)["us-equity"] == pytest.approx(0.65)
    # Delivering 65 rather than 67.16 frees 2.16 pp of capital, which becomes cash.
    assert sum(fixed.values()) == pytest.approx(1.0 - 0.0216, abs=1e-9)
    assert fixed["VTI"] / fixed["AVLV"] == pytest.approx(20.0 / 15.0)


def test_capital_for_notional_refuses_when_the_fixed_lines_already_overshoot() -> None:
    with pytest.raises(ValueError, match="negative weight"):
        capital_for_notional(
            CANDIDATE_CAPITAL, kind="us-equity", target=0.20, adjust=["VTI"]
        )


def test_capital_for_notional_refuses_a_line_carrying_none_of_the_kind() -> None:
    with pytest.raises(ValueError, match="no rescaling"):
        capital_for_notional(
            CANDIDATE_CAPITAL, kind="trend", target=0.40, adjust=["VTI"]
        )


def test_both_unit_mistakes_lose_about_a_quarter_of_the_trend_sleeve() -> None:
    for mistake in (normalised_notional_capital(), double_counted_capital()):
        assert mistake.capital_deployed == pytest.approx(1.0)
        error = mistake.error_by_kind["trend"]
        assert -0.08 < error < -0.06, mistake.label
        assert error / 0.30 < -0.20, mistake.label


def test_a_leg_ratio_of_one_would_make_the_capital_sheet_accidentally_right() -> None:
    """The trap is invisible only because RSST's *trend* leg happens to be 1.0.

    Give the wrapper a 1.5x trend leg and the same capital weights deliver 45 pp of
    trend, so a sheet that reads the capital weight as the exposure is out by half.
    """
    legs = {
        name: (
            (NotionalLeg("us-equity", 1.072), NotionalLeg("trend", 1.5))
            if name == "RSST"
            else value
        )
        for name, value in _legs().items()
    }
    assert implied_notional(CANDIDATE_CAPITAL, legs=legs)["trend"] == pytest.approx(0.45)


def _legs() -> dict[str, tuple[NotionalLeg, ...]]:
    from portfolio_edge.studies.rebalancing_operations import CANDIDATE_LEGS

    return dict(CANDIDATE_LEGS)


# --------------------------------------------------------------------------------
# Feasibility
# --------------------------------------------------------------------------------


def test_headroom_is_zero_when_taxable_holds_a_fund_at_exactly_its_target() -> None:
    target = {"A": 0.5, "B": 0.3, "C": 0.2}
    room = headroom(target, {"B": 0.3})
    assert room.minimum == pytest.approx(0.0)
    assert room.binding_fund == "B"
    assert room.feasible


def test_the_target_is_reachable_exactly_when_headroom_is_non_negative() -> None:
    target = {"A": 0.5, "B": 0.3, "C": 0.2}
    feasible = {"B": 0.3, "C": 0.2}
    assert headroom(target, feasible).feasible
    assert nearest_reachable(target, feasible) == pytest.approx(target)

    infeasible = {"B": 0.45, "C": 0.2}
    assert not headroom(target, infeasible).feasible
    reached = nearest_reachable(target, infeasible)
    assert reached["B"] == pytest.approx(0.45)
    assert sum(reached.values()) == pytest.approx(1.0)
    assert reached["A"] < target["A"]


def test_nearest_reachable_is_the_euclidean_projection() -> None:
    """Checked against a brute-force search over the reachable set."""
    target = {"A": 0.5, "B": 0.3, "C": 0.2}
    taxable = {"A": 0.0, "B": 0.5, "C": 0.1}
    reached = nearest_reachable(target, taxable)
    best = sum((reached[name] - target[name]) ** 2 for name in target)
    sheltered = 1.0 - sum(taxable.values())
    rng = np.random.default_rng(20260822)
    for _ in range(4000):
        draw = rng.dirichlet(np.ones(3)) * sheltered
        candidate = {
            name: taxable.get(name, 0.0) + draw[i] for i, name in enumerate(sorted(target))
        }
        assert best <= sum((candidate[n] - target[n]) ** 2 for n in target) + 1e-12


def test_barring_a_line_from_taxable_lowers_the_headroom_ceiling() -> None:
    """The two constraints fight: the wrapper is the largest line, so barring it removes
    the most taxable capacity and roughly halves the ceiling."""
    free = max_achievable_headroom(dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE)
    barred = max_achievable_headroom(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, barred=["RSST"]
    )
    assert free == pytest.approx(0.1056, abs=5e-4)
    assert barred == pytest.approx(0.0542, abs=5e-4)


def test_a_bar_that_empties_the_taxable_account_is_refused() -> None:
    with pytest.raises(ValueError, match="cannot fill it"):
        max_achievable_headroom(
            {"A": 0.5, "B": 0.5}, taxable_share=0.6, barred=["A", "B"]
        )


def test_maximum_headroom_falls_as_the_portfolio_is_cut_into_more_lines() -> None:
    eight = max_achievable_headroom(dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE)
    three = max_achievable_headroom(
        {"RSST": 0.30, "VTI": 0.35, "VXUS": 0.35}, taxable_share=TAXABLE_SHARE
    )
    assert eight == pytest.approx(0.1056, abs=5e-4)
    assert three == pytest.approx(0.2222, abs=5e-4)
    assert three > eight


def test_maximum_headroom_solves_its_own_defining_equation() -> None:
    target = dict(CANDIDATE_CAPITAL)
    bound = max_achievable_headroom(target, taxable_share=TAXABLE_SHARE)
    capacity = sum(max(want - bound, 0.0) for want in target.values())
    assert capacity == pytest.approx(TAXABLE_SHARE, abs=1e-9)


def test_relative_drift_to_infeasibility_matches_a_direct_calculation() -> None:
    ratio = relative_drift_to_infeasibility(
        taxable_share=TAXABLE_SHARE, sheltered_share=1.0 - TAXABLE_SHARE, limit=0.35
    )
    share = TAXABLE_SHARE * ratio / (TAXABLE_SHARE * ratio + (1.0 - TAXABLE_SHARE))
    assert share == pytest.approx(0.35)
    assert ratio == pytest.approx(1.0769, abs=1e-4)


def test_a_wider_band_buys_drift_budget_monotonically() -> None:
    budgets = [
        relative_drift_to_infeasibility(
            taxable_share=TAXABLE_SHARE, sheltered_share=1.0 - TAXABLE_SHARE, limit=limit
        )
        for limit in (0.35, 0.375, 0.40, 0.4375)
    ]
    assert budgets == sorted(budgets)
    assert budgets[-1] == pytest.approx(1.5556, abs=1e-4)


# --------------------------------------------------------------------------------
# The price of a forced trade, and of headroom
# --------------------------------------------------------------------------------


def test_the_tax_on_a_forced_sale_dwarfs_the_spread() -> None:
    trade = forced_realisation_cost(
        traded=1.0,
        gain_fraction=gain_fraction_after(years=10, growth_rate=0.07),
        tax_rate=0.238,
        spread_bp=2.0,
    )
    assert trade.gain_realised == pytest.approx(0.4917, abs=1e-4)
    assert trade.tax == pytest.approx(0.11701, abs=1e-5)
    assert trade.friction == pytest.approx(2e-4)
    assert trade.tax_to_friction > 500.0


def test_gain_fraction_is_the_stated_closed_form() -> None:
    assert gain_fraction_after(years=0.0, growth_rate=0.07) == 0.0
    assert gain_fraction_after(years=10.0, growth_rate=0.07) == pytest.approx(
        1.0 - 1.07**-10
    )


def test_forced_realisation_rejects_a_gain_stated_over_basis() -> None:
    with pytest.raises(ValueError, match="share of value"):
        forced_realisation_cost(
            traded=1.0, gain_fraction=1.4, tax_rate=0.238, spread_bp=2.0
        )


#: Every ``priorityBp`` published in ``src/content/placement.ts`` for this portfolio,
#: at 23.8% / 18.8% / 15% qualified. Reproducing all 24 from the filed yields and
#: qualified fractions is what licenses this module to reuse that page's ranking.
PUBLISHED_PRIORITY_BP = {
    "RSST": (361.78, 315.42, 213.79),
    "IDMO": (148.22, 126.20, 83.25),
    "AVES": (83.98, 64.43, 32.21),
    "IEMG": (64.27, 51.55, 28.60),
    "DFIV": (63.73, 43.56, 28.23),
    "VEA": (56.01, 44.07, 28.56),
    "AVLV": (42.13, 33.28, 26.55),
    "VTI": (25.39, 20.06, 16.00),
}


def test_placement_costs_reproduce_every_published_priority() -> None:
    for column, (rate, _) in enumerate(BRACKETS):
        costs = placement_costs_at(rate)
        for name, published in PUBLISHED_PRIORITY_BP.items():
            assert costs[name].priority_bp == pytest.approx(
                published[column], abs=0.01
            ), f"{name} at {rate}"


def test_the_wrappers_two_readings_differ_by_an_order_of_magnitude() -> None:
    """Both are the same filing; which one is right decides nothing here, because the
    wrapper is sheltered under every placement this module recommends."""
    recognised = placement_costs_at(0.238)["RSST"]
    distributed = placement_costs_at(0.238, wrapper_reading="distributed")["RSST"]
    assert recognised.priority_bp == pytest.approx(361.78, abs=0.01)
    assert distributed.priority_bp == pytest.approx(33.72, abs=0.01)
    assert recognised.sheltered_bp == distributed.sheltered_bp == 0.0


def test_a_qualified_rate_implies_its_ordinary_rate() -> None:
    assert ordinary_rate_for(0.238) == pytest.approx(0.408)
    assert ordinary_rate_for(0.15) == pytest.approx(0.24)
    with pytest.raises(KeyError, match="no ordinary rate"):
        ordinary_rate_for(0.20)


def test_the_fill_order_puts_us_equity_in_taxable_at_every_bracket() -> None:
    """The 2026-08-22 correction: partly-qualified international dividends are dearer in
    a taxable account than fully-qualified US ones, so VTI goes first and the wrapper
    last, at all three brackets."""
    for rate, _ in BRACKETS:
        costs = placement_costs_at(rate)
        order = sorted(costs, key=lambda name: costs[name].priority_bp)
        assert order[0] == "VTI"
        assert order[1] == "AVLV"
        assert order[-1] == "RSST"
        assert order[-2] == "IDMO"


def test_assuming_full_qualification_reverses_the_ranking() -> None:
    """Why the old table was wrong.

    At an assumed qualified fraction of 1.00, IEMG's taxable cost falls below AVLV's and
    an emerging-market fund sorts *ahead* of US large value into the taxable account. The
    filed 34.82% puts it 22 bp behind instead. One input, and the second and third lines
    of the fill order swap.
    """
    honest = placement_costs_at(0.238)
    naive = {
        name: FundTaxProfile(
            profile.box_1a_yield, 1.0, profile.creditable_foreign_tax_yield
        )
        for name, profile in FUND_TAX_PROFILE.items()
    }
    wrong = placement_costs_at(0.238, profiles=naive)
    assert honest["IEMG"].priority_bp > honest["AVLV"].priority_bp
    assert wrong["IEMG"].priority_bp < wrong["AVLV"].priority_bp
    assert sorted(wrong, key=lambda n: wrong[n].priority_bp)[:3] == [
        "VTI", "IEMG", "AVLV"
    ]
    assert sorted(honest, key=lambda n: honest[n].priority_bp)[:3] == [
        "VTI", "AVLV", "VEA"
    ]


def test_the_zero_headroom_optimum_is_the_published_placement_plan() -> None:
    """The two analyses are the same knapsack at two constraint levels.

    ``src/content/placement.ts`` puts VTI entire and the balance of AVLV in the taxable
    account. That is exactly what minimising drag with no feasibility constraint returns,
    which is why the disagreement between the two pages is a constraint level and not a
    method.
    """
    plan = min_drag_placement(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, min_headroom=0.0,
        taxable_capacity={"RSST": 0.0},
    )
    taxable = {name: by[Account.TAXABLE] for name, by in plan.items()}
    assert taxable["VTI"] == pytest.approx(0.20)
    assert taxable["AVLV"] == pytest.approx(TAXABLE_SHARE - 0.20)
    assert all(taxable[name] == pytest.approx(0.0) for name in ("RSST", "DFIV", "VEA"))
    assert headroom(dict(CANDIDATE_CAPITAL), taxable).binding_fund == "VTI"
    assert headroom(dict(CANDIDATE_CAPITAL), taxable).minimum == pytest.approx(0.0)


def test_two_taxable_lines_cannot_reach_one_point_of_headroom() -> None:
    """The obvious fix — move a point of VTI into shelter — does not work.

    VTI and AVLV target 35 pp between them and must hold 33.33, so the two lines share
    1.67 pp of slack and the best achievable minimum is 0.83. Reaching a full point on
    every line needs a *third* fund in the taxable account.
    """
    best = max(
        min(0.20 - vti, 0.15 - (TAXABLE_SHARE - vti))
        for vti in [0.18 + i / 10000.0 for i in range(400)]
    )
    assert best == pytest.approx(0.00833, abs=1e-4)
    reached = min_drag_placement(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, min_headroom=0.01,
        taxable_capacity={"RSST": 0.0},
    )
    held = [n for n, by in reached.items() if by[Account.TAXABLE] > 1e-9]
    assert len(held) == 3


def test_headroom_is_cheap_and_the_cheapest_placement_has_none() -> None:
    target = dict(CANDIDATE_CAPITAL)
    free = min_drag_placement(target, taxable_share=TAXABLE_SHARE, min_headroom=0.0)
    paid = min_drag_placement(target, taxable_share=TAXABLE_SHARE, min_headroom=0.05)
    assert headroom(
        placement_totals(free),
        {name: by[Account.TAXABLE] for name, by in free.items()},
    ).minimum == pytest.approx(0.0, abs=1e-9)
    assert headroom(
        placement_totals(paid),
        {name: by[Account.TAXABLE] for name, by in paid.items()},
    ).minimum == pytest.approx(0.05, abs=1e-9)
    premium = placement_drag_bp(paid) - placement_drag_bp(free)
    assert 0.0 < premium < 5.0


def test_min_drag_placement_is_a_valid_placement_of_exactly_one_dollar() -> None:
    placement = min_drag_placement(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, min_headroom=0.05
    )
    check_placement(placement)
    assert account_totals(placement)[Account.TAXABLE] == pytest.approx(TAXABLE_SHARE)
    assert placement_totals(placement) == pytest.approx(dict(CANDIDATE_CAPITAL))


def test_min_drag_placement_honours_a_bar_on_a_fund_in_taxable() -> None:
    placement = min_drag_placement(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, min_headroom=0.05,
        taxable_capacity={"RSST": 0.0},
    )
    check_placement(placement)
    assert placement["RSST"][Account.TAXABLE] == pytest.approx(0.0)


def test_min_drag_placement_refuses_an_unreachable_headroom() -> None:
    with pytest.raises(ValueError, match="ceiling"):
        min_drag_placement(
            dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, min_headroom=0.20
        )


def test_after_tax_shares_make_the_taxable_account_larger_not_smaller() -> None:
    shares = after_tax_account_shares(
        balances={account: 1.0 / 3.0 for account in Account},
        ordinary_rate=0.24,
        capital_gains_rate=0.238,
        taxable_gain_fraction=gain_fraction_after(years=10, growth_rate=0.07),
    )
    assert sum(shares.values()) == pytest.approx(1.0)
    assert shares[Account.TAXABLE] > 1.0 / 3.0
    assert shares[Account.TRADITIONAL] < shares[Account.ROTH]


# --------------------------------------------------------------------------------
# The executable rule
# --------------------------------------------------------------------------------


def _flat_returns(months: int = 60) -> dict[str, list[float]]:
    return {name: [0.0] * months for name in CANDIDATE_CAPITAL}


def _placement(min_headroom: float = 0.03) -> Placement:
    return min_drag_placement(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE, min_headroom=min_headroom,
        taxable_capacity={"RSST": 0.0},
    )


def _regime(spread_bp: float = 2.0) -> TaxRegime:
    return TaxRegime(long_term_rate=0.238, spread_bp=spread_bp)


def test_a_portfolio_that_never_moves_is_never_traded_and_never_taxed() -> None:
    result = simulate_operations(
        returns=_flat_returns(),
        placement=_placement(),
        rule=RebalanceRule("quarterly", review_months=3),
        regime=_regime(),
    )
    assert result.trades == 0
    assert result.friction_cost_per_year == 0.0
    assert result.tax_paid_per_year == 0.0
    assert result.mean_absolute_deviation == pytest.approx(0.0, abs=1e-12)
    assert result.terminal_wealth == pytest.approx(1.0)


def test_an_embedded_gain_raises_the_cost_of_every_forced_sale() -> None:
    months = 120
    returns = {name: [0.0] * months for name in CANDIDATE_CAPITAL}
    returns["VTI"] = [0.02] * months
    paid = [
        simulate_operations(
            returns=returns, placement=_placement(0.0),
            rule=RebalanceRule("annual", review_months=12, allow_taxable_sales=True),
            regime=_regime(), initial_gain_fraction=fraction,
        ).tax_paid_per_year
        for fraction in (0.0, 0.4, 0.7)
    ]
    assert paid == sorted(paid)
    assert paid[0] > 0.0


def test_an_embedded_gain_must_be_a_share_of_value() -> None:
    with pytest.raises(ValueError, match="initial_gain_fraction"):
        simulate_operations(
            returns=_flat_returns(), placement=_placement(),
            rule=RebalanceRule("annual", review_months=12), regime=_regime(),
            initial_gain_fraction=1.0,
        )


def test_the_sheltered_only_rule_never_realises_a_gain() -> None:
    """The whole point of the rule. Any tax at all would be a defect, not a cost."""
    rng = np.random.default_rng(20260822)
    returns = {
        name: list(rng.normal(0.006, 0.05, size=360)) for name in CANDIDATE_CAPITAL
    }
    for rule in (
        RebalanceRule("annual", review_months=12),
        RebalanceRule("quarterly", review_months=3),
        RebalanceRule("band", review_months=1, relative_band=0.25),
    ):
        result = simulate_operations(
            returns=returns, placement=_placement(), rule=rule, regime=_regime(),
            contribution_per_year=0.05, contribution_to_taxable=TAXABLE_SHARE,
        )
        assert result.tax_paid_per_year == 0.0
        assert result.gain_realised_per_year == 0.0


def test_allowing_taxable_sales_buys_feasibility_and_pays_for_it() -> None:
    """One fund runs away inside the taxable account; only a sale can restore target."""
    months = 120
    returns = {name: [0.0] * months for name in CANDIDATE_CAPITAL}
    returns["VTI"] = [0.02] * months
    sheltered_only = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("annual", review_months=12), regime=_regime(),
    )
    with_sales = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("annual", review_months=12, allow_taxable_sales=True),
        regime=_regime(),
    )
    assert sheltered_only.months_infeasible > 0
    assert sheltered_only.tax_paid_per_year == 0.0
    assert with_sales.tax_paid_per_year > 0.0
    assert with_sales.mean_absolute_deviation < sheltered_only.mean_absolute_deviation


def test_costs_scale_with_the_spread_and_are_charged_on_traded_notional() -> None:
    rng = np.random.default_rng(4)
    returns = {
        name: list(rng.normal(0.005, 0.04, size=240)) for name in CANDIDATE_CAPITAL
    }
    cheap = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("quarterly", review_months=3), regime=_regime(2.0),
    )
    dear = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("quarterly", review_months=3), regime=_regime(8.0),
    )
    assert dear.friction_cost_per_year == pytest.approx(
        4.0 * cheap.friction_cost_per_year, rel=1e-3
    )
    assert cheap.friction_cost_per_year == pytest.approx(
        2.0 * cheap.turnover_per_year * 2.0 / 1e4, rel=5e-3
    )


def test_more_frequent_review_controls_exposure_better_and_costs_more() -> None:
    rng = np.random.default_rng(11)
    returns = {
        name: list(rng.normal(0.005, 0.045, size=360)) for name in CANDIDATE_CAPITAL
    }
    annual = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("annual", review_months=12), regime=_regime(),
    )
    quarterly = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("quarterly", review_months=3), regime=_regime(),
    )
    assert quarterly.mean_absolute_deviation < annual.mean_absolute_deviation
    assert quarterly.friction_cost_per_year > annual.friction_cost_per_year
    assert quarterly.decisions_per_year == pytest.approx(4.0, abs=0.05)
    assert annual.decisions_per_year == pytest.approx(1.0, abs=0.05)


def test_directing_taxable_money_by_headroom_preserves_more_of_it() -> None:
    rng = np.random.default_rng(7)
    returns = {
        name: list(rng.normal(0.005, 0.04, size=360)) for name in CANDIDATE_CAPITAL
    }
    def run(*, by_headroom: bool) -> object:
        return simulate_operations(
            returns=returns, placement=_placement(),
            rule=RebalanceRule("annual", review_months=12), regime=_regime(),
            contribution_per_year=0.10, contribution_to_taxable=TAXABLE_SHARE,
            taxable_contributions_by_headroom=by_headroom,
        )

    by_room = run(by_headroom=True)
    by_deficit = run(by_headroom=False)
    assert by_room.worst_headroom > by_deficit.worst_headroom  # type: ignore[attr-defined]


def test_a_rule_with_an_infinite_band_never_fires() -> None:
    rule = RebalanceRule("hold", review_months=1, absolute_band=math.inf)
    assert not rule.triggered({"A": 0.9, "B": 0.1}, {"A": 0.5, "B": 0.5})


def test_a_calendar_rule_with_no_band_always_fires() -> None:
    rule = RebalanceRule("annual", review_months=12)
    assert rule.triggered({"A": 0.5}, {"A": 0.5})


def test_a_relative_band_fires_on_a_small_line_an_absolute_band_ignores() -> None:
    relative = RebalanceRule("relative", review_months=1, relative_band=0.25)
    absolute = RebalanceRule("absolute", review_months=1, absolute_band=0.05)
    drifted = {"BIG": 0.93, "SMALL": 0.07}
    target = {"BIG": 0.95, "SMALL": 0.05}
    assert relative.triggered(drifted, target)
    assert not absolute.triggered(drifted, target)


def test_the_rule_rejects_impossible_settings() -> None:
    with pytest.raises(ValueError, match="review_months"):
        RebalanceRule("bad", review_months=0)
    with pytest.raises(ValueError, match="bands must be positive"):
        RebalanceRule("bad", review_months=1, relative_band=0.0)


def test_simulate_refuses_a_placement_that_is_not_one_dollar() -> None:
    broken = {"VTI": {Account.TAXABLE: 0.4}}
    with pytest.raises(ValueError, match="allocates"):
        simulate_operations(
            returns={"VTI": [0.0] * 24}, placement=broken,
            rule=RebalanceRule("annual", review_months=12), regime=_regime(),
        )


def test_simulate_refuses_a_fund_with_no_return_series() -> None:
    with pytest.raises(KeyError, match="RSST"):
        simulate_operations(
            returns={name: [0.0] * 24 for name in CANDIDATE_CAPITAL if name != "RSST"},
            placement=_placement(),
            rule=RebalanceRule("annual", review_months=12), regime=_regime(),
        )


def test_growth_is_time_weighted_and_ignores_the_contribution_schedule() -> None:
    """A portfolio earning 1% a month grows at 12 log-percent whatever is paid in.

    Exactly so with no cash flow. With one, the only wedge is the spread the rebalance
    pays on the trades the contribution itself creates, which is bounded by a basis
    point a year at these rates and is a cost rather than a money-weighting artefact.
    """
    months = 120
    returns = {name: [0.01] * months for name in CANDIDATE_CAPITAL}
    expected = 12.0 * math.log(1.01)
    quiet = simulate_operations(
        returns=returns, placement=_placement(),
        rule=RebalanceRule("annual", review_months=12), regime=_regime(),
    )
    assert quiet.growth_per_year == pytest.approx(expected, rel=1e-12)
    for contribution in (0.05, 0.20):
        result = simulate_operations(
            returns=returns, placement=_placement(),
            rule=RebalanceRule("annual", review_months=12), regime=_regime(),
            contribution_per_year=contribution, contribution_to_taxable=TAXABLE_SHARE,
        )
        shortfall = expected - result.growth_per_year
        assert 0.0 <= shortfall < 1e-4
        assert shortfall == pytest.approx(result.friction_cost_per_year, abs=2e-6)


# --------------------------------------------------------------------------------
# Complexity and holdability
# --------------------------------------------------------------------------------


def test_tracking_error_of_a_series_against_itself_is_zero() -> None:
    rng = np.random.default_rng(3)
    series = rng.normal(0.005, 0.04, size=200)
    assert tracking_error(series, series) == 0.0


def test_merging_two_lines_of_the_same_fund_is_free() -> None:
    """Four lines bought as three tickers is the same portfolio, so its cost is zero."""
    rng = np.random.default_rng(5)
    returns = {
        name: list(rng.normal(0.005, 0.04, size=200)) for name in CANDIDATE_CAPITAL
    }
    split = portfolio_returns(returns, {"VTI": 0.35, "VEA": 0.25, "IEMG": 0.10,
                                        "RSST": 0.30})
    merged = portfolio_returns(returns, {"VTI": 0.35, "VEA": 0.25, "IEMG": 0.10,
                                         "RSST": 0.30})
    assert tracking_error(split, merged) == 0.0


def test_worst_relative_stretch_finds_a_planted_run_of_underperformance() -> None:
    periods = [f"2000-{month:02d}" for month in range(1, 13)]
    benchmark = [0.0] * 12
    candidate = [0.0, 0.0, -0.10, -0.10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    stretch = worst_relative_stretch(candidate, benchmark, periods)
    assert stretch.depth == pytest.approx(0.9 * 0.9 - 1.0)
    assert stretch.start == "2000-02"
    assert stretch.trough == "2000-04"
    assert stretch.recovered is None


def test_worst_relative_stretch_reports_recovery_when_it_happens() -> None:
    periods = [f"2000-{month:02d}" for month in range(1, 7)]
    stretch = worst_relative_stretch(
        [0.0, -0.20, 0.0, 0.30, 0.0, 0.0], [0.0] * 6, periods
    )
    assert stretch.recovered == "2000-04"
    assert stretch.months == 3


def test_minimum_detectable_effect_shrinks_with_the_square_root_of_the_sample() -> None:
    rng = np.random.default_rng(9)
    short = minimum_detectable_effect(rng.normal(0.0, 0.02, size=100))
    long = minimum_detectable_effect(rng.normal(0.0, 0.02, size=400))
    assert long == pytest.approx(short / 2.0, rel=0.25)
