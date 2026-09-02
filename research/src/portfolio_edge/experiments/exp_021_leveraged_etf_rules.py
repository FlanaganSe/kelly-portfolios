"""Experiment 021: leveraged ETFs and the 200-day moving average.

What this is
------------
The investor asked whether "strategies like the 200 day SMA" belong in the
portfolio. The repository had tested a 10-month average on unlevered equity at
monthly resolution and nothing else. This module builds daily-reset 2x and 3x
market funds from Ken French's daily file (fee, swap spread and the volatility
drag that daily compounding produces, all inside the path), switches them with
a 200-day moving average as Gayed's "Leverage for the Long Run" does, holds the
55/45 UPRO/TMF mix (HFEA) on monthly data, and scores every construction
against an unlevered index, a continuous 1.3x exposure and the rule's own
beta-matched control, with the floor beside every gap.

What this is NOT
----------------
**It does not score funds.** A levered fund here is ``RF + L * (Mkt - RF)``
less a fee and a spread on the borrowed notional, compounded daily. That is the
mechanism of a swap-based leveraged ETF and it is nobody's NAV.

**It cannot resolve most of what it measures.** The specification predicts,
before the run, that every timed arm's mean gap comes back ``unresolved`` on
every window; the drawdown, whipsaw, crisis-episode and after-tax tables are
descriptions of one realised history and carry no significance claim.

**The signal index is the total-return index**, because the library has no
price-only daily series. A price proxy is run as a sensitivity.

Run it::

    uv run python -m portfolio_edge.experiments.exp_021_leveraged_etf_rules --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import french, goyal_welch
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    _at,
    _mapping,
    _number,
    _numbers,
    _sequence,
    _text,
    workspace_root,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
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
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.deflated_sharpe import (
    LinearDependenceWarning,
    deflated_sharpe_ratio,
    effective_number_of_trials,
    mean_off_diagonal_correlation,
    trial_dispersion_from_sharpes,
)
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.inference.multiple_testing import benjamini_hochberg
from portfolio_edge.studies.tax_structure import TOP_BRACKET, UPPER_MIDDLE_BRACKET
from portfolio_edge.studies.timing_rules import (
    Disposal,
    TaxableAssumptions,
    sheltered_path,
    taxable_path,
)

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

ENTRY_POINT: Final = "exp_021_leveraged_etf_rules"

#: Fees and spreads accrue per calendar day elapsed between closes, because the
#: file has six trading days a week until 1952 and a per-row accrual would
#: overcharge the early sample by a fifth.
DAYS_PER_YEAR: Final = 365.25

_NORMAL_975: Final = 1.959963984540054
_MONTHS_PER_YEAR: Final = 12

__all__ = [
    "DAYS_PER_YEAR",
    "ENTRY_POINT",
    "Descriptives",
    "GapStatistics",
    "LeveragedEtfRulesError",
    "RawSeries",
    "build_registry",
    "calendar_day_gaps",
    "compound_monthly",
    "default_specification_path",
    "describe",
    "episode_summary",
    "exposure_matched_returns",
    "gap_statistics",
    "levered_fund_returns",
    "main",
    "moving_average_signal",
    "positions_from_signal",
    "rebalanced_mix",
    "round_trip_count",
    "rule_returns",
    "run",
    "total_return_levels",
]


class LeveragedEtfRulesError(Exception):
    """The experiment refused to run, or a source did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_021_leveraged_etf_rules.yaml"


# --------------------------------------------------------------------------- #
# The daily arithmetic, pure
# --------------------------------------------------------------------------- #


