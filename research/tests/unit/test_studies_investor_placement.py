"""Tests for :mod:`portfolio_edge.studies.investor_placement`.

Every figure in the investor-specific section of
``docs/research/structural-and-tax-edges.md`` is pinned here. The module has no data
dependency and no randomness, so a failure is a changed input or a bug, never noise.

Three kinds of test, kept apart:

* **Closed forms derived here from scratch**, so the implementation is checked against
  algebra rather than against itself.
* **Invariants** — the guards that stop the two accounts being told apart on a drag
  that is identical in both, and the ordering properties the plan depends on.
* **Pinned figures**, with the arithmetic that produces them written out in the test.
"""

from __future__ import annotations

import math

import pytest

from portfolio_edge.studies.investor_placement import (
    AVES,
    AVLV,
    DFIV,
    EQUITY_HOLDINGS,
    IDMO,
    IEMG,
    INDEX_MENU,
    PLAUSIBLE_RANGE,
    THIRDS,
    TOP_BRACKET,
    UPPER_MIDDLE,
    UPPER_WITH_SURTAX,
    VEA,
    VTI,
    WRAPPER_DISTRIBUTED,
    WRAPPER_RECOGNISED,
    Accounts,
    Holding,
    conditional_wrapper_upside_bp,
    contributions_cover_the_constrained_direction,
    feasible_naive_saving_bp,
    forfeited_credit_bp,
    location_edge,
    location_edge_versus_feasible_bp,
    menu_binding_fraction,
    menu_constrained_plan,
    plan,
    plan_value_bp,
    portfolio,
    pro_rata_saving_bp,
    rank,
    roth_versus_traditional_bp,
    saving_bp,
    worst_saving_bp,
    wrapper_regret_bp,
)
from portfolio_edge.studies.outperformance_horizon import (
    Benchmark,
    Certainty,
    EdgeComponent,
    aggregate,
)

CAPACITY = THIRDS.shelter_capacity


def test_weights_sum_to_the_whole_portfolio() -> None:
    for wrapper in (WRAPPER_RECOGNISED, WRAPPER_DISTRIBUTED):
        total = sum(h.weight for h in portfolio(wrapper=wrapper))
        assert total == pytest.approx(1.0, abs=1e-12)


def test_every_holding_carries_a_source_and_a_date() -> None:
    for holding in portfolio(wrapper=WRAPPER_RECOGNISED):
        assert holding.source.strip()
        assert holding.as_of.strip()


def test_a_holding_without_a_source_is_refused() -> None:
    with pytest.raises(ValueError, match="not evidence"):
        Holding(
            ticker="X",
            name="unsourced",
            weight=0.1,
            expense_ratio=0.0,
            ordinary_yield=0.0,
            capital_gain_rate_yield=0.02,
            creditable_foreign_tax_yield=0.0,
            source="  ",
            as_of="2026-08-22",
        )


def test_accounts_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        Accounts(roth=0.5, traditional=0.5, taxable=0.5)


# --------------------------------------------------------------------------------------
# Closed forms
# --------------------------------------------------------------------------------------


def test_priority_is_the_us_tax_less_the_credit_computed_independently() -> None:
    """``priority = ordinary*O + qualified*Q - credit`` whenever the credit is usable."""
    for regime in PLAUSIBLE_RANGE:
        for holding in EQUITY_HOLDINGS:
            expected = (
                regime.ordinary * holding.ordinary_yield
                + regime.capital_gain * holding.capital_gain_rate_yield
                - holding.creditable_foreign_tax_yield
            ) / 1e-4
            assert holding.priority_bp(regime) == pytest.approx(expected, rel=1e-12)


def test_a_fully_qualified_domestic_fund_collapses_to_rate_times_yield() -> None:
    for regime in PLAUSIBLE_RANGE:
        assert VTI.priority_bp(regime) == pytest.approx(
            regime.capital_gain * VTI.capital_gain_rate_yield / 1e-4, rel=1e-12
        )
        assert AVLV.priority_bp(regime) == pytest.approx(
            regime.capital_gain * AVLV.capital_gain_rate_yield / 1e-4, rel=1e-12
        )


