"""Experiment 012: the trend leg rebuilt from live fund returns instead of a vendor index.

Why this exists
---------------
:mod:`portfolio_edge.experiments.exp_011_overlay_stack` returned ``unresolved`` for one
reason, and it was not arithmetic. Its trend leg is AQR's published TSMOM series: an
author-maintained workbook, reconstructed in full on every update, by a firm that sells
the strategy, stating **no fee, transaction-cost, slippage, roll-cost or financing basis
anywhere**. Its measured pre- to post-publication decay of 12.11 pp/yr exceeds the
9.57 pp/yr haircut at which the overlay stops paying, so no further analysis *of that
series* can settle the question.

This experiment replaces it with what investors actually received. Form N-PORT Item B.5
carries each fund's own monthly total return per share class, **net of the fund's own
ongoing fees and with distributions reinvested**, on a signed filing the SEC archives
permanently. :mod:`portfolio_edge.data.nport` already reads it and Experiment 008 already
used it for five exchange-traded funds. Here the screen is run over the whole mandate
census — mutual funds included, dead funds included — and the surviving series are
combined into an equal-weight monthly index.

What that fixes, and what it does not
-------------------------------------
Fixed:

* **Fees are inside the number.** The trend leg carries a zero modelled fee here, because
  charging one would double-count what Item B.5 already deducted. Experiment 011 charged
  1.45%/yr to a series that had never paid one.
* **Trading costs, slippage and roll are inside the number**, because a fund's reported
  total return is what its net asset value actually did.
* **Backfill is impossible.** A fund's filings begin when it begins filing. Nothing is
  reconstructed backwards and no vintage is rewritten.
* **Deaths are retained.** A fund that stopped filing inside the window contributes up to
  the month it stopped, which is the property a CTA peer-group index does not have.

Not fixed, and each is stated on every figure:

* **Public N-PORT filings begin in 2019.** Any managed-futures fund that closed before
  2019Q4 is invisible to both censuses, so every attrition figure is a **lower bound**.
* **A fund that both launched after 2019Q4 and closed before 2025Q4 is in neither
  census**, so it is missing from the index entirely. That is a survivorship hole *inside*
  the window and it flatters the index. Closing it needs the intermediate quarterly
  censuses, which this experiment does not read.
* **Item B.5 is unaudited**, and Form N-PORT General Instruction G lets each filer use its
  own internal methodology, so two funds' returns are not guaranteed comparable. The
  repository's cross-source check returned an HTTP error for all 44 US and all 25 ex-US
  tickers, so **Item B.5 is the sole measurement**.
* **The window is about 78 months.** That is the binding constraint on the overlay
  comparison and it is reported as a minimum detectable effect beside every gap.

Run it::

    uv run python -m portfolio_edge.experiments.exp_012_live_trend --build-census
    uv run python -m portfolio_edge.experiments.exp_012_live_trend --view-results
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.data import french, nport
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_008_universe import FOLLOW_UP_QUARTER, FRAME_QUARTER
from portfolio_edge.experiments.exp_011_overlay_stack import (
    MONTHS_PER_YEAR,
    CostModel,
    MatchedVolatilityComparison,
    Panel,
    PortfolioSummary,
    break_even_haircut,
    haircut_sweep,
    matched_volatility_comparison,
    require_one_benchmark,
    simulate_portfolio,
    sleeve_moments,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_index, period_from_index
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.runner import RunOutcome, run_experiment
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
)
from portfolio_edge.inference.hac import hac_mean, hac_ols

__all__ = [
    "CENSUS_SCHEMA_VERSION",
    "ENTRY_POINT",
    "FundReturns",
    "LiveIndex",
    "LiveTrendError",
    "ScreenedSeries",
    "VendorComparison",
    "build_census",
    "build_live_index",
    "build_panel",
    "build_registry",
    "census_path",
    "default_specification_path",
    "fetch_fund_returns",
    "load_census",
    "main",
    "robustness_arms",
    "run",
    "screen_census",
    "vendor_comparison",
    "write_census",
]

ENTRY_POINT: Final = "exp_012_live_trend"

CENSUS_SCHEMA_VERSION: Final = "1"

FloatArray = NDArray[np.float64]

#: A filing reaches EDGAR within about 60 days of its reporting period end and reports
#: the three months ending on it, so nothing filed more than eight months after the
#: window closes can contain a month inside it. Filings past that are never downloaded,
#: which makes the holdout a property of the code rather than a promise.
_HELD_OUT_FILING_MONTHS: Final = 8


class LiveTrendError(RuntimeError):
    """The experiment could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to the frozen specification
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise LiveTrendError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise LiveTrendError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise LiveTrendError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LiveTrendError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise LiveTrendError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _numbers(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[float, ...]:
    out: list[float] = []
    for item in _sequence(_at(data, key, where=where), where=f"{where}.{key}"):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise LiveTrendError(f"{where}.{key} must hold numbers, got {item!r}")
        out.append(float(item))
    return tuple(out)


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_012_live_trend.yaml"


def census_path() -> Path:
    return workspace_root() / "data-manifests" / "exp_012" / "live_trend_census.json"


# --------------------------------------------------------------------------- #
# The census
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class ScreenedSeries:
    """One mandate-matching fund series and why it is in or out.

    A failing series is kept in full. The screen's denominator is the whole census,
    and a screen whose rejections are not written down cannot supply one.
    """

    series_id: str
    series_name: str
    admitted: bool
    rejected_by: str
    """``""``, ``"exclusion_pattern"``, or ``"not_a_futures_programme"``."""
    reason: str
    in_frame_quarter: bool
    in_follow_up_quarter: bool
    net_assets_frame: float | None
    net_assets_follow_up: float | None
    net_assets_maximum: float | None

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "series_id": self.series_id,
            "series_name": self.series_name,
            "admitted": self.admitted,
            "rejected_by": self.rejected_by,
            "reason": self.reason,
            "in_frame_quarter": self.in_frame_quarter,
            "in_follow_up_quarter": self.in_follow_up_quarter,
            "net_assets_frame_usd": self.net_assets_frame,
            "net_assets_follow_up_usd": self.net_assets_follow_up,
            "net_assets_maximum_usd": self.net_assets_maximum,
        }


