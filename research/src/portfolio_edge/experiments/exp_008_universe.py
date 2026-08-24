"""Experiment 008, step one: the managed-futures product universe.

Built and committed BEFORE any fund return is downloaded, for the same reason as
:mod:`portfolio_edge.experiments.exp_002_universe`: a universe chosen after seeing
performance is not a universe, it is a result. This module reads only series
names, net assets and filing dates. The return tables of the data sets are never
opened.

Why the frame is a union and Experiment 002's was not
-----------------------------------------------------
Experiment 002 screened the **2019Q4** census alone, took its frame at the start
of its window, and followed every fund forward, which turns attrition into a
measurement. That is the right design and it is unavailable here. The products
this experiment exists to audit did not exist in 2019: DBMF's prospectus inception
is 2019-05-07, KMLM's 2020-12-01 and CTA's 2022-03-07. A 2019Q4-only frame would
exclude, by construction, every product the question is about.

So the frame is the **union** of the first and the most recent public census. A
series is screened if it appears in either. That admits funds launched inside the
window *and* retains funds present in 2019Q4 and absent in 2025Q4, which is the
least survivorship-selecting frame this source can support. It is not
survivorship-free, and the gap is stated rather than papered over: public N-PORT
filings begin in 2019, so a managed-futures fund that closed before 2019Q4 is
invisible to both censuses and the measured attrition is a lower bound.

The asset floor is applied to the **maximum** of a series' two observed net-asset
figures. Applying it to the latest census would select on terminal size as well as
on survival; applying it to the earliest would exclude every fund that launched
small and grew, which is every fund on this shelf.

What the filings do not carry
-----------------------------
Expense ratio, inception date, index and stated mandate are not in Form N-PORT.
They are read from each fund's own **SEC-filed summary prospectus** — a sponsor
document with an accession number and a filing date, which is a stronger record
than a sponsor web page — and committed to
``data-manifests/exp_008/product_facts.json`` with the URL and the date read. The
same file carries each fund's prospectus after-tax return table, because managed
futures are notoriously tax-inefficient and Form N-PORT cannot show it.
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
from portfolio_edge.data.manifest import DatasetManifest
from portfolio_edge.data.nport import FrameRow, load_frame
from portfolio_edge.experiments.exp_002_universe import (
    ProductFacts,
    UniverseError,
    _load_class_tickers,
    _load_exchange_flags,
    frame_manifest,
    workspace_root,
)

__all__ = [
    "CRITERION_ORDER",
    "FOLLOW_UP_QUARTER",
    "FRAME_QUARTER",
    "UNIVERSE_SCHEMA_VERSION",
    "AfterTaxRow",
    "ManagedFuturesUniverse",
    "ScreenedProduct",
    "build_universe",
    "load_product_facts",
    "load_universe",
    "product_facts_path",
    "screen_union_frame",
    "universe_manifests",
    "universe_path",
    "write_universe",
]

UNIVERSE_SCHEMA_VERSION: Final = "1"

FRAME_QUARTER: Final = "2019q4"
"""First limb of the union frame: the first public N-PORT quarter."""

FOLLOW_UP_QUARTER: Final = "2025q4"
"""Second limb of the union frame, and the quarter attrition is measured against."""

#: Applied in this fixed order; a fund records the FIRST criterion it failed, so
#: the reason a fund is absent is deterministic and the funnel adds up. The order
#: puts the asset floor before the expense ratio deliberately: a fund below the
#: floor is never looked up for a fee, so a gathering gap cannot masquerade as a
#: screen decision. Experiment 002 had to rebuild its universe mid-flight for
#: exactly that defect.
CRITERION_ORDER: Final = (
    "mandate_regex",
    "exclusion_regex",
    "exchange_traded",
    "minimum_net_assets",
    "maximum_expense_ratio",
    "inception_cutoff",
    "mandate_in_map",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class AfterTaxRow:
    """One row of a prospectus's standardised average-annual-total-return table.

    The SEC's after-tax methodology assumes the **highest individual federal
    marginal rates** and no state or local tax, and it is computed by the fund, so
    it is comparable across funds and is not this repository's estimate. It is the
    only tax observable on this shelf: Form N-PORT reports one total return and no
    distribution split at all.
    """

    period: str
    before_tax_percent: float
    after_tax_on_distributions_percent: float
    after_tax_on_distributions_and_sale_percent: float

    @property
    def distribution_tax_drag_percent(self) -> float:
        """Before-tax less after-tax-on-distributions, in percentage points a year.

        Positive means tax on distributions reduced the shareholder's return. It
        can be negative when the fund distributed a loss-driven return.
        """
        return self.before_tax_percent - self.after_tax_on_distributions_percent

    def to_json(self) -> dict[str, str | float]:
        return {
            "period": self.period,
            "before_tax_percent": self.before_tax_percent,
            "after_tax_on_distributions_percent": self.after_tax_on_distributions_percent,
            "after_tax_on_distributions_and_sale_percent": (
                self.after_tax_on_distributions_and_sale_percent
            ),
            "distribution_tax_drag_percent": self.distribution_tax_drag_percent,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductTaxFacts:
    """A fund's prospectus after-tax table, with the date it is stated as of."""

    ticker: str
    as_of: str
    rows: tuple[AfterTaxRow, ...]
    methodology: str
    source_url: str

    def row(self, period: str) -> AfterTaxRow | None:
        for item in self.rows:
            if item.period == period:
                return item
        return None

    def to_json(self) -> dict[str, str | list[dict[str, str | float]]]:
        return {
            "ticker": self.ticker,
            "as_of": self.as_of,
            "methodology": self.methodology,
            "source_url": self.source_url,
            "rows": [row.to_json() for row in self.rows],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ScreenedProduct:
    """One series' complete screen record, whether it passed or failed.

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
    """Net assets in the 2019Q4 census, or ``None`` if the series is absent from it."""
    net_assets_follow_up: float | None
    net_assets_maximum: float | None
    """The larger of the two, which is what the asset floor is applied to."""
    in_frame_quarter: bool
    in_follow_up_quarter: bool
    final_filing_flag_seen: bool
    exchange_listed_now: bool
    facts: ProductFacts | None
    intended_target: str | None
    """The exposure benchmark this fund is graded against, from the frozen map."""

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
            "net_assets_maximum_usd": self.net_assets_maximum,
            "in_frame_quarter": self.in_frame_quarter,
            "in_follow_up_quarter": self.in_follow_up_quarter,
            "final_filing_flag_seen": self.final_filing_flag_seen,
            "exchange_listed_now": self.exchange_listed_now,
            "intended_target": self.intended_target,
            "facts": None if self.facts is None else self.facts.to_json(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedFuturesUniverse:
    """The committed screening outcome and the attrition around it."""

    schema_version: str
    built_utc: str
    frame_quarter: str
    follow_up_quarter: str
    frame_series_count: int
    follow_up_series_count: int
    union_series_count: int
    mandate_matches: int
    products: tuple[ScreenedProduct, ...]
    attrition: Mapping[str, object]
    inputs: Mapping[str, object]
    notes: tuple[str, ...]

    @property
    def passing(self) -> tuple[ScreenedProduct, ...]:
        return tuple(item for item in self.products if item.passed)

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "built_utc": self.built_utc,
            "frame_quarter": self.frame_quarter,
            "follow_up_quarter": self.follow_up_quarter,
            "frame_series_count": self.frame_series_count,
            "follow_up_series_count": self.follow_up_series_count,
            "union_series_count": self.union_series_count,
            "mandate_matches": self.mandate_matches,
            "attrition": dict(self.attrition),
            "inputs": dict(self.inputs),
            "notes": list(self.notes),
            "products": [item.to_json() for item in self.products],
        }


def universe_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_008" / "product_universe.json"


def product_facts_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_008" / "product_facts.json"


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


def load_product_facts(
    path: Path | None = None,
) -> tuple[dict[str, ProductFacts], dict[str, ProductTaxFacts]]:
    """Read the committed per-fund sponsor facts and their after-tax tables.

    Returns two maps rather than one enriched type so that
    :class:`~portfolio_edge.experiments.exp_002_universe.ProductFacts` stays exactly
    what Experiment 002 froze. Extending a frozen dataclass to carry a field a later
    experiment wanted would silently change what "the committed product facts"
    means for the earlier one.
    """
    location = path or product_facts_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. The screen needs an expense ratio and an "
            "inception date per fund, and neither is in Form N-PORT; both are read "
            "from the fund's own SEC-filed summary prospectus and committed with "
            "the accession URL and the date read."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds = payload.get("funds", {})
    if not isinstance(funds, dict):
        raise UniverseError(f"{location}: 'funds' must be an object")
    facts: dict[str, ProductFacts] = {}
    taxes: dict[str, ProductTaxFacts] = {}
    for ticker, record in funds.items():
        key = str(ticker)
        facts[key] = ProductFacts(
            ticker=key,
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
        block = record.get("after_tax_returns")
        if isinstance(block, dict) and block.get("rows"):
            rows = tuple(
                AfterTaxRow(
                    period=str(row["period"]),
                    before_tax_percent=float(row["before_tax_percent"]),
                    after_tax_on_distributions_percent=float(
                        row["after_tax_on_distributions_percent"]
                    ),
                    after_tax_on_distributions_and_sale_percent=float(
                        row["after_tax_on_distributions_and_sale_percent"]
                    ),
                )
                for row in block["rows"]
            )
            taxes[key] = ProductTaxFacts(
                ticker=key,
                as_of=str(block.get("as_of", "")),
                rows=rows,
                methodology=str(block.get("methodology", "")),
                source_url=str(record.get("source_url", "")),
            )
    return facts, taxes


def screen_union_frame(
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
    intended_exposure_map: Mapping[str, str],
) -> tuple[tuple[ScreenedProduct, ...], int]:
    """Apply the predeclared criteria in their fixed order to the union census.

    A series that never matched the mandate pattern is not a managed-futures
    product and is not a rejection either, so it is counted but not enumerated.
    """
    mandate = re.compile(mandate_pattern, re.IGNORECASE)
    exclusion = re.compile(exclusion_pattern, re.IGNORECASE)

    union: dict[str, FrameRow] = dict(follow_up)
    for series_id, row in frame.items():
        union.setdefault(series_id, row)

    screened: list[ScreenedProduct] = []
    matches = 0
    for series_id in sorted(union):
        # The NAME is taken from the most recent census the series appears in, so a
        # fund that renamed is screened under the name it files today. Both names
        # are visible in the two committed frame manifests.
        row = follow_up.get(series_id) or frame[series_id]
        if not mandate.search(row.series_name):
            continue
        matches += 1
        classes = list(class_tickers.get(series_id, ()))
        etf_classes = [
            (class_id, ticker)
            for class_id, ticker in classes
            if exchange_flags.get(ticker, (False, ""))[0]
        ]
        chosen_class, ticker = (etf_classes or classes or [("", "")])[0]
        security_name = exchange_flags.get(ticker, (False, ""))[1]
        fund_facts = facts.get(ticker)

        frame_row = frame.get(series_id)
        follow_row = follow_up.get(series_id)
        assets_frame = None if frame_row is None else frame_row.net_assets
        assets_follow = None if follow_row is None else follow_row.net_assets
        observed = [value for value in (assets_frame, assets_follow) if value is not None]
        assets_max = max(observed) if observed else None

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
        elif assets_max is None or assets_max < minimum_net_assets:
            failed, detail = "minimum_net_assets", (
                f"largest observed net assets {assets_max!r} USD across "
                f"{FRAME_QUARTER} and {FOLLOW_UP_QUARTER} is below "
                f"{minimum_net_assets:,.0f}"
            )
        elif fund_facts is None or fund_facts.net_expense_ratio_percent is None:
            failed, detail = "maximum_expense_ratio", (
                f"no net expense ratio was verified from a prospectus for {ticker}"
            )
        elif fund_facts.net_expense_ratio_percent > maximum_expense_ratio:
            failed, detail = "maximum_expense_ratio", (
                f"net expense ratio {fund_facts.net_expense_ratio_percent}% exceeds "
                f"{maximum_expense_ratio}%"
            )
        elif fund_facts.inception_date is None:
            failed, detail = "inception_cutoff", (
                f"no inception date was verified from a prospectus for {ticker}"
            )
        elif fund_facts.inception_date > inception_on_or_before:
            failed, detail = "inception_cutoff", (
                f"inception {fund_facts.inception_date} is after {inception_on_or_before}, "
                "so three complete calendar years do not exist inside the window"
            )

        target: str | None = None
        if fund_facts is not None:
            target = intended_exposure_map.get(fund_facts.stated_mandate)
        if failed is None and target is None:
            # Distinct from mandate_regex: the NAME matched, so it is a trend-named
            # product; what failed is that the sponsor's stated mandate is not a
            # diversified futures programme. This is how an equity-and-cash trend
            # rotation is kept out -- recorded with its reason, not dropped.
            failed, detail = "mandate_in_map", (
                f"stated mandate {fund_facts.stated_mandate!r} is not in the frozen "
                "intended-exposure map, so there is no declared exposure to grade "
                "this fund against"
                if fund_facts is not None
                else "no prospectus facts were recorded for this ticker"
            )

        screened.append(
            ScreenedProduct(
                ticker=ticker,
                series_id=series_id,
                class_id=chosen_class,
                series_name=row.series_name,
                security_name=security_name,
                passed=failed is None,
                failed_criterion=failed,
                failure_detail=detail,
                net_assets_frame=assets_frame,
                net_assets_follow_up=assets_follow,
                net_assets_maximum=assets_max,
                in_frame_quarter=frame_row is not None,
                in_follow_up_quarter=follow_row is not None,
                final_filing_flag_seen=(frame_row is not None and frame_row.is_last_filing)
                or (follow_row is not None and follow_row.is_last_filing),
                exchange_listed_now=ticker in exchange_flags,
                facts=fund_facts,
                intended_target=target,
            )
        )

    screened.sort(key=lambda item: (-(item.net_assets_maximum or 0.0), item.ticker))
    return tuple(screened), matches


def _attrition(
    frame: Mapping[str, FrameRow],
    follow_up: Mapping[str, FrameRow],
    mandate_pattern: str,
    exclusion_pattern: str,
) -> dict[str, object]:
    """How much of the 2019 managed-futures shelf is gone, and what launched since.

    Membership is decided by running the patterns over each census's OWN series
    names, so a fund that renamed out of the mandate pattern counts as gone. That
    defect was found in Experiment 002's attrition figure and is repeated here
    only because the alternative -- matching on series identifier alone -- answers a
    different question. Both counts are reported: series absent from the follow-up
    census ALTOGETHER is the one that means liquidation.
    """
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
    gone_by_pattern = start - end
    gone_altogether = {series_id for series_id in start if series_id not in follow_up}
    born = end - start
    return {
        "mandate_qualifying_series_in_frame": len(start),
        "mandate_qualifying_series_in_follow_up": len(end),
        "series_present_in_frame_and_absent_at_follow_up_by_pattern": len(gone_by_pattern),
        "series_present_in_frame_and_absent_from_follow_up_census": len(gone_altogether),
        "attrition_rate_census_absence": (len(gone_altogether) / len(start)) if start else 0.0,
        "net_assets_of_series_absent_from_follow_up_census_usd": sum(
            frame[series_id].net_assets or 0.0 for series_id in gone_altogether
        ),
        "series_absent_from_frame_and_present_at_follow_up": len(born),
        "largest_series_absent_from_follow_up_census": [
            {
                "series_name": frame[series_id].series_name,
                "net_assets_usd": frame[series_id].net_assets,
                "last_report_date": frame[series_id].report_date,
            }
            for series_id in sorted(
                gone_altogether, key=lambda sid: -(frame[sid].net_assets or 0.0)
            )[:10]
        ],
        "interpretation": (
            "LOWER BOUND on survivorship contamination. Public N-PORT filings begin "
            "in 2019, so any managed-futures fund that closed before 2019Q4 is "
            "invisible to both censuses. The union frame retains the funds that died "
            "inside the window, which a single late frame would not, but it cannot "
            "recover the ones that died before the source existed."
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
    intended_exposure_map: Mapping[str, str],
    facts: Mapping[str, ProductFacts] | None = None,
) -> ManagedFuturesUniverse:
    """Screen the union census and assemble the committed universe record."""
    frame, frame_entry = load_frame(cache, FRAME_QUARTER)
    follow_up, follow_entry = load_frame(cache, FOLLOW_UP_QUARTER)
    class_tickers = _load_class_tickers(cache)
    exchange_flags = _load_exchange_flags(cache)
    product_facts = dict(facts) if facts is not None else load_product_facts()[0]

    screened, matches = screen_union_frame(
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
        intended_exposure_map=intended_exposure_map,
    )
    union_size = len(set(frame) | set(follow_up))

    return ManagedFuturesUniverse(
        schema_version=UNIVERSE_SCHEMA_VERSION,
        built_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        frame_quarter=FRAME_QUARTER,
        follow_up_quarter=FOLLOW_UP_QUARTER,
        frame_series_count=len(frame),
        follow_up_series_count=len(follow_up),
        union_series_count=union_size,
        mandate_matches=matches,
        products=screened,
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
            "criteria_order": list(CRITERION_ORDER),
            "mandate_pattern": mandate_pattern,
            "exclusion_pattern": exclusion_pattern,
            "minimum_net_assets_usd": minimum_net_assets,
            "net_assets_policy": (
                "the floor is applied to the MAXIMUM of the two observed census "
                "figures, so a fund that reached it and then shrank is still screened"
            ),
            "maximum_net_expense_ratio_percent": maximum_expense_ratio,
            "inception_on_or_before": inception_on_or_before,
            "intended_exposure_map": dict(intended_exposure_map),
        },
        notes=(
            "Built BEFORE any fund return was downloaded. The return tables of the "
            "data sets were never opened while screening.",
            "The frame is the UNION of the first and the most recent public census, "
            "because the products under audit did not exist in 2019 and a "
            "start-of-window frame would exclude them by construction.",
            "Every mandate-matching series is listed, passing or failing, because "
            "the multiple-testing denominator is the whole screen.",
            "Expense ratio, inception, index and the after-tax table come from each "
            "fund's own SEC-filed summary prospectus, not from Form N-PORT.",
        ),
    )


def write_universe(universe: ManagedFuturesUniverse, path: Path | None = None) -> Path:
    location = path or universe_path()
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(
        json.dumps(universe.to_json(), indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return location


def load_universe(path: Path | None = None) -> ManagedFuturesUniverse:
    """Read the committed universe. The experiment never rebuilds it."""
    location = path or universe_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. Build it with "
            "`python -m portfolio_edge.experiments.exp_008_managed_futures "
            "--build-universe` BEFORE running the audit; the universe must be fixed "
            "before returns are downloaded."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    products: list[ScreenedProduct] = []
    for record in payload.get("products", []):
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
        products.append(
            ScreenedProduct(
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
                net_assets_maximum=_optional_number(record.get("net_assets_maximum_usd")),
                in_frame_quarter=bool(record.get("in_frame_quarter", False)),
                in_follow_up_quarter=bool(record.get("in_follow_up_quarter", False)),
                final_filing_flag_seen=bool(record.get("final_filing_flag_seen", False)),
                exchange_listed_now=bool(record.get("exchange_listed_now", False)),
                facts=facts,
                intended_target=_optional_text(record.get("intended_target")),
            )
        )
    return ManagedFuturesUniverse(
        schema_version=str(payload.get("schema_version", UNIVERSE_SCHEMA_VERSION)),
        built_utc=str(payload.get("built_utc", "")),
        frame_quarter=str(payload.get("frame_quarter", FRAME_QUARTER)),
        follow_up_quarter=str(payload.get("follow_up_quarter", FOLLOW_UP_QUARTER)),
        frame_series_count=int(payload.get("frame_series_count", 0)),
        follow_up_series_count=int(payload.get("follow_up_series_count", 0)),
        union_series_count=int(payload.get("union_series_count", 0)),
        mandate_matches=int(payload.get("mandate_matches", 0)),
        products=tuple(products),
        attrition=payload.get("attrition", {}),
        inputs=payload.get("inputs", {}),
        notes=tuple(str(item) for item in payload.get("notes", [])),
    )


def universe_manifests(cache: RawCache) -> tuple[DatasetManifest, ...]:
    """Frame manifests for both limbs of the union.

    Reuses Experiment 002's frame manifest verbatim: the census table it hashes --
    series identifier, official name and net assets -- is exactly what this screen
    reads, and two manifests of the same bytes must not disagree.
    """
    return tuple(frame_manifest(cache, quarter) for quarter in (FRAME_QUARTER, FOLLOW_UP_QUARTER))