def test_the_credit_is_capped_at_the_us_tax_because_it_is_not_refundable() -> None:
    """In a 0% regime a foreign holding's taxable cost is the withholding itself."""
    zero = TOP_BRACKET.__class__(
        label="US zero long-term-rate bracket",
        jurisdiction="US federal",
        as_of="2026-08-22",
        ordinary_income=0.0,
        long_term_capital_gain=0.0,
        net_investment_income=0.0,
    )
    assert AVES.taxable_cost_bp(zero) == pytest.approx(AVES.sheltered_cost_bp(zero))
    assert AVES.priority_bp(zero) == pytest.approx(0.0, abs=1e-12)


def test_the_sheltered_cost_does_not_depend_on_the_bracket() -> None:
    """The whole reason a Roth and a traditional account cannot be ranked on the drag."""
    for holding in portfolio(wrapper=WRAPPER_RECOGNISED):
        costs = {holding.sheltered_cost_bp(regime) for regime in PLAUSIBLE_RANGE}
        assert len(costs) == 1


def test_box_1a_yield_is_the_two_character_buckets() -> None:
    assert VEA.box_1a_yield == pytest.approx(0.02387, abs=1e-9)
    assert DFIV.box_1a_yield == pytest.approx(0.04033, abs=1e-9)


def test_vea_reconciles_the_two_withholding_denominators() -> None:
    """6.068% of Box 1a over 79.6488% foreign source income is VEA's filed 7.61%.

    This is the arithmetic that closes ``tax_structure`` §1's largest open input. The
    worksheet ratio and the N-CSR ratio are the same fact in two denominators.
    """
    box_1a_rate = VEA.creditable_foreign_tax_yield / VEA.box_1a_yield
    assert box_1a_rate == pytest.approx(0.06068, rel=2e-4)
    foreign_source_rate = box_1a_rate / 0.796488
    assert foreign_source_rate == pytest.approx(0.0761, abs=1e-4)


def test_filed_qualified_fractions_are_what_the_module_carries() -> None:
    """The single correction that reverses ``tax_structure`` §1's emerging finding."""
    for holding, expected in (
        (VEA, 0.662741),
        (IEMG, 0.3482),
        (AVES, 0.4448),
        (IDMO, 0.25),
    ):
        share = holding.capital_gain_rate_yield / holding.box_1a_yield
        if holding is IDMO:
            # IDMO's capital-gain bucket also carries the 2025-12-22 long-term
            # distribution, so the dividend-only fraction is recovered net of it.
            share = (holding.capital_gain_rate_yield - 0.0056) / (
                holding.box_1a_yield - 0.0056 - 0.0158
            )
        assert share == pytest.approx(expected, rel=5e-3)


# --------------------------------------------------------------------------------------
# Invariants
# --------------------------------------------------------------------------------------


def test_the_plan_places_the_whole_portfolio() -> None:
    for regime in PLAUSIBLE_RANGE:
        for wrapper in (WRAPPER_RECOGNISED, WRAPPER_DISTRIBUTED):
            placements = plan(portfolio(wrapper=wrapper), regime=regime, capacity=CAPACITY)
            assert sum(p.sheltered_weight for p in placements) == pytest.approx(CAPACITY)
            assert sum(p.weight for p in placements) == pytest.approx(1.0)
            assert all(p.taxable_weight >= -1e-12 for p in placements)


def test_the_optimal_plan_beats_pro_rata_which_beats_the_reverse() -> None:
    for regime in PLAUSIBLE_RANGE:
        for wrapper in (WRAPPER_RECOGNISED, WRAPPER_DISTRIBUTED):
            holdings = portfolio(wrapper=wrapper)
            best = saving_bp(plan(holdings, regime=regime, capacity=CAPACITY))
            middle = pro_rata_saving_bp(holdings, regime=regime, capacity=CAPACITY)
            worst = worst_saving_bp(holdings, regime=regime, capacity=CAPACITY)
            assert best > middle > worst


