"""Tests for :mod:`portfolio_edge.core.kelly`.

The Kelly fixtures come from ``docs/research/portfolio-edge-research-framework.md``,
"Numerical fixtures", with the stylised illustrative parameters mu - r = 5%,
sigma = 18%, r = 5%. Every constant is re-derived from those three inputs in the
test body; none is asserted as a bare literal without its derivation beside it.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.kelly import (
    NonPositiveWealthScenarioError,
    cash_equivalent_leverage,
    expected_log_wealth,
    growth_curve,
    growth_rate_quadratic,
    growth_rate_vertex,
    kelly_leverage,
    kinked_growth_rate,
    leverage_financing_cost,
    maximise_expected_log_wealth,
    peak_growth_rate,
    wealth_relatives,
    zero_growth_leverage,
)

EXCESS = 0.05
SIGMA = 0.18
RISK_FREE = 0.05

PARAMETERS = {"excess_return": EXCESS, "volatility": SIGMA, "risk_free_rate": RISK_FREE}


def test_optimal_leverage_is_derivable_from_the_stated_inputs() -> None:
    """L* = (mu - r) / sigma^2 = 0.05 / 0.0324 = 1.5432098765..."""
    derived = EXCESS / SIGMA**2
    assert pytest.approx(0.0324, rel=0.0, abs=1e-15) == SIGMA**2
    assert derived == pytest.approx(1.5432098765, rel=0.0, abs=5e-11)
    assert kelly_leverage(excess_return=EXCESS, volatility=SIGMA) == pytest.approx(
        derived, rel=1e-15, abs=0.0
    )


def test_l_star_is_not_a_measured_quantity() -> None:
    """The widely repeated 1.54 comes from these stylised illustrative parameters,
    not from a measured S&P drift and volatility. Halving the excess return halves it.
    """
    assert kelly_leverage(excess_return=0.025, volatility=SIGMA) == pytest.approx(
        kelly_leverage(excess_return=EXCESS, volatility=SIGMA) / 2.0, rel=1e-15, abs=0.0
    )


def test_peak_growth_rate_fixture() -> None:
    """g(L*) = r + (mu - r)^2 / (2 sigma^2) = 0.05 + 0.0025 / 0.0648 = 0.0885802469."""
    derived = RISK_FREE + EXCESS**2 / (2.0 * SIGMA**2)
    assert pytest.approx(0.0648, rel=0.0, abs=1e-15) == 2.0 * SIGMA**2
    assert derived == pytest.approx(0.0885802469, rel=0.0, abs=5e-11)
    assert peak_growth_rate(**PARAMETERS) == pytest.approx(derived, rel=1e-15, abs=0.0)


def test_growth_returns_to_the_risk_free_rate_at_twice_l_star() -> None:
    """Fixture: growth = r at 3.0864. Re-derived as 2 L* = 2 * 1.5432098765."""
    derived = 2.0 * EXCESS / SIGMA**2
    assert derived == pytest.approx(3.0864197531, rel=0.0, abs=5e-11)
    assert cash_equivalent_leverage(excess_return=EXCESS, volatility=SIGMA) == pytest.approx(
        derived, rel=1e-15, abs=0.0
    )
    assert growth_rate_quadratic(derived, **PARAMETERS) == pytest.approx(
        RISK_FREE, rel=0.0, abs=1e-15
    )
    assert growth_rate_quadratic(0.0, **PARAMETERS) == pytest.approx(
        RISK_FREE, rel=0.0, abs=1e-15
    )


def test_zero_growth_leverage_fixture() -> None:
    """Fixture: growth = 0 at 3.8815675216.

    Re-derived as the positive root of L^2 - 2 L* L - 2 r / sigma^2 = 0, i.e.
    L* + sqrt((L*)^2 + 2 r / sigma^2) with L* = 1.5432098765 and
    2 r / sigma^2 = 0.10 / 0.0324 = 3.0864197531.
    """
    l_star = EXCESS / SIGMA**2
    derived = l_star + math.sqrt(l_star**2 + 2.0 * RISK_FREE / SIGMA**2)
    assert derived == pytest.approx(3.8815675216, rel=0.0, abs=5e-11)
    assert zero_growth_leverage(**PARAMETERS) == pytest.approx(derived, rel=1e-15, abs=0.0)
    assert growth_rate_quadratic(derived, **PARAMETERS) == pytest.approx(
        0.0, rel=0.0, abs=1e-15
    )


def test_the_zero_growth_root_lies_above_the_cash_equivalent_boundary() -> None:
    """For a log-growth investor the model boundary is 2 L*, not the zero-growth root:
    above 2 L* the model already loses to holding cash. Neither is a ruin boundary.
    """
    assert (
        cash_equivalent_leverage(excess_return=EXCESS, volatility=SIGMA)
        < zero_growth_leverage(**PARAMETERS)
    )


@pytest.mark.parametrize("leverage", [0.0, 0.5, 1.0, 1.5432, 2.0, 3.0, 3.88])
def test_vertex_form_agrees_with_the_quadratic_to_machine_precision(leverage: float) -> None:
    """Fixture: the two forms agree at L = 0, 0.5, 1, 1.5432, 2, 3, 3.88."""
    quadratic = RISK_FREE + leverage * EXCESS - 0.5 * leverage**2 * SIGMA**2
    l_star = EXCESS / SIGMA**2
    vertex = RISK_FREE + 0.5 * SIGMA**2 * (l_star**2 - (leverage - l_star) ** 2)
    assert quadratic == pytest.approx(vertex, rel=0.0, abs=1e-16)
    assert growth_rate_quadratic(leverage, **PARAMETERS) == pytest.approx(
        quadratic, rel=0.0, abs=1e-16
    )
    assert growth_rate_vertex(leverage, **PARAMETERS) == pytest.approx(
        quadratic, rel=0.0, abs=1e-16
    )


def test_growth_is_symmetric_about_l_star() -> None:
    """g(0) = g(2 L*) = r follows from the symmetry of the parabola alone."""
    l_star = kelly_leverage(excess_return=EXCESS, volatility=SIGMA)
    for offset in (0.1, 0.5, 1.0, 1.5):
        assert growth_rate_vertex(l_star - offset, **PARAMETERS) == pytest.approx(
            growth_rate_vertex(l_star + offset, **PARAMETERS), rel=0.0, abs=1e-15
        )


def test_growth_peaks_at_l_star() -> None:
    l_star = kelly_leverage(excess_return=EXCESS, volatility=SIGMA)
    peak = growth_rate_quadratic(l_star, **PARAMETERS)
    assert peak == pytest.approx(peak_growth_rate(**PARAMETERS), rel=1e-15, abs=0.0)
    for leverage in np.linspace(0.0, 4.0, 401):
        assert growth_rate_quadratic(float(leverage), **PARAMETERS) <= peak + 1e-15


def test_growth_curve_collects_the_four_landmarks() -> None:
    curve = growth_curve(**PARAMETERS)
    assert curve.optimal_leverage == pytest.approx(EXCESS / SIGMA**2, rel=1e-15, abs=0.0)
    assert curve.cash_equivalent_leverage == pytest.approx(
        2.0 * curve.optimal_leverage, rel=1e-15, abs=0.0
    )
    assert curve.peak_growth > curve.risk_free_rate
    assert curve.zero_growth_leverage > curve.cash_equivalent_leverage


def test_downscaling_an_estimated_kelly_fraction_is_close_to_free() -> None:
    """Thorp (2006), sec. 7.3, via the framework: if the true excess drift is half the
    estimate, betting 0.5 f-hat attains maximum growth, f-hat gives zero excess log
    growth over cash, and 1.5 f-hat gives negative excess log growth.
    """
    estimated_l_star = kelly_leverage(excess_return=EXCESS, volatility=SIGMA)
    true_parameters = {"excess_return": EXCESS / 2.0, "volatility": SIGMA, "risk_free_rate": 0.0}
    true_l_star = kelly_leverage(excess_return=EXCESS / 2.0, volatility=SIGMA)
    assert 0.5 * estimated_l_star == pytest.approx(true_l_star, rel=1e-15, abs=0.0)
    assert growth_rate_quadratic(estimated_l_star, **true_parameters) == pytest.approx(
        0.0, rel=0.0, abs=1e-16
    )
    assert growth_rate_quadratic(1.5 * estimated_l_star, **true_parameters) < 0.0
    assert growth_rate_quadratic(0.5 * estimated_l_star, **true_parameters) > 0.0


# --------------------------------------------------------------------------------------
# Kinked financing
# --------------------------------------------------------------------------------------


def test_kinked_growth_matches_the_smooth_model_below_one_times_exposure() -> None:
    mean_return = RISK_FREE + EXCESS
    for leverage in (0.0, 0.5, 1.0):
        assert kinked_growth_rate(
            leverage,
            mean_return=mean_return,
            volatility=SIGMA,
            lending_rate=RISK_FREE,
            borrow_spread=0.02,
        ) == pytest.approx(growth_rate_quadratic(leverage, **PARAMETERS), rel=0.0, abs=1e-15)


def test_the_borrowing_spread_bites_only_above_one_times_exposure() -> None:
    mean_return = RISK_FREE + EXCESS
    spread = 0.02
    leverage = 2.0
    smooth = growth_rate_quadratic(leverage, **PARAMETERS)
    kinked = kinked_growth_rate(
        leverage,
        mean_return=mean_return,
        volatility=SIGMA,
        lending_rate=RISK_FREE,
        borrow_spread=spread,
    )
    assert smooth - kinked == pytest.approx(spread * (leverage - 1.0), rel=1e-14, abs=0.0)


def test_a_borrowing_spread_lowers_the_growth_maximising_exposure() -> None:
    """The optimum does not survive unchanged when financing is kinked."""
    mean_return = RISK_FREE + EXCESS
    grid = np.linspace(0.0, 3.0, 3001)
    smooth = [growth_rate_quadratic(float(x), **PARAMETERS) for x in grid]
    kinked = [
        kinked_growth_rate(
            float(x),
            mean_return=mean_return,
            volatility=SIGMA,
            lending_rate=RISK_FREE,
            borrow_spread=0.02,
        )
        for x in grid
    ]
    assert float(grid[int(np.argmax(kinked))]) < float(grid[int(np.argmax(smooth))])


def test_an_instrument_cost_function_reduces_growth_at_every_exposure() -> None:
    mean_return = RISK_FREE + EXCESS
    base = kinked_growth_rate(
        1.5, mean_return=mean_return, volatility=SIGMA, lending_rate=RISK_FREE, borrow_spread=0.0
    )
    with_fee = kinked_growth_rate(
        1.5,
        mean_return=mean_return,
        volatility=SIGMA,
        lending_rate=RISK_FREE,
        borrow_spread=0.0,
        instrument_cost=lambda leverage: 0.004 * leverage,
    )
    assert base - with_fee == pytest.approx(0.004 * 1.5, rel=1e-14, abs=0.0)


def test_levering_a_low_volatility_portfolio_multiplies_the_financing_spread() -> None:
    """Framework, "Portfolio construction is an estimation problem": reaching 16%
    volatility from a 6.17%-volatility parity portfolio needs 2.59x leverage, so every
    100 bp of borrowing spread costs about 159 bp per year.
    """
    portfolio_volatility = math.sqrt(288.0 / 75625.0)  # the ERC fixture's sigma_p
    leverage = 0.16 / portfolio_volatility
    assert leverage == pytest.approx(2.5927249, rel=0.0, abs=5e-8)
    assert leverage - 1.0 == pytest.approx(1.5927249, rel=0.0, abs=5e-8)
    assert leverage_financing_cost(
        target_volatility=0.16,
        portfolio_volatility=portfolio_volatility,
        borrow_spread=0.01,
    ) == pytest.approx(0.015927249, rel=0.0, abs=5e-10)


# --------------------------------------------------------------------------------------
# Discrete multi-asset expected log wealth
# --------------------------------------------------------------------------------------


def test_expected_log_wealth_matches_a_hand_computation() -> None:
    scenarios = [[0.25, 0.10], [-0.20, 0.05]]
    weights = [0.5, 0.5]
    relatives = [1.0 + 0.5 * 0.25 + 0.5 * 0.10, 1.0 + 0.5 * -0.20 + 0.5 * 0.05]
    expected = 0.5 * math.log(relatives[0]) + 0.5 * math.log(relatives[1])
    assert wealth_relatives(weights, scenarios) == pytest.approx(
        relatives, rel=1e-15, abs=0.0
    )
    assert expected_log_wealth(weights, scenarios) == pytest.approx(
        expected, rel=1e-15, abs=0.0
    )


def test_unequal_probabilities_are_normalised_and_used() -> None:
    scenarios = [[0.25], [-0.20]]
    weighted = expected_log_wealth([1.0], scenarios, probabilities=[3.0, 1.0])
    assert weighted == pytest.approx(
        0.75 * math.log(1.25) + 0.25 * math.log(0.80), rel=1e-15, abs=0.0
    )


def test_a_scenario_producing_non_positive_wealth_is_rejected() -> None:
    """The constraint 1 + w'R > 0 almost surely is checked, never assumed."""
    scenarios = [[0.10], [-1.00]]
    with pytest.raises(NonPositiveWealthScenarioError) as info:
        expected_log_wealth([1.0], scenarios)
    assert info.value.scenario_index == 1
    assert info.value.wealth_relative == pytest.approx(0.0, rel=0.0, abs=1e-15)


