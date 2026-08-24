"""Unit tests for the logic Experiment 003 adds on top of ``core`` and ``studies``.

Everything asserted here is either a closed form computed independently of the
implementation under test, a hand-computed fixture, or an invariant that must hold
for any correct portfolio accounting. Nothing is asserted against a number this
module produced.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.rebalance import (
    BuyAndHold,
    CalendarRebalance,
    CashFlowDirected,
    RebalancePolicy,
    RelativeThreshold,
)
from portfolio_edge.experiments.exp_003_rebalancing import (
    MONTHS_PER_YEAR,
    Panel,
    PolicySummary,
    _drop_window,
    _two_period_identity_check,
    analyse_pair,
    calendar_year_gross_returns,
    crra_certainty_equivalent,
    expected_log_cosh_half,
    ljung_box,
    probability_beats_with_drift,
    summarise_policy,
    variance_ratio,
)
from portfolio_edge.studies.volatility_harvesting import (
    buy_and_hold_log_bonus,
    excess_growth_two_asset,
    log_cosh,
    probability_rebalanced_beats_buy_and_hold,
    relative_log_volatility,
)

# --------------------------------------------------------------------------- #
# CRRA certainty equivalent
# --------------------------------------------------------------------------- #


def test_certainty_equivalent_of_a_constant_is_that_constant() -> None:
    constant = np.full(20, 1.07, dtype=np.float64)
    for gamma in (0.0, 1.0, 3.0, 8.0):
        assert crra_certainty_equivalent(constant, gamma=gamma) == pytest.approx(0.07)


def test_certainty_equivalent_at_gamma_zero_is_the_arithmetic_mean() -> None:
    """``gamma = 0`` is risk neutrality, so the certainty equivalent is the mean."""
    sample = np.array([1.2, 0.9, 1.05, 1.31], dtype=np.float64)
    assert crra_certainty_equivalent(sample, gamma=0.0) == pytest.approx(
        float(np.mean(sample)) - 1.0
    )


def test_certainty_equivalent_at_gamma_one_is_the_geometric_mean() -> None:
    sample = np.array([1.2, 0.9, 1.05, 1.31], dtype=np.float64)
    expected = math.exp(sum(math.log(x) for x in sample) / len(sample)) - 1.0
    assert crra_certainty_equivalent(sample, gamma=1.0) == pytest.approx(expected)


def test_certainty_equivalent_matches_a_hand_computed_fixture_at_gamma_three() -> None:
    """Computed with plain arithmetic, independently of the implementation.

    ``mean(G**-2) = (1 / 1.2**2 + 1 / 0.9**2) / 2`` and ``CE = mean**-0.5 - 1``.
    """
    expected = (0.5 * (1.0 / 1.2**2 + 1.0 / 0.9**2)) ** -0.5 - 1.0
    sample = np.array([1.2, 0.9], dtype=np.float64)
    assert crra_certainty_equivalent(sample, gamma=3.0) == pytest.approx(expected)
    # And the risk penalty is real: a risk-averse investor prefers less than the mean.
    assert crra_certainty_equivalent(sample, gamma=3.0) < float(np.mean(sample)) - 1.0


def test_certainty_equivalent_falls_as_risk_aversion_rises() -> None:
    sample = np.array([1.30, 0.85, 1.12, 0.97], dtype=np.float64)
    values = [crra_certainty_equivalent(sample, gamma=g) for g in (0.0, 1.0, 3.0, 6.0)]
    assert values == sorted(values, reverse=True)


def test_certainty_equivalent_refuses_insolvency() -> None:
    with pytest.raises(ValueError, match="insolvency"):
        crra_certainty_equivalent(np.array([1.1, 0.0]), gamma=3.0)


# --------------------------------------------------------------------------- #
# Annual blocks
# --------------------------------------------------------------------------- #


def test_calendar_year_blocks_compound_within_the_year_only() -> None:
    monthly = np.full(24, 0.01, dtype=np.float64)
    blocks = calendar_year_gross_returns(monthly)
    assert blocks.shape == (2,)
    assert blocks == pytest.approx(np.full(2, 1.01**12))


def test_calendar_year_blocks_refuse_a_partial_year() -> None:
    with pytest.raises(ValueError, match="whole number of 12-month blocks"):
        calendar_year_gross_returns(np.zeros(13, dtype=np.float64))


# --------------------------------------------------------------------------- #
# The drift-aware extension of the closed form
# --------------------------------------------------------------------------- #


def test_expected_log_cosh_reduces_to_the_repository_closed_form_at_zero_drift() -> None:
    """The zero-mean case is already solved in ``studies``; agreeing is the test."""
    for variance in (0.01, 0.25, 1.0, 4.0, 9.0):
        assert expected_log_cosh_half(
            mean=0.0, standard_deviation=math.sqrt(variance)
        ) == pytest.approx(buy_and_hold_log_bonus(relative_variance=variance), rel=1e-8)


def test_expected_log_cosh_is_exact_when_there_is_no_dispersion() -> None:
    assert expected_log_cosh_half(mean=1.7, standard_deviation=0.0) == pytest.approx(
        log_cosh(1.7 / 2.0)
    )


def test_expected_log_cosh_grows_with_the_drift_gap() -> None:
    """A drift gap costs the rebalancer, and costs more the larger it is."""
    values = [
        expected_log_cosh_half(mean=mean, standard_deviation=1.0)
        for mean in (0.0, 0.5, 1.0, 2.0, 4.0)
    ]
    assert values == sorted(values)


def test_probability_with_drift_reduces_to_the_symmetric_closed_form() -> None:
    for gamma_star in (0.001, 0.004, 0.01):
        for horizon in (5.0, 30.0, 200.0):
            tau = math.sqrt(8.0 * gamma_star)
            assert probability_beats_with_drift(
                excess_growth=gamma_star,
                horizon_years=horizon,
                drift_gap=0.0,
                relative_volatility=tau,
            ) == pytest.approx(
                probability_rebalanced_beats_buy_and_hold(
                    excess_growth=gamma_star, horizon_years=horizon
                ),
                rel=1e-9,
            )


def test_probability_with_drift_falls_as_the_drift_gap_widens() -> None:
    tau = math.sqrt(8.0 * 0.01)
    values = [
        probability_beats_with_drift(
            excess_growth=0.01, horizon_years=35.0, drift_gap=gap, relative_volatility=tau
        )
        for gap in (0.0, 0.01, 0.02, 0.05)
    ]
    assert values == sorted(values, reverse=True)


# --------------------------------------------------------------------------- #
# Variance ratio
# --------------------------------------------------------------------------- #


def _reference_variance_ratio(values: list[float], horizon: int) -> float:
    """Lo-MacKinlay VR(q) written out in plain Python, independently of the module."""
    n = len(values)
    mu = sum(values) / n
    variance_1 = sum((x - mu) ** 2 for x in values) / (n - 1)
    total = 0.0
    for start in range(n - horizon + 1):
        block = sum(values[start : start + horizon]) - horizon * mu
        total += block**2
    m = horizon * (n - horizon + 1) * (1.0 - horizon / n)
    return (total / m) / variance_1


def test_variance_ratio_at_horizon_one_is_exactly_one() -> None:
    rng = np.random.default_rng(11)
    result = variance_ratio(rng.normal(size=200), horizon=1)
    assert result.ratio == 1.0


def test_variance_ratio_matches_an_independent_implementation() -> None:
    rng = np.random.default_rng(20260813)
    series = rng.normal(0.004, 0.05, size=300)
    for horizon in (2, 3, 6, 12):
        assert variance_ratio(series, horizon=horizon).ratio == pytest.approx(
            _reference_variance_ratio(list(series), horizon), rel=1e-12
        )


def test_variance_ratio_is_near_one_for_a_random_walk() -> None:
    rng = np.random.default_rng(7)
    series = rng.normal(0.0, 0.04, size=5000)
    for horizon in (2, 6, 12):
        result = variance_ratio(series, horizon=horizon)
        assert abs(result.ratio - 1.0) < 0.1
        assert abs(result.z_heteroskedastic) < 3.0


def test_variance_ratio_exceeds_one_when_the_series_trends() -> None:
    """A positively autocorrelated series is what makes rebalancing lose."""
    rng = np.random.default_rng(3)
    noise = rng.normal(0.0, 0.02, size=4000)
    series = np.empty_like(noise)
    series[0] = noise[0]
    for t in range(1, series.size):
        series[t] = 0.6 * series[t - 1] + noise[t]
    result = variance_ratio(series, horizon=6)
    assert result.ratio > 1.5
    assert result.z_heteroskedastic > 3.0


def test_variance_ratio_falls_below_one_when_the_series_reverses() -> None:
    rng = np.random.default_rng(5)
    noise = rng.normal(0.0, 0.02, size=4000)
    series = np.empty_like(noise)
    series[0] = noise[0]
    for t in range(1, series.size):
        series[t] = -0.6 * series[t - 1] + noise[t]
    result = variance_ratio(series, horizon=6)
    assert result.ratio < 0.6
    assert result.z_heteroskedastic < -3.0


def test_variance_ratio_refuses_a_constant_series() -> None:
    with pytest.raises(ValueError, match="zero variance"):
        variance_ratio(np.full(50, 0.01), horizon=4)


# --------------------------------------------------------------------------- #
# Ljung-Box
# --------------------------------------------------------------------------- #


def test_ljung_box_matches_an_independent_implementation() -> None:
    rng = np.random.default_rng(99)
    series = rng.normal(size=200)
    n = series.size
    mean = float(np.mean(series))
    denominator = sum((x - mean) ** 2 for x in series)
    expected = 0.0
    for lag in range(1, 6):
        rho = sum(
            (series[t] - mean) * (series[t - lag] - mean) for t in range(lag, n)
        ) / denominator
        expected += rho**2 / (n - lag)
    expected *= n * (n + 2)
    statistic, _ = ljung_box(series, lags=5)
    assert statistic == pytest.approx(expected, rel=1e-12)


def test_ljung_box_does_not_reject_white_noise_and_does_reject_an_ar1() -> None:
    rng = np.random.default_rng(42)
    white = rng.normal(size=1000)
    assert ljung_box(white, lags=12)[1] > 0.05

    noise = rng.normal(size=1000)
    ar1 = np.empty_like(noise)
    ar1[0] = noise[0]
    for t in range(1, ar1.size):
        ar1[t] = 0.5 * ar1[t - 1] + noise[t]
    assert ljung_box(ar1, lags=12)[1] < 1e-6


# --------------------------------------------------------------------------- #
# Portfolio accounting invariants
# --------------------------------------------------------------------------- #


def _panel(rng: np.random.Generator, months: int = 240) -> Panel:
    returns = rng.normal(0.006, 0.045, size=(months, 3))
    periods = tuple(
        f"{1991 + index // MONTHS_PER_YEAR:04d}-{index % MONTHS_PER_YEAR + 1:02d}"
        for index in range(months)
    )
    return Panel(
        periods=periods,
        sleeves=("us_equity", "developed_ex_us_equity", "emerging_equity"),
        returns=returns,
        provenance=(),
        findings=(),
    )


_TARGET = np.array([0.6, 0.3, 0.1], dtype=np.float64)


def test_monthly_rebalancing_with_no_costs_is_constant_weight_compounding() -> None:
    rng = np.random.default_rng(1)
    panel = _panel(rng)
    flows = np.zeros(panel.months, dtype=np.float64)
    summary = summarise_policy(
        panel.returns,
        _TARGET,
        CalendarRebalance(1),
        policy_id="monthly",
        cost_basis="gross",
        cost_bp=0.0,
        cash_flows=flows,
        gamma=3.0,
    )
    expected = float(np.prod(1.0 + panel.returns @ _TARGET))
    assert summary.terminal_wealth == pytest.approx(expected, rel=1e-12)
    assert summary.annual_cost_percent == 0.0


def test_buy_and_hold_with_no_cash_flow_is_the_drifting_portfolio() -> None:
    rng = np.random.default_rng(2)
    panel = _panel(rng)
    flows = np.zeros(panel.months, dtype=np.float64)
    summary = summarise_policy(
        panel.returns,
        _TARGET,
        BuyAndHold(),
        policy_id="hold",
        cost_basis="gross",
        cost_bp=0.0,
        cash_flows=flows,
        gamma=3.0,
    )
    expected = float(np.dot(_TARGET, np.prod(1.0 + panel.returns, axis=0)))
    assert summary.terminal_wealth == pytest.approx(expected, rel=1e-12)
    assert summary.annual_turnover_percent == 0.0
    assert summary.rebalance_count == 0


def test_cash_flow_directed_with_no_cash_flow_is_buy_and_hold() -> None:
    """The specification's own hostile test, asserted rather than only reported."""
    rng = np.random.default_rng(3)
    panel = _panel(rng)
    flows = np.zeros(panel.months, dtype=np.float64)
    def run_one(policy: RebalancePolicy, label: str) -> PolicySummary:
        return summarise_policy(
            panel.returns,
            _TARGET,
            policy,
            policy_id=label,
            cost_basis="gross",
            cost_bp=8.0,
            cash_flows=flows,
            gamma=3.0,
        )

    directed = run_one(CashFlowDirected(), "directed")
    held = run_one(BuyAndHold(), "hold")
    assert directed.terminal_wealth == pytest.approx(held.terminal_wealth, rel=1e-15)
    assert directed.certainty_equivalent_percent == pytest.approx(
        held.certainty_equivalent_percent, rel=1e-12
    )


