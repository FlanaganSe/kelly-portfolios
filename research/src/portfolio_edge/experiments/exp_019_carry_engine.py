"""Experiment 019: multi-asset futures carry as a second financed engine.

What this is
------------
The recommended portfolio is 70% cheap equity core plus 30% of an RSST-like
stocks-plus-trend wrapper. The stacking arithmetic says a second financed
engine earns its place only with a positive expected excess return and a low
correlation to what is already held. This module holds an RSSY-like wrapper
(1.0 equity + 1.0 multi-asset carry per dollar) stacked on the construction,
substituted for half of the trend wrapper, and alone in place of it, and scores
each against cheap, leverage-matched, volatility-matched and reference controls
on Experiment 018's panels, with the carry leg drawn from AQR's century-of-
factor-premia workbook.

What this is NOT
----------------
**It does not score funds.** Every wrapper is an assumed per-dollar exposure
vector and a fee. The carry leg is a vendor reconstruction gross of every cost.

**Its whole-experiment status is inherited from the trend reference** (which
clears its floor against the cheap control on 96 years) and says nothing about
carry; the carry question lives in the paired rows against the reference arm.

Run it::

    uv run python -m portfolio_edge.experiments.exp_019_carry_engine --view-results
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import aqr, french, goyal_welch
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MONTHS_PER_YEAR,
    BasisPanel,
    CostSettings,
    FundMapping,
    PortfolioPath,
    _at,
    _mapping,
    _number,
    _numbers,
    _sequence,
    _simulate,
    _text,
    annualised_log_growth,
    workspace_root,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    Comparison,
    FinancingRates,
    Wrapper,
    _apply_falsifier,
    _column,
    _era_windows,
    _require_cached,
    _round,
    _slice,
    arithmetic_gap,
    build_trend_book,
    contribution_terminal_wealth,
    read_episodes,
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
from portfolio_edge.studies.stress_dependence import (
    convexity,
    episode_returns,
    tail_dependence,
)
from portfolio_edge.studies.time_series_momentum import TimeSeriesMomentumSpec

FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]
MonthSeries = dict[str, float]

ENTRY_POINT: Final = "exp_019_carry_engine"

#: The legs a panel may carry, in the order the notional table prints them.
LEGS: Final = ("equity", "trend", "carry")

#: The carry-leg variants a panel may name. ``published`` is the vendor series
#: scaled once; the others are the hostile re-runs the specification freezes.
CARRY_VARIANTS: Final = (
    "published",
    "cost_1pp",
    "cost_2pp",
    "loading_0681",
    "shifted_one_month",
)

SCORED_ROLES: Final = frozenset({"primary", "primary_subwindow", "secondary", "check"})

__all__ = [
    "CARRY_VARIANTS",
    "ENTRY_POINT",
    "LEGS",
    "Arm",
    "CarryEngineError",
    "Notional",
    "arm_notional",
    "build_registry",
    "carry_variants",
    "correlation_table",
    "default_specification_path",
    "main",
    "read_arms",
    "read_wrappers",
    "run",
    "sum_rule_residual",
]


class CarryEngineError(Exception):
    """The experiment refused to run, or a source did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_019_carry_engine.yaml"


