"""The shared spreadsheet byte readers, and the per-column unit declaration.

The point of these tests is the *refusal*. Every source behind them is a public
web endpoint that can start returning an HTML error page, a login wall or a
bot-challenge interstitial without changing its URL, and a reader that pushed
those bytes into a spreadsheet library would fail somewhere deep instead of at
the door.
"""

from __future__ import annotations

import io

import openpyxl  # type: ignore[import-untyped]
import pytest

from portfolio_edge.data.workbook import (
    WorkbookParseError,
    column_unit_string,
    load_xls_sheets,
    load_xlsx_sheets,
)

_HTML_CHALLENGE = (
    b"<html><head><script>document.cookie=...</script></head>"
    b"<body>This site requires JavaScript to verify your browser</body></html>"
)


def _tiny_xlsx() -> bytes:
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Data"
    sheet.append(["year", "value"])
    sheet.append([1871, 4.44])
    sheet.append([1872, None])
    second = book.create_sheet("Notes")
    second.append(["a note"])
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def test_an_xlsx_reader_returns_every_sheet_in_workbook_order() -> None:
    sheets = load_xlsx_sheets(_tiny_xlsx(), source="unit-test")

    assert list(sheets) == ["Data", "Notes"]
    assert sheets["Data"][0] == ("year", "value")
    assert sheets["Data"][1] == (1871, 4.44)
    # An empty cell is None, never a zero and never an empty string.
    assert sheets["Data"][2] == (1872, None)


def test_html_served_in_place_of_an_xlsx_is_refused_at_the_door() -> None:
    with pytest.raises(WorkbookParseError) as excinfo:
        load_xlsx_sheets(_HTML_CHALLENGE, source="some-source")

    message = str(excinfo.value)
    assert "some-source" in message
    # The first bytes are quoted so the refusal itself identifies the challenge.
    assert "requires JavaScript" in message
    assert "failed acquisition" in message


def test_an_xlsx_is_refused_by_the_legacy_xls_reader_and_the_reverse() -> None:
    """The two formats are not interchangeable and neither reader guesses."""
    with pytest.raises(WorkbookParseError, match="OLE2"):
        load_xls_sheets(_tiny_xlsx(), source="unit-test")
    with pytest.raises(WorkbookParseError, match="zip container"):
        load_xlsx_sheets(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1truncated", source="unit-test")


def test_a_truncated_ole2_file_fails_as_a_parse_error_not_a_library_error() -> None:
    with pytest.raises(WorkbookParseError, match="xlrd could not open"):
        load_xls_sheets(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64, source="unit-test")


def test_column_units_are_rendered_in_column_order_and_never_guessed() -> None:
    columns = ("Index", "tbl", "mystery")
    units = {"Index": "index_level", "tbl": "decimal_per_year"}

    rendered = column_unit_string(columns, units)

    assert rendered == "Index=index_level|tbl=decimal_per_year|mystery=undeclared"
    # Order follows the columns, not the mapping, so the string is stable.
    assert column_unit_string(("tbl", "Index"), units) == (
        "tbl=decimal_per_year|Index=index_level"
    )
