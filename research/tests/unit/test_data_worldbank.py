"""The Pink Sheet reader, exercised offline against a verbatim slice of the real sheet.

The fixture keeps the workbook's first six rows — which carry the release stamp, the
commodity names and the units — plus the first six and last three data rows, narrowed to
four columns. It is the real layout, not a reconstruction of it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_edge.data import worldbank

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "worldbank_pinksheet_slice.json"
)


def _rows() -> tuple[tuple[object, ...], ...]:
    return tuple(tuple(row) for row in json.loads(FIXTURE.read_text()))


def _dataset() -> worldbank.PinkSheetDataset:
    return worldbank.get_dataset("worldbank_pinksheet_gold_monthly")


def test_the_registry_refuses_an_unregistered_dataset() -> None:
    with pytest.raises(worldbank.UnknownDatasetError):
        worldbank.get_dataset("worldbank_pinksheet_silver_monthly")


def test_the_slice_parses_into_a_monthly_gold_table() -> None:
    table = worldbank.parse_sheet(_rows(), dataset=_dataset())

    assert table.columns == ("Gold",)
    assert table.frequency == "monthly"
    assert table.first_observation == "1960-01"
    assert table.last_observation == "2026-07"
    assert table.rows == 9


def test_period_labels_are_converted_from_the_sheets_own_form() -> None:
    table = worldbank.parse_sheet(_rows(), dataset=_dataset())

    assert table.periods[0] == "1960-01"
    assert all(len(period) == 7 and period[4] == "-" for period in table.periods)


def test_the_pegged_era_reads_as_the_official_price() -> None:
    table = worldbank.parse_sheet(_rows(), dataset=_dataset())
    values = dict(worldbank.monthly_series(table, "Gold"))

    # 1960 is inside Bretton Woods and the series records the $35 peg, which is the
    # reason the study excludes it rather than a defect in the file.
    assert values["1960-01"] == pytest.approx(35.0)


def test_the_averaging_warning_and_the_licence_travel_with_the_table() -> None:
    warnings = " ".join(worldbank.parse_sheet(_rows(), dataset=_dataset()).warnings)

    assert "MONTHLY AVERAGES OF DAILY RATES, NOT MONTH-END LEVELS" in warnings
    assert "biased upward" in warnings
    assert "CC BY 4.0" in warnings
    assert "London afternoon fixing" in warnings


def test_a_release_mismatch_is_a_warning_because_a_stale_url_serves_stale_data() -> None:
    rows = list(_rows())
    rows[3] = ("Updated on January 06, 2025", None, None, None)

    table = worldbank.parse_sheet(tuple(rows), dataset=_dataset())
    assert any("RELEASE MISMATCH" in warning for warning in table.warnings)


def test_a_renamed_column_raises_rather_than_matching_something_else() -> None:
    rows = list(_rows())
    header = list(rows[4])
    header[3] = "Gold (spot)"
    rows[4] = tuple(header)

    with pytest.raises(worldbank.PinkSheetParseError, match="exactly one column"):
        worldbank.parse_sheet(tuple(rows), dataset=_dataset())


def test_a_missing_value_becomes_missing_rather_than_zero() -> None:
    rows = list(_rows())
    row = list(rows[6])
    row[3] = ".."
    rows[6] = tuple(row)

    table = worldbank.parse_sheet(tuple(rows), dataset=_dataset())
    assert table.column("Gold")[0] is None
    assert "1960-01" not in dict(worldbank.monthly_series(table, "Gold"))
    assert any("is missing in 1 of" in warning for warning in table.warnings)


def test_the_licence_permits_redistribution_and_the_attribution_is_carried() -> None:
    assert worldbank.LICENSE_OR_TERMS_URL.startswith("https://")
    assert "CC BY 4.0" in worldbank.ATTRIBUTION
    assert "Changes made" in worldbank.ATTRIBUTION