def test_placement_is_worth_nothing_when_the_shelter_covers_everything() -> None:
    holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
    best = saving_bp(plan(holdings, regime=TOP_BRACKET, capacity=1.0))
    middle = pro_rata_saving_bp(holdings, regime=TOP_BRACKET, capacity=1.0)
    assert best == pytest.approx(middle, rel=1e-12)


def test_vti_is_last_in_the_queue_at_every_plausible_rate() -> None:
    """The cheapest, lowest-yielding fund is the one that belongs in taxable."""
    for regime in PLAUSIBLE_RANGE:
        ordering = rank(EQUITY_HOLDINGS, regime=regime)
        assert ordering[-1][0] == "VTI"


def test_both_emerging_funds_outrank_us_equity_at_every_plausible_rate() -> None:
    """``tax_structure`` §1 concluded the opposite, on an assumed 100% qualified share."""
    for regime in PLAUSIBLE_RANGE:
        assert AVES.priority_bp(regime) > VTI.priority_bp(regime)
        assert IEMG.priority_bp(regime) > VTI.priority_bp(regime)
        assert AVES.priority_bp(regime) > AVLV.priority_bp(regime)
        assert IEMG.priority_bp(regime) > AVLV.priority_bp(regime)


def test_the_emerging_inversion_returns_if_the_funds_were_fully_qualified() -> None:
    """The filed fraction is load-bearing, so the counterfactual is pinned too."""
    as_if_fully_qualified = Holding(
        ticker="AVES-100",
        name="AVES as if 100% qualified",
        weight=AVES.weight,
        expense_ratio=AVES.expense_ratio,
        ordinary_yield=0.0,
        capital_gain_rate_yield=AVES.box_1a_yield,
        creditable_foreign_tax_yield=AVES.creditable_foreign_tax_yield,
        source="counterfactual, not a filing",
        as_of="2026-08-22",
    )
    assert as_if_fully_qualified.priority_bp(UPPER_MIDDLE) < VTI.priority_bp(UPPER_MIDDLE)
    assert AVES.priority_bp(UPPER_MIDDLE) > VTI.priority_bp(UPPER_MIDDLE)


def test_the_taxable_account_holds_only_us_equity_across_the_whole_range() -> None:
    """The plan does not move on the bracket, which is the decision-relevant finding."""
    for regime in PLAUSIBLE_RANGE:
        placements = plan(
            portfolio(wrapper=WRAPPER_RECOGNISED), regime=regime, capacity=CAPACITY
        )
        in_taxable = {p.ticker for p in placements if p.taxable_weight > 1e-9}
        assert in_taxable == {"VTI", "AVLV"}


# --------------------------------------------------------------------------------------
# Pinned figures
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ticker", "expected"),
    [
        ("RSST", 361.78),
        ("IDMO", 148.22),
        ("AVES", 83.98),
        ("IEMG", 64.27),
        ("DFIV", 63.73),
        ("VEA", 56.01),
        ("AVLV", 42.13),
        ("VTI", 25.39),
    ],
)
def test_top_bracket_priorities(ticker: str, expected: float) -> None:
    ordering = dict(rank(portfolio(wrapper=WRAPPER_RECOGNISED), regime=TOP_BRACKET))
    assert ordering[ticker] == pytest.approx(expected, abs=0.01)


def test_the_wrapper_on_the_distributed_basis() -> None:
    assert WRAPPER_DISTRIBUTED.priority_bp(TOP_BRACKET) == pytest.approx(33.72, abs=0.01)
    assert WRAPPER_DISTRIBUTED.box_1a_yield == pytest.approx(0.01285, abs=1e-6)


