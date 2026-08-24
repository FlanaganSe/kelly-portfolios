"""Tests for :mod:`portfolio_edge.studies.trend_weight_regret`.

The load-bearing checks are the ones that do not reuse the implementation's own algebra:
the leverage-matched gap is rebuilt from the definition of log growth rather than from the
closed form, and the minimax identity is checked against a brute-force minimax and against
a numerical average of the optimal weight over the support. Everything else is contracts,
units and numerical edges.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.trend_weight_regret import (
    OverlayGrowthModel,
    PremiumPrior,
    PremiumScenario,
    abandonment_adjusted_gap,
    conditional_decade_gaps,
    minimax_regret_weight,
    regret_from_gaps,
    regret_surface,
    restate_annual_mean,
    robust_range,
    years_to_resolve,
)

MODEL = OverlayGrowthModel(
    equity_excess_return=0.0982,
    equity_volatility=0.1511,
    trend_volatility=0.1238,
    correlation=-0.1559,
    equity_financing_spread=0.0062,
)

GRID = tuple(round(0.02 * i, 2) for i in range(21))


def _scenario(label: str, gross: float, weight: float) -> PremiumScenario:
    return PremiumScenario(
        label=label,
        gross_premium=gross,
        prior_weight=weight,
        provenance="fixture",
        vendor_authored=False,
    )


def _prior() -> PremiumPrior:
    return PremiumPrior(
        scenarios=(
            _scenario("floor", 0.0, 0.25),
            _scenario("middle", 0.0180, 0.45),
            _scenario("ceiling", 0.1098, 0.30),
        ),
        cost_per_unit_notional=0.01165,
    )


# --------------------------------------------------------------------------------
# The growth model
# --------------------------------------------------------------------------------


def test_cheap_index_gap_matches_an_independently_computed_fixture() -> None:
    """``w (m - rho sigma_e sigma_d) - w**2 sigma_d**2 / 2``, worked by hand."""
    covariance = -0.1559 * 0.1511 * 0.1238
    expected = 0.30 * (0.0063 - covariance) - 0.5 * 0.30**2 * 0.1238**2
    assert MODEL.growth_gap(
        weight=0.30, net_premium=0.0063, benchmark="cheap_index"
    ) == pytest.approx(expected, abs=1e-15)
    assert expected == pytest.approx(0.00207520, abs=1e-8)


def test_leverage_matched_gap_rebuilt_from_the_definition_of_log_growth() -> None:
    """Not the closed form: two portfolios' ``mean - variance / 2``, differenced.

    The candidate is one unit of equity plus ``w`` of trend earning ``m`` net; the control
    is ``1 + w`` units of equity paying the financing spread on the financed part. This is
    the fixture that would catch a sign error in the closed form, because it shares no
    algebra with it.
    """
    weight, net = 0.30, 0.0063
    sigma_e, sigma_d = 0.1511, 0.1238
    covariance = -0.1559 * sigma_e * sigma_d

    candidate_mean = 0.0982 + weight * net
    candidate_variance = sigma_e**2 + 2.0 * weight * covariance + weight**2 * sigma_d**2
    candidate_growth = candidate_mean - 0.5 * candidate_variance

    control_mean = (1.0 + weight) * 0.0982 - weight * 0.0062
    control_variance = (1.0 + weight) ** 2 * sigma_e**2
    control_growth = control_mean - 0.5 * control_variance

    assert MODEL.growth_gap(
        weight=weight, net_premium=net, benchmark="leverage_matched"
    ) == pytest.approx(candidate_growth - control_growth, abs=1e-15)


def test_the_two_benchmarks_differ_by_a_term_free_of_the_trend_leg() -> None:
    """The difference must not move when the trend premium does — that is the funding rule."""
    differences = [
        MODEL.growth_gap(weight=0.30, net_premium=m, benchmark="cheap_index")
        - MODEL.growth_gap(weight=0.30, net_premium=m, benchmark="leverage_matched")
        for m in (-0.02, 0.0, 0.03, 0.10)
    ]
    assert max(differences) - min(differences) < 1e-15


def test_break_even_is_the_exact_inverse_of_the_gap() -> None:
    for benchmark in ("cheap_index", "leverage_matched"):
        for weight in (0.05, 0.20, 0.30, 0.50, 1.00):
            premium = MODEL.break_even_net_premium(weight=weight, benchmark=benchmark)
            assert MODEL.growth_gap(
                weight=weight, net_premium=premium, benchmark=benchmark
            ) == pytest.approx(0.0, abs=1e-15)


def test_gap_is_linear_in_the_net_premium_at_a_fixed_weight() -> None:
    """Which is what licenses evaluating max regret at the support's endpoints alone."""
    for benchmark in ("cheap_index", "leverage_matched"):
        gaps = [
            MODEL.growth_gap(weight=0.25, net_premium=m, benchmark=benchmark)
            for m in (0.00, 0.01, 0.02, 0.03)
        ]
        first = np.diff(gaps)
        assert np.allclose(first, first[0], atol=1e-15)


