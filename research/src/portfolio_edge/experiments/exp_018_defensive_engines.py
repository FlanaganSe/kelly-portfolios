"""Experiment 018: defensive engines inside the leveraged construction.

What this is
------------
The recommended portfolio is 70% cheap equity core plus 30% of an RSST-like
stacked wrapper -- 1.0216 equity notional, 0.300 trend notional, 1.3216 gross --
and holds no bonds, TIPS, gold or cash. Every earlier sleeve test priced those
assets in isolation or at a pro-rata weight against an unlevered base. This
module holds each of them INSIDE the leveraged construction, as a financed stack,
a substitution or a bond-plus-trend wrapper, and scores the result against three
kinds of control (cheap, leverage-matched, volatility-matched) and against the
recommendation itself, on four panels.

What this is NOT
----------------
**It does not score funds.** Every wrapper is an assumed per-dollar exposure
vector and a fee, stated in the frozen specification.

**It cannot resolve most of what it measures.** The specification's freeze note
predicts, before the run, that every mean gap comes back ``unresolved``; the
drawdown and crisis tables it produces are descriptions of one realised history
and carry no significance claim.

**Its bond history contains the 1981-2020 bull market** and its long-panel trend
leg is this repository's own 4-asset book scaled by one full-window constant.
Both are stated in the artifact beside every figure they touch.

Run it::

    uv run python -m portfolio_edge.experiments.exp_018_defensive_engines --view-results
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import aqr, fred, french, goyal_welch, lbma
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    MONTHS_PER_YEAR,
    BasisPanel,
    CostSettings,
    FundMapping,
    GapStatistics,
    PortfolioPath,
    _at,
    _mapping,
    _number,
    _numbers,
    _sequence,
    _simulate,
    _text,
    annualised_log_growth,
    minimum_detectable_effect,
    workspace_root,
    years_to_distinguish,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_index
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
from portfolio_edge.inference.multiple_testing import benjamini_hochberg
from portfolio_edge.studies.fixed_income_shelf import (
    par_bond_total_returns,
    tips_nominal_total_return,
)
from portfolio_edge.studies.stress_dependence import (
    convexity,
    episode_returns,
    tail_dependence,
)
from portfolio_edge.studies.time_series_momentum import (
    TimeSeriesMomentumSpec,
    time_series_momentum,
)

FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]
MonthSeries = dict[str, float]

ENTRY_POINT: Final = "exp_018_defensive_engines"

#: The legs a panel may carry, in the order the notional table prints them.
LEGS: Final = ("equity", "treasury", "trend", "gold", "tips")

#: Which leg a financing rate key applies to. TIPS futures do not exist; the
#: specification charges the Treasury rate as a placeholder on the check window.
CONTROL_KINDS: Final = (
    "cheap",
    "leverage_matched",
    "volatility_matched_expost",
    "volatility_matched_exante",
    "reference",
)

__all__ = [
    "ENTRY_POINT",
    "LEGS",
    "Arm",
    "DefensiveEnginesError",
    "FinancingRates",
    "Notional",
    "Wrapper",
    "arithmetic_gap",
    "arm_notional",
    "build_registry",
    "build_trend_book",
    "contribution_terminal_wealth",
    "default_specification_path",
    "excess_matrix",
    "main",
    "read_arms",
    "read_wrappers",
    "run",
    "simulate_arm",
    "wrapper_excess",
]


class DefensiveEnginesError(Exception):
    """The experiment refused to run, or a source did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_018_defensive_engines.yaml"


# --------------------------------------------------------------------------- #
# Wrappers, arms, notional
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Wrapper:
    """One holding: per-dollar exposures, a fee, and the notional it finances."""

    ticker: str
    exposures: Mapping[str, float]
    fee_bp: float
    financed: Mapping[str, float]
    note: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class FinancingRates:
    """Annual basis points over cash, charged on financed notional by leg."""

    equity: float
    treasury: float
    gold: float
    tips: float

    def for_leg(self, leg: str) -> float:
        try:
            return {
                "equity": self.equity,
                "treasury": self.treasury,
                "gold": self.gold,
                "tips": self.tips,
            }[leg]
        except KeyError:
            raise DefensiveEnginesError(f"no financing rate for leg {leg!r}") from None


@dataclass(frozen=True, slots=True, kw_only=True)
class Arm:
    name: str
    role: str
    tickers: tuple[str, ...]
    weights: tuple[float, ...]
    note: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class Notional:
    """What an arm holds per dollar of capital, by leg."""

    gross: float
    equity: float
    trend: float
    bond: float
    gold: float
    cash: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "gross": round(self.gross, 4),
            "equity": round(self.equity, 4),
            "trend": round(self.trend, 4),
            "bond": round(self.bond, 4),
            "gold": round(self.gold, 4),
            "cash": round(self.cash, 4),
        }


def read_wrappers(specification: Specification) -> dict[str, Wrapper]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "wrappers", where="parameters"), where="wrappers")
    costs = _mapping(specification.cost_model, where="cost_model")
    fees = _mapping(
        _at(costs, "wrapper_expense_ratio_basis_points", where="cost_model"), where="fees"
    )
    out: dict[str, Wrapper] = {}
    for ticker in block:
        entry = _mapping(block[ticker], where=f"wrappers.{ticker}")
        exposures = _mapping(_at(entry, "exposures", where=f"wrappers.{ticker}"), where="exposures")
        financed = _mapping(_at(entry, "financed", where=f"wrappers.{ticker}"), where="financed")
        for leg in list(exposures) + list(financed):
            if leg not in LEGS:
                raise DefensiveEnginesError(f"wrappers.{ticker} names unknown leg {leg!r}")
        out[ticker] = Wrapper(
            ticker=ticker,
            exposures={leg: _number(exposures, leg, where="exposures") for leg in exposures},
            fee_bp=_number(fees, ticker, where="cost_model.wrapper_expense_ratio_basis_points"),
            financed={leg: _number(financed, leg, where="financed") for leg in financed},
            note=str(entry.get("note") or ""),
        )
    return out


def read_arms(specification: Specification) -> dict[str, Arm]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "contestants", where="parameters"), where="contestants")
    out: dict[str, Arm] = {}
    for name in block:
        entry = _mapping(block[name], where=f"contestants.{name}")
        raw = _mapping(_at(entry, "weights", where=f"contestants.{name}"), where="weights")
        tickers = tuple(raw)
        weights = tuple(_number(raw, t, where=f"contestants.{name}.weights") for t in tickers)
        if abs(sum(weights) - 1.0) > 1e-9:
            raise DefensiveEnginesError(
                f"contestants.{name}: capital weights sum to {sum(weights):.4f}, not 1. "
                "Leverage lives inside the wrappers, never in the capital weights."
            )
        out[name] = Arm(
            name=name,
            role=str(entry.get("role") or "candidate"),
            tickers=tickers,
            weights=weights,
            note=str(entry.get("note") or ""),
        )
    return out


def read_rates(specification: Specification) -> FinancingRates:
    costs = _mapping(specification.cost_model, where="cost_model")
    block = _mapping(
        _at(costs, "financing_basis_points_over_cash", where="cost_model"), where="financing"
    )
    return FinancingRates(
        equity=_number(block, "equity", where="financing"),
        treasury=_number(block, "treasury", where="financing"),
        gold=_number(block, "gold", where="financing"),
        tips=_number(block, "tips", where="financing"),
    )


def arm_notional(
    tickers: Sequence[str], weights: Sequence[float], wrappers: Mapping[str, Wrapper]
) -> Notional:
    """Capital weights times per-dollar exposures, leg by leg.

    ``cash`` is the capital not deployed into any exposure by a wrapper whose
    exposures sum to less than one (T-bills, or a wrapper's collateral); it is
    not part of gross notional.
    """
    by_leg = dict.fromkeys(LEGS, 0.0)
    cash = 0.0
    for ticker, weight in zip(tickers, weights, strict=True):
        wrapper = wrappers[ticker]
        for leg, exposure in wrapper.exposures.items():
            by_leg[leg] += weight * exposure
        cash += weight * max(0.0, 1.0 - sum(wrapper.exposures.values()))
    return Notional(
        gross=sum(abs(v) for v in by_leg.values()),
        equity=by_leg["equity"],
        trend=by_leg["trend"],
        bond=by_leg["treasury"] + by_leg["tips"],
        gold=by_leg["gold"],
        cash=cash,
    )