def screen_census(
    *,
    frame: Mapping[str, nport.FrameRow],
    follow_up: Mapping[str, nport.FrameRow],
    mandate_pattern: str,
    exclusion_pattern: str,
    not_a_futures_programme: Mapping[str, str],
) -> tuple[ScreenedSeries, ...]:
    """Screen the union census for a diversified futures mandate, on names alone.

    The mandate and exclusion patterns are Experiment 008's, reused verbatim rather
    than re-derived, because they were frozen before any fund return was downloaded
    and rewriting them here after seeing 008's results would launder that provenance.

    ``not_a_futures_programme`` is the one place judgement enters, and it enters by
    name with a written reason per series. It exists because the mandate pattern
    matches on the word "trend", which a 1958 US large-cap growth mutual fund also
    carries, and because a single-asset trend product is not a diversified futures
    programme. Every entry is a statement about a fund's mandate that can be checked
    against its prospectus; **none of them was made after looking at a return.**
    """
    mandate = re.compile(mandate_pattern, re.IGNORECASE)
    exclusion = re.compile(exclusion_pattern, re.IGNORECASE)

    union: dict[str, nport.FrameRow] = dict(follow_up)
    for series_id, row in frame.items():
        union.setdefault(series_id, row)

    screened: list[ScreenedSeries] = []
    for series_id in sorted(union):
        row = follow_up.get(series_id) or frame[series_id]
        if not mandate.search(row.series_name):
            continue
        first, last = frame.get(series_id), follow_up.get(series_id)
        observed = [
            item.net_assets for item in (first, last) if item is not None and item.net_assets
        ]
        rejected_by, reason = "", ""
        if exclusion.search(row.series_name):
            rejected_by = "exclusion_pattern"
            reason = f"series name matches the frozen exclusion pattern: {row.series_name!r}"
        elif series_id in not_a_futures_programme:
            rejected_by = "not_a_futures_programme"
            reason = not_a_futures_programme[series_id]
        screened.append(
            ScreenedSeries(
                series_id=series_id,
                series_name=row.series_name,
                admitted=not rejected_by,
                rejected_by=rejected_by,
                reason=reason,
                in_frame_quarter=first is not None,
                in_follow_up_quarter=last is not None,
                net_assets_frame=None if first is None else first.net_assets,
                net_assets_follow_up=None if last is None else last.net_assets,
                net_assets_maximum=max(observed) if observed else None,
            )
        )
    return tuple(screened)


def build_census(
    cache: RawCache,
    *,
    mandate_pattern: str,
    exclusion_pattern: str,
    not_a_futures_programme: Mapping[str, str],
) -> dict[str, JsonValue]:
    """Screen both censuses and assemble the record that gets committed."""
    frame, frame_entry = nport.load_frame(cache, FRAME_QUARTER)
    follow_up, follow_entry = nport.load_frame(cache, FOLLOW_UP_QUARTER)
    screened = screen_census(
        frame=frame,
        follow_up=follow_up,
        mandate_pattern=mandate_pattern,
        exclusion_pattern=exclusion_pattern,
        not_a_futures_programme=not_a_futures_programme,
    )
    return {
        "schema_version": CENSUS_SCHEMA_VERSION,
        "built_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frame_quarter": FRAME_QUARTER,
        "follow_up_quarter": FOLLOW_UP_QUARTER,
        "frame_series_count": len(frame),
        "follow_up_series_count": len(follow_up),
        "union_series_count": len(set(frame) | set(follow_up)),
        "mandate_matches": len(screened),
        "admitted": sum(1 for item in screened if item.admitted),
        "inputs": {
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
            "mandate_pattern": mandate_pattern,
            "exclusion_pattern": exclusion_pattern,
            "not_a_futures_programme": dict(not_a_futures_programme),
        },
        "notes": [
            "Screened on SERIES NAMES ONLY. No Item B.5 return was read while screening.",
            "The mandate and exclusion patterns are Experiment 008's, reused verbatim.",
            "The frame is the UNION of the first and the most recent public census. A "
            "fund that closed before 2019Q4 is invisible to both, and a fund that both "
            "launched after 2019Q4 and closed before 2025Q4 is in NEITHER. Every "
            "attrition figure derived from this census is a LOWER BOUND.",
            "Exchange listing, an asset floor, an expense-ratio cap and an inception "
            "cutoff are DELIBERATELY NOT applied. Experiment 008 audited a shelf an "
            "investor could buy; this census measures what the mandate earned, so "
            "screening it down to the survivors of a size test would reintroduce "
            "exactly the selection the exercise exists to remove.",
        ],
        "series": [item.to_json() for item in screened],
    }


def write_census(payload: Mapping[str, JsonValue], path: Path | None = None) -> Path:
    location = path or census_path()
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return location


def load_census(path: Path | None = None) -> tuple[ScreenedSeries, ...]:
    """Read the committed census. The experiment never rebuilds it mid-run."""
    location = path or census_path()
    if not location.is_file():
        raise LiveTrendError(
            f"{location} is missing. Build it with `python -m "
            "portfolio_edge.experiments.exp_012_live_trend --build-census` BEFORE "
            "running the experiment; the census must be fixed before returns are read."
        )
    payload = json.loads(location.read_text(encoding="utf-8"))
    return tuple(
        ScreenedSeries(
            series_id=str(row["series_id"]),
            series_name=str(row["series_name"]),
            admitted=bool(row["admitted"]),
            rejected_by=str(row.get("rejected_by", "")),
            reason=str(row.get("reason", "")),
            in_frame_quarter=bool(row.get("in_frame_quarter", False)),
            in_follow_up_quarter=bool(row.get("in_follow_up_quarter", False)),
            net_assets_frame=_optional_float(row.get("net_assets_frame_usd")),
            net_assets_follow_up=_optional_float(row.get("net_assets_follow_up_usd")),
            net_assets_maximum=_optional_float(row.get("net_assets_maximum_usd")),
        )
        for row in payload.get("series", [])
    )


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


# --------------------------------------------------------------------------- #
# One fund's filed returns
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FundReturns:
    """One fund's filed monthly total returns, averaged across its share classes.

    Share classes of one fund hold the same portfolio and differ essentially only by
    fee, so the equal-weight mean across classes is the fund's return at the average
    of the fee levels it offers. Taking the best class would be selection on an
    outcome and taking the first would be selection on an alphabetical accident;
    ``class_dispersion`` records how much the choice could possibly matter.
    """

    series_id: str
    series_name: str
    class_ids: tuple[str, ...]
    returns: Mapping[str, float]
    """``{YYYY-MM: total return}``, decimal, net of the fund's own fees."""
    filing_count: int
    amendment_count: int
    is_final_filing_seen: bool
    class_dispersion: float
    """Mean across months of (max - min) across classes, annualised, in decimal."""
    warnings: tuple[str, ...]

    @property
    def periods(self) -> tuple[str, ...]:
        return tuple(sorted(self.returns))


def fetch_fund_returns(
    cache: RawCache, *, series_id: str, series_name: str, start: str, end: str
) -> FundReturns:
    """Assemble one series' Item B.5 history across every filing, all classes."""
    holdout_cutoff = period_from_index(month_index(end) + _HELD_OUT_FILING_MONTHS)
    filings: list[nport.NportFiling] = []
    for ref in nport.filing_index(cache, series_id):
        if not ref.form_type.startswith("NPORT-P"):
            continue
        if ref.filing_date[:7] > holdout_cutoff:
            continue
        filings.append(nport.fetch_filing(cache, ref))
        nport.throttle()
    if not filings:
        raise LiveTrendError(f"{series_id}: EDGAR lists no NPORT-P filing inside the window")

    class_ids = sorted(
        {item.class_id for f in filings for item in f.class_returns if item.class_id}
    )
    by_month: dict[str, list[float]] = {}
    warnings: list[str] = []
    for class_id in class_ids:
        table = nport.build_return_table(
            filings, class_id=class_id, table_id=f"nport_{series_id}_{class_id}"
        )
        warnings.extend(table.warnings)
        for period, row in zip(table.periods, table.values, strict=True):
            value = row[0]
            if value is not None and start <= period <= end:
                by_month.setdefault(period, []).append(float(value))

    spreads = [max(v) - min(v) for v in by_month.values() if len(v) > 1]
    return FundReturns(
        series_id=series_id,
        series_name=series_name,
        class_ids=tuple(class_ids),
        returns={period: float(np.mean(v)) for period, v in by_month.items()},
        filing_count=len(filings),
        amendment_count=sum(1 for item in filings if item.form_type.endswith("/A")),
        is_final_filing_seen=any(item.is_final_filing for item in filings),
        class_dispersion=float(np.mean(spreads)) * MONTHS_PER_YEAR if spreads else 0.0,
        warnings=tuple(warnings[:8]),
    )