def test_gap_is_zero_at_zero_weight_on_both_benchmarks() -> None:
    for benchmark in ("cheap_index", "leverage_matched"):
        assert (
            MODEL.growth_gap(weight=0.0, net_premium=0.05, benchmark=benchmark)
            == 0.0
        )


def test_model_rejects_impossible_inputs() -> None:
    with pytest.raises(ValueError, match="equity volatility"):
        OverlayGrowthModel(
            equity_excess_return=0.05,
            equity_volatility=0.0,
            trend_volatility=0.12,
            correlation=0.0,
        )
    with pytest.raises(ValueError, match="trend volatility"):
        OverlayGrowthModel(
            equity_excess_return=0.05,
            equity_volatility=0.15,
            trend_volatility=-0.1,
            correlation=0.0,
        )
    with pytest.raises(ValueError, match="correlation"):
        OverlayGrowthModel(
            equity_excess_return=0.05,
            equity_volatility=0.15,
            trend_volatility=0.12,
            correlation=1.5,
        )
    with pytest.raises(ValueError, match="unknown benchmark"):
        MODEL.growth_gap(weight=0.3, net_premium=0.01, benchmark="something")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="degenerate"):
        MODEL.break_even_net_premium(weight=0.0, benchmark="cheap_index")
    with pytest.raises(ValueError, match="must not be empty"):
        MODEL.best_weight(net_premium=0.01, benchmark="cheap_index", weights=())


# --------------------------------------------------------------------------------
# The prior
# --------------------------------------------------------------------------------


def test_prior_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="must sum to 1"):
        PremiumPrior(
            scenarios=(_scenario("a", 0.0, 0.4), _scenario("b", 0.02, 0.4)),
            cost_per_unit_notional=0.01,
        )
    with pytest.raises(ValueError, match="at least one scenario"):
        PremiumPrior(scenarios=(), cost_per_unit_notional=0.01)
    with pytest.raises(ValueError, match="non-negative"):
        _scenario("a", 0.0, -0.1)


def test_net_premia_mean_median_and_support() -> None:
    prior = _prior()
    assert prior.net_premia == pytest.approx((-0.01165, 0.00635, 0.09815))
    assert prior.mean == pytest.approx(
        0.25 * -0.01165 + 0.45 * 0.00635 + 0.30 * 0.09815, abs=1e-15
    )
    # Cumulative weight reaches one half at the middle scenario.
    assert prior.median == pytest.approx(0.00635)
    assert prior.support == pytest.approx((-0.01165, 0.09815))
    assert prior.probability_below(0.0) == pytest.approx(0.25)


def test_a_zero_weight_scenario_leaves_the_support() -> None:
    """Otherwise the weight sweep would move the Bayes answer and never the minimax one."""
    prior = _prior().reweighted((0.35, 0.65, 0.0))
    assert prior.support == pytest.approx((-0.01165, 0.00635))
    with pytest.raises(ValueError, match="need one weight per scenario"):
        _prior().reweighted((0.5, 0.5))


# --------------------------------------------------------------------------------
# Regret
# --------------------------------------------------------------------------------


