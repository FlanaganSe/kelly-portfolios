"""Offline parser tests for Shiller's ``ie_data`` reader.

``tests/fixtures/shiller_ie_data_slice.json`` holds the Disclaimer sheet, the
eight-row stacked header block, the first four months of 1871, **October 1871**,
a modern month, and the trailing footnote row — all lifted verbatim from a real
download of 2026-08-16 (sha256 ``71c3636d…``). October is in the slice because
Shiller writes it as ``1871.1``, which a parser that reads the digits after the
decimal point turns into January.

A legacy OLE2 ``.xls`` cannot be truncated into a small fixture and no writer for
the format is installed, so the slice is stored as rows. The byte reader is
covered in ``test_data_workbook.py`` and the live file by the ``network`` test in
``tests/integration/test_data_network.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_edge.data import shiller
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.workbook import SheetRows

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "shiller_ie_data_slice.json"


def _sheets() -> dict[str, SheetRows]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {name: tuple(tuple(row) for row in rows) for name, rows in payload.items()}


@pytest.fixture
def dataset() -> shiller.ShillerDataset:
    return shiller.get_dataset("shiller_ie_data")


@pytest.fixture
def parsed(dataset: shiller.ShillerDataset) -> shiller.ShillerFile:
    return shiller.parse_sheets(_sheets(), dataset=dataset)


def _cell(parsed: shiller.ShillerFile, period: str, column: str) -> float | None:
    table = parsed.table
    return table.values[table.periods.index(period)][table.columns.index(column)]


def test_october_is_month_ten_and_not_month_one(parsed: shiller.ShillerFile) -> None:
    """``1871.1`` is October. This is the one place the file bites silently."""
    assert "1871-10" in parsed.table.periods
    assert parsed.table.periods.count("1871-01") == 1
    assert parsed.table.periods == (
        "1871-01",
        "1871-02",
        "1871-03",
        "1871-04",
        "1871-10",
        "2020-01",
    )


def test_the_stacked_header_becomes_declared_column_names(
    parsed: shiller.ShillerFile,
) -> None:
    columns = parsed.table.columns

    assert columns[0] == "P"
    assert "CAPE" in columns
    assert "TR_CAPE" in columns
    assert "Real_Total_Return_Price" in columns
    # The two blank spacer columns are dropped, and the drop is recorded.
    assert len(columns) == 19
    assert any("blank spacer column" in w for w in parsed.table.warnings)
    assert any("THIS REPOSITORY'S DECLARATION" in w for w in parsed.table.warnings)


def test_the_na_marker_becomes_missing_and_never_zero(
    parsed: shiller.ShillerFile,
) -> None:
    """CAPE needs ten prior years of earnings, so it is NA until 1881."""
    assert _cell(parsed, "1871-01", "CAPE") is None
    assert _cell(parsed, "1871-01", "TR_CAPE") is None
    assert _cell(parsed, "1871-01", "P") == pytest.approx(4.44)
    assert any("became missing values, not zeros" in w for w in parsed.table.warnings)


def test_units_are_declared_per_column_and_nothing_is_converted(
    parsed: shiller.ShillerFile,
) -> None:
    units = parsed.table.units

    assert parsed.table.source_units == units
    assert parsed.table.unit_transform == "identity"
    # The three columns a reader is most likely to misuse.
    assert "Long_Interest_Rate_GS10=percent_per_year" in units
    assert "Monthly_Total_Bond_Returns=gross_return_factor" in units
    assert "Real_Total_Return_Price=wealth_index_constant_currency" in units
    # The published yield is left as the percent the file contains.
    assert _cell(parsed, "1871-01", "Long_Interest_Rate_GS10") == pytest.approx(5.32)


def test_the_footnote_row_is_captured_rather_than_parsed_as_data(
    parsed: shiller.ShillerFile,
) -> None:
    """The footnotes are the only per-row availability statement in the file."""
    assert parsed.footnotes
    joined = " ".join(parsed.footnotes)
    assert "Aug 1st close" in joined or "CPI estimated" in joined
    assert any("footnote rows below the data block" in w for w in parsed.table.warnings)


def test_the_disclaimer_sheet_is_preserved_verbatim(
    parsed: shiller.ShillerFile,
) -> None:
    assert "do not guarantee the accuracy" in parsed.disclaimer


def test_a_price_that_is_a_monthly_average_says_so(parsed: shiller.ShillerFile) -> None:
    assert any("MONTHLY AVERAGE OF DAILY CLOSES" in w for w in parsed.table.warnings)
    assert any("TRAILING TWELVE-MONTH TOTALS" in w for w in parsed.table.warnings)


def test_a_changed_header_is_warned_about_but_still_parses(
    dataset: shiller.ShillerDataset,
) -> None:
    sheets = _sheets()
    rows = [list(row) for row in sheets["Data"]]
    rows[7][6] = "Rate GS10 (renamed)"
    mangled = {"Disclaimer": sheets["Disclaimer"], "Data": tuple(tuple(r) for r in rows)}

    parsed = shiller.parse_sheets(mangled, dataset=dataset)

    assert parsed.table.rows == 6
    assert any("header wording has changed" in w for w in parsed.table.warnings)


def test_a_sheet_with_no_dated_rows_is_fatal(dataset: shiller.ShillerDataset) -> None:
    with pytest.raises(shiller.ShillerParseError, match=r"no row has a YYYY\.MM date"):
        shiller.parse_sheets({"Data": (("Date", "P"), ("also", "text"))}, dataset=dataset)


def test_a_missing_declared_sheet_is_fatal(dataset: shiller.ShillerDataset) -> None:
    with pytest.raises(shiller.ShillerParseError, match="declared data sheet"):
        shiller.parse_sheets({"Renamed": (("Date",),)}, dataset=dataset)


def test_the_manifest_carries_the_disclaimer_and_the_revision_policy(
    dataset: shiller.ShillerDataset, parsed: shiller.ShillerFile, tmp_path: Path
) -> None:
    cache = RawCache(tmp_path)
    entry = cache.store(
        dataset.url,
        b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 not the real bytes",
        headers={
            "Content-Type": "application/vnd.ms-excel",
            "Last-Modified": "Tue, 04 Aug 2026 15:29:32 GMT",
        },
        retrieved_utc="2026-08-16T00:00:00Z",
    )
    (manifest,) = shiller.build_manifests(dataset, entry, parsed)

    assert manifest.dataset_id == "shiller_ie_data_monthly"
    assert manifest.source_last_modified == "Tue, 04 Aug 2026 15:29:32 GMT"
    assert "not point-in-time" in manifest.revision_policy.lower()
    assert any("Disclaimer sheet" in w for w in manifest.warnings)
    assert any(w.startswith("SHEET PINNED:") for w in manifest.warnings)