# --------------------------------------------------------------------------- #
# Series
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RawSeries:
    """Every month-keyed series the panels are built from, plus provenance."""

    equity: MonthSeries
    cash: MonthSeries
    ltr: MonthSeries
    corpr: MonthSeries
    gw_rfree: MonthSeries
    commodity: MonthSeries
    tsmom: MonthSeries
    gold_levels: MonthSeries
    gs10_yield: MonthSeries
    fii10_yield: MonthSeries
    cpi: MonthSeries
    provenance: tuple[Mapping[str, JsonValue], ...]
    findings: tuple[str, ...]


def _column(periods: Sequence[str], values: Sequence[float | None]) -> MonthSeries:
    return {p[:7]: float(v) for p, v in zip(periods, values, strict=True) if v is not None}


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
    """Return the entry holding the PINNED bytes, and a provenance record.

    This experiment never downloads: a run can never be the thing that silently
    pulls a new vintage. If the cache index has since been refreshed to a newer
    vintage by some other process, the pinned blob is read by its digest as
    long as it still exists, and the supersession is recorded; only a pinned
    blob that is gone entirely aborts the run.
    """
    where = "source_pin.files[]"
    expected = _text(pin, "expected_sha256_raw", where=where)
    entry = cache.entry_for(url)
    superseded: str | None = None
    if entry is None or entry.sha256 != expected:
        if not cache.has(expected):
            observed = "absent" if entry is None else entry.sha256
            raise DefensiveEnginesError(
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
                f"{file_id}: the pinned file ({record['sha256_raw']}) is a different "
                "vintage from the one the committed manifest records; the pin in the "
                "specification is the digest read and this is recorded, not hidden."
            )
        if record["index_superseded_by_sha256"] is not None:
            findings.append(
                f"{file_id}: the cache index now points at {record['index_superseded_by_sha256']}; "
                f"the pinned blob {record['sha256_raw']} was read by digest instead."
            )
        provenance.append(record)
        return entry, record

    ff3 = french.get_dataset("french_us_ff3")
    entry, record = take("french_us_ff3", ff3.url)
    market = french.parse(cache, entry, dataset=ff3).table("monthly")
    equity = _column(market.periods, market.column("Mkt-RF"))
    cash = _column(market.periods, market.column("RF"))
    record["first_observation"], record["last_observation"] = min(equity), max(equity)

    gw = goyal_welch.get_dataset("goyal_welch_predictors")
    entry, record = take("goyal_welch_predictors", gw.url)
    monthly = next(
        t for t in goyal_welch.parse(cache, entry, dataset=gw).tables if t.table_id == "monthly"
    )
    ltr = _column(monthly.periods, monthly.column("ltr"))
    corpr = _column(monthly.periods, monthly.column("corpr"))
    gw_rfree = _column(monthly.periods, monthly.column("Rfree"))
    record["first_observation"], record["last_observation"] = min(ltr), max(ltr)

    commodity_dataset = aqr.get_dataset("aqr_commodities_long_run")
    entry, record = take("aqr_commodities_long_run", commodity_dataset.url)
    table = aqr.parse(cache, entry, dataset=commodity_dataset).table
    commodity = _column(
        table.periods, table.column("Excess return of equal-weight commodities portfolio")
    )
    record["first_observation"], record["last_observation"] = min(commodity), max(commodity)

    tsmom_dataset = aqr.get_dataset("aqr_tsmom_factors")
    entry, record = take("aqr_tsmom_factors", tsmom_dataset.url)
    table = aqr.parse(cache, entry, dataset=tsmom_dataset).table
    tsmom = _column(table.periods, table.column("TSMOM"))
    record["first_observation"], record["last_observation"] = min(tsmom), max(tsmom)

    gold_dataset = lbma.get_dataset("lbma_gold_pm")
    entry, record = take("lbma_gold_pm", gold_dataset.url)
    gold_levels = dict(lbma.month_end_usd(lbma.parse(cache, entry, dataset=gold_dataset)))
    record["first_observation"], record["last_observation"] = min(gold_levels), max(gold_levels)

    fred_series: dict[str, MonthSeries] = {}
    for file_id, series_id in (
        ("fred_gs10", "GS10"),
        ("fred_fii10", "FII10"),
        ("fred_cpiaucns", "CPIAUCNS"),
    ):
        url = fred.series_url(series_id)
        entry, record = take(file_id, url)
        table = fred.parse(cache, entry, series_id)
        fred_series[series_id] = _column(table.periods, table.column(series_id))
        record["first_observation"] = min(fred_series[series_id])
        record["last_observation"] = max(fred_series[series_id])

    return RawSeries(
        equity=equity,
        cash=cash,
        ltr=ltr,
        corpr=corpr,
        gw_rfree=gw_rfree,
        commodity=commodity,
        tsmom=tsmom,
        gold_levels=gold_levels,
        gs10_yield=fred_series["GS10"],
        fii10_yield=fred_series["FII10"],
        cpi=fred_series["CPIAUCNS"],
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


def _month_label(index: int) -> str:
    return f"{(index - 1) // 12:04d}-{((index - 1) % 12) + 1:02d}"


def build_trend_book(
    instruments: Sequence[MonthSeries],
    *,
    spec: TimeSeriesMomentumSpec,
    minimum_instruments: int,
    end: str,
) -> MonthSeries:
    """The unscaled 4-asset book on the union of its instruments' months.

    Instruments may have different coverage; ``time_series_momentum`` drops a
    leg on the months it is missing rather than bridging it. The book is cut at
    ``end`` so that it never runs on fewer instruments than it started with
    because one source stopped publishing.
    """
    months_set: set[str] = set()
    for series in instruments:
        months_set |= set(series)
    if not months_set:
        raise DefensiveEnginesError("the trend book has no instruments")
    first, last = month_index(min(months_set)), month_index(max(months_set))
    months = [_month_label(i) for i in range(first, last + 1)]
    matrix = np.full((len(months), len(instruments)), np.nan, dtype=np.float64)
    for column, series in enumerate(instruments):
        for row, month in enumerate(months):
            value = series.get(month)
            if value is not None:
                matrix[row, column] = value
    book = time_series_momentum(matrix, spec=spec, minimum_instruments=minimum_instruments)
    return {
        month: float(value)
        for month, value in zip(months, book, strict=True)
        if np.isfinite(value) and month <= end
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class PanelSpec:
    id: str
    role: str
    trend_source: str
    bond_source: str
    legs: tuple[str, ...]
    arms: tuple[str, ...]
    start: str | None
    end: str | None
    note: str


def read_panels(specification: Specification) -> tuple[PanelSpec, ...]:
    parameters = _mapping(specification.parameters, where="parameters")
    out: list[PanelSpec] = []
    for item in _sequence(_at(parameters, "panels", where="parameters"), where="panels"):
        entry = _mapping(item, where="panels[]")
        start = entry.get("start")
        end = entry.get("end")
        out.append(
            PanelSpec(
                id=_text(entry, "id", where="panels[]"),
                role=_text(entry, "role", where="panels[]"),
                trend_source=_text(entry, "trend_source", where="panels[]"),
                bond_source=_text(entry, "bond_source", where="panels[]"),
                legs=tuple(
                    str(x) for x in _sequence(_at(entry, "legs", where="panels[]"), where="legs")
                ),
                arms=tuple(
                    str(x) for x in _sequence(_at(entry, "arms", where="panels[]"), where="arms")
                ),
                start=str(start) if isinstance(start, str) else None,
                end=str(end) if isinstance(end, str) else None,
                note=str(entry.get("note") or ""),
            )
        )
    return tuple(out)


def _price_returns(levels: MonthSeries) -> MonthSeries:
    months = sorted(levels)
    out: MonthSeries = {}
    for earlier, later in itertools.pairwise(months):
        if month_index(later) - month_index(earlier) == 1 and levels[earlier] > 0.0:
            out[later] = levels[later] / levels[earlier] - 1.0
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class LegLibrary:
    """Every leg as an excess-of-cash month series, by source, ready to intersect."""

    equity: MonthSeries
    cash: MonthSeries
    treasury: Mapping[str, MonthSeries]
    trend: Mapping[str, MonthSeries]
    gold: MonthSeries
    tips: MonthSeries
    trend_scalar: float
    trend_book_realised_volatility_pct: float
    trend_book_window: tuple[str, str]


def build_legs(raw: RawSeries, specification: Specification) -> LegLibrary:
    parameters = _mapping(specification.parameters, where="parameters")
    book_block = _mapping(_at(parameters, "trend_book", where="parameters"), where="trend_book")
    spec = TimeSeriesMomentumSpec(
        lookback=int(_number(book_block, "lookback_months", where="trend_book")),
        volatility_window=int(_number(book_block, "volatility_window_months", where="trend_book")),
        target_volatility=_number(book_block, "per_position_volatility_target", where="trend_book"),
        cap=_number(book_block, "position_cap", where="trend_book"),
    )
    minimum = int(_number(book_block, "minimum_live_instruments", where="trend_book"))
    target = _number(book_block, "target_volatility_percent", where="trend_book") / 100.0

    treasury_gw = {p: raw.ltr[p] - raw.gw_rfree[p] for p in raw.ltr if p in raw.gw_rfree}
    credit_gw = {p: raw.corpr[p] - raw.gw_rfree[p] for p in raw.corpr if p in raw.gw_rfree}
    unscaled = build_trend_book(
        (raw.equity, treasury_gw, credit_gw, raw.commodity),
        spec=spec,
        minimum_instruments=minimum,
        end=max(raw.commodity),
    )

    treasury_ltr = {p: raw.ltr[p] - raw.cash[p] for p in raw.ltr if p in raw.cash}
    # The primary window: everything the primary panel needs, intersected. The
    # scalar is computed here, once, and applied everywhere the book is used.
    primary = sorted(set(unscaled) & set(raw.equity) & set(raw.cash) & set(treasury_ltr))
    if len(primary) < 2 * MONTHS_PER_YEAR:
        raise DefensiveEnginesError("the primary window is shorter than two years")
    realised = float(np.std([unscaled[p] for p in primary], ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    scalar = target / realised
    scaled = {p: v * scalar for p, v in unscaled.items()}

    gs10 = par_bond_total_returns(raw.gs10_yield, maturity_years=10.0)
    treasury_gs10 = {p: gs10[p] - raw.cash[p] for p in gs10 if p in raw.cash}
    real = par_bond_total_returns(raw.fii10_yield, maturity_years=10.0)
    nominal = tips_nominal_total_return(real, raw.cpi)
    tips = {p: nominal[p] - raw.cash[p] for p in nominal if p in raw.cash}
    gold_returns = _price_returns(raw.gold_levels)
    gold = {p: gold_returns[p] - raw.cash[p] for p in gold_returns if p in raw.cash}

    return LegLibrary(
        equity=raw.equity,
        cash=raw.cash,
        treasury={"goyal_welch_ltr": treasury_ltr, "gs10_par_bond": treasury_gs10},
        trend={"own_4_asset_book": scaled, "aqr_tsmom": dict(raw.tsmom)},
        gold=gold,
        tips=tips,
        trend_scalar=scalar,
        trend_book_realised_volatility_pct=realised * 100.0,
        trend_book_window=(primary[0], primary[-1]),
    )


def build_panel(legs: LegLibrary, spec: PanelSpec) -> BasisPanel:
    """Intersect the legs a panel names, on the window it declares."""
    sources: dict[str, MonthSeries] = {"equity": legs.equity}
    if "treasury" in spec.legs:
        try:
            sources["treasury"] = legs.treasury[spec.bond_source]
        except KeyError:
            raise DefensiveEnginesError(f"unknown bond_source {spec.bond_source!r}") from None
    if "trend" in spec.legs:
        try:
            sources["trend"] = legs.trend[spec.trend_source]
        except KeyError:
            raise DefensiveEnginesError(f"unknown trend_source {spec.trend_source!r}") from None
    if "gold" in spec.legs:
        sources["gold"] = legs.gold
    if "tips" in spec.legs:
        sources["tips"] = legs.tips
    unknown = set(spec.legs) - set(sources)
    if unknown:
        raise DefensiveEnginesError(f"panel {spec.id}: unknown legs {sorted(unknown)}")

    common = set(legs.cash)
    for series in sources.values():
        common &= set(series)
    periods = sorted(common)
    if spec.start is not None:
        periods = [p for p in periods if month_index(p) >= month_index(spec.start)]
    if spec.end is not None:
        periods = [p for p in periods if month_index(p) <= month_index(spec.end)]
    if len(periods) < 3 * MONTHS_PER_YEAR:
        raise DefensiveEnginesError(f"panel {spec.id} holds {len(periods)} months")
    for earlier, later in itertools.pairwise(periods):
        if month_index(later) - month_index(earlier) != 1:
            raise DefensiveEnginesError(f"panel {spec.id} has a gap between {earlier} and {later}")
    starts = {name: min(series) for name, series in sources.items()}
    ends = {name: max(series) for name, series in sources.items()}
    binding_start = max(starts, key=lambda n: month_index(starts[n]))
    binding_end = min(ends, key=lambda n: month_index(ends[n]))
    return BasisPanel(
        periods=tuple(periods),
        series={
            name: np.array([series[p] for p in periods], dtype=np.float64)
            for name, series in sources.items()
        },
        cash=np.array([legs.cash[p] for p in periods], dtype=np.float64),
        provenance=(),
        findings=(
            f"panel {spec.id}: {len(periods)} months, {periods[0]}..{periods[-1]}; start set by "
            f"{binding_start} ({starts[binding_start]}) or the declared start, end set by "
            f"{binding_end} ({ends[binding_end]}) or the declared end.",
        ),
    )


# --------------------------------------------------------------------------- #
# Excess returns and simulation
# --------------------------------------------------------------------------- #


def wrapper_excess(panel: BasisPanel, wrapper: Wrapper, rates: FinancingRates) -> FloatArray:
    """``sum(exposure * leg) - fee/12 - sum(financed * rate)/12``, monthly."""
    total = np.zeros(panel.months, dtype=np.float64)
    for leg, exposure in wrapper.exposures.items():
        total = total + exposure * panel.column(leg)
    annual_charge = wrapper.fee_bp / 10_000.0
    for leg, notional in wrapper.financed.items():
        annual_charge += notional * rates.for_leg(leg) / 10_000.0
    return np.asarray(total - annual_charge / MONTHS_PER_YEAR, dtype=np.float64)


def excess_matrix(
    panel: BasisPanel,
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    *,
    tickers: Sequence[str],
) -> FloatArray:
    columns = [wrapper_excess(panel, wrappers[t], rates) for t in tickers]
    return np.column_stack(columns) if columns else np.zeros((panel.months, 0))


def _mappings_for(
    wrappers: Mapping[str, Wrapper], tickers: Sequence[str]
) -> dict[str, FundMapping]:
    return {
        t: FundMapping(
            ticker=t,
            coefficients=dict(wrappers[t].exposures),
            expense_ratio_bp=wrappers[t].fee_bp,
            futures_notional=0.0,
            spread_region="us_equity",
            alpha_less_pedestal_pp_yr=None,
            distribution_tax_drag_pp_yr=None,
            incremental_tax_drag_bp=None,
            structure_assumed=True,
            fee_assumed=False,
        )
        for t in tickers
    }


def _cost_settings(specification: Specification, rates: FinancingRates) -> CostSettings:
    costs = _mapping(specification.cost_model, where="cost_model")
    spreads = _mapping(
        _at(costs, "round_trip_spread_basis_points", where="cost_model"), where="spreads"
    )
    return CostSettings(
        equity_futures_basis=rates.equity / 10_000.0,
        trend_book_financing=0.0,
        round_trip_spread={k: _number(spreads, k, where="spreads") for k in spreads},
    )


def simulate_arm(
    panel: BasisPanel,
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    costs: CostSettings,
    *,
    tickers: Sequence[str],
    targets: FloatArray,
    first_month: int = 0,
) -> PortfolioPath:
    """Monthly rebalance to ``targets`` with positions and debt carried absolutely.

    Capital weights summing to more than one borrow the excess at cash plus the
    equity-futures basis; that is how the leverage-matched and levered
    volatility-matched controls are financed. Wrapper financing is inside
    :func:`wrapper_excess` and never reaches this debt line.
    """
    excess = excess_matrix(panel, wrappers, rates, tickers=tickers)
    return _simulate(
        panel,
        _mappings_for(wrappers, tickers),
        costs,
        tickers=tickers,
        excess=excess,
        targets=targets,
        first_month=first_month,
        rebalance_every=1,
    )


def _volatility(values: FloatArray) -> float:
    return float(np.std(values, ddof=1))


@dataclass(slots=True, kw_only=True)
class ArmPaths:
    """One arm on one panel with every control it is scored against."""

    arm: Arm
    notional: Notional
    path: PortfolioPath
    controls: dict[str, PortfolioPath]
    control_first_month: dict[str, int]
    control_definition: dict[str, str]


def simulate_panel(
    panel: BasisPanel,
    *,
    arms: Mapping[str, Arm],
    names: Sequence[str],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    costs: CostSettings,
    reference: str,
    volatility_window: int,
) -> dict[str, ArmPaths]:
    """Simulate every named arm and its cheap, levered, vol-matched and reference controls."""
    cheap = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.0]))
    core_total = cheap.total
    out: dict[str, ArmPaths] = {}
    for name in names:
        arm = arms[name]
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        path = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=arm.tickers,
            targets=np.asarray(arm.weights, dtype=np.float64),
        )
        controls: dict[str, PortfolioPath] = {"cheap": cheap}
        first: dict[str, int] = {"cheap": 0}
        definition: dict[str, str] = {"cheap": "100% CORE"}

        gross = notional.gross
        controls["leverage_matched"] = simulate_arm(
            panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([gross])
        )
        first["leverage_matched"] = 0
        definition["leverage_matched"] = f"{gross:.4f} x CORE, financed at the equity basis"

        scale = _volatility(path.total) / _volatility(core_total)
        if scale <= 1.0:
            tickers: tuple[str, ...] = ("CORE", "CASH")
            targets = np.array([scale, 1.0 - scale])
        else:
            tickers, targets = ("CORE",), np.array([scale])
        controls["volatility_matched_expost"] = simulate_arm(
            panel, wrappers, rates, costs, tickers=tickers, targets=targets
        )
        first["volatility_matched_expost"] = 0
        definition["volatility_matched_expost"] = (
            f"{scale:.4f} x CORE"
            + (f" + {1.0 - scale:.4f} x CASH" if scale <= 1.0 else ", financed at the equity basis")
            + " (full-window volatility match)"
        )

        rolling = np.zeros((panel.months, 2), dtype=np.float64)
        for t in range(volatility_window, panel.months):
            window_arm = _volatility(path.total[t - volatility_window : t])
            window_core = _volatility(core_total[t - volatility_window : t])
            w = window_arm / window_core if window_core > 0.0 else 1.0
            rolling[t, 0] = w
            rolling[t, 1] = max(0.0, 1.0 - w)
        controls["volatility_matched_exante"] = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=("CORE", "CASH"),
            targets=rolling,
            first_month=volatility_window,
        )
        first["volatility_matched_exante"] = volatility_window
        definition["volatility_matched_exante"] = (
            f"CORE scaled each month to the trailing {volatility_window}-month volatility "
            "ratio, remainder in CASH, excess above one financed at the equity basis"
        )
        out[name] = ArmPaths(
            arm=arm,
            notional=notional,
            path=path,
            controls=controls,
            control_first_month=first,
            control_definition=definition,
        )
    if reference in out:
        for name, item in out.items():
            if name != reference:
                item.controls["reference"] = out[reference].path
                item.control_first_month["reference"] = 0
                item.control_definition["reference"] = f"the {reference} arm"
    return out


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def arithmetic_gap(
    arm_total: FloatArray,
    benchmark_total: FloatArray,
    *,
    indices: IndexArray,
    confidence: float,
) -> GapStatistics:
    """``1200 * mean(r_arm - r_bench)`` with its bootstrap interval, MDE and p-value."""
    if arm_total.shape != benchmark_total.shape:
        raise DefensiveEnginesError("arm and benchmark must cover the same months")
    difference = arm_total - benchmark_total
    gap = float(np.mean(difference)) * MONTHS_PER_YEAR * 100.0
    resampled = difference[indices].mean(axis=1) * MONTHS_PER_YEAR * 100.0
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(resampled, [tail, 1.0 - tail])
    centred = resampled - gap
    exceed = int(np.sum(np.abs(centred) >= abs(gap)))
    return GapStatistics(
        gap_pp_yr=gap,
        interval=(float(low), float(high)),
        mde_pp_yr=minimum_detectable_effect(difference),
        mde_bootstrap_pp_yr=MDE_MULTIPLIER * float(np.std(resampled, ddof=1)),
        p_value=float((exceed + 1) / (resampled.size + 1)),
        tracking_error_pct=_volatility(difference) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
        months=int(difference.size),
        years_to_distinguish=years_to_distinguish(gap, difference),
    )


