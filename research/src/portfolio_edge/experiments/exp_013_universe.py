"""Experiment 013, step one: the US factor product universe on the UNION frame.

Built and committed BEFORE any fund return is downloaded, for the same reason as
:mod:`portfolio_edge.experiments.exp_002_universe` and
:mod:`portfolio_edge.experiments.exp_009_universe`: a universe chosen after
seeing performance is not a universe, it is a result. Nothing here reads a
return. The frames carry series names, net assets and filing dates only.

Why this module exists
----------------------
Experiment 002 screened the US shelf against the **2019Q4 census alone** and
required inception on or before 2016-12-31. Experiment 009 later established, for
the ex-US shelf, that a 2019Q4-only frame "would have excluded exactly the
products the question is about", and used the union of the 2019Q4 and 2025Q4
censuses instead. **That correction was never applied to the US shelf**, and the
same launch wave hit it: AVUV (2019-09), AVLV, AVSC, the Dimensional ETF
conversions DFAT, DFAS, DFUV, DFLV, DFSV and DUHP (2021-2022), plus a long tail
of Schwab, Vanguard and Fidelity products whose registrants simply do not appear
in the 2019Q4 file at all. Every one of them was excluded from Experiment 002 by
construction, and the exclusion points in a known direction: it removes the
newest, cheapest and highest-loading systematic products.

Exactly what changed, and what did not
--------------------------------------
**Experiment 002's screen is not modified.** Its module, its frozen
specification, its committed universe file and its published numbers are
untouched, and
:func:`~portfolio_edge.experiments.exp_009_universe.exp_002_screen_is_unmodified`
asserts its two regexes byte-for-byte so that a future edit to them fails a test
here rather than silently making the audits incomparable.

Two criteria move, and only two, and they are the same change twice:

1. **The frame is the union of the 2019Q4 and 2025Q4 censuses**, as in
   Experiment 009, and the asset floor is applied to the **maximum** of a series'
   two observed net-asset figures so that neither launch size nor terminal size
   selects.
2. **The inception cutoff is deleted.** Admitting post-2019 launches into the
   frame and then rejecting them for being post-2019 launches would be the same
   exclusion wearing a different name. What replaces it is a *sample-length*
   requirement applied at estimation time -- at least 36 filed monthly returns,
   as in Experiment 009 -- so a young fund is `unresolved` on a short window
   rather than absent from the audit.

Everything else is byte-identical to Experiment 002: the mandate pattern, the
exclusion pattern, the exchange-traded criterion, the $1bn asset floor, the 0.60%
expense cap, the intended-factor map and its signs, and the four falsifier
clauses with their thresholds.

The criterion order, and why a gathering gap cannot masquerade as a screen result
---------------------------------------------------------------------------------
Experiment 002 had to correct its universe once, before any return was read,
because nine growth ETFs were failing the expense criterion only because nobody
had looked their fees up. The order below is Experiment 002's, which already puts
every census-evaluable criterion before every criterion needing a sponsor
document; the set of funds requiring a prospectus read is therefore fixed by the
census rather than by how much looking was done, and it is enumerated in the
committed universe file whether or not a fee was found.
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
from portfolio_edge.experiments.exp_009_universe import (
    AttritionReport,
    ScreeningPatterns,
    attrition,
    exp_002_screen_is_unmodified,
)

__all__ = [
    "CRITERION_ORDER",
    "FOLLOW_UP_QUARTER",
    "FRAME_QUARTER",
    "UNIVERSE_SCHEMA_VERSION",
    "ScreenedUsFund",
    "UnionUniverse",
    "build_universe",
    "exp_002_screen_is_unmodified",
    "fiscal_quarter_coverage",
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

#: Applied in this fixed order. A fund records the FIRST criterion it failed, so
#: the reason a fund is absent is deterministic and the funnel adds up. This is
#: Experiment 002's order with ``inception_cutoff`` removed and nothing else
#: touched or reordered.
CRITERION_ORDER: Final = (
    "mandate_regex",
    "exclusion_regex",
    "exchange_traded",
    "minimum_net_assets",
    "maximum_expense_ratio",
    "mandate_in_map",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScreenedUsFund:
    """One series' complete screen record, whether it passed or failed.

    A failing fund is kept in full: the multiple-testing denominator is the whole
    screen, and a screen whose rejections are not written down cannot supply one.
    """

    ticker: str
    series_id: str
    class_id: str
    series_name_frame: str
    series_name_follow_up: str
    """The name in the LATER census. A change here is a rename, not a death."""
    security_name: str
    passed: bool
    failed_criterion: str | None
    failure_detail: str
    net_assets_frame: float | None
    net_assets_follow_up: float | None
    net_assets_max: float
    report_date_frame: str
    report_date_follow_up: str
    """The fiscal quarter-end each census carries for this series.

    Load-bearing, not decoration. The 2019Q4 data set contains only periods ending
    2019-09-30 and 2019-10-31, so a series whose fiscal quarter ends in AUGUST is
    absent from Experiment 002's frame whatever its age.
    """
    in_frame_census: bool
    in_follow_up_census: bool
    final_filing_flag_seen: bool
    exchange_listed_now: bool
    intended_factor: str | None
    intended_sign: int
    facts: ProductFacts | None

    @property
    def series_name(self) -> str:
        """The name of the product as it exists now, falling back to the earlier one."""
        return self.series_name_follow_up or self.series_name_frame

    @property
    def renamed(self) -> bool:
        both = self.series_name_frame and self.series_name_follow_up
        return bool(both) and self.series_name_frame != self.series_name_follow_up

    @property
    def in_exp_002_frame(self) -> bool:
        """Whether Experiment 002's 2019Q4-only frame could have seen this series."""
        return self.in_frame_census

    def to_json(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "series_id": self.series_id,
            "class_id": self.class_id,
            "series_name_frame": self.series_name_frame,
            "series_name_follow_up": self.series_name_follow_up,
            "renamed_inside_the_window": self.renamed,
            "security_name": self.security_name,
            "passed": self.passed,
            "failed_criterion": self.failed_criterion,
            "failure_detail": self.failure_detail,
            "net_assets_frame_usd": self.net_assets_frame,
            "net_assets_follow_up_usd": self.net_assets_follow_up,
            "net_assets_max_usd": self.net_assets_max,
            "report_date_frame": self.report_date_frame,
            "report_date_follow_up": self.report_date_follow_up,
            "in_frame_census": self.in_frame_census,
            "in_follow_up_census": self.in_follow_up_census,
            "visible_to_exp_002_frame": self.in_exp_002_frame,
            "final_filing_flag_seen": self.final_filing_flag_seen,
            "exchange_listed_now": self.exchange_listed_now,
            "intended_factor": self.intended_factor,
            "intended_sign": self.intended_sign,
            "facts": None if self.facts is None else self.facts.to_json(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class UnionUniverse:
    """The committed screening outcome for the US shelf on the union frame."""

    schema_version: str
    built_utc: str
    frame_quarter: str
    follow_up_quarter: str
    frame_series_count: int
    follow_up_series_count: int
    union_series_count: int
    mandate_matches: int
    funds: tuple[ScreenedUsFund, ...]
    attrition: AttritionReport
    inputs: Mapping[str, object]
    notes: tuple[str, ...]

    @property
    def passing(self) -> tuple[ScreenedUsFund, ...]:
        return tuple(fund for fund in self.funds if fund.passed)

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
            "attrition": self.attrition.to_json(),
            "inputs": dict(self.inputs),
            "notes": list(self.notes),
            "funds": [fund.to_json() for fund in self.funds],
        }


def universe_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_013" / "product_universe.json"


def product_facts_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_013" / "product_facts.json"


# --------------------------------------------------------------------------- #
# Product facts
# --------------------------------------------------------------------------- #


def load_product_facts(path: Path | None = None) -> dict[str, ProductFacts]:
    """Read the committed per-fund facts, read from each fund's own SEC filing.

    Reuses Experiment 002's :class:`ProductFacts` unchanged so that a fee, an
    inception date or a stated mandate means exactly the same thing in both
    audits. Experiment 002's own facts file is carried forward verbatim for every
    fund the two audits share; see the ``carried_from_exp_002`` flag in the
    committed file.
    """
    location = path or product_facts_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. The screen needs a net expense ratio and a "
            "stated mandate per fund, and neither is in Form N-PORT; they are read "
            "from each fund's own SEC-filed summary prospectus or registration "
            "statement and committed with a URL and a date."
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


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtraFacts:
    """The two fields Experiment 002's ``ProductFacts`` has no room for.

    ``converted_from_mutual_fund`` is the one that changes a number. An SEC fund
    series survives a conversion from a mutual fund into an ETF, so DFAT's series
    carries filings from the predecessor Tax-Managed portfolio and DFUV's from
    its own. Those months are a different product at a different fee, and the
    sponsor-stated inception date is the *predecessor's*. The ETF's own first day
    is recorded here and is what the estimation window floors on.
    """

    ticker: str
    converted_from_mutual_fund: str | None
    etf_inception_date: str | None
    source_form: str
    expense_detail: str

    def to_json(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "converted_from_mutual_fund": self.converted_from_mutual_fund,
            "etf_inception_date": self.etf_inception_date,
            "source_form": self.source_form,
            "expense_detail": self.expense_detail,
        }


def load_extra_facts(path: Path | None = None) -> dict[str, ExtraFacts]:
    """Read the conversion-aware half of the committed product facts."""
    location = path or product_facts_path()
    if not location.is_file():
        raise UniverseError(f"{location} is missing")
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds = payload.get("funds", {})
    out: dict[str, ExtraFacts] = {}
    for ticker, record in funds.items():
        out[str(ticker)] = ExtraFacts(
            ticker=str(ticker),
            converted_from_mutual_fund=_optional_text(record.get("converted_from_mutual_fund")),
            etf_inception_date=_optional_text(record.get("etf_inception_date")),
            source_form=str(record.get("source_form", "")),
            expense_detail=str(record.get("expense_detail", "")),
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


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


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
    intended_factor_map: Mapping[str, tuple[str, int]],
) -> tuple[tuple[ScreenedUsFund, ...], int]:
    """Apply Experiment 002's criteria, minus the inception cutoff, to the union."""
    mandate = re.compile(mandate_pattern, re.IGNORECASE)
    exclusion = re.compile(exclusion_pattern, re.IGNORECASE)

    screened: list[ScreenedUsFund] = []
    matches = 0
    for series_id in sorted(set(frame) | set(follow_up)):
        early, late = frame.get(series_id), follow_up.get(series_id)
        # The name in EITHER census may match. A fund renamed INTO the mandate is
        # as real as one renamed out of it, and testing only the earlier name
        # would miss every product launched after 2019 -- which is the whole
        # population this experiment exists to admit.
        names = [row.series_name for row in (early, late) if row is not None]
        if not any(mandate.search(name) for name in names):
            continue
        matches += 1

        # The LATER name decides the screen: a fund is graded as the product it is
        # now, and a fund that only exists in the earlier census is graded as the
        # product it was when it stopped filing.
        current = late if late is not None else early
        name = "" if current is None else current.series_name
        classes = list(class_tickers.get(series_id, ()))
        etf_classes = [
            (class_id, ticker)
            for class_id, ticker in classes
            if exchange_flags.get(ticker, (False, ""))[0]
        ]
        chosen_class, ticker = (etf_classes or classes or [("", "")])[0]
        assets = [
            row.net_assets
            for row in (early, late)
            if row is not None and row.net_assets is not None
        ]
        maximum_assets = max(assets, default=0.0)
        fund_facts = facts.get(ticker)

        failed: str | None = None
        detail = ""
        if exclusion.search(name):
            failed, detail = "exclusion_regex", (
                f"series name matches the exclusion pattern: {name!r}"
            )
        elif not classes:
            failed, detail = "exchange_traded", "EDGAR lists no ticker for this series"
        elif not etf_classes:
            failed, detail = "exchange_traded", (
                "no share class of this series carries an ETF=Y flag in the current "
                f"consolidated symbol directory (classes: {[t for _, t in classes]})"
            )
        elif maximum_assets < minimum_net_assets:
            failed, detail = "minimum_net_assets", (
                f"largest observed net assets across both censuses "
                f"{maximum_assets:,.0f} USD is below {minimum_net_assets:,.0f}"
            )
        elif fund_facts is None or fund_facts.net_expense_ratio_percent is None:
            failed, detail = "maximum_expense_ratio", (
                f"no net expense ratio was verified from an SEC-filed document for {ticker}"
            )
        elif fund_facts.net_expense_ratio_percent > maximum_expense_ratio:
            failed, detail = "maximum_expense_ratio", (
                f"net expense ratio {fund_facts.net_expense_ratio_percent}% exceeds "
                f"{maximum_expense_ratio}%"
            )

        factor, sign = (None, 0)
        if fund_facts is not None:
            factor, sign = intended_factor_map.get(fund_facts.stated_mandate, (None, 0))
        if failed is None and factor is None:
            # Distinct from ``mandate_regex``: the fund's NAME matched, so it is a
            # factor product; what failed is that its stated mandate has no entry
            # in the predeclared map. That is how a minimum-volatility fund, and a
            # fund which changed its objective inside the window, are kept out --
            # recorded, not dropped.
            failed, detail = "mandate_in_map", (
                f"stated mandate {fund_facts.stated_mandate!r} is not in the "
                "predeclared intended-factor map, so there is no declared factor "
                "to grade this fund against"
                if fund_facts is not None
                else "no sponsor facts were recorded for this ticker"
            )

        screened.append(
            ScreenedUsFund(
                ticker=ticker,
                series_id=series_id,
                class_id=chosen_class,
                series_name_frame="" if early is None else early.series_name,
                series_name_follow_up="" if late is None else late.series_name,
                security_name=exchange_flags.get(ticker, (False, ""))[1],
                passed=failed is None,
                failed_criterion=failed,
                failure_detail=detail,
                net_assets_frame=None if early is None else early.net_assets,
                net_assets_follow_up=None if late is None else late.net_assets,
                net_assets_max=maximum_assets,
                report_date_frame="" if early is None else early.report_date,
                report_date_follow_up="" if late is None else late.report_date,
                in_frame_census=early is not None,
                in_follow_up_census=late is not None,
                final_filing_flag_seen=any(
                    row.is_last_filing for row in (early, late) if row is not None
                ),
                exchange_listed_now=ticker in exchange_flags,
                intended_factor=factor,
                intended_sign=sign,
                facts=fund_facts,
            )
        )

    screened.sort(key=lambda fund: (-fund.net_assets_max, fund.ticker))
    return tuple(screened), matches


def fiscal_quarter_coverage(
    frame: Mapping[str, FrameRow], follow_up: Mapping[str, FrameRow]
) -> dict[str, object]:
    """Which fiscal quarter-ends each census actually carries.

    This is the mechanism behind most of the frame defect and it is measured
    rather than asserted. Form N-PORT is filed on each series' OWN fiscal
    calendar, and public reporting began with periods ending 2019-09-30. The
    2019Q4 data set therefore carries periods ending in September and October
    only, so **every fund whose fiscal quarter ends in August is absent from
    Experiment 002's frame whatever its age** -- which on the US shelf is the
    whole of Schwab's equity range, most of Vanguard's ETF-only trusts, Invesco's
    S&P factor range and Avantis.
    """
    def counts(rows: Mapping[str, FrameRow]) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in rows.values():
            out[row.report_date] = out.get(row.report_date, 0) + 1
        return dict(sorted(out.items()))

    early, late = counts(frame), counts(late_rows := follow_up)
    del late_rows
    august_late = sum(count for date, count in late.items() if date[5:7] == "08")
    august_early = sum(count for date, count in early.items() if date[5:7] == "08")
    return {
        "frame_report_dates": early,
        "follow_up_report_dates": late,
        "series_with_an_august_fiscal_quarter_in_the_frame": august_early,
        "series_with_an_august_fiscal_quarter_at_follow_up": august_late,
        "interpretation": (
            "Form N-PORT is filed on each series' own fiscal calendar and public "
            "reporting begins with periods ending 2019-09-30, so the 2019Q4 data "
            "set carries September and October quarter-ends only. A fund whose "
            "fiscal quarter ends in AUGUST is therefore absent from Experiment "
            "002's frame whatever its age, and that is a calendar fact about the "
            "filer rather than anything about the fund."
        ),
    }


def _patterns_for_attrition(mandate_pattern: str, exclusion_pattern: str) -> ScreeningPatterns:
    """Experiment 009's attrition decomposition, driven by Experiment 002's patterns.

    Experiment 002's screen tests a mandate pattern and an exclusion pattern and
    has no separate region pattern, so the region regex is set to "match
    everything" to reproduce its qualifying set exactly.
    """
    return ScreeningPatterns(
        region_regex="",
        factor_regex=mandate_pattern,
        exclusion_regex=exclusion_pattern,
        us_token_regex="",
        global_token_regex="",
        ex_us_token_regex="",
        emerging_regex="",
        world_ex_us_regex="",
        mandate_patterns=(),
    )


# --------------------------------------------------------------------------- #
# Building, writing and reading the committed universe
# --------------------------------------------------------------------------- #


def build_universe(
    *,
    cache: RawCache,
    mandate_pattern: str,
    exclusion_pattern: str,
    minimum_net_assets: float,
    maximum_expense_ratio: float,
    intended_factor_map: Mapping[str, tuple[str, int]],
    facts: Mapping[str, ProductFacts] | None = None,
) -> UnionUniverse:
    """Screen the union census and assemble the committed universe record."""
    frame, frame_entry = load_frame(cache, FRAME_QUARTER)
    follow_up, follow_entry = load_frame(cache, FOLLOW_UP_QUARTER)
    class_tickers = _load_class_tickers(cache)
    exchange_flags = _load_exchange_flags(cache)
    product_facts = dict(facts) if facts is not None else load_product_facts()

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
        intended_factor_map=intended_factor_map,
    )

    return UnionUniverse(
        schema_version=UNIVERSE_SCHEMA_VERSION,
        built_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        frame_quarter=FRAME_QUARTER,
        follow_up_quarter=FOLLOW_UP_QUARTER,
        frame_series_count=len(frame),
        follow_up_series_count=len(follow_up),
        union_series_count=len(set(frame) | set(follow_up)),
        mandate_matches=matches,
        funds=screened,
        attrition=attrition(
            frame, follow_up, _patterns_for_attrition(mandate_pattern, exclusion_pattern)
        ),
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
            "fiscal_quarter_coverage": fiscal_quarter_coverage(frame, follow_up),
            "criteria_order": list(CRITERION_ORDER),
            "mandate_pattern": mandate_pattern,
            "exclusion_pattern": exclusion_pattern,
            "minimum_net_assets_usd": minimum_net_assets,
            "maximum_net_expense_ratio_percent": maximum_expense_ratio,
            "inception_cutoff": None,
            "intended_factor_map": {
                mandate: {"factor": factor, "sign": sign}
                for mandate, (factor, sign) in sorted(intended_factor_map.items())
            },
        },
        notes=(
            "Built BEFORE any fund return was downloaded. The return tables of the "
            "data sets were never opened while screening.",
            "The frame is the UNION of the 2019Q4 and 2025Q4 censuses. Experiment "
            "002 screened 2019Q4 alone, which excluded by construction every US "
            "product that launched, converted or began filing after 2019 -- the "
            "newest, cheapest and highest-loading part of the shelf.",
            "The asset floor is applied to the MAXIMUM of a series' two observed "
            "net-asset figures, so neither terminal size nor launch size selects.",
            "Experiment 002's INCEPTION CUTOFF of 2016-12-31 is deleted, because "
            "admitting post-2019 launches into the frame and then rejecting them "
            "for being post-2019 launches is the same exclusion under another "
            "name. A sample-length requirement replaces it at estimation time.",
            "Nothing else moved. The mandate pattern, the exclusion pattern, the "
            "exchange-traded criterion, the $1bn floor, the 0.60% expense cap and "
            "the intended-factor map are Experiment 002's, unchanged.",
            "Experiment 002's screen is NOT modified by this module. Its two "
            "regexes are asserted unchanged, so the US audit's published numbers "
            "stand as a description of the frame that produced them.",
        ),
    )


