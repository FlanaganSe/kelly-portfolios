"""Experiment 002, step one: the product universe, built before any return is read.

The order matters more than the code
------------------------------------
``docs/the-plan.md`` puts "build the product-universe manifest for Experiment 002"
*before* "execute the exposure audit" for one reason: a universe chosen after
seeing performance is not a universe, it is a result. So this module runs first,
writes its output to a committed file, and the experiment then reads that file
and refuses to proceed if its digest has moved. Nothing here can read a return:
the frame it screens carries fund names, net assets and filing dates, and the
return table of the data set is never opened.

The frame is a census, not a list
---------------------------------
Every screened fund comes from the SEC's Form N-PORT structured data set for
**2019Q4** — every US registered fund that filed for the quarter ending September
2019. Two consequences follow, and both are the point.

* Nothing is curated. A vendor's "smart beta" list is a list of products the
  vendor still wants to talk about; a regulatory census is every fund that
  existed.
* The frame is taken at the **start** of the observation window. Screening the
  2025Q4 census instead would silently drop every fund that died in between,
  which is the exact failure this experiment is supposed to avoid. Screening
  2019Q4 and following each fund forward turns attrition into a measurement.

What it still cannot see: any fund that closed before 2019Q4, because public
N-PORT filings do not exist before then. The attrition reported here is a **lower
bound**, and it is labelled as one everywhere it appears.

Facts the filings do not carry
------------------------------
Expense ratio, inception date and index methodology are not in Form N-PORT. They
are read from each sponsor's own published page or prospectus and committed to
``data-manifests/exp_002/product_facts.json`` with a source URL and a date read,
per fund. That file is an input to the screen, not an output of it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.nport import FrameRow, load_frame
from portfolio_edge.data.table import ParsedTable

__all__ = [
    "COMPANY_TICKERS_MF_URL",
    "FOLLOW_UP_QUARTER",
    "FRAME_QUARTER",
    "NASDAQ_TRADED_URL",
    "UNIVERSE_SCHEMA_VERSION",
    "ProductFacts",
    "ScreenedFund",
    "Universe",
    "UniverseError",
    "build_universe",
    "load_product_facts",
    "load_universe",
    "screen_frame",
    "universe_path",
    "write_universe",
]

UNIVERSE_SCHEMA_VERSION: Final = "1"

FRAME_QUARTER: Final = "2019q4"
"""The census the screen is applied to: the first public N-PORT quarter."""

FOLLOW_UP_QUARTER: Final = "2025q4"
"""The census used ONLY to measure attrition. It never adds a fund."""

COMPANY_TICKERS_MF_URL: Final = "https://www.sec.gov/files/company_tickers_mf.json"
NASDAQ_TRADED_URL: Final = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"

#: The order criteria are applied in. A fund records the FIRST criterion it
#: failed, so the reason a fund is absent is deterministic rather than dependent
#: on evaluation order.
CRITERION_ORDER: Final = (
    "mandate_regex",
    "exclusion_regex",
    "exchange_traded",
    "minimum_net_assets",
    "maximum_expense_ratio",
    "inception_cutoff",
    "mandate_in_map",
)


class UniverseError(RuntimeError):
    """The universe could not be built from the declared inputs."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductFacts:
    """Per-fund facts read from the sponsor, with their provenance.

    Every field carries the URL it came from and the date it was read, because a
    fee or an index can change and a number without a date cannot be rechecked.
    """

    ticker: str
    net_expense_ratio_percent: float | None
    gross_expense_ratio_percent: float | None
    inception_date: str | None
    index_name: str
    index_provider: str
    stated_mandate: str
    source_url: str
    date_read: str

    def to_json(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "net_expense_ratio_percent": self.net_expense_ratio_percent,
            "gross_expense_ratio_percent": self.gross_expense_ratio_percent,
            "inception_date": self.inception_date,
            "index_name": self.index_name,
            "index_provider": self.index_provider,
            "stated_mandate": self.stated_mandate,
            "source_url": self.source_url,
            "date_read": self.date_read,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ScreenedFund:
    """One fund's complete screen record, whether it passed or failed.

    A failing fund is kept in full. The multiple-testing denominator is the whole
    screen, and a screen whose rejections are not written down cannot supply one.
    """

    ticker: str
    series_id: str
    class_id: str
    series_name: str
    security_name: str
    passed: bool
    failed_criterion: str | None
    failure_detail: str
    net_assets_frame: float | None
    net_assets_follow_up: float | None
    still_filing_at_follow_up: bool
    final_filing_flag_seen: bool
    exchange_listed_now: bool
    facts: ProductFacts | None
    intended_factor: str | None
    intended_sign: int

    def to_json(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "series_id": self.series_id,
            "class_id": self.class_id,
            "series_name": self.series_name,
            "security_name": self.security_name,
            "passed": self.passed,
            "failed_criterion": self.failed_criterion,
            "failure_detail": self.failure_detail,
            "net_assets_frame_usd": self.net_assets_frame,
            "net_assets_follow_up_usd": self.net_assets_follow_up,
            "still_filing_at_follow_up": self.still_filing_at_follow_up,
            "final_filing_flag_seen": self.final_filing_flag_seen,
            "exchange_listed_now": self.exchange_listed_now,
            "intended_factor": self.intended_factor,
            "intended_sign": self.intended_sign,
            "facts": None if self.facts is None else self.facts.to_json(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class Universe:
    """The committed screening outcome: every fund, and the attrition around it."""

    schema_version: str
    built_utc: str
    frame_quarter: str
    follow_up_quarter: str
    frame_series_count: int
    follow_up_series_count: int
    mandate_matches: int
    funds: tuple[ScreenedFund, ...]
    attrition: Mapping[str, object]
    inputs: Mapping[str, object]
    notes: tuple[str, ...]

    @property
    def passing(self) -> tuple[ScreenedFund, ...]:
        return tuple(fund for fund in self.funds if fund.passed)

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "built_utc": self.built_utc,
            "frame_quarter": self.frame_quarter,
            "follow_up_quarter": self.follow_up_quarter,
            "frame_series_count": self.frame_series_count,
            "follow_up_series_count": self.follow_up_series_count,
            "mandate_matches": self.mandate_matches,
            "attrition": dict(self.attrition),
            "inputs": dict(self.inputs),
            "notes": list(self.notes),
            "funds": [fund.to_json() for fund in self.funds],
        }


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def universe_path() -> Path:
    """Where the committed universe lives.

    Under ``data-manifests/exp_002/`` rather than beside the dataset manifests,
    because it is not one: a dataset manifest describes downloaded bytes, and this
    describes a screening decision. Keeping them in separate directories means the
    manifest schema test can hold every file it does cover to the full schema.
    """
    return workspace_root() / "data-manifests" / "exp_002" / "product_universe.json"


def product_facts_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_002" / "product_facts.json"


def load_product_facts(path: Path | None = None) -> dict[str, ProductFacts]:
    """Read the committed per-fund sponsor facts."""
    location = path or product_facts_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. The screen needs an expense ratio and an "
            "inception date per fund, and neither is in Form N-PORT; they are "
            "read from the sponsor and committed with a URL and a date."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds = payload.get("funds", {})
    if not isinstance(funds, dict):
        raise UniverseError(f"{location}: 'funds' must be an object")
    out: dict[str, ProductFacts] = {}
    for ticker, record in funds.items():
        out[str(ticker)] = ProductFacts(
            ticker=str(ticker),
            net_expense_ratio_percent=_optional_number(record.get("net_expense_ratio_percent")),
            gross_expense_ratio_percent=_optional_number(
                record.get("gross_expense_ratio_percent")
            ),
            inception_date=_optional_text(record.get("inception_date")),
            index_name=str(record.get("index_name", "")),
            index_provider=str(record.get("index_provider", "")),
            stated_mandate=str(record.get("stated_mandate", "")),
            source_url=str(record.get("source_url", "")),
            date_read=str(record.get("date_read", "")),
        )
    return out


def _optional_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_class_tickers(cache: RawCache) -> dict[str, list[tuple[str, str]]]:
    """Map each fund series to its ``(class id, ticker)`` pairs, from EDGAR."""
    entry = cache.require(COMPANY_TICKERS_MF_URL)
    payload = json.loads(cache.read(entry).decode("utf-8"))
    rows = payload.get("data", [])
    mapping: dict[str, list[tuple[str, str]]] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) < 4:
            continue
        mapping.setdefault(str(row[1]), []).append((str(row[2]), str(row[3])))
    return mapping


def _load_exchange_flags(cache: RawCache) -> dict[str, tuple[bool, str]]:
    """Map each listed symbol to ``(is_etf, security name)`` from the symbol directory.

    The consolidated symbol directory is an exchange record, so ``ETF=Y`` is a
    listing fact rather than a sponsor's marketing claim. It is also *current*
    only: a symbol delisted before today is simply absent, which is why absence
    is recorded as a fact about the fund rather than treated as a data error.
    """
    entry = cache.require(NASDAQ_TRADED_URL)
    text = cache.read(entry).decode("utf-8", errors="replace")
    flags: dict[str, tuple[bool, str]] = {}
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) < 7 or parts[1] == "Symbol" or parts[0] == "File Creation Time":
            continue
        flags[parts[1]] = (parts[5] == "Y", parts[2])
    return flags


