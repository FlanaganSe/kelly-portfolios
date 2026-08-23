"""Unit tests for :mod:`portfolio_edge.studies.stress_dependence`.

Every fixture here is constructed so the answer is known before the code runs — either
by hand arithmetic or by a design where the statistic is exact — because a stress
statistic that agrees with itself proves nothing.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.stress_dependence import (
    convexity,
    engine_summary,
    episode_returns,
    tail_dependence,
)

# --------------------------------------------------------------------------- episodes


def test_episode_returns_compounds_within_the_window() -> None:
    periods = ["2007-11", "2007-12", "2008-01", "2008-02"]
    series = [0.10, -0.20, 0.05, 0.00]
    (row,) = episode_returns(periods, series, windows={"w": ("2007-11", "2008-01")})
    assert row.months == 3
    assert row.covered and not row.partial
    # 1.10 * 0.80 * 1.05 - 1
    assert row.cumulative_return == pytest.approx(1.10 * 0.80 * 1.05 - 1.0)
    assert row.worst_month == pytest.approx(-0.20)
    # peak 1.10, trough 0.88 -> -0.20; the 1.05 month does not recover the peak.
    assert row.peak_to_trough == pytest.approx(0.88 / 1.10 - 1.0)


def test_episode_returns_reports_an_uncovered_window_rather_than_dropping_it() -> None:
    rows = episode_returns(
        ["2020-01", "2020-02"],
        [0.01, 0.01],
        windows={"covered": ("2020-01", "2020-02"), "1929": ("1929-09", "1932-06")},
    )
    assert [r.window for r in rows] == ["covered", "1929"]
    missing = rows[1]
    assert missing.covered is False
    assert missing.months == 0
    assert math.isnan(missing.cumulative_return)


def test_episode_returns_flags_partial_coverage() -> None:
    # The window spans three calendar months; the panel supplies two of them.
    (row,) = episode_returns(
        ["2008-09", "2008-10"], [0.0, 0.0], windows={"w": ("2008-09", "2008-11")}
    )
    assert row.covered is True
    assert row.partial is True
    assert row.months == 2


def test_episode_returns_rejects_a_backwards_window() -> None:
    with pytest.raises(ValueError, match="runs backwards"):
        episode_returns(["2020-01"], [0.0], windows={"w": ("2020-03", "2020-01")})


def test_episode_returns_rejects_misaligned_inputs() -> None:
    with pytest.raises(ValueError, match="aligned"):
        episode_returns(["2020-01", "2020-02"], [0.0], windows={})


# ---------------------------------------------------------------------- tail behaviour


def test_tail_dependence_selects_the_worst_months_of_the_base_only() -> None:
    # 100 months. The base is a ramp, so the worst decile is exactly the first ten
    # entries and the best decile exactly the last ten, whatever the engine does.
    base = np.linspace(-0.20, 0.20, 100)
    engine = np.zeros(100)
    engine[:10] = 0.05  # pays in every lower-tail month
    engine[-10:] = -0.01
    result = tail_dependence(base, engine, quantile=0.10)
    assert result.months_low == 10
    assert result.mean_low == pytest.approx(0.05)
    assert result.mean_high == pytest.approx(-0.01)
    assert result.hit_rate_low == pytest.approx(1.0)
    assert result.base_mean_low < result.base_mean_high


def test_tail_dependence_hit_rate_separates_reliable_from_lottery_payoffs() -> None:
    base = np.linspace(-0.20, 0.20, 100)
    lottery = np.zeros(100)
    lottery[0] = 0.50  # one enormous month carries the mean
    steady = np.zeros(100)
    steady[:10] = 0.05
    a = tail_dependence(base, lottery, quantile=0.10)
    b = tail_dependence(base, steady, quantile=0.10)
    assert a.mean_low == pytest.approx(b.mean_low)
    assert a.hit_rate_low == pytest.approx(0.10)
    assert b.hit_rate_low == pytest.approx(1.0)


def test_tail_dependence_refuses_a_tail_below_the_floor() -> None:
    base = np.linspace(-0.1, 0.1, 40)
    with pytest.raises(ValueError, match="below the"):
        tail_dependence(base, base, quantile=0.10)


def test_tail_dependence_rejects_a_quantile_outside_the_open_unit_half() -> None:
    base = np.linspace(-0.1, 0.1, 200)
    for bad in (0.0, 0.5, 0.9, -0.1):
        with pytest.raises(ValueError, match="quantile must lie"):
            tail_dependence(base, base, quantile=bad)


def test_tail_dependence_full_correlation_matches_numpy() -> None:
    rng = np.random.default_rng(7)
    base = rng.normal(size=300)
    engine = 0.4 * base + rng.normal(size=300)
    result = tail_dependence(base, engine, quantile=0.10)
    assert result.correlation_full == pytest.approx(float(np.corrcoef(base, engine)[0, 1]))


# -------------------------------------------------------------------------- convexity


def test_convexity_recovers_a_planted_kink_exactly() -> None:
    # Noiseless data: engine = 0.001 + 0.3 * base - 0.5 * min(base, 0).
    rng = np.random.default_rng(11)
    base = rng.normal(scale=0.04, size=400)
    engine = 0.001 + 0.3 * base - 0.5 * np.minimum(base, 0.0)
    result = convexity(base, engine)
    assert result.alpha == pytest.approx(0.001, abs=1e-9)
    assert result.up_beta == pytest.approx(0.3, abs=1e-9)
    assert result.kappa == pytest.approx(-0.5, abs=1e-9)
    assert result.down_beta == pytest.approx(-0.2, abs=1e-9)


def test_convexity_of_a_purely_linear_engine_is_zero() -> None:
    rng = np.random.default_rng(13)
    base = rng.normal(scale=0.04, size=400)
    engine = 1.5 * base
    result = convexity(base, engine)
    assert result.kappa == pytest.approx(0.0, abs=1e-9)
    assert result.up_beta == pytest.approx(1.5, abs=1e-9)
    assert result.down_beta == pytest.approx(1.5, abs=1e-9)


def test_convexity_needs_a_usable_sample() -> None:
    base = np.linspace(-0.1, 0.1, 24)
    with pytest.raises(ValueError, match="at least 36 months"):
        convexity(base, base)


def test_convexity_rejects_misaligned_inputs() -> None:
    with pytest.raises(ValueError, match="aligned"):
        convexity(np.zeros(40), np.zeros(41))


# ---------------------------------------------------------------------------- summary


def test_engine_summary_matches_hand_arithmetic_on_a_constant_series() -> None:
    engine = np.full(120, 0.01)
    result = engine_summary(engine)
    assert result.months == 120
    assert result.arithmetic_return == pytest.approx(0.12)
    assert result.geometric_return == pytest.approx(1.01**12 - 1.0)
    assert result.volatility == pytest.approx(0.0)
    assert math.isnan(result.sharpe)
    assert result.max_drawdown == pytest.approx(0.0)
    assert result.months_under_water == 0
    assert math.isnan(result.correlation_to_base)


def test_engine_summary_drawdown_and_underwater_count() -> None:
    # +10%, -50%, +10%: peak at 1.10, trough at 0.55, ends at 0.605 — still under water.
    result = engine_summary([0.10, -0.50, 0.10])
    assert result.max_drawdown == pytest.approx(0.55 / 1.10 - 1.0)
    assert result.months_under_water == 2


def test_engine_summary_correlation_requires_alignment() -> None:
    with pytest.raises(ValueError, match="aligned"):
        engine_summary(np.zeros(10), base=np.zeros(11))


def test_engine_summary_rejects_non_finite_input() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        engine_summary([0.01, float("nan"), 0.02])
