"""Unit tests for :mod:`portfolio_edge.studies.conditional_breadth`.

No market data. The panel fixture is built from orthogonal sign patterns so that inside
the condition every pairwise correlation is known exactly by construction, and outside it
the legs are wired differently so the unconditional matrix cannot accidentally agree with
the conditional one. The effective-bet count is then checked against the closed form
``2 / (1 + a) + 1`` for a matrix with one correlated pair and one orthogonal leg, which
shares no arithmetic with the ``1' R^-1 1`` solve under test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.conditional_breadth import (
    MINIMUM_CONDITION_MONTHS,
    conditional_breadth,
    effective_observations,
    trailing_negative_mask,
    window_mask,
    worst_quantile_mask,
)

#: The correlation planted between the two tilts inside the condition.
PLANTED = 0.6

#: A constant added to the second tilt inside the condition, so its conditional mean is
#: known and non-zero while the first tilt's is exactly zero.
SHIFT = 0.25


def _patterns(length: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Three mutually orthogonal, zero-mean, unit-variance sign sequences of ``length``.

    Requires ``length`` to be a multiple of 8, which makes the three patterns exactly
    orthogonal and exactly zero-mean, so every sample correlation below is exact rather
    than approximate.
    """
    assert length % 8 == 0
    base = np.arange(length)
    u = np.where(base % 2 == 0, 1.0, -1.0)
    v = np.where((base // 2) % 2 == 0, 1.0, -1.0)
    w = np.where((base // 4) % 2 == 0, 1.0, -1.0)
    return u, v, w


def _fixture() -> tuple[tuple[str, ...], np.ndarray, np.ndarray]:
    """Labels, a ``(months, 3)`` panel and a mask selecting the second half of it.

    Inside the mask: ``a = u``, ``b = PLANTED u + sqrt(1 - PLANTED^2) w + SHIFT``,
    ``trend = v``. So corr(a, b) = PLANTED, corr(a, trend) = 0, corr(b, trend) = 0,
    mean(a) = 0, mean(b) = SHIFT. Outside the mask: ``b = -u`` and ``trend = u``, which
    puts the unconditional correlations nowhere near the planted ones.
    """
    half = 48
    u, v, w = _patterns(half)
    inside = np.column_stack([u, PLANTED * u + math.sqrt(1.0 - PLANTED**2) * w + SHIFT, v])
    outside = np.column_stack([u, -u, u])
    panel = np.vstack([outside, inside])
    mask = np.concatenate([np.zeros(half, dtype=bool), np.ones(half, dtype=bool)])
    return ("a", "b", "trend"), panel, mask


# --------------------------------------------------------------------------- masks


def test_worst_quantile_mask_selects_the_floor_of_q_n_lowest_months() -> None:
    base = np.array([0.05, -0.30, 0.01, -0.10, 0.02, -0.20, 0.03, 0.00, 0.04, -0.05, 0.06])
    mask = worst_quantile_mask(base, quantile=0.30)
    # floor(0.3 * 11) = 3: the three lowest are -0.30, -0.20, -0.10.
    assert mask.sum() == 3
    assert set(np.flatnonzero(mask)) == {1, 3, 5}
    with pytest.raises(ValueError, match="quantile"):
        worst_quantile_mask(base, quantile=0.5)


def test_window_mask_is_the_inclusive_union_of_named_windows() -> None:
    periods = ["2007-10", "2007-11", "2007-12", "2008-01", "2020-02", "2020-03", "2020-04"]
    mask = window_mask(
        periods, {"gfc": ("2007-11", "2007-12"), "covid": ("2020-02", "2020-03")}
    )
    assert mask.tolist() == [False, True, True, False, True, True, False]
    # A window the panel does not cover contributes nothing and is not an error.
    assert window_mask(periods, {"1929": ("1929-09", "1932-06")}).sum() == 0
    with pytest.raises(ValueError, match="runs backwards"):
        window_mask(periods, {"bad": ("2008-01", "2007-11")})


def test_trailing_negative_mask_compounds_over_the_window_including_the_month() -> None:
    # Three-month window. Returns: +10%, -5%, -6%, +12%, +1%.
    r = np.array([0.10, -0.05, -0.06, 0.12, 0.01])
    mask = trailing_negative_mask(r, months=3)
    # First two months cannot be evaluated.
    assert mask[:2].tolist() == [False, False]
    # 1.10 * 0.95 * 0.94 = 0.9823 < 1 -> True at index 2.
    assert mask[2]
    # 0.95 * 0.94 * 1.12 = 1.0002 > 1 -> False at index 3.
    assert not mask[3]
    # 0.94 * 1.12 * 1.01 > 1 -> False at index 4.
    assert not mask[4]
    with pytest.raises(ValueError, match="months"):
        trailing_negative_mask(r, months=0)


# ----------------------------------------------------------- the conditional matrix


def test_conditional_correlation_and_effective_bets_are_the_planted_values() -> None:
    labels, panel, mask = _fixture()
    result = conditional_breadth(
        labels,
        panel,
        mask,
        name="planted",
        trend_label="trend",
        rng=np.random.default_rng(0),
        n_resamples=200,
    )
    assert result.months == 48
    assert result.share_of_panel == pytest.approx(0.5)
    r = np.asarray(result.correlation)
    assert r[0, 1] == pytest.approx(PLANTED, abs=1e-12)
    assert r[0, 2] == pytest.approx(0.0, abs=1e-12)
    assert r[1, 2] == pytest.approx(0.0, abs=1e-12)
    # 1'R^-1 1 for [[1, a, 0], [a, 1, 0], [0, 0, 1]] is 2/(1+a) + 1, by hand.
    assert result.effective_bets == pytest.approx(2.0 / (1.0 + PLANTED) + 1.0, abs=1e-12)
    assert result.effective_bets_lower <= result.effective_bets <= result.effective_bets_upper
    assert 2 <= result.resamples_kept <= 200

    pairs = {pair.label: pair for pair in result.trend_pairs}
    assert set(pairs) == {"a", "b"}
    assert pairs["a"].correlation == pytest.approx(0.0, abs=1e-12)
    assert pairs["b"].correlation == pytest.approx(0.0, abs=1e-12)
    assert pairs["a"].lower <= 0.0 <= pairs["a"].upper


def test_the_unconditional_matrix_differs_from_the_conditional_one() -> None:
    """Guards the fixture: outside the mask ``b = -a`` and ``trend = a``."""
    labels, panel, mask = _fixture()
    everything = conditional_breadth(
        labels,
        panel,
        np.ones(len(mask), dtype=bool),
        name="all",
        trend_label="trend",
        rng=np.random.default_rng(0),
        n_resamples=50,
    )
    r = np.asarray(everything.correlation)
    assert r[0, 1] < 0.0
    assert r[0, 2] > 0.0
    assert everything.effective_bets != pytest.approx(2.0 / (1.0 + PLANTED) + 1.0)


def test_conditional_means_and_intervals() -> None:
    labels, panel, mask = _fixture()
    result = conditional_breadth(
        labels,
        panel,
        mask,
        name="planted",
        trend_label="trend",
        rng=np.random.default_rng(1),
        n_resamples=50,
    )
    legs = {leg.label: leg for leg in result.legs}
    assert legs["a"].mean == pytest.approx(0.0, abs=1e-12)
    assert legs["b"].mean == pytest.approx(SHIFT, abs=1e-12)
    assert legs["a"].standard_error > 0.0
    assert legs["a"].lower < 0.0 < legs["a"].upper
    assert legs["b"].lower < SHIFT < legs["b"].upper
    assert legs["a"].hit_rate == pytest.approx(0.5)
    assert legs["a"].worst == -1.0
    assert 0.0 < legs["a"].effective_months <= 48


def test_effective_observations_is_n_for_white_noise_and_below_n_for_a_run() -> None:
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(2000)
    assert effective_observations(noise) == pytest.approx(2000, rel=0.15)
    # An AR(1) with coefficient 0.8 has long-run variance 9x its variance, so the
    # effective count is about n/9.
    ar = np.empty(2000)
    ar[0] = 0.0
    for i in range(1, 2000):
        ar[i] = 0.8 * ar[i - 1] + rng.standard_normal()
    assert effective_observations(ar) < 2000 / 4
    # Never above n.
    alternating = np.tile([1.0, -1.0], 100)
    assert effective_observations(alternating) == 200.0


# ------------------------------------------------------------------------- refusals


def test_conditional_breadth_refuses_a_thin_condition() -> None:
    labels, panel, mask = _fixture()
    thin = np.zeros(len(mask), dtype=bool)
    thin[: MINIMUM_CONDITION_MONTHS - 1] = True
    with pytest.raises(ValueError, match="below the"):
        conditional_breadth(
            labels, panel, thin, name="thin", trend_label="trend", rng=np.random.default_rng(0)
        )


def test_conditional_breadth_rejects_misaligned_inputs() -> None:
    labels, panel, mask = _fixture()
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="mask must have one entry"):
        conditional_breadth(labels, panel, mask[:-1], name="x", trend_label="trend", rng=rng)
    with pytest.raises(ValueError, match="panel must be"):
        conditional_breadth(labels, panel[:, :2], mask, name="x", trend_label="trend", rng=rng)
    with pytest.raises(ValueError, match="trend_label"):
        conditional_breadth(labels, panel, mask, name="x", trend_label="nope", rng=rng)