# --------------------------------------------------------------------------- #
# Wrappers, arms, notional
# --------------------------------------------------------------------------- #


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
    carry: float
    cash: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "gross": round(self.gross, 4),
            "equity": round(self.equity, 4),
            "trend": round(self.trend, 4),
            "carry": round(self.carry, 4),
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
                raise CarryEngineError(f"wrappers.{ticker} names unknown leg {leg!r}")
        for leg in financed:
            if leg != "equity":
                raise CarryEngineError(
                    f"wrappers.{ticker} finances {leg!r}; only equity futures carry a "
                    "signed basis here, the long/short books are charged none"
                )
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
            raise CarryEngineError(
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
    """The equity basis; the other legs of exp_018's rate table are zero and unused."""
    costs = _mapping(specification.cost_model, where="cost_model")
    block = _mapping(
        _at(costs, "financing_basis_points_over_cash", where="cost_model"), where="financing"
    )
    return FinancingRates(
        equity=_number(block, "equity", where="financing"), treasury=0.0, gold=0.0, tips=0.0
    )


def arm_notional(
    tickers: Sequence[str], weights: Sequence[float], wrappers: Mapping[str, Wrapper]
) -> Notional:
    """Capital weights times per-dollar exposures, leg by leg."""
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
        carry=by_leg["carry"],
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
    carry: MonthSeries
    carry_components: Mapping[str, MonthSeries]
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


def load_series(specification: Specification) -> RawSeries:
    """Read every pinned source from the cache, hash-checked, never downloaded."""
    cache = RawCache()
    pins = _pins(specification)
    parameters = _mapping(specification.parameters, where="parameters")
    carry_block = _mapping(_at(parameters, "carry_leg", where="parameters"), where="carry_leg")
    carry_column = _text(carry_block, "column", where="carry_leg")
    components = [
        str(x)
        for x in _sequence(_at(carry_block, "component_columns", where="carry_leg"), where="c")
    ]
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []

    def take(file_id: str, url: str) -> tuple[CacheEntry, dict[str, JsonValue]]:
        try:
            entry, record = _require_cached(cache, url, pins[file_id])
        except Exception as exc:
            raise CarryEngineError(str(exc)) from exc
        if record["committed_manifest_raw_hash_matches"] is False:
            findings.append(
                f"{file_id}: the pinned file ({record['sha256_raw']}) is a different "
                "vintage from the one the committed manifest records."
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
    table = french.parse(cache, entry, dataset=ff3).table("monthly")
    equity = _column(table.periods, table.column("Mkt-RF"))
    cash = _column(table.periods, table.column("RF"))
    record["first_observation"], record["last_observation"] = min(equity), max(equity)

    gw = goyal_welch.get_dataset("goyal_welch_predictors")
    entry, record = take("goyal_welch_predictors", gw.url)
    parsed = goyal_welch.parse(cache, entry, dataset=gw)
    monthly = next(t for t in parsed.tables if t.table_id == "monthly")
    ltr = _column(monthly.periods, monthly.column("ltr"))
    corpr = _column(monthly.periods, monthly.column("corpr"))
    gw_rfree = _column(monthly.periods, monthly.column("Rfree"))
    record["first_observation"], record["last_observation"] = min(ltr), max(ltr)

    commodity_dataset = aqr.get_dataset("aqr_commodities_long_run")
    entry, record = take("aqr_commodities_long_run", commodity_dataset.url)
    ctable = aqr.parse(cache, entry, dataset=commodity_dataset).table
    commodity = _column(
        ctable.periods, ctable.column("Excess return of equal-weight commodities portfolio")
    )
    record["first_observation"], record["last_observation"] = min(commodity), max(commodity)

    tsmom_dataset = aqr.get_dataset("aqr_tsmom_factors")
    entry, record = take("aqr_tsmom_factors", tsmom_dataset.url)
    ttable = aqr.parse(cache, entry, dataset=tsmom_dataset).table
    tsmom = _column(ttable.periods, ttable.column("TSMOM"))
    record["first_observation"], record["last_observation"] = min(tsmom), max(tsmom)

    carry_dataset = aqr.get_dataset("aqr_century_factor_premia")
    entry, record = take("aqr_century_factor_premia", carry_dataset.url)
    ktable = aqr.parse(cache, entry, dataset=carry_dataset).table
    carry = _column(ktable.periods, ktable.column(carry_column))
    carry_components = {name: _column(ktable.periods, ktable.column(name)) for name in components}
    record["first_observation"], record["last_observation"] = min(carry), max(carry)
    record["column"] = carry_column

    return RawSeries(
        equity=equity,
        cash=cash,
        ltr=ltr,
        corpr=corpr,
        gw_rfree=gw_rfree,
        commodity=commodity,
        tsmom=tsmom,
        carry=carry,
        carry_components=carry_components,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PanelSpec:
    id: str
    role: str
    trend_source: str
    carry_source: str
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
        carry_source = _text(entry, "carry_source", where="panels[]")
        if carry_source not in CARRY_VARIANTS:
            raise CarryEngineError(
                f"panel {entry.get('id')}: unknown carry_source {carry_source!r}"
            )
        out.append(
            PanelSpec(
                id=_text(entry, "id", where="panels[]"),
                role=_text(entry, "role", where="panels[]"),
                trend_source=_text(entry, "trend_source", where="panels[]"),
                carry_source=carry_source,
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


def carry_variants(
    scaled: MonthSeries, *, haircuts_pp_yr: Mapping[str, float], loading: float
) -> dict[str, MonthSeries]:
    """The published leg and the frozen hostile re-runs of it.

    ``cost_*`` subtract a flat annual haircut per unit of notional; ``loading_0681``
    multiplies the leg by the delivered loading; ``shifted_one_month`` moves every
    observation one month later, which keeps the mean and destroys same-month
    alignment. Nothing here changes a sign of the underlying series.
    """
    months = sorted(scaled)
    out: dict[str, MonthSeries] = {"published": dict(scaled)}
    out["cost_1pp"] = {
        m: v - haircuts_pp_yr["cost_1pp"] / 100.0 / MONTHS_PER_YEAR for m, v in scaled.items()
    }
    out["cost_2pp"] = {
        m: v - haircuts_pp_yr["cost_2pp"] / 100.0 / MONTHS_PER_YEAR for m, v in scaled.items()
    }
    out["loading_0681"] = {m: v * loading for m, v in scaled.items()}
    shifted: MonthSeries = {}
    for earlier, later in itertools.pairwise(months):
        if month_index(later) - month_index(earlier) == 1:
            shifted[later] = scaled[earlier]
    out["shifted_one_month"] = shifted
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class LegLibrary:
    equity: MonthSeries
    cash: MonthSeries
    trend: Mapping[str, MonthSeries]
    carry: Mapping[str, MonthSeries]
    carry_components: Mapping[str, MonthSeries]
    trend_scalar: float
    trend_realised_volatility_pct: float
    carry_scalar: float
    carry_realised_volatility_pct: float
    primary_window: tuple[str, str]


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
    trend_target = _number(book_block, "target_volatility_percent", where="trend_book") / 100.0
    carry_block = _mapping(_at(parameters, "carry_leg", where="parameters"), where="carry_leg")
    carry_target = _number(carry_block, "target_volatility_percent", where="carry_leg") / 100.0
    loading = _number(carry_block, "delivered_loading_sensitivity", where="carry_leg")
    costs = _mapping(specification.cost_model, where="cost_model")
    haircut_block = _mapping(_at(costs, "carry_leg_haircut_pp_yr", where="cost_model"), where="h")
    haircuts = {
        k: _number(haircut_block, k, where="carry_leg_haircut_pp_yr")
        for k in ("cost_1pp", "cost_2pp")
    }

    treasury_gw = {p: raw.ltr[p] - raw.gw_rfree[p] for p in raw.ltr if p in raw.gw_rfree}
    credit_gw = {p: raw.corpr[p] - raw.gw_rfree[p] for p in raw.corpr if p in raw.gw_rfree}
    try:
        unscaled = build_trend_book(
            (raw.equity, treasury_gw, credit_gw, raw.commodity),
            spec=spec,
            minimum_instruments=minimum,
            end=max(raw.commodity),
        )
    except Exception as exc:
        raise CarryEngineError(str(exc)) from exc

    primary = sorted(set(unscaled) & set(raw.equity) & set(raw.cash) & set(raw.carry))
    if len(primary) < 2 * MONTHS_PER_YEAR:
        raise CarryEngineError("the primary window is shorter than two years")
    trend_realised = float(np.std([unscaled[p] for p in primary], ddof=1)) * math.sqrt(
        MONTHS_PER_YEAR
    )
    trend_scalar = trend_target / trend_realised
    scaled_trend = {p: v * trend_scalar for p, v in unscaled.items()}

    carry_realised = float(np.std([raw.carry[p] for p in primary], ddof=1)) * math.sqrt(
        MONTHS_PER_YEAR
    )
    carry_scalar = carry_target / carry_realised
    scaled_carry = {p: v * carry_scalar for p, v in raw.carry.items()}

    return LegLibrary(
        equity=raw.equity,
        cash=raw.cash,
        trend={"own_4_asset_book": scaled_trend, "aqr_tsmom": dict(raw.tsmom)},
        carry=carry_variants(scaled_carry, haircuts_pp_yr=haircuts, loading=loading),
        carry_components={k: dict(v) for k, v in raw.carry_components.items()},
        trend_scalar=trend_scalar,
        trend_realised_volatility_pct=trend_realised * 100.0,
        carry_scalar=carry_scalar,
        carry_realised_volatility_pct=carry_realised * 100.0,
        primary_window=(primary[0], primary[-1]),
    )


def build_panel(legs: LegLibrary, spec: PanelSpec) -> BasisPanel:
    """Intersect the legs a panel names, on the window it declares."""
    sources: dict[str, MonthSeries] = {"equity": legs.equity}
    if "trend" in spec.legs:
        try:
            sources["trend"] = legs.trend[spec.trend_source]
        except KeyError:
            raise CarryEngineError(f"unknown trend_source {spec.trend_source!r}") from None
    if "carry" in spec.legs:
        sources["carry"] = legs.carry[spec.carry_source]
    unknown = set(spec.legs) - set(sources)
    if unknown:
        raise CarryEngineError(f"panel {spec.id}: unknown legs {sorted(unknown)}")
    common = set(legs.cash)
    for series in sources.values():
        common &= set(series)
    periods = sorted(common)
    if spec.start is not None:
        periods = [p for p in periods if month_index(p) >= month_index(spec.start)]
    if spec.end is not None:
        periods = [p for p in periods if month_index(p) <= month_index(spec.end)]
    if len(periods) < 3 * MONTHS_PER_YEAR:
        raise CarryEngineError(f"panel {spec.id} holds {len(periods)} months")
    for earlier, later in itertools.pairwise(periods):
        if month_index(later) - month_index(earlier) != 1:
            raise CarryEngineError(f"panel {spec.id} has a gap between {earlier} and {later}")
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
# Simulation
# --------------------------------------------------------------------------- #


def wrapper_excess(panel: BasisPanel, wrapper: Wrapper, rates: FinancingRates) -> FloatArray:
    """``sum(exposure * leg) - fee/12 - financed_equity * basis/12``, monthly."""
    total = np.zeros(panel.months, dtype=np.float64)
    for leg, exposure in wrapper.exposures.items():
        total = total + exposure * panel.column(leg)
    annual_charge = wrapper.fee_bp / 10_000.0
    for leg, notional in wrapper.financed.items():
        annual_charge += notional * rates.for_leg(leg) / 10_000.0
    return np.asarray(total - annual_charge / MONTHS_PER_YEAR, dtype=np.float64)


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
    """Monthly rebalance to ``targets``; capital above one borrows at the equity basis."""
    columns = [wrapper_excess(panel, wrappers[t], rates) for t in tickers]
    excess = np.column_stack(columns) if columns else np.zeros((panel.months, 0))
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
# Descriptive statistics that are the point of this experiment
# --------------------------------------------------------------------------- #


def _corr(a: FloatArray, b: FloatArray) -> float | None:
    if a.size < 3 or _volatility(a) == 0.0 or _volatility(b) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def correlation_table(
    legs: Mapping[str, FloatArray], *, equity: FloatArray, tail: float
) -> dict[str, JsonValue]:
    """Pairwise correlations of the named legs, full sample and in equity's worst decile.

    The tail is the lowest ``tail`` fraction of ``equity`` months; the same months
    are selected for every pair so the rows are comparable. A conditional
    correlation is biased toward zero by the truncation and is read only against
    the other conditional entries.
    """
    n = equity.size
    k = max(1, math.floor(n * tail))
    order = np.argsort(equity)
    low = order[:k]
    names = list(legs)
    full: dict[str, JsonValue] = {}
    worst: dict[str, JsonValue] = {}
    for a, b in itertools.combinations(names, 2):
        c_full = _corr(legs[a], legs[b])
        full[f"{a}_{b}"] = None if c_full is None else _round(c_full, 3)
        c_low = _corr(legs[a][low], legs[b][low])
        worst[f"{a}_{b}"] = None if c_low is None else _round(c_low, 3)
    means: dict[str, JsonValue] = {}
    for a in names:
        means[a] = {
            "full_pp_yr": _round(float(np.mean(legs[a])) * MONTHS_PER_YEAR * 100.0, 2),
            "worst_decile_pp_month": _round(float(np.mean(legs[a][low])) * 100.0, 3),
            "worst_decile_hit_rate": _round(float(np.mean(legs[a][low] > 0.0)), 3),
            "volatility_pct": _round(_volatility(legs[a]) * math.sqrt(MONTHS_PER_YEAR) * 100.0, 2),
        }
    return {
        "months": n,
        "worst_decile_months": int(k),
        "correlation_full": full,
        "correlation_worst_decile_of_equity": worst,
        "legs": means,
    }


def sum_rule_residual(gap_both: float, gap_trend_only: float, gap_carry_only: float) -> float:
    """``gap(both) - gap(trend) - gap(carry)``, all against the cheap control."""
    return gap_both - gap_trend_only - gap_carry_only


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
    correlations: dict[str, JsonValue]
    correlations_by_era: list[dict[str, JsonValue]]
    sum_rule: dict[str, JsonValue]
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
        raise CarryEngineError(f"panel {spec.id} names unknown arms {sorted(missing)}")
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

    financing: dict[str, JsonValue] = {}
    if full:
        sensitivity = _mapping(
            _at(parameters, "financing_sensitivity", where="parameters"), where="financing"
        )
        grid = _numbers(_at(sensitivity, "equity_basis_points", where="financing"), where="eq")
        per_point: dict[str, dict[str, list[float]]] = {}
        for point in grid:
            shifted = FinancingRates(equity=point, treasury=0.0, gold=0.0, tips=0.0)
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
        ordering: list[list[str]] = []
        for i in range(len(grid)):
            ranked = sorted(
                (n for n in names if "reference" in per_point.get(n, {})),
                key=lambda n: -per_point[n]["reference"][i],
            )
            ordering.append(ranked)
        financing["equity"] = {
            "grid_basis_points": list(grid),
            "gaps_pp_yr": {
                n: {c: [_round(v) for v in vs] for c, vs in by_control.items()}
                for n, by_control in per_point.items()
            },
            "ordering_against_reference_by_point": ordering,
            "ordering_against_reference_stable": all(o == ordering[0] for o in ordering),
        }
        for name in names:
            for control, comparison in comparisons[name].items():
                values = per_point.get(name, {}).get(control)
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
        summary = drawdown_summary(np.cumprod(1.0 + total))
        excess_std = _volatility(item.path.excess)
        terminal = contribution_terminal_wealth(total, contribution=contribution)
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
            "terminal_wealth_with_contributions": _round(terminal, 3),
            "terminal_wealth_ratio_vs_cheap": _round(terminal / cheap_terminal, 4),
            "terminal_wealth_ratio_vs_reference": (
                None if reference_terminal is None else _round(terminal / reference_terminal, 4)
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
                "cheap_cumulative_pct": _round(c.cumulative_return * 100.0, 2),
                "offset_vs_cheap_pp": _round(
                    (a.cumulative_return - c.cumulative_return) * 100.0, 2
                ),
            }
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
        control_rows: dict[str, JsonValue] = {}
        for control, control_path in item.controls.items():
            control_summary = drawdown_summary(np.cumprod(1.0 + control_path.total))
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

    # Correlations: the premise of the stacking argument, measured.
    leg_arrays = {leg: panel.column(leg) for leg in LEGS if leg in panel.series}
    correlations = correlation_table(leg_arrays, equity=equity_leg, tail=tail)
    by_era: list[dict[str, JsonValue]] = []
    for era_name, start, end in windows:
        keep = _slice(panel.periods, start, end)
        if keep.size < 2 * MONTHS_PER_YEAR:
            continue
        sub = {leg: values[keep] for leg, values in leg_arrays.items()}
        entry_era = correlation_table(sub, equity=equity_leg[keep], tail=tail)
        entry_era["era"] = era_name
        entry_era["window"] = f"{start}..{end}"
        by_era.append(entry_era)

    sum_rule: dict[str, JsonValue] = {}
    needed = ("trend30_carry30", "base_trend30", "carry30_no_trend")
    if all(n in comparisons and "cheap" in comparisons[n] for n in needed):
        three: list[float] = []
        for n in needed:
            g = comparisons[n]["cheap"].gap
            three.append(g.gap_pp_yr if g is not None else 0.0)
        sum_rule = {
            "gap_both_vs_cheap_pp_yr": _round(three[0]),
            "gap_trend_only_vs_cheap_pp_yr": _round(three[1]),
            "gap_carry_only_vs_cheap_pp_yr": _round(three[2]),
            "residual_pp_yr": _round(sum_rule_residual(three[0], three[1], three[2])),
            "note": (
                "Zero up to rebalancing drift and the extra 3 bp core displaced if the "
                "overlay adds as a sum; the residual is descriptive."
            ),
        }

    return PanelResult(
        spec=spec,
        panel=panel,
        arms=simulated,
        comparisons=comparisons,
        descriptives=descriptives,
        correlations=correlations,
        correlations_by_era=by_era,
        sum_rule=sum_rule,
        financing=financing,
        families=families,
    )


def _component_table(legs: LegLibrary, panel: BasisPanel, *, tail: float) -> dict[str, JsonValue]:
    """Each per-asset-class carry column against the trend leg and equity, unscaled."""
    out: dict[str, JsonValue] = {}
    trend = panel.column("trend")
    equity = panel.column("equity")
    for name, series in legs.carry_components.items():
        keep = [i for i, p in enumerate(panel.periods) if p in series]
        if len(keep) < 3 * MONTHS_PER_YEAR:
            out[name] = {"months": len(keep)}
            continue
        idx = np.asarray(keep, dtype=np.intp)
        values = np.array([series[panel.periods[i]] for i in keep], dtype=np.float64)
        table = correlation_table(
            {"equity": equity[idx], "trend": trend[idx], "component": values},
            equity=equity[idx],
            tail=tail,
        )
        legs_json = table["legs"]
        assert isinstance(legs_json, Mapping)
        component = legs_json["component"]
        assert isinstance(component, Mapping)
        out[name] = {
            "months": len(keep),
            "window": f"{panel.periods[keep[0]]}..{panel.periods[keep[-1]]}",
            "correlation_full": table["correlation_full"],
            "correlation_worst_decile_of_equity": table["correlation_worst_decile_of_equity"],
            "mean_pp_yr_unscaled": component["full_pp_yr"],
            "volatility_pct_unscaled": component["volatility_pct"],
        }
    return out


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
        "carry_source": result.spec.carry_source,
        "window": f"{result.panel.periods[0]}..{result.panel.periods[-1]}",
        "months": result.panel.months,
        "panel_findings": list(result.panel.findings),
        "arms": arms_json,
        "correlations": result.correlations,
        "correlations_by_era": list(result.correlations_by_era),
        "sum_rule": result.sum_rule,
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
        raise CarryEngineError(f"expected a mapping, got {type(value).__name__}")
    return value


def _seq(value: JsonValue) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise CarryEngineError(f"expected a list, got {type(value).__name__}")
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


def _arm_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Arms: notional, growth, drawdown (descriptive)\n",
        "| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % "
        "| Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: "
        "| ---: | ---: |",
    ]
    for name, item in result.arms.items():
        d = result.descriptives[name]
        n = item.notional
        lines.append(
            f"| `{name}` | {n.gross:.3f} | {n.equity:.3f} | {n.trend:.3f} | {n.carry:.3f} | "
            f"{n.cash:.3f} | {d['arithmetic_mean_pp_yr']} | {d['growth_log_pp_yr']} | "
            f"{d['volatility_pct']} | {d['sharpe']} | {d['max_drawdown_pct']} | "
            f"{d['time_under_water_months']} | {d['terminal_wealth_ratio_vs_reference']} | "
            f"{d['terminal_wealth_ratio_vs_cheap']} |"
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


def _era_gap_table(result: PanelResult) -> list[str]:
    eras: list[str] = []
    for by_control in result.comparisons.values():
        for comparison in by_control.values():
            if comparison.era_gaps:
                eras = list(comparison.era_gaps)
                break
        if eras:
            break
    lines = [
        "\n### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)\n",
        "| arm | " + " | ".join(eras) + " |",
        "| --- | " + " | ".join("---:" for _ in eras) + " |",
    ]
    for name in result.arms:
        c = result.comparisons[name].get("reference")
        if c is None:
            c = result.comparisons[name].get("cheap")
        assert c is not None
        cells = [_fmt(c.era_gaps.get(e)) for e in eras]
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    return lines


def _crisis_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Crisis behaviour against the reference arm (descriptive)\n",
        "| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | "
        "deflationary episodes mean pp | inflation episodes mean pp |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in result.arms:
        d = result.descriptives[name]
        wd = d.get("worst_decile_offset_vs_reference")
        cv = d.get("convexity_vs_reference")
        kinds = _map(d["episode_type_mean_offset_vs_reference_pp"])
        wd_text = (
            f"{wd['offset_mean_pp_month']} ({wd['offset_hit_rate']})"
            if isinstance(wd, Mapping)
            else "--"
        )
        cv_text = f"{cv['kappa']} ({cv['kappa_t']})" if isinstance(cv, Mapping) else "--"

        def kind_cell(value: JsonValue) -> str:
            if not isinstance(value, Mapping):
                return "--"
            return f"{value['mean_pp']} ({value['episodes']} ep.)"

        lines.append(
            f"| `{name}` | {wd_text} | {cv_text} | "
            f"{kind_cell(kinds.get('deflationary_or_growth'))} | "
            f"{kind_cell(kinds.get('inflation_or_rate'))} |"
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


def _correlation_lines(table: Mapping[str, JsonValue], *, title: str) -> list[str]:
    full = _map(table["correlation_full"])
    worst = _map(table["correlation_worst_decile_of_equity"])
    legs = _map(table["legs"])
    lines = [
        f"\n### {title}: {table['months']} months, worst decile = "
        f"{table['worst_decile_months']} months (descriptive)\n",
        "| pair | full sample | worst decile of equity months |",
        "| --- | ---: | ---: |",
    ]
    for pair in full:
        lines.append(f"| {pair} | {full[pair]} | {worst.get(pair)} |")
    lines.append("")
    lines.append(
        "| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for leg, raw in legs.items():
        m = _map(raw)
        lines.append(
            f"| {leg} | {m['full_pp_yr']} | {m['volatility_pct']} | "
            f"{m['worst_decile_pp_month']} | {m['worst_decile_hit_rate']} |"
        )
    return lines


def _era_correlation_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Correlations and leg means by era (descriptive)\n",
        "| era | window | months | carry-trend | carry-equity | trend-equity | "
        "carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | "
        "trend pp/yr | equity pp/yr |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for era in result.correlations_by_era:
        full = _map(era["correlation_full"])
        worst = _map(era["correlation_worst_decile_of_equity"])
        legs = _map(era["legs"])
        means = {
            leg: (_map(legs[leg])["full_pp_yr"] if leg in legs else "--")
            for leg in ("carry", "trend", "equity")
        }
        lines.append(
            f"| {era['era']} | {era['window']} | {era['months']} | {full.get('trend_carry')} | "
            f"{full.get('equity_carry')} | {full.get('equity_trend')} | "
            f"{worst.get('trend_carry')} | {worst.get('equity_carry')} | {means['carry']} | "
            f"{means['trend']} | {means['equity']} |"
        )
    return lines


def _financing_table(result: PanelResult) -> list[str]:
    lines = [
        "\n### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), "
        "then against the cheap control\n"
    ]
    for attribute, raw_block in result.financing.items():
        block = _map(raw_block)
        grid = [str(int(_as_float(x) or 0.0)) for x in _seq(block["grid_basis_points"])]
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


def render_tables(
    results: Sequence[PanelResult],
    *,
    header: Sequence[str],
    components: Mapping[str, JsonValue],
) -> str:
    lines: list[str] = list(header)
    for result in results:
        lines.append(
            f"\n## Panel `{result.spec.id}` ({result.spec.role}): "
            f"{result.panel.periods[0]}..{result.panel.periods[-1]}, {result.panel.months} "
            f"months, trend `{result.spec.trend_source}`, carry `{result.spec.carry_source}`\n"
        )
        lines.append(result.spec.note.strip())
        lines.extend(_arm_table(result))
        lines.extend(_gap_table(result))
        lines.extend(_era_gap_table(result))
        lines.extend(_correlation_lines(result.correlations, title="Leg correlations"))
        if result.correlations_by_era:
            lines.extend(_era_correlation_table(result))
        if result.sum_rule:
            s = result.sum_rule
            lines.append(
                f"\nSum rule against the cheap control: both {s['gap_both_vs_cheap_pp_yr']} = "
                f"trend {s['gap_trend_only_vs_cheap_pp_yr']} + carry "
                f"{s['gap_carry_only_vs_cheap_pp_yr']} + residual {s['residual_pp_yr']} pp/yr."
            )
        lines.extend(_crisis_table(result))
        lines.extend(_episode_table(result))
        if result.financing:
            lines.extend(_financing_table(result))
    if components:
        lines.append(
            "\n## Carry components on the primary panel: each per-asset-class carry column, "
            "unscaled, against the own trend book and equity (descriptive)\n"
        )
        lines.append(
            "| component | window | months | corr with trend | corr with equity | "
            "corr with trend (worst decile) | corr with equity (worst decile) | mean pp/yr | "
            "vol % |"
        )
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for name, raw in components.items():
            c = _map(raw)
            if "correlation_full" not in c:
                lines.append(f"| {name} | -- | {c['months']} | -- | -- | -- | -- | -- | -- |")
                continue
            full = _map(c["correlation_full"])
            worst = _map(c["correlation_worst_decile_of_equity"])
            lines.append(
                f"| {name} | {c['window']} | {c['months']} | {full.get('trend_component')} | "
                f"{full.get('equity_component')} | {worst.get('trend_component')} | "
                f"{worst.get('equity_component')} | {c['mean_pp_yr_unscaled']} | "
                f"{c['volatility_pct_unscaled']} |"
            )
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
    tail = _number(parameters, "tail_quantile", where="parameters")
    in_estimates = tuple(
        str(x)
        for x in _sequence(_at(parameters, "controls_in_estimates", where="parameters"), where="c")
    )

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
                full=spec.role in SCORED_ROLES,
            )
        )
    by_id = {r.spec.id: r for r in results}
    components: dict[str, JsonValue] = {}
    if "primary" in by_id:
        components = _component_table(legs, by_id["primary"].panel, tail=tail)

    # Hostile re-runs, read as differences against the primary panel's paired gaps.
    hostile: dict[str, JsonValue] = {}
    if "primary" in by_id:
        base = by_id["primary"]
        for result in results:
            if result.spec.role != "sensitivity":
                continue
            rows: dict[str, JsonValue] = {}
            for name in result.arms:
                entry: dict[str, JsonValue] = {}
                for control in ("cheap", "reference"):
                    a = result.comparisons[name].get(control)
                    b = base.comparisons[name].get(control)
                    if a is None or b is None or a.gap is None or b.gap is None:
                        continue
                    entry[f"gap_vs_{control}_pp_yr"] = _round(a.gap.gap_pp_yr)
                    entry[f"gap_vs_{control}_published_pp_yr"] = _round(b.gap.gap_pp_yr)
                    entry[f"change_vs_{control}_pp_yr"] = _round(a.gap.gap_pp_yr - b.gap.gap_pp_yr)
                    entry[f"status_vs_{control}"] = a.status
                entry["max_drawdown_pct"] = result.descriptives[name]["max_drawdown_pct"]
                rows[name] = entry
            hostile[result.spec.id] = {
                "carry_source": result.spec.carry_source,
                "window": f"{result.panel.periods[0]}..{result.panel.periods[-1]}",
                "arms": rows,
            }

    estimates: list[Estimate] = []
    resolved: list[str] = []
    carry_resolved: list[str] = []
    scored = 0
    for result in results:
        if result.spec.role not in SCORED_ROLES:
            continue
        for name, by_control in result.comparisons.items():
            for control, comparison in by_control.items():
                if comparison.gap is None or comparison.identical:
                    continue
                if comparison.status == "exploratory" and result.spec.role != "check":
                    resolved.append(f"{result.spec.id}:{name} vs {control}")
                    if (
                        control == "reference"
                        and arm_notional(arms[name].tickers, arms[name].weights, wrappers).carry
                        > 0.0
                    ):
                        carry_resolved.append(f"{result.spec.id}:{name} vs {control}")
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
                            "80% power, two-sided at 0.05, from this comparison's own paired "
                            "series."
                        ),
                        uncertainty_unavailable_reason=(
                            "a detection floor is a property of the design, not an estimate of "
                            "a quantity in the world, so it carries no interval"
                        ),
                    )
                )
    status = ResultStatus.EXPLORATORY if resolved else ResultStatus.UNRESOLVED

    primary_note = ""
    primary = by_id.get("primary")
    if primary is not None:
        c = primary.correlations
        full = _map(c["correlation_full"])
        worst = _map(c["correlation_worst_decile_of_equity"])
        stack10 = primary.comparisons.get("trend30_carrystack10", {}).get("reference")
        primary_note = (
            f" On the {primary.panel.months}-month primary panel carry-trend correlation is "
            f"{full.get('trend_carry')} (worst decile of equity months {worst.get('trend_carry')}) "
            f"and carry-equity is {full.get('equity_carry')} ({worst.get('equity_carry')})."
        )
        if stack10 is not None and stack10.gap is not None:
            primary_note += (
                f" The 10-point carry stack against the reference reads "
                f"{stack10.gap.gap_pp_yr:+.2f} pp/yr against a {stack10.gap.mde_pp_yr:.2f} floor "
                f"({stack10.status})."
            )
    scored_panels = len([r for r in results if r.spec.role in SCORED_ROLES])
    summary = (
        f"{scored} arm-against-control comparisons scored on {scored_panels} panels, on assumed "
        f"wrapper exposure vectors and a gross vendor carry series. {len(carry_resolved)} carry "
        "arm(s) separate from the reference arm by more than the design can resolve on a "
        f"scored panel; {len(resolved)} comparisons in total reach `exploratory`, most of them "
        "the trend reference against the cheap and volatility-matched controls, which is where "
        f"the whole-experiment status comes from.{primary_note} The correlation, drawdown, "
        "crisis-episode and sum-rule tables are descriptive and carry no significance claim."
    )
    freeze_note = (
        "WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS. The carry leg is AQR's "
        "'All Macro Carry' from the century-of-factor-premia workbook, a vendor reconstruction "
        "gross of trading costs and fees, three asset classes before 1974-02 and four after, "
        "scaled to 12.38% volatility by one full-window constant. The long-panel trend leg is "
        "this repository's own 4-asset book scaled the same way; the secondary panel's is AQR's "
        "TSMOM. The prediction was a bracket: `exploratory` at the gross series and full "
        "loading, `unresolved` under a 2 pp/yr haircut and a 0.681 loading. The whole-experiment "
        "status is inherited from the trend reference and says nothing about carry."
    )
    header = [
        "# Experiment 019: carry as a second financed engine",
        "",
        f"Run `{context.run_id}`; specification hash `{specification.spec_hash}`.",
        "",
        freeze_note,
        "",
        f"Trend-book volatility scalar {legs.trend_scalar:.4f} (realised "
        f"{legs.trend_realised_volatility_pct:.2f}% on {legs.primary_window[0]}.."
        f"{legs.primary_window[1]}, target 12.38%). Carry-leg volatility scalar "
        f"{legs.carry_scalar:.4f} (realised {legs.carry_realised_volatility_pct:.2f}% on the "
        "same window, target 12.38%).",
        "",
        "Gap cells read: point estimate [95% block-bootstrap interval] MDE at 80% power, "
        "years to distinguish, falsifier status. A control column marked `identical` is the "
        "arm itself. Descriptive tables carry no status by design.",
    ]
    tables = render_tables(results, header=header, components=components)

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in raw.provenance],
        "source_findings": list(raw.findings),
        "trend_book": {
            "scalar": round(legs.trend_scalar, 6),
            "realised_volatility_pct_on_primary_window": round(
                legs.trend_realised_volatility_pct, 4
            ),
        },
        "carry_leg": {
            "scalar": round(legs.carry_scalar, 6),
            "realised_volatility_pct_on_primary_window": round(
                legs.carry_realised_volatility_pct, 4
            ),
            "primary_window": list(legs.primary_window),
            "note": (
                "One constant applied to every month; Sharpe-preserving; a look-ahead on "
                "magnitude only. Every carry gap scales linearly in the carry weight."
            ),
        },
        "financing_rates_basis_points": {"equity": rates.equity},
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
        "carry_components_primary": components,
        "hostile_reruns": hostile,
        "resolved_comparisons": resolved,
        "carry_arms_resolved_against_reference": carry_resolved,
        "markdown_tables": tables,
        "what_this_cannot_resolve": (
            "A comparison's floor is 0.285 pp/yr per point of tracking error on the primary "
            "panel and 0.437 on the secondary. A 10-point carry stack is measured against a "
            "floor of about 0.35 pp/yr (primary) and 0.54 (secondary); the 15/15 substitution "
            "against about 0.75 and 1.15."
        ),
    }
    caveats = (
        "Wrappers are assumed exposure vectors. This ranks constructions and cannot rank funds.",
        "The carry leg is a vendor reconstruction gross of every cost; the haircut panels are "
        "the only cost evidence and are assumptions.",
        "The carry composite holds three asset classes before 1974-02 and four after.",
        "The own 4-asset trend book is scaled by one full-window constant and charged no "
        "trading cost; AQR's TSMOM is gross of the vendor's trading costs by omission.",
        "Correlation, drawdown, worst-decile, episode and sum-rule figures describe one "
        "realised history and carry no significance claim.",
        "The whole-experiment status is inherited from the trend reference.",
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
        prog="python -m portfolio_edge.experiments.exp_019_carry_engine",
        description="Hold a multi-asset carry wrapper beside the trend wrapper and score it.",
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