def screen_frame(
    *,
    frame: Mapping[str, FrameRow],
    follow_up: Mapping[str, FrameRow],
    class_tickers: Mapping[str, Sequence[tuple[str, str]]],
    exchange_flags: Mapping[str, tuple[bool, str]],
    facts: Mapping[str, ProductFacts],
    mandate_pattern: str,
    exclusion_pattern: str,
    minimum_net_assets: float,
    maximum_expense_ratio: float,
    inception_on_or_before: str,
    intended_factor_map: Mapping[str, tuple[str, int]],
) -> tuple[tuple[ScreenedFund, ...], int]:
    """Apply the predeclared criteria in their fixed order to the whole census.

    Returns every series whose name matches the mandate pattern, passing or not,
    together with the count of mandate matches. A series that never matched the
    mandate pattern is not a factor product and is not a rejection either, so it
    is counted but not enumerated.
    """
    mandate = re.compile(mandate_pattern, re.IGNORECASE)
    exclusion = re.compile(exclusion_pattern, re.IGNORECASE)

    screened: list[ScreenedFund] = []
    matches = 0
    for series_id, row in frame.items():
        if not mandate.search(row.series_name):
            continue
        matches += 1
        classes = list(class_tickers.get(series_id, ()))
        etf_classes = [
            (class_id, ticker)
            for class_id, ticker in classes
            if exchange_flags.get(ticker, (False, ""))[0]
        ]
        follow_row = follow_up.get(series_id)
        chosen_class, ticker = (etf_classes or classes or [("", "")])[0]
        security_name = exchange_flags.get(ticker, (False, ""))[1]
        fund_facts = facts.get(ticker)

        failed: str | None = None
        detail = ""
        if exclusion.search(row.series_name):
            failed, detail = "exclusion_regex", (
                f"series name matches the exclusion pattern: {row.series_name!r}"
            )
        elif not classes:
            failed, detail = "exchange_traded", "EDGAR lists no ticker for this series"
        elif not etf_classes:
            failed, detail = "exchange_traded", (
                "no share class of this series carries an ETF=Y flag in the current "
                f"consolidated symbol directory (classes: {[t for _, t in classes]})"
            )
        elif row.net_assets is None or row.net_assets < minimum_net_assets:
            failed, detail = "minimum_net_assets", (
                f"net assets {row.net_assets!r} USD at {row.report_date} is below "
                f"{minimum_net_assets:,.0f}"
            )
        elif fund_facts is None or fund_facts.net_expense_ratio_percent is None:
            failed, detail = "maximum_expense_ratio", (
                f"no net expense ratio was verified from a sponsor source for {ticker}"
            )
        elif fund_facts.net_expense_ratio_percent > maximum_expense_ratio:
            failed, detail = "maximum_expense_ratio", (
                f"net expense ratio {fund_facts.net_expense_ratio_percent}% exceeds "
                f"{maximum_expense_ratio}%"
            )
        elif fund_facts.inception_date is None:
            failed, detail = "inception_cutoff", (
                f"no inception date was verified from a sponsor source for {ticker}"
            )
        elif fund_facts.inception_date > inception_on_or_before:
            failed, detail = "inception_cutoff", (
                f"inception {fund_facts.inception_date} is after {inception_on_or_before}"
            )

        factor, sign = (None, 0)
        if fund_facts is not None:
            factor, sign = intended_factor_map.get(fund_facts.stated_mandate, (None, 0))
        if failed is None and factor is None:
            # Distinct from ``mandate_regex``: the fund's NAME matched, so it is a
            # factor product; what failed is that its stated mandate has no entry
            # in the predeclared map. That is how a fund which changed its
            # objective inside the window is kept out -- recorded, not dropped.
            failed, detail = "mandate_in_map", (
                f"stated mandate {fund_facts.stated_mandate!r} is not in the "
                "predeclared intended-factor map, so there is no declared factor "
                "to grade this fund against"
                if fund_facts is not None
                else "no sponsor facts were recorded for this ticker"
            )

        screened.append(
            ScreenedFund(
                ticker=ticker,
                series_id=series_id,
                class_id=chosen_class,
                series_name=row.series_name,
                security_name=security_name,
                passed=failed is None,
                failed_criterion=failed,
                failure_detail=detail,
                net_assets_frame=row.net_assets,
                net_assets_follow_up=None if follow_row is None else follow_row.net_assets,
                still_filing_at_follow_up=follow_row is not None,
                final_filing_flag_seen=row.is_last_filing
                or (follow_row is not None and follow_row.is_last_filing),
                exchange_listed_now=ticker in exchange_flags,
                facts=fund_facts,
                intended_factor=factor,
                intended_sign=sign,
            )
        )

    screened.sort(key=lambda fund: (-(fund.net_assets_frame or 0.0), fund.ticker))
    return tuple(screened), matches