def _as_1d(values: Sequence[float] | FloatArray, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise LeveragedEtfRulesError(f"{name} must be one-dimensional, got {array.shape}")
    if array.size == 0:
        raise LeveragedEtfRulesError(f"{name} is empty")
    return array


def calendar_day_gaps(dates: Sequence[str]) -> IntArray:
    """Calendar days elapsed since the previous row; the first row counts one.

    ``dates`` are ``YYYY-MM-DD`` labels in ascending order. A Monday after a
    weekend returns 3, which is what a fee accrued per calendar day must see.
    """
    if not dates:
        raise LeveragedEtfRulesError("dates is empty")
    ordinals = np.array([date.fromisoformat(d).toordinal() for d in dates], dtype=np.int64)
    gaps = np.diff(ordinals, prepend=ordinals[0] - 1)
    if np.any(gaps <= 0):
        first = int(np.argmax(gaps <= 0))
        raise LeveragedEtfRulesError(f"dates are not strictly increasing at {dates[first]}")
    return np.asarray(gaps, dtype=np.int64)


def levered_fund_returns(
    market_excess: Sequence[float] | FloatArray,
    cash: Sequence[float] | FloatArray,
    day_gaps: Sequence[int] | IntArray,
    *,
    leverage: float,
    fee_bp: float,
    spread_bp: float,
) -> FloatArray:
    """One day of a daily-reset ``leverage``-times fund, per dollar of net assets.

    ``RF + L * (Mkt - RF)`` is the identity for a fund holding ``L`` of index
    exposure and borrowing ``L - 1`` at the bill rate: the bill part of the
    financing nets against the bill earned on the collateral. What is left to
    charge is the spread on the borrowed ``L - 1`` and the fee on net assets,
    both accrued per calendar day elapsed. Daily-reset volatility drag is not
    here; it appears when the caller compounds the series.
    """
    excess = _as_1d(market_excess, name="market_excess")
    bills = _as_1d(cash, name="cash")
    gaps = np.asarray(day_gaps, dtype=np.float64)
    if bills.shape != excess.shape or gaps.shape != excess.shape:
        raise LeveragedEtfRulesError("market_excess, cash and day_gaps must be the same shape")
    if leverage < 0.0:
        raise LeveragedEtfRulesError(f"leverage cannot be negative, got {leverage}")
    if fee_bp < 0.0 or spread_bp < 0.0:
        raise LeveragedEtfRulesError("fee_bp and spread_bp cannot be negative")
    annual_charge = (max(leverage - 1.0, 0.0) * spread_bp + fee_bp) / 10_000.0
    return np.asarray(bills + leverage * excess - annual_charge * gaps / DAYS_PER_YEAR)


def total_return_levels(
    market_excess: Sequence[float] | FloatArray,
    cash: Sequence[float] | FloatArray,
    *,
    day_gaps: Sequence[int] | IntArray | None = None,
    dividend_yield: float = 0.0,
) -> FloatArray:
    """Cumulative index level, ``levels[t]`` the close at the end of day ``t``.

    ``dividend_yield`` above zero subtracts a constant annual yield accrued per
    calendar day, which is the price-index proxy the specification runs as a
    sensitivity; zero is the total-return index the base arms use.
    """
    total = _as_1d(market_excess, name="market_excess") + _as_1d(cash, name="cash")
    if dividend_yield > 0.0:
        if day_gaps is None:
            raise LeveragedEtfRulesError("a dividend deflation needs day_gaps")
        total = total - dividend_yield * np.asarray(day_gaps, dtype=np.float64) / DAYS_PER_YEAR
    levels = np.cumprod(1.0 + total)
    if np.any(levels <= 0.0):
        raise LeveragedEtfRulesError("the index level reached zero")
    return np.asarray(levels, dtype=np.float64)


def moving_average_signal(
    levels: Sequence[float] | FloatArray, *, window: int, band: float = 0.0
) -> FloatArray:
    """1.0 where the close is above its ``window``-day average, 0.0 below, nan unformed.

    The average includes the close it is compared with. With ``band`` above
    zero the signal is a hysteresis: it turns on only when the close exceeds
    the average by more than ``band``, turns off only when it falls short by
    more than ``band``, and otherwise keeps its previous state. The first
    formed day, which has no previous state, is decided on the plain
    comparison.
    """
    series = _as_1d(levels, name="levels")
    if window < 2:
        raise LeveragedEtfRulesError(f"window must be at least 2 days, got {window}")
    if band < 0.0:
        raise LeveragedEtfRulesError(f"band cannot be negative, got {band}")
    out = np.full(series.size, np.nan, dtype=np.float64)
    if series.size < window:
        return out
    cumulative = np.concatenate([[0.0], np.cumsum(series)])
    average = (cumulative[window:] - cumulative[:-window]) / window
    state = 1.0 if series[window - 1] > average[0] else 0.0
    for offset in range(average.size):
        index = window - 1 + offset
        level, mean = float(series[index]), float(average[offset])
        if offset > 0:
            if level > mean * (1.0 + band):
                state = 1.0
            elif level < mean * (1.0 - band):
                state = 0.0
        out[index] = state
    return out


def positions_from_signal(signal: Sequence[float] | FloatArray, *, lag: int) -> FloatArray:
    """Position held on day ``t`` is the signal read at close ``t - 1 - lag``.

    ``lag = 0`` trades at the close the signal was read at; ``lag = 1`` reads
    at one close and trades at the next, which is the specification's base
    case. Nothing here can see the return the position earns.
    """
    series = _as_1d(signal, name="signal")
    if lag < 0:
        raise LeveragedEtfRulesError(f"lag cannot be negative, got {lag}")
    shift = 1 + lag
    out = np.full(series.size, np.nan, dtype=np.float64)
    out[shift:] = series[:-shift] if shift < series.size else out[shift:]
    return out


def _live_slice(position: FloatArray) -> tuple[int, int]:
    live = np.flatnonzero(np.isfinite(position))
    if live.size == 0:
        raise LeveragedEtfRulesError("position has no formed days")
    first, last = int(live[0]), int(live[-1])
    if not np.all(np.isfinite(position[first : last + 1])):
        raise LeveragedEtfRulesError("position has a gap inside its live window")
    return first, last


def rule_returns(
    fund_total: Sequence[float] | FloatArray,
    cash: Sequence[float] | FloatArray,
    position: Sequence[float] | FloatArray,
    *,
    one_way_cost: float,
) -> FloatArray:
    """The switched portfolio's total return, its trading cost charged inside it.

    ``r[t] = p[t] fund[t] + (1 - p[t]) cash[t] - cost |p[t] - p[t-1]|``. The
    position before the first formed day is taken to be the first formed
    position, so the initial entry is free: buy-and-hold has to buy too. Days
    before the first formed position are nan.
    """
    fund = _as_1d(fund_total, name="fund_total")
    bills = _as_1d(cash, name="cash")
    weights = np.asarray(position, dtype=np.float64)
    if fund.shape != bills.shape or weights.shape != fund.shape:
        raise LeveragedEtfRulesError("fund_total, cash and position must be the same shape")
    if one_way_cost < 0.0:
        raise LeveragedEtfRulesError(f"one_way_cost cannot be negative, got {one_way_cost}")
    first, last = _live_slice(weights)
    out = np.full(fund.size, np.nan, dtype=np.float64)
    live = weights[first : last + 1]
    previous = np.concatenate([[live[0]], live[:-1]])
    out[first : last + 1] = (
        live * fund[first : last + 1]
        + (1.0 - live) * bills[first : last + 1]
        - one_way_cost * np.abs(live - previous)
    )
    return out


def exposure_matched_returns(
    fund_total: Sequence[float] | FloatArray,
    cash: Sequence[float] | FloatArray,
    position: Sequence[float] | FloatArray,
) -> tuple[FloatArray, float]:
    """The same fund at a constant weight equal to the rule's average exposure.

    Returns the control's total return and the weight. Its excess over bills is
    exactly ``w`` times the fund's, with no rebalancing term and no cost, so
    the difference between the rule and this series is timing content only.
    """
    fund = _as_1d(fund_total, name="fund_total")
    bills = _as_1d(cash, name="cash")
    weights = np.asarray(position, dtype=np.float64)
    first, last = _live_slice(weights)
    w = float(np.mean(weights[first : last + 1]))
    out = np.full(fund.size, np.nan, dtype=np.float64)
    out[first : last + 1] = w * fund[first : last + 1] + (1.0 - w) * bills[first : last + 1]
    return out, w


def round_trip_count(position: Sequence[float] | FloatArray) -> int:
    """Number of exits over the formed days. Each exit begins one round trip."""
    weights = np.asarray(position, dtype=np.float64)
    first, last = _live_slice(weights)
    live = weights[first : last + 1]
    return int(np.count_nonzero((live[1:] == 0.0) & (live[:-1] == 1.0)))


# --------------------------------------------------------------------------- #
# Monthly arithmetic for HFEA
# --------------------------------------------------------------------------- #


def compound_monthly(
    dates: Sequence[str], returns: Sequence[float] | FloatArray
) -> tuple[tuple[str, ...], FloatArray]:
    """Compound a daily series inside each calendar month; nan days drop the month."""
    series = _as_1d(returns, name="returns")
    if len(dates) != series.size:
        raise LeveragedEtfRulesError("dates and returns must be the same length")
    months: list[str] = []
    values: list[float] = []
    growth = 1.0
    complete = True
    current = dates[0][:7]
    for label, value in zip(dates, series, strict=True):
        month = label[:7]
        if month != current:
            months.append(current)
            values.append(growth - 1.0 if complete else math.nan)
            current, growth, complete = month, 1.0, True
        if not math.isfinite(value):
            complete = False
        else:
            growth *= 1.0 + float(value)
    months.append(current)
    values.append(growth - 1.0 if complete else math.nan)
    return tuple(months), np.asarray(values, dtype=np.float64)


def rebalanced_mix(
    legs: FloatArray,
    weights: Sequence[float],
    *,
    every: int,
    one_way_cost: float,
) -> FloatArray:
    """Total return of a mix rebalanced to ``weights`` every ``every`` periods.

    ``legs`` is ``(periods, legs)`` of total returns. Positions drift between
    rebalances; at a rebalance each leg is traded to its target and the traded
    amount on every leg pays ``one_way_cost``, so moving a dollar from one leg
    to another costs twice it. The first period starts at the targets for free.
    """
    matrix = np.asarray(legs, dtype=np.float64)
    target = np.asarray(weights, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != target.size:
        raise LeveragedEtfRulesError("legs must be (periods, legs) matching the weights")
    if abs(float(target.sum()) - 1.0) > 1e-12 or np.any(target < 0.0):
        raise LeveragedEtfRulesError("weights must be non-negative and sum to one")
    if every < 1:
        raise LeveragedEtfRulesError("every must be at least 1")
    values = target.copy()
    out = np.empty(matrix.shape[0], dtype=np.float64)
    for t in range(matrix.shape[0]):
        wealth = float(values.sum())
        if t > 0 and t % every == 0:
            desired = target * wealth
            traded = float(np.abs(desired - values).sum())
            cost = one_way_cost * traded
            values = desired * (1.0 - cost / wealth)
        values = values * (1.0 + matrix[t])
        out[t] = float(values.sum()) / wealth - 1.0
    return out


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class GapStatistics:
    """One arm-against-control comparison with everything a verdict needs."""

    gap_pp_yr: float
    hac_standard_error_pp_yr: float
    hac_interval: tuple[float, float]
    bootstrap_interval: tuple[float, float]
    mde_pp_yr: float
    p_value: float
    tracking_error_pct: float
    rows: int
    years: float
    years_to_distinguish: float


def _span_years(dates: Sequence[str], gaps: IntArray | None = None) -> float:
    first = date.fromisoformat(dates[0]).toordinal()
    last = date.fromisoformat(dates[-1]).toordinal()
    lead = int(gaps[0]) if gaps is not None else 1
    return (last - first + lead) / DAYS_PER_YEAR


def gap_statistics(
    difference: FloatArray,
    *,
    rows_per_year: float,
    n_lags: int | None,
    rng: np.random.Generator,
    block: float,
    resamples: int,
    chunk: int,
) -> GapStatistics:
    """Mean paired difference annualised, with HAC and block-bootstrap intervals."""
    d = _as_1d(difference, name="difference")
    if not np.all(np.isfinite(d)):
        raise LeveragedEtfRulesError("difference contains non-finite values")
    scale = rows_per_year * 100.0
    estimate = hac_mean(d, n_lags=n_lags)
    gap = estimate.mean * scale
    se = estimate.standard_error * scale
    half = _NORMAL_975 * se
    resampled: list[FloatArray] = []
    remaining = resamples
    while remaining > 0:
        size = min(chunk, remaining)
        indices = stationary_bootstrap_indices(d.size, block, size, rng)
        resampled.append(d[indices].mean(axis=1) * scale)
        remaining -= size
    draws = np.concatenate(resampled)
    low, high = np.quantile(draws, [0.025, 0.975])
    sigma_annual = float(np.std(d, ddof=1)) * math.sqrt(rows_per_year) * 100.0
    return GapStatistics(
        gap_pp_yr=gap,
        hac_standard_error_pp_yr=se,
        hac_interval=(gap - half, gap + half),
        bootstrap_interval=(float(low), float(high)),
        mde_pp_yr=MDE_MULTIPLIER * se,
        p_value=estimate.p_value,
        tracking_error_pct=sigma_annual,
        rows=int(d.size),
        years=d.size / rows_per_year,
        years_to_distinguish=(
            float("inf") if gap == 0.0 else (MDE_MULTIPLIER * sigma_annual / abs(gap)) ** 2
        ),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Descriptives:
    """One arm on one window. Every field describes one realised path."""

    rows: int
    years: float
    cagr_pct: float
    arithmetic_mean_pct: float
    volatility_pct: float
    sharpe: float
    max_drawdown_pct: float
    time_under_water_rows: int
    time_under_water_years: float
    terminal_wealth: float
    time_in_market: float | None
    round_trips_per_year: float | None

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "rows": self.rows,
            "years": round(self.years, 2),
            "cagr_pct": round(self.cagr_pct, 3),
            "arithmetic_mean_pct": round(self.arithmetic_mean_pct, 3),
            "volatility_pct": round(self.volatility_pct, 3),
            "sharpe": round(self.sharpe, 3),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "time_under_water_rows": self.time_under_water_rows,
            "time_under_water_years": round(self.time_under_water_years, 2),
            "terminal_wealth": round(self.terminal_wealth, 3),
            "time_in_market": None
            if self.time_in_market is None
            else round(self.time_in_market, 4),
            "round_trips_per_year": (
                None if self.round_trips_per_year is None else round(self.round_trips_per_year, 3)
            ),
        }


def describe(
    total: FloatArray,
    cash: FloatArray,
    *,
    years: float,
    position: FloatArray | None = None,
) -> Descriptives:
    """CAGR, mean, volatility, drawdown and the whipsaw counts of one path."""
    t = _as_1d(total, name="total")
    bills = _as_1d(cash, name="cash")
    if bills.shape != t.shape or not np.all(np.isfinite(t)):
        raise LeveragedEtfRulesError("total and cash must be finite and the same shape")
    if years <= 0.0:
        raise LeveragedEtfRulesError("years must be positive")
    rows_per_year = t.size / years
    curve = np.cumprod(1.0 + t)
    summary = drawdown_summary(curve)
    excess = t - bills
    sd = float(np.std(excess, ddof=1))
    trips: float | None = None
    exposure: float | None = None
    if position is not None:
        first, last = _live_slice(position)
        exposure = float(np.mean(position[first : last + 1]))
        trips = round_trip_count(position) / years
    return Descriptives(
        rows=int(t.size),
        years=years,
        cagr_pct=(float(curve[-1]) ** (1.0 / years) - 1.0) * 100.0,
        arithmetic_mean_pct=float(np.mean(t)) * rows_per_year * 100.0,
        volatility_pct=float(np.std(t, ddof=1)) * math.sqrt(rows_per_year) * 100.0,
        sharpe=float(np.mean(excess)) / sd * math.sqrt(rows_per_year) if sd > 0.0 else 0.0,
        max_drawdown_pct=summary.max_drawdown * 100.0,
        time_under_water_rows=summary.max_time_under_water,
        time_under_water_years=summary.max_time_under_water / rows_per_year,
        terminal_wealth=float(curve[-1]),
        time_in_market=exposure,
        round_trips_per_year=trips,
    )


def episode_summary(
    labels: Sequence[str], total: FloatArray, *, start: str, end: str
) -> dict[str, JsonValue]:
    """Cumulative return and peak-to-trough inside ``[start, end]`` on ``labels``."""
    keep = [i for i, label in enumerate(labels) if start <= label <= end]
    if not keep:
        return {"covered": False}
    window = total[keep]
    curve = np.concatenate([[1.0], np.cumprod(1.0 + window)])
    summary = drawdown_summary(curve)
    return {
        "covered": True,
        "partial": labels[0] > start or labels[-1] < end,
        "rows": len(keep),
        "cumulative_pct": round((float(curve[-1]) - 1.0) * 100.0, 2),
        "peak_to_trough_pct": round(summary.max_drawdown * 100.0, 2),
    }


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RawSeries:
    """Every series the experiment reads, plus provenance."""

    dates: tuple[str, ...]
    market_excess: FloatArray
    cash: FloatArray
    monthly_rf: Mapping[str, float]
    ltr: Mapping[str, float]
    provenance: tuple[Mapping[str, JsonValue], ...]
    findings: tuple[str, ...]


def _pins(specification: Specification) -> dict[str, Mapping[str, JsonValue]]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    out: dict[str, Mapping[str, JsonValue]] = {}
    for item in _sequence(_at(block, "files", where="source_pin"), where="source_pin.files"):
        pin = _mapping(item, where="source_pin.files[]")
        out[_text(pin, "id", where="source_pin.files[]")] = pin
    return out


def _require_cached(
    cache: RawCache, url: str, pin: Mapping[str, JsonValue]
) -> tuple[CacheEntry, dict[str, JsonValue]]:
    """The entry holding the pinned bytes, never downloaded, and its provenance."""
    where = "source_pin.files[]"
    expected = _text(pin, "expected_sha256_raw", where=where)
    entry = cache.entry_for(url)
    superseded: str | None = None
    if entry is None or entry.sha256 != expected:
        if not cache.has(expected):
            observed = "absent" if entry is None else entry.sha256
            raise LeveragedEtfRulesError(
                f"{url} is {observed} in the raw cache and the pinned blob {expected} is not "
                "held either. This experiment does not download; a new vintage needs a new "
                "specification."
            )
        superseded = None if entry is None else entry.sha256
        entry = CacheEntry(
            url=url,
            sha256=expected,
            size_bytes=cache.blob_path(expected).stat().st_size,
            retrieved_utc="unknown: the index entry for this url was superseded",
            http_status=200,
            headers=(),
        )
    manifest_hash: str | None = None
    manifest_matches: bool | None = None
    manifest_path = workspace_root() / _text(pin, "committed_manifest", where=where)
    if manifest_path.is_file():
        manifest = read_manifest(manifest_path)
        manifest_hash = manifest.sha256_manifest()
        manifest_matches = manifest.sha256_raw == entry.sha256
    record: dict[str, JsonValue] = {
        "id": _text(pin, "id", where=where),
        "source": _text(pin, "source", where=where),
        "dataset_id": _text(pin, "dataset_id", where=where),
        "source_url": url,
        "sha256_raw": entry.sha256,
        "retrieved_utc": entry.retrieved_utc,
        "index_superseded_by_sha256": superseded,
        "committed_manifest_sha256": manifest_hash,
        "committed_manifest_raw_hash_matches": manifest_matches,
    }
    return entry, record


def load_series(specification: Specification) -> RawSeries:
    """Read every pinned source from the cache, hash-checked, never downloaded."""
    cache = RawCache()
    pins = _pins(specification)
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []

    def take(file_id: str, url: str) -> tuple[CacheEntry, dict[str, JsonValue]]:
        entry, record = _require_cached(cache, url, pins[file_id])
        if record["committed_manifest_raw_hash_matches"] is False:
            findings.append(
                f"{file_id}: the pinned file ({record['sha256_raw']}) is a different vintage "
                "from the one the committed manifest records; recorded, not hidden."
            )
        if record["index_superseded_by_sha256"] is not None:
            findings.append(
                f"{file_id}: the cache index now points at "
                f"{record['index_superseded_by_sha256']}; the pinned blob was read by digest."
            )
        provenance.append(record)
        return entry, record

    daily = french.get_dataset("french_us_ff3_daily")
    entry, record = take("french_us_ff3_daily", daily.url)
    table = french.parse(cache, entry, dataset=daily).table("daily")
    dates: list[str] = []
    market: list[float] = []
    bills: list[float] = []
    for label, m, r in zip(table.periods, table.column("Mkt-RF"), table.column("RF"), strict=True):
        if m is None or r is None:
            findings.append(f"french_us_ff3_daily: {label} is missing and was dropped")
            continue
        dates.append(label)
        market.append(float(m))
        bills.append(float(r))
    record["first_observation"], record["last_observation"] = dates[0], dates[-1]

    monthly_ds = french.get_dataset("french_us_ff3")
    entry, record = take("french_us_ff3", monthly_ds.url)
    monthly = french.parse(cache, entry, dataset=monthly_ds).table("monthly")
    monthly_rf = {
        p[:7]: float(v)
        for p, v in zip(monthly.periods, monthly.column("RF"), strict=True)
        if v is not None
    }
    record["first_observation"], record["last_observation"] = min(monthly_rf), max(monthly_rf)

    gw = goyal_welch.get_dataset("goyal_welch_predictors")
    entry, record = take("goyal_welch_predictors", gw.url)
    gw_table = next(
        t for t in goyal_welch.parse(cache, entry, dataset=gw).tables if t.table_id == "monthly"
    )
    ltr = {
        p[:7]: float(v)
        for p, v in zip(gw_table.periods, gw_table.column("ltr"), strict=True)
        if v is not None
    }
    record["first_observation"], record["last_observation"] = min(ltr), max(ltr)

    return RawSeries(
        dates=tuple(dates),
        market_excess=np.asarray(market, dtype=np.float64),
        cash=np.asarray(bills, dtype=np.float64),
        monthly_rf=monthly_rf,
        ltr=ltr,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# Reading the specification
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Costs:
    fee_index_bp: float
    fee_2x_bp: float
    fee_3x_bp: float
    fee_treasury_3x_bp: float
    fee_130_bp: float
    spread_bp: float
    stress_spread_bp: float
    one_way_cost: float
    cost_grid: tuple[float, ...]

    def fee_for(self, leverage: float) -> float:
        if leverage == 1.0:
            return self.fee_index_bp
        if leverage == 2.0:
            return self.fee_2x_bp
        if leverage == 3.0:
            return self.fee_3x_bp
        if abs(leverage - 1.3) < 1e-9:
            return self.fee_130_bp
        raise LeveragedEtfRulesError(f"no fee declared for leverage {leverage}")


def read_costs(specification: Specification) -> Costs:
    costs = _mapping(specification.cost_model, where="cost_model")
    fees = _mapping(_at(costs, "fund_fee_basis_points", where="cost_model"), where="fees")
    spreads = _mapping(
        _at(costs, "swap_financing_spread_basis_points_over_bill", where="cost_model"),
        where="spread",
    )
    return Costs(
        fee_index_bp=_number(fees, "index_1x", where="fees"),
        fee_2x_bp=_number(fees, "levered_2x", where="fees"),
        fee_3x_bp=_number(fees, "levered_3x", where="fees"),
        fee_treasury_3x_bp=_number(fees, "treasury_3x", where="fees"),
        fee_130_bp=_number(fees, "leverage_matched_130", where="fees"),
        spread_bp=_number(spreads, "base", where="spread"),
        stress_spread_bp=_number(spreads, "stress", where="spread"),
        one_way_cost=_number(costs, "one_way_trading_cost_basis_points", where="cost_model")
        / 10_000.0,
        cost_grid=tuple(
            x / 10_000.0
            for x in _numbers(
                _at(costs, "trading_cost_sensitivity_basis_points", where="cost_model"),
                where="cost grid",
            )
        ),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Arm:
    name: str
    role: str
    construction: str
    leverage: float
    band: float
    note: str


def read_arms(specification: Specification) -> dict[str, Arm]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "arms", where="parameters"), where="arms")
    out: dict[str, Arm] = {}
    for name in block:
        entry = _mapping(block[name], where=f"arms.{name}")
        construction = _text(entry, "construction", where=f"arms.{name}")
        if construction not in {"buy_and_hold", "constant_130", "sma"}:
            raise LeveragedEtfRulesError(f"arms.{name}: unknown construction {construction!r}")
        band = entry.get("band", 0.0)
        out[name] = Arm(
            name=name,
            role=_text(entry, "role", where=f"arms.{name}"),
            construction=construction,
            leverage=_number(entry, "leverage", where=f"arms.{name}"),
            band=float(band)
            if isinstance(band, int | float) and not isinstance(band, bool)
            else 0.0,
            note=str(entry.get("note") or ""),
        )
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class RuleSettings:
    lookback: int
    band: float
    lag: int
    lag_sensitivity: int
    price_proxy_yield: float


def read_rule(specification: Specification) -> RuleSettings:
    parameters = _mapping(specification.parameters, where="parameters")
    rule = _mapping(_at(parameters, "rule", where="parameters"), where="rule")
    return RuleSettings(
        lookback=int(_number(rule, "lookback_days", where="rule")),
        band=_number(rule, "band", where="rule"),
        lag=int(_number(rule, "execution_lag_days", where="rule")),
        lag_sensitivity=int(_number(rule, "execution_lag_sensitivity_days", where="rule")),
        price_proxy_yield=_number(rule, "price_proxy_dividend_yield_percent", where="rule") / 100.0,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Window:
    id: str
    start: str | None
    end: str | None


def read_windows(specification: Specification, key: str = "windows") -> tuple[Window, ...]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = (
        parameters
        if key == "windows"
        else _mapping(_at(parameters, "hfea", where="parameters"), where="hfea")
    )
    out: list[Window] = []
    for item in _sequence(_at(block, "windows", where=key), where=key):
        entry = _mapping(item, where=f"{key}[]")
        start, end = entry.get("start"), entry.get("end")
        out.append(
            Window(
                id=_text(entry, "id", where=f"{key}[]"),
                start=str(start) if isinstance(start, str) else None,
                end=str(end) if isinstance(end, str) else None,
            )
        )
    return tuple(out)


def _episodes(specification: Specification, key: str) -> list[tuple[str, str, str]]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "crisis_episodes", where="parameters"), where="episodes")
    out: list[tuple[str, str, str]] = []
    for item in _sequence(_at(block, key, where="crisis_episodes"), where=key):
        entry = _mapping(item, where=f"crisis_episodes.{key}[]")
        out.append(
            (
                _text(entry, "name", where=key),
                _text(entry, "start", where=key),
                _text(entry, "end", where=key),
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Building the daily paths
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class DailyPaths:
    """Every arm's total return on the full daily index, nan before it is formed."""

    dates: tuple[str, ...]
    gaps: IntArray
    cash: FloatArray
    totals: dict[str, FloatArray]
    positions: dict[str, FloatArray]
    controls: dict[str, FloatArray]
    exposure_controls: dict[str, tuple[FloatArray, float]]
    first_live: int


def build_daily_paths(
    raw: RawSeries,
    *,
    arms: Mapping[str, Arm],
    rule: RuleSettings,
    costs: Costs,
    spread_bp: float,
    lag: int,
    dividend_yield: float,
    one_way_cost: float,
) -> DailyPaths:
    gaps = calendar_day_gaps(raw.dates)
    levels = total_return_levels(
        raw.market_excess, raw.cash, day_gaps=gaps, dividend_yield=dividend_yield
    )
    funds: dict[float, FloatArray] = {}

    def fund(leverage: float) -> FloatArray:
        if leverage not in funds:
            funds[leverage] = levered_fund_returns(
                raw.market_excess,
                raw.cash,
                gaps,
                leverage=leverage,
                fee_bp=costs.fee_for(leverage),
                spread_bp=spread_bp,
            )
        return funds[leverage]

    totals: dict[str, FloatArray] = {}
    positions: dict[str, FloatArray] = {}
    exposure: dict[str, tuple[FloatArray, float]] = {}
    signals: dict[float, FloatArray] = {}
    first_live = 0
    for name, arm in arms.items():
        if arm.construction in {"buy_and_hold", "constant_130"}:
            totals[name] = fund(arm.leverage)
            continue
        if arm.band not in signals:
            signals[arm.band] = moving_average_signal(levels, window=rule.lookback, band=arm.band)
        position = positions_from_signal(signals[arm.band], lag=lag)
        positions[name] = position
        totals[name] = rule_returns(
            fund(arm.leverage), raw.cash, position, one_way_cost=one_way_cost
        )
        exposure[name] = exposure_matched_returns(fund(arm.leverage), raw.cash, position)
        first_live = max(first_live, _live_slice(position)[0])
    controls = {"cheap": fund(1.0), "leverage_matched_130": fund(1.3)}
    return DailyPaths(
        dates=raw.dates,
        gaps=gaps,
        cash=raw.cash,
        totals=totals,
        positions=positions,
        controls=controls,
        exposure_controls=exposure,
        first_live=first_live,
    )


def _window_indices(labels: Sequence[str], window: Window, *, first_live: int) -> IntArray:
    keep = [
        i
        for i, label in enumerate(labels)
        if i >= first_live
        and (window.start is None or label >= window.start)
        and (window.end is None or label <= window.end)
    ]
    if len(keep) < 2:
        raise LeveragedEtfRulesError(f"window {window.id} selects {len(keep)} rows")
    return np.asarray(keep, dtype=np.int64)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class Comparison:
    control: str
    definition: str
    gap: GapStatistics | None
    identical: bool = False
    adjusted_p: float | None = None
    stress_gap_pp_yr: float | None = None
    status: str = "not-scored"
    clause: str = ""
    sensitivities: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict[str, JsonValue]:
        g = self.gap
        return {
            "control": self.control,
            "control_definition": self.definition,
            "identical_construction": self.identical,
            "gap_pp_yr": None if g is None else round(g.gap_pp_yr, 4),
            "hac_interval_pp_yr": (
                None if g is None else [round(g.hac_interval[0], 4), round(g.hac_interval[1], 4)]
            ),
            "block_bootstrap_interval_pp_yr": (
                None
                if g is None
                else [round(g.bootstrap_interval[0], 4), round(g.bootstrap_interval[1], 4)]
            ),
            "mde_80pc_power_pp_yr": None if g is None else round(g.mde_pp_yr, 4),
            "hac_p_value": None if g is None else round(g.p_value, 5),
            "tracking_error_pct": None if g is None else round(g.tracking_error_pct, 3),
            "years_to_distinguish_at_80pc_power": (
                None
                if g is None or not math.isfinite(g.years_to_distinguish)
                else round(g.years_to_distinguish, 1)
            ),
            "benjamini_hochberg_adjusted_p": (
                None if self.adjusted_p is None else round(self.adjusted_p, 5)
            ),
            "stress_spread_gap_pp_yr": (
                None if self.stress_gap_pp_yr is None else round(self.stress_gap_pp_yr, 4)
            ),
            "status": self.status,
            "falsifier_clause": self.clause,
            "sensitivity_gaps_pp_yr": {k: round(v, 4) for k, v in self.sensitivities.items()},
        }


def apply_falsifier(comparison: Comparison, *, q: float) -> None:
    gap = comparison.gap
    if gap is None or comparison.identical:
        comparison.status, comparison.clause = "not-scored", "identical construction"
        return
    if gap.gap_pp_yr <= 0.0:
        comparison.status, comparison.clause = "rejected", "(a) gap at or below zero"
        return
    if gap.gap_pp_yr < gap.mde_pp_yr:
        comparison.status, comparison.clause = (
            "unresolved",
            f"(b) the gap {gap.gap_pp_yr:+.2f} pp/yr is inside this design's own "
            f"{gap.mde_pp_yr:.2f} pp/yr detection floor at 80% power",
        )
        return
    if comparison.adjusted_p is not None and comparison.adjusted_p > q:
        comparison.status, comparison.clause = (
            "unresolved",
            f"(c) Benjamini-Hochberg adjusted p = {comparison.adjusted_p:.3f} exceeds q = {q:.2f}",
        )
        return
    if comparison.stress_gap_pp_yr is not None and comparison.stress_gap_pp_yr <= 0.0:
        comparison.status, comparison.clause = (
            "unresolved",
            f"(d) the gap changes sign at the stress spread, reading "
            f"{comparison.stress_gap_pp_yr:+.2f} pp/yr",
        )
        return
    comparison.status, comparison.clause = "exploratory", "(e) survived every clause"


@dataclass(slots=True, kw_only=True)
class WindowResult:
    window: Window
    frequency: str
    labels: tuple[str, ...]
    years: float
    descriptives: dict[str, Descriptives]
    comparisons: dict[str, dict[str, Comparison]]
    episodes: dict[str, dict[str, dict[str, JsonValue]]]
    control_descriptives: dict[str, Descriptives]


def _point_gap(a: FloatArray, b: FloatArray, *, years: float) -> float:
    return float(np.sum(a - b)) / years * 100.0


def score_daily_window(
    window: Window,
    *,
    base: DailyPaths,
    variants: Mapping[str, DailyPaths],
    stress: DailyPaths,
    arms: Mapping[str, Arm],
    specification: Specification,
    rng: np.random.Generator,
) -> WindowResult:
    parameters = _mapping(specification.parameters, where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    n_lags = int(_number(parameters, "hac_lags_daily", where="parameters"))
    block = _number(parameters, "bootstrap_block_days", where="parameters")
    chunk = int(_number(parameters, "bootstrap_chunk_rows", where="parameters"))
    resamples = specification.inference.resamples
    keep = _window_indices(base.dates, window, first_live=base.first_live)
    labels = tuple(base.dates[i] for i in keep)
    years = _span_years(labels, base.gaps[keep])
    rows_per_year = keep.size / years
    cash = base.cash[keep]

    controls = {name: series[keep] for name, series in base.controls.items()}
    definitions = {
        "cheap": "unlevered index fund at 3 bp, held",
        "leverage_matched_130": "continuous daily-reset 1.3x exposure, 15.9 bp, spread on 0.30",
    }
    comparisons: dict[str, dict[str, Comparison]] = {}
    descriptives: dict[str, Descriptives] = {}
    episodes: dict[str, dict[str, dict[str, JsonValue]]] = {}
    families: dict[str, list[str]] = {}
    episode_windows = _episodes(specification, "daily")
    for name, arm in arms.items():
        total = base.totals[name][keep]
        position = base.positions.get(name)
        descriptives[name] = describe(
            total, cash, years=years, position=None if position is None else position[keep]
        )
        episodes[name] = {
            e: episode_summary(labels, total, start=s, end=t) for e, s, t in episode_windows
        }
        comparisons[name] = {}
        candidates: dict[str, tuple[FloatArray, str]] = {
            c: (series, definitions[c]) for c, series in controls.items()
        }
        if name in base.exposure_controls:
            series, w = base.exposure_controls[name]
            candidates["exposure_matched"] = (
                series[keep],
                f"the same fund at a constant {w:.4f} weight, remainder in bills, no cost",
            )
        elif arm.construction == "buy_and_hold":
            candidates["exposure_matched"] = (
                total,
                "the arm itself: buy-and-hold is its own exposure match",
            )
        for control, (series, definition) in candidates.items():
            difference = total - series
            identical = float(np.std(difference)) == 0.0
            stats = None
            if not identical:
                stats = gap_statistics(
                    difference,
                    rows_per_year=rows_per_year,
                    n_lags=n_lags,
                    rng=rng,
                    block=block,
                    resamples=resamples,
                    chunk=chunk,
                )
            comparison = Comparison(
                control=control, definition=definition, gap=stats, identical=identical
            )
            if not identical:
                comparison.stress_gap_pp_yr = _control_gap(
                    stress, name, control, keep=keep, years=years
                )
                for label, paths in variants.items():
                    comparison.sensitivities[label] = _control_gap(
                        paths, name, control, keep=keep, years=years
                    )
                families.setdefault(control, []).append(name)
            comparisons[name][control] = comparison

    for control, members in families.items():
        p_values = [comparisons[n][control].gap.p_value for n in members]  # type: ignore[union-attr]
        adjusted = benjamini_hochberg(p_values, alpha=q)
        for n, value in zip(members, adjusted.adjusted_p_values, strict=True):
            comparisons[n][control].adjusted_p = float(value)
    for by_control in comparisons.values():
        for comparison in by_control.values():
            apply_falsifier(comparison, q=q)

    control_descriptives = {
        name: describe(series, cash, years=years) for name, series in controls.items()
    }
    return WindowResult(
        window=window,
        frequency="daily",
        labels=labels,
        years=years,
        descriptives=descriptives,
        comparisons=comparisons,
        episodes=episodes,
        control_descriptives=control_descriptives,
    )


def _control_gap(
    paths: DailyPaths, arm: str, control: str, *, keep: IntArray, years: float
) -> float:
    total = paths.totals[arm][keep]
    if control == "exposure_matched":
        series = paths.exposure_controls[arm][0][keep]
    else:
        series = paths.controls[control][keep]
    return _point_gap(total, series, years=years)


# --------------------------------------------------------------------------- #
# HFEA on monthly data
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class MonthlyPanel:
    months: tuple[str, ...]
    hfea: FloatArray
    cash: FloatArray
    controls: dict[str, FloatArray]
    equity_leg: FloatArray
    treasury_leg: FloatArray


def build_hfea(
    raw: RawSeries, base: DailyPaths, *, specification: Specification, costs: Costs
) -> MonthlyPanel:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "hfea", where="parameters"), where="hfea")
    equity_weight = _number(block, "equity_weight", where="hfea")
    treasury_weight = _number(block, "treasury_weight", where="hfea")
    equity_leverage = _number(block, "equity_leverage", where="hfea")
    treasury_leverage = _number(block, "treasury_leverage", where="hfea")
    every = int(_number(block, "rebalance_every_months", where="hfea"))

    equity_fund = levered_fund_returns(
        raw.market_excess,
        raw.cash,
        base.gaps,
        leverage=equity_leverage,
        fee_bp=costs.fee_for(equity_leverage),
        spread_bp=costs.spread_bp,
    )
    months, equity_monthly = compound_monthly(raw.dates, equity_fund)
    _, cheap_monthly = compound_monthly(raw.dates, base.controls["cheap"])
    _, lev_monthly = compound_monthly(raw.dates, base.controls["leverage_matched_130"])
    _, cash_monthly = compound_monthly(raw.dates, raw.cash)
    charge = ((treasury_leverage - 1.0) * costs.spread_bp + costs.fee_treasury_3x_bp) / 10_000.0
    keep: list[int] = []
    treasury: list[float] = []
    for i, month in enumerate(months):
        if month in raw.ltr and month in raw.monthly_rf and math.isfinite(equity_monthly[i]):
            rf = raw.monthly_rf[month]
            treasury.append(
                rf + treasury_leverage * (raw.ltr[month] - rf) - charge / _MONTHS_PER_YEAR
            )
            keep.append(i)
    if len(keep) < 3 * _MONTHS_PER_YEAR:
        raise LeveragedEtfRulesError("the HFEA panel holds fewer than three years")
    index = np.asarray(keep, dtype=np.int64)
    legs = np.column_stack([equity_monthly[index], np.asarray(treasury, dtype=np.float64)])
    hfea = rebalanced_mix(
        legs, (equity_weight, treasury_weight), every=every, one_way_cost=costs.one_way_cost
    )
    return MonthlyPanel(
        months=tuple(months[i] for i in keep),
        hfea=hfea,
        cash=cash_monthly[index],
        controls={"cheap": cheap_monthly[index], "leverage_matched_130": lev_monthly[index]},
        equity_leg=legs[:, 0],
        treasury_leg=legs[:, 1],
    )


def score_monthly_window(
    window: Window,
    panel: MonthlyPanel,
    *,
    specification: Specification,
    rng: np.random.Generator,
    stress_hfea: FloatArray,
) -> WindowResult:
    parameters = _mapping(specification.parameters, where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")
    chunk = int(_number(parameters, "bootstrap_chunk_rows", where="parameters"))
    keep = _window_indices(panel.months, window, first_live=0)
    labels = tuple(panel.months[i] for i in keep)
    years = keep.size / _MONTHS_PER_YEAR
    cash = panel.cash[keep]
    total = panel.hfea[keep]
    episodes = _episodes(specification, "monthly")
    definitions = {
        "cheap": "unlevered index fund at 3 bp, compounded monthly",
        "leverage_matched_130": "continuous 1.3x exposure, compounded monthly",
    }
    comparisons: dict[str, Comparison] = {}
    members: list[str] = []
    for control, series in panel.controls.items():
        difference = total - series[keep]
        stats = gap_statistics(
            difference,
            rows_per_year=float(_MONTHS_PER_YEAR),
            n_lags=None,
            rng=rng,
            block=block,
            resamples=specification.inference.resamples,
            chunk=chunk,
        )
        comparison = Comparison(control=control, definition=definitions[control], gap=stats)
        comparison.stress_gap_pp_yr = _point_gap(stress_hfea[keep], series[keep], years=years)
        comparisons[control] = comparison
        members.append(control)
    adjusted = benjamini_hochberg([comparisons[c].gap.p_value for c in members], alpha=q)  # type: ignore[union-attr]
    for c, value in zip(members, adjusted.adjusted_p_values, strict=True):
        comparisons[c].adjusted_p = float(value)
        apply_falsifier(comparisons[c], q=q)
    descriptives = {"hfea_55_45": describe(total, cash, years=years)}
    descriptives["hfea_equity_leg_3x"] = describe(panel.equity_leg[keep], cash, years=years)
    descriptives["hfea_treasury_leg_3x"] = describe(panel.treasury_leg[keep], cash, years=years)
    return WindowResult(
        window=window,
        frequency="monthly",
        labels=labels,
        years=years,
        descriptives=descriptives,
        comparisons={"hfea_55_45": comparisons},
        episodes={
            "hfea_55_45": {
                e: episode_summary(labels, total, start=s, end=t) for e, s, t in episodes
            },
            "hfea_equity_leg_3x": {
                e: episode_summary(labels, panel.equity_leg[keep], start=s, end=t)
                for e, s, t in episodes
            },
            "hfea_treasury_leg_3x": {
                e: episode_summary(labels, panel.treasury_leg[keep], start=s, end=t)
                for e, s, t in episodes
            },
        },
        control_descriptives={
            name: describe(series[keep], cash, years=years)
            for name, series in panel.controls.items()
        },
    )


# --------------------------------------------------------------------------- #
# Deflation over the declared grid
# --------------------------------------------------------------------------- #


def deflate_grid(
    raw: RawSeries,
    base: DailyPaths,
    *,
    specification: Specification,
    costs: Costs,
    rule: RuleSettings,
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    grid = _mapping(_at(parameters, "deflation_grid", where="parameters"), where="deflation_grid")
    lookbacks = [
        int(x) for x in _numbers(_at(grid, "lookbacks_days", where="grid"), where="lookbacks")
    ]
    bands = list(_numbers(_at(grid, "bands", where="grid"), where="bands"))
    leverages = list(_numbers(_at(grid, "leverage_levels", where="grid"), where="leverages"))
    lag = int(_number(grid, "execution_lag_days", where="grid"))
    also = list(_numbers(_at(grid, "trial_counts_also_reported", where="grid"), where="counts"))
    levels = total_return_levels(raw.market_excess, raw.cash)
    funds = {
        L: levered_fund_returns(
            raw.market_excess,
            raw.cash,
            base.gaps,
            leverage=L,
            fee_bp=costs.fee_for(L),
            spread_bp=costs.spread_bp,
        )
        for L in leverages
    }
    burn = max(lookbacks) + lag + 1
    labels: list[str] = []
    actives: list[FloatArray] = []
    for L in leverages:
        for band in bands:
            for lookback in lookbacks:
                signal = moving_average_signal(levels, window=lookback, band=band)
                position = positions_from_signal(signal, lag=lag)
                total = rule_returns(funds[L], raw.cash, position, one_way_cost=costs.one_way_cost)
                # Re-match the exposure on the common window so every column is a
                # zero-beta active return on the same days.
                live = position[burn:]
                w = float(np.mean(live))
                active = total[burn:] - (w * funds[L][burn:] + (1.0 - w) * raw.cash[burn:])
                labels.append(f"sma{lookback}_{L:.0f}x_band{band:g}")
                actives.append(active)
    matrix = np.column_stack(actives)
    # A rule that never left the market on this window has no active return and
    # no Sharpe ratio; it is dropped from the trial family and named.
    live_columns = matrix.std(axis=0, ddof=1) > 0.0
    dropped = [label for label, keep in zip(labels, live_columns, strict=True) if not keep]
    labels = [label for label, keep in zip(labels, live_columns, strict=True) if keep]
    matrix = matrix[:, live_columns]
    if matrix.shape[1] < 2:
        raise LeveragedEtfRulesError("fewer than two grid rules have any timing content")
    sharpes = matrix.mean(axis=0) / matrix.std(axis=0, ddof=1)
    dispersion = trial_dispersion_from_sharpes(sharpes)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", LinearDependenceWarning)
        rho = mean_off_diagonal_correlation(matrix)
    effective = effective_number_of_trials(len(labels), rho)
    rows_per_year = matrix.shape[0] / _span_years(raw.dates[burn:], base.gaps[burn:])
    candidates: dict[str, JsonValue] = {}
    best = int(np.argmax(sharpes))
    wanted = [
        f"sma{rule.lookback}_{L:.0f}x_band{band:g}"
        for L in leverages
        for band in bands
        if f"sma{rule.lookback}_{L:.0f}x_band{band:g}" in labels
    ]
    for label in dict.fromkeys([*wanted, labels[best]]):
        index = labels.index(label)
        series = matrix[:, index]
        centred = series - series.mean()
        variance = float(np.mean(centred**2))
        skew = float(np.mean(centred**3) / variance**1.5)
        kurt = float(np.mean(centred**4) / variance**2)
        rows: list[JsonValue] = []
        for trials in [effective, *also]:
            result = deflated_sharpe_ratio(
                float(sharpes[index]),
                trial_dispersion=dispersion,
                n_trials=trials,
                n_observations=matrix.shape[0],
                skewness=skew,
                kurtosis=kurt,
            )
            rows.append(
                {
                    "n_trials": round(trials, 2),
                    "sharpe_threshold_annualised": round(
                        result.sharpe_threshold * math.sqrt(rows_per_year), 4
                    ),
                    "deflated_significance": round(result.deflated_significance, 4),
                }
            )
        candidates[label] = {
            "active_sharpe_annualised": round(float(sharpes[index]) * math.sqrt(rows_per_year), 4),
            "active_mean_pp_yr": round(float(series.mean()) * rows_per_year * 100.0, 3),
            "skewness": round(skew, 3),
            "kurtosis": round(kurt, 2),
            "is_best_in_grid": index == best,
            "by_trial_count": rows,
        }
    return {
        "rules": len(labels),
        "rules_dropped_for_no_timing_content": dropped,
        "rows": int(matrix.shape[0]),
        "window": f"{raw.dates[burn]}..{raw.dates[-1]}",
        "trial_sharpe_dispersion_per_row": round(dispersion, 6),
        "mean_off_diagonal_correlation_of_active_returns": round(rho, 4),
        "effective_independent_trials": round(effective, 2),
        "best_in_grid": labels[best],
        "candidates": candidates,
        "note": (
            "Deflated on the beta-matched ACTIVE return. The effective count is the linear "
            "reading of Bailey and Lopez de Prado, marked UNVERIFIED in inference/deflated_sharpe; "
            "the grid is a lower bound on the literature's search, so every count here is a "
            "lower bound and every significance an upper bound."
        ),
    }


# --------------------------------------------------------------------------- #
# After tax
# --------------------------------------------------------------------------- #


def after_tax(
    raw: RawSeries,
    base: DailyPaths,
    *,
    arms: Mapping[str, Arm],
    specification: Specification,
    costs: Costs,
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "after_tax", where="parameters"), where="after_tax")
    window_id = _text(block, "window", where="after_tax")
    window = next(w for w in read_windows(specification) if w.id == window_id)
    names = [str(x) for x in _sequence(_at(block, "arms", where="after_tax"), where="arms")]
    yields = _mapping(_at(block, "dividend_yield_percent", where="after_tax"), where="yields")
    long_term = int(_number(block, "long_term_holding_trading_days", where="after_tax"))
    keep = _window_indices(base.dates, window, first_live=base.first_live)
    years = _span_years(tuple(base.dates[i] for i in keep), base.gaps[keep])
    per_year = round(keep.size / years)
    cash = base.cash[keep]

    funds: dict[float, FloatArray] = {}
    for name in names:
        L = arms[name].leverage
        if L not in funds:
            funds[L] = levered_fund_returns(
                raw.market_excess,
                raw.cash,
                base.gaps,
                leverage=L,
                fee_bp=costs.fee_for(L),
                spread_bp=costs.spread_bp,
            )[keep]

    def position_for(name: str) -> FloatArray:
        p = base.positions.get(name)
        return np.ones(keep.size) if p is None else p[keep]

    regimes = {"top": TOP_BRACKET, "upper_middle": UPPER_MIDDLE_BRACKET}
    rows: dict[str, JsonValue] = {}
    sheltered_growth: dict[str, float] = {}
    for name in names:
        arm = arms[name]
        outcome = sheltered_path(
            label=name,
            position=position_for(name),
            risky_total=funds[arm.leverage],
            cash=cash,
            one_way_cost=costs.one_way_cost,
            periods_per_year=per_year,
        )
        sheltered_growth[name] = outcome.annualised_after_tax_growth
        rows[f"{name}|sheltered"] = {
            "arm": name,
            "account": "sheltered",
            "terminal_wealth": round(outcome.terminal_after_disposal, 3),
            "tax_paid": 0.0,
            "growth_pct_yr": round(outcome.annualised_after_tax_growth * 100.0, 3),
        }
    for bracket, regime in regimes.items():
        for disposal in (Disposal.STEP_UP, Disposal.LIQUIDATE):
            growth: dict[str, float] = {}
            for name in names:
                arm = arms[name]
                yield_key = "index_1x" if arm.leverage == 1.0 else "levered"
                assumptions = TaxableAssumptions(
                    ordinary_rate=regime.ordinary,
                    long_term_rate=regime.capital_gain,
                    dividend_yield=_number(yields, yield_key, where="yields") / 100.0,
                    long_term_months=long_term,
                )
                outcome = taxable_path(
                    label=name,
                    position=position_for(name),
                    risky_total=funds[arm.leverage],
                    cash=cash,
                    assumptions=assumptions,
                    one_way_cost=costs.one_way_cost,
                    disposal=disposal,
                    periods_per_year=per_year,
                )
                growth[name] = outcome.annualised_after_tax_growth
                rows[f"{name}|{bracket}|{disposal.value}"] = {
                    "arm": name,
                    "account": f"taxable {bracket} {disposal.value}",
                    "terminal_wealth": round(outcome.terminal_after_disposal, 3),
                    "tax_paid": round(outcome.cumulative_tax, 3),
                    "growth_pct_yr": round(outcome.annualised_after_tax_growth * 100.0, 3),
                    "realised_short_term_gain": round(outcome.realised_short_term_gain, 3),
                    "realised_long_term_gain": round(outcome.realised_long_term_gain, 3),
                    "unused_loss_carryforward": round(outcome.unused_loss_carryforward, 3),
                }
            for name in names:
                entry = rows[f"{name}|{bracket}|{disposal.value}"]
                assert isinstance(entry, dict)
                taxable_shortfall = (growth[name] - growth["hold_1x"]) * 100.0
                sheltered_shortfall = (sheltered_growth[name] - sheltered_growth["hold_1x"]) * 100.0
                entry["shortfall_vs_hold_1x_same_account_pp_yr"] = round(taxable_shortfall, 3)
                entry["tax_cost_of_the_arm_pp_yr"] = round(
                    sheltered_shortfall - taxable_shortfall, 3
                )
    return {
        "window": f"{base.dates[keep[0]]}..{base.dates[keep[-1]]}",
        "years": round(years, 2),
        "periods_per_year_used": per_year,
        "rows": rows,
        "note": (
            "Tax cost of an arm is its shortfall against buy-and-hold of the unlevered index "
            "in the sheltered account less the same shortfall in the taxable account; a "
            "positive number is what the account costs the rule. Losses carry forward against "
            "later capital gains only; the 3,000 dollar ordinary offset is omitted."
        ),
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _fmt(value: float | None, digits: int = 2) -> str:
    return "--" if value is None or not math.isfinite(value) else f"{value:+.{digits}f}"


def _cell(comparison: Comparison | None) -> str:
    if comparison is None:
        return "--"
    if comparison.gap is None:
        return "identical" if comparison.identical else "--"
    g = comparison.gap
    years = "inf" if not math.isfinite(g.years_to_distinguish) else f"{g.years_to_distinguish:.0f}y"
    return (
        f"{g.gap_pp_yr:+.2f} [{g.hac_interval[0]:+.2f}, {g.hac_interval[1]:+.2f}] "
        f"MDE {g.mde_pp_yr:.2f} {years} `{comparison.status}`"
    )


def _window_tables(result: WindowResult) -> list[str]:
    lines = [
        f"\n## Window `{result.window.id}` ({result.frequency}): "
        f"{result.labels[0]}..{result.labels[-1]}, {len(result.labels)} rows, "
        f"{result.years:.1f} years\n",
        "\n### Arms (descriptive)\n",
        "| arm | CAGR % | arith % | vol % | Sharpe | max DD % | under water (yrs) | "
        "in market | round trips/yr | terminal $1 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in [*result.descriptives.items(), *result.control_descriptives.items()]:
        label = name if name in result.descriptives else f"control: {name}"
        lines.append(
            f"| `{label}` | {d.cagr_pct:.2f} | {d.arithmetic_mean_pct:.2f} | "
            f"{d.volatility_pct:.2f} | "
            f"{d.sharpe:.3f} | {d.max_drawdown_pct:.2f} | {d.time_under_water_years:.1f} | "
            f"{'--' if d.time_in_market is None else f'{d.time_in_market:.3f}'} | "
            f"{'--' if d.round_trips_per_year is None else f'{d.round_trips_per_year:.2f}'} | "
            f"{d.terminal_wealth:.2f} |"
        )
    lines += [
        "\n### Gaps: point [95% HAC] floor years status\n",
        "| arm | vs cheap 1x | vs 1.3x | vs exposure-matched |",
        "| --- | --- | --- | --- |",
    ]
    for name, by_control in result.comparisons.items():
        lines.append(
            f"| `{name}` | {_cell(by_control.get('cheap'))} | "
            f"{_cell(by_control.get('leverage_matched_130'))} | "
            f"{_cell(by_control.get('exposure_matched'))} |"
        )
    lines += [
        "\n### Sensitivities: point gap pp/yr against each control "
        "(base / stress spread / other)\n",
        "| arm | control | base | 80 bp spread | sensitivities |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for name, by_control in result.comparisons.items():
        for control, c in by_control.items():
            if c.gap is None:
                continue
            extra = ", ".join(f"{k} {_fmt(v)}" for k, v in c.sensitivities.items())
            lines.append(
                f"| `{name}` | {control} | {_fmt(c.gap.gap_pp_yr)} | "
                f"{_fmt(c.stress_gap_pp_yr)} | {extra or '--'} |"
            )
    names = list(result.episodes)
    episode_names = list(result.episodes[names[0]]) if names else []
    lines += [
        "\n### Crisis episodes: cumulative % (peak-to-trough %); * partial, n/c not covered\n",
        "| arm | " + " | ".join(episode_names) + " |",
        "| --- | " + " | ".join("---:" for _ in episode_names) + " |",
    ]
    for name in names:
        cells = []
        for e in episode_names:
            entry = result.episodes[name][e]
            if not entry.get("covered"):
                cells.append("n/c")
                continue
            star = "*" if entry.get("partial") else ""
            cells.append(f"{entry['cumulative_pct']}{star} ({entry['peak_to_trough_pct']})")
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    return lines


def _deflation_table(block: Mapping[str, JsonValue]) -> list[str]:
    lines = [
        f"\n## Deflation over the declared grid: {block['rules']} rules, {block['rows']} rows, "
        f"{block['window']}\n",
        f"trial Sharpe dispersion {block['trial_sharpe_dispersion_per_row']}; mean off-diagonal "
        "correlation of active returns "
        f"{block['mean_off_diagonal_correlation_of_active_returns']}; "
        f"effective independent trials {block['effective_independent_trials']}; best in grid "
        f"`{block['best_in_grid']}`\n",
        "| candidate | active SR ann. | active mean pp/yr | N trials | SR* ann. | DSR |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    candidates = block["candidates"]
    assert isinstance(candidates, Mapping)
    for label, raw_entry in candidates.items():
        entry = raw_entry
        assert isinstance(entry, Mapping)
        rows = entry["by_trial_count"]
        assert isinstance(rows, Sequence)
        for i, raw_row in enumerate(rows):
            row = raw_row
            assert isinstance(row, Mapping)
            lines.append(
                f"| {label if i == 0 else ''} | "
                f"{entry['active_sharpe_annualised'] if i == 0 else ''} | "
                f"{entry['active_mean_pp_yr'] if i == 0 else ''} | {row['n_trials']} | "
                f"{row['sharpe_threshold_annualised']} | {row['deflated_significance']} |"
            )
    return lines


def _tax_table(block: Mapping[str, JsonValue]) -> list[str]:
    lines = [
        f"\n## After tax on {block['window']} ({block['years']} years, "
        f"{block['periods_per_year_used']} rows a year)\n",
        "| arm | account | terminal $1 | tax paid | growth %/yr | vs hold_1x same account "
        "| tax cost pp/yr |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    rows = block["rows"]
    assert isinstance(rows, Mapping)
    for raw_row in rows.values():
        row = raw_row
        assert isinstance(row, Mapping)
        lines.append(
            f"| `{row['arm']}` | {row['account']} | {row['terminal_wealth']} | {row['tax_paid']} | "
            f"{row['growth_pct_yr']} | "
            f"{row.get('shortfall_vs_hold_1x_same_account_pp_yr', '--')} | "
            f"{row.get('tax_cost_of_the_arm_pp_yr', '--')} |"
        )
    return lines


def _window_json(result: WindowResult) -> dict[str, JsonValue]:
    return {
        "id": result.window.id,
        "frequency": result.frequency,
        "window": f"{result.labels[0]}..{result.labels[-1]}",
        "rows": len(result.labels),
        "years": round(result.years, 3),
        "arms": {
            name: {
                "descriptives": d.to_json(),
                "episodes": {e: dict(v) for e, v in result.episodes.get(name, {}).items()},
                "comparisons": {
                    c: comp.to_json() for c, comp in result.comparisons.get(name, {}).items()
                },
            }
            for name, d in result.descriptives.items()
        },
        "controls": {name: d.to_json() for name, d in result.control_descriptives.items()},
    }


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    parameters = _mapping(specification.parameters, where="parameters")
    raw = load_series(specification)
    costs = read_costs(specification)
    arms = read_arms(specification)
    rule = read_rule(specification)
    sensitivities = _mapping(_at(parameters, "sensitivities", where="parameters"), where="sens")
    stress_bp = _number(sensitivities, "spread_stress_basis_points", where="sens")
    lag_alt = int(_number(sensitivities, "execution_lag_days", where="sens"))
    proxy_yield = _number(sensitivities, "price_proxy_dividend_yield_percent", where="sens") / 100.0

    def paths(*, spread: float, lag: int, dividend: float, cost: float) -> DailyPaths:
        return build_daily_paths(
            raw,
            arms=arms,
            rule=rule,
            costs=costs,
            spread_bp=spread,
            lag=lag,
            dividend_yield=dividend,
            one_way_cost=cost,
        )

    base = paths(spread=costs.spread_bp, lag=rule.lag, dividend=0.0, cost=costs.one_way_cost)
    stress = paths(spread=stress_bp, lag=rule.lag, dividend=0.0, cost=costs.one_way_cost)
    variants: dict[str, DailyPaths] = {
        f"lag{lag_alt}": paths(
            spread=costs.spread_bp, lag=lag_alt, dividend=0.0, cost=costs.one_way_cost
        ),
        f"price_proxy_{proxy_yield * 100:g}pct": paths(
            spread=costs.spread_bp, lag=rule.lag, dividend=proxy_yield, cost=costs.one_way_cost
        ),
    }
    for cost in costs.cost_grid:
        if cost != costs.one_way_cost:
            variants[f"cost{cost * 10_000:g}bp"] = paths(
                spread=costs.spread_bp, lag=rule.lag, dividend=0.0, cost=cost
            )
    # The lag-0 variant is formed one day earlier than the base; score every
    # variant on the base's common window so no arm is credited with an extra day.
    for v in variants.values():
        v.first_live = base.first_live

    results: list[WindowResult] = [
        score_daily_window(
            window,
            base=base,
            variants=variants,
            stress=stress,
            arms=arms,
            specification=specification,
            rng=context.rng,
        )
        for window in read_windows(specification)
    ]
    hfea = build_hfea(raw, base, specification=specification, costs=costs)
    stress_costs = Costs(
        fee_index_bp=costs.fee_index_bp,
        fee_2x_bp=costs.fee_2x_bp,
        fee_3x_bp=costs.fee_3x_bp,
        fee_treasury_3x_bp=costs.fee_treasury_3x_bp,
        fee_130_bp=costs.fee_130_bp,
        spread_bp=stress_bp,
        stress_spread_bp=stress_bp,
        one_way_cost=costs.one_way_cost,
        cost_grid=costs.cost_grid,
    )
    hfea_stress = build_hfea(raw, stress, specification=specification, costs=stress_costs)
    if hfea_stress.months != hfea.months:
        raise LeveragedEtfRulesError("the stress HFEA panel is not on the base panel's months")
    results += [
        score_monthly_window(
            window, hfea, specification=specification, rng=context.rng, stress_hfea=hfea_stress.hfea
        )
        for window in read_windows(specification, key="hfea")
    ]
    deflation = deflate_grid(raw, base, specification=specification, costs=costs, rule=rule)
    tax = after_tax(raw, base, arms=arms, specification=specification, costs=costs)

    in_estimates = {
        str(x)
        for x in _sequence(_at(parameters, "controls_in_estimates", where="parameters"), where="c")
    }
    estimates: list[Estimate] = []
    resolved: list[str] = []
    scored = 0
    for result in results:
        for name, by_control in result.comparisons.items():
            for control, comparison in by_control.items():
                g = comparison.gap
                if g is None or comparison.identical:
                    continue
                scored += 1
                label = f"{result.window.id}:{name} vs {control}"
                if comparison.status == "exploratory":
                    resolved.append(label)
                if control not in in_estimates:
                    continue
                estimates.append(
                    Estimate(
                        name=f"arithmetic_gap[{label}]",
                        value=g.gap_pp_yr,
                        units="percentage points per year",
                        interval=g.hac_interval,
                        interval_method=(
                            "Newey-West HAC standard error of the mean paired difference, "
                            "95% normal interval; block bootstrap interval in diagnostics"
                        ),
                        cost_basis=CostBasis.NET_PESSIMISTIC,
                        n_obs=g.rows,
                        notes=(
                            f"{comparison.status}: {comparison.clause}. Tracking error "
                            f"{g.tracking_error_pct:.2f}%; years to distinguish "
                            f"{g.years_to_distinguish:.0f}."
                        ),
                    )
                )
                estimates.append(
                    Estimate(
                        name=f"minimum_detectable_effect[{label}]",
                        value=g.mde_pp_yr,
                        units="percentage points per year",
                        cost_basis=CostBasis.NOT_APPLICABLE,
                        n_obs=g.rows,
                        notes=(
                            "80% power, two-sided at 0.05, from this comparison's HAC "
                            "standard error."
                        ),
                        uncertainty_unavailable_reason=(
                            "a detection floor is a property of the design, not an estimate of "
                            "a quantity in the world, so it carries no interval"
                        ),
                    )
                )
    status = ResultStatus.EXPLORATORY if resolved else ResultStatus.UNRESOLVED

    freeze_note = (
        "FUNDS ARE MODELLED EXPOSURES, NOT FUND RETURNS: RF + L (Mkt - RF) less fee and "
        "spread, compounded daily. The signal index is the TOTAL-RETURN index because the "
        "library has no daily price index; the price proxy is a sensitivity. The financing "
        "spread is an assumption at 40 bp with an 80 bp stress case. The HFEA bond leg is "
        "monthly and contains the 1981-2020 bull market. Every timed mean gap was predicted "
        "`unresolved` before the run."
    )
    header = [
        "# Experiment 021: leveraged ETFs and the 200-day moving average",
        "",
        f"Run `{context.run_id}`; specification hash `{specification.spec_hash}`.",
        "",
        freeze_note,
        "",
        f"Base settings: spread {costs.spread_bp:g} bp, stress {stress_bp:g} bp, fees "
        f"{costs.fee_index_bp:g}/{costs.fee_2x_bp:g}/{costs.fee_3x_bp:g}/"
        f"{costs.fee_treasury_3x_bp:g} bp "
        f"(1x/2x/3x/TMF-like), 1.3x control {costs.fee_130_bp:g} bp, one-way cost "
        f"{costs.one_way_cost * 10_000:g} bp, lookback {rule.lookback} days, band {rule.band:g}, "
        f"lag {rule.lag} day(s). Gap cells read: point [95% HAC] floor at 80% power, years to "
        "distinguish, falsifier status.",
    ]
    lines = list(header)
    for result in results:
        lines.extend(_window_tables(result))
    lines.extend(_deflation_table(deflation))
    lines.extend(_tax_table(tax))
    tables = "\n".join(lines) + "\n"

    summary = (
        f"{scored} arm-against-control comparisons scored on {len(results)} windows, on "
        f"modelled daily-reset exposures rather than fund returns. {len(resolved)} separate from "
        "their control by more than the design can resolve; every other mean gap is "
        "`unresolved` or `rejected`. Drawdown, whipsaw, crisis-episode, deflation and after-tax "
        "tables are descriptive and carry no significance claim."
    )
    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in raw.provenance],
        "source_findings": list(raw.findings),
        "settings": {
            "spread_bp": costs.spread_bp,
            "stress_spread_bp": stress_bp,
            "fees_bp": {
                "index_1x": costs.fee_index_bp,
                "levered_2x": costs.fee_2x_bp,
                "levered_3x": costs.fee_3x_bp,
                "treasury_3x": costs.fee_treasury_3x_bp,
                "leverage_matched_130": costs.fee_130_bp,
            },
            "one_way_cost_bp": costs.one_way_cost * 10_000.0,
            "lookback_days": rule.lookback,
            "band": rule.band,
            "execution_lag_days": rule.lag,
            "first_live_date": raw.dates[base.first_live],
        },
        "windows": [_window_json(r) for r in results],
        "deflation": deflation,
        "after_tax": tax,
        "resolved_comparisons": resolved,
        "markdown_tables": tables,
    }
    caveats = (
        "Funds are modelled exposures. This ranks constructions and cannot rank funds.",
        "The signal index is the total-return index; the price proxy sensitivity bounds the bias.",
        "The 40 bp swap spread is an assumption no issuer discloses; the 80 bp case is "
        "beside every gap.",
        "The HFEA Treasury leg is monthly, about 20-year duration, and contains the "
        "1981-2020 bull market.",
        "Drawdown, whipsaw, episode, deflation and after-tax figures describe one realised "
        "history.",
        "No sleeve, fund, rule or portfolio is promoted.",
    )
    return ExperimentResult(
        status=status,
        summary=summary,
        estimates=tuple(estimates),
        diagnostics=diagnostics,
        caveats=caveats,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _manifest_hashes(specification: Specification) -> list[str]:
    out: list[str] = []
    for source in specification.data_sources:
        if not isinstance(source, Mapping):
            continue
        location = source.get("manifest")
        if isinstance(location, str):
            path = workspace_root() / location
            if path.is_file():
                out.append(read_manifest(path).sha256_manifest())
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_021_leveraged_etf_rules",
        description="Score leveraged-ETF timing rules and HFEA against their controls.",
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument("--view-results", action="store_true")
    arguments = parser.parse_args(argv)
    specification = load_specification(arguments.specification)
    ledger = Ledger(arguments.ledger)
    outcome: RunOutcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=_manifest_hashes(specification),
    )
    result = outcome.result
    assert result is not None
    root = (
        Path(arguments.artifact_root) if arguments.artifact_root is not None else Path("artifacts")
    )
    tables_path = root / outcome.run_id / "tables.md"
    tables_path.write_text(str(result.diagnostics["markdown_tables"]), encoding="utf-8")
    print(f"run {outcome.run_id}: {result.status.value}")
    print(f"tables written to {tables_path}")
    if arguments.view_results:
        ledger.record_results_viewed(
            outcome.run_id, origin=Origin(arguments.origin), notes="printed by --view-results"
        )
        print(result.summary)
        print(str(result.diagnostics["markdown_tables"]))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
