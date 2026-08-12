"""Experiment 009, step one: the ex-US factor product universe.

Built and committed BEFORE any fund return is downloaded, for the same reason as
:mod:`portfolio_edge.experiments.exp_002_universe` and
:mod:`portfolio_edge.experiments.exp_008_universe`: a universe chosen after
seeing performance is not a universe, it is a result. Nothing here reads a
return. The frames carry series names, net assets and filing dates only.

Why this module exists at all
-----------------------------
Experiment 002 audited the factor-product shelf and audited **zero** ex-US
products. Its exclusion pattern removes any series whose name carries
``international``, ``intl``, ``global``, ``world``, ``emerging``, ``developed``,
``eafe``, ``acwi`` or ``ex-US``, which is roughly 185 international, 82 global
and 51 emerging series. Experiments 005 and 007 then located essentially all of
the value premium's measurable weight outside the United States. So the
repository audited products in the region where the premium is weakest and
audited none where it is strongest.

What changed in the screen, exactly, and what did not
-----------------------------------------------------
**Experiment 002's screen is not modified.** Its module, its frozen
specification, its committed universe file and its published numbers are
untouched, and :func:`exp_002_screen_is_unmodified` asserts the two regexes in
its specification byte-for-byte so that a future edit to them fails a test here
rather than silently making the two audits incomparable.

This module instead applies the **complementary** screen. Three differences, each
deliberate:

1. The mandate pattern requires a region word **and** a factor word, where
   Experiment 002 required a factor word and forbade every region word.
2. A ``us_overlap`` criterion replaces the ex-US exclusion. A fund whose mandate
   includes the United States (``global``, ``world``, ``ACWI`` without an
   ``ex-US`` qualifier, or an explicit ``U.S.`` token) cannot be priced by a
   non-US factor panel, so it is recorded and excluded rather than mispriced.
3. A ``region_in_map`` criterion is added. Ken French publishes a
   developed-ex-US file and an emerging file, and nothing in between. A
   world-ex-US product spans both, so grading it against either one alone would
   be a misspecification chosen for convenience. Such a fund is recorded, not
   graded, and the largest of them (VSS) still enters the audit as a *comparator*
   where no factor panel is needed.

The frame is a union, as in Experiment 008
------------------------------------------
Every fund the question is actually about launched after 2019: AVDV 2019-09,
AVIV and AVES 2021-09, DISV 2021-09, DFIV 2021-11, DFEV 2022-04. A 2019Q4-only
frame would exclude them by construction. So the frame is the union of the first
and the most recent public census, and the asset floor is applied to the
**maximum** of a series' two observed net-asset figures.

The rename trap this repository already hit once
------------------------------------------------
Experiment 002 measures attrition by differencing two **name-qualified** sets of
series identifiers. A fund that renamed out of the mandate pattern — every
``iShares Edge MSCI ...`` product dropped ``Edge`` in 2021, and
``iShares Edge MSCI Multifactor Intl ETF`` became ``iShares International Equity
Factor ETF`` in 2022 — is counted as a **death** by that construction even though
its series identifier kept filing every quarter. :func:`attrition` here splits
the difference three ways instead: gone from the census entirely, present in the
census but no longer name-qualifying, and still qualifying. Only the first is a
death.
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
    "GRADED_REGIONS",
    "UNIVERSE_SCHEMA_VERSION",
    "AttritionReport",
    "ExUsUniverse",
    "ScreenedExUsFund",
    "ScreeningPatterns",
    "attrition",
    "build_universe",
    "derive_mandate",
    "derive_region",
    "exp_002_screen_is_unmodified",
    "load_product_facts",
    "load_universe",
    "product_facts_path",
    "screen_union_frame",
    "universe_manifests",
    "universe_path",
    "us_overlap",
    "write_universe",
]

UNIVERSE_SCHEMA_VERSION: Final = "1"

FRAME_QUARTER: Final = "2019q4"
"""First limb of the union frame: the first public N-PORT quarter."""

FOLLOW_UP_QUARTER: Final = "2025q4"
"""Second limb of the union frame, and the quarter attrition is measured against."""

#: The two regions Ken French publishes a factor file for that exclude the United
#: States. A product spanning both is recorded and not graded; see the module
#: docstring.
GRADED_REGIONS: Final = ("developed_ex_us", "emerging")

#: Applied in this fixed order. A fund records the FIRST criterion it failed, so
#: the reason a fund is absent is deterministic and the funnel adds up.
#:
#: The order matters in one specific way, learned from Experiment 008: every
#: criterion that can be evaluated from the CENSUS ALONE comes before every
#: criterion that needs a sponsor document. A fund excluded for its region or its
#: mandate is never looked up for a fee, so a gap in fact-gathering can never
#: masquerade as a screen decision, and the set of funds needing a prospectus
#: read is fixed by the census rather than by how much looking was done.
CRITERION_ORDER: Final = (
    "mandate_regex",
    "exclusion_regex",
    "us_overlap",
    "exchange_traded",
    "minimum_net_assets",
    "mandate_in_map",
    "region_in_map",
    "maximum_expense_ratio",
    "mandate_stable",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScreeningPatterns:
    """Every regular expression the screen applies, frozen in one object.

    Held together rather than passed as loose strings because the screen's
    meaning is the *conjunction* of them, and a caller that supplied five of six
    would produce a universe whose name did not describe it.
    """

    region_regex: str
    factor_regex: str
    exclusion_regex: str
    us_token_regex: str
    global_token_regex: str
    ex_us_token_regex: str
    emerging_regex: str
    world_ex_us_regex: str
    mandate_patterns: tuple[tuple[str, str], ...]
    """Ordered ``(mandate, pattern)`` pairs; the FIRST match wins."""

    def to_json(self) -> dict[str, object]:
        return {
            "region_regex": self.region_regex,
            "factor_regex": self.factor_regex,
            "exclusion_regex": self.exclusion_regex,
            "us_token_regex": self.us_token_regex,
            "global_token_regex": self.global_token_regex,
            "ex_us_token_regex": self.ex_us_token_regex,
            "emerging_regex": self.emerging_regex,
            "world_ex_us_regex": self.world_ex_us_regex,
            "mandate_patterns": [list(pair) for pair in self.mandate_patterns],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ScreenedExUsFund:
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
    in_frame_census: bool
    in_follow_up_census: bool
    final_filing_flag_seen: bool
    exchange_listed_now: bool
    derived_mandate: str | None
    derived_region: str | None
    intended_factor: str | None
    intended_sign: int
    facts: ProductFacts | None

    @property
    def renamed(self) -> bool:
        both = self.series_name_frame and self.series_name_follow_up
        return bool(both) and self.series_name_frame != self.series_name_follow_up

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
            "in_frame_census": self.in_frame_census,
            "in_follow_up_census": self.in_follow_up_census,
            "final_filing_flag_seen": self.final_filing_flag_seen,
            "exchange_listed_now": self.exchange_listed_now,
            "derived_mandate": self.derived_mandate,
            "derived_region": self.derived_region,
            "intended_factor": self.intended_factor,
            "intended_sign": self.intended_sign,
            "facts": None if self.facts is None else self.facts.to_json(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class AttritionReport:
    """Attrition with renames separated from deaths.

    ``renamed_out_of_the_pattern`` is the number Experiment 002's construction
    would have counted as disappearances. It is reported separately here because
    a fund that changed its name is not a fund that died, and conflating the two
    inflates the measured survivorship contamination of the shelf.
    """

    qualifying_in_frame: int
    qualifying_in_follow_up: int
    absent_from_follow_up_census: int
    renamed_out_of_the_pattern: int
    still_qualifying: int
    launched_inside_the_window: int
    renamed_into_the_pattern: int
    net_assets_of_absent_series_usd: float
    net_assets_of_renamed_series_usd: float
    largest_absent_series: tuple[Mapping[str, object], ...]
    renamed_examples: tuple[Mapping[str, object], ...]

    @property
    def death_rate(self) -> float:
        return (
            self.absent_from_follow_up_census / self.qualifying_in_frame
            if self.qualifying_in_frame
            else 0.0
        )

    @property
    def naive_rate(self) -> float:
        """What differencing name-qualified sets alone would have reported."""
        gone = self.absent_from_follow_up_census + self.renamed_out_of_the_pattern
        return gone / self.qualifying_in_frame if self.qualifying_in_frame else 0.0

    def to_json(self) -> dict[str, object]:
        return {
            "qualifying_in_frame": self.qualifying_in_frame,
            "qualifying_in_follow_up": self.qualifying_in_follow_up,
            "absent_from_follow_up_census": self.absent_from_follow_up_census,
            "renamed_out_of_the_pattern": self.renamed_out_of_the_pattern,
            "still_qualifying": self.still_qualifying,
            "launched_inside_the_window": self.launched_inside_the_window,
            "renamed_into_the_pattern": self.renamed_into_the_pattern,
            "net_assets_of_absent_series_usd": self.net_assets_of_absent_series_usd,
            "net_assets_of_renamed_series_usd": self.net_assets_of_renamed_series_usd,
            "death_rate": self.death_rate,
            "naive_rate_counting_renames_as_deaths": self.naive_rate,
            "largest_absent_series": [dict(row) for row in self.largest_absent_series],
            "renamed_examples": [dict(row) for row in self.renamed_examples],
            "interpretation": (
                "A series absent from the later census liquidated, merged or "
                "stopped filing: that is a death. A series still in the census "
                "whose name no longer matches the mandate pattern was RENAMED or "
                "re-mandated: that is not a death, and counting it as one is the "
                "trap this decomposition exists to avoid. Both rates are a LOWER "
                "BOUND on survivorship contamination, because public N-PORT "
                "filings begin in 2019 and a fund that closed before then is "
                "invisible to both censuses."
            ),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ExUsUniverse:
    """The committed screening outcome for the ex-US shelf."""

    schema_version: str
    built_utc: str
    frame_quarter: str
    follow_up_quarter: str
    frame_series_count: int
    follow_up_series_count: int
    union_series_count: int
    mandate_matches: int
    funds: tuple[ScreenedExUsFund, ...]
    attrition: AttritionReport
    inputs: Mapping[str, object]
    notes: tuple[str, ...]

    @property
    def passing(self) -> tuple[ScreenedExUsFund, ...]:
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
    return workspace_root() / "data-manifests" / "exp_009" / "product_universe.json"


def product_facts_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_009" / "product_facts.json"


# --------------------------------------------------------------------------- #
# Name-derived mandate and region
# --------------------------------------------------------------------------- #


def derive_mandate(name: str, patterns: ScreeningPatterns) -> str | None:
    """The mandate a series' official name declares, or ``None``.

    Derived MECHANICALLY from the name rather than typed in by hand, for two
    reasons. It needs no sponsor document, so the criterion can be evaluated on
    the census alone and cannot be quietly revised while reading prospectuses.
    And it gives the sponsor-stated mandate in the product facts something to
    disagree with: any disagreement is a recorded finding rather than an
    invisible reconciliation.

    Order matters and is frozen in ``patterns.mandate_patterns``: "International
    Small Cap Value" is small-cap value, not small-cap and not value.
    """
    for mandate, pattern in patterns.mandate_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return mandate
    return None


def derive_region(name: str, patterns: ScreeningPatterns) -> str:
    """``emerging``, ``world_ex_us`` or ``developed_ex_us`` from the name alone.

    ``developed_ex_us`` is the residual, which is the right default for this
    shelf: in ETF naming "International" means developed markets outside the
    United States unless the name says otherwise. The product facts record the
    tracked index's own region words, and the audit checks the two agree.
    """
    if re.search(patterns.emerging_regex, name, re.IGNORECASE):
        return "emerging"
    if re.search(patterns.world_ex_us_regex, name, re.IGNORECASE):
        return "world_ex_us"
    return "developed_ex_us"


def us_overlap(name: str, patterns: ScreeningPatterns) -> bool:
    """Whether the name claims a mandate that includes the United States.

    Two ways it can. An explicit US token — ``U.S.``, ``USA``, ``America``,
    ``Domestic`` — anywhere except inside an ``ex-US`` qualifier, which is why
    the qualifier is stripped before the token is looked for; without that,
    "Hartford Multifactor Developed Markets (ex-US) ETF" excludes itself. Or a
    ``global``/``world``/``ACWI`` token with no ``ex-US`` qualifier at all.
    """
    stripped = re.sub(patterns.ex_us_token_regex, " ", name, flags=re.IGNORECASE)
    if re.search(patterns.us_token_regex, stripped, re.IGNORECASE):
        return True
    return bool(
        re.search(patterns.global_token_regex, name, re.IGNORECASE)
        and not re.search(patterns.ex_us_token_regex, name, re.IGNORECASE)
    )


# --------------------------------------------------------------------------- #
# Product facts
# --------------------------------------------------------------------------- #


def load_product_facts(path: Path | None = None) -> dict[str, ProductFacts]:
    """Read the committed per-fund sponsor facts.

    Reuses Experiment 002's :class:`ProductFacts` unchanged so that a fee or an
    inception date means exactly the same thing in both audits. The extra fields
    this shelf needs — the index's region words, whether the ETF was converted
    from a mutual fund, whether a mandate changed — live in the same JSON file
    and are read by :func:`load_extra_facts`.
    """
    location = path or product_facts_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. The screen needs a net expense ratio and an "
            "inception date per fund, and neither is in Form N-PORT; they are read "
            "from each fund's own SEC-filed prospectus and committed with a URL "
            "and a date."
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
    """The ex-US-specific fields Experiment 002's ``ProductFacts`` has no room for."""

    ticker: str
    index_region_words: str
    stated_region: str | None
    converted_from_mutual_fund: str | None
    mandate_change_tier: int
    mandate_change_note: str
    expense_detail: str
    source_form: str

    def to_json(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "index_region_words": self.index_region_words,
            "stated_region": self.stated_region,
            "converted_from_mutual_fund": self.converted_from_mutual_fund,
            "mandate_change_tier": self.mandate_change_tier,
            "mandate_change_note": self.mandate_change_note,
            "expense_detail": self.expense_detail,
            "source_form": self.source_form,
        }