def write_universe(universe: UnionUniverse, path: Path | None = None) -> Path:
    location = path or universe_path()
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(
        json.dumps(universe.to_json(), indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return location


def load_universe(path: Path | None = None) -> UnionUniverse:
    """Read the committed universe. The experiment never rebuilds it."""
    location = path or universe_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. Build it with "
            "`python -m portfolio_edge.experiments.exp_013_us_products_union_frame "
            "--build-universe` BEFORE running the audit; the universe must be fixed "
            "before returns are downloaded."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds: list[ScreenedUsFund] = []
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
            ScreenedUsFund(
                ticker=str(record["ticker"]),
                series_id=str(record["series_id"]),
                class_id=str(record["class_id"]),
                series_name_frame=str(record.get("series_name_frame", "")),
                series_name_follow_up=str(record.get("series_name_follow_up", "")),
                security_name=str(record.get("security_name", "")),
                passed=bool(record["passed"]),
                failed_criterion=_optional_text(record.get("failed_criterion")),
                failure_detail=str(record.get("failure_detail", "")),
                net_assets_frame=_optional_number(record.get("net_assets_frame_usd")),
                net_assets_follow_up=_optional_number(record.get("net_assets_follow_up_usd")),
                net_assets_max=float(record.get("net_assets_max_usd", 0.0) or 0.0),
                report_date_frame=str(record.get("report_date_frame", "")),
                report_date_follow_up=str(record.get("report_date_follow_up", "")),
                in_frame_census=bool(record.get("in_frame_census", False)),
                in_follow_up_census=bool(record.get("in_follow_up_census", False)),
                final_filing_flag_seen=bool(record.get("final_filing_flag_seen", False)),
                exchange_listed_now=bool(record.get("exchange_listed_now", False)),
                intended_factor=_optional_text(record.get("intended_factor")),
                intended_sign=int(record.get("intended_sign", 0) or 0),
                facts=facts,
            )
        )
    raw = payload.get("attrition", {})
    report = AttritionReport(
        qualifying_in_frame=int(raw.get("qualifying_in_frame", 0)),
        qualifying_in_follow_up=int(raw.get("qualifying_in_follow_up", 0)),
        absent_from_follow_up_census=int(raw.get("absent_from_follow_up_census", 0)),
        renamed_out_of_the_pattern=int(raw.get("renamed_out_of_the_pattern", 0)),
        still_qualifying=int(raw.get("still_qualifying", 0)),
        launched_inside_the_window=int(raw.get("launched_inside_the_window", 0)),
        renamed_into_the_pattern=int(raw.get("renamed_into_the_pattern", 0)),
        net_assets_of_absent_series_usd=float(raw.get("net_assets_of_absent_series_usd", 0.0)),
        net_assets_of_renamed_series_usd=float(raw.get("net_assets_of_renamed_series_usd", 0.0)),
        largest_absent_series=tuple(raw.get("largest_absent_series", [])),
        renamed_examples=tuple(raw.get("renamed_examples", [])),
    )
    return UnionUniverse(
        schema_version=str(payload.get("schema_version", UNIVERSE_SCHEMA_VERSION)),
        built_utc=str(payload.get("built_utc", "")),
        frame_quarter=str(payload.get("frame_quarter", FRAME_QUARTER)),
        follow_up_quarter=str(payload.get("follow_up_quarter", FOLLOW_UP_QUARTER)),
        frame_series_count=int(payload.get("frame_series_count", 0)),
        follow_up_series_count=int(payload.get("follow_up_series_count", 0)),
        union_series_count=int(payload.get("union_series_count", 0)),
        mandate_matches=int(payload.get("mandate_matches", 0)),
        funds=tuple(funds),
        attrition=report,
        inputs=payload.get("inputs", {}),
        notes=tuple(str(item) for item in payload.get("notes", [])),
    )


def universe_manifests(cache: RawCache) -> tuple[DatasetManifest, ...]:
    """Manifests for both census limbs of the union frame."""
    return tuple(
        frame_manifest(cache, quarter) for quarter in (FRAME_QUARTER, FOLLOW_UP_QUARTER)
    )