def test_the_wrapper_queue_is_the_whole_difference_between_the_two_readings() -> None:
    ratio = WRAPPER_RECOGNISED.priority_bp(TOP_BRACKET) / WRAPPER_DISTRIBUTED.priority_bp(
        TOP_BRACKET
    )
    assert ratio == pytest.approx(10.73, abs=0.05)


@pytest.mark.parametrize(
    ("regime", "optimal", "pro_rata", "worst"),
    [
        (TOP_BRACKET, 136.03, 97.82, 33.25),
        (UPPER_WITH_SURTAX, 116.05, 83.00, 25.67),
        (UPPER_MIDDLE, 77.46, 56.13, 17.29),
    ],
)
def test_plan_value_on_the_recognised_basis(
    regime: object, optimal: float, pro_rata: float, worst: float
) -> None:
    holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
    assert saving_bp(plan(holdings, regime=regime, capacity=CAPACITY)) == pytest.approx(  # type: ignore[arg-type]
        optimal, abs=0.01
    )
    assert pro_rata_saving_bp(holdings, regime=regime, capacity=CAPACITY) == pytest.approx(  # type: ignore[arg-type]
        pro_rata, abs=0.01
    )
    assert worst_saving_bp(holdings, regime=regime, capacity=CAPACITY) == pytest.approx(  # type: ignore[arg-type]
        worst, abs=0.01
    )


@pytest.mark.parametrize(
    ("regime", "optimal", "pro_rata"),
    [
        (TOP_BRACKET, 38.73, 32.21),
        (UPPER_WITH_SURTAX, 30.41, 25.38),
        (UPPER_MIDDLE, 20.35, 17.56),
    ],
)
def test_plan_value_on_the_distributed_basis(
    regime: object, optimal: float, pro_rata: float
) -> None:
    holdings = portfolio(wrapper=WRAPPER_DISTRIBUTED)
    assert saving_bp(plan(holdings, regime=regime, capacity=CAPACITY)) == pytest.approx(  # type: ignore[arg-type]
        optimal, abs=0.01
    )
    assert pro_rata_saving_bp(holdings, regime=regime, capacity=CAPACITY) == pytest.approx(  # type: ignore[arg-type]
        pro_rata, abs=0.01
    )


def test_the_credit_forfeited_by_sheltering_the_international_sleeve() -> None:
    """8.81 bp/yr, permanent, identical in a Roth and a traditional account."""
    for regime in PLAUSIBLE_RANGE:
        holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
        placements = plan(holdings, regime=regime, capacity=CAPACITY)
        assert forfeited_credit_bp(placements, holdings) == pytest.approx(8.81, abs=0.01)


def test_the_whole_international_sleeve_is_sheltered() -> None:
    for regime in PLAUSIBLE_RANGE:
        placements = {
            p.ticker: p
            for p in plan(
                portfolio(wrapper=WRAPPER_RECOGNISED), regime=regime, capacity=CAPACITY
            )
        }
        for ticker in ("DFIV", "VEA", "IDMO", "IEMG", "AVES"):
            assert placements[ticker].taxable_weight == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------------------------------
# Roth versus traditional
# --------------------------------------------------------------------------------------


def test_roth_versus_traditional_is_worth_nothing_without_a_growth_gap() -> None:
    value = roth_versus_traditional_bp(
        accounts=THIRDS,
        withdrawal_rate=0.24,
        swapped_weight=0.30,
        high_growth=0.07,
        low_growth=0.07,
        years=30,
    )
    assert value == pytest.approx(0.0, abs=1e-12)


