"""Unit tests for the statistics Experiment 010 adds.

Every expected value here is computed in this file, from first principles, never
by calling the function under test. The marginal-growth decomposition carries a
table of closed-form cases at the top; a case derived independently of this
implementation is a one-line addition to that table, and if it disagrees with the
implementation the closed form wins.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from statistics import NormalDist

import numpy as np
import pytest

from portfolio_edge.experiments.exp_010_marginal_sleeve_value import (
    ASSET_NAMES,
    BASE_PORTFOLIO_IDS,
    ENTRY_POINT,
    FUNDING_LEG_IDS,
    MarginalSleeveValueError,
    _annual_gross_matrix,
    _certainty_equivalent_rows,
    _grid,
    _index_of,
    _mask_for,
    _weights_for,
    _whole_year_mask,
    bond_total_return_from_yield,
    build_registry,
    certainty_equivalent_annual,
    closed_form_optimum,
    default_specification_path,
    exact_growth_derivative,
    high_water_mark_performance_fee,
    minimum_detectable_effect,
    moment_growth_decomposition,
    optimal_long_only_weight,
    par_bond_risk,
    run_constant_weights,
)
from portfolio_edge.experiments.specification import JsonValue, load_specification
from tests.unit.test_marginal_sleeve_value import (
    BASE_DRIFT,
    BASE_VARIANCE,
    MARGINAL_VALUE_FIXTURES,
    WEIGHT_CAP,
    SleeveCase,
)

# --------------------------------------------------------------------------- #
# Closed-form fixtures for the marginal-growth decomposition
#
# Each case states the five monthly moments and the expected ANNUALISED outputs,
# worked out by hand from
#
#     alpha  = 12 (mu_i - mu_f)
#     credit = 12 gamma (sigma_fp - sigma_ip)
#
# and, where the funding leg is the portfolio itself, cross-checked against the
# equivalent form gamma sigma_p^2 (1 - beta_ip). A fixture derived independently
# of the implementation is added here as one more entry.
# --------------------------------------------------------------------------- #

CLOSED_FORM_CASES: tuple[dict[str, float | str], ...] = (
    {
        "name": "equity sleeve funded pro rata, beta above one, credit negative",
        "mean_sleeve": 0.010,
        "mean_funding": 0.008,
        "cov_sleeve_portfolio": 0.0020,
        "cov_funding_portfolio": 0.0018,
        "variance_sleeve": 0.0036,
        "variance_portfolio": 0.0018,
        "gamma": 1.0,
        # 12 * (0.010 - 0.008)
        "alpha_term": 0.024,
        # 12 * 1 * (0.0018 - 0.0020)
        "credit_term": -0.0024,
        "beta": 0.0020 / 0.0018,
    },
    {
        "name": "cash sleeve, zero covariance, credit is exactly gamma sigma_p squared",
        "mean_sleeve": 0.002,
        "mean_funding": 0.009,
        "cov_sleeve_portfolio": 0.0,
        "cov_funding_portfolio": 0.0018,
        "variance_sleeve": 0.0,
        "variance_portfolio": 0.0018,
        "gamma": 3.0,
        "alpha_term": 12.0 * (0.002 - 0.009),
        "credit_term": 3.0 * 12.0 * 0.0018,
        "beta": 0.0,
    },
    {
        "name": "the sleeve IS the portfolio: nothing changes, both terms vanish",
        "mean_sleeve": 0.009,
        "mean_funding": 0.009,
        "cov_sleeve_portfolio": 0.0018,
        "cov_funding_portfolio": 0.0018,
        "variance_sleeve": 0.0018,
        "variance_portfolio": 0.0018,
        "gamma": 3.0,
        "alpha_term": 0.0,
        "credit_term": 0.0,
        "beta": 1.0,
    },
    {
        "name": "negative-beta sleeve funded from cash, credit larger than sigma_p squared",
        "mean_sleeve": 0.006,
        "mean_funding": 0.0025,
        "cov_sleeve_portfolio": -0.0004,
        "cov_funding_portfolio": 0.0,
        "variance_sleeve": 0.0012,
        "variance_portfolio": 0.0018,
        "gamma": 1.0,
        "alpha_term": 12.0 * (0.006 - 0.0025),
        "credit_term": 12.0 * 0.0004,
        "beta": -0.0004 / 0.0018,
    },
)


@pytest.mark.parametrize("case", CLOSED_FORM_CASES, ids=lambda case: str(case["name"]))
def test_the_decomposition_matches_its_closed_form(case: Mapping[str, float | str]) -> None:
    result = moment_growth_decomposition(
        mean_sleeve=float(case["mean_sleeve"]),
        mean_funding=float(case["mean_funding"]),
        cov_sleeve_portfolio=float(case["cov_sleeve_portfolio"]),
        cov_funding_portfolio=float(case["cov_funding_portfolio"]),
        variance_sleeve=float(case["variance_sleeve"]),
        variance_portfolio=float(case["variance_portfolio"]),
        gamma=float(case["gamma"]),
    )
    assert result.alpha_term == pytest.approx(float(case["alpha_term"]), rel=1e-12, abs=1e-15)
    assert result.credit_term == pytest.approx(float(case["credit_term"]), rel=1e-12, abs=1e-15)
    assert result.moment_total == pytest.approx(
        float(case["alpha_term"]) + float(case["credit_term"]), rel=1e-12, abs=1e-15
    )
    assert result.beta_sleeve_to_portfolio == pytest.approx(float(case["beta"]), rel=1e-12)


def test_pro_rata_funding_collapses_the_credit_to_gamma_sigma_squared_times_one_minus_beta() -> (
    None
):
    """With ``f = p`` the credit must be ``gamma sigma_p^2 (1 - beta_ip)`` exactly.

    Computed here from the definition rather than from the function, because this
    identity is the whole reason the experiment exists.
    """
    variance_portfolio = 0.0021
    cov = 0.0027
    gamma = 3.0
    result = moment_growth_decomposition(
        mean_sleeve=0.011,
        mean_funding=0.009,
        cov_sleeve_portfolio=cov,
        cov_funding_portfolio=variance_portfolio,
        variance_sleeve=0.0049,
        variance_portfolio=variance_portfolio,
        gamma=gamma,
    )
    beta = cov / variance_portfolio
    annualised_variance = 12.0 * variance_portfolio
    assert result.credit_term == pytest.approx(gamma * annualised_variance * (1.0 - beta))
    assert beta > 1.0
    assert result.credit_term < 0.0, "a beta above one must produce a NEGATIVE credit"


def test_the_credit_is_annualised_by_exactly_the_periods_per_year() -> None:
    """Monthly moments in, annual rates out. Twelve times, once, not twice."""
    arguments: dict[str, float] = {
        "mean_sleeve": 0.010,
        "mean_funding": 0.008,
        "cov_sleeve_portfolio": 0.0020,
        "cov_funding_portfolio": 0.0018,
        "variance_sleeve": 0.0036,
        "variance_portfolio": 0.0018,
        "gamma": 2.0,
    }
    monthly = moment_growth_decomposition(**arguments, periods_per_year=12)
    per_period = moment_growth_decomposition(**arguments, periods_per_year=1)
    assert monthly.alpha_term == pytest.approx(12.0 * per_period.alpha_term)
    assert monthly.credit_term == pytest.approx(12.0 * per_period.credit_term)
    # Volatility annualises by the SQUARE ROOT of the same factor.
    assert monthly.sleeve_volatility == pytest.approx(
        math.sqrt(12.0) * per_period.sleeve_volatility
    )
    assert monthly.portfolio_volatility == pytest.approx(
        math.sqrt(12.0) * per_period.portfolio_volatility
    )


def test_the_correlation_derivative_of_the_credit_uses_annualised_volatilities() -> None:
    """``d(credit)/d(rho) = -gamma sigma_i sigma_p`` with both volatilities annual."""
    variance_sleeve, variance_portfolio, gamma = 0.0036, 0.0018, 3.0
    result = moment_growth_decomposition(
        mean_sleeve=0.01,
        mean_funding=0.01,
        cov_sleeve_portfolio=0.002,
        cov_funding_portfolio=0.0018,
        variance_sleeve=variance_sleeve,
        variance_portfolio=variance_portfolio,
        gamma=gamma,
    )
    expected = -gamma * math.sqrt(12.0 * variance_sleeve) * math.sqrt(12.0 * variance_portfolio)
    assert result.credit_derivative_per_correlation == pytest.approx(expected)
    # And it agrees with a finite difference of the credit through the covariance.
    step = 0.01
    covariance_step = step * math.sqrt(variance_sleeve * variance_portfolio)
    moved = moment_growth_decomposition(
        mean_sleeve=0.01,
        mean_funding=0.01,
        cov_sleeve_portfolio=0.002 + covariance_step,
        cov_funding_portfolio=0.0018,
        variance_sleeve=variance_sleeve,
        variance_portfolio=variance_portfolio,
        gamma=gamma,
    )
    assert (moved.credit_term - result.credit_term) / step == pytest.approx(expected)


def test_a_zero_variance_portfolio_yields_no_beta_rather_than_a_division() -> None:
    result = moment_growth_decomposition(
        mean_sleeve=0.01,
        mean_funding=0.002,
        cov_sleeve_portfolio=0.0,
        cov_funding_portfolio=0.0,
        variance_sleeve=0.004,
        variance_portfolio=0.0,
        gamma=1.0,
    )
    assert math.isnan(result.beta_sleeve_to_portfolio)
    assert math.isnan(result.correlation_sleeve_to_portfolio)
    assert result.credit_term == 0.0


def test_a_negative_variance_is_refused() -> None:
    with pytest.raises(ValueError, match="variances must be non-negative"):
        moment_growth_decomposition(
            mean_sleeve=0.0,
            mean_funding=0.0,
            cov_sleeve_portfolio=0.0,
            cov_funding_portfolio=0.0,
            variance_sleeve=-1.0,
            variance_portfolio=0.001,
        )


# --------------------------------------------------------------------------- #
# The INDEPENDENTLY DERIVED fixtures
#
# ``tests/unit/test_marginal_sleeve_value.py`` is a second derivation of the same
# algebra, written without sight of this implementation and importing nothing from
# it. Its literals are checked there by exact rational arithmetic, a brute-force
# grid and a seeded Monte Carlo. They are consumed here as the authority: if these
# tests fail, the closed form wins and the disagreement is a finding, never a
# tolerance to loosen.
#
# Its convention is annual, continuous-time, pro-rata funded, so the moments are
# passed with ``periods_per_year = 1`` and ``gamma = 1``.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda case: case.name)
def test_the_decomposition_reproduces_the_independent_derivation(case: SleeveCase) -> None:
    result = moment_growth_decomposition(
        mean_sleeve=case.drift,
        mean_funding=BASE_DRIFT,
        cov_sleeve_portfolio=case.covariance,
        cov_funding_portfolio=BASE_VARIANCE,
        variance_sleeve=case.volatility**2,
        variance_portfolio=BASE_VARIANCE,
        gamma=1.0,
        periods_per_year=1,
    )
    assert result.alpha_term == pytest.approx(case.standalone, rel=1e-12, abs=1e-15)
    assert result.credit_term == pytest.approx(case.credit, rel=1e-12, abs=1e-15)
    assert result.moment_total == pytest.approx(case.marginal_growth, rel=1e-12, abs=1e-15)
    assert result.beta_sleeve_to_portfolio == pytest.approx(case.beta, rel=1e-12, abs=1e-15)
    if case.volatility > 0.0:
        assert result.correlation_sleeve_to_portfolio == pytest.approx(
            case.correlation, rel=1e-12, abs=1e-15
        )
    else:
        # A zero-variance sleeve has no correlation. The fixture carries 0.0 as the
        # INPUT that makes the covariance vanish; this implementation reports the
        # quantity as undefined rather than as zero, which is the stricter reading.
        assert math.isnan(result.correlation_sleeve_to_portfolio)


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda case: case.name)
def test_the_closed_form_optimum_reproduces_the_independent_derivation(
    case: SleeveCase,
) -> None:
    analytic = closed_form_optimum(
        case.marginal_growth, case.relative_variance, cap=WEIGHT_CAP
    )
    if case.optimal_weight is None:
        assert analytic.degenerate
        return
    assert not analytic.degenerate
    assert analytic.interior_weight == pytest.approx(case.optimal_weight, rel=1e-12, abs=1e-15)
    assert analytic.interior_gain == pytest.approx(case.optimal_gain, rel=1e-12, abs=1e-15)
    assert case.capped_weight is not None and case.capped_gain is not None
    assert analytic.constrained_weight == pytest.approx(
        case.capped_weight, rel=1e-12, abs=1e-15
    )
    assert analytic.constrained_gain == pytest.approx(case.capped_gain, rel=1e-12, abs=1e-15)


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda case: case.name)
def test_the_numerical_optimiser_finds_the_analytic_optimum_on_the_exact_curve(
    case: SleeveCase,
) -> None:
    """Feed the optimiser the exact quadratic and it must land where the algebra says.

    ``g(w) - g(0) = w D - 0.5 w^2 tau^2`` on a 0.005 grid over ``[0, 0.20]``. This
    is the check that the constrained search itself is right, separately from the
    data it is normally fed.
    """
    step = 0.005
    weights = _linear_grid(WEIGHT_CAP, step)
    gains = [
        100.0 * (weight * case.marginal_growth - 0.5 * weight**2 * case.relative_variance)
        for weight in weights
    ]
    if case.capped_weight is None or case.capped_gain is None:
        # The degenerate clone: a flat curve, refused by the closed form and
        # therefore not a case the optimiser is asked to answer.
        assert case.relative_variance == 0.0
        return
    surface = optimal_long_only_weight(weights, gains, cap=WEIGHT_CAP, materiality=0.30)
    # The grid can only resolve the optimum to half a step.
    assert abs(surface.optimal_weight - case.capped_weight) <= step / 2.0 + 1e-12
    assert surface.optimal_gain == pytest.approx(100.0 * case.capped_gain, abs=1e-6)
    if case.capped_weight == 0.0:
        assert surface.at_lower_boundary, "clause (c) must fire on a sleeve worth nothing"


def test_a_clone_of_the_funding_leg_is_refused_rather_than_answered() -> None:
    """``tau^2 = 0`` is a genuine degeneracy, not a number to return."""
    analytic = closed_form_optimum(0.0, 0.0, cap=0.20)
    assert analytic.degenerate
    assert math.isnan(analytic.interior_weight)
    assert analytic.constrained_gain == 0.0


def test_a_zero_alpha_sleeve_can_never_add_more_than_half_the_base_variance() -> None:
    """The ceiling from the independent derivation: ``g(w*) - g(0) <= sigma_p^2 / 2``.

    Checked across every zero-alpha fixture and against a dense sweep of the
    correlation, because it is the number that bounds the whole diversification
    story: at a 10% portfolio volatility it is 50 basis points a year, and it is
    reached only by a perfect hedge.
    """
    ceiling = BASE_VARIANCE / 2.0
    for case in MARGINAL_VALUE_FIXTURES:
        if case.standalone != 0.0 or case.optimal_gain is None:
            continue
        assert case.optimal_gain <= ceiling + 1e-15
    volatility = 0.20
    for correlation in np.linspace(-0.999, 0.999, 401):
        covariance = float(correlation) * volatility * math.sqrt(BASE_VARIANCE)
        marginal = BASE_VARIANCE - covariance
        relative = volatility**2 - 2.0 * covariance + BASE_VARIANCE
        analytic = closed_form_optimum(marginal, relative, cap=1e9)
        assert analytic.interior_gain <= ceiling + 1e-12


# --------------------------------------------------------------------------- #
# The exact derivative
# --------------------------------------------------------------------------- #


def test_the_exact_derivative_matches_a_hand_enumerated_expectation() -> None:
    """``12 E[(r_i - r_f)/(1 + r_p)]`` on a two-point sample, summed by hand."""
    sleeve = np.array([0.20, -0.10])
    funding = np.array([0.05, 0.00])
    portfolio = np.array([0.10, -0.05])
    expected = 12.0 * 0.5 * ((0.20 - 0.05) / 1.10 + (-0.10 - 0.00) / 0.95)
    assert exact_growth_derivative(sleeve, funding, portfolio) == pytest.approx(
        expected, rel=1e-12
    )


def test_the_exact_derivative_is_the_slope_of_the_realised_growth_rate() -> None:
    """A finite difference of the realised log growth rate reproduces it.

    This is the check that the closed form describes the portfolio actually built
    rather than an idealised one: the growth rate is recomputed at two nearby
    weights with plain NumPy and differenced.
    """
    rng = np.random.default_rng(909)
    n = 4000
    portfolio = rng.normal(0.008, 0.04, size=n)
    sleeve = rng.normal(0.005, 0.05, size=n)
    funding = portfolio.copy()

    def growth(weight: float) -> float:
        return float(np.mean(np.log1p(portfolio + weight * (sleeve - funding))))

    step = 1e-6
    numerical = 12.0 * (growth(step) - growth(-step)) / (2.0 * step)
    assert exact_growth_derivative(sleeve, funding, portfolio) == pytest.approx(
        numerical, rel=1e-6
    )


def test_the_two_moment_split_approximates_the_exact_derivative() -> None:
    """At realistic monthly magnitudes the residual is small, and it is REPORTED."""
    rng = np.random.default_rng(4242)
    n = 20_000
    market = rng.normal(0.007, 0.043, size=n)
    portfolio = market
    sleeve = 0.8 * market + rng.normal(0.001, 0.02, size=n)
    covariance = np.cov(np.column_stack([sleeve, portfolio, portfolio]), rowvar=False, ddof=1)
    decomposition = moment_growth_decomposition(
        mean_sleeve=float(np.mean(sleeve)),
        mean_funding=float(np.mean(portfolio)),
        cov_sleeve_portfolio=float(covariance[0, 1]),
        cov_funding_portfolio=float(covariance[1, 1]),
        variance_sleeve=float(covariance[0, 0]),
        variance_portfolio=float(covariance[1, 1]),
        gamma=1.0,
    )
    exact = exact_growth_derivative(sleeve, portfolio, portfolio)
    # Third-moment sized: well under a tenth of a percentage point a year.
    assert abs(exact - decomposition.moment_total) < 0.001


def test_the_exact_derivative_refuses_an_insolvent_portfolio() -> None:
    with pytest.raises(ValueError, match="non-positive wealth"):
        exact_growth_derivative(
            np.array([0.1, 0.1]), np.array([0.0, 0.0]), np.array([0.0, -1.0])
        )


def test_the_exact_derivative_refuses_misaligned_series() -> None:
    with pytest.raises(ValueError, match="one-dimensional and aligned"):
        exact_growth_derivative(np.array([0.1]), np.array([0.0, 0.0]), np.array([0.0, 0.0]))


# --------------------------------------------------------------------------- #
# Minimum detectable effect
# --------------------------------------------------------------------------- #


def test_the_detection_constants_are_the_standard_normal_quantiles() -> None:
    """Checked against the standard library's own inverse normal, not a literal."""
    normal = NormalDist()
    expected = normal.inv_cdf(0.95) + normal.inv_cdf(0.80)
    assert minimum_detectable_effect(1.0) == pytest.approx(expected, rel=1e-12)
    assert expected == pytest.approx(2.486474860524386, rel=1e-12)