# --------------------------------------------------------------------------- #
# The live index
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class LiveIndex:
    """An equal-weight monthly index of live, net, fund-reported total returns.

    Equal weight across **the funds that filed a return for that month**, so a fund
    that died contributes until it died and a fund that launched contributes from
    launch. Nothing is backfilled and no fund is dropped for dying, which is the
    property that distinguishes this from a CTA peer-group index.
    """

    periods: tuple[str, ...]
    total_return: FloatArray
    fund_count: tuple[int, ...]
    funds: tuple[FundReturns, ...]

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "window": f"{self.periods[0]}..{self.periods[-1]}",
            "months": len(self.periods),
            "funds_contributing": len(self.funds),
            "fund_count_by_month": {
                period: count for period, count in zip(self.periods, self.fund_count, strict=True)
            },
            "minimum_funds_in_any_month": min(self.fund_count),
            "maximum_funds_in_any_month": max(self.fund_count),
        }


def build_live_index(
    funds: Sequence[FundReturns], *, start: str, end: str, minimum_funds: int
) -> LiveIndex:
    """Equal-weight the funds reporting in each month of ``start..end``.

    ``minimum_funds`` truncates both ends of the window rather than filtering the
    middle: the first and last months of an N-PORT window are thin because filers'
    fiscal quarters differ, and an index month resting on three funds is a different
    statistic from one resting on thirty.
    """
    wanted = [
        period_from_index(index) for index in range(month_index(start), month_index(end) + 1)
    ]
    rows = [
        (period, [f.returns[period] for f in funds if period in f.returns]) for period in wanted
    ]
    kept = [(period, values) for period, values in rows if len(values) >= minimum_funds]
    if not kept:
        raise LiveTrendError(
            f"no month in {start}..{end} has {minimum_funds} funds reporting; the index "
            "cannot be formed"
        )
    # Truncate to the contiguous run: a hole in the middle would silently splice two
    # different fund populations into one series.
    first, last = kept[0][0], kept[-1][0]
    span = [
        period_from_index(index) for index in range(month_index(first), month_index(last) + 1)
    ]
    lookup = dict(kept)
    missing = [period for period in span if period not in lookup]
    if missing:
        raise LiveTrendError(
            f"months {missing[:6]} inside {first}..{last} fall below {minimum_funds} "
            "reporting funds, so the index would splice two fund populations"
        )
    contributing = tuple(f for f in funds if any(period in f.returns for period in span))
    return LiveIndex(
        periods=tuple(span),
        total_return=np.array([float(np.mean(lookup[period])) for period in span]),
        fund_count=tuple(len(lookup[period]) for period in span),
        funds=contributing,
    )


# --------------------------------------------------------------------------- #
# The panel
# --------------------------------------------------------------------------- #


def build_panel(
    index: LiveIndex, *, market: Mapping[str, float], cash: Mapping[str, float]
) -> Panel:
    """A two-sleeve :class:`Panel`: US equity and the live trend index, excess of cash.

    The live index is a **total** return, so cash is subtracted once, here, to put it
    on the same basis as French's ``Mkt-RF``. Managed-futures funds hold their margin
    in bills, so the subtraction removes the collateral yield and leaves the strategy
    return; leaving it in would credit the sleeve with a cash rate the base portfolio
    already earns.
    """
    periods = tuple(p for p in index.periods if p in market and p in cash)
    if not periods:
        raise LiveTrendError("the live index and the market factor share no month")
    lookup = dict(zip(index.periods, index.total_return, strict=True))
    excess = np.array(
        [[market[p], lookup[p] - cash[p]] for p in periods], dtype=np.float64
    )
    return Panel(
        periods=periods,
        sleeves=("equity", "trend"),
        excess=excess,
        cash=np.array([cash[p] for p in periods], dtype=np.float64),
        provenance=(),
        findings=(
            f"the live trend leg is an equal-weight index of {len(index.funds)} "
            "fund-reported Item B.5 monthly total returns, net of each fund's own fees, "
            f"over {periods[0]}..{periods[-1]}",
        ),
    )


# --------------------------------------------------------------------------- #
# The decisive comparison
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class VendorComparison:
    """What the vendor series earned that the funds did not, over the same months.

    ``alpha`` is the intercept of the vendor series regressed on the live one, which
    is the vendor's excess **at matched exposure to the live funds**. It is the
    quantity that would be the survivorship-plus-backfill-plus-cost gap if it were
    positive; reporting it with its interval is the point of this experiment, and the
    interval is wide enough that reporting the point estimate alone would mislead.
    """

    months: int
    alpha: float
    alpha_standard_error: float
    beta: float
    beta_standard_error: float
    r_squared: float
    residual_volatility: float
    hac_lags: int
    mean_difference: float
    mean_difference_interval: tuple[float, float]
    volatility_matched_difference: float
    volatility_matched_interval: tuple[float, float]
    live_moments: Mapping[str, float]
    vendor_moments: Mapping[str, float]
    correlation: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "months": self.months,
            "alpha_percent_per_year": self.alpha * 100.0,
            "alpha_standard_error_percent_per_year": self.alpha_standard_error * 100.0,
            "beta_on_the_live_index": self.beta,
            "beta_standard_error": self.beta_standard_error,
            "r_squared": self.r_squared,
            "residual_volatility_percent_per_year": self.residual_volatility * 100.0,
            "newey_west_lags": self.hac_lags,
            "mean_difference_vendor_less_live_pp_per_year": self.mean_difference * 100.0,
            "mean_difference_interval": [x * 100.0 for x in self.mean_difference_interval],
            "volatility_matched_difference_pp_per_year": (
                self.volatility_matched_difference * 100.0
            ),
            "volatility_matched_interval": [
                x * 100.0 for x in self.volatility_matched_interval
            ],
            "live": dict(self.live_moments),
            "vendor": dict(self.vendor_moments),
            "correlation": self.correlation,
        }


def _annualised_mean(x: FloatArray) -> float:
    return float(np.mean(x)) * MONTHS_PER_YEAR