def load_extra_facts(path: Path | None = None) -> dict[str, ExtraFacts]:
    """Read the ex-US-specific half of the committed product facts."""
    location = path or product_facts_path()
    if not location.is_file():
        raise UniverseError(f"{location} is missing")
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds = payload.get("funds", {})
    out: dict[str, ExtraFacts] = {}
    for ticker, record in funds.items():
        out[str(ticker)] = ExtraFacts(
            ticker=str(ticker),
            index_region_words=str(record.get("index_region_words", "")),
            stated_region=_optional_text(record.get("stated_region")),
            converted_from_mutual_fund=_optional_text(record.get("converted_from_mutual_fund")),
            mandate_change_tier=int(record.get("mandate_change_tier", 0) or 0),
            mandate_change_note=str(record.get("index_changed_since_2019") or ""),
            expense_detail=str(record.get("expense_detail", "")),
            source_form=str(record.get("source_form", "")),
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
    extra_facts: Mapping[str, ExtraFacts],
    patterns: ScreeningPatterns,
    minimum_net_assets: float,
    maximum_expense_ratio: float,
    intended_factor_map: Mapping[str, tuple[str, int]],
) -> tuple[tuple[ScreenedExUsFund, ...], int]:
    """Apply the predeclared criteria in their fixed order to the union census."""
    region = re.compile(patterns.region_regex, re.IGNORECASE)
    factor = re.compile(patterns.factor_regex, re.IGNORECASE)
    exclusion = re.compile(patterns.exclusion_regex, re.IGNORECASE)

    series_ids = sorted(set(frame) | set(follow_up))
    screened: list[ScreenedExUsFund] = []
    matches = 0
    for series_id in series_ids:
        early, late = frame.get(series_id), follow_up.get(series_id)
        # The name in EITHER census may match. A fund renamed INTO the mandate is
        # as real as one renamed out of it, and testing only the earlier name
        # would miss every product launched after 2019 -- which is every product
        # this experiment exists to audit.
        names = [row.series_name for row in (early, late) if row is not None]
        if not any(region.search(name) and factor.search(name) for name in names):
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
        assets = [row.net_assets for row in (early, late) if row is not None]
        maximum_assets = max([value for value in assets if value is not None], default=0.0)
        fund_facts = facts.get(ticker)
        extra = extra_facts.get(ticker)
        mandate = derive_mandate(name, patterns)
        derived_region = derive_region(name, patterns)

        failed: str | None = None
        detail = ""
        if exclusion.search(name):
            failed, detail = "exclusion_regex", (
                f"series name matches the exclusion pattern: {name!r}"
            )
        elif us_overlap(name, patterns):
            failed, detail = "us_overlap", (
                f"{name!r} claims a mandate that includes the United States, so no "
                "ex-US factor panel can price it"
            )
        elif not classes:
            failed, detail = "exchange_traded", "EDGAR lists no ticker for this series"
        elif not etf_classes:
            failed, detail = "exchange_traded", (
                "no share class carries an ETF=Y flag in the current consolidated "
                f"symbol directory (classes: {[symbol for _, symbol in classes]})"
            )
        elif maximum_assets < minimum_net_assets:
            failed, detail = "minimum_net_assets", (
                f"largest observed net assets across both censuses "
                f"{maximum_assets:,.0f} USD is below {minimum_net_assets:,.0f}"
            )
        elif mandate is None or mandate not in intended_factor_map:
            failed, detail = "mandate_in_map", (
                f"name-derived mandate {mandate!r} has no entry in the predeclared "
                "intended-factor map, so there is no declared factor to grade this "
                "fund against"
            )
        elif derived_region not in GRADED_REGIONS:
            failed, detail = "region_in_map", (
                f"region {derived_region!r} spans both published ex-US factor files; "
                "grading it against either alone would be a misspecification chosen "
                "for convenience"
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
        elif extra is not None and extra.mandate_change_tier == 1:
            failed, detail = "mandate_stable", (
                "the fund's stated mandate changed inside the window, so it has no "
                f"single mandate to be graded against: {extra.mandate_change_note}"
            )

        factor_name, sign = (None, 0)
        if mandate is not None:
            factor_name, sign = intended_factor_map.get(mandate, (None, 0))

        screened.append(
            ScreenedExUsFund(
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
                in_frame_census=early is not None,
                in_follow_up_census=late is not None,
                final_filing_flag_seen=any(
                    row.is_last_filing for row in (early, late) if row is not None
                ),
                exchange_listed_now=ticker in exchange_flags,
                derived_mandate=mandate,
                derived_region=derived_region,
                intended_factor=factor_name,
                intended_sign=sign,
                facts=fund_facts,
            )
        )

    screened.sort(key=lambda fund: (-fund.net_assets_max, fund.ticker))
    return tuple(screened), matches


def attrition(
    frame: Mapping[str, FrameRow],
    follow_up: Mapping[str, FrameRow],
    patterns: ScreeningPatterns,
) -> AttritionReport:
    """Split disappearance from rename, which Experiment 002's construction does not.

    See the module docstring. The distinction is the whole point: differencing
    two name-qualified sets of identifiers counts a fund that changed its name as
    a fund that died.
    """
    region = re.compile(patterns.region_regex, re.IGNORECASE)
    factor = re.compile(patterns.factor_regex, re.IGNORECASE)
    exclusion = re.compile(patterns.exclusion_regex, re.IGNORECASE)

    def qualifies(row: FrameRow) -> bool:
        name = row.series_name
        return bool(
            region.search(name) and factor.search(name) and not exclusion.search(name)
        )

    start = {sid for sid, row in frame.items() if qualifies(row)}
    end = {sid for sid, row in follow_up.items() if qualifies(row)}

    absent = sorted(sid for sid in start if sid not in follow_up)
    renamed_out = sorted(sid for sid in start - end if sid in follow_up)
    launched = sorted(sid for sid in end if sid not in frame)
    renamed_in = sorted(sid for sid in end - start if sid in frame)

    return AttritionReport(
        qualifying_in_frame=len(start),
        qualifying_in_follow_up=len(end),
        absent_from_follow_up_census=len(absent),
        renamed_out_of_the_pattern=len(renamed_out),
        still_qualifying=len(start & end),
        launched_inside_the_window=len(launched),
        renamed_into_the_pattern=len(renamed_in),
        net_assets_of_absent_series_usd=sum(frame[sid].net_assets or 0.0 for sid in absent),
        net_assets_of_renamed_series_usd=sum(
            frame[sid].net_assets or 0.0 for sid in renamed_out
        ),
        largest_absent_series=tuple(
            {
                "series_name": frame[sid].series_name,
                "net_assets_usd": frame[sid].net_assets,
                "last_report_date": frame[sid].report_date,
            }
            for sid in sorted(absent, key=lambda s: -(frame[s].net_assets or 0.0))[:10]
        ),
        renamed_examples=tuple(
            {
                "series_name_2019": frame[sid].series_name,
                "series_name_2025": follow_up[sid].series_name,
                "net_assets_2019_usd": frame[sid].net_assets,
                "net_assets_2025_usd": follow_up[sid].net_assets,
            }
            for sid in sorted(renamed_out, key=lambda s: -(frame[s].net_assets or 0.0))[:10]
        ),
    )


# --------------------------------------------------------------------------- #
# The guard on Experiment 002
# --------------------------------------------------------------------------- #

#: Experiment 002's two screening regexes, copied here at the time this module
#: was written. They are not used to screen anything; they exist so that a change
#: to Experiment 002's frozen specification fails a test in Experiment 009 rather
#: than silently making the US and ex-US audits incomparable.
EXP_002_MANDATE_REGEX: Final = (
    r"\b(value|growth|momentum|quality|profitab\w*|min(?:imum)?\s+volatility|low\s+"
    r"volatility|multi-?factor|factor|small[- ]?cap|mid[- ]?cap)\b"
)
EXP_002_EXCLUSION_REGEX: Final = (
    r"\b(bond|municipal|treasury|credit|corporate|high yield|target|lifecycle|"
    r"retirement|esg|sustainab\w*|social|climate|clean|carbon|health|technolog\w*|"
    r"financial|energy|utilit\w*|real estate|reit|gold|commodit\w*|ultra|2x|3x|"
    r"inverse|bear|leveraged|emerging|international|intl|global|world|ex-?u\.?s|"
    r"developed|japan|china|europe|eafe|acwi|currency|hedged|balanced|allocation|"
    r"money market|convertible|preferred|option|buffer|covered call|dividend|income)\b"
)


def exp_002_screen_is_unmodified(specification_parameters: Mapping[str, object]) -> None:
    """Raise unless Experiment 002's screen is still byte-for-byte what it was.

    Experiment 009 does not change Experiment 002's screen; it complements it. So
    the honest way to report "no previously published US result changed" is to
    assert the thing that would have to change for one to.
    """
    patterns = specification_parameters.get("screening_patterns")
    if not isinstance(patterns, Mapping):
        raise UniverseError("exp_002's specification has no screening_patterns block")
    mandate = str(patterns.get("mandate_regex", "")).strip()
    exclusion = str(patterns.get("exclusion_regex", "")).strip()
    if mandate != EXP_002_MANDATE_REGEX:
        raise UniverseError(
            "Experiment 002's mandate pattern has changed since Experiment 009 was "
            "written. The two audits are no longer comparable and the published US "
            "numbers must be re-derived before this one is read beside them."
        )
    if exclusion != EXP_002_EXCLUSION_REGEX:
        raise UniverseError(
            "Experiment 002's exclusion pattern has changed since Experiment 009 was "
            "written. The two audits are no longer comparable."
        )


# --------------------------------------------------------------------------- #
# Building, writing and reading the committed universe
# --------------------------------------------------------------------------- #


def build_universe(
    *,
    cache: RawCache,
    patterns: ScreeningPatterns,
    minimum_net_assets: float,
    maximum_expense_ratio: float,
    intended_factor_map: Mapping[str, tuple[str, int]],
    facts: Mapping[str, ProductFacts] | None = None,
    extra_facts: Mapping[str, ExtraFacts] | None = None,
) -> ExUsUniverse:
    """Screen the union census and assemble the committed universe record."""
    frame, frame_entry = load_frame(cache, FRAME_QUARTER)
    follow_up, follow_entry = load_frame(cache, FOLLOW_UP_QUARTER)
    class_tickers = _load_class_tickers(cache)
    exchange_flags = _load_exchange_flags(cache)
    product_facts = dict(facts) if facts is not None else load_product_facts()
    extras = dict(extra_facts) if extra_facts is not None else load_extra_facts()

    screened, matches = screen_union_frame(
        frame=frame,
        follow_up=follow_up,
        class_tickers=class_tickers,
        exchange_flags=exchange_flags,
        facts=product_facts,
        extra_facts=extras,
        patterns=patterns,
        minimum_net_assets=minimum_net_assets,
        maximum_expense_ratio=maximum_expense_ratio,
        intended_factor_map=intended_factor_map,
    )

    return ExUsUniverse(
        schema_version=UNIVERSE_SCHEMA_VERSION,
        built_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        frame_quarter=FRAME_QUARTER,
        follow_up_quarter=FOLLOW_UP_QUARTER,
        frame_series_count=len(frame),
        follow_up_series_count=len(follow_up),
        union_series_count=len(set(frame) | set(follow_up)),
        mandate_matches=matches,
        funds=screened,
        attrition=attrition(frame, follow_up, patterns),
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
            "patterns": patterns.to_json(),
            "minimum_net_assets_usd": minimum_net_assets,
            "maximum_net_expense_ratio_percent": maximum_expense_ratio,
            "graded_regions": list(GRADED_REGIONS),
            "intended_factor_map": {
                mandate: {"factor": factor, "sign": sign}
                for mandate, (factor, sign) in sorted(intended_factor_map.items())
            },
        },
        notes=(
            "Built BEFORE any fund return was downloaded. The return tables of the "
            "data sets were never opened while screening.",
            "The frame is the UNION of the first and the most recent public census, "
            "because every product this experiment exists to audit launched after "
            "2019 and a 2019Q4-only frame would exclude them by construction.",
            "The asset floor is applied to the MAXIMUM of a series' two observed "
            "net-asset figures, so neither terminal size nor launch size selects.",
            "Every criterion evaluable from the census alone is applied before every "
            "criterion needing a sponsor document, so a gap in fact-gathering cannot "
            "masquerade as a screen decision.",
            "Mandate and region are derived MECHANICALLY from the official series "
            "name. The sponsor-stated mandate and the tracked index's region words "
            "are recorded separately and any disagreement is reported.",
            "Attrition separates funds that left the census from funds that merely "
            "renamed out of the mandate pattern. Only the first are deaths.",
            "Experiment 002's screen is NOT modified by this module. Its two regexes "
            "are asserted unchanged, so the US audit's published numbers stand.",
        ),
    )


