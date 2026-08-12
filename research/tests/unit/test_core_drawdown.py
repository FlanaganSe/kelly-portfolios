"""Tests for :mod:`portfolio_edge.core.drawdown`."""

from __future__ import annotations

import pytest

from portfolio_edge.core.drawdown import (
    drawdown_series,
    drawdown_summary,
    max_drawdown,
    time_under_water,
)
from portfolio_edge.core.wealth import NonPositiveWealthError, equity_curve

# Fixture: docs/research/portfolio-engine-specification.md, Layer 1 "Drawdown".
HAND_COMPUTED_PATH = [100.0, 110.0, 105.0, 95.0, 120.0, 90.0, 130.0]


def test_hand_computed_drawdown_path() -> None:
    """Reproduce the specification fixture, re-derived by hand below.

    Running peaks:      100, 110, 110, 110, 120, 120, 130
    Drawdowns:            0,   0, -1/22, -15/110, 0, -0.25, 0
    The deepest is 90/120 - 1 = -0.25. The longest run strictly below the running
    peak is [105, 95], i.e. 2 observations; the later run [90] is only 1 and is
    closed by the final 130.
    """
    assert pytest.approx(-0.0454545454545, rel=1e-12, abs=0.0) == 105.0 / 110.0 - 1.0
    assert pytest.approx(-0.1363636363636, rel=1e-12, abs=0.0) == 95.0 / 110.0 - 1.0
    assert pytest.approx(-0.25, rel=0.0, abs=1e-15) == 90.0 / 120.0 - 1.0

    summary = drawdown_summary(HAND_COMPUTED_PATH)
    assert summary.max_drawdown == pytest.approx(-0.25, rel=0.0, abs=1e-15)
    assert summary.max_time_under_water == 2
    assert summary.peak_index == 4
    assert summary.trough_index == 5
    assert summary.open_at_end is False
    assert summary.observations == 7


def test_convenience_wrappers_agree_with_the_summary() -> None:
    assert max_drawdown(HAND_COMPUTED_PATH) == pytest.approx(-0.25, rel=0.0, abs=1e-15)
    assert time_under_water(HAND_COMPUTED_PATH) == 2


def test_a_drawdown_still_open_at_the_end_is_counted() -> None:
    """The final `tuw = max(tuw, run)` in the specification's pseudocode.

    Dropping it silently understates time under water for every strategy that ends
    below its high-water mark, which is most of them at most measurement dates.
    """
    path = [100.0, 120.0, 110.0, 105.0, 100.0, 95.0]
    summary = drawdown_summary(path)
    assert summary.max_time_under_water == 4
    assert summary.final_time_under_water == 4
    assert summary.open_at_end is True


def test_a_monotonically_rising_path_has_no_drawdown() -> None:
    summary = drawdown_summary([100.0, 101.0, 102.0, 103.0])
    assert summary.max_drawdown == 0.0
    assert summary.max_time_under_water == 0
    assert summary.open_at_end is False


def test_a_flat_path_is_never_under_water() -> None:
    summary = drawdown_summary([100.0] * 5)
    assert summary.max_drawdown == 0.0
    assert summary.max_time_under_water == 0


def test_drawdown_series_matches_the_summary_minimum() -> None:
    series = drawdown_series(HAND_COMPUTED_PATH)
    assert float(series.min()) == pytest.approx(-0.25, rel=0.0, abs=1e-15)
    assert float(series.max()) == pytest.approx(0.0, rel=0.0, abs=1e-15)


def test_drawdown_is_computed_from_the_equity_curve_not_the_returns() -> None:
    """Same fixture, reached through the return series that generates it."""
    returns = [
        HAND_COMPUTED_PATH[i + 1] / HAND_COMPUTED_PATH[i] - 1.0
        for i in range(len(HAND_COMPUTED_PATH) - 1)
    ]
    curve = equity_curve(returns, initial_wealth=100.0)
    assert max_drawdown(curve) == pytest.approx(-0.25, rel=1e-14, abs=0.0)


def test_drawdown_deepens_mechanically_with_sample_length() -> None:
    """Maximum drawdown is not scale-free in T, so it must not be compared across
    unequal sample lengths (engine specification, Layer 1)."""
    short_path = [100.0, 90.0]
    long_path = [100.0, 90.0, 95.0, 80.0]
    assert max_drawdown(long_path) < max_drawdown(short_path)


def test_a_non_positive_equity_point_is_rejected() -> None:
    with pytest.raises(NonPositiveWealthError):
        drawdown_summary([100.0, 0.0, 50.0])


def test_an_empty_curve_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one observation"):
        drawdown_summary([])
