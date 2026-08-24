"""Tests for the block bootstrap and the corrected Politis-White block-length rule.

Fixture sources are cited beside each assertion. The Politis-White logic is checked against
an independent re-implementation written from the published formulas in the docstring of
:func:`_reference_block_length`, and structurally against the archived reference
implementation at http://www.math.ucsd.edu/~politis/SOFT/ppwR.txt (retrieved 2026-08-11).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.inference.bootstrap import (
    STATIONARY_TO_CIRCULAR_ARE,
    autocorrelation,
    autocovariance,
    bootstrap_confidence_interval,
    circular_block_indices,
    iid_bootstrap_indices,
    optimal_block_length,
    stationary_bootstrap_indices,
)


def ar1_series(n: int, phi: float, seed: int, burn: int = 500) -> np.ndarray:
    """AR(1) path with an explicit seed; deterministic given (n, phi, seed, burn)."""
    rng = np.random.default_rng(seed)
    innovations = rng.standard_normal(n + burn)
    out = np.zeros(n + burn)
    for t in range(1, n + burn):
        out[t] = phi * out[t - 1] + innovations[t]
    return out[burn:]


# --------------------------------------------------------------------------------------
# Autocovariance versus autocorrelation
# --------------------------------------------------------------------------------------


def test_autocovariance_uses_the_1_over_n_divisor_at_every_lag() -> None:
    """Independent hand computation on a five-point series.

    x = [1, 2, 3, 4, 5], mean 3, centred [-2, -1, 0, 1, 2].
    R(0) = (4+1+0+1+4)/5 = 2.0
    R(1) = ((-2)(-1) + (-1)(0) + (0)(1) + (1)(2))/5 = (2+0+0+2)/5 = 0.8
    R(2) = ((-2)(0) + (-1)(1) + (0)(2))/5 = -0.2
    Matches R's ``acf(type="covariance")``, which the ppwR.txt reference uses.
    """
    gamma = autocovariance([1.0, 2.0, 3.0, 4.0, 5.0], 2)
    assert gamma == pytest.approx([2.0, 0.8, -0.2])


def test_autocorrelation_is_the_autocovariance_divided_by_lag_zero() -> None:
    """rho(k) = R(k)/R(0) — the lag-selection step uses this, the block formula uses R(k).

    From the fixture above: rho = [1.0, 0.4, -0.1].
    """
    rho = autocorrelation([1.0, 2.0, 3.0, 4.0, 5.0], 2)
    assert rho == pytest.approx([1.0, 0.4, -0.1])
    gamma = autocovariance([1.0, 2.0, 3.0, 4.0, 5.0], 2)
    assert rho == pytest.approx(gamma / gamma[0])
    # The two are numerically distinct here, so a port that swapped them would fail.
    assert not np.allclose(rho, gamma)


def test_autocorrelation_rejects_a_constant_series() -> None:
    with pytest.raises(ValueError, match="zero variance"):
        autocorrelation(np.ones(20), 3)


# --------------------------------------------------------------------------------------
# The Patton-Politis-White (2009) correction
# --------------------------------------------------------------------------------------


def test_asymptotic_relative_efficiency_reproduces_the_correction_constant() -> None:
    """PPW 2009: D_SB = 2 g(0)^2 (not the pre-2009 constant), giving ARE (2/3)^(2/3).

    Source: docs/research/portfolio-engine-specification.md, "Resampling"; Patton, Politis
    and White (2009), https://www.math.ucsd.edu/~politis/PAPER/SBblockCORRECTION.pdf
    """
    assert pytest.approx(0.7631428, abs=5e-8) == STATIONARY_TO_CIRCULAR_ARE
    assert pytest.approx((2.0 / 3.0) ** (2.0 / 3.0)) == STATIONARY_TO_CIRCULAR_ARE


def test_the_are_follows_from_the_d_constants_the_code_actually_uses() -> None:
    """The constant is not free-standing: it is (D_CB / D_SB)^(2/3) from the fitted terms.

    The minimised MSE of the block-length-optimal variance estimator is proportional to
    D^(2/3), so the efficiency ratio is (D_CB/D_SB)^(2/3). If someone reinstated the
    pre-2009 D_SB this test fails, which is the point.
    """
    selection = optimal_block_length(ar1_series(2000, 0.6, seed=11))
    assert selection.d_sb == pytest.approx(2.0 * selection.g_zero**2)
    assert selection.d_cb == pytest.approx((4.0 / 3.0) * selection.g_zero**2)
    assert (selection.d_cb / selection.d_sb) ** (2.0 / 3.0) == pytest.approx(
        STATIONARY_TO_CIRCULAR_ARE
    )


def test_stationary_block_is_shorter_than_circular_by_the_cube_root_ratio() -> None:
    """b_SB / b_CB = (D_CB/D_SB)^(1/3) = (2/3)^(1/3) = 0.873580.

    Cross-check against the archived output in ppwR.txt, whose own example prints
    BstarSB/BstarCB = 50.39272/57.68526 = 0.8735805 and 251.62894/288.04323 = 0.8735805.
    Reproducing that ratio to seven digits confirms both D constants simultaneously.
    """
    expected_ratio = (2.0 / 3.0) ** (1.0 / 3.0)
    assert pytest.approx(expected_ratio, abs=1e-6) == 50.39272 / 57.68526
    assert pytest.approx(expected_ratio, abs=1e-6) == 251.62894 / 288.04323
    for phi, seed in ((0.5, 1), (0.8, 2), (-0.3, 3)):
        selection = optimal_block_length(ar1_series(5000, phi, seed=seed))
        assert selection.stationary / selection.circular == pytest.approx(
            expected_ratio, rel=1e-9
        )


def _reference_block_length(x: np.ndarray) -> tuple[float, float]:
    """Independent re-implementation of ppwR.txt in plain Python loops.

    Written from the published formulas rather than from the module under test:
      lam(s) = 1 for |s| < 1/2, 2(1-|s|) for 1/2 <= |s| <= 1, else 0
      Kn = max(5, ceil(log10 n)); mmax = ceil(sqrt n) + Kn; c = qnorm(0.975)
      rho crit = c sqrt(log10(n)/n); mhat per footnote (c); M = min(2 mhat, mmax)
    (when no run of Kn insignificant lags exists, mhat is the largest significant lag,
    which subsumes the "sole significant lag" case)
      Ghat = sum_k lam(k/M) |k| R(k);  ghat0 = sum_k lam(k/M) R(k)
      b_SB = (2 Ghat^2 / (2 ghat0^2))^(1/3) n^(1/3)
      b_CB = (2 Ghat^2 / ((4/3) ghat0^2))^(1/3) n^(1/3)
    """
    values = [float(v) for v in x]
    n = len(values)
    mean = sum(values) / n

    def r(k: int) -> float:
        return sum((values[t] - mean) * (values[t + k] - mean) for t in range(n - k)) / n

    def lam(s: float) -> float:
        a = abs(s)
        if a < 0.5:
            return 1.0
        if a <= 1.0:
            return 2.0 * (1.0 - a)
        return 0.0

    k_n = max(5, math.ceil(math.log10(n)))
    m_max = min(math.ceil(math.sqrt(n)) + k_n, n - 1)
    r0 = r(0)
    rho = [r(k) / r0 for k in range(1, m_max + 1)]
    crit = 1.959963984540054 * math.sqrt(math.log10(n) / n)
    insignificant = [abs(v) < crit for v in rho]

    m_hat = None
    for j in range(m_max - k_n + 1):
        if all(insignificant[j : j + k_n]):
            m_hat = j + 1
            break
    if m_hat is None:
        significant = [i + 1 for i, flag in enumerate(insignificant) if not flag]
        m_hat = max(significant) if significant else 1
    m = m_max if 2 * m_hat > m_max else 2 * m_hat

    g_hat = sum(lam(k / m) * abs(k) * r(abs(k)) for k in range(-m, m + 1))
    g_zero = sum(lam(k / m) * r(abs(k)) for k in range(-m, m + 1))
    scale = n ** (1.0 / 3.0)
    b_sb = (2.0 * g_hat**2 / (2.0 * g_zero**2)) ** (1.0 / 3.0) * scale
    b_cb = (2.0 * g_hat**2 / ((4.0 / 3.0) * g_zero**2)) ** (1.0 / 3.0) * scale
    b_max = math.ceil(min(3.0 * math.sqrt(n), n / 3.0))
    return min(max(b_sb, 1.0), b_max), min(max(b_cb, 1.0), b_max)


@pytest.mark.parametrize(("phi", "seed"), [(0.0, 21), (0.4, 22), (0.7, 23), (-0.5, 24)])
def test_block_length_matches_an_independent_reimplementation(phi: float, seed: int) -> None:
    """Vectorised implementation against a plain-Python transcription of ppwR.txt."""
    series = ar1_series(600, phi, seed=seed)
    selection = optimal_block_length(series)
    expected_sb, expected_cb = _reference_block_length(series)
    assert selection.stationary == pytest.approx(expected_sb, rel=1e-10)
    assert selection.circular == pytest.approx(expected_cb, rel=1e-10)


def test_block_length_tracks_persistence() -> None:
    """More persistent series need longer blocks; this is the rule's whole purpose."""
    lengths = [
        optimal_block_length(ar1_series(4000, phi, seed=31)).stationary
        for phi in (0.0, 0.3, 0.6, 0.9)
    ]
    assert lengths == sorted(lengths)
    assert lengths[0] < 3.0
    assert lengths[-1] > 20.0


