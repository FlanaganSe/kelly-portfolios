"""Tests for ``YYYY-MM`` period arithmetic.

Every expected value here is computed by hand in the assertion's own comment, not
by calling a second implementation of the same rule.
"""

from __future__ import annotations

import pytest

from portfolio_edge.experiments.periods import (
    PeriodError,
    month_count,
    month_index,
    period_from_index,
    shift_period,
)


def test_month_index_is_months_since_year_zero() -> None:
    """1963-07 is 1963*12 + 6 = 23562."""
    assert month_index("1963-07") == 23562
    assert month_index("1963-01") == 1963 * 12


def test_month_index_round_trips_through_period_from_index() -> None:
    for period in ("1927-01", "1963-07", "1999-12", "2026-06"):
        assert period_from_index(month_index(period)) == period


def test_shift_period_crosses_a_year_boundary_in_both_directions() -> None:
    assert shift_period("1993-12", 1) == "1994-01"
    assert shift_period("1994-01", -1) == "1993-12"
    assert shift_period("2014-01", -24) == "2012-01"
    assert shift_period("2003-12", 24) == "2005-12"


def test_month_count_is_inclusive_of_both_endpoints() -> None:
    """July 1963 to December 2013 is the 606 months Fama and French print."""
    assert month_count("1963-07", "2013-12") == 606
    assert month_count("1963-07", "1991-12") == 342  # Fama and French (1993)
    assert month_count("1965-01", "1989-12") == 300  # Jegadeesh and Titman (1993)
    assert month_count("2014-01", "2019-12") == 72
    assert month_count("1963-07", "1963-07") == 1


def test_month_count_of_an_inverted_range_is_not_positive() -> None:
    assert month_count("1994-01", "1993-12") == 0


@pytest.mark.parametrize(
    "bad", ["1963", "1963-07-01", "", "63-07", "1963-13", "1963-00", "abcd-ef"]
)
def test_a_label_that_is_not_yyyy_mm_is_rejected(bad: str) -> None:
    with pytest.raises(PeriodError):
        month_index(bad)


def test_a_negative_index_has_no_period_label() -> None:
    with pytest.raises(PeriodError):
        period_from_index(-1)