def test_regret_from_gaps_on_a_hand_built_matrix() -> None:
    prior = PremiumPrior(
        scenarios=(_scenario("lo", 0.0, 0.5), _scenario("hi", 0.10, 0.5)),
        cost_per_unit_notional=0.0,
    )
    # Row 0 wins at the low premium, row 2 at the high one, row 1 is never best.
    gaps = ((0.0, 0.0), (-0.01, 0.02), (-0.035, 0.05))
    surface = regret_from_gaps(
        gaps, weights=(0.0, 0.2, 0.4), prior=prior, benchmark="cheap_index"
    )
    assert surface.regret[0] == pytest.approx((0.0, 0.05))
    assert surface.regret[1] == pytest.approx((0.01, 0.03))
    assert surface.regret[2] == pytest.approx((0.035, 0.0))
    assert surface.max_regret == pytest.approx((0.05, 0.03, 0.035))
    assert surface.minimax_weight == 0.2
    assert surface.expected_regret == pytest.approx((0.025, 0.02, 0.0175))
    assert surface.bayes_weight == 0.4
    with pytest.raises(ValueError, match="one row of gaps per weight"):
        regret_from_gaps(gaps, weights=(0.0,), prior=prior, benchmark="cheap_index")
    with pytest.raises(ValueError, match="one column of gaps per prior scenario"):
        regret_from_gaps(
            ((0.0,), (0.0,), (0.0,)),
            weights=(0.0, 0.2, 0.4),
            prior=prior,
            benchmark="cheap_index",
        )


def test_regret_is_non_negative_and_zero_at_the_best_weight() -> None:
    surface = regret_surface(
        MODEL, weights=GRID, prior=_prior(), benchmark="leverage_matched"
    )
    flat = [value for row in surface.regret for value in row]
    assert min(flat) >= -1e-15
    for j in range(len(surface.net_premia)):
        assert min(surface.regret[i][j] for i in range(len(surface.weights))) == pytest.approx(
            0.0, abs=1e-15
        )


def test_minimax_identity_matches_a_brute_force_minimax() -> None:
    """The closed form against a dense search over the same action space."""
    prior = _prior()
    dense = tuple(round(0.001 * i, 3) for i in range(1001))
    for benchmark in ("cheap_index", "leverage_matched"):
        closed = minimax_regret_weight(
            MODEL, weights=dense, support=prior.support, benchmark=benchmark
        )
        lo, hi = prior.support
        worst = [
            max(
                MODEL.best_weight(net_premium=m, benchmark=benchmark, weights=dense)[1]
                - MODEL.growth_gap(weight=w, net_premium=m, benchmark=benchmark)
                for m in (lo, hi)
            )
            for w in dense
        ]
        brute = dense[int(np.argmin(worst))]
        assert closed == pytest.approx(brute, abs=0.002)


def test_minimax_weight_is_the_average_optimal_weight_over_the_support() -> None:
    """The envelope-theorem reading, checked numerically and not asserted in prose."""
    prior = _prior()
    lo, hi = prior.support
    for benchmark in ("cheap_index", "leverage_matched"):
        closed = minimax_regret_weight(
            MODEL, weights=GRID, support=(lo, hi), benchmark=benchmark
        )
        grid = np.linspace(lo, hi, 20_001)
        optimal = np.array(
            [
                MODEL.best_weight(net_premium=float(m), benchmark=benchmark, weights=GRID)[0]
                for m in grid
            ]
        )
        assert closed == pytest.approx(float(np.trapezoid(optimal, grid) / (hi - lo)), abs=1e-3)


def test_minimax_weight_rejects_a_degenerate_support() -> None:
    with pytest.raises(ValueError, match="non-degenerate"):
        minimax_regret_weight(
            MODEL, weights=GRID, support=(0.02, 0.02), benchmark="cheap_index"
        )


def test_robust_range_brackets_the_minimax_weight() -> None:
    surface = regret_surface(MODEL, weights=GRID, prior=_prior(), benchmark="leverage_matched")
    low, high = robust_range(surface, tolerance=0.0010)
    assert low <= surface.minimax_weight <= high
    tight = robust_range(surface, tolerance=0.0)
    assert tight[0] <= surface.minimax_weight <= tight[1]
    with pytest.raises(ValueError, match="non-negative"):
        robust_range(surface, tolerance=-0.1)


def test_regret_at_looks_up_a_cell() -> None:
    prior = _prior()
    surface = regret_surface(MODEL, weights=GRID, prior=prior, benchmark="cheap_index")
    assert surface.regret_at(0.30, prior.net_premia[0]) == pytest.approx(
        surface.regret[GRID.index(0.30)][0]
    )


