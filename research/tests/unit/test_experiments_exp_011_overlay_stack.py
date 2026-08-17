"""Offline tests for Experiment 011's arithmetic, on a panel small enough to check by hand.

Every expected value below is a **closed form written out in this file**, never a call
into the module under test. The panel alternates two values in every series, which makes
each statistic a two-line derivation:

    a series of ``n`` copies of ``a`` and ``n`` copies of ``b`` has mean ``(a + b) / 2``
    and sample variance ``n (a - b)**2 / (2 (2n - 1))``,

because the squared deviations are ``n`` copies of ``((a - b) / 2)**2`` on each side.
Alternating up and down months also make the wealth path's drawdown exactly one month
deep, so the drawdown assertions are read off the construction rather than simulated.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pytest

from portfolio_edge.experiments.exp_011_overlay_stack import (
    MONTHS_PER_YEAR,
    AdmissionVerdict,
    CostModel,
    HaircutPoint,
    OverlayStackError,
    Panel,
    admission_verdicts,
    break_even_haircut,
    correlation_matrix,
    default_specification_path,
    haircut_sweep,
    matched_volatility_comparison,
    minimum_detectable_effect,
    require_one_benchmark,
    simulate_portfolio,
    sleeve_moments,
)
from portfolio_edge.experiments.specification import EvidenceClass, RunKind, load_specification

# --------------------------------------------------------------------------- #
# The hand-checkable panel
# --------------------------------------------------------------------------- #

PAIRS: dict[str, tuple[float, float]] = {
    "equity": (0.02, -0.01),
    "treasury": (0.01, 0.00),
    "credit": (0.004, 0.002),
    "commodity": (-0.011, 0.015),
    "trend": (0.03, 0.01),
}
SLEEVES = ("equity", "treasury", "credit", "commodity", "trend")
PORTFOLIO_SLEEVES = ("equity", "treasury", "credit", "trend")
CASH = 0.003
YEARS = 2
N = 6 * YEARS
"""Half the panel length: ``N`` up months and ``N`` down months."""


def alternating(pair: tuple[float, float]) -> list[float]:
    high, low = pair
    return [high if index % 2 == 0 else low for index in range(2 * N)]


def periods() -> tuple[str, ...]:
    return tuple(
        f"{1990 + index // MONTHS_PER_YEAR:04d}-{index % MONTHS_PER_YEAR + 1:02d}"
        for index in range(2 * N)
    )


def build_panel() -> Panel:
    columns = [alternating(PAIRS[sleeve]) for sleeve in SLEEVES]
    return Panel(
        periods=periods(),
        sleeves=SLEEVES,
        excess=np.array(columns, dtype=np.float64).T,
        cash=np.full(2 * N, CASH, dtype=np.float64),
        provenance=(),
        findings=(),
    )


def closed_form_mean(pair: tuple[float, float]) -> float:
    """Annualised arithmetic mean of an alternating series."""
    return (pair[0] + pair[1]) / 2.0 * MONTHS_PER_YEAR


def closed_form_volatility(pair: tuple[float, float]) -> float:
    """Annualised sample volatility of an alternating series, ``ddof = 1``."""
    variance = N * (pair[0] - pair[1]) ** 2 / (2.0 * (2 * N - 1))
    return math.sqrt(variance * MONTHS_PER_YEAR)


def combined_pair(weights: Sequence[float], charge: float) -> tuple[float, float]:
    """The alternating pair a weighted portfolio's monthly excess return takes."""
    monthly = charge / MONTHS_PER_YEAR
    return (
        sum(w * PAIRS[s][0] for s, w in zip(PORTFOLIO_SLEEVES, weights, strict=True)) - monthly,
        sum(w * PAIRS[s][1] for s, w in zip(PORTFOLIO_SLEEVES, weights, strict=True)) - monthly,
    )


COSTS = CostModel(
    sleeve_fee={"equity": 0.0, "treasury": 0.0, "credit": 0.0, "commodity": 0.0, "trend": 0.0145},
    borrow_spread=0.0059,
)


# --------------------------------------------------------------------------- #
# Moments
# --------------------------------------------------------------------------- #


def test_sleeve_moments_match_the_closed_form_for_an_alternating_series() -> None:
    moments = sleeve_moments(build_panel())
    for sleeve, pair in PAIRS.items():
        assert moments[sleeve]["arithmetic_excess_return"] == pytest.approx(
            closed_form_mean(pair)
        )
        assert moments[sleeve]["volatility"] == pytest.approx(closed_form_volatility(pair))
        assert moments[sleeve]["sharpe"] == pytest.approx(
            closed_form_mean(pair) / closed_form_volatility(pair)
        )