def resolve_ticker(cache: RawCache, ticker: str) -> tuple[str, str, str]:
    """Map an exchange ticker to its ``(series id, class id, series name)``.

    Needed for the comparators, which are deliberately NOT selected by the screen:
    a cheap total-market fund has no factor mandate, so it never matches the
    mandate pattern and could not arrive through the universe. Resolving it
    separately keeps the benchmark outside the thing being screened.
    """
    entry = cache.require(COMPANY_TICKERS_MF_URL)
    payload = json.loads(cache.read(entry).decode("utf-8"))
    for row in payload.get("data", []):
        if isinstance(row, list) and len(row) >= 4 and str(row[3]) == ticker:
            series_id, class_id = str(row[1]), str(row[2])
            frame, _ = load_frame(cache, FRAME_QUARTER)
            row_in_frame = frame.get(series_id)
            name = "" if row_in_frame is None else row_in_frame.series_name
            return series_id, class_id, name
    raise UniverseError(
        f"{ticker} is not in EDGAR's fund ticker map, so its filings cannot be found"
    )


def _attrition(
    frame: Mapping[str, FrameRow],
    follow_up: Mapping[str, FrameRow],
    mandate_pattern: str,
    exclusion_pattern: str,
) -> dict[str, object]:
    """How much of the 2019 factor shelf is gone, and what a today-frame would add."""
    mandate = re.compile(mandate_pattern, re.IGNORECASE)
    exclusion = re.compile(exclusion_pattern, re.IGNORECASE)

    def qualifying(rows: Mapping[str, FrameRow]) -> set[str]:
        return {
            series_id
            for series_id, row in rows.items()
            if mandate.search(row.series_name) and not exclusion.search(row.series_name)
        }

    start = qualifying(frame)
    end = qualifying(follow_up)
    gone = start - end
    born = end - start
    gone_assets = sum(frame[series_id].net_assets or 0.0 for series_id in gone)
    return {
        "mandate_qualifying_series_in_frame": len(start),
        "mandate_qualifying_series_in_follow_up": len(end),
        "series_present_in_frame_and_absent_at_follow_up": len(gone),
        "attrition_rate": (len(gone) / len(start)) if start else 0.0,
        "net_assets_of_disappeared_series_usd": gone_assets,
        "series_absent_from_frame_and_present_at_follow_up": len(born),
        "largest_disappeared_series": [
            {
                "series_name": frame[series_id].series_name,
                "net_assets_usd": frame[series_id].net_assets,
                "last_report_date": frame[series_id].report_date,
            }
            for series_id in sorted(
                gone, key=lambda sid: -(frame[sid].net_assets or 0.0)
            )[:15]
        ],
        "interpretation": (
            "LOWER BOUND on survivorship contamination. A series absent at the "
            "follow-up quarter liquidated, merged, or stopped filing; a series "
            "absent from the frame and present later launched during the window. "
            "A universe assembled from today's listings would contain the second "
            "group and none of the first. Funds that closed before 2019Q4 are "
            "invisible to both censuses, so the true rate is higher than this."
        ),
    }