def test_the_detectable_effect_is_linear_in_the_standard_error() -> None:
    assert minimum_detectable_effect(2.0) == pytest.approx(2.0 * minimum_detectable_effect(1.0))
    assert minimum_detectable_effect(0.0) == 0.0


def test_a_negative_standard_error_is_refused() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        minimum_detectable_effect(-1.0)


# --------------------------------------------------------------------------- #
# Certainty equivalent
# --------------------------------------------------------------------------- #


def test_certainty_equivalent_matches_an_independently_computed_value() -> None:
    gross = np.array([1.10, 0.90])
    expected = (0.5 * (1.10**-2 + 0.90**-2)) ** (-0.5) - 1.0
    assert certainty_equivalent_annual(gross, gamma=3.0) == pytest.approx(expected, rel=1e-12)


def test_certainty_equivalent_at_gamma_one_is_the_geometric_mean() -> None:
    gross = np.array([1.2, 0.9, 1.05])
    expected = (1.2 * 0.9 * 1.05) ** (1.0 / 3.0) - 1.0
    assert certainty_equivalent_annual(gross, gamma=1.0) == pytest.approx(expected, rel=1e-12)


def test_certainty_equivalent_refuses_insolvency_rather_than_returning_a_number() -> None:
    with pytest.raises(ValueError, match="insolvency"):
        certainty_equivalent_annual(np.array([1.1, 0.0]), gamma=3.0)