def test_two_series_that_move_together_correlate_exactly_one() -> None:
    """Every column here is a scaled, shifted copy of the same square wave."""
    matrix = correlation_matrix(build_panel())
    for row in SLEEVES:
        for column in SLEEVES:
            same_sign = (PAIRS[row][0] - PAIRS[row][1]) * (
                PAIRS[column][0] - PAIRS[column][1]
            ) > 0
            assert matrix[row][column] == pytest.approx(1.0 if same_sign else -1.0)


# --------------------------------------------------------------------------- #
# Costs
# --------------------------------------------------------------------------- #


def test_the_charge_is_a_fee_on_notional_plus_a_spread_on_gross_above_one() -> None:
    charge = COSTS.annual_charge(PORTFOLIO_SLEEVES, (1.0, 0.0, 0.0, 0.5))
    assert charge == pytest.approx(0.5 * 0.0145 + 0.0059 * 0.5)


def test_an_unlevered_portfolio_pays_no_borrow_spread() -> None:
    assert COSTS.annual_charge(PORTFOLIO_SLEEVES, (1.0, 0.0, 0.0, 0.0)) == pytest.approx(0.0)


def test_the_levered_control_pays_the_same_spread_as_the_overlay() -> None:
    """The comparison's sign turns on this: exempting the control would flatter the overlay."""
    overlay = COSTS.annual_charge(PORTFOLIO_SLEEVES, (1.0, 0.0, 0.0, 0.5))
    levered = COSTS.annual_charge(PORTFOLIO_SLEEVES, (1.5, 0.0, 0.0, 0.0))
    assert levered == pytest.approx(0.0059 * 0.5)
    assert overlay - levered == pytest.approx(0.5 * 0.0145)


def test_an_undeclared_fee_is_refused_rather_than_treated_as_zero() -> None:
    with pytest.raises(OverlayStackError, match="no fee is declared"):
        COSTS.fee_for("gold")


def test_a_negative_spread_is_refused() -> None:
    with pytest.raises(OverlayStackError, match="borrow spread cannot be negative"):
        CostModel(sleeve_fee={}, borrow_spread=-0.01)


# --------------------------------------------------------------------------- #
# The simulation
# --------------------------------------------------------------------------- #


def test_equity_only_reproduces_the_hand_computed_wealth_path() -> None:
    summary = simulate_portfolio(
        build_panel(),
        name="equity_only",
        sleeves=PORTFOLIO_SLEEVES,
        weights=(1.0, 0.0, 0.0, 0.0),
        costs=COSTS,
    )
    up, down = PAIRS["equity"][0] + CASH, PAIRS["equity"][1] + CASH
    # Terminal wealth is N up months and N down months in any order; the geometric
    # return over 2N months annualises to the Nth root of the product per year.
    expected_geometric = (1.0 + up) ** (N / YEARS) * (1.0 + down) ** (N / YEARS) - 1.0
    assert summary.geometric_return == pytest.approx(expected_geometric)
    assert summary.gross_notional == pytest.approx(1.0)
    assert summary.annual_cost == pytest.approx(0.0)
    # Up, down, up, down: every trough is exactly one down month below a fresh peak.
    assert summary.max_drawdown == pytest.approx(down)
    assert summary.months_under_water == 1
    assert summary.volatility == pytest.approx(closed_form_volatility(PAIRS["equity"]))
    assert summary.total_return_volatility == pytest.approx(summary.volatility)


def test_the_overlay_charge_is_taken_monthly_inside_the_simulation() -> None:
    weights = (1.0, 0.0, 0.0, 0.5)
    summary = simulate_portfolio(
        build_panel(),
        name="equity_plus_trend_50",
        sleeves=PORTFOLIO_SLEEVES,
        weights=weights,
        costs=COSTS,
    )
    charge = 0.5 * 0.0145 + 0.0059 * 0.5
    pair = combined_pair(weights, charge)
    assert summary.arithmetic_excess_return == pytest.approx(closed_form_mean(pair))
    assert summary.volatility == pytest.approx(closed_form_volatility(pair))
    # Charging the same amount once a year instead would give a different wealth path.
    up, down = pair[0] + CASH, pair[1] + CASH
    assert summary.geometric_return == pytest.approx(
        (1.0 + up) ** (N / YEARS) * (1.0 + down) ** (N / YEARS) - 1.0
    )