def contribution_terminal_wealth(total: FloatArray, *, contribution: float) -> float:
    """Terminal wealth from a unit start with ``contribution`` added before each month."""
    wealth = 1.0
    for r in total:
        wealth = (wealth + contribution) * (1.0 + float(r))
    return wealth


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _round(value: float, digits: int = 4) -> float | None:
    finite = _finite(value)
    return None if finite is None else round(finite, digits)


@dataclass(slots=True, kw_only=True)
class Comparison:
    control: str
    definition: str
    gap: GapStatistics | None
    identical: bool = False
    adjusted_p: float | None = None
    status: str = "not-scored"
    clause: str = ""
    financing_band_range: tuple[float, float] | None = None
    era_gaps: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict[str, JsonValue]:
        gap = self.gap
        return {
            "control": self.control,
            "control_definition": self.definition,
            "identical_construction": self.identical,
            "gap_pp_yr": None if gap is None else _round(gap.gap_pp_yr),
            "gap_interval_pp_yr": (
                None if gap is None else [_round(gap.interval[0]), _round(gap.interval[1])]
            ),
            "mde_80pc_power_pp_yr": None if gap is None else _round(gap.mde_pp_yr),
            "mde_80pc_power_block_bootstrap_pp_yr": (
                None if gap is None else _round(gap.mde_bootstrap_pp_yr)
            ),
            "tracking_error_pct": None if gap is None else _round(gap.tracking_error_pct),
            "years_to_distinguish_at_80pc_power": (
                None if gap is None else _round(gap.years_to_distinguish, 1)
            ),
            "p_value": None if gap is None else _round(gap.p_value, 5),
            "benjamini_hochberg_adjusted_p": (
                None if self.adjusted_p is None else _round(self.adjusted_p, 5)
            ),
            "equity_financing_band_gap_range_pp_yr": (
                None
                if self.financing_band_range is None
                else [_round(self.financing_band_range[0]), _round(self.financing_band_range[1])]
            ),
            "status": self.status,
            "falsifier_clause": self.clause,
            "era_gaps_pp_yr": {k: _round(v) for k, v in self.era_gaps.items()},
        }