def test_block_length_respects_b_max_and_the_unit_floor() -> None:
    selection = optimal_block_length(ar1_series(300, 0.99, seed=41))
    assert 1.0 <= selection.stationary <= selection.b_max
    assert selection.b_max == math.ceil(min(3.0 * math.sqrt(300), 100.0))
    white_noise = np.random.default_rng(42).standard_normal(500)
    assert optimal_block_length(white_noise).stationary >= 1.0


def test_block_length_defaults_follow_the_reference_implementation() -> None:
    """Kn = max(5, ceil(log10 n)); mmax = ceil(sqrt n) + Kn; Bmax = ceil(min(3 sqrt n, n/3))."""
    selection = optimal_block_length(ar1_series(1000, 0.5, seed=51))
    assert selection.k_n == 5
    assert selection.m_max == math.ceil(math.sqrt(1000)) + 5
    assert selection.b_max == math.ceil(min(3.0 * math.sqrt(1000), 1000 / 3.0))
    assert selection.m == min(2 * selection.m_hat, selection.m_max)


# --------------------------------------------------------------------------------------
# Resampling mechanics
# --------------------------------------------------------------------------------------


def test_every_observation_is_equally_likely_under_the_circular_bootstrap() -> None:
    """The circular wrap is what removes the moving-block bootstrap's end-effect bias."""
    rng = np.random.default_rng(101)
    n, block = 25, 5
    indices = circular_block_indices(n, block, 40000, rng)
    counts = np.bincount(indices.ravel(), minlength=n).astype(float)
    frequencies = counts / counts.sum()
    assert frequencies == pytest.approx(np.full(n, 1.0 / n), abs=0.002)


