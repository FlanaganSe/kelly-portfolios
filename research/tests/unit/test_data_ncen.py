"""Form N-CEN reader: the two traps are the units and the missing value.

The fixture is a trimmed copy of Vanguard Index Funds' fiscal-2025 N-CEN, cut down to
the VTI and VOO series blocks. Expected values are read off the filing itself and the
derived ones are computed here by hand, so a passing test checks the parser rather than
restating it.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from portfolio_edge.data.ncen import (
    NcenError,
    NcenFilingRef,
    NcenSeriesRecord,
    latest_by_series,
    parse_ncen,
    securities_lending_bp,
    tracking_difference_is_internally_consistent,
)

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "ncen_vanguard_index_funds_2025.xml"
)
ACCESSION = "0000036405-26-000103"


def _by_ticker(ticker: str) -> NcenSeriesRecord:
    for record in parse_ncen(FIXTURE.read_bytes(), accession=ACCESSION):
        if ticker in record.tickers:
            return record
    raise AssertionError(f"fixture has no series carrying {ticker}")


def test_the_fixture_yields_one_record_per_series_with_its_classes() -> None:
    records = parse_ncen(FIXTURE.read_bytes(), accession=ACCESSION)
    assert len(records) == 2
    assert {record.series_id for record in records} == {"S000002839", "S000002848"}
    for record in records:
        assert record.fiscal_year_end == "2025-12-31"
        assert record.accession == ACCESSION

    voo = _by_ticker("VOO")
    assert voo.fund_name == "VANGUARD 500 INDEX FUND"
    # Four classes share one portfolio, which is exactly why the after-expense
    # tracking difference below cannot be read as the ETF class's.
    assert voo.class_count == 4
    assert set(voo.tickers) == {"VFIAX", "VOO", "VFFSX", "VFINX"}


def test_securities_lending_is_reported_in_dollars_and_converts_to_basis_points() -> None:
    """VOO earns 0.07 bp of net assets a year and VTI 1.02 — a fourteen-fold gap.

    Both figures are Item C.6.g over Item C.2, computed here from the filed dollars
    rather than read back from the parser. The gap is the whole of the contractual
    difference between the two funds, which charge the same fee and distribute the same
    nothing, and it is the reason a total-market fund is not merely "the S&P 500 plus
    noise" on cost.
    """
    voo, vti = _by_ticker("VOO"), _by_ticker("VTI")
    assert voo.net_securities_lending_income == pytest.approx(10_002_223.40)
    assert voo.monthly_average_net_assets == pytest.approx(1_408_456_183_321.804, rel=1e-9)
    assert voo.securities_lending_bp == pytest.approx(
        10_002_223.40 / 1_408_456_183_321.804 * 1e4, rel=1e-12
    )
    assert voo.securities_lending_bp == pytest.approx(0.071, abs=5e-4)

    assert vti.securities_lending_bp == pytest.approx(
        194_031_188.51 / 1_903_470_699_301.935 * 1e4, rel=1e-12
    )
    assert vti.securities_lending_bp == pytest.approx(1.019, abs=5e-4)
    assert vti.lends_securities and voo.lends_securities

    # Vanguard is its own lending agent and indemnifies nothing, which the ratio hides.
    assert voo.lending_agent == "The Vanguard Group, Inc."
    assert voo.lending_agent_affiliated is True
    assert voo.borrower_default_indemnified is False


def test_a_missing_denominator_returns_none_rather_than_zero() -> None:
    """A fund that filed nothing and a fund that earned nothing are different facts.

    Form N-CEN lets a filer write ``N/A`` into a numeric field, and several bond funds
    do exactly that for lending income because they do not lend. Coercing it to zero
    would make "did not lend" indistinguishable from "lent and earned nothing", and the
    second is a judgement about the lending desk that the filing does not support.
    """
    assert securities_lending_bp(None, 1.0) is None
    assert securities_lending_bp(1.0, None) is None
    assert securities_lending_bp(1.0, 0.0) is None
    assert securities_lending_bp(1.0, 1e8) == pytest.approx(0.0001)


def test_the_tracking_difference_consistency_screen_catches_a_filer_error() -> None:
    """``before - after`` must be positive, and for a single-class ETF it is the fee.

    On this multi-class fixture it is not: VOO's gap is 16.5 bp against an ETF-class
    expense ratio of 3, because Item C.3.b does not say which class the fund answered
    for. The screen still passes, because the ordering is right; what fails the screen
    elsewhere is a filer reporting one number twice.
    """
    voo = _by_ticker("VOO")
    assert voo.tracking_difference_before_expenses == pytest.approx(-0.00397999)
    assert voo.tracking_difference_after_expenses == pytest.approx(-0.16890)
    assert voo.implied_expense_ratio == pytest.approx(0.16492001, abs=5e-8)
    assert voo.implied_expense_ratio is not None and voo.implied_expense_ratio > 0.10
    assert tracking_difference_is_internally_consistent(voo)

    equal = _replace_tracking(voo, before=-0.04, after=-0.04)
    transposed = _replace_tracking(voo, before=-0.13, after=-0.03)
    absent = _replace_tracking(voo, before=None, after=None)
    assert not tracking_difference_is_internally_consistent(equal)
    assert not tracking_difference_is_internally_consistent(transposed)
    assert not tracking_difference_is_internally_consistent(absent)
    assert absent.implied_expense_ratio is None


def test_latest_by_series_keeps_the_newest_fiscal_year_not_the_newest_filing() -> None:
    """A registrant files several N-CENs a year, one per fiscal-year group.

    So the most recent *filing* is not the most recent *year* for every series in the
    trust, and taking the first record seen would silently mix vintages.
    """
    old = _replace_year(_by_ticker("VOO"), "2024-12-31")
    new = _by_ticker("VOO")
    assert latest_by_series([new, old])["S000002839"].fiscal_year_end == "2025-12-31"
    assert latest_by_series([old, new])["S000002839"].fiscal_year_end == "2025-12-31"


def test_expense_limitation_flags_are_read_and_vanguard_carries_none() -> None:
    for record in parse_ncen(FIXTURE.read_bytes(), accession=ACCESSION):
        assert record.expense_limitation_in_place is False
        assert record.expenses_waived is False
        assert record.waived_fees_recoupable is False
        assert record.waived_expenses_recouped is False


def test_a_document_that_is_not_an_n_cen_raises_rather_than_parsing_to_nothing() -> None:
    with pytest.raises(NcenError, match="not XML"):
        parse_ncen(b"<not xml", accession=ACCESSION)
    with pytest.raises(NcenError, match="not a Form N-CEN"):
        parse_ncen(
            b'<?xml version="1.0"?><edgarSubmission '
            b'xmlns="http://www.sec.gov/edgar/ncen"></edgarSubmission>',
            accession=ACCESSION,
        )


def test_the_document_url_is_built_from_the_accession() -> None:
    ref = NcenFilingRef(cik=36405, accession=ACCESSION, filing_date="2026-03-12")
    assert ref.document_url == (
        "https://www.sec.gov/Archives/edgar/data/36405/000003640526000103/primary_doc.xml"
    )


def _replace_tracking(
    record: NcenSeriesRecord, *, before: float | None, after: float | None
) -> NcenSeriesRecord:
    return dataclasses.replace(
        record,
        tracking_difference_before_expenses=before,
        tracking_difference_after_expenses=after,
    )


def _replace_year(record: NcenSeriesRecord, year: str) -> NcenSeriesRecord:
    return dataclasses.replace(record, fiscal_year_end=year)