def _apply_falsifier(comparison: Comparison, *, q: float) -> None:
    gap = comparison.gap
    if gap is None or comparison.identical:
        comparison.status, comparison.clause = "not-scored", "identical construction"
        return
    if gap.gap_pp_yr <= 0.0:
        comparison.status, comparison.clause = "rejected", "(a) gap at or below zero"
        return
    if abs(gap.gap_pp_yr) < gap.mde_pp_yr:
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
    band = comparison.financing_band_range
    if band is not None and band[0] <= 0.0:
        comparison.status, comparison.clause = (
            "unresolved",
            f"(d) the gap changes sign on the equity-financing band, reaching {band[0]:+.2f} pp/yr",
        )
        return
    comparison.status, comparison.clause = "exploratory", "(e) survived every clause"


@dataclass(slots=True, kw_only=True)
class Episode:
    name: str
    kind: str
    start: str
    end: str


def read_episodes(specification: Specification) -> tuple[Episode, ...]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "crisis_episodes", where="parameters"), where="episodes")
    out: list[Episode] = []
    for kind in ("deflationary_or_growth", "inflation_or_rate"):
        for item in _sequence(_at(block, kind, where="crisis_episodes"), where=kind):
            entry = _mapping(item, where=f"crisis_episodes.{kind}[]")
            out.append(
                Episode(
                    name=_text(entry, "name", where=kind),
                    kind=kind,
                    start=_text(entry, "start", where=kind),
                    end=_text(entry, "end", where=kind),
                )
            )
    return tuple(out)


def _slice(periods: Sequence[str], start: str, end: str) -> IndexArray:
    low, high = month_index(start), month_index(end)
    return np.asarray(
        [i for i, p in enumerate(periods) if low <= month_index(p) <= high], dtype=np.intp
    )


def _era_windows(
    specification: Specification, periods: Sequence[str]
) -> list[tuple[str, str, str]]:
    """Declared eras clipped to the panel, plus the panel's own mechanical halves."""
    n = len(periods)
    half = n // 2
    windows: list[tuple[str, str, str]] = [
        ("panel_first_half", periods[0], periods[half - 1]),
        ("panel_second_half", periods[half], periods[-1]),
    ]
    for era in specification.sample_policy.eras:
        keep = _slice(periods, era.start, era.end)
        if keep.size >= 2 * MONTHS_PER_YEAR:
            windows.append((era.name, periods[int(keep[0])], periods[int(keep[-1])]))
    return windows