def test_circular_blocks_are_contiguous_modulo_n() -> None:
    rng = np.random.default_rng(102)
    n, block = 12, 4
    indices = circular_block_indices(n, block, 50, rng)
    for row in indices:
        for offset in range(0, n, block):
            chunk = row[offset : offset + block]
            expected = (chunk[0] + np.arange(chunk.size)) % n
            assert np.array_equal(chunk, expected)


def test_stationary_bootstrap_block_lengths_are_geometric_on_average() -> None:
    """Mean run length should approach the requested mean block length."""
    rng = np.random.default_rng(103)
    n, mean_block = 400, 8.0
    indices = stationary_bootstrap_indices(n, mean_block, 400, rng)
    continuations = ((indices[:, 1:] - indices[:, :-1]) % n) == 1
    # P(continue) = 1 - 1/L, so the observed continuation rate identifies L.
    observed_mean_block = 1.0 / (1.0 - continuations.mean())
    assert observed_mean_block == pytest.approx(mean_block, rel=0.06)


@pytest.mark.parametrize(
    "draw",
    [
        lambda rng: circular_block_indices(50, 6, 20, rng),
        lambda rng: stationary_bootstrap_indices(50, 6.0, 20, rng),
        lambda rng: iid_bootstrap_indices(50, 20, rng),
    ],
)
def test_resampling_is_exactly_reproducible_from_a_seed(draw) -> None:  # type: ignore[no-untyped-def]
    first = draw(np.random.default_rng(2024))
    second = draw(np.random.default_rng(2024))
    third = draw(np.random.default_rng(2025))
    assert np.array_equal(first, second)
    assert not np.array_equal(first, third)


def test_resamplers_reject_degenerate_arguments() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="block_length"):
        circular_block_indices(10, 0.0, 5, rng)
    with pytest.raises(ValueError, match="mean_block_length"):
        stationary_bootstrap_indices(10, 0.5, 5, rng)
    with pytest.raises(ValueError, match="n_resamples"):
        iid_bootstrap_indices(10, 0, rng)


# --------------------------------------------------------------------------------------
# Confidence intervals — the reason the module exists
# --------------------------------------------------------------------------------------