def build_universe(
    *,
    cache: RawCache,
    mandate_pattern: str,
    exclusion_pattern: str,
    minimum_net_assets: float,
    maximum_expense_ratio: float,
    inception_on_or_before: str,
    intended_factor_map: Mapping[str, tuple[str, int]],
    facts: Mapping[str, ProductFacts] | None = None,
) -> Universe:
    """Screen the census and assemble the committed universe record."""
    frame, frame_entry = load_frame(cache, FRAME_QUARTER)
    follow_up, follow_entry = load_frame(cache, FOLLOW_UP_QUARTER)
    class_tickers = _load_class_tickers(cache)
    exchange_flags = _load_exchange_flags(cache)
    product_facts = dict(facts) if facts is not None else load_product_facts()

    screened, matches = screen_frame(
        frame=frame,
        follow_up=follow_up,
        class_tickers=class_tickers,
        exchange_flags=exchange_flags,
        facts=product_facts,
        mandate_pattern=mandate_pattern,
        exclusion_pattern=exclusion_pattern,
        minimum_net_assets=minimum_net_assets,
        maximum_expense_ratio=maximum_expense_ratio,
        inception_on_or_before=inception_on_or_before,
        intended_factor_map=intended_factor_map,
    )

    return Universe(
        schema_version=UNIVERSE_SCHEMA_VERSION,
        built_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        frame_quarter=FRAME_QUARTER,
        follow_up_quarter=FOLLOW_UP_QUARTER,
        frame_series_count=len(frame),
        follow_up_series_count=len(follow_up),
        mandate_matches=matches,
        funds=screened,
        attrition=_attrition(frame, follow_up, mandate_pattern, exclusion_pattern),
        inputs={
            "frame_data_set": {
                "url": frame_entry.url,
                "sha256_raw": frame_entry.sha256,
                "retrieved_utc": frame_entry.retrieved_utc,
            },
            "follow_up_data_set": {
                "url": follow_entry.url,
                "sha256_raw": follow_entry.sha256,
                "retrieved_utc": follow_entry.retrieved_utc,
            },
            "class_tickers": {
                "url": COMPANY_TICKERS_MF_URL,
                "sha256_raw": cache.require(COMPANY_TICKERS_MF_URL).sha256,
            },
            "exchange_flags": {
                "url": NASDAQ_TRADED_URL,
                "sha256_raw": cache.require(NASDAQ_TRADED_URL).sha256,
            },
            "criteria_order": list(CRITERION_ORDER),
            "mandate_pattern": mandate_pattern,
            "exclusion_pattern": exclusion_pattern,
            "minimum_net_assets_usd": minimum_net_assets,
            "maximum_net_expense_ratio_percent": maximum_expense_ratio,
            "inception_on_or_before": inception_on_or_before,
        },
        notes=(
            "Built BEFORE any fund return was downloaded. The return table of the "
            "data set was never opened while screening.",
            "The frame is the census at the START of the observation window. "
            "Screening today's listings would select on survival.",
            "Every mandate-matching series is listed, passing or failing, because "
            "the multiple-testing denominator is the whole screen.",
            "Expense ratio, inception date and index come from the sponsor, not "
            "from Form N-PORT, and each carries its own URL and date read.",
        ),
    )