def test_the_vectorised_certainty_equivalent_matches_the_scalar_one() -> None:
    rng = np.random.default_rng(11)
    monthly = rng.normal(0.006, 0.03, size=(4, 36))
    for gamma in (1.0, 3.0):
        rows = _certainty_equivalent_rows(monthly, gamma=gamma)
        for index in range(monthly.shape[0]):
            scalar = certainty_equivalent_annual(
                _annual_gross_matrix(monthly[index]), gamma=gamma
            )
            assert rows[index] == pytest.approx(scalar, rel=1e-12)


def test_annual_blocks_compound_and_reject_a_partial_year() -> None:
    monthly = np.full(24, 0.01)
    annual = _annual_gross_matrix(monthly)
    assert annual.shape == (2,)
    assert annual[0] == pytest.approx(1.01**12)
    with pytest.raises(ValueError, match="whole number of 12-month blocks"):
        _annual_gross_matrix(np.zeros(13))


# --------------------------------------------------------------------------- #
# Constant-weight realisation
# --------------------------------------------------------------------------- #


def _reference_constant_weights(
    target: np.ndarray, returns: np.ndarray, one_way_bps: float
) -> tuple[np.ndarray, np.ndarray]:
    """A plain, obviously-correct loop, written here and not imported."""
    periods = returns.shape[0]
    portfolio = np.empty(periods)
    cost = np.empty(periods)
    drifted = target.copy()
    for index in range(periods):
        traded = float(np.sum(np.abs(target - drifted)))
        cost[index] = traded * one_way_bps / 1e4
        portfolio[index] = float(np.dot(target, returns[index])) - cost[index]
        grown = target * (1.0 + returns[index])
        total = float(np.sum(grown))
        drifted = grown / total if total > 0.0 else target.copy()
    return portfolio, cost