def _sharpe(x: np.ndarray) -> float:
    sd = float(np.std(x, ddof=1))
    return float(np.mean(x)) / sd if sd > 0.0 else 0.0


def _max_drawdown(x: np.ndarray) -> float:
    equity = np.cumprod(1.0 + x)
    return float(np.min(equity / np.maximum.accumulate(equity)) - 1.0)


def test_iid_bootstrap_intervals_are_materially_narrower_on_an_ar1_series() -> None:
    """The whole reason this module exists.

    An i.i.d. bootstrap destroys serial dependence, so it understates the sampling
    variability of any statistic that depends on it. On a strongly autocorrelated series
    the i.i.d. interval for the mean must be much narrower than the block interval — the
    narrowness is the bug, not a feature.

    Source: docs/research/portfolio-engine-specification.md, "Resampling".
    """
    series = ar1_series(500, 0.8, seed=777) * 0.01

    def sample_mean(x: np.ndarray) -> float:
        return float(np.mean(x))

    iid = bootstrap_confidence_interval(
        series, sample_mean, rng=np.random.default_rng(5), method="iid", n_resamples=2000
    )
    circular = bootstrap_confidence_interval(
        series, sample_mean, rng=np.random.default_rng(5), method="circular", n_resamples=2000
    )
    stationary = bootstrap_confidence_interval(
        series, sample_mean, rng=np.random.default_rng(5), method="stationary", n_resamples=2000
    )
    assert circular.width > 1.5 * iid.width
    assert stationary.width > 1.5 * iid.width
    # And the block bootstrap should be in the right neighbourhood of the true long-run
    # standard error: for AR(1), sd(mean) inflates by 1/(1-phi) = 5 relative to i.i.d.
    assert circular.standard_error / iid.standard_error > 2.0


def test_block_bootstrap_widens_a_sharpe_interval_too() -> None:
    series = ar1_series(400, 0.7, seed=778) * 0.01 + 0.002
    iid = bootstrap_confidence_interval(
        series, _sharpe, rng=np.random.default_rng(9), method="iid", n_resamples=1500
    )
    block = bootstrap_confidence_interval(
        series, _sharpe, rng=np.random.default_rng(9), method="circular", n_resamples=1500
    )
    assert block.width > iid.width


def test_confidence_interval_covers_the_point_estimate_and_reports_its_inputs() -> None:
    series = ar1_series(300, 0.4, seed=779) * 0.01 + 0.003
    result = bootstrap_confidence_interval(
        series, _max_drawdown, rng=np.random.default_rng(13), method="stationary", n_resamples=500
    )
    assert result.lower <= result.point_estimate <= result.upper
    assert result.point_estimate == pytest.approx(_max_drawdown(series))
    assert result.method == "stationary"
    assert result.n_resamples == 500
    assert result.replicates.shape == (500,)
    assert result.block_length == pytest.approx(optimal_block_length(series).stationary)


def test_basic_and_percentile_intervals_reflect_each_other_about_the_estimate() -> None:
    """The basic interval is the percentile interval reflected through the point estimate."""
    series = ar1_series(200, 0.3, seed=780) * 0.01

    def sample_mean(x: np.ndarray) -> float:
        return float(np.mean(x))

    percentile = bootstrap_confidence_interval(
        series,
        sample_mean,
        rng=np.random.default_rng(3),
        method="circular",
        block_length=5.0,
        n_resamples=400,
    )
    basic = bootstrap_confidence_interval(
        series,
        sample_mean,
        rng=np.random.default_rng(3),
        method="circular",
        block_length=5.0,
        n_resamples=400,
        interval="basic",
    )
    assert basic.width == pytest.approx(percentile.width)
    assert basic.lower == pytest.approx(2.0 * percentile.point_estimate - percentile.upper)
    assert basic.upper == pytest.approx(2.0 * percentile.point_estimate - percentile.lower)


def test_confidence_interval_is_reproducible_and_rejects_bad_levels() -> None:
    series = ar1_series(120, 0.2, seed=781)
    first = bootstrap_confidence_interval(
        series, lambda x: float(np.mean(x)), rng=np.random.default_rng(77), n_resamples=200
    )
    second = bootstrap_confidence_interval(
        series, lambda x: float(np.mean(x)), rng=np.random.default_rng(77), n_resamples=200
    )
    assert first.lower == second.lower
    assert first.upper == second.upper
    with pytest.raises(ValueError, match="confidence_level"):
        bootstrap_confidence_interval(
            series,
            lambda x: float(np.mean(x)),
            rng=np.random.default_rng(1),
            confidence_level=1.5,
        )
