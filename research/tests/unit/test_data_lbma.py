"""The LBMA reader, exercised offline against a verbatim slice of the real payload.

The slice is 29 consecutive publication days spanning 2008-08-27 to 2008-10-06, chosen
because it crosses two month boundaries and so exercises the month-end rule against a
real holiday and weekend pattern rather than a manufactured one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_edge.data import lbma
from portfolio_edge.data.table import ParsedTable

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "lbma_gold_pm_slice.json"


def _slice_bytes() -> bytes:
    return FIXTURE.read_bytes()


def _table() -> ParsedTable:
    return lbma.parse_bytes(
        _slice_bytes(), dataset=lbma.get_dataset("lbma_gold_pm")
    )


def test_the_registry_refuses_an_unregistered_dataset() -> None:
    with pytest.raises(lbma.UnknownDatasetError, match="lbma_gold_pm"):
        lbma.get_dataset("lbma_platinum_pm")


def test_the_slice_parses_into_a_three_currency_daily_table() -> None:
    table = _table()

    assert table.columns == ("USD", "GBP", "EUR")
    assert table.frequency == "daily"
    assert table.units == "currency_per_troy_ounce"
    assert table.unit_transform == "identity"
    assert table.first_observation == "2008-08-27"
    assert table.last_observation == "2008-10-06"
    assert table.rows == 29


def test_the_parser_states_that_these_are_prices_and_not_returns() -> None:
    warnings = " ".join(_table().warnings)

    assert "PRICE LEVEL, not a return" in warnings
    assert "storage and vehicle cost" in warnings
    assert "1971-08-15" in warnings


def test_month_end_is_the_last_published_fix_not_the_last_calendar_day() -> None:
    # 2008-08-31 was a Sunday and 2008-09-30 a Tuesday, so the two months resolve to
    # different weekday offsets. Both values are read straight out of the fixture.
    rows = json.loads(FIXTURE.read_text())
    by_day = {row["d"]: row["v"][0] for row in rows}
    months = dict(lbma.month_end_usd(_table()))

    assert months["2008-08"] == by_day["2008-08-29"]
    assert months["2008-09"] == by_day["2008-09-30"]
    assert months["2008-10"] == by_day["2008-10-06"]
    assert list(months) == ["2008-08", "2008-09", "2008-10"]


def test_month_end_never_carries_a_price_across_a_month_boundary() -> None:
    months = dict(lbma.month_end_usd(_table()))

    # Three distinct months, three distinct fixes. A carry-forward bug would show up as
    # two equal levels, which is why this asserts inequality rather than a value.
    assert len({months["2008-08"], months["2008-09"], months["2008-10"]}) == 3


def test_a_missing_usd_observation_is_skipped_rather_than_zeroed() -> None:
    rows = json.loads(FIXTURE.read_text())
    for row in rows:
        if row["d"].startswith("2008-10"):
            row["v"][0] = None
    table = lbma.parse_bytes(
        json.dumps(rows).encode(), dataset=lbma.get_dataset("lbma_gold_pm")
    )

    months = dict(lbma.month_end_usd(table))
    assert "2008-10" not in months
    assert "2008-09" in months
    assert any("USD is missing on" in warning for warning in table.warnings)


def test_out_of_order_dates_raise_rather_than_being_sorted() -> None:
    rows = json.loads(FIXTURE.read_text())
    rows[0], rows[1] = rows[1], rows[0]

    with pytest.raises(lbma.LbmaParseError, match="increasing order"):
        lbma.parse_bytes(
            json.dumps(rows).encode(), dataset=lbma.get_dataset("lbma_gold_pm")
        )


def test_a_changed_payload_shape_raises_rather_than_being_worked_around() -> None:
    dataset = lbma.get_dataset("lbma_gold_pm")

    with pytest.raises(lbma.LbmaParseError, match="non-empty JSON array"):
        lbma.parse_bytes(b'{"d": "2008-08-27"}', dataset=dataset)
    with pytest.raises(lbma.LbmaParseError, match="currency values"):
        lbma.parse_bytes(b'[{"d": "2008-08-27", "v": [1.0]}]', dataset=dataset)
    with pytest.raises(lbma.LbmaParseError, match="not JSON"):
        lbma.parse_bytes(b"<html>challenge</html>", dataset=dataset)


def test_the_two_auctions_are_registered_as_separate_datasets() -> None:
    assert lbma.get_dataset("lbma_gold_pm").auction == "pm"
    assert lbma.get_dataset("lbma_gold_am").auction == "am"
    assert (
        lbma.get_dataset("lbma_gold_pm").url != lbma.get_dataset("lbma_gold_am").url
    )


def test_the_source_is_not_research_grade_and_the_licence_is_recorded() -> None:
    assert lbma.RESEARCH_GRADE is False
    assert "written licence from IBA" in lbma.LICENCE_RESTRICTION
    assert lbma.LICENSE_OR_TERMS_URL.startswith("https://")