# --------------------------------------------------------------------------------
# Capitulation
# --------------------------------------------------------------------------------


def test_restate_mean_moves_only_the_mean() -> None:
    rng = np.random.default_rng(7)
    series = rng.normal(0.004, 0.03, size=400)
    other = rng.normal(0.006, 0.04, size=400)
    shifted = restate_annual_mean(series, annual_mean=0.018)
    assert float(np.mean(shifted)) * 12.0 == pytest.approx(0.018, abs=1e-15)
    assert float(np.std(shifted, ddof=1)) == pytest.approx(float(np.std(series, ddof=1)))
    assert float(np.corrcoef(shifted, other)[0, 1]) == pytest.approx(
        float(np.corrcoef(series, other)[0, 1])
    )


def test_abandonment_annualises_exactly_on_a_deterministic_pair() -> None:
    """Constant monthly returns: every resample is the same path, so the answer is exact."""
    candidate = np.full(240, 0.008)
    control = np.full(240, 0.006)
    outcome = abandonment_adjusted_gap(
        candidate,
        control,
        weight=0.3,
        net_premium=0.02,
        trigger=-0.20,
        horizon_years=10.0,
        resamples=64,
        block_length=12,
        rng=np.random.default_rng(1),
    )
    expected = 12.0 * math.log(1.008 / 1.006)
    assert outcome.gap_if_held == pytest.approx(expected, abs=1e-12)
    assert outcome.gap_with_abandonment == pytest.approx(expected, abs=1e-12)
    assert outcome.probability_abandoned == 0.0
    assert outcome.probability_underperform_if_held == 0.0
    assert math.isnan(outcome.median_months_to_abandonment)
    assert outcome.capitulation_cost == pytest.approx(0.0, abs=1e-12)


def test_an_identical_pair_has_no_gap_and_never_capitulates() -> None:
    rng = np.random.default_rng(3)
    series = rng.normal(0.005, 0.04, size=300)
    outcome = abandonment_adjusted_gap(
        series,
        series,
        weight=0.3,
        net_premium=0.0,
        trigger=-0.05,
        horizon_years=20.0,
        resamples=200,
        block_length=24,
        rng=np.random.default_rng(5),
    )
    assert outcome.gap_if_held == pytest.approx(0.0, abs=1e-12)
    assert outcome.probability_abandoned == 0.0


def test_a_trigger_that_can_never_fire_reproduces_the_held_gap() -> None:
    rng = np.random.default_rng(11)
    control = rng.normal(0.006, 0.04, size=400)
    candidate = control + rng.normal(0.0005, 0.01, size=400)
    loose = abandonment_adjusted_gap(
        candidate,
        control,
        weight=0.3,
        net_premium=0.01,
        trigger=-0.99,
        horizon_years=20.0,
        resamples=300,
        block_length=24,
        rng=np.random.default_rng(2),
    )
    assert loose.probability_abandoned == 0.0
    assert loose.gap_with_abandonment == pytest.approx(loose.gap_if_held, abs=1e-12)
    tight = abandonment_adjusted_gap(
        candidate,
        control,
        weight=0.3,
        net_premium=0.01,
        trigger=-0.01,
        horizon_years=20.0,
        resamples=300,
        block_length=24,
        rng=np.random.default_rng(2),
    )
    assert tight.probability_abandoned > loose.probability_abandoned


def test_capitulation_probability_rises_with_the_overlay_weight() -> None:
    rng = np.random.default_rng(13)
    equity = rng.normal(0.007, 0.045, size=427)
    trend = rng.normal(0.001, 0.036, size=427)
    control = equity.copy()
    probabilities = []
    for weight in (0.05, 0.20, 0.40):
        outcome = abandonment_adjusted_gap(
            equity + weight * trend,
            control,
            weight=weight,
            net_premium=0.012,
            trigger=-0.10,
            horizon_years=30.0,
            resamples=500,
            block_length=24,
            rng=np.random.default_rng(17),
        )
        probabilities.append(outcome.probability_abandoned)
    assert probabilities[0] < probabilities[1] < probabilities[2]