def write_universe(universe: Universe, path: Path | None = None) -> Path:
    """Write the universe as committed JSON and return the path."""
    location = path or universe_path()
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(
        json.dumps(universe.to_json(), indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return location


def load_universe(path: Path | None = None) -> Universe:
    """Read the committed universe. The experiment never rebuilds it."""
    location = path or universe_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. Build it with "
            "`python -m portfolio_edge.experiments.exp_002_fund_exposure --build-universe` "
            "BEFORE running the audit; the universe must be fixed before returns "
            "are downloaded."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds: list[ScreenedFund] = []
    for record in payload.get("funds", []):
        raw_facts = record.get("facts")
        facts = (
            None
            if raw_facts is None
            else ProductFacts(
                ticker=str(raw_facts["ticker"]),
                net_expense_ratio_percent=_optional_number(
                    raw_facts.get("net_expense_ratio_percent")
                ),
                gross_expense_ratio_percent=_optional_number(
                    raw_facts.get("gross_expense_ratio_percent")
                ),
                inception_date=_optional_text(raw_facts.get("inception_date")),
                index_name=str(raw_facts.get("index_name", "")),
                index_provider=str(raw_facts.get("index_provider", "")),
                stated_mandate=str(raw_facts.get("stated_mandate", "")),
                source_url=str(raw_facts.get("source_url", "")),
                date_read=str(raw_facts.get("date_read", "")),
            )
        )
        funds.append(
            ScreenedFund(
                ticker=str(record["ticker"]),
                series_id=str(record["series_id"]),
                class_id=str(record["class_id"]),
                series_name=str(record["series_name"]),
                security_name=str(record.get("security_name", "")),
                passed=bool(record["passed"]),
                failed_criterion=_optional_text(record.get("failed_criterion")),
                failure_detail=str(record.get("failure_detail", "")),
                net_assets_frame=_optional_number(record.get("net_assets_frame_usd")),
                net_assets_follow_up=_optional_number(record.get("net_assets_follow_up_usd")),
                still_filing_at_follow_up=bool(record.get("still_filing_at_follow_up", False)),
                final_filing_flag_seen=bool(record.get("final_filing_flag_seen", False)),
                exchange_listed_now=bool(record.get("exchange_listed_now", False)),
                facts=facts,
                intended_factor=_optional_text(record.get("intended_factor")),
                intended_sign=int(record.get("intended_sign", 0) or 0),
            )
        )
    return Universe(
        schema_version=str(payload.get("schema_version", UNIVERSE_SCHEMA_VERSION)),
        built_utc=str(payload.get("built_utc", "")),
        frame_quarter=str(payload.get("frame_quarter", FRAME_QUARTER)),
        follow_up_quarter=str(payload.get("follow_up_quarter", FOLLOW_UP_QUARTER)),
        frame_series_count=int(payload.get("frame_series_count", 0)),
        follow_up_series_count=int(payload.get("follow_up_series_count", 0)),
        mandate_matches=int(payload.get("mandate_matches", 0)),
        funds=tuple(funds),
        attrition=payload.get("attrition", {}),
        inputs=payload.get("inputs", {}),
        notes=tuple(str(item) for item in payload.get("notes", [])),
    )


def frame_manifest(cache: RawCache, quarter: str) -> DatasetManifest:
    """A manifest for one quarterly N-PORT data set, describing only its frame use.

    The derived table hashed here is the *census* — series id, name and net
    assets — because that is the only part of the archive this experiment reads
    while screening. Hashing the whole ZIP's contents would claim a dependence on
    holdings and returns that the screen does not have.
    """
    frame, entry = load_frame(cache, quarter)
    ordered = sorted(frame.values(), key=lambda row: row.series_id)
    table = ParsedTable(
        table_id=f"nport_frame_{quarter}",
        banner=(
            f"Census of NPORT-P fund series in the SEC N-PORT data set for {quarter}: "
            "series identifier, official name and net assets. No return is read."
        ),
        columns=("net_assets_usd",),
        periods=tuple(f"{row.series_id}|{row.series_name}" for row in ordered),
        values=tuple((row.net_assets,) for row in ordered),
        frequency="unknown",
        source_units="usd",
        units="usd",
        unit_transform="identity",
        warnings=(
            "This table is a UNIVERSE FRAME, not a time series. Its periods are "
            "series identifiers so that the canonical form pins exactly which "
            "funds the screen saw.",
            "NPORT-P/A amendments are excluded; an amendment restates a filing "
            "already counted and would double a fund in the census.",
        ),
    )
    return manifest_from_table(
        dataset_id=f"sec_nport_data_set_{quarter}",
        entry=entry,
        table=table,
        parser_version=f"exp002-universe/{UNIVERSE_SCHEMA_VERSION}",
        availability_policy=(
            "Public N-PORT reporting begins with periods ending 2019-09-30; the "
            "first filings reached EDGAR on 2019-10-22. Nothing in this frame was "
            "public before then, and no earlier census exists."
        ),
        revision_policy=(
            "The quarterly data sets fold amendments into the same file rather "
            "than preserving both versions, so this frame is 'as most recently "
            "filed' and is not point-in-time: a fund's reported net assets for "
            "this quarter can be restated by a later NPORT-P/A and this file "
            "would show the restated figure. The raw EDGAR filings retain the "
            "full revision history."
        ),
        license_or_terms_url="https://www.sec.gov/os/webmaster-faq#developers",
        extra_warnings=(
            "SEC disclaimer: the data are derived from information provided by "
            "individual registrants and their accuracy is not guaranteed.",
            "Used ONLY as a screening frame. No return is read from this archive.",
        ),
    )