def _annualised_volatility(x: FloatArray) -> float:
    return float(np.std(x, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)


def _moments(x: FloatArray) -> dict[str, float]:
    mean, volatility = _annualised_mean(x), _annualised_volatility(x)
    return {
        "arithmetic_excess_return": mean,
        "volatility": volatility,
        "sharpe": mean / volatility,
    }


def vendor_comparison(live: FloatArray, vendor: FloatArray) -> VendorComparison:
    """Regress the vendor series on the live one and report both differences.

    Two differences, because they answer different questions and a single number
    would conflate them. The **raw** difference is what the two series paid over the
    same months at whatever exposure each ran; the **volatility-matched** difference
    removes the exposure gap, which is large here because the funds run at a lower
    volatility than the vendor's 40%-per-position target implies.
    """
    if live.size != vendor.size:
        raise LiveTrendError(
            f"the live index has {live.size} months and the vendor series {vendor.size}"
        )
    fit = hac_ols(vendor, live[:, None])
    residual_sum = float(np.sum(fit.residuals**2))
    total_sum = float(np.sum((vendor - float(np.mean(vendor))) ** 2))

    difference = vendor - live
    raw = hac_mean(difference)
    scale = float(np.std(vendor, ddof=1)) / float(np.std(live, ddof=1))
    matched = hac_mean(vendor - scale * live)
    return VendorComparison(
        months=int(live.size),
        alpha=float(fit.coefficients[0]) * MONTHS_PER_YEAR,
        alpha_standard_error=float(fit.standard_errors[0]) * MONTHS_PER_YEAR,
        beta=float(fit.coefficients[1]),
        beta_standard_error=float(fit.standard_errors[1]),
        r_squared=1.0 - residual_sum / total_sum,
        residual_volatility=_annualised_volatility(np.asarray(fit.residuals, dtype=np.float64)),
        hac_lags=fit.n_lags,
        mean_difference=_annualised_mean(difference),
        mean_difference_interval=(
            (raw.mean - 1.96 * raw.standard_error) * MONTHS_PER_YEAR,
            (raw.mean + 1.96 * raw.standard_error) * MONTHS_PER_YEAR,
        ),
        volatility_matched_difference=_annualised_mean(vendor - scale * live),
        volatility_matched_interval=(
            (matched.mean - 1.96 * matched.standard_error) * MONTHS_PER_YEAR,
            (matched.mean + 1.96 * matched.standard_error) * MONTHS_PER_YEAR,
        ),
        live_moments=_moments(live),
        vendor_moments=_moments(vendor),
        correlation=float(np.corrcoef(live, vendor)[0, 1]),
    )


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class _Settings:
    portfolios: tuple[tuple[str, tuple[float, ...], str], ...]
    costs: CostModel
    haircut_grid: tuple[float, ...]
    haircut_portfolio: str
    minimum_funds: int
    robustness_minimum_net_assets: float
    materiality: float
    primary_benchmark: str
    secondary_benchmark: str
    resamples: int
    confidence_level: float
    not_a_futures_programme: Mapping[str, str]
    mandate_pattern: str
    exclusion_pattern: str


def _read_settings(specification: Specification) -> _Settings:
    parameters = _mapping(specification.parameters, where="parameters")
    cost_model = _mapping(specification.cost_model, where="cost_model")
    fees_raw = _mapping(
        _at(cost_model, "sleeve_fee_annual_percent", where="cost_model"),
        where="cost_model.sleeve_fee_annual_percent",
    )
    fees: dict[str, float] = {}
    for sleeve, value in fees_raw.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise LiveTrendError(f"cost_model fee for {sleeve!r} must be a number")
        fees[sleeve] = float(value) / 100.0
    if fees.get("trend", 0.0) != 0.0:
        raise LiveTrendError(
            "the trend leg's modelled fee must be zero. Item B.5 returns are already net "
            "of the fund's own ongoing fees, so charging one here would deduct it twice. "
            "This is not a conservatism to be tuned; it is the arithmetic."
        )
    costs = CostModel(
        sleeve_fee=fees,
        borrow_spread=_number(cost_model, "borrow_spread_annual_percent", where="cost_model")
        / 100.0,
    )

    portfolios: list[tuple[str, tuple[float, ...], str]] = []
    for item in _sequence(_at(parameters, "portfolios", where="parameters"), where="portfolios"):
        entry = _mapping(item, where="parameters.portfolios[]")
        portfolios.append(
            (
                _text(entry, "name", where="portfolios[]"),
                _numbers(entry, "weights", where="portfolios[]"),
                _text(entry, "role", where="portfolios[]"),
            )
        )

    sweep = _mapping(_at(parameters, "haircut_sweep", where="parameters"), where="haircut_sweep")
    start = _number(sweep, "start_percent_per_year", where="haircut_sweep") / 100.0
    stop = _number(sweep, "stop_percent_per_year", where="haircut_sweep") / 100.0
    step = _number(sweep, "step_percent_per_year", where="haircut_sweep") / 100.0
    if step <= 0.0 or stop < start:
        raise LiveTrendError("the haircut sweep grid is empty or has a non-positive step")
    grid = tuple(start + step * i for i in range(round((stop - start) / step) + 1))

    screen = _mapping(_at(parameters, "screen", where="parameters"), where="parameters.screen")
    exclusions_raw = _mapping(
        _at(screen, "not_a_futures_programme", where="screen"), where="not_a_futures_programme"
    )
    benchmark = _mapping(specification.benchmark, where="benchmark")
    return _Settings(
        portfolios=tuple(portfolios),
        costs=costs,
        haircut_grid=grid,
        haircut_portfolio=_text(sweep, "portfolio", where="haircut_sweep"),
        minimum_funds=int(_number(parameters, "minimum_funds_per_month", where="parameters")),
        robustness_minimum_net_assets=_number(
            _mapping(_at(parameters, "robustness_arms", where="parameters"), where="arms"),
            "largest_funds_minimum_net_assets_usd",
            where="robustness_arms",
        ),
        materiality=_number(parameters, "materiality_threshold_annual_percent", where="parameters")
        / 100.0,
        primary_benchmark=_text(
            _mapping(_at(benchmark, "primary", where="benchmark"), where="benchmark.primary"),
            "id",
            where="benchmark.primary",
        ),
        secondary_benchmark=_text(
            _mapping(_at(benchmark, "secondary", where="benchmark"), where="benchmark.secondary"),
            "id",
            where="benchmark.secondary",
        ),
        resamples=specification.inference.resamples,
        confidence_level=specification.inference.confidence_level,
        not_a_futures_programme={k: str(v) for k, v in exclusions_raw.items()},
        mandate_pattern=_text(screen, "mandate_pattern", where="screen"),
        exclusion_pattern=_text(screen, "exclusion_pattern", where="screen"),
    )


def _load_market(specification: Specification, cache: RawCache) -> tuple[
    dict[str, float], dict[str, float], dict[str, float], dict[str, JsonValue]
]:
    """Ken French ``Mkt-RF`` and ``RF``, hash-pinned, plus the AQR vendor series."""
    from portfolio_edge.data import aqr

    parameters = _mapping(specification.parameters, where="parameters")
    pins = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")

    french_pin = _mapping(_at(pins, "french", where="source_pin"), where="source_pin.french")
    dataset = french.get_dataset(_text(french_pin, "dataset_id", where="french"))
    entry = french.download(cache, dataset)
    expected = _text(french_pin, "expected_sha256_raw", where="french")
    if entry.sha256 != expected:
        raise LiveTrendError(
            f"{dataset.url} now hashes to {entry.sha256} but this specification is frozen "
            f"against {expected}. Ken French rebuilds from each CRSP vintage, so this is a "
            "NEW VINTAGE rather than a corrupted download. Freeze a new specification."
        )
    table = french.parse(cache, entry, dataset=dataset).table("monthly")
    market = {
        p: float(v)
        for p, v in zip(table.periods, table.column("Mkt-RF"), strict=True)
        if v is not None
    }
    cash = {
        p: float(v)
        for p, v in zip(table.periods, table.column("RF"), strict=True)
        if v is not None
    }

    aqr_pin = _mapping(_at(pins, "aqr", where="source_pin"), where="source_pin.aqr")
    aqr_dataset = aqr.get_dataset(_text(aqr_pin, "dataset_id", where="aqr"))
    aqr_entry = aqr.download(cache, aqr_dataset)
    aqr_expected = _text(aqr_pin, "expected_sha256_raw", where="aqr")
    if aqr_entry.sha256 != aqr_expected:
        raise LiveTrendError(
            f"{aqr_dataset.url} now hashes to {aqr_entry.sha256} but this specification is "
            f"frozen against {aqr_expected}. AQR reconstructs its full history on every "
            "update, so this is a NEW VINTAGE. Freeze a new specification."
        )
    aqr_table = aqr.parse(cache, aqr_entry, dataset=aqr_dataset).table
    vendor = {
        p: float(v)
        for p, v in zip(aqr_table.periods, aqr_table.column("TSMOM"), strict=True)
        if v is not None
    }
    provenance: dict[str, JsonValue] = {
        "french": {
            "url": dataset.url,
            "sha256_raw": entry.sha256,
            "retrieved_utc": entry.retrieved_utc,
            "parser_version": french.PARSER_VERSION,
        },
        "aqr_tsmom": {
            "url": aqr_dataset.url,
            "sha256_raw": aqr_entry.sha256,
            "retrieved_utc": aqr_entry.retrieved_utc,
            "parser_version": aqr.PARSER_VERSION,
        },
    }
    return market, cash, vendor, provenance


def robustness_arms(
    funds: Sequence[FundReturns],
    census: Sequence[ScreenedSeries],
    *,
    periods: Sequence[str],
    market: Mapping[str, float],
    cash: Mapping[str, float],
    vendor: Mapping[str, float],
    minimum_funds: int,
    minimum_net_assets: float,
) -> list[dict[str, JsonValue]]:
    """Rebuild the index on three declared subsets and report what moves.

    Each subset is defined by something in the committed census -- the sponsor's name
    or the filed net assets -- or by a fund's own filing coverage. None of them is
    defined by a return, so none is a screen on an outcome.

    The first arm is the one that matters. AQR authors the vendor series this
    experiment is measuring against and also runs several of the funds in the index,
    so the comparison is not fully independent while they are in it.
    """
    assets = {item.series_id: item.net_assets_maximum or 0.0 for item in census}
    subsets: list[tuple[str, str, list[FundReturns]]] = [
        (
            "excluding_the_vendors_own_funds",
            "every fund whose series name carries the name of the firm that authors the "
            "comparator series is dropped, because the comparison is not independent "
            "while they are in it",
            [f for f in funds if "aqr" not in f.series_name.lower()],
        ),
        (
            "funds_filing_every_month",
            "the balanced panel. It is a SURVIVORSHIP SCREEN and is reported only to "
            "show how much the entry and exit of funds moves the index",
            [f for f in funds if all(period in f.returns for period in periods)],
        ),
        (
            "largest_funds_only",
            f"funds whose larger observed net assets across the two censuses reached "
            f"${minimum_net_assets / 1e6:,.0f}m. Also a selection on survival, and "
            "reported for the same reason",
            [f for f in funds if assets.get(f.series_id, 0.0) >= minimum_net_assets],
        ),
    ]
    out: list[dict[str, JsonValue]] = []
    for name, note, subset in subsets:
        if len(subset) < minimum_funds:
            out.append({"arm": name, "note": note, "funds": len(subset), "usable": False})
            continue
        index = build_live_index(
            subset, start=periods[0], end=periods[-1], minimum_funds=minimum_funds
        )
        panel = build_panel(index, market=market, cash=cash)
        live = panel.column("trend")
        vendor_leg = np.array([vendor[p] for p in panel.periods], dtype=np.float64)
        moments = _moments(live)
        out.append(
            {
                "arm": name,
                "note": note,
                "funds": len(subset),
                "usable": True,
                "months": panel.months,
                "window": f"{panel.periods[0]}..{panel.periods[-1]}",
                "arithmetic_excess_return": moments["arithmetic_excess_return"],
                "volatility": moments["volatility"],
                "sharpe": moments["sharpe"],
                "correlation_with_equity": float(
                    np.corrcoef(live, panel.column("equity"))[0, 1]
                ),
                "vendor_less_live_at_matched_volatility": vendor_comparison(
                    live, vendor_leg
                ).volatility_matched_difference,
            }
        )
    return out


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 012 against the committed census and the pinned sources."""
    settings = _read_settings(specification)
    census = load_census()
    admitted = [item for item in census if item.admitted]
    if not admitted:
        raise LiveTrendError("the committed census admits no series")

    cache = RawCache()
    start, end = specification.sample_policy.start, specification.sample_policy.end
    market, cash, vendor, provenance = _load_market(specification, cache)

    funds: list[FundReturns] = []
    failures: list[dict[str, JsonValue]] = []
    for item in admitted:
        try:
            funds.append(
                fetch_fund_returns(
                    cache,
                    series_id=item.series_id,
                    series_name=item.series_name,
                    start=start,
                    end=end,
                )
            )
        except Exception as exc:  # recorded below, never silently dropped
            failures.append(
                {
                    "series_id": item.series_id,
                    "series_name": item.series_name,
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )
    index = build_live_index(
        funds, start=start, end=end, minimum_funds=settings.minimum_funds
    )
    panel = build_panel(index, market=market, cash=cash)

    missing_vendor = [p for p in panel.periods if p not in vendor]
    if missing_vendor:
        raise LiveTrendError(
            f"the vendor series has no observation for {missing_vendor[:6]}, so the two "
            "cannot be compared over the same months"
        )
    comparison = vendor_comparison(
        panel.column("trend"),
        np.array([vendor[p] for p in panel.periods], dtype=np.float64),
    )

    portfolios = {
        name: simulate_portfolio(
            panel,
            name=name,
            sleeves=("equity", "trend"),
            weights=weights,
            costs=settings.costs,
        )
        for name, weights, _role in settings.portfolios
    }
    controls = tuple(name for name, _w, role in settings.portfolios if "control" in role)
    candidates = tuple(name for name in portfolios if name not in controls)

    comparisons: dict[str, tuple[MatchedVolatilityComparison, ...]] = {}
    for benchmark_name in (settings.primary_benchmark, settings.secondary_benchmark):
        rows = tuple(
            matched_volatility_comparison(
                portfolios[name],
                portfolios[benchmark_name],
                rng=context.rng,
                resamples=settings.resamples,
                mean_block_length=12.0,
                confidence_level=settings.confidence_level,
            )
            for name in candidates
        )
        require_one_benchmark(rows)
        comparisons[benchmark_name] = rows

    headline = settings.haircut_portfolio
    headline_weights = next(w for n, w, _r in settings.portfolios if n == headline)
    sweeps: dict[str, list[dict[str, float]]] = {}
    break_evens: dict[str, float | None] = {}
    for benchmark_name in (settings.primary_benchmark, settings.secondary_benchmark):
        points = haircut_sweep(
            panel,
            sleeve="trend",
            portfolio_sleeves=("equity", "trend"),
            weights=headline_weights,
            benchmark=portfolios[benchmark_name],
            costs=settings.costs,
            grid=settings.haircut_grid,
            name=headline,
        )
        sweeps[benchmark_name] = [
            {
                "haircut": point.haircut,
                "gap": point.gap,
                "geometric_return": point.geometric_return,
                "sharpe": point.sharpe,
            }
            for point in points
        ]
        break_evens[benchmark_name] = break_even_haircut(points)

    headline_row = next(
        row for row in comparisons[settings.primary_benchmark] if row.portfolio == headline
    )
    status, verdict = _decide(
        headline=headline_row,
        levered_beats=any(
            portfolios[name].sharpe >= portfolios[headline].sharpe
            for name, _w, role in settings.portfolios
            if "leverage-matched" in role
        ),
        break_even=break_evens[settings.primary_benchmark],
    )

    attrition = _attrition(index, census)
    diagnostics: dict[str, JsonValue] = {
        "verdict": verdict,
        "census": {
            "mandate_matches": len(census),
            "rejected_by_exclusion_pattern": sum(
                1 for item in census if item.rejected_by == "exclusion_pattern"
            ),
            "rejected_as_not_a_futures_programme": sum(
                1 for item in census if item.rejected_by == "not_a_futures_programme"
            ),
            "admitted": len(admitted),
            "with_at_least_one_filed_month": len(funds),
            "fetch_failures": failures,
        },
        "live_index": index.to_json(),
        "attrition": attrition,
        "per_fund": [
            {
                "series_id": fund.series_id,
                "series_name": fund.series_name,
                "months_filed": len(fund.returns),
                "first_filed_month": fund.periods[0] if fund.returns else None,
                "last_filed_month": fund.periods[-1] if fund.returns else None,
                "share_classes": len(fund.class_ids),
                "filings": fund.filing_count,
                "amendments": fund.amendment_count,
                "is_final_filing_seen": fund.is_final_filing_seen,
                "cross_class_return_dispersion_percent_per_year": fund.class_dispersion * 100.0,
            }
            for fund in sorted(index.funds, key=lambda f: f.series_name)
        ],
        "moments": {k: dict(v) for k, v in sleeve_moments(panel).items()},
        "correlation_equity_trend": float(
            np.corrcoef(panel.column("equity"), panel.column("trend"))[0, 1]
        ),
        "vendor_comparison": comparison.to_json(),
        "robustness_arms": robustness_arms(
            funds,
            census,
            periods=panel.periods,
            market=market,
            cash=cash,
            vendor=vendor,
            minimum_funds=settings.minimum_funds,
            minimum_net_assets=settings.robustness_minimum_net_assets,
        ),
        "portfolios": {name: item.to_json() for name, item in portfolios.items()},
        "matched_volatility": {
            name: [row.to_json() for row in rows] for name, rows in comparisons.items()
        },
        "haircut_sweep": {k: list(v) for k, v in sweeps.items()},
        "break_even_haircut": dict(break_evens),
        "cost_model": {
            "sleeve_fee_annual": dict(settings.costs.sleeve_fee),
            "borrow_spread_annual": settings.costs.borrow_spread,
            "trend_fee_is_zero_because": (
                "Item B.5 returns are already net of the fund's own ongoing fees"
            ),
        },
        "benchmarks": {
            "primary": settings.primary_benchmark,
            "secondary": settings.secondary_benchmark,
            "never_combined": True,
        },
        "provenance": provenance,
        "data_findings": list(panel.findings),
    }

    frames = {
        "per_fund": pd.DataFrame(diagnostics["per_fund"]),  # type: ignore[arg-type]
        "portfolios": pd.DataFrame([item.to_json() for item in portfolios.values()]),
        "haircut_sweep": pd.DataFrame(
            [
                {"benchmark": name, **point}
                for name, points in sweeps.items()
                for point in points
            ]
        ),
    }
    return ExperimentResult(
        status=status,
        summary=verdict,
        estimates=_build_estimates(portfolios, comparisons, comparison, break_evens, settings),
        diagnostics=diagnostics,
        caveats=_CAVEATS,
        frames=frames,
    )


def _attrition(index: LiveIndex, census: Sequence[ScreenedSeries]) -> dict[str, JsonValue]:
    """How much of the shelf died inside the window. Every figure a lower bound."""
    if not index.periods:  # pragma: no cover - defensive
        return {}
    opened = index.periods[0]
    closed = index.periods[-1]
    open_cutoff = period_from_index(month_index(opened) + 2)
    death_cutoff = period_from_index(month_index(closed) - 3)
    at_open = [f for f in index.funds if f.periods and f.periods[0] <= open_cutoff]
    stopped = [f for f in index.funds if f.periods and f.periods[-1] <= death_cutoff]
    stopped_from_open = [f for f in at_open if f.periods[-1] <= death_cutoff]
    assets = {item.series_id: item.net_assets_maximum for item in census}
    return {
        "window": f"{opened}..{closed}",
        "funds_reporting_at_the_window_open": len(at_open),
        "funds_that_stopped_filing_inside_the_window": len(stopped),
        "of_those_present_at_the_open": len(stopped_from_open),
        "attrition_rate_of_the_opening_cohort": (
            len(stopped_from_open) / len(at_open) if at_open else 0.0
        ),
        "funds_first_filing_after_the_open": len(
            [f for f in index.funds if f.periods and f.periods[0] > open_cutoff]
        ),
        "largest_that_stopped": [
            {
                "series_name": fund.series_name,
                "last_filed_month": fund.periods[-1],
                "net_assets_usd": assets.get(fund.series_id),
                "final_filing_flag": fund.is_final_filing_seen,
            }
            for fund in sorted(
                stopped, key=lambda f: -(assets.get(f.series_id) or 0.0)
            )[:10]
        ],
        "interpretation": (
            "A LOWER BOUND, twice over. Public N-PORT filings begin in 2019, so a fund "
            "that closed before 2019Q4 is invisible; and a fund that both launched after "
            "2019Q4 and closed before 2025Q4 appears in neither census, so it is missing "
            "from this index altogether. Both omissions remove funds that failed, and "
            "both therefore flatter every return reported here."
        ),
    }


_CAVEATS: Final = (
    "EXPLORATORY AND UNPROMOTABLE. This specification was written after Experiment 011's "
    "result was known and after its unresolved verdict was traced to the vendor series. "
    "The index construction, the fund-level screen and the window were chosen with that "
    "in view. No re-run converts that into a confirmatory result.",
    "ITEM B.5 IS UNAUDITED AND SELF-REPORTED. Form N-PORT General Instruction G lets each "
    "filer use its own internal methodology, so two funds' returns are not guaranteed to "
    "be computed identically. The repository's cross-source check returned an HTTP error "
    "for all 44 US and all 25 ex-US tickers, so Item B.5 is the SOLE measurement of every "
    "fund return here and no independent corroboration exists.",
    "SURVIVORSHIP IS BOUNDED, NOT REMOVED, AND EVERY ATTRITION FIGURE IS A LOWER BOUND. "
    "Public N-PORT filings begin in 2019, so a managed-futures fund that closed before "
    "2019Q4 is invisible to both censuses. Worse for this design: a fund that both "
    "launched after 2019Q4 and closed before 2025Q4 is in NEITHER census and is missing "
    "from the index entirely. Both omissions delete funds that failed.",
    "THE WINDOW IS THE BINDING CONSTRAINT. Roughly 78 months cannot resolve a portfolio "
    "effect of the size at issue; the minimum detectable effect at 80% power is reported "
    "beside every gap and is several times the point estimate. A gap below that floor is "
    "not evidence of an effect and must not be read as one.",
    "THE TREND LEG CARRIES A ZERO MODELLED FEE, and that is not optimism. Item B.5 is "
    "already net of the fund's own ongoing fees, its trading costs, its slippage and its "
    "roll. Charging Experiment 011's 1.45% on top would deduct the fee twice.",
    "THE INDEX IS EQUAL-WEIGHT ACROSS FUNDS, NOT ACROSS DOLLARS. It is what the average "
    "managed-futures fund delivered, not what the average managed-futures dollar earned. "
    "N-PORT gives net assets at two dates only, which cannot support a monthly asset "
    "weighting.",
    "THE FUND POPULATION IS NOT CONSTANT. It ranges from about eighteen to about "
    "thirty-three funds a month, and the composition changes as funds launch and die. "
    "That is the design -- a fixed population would be a survivorship screen -- but it "
    "means no two months' index values rest on the same funds.",
    "THE TWO BENCHMARKS ARE NEVER COMBINED. The leverage-matched control answers whether "
    "this is alpha; the unlevered control answers what a non-borrowing investor gives up.",
    "PRETAX everywhere, and managed futures are the worst case for that omission. The "
    "simulation holds no tax lots, so it cannot know a basis, so it may not price a "
    "realisation.",
    "No sleeve is promoted by this result and decision 0004 stands.",
)


def _decide(
    *,
    headline: MatchedVolatilityComparison,
    levered_beats: bool,
    break_even: float | None,
) -> tuple[ResultStatus, str]:
    """Apply the frozen falsifiers, in the order the specification states them."""
    gap_pp = headline.gap * 100.0
    if headline.gap <= 0.0:
        return (
            ResultStatus.REJECTED,
            f"falsifier (a): the matched-volatility gap of {headline.portfolio} against "
            f"{headline.benchmark} is {gap_pp:+.2f} pp/yr, at or below zero, on a trend "
            "leg that is live, net of fees and free of backfill.",
        )
    if levered_beats:
        return (
            ResultStatus.REJECTED,
            "falsifier (b): a leverage-matched control attains a Sharpe ratio at or above "
            "the overlay portfolio's, so the gain is leveraged beta rather than alpha.",
        )
    if headline.interval is not None and headline.interval[0] <= 0.0 <= headline.interval[1]:
        return (
            ResultStatus.UNRESOLVED,
            f"the gap is {gap_pp:+.2f} pp/yr but its bootstrap interval "
            f"[{headline.interval[0] * 100:+.2f}, {headline.interval[1] * 100:+.2f}] "
            f"includes zero, and the minimum detectable effect is "
            f"{headline.minimum_detectable_effect * 100:.2f} pp/yr over "
            f"{headline.months} months. The window, not the series, is now the "
            "binding constraint.",
        )
    if not headline.resolved:
        return (
            ResultStatus.UNRESOLVED,
            f"the gap is {gap_pp:+.2f} pp/yr, below the minimum detectable effect of "
            f"{headline.minimum_detectable_effect * 100:.2f} pp/yr over {headline.months} "
            "months. A positive point estimate below the resolution of the instrument is "
            "not evidence of an effect.",
        )
    if break_even is not None:
        return (
            ResultStatus.EXPLORATORY,
            f"the gap is {gap_pp:+.2f} pp/yr against {headline.benchmark}, its interval "
            f"excludes zero, and the break-even haircut on the live leg is "
            f"{break_even * 100:.2f} pp/yr. Exploratory only: see the freeze note.",
        )
    return (
        ResultStatus.EXPLORATORY,
        f"the gap is {gap_pp:+.2f} pp/yr against {headline.benchmark} and its interval "
        "excludes zero. Exploratory only: see the freeze note.",
    )


def _build_estimates(
    portfolios: Mapping[str, PortfolioSummary],
    comparisons: Mapping[str, Sequence[MatchedVolatilityComparison]],
    comparison: VendorComparison,
    break_evens: Mapping[str, float | None],
    settings: _Settings,
) -> tuple[Estimate, ...]:
    """Net-optimistic, and the *trend* leg is the one part of it that is genuinely net.

    Item B.5 has already deducted the fund's fee, its trading costs, its slippage and
    its roll, so the trend leg carries no modelled cost at all. The equity leg still
    carries a zero fee and nothing here pays tax or rebalancing, so the column as a
    whole stays net-optimistic rather than becoming a net-actual one.
    """
    basis = CostBasis.NET_OPTIMISTIC
    estimates: list[Estimate] = [
        Estimate(
            name="live_managed_futures_excess_return",
            value=comparison.live_moments["arithmetic_excess_return"] * 100.0,
            units="percent per year",
            cost_basis=basis,
            n_obs=comparison.months,
            notes=(
                f"equal-weight index of fund-reported Item B.5 total returns, net of each "
                f"fund's own fees; volatility "
                f"{comparison.live_moments['volatility'] * 100:.2f}%, Sharpe "
                f"{comparison.live_moments['sharpe']:.3f}"
            ),
            uncertainty_unavailable_reason=(
                "the interval that decides is on the difference from the vendor series and "
                "on the portfolio gap, and both are reported"
            ),
        ),
        Estimate(
            name="vendor_alpha_against_the_live_funds",
            value=comparison.alpha * 100.0,
            units="percentage points per year",
            interval=(
                (comparison.alpha - 1.96 * comparison.alpha_standard_error) * 100.0,
                (comparison.alpha + 1.96 * comparison.alpha_standard_error) * 100.0,
            ),
            interval_method="Newey-West HAC, "
            f"{comparison.hac_lags} lags, normal 95% interval",
            cost_basis=CostBasis.GROSS,
            n_obs=comparison.months,
            notes=(
                f"intercept of AQR TSMOM regressed on the live net index; beta "
                f"{comparison.beta:.3f} (se {comparison.beta_standard_error:.3f}), R^2 "
                f"{comparison.r_squared:.3f}. POSITIVE would be the survivorship, backfill "
                "and unpriced-cost gap the repository bounds at 7.7 pp/yr"
            ),
        ),
        Estimate(
            name="vendor_less_live_at_matched_volatility",
            value=comparison.volatility_matched_difference * 100.0,
            units="percentage points per year",
            interval=(
                comparison.volatility_matched_interval[0] * 100.0,
                comparison.volatility_matched_interval[1] * 100.0,
            ),
            interval_method="Newey-West HAC on the paired difference, normal 95% interval",
            cost_basis=CostBasis.GROSS,
            n_obs=comparison.months,
            notes=(
                "the live index scaled to the vendor series' volatility and subtracted from "
                "it, so the exposure difference is removed and only the level remains"
            ),
        ),
    ]
    for name, summary in portfolios.items():
        estimates.append(
            Estimate(
                name=f"net_geometric_return[{name}]",
                value=summary.geometric_return * 100.0,
                units="percent per year",
                cost_basis=basis,
                n_obs=summary.months,
                notes=(
                    f"gross notional {summary.gross_notional:.2f}x, annual charge "
                    f"{summary.annual_cost * 100:.3f}% (the trend leg's fee is inside its "
                    "own reported return)"
                ),
                uncertainty_unavailable_reason=(
                    "a geometric return over one realised path has no sampling interval "
                    "that is not a restatement of the arithmetic mean's; the interval that "
                    "decides is on the matched-volatility gap, which is reported"
                ),
            )
        )
    for benchmark, rows in comparisons.items():
        for row in rows:
            estimates.append(
                Estimate(
                    name=f"matched_volatility_gap[{row.portfolio} vs {benchmark}]",
                    value=row.gap * 100.0,
                    units="percentage points per year",
                    interval=(
                        (row.interval[0] * 100.0, row.interval[1] * 100.0)
                        if row.interval
                        else None
                    ),
                    interval_method=row.interval_method,
                    cost_basis=basis,
                    n_obs=row.months,
                    notes=(
                        f"minimum detectable effect at 80% power "
                        f"{row.minimum_detectable_effect * 100:.2f} pp/yr, so this gap is "
                        f"{'resolved' if row.resolved else 'BELOW the resolution of the sample'}"
                        f"; materiality threshold {settings.materiality * 100:.2f} pp/yr"
                    ),
                )
            )
    for benchmark, value in break_evens.items():
        if value is None:
            continue
        estimates.append(
            Estimate(
                name=f"break_even_haircut_on_live_trend[vs {benchmark}]",
                value=value * 100.0,
                units="percentage points per year",
                cost_basis=basis,
                n_obs=None,
                notes=(
                    "what can be subtracted from the live leg's arithmetic mean before the "
                    "overlay stops beating this benchmark. It is far thinner than "
                    "Experiment 011's 9.57 pp/yr because the live window is a poor one for "
                    "trend, not because the leg is worse"
                ),
                uncertainty_unavailable_reason=(
                    "a deterministic function of the sample mean; its uncertainty is the "
                    "gap's and is reported there"
                ),
            )
        )
    return tuple(estimates)


# --------------------------------------------------------------------------- #
# Registry and CLI
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def _render_console_report(outcome: RunOutcome) -> str:
    result = outcome.result
    if result is None:  # pragma: no cover - defensive
        return "no result"
    d = result.diagnostics
    lines = [f"Experiment 012 -- {result.status.value}", str(d.get("verdict", "")), ""]

    census = _mapping(d.get("census"), where="census")
    lines += [
        "Census (names only, no return read while screening)",
        f"  mandate matches                    {census['mandate_matches']}",
        f"  rejected by the exclusion pattern  {census['rejected_by_exclusion_pattern']}",
        f"  rejected as not a futures fund     {census['rejected_as_not_a_futures_programme']}",
        f"  admitted                           {census['admitted']}",
        f"  with a filed Item B.5 month        {census['with_at_least_one_filed_month']}",
        "",
    ]
    index = _mapping(d.get("live_index"), where="live_index")
    lines += [
        f"Live index {index['window']}  n={index['months']}  "
        f"funds {index['minimum_funds_in_any_month']}..{index['maximum_funds_in_any_month']}",
        "",
        "Moments, annualised, excess of the French one-month bill",
        f"  {'sleeve':<12}{'mean':>9}{'vol':>9}{'sharpe':>9}",
    ]
    moments = _mapping(d.get("moments"), where="moments")
    for sleeve, payload in moments.items():
        row = _mapping(payload, where="moments[]")
        lines.append(
            f"  {sleeve:<12}{float(str(row['arithmetic_excess_return'])) * 100:>8.2f}%"
            f"{float(str(row['volatility'])) * 100:>8.2f}%{float(str(row['sharpe'])):>9.3f}"
        )

    v = _mapping(d.get("vendor_comparison"), where="vendor_comparison")
    lines += [
        "",
        "The decisive comparison: AQR TSMOM regressed on the live net index",
        f"  alpha {float(str(v['alpha_percent_per_year'])):+.2f} pp/yr  "
        f"(se {float(str(v['alpha_standard_error_percent_per_year'])):.2f})",
        f"  beta  {float(str(v['beta_on_the_live_index'])):+.3f}  "
        f"R2 {float(str(v['r_squared'])):.3f}",
        f"  vendor less live at matched volatility "
        f"{float(str(v['volatility_matched_difference_pp_per_year'])):+.2f} pp/yr",
        "",
        "Portfolios, net, over the live window",
        f"  {'portfolio':<26}{'geo':>8}{'vol':>8}{'sharpe':>8}{'maxDD':>8}{'under':>7}",
    ]
    for name, payload in _mapping(d.get("portfolios"), where="portfolios").items():
        row = _mapping(payload, where="portfolios[]")
        lines.append(
            f"  {name:<26}{float(str(row['geometric_return'])) * 100:>7.2f}%"
            f"{float(str(row['volatility_of_excess_return'])) * 100:>7.2f}%"
            f"{float(str(row['sharpe'])):>8.3f}"
            f"{float(str(row['max_drawdown'])) * 100:>7.1f}%"
            f"{int(str(row['months_under_water'])):>7d}"
        )
    lines.append("")
    for benchmark, rows in _mapping(d.get("matched_volatility"), where="mv").items():
        lines.append(f"Matched-volatility gap against {benchmark} (never added to the other)")
        for item in _sequence(rows, where="mv[]"):
            row = _mapping(item, where="mv[][]")
            interval = row.get("interval")
            span = (
                f"[{float(str(_sequence(interval, where='i')[0])) * 100:+.2f}, "
                f"{float(str(_sequence(interval, where='i')[1])) * 100:+.2f}]"
                if isinstance(interval, Sequence) and not isinstance(interval, str)
                else "no interval"
            )
            lines.append(
                f"  {row['portfolio']!s:<26}{float(str(row['gap'])) * 100:>+7.2f} pp/yr  "
                f"{span:>20}  MDE {float(str(row['minimum_detectable_effect'])) * 100:.2f}"
            )
        lines.append("")
    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_012_live_trend",
        description=(
            "Rebuild the trend leg from live, net, fund-reported Form N-PORT returns and "
            "re-run Experiment 011's overlay comparison against it."
        ),
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument(
        "--build-census",
        action="store_true",
        help=(
            "screen both N-PORT censuses on series names and commit the result. Must be "
            "run BEFORE the experiment; no return is read while screening."
        ),
    )
    parser.add_argument(
        "--view-results",
        action="store_true",
        help=(
            "print the computed numbers AND append a results_viewed entry to the ledger. "
            "Looking is an event with consequences, so it is recorded."
        ),
    )
    arguments = parser.parse_args(argv)
    specification = load_specification(arguments.specification)

    if arguments.build_census:
        settings = _read_settings(specification)
        payload = build_census(
            RawCache(),
            mandate_pattern=settings.mandate_pattern,
            exclusion_pattern=settings.exclusion_pattern,
            not_a_futures_programme=settings.not_a_futures_programme,
        )
        location = write_census(payload)
        print(f"census written to {location}")
        print(f"  mandate matches {payload['mandate_matches']}, admitted {payload['admitted']}")
        return 0

    ledger = Ledger(arguments.ledger)
    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
    )
    print(f"run_id       {outcome.run_id}")
    print(f"spec_hash    {outcome.spec_hash}")
    print(f"status       {outcome.status.value}")
    print(f"result       {outcome.result.status.value if outcome.result else 'none'}")
    print(f"git_commit   {outcome.git_state.commit} (dirty={outcome.git_state.dirty})")
    for record in outcome.artifacts:
        print(f"artifact     {record.path}  {record.sha256}  {record.size_bytes}B")

    if arguments.view_results:
        print()
        print(_render_console_report(outcome))
        ledger.record_results_viewed(
            outcome.run_id,
            origin=Origin(arguments.origin),
            notes=(
                "numbers printed to the console by the --view-results flag of "
                "exp_012_live_trend"
            ),
        )
        print()
        print("results_viewed appended to the ledger")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