def test_costs_never_increase_wealth_for_any_policy() -> None:
    rng = np.random.default_rng(4)
    panel = _panel(rng)
    flows = np.full(panel.months, 0.05 / MONTHS_PER_YEAR, dtype=np.float64)
    policies: dict[str, RebalancePolicy] = {
        "hold": BuyAndHold(),
        "annual": CalendarRebalance(12),
        "monthly": CalendarRebalance(1),
        "threshold": RelativeThreshold(0.25),
        "directed": CashFlowDirected(),
    }
    for name, policy in policies.items():
        gross = summarise_policy(
            panel.returns,
            _TARGET,
            policy,
            policy_id=name,
            cost_basis="gross",
            cost_bp=0.0,
            cash_flows=flows,
            gamma=3.0,
        )
        net = summarise_policy(
            panel.returns,
            _TARGET,
            policy,
            policy_id=name,
            cost_basis="net-pessimistic",
            cost_bp=8.0,
            cash_flows=flows,
            gamma=3.0,
        )
        assert net.terminal_wealth <= gross.terminal_wealth + 1e-12
        assert net.annual_cost_percent >= 0.0


def test_monthly_rebalancing_tracks_the_target_more_closely_than_holding() -> None:
    rng = np.random.default_rng(6)
    panel = _panel(rng)
    flows = np.full(panel.months, 0.05 / MONTHS_PER_YEAR, dtype=np.float64)
    def run_one(policy: RebalancePolicy, label: str) -> PolicySummary:
        return summarise_policy(
            panel.returns,
            _TARGET,
            policy,
            policy_id=label,
            cost_basis="gross",
            cost_bp=0.0,
            cash_flows=flows,
            gamma=3.0,
        )

    monthly = run_one(CalendarRebalance(1), "monthly")
    held = run_one(BuyAndHold(), "hold")
    assert monthly.max_deviation_pp < held.max_deviation_pp
    assert monthly.mean_absolute_deviation_pp < held.mean_absolute_deviation_pp


