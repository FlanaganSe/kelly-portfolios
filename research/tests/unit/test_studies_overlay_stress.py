"""Tests for :mod:`portfolio_edge.studies.overlay_stress`.

Every expected value below is either computed by hand in the test, derived from a
closed form written out independently of the implementation, or pinned as an
invariant the implementation must not be able to violate. Nothing here asserts the
module's own output back at it.

The tests that matter most are the ones on
:func:`~portfolio_edge.studies.overlay_stress.stress_crisis_correlation` and on
:func:`~portfolio_edge.studies.overlay_stress._paired_difference`. The first is a
construction that would be easy to get subtly wrong in a way that flatters the
overlay — a rotation that moved the crisis-window *mean* as well as the correlation
would confound the two stresses the module exists to separate. The second pins the
scale invariance that caught this module out in review: the leverage-matched gap
against unlevered equity and against equity levered 1.30x is the *same number*, so
printing both as two rows would be double-counting one observation.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.overlay_growth import OverlayInputs
from portfolio_edge.studies.overlay_stress import (
    ADVERSE_COPULA,
    INDEPENDENT_COPULA,
    JointPrior,
    abandonment_cost,
    break_even_net_excess_return,
    closure_hazard,
    drawdown_ladder,
    drought_probability,
    forced_deleveraging,
    gap_pair,
    joint_loss_frequency,
    leave_out_gaps,
    matched_volatility_gap,
    overlay_total_returns,
    paired_drawdown_bootstrap,
    sample_joint_prior,
    stress_crisis_correlation,
    stress_surface,
    tolerable_financing_spread,
    window_drawdowns,
)
from portfolio_edge.studies.overlay_stress import (
    _paired_difference as paired_difference,
)

PRIOR_KWARGS = {
    "excess_centre": 0.040,
    "excess_scale": 0.040,
    "correlation_centre": -0.08,
    "correlation_scale": 0.20,
    "volatility_centre": 0.126,
    "volatility_log_scale": 0.25,
    "spread_centre": 0.0059,
    "spread_log_scale": 0.80,
}


# --------------------------------------------------------------------------------
# 1. The break-even, closed form and by hand
# --------------------------------------------------------------------------------


def test_break_even_matches_a_hand_computation_at_zero_correlation() -> None:
    """At rho = 0, sigma_p = sigma_d and w = 1 the total volatility is sigma_p sqrt(2).

    So the leverage-matched break-even is ``a_p (sqrt(2) - 1)``, which is 2.07107% at
    a 5% base excess return. Worked out on paper, not read off the implementation.
    """
    value = break_even_net_excess_return(
        base_excess_return=0.05,
        base_volatility=0.20,
        diversifier_volatility=0.20,
        correlation=0.0,
        weight=1.0,
    )
    assert value == pytest.approx(0.05 * (math.sqrt(2.0) - 1.0), abs=1e-15)


def test_break_even_is_the_net_return_at_which_the_leverage_matched_gap_is_zero() -> None:
    """The closed form and the simulation-free algebra must agree at every input."""
    for correlation in (-0.4, -0.08, 0.0, 0.25, 0.6):
        for weight in (0.15, 0.30, 1.0):
            a_net = break_even_net_excess_return(
                base_excess_return=0.05,
                base_volatility=0.155,
                diversifier_volatility=0.126,
                correlation=correlation,
                weight=weight,
            )
            pair = gap_pair(
                OverlayInputs(
                    base_excess_return=0.05,
                    base_volatility=0.155,
                    diversifier_excess_return=a_net,
                    diversifier_volatility=0.126,
                    correlation=correlation,
                ),
                weight=weight,
            )
            assert pair.versus_leverage_matched == pytest.approx(0.0, abs=1e-12)


def test_the_leverage_matched_bar_is_positive_even_at_negative_correlation() -> None:
    """The overlay bar of ``overlay_growth`` is negative at rho < 0; this one is not.

    A portfolio held at higher volatility must earn more merely to keep the base's
    Sharpe ratio, so the honest bar is strictly positive whenever the overlay raises
    volatility at all — which it does at every correlation above ``-sigma_d/(2 sigma_p w)``.
    """
    value = break_even_net_excess_return(
        base_excess_return=0.05,
        base_volatility=0.155,
        diversifier_volatility=0.126,
        correlation=-0.08,
        weight=0.30,
    )
    assert value > 0.0


def test_tolerable_financing_spread_is_the_break_even_read_from_the_other_side() -> None:
    spread = tolerable_financing_spread(
        base_excess_return=0.05,
        base_volatility=0.155,
        diversifier_excess_return=0.04,
        diversifier_volatility=0.126,
        correlation=-0.08,
        fee=0.0086,
        weight=0.30,
    )
    bar = break_even_net_excess_return(
        base_excess_return=0.05,
        base_volatility=0.155,
        diversifier_volatility=0.126,
        correlation=-0.08,
        weight=0.30,
    )
    assert spread == pytest.approx(0.04 - 0.0086 - bar, abs=1e-15)


def test_break_even_refuses_a_non_positive_weight() -> None:
    with pytest.raises(ValueError, match="weight must be positive"):
        break_even_net_excess_return(
            base_excess_return=0.05,
            base_volatility=0.155,
            diversifier_volatility=0.126,
            correlation=0.0,
            weight=0.0,
        )


# --------------------------------------------------------------------------------
# 2. The joint prior
# --------------------------------------------------------------------------------


def test_the_prior_reproduces_the_copula_it_was_given() -> None:
    """Rank correlation of the drawn axes must recover the latent correlation matrix.

    Checked on the two monotone marginals whose transform preserves rank exactly
    (the lognormal volatility and spread axes) and on the Gaussian mean axis, so the
    check does not depend on the clipping applied to the correlation axis.
    """
    prior = JointPrior(copula=ADVERSE_COPULA, **PRIOR_KWARGS)
    drawn = sample_joint_prior(prior, draws=200_000, rng=np.random.default_rng(11))
    observed = float(
        np.corrcoef(
            np.log(drawn["diversifier_volatility"]), np.log(drawn["financing_spread"])
        )[0, 1]
    )
    assert observed == pytest.approx(ADVERSE_COPULA[2][3], abs=0.01)
    mean_versus_spread = float(
        np.corrcoef(drawn["diversifier_excess_return"], np.log(drawn["financing_spread"]))[0, 1]
    )
    assert mean_versus_spread == pytest.approx(ADVERSE_COPULA[0][3], abs=0.01)


def test_the_prior_is_reproducible_from_its_seed() -> None:
    prior = JointPrior(copula=ADVERSE_COPULA, **PRIOR_KWARGS)
    first = sample_joint_prior(prior, draws=500, rng=np.random.default_rng(7))
    second = sample_joint_prior(prior, draws=500, rng=np.random.default_rng(7))
    for key in first:
        assert np.array_equal(first[key], second[key])


def test_the_lognormal_axes_have_the_stated_median() -> None:
    """``centre`` is the median, not the mean, and the docstring says so."""
    prior = JointPrior(copula=INDEPENDENT_COPULA, **PRIOR_KWARGS)
    drawn = sample_joint_prior(prior, draws=200_000, rng=np.random.default_rng(3))
    assert float(np.median(drawn["diversifier_volatility"])) == pytest.approx(0.126, abs=0.001)
    assert float(np.median(drawn["financing_spread"])) == pytest.approx(0.0059, abs=0.0001)


def test_a_copula_that_is_not_positive_definite_is_refused() -> None:
    broken = tuple(tuple(1.0 for _ in range(4)) for _ in range(4))
    with pytest.raises(ValueError, match="positive definite"):
        JointPrior(copula=broken, **PRIOR_KWARGS)


def test_a_degenerate_prior_collapses_the_surface_onto_the_point_estimate() -> None:
    """With every scale at zero the surface must be the single deterministic gap."""
    flat = dict(PRIOR_KWARGS)
    flat.update(
        excess_scale=0.0, correlation_scale=0.0, volatility_log_scale=0.0, spread_log_scale=0.0
    )
    prior = JointPrior(copula=INDEPENDENT_COPULA, **flat)
    surface = stress_surface(
        prior,
        base_excess_return=0.05,
        base_volatility=0.155,
        fee=0.0086,
        weight=0.30,
        draws=64,
        rng=np.random.default_rng(1),
    )
    expected = gap_pair(
        OverlayInputs(
            base_excess_return=0.05,
            base_volatility=0.155,
            diversifier_excess_return=0.040,
            diversifier_volatility=0.126,
            correlation=-0.08,
            financing_spread=0.0059,
            fee=0.0086,
        ),
        weight=0.30,
    )
    assert surface.mean_leverage_matched == pytest.approx(expected.versus_leverage_matched)
    assert surface.probability_negative_leverage_matched == 0.0
    assert surface.univariate_worst == pytest.approx(expected.versus_leverage_matched)


def test_dependence_moves_the_tail_further_than_it_moves_the_failure_rate() -> None:
    """The module's first finding, pinned as an ordering rather than as a level.

    An adverse copula must not make the *centre* of the distribution worse — the
    marginals are unchanged — but it must make the low quantile worse. If a future
    change reverses either half, the copula is being applied wrongly.
    """
    arms = {}
    for name, copula in (("independent", INDEPENDENT_COPULA), ("adverse", ADVERSE_COPULA)):
        arms[name] = stress_surface(
            JointPrior(copula=copula, **PRIOR_KWARGS),
            base_excess_return=0.05,
            base_volatility=0.155,
            fee=0.0086,
            weight=0.30,
            draws=20_000,
            rng=np.random.default_rng(20260816),
        )
    assert arms["adverse"].quantiles_leverage_matched["p5"] < (
        arms["independent"].quantiles_leverage_matched["p5"]
    )
    assert arms["adverse"].conditional_shortfall < arms["independent"].conditional_shortfall
    assert arms["adverse"].quantiles_leverage_matched["p50"] == pytest.approx(
        arms["independent"].quantiles_leverage_matched["p50"], abs=0.002
    )


# --------------------------------------------------------------------------------
# 3. Paths, ladders and drawdowns
# --------------------------------------------------------------------------------


def test_overlay_total_returns_on_a_hand_computed_path() -> None:
    base = np.array([0.02, -0.03, 0.01])
    sleeve = np.array([0.01, 0.04, -0.02])
    cash = np.array([0.001, 0.001, 0.001])
    got = overlay_total_returns(
        base, sleeve, cash, weight=0.5, fee=0.012, borrow_spread=0.006
    )
    charge = (0.012 * 0.5 + 0.006 * 0.5) / 12.0
    expected = base + 0.5 * sleeve - charge + cash
    assert np.allclose(got, expected)


def test_the_ladder_at_zero_weight_is_the_base_path_exactly() -> None:
    rng = np.random.default_rng(5)
    base = rng.normal(0.008, 0.04, size=240)
    sleeve = rng.normal(0.005, 0.03, size=240)
    cash = np.full(240, 0.002)
    rung = drawdown_ladder(base, sleeve, cash, weights=(0.0,), fee=0.0095)[0]
    curve = np.cumprod(1.0 + base + cash)
    assert rung.max_drawdown == pytest.approx(
        float(np.min(curve / np.maximum.accumulate(curve))) - 1.0
    )
    assert rung.geometric_return == pytest.approx(float(curve[-1]) ** (12 / 240) - 1.0)
    assert rung.gross_notional == 1.0


def test_the_paired_drawdown_bootstrap_is_identically_zero_at_zero_weight() -> None:
    """At w = 0 the two arms are the same path, so every resample must give exactly 0."""
    rng = np.random.default_rng(9)
    base = rng.normal(0.008, 0.04, size=360)
    sleeve = rng.normal(0.004, 0.03, size=360)
    cash = np.full(360, 0.002)
    interval = paired_drawdown_bootstrap(
        base,
        sleeve,
        cash,
        weight=0.0,
        resamples=50,
        block_length=12,
        rng=np.random.default_rng(2),
    )
    assert interval.observed_difference == pytest.approx(0.0, abs=1e-15)
    assert interval.interval[0] == pytest.approx(0.0, abs=1e-15)
    assert interval.interval[1] == pytest.approx(0.0, abs=1e-15)
    assert interval.probability_deeper == 0.0


def test_the_paired_drawdown_bootstrap_is_reproducible_from_its_seed() -> None:
    rng = np.random.default_rng(4)
    base = rng.normal(0.008, 0.04, size=300)
    sleeve = rng.normal(0.004, 0.03, size=300)
    cash = np.full(300, 0.002)
    arms = [
        paired_drawdown_bootstrap(
            base,
            sleeve,
            cash,
            weight=0.3,
            resamples=200,
            block_length=24,
            rng=np.random.default_rng(77),
        )
        for _ in range(2)
    ]
    assert arms[0].interval == arms[1].interval
    assert arms[0].mean_difference == arms[1].mean_difference


def test_window_drawdowns_skips_a_window_the_panel_does_not_cover() -> None:
    periods = tuple(f"2000-{month:02d}" for month in range(1, 13))
    base = np.full(12, -0.02)
    sleeve = np.full(12, 0.01)
    cash = np.zeros(12)
    rows = window_drawdowns(
        periods,
        base,
        sleeve,
        cash,
        windows={"covered": ("2000-01", "2000-06"), "absent": ("1929-09", "1932-06")},
        weights=(0.0, 0.5),
    )
    assert {row.window for row in rows} == {"covered"}
    assert {row.months for row in rows} == {6}
    #: ``drawdown_summary`` takes the FIRST point of the curve as the opening peak, so a
    #: constant -2%/month base draws down 0.98**5 - 1 over six observations, not 0.98**6 - 1.
    #: Pinned here because getting this wrong overstates every windowed drawdown by one month.
    zero_weight = next(row for row in rows if row.weight == 0.0)
    assert zero_weight.peak_to_trough == pytest.approx(0.98**5 - 1.0)


# --------------------------------------------------------------------------------
# 4. The crisis-correlation rotation — the construction most able to mislead
# --------------------------------------------------------------------------------


def _crisis_panel() -> tuple[np.typing.NDArray[np.float64], np.typing.NDArray[np.float64]]:
    rng = np.random.default_rng(31)
    base = rng.normal(0.006, 0.045, size=600)
    sleeve = rng.normal(0.004, 0.035, size=600)
    return base, sleeve


@pytest.mark.parametrize("target", [-0.5, 0.0, 0.3, 0.75, 0.99])
def test_the_rotation_sets_the_crisis_correlation_to_the_target_exactly(target: float) -> None:
    base, sleeve = _crisis_panel()
    stressed = stress_crisis_correlation(
        base, sleeve, target_correlation=target, drawdown_threshold=0.05
    )
    assert stressed.crisis_correlation_after == pytest.approx(target, abs=1e-12)


def test_the_rotation_preserves_the_crisis_mean_and_volatility() -> None:
    """Otherwise the correlation stress and the return-drought stress are confounded."""
    base, sleeve = _crisis_panel()
    stressed = stress_crisis_correlation(
        base, sleeve, target_correlation=0.6, drawdown_threshold=0.05
    )
    curve = np.cumprod(1.0 + base)
    in_crisis = curve / np.maximum.accumulate(curve) - 1.0 <= -0.05
    assert float(np.mean(stressed.stressed[in_crisis])) == pytest.approx(
        float(np.mean(sleeve[in_crisis])), abs=1e-14
    )
    assert float(np.std(stressed.stressed[in_crisis], ddof=1)) == pytest.approx(
        float(np.std(sleeve[in_crisis], ddof=1)), abs=1e-14
    )


def test_the_rotation_touches_no_month_outside_a_drawdown() -> None:
    base, sleeve = _crisis_panel()
    stressed = stress_crisis_correlation(
        base, sleeve, target_correlation=0.9, drawdown_threshold=0.05
    )
    curve = np.cumprod(1.0 + base)
    outside = curve / np.maximum.accumulate(curve) - 1.0 > -0.05
    assert np.array_equal(stressed.stressed[outside], sleeve[outside])


def test_forcing_the_crisis_mean_moves_only_the_mean() -> None:
    base, sleeve = _crisis_panel()
    stressed = stress_crisis_correlation(
        base, sleeve, target_correlation=0.3, drawdown_threshold=0.05, crisis_mean=0.0
    )
    curve = np.cumprod(1.0 + base)
    in_crisis = curve / np.maximum.accumulate(curve) - 1.0 <= -0.05
    assert float(np.mean(stressed.stressed[in_crisis])) == pytest.approx(0.0, abs=1e-15)
    assert stressed.crisis_correlation_after == pytest.approx(0.3, abs=1e-12)
    assert float(np.std(stressed.stressed[in_crisis], ddof=1)) == pytest.approx(
        float(np.std(sleeve[in_crisis], ddof=1)), abs=1e-14
    )


def test_a_threshold_that_leaves_too_few_crisis_months_raises() -> None:
    base = np.full(50, 0.01)  # never in drawdown at all
    sleeve = np.linspace(-0.01, 0.01, 50)
    with pytest.raises(ValueError, match="crisis months"):
        stress_crisis_correlation(
            base, sleeve, target_correlation=0.5, drawdown_threshold=0.20
        )


# --------------------------------------------------------------------------------
# 5. The failure modes
# --------------------------------------------------------------------------------


def test_forced_deleveraging_is_a_no_op_when_the_trigger_is_never_reached() -> None:
    base = np.full(120, 0.01)
    sleeve = np.full(120, 0.005)
    cash = np.zeros(120)
    outcome = forced_deleveraging(
        base, sleeve, cash, weight=0.3, trigger=0.5, reduced_weight=0.0
    )
    assert outcome.months_deleveraged == 0
    assert outcome.geometric_cost_versus_unconstrained == pytest.approx(0.0, abs=1e-15)
    assert outcome.drawdown_change_versus_unconstrained == pytest.approx(0.0, abs=1e-15)


def test_forced_deleveraging_cuts_after_the_loss_and_restores_only_at_a_new_high() -> None:
    """A hand-built path: -25% then five months of +10%, with a 20% trigger.

    Month 0 loses 25%, so from month 1 the fund is 25% below its peak and the overlay
    is cut. Wealth passes the old peak during the recovery, after which the overlay is
    back on. The overlay is therefore absent for exactly the first part of the
    recovery, which is the mechanism being priced.
    """
    base = np.array([-0.25, 0.10, 0.10, 0.10, 0.10, 0.10])
    sleeve = np.zeros(6)
    cash = np.zeros(6)
    outcome = forced_deleveraging(
        base, sleeve, cash, weight=1.0, trigger=0.20, reduced_weight=0.0, restore_fraction=1.0
    )
    # 0.75 * 1.1**k = 0.825, 0.9075, 0.99825, 1.098 — it first passes the old peak at
    # k = 4, so months 1, 2, 3 and 4 are held with the overlay cut and month 5 is not.
    assert outcome.months_deleveraged == 4


def test_forced_deleveraging_refuses_an_out_of_range_trigger() -> None:
    base = np.full(24, 0.01)
    with pytest.raises(ValueError, match="trigger must lie"):
        forced_deleveraging(
            base, np.zeros(24), np.zeros(24), weight=0.3, trigger=1.5
        )


def test_joint_loss_frequency_on_a_hand_counted_array() -> None:
    base = np.array([-0.01, -0.02, 0.03, 0.04, -0.05, 0.06, -0.07, 0.08])
    sleeve = np.array([-0.01, 0.02, -0.03, 0.04, -0.05, -0.06, 0.07, 0.08])
    joint = joint_loss_frequency(base, sleeve, base_tail_quantile=0.25)
    assert joint.probability_base_loses == pytest.approx(4 / 8)
    assert joint.probability_diversifier_loses == pytest.approx(4 / 8)
    #: both negative at rows 0 and 4.
    assert joint.probability_both_lose == pytest.approx(2 / 8)
    assert joint.independence_benchmark == pytest.approx(0.25)
    assert joint.worst_joint_month == pytest.approx(-0.10)


def test_closure_hazard_matches_an_independent_computation() -> None:
    """13 of 25 over 6.5 years, from Experiment 012's attrition table."""
    hazard = closure_hazard(cohort=25, deaths=13, years_observed=6.5, hold_years=20.0)
    expected = 1.0 - (1.0 - 13 / 25) ** (1.0 / 6.5)
    assert hazard.annual_hazard == pytest.approx(expected, abs=1e-15)
    assert hazard.probability_of_closure_within_hold == pytest.approx(
        1.0 - (1.0 - expected) ** 20.0, abs=1e-15
    )
    low, high = hazard.annual_hazard_interval
    assert low < hazard.annual_hazard < high