def test_roth_versus_traditional_is_worth_nothing_when_the_accounts_match_after_tax() -> None:
    """``R = T(1-t)`` is the algebraic zero, and it is the whole content of the rule."""
    withdrawal = 0.25
    accounts = Accounts(roth=0.3, traditional=0.4, taxable=0.3)
    assert accounts.roth == pytest.approx(accounts.traditional * (1 - withdrawal))
    value = roth_versus_traditional_bp(
        accounts=accounts,
        withdrawal_rate=withdrawal,
        swapped_weight=0.30,
        high_growth=0.07,
        low_growth=0.05,
        years=30,
    )
    assert value == pytest.approx(0.0, abs=1e-12)


def test_roth_versus_traditional_pinned_at_the_stated_inputs() -> None:
    """2 bp/yr — an order of magnitude below the taxable-versus-sheltered decision."""
    value = roth_versus_traditional_bp(
        accounts=THIRDS,
        withdrawal_rate=0.24,
        swapped_weight=0.30,
        high_growth=0.07,
        low_growth=0.06,
        years=30,
    )
    assert value == pytest.approx(1.96, abs=0.01)
    # Derived here from scratch rather than from the implementation.
    size_gap = 1 / 3 - (1 / 3) * 0.76
    growth_gap = 1.07**30 - 1.06**30
    expected = math.log(1 + 0.30 * size_gap * growth_gap / 1.07**30) / 30 / 1e-4
    assert value == pytest.approx(expected, rel=1e-12)


def test_after_tax_capacity_is_below_nominal_capacity() -> None:
    assert THIRDS.after_tax_shelter_capacity(withdrawal_rate=0.24) == pytest.approx(
        0.58667, abs=1e-5
    )
    assert THIRDS.after_tax_shelter_capacity(withdrawal_rate=0.0) == pytest.approx(
        THIRDS.shelter_capacity
    )


# --------------------------------------------------------------------------------------
# The employer plan's menu
# --------------------------------------------------------------------------------------


def test_the_menu_binds_below_a_fraction_derived_not_asserted() -> None:
    """The unconstrained plan shelters VEA and IEMG; while the employer plan is no
    larger than those two it is free."""
    assert menu_binding_fraction() == pytest.approx(0.55, abs=1e-9)
    index_sheltered = VEA.weight + IEMG.weight
    assert index_sheltered == pytest.approx(0.15)
    assert 1 - index_sheltered / THIRDS.traditional == pytest.approx(menu_binding_fraction())


def test_the_employer_plan_can_always_be_filled_from_the_index_menu() -> None:
    """A third of the portfolio against 35% of index-eligible funds — feasible, barely."""
    eligible = sum(h.weight for h in EQUITY_HOLDINGS if h.ticker in INDEX_MENU)
    assert eligible == pytest.approx(0.35)
    assert eligible > THIRDS.traditional
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        for regime in PLAUSIBLE_RANGE:
            menu_constrained_plan(
                portfolio(wrapper=WRAPPER_RECOGNISED), regime=regime, open_menu_fraction=f
            )


def test_the_wrapper_never_has_to_leave_the_shelter() -> None:
    """The Roth alone exceeds the wrapper's weight, so no open-menu shortage can evict it."""
    assert THIRDS.roth > WRAPPER_RECOGNISED.weight
    for f in (0.0, 0.5, 1.0):
        for regime in PLAUSIBLE_RANGE:
            placed = menu_constrained_plan(
                portfolio(wrapper=WRAPPER_RECOGNISED), regime=regime, open_menu_fraction=f
            )
            assert placed["RSST"] == pytest.approx(0.30)


def test_a_bigger_wrapper_would_evict_itself() -> None:
    """The margin is 3.3 pp of the portfolio, so the invariant above is not structural."""
    fat = Holding(
        ticker="RSST",
        name="a wrapper sized above the Roth",
        weight=0.40,
        expense_ratio=0.0099,
        ordinary_yield=WRAPPER_RECOGNISED.ordinary_yield,
        capital_gain_rate_yield=WRAPPER_RECOGNISED.capital_gain_rate_yield,
        creditable_foreign_tax_yield=0.0,
        source="counterfactual, not a filing",
        as_of="2026-08-22",
    )
    trimmed = tuple(h for h in EQUITY_HOLDINGS if h.ticker != "VTI")
    placed = menu_constrained_plan(
        (fat, *trimmed, VTI), regime=TOP_BRACKET, open_menu_fraction=0.0
    )
    assert placed["RSST"] < 0.40


