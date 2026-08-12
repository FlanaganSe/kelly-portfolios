"""Look-ahead guard: an observation may never be read before it was available.

Every historical datum has two distinct timestamps. ``observation_date`` is the
period the number describes; ``available_date`` is the first moment a researcher
could have known it. Accounting figures, index memberships, factor files, and
revised macro series all have a gap between the two, and closing that gap silently
is the most common way a backtest manufactures skill.

This module makes the gap a type error rather than a convention. Values are only
reachable through :meth:`Observation.read`, which requires the caller to state the
``as_of`` date it is standing on.

See ``docs/the-plan.md`` ("No observation may be used before its availability
timestamp") and the point-in-time data requirement in
``docs/research/portfolio-edge-research-framework.md``.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date


class LookAheadError(LookupError):
    """Raised when an observation is read before its availability timestamp."""

    def __init__(self, observation_date: date, available_date: date, as_of: date) -> None:
        self.observation_date = observation_date
        self.available_date = available_date
        self.as_of = as_of
        super().__init__(
            f"observation for {observation_date.isoformat()} first became available on "
            f"{available_date.isoformat()} and cannot be read as of {as_of.isoformat()}"
        )


@dataclass(frozen=True)
class Observation[T]:
    """A value carrying both the period it describes and when it became knowable."""

    observation_date: date
    available_date: date
    value: T

    def __post_init__(self) -> None:
        if self.available_date < self.observation_date:
            raise ValueError(
                f"available_date {self.available_date.isoformat()} precedes "
                f"observation_date {self.observation_date.isoformat()}; a datum cannot "
                "be known before the period it describes"
            )

    def is_available(self, as_of: date) -> bool:
        """Return whether this observation could be read on ``as_of``."""
        return as_of >= self.available_date

    def read(self, as_of: date) -> T:
        """Return the value, raising :class:`LookAheadError` if not yet available."""
        if not self.is_available(as_of):
            raise LookAheadError(self.observation_date, self.available_date, as_of)
        return self.value

    @property
    def publication_lag_days(self) -> int:
        """Days between the observation period and the moment it became knowable."""
        return (self.available_date - self.observation_date).days


class ObservationSeries[T]:
    """An immutable, observation-date-ordered collection of :class:`Observation`.

    Reads are always filtered by an ``as_of`` date, so a caller cannot accidentally
    iterate over the whole history while standing at a point in the past.
    """

    __slots__ = ("_observations",)

    def __init__(self, observations: Iterable[Observation[T]]) -> None:
        ordered = tuple(sorted(observations, key=lambda item: item.observation_date))
        dates = [item.observation_date for item in ordered]
        if len(set(dates)) != len(dates):
            raise ValueError("observation dates must be unique within a series")
        self._observations = ordered

    def __len__(self) -> int:
        return len(self._observations)

    def __iter__(self) -> Iterator[Observation[T]]:
        return iter(self._observations)

    def visible_at(self, as_of: date) -> tuple[Observation[T], ...]:
        """Return every observation that had been published by ``as_of``."""
        return tuple(item for item in self._observations if item.is_available(as_of))

    def values_at(self, as_of: date) -> tuple[T, ...]:
        """Return the values of every observation published by ``as_of``."""
        return tuple(item.read(as_of) for item in self.visible_at(as_of))

    def latest_at(self, as_of: date) -> Observation[T]:
        """Return the most recent observation published by ``as_of``."""
        visible = self.visible_at(as_of)
        if not visible:
            raise LookupError(f"no observation was available as of {as_of.isoformat()}")
        return visible[-1]


def guard_availability[T](
    observations: Sequence[Observation[T]],
    as_of: date,
) -> tuple[T, ...]:
    """Read every observation in ``observations``, raising on the first look-ahead.

    Unlike :meth:`ObservationSeries.values_at`, which filters, this refuses: it is
    the right call when the caller believes the whole slice is already available
    and wants to be told loudly if it is not.
    """
    return tuple(item.read(as_of) for item in observations)
