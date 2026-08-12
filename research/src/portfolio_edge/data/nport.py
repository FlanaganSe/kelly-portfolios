"""Form N-PORT: fund-reported monthly total returns, from the filings themselves.

Why this module exists
----------------------
``docs/decisions/0002-no-research-grade-free-price-source.md`` records that no
free *price* feed reachable from this project documents a total-return contract,
a corporate-action policy, delisting coverage or a revision history. That
decision stands. This module does not overturn it, because Form N-PORT is not a
price feed: it is a regulatory disclosure in which the fund itself reports its
own monthly total return, per share class, on a signed filing that the SEC
archives permanently.

That gives four properties a scraped price series does not have.

* **A defined statistic.** Item B.5 asks for the fund's monthly total return for
  each of the three months in the reporting period. It is the fund's own number,
  net of the fund's own ongoing fees, not a quotient of two adjusted closes.
* **A point-in-time archive.** Every filing keeps its own accession number,
  filing date and immutable document. A correction is a *new* document
  (``NPORT-P/A``) and the original stays readable, so a revision is visible
  rather than silent.
* **Coverage of funds that stopped existing.** A liquidated fund's filings do not
  disappear when its ticker does, and ``isFinalFiling`` marks the last one.
* **A stated filer.** The registrant, series and class identifiers are the SEC's,
  so a share class cannot be silently re-pointed at a different product.

What it still does not give, and why this stays exploratory
-----------------------------------------------------------
* Public N-PORT filings begin in 2019. Six years is far too short to identify a
  small residual return, which is the binding constraint on every conclusion
  drawn from it here.
* The figures are unaudited fund-reported data. They are checked here against an
  independent source and against the market factor, but not audited.
* A universe assembled from filings still misses any fund that died before the
  first quarter examined. N-PORT bounds survivorship; it does not remove it.

So :class:`NportReturnSeries` carries ``research_grade=False`` like every other
series in this package, and the guard in
:mod:`portfolio_edge.data.prices` still refuses it for confirmatory work.

Two shapes of access
--------------------
:func:`load_frame` reads one of the SEC's quarterly **N-PORT structured data
sets**, a single ZIP holding every filer's submission, fund and return tables for
that quarter. It is used to build the *universe* — every series that filed, with
its official name and net assets — because a census is the only honest frame for
a screen.

:func:`fetch_filing` reads **one filing's own XML**, which is how a single
series' history is assembled across quarters without downloading every filer.

Access policy: ``www.sec.gov`` requires a ``User-Agent`` that identifies the
requester and asks for no more than ten requests a second. Both are honoured
here; see https://www.sec.gov/os/webmaster-faq#developers.
"""

from __future__ import annotations

import csv
import io
import re
import time
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Final
from xml.etree import ElementTree

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import ParsedTable

__all__ = [
    "DATA_SET_URL_TEMPLATE",
    "EDGAR_USER_AGENT",
    "NPORT_PARSER_VERSION",
    "ClassReturn",
    "FilingRef",
    "FrameRow",
    "NportError",
    "NportFiling",
    "browse_edgar_url",
    "build_return_table",
    "data_set_url",
    "fetch_filing",
    "filing_index",
    "load_frame",
    "manifest_for_return_table",
    "months_covered",
]

NPORT_PARSER_VERSION: Final = "nport/1.0.0"

#: The SEC asks automated clients to identify themselves. An anonymous or
#: browser-shaped agent is throttled or blocked, and misrepresenting the client
#: would also be dishonest about who is fetching.
EDGAR_USER_AGENT: Final = "kelly-portfolios-research flanspan11@gmail.com"

DATA_SET_URL_TEMPLATE: Final = (
    "https://www.sec.gov/files/dera/data/form-n-port-data-sets/{quarter}_nport.zip"
)

#: SEC guidance is ten requests a second; this stays comfortably under it.
_REQUEST_INTERVAL_SECONDS: Final = 0.15

