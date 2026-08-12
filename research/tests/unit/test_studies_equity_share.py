"""Tests for the equity-share study.

Every fixture here is computed independently of the function under test: by hand,
by an annuity formula, by numerical maximisation of the objective, by seeded Monte
Carlo, or by a different module in this repository. Nothing is pinned to output the
study itself produced.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.kelly import growth_rate_vertex, kelly_leverage, peak_growth_rate
from portfolio_edge.studies.equity_share import (
    break_even_excess_return,
    constant_mix_ladder,
    constant_mix_returns,
    fully_invested_growth_optimal_weight,
    growth_retained_fraction,
    growth_shortfall,
    implied_effective_years,
    inverse_variance_bias_factor,
    kelly_estimator_standard_error,
    optimal_kelly_shrinkage,
    permuted_terminal_wealth,
    plug_in_growth_cost,
    terminal_wealth_with_level_flow,
)

# ---------------------------------------------------------------------------
# 1. The growth parabola
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fraction", "expected"),
    [(0.0, 0.0), (0.25, 0.4375), (0.5, 0.75), (1.0, 1.0), (1.5, 0.75), (2.0, 0.0), (3.0, -3.0)],
)
def test_growth_retained_fraction_matches_hand_arithmetic(
    fraction: float, expected: float
) -> None:
    assert growth_retained_fraction(fraction) == pytest.approx(expected)


def test_half_and_double_kelly_are_asymmetric_in_the_multiplicative_sense() -> None:
    """The parabola is symmetric in ``L``; the *factor of two* is not."""
    assert growth_retained_fraction(0.5) == pytest.approx(0.75)
    assert growth_retained_fraction(2.0) == pytest.approx(0.0)


def test_growth_shortfall_agrees_with_the_core_kelly_module() -> None:
    """Cross-check against an implementation written for a different purpose."""
    excess, sigma, risk_free = 0.055, 0.16, 0.03
    optimal = kelly_leverage(excess_return=excess, volatility=sigma)
    peak = peak_growth_rate(
        excess_return=excess, volatility=sigma, risk_free_rate=risk_free
    )
    for fraction in (0.2, 0.5, 0.9, 1.0, 1.4, 2.0, 2.5):
        from_core = growth_rate_vertex(
            fraction * optimal,
            excess_return=excess,
            volatility=sigma,
            risk_free_rate=risk_free,
        )
        from_study = peak - growth_shortfall(
            fraction, excess_return=excess, volatility=sigma
        )
        assert from_study == pytest.approx(from_core, abs=1e-15)


def test_growth_shortfall_rejects_non_positive_volatility() -> None:
    with pytest.raises(ValueError, match="volatility must be positive"):
        growth_shortfall(1.0, excess_return=0.05, volatility=0.0)


# ---------------------------------------------------------------------------
# 2. The fully invested two-asset optimum
# ---------------------------------------------------------------------------


def _mix_growth(
    weight: float,
    *,
    premium: float,
    equity_volatility: float,
    bond_volatility: float,
    correlation: float,
) -> float:
    """``w (mu_e - mu_b) - 0.5 sigma_p**2(w)``, up to a constant in ``w``."""
    variance = (
        weight**2 * equity_volatility**2
        + (1.0 - weight) ** 2 * bond_volatility**2
        + 2.0 * weight * (1.0 - weight) * correlation * equity_volatility * bond_volatility
    )
    return weight * premium - 0.5 * variance


@pytest.mark.parametrize("correlation", [-0.4, 0.0, 0.2, 0.6])
@pytest.mark.parametrize("premium", [0.005, 0.012, 0.02])
def test_two_asset_optimum_maximises_the_growth_objective(
    correlation: float, premium: float
) -> None:
    """Independent check: a fine grid search over the same objective."""
    equity_volatility, bond_volatility = 0.154, 0.0673
    analytic = fully_invested_growth_optimal_weight(
        excess_return_over_bond=premium,
        equity_volatility=equity_volatility,
        bond_volatility=bond_volatility,
        correlation=correlation,
        clip=False,
    )
    grid = np.linspace(analytic - 0.05, analytic + 0.05, 20_001)
    values = [
        _mix_growth(
            float(weight),
            premium=premium,
            equity_volatility=equity_volatility,
            bond_volatility=bond_volatility,
            correlation=correlation,
        )
        for weight in grid
    ]
    assert float(grid[int(np.argmax(values))]) == pytest.approx(analytic, abs=1e-5)


def test_break_even_excess_return_inverts_the_optimum() -> None:
    equity_volatility, bond_volatility, correlation = 0.154, 0.0673, 0.133
    for weight in (0.2, 0.4, 0.6, 0.8, 1.0):
        premium = break_even_excess_return(
            weight=weight,
            equity_volatility=equity_volatility,
            bond_volatility=bond_volatility,
            correlation=correlation,
        )
        assert fully_invested_growth_optimal_weight(
            excess_return_over_bond=premium,
            equity_volatility=equity_volatility,
            bond_volatility=bond_volatility,
            correlation=correlation,
        ) == pytest.approx(weight)


def test_all_equity_needs_only_a_small_premium_over_bonds() -> None:
    """The number the page leans on, computed by hand as a check.

    ``w* = 1`` requires ``mu_e - mu_b = sigma_e**2 - rho sigma_e sigma_b``. At
    ``sigma_e = 15.4%``, ``sigma_b = 6.73%``, ``rho = 0.133`` that is
    ``0.0237 - 0.133 * 0.154 * 0.0673 = 2.23%``.
    """
    premium = break_even_excess_return(
        weight=1.0, equity_volatility=0.154, bond_volatility=0.0673, correlation=0.133
    )
    assert premium == pytest.approx(0.154**2 - 0.133 * 0.154 * 0.0673)
    assert premium == pytest.approx(0.0223, abs=5e-5)


def test_weight_is_clipped_to_the_no_leverage_constraint() -> None:
    def weight_at(premium: float, *, clip: bool = True) -> float:
        return fully_invested_growth_optimal_weight(
            excess_return_over_bond=premium,
            equity_volatility=0.154,
            bond_volatility=0.0673,
            correlation=0.133,
            clip=clip,
        )

    assert weight_at(0.055) == pytest.approx(1.0)
    assert weight_at(0.055, clip=False) > 2.0
    assert weight_at(-0.05) == pytest.approx(0.0)


def test_perfectly_comoving_assets_are_rejected() -> None:
    with pytest.raises(ValueError, match="perfectly co-moving"):
        fully_invested_growth_optimal_weight(
            excess_return_over_bond=0.02,
            equity_volatility=0.15,
            bond_volatility=0.15,
            correlation=1.0,
        )


# ---------------------------------------------------------------------------
# 3. Estimation error
# ---------------------------------------------------------------------------


def test_kelly_standard_error_reproduces_the_core_module_docstring() -> None:
    assert kelly_estimator_standard_error(volatility=0.18, years=20.0) == pytest.approx(
        1.24, abs=0.005
    )


def test_plug_in_growth_cost_and_shrinkage_against_monte_carlo() -> None:
    """The independent computation is a seeded simulation, not a rearranged formula."""
    mu, sigma, years, draws = 0.05, 0.154, 30.0, 400_000
    generator = np.random.default_rng(20260812)
    estimates = (mu + generator.normal(0.0, sigma / math.sqrt(years), draws)) / sigma**2

    def excess_growth(exposure: np.ndarray) -> float:
        return float(np.mean(exposure * mu - 0.5 * exposure**2 * sigma**2))

    peak = 0.5 * mu**2 / sigma**2
    simulated_cost = peak - excess_growth(estimates)
    assert simulated_cost == pytest.approx(plug_in_growth_cost(years), rel=0.02)

    grid = np.arange(0.30, 1.20, 0.002)
    best = float(grid[int(np.argmax([excess_growth(f * estimates) for f in grid]))])
    assert best == pytest.approx(
        optimal_kelly_shrinkage(sharpe_ratio=mu / sigma, years=years), abs=0.005
    )


def test_shrinkage_depends_only_on_squared_sharpe_times_years() -> None:
    left = optimal_kelly_shrinkage(sharpe_ratio=0.40, years=25.0)
    right = optimal_kelly_shrinkage(sharpe_ratio=0.20, years=100.0)
    assert left == pytest.approx(right)
    assert left == pytest.approx(4.0 / 5.0)


def test_half_kelly_implies_one_over_squared_sharpe_years() -> None:
    for sharpe in (0.25, 0.40, 0.55):
        assert implied_effective_years(
            sharpe_ratio=sharpe, shrinkage=0.5
        ) == pytest.approx(1.0 / sharpe**2)


def test_effective_years_inverts_the_shrinkage() -> None:
    for years in (5.0, 30.0, 62.5):
        shrinkage = optimal_kelly_shrinkage(sharpe_ratio=0.4631, years=years)
        assert implied_effective_years(
            sharpe_ratio=0.4631, shrinkage=shrinkage
        ) == pytest.approx(years)


def test_inverse_variance_bias_against_monte_carlo() -> None:
    observations = 60
    generator = np.random.default_rng(7)
    sample = generator.normal(0.0, 1.0, size=(400_000, observations))
    simulated = float(np.mean(1.0 / sample.var(axis=1, ddof=1)))
    assert simulated == pytest.approx(inverse_variance_bias_factor(observations), rel=0.02)


def test_inverse_variance_bias_is_negligible_in_a_long_sample() -> None:
    assert inverse_variance_bias_factor(750) == pytest.approx(1.00268, abs=1e-5)


# ---------------------------------------------------------------------------
# 4. Sequence risk
# ---------------------------------------------------------------------------


def test_level_flow_terminal_wealth_matches_the_annuity_formula() -> None:
    """At a constant return the path has a closed form; use it as the fixture."""
    rate, periods, contribution = 0.01, 120, 3.0
    returns = np.full(periods, rate)
    expected = contribution * ((1.0 + rate) ** (periods + 1) - (1.0 + rate)) / rate
    assert terminal_wealth_with_level_flow(
        returns, initial_wealth=1e-12, flow_per_period=contribution
    ) == pytest.approx(expected, rel=1e-9)


def test_level_withdrawal_can_reach_ruin_without_raising() -> None:
    returns = np.zeros(20)
    assert terminal_wealth_with_level_flow(
        returns, initial_wealth=1.0, flow_per_period=-0.1
    ) == 0.0


def test_terminal_wealth_is_permutation_invariant_without_flows() -> None:
    generator = np.random.default_rng(3)
    returns = generator.normal(0.006, 0.045, 240)
    result = permuted_terminal_wealth(
        returns,
        initial_wealth=1.0,
        flow_per_period=0.0,
        periods=240,
        draws=500,
        seed=11,
        early_periods=60,
    )
    assert result.minimum == pytest.approx(result.maximum, rel=1e-12)
    assert result.spread_ratio == pytest.approx(1.0, abs=1e-12)
    assert result.early_return_correlation == pytest.approx(0.0, abs=1e-9)


def test_contributions_and_withdrawals_have_mirror_image_sequence_exposure() -> None:
    generator = np.random.default_rng(5)
    returns = generator.normal(0.008, 0.045, 360)
    shared = {
        "periods": 360,
        "draws": 4_000,
        "seed": 101,
        "early_periods": 120,
    }
    contributing = permuted_terminal_wealth(
        returns, initial_wealth=1e-12, flow_per_period=1.0, **shared
    )
    withdrawing = permuted_terminal_wealth(
        returns, initial_wealth=1.0, flow_per_period=-0.05 / 12.0, **shared
    )
    assert contributing.early_return_correlation < -0.5
    assert withdrawing.early_return_correlation > 0.5
    assert contributing.spread_ratio > 1.5
    assert withdrawing.spread_ratio > 1.5


def test_permuted_terminal_wealth_validates_its_window() -> None:
    returns = np.zeros(10)
    with pytest.raises(ValueError, match="periods must lie"):
        permuted_terminal_wealth(
            returns,
            initial_wealth=1.0,
            flow_per_period=0.0,
            periods=11,
            draws=5,
            seed=1,
            early_periods=1,
        )


# ---------------------------------------------------------------------------
# 5. The drawdown ladder
# ---------------------------------------------------------------------------


def test_constant_mix_endpoints_return_the_underlying_series() -> None:
    generator = np.random.default_rng(13)
    equity = generator.normal(0.008, 0.043, 120)
    safe = generator.normal(0.003, 0.004, 120)
    assert constant_mix_returns(equity, safe, 1.0) == pytest.approx(equity)
    assert constant_mix_returns(equity, safe, 0.0) == pytest.approx(safe)


def test_constant_mix_rejects_leverage_and_shorting() -> None:
    zeros = np.zeros(5)
    with pytest.raises(ValueError, match=r"weight must lie in \[0, 1\]"):
        constant_mix_returns(zeros, zeros, 1.2)
    with pytest.raises(ValueError, match=r"weight must lie in \[0, 1\]"):
        constant_mix_returns(zeros, zeros, -0.1)


def test_ladder_reproduces_a_hand_computed_rung() -> None:
    equity = np.array([0.10, -0.20, 0.15, -0.05])
    safe = np.array([0.01, 0.01, 0.01, 0.01])
    (rung,) = constant_mix_ladder(equity, safe, [0.5], periods_per_year=4)
    mixed = np.array([0.055, -0.095, 0.08, -0.02])
    assert rung.geometric_return == pytest.approx(float(np.prod(1.0 + mixed)) - 1.0)
    # Peak 1.055 at t=1, trough 1.055 * 0.905 * 1.08 * 0.98 = 1.010... < 1.055.
    curve = np.cumprod(1.0 + mixed)
    assert rung.max_drawdown == pytest.approx(curve[1] / curve[0] - 1.0)
    assert rung.max_time_under_water == 3


def test_ladder_is_monotone_in_volatility() -> None:
    generator = np.random.default_rng(17)
    equity = generator.normal(0.008, 0.043, 600)
    safe = generator.normal(0.003, 0.002, 600)
    rungs = constant_mix_ladder(equity, safe, [0.2, 0.4, 0.6, 0.8, 1.0])
    volatilities = [rung.volatility for rung in rungs]
    assert volatilities == sorted(volatilities)