# --------------------------------------------------------------------------- #
# One panel, scored
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class PanelResult:
    spec: PanelSpec
    panel: BasisPanel
    arms: dict[str, ArmPaths]
    comparisons: dict[str, dict[str, Comparison]]
    descriptives: dict[str, dict[str, JsonValue]]
    bond_regime: list[dict[str, JsonValue]]
    financing: dict[str, JsonValue]
    families: dict[str, list[str]]


def _band_gaps(
    panel: BasisPanel,
    *,
    specification: Specification,
    arms: Mapping[str, Arm],
    names: Sequence[str],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    reference: str,
    volatility_window: int,
) -> dict[str, dict[str, float]]:
    """Point gaps (no bootstrap) of every arm against every control at one rate setting."""
    costs = _cost_settings(specification, rates)
    simulated = simulate_panel(
        panel,
        arms=arms,
        names=names,
        wrappers=wrappers,
        rates=rates,
        costs=costs,
        reference=reference,
        volatility_window=volatility_window,
    )
    out: dict[str, dict[str, float]] = {}
    for name, item in simulated.items():
        out[name] = {}
        for control, path in item.controls.items():
            first = item.control_first_month[control]
            d = item.path.total[first:] - path.total
            out[name][control] = float(np.mean(d)) * MONTHS_PER_YEAR * 100.0
    return out