_NPORT_NS: Final = "{http://www.sec.gov/edgar/nport}"
_ATOM_FILING_HREF: Final = re.compile(r"<filing-href>([^<]+)</filing-href>")
_ATOM_FILING_DATE: Final = re.compile(r"<filing-date>([^<]+)</filing-date>")
_ATOM_FILING_TYPE: Final = re.compile(r"<filing-type>([^<]+)</filing-type>")

_MONTH_NAMES: Final = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}  # fmt: skip


class NportError(RuntimeError):
    """A filing or data set did not contain what Form N-PORT requires."""


def data_set_url(quarter: str) -> str:
    """URL of the SEC's structured data set for ``quarter``, e.g. ``2019q4``."""
    return DATA_SET_URL_TEMPLATE.format(quarter=quarter)


def browse_edgar_url(series_id: str, *, form_type: str = "NPORT-P", count: int = 100) -> str:
    """URL of the Atom feed listing ``form_type`` filings for one fund series.

    Series-level rather than registrant-level: a single trust files for dozens of
    series, and the registrant feed cannot say which filing belongs to which
    fund without opening every document.
    """
    return (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
        f"&CIK={series_id}&type={form_type}&dateb=&owner=include"
        f"&count={count}&output=atom"
    )


def _parse_dera_date(value: str) -> str:
    """``30-SEP-2019`` to ``2019-09-30``. Raises on anything else."""
    parts = value.strip().upper().split("-")
    if len(parts) != 3 or parts[1] not in _MONTH_NAMES:
        raise NportError(f"unrecognised N-PORT data-set date: {value!r}")
    return f"{int(parts[2]):04d}-{_MONTH_NAMES[parts[1]]:02d}-{int(parts[0]):02d}"


@dataclass(frozen=True, slots=True, kw_only=True)
class FrameRow:
    """One fund series as it appears in a quarterly N-PORT data set.

    This is *universe* information only. It deliberately carries no return, so
    that a screen written against it cannot be tuned on performance.
    """

    accession: str
    series_id: str
    series_name: str
    report_date: str
    """The reporting period end, ISO. The last of the three months covered."""
    net_assets: float | None
    is_last_filing: bool


def _iter_tsv(archive: zipfile.ZipFile, member: str) -> Iterator[dict[str, str]]:
    with archive.open(member) as handle:
        text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace", newline="")
        reader = csv.DictReader(text, delimiter="\t")
        for row in reader:
            yield {key: (value or "") for key, value in row.items() if key is not None}


def load_frame(cache: RawCache, quarter: str) -> tuple[dict[str, FrameRow], CacheEntry]:
    """Every ``NPORT-P`` fund series in one quarterly data set, by series id.

    When a series filed more than once in the quarter, the row with the latest
    reporting period is kept and the earlier one discarded; both describe the
    same fund and the later one is closer to the frame date.

    ``NPORT-P/A`` amendments are excluded: an amendment restates a filing already
    in the set, and counting both would double a fund in the census.
    """
    entry = cache.require(data_set_url(quarter))
    payload = cache.read(entry)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        submissions = {
            row["ACCESSION_NUMBER"]: row
            for row in _iter_tsv(archive, "SUBMISSION.tsv")
            if row.get("SUB_TYPE") == "NPORT-P"
        }
        frame: dict[str, FrameRow] = {}
        for row in _iter_tsv(archive, "FUND_REPORTED_INFO.tsv"):
            submission = submissions.get(row["ACCESSION_NUMBER"])
            if submission is None:
                continue
            report_date = _parse_dera_date(submission["REPORT_DATE"])
            series_id = row["SERIES_ID"].strip()
            if not series_id:
                # A handful of filers leave the series identifier blank. Such a
                # row cannot be joined to a ticker or to its own later filings, so
                # keying it would silently merge unrelated funds under one empty
                # key. It is dropped rather than guessed at.
                continue
            existing = frame.get(series_id)
            if existing is not None and existing.report_date >= report_date:
                continue
            raw_assets = row.get("NET_ASSETS", "").strip()
            frame[series_id] = FrameRow(
                accession=row["ACCESSION_NUMBER"],
                series_id=series_id,
                series_name=row["SERIES_NAME"].strip(),
                report_date=report_date,
                net_assets=float(raw_assets) if raw_assets else None,
                is_last_filing=submission.get("IS_LAST_FILING", "N").upper() == "Y",
            )
    return frame, entry