def test_closure_hazard_with_no_observed_deaths_is_zero_with_a_non_zero_upper_bound() -> None:
    """The shelf of return-stacked funds has seen no deaths, and that is not evidence of none."""
    hazard = closure_hazard(cohort=13, deaths=0, years_observed=5.0, hold_years=20.0)
    assert hazard.annual_hazard == 0.0
    assert hazard.annual_hazard_interval[0] == 0.0
    assert hazard.annual_hazard_interval[1] > 0.03
    assert hazard.probability_interval_within_hold[1] > 0.5


def test_closure_hazard_rejects_impossible_cohorts() -> None:
    with pytest.raises(ValueError, match="deaths"):
        closure_hazard(cohort=10, deaths=11, years_observed=5.0, hold_years=10.0)


# --------------------------------------------------------------------------------
# 6. The benchmark rule, pinned
# --------------------------------------------------------------------------------


def test_the_leverage_matched_gap_is_invariant_to_rescaling_the_benchmark() -> None:
    """The defect this pins: unlevered equity and equity levered 1.30x are ONE row.

    Reporting them as two lines of a table would present one observation as two, which
    is the benchmark-aggregation error the repository's own tooling raises on
    elsewhere. The unlevered gap is *not* invariant, which is why the two scalings are
    separate arguments rather than a default.
    """
    rng = np.random.default_rng(19)
    portfolio = rng.normal(0.009, 0.045, size=400)
    benchmark = rng.normal(0.006, 0.040, size=400)
    matched = paired_difference(portfolio, benchmark, scaling="leverage_matched")
    rescaled = paired_difference(portfolio, 1.30 * benchmark, scaling="leverage_matched")
    assert np.allclose(matched, rescaled, atol=1e-15)
    unlevered = paired_difference(portfolio, benchmark, scaling="unlevered")
    rescaled_unlevered = paired_difference(portfolio, 1.30 * benchmark, scaling="unlevered")
    assert not np.allclose(unlevered, rescaled_unlevered)


