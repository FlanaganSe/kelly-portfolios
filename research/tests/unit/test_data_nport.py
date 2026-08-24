"""Form N-PORT reader: the month alignment is the test that matters.

Item B.5 reports three monthly returns per filing and nothing in the XML says
which month is which. Reading them in the wrong order shifts every fund's history
by two months while leaving every number plausible, so the mapping is pinned here
and cross-checked against a live filing in the network tests.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import pytest

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.nport import (
    ClassReturn,
    FilingRef,
    MonthlyFlow,
    NportError,
    NportFiling,
    browse_edgar_url,
    build_flow_table,
    build_return_table,
    data_set_url,
    load_frame,
    manifest_for_return_table,
    months_covered,
    parse_filing,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "nport_mtum_2026q1.xml"


def _entry(url: str = "https://example.invalid/primary_doc.xml") -> CacheEntry:
    return CacheEntry(
        url=url,
        sha256="0" * 64,
        size_bytes=1,
        retrieved_utc="2026-08-12T00:00:00Z",
        http_status=200,
        headers=(("content-type", "text/xml"),),
    )


def _ref(accession: str = "0001004726-26-005159", form_type: str = "NPORT-P") -> FilingRef:
    return FilingRef(
        series_id="S000040316",
        accession=accession,
        filing_date="2026-06-25",
        form_type=form_type,
        document_url="https://example.invalid/primary_doc.xml",
    )


# --------------------------------------------------------------------------- #
# Month alignment
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("report_period_end", "expected"),
    [
        ("2026-04-30", ("2026-02", "2026-03", "2026-04")),
        ("2020-01-31", ("2019-11", "2019-12", "2020-01")),
        ("2019-09-30", ("2019-07", "2019-08", "2019-09")),
        ("2021-12-31", ("2021-10", "2021-11", "2021-12")),
        ("2022-01-31", ("2021-11", "2021-12", "2022-01")),
    ],
)
def test_rtn1_is_the_earliest_month_and_rtn3_ends_on_the_report_date(
    report_period_end: str, expected: tuple[str, str, str]
) -> None:
    """The SEC's own data-set documentation names them First, Second, Third month.

    Confirmed independently against a real filing: iShares MSCI USA Momentum
    Factor ETF, reporting period ending 2020-04-30, filed rtn1 = -7.36,
    rtn2 = -11.41, rtn3 = +11.75. February, March and April 2020 in that order --
    March 2020 is the COVID crash and April the rebound. Read in reverse the
    crash would land in February and the rebound in February's place.
    """
    assert months_covered(report_period_end) == expected


def test_months_covered_crosses_a_year_boundary_without_arithmetic_error() -> None:
    assert months_covered("2020-02-29") == ("2019-12", "2020-01", "2020-02")


# --------------------------------------------------------------------------- #
# Parsing a real filing
# --------------------------------------------------------------------------- #


def test_parses_a_real_filing_header_and_item_b5() -> None:
    """The fixture is a genuine filing with only its holdings list removed."""
    filing = parse_filing(FIXTURE.read_bytes(), ref=_ref(), entry=_entry())
    assert filing.series_id == "S000040316"
    assert filing.series_name == "iShares MSCI USA Momentum Factor ETF"
    assert filing.report_period_end == "2026-04-30"
    assert filing.fiscal_year_end == "2026-07-31"
    assert filing.is_final_filing is False
    assert filing.net_assets is not None and filing.net_assets > 0.0
    assert len(filing.class_returns) == 1
    assert filing.returns_for("C000125223") == (-1.09, -4.96, 18.22)
    assert filing.returns_for("C000000000") is None


def test_report_period_end_is_used_not_the_fiscal_year_end() -> None:
    """``repPdEnd`` is the fiscal year end and would misdate every return.

    In the fixture the two differ by three months, so confusing them is
    detectable rather than a coin flip.
    """
    filing = parse_filing(FIXTURE.read_bytes(), ref=_ref(), entry=_entry())
    assert filing.fiscal_year_end != filing.report_period_end
    assert months_covered(filing.report_period_end)[-1] == "2026-04"


def test_a_non_nport_document_is_refused_rather_than_half_parsed() -> None:
    payload = b'<?xml version="1.0"?><somethingElse><a/></somethingElse>'
    with pytest.raises(NportError, match="no genInfo"):
        parse_filing(payload, ref=_ref(), entry=_entry())


def test_invalid_xml_is_refused() -> None:
    with pytest.raises(NportError, match="not XML"):
        parse_filing(b"<not xml", ref=_ref(), entry=_entry())


def test_a_missing_report_date_is_refused_because_months_cannot_be_assigned() -> None:
    payload = (
        b'<?xml version="1.0"?>'
        b'<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">'
        b"<formData><genInfo><repPdDate></repPdDate></genInfo></formData>"
        b"</edgarSubmission>"
    )
    with pytest.raises(NportError, match="not an ISO date"):
        parse_filing(payload, ref=_ref(), entry=_entry())


def test_the_string_na_becomes_a_missing_value_not_a_zero() -> None:
    """A terminated share class legitimately files ``N/A``; zero would be a return."""
    payload = (
        b'<?xml version="1.0"?>'
        b'<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">'
        b"<formData><genInfo><repPdDate>2021-03-31</repPdDate></genInfo>"
        b'<fundInfo><returnInfo><monthlyTotReturns>'
        b'<monthlyTotReturn classId="C1" rtn1="1.5" rtn2="N/A" rtn3="N/A"/>'
        b"</monthlyTotReturns></returnInfo></fundInfo></formData>"
        b"</edgarSubmission>"
    )
    filing = parse_filing(payload, ref=_ref(), entry=_entry())
    assert filing.returns_for("C1") == (1.5, None, None)


# --------------------------------------------------------------------------- #
# Stitching filings into one series
# --------------------------------------------------------------------------- #


def _filing(
    period_end: str,
    values: tuple[float | None, float | None, float | None],
    *,
    accession: str,
    filing_date: str,
    form_type: str = "NPORT-P",
) -> NportFiling:
    return NportFiling(
        accession=accession,
        form_type=form_type,
        filing_date=filing_date,
        series_id="S1",
        series_name="Test Fund",
        report_period_end=period_end,
        fiscal_year_end=period_end,
        is_final_filing=False,
        net_assets=1.0,
        class_returns=(ClassReturn(class_id="C1", returns=values),),
        entry=_entry(),
    )


def test_consecutive_filings_stitch_into_a_contiguous_monthly_series() -> None:
    """Quarterly filings each carry three months, so coverage has no holes."""
    filings = [
        _filing("2020-03-31", (1.0, 2.0, 3.0), accession="a", filing_date="2020-05-01"),
        _filing("2020-06-30", (4.0, 5.0, 6.0), accession="b", filing_date="2020-08-01"),
    ]
    table = build_return_table(filings, class_id="C1", table_id="t")
    assert table.periods == (
        "2020-01", "2020-02", "2020-03", "2020-04", "2020-05", "2020-06",
    )
    assert table.units == "decimal"
    assert table.source_units == "percent"
    assert [row[0] for row in table.values] == pytest.approx(
        [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
    )


def test_an_amendment_supersedes_the_original_and_the_disagreement_is_recorded() -> None:
    """A restatement must be visible, never silently averaged away."""
    filings = [
        _filing("2020-03-31", (1.0, 2.0, 3.0), accession="a", filing_date="2020-05-01"),
        _filing(
            "2020-03-31",
            (1.0, 2.0, 9.0),
            accession="b",
            filing_date="2020-07-01",
            form_type="NPORT-P/A",
        ),
    ]
    table = build_return_table(filings, class_id="C1", table_id="t")
    assert dict(zip(table.periods, (row[0] for row in table.values), strict=True))[
        "2020-03"
    ] == pytest.approx(0.09)
    joined = " ".join(table.warnings)
    assert "amendments" in joined
    assert "3.000000%" in joined and "9.000000%" in joined
    assert "the later filing is used" in joined


def test_a_gap_between_filings_is_reported_and_not_interpolated() -> None:
    filings = [
        _filing("2020-03-31", (1.0, 2.0, 3.0), accession="a", filing_date="2020-05-01"),
        _filing("2020-12-31", (4.0, 5.0, 6.0), accession="b", filing_date="2021-02-01"),
    ]
    table = build_return_table(filings, class_id="C1", table_id="t")
    assert "2020-04" not in table.periods
    joined = " ".join(table.warnings)
    assert "have no filed return" in joined
    assert "2020-04" in joined


def test_a_blank_return_is_a_gap_not_a_zero() -> None:
    filings = [
        _filing("2020-03-31", (1.0, None, 3.0), accession="a", filing_date="2020-05-01")
    ]
    table = build_return_table(filings, class_id="C1", table_id="t")
    assert table.periods == ("2020-01", "2020-03")
    assert any("blank in the filing" in warning for warning in table.warnings)


def test_a_class_absent_from_a_filing_is_recorded() -> None:
    filings = [_filing("2020-03-31", (1.0, 2.0, 3.0), accession="a", filing_date="2020-05-01")]
    table = build_return_table(filings, class_id="C-OTHER", table_id="t")
    assert table.periods == ()
    assert any("no Item B.5 return" in warning for warning in table.warnings)


def test_the_manifest_names_every_filing_that_produced_the_series() -> None:
    """Pinning only the newest filing would overstate what is reproducible."""
    filings = [
        _filing("2020-03-31", (1.0, 2.0, 3.0), accession="a", filing_date="2020-05-01"),
        _filing("2020-06-30", (4.0, 5.0, 6.0), accession="b", filing_date="2020-08-01"),
    ]
    table = build_return_table(filings, class_id="C1", table_id="t")
    manifest = manifest_for_return_table(
        dataset_id="nport_test",
        table=table,
        entry=_entry(),
        filings=filings,
        class_id="C1",
        ticker="TEST",
    )
    joined = " ".join(manifest.warnings)
    assert "filing a NPORT-P" in joined and "filing b NPORT-P" in joined
    assert "research_grade=False" in joined
    assert "2019" in manifest.availability_policy
    assert "NPORT-P/A" in manifest.revision_policy


# --------------------------------------------------------------------------- #
# URLs and the data set reader
# --------------------------------------------------------------------------- #


def test_urls_are_built_from_the_identifiers_not_string_formatted_by_hand() -> None:
    assert data_set_url("2019q4").endswith("/2019q4_nport.zip")
    assert "CIK=S000040316" in browse_edgar_url("S000040316")
    assert "type=NPORT-P" in browse_edgar_url("S000040316")
    assert "output=atom" in browse_edgar_url("S000040316")


def _data_set_bytes(rows: list[dict[str, str]], fund_rows: list[dict[str, str]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, records, columns in (
            (
                "SUBMISSION.tsv",
                rows,
                ["ACCESSION_NUMBER", "SUB_TYPE", "REPORT_DATE", "IS_LAST_FILING"],
            ),
            (
                "FUND_REPORTED_INFO.tsv",
                fund_rows,
                ["ACCESSION_NUMBER", "SERIES_NAME", "SERIES_ID", "NET_ASSETS"],
            ),
        ):
            text = io.StringIO()
            writer = csv.DictWriter(text, fieldnames=columns, delimiter="\t")
            writer.writeheader()
            writer.writerows(records)
            archive.writestr(name, text.getvalue())
    return buffer.getvalue()


def test_the_frame_keeps_the_latest_report_and_drops_amendments(tmp_path: Path) -> None:
    """An NPORT-P/A restates a filing already counted; both would double the fund."""
    payload = _data_set_bytes(
        [
            {
                "ACCESSION_NUMBER": "a",
                "SUB_TYPE": "NPORT-P",
                "REPORT_DATE": "31-JUL-2019",
                "IS_LAST_FILING": "N",
            },
            {
                "ACCESSION_NUMBER": "b",
                "SUB_TYPE": "NPORT-P",
                "REPORT_DATE": "30-SEP-2019",
                "IS_LAST_FILING": "Y",
            },
            {
                "ACCESSION_NUMBER": "c",
                "SUB_TYPE": "NPORT-P/A",
                "REPORT_DATE": "30-SEP-2019",
                "IS_LAST_FILING": "N",
            },
        ],
        [
            {
                "ACCESSION_NUMBER": "a",
                "SERIES_NAME": "Fund One",
                "SERIES_ID": "S1",
                "NET_ASSETS": "100",
            },
            {
                "ACCESSION_NUMBER": "b",
                "SERIES_NAME": "Fund One",
                "SERIES_ID": "S1",
                "NET_ASSETS": "250",
            },
            {
                "ACCESSION_NUMBER": "c",
                "SERIES_NAME": "Fund One",
                "SERIES_ID": "S1",
                "NET_ASSETS": "999",
            },
        ],
    )
    cache = RawCache(tmp_path)
    cache.store(data_set_url("2019q4"), payload)
    frame, entry = load_frame(cache, "2019q4")
    assert set(frame) == {"S1"}
    assert frame["S1"].net_assets == pytest.approx(250.0)
    assert frame["S1"].report_date == "2019-09-30"
    assert frame["S1"].is_last_filing is True
    assert entry.sha256


def test_a_malformed_data_set_date_is_refused(tmp_path: Path) -> None:
    payload = _data_set_bytes(
        [
            {
                "ACCESSION_NUMBER": "a",
                "SUB_TYPE": "NPORT-P",
                "REPORT_DATE": "2019-09-30",
                "IS_LAST_FILING": "N",
            }
        ],
        [
            {
                "ACCESSION_NUMBER": "a",
                "SERIES_NAME": "Fund",
                "SERIES_ID": "S1",
                "NET_ASSETS": "1",
            }
        ],
    )
    cache = RawCache(tmp_path)
    cache.store(data_set_url("2019q4"), payload)
    with pytest.raises(NportError, match="unrecognised N-PORT data-set date"):
        load_frame(cache, "2019q4")


def test_a_blank_net_assets_becomes_none_rather_than_zero(tmp_path: Path) -> None:
    payload = _data_set_bytes(
        [
            {
                "ACCESSION_NUMBER": "a",
                "SUB_TYPE": "NPORT-P",
                "REPORT_DATE": "30-SEP-2019",
                "IS_LAST_FILING": "N",
            }
        ],
        [
            {
                "ACCESSION_NUMBER": "a",
                "SERIES_NAME": "Fund",
                "SERIES_ID": "S1",
                "NET_ASSETS": "",
            }
        ],
    )
    cache = RawCache(tmp_path)
    cache.store(data_set_url("2019q4"), payload)
    frame, _ = load_frame(cache, "2019q4")
    assert frame["S1"].net_assets is None


def test_the_fixture_is_a_real_filing_and_stays_that_way() -> None:
    """Guards against the fixture being quietly regenerated into a mock."""
    text = FIXTURE.read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?><edgarSubmission')
    assert "http://www.sec.gov/edgar/nport" in text
    assert "holdings removed" in text, "the fixture must say what was removed from it"
    assert json.dumps(text.count("<monthlyTotReturn ")) == "1"


def test_a_row_with_a_blank_series_identifier_is_dropped_not_merged(tmp_path: Path) -> None:
    """A blank series id cannot be joined to a ticker or to its own later filings.

    Keying on it would silently merge unrelated funds under one empty key, and the
    merged row would then sort ahead of every real one.
    """
    payload = _data_set_bytes(
        [
            {
                "ACCESSION_NUMBER": "a",
                "SUB_TYPE": "NPORT-P",
                "REPORT_DATE": "30-SEP-2019",
                "IS_LAST_FILING": "N",
            },
            {
                "ACCESSION_NUMBER": "b",
                "SUB_TYPE": "NPORT-P",
                "REPORT_DATE": "30-SEP-2019",
                "IS_LAST_FILING": "N",
            },
        ],
        [
            {
                "ACCESSION_NUMBER": "a",
                "SERIES_NAME": "Nameless One",
                "SERIES_ID": "",
                "NET_ASSETS": "1",
            },
            {
                "ACCESSION_NUMBER": "b",
                "SERIES_NAME": "Real Fund",
                "SERIES_ID": "S1",
                "NET_ASSETS": "2",
            },
        ],
    )
    cache = RawCache(tmp_path)
    cache.store(data_set_url("2019q4"), payload)
    frame, _ = load_frame(cache, "2019q4")
    assert set(frame) == {"S1"}


def test_the_two_cash_rate_conventions_are_not_the_same_number() -> None:
    """The units trap behind the cash-rate substitution test.

    Ken French distributes RF as a decimal rate PER MONTH; this repository's FRED
    reader normalises TB3MS, DGS3MO and DFF to ``decimal_per_year``. Treating one
    as the other is a factor-of-100 error in the direction that makes the choice
    of cash series look enormously important when it is worth a few basis points.
    """
    french_monthly_rate = 0.00222  # about 2.66% a year
    fred_annual_rate = 0.0270  # 2.70% a year, as FRED is parsed

    french_annual_percent = french_monthly_rate * 12 * 100
    fred_annual_percent = fred_annual_rate * 100

    assert french_annual_percent == pytest.approx(2.664, abs=0.001)
    assert fred_annual_percent == pytest.approx(2.700, abs=0.001)
    # Converted correctly the two agree to a few basis points a year.
    assert abs(french_annual_percent - fred_annual_percent) < 0.10
    # Compared without converting they differ by roughly the whole rate.
    assert abs(french_annual_percent - fred_annual_rate) > 2.6


# --------------------------------------------------------------------------- #
# Item B.6 monthly flows
# --------------------------------------------------------------------------- #


def test_monthly_flows_are_parsed_and_ordered_like_the_returns() -> None:
    """``mon1Flow`` is the first month of the period, exactly as ``rtn1`` is.

    If the two blocks were read in opposite orders a distribution would be
    attributed to the wrong month while every number stayed plausible, which is the
    same failure the return alignment test exists to prevent.
    """
    filing = parse_filing(FIXTURE.read_bytes(), ref=_ref(), entry=_entry())
    assert [flow.month for flow in filing.monthly_flows] == [1, 2, 3]
    first = filing.monthly_flows[0]
    assert first.sales == pytest.approx(632839095.95)
    assert first.redemption == pytest.approx(442684928.35)
    assert first.reinvestment == pytest.approx(0.0)


def test_a_filing_without_a_flow_block_carries_no_flows_rather_than_zeros() -> None:
    """"Reported nothing" and "reported zero" are different statements."""
    payload = FIXTURE.read_bytes()
    for position in (1, 2, 3):
        start = payload.index(f"<mon{position}Flow".encode())
        end = payload.index(b"/>", start) + 2
        payload = payload[:start] + payload[end:]
    filing = parse_filing(payload, ref=_ref(), entry=_entry())
    assert filing.monthly_flows == ()


def test_build_flow_table_assigns_each_flow_to_its_calendar_month() -> None:
    filings = [
        _filing_with_flows(
            "2020-03-31", accession="a", filing_date="2020-05-01", reinvestments=(1.0, 2.0, 3.0)
        ),
        _filing_with_flows(
            "2020-06-30", accession="b", filing_date="2020-08-01", reinvestments=(4.0, 5.0, 6.0)
        ),
    ]
    table = build_flow_table(filings)
    assert sorted(table) == [
        "2020-01", "2020-02", "2020-03", "2020-04", "2020-05", "2020-06",
    ]
    assert table["2020-01"].reinvestment == pytest.approx(1.0)
    assert table["2020-06"].reinvestment == pytest.approx(6.0)


def test_a_later_filing_supersedes_an_earlier_one_for_a_shared_flow_month() -> None:
    """The same rule as the returns: an amendment restates, it does not average."""
    filings = [
        _filing_with_flows(
            "2020-03-31", accession="a", filing_date="2020-05-01", reinvestments=(1.0, 2.0, 3.0)
        ),
        _filing_with_flows(
            "2020-03-31",
            accession="b",
            filing_date="2020-09-01",
            reinvestments=(9.0, 9.0, 9.0),
            form_type="NPORT-P/A",
        ),
    ]
    assert build_flow_table(filings)["2020-02"].reinvestment == pytest.approx(9.0)


def _filing_with_flows(
    period_end: str,
    *,
    accession: str,
    filing_date: str,
    reinvestments: tuple[float, float, float],
    form_type: str = "NPORT-P",
) -> NportFiling:
    filing = _filing(
        period_end, (0.0, 0.0, 0.0), accession=accession, filing_date=filing_date,
        form_type=form_type,
    )
    return NportFiling(
        accession=filing.accession,
        form_type=filing.form_type,
        filing_date=filing.filing_date,
        series_id=filing.series_id,
        series_name=filing.series_name,
        report_period_end=filing.report_period_end,
        fiscal_year_end=filing.fiscal_year_end,
        is_final_filing=filing.is_final_filing,
        net_assets=filing.net_assets,
        class_returns=filing.class_returns,
        entry=filing.entry,
        monthly_flows=tuple(
            MonthlyFlow(month=index + 1, sales=None, redemption=None, reinvestment=value)
            for index, value in enumerate(reinvestments)
        ),
    )