def test_the_vectorised_weight_path_matches_a_plain_loop() -> None:
    rng = np.random.default_rng(77)
    returns = rng.normal(0.005, 0.04, size=(60, 4))
    target = np.array([0.5, 0.2, 0.2, 0.1])
    expected_returns, expected_cost = _reference_constant_weights(target, returns, 8.0)
    realised, _, cost = run_constant_weights(target, returns, one_way_bps=8.0)
    assert np.allclose(realised, expected_returns, atol=1e-15)
    assert np.allclose(cost, expected_cost, atol=1e-15)


def test_a_costless_constant_weight_path_is_the_weighted_return() -> None:
    returns = np.array([[0.02, -0.01], [0.00, 0.03]])
    target = np.array([0.6, 0.4])
    realised, _, cost = run_constant_weights(target, returns, one_way_bps=0.0)
    assert np.allclose(realised, returns @ target)
    assert np.all(cost == 0.0)


def test_a_path_whose_assets_move_together_never_trades() -> None:
    """Identical returns leave the weights where they were, so nothing is traded."""
    returns = np.tile(np.array([0.01, -0.02, 0.03])[:, None], (1, 3))
    target = np.array([0.2, 0.3, 0.5])
    _, turnover, cost = run_constant_weights(target, returns, one_way_bps=50.0)
    assert np.allclose(turnover, 0.0, atol=1e-15)
    assert np.allclose(cost, 0.0, atol=1e-15)


