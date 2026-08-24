"""Arithmetic on ``YYYY-MM`` period labels.

Monthly experiment windows are frozen in specifications as calendar labels, not
as timestamps, because that is how the sources publish them and how the papers
print them. Turning a label into an integer month index makes shifts, spans and
gap detection plain integer arithmetic, with no timezone, no day-of-month and no
dependence on a datetime library's calendar.

The one rule worth stating: an index is *months since year zero*, so it is only
ever meaningful as a difference or a round trip through
:func:`period_from_index`. Nothing outside this module should read its value.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "PeriodError",
    "month_count",
    "month_index",
    "period_from_index",
    "shift_period",
]

_MONTHS_PER_YEAR: Final = 12


class PeriodError(ValueError):
    """A string is not a ``YYYY-MM`` period label."""


def month_index(period: str) -> int:
    """Months since year zero, so differences and shifts are plain integers."""
    parts = period.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise PeriodError(f"not a YYYY-MM period label: {period!r}")
    try:
        year, month = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise PeriodError(f"not a YYYY-MM period label: {period!r}") from exc
    if not 1 <= month <= _MONTHS_PER_YEAR:
        raise PeriodError(f"month out of range in {period!r}")
    return year * _MONTHS_PER_YEAR + (month - 1)


def period_from_index(index: int) -> str:
    """Inverse of :func:`month_index`."""
    if index < 0:
        raise PeriodError(f"month index cannot be negative, got {index}")
    year, month = divmod(index, _MONTHS_PER_YEAR)
    return f"{year:04d}-{month + 1:02d}"


def shift_period(period: str, months: int) -> str:
    """``period`` moved by ``months``, forwards or backwards."""
    return period_from_index(month_index(period) + months)


def month_count(start: str, end: str) -> int:
    """Calendar months in ``[start, end]`` inclusive; zero or negative if inverted."""
    return month_index(end) - month_index(start) + 1