@dataclass(frozen=True, slots=True, kw_only=True)
class FilingRef:
    """One filing located in EDGAR, before its document has been read."""

    series_id: str
    accession: str
    filing_date: str
    form_type: str
    document_url: str


def filing_index(
    cache: RawCache, series_id: str, *, force: bool = False
) -> tuple[FilingRef, ...]:
    """Every ``NPORT-P`` filing EDGAR lists for ``series_id``, newest first.

    Amendments (``NPORT-P/A``) are returned too. Deduplication happens in
    :func:`build_return_table`, where the reporting period is known.
    """
    url = browse_edgar_url(series_id)
    entry = cache.fetch_via_curl(url, user_agent=EDGAR_USER_AGENT, force=force)
    text = cache.read(entry).decode("utf-8", errors="replace")
    hrefs = _ATOM_FILING_HREF.findall(text)
    dates = _ATOM_FILING_DATE.findall(text)
    types = _ATOM_FILING_TYPE.findall(text)
    if not (len(hrefs) == len(dates) == len(types)):
        raise NportError(
            f"{series_id}: EDGAR feed has {len(hrefs)} hrefs, {len(dates)} dates and "
            f"{len(types)} types; the feed layout has changed and parsing it would guess"
        )
    refs: list[FilingRef] = []
    for href, filing_date, form_type in zip(hrefs, dates, types, strict=True):
        directory, _, filename = href.rpartition("/")
        accession = filename.removesuffix("-index.htm")
        refs.append(
            FilingRef(
                series_id=series_id,
                accession=accession,
                filing_date=filing_date.strip(),
                form_type=form_type.strip(),
                document_url=f"{directory}/primary_doc.xml",
            )
        )
    return tuple(refs)


@dataclass(frozen=True, slots=True, kw_only=True)
class ClassReturn:
    """Item B.5 for one share class: three monthly total returns, in percent."""

    class_id: str
    returns: tuple[float | None, float | None, float | None]


@dataclass(frozen=True, slots=True, kw_only=True)
class NportFiling:
    """The header, fund totals and Item B.5 returns of one N-PORT filing."""

    accession: str
    form_type: str
    filing_date: str
    series_id: str
    series_name: str
    report_period_end: str
    """``repPdDate``: the last of the three months this filing reports."""
    fiscal_year_end: str
    is_final_filing: bool
    net_assets: float | None
    class_returns: tuple[ClassReturn, ...]
    entry: CacheEntry

    def returns_for(self, class_id: str) -> tuple[float | None, ...] | None:
        for item in self.class_returns:
            if item.class_id == class_id:
                return item.returns
        return None


