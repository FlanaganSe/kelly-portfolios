"""Tests for :mod:`portfolio_edge.core.availability`."""

from __future__ import annotations

from datetime import date

import pytest

from portfolio_edge.core.availability import (
    LookAheadError,
    Observation,
    ObservationSeries,
    guard_availability,
)

# A monthly factor observation for January, published on the fifth business day of
# February. Reading it on 1 February is look-ahead.
JANUARY = Observation(
    observation_date=date(2020, 1, 31),
    available_date=date(2020, 2, 5),
    value=0.0123,
)
FEBRUARY = Observation(
    observation_date=date(2020, 2, 29),
    available_date=date(2020, 3, 5),
    value=-0.0456,
)


def test_reading_before_the_availability_date_raises() -> None:
    with pytest.raises(LookAheadError) as info:
        JANUARY.read(date(2020, 2, 1))
    assert info.value.observation_date == date(2020, 1, 31)
    assert info.value.available_date == date(2020, 2, 5)
    assert info.value.as_of == date(2020, 2, 1)


def test_reading_on_the_availability_date_succeeds() -> None:
    assert JANUARY.read(date(2020, 2, 5)) == pytest.approx(0.0123, rel=0.0, abs=1e-15)
    assert JANUARY.read(date(2020, 3, 1)) == pytest.approx(0.0123, rel=0.0, abs=1e-15)


def test_reading_on_the_observation_date_itself_raises_when_there_is_a_lag() -> None:
    with pytest.raises(LookAheadError):
        JANUARY.read(date(2020, 1, 31))


def test_availability_is_queryable_without_raising() -> None:
    assert not JANUARY.is_available(date(2020, 2, 4))
    assert JANUARY.is_available(date(2020, 2, 5))


def test_publication_lag_is_exposed() -> None:
    assert JANUARY.publication_lag_days == 5


def test_an_observation_cannot_be_available_before_it_is_observed() -> None:
    with pytest.raises(ValueError, match="precedes"):
        Observation(
            observation_date=date(2020, 1, 31),
            available_date=date(2020, 1, 30),
            value=0.0,
        )


def test_zero_lag_observations_are_allowed() -> None:
    same_day = Observation(
        observation_date=date(2020, 1, 31), available_date=date(2020, 1, 31), value=1.0
    )
    assert same_day.read(date(2020, 1, 31)) == 1.0
    assert same_day.publication_lag_days == 0


def test_a_series_filters_to_what_was_published() -> None:
    series = ObservationSeries([FEBRUARY, JANUARY])
    assert len(series) == 2
    assert series.values_at(date(2020, 2, 10)) == (0.0123,)
    assert series.values_at(date(2020, 3, 10)) == (0.0123, -0.0456)
    assert series.values_at(date(2020, 2, 1)) == ()


def test_a_series_orders_by_observation_date_not_insertion_order() -> None:
    series = ObservationSeries([FEBRUARY, JANUARY])
    assert [item.observation_date for item in series] == [
        date(2020, 1, 31),
        date(2020, 2, 29),
    ]


def test_duplicate_observation_dates_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        ObservationSeries([JANUARY, JANUARY])


def test_latest_at_returns_the_most_recent_published_observation() -> None:
    series = ObservationSeries([JANUARY, FEBRUARY])
    assert series.latest_at(date(2020, 3, 10)).observation_date == date(2020, 2, 29)
    assert series.latest_at(date(2020, 2, 10)).observation_date == date(2020, 1, 31)
    with pytest.raises(LookupError):
        series.latest_at(date(2020, 1, 1))


def test_guard_availability_refuses_rather_than_filters() -> None:
    """Filtering is right when scanning a history; refusing is right when the caller
    believes the whole slice is available and must be told loudly if it is not."""
    assert guard_availability([JANUARY], date(2020, 2, 10)) == (0.0123,)
    with pytest.raises(LookAheadError):
        guard_availability([JANUARY, FEBRUARY], date(2020, 2, 10))