def test_costs_never_increase_a_realised_return() -> None:
    rng = np.random.default_rng(5)
    returns = rng.normal(0.004, 0.05, size=(48, 3))
    target = np.array([0.5, 0.3, 0.2])
    free, _, _ = run_constant_weights(target, returns, one_way_bps=0.0)
    charged, _, cost = run_constant_weights(target, returns, one_way_bps=10.0)
    assert np.all(charged <= free + 1e-15)
    assert np.all(cost >= 0.0)


def test_the_cost_is_proportional_to_the_spread() -> None:
    rng = np.random.default_rng(6)
    returns = rng.normal(0.004, 0.05, size=(24, 3))
    target = np.array([0.5, 0.3, 0.2])
    _, _, cheap = run_constant_weights(target, returns, one_way_bps=2.0)
    _, _, dear = run_constant_weights(target, returns, one_way_bps=8.0)
    assert np.allclose(dear, 4.0 * cheap)


def test_a_wipeout_holds_the_target_instead_of_inventing_drifted_weights() -> None:
    returns = np.array([[-1.0, -1.0], [0.01, 0.02]])
    target = np.array([0.5, 0.5])
    realised, turnover, _ = run_constant_weights(target, returns, one_way_bps=8.0)
    assert realised[0] == pytest.approx(-1.0)
    assert turnover[1] == pytest.approx(0.0)


