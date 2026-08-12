"""Tests for multiple-testing corrections and bootstrap data-snooping tests.

The Holm and Benjamini-Hochberg fixtures below were derived by hand from the published step
definitions before the implementation was run; the arithmetic is written out in each
docstring so a reader can check it without executing anything.
"""

from __future__ import annotations

import numpy as np
import pytest

from portfolio_edge.inference.multiple_testing import (
    benjamini_hochberg,
    holm_bonferroni,
    reality_check,
    spa_test,
)

# Hand-worked example, M = 5.
#   p            = [0.001, 0.008, 0.039, 0.041, 0.042]
# Holm multipliers (M - i + 1) = [5, 4, 3, 2, 1]
#   raw products = [0.005, 0.032, 0.117, 0.082, 0.042]
#   running max  = [0.005, 0.032, 0.117, 0.117, 0.117]
#   at alpha 0.05 -> reject the first two only.
# BH scaling (M/i) = [5/1, 5/2, 5/3, 5/4, 5/5]
#   raw products = [0.005, 0.020, 0.065, 0.05125, 0.042]
#   reverse cumulative minimum = [0.005, 0.020, 0.042, 0.042, 0.042]
#   at alpha 0.05 -> reject all five.
HAND_P_VALUES = [0.001, 0.008, 0.039, 0.041, 0.042]
HAND_HOLM_ADJUSTED = [0.005, 0.032, 0.117, 0.117, 0.117]
HAND_BH_ADJUSTED = [0.005, 0.020, 0.042, 0.042, 0.042]


def test_holm_bonferroni_matches_the_hand_computed_example() -> None:
    result = holm_bonferroni(HAND_P_VALUES, alpha=0.05)
    assert result.adjusted_p_values == pytest.approx(HAND_HOLM_ADJUSTED)
    assert result.rejected.tolist() == [True, True, False, False, False]
    assert result.n_rejected == 2


def test_benjamini_hochberg_matches_the_hand_computed_example() -> None:
    result = benjamini_hochberg(HAND_P_VALUES, alpha=0.05)
    assert result.adjusted_p_values == pytest.approx(HAND_BH_ADJUSTED)
    assert result.rejected.tolist() == [True] * 5
    assert result.n_rejected == 5


def test_bh_is_never_more_conservative_than_holm() -> None:
    """FDR control rejects at least as much as FWER control, by construction."""
    rng = np.random.default_rng(1)
    for _ in range(20):
        p = rng.uniform(size=30)
        holm = holm_bonferroni(p)
        bh = benjamini_hochberg(p)
        assert np.all(bh.adjusted_p_values <= holm.adjusted_p_values + 1e-12)
        assert bh.n_rejected >= holm.n_rejected


def test_adjusted_p_values_are_returned_in_the_callers_ordering() -> None:
    """Shuffling the input must permute the output identically, not reorder it."""
    permutation = [3, 0, 4, 1, 2]
    shuffled = [HAND_P_VALUES[i] for i in permutation]
    result = holm_bonferroni(shuffled)
    assert result.adjusted_p_values == pytest.approx([HAND_HOLM_ADJUSTED[i] for i in permutation])


def test_both_procedures_are_monotone_and_bounded() -> None:
    result = holm_bonferroni([0.6, 0.7, 0.8, 0.9])
    assert np.all(result.adjusted_p_values <= 1.0)
    assert result.n_rejected == 0
    single = benjamini_hochberg([0.04])
    assert single.adjusted_p_values == pytest.approx([0.04])
    assert single.rejected.tolist() == [True]


def test_holm_handles_ties_without_breaking_step_down_monotonicity() -> None:
    """Four identical p-values of 0.01 at M = 4: products 0.04, 0.03, 0.02, 0.01,
    running max 0.04, 0.04, 0.04, 0.04 — the step-down rule forces them equal."""
    result = holm_bonferroni([0.01, 0.01, 0.01, 0.01])
    assert result.adjusted_p_values == pytest.approx([0.04] * 4)


def test_multiple_testing_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        holm_bonferroni([0.1, 1.5])
    with pytest.raises(ValueError, match="alpha"):
        benjamini_hochberg([0.1, 0.2], alpha=0.0)
    with pytest.raises(ValueError, match="not be empty"):
        holm_bonferroni([])


# --------------------------------------------------------------------------------------
# White's Reality Check and Hansen's SPA
# --------------------------------------------------------------------------------------


def _noise_panel(t: int, m: int, seed: int, phi: float = 0.4) -> np.ndarray:
    """Zero-mean autocorrelated performance differentials: nothing beats the benchmark."""
    rng = np.random.default_rng(seed)
    innovations = rng.standard_normal((t + 200, m))
    out = np.zeros((t + 200, m))
    for i in range(1, t + 200):
        out[i] = phi * out[i - 1] + innovations[i]
    return out[200:] * 0.01


def test_reality_check_controls_size_when_every_strategy_is_noise() -> None:
    """The point of the test: the best of many pure-noise strategies looks good and is not.

    A single p-value is uniform under the null, so this asserts size over 24 independent
    panels rather than on one draw: the 5% rejection rate must not be badly inflated and
    the p-values must not pile up near zero.
    """
    p_values = []
    for seed in range(24):
        panel = _noise_panel(300, 20, seed=1000 + seed)
        p_values.append(
            reality_check(panel, rng=np.random.default_rng(seed), n_resamples=300).p_value
        )
    rejections = sum(p <= 0.05 for p in p_values)
    assert rejections <= 3
    assert float(np.median(p_values)) > 0.20