def test_the_menu_constraint_costs_nothing_above_the_binding_fraction() -> None:
    holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
    for regime in PLAUSIBLE_RANGE:
        unconstrained = saving_bp(plan(holdings, regime=regime, capacity=CAPACITY))
        at_binding = plan_value_bp(
            menu_constrained_plan(
                holdings, regime=regime, open_menu_fraction=menu_binding_fraction()
            ),
            holdings,
            regime=regime,
        )
        assert at_binding == pytest.approx(unconstrained, abs=1e-9)


def test_the_menu_constraint_costs_more_the_lower_the_open_fraction() -> None:
    holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
    values = [
        plan_value_bp(
            menu_constrained_plan(holdings, regime=TOP_BRACKET, open_menu_fraction=f),
            holdings,
            regime=TOP_BRACKET,
        )
        for f in (0.0, 0.25, 0.5, 0.75, 1.0)
    ]
    assert values == sorted(values)


@pytest.mark.parametrize(
    ("open_menu_fraction", "expected"),
    [(0.0, 126.95), (0.5, 135.75), (1.0, 136.03)],
)
def test_menu_constrained_plan_value_at_the_top_bracket(
    open_menu_fraction: float, expected: float
) -> None:
    holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
    placed = menu_constrained_plan(
        holdings, regime=TOP_BRACKET, open_menu_fraction=open_menu_fraction
    )
    assert plan_value_bp(placed, holdings, regime=TOP_BRACKET) == pytest.approx(
        expected, abs=0.01
    )


def test_at_a_captive_traditional_the_two_highest_yielding_funds_are_evicted() -> None:
    """The single most consequential practical fact in the plan."""
    holdings = portfolio(wrapper=WRAPPER_RECOGNISED)
    placed = menu_constrained_plan(holdings, regime=TOP_BRACKET, open_menu_fraction=0.0)
    by_ticker = {h.ticker: h for h in holdings}
    for ticker in ("DFIV", "AVES"):
        assert placed[ticker] == pytest.approx(0.0, abs=1e-12)
    # and VTI, last in the queue at every rate, is forced into the shelter instead
    assert placed["VTI"] > 0.15
    assert by_ticker["VTI"].priority_bp(TOP_BRACKET) < by_ticker["DFIV"].priority_bp(
        TOP_BRACKET
    )


# --------------------------------------------------------------------------------------
# Regret, and why the unresolved accrual does not stall the decision
# --------------------------------------------------------------------------------------


def test_sheltering_the_wrapper_is_regret_dominant_at_every_fraction() -> None:
    for regime in PLAUSIBLE_RANGE:
        for f in (0.0, 0.25, 0.5, 0.75, 1.0):
            cost_if_wrong, cost_if_not = wrapper_regret_bp(
                regime=regime, open_menu_fraction=f
            )
            assert cost_if_wrong > 0.0
            assert cost_if_not > 5.0 * cost_if_wrong


def test_regret_pinned_at_the_top_bracket() -> None:
    assert wrapper_regret_bp(regime=TOP_BRACKET, open_menu_fraction=1.0) == pytest.approx(
        (1.12, 42.62), abs=0.01
    )
    assert wrapper_regret_bp(regime=TOP_BRACKET, open_menu_fraction=0.0) == pytest.approx(
        (8.54, 89.88), abs=0.01
    )


# --------------------------------------------------------------------------------------
# The budget: one benchmark, no summing across, nothing conditional booked
# --------------------------------------------------------------------------------------