def score_panel(
    spec: PanelSpec,
    panel: BasisPanel,
    *,
    specification: Specification,
    arms: Mapping[str, Arm],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    rng: np.random.Generator,
    full: bool,
) -> PanelResult:
    """Simulate, compare, describe. ``full`` adds the bootstrap and sensitivities."""
    parameters = _mapping(specification.parameters, where="parameters")
    reference = _text(parameters, "reference_arm", where="parameters")
    volatility_window = int(
        _number(parameters, "volatility_match_window_months", where="parameters")
    )
    contribution = _number(
        parameters, "contribution_per_month_of_starting_balance", where="parameters"
    )
    tail = _number(parameters, "tail_quantile", where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")
    names = [n for n in spec.arms if n in arms]
    missing = set(spec.arms) - set(names)
    if missing:
        raise DefensiveEnginesError(f"panel {spec.id} names unknown arms {sorted(missing)}")
    costs = _cost_settings(specification, rates)
    simulated = simulate_panel(
        panel,
        arms=arms,
        names=names,
        wrappers=wrappers,
        rates=rates,
        costs=costs,
        reference=reference,
        volatility_window=volatility_window,
    )

    indices_by_length: dict[int, IndexArray] = {}

    def indices(length: int) -> IndexArray:
        if length not in indices_by_length:
            indices_by_length[length] = stationary_bootstrap_indices(
                length, block, specification.inference.resamples if full else 200, rng
            )
        return indices_by_length[length]

    windows = _era_windows(specification, panel.periods)
    comparisons: dict[str, dict[str, Comparison]] = {}
    families: dict[str, list[str]] = {}
    for name, item in simulated.items():
        comparisons[name] = {}
        for control, path in item.controls.items():
            first = item.control_first_month[control]
            arm_total = item.path.total[first:]
            identical = _volatility(arm_total - path.total) == 0.0
            stats = None
            if not identical:
                stats = arithmetic_gap(
                    arm_total,
                    path.total,
                    indices=indices(arm_total.size),
                    confidence=specification.inference.confidence_level,
                )
            comparison = Comparison(
                control=control,
                definition=item.control_definition[control],
                gap=stats,
                identical=identical,
            )
            for era_name, start, end in windows:
                keep = _slice(panel.periods[first:], start, end)
                if keep.size >= MONTHS_PER_YEAR:
                    d = arm_total[keep] - path.total[keep]
                    comparison.era_gaps[era_name] = float(np.mean(d)) * MONTHS_PER_YEAR * 100.0
            comparisons[name][control] = comparison
            if not identical:
                families.setdefault(control, []).append(name)

    for control, members in families.items():
        p_values: list[float] = []
        for n in members:
            gap = comparisons[n][control].gap
            assert gap is not None
            p_values.append(gap.p_value)
        adjusted = benjamini_hochberg(p_values, alpha=q)
        for n, value in zip(members, adjusted.adjusted_p_values, strict=True):
            comparisons[n][control].adjusted_p = float(value)

    # Financing sensitivity: the equity band feeds clause (d); the Treasury and
    # gold bands are reported.
    financing: dict[str, JsonValue] = {}
    if full:
        sensitivity = _mapping(
            _at(parameters, "financing_sensitivity", where="parameters"), where="financing"
        )
        band_records: dict[str, dict[str, dict[str, list[float]]]] = {}
        for key, attribute in (
            ("equity_basis_points", "equity"),
            ("treasury_basis_points", "treasury"),
            ("gold_basis_points", "gold"),
        ):
            if attribute == "gold" and "gold" not in spec.legs:
                continue
            grid = _numbers(_at(sensitivity, key, where="financing"), where=key)
            per_point: dict[str, dict[str, list[float]]] = {}
            for point in grid:
                shifted = FinancingRates(
                    equity=point if attribute == "equity" else rates.equity,
                    treasury=point if attribute == "treasury" else rates.treasury,
                    gold=point if attribute == "gold" else rates.gold,
                    tips=rates.tips,
                )
                gaps = _band_gaps(
                    panel,
                    specification=specification,
                    arms=arms,
                    names=names,
                    wrappers=wrappers,
                    rates=shifted,
                    reference=reference,
                    volatility_window=volatility_window,
                )
                for name, by_control in gaps.items():
                    for control, value in by_control.items():
                        per_point.setdefault(name, {}).setdefault(control, []).append(value)
            band_records[attribute] = per_point
            ordering: list[list[str]] = []
            for i in range(len(grid)):
                ranked = sorted(
                    (n for n in names if "reference" in per_point.get(n, {})),
                    key=lambda n: -per_point[n]["reference"][i],
                )
                ordering.append(ranked)
            financing[attribute] = {
                "grid_basis_points": list(grid),
                "gaps_pp_yr": {
                    n: {c: [_round(v) for v in vs] for c, vs in by_control.items()}
                    for n, by_control in per_point.items()
                },
                "ordering_against_reference_by_point": ordering,
                "ordering_against_reference_stable": all(o == ordering[0] for o in ordering),
            }
        equity_band = band_records.get("equity", {})
        for name in names:
            for control, comparison in comparisons[name].items():
                values = equity_band.get(name, {}).get(control)
                if values:
                    comparison.financing_band_range = (min(values), max(values))

    for name in names:
        for comparison in comparisons[name].values():
            _apply_falsifier(comparison, q=q)

    # Descriptives.
    episodes = read_episodes(specification)
    episode_windows = {e.name: (e.start, e.end) for e in episodes}
    equity_leg = panel.column("equity")
    reference_total = simulated[reference].path.total if reference in simulated else None
    cheap_total = simulated[names[0]].controls["cheap"].total
    reference_terminal = (
        contribution_terminal_wealth(reference_total, contribution=contribution)
        if reference_total is not None
        else None
    )
    cheap_terminal = contribution_terminal_wealth(cheap_total, contribution=contribution)
    descriptives: dict[str, dict[str, JsonValue]] = {}
    for name, item in simulated.items():
        total = item.path.total
        curve = np.cumprod(1.0 + total)
        summary = drawdown_summary(curve)
        excess_std = _volatility(item.path.excess)
        row: dict[str, JsonValue] = {
            "notional": item.notional.to_json(),
            "growth_log_pp_yr": _round(annualised_log_growth(total)),
            "arithmetic_mean_pp_yr": _round(float(np.mean(total)) * MONTHS_PER_YEAR * 100.0),
            "volatility_pct": _round(_volatility(total) * math.sqrt(MONTHS_PER_YEAR) * 100.0),
            "sharpe": _round(
                float(np.mean(item.path.excess)) / excess_std * math.sqrt(MONTHS_PER_YEAR)
                if excess_std > 0.0
                else 0.0
            ),
            "max_drawdown_pct": _round(summary.max_drawdown * 100.0, 2),
            "time_under_water_months": summary.max_time_under_water,
            "weighted_fee_bp": _round(item.path.weighted_fee_bp, 2),
            "annual_turnover_pct": _round(item.path.annual_turnover * 100.0, 3),
            "terminal_wealth_with_contributions": _round(
                contribution_terminal_wealth(total, contribution=contribution), 3
            ),
            "terminal_wealth_ratio_vs_cheap": _round(
                contribution_terminal_wealth(total, contribution=contribution) / cheap_terminal, 4
            ),
            "terminal_wealth_ratio_vs_reference": (
                None
                if reference_terminal is None
                else _round(
                    contribution_terminal_wealth(total, contribution=contribution)
                    / reference_terminal,
                    4,
                )
            ),
        }
        for label, other in (("vs_reference", reference_total), ("vs_cheap", cheap_total)):
            if other is None or _volatility(total - other) == 0.0:
                row[f"worst_decile_offset_{label}"] = None
                row[f"convexity_{label}"] = None
                continue
            offset = total - other
            dependence = tail_dependence(equity_leg, offset, quantile=tail)
            row[f"worst_decile_offset_{label}"] = {
                "months": dependence.months_low,
                "equity_mean_pp_month": _round(dependence.base_mean_low * 100.0, 3),
                "offset_mean_pp_month": _round(dependence.mean_low * 100.0, 3),
                "offset_hit_rate": _round(dependence.hit_rate_low, 3),
                "offset_worst_pp_month": _round(dependence.worst_low * 100.0, 3),
                "best_decile_offset_mean_pp_month": _round(dependence.mean_high * 100.0, 3),
            }
            shape = convexity(equity_leg, offset)
            row[f"convexity_{label}"] = {
                "kappa": _round(shape.kappa),
                "kappa_t": _round(shape.kappa_t, 2),
                "up_beta": _round(shape.up_beta),
                "down_beta": _round(shape.down_beta),
                "alpha_pp_month": _round(shape.alpha * 100.0, 3),
            }
        arm_episodes = episode_returns(panel.periods, total, windows=episode_windows)
        ref_episodes = (
            episode_returns(panel.periods, reference_total, windows=episode_windows)
            if reference_total is not None
            else None
        )
        cheap_episodes = episode_returns(panel.periods, cheap_total, windows=episode_windows)
        episode_rows: dict[str, JsonValue] = {}
        offsets_by_kind: dict[str, list[float]] = {}
        offsets_cheap_by_kind: dict[str, list[float]] = {}
        for i, episode in enumerate(episodes):
            a = arm_episodes[i]
            if not a.covered:
                episode_rows[episode.name] = {"kind": episode.kind, "covered": False}
                continue
            c = cheap_episodes[i]
            entry: dict[str, JsonValue] = {
                "kind": episode.kind,
                "covered": True,
                "partial": a.partial,
                "months": a.months,
                "arm_cumulative_pct": _round(a.cumulative_return * 100.0, 2),
                "arm_peak_to_trough_pct": _round(a.peak_to_trough * 100.0, 2),
                "cheap_cumulative_pct": _round(c.cumulative_return * 100.0, 2),
                "offset_vs_cheap_pp": _round(
                    (a.cumulative_return - c.cumulative_return) * 100.0, 2
                ),
            }
            offsets_cheap_by_kind.setdefault(episode.kind, []).append(
                (a.cumulative_return - c.cumulative_return) * 100.0
            )
            if ref_episodes is not None:
                r = ref_episodes[i]
                entry["reference_cumulative_pct"] = _round(r.cumulative_return * 100.0, 2)
                entry["offset_vs_reference_pp"] = _round(
                    (a.cumulative_return - r.cumulative_return) * 100.0, 2
                )
                offsets_by_kind.setdefault(episode.kind, []).append(
                    (a.cumulative_return - r.cumulative_return) * 100.0
                )
            episode_rows[episode.name] = entry
        row["episodes"] = episode_rows
        row["episode_type_mean_offset_vs_reference_pp"] = {
            kind: {"episodes": len(vals), "mean_pp": _round(float(np.mean(vals)), 2)}
            for kind, vals in offsets_by_kind.items()
        }
        row["episode_type_mean_offset_vs_cheap_pp"] = {
            kind: {"episodes": len(vals), "mean_pp": _round(float(np.mean(vals)), 2)}
            for kind, vals in offsets_cheap_by_kind.items()
        }
        control_rows: dict[str, JsonValue] = {}
        for control, control_path in item.controls.items():
            control_curve = np.cumprod(1.0 + control_path.total)
            control_summary = drawdown_summary(control_curve)
            control_rows[control] = {
                "definition": item.control_definition[control],
                "growth_log_pp_yr": _round(annualised_log_growth(control_path.total)),
                "arithmetic_mean_pp_yr": _round(
                    float(np.mean(control_path.total)) * MONTHS_PER_YEAR * 100.0
                ),
                "volatility_pct": _round(
                    _volatility(control_path.total) * math.sqrt(MONTHS_PER_YEAR) * 100.0
                ),
                "max_drawdown_pct": _round(control_summary.max_drawdown * 100.0, 2),
                "time_under_water_months": control_summary.max_time_under_water,
            }
        row["controls"] = control_rows
        descriptives[name] = row

    # Bond-equity regime, era by era, beside the bond leg's realised excess return.
    bond_regime: list[dict[str, JsonValue]] = []
    if "treasury" in panel.series:
        bond = panel.column("treasury")
        trend = panel.column("trend") if "trend" in panel.series else None
        for era_name, start, end in [("panel_full", panel.periods[0], panel.periods[-1]), *windows]:
            keep = _slice(panel.periods, start, end)
            b, e = bond[keep], equity_leg[keep]
            entry_regime: dict[str, JsonValue] = {
                "era": era_name,
                "window": f"{start}..{end}",
                "months": int(keep.size),
                "bond_equity_correlation": _round(float(np.corrcoef(b, e)[0, 1]), 3),
                "bond_excess_pp_yr": _round(float(np.mean(b)) * MONTHS_PER_YEAR * 100.0, 2),
                "bond_volatility_pct": _round(
                    _volatility(b) * math.sqrt(MONTHS_PER_YEAR) * 100.0, 2
                ),
                "equity_excess_pp_yr": _round(float(np.mean(e)) * MONTHS_PER_YEAR * 100.0, 2),
                "cash_pp_yr": _round(float(np.mean(panel.cash[keep])) * MONTHS_PER_YEAR * 100.0, 2),
            }
            if trend is not None:
                entry_regime["trend_excess_pp_yr"] = _round(
                    float(np.mean(trend[keep])) * MONTHS_PER_YEAR * 100.0, 2
                )
            bond_regime.append(entry_regime)

    return PanelResult(
        spec=spec,
        panel=panel,
        arms=simulated,
        comparisons=comparisons,
        descriptives=descriptives,
        bond_regime=bond_regime,
        financing=financing,
        families=families,
    )


def _panel_json(result: PanelResult) -> dict[str, JsonValue]:
    arms_json: list[JsonValue] = []
    for name, item in result.arms.items():
        row: dict[str, JsonValue] = {
            "arm": name,
            "role": item.arm.role,
            "note": item.arm.note,
            "weights": {t: w for t, w in zip(item.arm.tickers, item.arm.weights, strict=True)},
        }
        row.update(result.descriptives[name])
        row["comparisons"] = {
            control: comparison.to_json()
            for control, comparison in result.comparisons[name].items()
        }
        arms_json.append(row)
    return {
        "id": result.spec.id,
        "role": result.spec.role,
        "note": result.spec.note,
        "trend_source": result.spec.trend_source,
        "bond_source": result.spec.bond_source,
        "window": f"{result.panel.periods[0]}..{result.panel.periods[-1]}",
        "months": result.panel.months,
        "panel_findings": list(result.panel.findings),
        "arms": arms_json,
        "bond_equity_regime_by_era": list(result.bond_regime),
        "financing_sensitivity": result.financing,
        "multiple_testing_families": {k: sorted(v) for k, v in result.families.items()},
    }


# --------------------------------------------------------------------------- #
# Markdown tables
# --------------------------------------------------------------------------- #


def _fmt(value: float | None, digits: int = 2) -> str:
    return "--" if value is None else f"{value:+.{digits}f}"


def _map(value: JsonValue) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise DefensiveEnginesError(f"expected a mapping, got {type(value).__name__}")
    return value


def _seq(value: JsonValue) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise DefensiveEnginesError(f"expected a list, got {type(value).__name__}")
    return value


def _as_float(value: JsonValue) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _cell(comparison: Comparison | None) -> str:
    if comparison is None:
        return "--"
    if comparison.gap is None:
        return "identical" if comparison.identical else "--"
    g = comparison.gap
    years = "inf" if not math.isfinite(g.years_to_distinguish) else f"{g.years_to_distinguish:.0f}y"
    return (
        f"{g.gap_pp_yr:+.2f} [{g.interval[0]:+.2f}, {g.interval[1]:+.2f}] "
        f"MDE {g.mde_pp_yr:.2f} {years} `{comparison.status}`"
    )


def _kind_cell(value: JsonValue) -> str:
    if not isinstance(value, Mapping):
        return "--"
    return f"{value['mean_pp']} ({value['episodes']} ep.)"


def _arm_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Arms: notional, growth, drawdown (descriptive)\n",
        "| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % "
        "| Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: "
        "| ---: | ---: |",
    ]
    for name, item in result.arms.items():
        d = result.descriptives[name]
        n = item.notional
        lines.append(
            f"| `{name}` | {n.gross:.3f} | {n.equity:.3f} | {n.trend:.3f} | {n.bond:.3f} | "
            f"{n.gold:.3f} | {n.cash:.3f} | {d['arithmetic_mean_pp_yr']} | "
            f"{d['growth_log_pp_yr']} | {d['volatility_pct']} | {d['sharpe']} | "
            f"{d['max_drawdown_pct']} | {d['time_under_water_months']} | "
            f"{d['terminal_wealth_ratio_vs_reference']} | {d['terminal_wealth_ratio_vs_cheap']} |"
        )
    return lines