def test_abandonment_rejects_bad_arguments() -> None:
    series = np.full(120, 0.005)
    with pytest.raises(ValueError, match="negative relative drawdown"):
        abandonment_adjusted_gap(
            series,
            series,
            weight=0.3,
            net_premium=0.0,
            trigger=0.1,
            horizon_years=5.0,
            resamples=10,
            block_length=12,
            rng=np.random.default_rng(0),
        )
    with pytest.raises(ValueError, match="same length"):
        abandonment_adjusted_gap(
            series,
            series[:100],
            weight=0.3,
            net_premium=0.0,
            trigger=-0.1,
            horizon_years=5.0,
            resamples=10,
            block_length=12,
            rng=np.random.default_rng(0),
        )
    with pytest.raises(ValueError, match="at least one"):
        abandonment_adjusted_gap(
            series,
            series,
            weight=0.3,
            net_premium=0.0,
            trigger=-0.1,
            horizon_years=5.0,
            resamples=0,
            block_length=12,
            rng=np.random.default_rng(0),
        )
    with pytest.raises(ValueError, match="must cover a month"):
        abandonment_adjusted_gap(
            series,
            series,
            weight=0.3,
            net_premium=0.0,
            trigger=-0.1,
            horizon_years=0.0,
            resamples=10,
            block_length=12,
            rng=np.random.default_rng(0),
        )


# --------------------------------------------------------------------------------
# Conditional decades
# --------------------------------------------------------------------------------


def test_decade_gaps_recover_a_known_constant_edge() -> None:
    """A candidate that is the control plus a fixed monthly increment has a flat gap."""
    rng = np.random.default_rng(23)
    control = rng.normal(0.006, 0.04, size=300)
    periods = tuple(f"{1990 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(300))
    candidate = (1.0 + control) * 1.001 - 1.0
    decade = conditional_decade_gaps(
        periods, candidate, control, weight=0.3, net_premium=0.01
    )
    expected = 12.0 * math.log(1.001)
    assert decade.mean_gap_in_worst_decile == pytest.approx(expected, abs=1e-12)
    assert decade.mean_gap_elsewhere == pytest.approx(expected, abs=1e-12)
    assert decade.windows == 300 - 120 + 1
    assert decade.worst_candidate_growth > decade.worst_equity_growth


def test_decade_gaps_find_the_worst_window() -> None:
    periods = tuple(f"{1990 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(240))
    control = np.full(240, 0.01)
    control[60:180] = -0.005  # the decade starting at index 60 is the worst
    decade = conditional_decade_gaps(
        periods, control.copy(), control, weight=0.0, net_premium=0.0
    )
    assert decade.worst_window == (periods[60], periods[179])
    assert decade.worst_equity_growth == pytest.approx(12.0 * math.log(0.995), abs=1e-12)


def test_decade_gaps_reject_short_or_mismatched_input() -> None:
    periods = tuple(f"{1990 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(60))
    series = np.full(60, 0.005)
    with pytest.raises(ValueError, match="at least 120 months"):
        conditional_decade_gaps(periods, series, series, weight=0.3, net_premium=0.0)
    with pytest.raises(ValueError, match="line up"):
        conditional_decade_gaps(
            periods[:50], np.full(200, 0.005), np.full(200, 0.005), weight=0.3, net_premium=0.0
        )


# --------------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------------


def test_years_to_resolve_is_the_square_of_the_floor_ratio() -> None:
    assert years_to_resolve(
        gap=0.0021, minimum_detectable_effect=0.0174, window_years=35.6
    ) == pytest.approx(35.6 * (0.0174 / 0.0021) ** 2, abs=1e-9)
    assert years_to_resolve(
        gap=-0.02, minimum_detectable_effect=0.02, window_years=10.0
    ) == pytest.approx(10.0)
    assert math.isinf(
        years_to_resolve(gap=0.0, minimum_detectable_effect=0.01, window_years=10.0)
    )
    with pytest.raises(ValueError, match="window_years"):
        years_to_resolve(gap=0.01, minimum_detectable_effect=0.01, window_years=0.0)
    with pytest.raises(ValueError, match="non-negative"):
        years_to_resolve(gap=0.01, minimum_detectable_effect=-0.01, window_years=10.0)