def _text(element: ElementTree.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _optional_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def fetch_filing(cache: RawCache, ref: FilingRef, *, force: bool = False) -> NportFiling:
    """Download (or read from cache) and parse one filing's primary document."""
    entry = cache.fetch_via_curl(
        ref.document_url, user_agent=EDGAR_USER_AGENT, force=force
    )
    return parse_filing(cache.read(entry), ref=ref, entry=entry)


def parse_filing(payload: bytes, *, ref: FilingRef, entry: CacheEntry) -> NportFiling:
    """Parse the bytes of one ``primary_doc.xml``.

    Split from :func:`fetch_filing` so the parser is exercised offline against a
    frozen fixture rather than only against whatever EDGAR serves today.
    """
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise NportError(f"{ref.accession}: primary document is not XML: {exc}") from exc

    general = root.find(f".//{_NPORT_NS}genInfo")
    if general is None:
        raise NportError(f"{ref.accession}: no genInfo block; this is not a Form N-PORT")
    report_period_end = _text(general.find(f"{_NPORT_NS}repPdDate"))
    if len(report_period_end) != 10:
        raise NportError(
            f"{ref.accession}: repPdDate {report_period_end!r} is not an ISO date, so "
            "the three monthly returns cannot be assigned to months"
        )

    fund = root.find(f".//{_NPORT_NS}fundInfo")
    net_assets = (
        _optional_float(_text(fund.find(f"{_NPORT_NS}netAssets"))) if fund is not None else None
    )

    class_returns: list[ClassReturn] = []
    for node in root.iter(f"{_NPORT_NS}monthlyTotReturn"):
        class_returns.append(
            ClassReturn(
                class_id=node.get("classId", "").strip(),
                returns=(
                    _optional_float(node.get("rtn1", "")),
                    _optional_float(node.get("rtn2", "")),
                    _optional_float(node.get("rtn3", "")),
                ),
            )
        )

    return NportFiling(
        accession=ref.accession,
        form_type=ref.form_type,
        filing_date=ref.filing_date,
        series_id=_text(general.find(f"{_NPORT_NS}seriesId")) or ref.series_id,
        series_name=_text(general.find(f"{_NPORT_NS}seriesName")),
        report_period_end=report_period_end,
        fiscal_year_end=_text(general.find(f"{_NPORT_NS}repPdEnd")),
        is_final_filing=_text(general.find(f"{_NPORT_NS}isFinalFiling")).upper() == "Y",
        net_assets=net_assets,
        class_returns=tuple(class_returns),
        entry=entry,
    )


def months_covered(report_period_end: str) -> tuple[str, str, str]:
    """The three ``YYYY-MM`` labels a filing ending ``report_period_end`` reports.

    ``rtn1`` is the *first* month of the reporting period and ``rtn3`` the last,
    so the month ending on ``repPdDate`` is ``rtn3``. That ordering decides every
    number this module produces, so it is asserted against an independent series
    in the tests rather than taken on trust: a reversed reading would shift every
    fund's history by two months and quietly destroy every regression.
    """
    year, month = int(report_period_end[:4]), int(report_period_end[5:7])
    index = year * 12 + (month - 1)
    return tuple(  # type: ignore[return-value]
        f"{(index - offset) // 12:04d}-{(index - offset) % 12 + 1:02d}"
        for offset in (2, 1, 0)
    )


def build_return_table(
    filings: Sequence[NportFiling],
    *,
    class_id: str,
    table_id: str,
) -> ParsedTable:
    """Stitch one share class' monthly total returns into a single table.

    Returns are converted from the filed percent to decimal, the same convention
    every other reader in this package uses.

    Conflicts are recorded, never averaged. When two filings report the same
    month — an amendment, or overlapping reporting periods — the value from the
    filing with the later filing date wins and the disagreement becomes a
    warning, because a silently reconciled restatement is exactly the kind of
    revision this source exists to make visible.
    """
    chosen: dict[str, tuple[float, str, str]] = {}
    warnings: list[str] = []
    amendments = sum(1 for filing in filings if filing.form_type.endswith("/A"))
    if amendments:
        warnings.append(
            f"{amendments} of {len(filings)} filings are NPORT-P/A amendments; the "
            "later filing supersedes the earlier one for any month they share"
        )

    for filing in sorted(filings, key=lambda item: (item.filing_date, item.accession)):
        values = filing.returns_for(class_id)
        if values is None:
            warnings.append(
                f"{filing.accession} ({filing.report_period_end}) reports no Item B.5 "
                f"return for class {class_id}"
            )
            continue
        for period, value in zip(months_covered(filing.report_period_end), values, strict=True):
            if value is None:
                warnings.append(f"{filing.accession}: {period} return was blank in the filing")
                continue
            previous = chosen.get(period)
            if previous is not None and abs(previous[0] - value) > 1e-9:
                warnings.append(
                    f"{period}: {previous[1]} reported {previous[0]:.6f}% and "
                    f"{filing.accession} reported {value:.6f}%; the later filing is used"
                )
            chosen[period] = (value, filing.accession, filing.filing_date)

    periods = tuple(sorted(chosen))
    if periods:
        expected = _month_span(periods[0], periods[-1])
        missing = [period for period in expected if period not in chosen]
        if missing:
            warnings.append(
                f"{len(missing)} month(s) inside {periods[0]}..{periods[-1]} have no "
                f"filed return: {', '.join(missing[:12])}"
                + (" ..." if len(missing) > 12 else "")
            )

    return ParsedTable(
        table_id=table_id,
        banner=(
            "Form N-PORT Item B.5 monthly total return, as reported by the fund for "
            f"share class {class_id}"
        ),
        columns=("total_return",),
        periods=periods,
        values=tuple((chosen[period][0] / 100.0,) for period in periods),
        frequency="monthly",
        source_units="percent",
        units="decimal",
        unit_transform="value / 100",
        warnings=tuple(warnings),
    )


def _month_span(first: str, last: str) -> tuple[str, ...]:
    start = int(first[:4]) * 12 + int(first[5:7]) - 1
    end = int(last[:4]) * 12 + int(last[5:7]) - 1
    return tuple(f"{index // 12:04d}-{index % 12 + 1:02d}" for index in range(start, end + 1))


def manifest_for_return_table(
    *,
    dataset_id: str,
    table: ParsedTable,
    entry: CacheEntry,
    filings: Sequence[NportFiling],
    class_id: str,
    ticker: str,
) -> DatasetManifest:
    """Provenance for a stitched N-PORT return series.

    ``entry`` pins one filing; the series is built from many, so every accession
    and its digest is written into the warnings. A manifest that pinned only the
    newest filing would claim more reproducibility than it has.
    """
    return manifest_from_table(
        dataset_id=dataset_id,
        entry=entry,
        table=table,
        parser_version=NPORT_PARSER_VERSION,
        availability_policy=(
            "Public Form N-PORT reporting begins with periods ending 2019-09-30; "
            "the first filings reached EDGAR on 2019-10-22, and reports for "
            "periods from 2019-03 to 2019-08 were filed but kept non-public. Each "
            "monthly return became public when its filing was accepted, which is "
            "30 to 60 days after the reporting period ends. No observation here "
            "may be treated as available on the last day of the month it "
            "describes."
        ),
        revision_policy=(
            "A correction is filed as a separate NPORT-P/A document and the "
            "original filing stays retrievable, so revisions are visible rather "
            "than silent. Figures are fund-reported and unaudited."
        ),
        license_or_terms_url="https://www.sec.gov/os/webmaster-faq#developers",
        extra_warnings=(
            f"ticker={ticker}, series_class={class_id}",
            "series_kind=fund_reported_total_return; research_grade=False",
            "EXPLORATORY. Public Form N-PORT filings begin in 2019, so this "
            "series is far too short to identify a small residual return.",
            *(
                f"filing {filing.accession} {filing.form_type} filed "
                f"{filing.filing_date} covering ..{filing.report_period_end} "
                f"sha256={filing.entry.sha256}"
                for filing in sorted(filings, key=lambda item: item.report_period_end)
            ),
        ),
    )


def throttle() -> None:
    """Sleep between EDGAR requests, honouring the SEC's ten-per-second guidance."""
    time.sleep(_REQUEST_INTERVAL_SECONDS)


def frame_net_assets(frame: Mapping[str, FrameRow], series_id: str) -> float | None:
    """Net assets for ``series_id`` in a loaded frame, or ``None`` if absent."""
    row = frame.get(series_id)
    return None if row is None else row.net_assets