def _controls_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### The controls themselves: what the levered and volatility-matched "
        "comparators cost in drawdown (descriptive)\n",
        "| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | "
        "months under water |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in result.arms:
        controls = _map(result.descriptives[name]["controls"])
        for control in (
            "leverage_matched",
            "volatility_matched_expost",
            "volatility_matched_exante",
        ):
            if control not in controls:
                continue
            c = _map(controls[control])
            lines.append(
                f"| `{name}` | {control} | {c['definition']} | {c['arithmetic_mean_pp_yr']} | "
                f"{c['growth_log_pp_yr']} | {c['volatility_pct']} | {c['max_drawdown_pct']} | "
                f"{c['time_under_water_months']} |"
            )
    return lines


def _gap_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Arithmetic gaps against each control: gap [95% interval] MDE "
        "years-to-distinguish status\n",
        "| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | "
        "vs vol-matched (ex ante, from month 37) | vs reference |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name in result.arms:
        c = result.comparisons[name]
        lines.append(
            f"| `{name}` | {_cell(c.get('cheap'))} | {_cell(c.get('leverage_matched'))} | "
            f"{_cell(c.get('volatility_matched_expost'))} | "
            f"{_cell(c.get('volatility_matched_exante'))} | {_cell(c.get('reference'))} |"
        )
    return lines


def _crisis_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Crisis behaviour against the reference arm (descriptive)\n",
        "| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | "
        "deflationary episodes mean pp | inflation episodes mean pp | "
        "flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in result.arms:
        d = result.descriptives[name]
        wd = d.get("worst_decile_offset_vs_reference")
        cv = d.get("convexity_vs_reference")
        kinds = _map(d["episode_type_mean_offset_vs_reference_pp"])
        c = result.comparisons[name]
        flat_ref = c["reference"].era_gaps.get("flat_equity_decade") if "reference" in c else None
        flat_cheap = c["cheap"].era_gaps.get("flat_equity_decade")
        wd_text = (
            f"{wd['offset_mean_pp_month']} ({wd['offset_hit_rate']})"
            if isinstance(wd, Mapping)
            else "--"
        )
        cv_text = f"{cv['kappa']} ({cv['kappa_t']})" if isinstance(cv, Mapping) else "--"
        lines.append(
            f"| `{name}` | {wd_text} | {cv_text} | "
            f"{_kind_cell(kinds.get('deflationary_or_growth'))} | "
            f"{_kind_cell(kinds.get('inflation_or_rate'))} | "
            f"{_fmt(flat_ref)} | {_fmt(flat_cheap)} |"
        )
    return lines


def _episode_table(result: PanelResult) -> list[str]:
    first_name = next(iter(result.arms))
    episode_names = list(_map(result.descriptives[first_name]["episodes"]))
    lines = [
        "\n### Crisis episodes: arm cumulative return % (offset against reference, pp); "
        "* marks partial coverage, n/c not covered\n",
        "| arm | " + " | ".join(episode_names) + " |",
        "| --- | " + " | ".join("---:" for _ in episode_names) + " |",
    ]
    for name in result.arms:
        episodes = _map(result.descriptives[name]["episodes"])
        cells: list[str] = []
        for episode_name in episode_names:
            e = _map(episodes[episode_name])
            if not e.get("covered"):
                cells.append("n/c")
                continue
            star = "*" if e.get("partial") else ""
            cells.append(
                f"{e['arm_cumulative_pct']}{star} "
                f"({_fmt(_as_float(e.get('offset_vs_reference_pp')))})"
            )
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    return lines


def _regime_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Bond-equity regime by era (the bond leg's realised history, to haircut against)\n",
        "| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | "
        "equity excess pp/yr | trend excess pp/yr | cash pp/yr |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in result.bond_regime:
        lines.append(
            f"| {r['era']} | {r['window']} | {r['months']} | {r['bond_equity_correlation']} | "
            f"{r['bond_excess_pp_yr']} | {r['bond_volatility_pct']} | "
            f"{r['equity_excess_pp_yr']} | {r.get('trend_excess_pp_yr', '--')} | "
            f"{r['cash_pp_yr']} |"
        )
    return lines


def _financing_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Financing sensitivity: gap against the reference arm at each basis (pp/yr), "
        "then against the cheap control\n"
    ]
    for attribute, raw_block in result.financing.items():
        block = _map(raw_block)
        grid = [
            str(int(g)) for g in (_as_float(x) or 0.0 for x in _seq(block["grid_basis_points"]))
        ]
        lines.append(f"\n{attribute} basis, bp: " + ", ".join(grid))
        lines.append(
            "ordering against reference stable across the band: "
            f"`{block['ordering_against_reference_stable']}`\n"
        )
        lines.append("| arm | " + " | ".join(grid) + " | vs cheap at each point |")
        lines.append("| --- | " + " | ".join("---:" for _ in grid) + " | --- |")
        for name, raw_controls in _map(block["gaps_pp_yr"]).items():
            by_control = _map(raw_controls)
            ref = by_control.get("reference")
            cheap = by_control.get("cheap")
            ref_cells = (
                " | ".join(_fmt(_as_float(v)) for v in _seq(ref))
                if ref is not None
                else " | ".join("--" for _ in grid)
            )
            cheap_cells = (
                ", ".join(_fmt(_as_float(v)) for v in _seq(cheap)) if cheap is not None else "--"
            )
            lines.append(f"| `{name}` | {ref_cells} | {cheap_cells} |")
    return lines