def test_the_two_period_identity_reproduces_exactly() -> None:
    """``R_rebal - R_hold = -w1 w2 k1 k2`` (Rattray et al. 2020), to machine precision."""
    check = _two_period_identity_check()
    assert check["agrees"] is True
    assert isinstance(check["absolute_error"], float)
    assert check["absolute_error"] < 1e-15


# --------------------------------------------------------------------------- #
# Panel windowing
# --------------------------------------------------------------------------- #


def test_window_and_drop_window_are_complementary() -> None:
    panel = _panel(np.random.default_rng(8), months=120)
    kept = panel.window(start="1993-01", end="1995-12")
    dropped = _drop_window(panel, "1993-01", "1995-12")
    assert kept.months == 36
    assert dropped.months == panel.months - 36
    assert set(kept.periods) & set(dropped.periods) == set()


# --------------------------------------------------------------------------- #
# The theory, checked against data generated by the model it assumes
# --------------------------------------------------------------------------- #


def test_realised_excess_growth_matches_the_closed_form_on_simulated_gbm() -> None:
    """Under the model's own assumptions the realised gamma_star must match.

    This is the control for the experiment's first question. If real regional
    returns disagree with the closed form, this test establishes that the
    disagreement is in the data and not in the measurement: on lognormal returns
    with the assumed structure, the measured value converges on the predicted one.
    """
    rng = np.random.default_rng(20260813)
    months = 12_000
    sigma = 0.16 / math.sqrt(MONTHS_PER_YEAR)
    correlation = 0.3
    chol = np.linalg.cholesky(np.array([[1.0, correlation], [correlation, 1.0]]))
    shocks = (rng.normal(size=(months, 2)) @ chol.T) * sigma
    logs = shocks - 0.5 * sigma**2  # equal drifts, zero expected log growth
    returns = np.expm1(logs)
    panel = Panel(
        periods=tuple(
            f"{1000 + index // MONTHS_PER_YEAR:04d}-{index % MONTHS_PER_YEAR + 1:02d}"
            for index in range(months)
        ),
        sleeves=("a", "b"),
        returns=returns,
        provenance=(),
        findings=(),
    )
    result = analyse_pair(panel, "a", "b")

    predicted = excess_growth_two_asset(
        volatility_a=result.volatility_a,
        volatility_b=result.volatility_b,
        correlation=result.correlation,
        weight_a=0.5,
    )
    assert result.gamma_star_continuous == pytest.approx(predicted, rel=1e-12)
    # The discrete monthly capture is strictly below the continuous limit, and the
    # realised value sits on the discrete one because the simulation rebalances
    # monthly. One basis point per year is 1e-4.
    assert result.gamma_star_discrete_monthly < result.gamma_star_continuous
    assert result.gamma_star_realised == pytest.approx(
        result.gamma_star_discrete_monthly, abs=2e-4
    )


def test_the_relative_volatility_used_is_the_one_the_closed_form_defines() -> None:
    rng = np.random.default_rng(12)
    panel = _panel(rng, months=600)
    result = analyse_pair(panel, "us_equity", "emerging_equity")
    assert result.relative_volatility == pytest.approx(
        relative_log_volatility(
            volatility_a=result.volatility_a,
            volatility_b=result.volatility_b,
            correlation=result.correlation,
        )
    )