def test_a_short_weight_is_realised_rather_than_clipped() -> None:
    """Funding a sleeve out of a leg that cannot carry it goes short, visibly."""
    returns = np.array([[0.02, 0.01]])
    target = np.array([-0.1, 1.1])
    realised, _, _ = run_constant_weights(target, returns, one_way_bps=0.0)
    assert realised[0] == pytest.approx(-0.1 * 0.02 + 1.1 * 0.01)


def test_a_mismatched_weight_vector_is_refused() -> None:
    with pytest.raises(ValueError, match="match asset_returns"):
        run_constant_weights(np.array([0.5, 0.5]), np.zeros((3, 4)), one_way_bps=0.0)


def test_a_negative_spread_is_refused() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        run_constant_weights(np.array([1.0]), np.zeros((2, 1)), one_way_bps=-1.0)


# --------------------------------------------------------------------------- #
# The constrained optimum and its flatness
# --------------------------------------------------------------------------- #


def _linear_grid(cap: float, step: float) -> list[float]:
    count = round(cap / step)
    return [step * index for index in range(count + 1)]


def test_a_monotonically_rising_surface_optimises_at_the_cap() -> None:
    weights = _linear_grid(0.20, 0.005)
    gains = [10.0 * weight for weight in weights]
    surface = optimal_long_only_weight(weights, gains, cap=0.20, materiality=0.30)
    assert surface.optimal_weight == pytest.approx(0.20)
    assert surface.at_upper_boundary
    assert not surface.at_lower_boundary
    assert surface.optimal_gain == pytest.approx(2.0)
    # An exactly linear surface has zero deviation from its own chord.
    assert surface.max_deviation_from_linear == pytest.approx(0.0, abs=1e-12)


def test_a_monotonically_falling_surface_optimises_at_zero_which_is_clause_c() -> None:
    weights = _linear_grid(0.20, 0.005)
    gains = [-10.0 * weight for weight in weights]
    surface = optimal_long_only_weight(weights, gains, cap=0.20, materiality=0.30)
    assert surface.optimal_weight == 0.0
    assert surface.at_lower_boundary
    assert surface.optimal_gain == 0.0
    assert surface.material_width == 0.0


def test_an_interior_optimum_is_located_and_its_curvature_matches_a_hand_difference() -> None:
    step = 0.005
    weights = _linear_grid(0.20, step)
    # A concave quadratic peaking at w = 0.10 with a maximum gain of 1.0.
    gains = [1.0 - 100.0 * (weight - 0.10) ** 2 for weight in weights]
    surface = optimal_long_only_weight(weights, gains, cap=0.20, materiality=0.30)
    assert surface.optimal_weight == pytest.approx(0.10)
    assert surface.optimal_gain == pytest.approx(1.0)
    assert not surface.at_lower_boundary and not surface.at_upper_boundary
    # The exact second derivative of the quadratic is -200.
    assert surface.curvature == pytest.approx(-200.0, rel=1e-9)
    # The 90%-of-peak plateau of 1 - 100 (w - 0.1)^2 >= 0.9 is |w - 0.1| <= 0.1/sqrt(100),
    # that is 0.03162, which the 0.005 grid resolves to [0.07, 0.13].
    assert (surface.plateau_low, surface.plateau_high) == pytest.approx((0.07, 0.13))
    assert surface.plateau_width == pytest.approx(0.06)


def test_a_flat_surface_reports_a_plateau_spanning_the_whole_grid() -> None:
    weights = _linear_grid(0.20, 0.01)
    gains = [1.0] * len(weights)
    surface = optimal_long_only_weight(weights, gains, cap=0.20, materiality=0.30)
    assert surface.plateau_width == pytest.approx(0.20)
    assert surface.material_width == pytest.approx(0.20)


def test_the_material_region_is_empty_when_the_peak_is_below_the_threshold() -> None:
    weights = _linear_grid(0.20, 0.01)
    gains = [0.5 * weight for weight in weights]
    surface = optimal_long_only_weight(weights, gains, cap=0.20, materiality=0.30)
    assert surface.optimal_gain < 0.30
    assert surface.material_width == 0.0


def test_the_deviation_from_a_straight_line_detects_a_bowed_surface() -> None:
    weights = _linear_grid(0.20, 0.005)
    gains = [10.0 * weight - 100.0 * weight**2 for weight in weights]
    surface = optimal_long_only_weight(weights, gains, cap=0.20, materiality=0.30)
    # The chord through the endpoints of a * w + b * w^2 leaves a maximum gap of
    # |b| * cap^2 / 4 at the midpoint.
    assert surface.max_deviation_from_linear == pytest.approx(100.0 * 0.20**2 / 4.0, rel=1e-3)


def test_a_grid_that_does_not_start_at_zero_is_refused() -> None:
    with pytest.raises(ValueError, match="start at zero weight"):
        optimal_long_only_weight([0.01, 0.02, 0.03], [0.0, 1.0, 2.0], cap=0.03, materiality=0.3)


def test_a_non_increasing_grid_is_refused() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        optimal_long_only_weight([0.0, 0.02, 0.01], [0.0, 1.0, 2.0], cap=0.02, materiality=0.3)


def test_a_non_finite_gain_is_refused_rather_than_maximised() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        optimal_long_only_weight(
            [0.0, 0.01, 0.02], [0.0, float("inf"), 1.0], cap=0.02, materiality=0.3
        )