def render_tables(results: Sequence[PanelResult], *, header: Sequence[str]) -> str:
    lines: list[str] = list(header)
    for result in results:
        lines.append(
            f"\n## Panel `{result.spec.id}` ({result.spec.role}): "
            f"{result.panel.periods[0]}..{result.panel.periods[-1]}, {result.panel.months} "
            f"months, trend `{result.spec.trend_source}`, bond `{result.spec.bond_source}`\n"
        )
        lines.append(result.spec.note.strip())
        lines.extend(_arm_table(result))
        lines.extend(_gap_table(result))
        lines.extend(_controls_table(result))
        lines.extend(_crisis_table(result))
        lines.extend(_episode_table(result))
        if result.bond_regime:
            lines.extend(_regime_table(result))
        if result.financing:
            lines.extend(_financing_table(result))
    return "\n".join(lines) + "\n"


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
    legs = build_legs(raw, specification)
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = read_rates(specification)
    panels = read_panels(specification)
    reference = _text(parameters, "reference_arm", where="parameters")
    in_estimates = tuple(
        str(x)
        for x in _sequence(_at(parameters, "controls_in_estimates", where="parameters"), where="c")
    )
    scored_roles = {"primary", "primary_subwindow", "secondary", "check"}

    results: list[PanelResult] = []
    for spec in panels:
        panel = build_panel(legs, spec)
        results.append(
            score_panel(
                spec,
                panel,
                specification=specification,
                arms=arms,
                wrappers=wrappers,
                rates=rates,
                rng=context.rng,
                full=spec.role in scored_roles,
            )
        )

    # Bond-series sensitivity: the GS10 panel against the ltr panel on one window.
    by_id = {r.spec.id: r for r in results}
    bond_sensitivity: dict[str, JsonValue] = {}
    if "bond_series_sensitivity" in by_id and "bond_series_sensitivity_ltr" in by_id:
        gs10, ltr = by_id["bond_series_sensitivity"], by_id["bond_series_sensitivity_ltr"]
        if gs10.panel.periods != ltr.panel.periods:
            raise DefensiveEnginesError("the two bond-series panels are not on one window")
        rows: dict[str, JsonValue] = {}
        for name in gs10.arms:
            entry: dict[str, JsonValue] = {}
            for control in ("cheap", "reference"):
                a = gs10.comparisons[name].get(control)
                b = ltr.comparisons[name].get(control)
                if a is None or b is None or a.gap is None or b.gap is None:
                    continue
                entry[f"gap_vs_{control}_gs10_pp_yr"] = _round(a.gap.gap_pp_yr)
                entry[f"gap_vs_{control}_ltr_pp_yr"] = _round(b.gap.gap_pp_yr)
                entry[f"gs10_minus_ltr_vs_{control}_pp_yr"] = _round(
                    a.gap.gap_pp_yr - b.gap.gap_pp_yr
                )
            entry["max_drawdown_gs10_pct"] = gs10.descriptives[name]["max_drawdown_pct"]
            entry["max_drawdown_ltr_pct"] = ltr.descriptives[name]["max_drawdown_pct"]
            rows[name] = entry
        bond_sensitivity = {
            "window": f"{gs10.panel.periods[0]}..{gs10.panel.periods[-1]}",
            "months": gs10.panel.months,
            "what": (
                "Every arm re-run with a 10-year par bond modelled from GS10 in place of the "
                "~20-year Goyal-Welch ltr, on one window, own trend book on both. Positive "
                "gs10_minus_ltr means the shorter bond helped the arm more."
            ),
            "arms": rows,
        }

    # Estimates and the verdict.
    estimates: list[Estimate] = []
    resolved: list[str] = []
    scored = 0
    for result in results:
        if result.spec.role not in scored_roles:
            continue
        for name, by_control in result.comparisons.items():
            for control, comparison in by_control.items():
                if comparison.gap is None or comparison.identical:
                    continue
                if comparison.status == "exploratory" and result.spec.role != "check":
                    resolved.append(f"{result.spec.id}:{name} vs {control}")
                if control not in in_estimates:
                    continue
                scored += 1
                label = f"{result.spec.id}:{name} vs {control}"
                g = comparison.gap
                estimates.append(
                    Estimate(
                        name=f"arithmetic_gap[{label}]",
                        value=g.gap_pp_yr,
                        units="percentage points per year",
                        interval=g.interval,
                        interval_method=(
                            "stationary block bootstrap on the joint panel, whole rows, mean "
                            f"block 12 months, {specification.inference.resamples} resamples, "
                            "95% percentile"
                        ),
                        cost_basis=CostBasis.NET_PESSIMISTIC,
                        n_obs=g.months,
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
                        n_obs=g.months,
                        notes=(
                            "80% power, two-sided at 0.05, from this comparison's own "
                            "paired series."
                        ),
                        uncertainty_unavailable_reason=(
                            "a detection floor is a property of the design, not an estimate of "
                            "a quantity in the world, so it carries no interval"
                        ),
                    )
                )
    status = ResultStatus.EXPLORATORY if resolved else ResultStatus.UNRESOLVED

    primary = by_id.get("primary")
    primary_note = ""
    if primary is not None:
        ref_vs_cheap = primary.comparisons[reference]["cheap"].gap
        if ref_vs_cheap is not None:
            primary_note = (
                f" On the {primary.panel.months}-month primary panel the reference arm's gap "
                f"against the cheap control is {ref_vs_cheap.gap_pp_yr:+.2f} pp/yr against a "
                f"{ref_vs_cheap.mde_pp_yr:.2f} pp/yr floor."
            )
    scored_panels = len([r for r in results if r.spec.role in scored_roles])
    summary = (
        f"{scored} arm-against-control comparisons scored on {scored_panels} panels, "
        "on assumed wrapper exposure vectors rather than fund returns. "
        f"{len(resolved)} comparison(s) on the primary, gold-subwindow or secondary panel "
        f"separate from their control by more than the design can resolve; every other "
        f"mean gap is `unresolved`, as the freeze note predicted.{primary_note} The drawdown, "
        "worst-decile, crisis-episode and terminal-wealth tables are descriptive and carry no "
        "significance claim."
    )

    freeze_note = (
        "WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS. The bond leg is realised "
        "history that contains the 1981-2020 bull market and is a ~20-year bond, longer than "
        "the Treasury-futures ladders RSSB and NTSX hold. The long-panel trend leg is this "
        "repository's own 4-asset book scaled by one full-window constant; the secondary "
        "panel's is AQR's TSMOM, gross of the vendor's trading costs by omission. The gold "
        "sub-window includes 1971-08..1974-12, when the dollar gold price was an administered "
        "peg and private US ownership was illegal. Gold financing at 30 bp is an assumption. "
        "Every mean gap was predicted `unresolved` before the run."
    )
    header = [
        "# Experiment 018: defensive engines inside the leveraged construction",
        "",
        f"Run `{context.run_id}`; specification hash `{specification.spec_hash}`.",
        "",
        freeze_note,
        "",
        f"Trend-book volatility scalar {legs.trend_scalar:.4f} (realised "
        f"{legs.trend_book_realised_volatility_pct:.2f}% on {legs.trend_book_window[0]}.."
        f"{legs.trend_book_window[1]}, target 12.38%).",
        "",
        "Gap cells read: point estimate [95% block-bootstrap interval] MDE at 80% power, "
        "years to distinguish, falsifier status. A control column marked `identical` is the "
        "arm itself. Descriptive tables carry no status by design.",
    ]
    tables = render_tables(results, header=header)

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in raw.provenance],
        "source_findings": list(raw.findings),
        "trend_book": {
            "scalar": round(legs.trend_scalar, 6),
            "realised_volatility_pct_on_primary_window": round(
                legs.trend_book_realised_volatility_pct, 4
            ),
            "primary_window": list(legs.trend_book_window),
            "note": (
                "One constant applied to every month; Sharpe-preserving; a look-ahead on "
                "magnitude only. The book ends where the AQR commodity leg ends."
            ),
        },
        "financing_rates_basis_points": {
            "equity": rates.equity,
            "treasury": rates.treasury,
            "gold": rates.gold,
            "tips": rates.tips,
        },
        "wrappers": {
            t: {
                "exposures": dict(w.exposures),
                "fee_bp": w.fee_bp,
                "financed": dict(w.financed),
                "note": w.note,
            }
            for t, w in wrappers.items()
        },
        "panels": [_panel_json(r) for r in results],
        "bond_series_sensitivity": bond_sensitivity,
        "resolved_comparisons": resolved,
        "markdown_tables": tables,
        "what_this_cannot_resolve": (
            "A comparison's floor is 0.285 pp/yr per point of tracking error on the primary "
            "panel and 0.435 on the secondary. A financed 20-point Treasury leg's expected "
            "contribution is a few tenths of a point against a floor of about half a point; "
            "the reference arm's trend contribution is measured against a floor of about "
            "1.1 pp/yr (primary) and 1.7 pp/yr (secondary)."
        ),
    }
    caveats = (
        "Wrappers are assumed exposure vectors. This ranks constructions and cannot rank funds.",
        "The bond leg (Goyal-Welch ltr) is a ~20-year bond and its window contains the "
        "1981-2020 bull market; read every bond arm beside the era table.",
        "The own 4-asset trend book is scaled by one full-window constant and charged no "
        "trading cost; AQR's TSMOM is gross of the vendor's trading costs by omission.",
        "The gold sub-window includes 1971-08..1974-12; gold financing at 30 bp is an assumption.",
        "The TIPS series is modelled from a real par yield on 280 months; a check, not a test.",
        "Drawdown, worst-decile, episode and terminal-wealth figures describe one realised "
        "history and carry no significance claim.",
        "No sleeve, fund or portfolio is promoted.",
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
        prog="python -m portfolio_edge.experiments.exp_018_defensive_engines",
        description="Hold defensive engines inside the leveraged construction and score them.",
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