def test_the_equity_weight_is_not_sold_down_to_fund_the_sleeve() -> None:
    """The overlay funding rule is the whole point: gross notional exceeds one."""
    panel = build_panel()
    base = simulate_portfolio(
        panel, name="b", sleeves=PORTFOLIO_SLEEVES, weights=(1.0, 0.0, 0.0, 0.0), costs=COSTS
    )
    overlay = simulate_portfolio(
        panel, name="o", sleeves=PORTFOLIO_SLEEVES, weights=(1.0, 0.0, 0.0, 0.5), costs=COSTS
    )
    assert overlay.gross_notional == pytest.approx(1.5)
    charge = 0.5 * 0.0145 + 0.0059 * 0.5
    assert overlay.arithmetic_excess_return - base.arithmetic_excess_return == pytest.approx(
        0.5 * closed_form_mean(PAIRS["trend"]) - charge
    )


def test_a_portfolio_that_reaches_zero_wealth_is_refused_a_growth_rate() -> None:
    panel = build_panel()
    ruined = Panel(
        periods=panel.periods,
        sleeves=panel.sleeves,
        excess=panel.excess,
        cash=panel.cash,
        provenance=(),
        findings=(),
    )
    with pytest.raises(OverlayStackError, match="insolvency"):
        simulate_portfolio(
            ruined,
            name="ruin",
            sleeves=PORTFOLIO_SLEEVES,
            weights=(0.0, 0.0, 0.0, -200.0),
            costs=COSTS,
        )


# --------------------------------------------------------------------------- #
# Equation (5)
# --------------------------------------------------------------------------- #


def _summary(weights: tuple[float, float, float, float], name: str) -> object:
    return simulate_portfolio(
        build_panel(), name=name, sleeves=PORTFOLIO_SLEEVES, weights=weights, costs=COSTS
    )


def test_the_gap_is_sigma_p_times_the_sharpe_difference_exactly() -> None:
    panel = build_panel()
    overlay = simulate_portfolio(
        panel, name="overlay", sleeves=PORTFOLIO_SLEEVES, weights=(1.0, 0.0, 0.0, 0.5), costs=COSTS
    )
    levered = simulate_portfolio(
        panel, name="levered", sleeves=PORTFOLIO_SLEEVES, weights=(1.5, 0.0, 0.0, 0.0), costs=COSTS
    )
    comparison = matched_volatility_comparison(overlay, levered)

    overlay_pair = combined_pair((1.0, 0.0, 0.0, 0.5), 0.5 * 0.0145 + 0.0059 * 0.5)
    levered_pair = combined_pair((1.5, 0.0, 0.0, 0.0), 0.0059 * 0.5)
    overlay_sharpe = closed_form_mean(overlay_pair) / closed_form_volatility(overlay_pair)
    levered_sharpe = closed_form_mean(levered_pair) / closed_form_volatility(levered_pair)
    expected = closed_form_volatility(overlay_pair) * (overlay_sharpe - levered_sharpe)
    assert comparison.gap == pytest.approx(expected)


def test_a_matched_volatility_gap_is_zero_against_a_scaled_copy_of_the_same_portfolio() -> None:
    """Levering the base cannot beat the base at matched volatility. That is equation (5)."""
    panel = build_panel()
    free = CostModel(sleeve_fee=dict.fromkeys(SLEEVES, 0.0), borrow_spread=0.0)
    base = simulate_portfolio(
        panel, name="base", sleeves=PORTFOLIO_SLEEVES, weights=(1.0, 0.0, 0.0, 0.0), costs=free
    )
    levered = simulate_portfolio(
        panel, name="levered", sleeves=PORTFOLIO_SLEEVES, weights=(2.0, 0.0, 0.0, 0.0), costs=free
    )
    assert matched_volatility_comparison(levered, base).gap == pytest.approx(0.0, abs=1e-15)


def test_windows_of_different_length_cannot_be_compared() -> None:
    panel = build_panel()
    long_arm = simulate_portfolio(
        panel, name="long", sleeves=PORTFOLIO_SLEEVES, weights=(1.0, 0.0, 0.0, 0.0), costs=COSTS
    )
    short_arm = simulate_portfolio(
        panel.window(start=panel.periods[0], end=panel.periods[5]),
        name="short",
        sleeves=PORTFOLIO_SLEEVES,
        weights=(1.0, 0.0, 0.0, 0.0),
        costs=COSTS,
    )
    with pytest.raises(OverlayStackError, match="not simulated over the same window"):
        matched_volatility_comparison(long_arm, short_arm)