def test_reality_check_reports_its_inputs() -> None:
    panel = _noise_panel(500, 50, seed=11)
    result = reality_check(panel, rng=np.random.default_rng(21), n_resamples=200)
    assert result.n_strategies == 50
    assert result.n_observations == 500
    assert 0 <= result.best_index < 50
    assert result.bootstrap_statistics.shape == (200,)


def test_reality_check_rejects_a_genuinely_superior_strategy() -> None:
    panel = _noise_panel(500, 20, seed=12)
    panel[:, 7] += 0.004  # a real edge, roughly 0.4 sd of the noise per period
    result = reality_check(panel, rng=np.random.default_rng(22), n_resamples=500)
    assert result.best_index == 7
    assert result.p_value < 0.05


def test_reality_check_is_more_conservative_than_looking_at_the_best_alone() -> None:
    """A single-strategy Reality Check on the winner alone gives a much smaller p-value."""
    panel = _noise_panel(400, 40, seed=13)
    full = reality_check(panel, rng=np.random.default_rng(23), n_resamples=500)
    winner_only = reality_check(
        panel[:, [full.best_index]],
        rng=np.random.default_rng(23),
        n_resamples=500,
        block_length=full.block_length,
    )
    assert full.p_value > winner_only.p_value


def test_reality_check_is_reproducible_from_a_seed() -> None:
    panel = _noise_panel(300, 10, seed=14)
    first = reality_check(panel, rng=np.random.default_rng(99), n_resamples=200)
    second = reality_check(panel, rng=np.random.default_rng(99), n_resamples=200)
    assert first.p_value == second.p_value
    assert np.array_equal(first.bootstrap_statistics, second.bootstrap_statistics)


def test_spa_is_more_powerful_than_the_reality_check_when_padded_with_bad_strategies() -> None:
    """Hansen's recentring is precisely the fix for White's least-favourable null.

    Add 40 strategies that are clearly *worse* than the benchmark. They cannot be the best,
    but under White's null they inflate the critical value, so the Reality Check loses
    power. SPA's consistent recentring removes them from the null and keeps it.
    """
    panel = _noise_panel(500, 45, seed=15)
    panel[:, 0] += 0.0035
    panel[:, 5:] -= 0.02  # loudly inferior strategies
    rc = reality_check(panel, rng=np.random.default_rng(31), n_resamples=800)
    spa = spa_test(panel, rng=np.random.default_rng(31), n_resamples=800)
    assert spa.p_value <= rc.p_value
    assert spa.best_index == 0


def test_spa_recentring_variants_are_ordered() -> None:
    """p_lower <= p_consistent <= p_upper is Hansen's own bracketing of the true p-value.

    It follows from ``g^upper <= g^consistent <= g^lower`` pointwise: a larger recentring
    term shrinks every bootstrap replicate and therefore the p-value.
    """
    panel = _noise_panel(400, 25, seed=16)
    panel[:, 3] += 0.002
    panel[:, 10:] -= 0.01
    lower = spa_test(
        panel,
        rng=np.random.default_rng(41),
        recentring="lower",
        n_resamples=600,
        block_length=6.0,
    )
    consistent = spa_test(
        panel,
        rng=np.random.default_rng(41),
        recentring="consistent",
        n_resamples=600,
        block_length=6.0,
    )
    upper = spa_test(
        panel,
        rng=np.random.default_rng(41),
        recentring="upper",
        n_resamples=600,
        block_length=6.0,
    )
    assert lower.p_value <= consistent.p_value <= upper.p_value
    assert lower.p_value < upper.p_value


def test_spa_does_not_reject_pure_noise() -> None:
    panel = _noise_panel(500, 30, seed=17)
    result = spa_test(panel, rng=np.random.default_rng(51), n_resamples=600)
    assert result.p_value > 0.10
    assert result.method == "hansen-spa-consistent"


def test_bootstrap_tests_pick_a_block_length_and_report_it() -> None:
    panel = _noise_panel(400, 5, seed=18, phi=0.7)
    result = reality_check(panel, rng=np.random.default_rng(61), n_resamples=100)
    assert result.block_length > 1.0
    explicit = reality_check(
        panel, rng=np.random.default_rng(61), n_resamples=100, block_length=3.0
    )
    assert explicit.block_length == 3.0


def test_bootstrap_tests_reject_malformed_panels() -> None:
    with pytest.raises(ValueError, match="four periods"):
        reality_check(np.zeros((3, 2)), rng=np.random.default_rng(0))
    with pytest.raises(ValueError, match="non-finite"):
        spa_test(np.full((10, 2), np.nan), rng=np.random.default_rng(0))
    with pytest.raises(ValueError, match="recentring"):
        spa_test(
            _noise_panel(50, 3, seed=19),
            rng=np.random.default_rng(0),
            n_resamples=10,
            recentring="nonsense",  # type: ignore[arg-type]
        )
