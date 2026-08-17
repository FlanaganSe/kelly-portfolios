"""The property that matters here is that nothing can see the future.

Most of these tests are causality tests: perturb a return at time ``t`` and assert
that no position formed at or before ``t`` moves. A trend strategy that quietly peeks
produces spectacular results, so the absence of look-ahead is checked directly rather
than argued from the code's shape.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.time_series_momentum import (
    TimeSeriesMomentumSpec,
    position_sizes,
    time_series_momentum,
    volatility_targeted,
)

SPEC = TimeSeriesMomentumSpec(lookback=3, volatility_window=4, target_volatility=0.10, cap=2.0)


def _panel(seed: int = 20260816, periods: int = 60, instruments: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.005, 0.04, size=(periods, instruments))


# --------------------------------------------------------------------------------
# 1. Look-ahead
# --------------------------------------------------------------------------------


def test_a_position_does_not_move_when_its_own_period_return_changes() -> None:
    """The decisive test. Position at t must not depend on the return at t."""
    panel = _panel()
    for index in (10, 25, 40):
        before = position_sizes(panel, index=index, spec=SPEC)
        perturbed = panel.copy()
        perturbed[index] += 10.0
        after = position_sizes(perturbed, index=index, spec=SPEC)
        np.testing.assert_allclose(before, after)


def test_a_position_does_not_move_when_any_future_return_changes() -> None:
    panel = _panel()
    perturbed = panel.copy()
    perturbed[30:] = 99.0
    for index in range(SPEC.burn_in, 30):
        np.testing.assert_allclose(
            position_sizes(panel, index=index, spec=SPEC),
            position_sizes(perturbed, index=index, spec=SPEC),
        )


def test_the_strategy_series_is_unchanged_before_a_future_perturbation() -> None:
    panel = _panel()
    perturbed = panel.copy()
    perturbed[40:] += 5.0
    a = time_series_momentum(panel, spec=SPEC)
    b = time_series_momentum(perturbed, spec=SPEC)
    np.testing.assert_allclose(a[: 40], b[: 40], equal_nan=True)


def test_forming_a_position_inside_the_burn_in_raises() -> None:
    panel = _panel()
    with pytest.raises(ValueError, match="burn-in"):
        position_sizes(panel, index=SPEC.burn_in - 1, spec=SPEC)
    with pytest.raises(ValueError, match="past the end"):
        position_sizes(panel, index=len(panel), spec=SPEC)


# --------------------------------------------------------------------------------
# 2. The construction, checked longhand
# --------------------------------------------------------------------------------


def test_position_matches_a_hand_computed_signal_and_size() -> None:
    panel = _panel()
    index, column = 20, 1
    series = panel[:, column]
    signal = float(np.prod(1.0 + series[index - 3 : index]) - 1.0)
    volatility = float(np.std(series[index - 4 : index], ddof=1)) * math.sqrt(12)
    expected = math.copysign(min(0.10 / volatility, 2.0), signal)
    assert position_sizes(panel, index=index, spec=SPEC)[column] == pytest.approx(expected)


def test_the_sign_of_the_position_is_the_sign_of_the_lookback_return() -> None:
    panel = _panel()
    for index in range(SPEC.burn_in, len(panel)):
        sizes = position_sizes(panel, index=index, spec=SPEC)
        for column in range(panel.shape[1]):
            signal = np.prod(1.0 + panel[index - 3 : index, column]) - 1.0
            assert np.sign(sizes[column]) == np.sign(signal)


def test_the_cap_binds_on_a_very_quiet_instrument() -> None:
    """A near-zero-volatility leg would otherwise take an unbounded position."""
    panel = np.full((20, 1), 0.001)
    panel[:, 0] += np.linspace(0, 1e-9, 20)
    sizes = position_sizes(panel, index=10, spec=SPEC)
    assert sizes[0] == pytest.approx(SPEC.cap)


def test_a_strictly_trending_instrument_is_held_long_and_earns_its_return() -> None:
    panel = np.full((30, 1), 0.02)
    panel += np.linspace(0.0, 1e-6, 30).reshape(-1, 1)
    series = time_series_momentum(panel, spec=SPEC)
    live = series[SPEC.burn_in :]
    assert np.all(live > 0.0)


def test_a_compounded_signal_is_not_antisymmetric_under_negation() -> None:
    """Worth pinning, because it is the natural wrong assumption to make.

    A *summed* lookback signal would satisfy ``signal(-r) = -signal(r)``. The
    compounded one does not: ``prod(1 + r) - 1`` and ``prod(1 - r) - 1`` are unrelated
    in general, because the product is symmetric in the ordering but not in the sign.
    """
    up = np.array([[0.5], [0.5], [0.5]])
    assert np.prod(1.0 + up) - 1.0 > 0.0
    assert np.prod(1.0 - up) - 1.0 < 0.0  # here the sign does flip
    mixed = np.array([[0.5], [-0.5]])
    assert np.prod(1.0 + mixed) - 1.0 == pytest.approx(-0.25)
    assert np.prod(1.0 - mixed) - 1.0 == pytest.approx(-0.25)  # and here it does not


def test_a_monotone_downtrend_is_held_short_and_still_earns() -> None:
    panel = np.full((30, 1), -0.02)
    panel += np.linspace(0.0, 1e-6, 30).reshape(-1, 1)  # a volatility estimate needs variation
    series = time_series_momentum(panel, spec=SPEC)
    live = series[SPEC.burn_in :]
    assert np.all(live > 0.0), "short a falling instrument must make money"


# --------------------------------------------------------------------------------
# 3. Missing data and thin books
# --------------------------------------------------------------------------------


def test_an_instrument_with_a_gap_is_dropped_rather_than_bridged() -> None:
    panel = _panel()
    panel[15, 2] = np.nan
    sizes = position_sizes(panel, index=17, spec=SPEC)
    assert math.isnan(sizes[2])
    assert np.isfinite(sizes[0]) and np.isfinite(sizes[1])


def test_a_book_thinner_than_the_minimum_returns_nan() -> None:
    panel = _panel(instruments=2)
    panel[:, 1] = np.nan
    series = time_series_momentum(panel, spec=SPEC, minimum_instruments=2)
    assert np.all(np.isnan(series))
    thin = time_series_momentum(panel, spec=SPEC, minimum_instruments=1)
    assert np.isfinite(thin[SPEC.burn_in :]).any()


def test_burn_in_periods_are_nan_not_zero() -> None:
    series = time_series_momentum(_panel(), spec=SPEC)
    assert np.all(np.isnan(series[: SPEC.burn_in]))
    assert np.isfinite(series[SPEC.burn_in :]).all()


# --------------------------------------------------------------------------------
# 4. Volatility targeting, and its own look-ahead
# --------------------------------------------------------------------------------


def test_targeting_uses_only_prior_periods() -> None:
    series = _panel(instruments=1)[:, 0]
    perturbed = series.copy()
    perturbed[40:] *= 20.0
    a = volatility_targeted(series, window=12, target=0.12)
    b = volatility_targeted(perturbed, window=12, target=0.12)
    np.testing.assert_allclose(a[:40], b[:40], equal_nan=True)


def test_targeting_hits_the_target_when_volatility_is_constant() -> None:
    rng = np.random.default_rng(7)
    series = rng.normal(0.0, 0.05, size=400)
    scaled = volatility_targeted(series, window=60, target=0.12, cap=100.0)
    live = scaled[np.isfinite(scaled)]
    realised = float(np.std(live, ddof=1)) * math.sqrt(12)
    assert realised == pytest.approx(0.12, rel=0.15)


def test_targeting_leaves_the_sign_of_every_period_alone() -> None:
    series = _panel(instruments=1)[:, 0]
    scaled = volatility_targeted(series, window=12, target=0.12)
    live = np.isfinite(scaled)
    assert np.all(np.sign(scaled[live]) == np.sign(series[live]))


# --------------------------------------------------------------------------------
# 5. Specification validation
# --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lookback", 0),
        ("volatility_window", 1),
        ("target_volatility", 0.0),
        ("cap", -1.0),
        ("periods_per_year", 0),
    ],
)
def test_specification_rejects_impossible_parameters(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        TimeSeriesMomentumSpec(**{field: value})  # type: ignore[arg-type]


def test_burn_in_is_the_longer_of_the_two_windows() -> None:
    assert TimeSeriesMomentumSpec(lookback=12, volatility_window=36).burn_in == 36
    assert TimeSeriesMomentumSpec(lookback=48, volatility_window=36).burn_in == 48


def test_volatility_targeted_rejects_bad_arguments() -> None:
    with pytest.raises(ValueError, match="one-dimensional"):
        volatility_targeted(np.zeros((4, 2)), window=2, target=0.1)
    with pytest.raises(ValueError, match="window"):
        volatility_targeted(np.zeros(10), window=1, target=0.1)
    with pytest.raises(ValueError, match="target"):
        volatility_targeted(np.zeros(10), window=4, target=0.0)


def test_minimum_instruments_must_be_positive() -> None:
    with pytest.raises(ValueError, match="minimum_instruments"):
        time_series_momentum(_panel(), spec=SPEC, minimum_instruments=0)
