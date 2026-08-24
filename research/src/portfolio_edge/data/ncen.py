"""Form N-CEN: the annual census, and the only *structured* source of fund costs held.

Why this module exists
----------------------
:mod:`portfolio_edge.data.nport` reads a fund's own monthly total return. It cannot
read what that return cost. Form N-CEN can, because three of its items are exactly the
contractual quantities a fund-selection decision turns on, and all three are filed as
XML rather than buried in an annual report's HTML:

``Item C.3.b.ii`` — **tracking difference**
    "the annualized difference between the Fund's total return during the reporting
    period and the index's return during the reporting period", reported twice: before
    fund fees and expenses, and after them. This is the number a fee comparison is
    usually mistaken for.
``Item C.6.f`` and ``C.6.g`` — **securities lending**
    the monthly average value of portfolio securities on loan, and the net income from
    lending them. Over Item C.2's monthly average net assets this is the pass-through
    accruing to shareholders, in basis points, per fund per year.
``Item C.8`` — **expense limitations**
    whether an expense limitation arrangement was in place, whether anything was waived
    under it, and — the field that changes a forward cost and is invisible in a fee
    table's headline — whether the waiver is **recoupable**.

What it does not give, and why nothing here is promoted
-------------------------------------------------------
* **The figures are filer-reported and unaudited, and the filings show it.** Every
  fiscal-2025 and fiscal-2026 iShares filing read here reports the before- and
  after-expense tracking difference as the *same number*, which cannot be right for a
  fund that charges a fee. :func:`tracking_difference_is_internally_consistent` is the
  screen that catches it; it is a data-quality check, not a judgement about the fund.
* **The item does not say which share class a multi-class fund answers for.** For a
  single-class ETF the gap between the two figures recovers the expense ratio to the
  filed rounding. For a Vanguard series with six classes it does not, so the
  after-expense figure there is not the ETF class's tracking difference and must not be
  compared with a single-class ETF's.
* **Each fund's difference is against its own index, and the indices differ.** Ranking
  across categories on this field would add lines measured against different benchmarks,
  which is the error ``aggregate()`` in
  :mod:`portfolio_edge.studies.outperformance_horizon` raises rather than commits.
* Public N-CEN filings begin in 2018, so the panel is short for the same reason
  everything else built on EDGAR here is.

Access policy is :mod:`portfolio_edge.data.nport`'s: ``www.sec.gov`` requires a
``User-Agent`` identifying the requester and no more than ten requests a second, and
both are honoured through :class:`portfolio_edge.data.cache.RawCache`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final
from xml.etree import ElementTree

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.nport import EDGAR_USER_AGENT, throttle

__all__ = [
    "NCEN_PARSER_VERSION",
    "NcenError",
    "NcenFilingRef",
    "NcenSeriesRecord",
    "fetch_ncen",
    "latest_by_series",
    "ncen_filing_index",
    "parse_ncen",
    "securities_lending_bp",
    "tracking_difference_is_internally_consistent",
]

NCEN_PARSER_VERSION: Final = "ncen/1.0.0"

_NS: Final = "{http://www.sec.gov/edgar/ncen}"
_SUBMISSIONS_URL: Final = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_DOCUMENT_URL: Final = "https://www.sec.gov/Archives/edgar/data/{cik}/{plain}/primary_doc.xml"
_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")


class NcenError(RuntimeError):
    """A filing did not contain what Form N-CEN requires."""


@dataclass(frozen=True)
class NcenFilingRef:
    """One registrant-level N-CEN filing. A registrant files several a year."""

    cik: int
    accession: str
    filing_date: str

    @property
    def document_url(self) -> str:
        return _DOCUMENT_URL.format(cik=self.cik, plain=self.accession.replace("-", ""))


@dataclass(frozen=True)
class NcenSeriesRecord:
    """The cost items Form N-CEN files for one series in one fiscal year."""

    series_id: str
    fund_name: str
    tickers: tuple[str, ...]
    class_count: int
    fiscal_year_end: str
    accession: str
    monthly_average_net_assets: float | None
    #: Item C.3.b.ii, percent per year. ``None`` when the fund is not an index fund.
    tracking_difference_before_expenses: float | None
    tracking_difference_after_expenses: float | None
    lends_securities: bool
    #: Item C.6.f and C.6.g, US dollars.
    average_securities_on_loan: float | None
    net_securities_lending_income: float | None
    lending_agent: str | None
    lending_agent_affiliated: bool | None
    borrower_default_indemnified: bool | None
    #: Item C.8. ``expense_limitation_in_place`` can be true with nothing waived.
    expense_limitation_in_place: bool
    expenses_waived: bool
    waived_fees_recoupable: bool
    waived_expenses_recouped: bool

    @property
    def securities_lending_bp(self) -> float | None:
        """Net lending income over monthly average net assets, in basis points a year."""
        return securities_lending_bp(
            self.net_securities_lending_income, self.monthly_average_net_assets
        )

    @property
    def implied_expense_ratio(self) -> float | None:
        """``before - after``, which for a **single-class** ETF is its expense ratio.

        For a multi-class series it is not, because Item C.3.b does not say which class
        the fund answered for. Read it as a consistency check rather than a fee.
        """
        if (
            self.tracking_difference_before_expenses is None
            or self.tracking_difference_after_expenses is None
        ):
            return None
        return (
            self.tracking_difference_before_expenses - self.tracking_difference_after_expenses
        )


def securities_lending_bp(
    net_income: float | None, average_net_assets: float | None
) -> float | None:
    """Net lending income as basis points of average net assets, or ``None``.

    Returns ``None`` rather than zero when either input is missing, because a fund that
    filed nothing and a fund that earned nothing are different facts and collapsing them
    would silently flatter whichever is which.
    """
    if net_income is None or average_net_assets is None or average_net_assets <= 0.0:
        return None
    return net_income / average_net_assets * 1e4


def tracking_difference_is_internally_consistent(record: NcenSeriesRecord) -> bool:
    """Whether the two filed tracking differences can both be true of a fund with a fee.

    A fund's return after its own fees is lower than before them, so the after-expense
    difference must be strictly *below* the before-expense one. Equality means the filer
    reported one number twice; a positive gap means the two were transposed. Both occur
    in the filings and neither is a property of the fund.
    """
    gap = record.implied_expense_ratio
    return gap is not None and gap > 0.0


def ncen_filing_index(
    cache: RawCache, cik: int, *, force: bool = False
) -> tuple[NcenFilingRef, ...]:
    """Every N-CEN the registrant has filed, newest first.

    EDGAR splits a prolific filer's history across paged JSON, and a registrant that
    files an N-PORT a month per series exhausts the first page in a couple of years, so
    the older pages are followed rather than assumed empty.
    """
    entry = cache.fetch_via_curl(
        _SUBMISSIONS_URL.format(cik=cik), user_agent=EDGAR_USER_AGENT, force=force
    )
    document = json.loads(cache.read(entry))
    pages = [document["filings"]["recent"]]
    for extra in document["filings"].get("files", []):
        throttle()
        page = cache.fetch_via_curl(
            f"https://data.sec.gov/submissions/{extra['name']}",
            user_agent=EDGAR_USER_AGENT,
            force=force,
        )
        pages.append(json.loads(cache.read(page)))

    refs: dict[str, NcenFilingRef] = {}
    for page in pages:
        for form, filing_date, accession in zip(
            page["form"], page["filingDate"], page["accessionNumber"], strict=True
        ):
            if form != "N-CEN":
                continue
            if not _ACCESSION.match(accession):
                raise NcenError(f"CIK {cik}: unexpected accession format {accession!r}")
            refs[accession] = NcenFilingRef(
                cik=cik, accession=accession, filing_date=filing_date
            )
    return tuple(sorted(refs.values(), key=lambda ref: ref.filing_date, reverse=True))


def fetch_ncen(
    cache: RawCache, ref: NcenFilingRef, *, force: bool = False
) -> tuple[tuple[NcenSeriesRecord, ...], CacheEntry]:
    """Download (or read from cache) and parse one N-CEN filing."""
    entry = cache.fetch_via_curl(
        ref.document_url, user_agent=EDGAR_USER_AGENT, force=force
    )
    return parse_ncen(cache.read(entry), accession=ref.accession), entry


def parse_ncen(payload: bytes, *, accession: str) -> tuple[NcenSeriesRecord, ...]:
    """Parse the bytes of one ``primary_doc.xml`` into one record per series.

    Split from :func:`fetch_ncen` so the parser runs offline against a frozen fixture
    rather than only against whatever EDGAR serves today.
    """
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise NcenError(f"{accession}: primary document is not XML: {exc}") from exc

    general = root.find(f".//{_NS}generalInfo")
    if general is None:
        raise NcenError(f"{accession}: no generalInfo block; this is not a Form N-CEN")
    fiscal_year_end = general.get("reportEndingPeriod")
    if not fiscal_year_end:
        raise NcenError(f"{accession}: generalInfo carries no reportEndingPeriod")

    records = [
        _series_record(block, accession=accession, fiscal_year_end=fiscal_year_end)
        for block in root.iter(f"{_NS}managementInvestmentQuestion")
    ]
    return tuple(records)


def _series_record(
    block: ElementTree.Element, *, accession: str, fiscal_year_end: str
) -> NcenSeriesRecord:
    series_id = _text(block, "mgmtInvSeriesId")
    if series_id is None:
        raise NcenError(f"{accession}: a series block carries no mgmtInvSeriesId")
    index_info = block.find(f"{_NS}fundTypes/{_NS}indexFundInfo")
    lending = block.find(f"{_NS}securityLendings/{_NS}securityLending")
    shares = block.findall(f"{_NS}sharesOutstandings/{_NS}sharesOutstanding")
    return NcenSeriesRecord(
        series_id=series_id,
        fund_name=_text(block, "mgmtInvFundName") or "",
        tickers=tuple(
            ticker
            for share in shares
            if (ticker := share.get("sharesOutstandingTickerSymbol"))
        ),
        class_count=len(shares),
        fiscal_year_end=fiscal_year_end,
        accession=accession,
        monthly_average_net_assets=_number(block, "mnthlyAvgNetAssets"),
        tracking_difference_before_expenses=_number(
            index_info, "indexFundReturnDiffBeforeExpense"
        ),
        tracking_difference_after_expenses=_number(
            index_info, "indexFundReturnDiffAfterExpense"
        ),
        lends_securities=_flag(block, "isFundSecuritiesLending") is True,
        average_securities_on_loan=_number(block, "avgPortfolioSecuritiesValue"),
        net_securities_lending_income=_number(block, "netIncomeSecuritiesLending"),
        lending_agent=_text(lending, "securitiesAgentName"),
        lending_agent_affiliated=_flag(lending, "isSecuritiesAgentAffiliated"),
        borrower_default_indemnified=_flag(lending, "isSecurityAgentIdemnity"),
        expense_limitation_in_place=_flag(block, "isExpenseLimitationInPlace") is True,
        expenses_waived=_flag(block, "isExpenseReducedOrWaived") is True,
        waived_fees_recoupable=_flag(block, "isFeesWaivedRecoupable") is True,
        waived_expenses_recouped=_flag(block, "isExpenseWaivedRecoupable") is True,
    )


def _text(parent: ElementTree.Element | None, tag: str) -> str | None:
    if parent is None:
        return None
    found = parent.find(f"{_NS}{tag}")
    if found is None or found.text is None:
        return None
    stripped = found.text.strip()
    return stripped or None


def _number(parent: ElementTree.Element | None, tag: str) -> float | None:
    """A filed numeric field, or ``None`` — including for the literal ``N/A``.

    Filers write ``N/A`` into numeric fields the form allows them to skip. Treating that
    as zero would turn "did not lend" into "lent and earned nothing".
    """
    raw = _text(parent, tag)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _flag(parent: ElementTree.Element | None, tag: str) -> bool | None:
    raw = _text(parent, tag)
    if raw is None:
        return None
    upper = raw.upper()
    if upper in {"Y", "YES", "TRUE"}:
        return True
    if upper in {"N", "NO", "FALSE"}:
        return False
    return None


def latest_by_series(
    records: Sequence[NcenSeriesRecord],
) -> dict[str, NcenSeriesRecord]:
    """The most recent fiscal year filed for each series.

    Registrants file several N-CENs a year, one per fiscal-year group, so "the latest
    filing" is not the latest year for every series in the trust.
    """
    newest: dict[str, NcenSeriesRecord] = {}
    for record in records:
        held = newest.get(record.series_id)
        if held is None or record.fiscal_year_end > held.fiscal_year_end:
            newest[record.series_id] = record
    return newest