# --------------------------------------------------------------------------- #
# Weight construction and the funding legs
# --------------------------------------------------------------------------- #


def test_pro_rata_funding_scales_every_base_asset_and_still_sums_to_one() -> None:
    base = np.array([0.6, 0.3, 0.1, 0.0])
    target, levered = _weights_for(base, sleeve_weight=0.10, leg="pro_rata", named_leg="us_equity")
    assert target.size == len(ASSET_NAMES)
    assert np.allclose(target[:4], 0.9 * base)
    assert target[4] == pytest.approx(0.10)
    assert float(target.sum()) == pytest.approx(1.0)
    assert not levered


def test_named_leg_funding_takes_the_whole_weight_out_of_one_asset() -> None:
    base = np.array([0.6, 0.3, 0.1, 0.0])
    target, levered = _weights_for(base, sleeve_weight=0.10, leg="named_leg", named_leg="us_equity")
    assert target[0] == pytest.approx(0.5)
    assert target[1] == pytest.approx(0.3)
    assert float(target.sum()) == pytest.approx(1.0)
    assert not levered


def test_funding_a_sleeve_from_a_leg_too_small_to_carry_it_is_flagged_as_levered() -> None:
    base = np.array([0.6, 0.3, 0.1, 0.0])
    target, levered = _weights_for(
        base, sleeve_weight=0.20, leg="named_leg", named_leg="emerging_equity"
    )
    assert target[2] == pytest.approx(-0.10)
    assert levered, "a short weight must be reported, not clipped"


def test_funding_from_cash_when_there_is_none_is_borrowing_and_says_so() -> None:
    base = np.array([0.6, 0.3, 0.1, 0.0])
    _, levered = _weights_for(base, sleeve_weight=0.05, leg="cash", named_leg="us_equity")
    assert levered


def test_an_unknown_funding_leg_is_refused() -> None:
    base = np.array([0.6, 0.3, 0.1, 0.0])
    with pytest.raises(MarginalSleeveValueError, match="funding leg"):
        _weights_for(base, sleeve_weight=0.1, leg="named_leg", named_leg="gold")


# --------------------------------------------------------------------------- #
# Grids and windows
# --------------------------------------------------------------------------- #


def test_the_weight_grid_starts_at_zero_and_ends_at_the_cap() -> None:
    grid = _grid(0.20, 0.005)
    assert grid[0] == 0.0
    assert grid[-1] == pytest.approx(0.20)
    assert grid.size == 41
    assert _index_of(grid, 0.10) == 20


def test_a_cap_that_is_not_a_whole_number_of_steps_is_refused() -> None:
    with pytest.raises(MarginalSleeveValueError, match="whole number of steps"):
        _grid(0.20, 0.003)


def test_a_reference_weight_off_the_grid_is_refused() -> None:
    with pytest.raises(MarginalSleeveValueError, match="not a point of the frozen grid"):
        _index_of(_grid(0.20, 0.02), 0.055)


def test_a_window_mask_selects_its_own_months_inclusively() -> None:
    periods = ("1991-01", "1991-02", "1991-03")
    assert list(_mask_for(periods, "1991-01", "1991-02")) == [True, True, False]


def test_a_whole_year_mask_refuses_a_window_that_is_not_whole_years() -> None:
    periods = tuple(f"1991-{month:02d}" for month in range(1, 13))
    assert bool(_whole_year_mask(periods, "1991-01", "1991-12").all())
    assert not bool(_whole_year_mask(periods, "1991-01", "1991-06").any())


# --------------------------------------------------------------------------- #
# The modelled proxy and the fee model
# --------------------------------------------------------------------------- #


def test_par_bond_risk_matches_an_exact_repricing_of_the_bond() -> None:
    """Differentiate the exact price function numerically; never trust the algebra alone.

    A ten-year semi-annual par bond priced at 1 has coupon equal to its yield, so
    ``P(y) = sum_k c v^k + v^n`` with ``c = y0/2`` fixed and ``v = 1/(1+y/2)``.
    Modified duration is ``-P'(y)/P(y)`` and convexity is ``P''(y)/P(y)``, both in
    annual units. Both are recomputed here from that price function by central
    differences, entirely independently of :func:`par_bond_risk`.
    """
    y0, periods = 0.04, 20

    def price(annual_yield: float) -> float:
        coupon = y0 / 2.0
        discount = 1.0 / (1.0 + annual_yield / 2.0)
        return sum(coupon * discount**k for k in range(1, periods + 1)) + discount**periods

    assert price(y0) == pytest.approx(1.0, abs=1e-15), "a par bond prices at one"
    step = 1e-6
    first = (price(y0 + step) - price(y0 - step)) / (2.0 * step)
    second = (price(y0 + step) - 2.0 * price(y0) + price(y0 - step)) / step**2
    modified, convexity = par_bond_risk(y0, periods=float(periods))
    assert modified == pytest.approx(-first / price(y0), rel=1e-8)
    assert convexity == pytest.approx(second / price(y0), rel=1e-4)
    # And the textbook magnitudes, so a sign or factor error is obvious to a reader.
    assert modified == pytest.approx(8.176, abs=1e-3)
    assert convexity == pytest.approx(78.898, abs=1e-3)
    # FINDING, surfaced here and since repaired: exp_004's copy of this helper
    # returned 39.449, exactly half, because its second-derivative formula dropped
    # a factor of two, and its own test asserted 39.4490 — the implementation's own
    # output — so it could not catch it. Both copies now agree, and exp_004's test
    # asserts that they do.