def _comparison(benchmark: str) -> object:
    panel = build_panel()
    weights = {"equity_only": (1.0, 0.0, 0.0, 0.0), "levered": (1.5, 0.0, 0.0, 0.0)}[benchmark]
    return matched_volatility_comparison(
        simulate_portfolio(
            panel, name="o", sleeves=PORTFOLIO_SLEEVES, weights=(1.0, 0.0, 0.0, 0.5), costs=COSTS
        ),
        simulate_portfolio(
            panel, name=benchmark, sleeves=PORTFOLIO_SLEEVES, weights=weights, costs=COSTS
        ),
    )


def test_comparisons_against_different_benchmarks_may_not_be_combined() -> None:
    """The unlevered control and the levered control are two different claims."""
    rows = [_comparison("equity_only"), _comparison("levered")]
    with pytest.raises(OverlayStackError, match="different benchmarks"):
        require_one_benchmark(rows)  # type: ignore[arg-type]


def test_comparisons_sharing_a_benchmark_report_it() -> None:
    rows = [_comparison("levered")]
    assert require_one_benchmark(rows) == "levered"  # type: ignore[arg-type]


def test_an_empty_set_of_comparisons_is_refused() -> None:
    with pytest.raises(OverlayStackError, match="no comparisons"):
        require_one_benchmark([])


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #


def test_the_detectable_effect_is_the_textbook_two_sided_formula() -> None:
    values = np.array([0.01, -0.01] * 60, dtype=np.float64)
    # sd of a symmetric two-value series with n copies of each is
    # sqrt(n (a-b)^2 / (2 (2n-1))) = 0.01 * sqrt(120/119).
    sd = 0.01 * math.sqrt(120.0 / 119.0)
    expected = (1.959963984540054 + 0.8416212335729143) * MONTHS_PER_YEAR * sd / math.sqrt(120.0)
    assert minimum_detectable_effect(values) == pytest.approx(expected, rel=1e-9)


def test_the_detectable_effect_falls_as_the_root_of_the_sample_length() -> None:
    """Quadrupling the sample halves the floor, up to the ``ddof = 1`` correction."""
    short = np.array([0.01, -0.01] * 60, dtype=np.float64)
    long = np.array([0.01, -0.01] * 240, dtype=np.float64)
    exact = 2.0 * math.sqrt((120.0 / 119.0) / (480.0 / 479.0))
    assert minimum_detectable_effect(short) / minimum_detectable_effect(long) == pytest.approx(
        exact, rel=1e-12
    )


def test_one_observation_cannot_detect_anything() -> None:
    with pytest.raises(OverlayStackError, match="at least two observations"):
        minimum_detectable_effect(np.array([0.01]))


# --------------------------------------------------------------------------- #
# The haircut sweep
# --------------------------------------------------------------------------- #


def test_the_sweep_moves_the_gap_linearly_at_the_sleeve_weight() -> None:
    """A constant off the mean moves the mean and nothing else, so the line is exact."""
    panel = build_panel()
    benchmark = simulate_portfolio(
        panel, name="levered", sleeves=PORTFOLIO_SLEEVES, weights=(1.5, 0.0, 0.0, 0.0), costs=COSTS
    )
    points = haircut_sweep(
        panel,
        sleeve="trend",
        portfolio_sleeves=PORTFOLIO_SLEEVES,
        weights=(1.0, 0.0, 0.0, 0.5),
        benchmark=benchmark,
        costs=COSTS,
        grid=(0.0, 0.01, 0.02, 0.03),
        name="overlay",
    )
    steps = [second.gap - first.gap for first, second in itertools.pairwise(points)]
    for step in steps:
        assert step == pytest.approx(-0.5 * 0.01)


def test_the_break_even_is_interpolated_exactly_on_a_straight_line() -> None:
    points = (
        HaircutPoint(haircut=0.09, gap=0.004, geometric_return=0.0, sharpe=0.0, benchmark="b"),
        HaircutPoint(haircut=0.10, gap=-0.006, geometric_return=0.0, sharpe=0.0, benchmark="b"),
    )
    assert break_even_haircut(points) == pytest.approx(0.09 + 0.01 * 0.004 / 0.010)