def write_universe(universe: ExUsUniverse, path: Path | None = None) -> Path:
    location = path or universe_path()
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(
        json.dumps(universe.to_json(), indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return location


def load_universe(path: Path | None = None) -> ExUsUniverse:
    """Read the committed universe. The experiment never rebuilds it."""
    location = path or universe_path()
    if not location.is_file():
        raise UniverseError(
            f"{location} is missing. Build it with "
            "`python -m portfolio_edge.experiments.exp_009_exus_products --build-universe` "
            "BEFORE running the audit; the universe must be fixed before returns are "
            "downloaded."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    funds: list[ScreenedExUsFund] = []
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
            ScreenedExUsFund(
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
                in_frame_census=bool(record.get("in_frame_census", False)),
                in_follow_up_census=bool(record.get("in_follow_up_census", False)),
                final_filing_flag_seen=bool(record.get("final_filing_flag_seen", False)),
                exchange_listed_now=bool(record.get("exchange_listed_now", False)),
                derived_mandate=_optional_text(record.get("derived_mandate")),
                derived_region=_optional_text(record.get("derived_region")),
                intended_factor=_optional_text(record.get("intended_factor")),
                intended_sign=int(record.get("intended_sign", 0) or 0),
                facts=facts,
            )
        )
    raw_attrition = payload.get("attrition", {})
    report = AttritionReport(
        qualifying_in_frame=int(raw_attrition.get("qualifying_in_frame", 0)),
        qualifying_in_follow_up=int(raw_attrition.get("qualifying_in_follow_up", 0)),
        absent_from_follow_up_census=int(raw_attrition.get("absent_from_follow_up_census", 0)),
        renamed_out_of_the_pattern=int(raw_attrition.get("renamed_out_of_the_pattern", 0)),
        still_qualifying=int(raw_attrition.get("still_qualifying", 0)),
        launched_inside_the_window=int(raw_attrition.get("launched_inside_the_window", 0)),
        renamed_into_the_pattern=int(raw_attrition.get("renamed_into_the_pattern", 0)),
        net_assets_of_absent_series_usd=float(
            raw_attrition.get("net_assets_of_absent_series_usd", 0.0)
        ),
        net_assets_of_renamed_series_usd=float(
            raw_attrition.get("net_assets_of_renamed_series_usd", 0.0)
        ),
        largest_absent_series=tuple(raw_attrition.get("largest_absent_series", [])),
        renamed_examples=tuple(raw_attrition.get("renamed_examples", [])),
    )
    return ExUsUniverse(
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
    return tuple(frame_manifest(cache, quarter) for quarter in (FRAME_QUARTER, FOLLOW_UP_QUARTER))
