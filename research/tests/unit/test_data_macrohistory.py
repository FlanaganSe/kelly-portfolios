"""Offline parser tests for the Jordà-Schularick-Taylor reader.

``tests/fixtures/jst_macrohistory_r6_slice.json`` holds the header row and 22
country-year rows lifted **verbatim** out of a real download of the R6 workbook on
2026-08-16 (sha256 ``c1bb91fe…``). The rows were chosen because each one is a
documented trap rather than a typical observation: Portugal's interpolated
1975-1977, Japan's missing 1946-1947, Germany's 1922-1924 hyperinflation,
Canada's total absence of returns, and the US 1928-1933 as a control. A ``.xlsx``
cannot be sliced the way a CSV can, so the slice is stored as rows; the byte
reader is covered in ``test_data_workbook.py`` and the live download by the
``network`` test in ``tests/integration/test_data_network.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_edge.data import macrohistory
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.workbook import SheetRows

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "jst_macrohistory_r6_slice.json"


def _sheets() -> dict[str, SheetRows]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {name: tuple(tuple(row) for row in rows) for name, rows in payload.items()}


@pytest.fixture
def dataset() -> macrohistory.JstDataset:
    return macrohistory.get_dataset("jst_macrohistory_r6")


@pytest.fixture
def parsed(dataset: macrohistory.JstDataset) -> macrohistory.JstFile:
    return macrohistory.parse_sheets(_sheets(), dataset=dataset)


def _cell(table: ParsedTable, year: str, iso: str) -> float | None:
    return table.values[table.periods.index(year)][table.columns.index(iso)]


def test_the_panel_pivots_to_one_table_per_variable_with_countries_as_columns(
    parsed: macrohistory.JstFile,
) -> None:
    assert [t.table_id for t in parsed.tables] == [
        "equity_total_return",
        "equity_capital_gain",
        "equity_dividend_yield",
        "bond_total_return",
        "bill_rate",
        "housing_total_return",
        "consumer_prices",
    ]
    assert parsed.countries == ("CAN", "DEU", "JPN", "PRT", "USA")
    equity = parsed.table("equity_total_return")
    assert equity.columns == parsed.countries
    assert equity.frequency == "annual"
    assert equity.periods[0] == "1922"
    assert equity.units == "decimal"
    assert equity.unit_transform == "identity"


def test_canada_carries_no_returns_at_all_and_the_table_says_so(
    parsed: macrohistory.JstFile,
) -> None:
    """The single easiest way to overstate this panel is to count 18 countries."""
    equity = parsed.table("equity_total_return")
    index = equity.columns.index("CAN")

    assert all(row[index] is None for row in equity.values)
    assert any("no observation of this variable at all" in w for w in equity.warnings)
    assert "CAN" not in macrohistory.RETURN_COUNTRIES
    assert "IRL" not in macrohistory.RETURN_COUNTRIES
    assert len(macrohistory.RETURN_COUNTRIES) == 16


def test_a_missing_country_year_is_none_and_never_zero(
    parsed: macrohistory.JstFile,
) -> None:
    """Japan's exchange was shut; the source publishes nothing for 1946-1947."""
    equity = parsed.table("equity_total_return")

    assert _cell(equity, "1945", "JPN") is not None
    assert _cell(equity, "1946", "JPN") is None
    assert _cell(equity, "1947", "JPN") is None
    # The consumer price index is published right through the hole, which is
    # exactly what makes bridging the gap at zero real return so wrong.
    assert _cell(parsed.table("consumer_prices"), "1946", "JPN") is not None


def test_the_source_interpolation_flags_are_carried_out_of_the_file(
    parsed: macrohistory.JstFile,
) -> None:
    flagged = {(variable, iso, year) for variable, iso, year in parsed.interpolated}

    assert ("eq_tr", "PRT", "1975") in flagged
    assert ("eq_tr", "PRT", "1976") in flagged
    assert ("eq_tr", "PRT", "1977") in flagged
    assert ("eq_tr", "USA", "1929") not in flagged
    assert any("interpolated to cover an exchange closure" in w for w in parsed.warnings)


def test_portugals_filled_years_are_literally_the_same_number(
    parsed: macrohistory.JstFile,
) -> None:
    """The fill is visible in the data, not only in the documentation.

    The RORE documentation says prices were interpolated across the Carnation
    Revolution closure and no dividends assumed. What the file actually contains
    is one number repeated, which is worth asserting because it is the difference
    between "estimated" and "invented".
    """
    equity = parsed.table("equity_total_return")

    assert _cell(equity, "1975", "PRT") == _cell(equity, "1976", "PRT")