def test_the_feasible_control_and_pro_rata_coincide_when_the_menu_is_open() -> None:
    holdings = portfolio(wrapper=WRAPPER_DISTRIBUTED)
    for regime in PLAUSIBLE_RANGE:
        assert feasible_naive_saving_bp(
            holdings, regime=regime, open_menu_fraction=1.0
        ) == pytest.approx(
            pro_rata_saving_bp(holdings, regime=regime, capacity=CAPACITY), abs=1e-9
        )


def test_the_booked_line_is_measured_on_the_audited_basis_only() -> None:
    """94.7% of the headline was one fund's unrealised accrual. It is now not booked."""
    for regime in PLAUSIBLE_RANGE:
        booked = location_edge(regime=regime, open_menu_fraction=1.0)
        conditional = conditional_wrapper_upside_bp(regime=regime, open_menu_fraction=1.0)
        assert conditional > booked.central_bp
        assert booked.certainty is Certainty.DETERMINISTIC
        assert booked.benchmark is Benchmark.COUNTERFACTUAL_HOLDING


@pytest.mark.parametrize(
    ("regime", "booked", "conditional"),
    [
        (TOP_BRACKET, 5.41, 32.81),
        (UPPER_WITH_SURTAX, 4.24, 28.81),
        (UPPER_MIDDLE, 2.04, 19.29),
    ],
)
def test_booked_and_conditional_at_an_open_menu(
    regime: object, booked: float, conditional: float
) -> None:
    assert location_edge_versus_feasible_bp(regime=regime, open_menu_fraction=1.0) == pytest.approx(  # type: ignore[arg-type]
        booked, abs=0.01
    )
    assert conditional_wrapper_upside_bp(regime=regime, open_menu_fraction=1.0) == pytest.approx(  # type: ignore[arg-type]
        conditional, abs=0.01
    )


def test_a_captive_traditional_makes_the_booked_line_negative() -> None:
    """And the guard refuses to publish it as an edge, which is the point of the guard."""
    for regime in PLAUSIBLE_RANGE:
        assert location_edge_versus_feasible_bp(regime=regime, open_menu_fraction=0.0) < 0.0
        with pytest.raises(ValueError, match="loses to pro-rata"):
            location_edge(regime=regime, open_menu_fraction=0.0)


def test_the_booked_line_turns_positive_on_a_very_small_rollover() -> None:
    for regime in PLAUSIBLE_RANGE:
        assert location_edge_versus_feasible_bp(regime=regime, open_menu_fraction=0.10) > 0.0


def test_the_budget_refuses_to_add_across_benchmarks() -> None:
    """`docs/charter.md` forbids it outright, and the guard is the repository's own."""
    against_an_index = EdgeComponent(
        name="a fee gap against a cheap index",
        mechanism="expense-ratio difference",
        benchmark=Benchmark.STATED_INDEX,
        certainty=Certainty.DETERMINISTIC,
        low_bp=0.0,
        central_bp=10.0,
        high_bp=20.0,
        tracking_error_bp=0.0,
        conditions="stated",
        falsifier="a fee change",
    )
    with pytest.raises(ValueError, match="share one benchmark"):
        aggregate([location_edge(regime=TOP_BRACKET), against_an_index])


def test_the_location_line_aggregates_with_itself_and_nothing_else_is_booked() -> None:
    total = aggregate([location_edge(regime=TOP_BRACKET)])
    assert total.benchmark is Benchmark.COUNTERFACTUAL_HOLDING
    assert total.central_bp == pytest.approx(5.41, abs=0.01)


# --------------------------------------------------------------------------------------
# Contributions
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rate", "cover"), [(0.05, 2.5), (0.10, 5.0), (0.15, 7.5)]
)
def test_contributions_cover_the_one_constrained_direction(rate: float, cover: float) -> None:
    assert contributions_cover_the_constrained_direction(contribution_rate=rate) == pytest.approx(
        cover
    )
    assert contributions_cover_the_constrained_direction(contribution_rate=rate) > 1.0
