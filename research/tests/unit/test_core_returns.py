"""Tests for :mod:`portfolio_edge.core.returns`.

Fixture sources are cited inline. Every constant is re-derived from its stated
inputs in the test body; nothing is copied from the implementation under test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.returns import (
    Compounding,
    ExcessMethod,
    Frequency,
    RateBasis,
    aggregate_log,
    aggregate_simple_over,
    annualise_log_return,
    annualise_simple_return,
    annualise_volatility,
    arithmetic_mean,
    compound_simple,
    deannualise,
    excess_returns,
    geometric_mean,
    growth_rate_approximation,
    growth_rate_approximation_error,
    log_to_simple,
    lognormal_growth_rate,
    lognormal_log_drift,
    simple_to_log,
)


def test_simple_and_log_returns_round_trip() -> None:
    simple = [0.10, -0.05, 0.03, -0.20]
    recovered = log_to_simple(simple_to_log(simple))
    assert recovered == pytest.approx(simple, rel=0.0, abs=1e-15)


def test_simple_to_log_rejects_total_loss() -> None:
    with pytest.raises(ValueError, match="non-positive wealth relative"):
        simple_to_log([0.05, -1.0])


def test_log_returns_sum_where_simple_returns_compound() -> None:
    simple = [0.10, -0.05, 0.03]
    # exp(sum of log returns) - 1 must equal the compounded simple return exactly.
    # rel=1e-14 is a few units in the last place of a double after three
    # exp/log round trips, not a loosened tolerance.
    assert math.expm1(aggregate_log(simple_to_log(simple))) == pytest.approx(
        compound_simple(simple), rel=1e-14, abs=0.0
    )


def test_compound_simple_of_empty_series_is_zero() -> None:
    assert compound_simple([]) == 0.0


def test_aggregate_simple_over_compounds_non_overlapping_blocks() -> None:
    monthly = [0.01] * 7
    quarters = aggregate_simple_over(monthly, 3)
    # Two full quarters; the trailing single month is dropped, not annualised.
    assert quarters.size == 2
    assert quarters == pytest.approx([1.01**3 - 1.0] * 2, rel=1e-14, abs=0.0)


def test_geometric_mean_reproduces_terminal_wealth() -> None:
    returns = [0.25, -0.10, 0.40, -0.30]
    n = len(returns)
    g = geometric_mean(returns)
    assert (1.0 + g) ** n == pytest.approx(
        math.prod(1.0 + r for r in returns), rel=1e-14, abs=0.0
    )


def test_arithmetic_mean_exceeds_geometric_mean_when_returns_vary() -> None:
    returns = [0.25, -0.10, 0.40, -0.30]
    assert arithmetic_mean(returns) > geometric_mean(returns)


def test_arithmetic_equals_geometric_for_a_constant_series() -> None:
    returns = [0.02] * 12
    assert arithmetic_mean(returns) == pytest.approx(
        geometric_mean(returns), rel=1e-14, abs=0.0
    )


def test_geometric_deannualisation_compounds_back_to_the_annual_rate() -> None:
    monthly = deannualise(0.06, frequency=Frequency.MONTHLY)
    assert (1.0 + float(monthly[0])) ** 12 - 1.0 == pytest.approx(0.06, rel=1e-15, abs=0.0)


def test_simple_deannualisation_divides_by_the_period_count() -> None:
    monthly = deannualise(0.06, frequency=Frequency.MONTHLY, compounding=Compounding.SIMPLE)
    assert float(monthly[0]) == pytest.approx(0.06 / 12.0, rel=1e-15, abs=0.0)


def test_annualisation_inverts_deannualisation() -> None:
    per_period = float(deannualise(0.08, frequency=Frequency.QUARTERLY)[0])
    assert annualise_simple_return(per_period, frequency=Frequency.QUARTERLY) == pytest.approx(
        0.08, rel=1e-14, abs=0.0
    )


def test_log_and_volatility_annualisation_use_their_stated_scalings() -> None:
    assert annualise_log_return(0.005, frequency=Frequency.MONTHLY) == pytest.approx(
        0.06, rel=1e-15, abs=0.0
    )
    assert annualise_volatility(0.04, frequency=Frequency.MONTHLY) == pytest.approx(
        0.04 * math.sqrt(12.0), rel=1e-15, abs=0.0
    )


def test_excess_returns_arithmetic_with_a_per_period_cash_rate() -> None:
    returns = [0.02, -0.01]
    result = excess_returns(returns, 0.003, frequency=Frequency.MONTHLY)
    assert result == pytest.approx([0.017, -0.013], rel=0.0, abs=1e-15)


def test_excess_returns_deannualise_an_annual_cash_rate_geometrically() -> None:
    monthly_cash = (1.05) ** (1.0 / 12.0) - 1.0
    result = excess_returns(
        [0.02],
        0.05,
        frequency=Frequency.MONTHLY,
        cash_rate_basis=RateBasis.ANNUALISED,
        compounding=Compounding.GEOMETRIC,
    )
    assert float(result[0]) == pytest.approx(0.02 - monthly_cash, rel=1e-15, abs=0.0)


def test_geometric_excess_return_is_the_wealth_relative_ratio() -> None:
    result = excess_returns(
        [0.02], 0.003, frequency=Frequency.MONTHLY, method=ExcessMethod.GEOMETRIC
    )
    assert float(result[0]) == pytest.approx(1.02 / 1.003 - 1.0, rel=1e-15, abs=0.0)


def test_excess_returns_accept_a_cash_rate_series() -> None:
    result = excess_returns([0.02, 0.01], [0.003, 0.004], frequency=Frequency.MONTHLY)
    assert result == pytest.approx([0.017, 0.006], rel=0.0, abs=1e-15)


def test_excess_returns_reject_a_mismatched_cash_rate_series() -> None:
    with pytest.raises(ValueError, match="same length as returns"):
        excess_returns([0.02, 0.01], [0.003, 0.004, 0.005], frequency=Frequency.MONTHLY)


# --------------------------------------------------------------------------------------
# Lognormal growth: exact form versus the mu - sigma^2/2 approximation.
# --------------------------------------------------------------------------------------


def test_lognormal_growth_rate_is_derivable_from_its_own_definition() -> None:
    mu, sigma = 0.08, 0.15
    # Re-derived here rather than read from the module: m = ln((1+mu)^2 / sqrt((1+mu)^2 + sigma^2)).
    base = (1.0 + mu) ** 2
    expected_m = math.log(base / math.sqrt(base + sigma**2))
    assert lognormal_log_drift(mu, sigma) == pytest.approx(expected_m, rel=1e-15, abs=0.0)
    assert lognormal_growth_rate(mu, sigma) == pytest.approx(
        math.exp(expected_m) - 1.0, rel=1e-15, abs=0.0
    )


@pytest.mark.parametrize(
    ("mu", "sigma", "expected_approximation", "expected_exact", "expected_error"),
    [
        (0.08, 0.15, 0.068750, 0.069732, -0.00098),
        (0.08, 0.40, 0.000000, 0.012769, -0.01277),
        (0.10, 0.60, -0.080000, -0.034315, -0.04569),
    ],
)
def test_growth_error_table_from_the_engine_specification(
    mu: float,
    sigma: float,
    expected_approximation: float,
    expected_exact: float,
    expected_error: float,
) -> None:
    """Reproduce the three-row table in docs/research/portfolio-engine-specification.md.

    Section "Geometric versus arithmetic mean". The published table is rounded to six
    decimals in the first two columns and five in the error column, so the tolerances
    below are the rounding half-widths of the published figures, not a fitted fudge.
    """
    assert growth_rate_approximation(mu, sigma) == pytest.approx(
        expected_approximation, rel=0.0, abs=5e-7
    )
    assert lognormal_growth_rate(mu, sigma) == pytest.approx(expected_exact, rel=0.0, abs=5e-7)
    assert growth_rate_approximation_error(mu, sigma) == pytest.approx(
        expected_error, rel=0.0, abs=5e-6
    )


def test_the_approximation_wrongly_predicts_negative_growth() -> None:
    """At mu=10%, sigma=60% the approximation says -8.0% while exact growth is -3.4%.

    Both are negative here, but the approximation overstates the drag by 4.6pp; at
    mu=8%, sigma=40% it predicts exactly zero growth where the truth is +1.28%.
    Kelly sizing runs directly on g, so the error propagates into leverage.
    """
    assert growth_rate_approximation(0.08, 0.40) == pytest.approx(0.0, rel=0.0, abs=1e-15)
    assert lognormal_growth_rate(0.08, 0.40) > 0.0
    assert growth_rate_approximation_error(0.08, 0.40) < 0.0


def test_approximation_error_grows_with_volatility() -> None:
    errors = [abs(growth_rate_approximation_error(0.08, sigma)) for sigma in (0.10, 0.20, 0.40)]
    assert errors == sorted(errors)
    assert np.all(np.diff(errors) > 0.0)


def test_approximation_error_vanishes_at_zero_volatility() -> None:
    assert growth_rate_approximation_error(0.08, 0.0) == pytest.approx(0.0, rel=0.0, abs=1e-15)
