"""Tests for Newey-West / HAC standard errors.

The cross-check against ``statsmodels`` ``cov_type='HAC'`` is a check against a widely used
independent *codebase*, not against an independent *derivation*: both implement the same
Newey-West sandwich from the same published formula, so agreement rules out coding slips
but cannot rule out a shared misreading of the estimator. The closed-form AR(1) test below
is the check that does not share an implementation.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import statsmodels.api as sm

from portfolio_edge.inference.hac import (
    bartlett_weights,
    hac_mean,
    hac_ols,
    long_run_variance,
    newey_west_lag_count,
)


def ar1_series(n: int, phi: float, seed: int, burn: int = 500) -> np.ndarray:
    rng = np.random.default_rng(seed)
    innovations = rng.standard_normal(n + burn)
    out = np.zeros(n + burn)
    for t in range(1, n + burn):
        out[t] = phi * out[t - 1] + innovations[t]
    return out[burn:]


def test_bandwidth_rule_is_the_documented_newey_west_1994_form() -> None:
    """L = floor(4 (T/100)^(2/9)); hand-computed at three sizes.

    T = 100: 4 * 1^(2/9) = 4.0 -> 4
    T = 1000: 4 * 10^(2/9) = 4 * 1.66810 = 6.672 -> 6
    T = 12: 4 * 0.12^(2/9) = 4 * 0.62556 = 2.502 -> 2
    """
    assert newey_west_lag_count(100) == 4
    assert newey_west_lag_count(1000) == 6
    assert newey_west_lag_count(12) == 2
    for t in (5, 50, 250, 5000):
        assert newey_west_lag_count(t) == math.floor(4.0 * (t / 100.0) ** (2.0 / 9.0))


def test_bartlett_weights_decline_linearly_to_zero() -> None:
    """w_j = 1 - j/(L+1); at L = 4 that is [0.8, 0.6, 0.4, 0.2]."""
    assert bartlett_weights(4) == pytest.approx([0.8, 0.6, 0.4, 0.2])
    assert bartlett_weights(0).size == 0


def test_long_run_variance_matches_a_hand_computed_example() -> None:
    """u = [1, -1, 2, -2, 1], L = 1, so w_1 = 0.5.

    gamma_0 = (1 + 1 + 4 + 4 + 1)/5 = 2.2
    gamma_1 = ((1)(-1) + (-1)(2) + (2)(-2) + (-2)(1))/5 = (-1 - 2 - 4 - 2)/5 = -1.8
    S = 2.2 + 2 * 0.5 * (-1.8) = 0.4
    """
    u = np.array([1.0, -1.0, 2.0, -2.0, 1.0])
    assert long_run_variance(u, n_lags=1) == pytest.approx(0.4)
    assert long_run_variance(u, n_lags=0) == pytest.approx(2.2)


def test_hac_mean_inflates_the_standard_error_under_positive_autocorrelation() -> None:
    """For AR(1) with phi > 0 the long-run variance is gamma_0 (1+phi)/(1-phi) > gamma_0.

    At phi = 0.7 that factor is 5.667, so the HAC standard error must exceed the i.i.d. one
    substantially. The Bartlett truncation biases the estimate downwards, so this asserts a
    direction and a loose magnitude, not equality.
    """
    series = ar1_series(4000, 0.7, seed=101)
    result = hac_mean(series, n_lags=20)
    naive = float(np.std(series, ddof=1)) / math.sqrt(series.size)
    assert result.standard_error > 1.8 * naive
    assert result.n_lags == 20
    assert result.n_observations == 4000


def test_hac_mean_collapses_to_the_iid_standard_error_at_zero_lags() -> None:
    series = np.random.default_rng(7).standard_normal(200)
    result = hac_mean(series, n_lags=0)
    expected = float(np.std(series, ddof=0)) / math.sqrt(series.size)
    assert result.standard_error == pytest.approx(expected)


def test_hac_mean_matches_statsmodels_via_a_constant_only_regression() -> None:
    """A mean is OLS on a constant, so statsmodels HAC on that regression is the same thing.

    Independent-codebase check, not an independent derivation.
    """
    series = ar1_series(500, 0.6, seed=202)
    ours = hac_mean(series, n_lags=5)
    reference = sm.OLS(series, np.ones((series.size, 1))).fit(
        cov_type="HAC", cov_kwds={"maxlags": 5, "use_correction": False}
    )
    assert ours.mean == pytest.approx(float(reference.params[0]))
    assert ours.standard_error == pytest.approx(float(reference.bse[0]), rel=1e-10)


@pytest.mark.parametrize("n_lags", [0, 1, 4, 12])
def test_hac_ols_matches_statsmodels(n_lags: int) -> None:
    """Newey-West sandwich against statsmodels ``cov_type='HAC'``.

    statsmodels' ``use_correction=False`` is the plain asymptotic sandwich; ``True`` adds
    the T/(T-k) degrees-of-freedom factor, which this module exposes as ``dof_correction``.
    Again: a shared formula implemented twice, not two independent derivations.
    """
    rng = np.random.default_rng(303)
    t = 300
    x = rng.standard_normal((t, 2))
    errors = ar1_series(t, 0.7, seed=404)
    y = 1.0 + 0.5 * x[:, 0] - 0.3 * x[:, 1] + errors

    ours = hac_ols(y, x, n_lags=n_lags)
    design = sm.add_constant(x)
    reference = sm.OLS(y, design).fit(
        cov_type="HAC", cov_kwds={"maxlags": n_lags, "use_correction": False}
    )
    assert ours.coefficients == pytest.approx(np.asarray(reference.params), rel=1e-10)
    assert ours.standard_errors == pytest.approx(np.asarray(reference.bse), rel=1e-9)
    assert ours.covariance == pytest.approx(np.asarray(reference.cov_params()), rel=1e-9)

    corrected = hac_ols(y, x, n_lags=n_lags, dof_correction=True)
    reference_corrected = sm.OLS(y, design).fit(
        cov_type="HAC", cov_kwds={"maxlags": n_lags, "use_correction": True}
    )
    assert corrected.standard_errors == pytest.approx(np.asarray(reference_corrected.bse), rel=1e-9)


def test_hac_ols_reduces_to_ols_point_estimates_and_reports_shape() -> None:
    rng = np.random.default_rng(505)
    x = rng.standard_normal((120, 3))
    y = x @ np.array([1.0, -2.0, 0.5]) + rng.standard_normal(120)
    result = hac_ols(y, x, add_constant=False, n_lags=2)
    expected, *_ = np.linalg.lstsq(x, y, rcond=None)
    assert result.coefficients == pytest.approx(expected)
    assert result.n_parameters == 3
    assert result.residuals.shape == (120,)
    assert result.p_values.shape == (3,)
    # Sandwich covariance must be symmetric.
    assert result.covariance == pytest.approx(result.covariance.T)


def test_hac_ols_default_bandwidth_is_the_documented_rule() -> None:
    rng = np.random.default_rng(606)
    x = rng.standard_normal((250, 1))
    y = x[:, 0] + rng.standard_normal(250)
    assert hac_ols(y, x).n_lags == newey_west_lag_count(250)


def test_hac_ols_rejects_malformed_inputs() -> None:
    rng = np.random.default_rng(707)
    x = rng.standard_normal((50, 2))
    y = rng.standard_normal(50)
    with pytest.raises(ValueError, match="rows"):
        hac_ols(y[:40], x)
    with pytest.raises(ValueError, match="n_lags"):
        hac_ols(y, x, n_lags=50)
    with pytest.raises(ValueError, match="more observations"):
        hac_ols(y[:2], x[:2])