def test_matched_volatility_gap_returns_the_estimate_and_its_floor() -> None:
    rng = np.random.default_rng(23)
    portfolio = rng.normal(0.009, 0.045, size=400)
    benchmark = rng.normal(0.006, 0.040, size=400)
    gap, mde = matched_volatility_gap(portfolio, benchmark, scaling="leverage_matched")
    difference = paired_difference(portfolio, benchmark, scaling="leverage_matched")
    assert gap == pytest.approx(float(np.mean(difference)) * 12.0)
    assert mde > 0.0


def test_a_portfolio_compared_with_itself_never_droughts() -> None:
    rng = np.random.default_rng(29)
    series = rng.normal(0.008, 0.04, size=480)
    estimate = drought_probability(
        series,
        series,
        scaling="leverage_matched",
        horizon_months=60,
        resamples=200,
        block_length=24,
        rng=np.random.default_rng(3),
    )
    assert estimate.probability_negative_gap == 0.0
    assert estimate.median_gap == pytest.approx(0.0, abs=1e-14)
    assert estimate.scaling == "leverage_matched"


def test_leave_out_gaps_removing_the_strongest_months_lowers_the_gap() -> None:
    rng = np.random.default_rng(37)
    benchmark = rng.normal(0.006, 0.040, size=360)
    portfolio = benchmark.copy()
    portfolio[100:112] += 0.05  # one very good year for the portfolio only
    rows = leave_out_gaps(
        portfolio,
        benchmark,
        scaling="unlevered",
        groups={"the good year": list(range(100, 112)), "a quiet year": list(range(200, 212))},
    )
    by_name = {row.removed: row for row in rows}
    assert by_name["the good year"].change_from_full_sample < -0.01
    assert abs(by_name["a quiet year"].change_from_full_sample) < abs(
        by_name["the good year"].change_from_full_sample
    )
    assert by_name["the good year"].months_removed == 12


def test_abandonment_cost_counts_its_windows_correctly() -> None:
    rng = np.random.default_rng(41)
    portfolio = rng.normal(0.009, 0.045, size=300)
    benchmark = rng.normal(0.006, 0.040, size=300)
    cost = abandonment_cost(
        portfolio, benchmark, scaling="leverage_matched", review_years=5, subsequent_years=5
    )
    assert cost.windows == 300 - 60 - 60 + 1
    assert 0.0 <= cost.probability_review_shows_a_loss <= 1.0
    assert cost.scaling == "leverage_matched"


def test_abandonment_cost_refuses_a_series_too_short_for_its_windows() -> None:
    with pytest.raises(ValueError, match="need at least"):
        abandonment_cost(
            np.zeros(60) + 0.01,
            np.zeros(60) + 0.005,
            scaling="unlevered",
            review_years=5,
            subsequent_years=5,
        )