def test_a_gap_that_never_crosses_zero_has_no_break_even() -> None:
    points = (
        HaircutPoint(haircut=0.0, gap=0.05, geometric_return=0.0, sharpe=0.0, benchmark="b"),
        HaircutPoint(haircut=0.01, gap=0.04, geometric_return=0.0, sharpe=0.0, benchmark="b"),
    )
    assert break_even_haircut(points) is None


# --------------------------------------------------------------------------- #
# The admission test
# --------------------------------------------------------------------------- #


def test_the_admission_threshold_is_L_rho_sigma_p() -> None:
    verdicts = admission_verdicts(
        build_panel(),
        base="equity",
        sleeves=("trend",),
        costs=COSTS,
        base_exposures=(1.0, 1.5),
    )
    equity_volatility = closed_form_volatility(PAIRS["equity"])
    trend_volatility = closed_form_volatility(PAIRS["trend"])
    net = closed_form_mean(PAIRS["trend"]) - 0.0059 - 0.0145
    for verdict in verdicts:
        assert isinstance(verdict, AdmissionVerdict)
        # Every series here is the same square wave, so rho with equity is exactly 1.
        assert verdict.threshold_sharpe == pytest.approx(
            verdict.base_exposure * 1.0 * equity_volatility
        )
        assert verdict.net_sharpe == pytest.approx(net / trend_volatility)
        assert verdict.margin == pytest.approx(verdict.net_sharpe - verdict.threshold_sharpe)


def test_a_negatively_correlated_sleeve_faces_a_negative_bar() -> None:
    """Not a loophole: it is equation (3) seen from the other side."""
    verdicts = admission_verdicts(
        build_panel(),
        base="equity",
        sleeves=("treasury", "commodity"),
        costs=COSTS,
        base_exposures=(1.0,),
    )
    by_sleeve = {item.sleeve: item for item in verdicts}
    assert by_sleeve["commodity"].correlation == pytest.approx(-1.0)
    assert by_sleeve["commodity"].threshold_sharpe < 0.0
    assert by_sleeve["treasury"].threshold_sharpe > 0.0


# --------------------------------------------------------------------------- #
# Panel plumbing
# --------------------------------------------------------------------------- #


def test_an_unknown_sleeve_names_the_ones_that_exist() -> None:
    with pytest.raises(OverlayStackError, match="no sleeve 'gold'"):
        build_panel().index_of("gold")


def test_a_window_that_selects_nothing_is_refused() -> None:
    with pytest.raises(OverlayStackError, match="selects no months"):
        build_panel().window(start="2050-01", end="2050-12")


def test_a_window_keeps_the_months_it_names() -> None:
    window = build_panel().window(start="1990-04", end="1990-09")
    assert window.periods == ("1990-04", "1990-05", "1990-06", "1990-07", "1990-08", "1990-09")
    assert window.months == 6


# --------------------------------------------------------------------------- #
# What the frozen specification promises
# --------------------------------------------------------------------------- #


def test_the_specification_is_exploratory_and_says_it_cannot_be_promoted() -> None:
    spec = load_specification(default_specification_path())
    assert spec.run_kind is RunKind.EXPLORATORY
    assert spec.evidence_class is EvidenceClass.VENDOR_SERIES_EVALUATION
    assert not spec.consumes_final_holdout
    assert "above `exploratory`" in spec.falsifier
    text = default_specification_path().read_text(encoding="utf-8")
    assert "NOT CONFIRMATORY AND CANNOT BE MADE CONFIRMATORY LATER" in text


def as_mapping(value: object) -> Mapping[str, Any]:
    assert isinstance(value, Mapping)
    return value


def as_sequence(value: object) -> Sequence[Any]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


def test_the_specification_charges_the_borrow_spread_to_the_levered_controls() -> None:
    cost_model = as_mapping(load_specification(default_specification_path()).cost_model)
    assert "LEVERAGE-MATCHED CONTROLS ON THE SAME TERMS" in str(cost_model["charged_uniformly"])


def test_the_specification_forbids_combining_the_two_benchmarks() -> None:
    benchmark = as_mapping(load_specification(default_specification_path()).benchmark)
    assert "MAY NEVER BE ADDED" in str(benchmark["aggregation_rule"])


def test_the_commodity_leg_is_pinned_as_excess_of_cash_and_not_a_total_return() -> None:
    universe = as_mapping(load_specification(default_specification_path()).universe)
    entry = next(
        as_mapping(item)
        for item in as_sequence(universe["series"])
        if as_mapping(item)["id"] == "commodity"
    )
    assert "NOT a collateralised total return" in str(entry["basis"])
