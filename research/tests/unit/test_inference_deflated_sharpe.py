"""Tests for the deflated and probabilistic Sharpe ratios.

Fixtures come from ``docs/research/portfolio-engine-specification.md``, "Deflated Sharpe
ratio", which restates Bailey and Lopez de Prado (2014), https://ssrn.com/abstract=2460551.
Each was recomputed here from the published formula before being asserted.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.inference.deflated_sharpe import (
    EULER_MASCHERONI,
    LinearDependenceWarning,
    TrialCorrelationError,
    deflated_sharpe_ratio,
    effective_number_of_trials,
    expected_max_sharpe,
    mean_off_diagonal_correlation,
    probabilistic_sharpe_ratio,
    trial_dispersion_from_sharpes,
)

# Source: docs/research/portfolio-engine-specification.md, "Deflated Sharpe ratio", and the
# "Expected maximum Sharpe" row of the "Numerical fixtures" table in
# docs/research/portfolio-edge-research-framework.md.
EXPECTED_MAX_Z_FIXTURES = {
    2: 0.519755,
    10: 1.574598,
    50: 2.276303,
    100: 2.530603,
    1000: 3.255122,
    10000: 3.860665,
}

# Source: same page, "The effect is not cosmetic." Trial dispersion 0.5, SR = 1.0, T = 120,
# skew -0.5, kurtosis 6.
DEFLATED_SIGNIFICANCE_FIXTURES = {
    10: 0.919122,
    100: 0.040474,
    1000: 0.000018,
}


@pytest.mark.parametrize(("n_trials", "expected"), sorted(EXPECTED_MAX_Z_FIXTURES.items()))
def test_expected_max_sharpe_reproduces_the_published_table(n_trials: int, expected: float) -> None:
    assert expected_max_sharpe(n_trials) == pytest.approx(expected, abs=5e-7)


def test_expected_max_sharpe_uses_the_stated_euler_mascheroni_constant() -> None:
    assert EULER_MASCHERONI == 0.5772156649
    # Reproduce N = 100 from the formula directly, without the module's arithmetic path.
    from scipy.stats import norm

    gamma = 0.5772156649
    manual = (1.0 - gamma) * float(norm.ppf(1.0 - 1.0 / 100)) + gamma * float(
        norm.ppf(1.0 - 1.0 / (100 * math.e))
    )
    assert manual == pytest.approx(2.530603, abs=5e-7)
    assert expected_max_sharpe(100) == pytest.approx(manual)


def test_expected_max_sharpe_is_increasing_and_rejects_impossible_counts() -> None:
    values = [expected_max_sharpe(n) for n in (2, 5, 10, 100, 1000)]
    assert values == sorted(values)
    assert expected_max_sharpe(1) == 0.0
    with pytest.raises(ValueError, match="n_trials"):
        expected_max_sharpe(0.5)


def test_probabilistic_sharpe_ratio_matches_a_hand_computed_value() -> None:
    """SR = 1.0, SR* = 0, T = 120, skew -0.5, kurtosis 6 (non-excess).

    denominator = sqrt(1 - (-0.5)(1) + (6-1)/4 * 1) = sqrt(2.75) = 1.6583124
    numerator   = 1.0 * sqrt(119)                  = 10.9087121
    z           = 6.5782...  -> Phi(z) is essentially 1
    Compare with the normal case (skew 0, kurtosis 3): sqrt(1.5) = 1.2247449,
    z = 8.9069, strictly larger. Negative skew and fat tails must *reduce* significance.
    """
    fat = probabilistic_sharpe_ratio(
        1.0, benchmark_sharpe=0.0, n_observations=120, skewness=-0.5, kurtosis=6.0
    )
    normal = probabilistic_sharpe_ratio(
        1.0, benchmark_sharpe=0.0, n_observations=120, skewness=0.0, kurtosis=3.0
    )
    assert fat < normal
    assert math.sqrt(2.75) == pytest.approx(1.6583123952)
    assert math.sqrt(119) == pytest.approx(10.9087121)


def test_probabilistic_sharpe_ratio_rejects_excess_kurtosis_passed_by_mistake() -> None:
    """Passing excess kurtosis (3.0 for a normal sample) is the silent failure this guards.

    An excess kurtosis of 0 would be read as a non-excess kurtosis of 0, which is
    impossible: the fourth standardised moment is at least 1.
    """
    with pytest.raises(ValueError, match="non-excess"):
        probabilistic_sharpe_ratio(1.0, benchmark_sharpe=0.0, n_observations=120, kurtosis=0.0)


@pytest.mark.parametrize(
    ("n_trials", "expected"), sorted(DEFLATED_SIGNIFICANCE_FIXTURES.items())
)
def test_deflated_sharpe_ratio_reproduces_the_effect_table(n_trials: int, expected: float) -> None:
    result = deflated_sharpe_ratio(
        1.0,
        trial_dispersion=0.5,
        n_trials=n_trials,
        n_observations=120,
        skewness=-0.5,
        kurtosis=6.0,
    )
    assert result.deflated_significance == pytest.approx(expected, abs=5e-7)
    assert result.sharpe_threshold == pytest.approx(0.5 * expected_max_sharpe(n_trials))
    assert result.n_trials_used == float(n_trials)


def test_deflated_sharpe_reports_the_trial_count_actually_used() -> None:
    """The DSR is a monotone function of an assumption, so N must always be reported."""
    result = deflated_sharpe_ratio(
        1.0, trial_dispersion=0.5, n_trials=37.4, n_observations=120
    )
    assert result.n_trials_used == 37.4
    assert result.trial_dispersion == 0.5
    assert result.observed_sharpe == 1.0
    assert result.n_observations == 120


def test_deflated_significance_falls_monotonically_in_the_trial_count() -> None:
    values = [
        deflated_sharpe_ratio(
            1.0,
            trial_dispersion=0.5,
            n_trials=n,
            n_observations=120,
            skewness=-0.5,
            kurtosis=6.0,
        ).deflated_significance
        for n in (2, 10, 100, 1000, 10000)
    ]
    assert values == sorted(values, reverse=True)


def test_trial_dispersion_is_across_trials_not_the_sampling_error_of_one_sharpe() -> None:
    """The most common implementation error in this formula, made unavailable by the API.

    ``trial_dispersion`` is keyword-only and has no default, so the function cannot be
    called at all without stating the across-trial dispersion. This test pins that contract
    and shows the two quantities are numerically different: the sampling standard error of a
    single Sharpe at SR = 1.0, T = 120 is sqrt((1 + SR^2/2)/T) = 0.1118034
    (docs/research/portfolio-engine-specification.md, "Sharpe ratio inference"), while the
    across-trial dispersion in the effect table is 0.5.
    """
    with pytest.raises(TypeError):
        deflated_sharpe_ratio(1.0, n_trials=10, n_observations=120)  # type: ignore[call-arg]

    sampling_se = math.sqrt((1.0 + 1.0**2 / 2.0) / 120)
    assert sampling_se == pytest.approx(0.1118033989, abs=1e-9)

    with_correct_input = deflated_sharpe_ratio(
        1.0, trial_dispersion=0.5, n_trials=100, n_observations=120, skewness=-0.5, kurtosis=6.0
    )
    with_the_common_error = deflated_sharpe_ratio(
        1.0,
        trial_dispersion=sampling_se,
        n_trials=100,
        n_observations=120,
        skewness=-0.5,
        kurtosis=6.0,
    )
    # The error inflates significance from 4% to essentially certain — the failure mode.
    assert with_correct_input.deflated_significance == pytest.approx(0.040474, abs=5e-7)
    assert with_the_common_error.deflated_significance > 0.99


def test_trial_dispersion_from_sharpes_is_the_sample_standard_deviation() -> None:
    """Hand-computed: [0.2, 0.4, 0.6, 0.8] has mean 0.5 and ddof=1 sd of sqrt(1/15).

    deviations: -0.3, -0.1, 0.1, 0.3 -> sum of squares 0.20 -> /3 -> 0.0666667
    sqrt = 0.2581989
    """
    assert trial_dispersion_from_sharpes([0.2, 0.4, 0.6, 0.8]) == pytest.approx(0.2581988897)
    with pytest.raises(ValueError, match="at least two trials"):
        trial_dispersion_from_sharpes([0.3])


# --------------------------------------------------------------------------------------
# Correlated trials
# --------------------------------------------------------------------------------------


def test_effective_trial_count_reproduces_both_endpoints() -> None:
    """N_hat = M(1 - rho_bar) + rho_bar: N_hat = M at rho_bar -> 0, N_hat = 1 at rho_bar -> 1.

    UNVERIFIED linear reading; see the docstring of effective_number_of_trials and open
    question 1 in docs/research/portfolio-engine-specification.md.
    """
    assert effective_number_of_trials(50, 0.0) == pytest.approx(50.0)
    assert effective_number_of_trials(50, 1.0) == pytest.approx(1.0)
    # Halfway is the arithmetic midpoint of the two endpoints under the linear reading.
    assert effective_number_of_trials(50, 0.5) == pytest.approx(25.5)


def test_effective_trial_count_is_decreasing_in_correlation() -> None:
    values = [effective_number_of_trials(100, rho) for rho in (0.0, 0.2, 0.5, 0.9, 1.0)]
    assert values == sorted(values, reverse=True)
    assert min(values) >= 1.0


def test_effective_trial_count_enforces_the_psd_lower_bound() -> None:
    """rho_bar >= -1/(M-1) by positive semi-definiteness. At M = 5 that is -0.25."""
    assert effective_number_of_trials(5, -0.25) == pytest.approx(5 * 1.25 - 0.25)
    with pytest.raises(TrialCorrelationError, match="lower bound"):
        effective_number_of_trials(5, -0.30)
    with pytest.raises(TrialCorrelationError, match="exceeds 1"):
        effective_number_of_trials(5, 1.2)


def test_mean_off_diagonal_correlation_refuses_a_singular_trial_matrix() -> None:
    """T < M makes the trial correlation matrix singular, so rho_bar from it is overfit."""
    rng = np.random.default_rng(11)
    returns = rng.standard_normal((20, 40))
    with pytest.raises(TrialCorrelationError, match="singular"):
        mean_off_diagonal_correlation(returns)
    # The override exists only to test the arithmetic; it still warns.
    with pytest.warns(LinearDependenceWarning):
        value = mean_off_diagonal_correlation(returns, allow_rank_deficient=True)
    assert -1.0 <= value <= 1.0


def test_mean_off_diagonal_correlation_recovers_a_known_average() -> None:
    """One common factor plus independent noise gives a known population correlation.

    r_k = sqrt(w) * f + sqrt(1 - w) * e_k gives pairwise correlation exactly w.
    With w = 0.36 and a long sample, rho_bar must be close to 0.36.
    """
    rng = np.random.default_rng(12)
    t, m, w = 4000, 12, 0.36
    factor = rng.standard_normal((t, 1))
    noise = rng.standard_normal((t, m))
    returns = math.sqrt(w) * factor + math.sqrt(1.0 - w) * noise
    with pytest.warns(LinearDependenceWarning):
        rho_bar = mean_off_diagonal_correlation(returns)
    assert rho_bar == pytest.approx(w, abs=0.03)


def test_mean_off_diagonal_correlation_always_warns_about_linear_dependence() -> None:
    rng = np.random.default_rng(13)
    returns = rng.standard_normal((200, 5))
    with pytest.warns(LinearDependenceWarning, match="linear dependence only"):
        mean_off_diagonal_correlation(returns)


def test_correlated_trials_raise_deflated_significance_relative_to_naive_counting() -> None:
    """Counting M correlated trials as independent over-deflates; N_hat is the correction."""
    m, rho_bar = 200, 0.7
    n_hat = effective_number_of_trials(m, rho_bar)
    assert n_hat == pytest.approx(200 * 0.3 + 0.7)
    naive = deflated_sharpe_ratio(
        1.0, trial_dispersion=0.5, n_trials=m, n_observations=120
    ).deflated_significance
    adjusted = deflated_sharpe_ratio(
        1.0, trial_dispersion=0.5, n_trials=n_hat, n_observations=120
    ).deflated_significance
    assert adjusted > naive