def test_leverage_can_push_an_otherwise_admissible_scenario_set_over_the_edge() -> None:
    scenarios = [[0.30], [-0.60]]
    assert expected_log_wealth([1.0], scenarios) < 0.0
    with pytest.raises(NonPositiveWealthScenarioError):
        expected_log_wealth([2.0], scenarios)


def test_the_optimiser_refuses_an_inadmissible_scenario_set() -> None:
    scenarios = [[0.10, 0.05], [-1.50, 0.02]]
    with pytest.raises(NonPositiveWealthScenarioError):
        maximise_expected_log_wealth(scenarios)


def test_the_optimiser_finds_the_growth_optimal_mix_of_two_bounded_assets() -> None:
    """A dominated asset receives no weight; the objective at the solution is at least
    that of every point on a fine grid of the simplex."""
    scenarios = [[0.25, 0.02], [-0.10, 0.02]]
    weights = maximise_expected_log_wealth(scenarios)
    assert float(np.sum(weights)) == pytest.approx(1.0, rel=0.0, abs=1e-9)
    best = expected_log_wealth(weights, scenarios)
    for share in np.linspace(0.0, 1.0, 201):
        candidate = [float(share), 1.0 - float(share)]
        assert expected_log_wealth(candidate, scenarios) <= best + 1e-9