def test_a_flat_yield_earns_only_its_coupon() -> None:
    yields = np.array([0.04, 0.04, 0.04])
    returns = bond_total_return_from_yield(yields)
    assert math.isnan(returns[0]), "the first month has no previous yield"
    assert returns[1] == pytest.approx(0.04 / 12.0)


def test_a_rising_yield_loses_roughly_duration_times_the_change() -> None:
    yields = np.array([0.04, 0.05])
    returns = bond_total_return_from_yield(yields)
    modified, convexity = par_bond_risk(0.04, periods=20.0)
    assert returns[1] == pytest.approx(0.04 / 12.0 - modified * 0.01 + 0.5 * convexity * 0.01**2)


def test_a_non_positive_yield_is_left_missing_rather_than_invented() -> None:
    returns = bond_total_return_from_yield(np.array([0.0, 0.02, 0.03]))
    assert math.isnan(returns[1])
    assert not math.isnan(returns[2])


def test_the_performance_fee_is_ten_percent_of_a_gain_above_the_high_water_mark() -> None:
    net, total = high_water_mark_performance_fee(np.array([0.10]), rate=0.10)
    assert net[0] == pytest.approx(0.09)
    assert total == pytest.approx(0.01)


def test_recovering_ground_is_not_charged_twice() -> None:
    gross = np.array([-0.10, 0.10])
    net, total = high_water_mark_performance_fee(gross, rate=0.10)
    assert net[0] == pytest.approx(-0.10)
    # 0.9 * 1.1 = 0.99, still below the mark of 1.0, so nothing is charged.
    assert net[1] == pytest.approx(0.10)
    assert total == pytest.approx(0.0)


def test_a_zero_rate_charges_nothing() -> None:
    gross = np.array([0.05, -0.02, 0.03])
    net, total = high_water_mark_performance_fee(gross, rate=0.0)
    assert np.allclose(net, gross)
    assert total == 0.0


def test_an_impossible_fee_rate_is_refused() -> None:
    with pytest.raises(ValueError, match=r"rate must lie in \[0, 1\)"):
        high_water_mark_performance_fee(np.array([0.1]), rate=1.0)


# --------------------------------------------------------------------------- #
# The module against its own committed specification
# --------------------------------------------------------------------------- #


def _as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def _as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


def test_the_registry_resolves_the_committed_entry_point() -> None:
    registry = build_registry()
    specification = load_specification(default_specification_path())
    assert specification.entry_point == ENTRY_POINT
    assert ENTRY_POINT in registry
    assert registry.resolve(ENTRY_POINT) is not None


def test_the_frozen_reference_weight_and_caps_lie_on_the_frozen_grid() -> None:
    parameters = _as_mapping(load_specification(default_specification_path()).parameters)
    cap = float(str(parameters["weight_cap"]))
    step = float(str(parameters["weight_grid_step"]))
    grid = _grid(cap, step)
    for key in ("reference_weight", "weight_cap_half"):
        assert _index_of(grid, float(str(parameters[key]))) >= 0
    coarse = _grid(cap, float(str(parameters["bootstrap_weight_grid_step"])))
    assert _index_of(coarse, float(str(parameters["reference_weight"]))) >= 0


def test_every_declared_funding_leg_is_a_base_asset_or_pro_rata() -> None:
    universe = _as_mapping(load_specification(default_specification_path()).universe)
    declared = [
        str(_as_mapping(item)["funding_leg"]) for item in _as_sequence(universe["sleeves"])
    ]
    assert declared, "the specification must declare at least one sleeve"
    assert set(declared) <= set(ASSET_NAMES[:4])
    assert FUNDING_LEG_IDS == ("pro_rata", "named_leg", "cash")


def test_the_base_weights_sum_to_one_and_name_the_three_registered_regions() -> None:
    parameters = _as_mapping(load_specification(default_specification_path()).parameters)
    weights = _as_mapping(parameters["base_weights"])
    total = sum(float(str(weights[key])) for key in ("us", "developed_ex_us", "emerging"))
    assert total == pytest.approx(1.0)
    assert BASE_PORTFOLIO_IDS == ("global_equity_core", "balanced_60_40")


def test_the_specification_names_gold_as_untested_and_says_why() -> None:
    """The gap has to be in the frozen specification, not only in the write-up."""
    parameters = _as_mapping(load_specification(default_specification_path()).parameters)
    rows = {
        str(_as_mapping(item)["id"]): str(_as_mapping(item)["reason"])
        for item in _as_sequence(parameters["sleeves_not_tested"])
    }
    assert "gold" in rows
    assert "NOT TESTED" in rows["gold"]
    assert "0002" in rows["gold"]


def test_the_error_type_is_specific_enough_to_catch() -> None:
    assert issubclass(MarginalSleeveValueError, RuntimeError)
