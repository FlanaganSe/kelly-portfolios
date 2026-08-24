"""Tests for :mod:`portfolio_edge.studies.volatility_harvesting`.

Every closed form here is asserted twice: against an independently derived algebraic
value, and against a seeded Monte Carlo with a stated tolerance. The tolerances are
derived from the simulation's own standard error rather than tuned until they pass; a
fixture that disagrees with our own computation is a finding, not a tolerance to loosen.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.polynomial.hermite import hermgauss
from numpy.typing import NDArray
from scipy.stats import norm

from portfolio_edge.core.portfolio import excess_growth_rate
from portfolio_edge.studies.rebalancing_monte_carlo import (
    core_simulator_growth_rates,
    simulate_growth_comparison,
)
from portfolio_edge.studies.volatility_harvesting import (
    MINIMUM_PROBABILITY,
    asymptotic_buy_and_hold_growth,
    breakeven_drift_gap,
    buy_and_hold_growth_rate,
    buy_and_hold_log_bonus,
    discrete_rebalancing_growth_bonus,
    excess_growth_two_asset,
    horizon_for_rebalancing_confidence,
    log_cosh,
    probability_rebalanced_beats_buy_and_hold,
    probability_rebalanced_beats_single_asset,
    rebalanced_growth_rate,
    rebalancing_advantage,
    rebalancing_advantage_quantile,
    rebalancing_beats_buy_and_hold_asymptotically,
    relative_log_volatility,
)

FloatArray = NDArray[np.float64]

SIGMA = 0.2
DRIFT = 0.05
HORIZON = 30.0


# --------------------------------------------------------------------------------------
# The excess growth rate itself
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("correlation", "expected"),
    [(0.0, 0.01), (0.3, 0.007), (0.6, 0.004), (0.9, 0.001), (1.0, 0.0)],
)
def test_excess_growth_is_quarter_sigma_squared_times_one_minus_rho(
    correlation: float, expected: float
) -> None:
    """gamma* = sigma**2 (1 - rho) / 4 at equal volatilities and 50/50.

    Derived independently: sum_i w_i sigma_i**2 = sigma**2 and
    sigma_p**2 = sigma**2 (1 + rho) / 2, so
    gamma* = (sigma**2 - sigma**2 (1 + rho) / 2) / 2 = sigma**2 (1 - rho) / 4.
    At sigma = 20% this is exactly 100 bp/yr per unit of (1 - rho).
    """
    value = excess_growth_two_asset(
        volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
    )
    assert value == pytest.approx(expected, rel=0.0, abs=1e-15)


def test_excess_growth_two_asset_matches_the_general_core_formula() -> None:
    """The scalar shortcut must equal core.portfolio.excess_growth_rate exactly."""
    for correlation in (-0.5, 0.0, 0.25, 0.8):
        for weight in (0.2, 0.5, 0.75):
            sigma_a, sigma_b = 0.18, 0.27
            covariance = [
                [sigma_a**2, correlation * sigma_a * sigma_b],
                [correlation * sigma_a * sigma_b, sigma_b**2],
            ]
            general = excess_growth_rate([weight, 1.0 - weight], covariance)
            scalar = excess_growth_two_asset(
                volatility_a=sigma_a,
                volatility_b=sigma_b,
                correlation=correlation,
                weight_a=weight,
            )
            assert scalar == pytest.approx(general, rel=0.0, abs=1e-15)


def test_excess_growth_vanishes_at_perfect_correlation() -> None:
    """No dispersion in log space, no excess growth. There is nothing to harvest."""
    assert excess_growth_two_asset(volatility_a=0.2, volatility_b=0.2, correlation=1.0) == 0.0


def test_relative_log_volatility_and_excess_growth_satisfy_tau_squared_over_eight() -> None:
    """gamma* = tau**2 / 8 in the symmetric case; this identity carries the whole study."""
    for correlation in (-0.9, 0.0, 0.5, 0.99):
        tau = relative_log_volatility(
            volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
        )
        gamma = excess_growth_two_asset(
            volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
        )
        assert gamma == pytest.approx(tau**2 / 8.0, rel=0.0, abs=1e-15)


# --------------------------------------------------------------------------------------
# The asymptotic condition
# --------------------------------------------------------------------------------------


def test_asymptotic_buy_and_hold_growth_is_the_maximum_component_growth() -> None:
    assert asymptotic_buy_and_hold_growth([0.03, 0.05, 0.04]) == 0.05


def test_proved_condition_is_g_p_greater_than_max_component_growth() -> None:
    """With equal drifts, any positive gamma* wins; a drift gap above gamma* loses."""
    gamma = excess_growth_two_asset(volatility_a=SIGMA, volatility_b=SIGMA, correlation=0.0)
    equal = rebalanced_growth_rate(
        growth_a=DRIFT,
        growth_b=DRIFT,
        volatility_a=SIGMA,
        volatility_b=SIGMA,
        correlation=0.0,
    )
    assert equal == pytest.approx(DRIFT + gamma, rel=0.0, abs=1e-15)
    assert rebalancing_beats_buy_and_hold_asymptotically(
        portfolio_growth_rate=equal, component_growth_rates=[DRIFT, DRIFT]
    )

    gap = 2.0 * gamma
    unequal = rebalanced_growth_rate(
        growth_a=DRIFT + gap,
        growth_b=DRIFT - gap,
        volatility_a=SIGMA,
        volatility_b=SIGMA,
        correlation=0.0,
    )
    assert not rebalancing_beats_buy_and_hold_asymptotically(
        portfolio_growth_rate=unequal, component_growth_rates=[DRIFT + gap, DRIFT - gap]
    )


def test_asymptotic_condition_ties_are_not_a_win() -> None:
    """At g_p = max_i g_i the difference is driftless O(sqrt(T)) noise, so False."""
    assert not rebalancing_beats_buy_and_hold_asymptotically(
        portfolio_growth_rate=0.05, component_growth_rates=[0.05, 0.01]
    )


def test_buy_and_hold_growth_converges_to_the_maximum_component_growth() -> None:
    """The expected-log rate falls towards max_i g_i, but only like 1/sqrt(T)."""
    previous = math.inf
    for horizon in (10.0, 100.0, 1_000.0, 10_000.0, 100_000.0):
        rate = buy_and_hold_growth_rate(
            growth_a=DRIFT,
            growth_b=DRIFT,
            volatility_a=SIGMA,
            volatility_b=SIGMA,
            correlation=0.0,
            horizon_years=horizon,
        )
        assert rate < previous
        previous = rate
    assert previous == pytest.approx(DRIFT, rel=0.0, abs=4e-4)


def test_buy_and_hold_bonus_decays_like_one_over_root_horizon() -> None:
    """E[log cosh(D/2)]/T ~ tau / sqrt(2 pi T) - log 2 / T for large T."""
    tau = relative_log_volatility(volatility_a=SIGMA, volatility_b=SIGMA, correlation=0.0)
    horizon = 5_000.0
    exact = buy_and_hold_log_bonus(relative_variance=tau**2 * horizon) / horizon
    asymptotic = tau / math.sqrt(2.0 * math.pi * horizon) - math.log(2.0) / horizon
    assert exact == pytest.approx(asymptotic, rel=5e-3)


# --------------------------------------------------------------------------------------
# Finite-horizon capture: the number that reframes the premise
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("correlation", "expected_gamma", "expected_bonus", "expected_advantage"),
    [
        (0.0, 0.010000, 0.00816855, 0.00183145),
        (0.3, 0.007000, 0.00599737, 0.00100263),
        (0.6, 0.004000, 0.00362557, 0.00037443),
        (0.9, 0.001000, 0.00097214, 0.00002786),
    ],
)
def test_thirty_year_capture_split_between_holding_and_rebalancing(
    correlation: float,
    expected_gamma: float,
    expected_bonus: float,
    expected_advantage: float,
) -> None:
    """At 30 years buy-and-hold captures 82% of gamma* for free at rho = 0.

    This is the finding that reframes the premise: the diversification bonus is real,
    but almost all of it accrues to simply *owning both assets*, not to trading them
    back to target. The rebalancing residual at rho = 0, sigma = 20% is 18.3 bp/yr.
    """
    tau = relative_log_volatility(
        volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
    )
    gamma = excess_growth_two_asset(
        volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
    )
    bonus = buy_and_hold_log_bonus(relative_variance=tau**2 * HORIZON) / HORIZON

    assert gamma == pytest.approx(expected_gamma, rel=0.0, abs=1e-12)
    assert bonus == pytest.approx(expected_bonus, rel=0.0, abs=1e-7)
    assert gamma - bonus == pytest.approx(expected_advantage, rel=0.0, abs=1e-7)


def test_buy_and_hold_growth_general_form_matches_the_cosh_identity() -> None:
    """The general Gaussian integral must reproduce E[log cosh(D/2)] in the symmetric case."""
    for correlation in (-0.4, 0.0, 0.55, 0.95):
        tau = relative_log_volatility(
            volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
        )
        general = buy_and_hold_growth_rate(
            growth_a=DRIFT,
            growth_b=DRIFT,
            volatility_a=SIGMA,
            volatility_b=SIGMA,
            correlation=correlation,
            horizon_years=HORIZON,
        )
        identity = DRIFT + buy_and_hold_log_bonus(relative_variance=tau**2 * HORIZON) / HORIZON
        assert general == pytest.approx(identity, rel=0.0, abs=1e-10)


def test_monthly_rebalancing_captures_essentially_all_of_the_continuous_bonus() -> None:
    """Rebalancing frequency is a second-order effect; horizon is a first-order one.

    Monthly rebalancing captures 99.92% of the continuous-time gamma* at sigma = 20%,
    rho = 0. Buy-and-hold over 30 years captures 82%. The gap between policies is
    therefore not about how often one trades.
    """
    tau = relative_log_volatility(volatility_a=SIGMA, volatility_b=SIGMA, correlation=0.0)
    gamma = tau**2 / 8.0
    monthly = discrete_rebalancing_growth_bonus(
        relative_log_variance=tau**2, interval_years=1.0 / 12.0
    )
    annual = discrete_rebalancing_growth_bonus(relative_log_variance=tau**2, interval_years=1.0)
    assert monthly / gamma == pytest.approx(0.9991685, rel=0.0, abs=1e-6)
    assert annual / gamma == pytest.approx(0.9902559, rel=0.0, abs=1e-6)
    assert monthly < gamma
    assert annual < monthly


def test_buy_and_hold_is_the_interval_equals_horizon_case_of_one_function() -> None:
    """Continuous, calendar and buy-and-hold are one function evaluated at three points."""
    tau = relative_log_volatility(volatility_a=SIGMA, volatility_b=SIGMA, correlation=0.0)
    as_interval = discrete_rebalancing_growth_bonus(
        relative_log_variance=tau**2, interval_years=HORIZON
    )
    as_bonus = buy_and_hold_log_bonus(relative_variance=tau**2 * HORIZON) / HORIZON
    assert as_interval == pytest.approx(as_bonus, rel=0.0, abs=1e-14)


# --------------------------------------------------------------------------------------
# Probabilities
# --------------------------------------------------------------------------------------


def test_probability_depends_on_horizon_and_volatility_only_through_their_product() -> None:
    """P is a function of c = gamma* T alone: the drift and the level of sigma cancel."""
    a = probability_rebalanced_beats_buy_and_hold(excess_growth=0.01, horizon_years=30.0)
    b = probability_rebalanced_beats_buy_and_hold(excess_growth=0.03, horizon_years=10.0)
    c = probability_rebalanced_beats_buy_and_hold(excess_growth=0.001, horizon_years=300.0)
    assert a == pytest.approx(b, rel=0.0, abs=1e-12)
    assert a == pytest.approx(c, rel=0.0, abs=1e-12)


def test_probability_floor_is_two_phi_one_minus_one() -> None:
    """As c -> 0 the probability tends to 68.27%, not to 50%.

    Independently derived: arccosh(e**c) -> sqrt(2c), so the argument of Phi tends to
    2 sqrt(2c) / sqrt(8c) = 1. A 68% win rate against buy-and-hold is therefore the
    floor of the null, and cannot be cited as evidence of anything.
    """
    assert pytest.approx(0.6826894921, rel=0.0, abs=1e-9) == MINIMUM_PROBABILITY
    tiny = probability_rebalanced_beats_buy_and_hold(excess_growth=1e-9, horizon_years=1.0)
    assert tiny == pytest.approx(MINIMUM_PROBABILITY, rel=0.0, abs=1e-6)


@pytest.mark.parametrize(
    ("correlation", "expected"),
    [(0.0, 0.7065892), (0.3, 0.6994897), (0.6, 0.6923260), (0.9, 0.6851067)],
)
def test_thirty_year_win_probability_barely_moves_with_correlation(
    correlation: float, expected: float
) -> None:
    """0.685 to 0.707 across the whole correlation range. The statistic is nearly inert."""
    gamma = excess_growth_two_asset(
        volatility_a=SIGMA, volatility_b=SIGMA, correlation=correlation
    )
    probability = probability_rebalanced_beats_buy_and_hold(
        excess_growth=gamma, horizon_years=HORIZON
    )
    assert probability == pytest.approx(expected, rel=0.0, abs=1e-6)


@pytest.mark.parametrize(
    ("confidence", "expected_years"),
    [(0.75, 87.589), (0.80, 163.1589), (0.90, 390.190), (0.95, 621.937)],
)
def test_horizon_for_rebalancing_confidence_is_measured_in_centuries(
    confidence: float, expected_years: float
) -> None:
    """At the most favourable plausible gamma* of 100 bp/yr, 90% needs 390 years.

    This is the quantitative refutation of "near definitively beat the market by
    rebalancing". The premium grows like T while the straddle it is short grows like
    sqrt(T), so confidence accrues, but at a rate no investor can use.
    """
    years = horizon_for_rebalancing_confidence(excess_growth=0.01, probability=confidence)
    assert years == pytest.approx(expected_years, rel=1e-5)
    round_trip = probability_rebalanced_beats_buy_and_hold(
        excess_growth=0.01, horizon_years=years
    )
    assert round_trip == pytest.approx(confidence, rel=0.0, abs=1e-10)


def test_horizon_below_the_probability_floor_is_refused() -> None:
    with pytest.raises(ValueError, match="probability must lie strictly between"):
        horizon_for_rebalancing_confidence(excess_growth=0.01, probability=0.6)


@pytest.mark.parametrize(
    ("drift_gap", "expected"),
    [
        (0.000, 0.650732),
        (0.005, 0.576775),
        (0.010, 0.500000),
        (0.020, 0.349268),
        (0.040, 0.122639),
    ],
)
def test_drift_gap_equal_to_excess_growth_is_an_exact_coin_flip(
    drift_gap: float, expected: float
) -> None:
    """P = Phi((gamma* - delta) sqrt(T / 2 gamma*)); at delta = gamma* it is 0.5 exactly.

    Independently derived from log V_reb - X_a = (gamma* - delta) T - D_0/2 with
    D_0 ~ N(0, tau**2 T) and tau**2 = 8 gamma*. The break-even is horizon-independent,
    which is the point: time does not rescue a portfolio whose components' true growth
    rates differ by more than its excess growth rate.
    """
    probability = probability_rebalanced_beats_single_asset(
        excess_growth=0.01, drift_gap=drift_gap, horizon_years=HORIZON
    )
    assert probability == pytest.approx(expected, rel=0.0, abs=1e-6)


def test_breakeven_drift_gap_is_horizon_free() -> None:
    gamma = 0.004
    assert breakeven_drift_gap(excess_growth=gamma) == gamma
    for horizon in (1.0, 30.0, 500.0):
        assert probability_rebalanced_beats_single_asset(
            excess_growth=gamma, drift_gap=gamma, horizon_years=horizon
        ) == pytest.approx(0.5, rel=0.0, abs=1e-14)


# --------------------------------------------------------------------------------------
# The short-straddle shape
# --------------------------------------------------------------------------------------


def test_advantage_is_a_short_straddle_capped_above_and_unbounded_below() -> None:
    """Mean 18 bp, median 56 bp, 5th percentile -191 bp, upside capped at gamma*."""
    result = rebalancing_advantage(excess_growth=0.01, horizon_years=HORIZON)
    assert result.mean == pytest.approx(0.00183145, rel=0.0, abs=1e-8)
    assert result.median == pytest.approx(0.00564368, rel=0.0, abs=1e-8)
    assert result.quantile_05 == pytest.approx(-0.01906422, rel=0.0, abs=1e-8)
    assert result.quantile_95 == pytest.approx(0.00996069, rel=0.0, abs=1e-8)
    assert result.probability_positive == pytest.approx(0.7065892, rel=0.0, abs=1e-7)
    # The upside is capped at gamma* and the downside is not capped at all.
    assert result.quantile_95 < 0.01
    assert rebalancing_advantage_quantile(
        excess_growth=0.01, horizon_years=HORIZON, quantile=0.001
    ) < -0.03


def test_median_advantage_exceeds_the_mean_advantage() -> None:
    """log cosh is convex in |D| and |D| is right-skewed, so E[.] > median[.].

    Reporting the expected-log advantage alone understates what a typical path sees;
    reporting the median alone hides the tail in which the untouched winner runs away.
    """
    result = rebalancing_advantage(excess_growth=0.01, horizon_years=HORIZON)
    assert result.median > result.mean
    assert result.median / result.mean == pytest.approx(3.0815, rel=1e-4)


def test_log_cosh_is_stable_and_matches_the_straddle_asymptote() -> None:
    assert log_cosh(0.0) == 0.0
    assert log_cosh(1e-6) == pytest.approx(0.5e-12, rel=1e-6)
    assert log_cosh(800.0) == pytest.approx(800.0 - math.log(2.0), rel=0.0, abs=1e-12)
    assert log_cosh(-3.0) == log_cosh(3.0)
    assert log_cosh(3.0) == pytest.approx(math.log(math.cosh(3.0)), rel=0.0, abs=1e-14)


# --------------------------------------------------------------------------------------
# Monte Carlo agreement
# --------------------------------------------------------------------------------------


def test_monte_carlo_reproduces_the_closed_form_advantage_within_three_standard_errors() -> None:
    """Seeded 20,000-path check at rho = 0 and rho = 0.9, monthly rebalancing.

    The tolerance is three simulated standard errors, computed by the simulation itself
    rather than chosen. The closed form is the authority; this asserts it is the right
    closed form for the model actually being simulated.
    """
    tau_squared = relative_log_volatility(
        volatility_a=SIGMA, volatility_b=SIGMA, correlation=0.0
    ) ** 2
    expected = discrete_rebalancing_growth_bonus(
        relative_log_variance=tau_squared, interval_years=1.0 / 12.0
    ) - buy_and_hold_log_bonus(relative_variance=tau_squared * HORIZON) / HORIZON

    result = simulate_growth_comparison(
        growth_rates=[DRIFT, DRIFT],
        volatilities=[SIGMA, SIGMA],
        correlation_matrix=[[1.0, 0.0], [0.0, 1.0]],
        weights=[0.5, 0.5],
        horizon_years=HORIZON,
        steps_per_year=12,
        rebalance_interval_steps=1,
        paths=20_000,
    )
    assert abs(result.advantage_mean - expected) < 3.0 * result.advantage_standard_error
    assert result.advantage_standard_error < 1e-4

    closed_form_probability = probability_rebalanced_beats_buy_and_hold(
        excess_growth=tau_squared / 8.0, horizon_years=HORIZON
    )
    assert (
        abs(result.probability_rebalanced_wins - closed_form_probability)
        < 4.0 * result.probability_standard_error
    )


def test_monte_carlo_median_advantage_matches_the_closed_form() -> None:
    result = simulate_growth_comparison(
        growth_rates=[DRIFT, DRIFT],
        volatilities=[SIGMA, SIGMA],
        correlation_matrix=[[1.0, 0.0], [0.0, 1.0]],
        weights=[0.5, 0.5],
        horizon_years=HORIZON,
        steps_per_year=12,
        rebalance_interval_steps=1,
        paths=20_000,
    )
    expected = rebalancing_advantage(excess_growth=0.01, horizon_years=HORIZON).median
    assert result.advantage_median == pytest.approx(expected, rel=0.0, abs=5e-4)


def test_vectorised_simulation_agrees_with_the_audited_core_rebalancer() -> None:
    """The blockwise path arithmetic must equal core.rebalance.simulate, path by path."""
    rng = np.random.default_rng(20260812)
    steps, horizon = 60, 5.0
    for interval in (1, 3, 12):
        log_returns = rng.normal(0.05 / 12.0, 0.2 / math.sqrt(12.0), size=(steps, 2))
        rebalanced, held = core_simulator_growth_rates(
            asset_log_returns=log_returns,
            weights=[0.5, 0.5],
            rebalance_interval_steps=interval,
            horizon_years=horizon,
        )
        blocks = steps // interval
        block_logs = log_returns.reshape(blocks, interval, 2).sum(axis=1)
        vector_rebalanced = float(
            np.log(np.exp(block_logs) @ np.array([0.5, 0.5])).sum() / horizon
        )
        vector_held = float(
            math.log(float(np.exp(block_logs.sum(axis=0)) @ np.array([0.5, 0.5]))) / horizon
        )
        assert vector_rebalanced == pytest.approx(rebalanced, rel=0.0, abs=1e-12)
        assert vector_held == pytest.approx(held, rel=0.0, abs=1e-12)


def test_simulation_is_deterministic_under_its_seed() -> None:
    kwargs = {
        "growth_rates": [DRIFT, DRIFT],
        "volatilities": [SIGMA, SIGMA],
        "correlation_matrix": [[1.0, 0.5], [0.5, 1.0]],
        "weights": [0.5, 0.5],
        "horizon_years": 10.0,
        "steps_per_year": 12,
        "paths": 2_000,
    }
    first = simulate_growth_comparison(**kwargs)  # type: ignore[arg-type]
    second = simulate_growth_comparison(**kwargs)  # type: ignore[arg-type]
    assert first.advantage_mean == second.advantage_mean
    assert first.probability_rebalanced_wins == second.probability_rebalanced_wins


def test_simulation_refuses_a_horizon_that_does_not_divide_into_whole_blocks() -> None:
    with pytest.raises(ValueError, match="do not divide evenly"):
        simulate_growth_comparison(
            growth_rates=[DRIFT, DRIFT],
            volatilities=[SIGMA, SIGMA],
            correlation_matrix=[[1.0, 0.0], [0.0, 1.0]],
            weights=[0.5, 0.5],
            horizon_years=10.0,
            steps_per_year=12,
            rebalance_interval_steps=7,
            paths=100,
        )


# --------------------------------------------------------------------------------------
# Realistic portfolios, not the toy
# --------------------------------------------------------------------------------------


def test_realistic_sixty_forty_leaves_two_and_a_half_basis_points_for_rebalancing() -> None:
    """sigma_e = 16%, sigma_b = 6%, rho = 0.1, w = 60/40 gives gamma* = 32.7 bp/yr.

    The toy's 100 bp/yr comes from two 20%-volatility uncorrelated assets, which no
    investable pair resembles. A realistic balanced portfolio has a third of it, and a
    30-year buy-and-hold captures 30.3 bp of the 32.7 for free, leaving **2.5 bp/yr** in
    the mean for rebalancing as a policy. The median advantage is 17.9 bp because the
    mean is dragged down by the paths on which equities run away from bonds.

    Note that the cosh identity does *not* apply here: it needs equal volatilities at
    50/50, so ``gamma_star = tau**2 / 8`` fails and the general Gaussian integral in
    :func:`buy_and_hold_growth_rate` is the correct route. Using the symmetric shortcut
    off its domain understates the residual by 41%, which is the kind of error that
    survives review because both numbers are small and neither is obviously wrong.
    """
    gamma = excess_growth_two_asset(
        volatility_a=0.16, volatility_b=0.06, correlation=0.1, weight_a=0.6
    )
    assert gamma == pytest.approx(0.0032736, rel=0.0, abs=1e-9)

    held = buy_and_hold_growth_rate(
        growth_a=DRIFT,
        growth_b=DRIFT,
        volatility_a=0.16,
        volatility_b=0.06,
        correlation=0.1,
        horizon_years=HORIZON,
        weight_a=0.6,
    )
    assert held - DRIFT == pytest.approx(0.00302902, rel=0.0, abs=1e-8)
    assert DRIFT + gamma - held == pytest.approx(0.00024458, rel=0.0, abs=1e-8)

    tau = relative_log_volatility(volatility_a=0.16, volatility_b=0.06, correlation=0.1)
    symmetric_shortcut = gamma - buy_and_hold_log_bonus(
        relative_variance=tau**2 * HORIZON
    ) / HORIZON
    assert symmetric_shortcut / (DRIFT + gamma - held) == pytest.approx(0.58914, rel=1e-4)


def test_equal_weight_stock_portfolio_has_a_large_excess_growth_rate() -> None:
    """100 equicorrelated stocks at sigma = 30%, rho = 0.25 give gamma* = 3.34%/yr.

    The largest excess growth rates available to a retail investor are inside the equity
    market, not across asset classes. But a cap-weighted index is itself the drifting
    portfolio, so capturing this means running equal weights against it, which is a size
    tilt in disguise; the framework's factor evidence governs whether that pays.
    """
    n, sigma, rho = 100, 0.30, 0.25
    covariance = np.full((n, n), rho * sigma**2)
    np.fill_diagonal(covariance, sigma**2)
    weights = np.full(n, 1.0 / n)
    gamma = excess_growth_rate(weights, covariance)
    closed_form = 0.5 * sigma**2 * (1.0 - rho) * (1.0 - 1.0 / n)
    assert gamma == pytest.approx(closed_form, rel=0.0, abs=1e-12)
    assert gamma == pytest.approx(0.0334125, rel=0.0, abs=1e-7)


def test_n_asset_simulation_agrees_with_the_rebalanced_closed_form() -> None:
    """For n assets the rebalanced growth rate is still sum w_i g_i + gamma*, exactly."""
    n, sigma, rho, drift = 8, 0.25, 0.3, 0.04
    covariance = np.full((n, n), rho * sigma**2)
    np.fill_diagonal(covariance, sigma**2)
    weights = np.full(n, 1.0 / n)
    gamma = excess_growth_rate(weights, covariance)

    result = simulate_growth_comparison(
        growth_rates=[drift] * n,
        volatilities=[sigma] * n,
        correlation_matrix=(np.full((n, n), rho) + np.eye(n) * (1.0 - rho)).tolist(),
        weights=weights.tolist(),
        horizon_years=HORIZON,
        steps_per_year=52,
        rebalance_interval_steps=1,
        paths=8_000,
    )
    # Weekly rebalancing captures gamma* to within a few tenths of a basis point.
    expected = drift + gamma
    standard_error = float(np.std(result.component_growth)) / math.sqrt(n) + 1e-4
    assert result.rebalanced_growth == pytest.approx(expected, rel=0.0, abs=4.0 * standard_error)
    # Buy-and-hold sits strictly between the components' growth and the rebalanced rate.
    assert drift < result.buy_and_hold_growth < result.rebalanced_growth


def test_normal_quantile_convention_used_by_the_advantage_quantiles() -> None:
    """Guard the |D| quantile mapping: q-quantile of the advantage uses 1 - q/2 of |D|."""
    gamma, horizon, quantile = 0.01, 30.0, 0.25
    scale = math.sqrt(8.0 * gamma * horizon)
    expected = gamma - log_cosh(scale * float(norm.ppf(1.0 - quantile / 2.0)) / 2.0) / horizon
    assert rebalancing_advantage_quantile(
        excess_growth=gamma, horizon_years=horizon, quantile=quantile
    ) == pytest.approx(expected, rel=0.0, abs=1e-15)


def test_more_assets_makes_buy_and_hold_capture_more_not_less() -> None:
    """The counter-intuitive result that decides the equal-weight question.

    With 100 equicorrelated stocks at sigma = 30%, rho = 0.25 the excess growth rate is
    334 bp/yr — an order of magnitude above anything available across asset classes. Yet
    over 30 years a buy-and-hold portfolio of the same 100 stocks captures 330 bp of it,
    leaving about 4 bp/yr for rebalancing. Dispersion across many assets makes the
    *untouched* portfolio's log-sum-exp large, so widening the universe raises the free
    component faster than it raises the total.

    The practical reading is that an equal-weight sleeve run against a cap-weighted index
    is not harvesting 334 bp of volatility; whatever it earns or loses is a size and
    value tilt, which the research framework's factor evidence governs, not this page.
    """
    n, sigma, rho, drift = 100, 0.30, 0.25, 0.05
    covariance = np.full((n, n), rho * sigma**2)
    np.fill_diagonal(covariance, sigma**2)
    gamma = excess_growth_rate(np.full(n, 1.0 / n), covariance)
    assert gamma == pytest.approx(0.0334125, rel=0.0, abs=1e-7)

    result = simulate_growth_comparison(
        growth_rates=[drift] * n,
        volatilities=[sigma] * n,
        correlation_matrix=(np.full((n, n), rho) + np.eye(n) * (1.0 - rho)).tolist(),
        weights=(np.full(n, 1.0 / n)).tolist(),
        horizon_years=HORIZON,
        steps_per_year=12,
        paths=4_000,
        chunk_size=250,
    )
    assert result.rebalanced_growth == pytest.approx(drift + gamma, rel=0.0, abs=5e-4)
    assert result.advantage_mean < 0.0010
    assert result.advantage_mean > 0.0
    # Buy-and-hold captures more than 95% of the excess growth rate at 30 years.
    assert (result.buy_and_hold_growth - drift) / gamma > 0.95


def _monthly_advantage_mean_by_quadrature(
    *, weight_a: float, tau_squared: float, horizon_years: float, steps_per_year: int
) -> float:
    """``E[advantage]`` for monthly rebalancing, by Gauss-Hermite quadrature.

    Derived from scratch, and the derivation is the point. Writing ``D_m = X_b,m -
    X_a,m`` for the step-by-step log-return difference and ``f(x) = log(w_a + w_b
    e**x)``:

        log V_reb(T) = X_a(T) + sum_m f(D_m)      (rebalance each step)
        log V_hold(T) = X_a(T) + f(sum_m D_m)     (never trade)

    ``X_a(T)`` cancels exactly, so the *entire* rebalancing advantage is a functional of
    one scalar iid sequence ``D_m ~ N(0, tau**2 / steps_per_year)`` — the individual
    volatilities, the drifts and the correlation enter only through ``tau``. Taking
    expectations,

        E[advantage] = steps_per_year x E[f(D_1)] - E[f(sum D_m)] / T

    and both expectations are one-dimensional Gaussian integrals. This routine uses
    Gauss-Hermite, which shares no code path with the adaptive quadrature inside
    :func:`buy_and_hold_growth_rate`.
    """
    nodes, weights = hermgauss(200)
    log_a, log_b = math.log(weight_a), math.log(1.0 - weight_a)

    def expectation(variance: float) -> float:
        z = nodes * math.sqrt(2.0 * variance)
        return float((weights / math.sqrt(math.pi)) @ np.logaddexp(log_a, log_b + z))

    per_step = steps_per_year * expectation(tau_squared / steps_per_year)
    whole = expectation(tau_squared * horizon_years) / horizon_years
    return per_step - whole


def test_sixty_forty_median_and_win_probability_are_pinned_by_simulation() -> None:
    """The 60/40 median advantage and win rate quoted in the synthesis.

    The closed-form quantile machinery needs equal volatilities at 50/50, so at 60/40 the
    median and the win probability come from the seeded simulation. Three literals below
    are therefore **reproducibility pins on one RNG stream**, and were nothing else
    asserted they would only ever confirm whatever the simulator did. The independent
    statements are the ones that follow them:

    * the *mean* has a closed form. By the reduction in
      :func:`_monthly_advantage_mean_by_quadrature` it is
      ``12 E[f(D_month)] - E[f(D_30y)]/30 = 0.00024376``. The seeded run reports
      0.000272, which is 1.7 standard errors above it — ordinary Monte Carlo noise, and
      exactly why the reproducibility pin's own tolerance (1e-5) must not be read as a
      claim about the quantity. The run's standard error is 1.65e-5, larger than that
      tolerance.
    * ``12 E[f(D_month)] = 0.00327278`` sits 0.08 bp/yr *below* ``gamma* = 0.0032736``.
      That gap is the cost of rebalancing monthly rather than continuously, and it is
      three hundred times smaller than the rebalancing advantage itself, which is why
      the continuous-time algebra is a legitimate stand-in for a monthly policy here.
    * the median and the win probability have no closed form, so they are checked
      against a 4,000,000-path simulation of the one-dimensional reduction above, run
      with a different generator seed: median 0.0017867 (se 2.5e-6) and
      P(win) 0.690069 (se 2.3e-4). Both agree with the seeded two-asset run to within
      its own standard error, so the reduction and the full simulator describe the same
      distribution.
    """
    result = simulate_growth_comparison(
        growth_rates=[DRIFT, DRIFT],
        volatilities=[0.16, 0.06],
        correlation_matrix=[[1.0, 0.1], [0.1, 1.0]],
        weights=[0.6, 0.4],
        horizon_years=HORIZON,
        steps_per_year=12,
        paths=60_000,
        chunk_size=3_000,
    )
    # Reproducibility pins: this seed, this path count, this generator.
    assert result.advantage_mean == pytest.approx(0.000272, rel=0.0, abs=1e-5)
    assert result.advantage_median == pytest.approx(0.001792, rel=0.0, abs=5e-5)
    assert result.probability_rebalanced_wins == pytest.approx(0.6923, rel=0.0, abs=2e-3)
    assert result.advantage_standard_error < 2e-5

    tau = relative_log_volatility(volatility_a=0.16, volatility_b=0.06, correlation=0.1)
    assert tau**2 == pytest.approx(0.02728, rel=0.0, abs=1e-15)
    analytic_mean = _monthly_advantage_mean_by_quadrature(
        weight_a=0.6, tau_squared=tau**2, horizon_years=HORIZON, steps_per_year=12
    )
    assert analytic_mean == pytest.approx(0.000243764322, rel=0.0, abs=1e-11)
    # The simulated mean must agree with it inside the run's OWN standard error, which
    # is the only tolerance that is not a tuning knob.
    assert abs(result.advantage_mean - analytic_mean) < 3.0 * result.advantage_standard_error
    assert result.advantage_standard_error == pytest.approx(1.65e-5, rel=0.0, abs=5e-7)

    # Monthly rebalancing captures all but 0.08 bp/yr of the continuous-time gamma*.
    held_excess = (
        buy_and_hold_growth_rate(
            growth_a=DRIFT,
            growth_b=DRIFT,
            volatility_a=0.16,
            volatility_b=0.06,
            correlation=0.1,
            horizon_years=HORIZON,
            weight_a=0.6,
        )
        - DRIFT
    )
    monthly_capture = analytic_mean + held_excess
    gamma = excess_growth_two_asset(
        volatility_a=0.16, volatility_b=0.06, correlation=0.1, weight_a=0.6
    )
    assert monthly_capture == pytest.approx(0.00327278188, rel=0.0, abs=1e-9)
    assert 0.0 < gamma - monthly_capture < 1e-6

    # Median and win rate, against an independent simulation of the scalar reduction,
    # judged against that sample's own standard errors rather than a tuned tolerance.
    sample = _reduced_advantage_sample(
        weight_a=0.6,
        tau_squared=tau**2,
        horizon_years=HORIZON,
        steps_per_year=12,
        paths=200_000,
        seed=987654321,
    )
    median = float(np.median(sample))
    win_rate = float((sample > 0.0).mean())
    median_se = 1.2533 * float(np.std(sample, ddof=1)) / math.sqrt(sample.size)
    win_se = math.sqrt(win_rate * (1.0 - win_rate) / sample.size)
    # The 4,000,000-path reference values quoted in the docstring.
    assert abs(median - 0.0017867) < 5.0 * median_se
    assert abs(win_rate - 0.690069) < 5.0 * win_se
    # And the seeded two-asset run describes the same distribution.
    assert abs(median - result.advantage_median) < 5.0 * median_se
    assert abs(win_rate - result.probability_rebalanced_wins) < 5.0 * (
        win_se + result.probability_standard_error
    )


def _reduced_advantage_sample(
    *,
    weight_a: float,
    tau_squared: float,
    horizon_years: float,
    steps_per_year: int,
    paths: int,
    seed: int,
    chunk: int = 20_000,
) -> FloatArray:
    """Per-path rebalancing advantage from the scalar reduction, in one dimension.

    ``advantage x T = sum_m f(D_m) - f(sum_m D_m)``; see
    :func:`_monthly_advantage_mean_by_quadrature` for the derivation. Two assets, a
    Cholesky factor and a 3-tensor of shocks all collapse to one array of iid normals,
    so this shares nothing with :func:`simulate_growth_comparison` except the model.
    """
    rng = np.random.default_rng(seed)
    steps = round(horizon_years * steps_per_year)
    log_a, log_b = math.log(weight_a), math.log(1.0 - weight_a)
    scale = math.sqrt(tau_squared / steps_per_year)
    out = np.empty(paths, dtype=np.float64)
    done = 0
    while done < paths:
        size = min(chunk, paths - done)
        d = rng.normal(0.0, scale, size=(size, steps))
        block = np.logaddexp(log_a, log_b + d).sum(axis=1)
        whole = np.logaddexp(log_a, log_b + d.sum(axis=1))
        out[done : done + size] = (block - whole) / horizon_years
        done += size
    return out