def test_the_german_hyperinflation_rows_survive_parsing_unaltered(
    parsed: macrohistory.JstFile,
) -> None:
    equity = parsed.table("equity_total_return")
    prices = parsed.table("consumer_prices")
    nominal_1923 = _cell(equity, "1923", "DEU")
    cpi_1922 = _cell(prices, "1922", "DEU")
    cpi_1923 = _cell(prices, "1923", "DEU")

    assert nominal_1923 is not None and nominal_1923 > 1e9
    assert cpi_1922 is not None and cpi_1923 is not None
    assert cpi_1923 / cpi_1922 > 1e9
    assert any("HYPERINFLATION ARITHMETIC" in w for w in equity.warnings)


def test_every_table_states_that_it_is_nominal_annual_and_not_investable(
    parsed: macrohistory.JstFile,
) -> None:
    for table_id in ("equity_total_return", "bond_total_return", "housing_total_return"):
        warnings = parsed.table(table_id).warnings
        assert any("NOMINAL and in LOCAL CURRENCY" in w for w in warnings)
        assert any("LOWER BOUND on the realised loss" in w for w in warnings)
        assert any("NOT INVESTABLE" in w for w in warnings)


def test_a_missing_declared_sheet_is_fatal(dataset: macrohistory.JstDataset) -> None:
    with pytest.raises(macrohistory.JstParseError, match="declared data sheet"):
        macrohistory.parse_sheets({"Renamed": (("year", "iso"),)}, dataset=dataset)


def test_a_renamed_column_is_fatal_rather_than_quietly_dropped(
    dataset: macrohistory.JstDataset,
) -> None:
    sheets = _sheets()
    header = list(sheets["Sheet1"][0])
    header[header.index("eq_tr")] = "equity_total_return_renamed"
    mangled = {"Sheet1": (tuple(header), *sheets["Sheet1"][1:])}

    with pytest.raises(macrohistory.JstParseError, match="eq_tr"):
        macrohistory.parse_sheets(mangled, dataset=dataset)


def test_the_manifest_pins_the_release_the_sheet_and_the_citation(
    dataset: macrohistory.JstDataset, parsed: macrohistory.JstFile, tmp_path: Path
) -> None:
    cache = RawCache(tmp_path)
    entry: CacheEntry = cache.store(
        dataset.url,
        b"PK\x03\x04 not the real bytes, only a cache entry to hang a manifest on",
        headers={
            "Content-Type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            "Last-Modified": "Wed, 10 Jul 2024 08:29:43 GMT",
        },
        retrieved_utc="2026-08-16T00:00:00Z",
    )
    manifests = macrohistory.build_manifests(dataset, entry, parsed)

    assert len(manifests) == len(parsed.tables)
    equity = next(
        m
        for m in manifests
        if m.dataset_id == "jst_macrohistory_r6_equity_total_return_annual"
    )
    assert equity.dataset_id == "jst_macrohistory_r6_equity_total_return_annual"
    assert equity.sha256_raw == entry.sha256
    assert "not point-in-time" in equity.revision_policy.lower()
    assert any(w.startswith("RELEASE PINNED:") for w in equity.warnings)
    assert any("Rate of Return on Everything" in w for w in equity.warnings)
    assert any("countries, in column order" in w for w in equity.warnings)


def test_real_total_return_deflates_period_by_period() -> None:
    """A closed-form case: 20% nominal against 20% inflation is exactly zero."""
    real = macrohistory.real_total_return(
        [None, 0.20, 0.10], [100.0, 120.0, 120.0]
    )

    assert real[0] is None
    assert real[1] == pytest.approx(0.0, abs=1e-15)
    assert real[2] == pytest.approx(0.10, abs=1e-15)


def test_real_total_return_propagates_a_hole_rather_than_bridging_it() -> None:
    """Japan 1946-1947 is the case this behaviour exists for."""
    real = macrohistory.real_total_return(
        [None, 0.05, None, 0.05], [100.0, 100.0, 200.0, 400.0]
    )

    assert real[1] == pytest.approx(0.05)
    assert real[2] is None
    # The period after the hole is still computable, and it is measured against
    # the price index that moved through the hole, not around it.
    assert real[3] == pytest.approx(1.05 * 200.0 / 400.0 - 1.0)


def test_real_total_return_refuses_misaligned_inputs() -> None:
    with pytest.raises(ValueError, match="aligned on the same periods"):
        macrohistory.real_total_return([None, 0.1], [100.0])
