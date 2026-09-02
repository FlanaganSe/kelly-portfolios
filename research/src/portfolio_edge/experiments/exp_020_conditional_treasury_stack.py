"""Experiment 020: a bond-regime-conditioned Treasury stack.

What this is
------------
Experiment 018 held a financed 20-point Treasury leg on top of the reference
construction (70% equity core + 30% RSST-like wrapper) and found it
``unresolved`` on 1157 months, with its whole contribution inside the 1981-2020
bond bull market and 576 consecutive months behind the reference before it.
This module switches the same leg on only when the trailing bond-equity
correlation, computed through month t-1, is below a threshold, and scores the
result against the reference and against the unconditional stack on the full
window AND on the months outside 1981-10..2020-07.

What this is NOT
----------------
**It does not score funds.** Every wrapper is an assumed exposure vector.

**It does not search.** Four rules on one signal are declared in the frozen
specification, with one predeclared primary; the artifact reports the
effective number of trials the four imply.

**Its bond leg is a ~20-year bond whose history contains the bull market**, and
the regret table is arithmetic on stated inputs, not a measurement.

Run it::

    uv run python -m portfolio_edge.experiments.exp_020_conditional_treasury_stack --view-results
"""

from __future__ import annotations

import argparse
import dataclasses
import itertools
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import aqr, french, goyal_welch
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MONTHS_PER_YEAR,
    BasisPanel,
    PortfolioPath,
    _at,
    _mapping,
    _number,
    _numbers,
    _sequence,
    _text,
    annualised_log_growth,
    minimum_detectable_effect,
    workspace_root,
    years_to_distinguish,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    Arm,
    DefensiveEnginesError,
    FinancingRates,
    Notional,
    Wrapper,
    _column,
    _cost_settings,
    _pins,
    _require_cached,
    arm_notional,
    build_trend_book,
    contribution_terminal_wealth,
    read_arms,
    read_episodes,
    read_rates,
    read_wrappers,
    simulate_arm,
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
from portfolio_edge.inference.deflated_sharpe import (
    deflated_sharpe_ratio,
    effective_number_of_trials,
    mean_off_diagonal_correlation,
    trial_dispersion_from_sharpes,
)
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.inference.multiple_testing import benjamini_hochberg
from portfolio_edge.studies.stress_dependence import episode_returns, tail_dependence
from portfolio_edge.studies.time_series_momentum import TimeSeriesMomentumSpec

FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]
MonthSeries = dict[str, float]

ENTRY_POINT: Final = "exp_020_conditional_treasury_stack"

#: The two windows the falsifier scores; every other window is reported only.
FULL_WINDOW: Final = "full"
COMPLEMENT_WINDOW: Final = "complement_of_bond_bull"
BULL_ERA: Final = "bond_bull_market"

#: Normal quantile for the 95% HAC interval.
Z_95: Final = 1.959964

__all__ = [
    "ENTRY_POINT",
    "ConditionalStackError",
    "RuleSpec",
    "build_registry",
    "default_specification_path",
    "main",
    "read_rules",
    "regret_gap_pp_yr",
    "rule_state",
    "run",
    "switch_cost_series",
    "trailing_correlation",
    "window_gap",
]


class ConditionalStackError(Exception):
    """The experiment refused to run, or a source did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_020_conditional_treasury_stack.yaml"


# --------------------------------------------------------------------------- #
# Series
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RawSeries:
    """Every month-keyed series this experiment reads, plus provenance."""

    equity: MonthSeries
    cash: MonthSeries
    ltr: MonthSeries
    corpr: MonthSeries
    gw_rfree: MonthSeries
    commodity: MonthSeries
    provenance: tuple[Mapping[str, JsonValue], ...]
    findings: tuple[str, ...]


def load_series(specification: Specification) -> RawSeries:
    """Read the three pinned sources from the cache, hash-checked, never downloaded."""
    cache = RawCache()
    pins = _pins(specification)
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []

    def take(file_id: str, url: str) -> tuple[CacheEntry, dict[str, JsonValue]]:
        try:
            entry, record = _require_cached(cache, url, pins[file_id])
        except DefensiveEnginesError as error:
            raise ConditionalStackError(str(error)) from error
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

    ff3 = french.get_dataset("french_us_ff3")
    entry, record = take("french_us_ff3", ff3.url)
    market = french.parse(cache, entry, dataset=ff3).table("monthly")
    equity = _column(market.periods, market.column("Mkt-RF"))
    cash = _column(market.periods, market.column("RF"))
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
    table = aqr.parse(cache, entry, dataset=commodity_dataset).table
    commodity = _column(
        table.periods, table.column("Excess return of equal-weight commodities portfolio")
    )
    record["first_observation"], record["last_observation"] = min(commodity), max(commodity)

    return RawSeries(
        equity=equity,
        cash=cash,
        ltr=ltr,
        corpr=corpr,
        gw_rfree=gw_rfree,
        commodity=commodity,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Legs:
    """The legs as excess-of-cash month series, and the trend book's scaling."""

    equity: MonthSeries
    cash: MonthSeries
    treasury: MonthSeries
    trend: MonthSeries
    trend_scalar: float
    trend_book_realised_volatility_pct: float
    trend_book_window: tuple[str, str]


def build_legs(raw: RawSeries, specification: Specification) -> Legs:
    """exp_018's leg construction, restricted to what this experiment holds."""
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
    treasury = {p: raw.ltr[p] - raw.cash[p] for p in raw.ltr if p in raw.cash}
    primary = sorted(set(unscaled) & set(raw.equity) & set(raw.cash) & set(treasury))
    if len(primary) < 2 * MONTHS_PER_YEAR:
        raise ConditionalStackError("the panel window is shorter than two years")
    realised = float(np.std([unscaled[p] for p in primary], ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    scalar = target / realised
    return Legs(
        equity=raw.equity,
        cash=raw.cash,
        treasury=treasury,
        trend={p: v * scalar for p, v in unscaled.items()},
        trend_scalar=scalar,
        trend_book_realised_volatility_pct=realised * 100.0,
        trend_book_window=(primary[0], primary[-1]),
    )


def _contiguous(periods: Sequence[str], *, what: str) -> None:
    for earlier, later in itertools.pairwise(periods):
        if month_index(later) - month_index(earlier) != 1:
            raise ConditionalStackError(f"{what} has a gap between {earlier} and {later}")


def build_panel(legs: Legs) -> BasisPanel:
    """Intersect equity, cash, treasury and trend: the exp_018 primary panel."""
    common = set(legs.cash) & set(legs.equity) & set(legs.treasury) & set(legs.trend)
    periods = sorted(common)
    if len(periods) < 3 * MONTHS_PER_YEAR:
        raise ConditionalStackError(f"the panel holds {len(periods)} months")
    _contiguous(periods, what="the panel")
    return BasisPanel(
        periods=tuple(periods),
        series={
            "equity": np.array([legs.equity[p] for p in periods], dtype=np.float64),
            "treasury": np.array([legs.treasury[p] for p in periods], dtype=np.float64),
            "trend": np.array([legs.trend[p] for p in periods], dtype=np.float64),
        },
        cash=np.array([legs.cash[p] for p in periods], dtype=np.float64),
        provenance=(),
        findings=(f"panel: {len(periods)} months, {periods[0]}..{periods[-1]}",),
    )


# --------------------------------------------------------------------------- #
# The signal and the rules
# --------------------------------------------------------------------------- #


def trailing_correlation(x: FloatArray, y: FloatArray, window: int) -> FloatArray:
    """``out[t] = corr(x[t-window:t], y[t-window:t])``: the months before t only.

    ``out[t]`` is what a reader of the two series knows at the end of month
    ``t-1`` and is the signal applied to month ``t``. The first ``window``
    entries are NaN.
    """
    if x.shape != y.shape or x.ndim != 1:
        raise ConditionalStackError("the two signal series must be one-dimensional and aligned")
    if window < 3:
        raise ConditionalStackError("a correlation window needs at least three months")
    n = x.size
    out = np.full(n, np.nan, dtype=np.float64)
    for t in range(window, n):
        a = x[t - window : t]
        b = y[t - window : t]
        sa, sb = float(np.std(a, ddof=1)), float(np.std(b, ddof=1))
        if sa > 0.0 and sb > 0.0:
            out[t] = float(np.corrcoef(a, b)[0, 1])
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class RuleSpec:
    name: str
    rule: str
    window_months: int
    threshold: float | None
    median_window_months: int | None
    note: str


def read_rules(specification: Specification) -> tuple[dict[str, RuleSpec], str, float, str, str]:
    """The conditioned arms, the primary arm's name, the stack size and its wrappers."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(
        _at(parameters, "conditioned_arms", where="parameters"), where="conditioned_arms"
    )
    points = _number(block, "stack_points", where="conditioned_arms")
    stack_wrapper = _text(block, "stack_wrapper", where="conditioned_arms")
    funded_from = _text(block, "funded_from", where="conditioned_arms")
    primary = _text(block, "primary", where="conditioned_arms")
    arms = _mapping(_at(block, "arms", where="conditioned_arms"), where="conditioned_arms.arms")
    out: dict[str, RuleSpec] = {}
    for name in arms:
        entry = _mapping(arms[name], where=f"conditioned_arms.arms.{name}")
        rule = _text(entry, "rule", where=name)
        if rule not in {"threshold", "trailing_median"}:
            raise ConditionalStackError(f"{name}: unknown rule {rule!r}")
        threshold = _number(entry, "threshold", where=name) if rule == "threshold" else None
        median = (
            int(_number(entry, "median_window_months", where=name))
            if rule == "trailing_median"
            else None
        )
        out[name] = RuleSpec(
            name=name,
            rule=rule,
            window_months=int(_number(entry, "window_months", where=name)),
            threshold=threshold,
            median_window_months=median,
            note=str(entry.get("note") or ""),
        )
    if primary not in out:
        raise ConditionalStackError(f"primary arm {primary!r} is not a declared arm")
    return out, primary, points, stack_wrapper, funded_from


def rule_state(signal: FloatArray, rule: RuleSpec) -> FloatArray:
    """1.0 when the stack is on, 0.0 when off, NaN where the rule is undefined."""
    n = signal.size
    state = np.full(n, np.nan, dtype=np.float64)
    if rule.rule == "threshold":
        assert rule.threshold is not None
        finite = np.isfinite(signal)
        state[finite] = (signal[finite] < rule.threshold).astype(np.float64)
        return state
    assert rule.median_window_months is not None
    m = rule.median_window_months
    for t in range(n):
        if t + 1 < m:
            continue
        values = signal[t + 1 - m : t + 1]
        if np.all(np.isfinite(values)):
            state[t] = 1.0 if signal[t] < float(np.median(values)) else 0.0
    return state


@dataclass(frozen=True, slots=True, kw_only=True)
class SignalHistory:
    """Equity and Treasury excess returns on their longest common contiguous history."""

    periods: tuple[str, ...]
    equity: FloatArray
    treasury: FloatArray

    def signal(self, window: int) -> dict[str, float]:
        values = trailing_correlation(self.equity, self.treasury, window)
        return {p: float(v) for p, v in zip(self.periods, values, strict=True)}


def build_signal_history(legs: Legs) -> SignalHistory:
    periods = sorted(set(legs.equity) & set(legs.treasury))
    _contiguous(periods, what="the signal history")
    return SignalHistory(
        periods=tuple(periods),
        equity=np.array([legs.equity[p] for p in periods], dtype=np.float64),
        treasury=np.array([legs.treasury[p] for p in periods], dtype=np.float64),
    )


def state_on_panel(history: SignalHistory, panel: BasisPanel, rule: RuleSpec) -> FloatArray:
    """The rule's state for every panel month, NaN before the signal exists."""
    signal_by_month = history.signal(rule.window_months)
    signal = np.array([signal_by_month.get(p, math.nan) for p in history.periods], dtype=np.float64)
    state = rule_state(signal, rule)
    by_month = dict(zip(history.periods, state, strict=True))
    return np.array([by_month.get(p, math.nan) for p in panel.periods], dtype=np.float64)


def switch_cost_series(state: FloatArray, *, one_way_bp: float, points: float) -> FloatArray:
    """Cost of portfolio value in each month the state changes: ``2 * points * one_way``.

    A switch sells ``points`` of one holding and buys ``points`` of another, so
    both legs pay the one-way cost. The first month pays nothing: every arm
    starts from a common portfolio.
    """
    cost = np.zeros(state.size, dtype=np.float64)
    for t in range(1, state.size):
        if state[t] != state[t - 1]:
            cost[t] = 2.0 * points * one_way_bp / 10_000.0
    return cost


def _spells(state: FloatArray) -> list[tuple[int, int, int]]:
    """``(start, end, value)`` runs of a 0/1 series."""
    out: list[tuple[int, int, int]] = []
    start = 0
    for t in range(1, state.size + 1):
        if t == state.size or state[t] != state[start]:
            out.append((start, t - 1, int(state[start])))
            start = t
    return out


# --------------------------------------------------------------------------- #
# Simulation
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class ArmRun:
    """One arm on the panel, scored from ``first``; controls aligned to the same months."""

    name: str
    role: str
    first: int
    periods: tuple[str, ...]
    total: FloatArray
    excess: FloatArray
    state: FloatArray
    switches: int
    notional_on: Notional
    notional_off: Notional
    controls: dict[str, FloatArray]
    control_definition: dict[str, str]
    weighted_fee_bp: float
    annual_turnover: float


def _slice_path(path: PortfolioPath, first: int) -> tuple[FloatArray, FloatArray]:
    return path.total[first:], path.excess[first:]


def _volatility(values: FloatArray) -> float:
    return float(np.std(values, ddof=1))


def simulate_all(
    panel: BasisPanel,
    *,
    specification: Specification,
    wrappers: Mapping[str, Wrapper],
    arms: Mapping[str, Arm],
    rules: Mapping[str, RuleSpec],
    states: Mapping[str, FloatArray],
    rates: FinancingRates,
    switching_cost_bp: float,
    points: float,
    stack_wrapper: str,
    funded_from: str,
    reference: str,
    unconditional: str,
) -> dict[str, ArmRun]:
    """Every fixed arm, every conditioned arm, and every control, on one panel."""
    costs = _cost_settings(specification, rates)
    n = panel.months
    fixed_paths: dict[str, PortfolioPath] = {}
    for name, arm in arms.items():
        fixed_paths[name] = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=arm.tickers,
            targets=np.asarray(arm.weights, dtype=np.float64),
        )
    cheap = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.0]))
    ref_arm = arms[reference]
    ref_tickers = list(ref_arm.tickers)
    if funded_from not in ref_tickers:
        raise ConditionalStackError(f"{funded_from} is not held by the reference arm")
    ref_weights = dict(zip(ref_arm.tickers, ref_arm.weights, strict=True))
    if ref_weights[funded_from] < points:
        raise ConditionalStackError("the stack is funded from more capital than the core holds")
    tickers = (*ref_tickers, stack_wrapper)

    out: dict[str, ArmRun] = {}

    def attach_controls(run: ArmRun, *, gross_by_month: FloatArray, arm_total: FloatArray) -> None:
        first = run.first
        run.controls["cheap"] = cheap.total[first:]
        run.control_definition["cheap"] = "100% CORE"
        levered = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=("CORE",),
            targets=gross_by_month.reshape(-1, 1),
            first_month=first,
        )
        run.controls["leverage_matched"] = levered.total
        run.control_definition["leverage_matched"] = (
            "CORE levered each month to the arm's own gross notional, financed at the equity basis"
        )
        scale = _volatility(arm_total) / _volatility(cheap.total[first:])
        if scale <= 1.0:
            vm_tickers: tuple[str, ...] = ("CORE", "CASH")
            vm_targets = np.array([scale, 1.0 - scale])
        else:
            vm_tickers, vm_targets = ("CORE",), np.array([scale])
        matched = simulate_arm(
            panel, wrappers, rates, costs, tickers=vm_tickers, targets=vm_targets
        )
        run.controls["volatility_matched_expost"] = matched.total[first:]
        run.control_definition["volatility_matched_expost"] = (
            f"{scale:.4f} x CORE"
            + (f" + {1.0 - scale:.4f} x CASH" if scale <= 1.0 else ", financed at the equity basis")
            + " (full-window volatility match)"
        )
        if run.name != reference:
            run.controls["reference"] = fixed_paths[reference].total[first:]
            run.control_definition["reference"] = f"the {reference} arm"
        if run.name != unconditional:
            run.controls["unconditional_stack"] = fixed_paths[unconditional].total[first:]
            run.control_definition["unconditional_stack"] = f"the {unconditional} arm"

    for name, arm in arms.items():
        path = fixed_paths[name]
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        on = 1.0 if stack_wrapper in arm.tickers else 0.0
        state = np.full(n, on, dtype=np.float64)
        run = ArmRun(
            name=name,
            role=arm.role,
            first=0,
            periods=panel.periods,
            total=path.total,
            excess=path.excess,
            state=state,
            switches=0,
            notional_on=notional,
            notional_off=notional,
            controls={},
            control_definition={},
            weighted_fee_bp=path.weighted_fee_bp,
            annual_turnover=path.annual_turnover,
        )
        attach_controls(
            run, gross_by_month=np.full(n, notional.gross, dtype=np.float64), arm_total=path.total
        )
        out[name] = run

    off_weights = np.array([ref_weights.get(t, 0.0) for t in tickers], dtype=np.float64)
    on_weights = off_weights.copy()
    on_weights[tickers.index(funded_from)] -= points
    on_weights[tickers.index(stack_wrapper)] += points
    notional_off = arm_notional(tickers, off_weights.tolist(), wrappers)
    notional_on = arm_notional(tickers, on_weights.tolist(), wrappers)

    for name, rule in rules.items():
        state = states[name]
        finite = np.flatnonzero(np.isfinite(state))
        if finite.size < 2 * MONTHS_PER_YEAR:
            raise ConditionalStackError(f"{name}: fewer than two years of defined state")
        first = int(finite[0])
        if not np.all(np.isfinite(state[first:])):
            raise ConditionalStackError(f"{name}: the state is undefined after its first month")
        targets = np.tile(off_weights, (n, 1))
        for t in range(first, n):
            targets[t, :] = on_weights if state[t] > 0.5 else off_weights
        path = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=tickers,
            targets=targets,
            first_month=first,
        )
        scored_state = state[first:]
        switch = switch_cost_series(scored_state, one_way_bp=switching_cost_bp, points=points)
        total = path.total - switch
        excess = path.excess - switch
        gross = np.where(state > 0.5, notional_on.gross, notional_off.gross)
        run = ArmRun(
            name=name,
            role=f"conditioned: {rule.note}",
            first=first,
            periods=panel.periods[first:],
            total=total,
            excess=excess,
            state=scored_state,
            switches=int(np.count_nonzero(switch)),
            notional_on=notional_on,
            notional_off=notional_off,
            controls={},
            control_definition={},
            weighted_fee_bp=path.weighted_fee_bp,
            annual_turnover=path.annual_turnover,
        )
        attach_controls(run, gross_by_month=gross, arm_total=total)
        out[name] = run
    return out


# --------------------------------------------------------------------------- #
# Windows and statistics
# --------------------------------------------------------------------------- #


def _in_range(periods: Sequence[str], start: str, end: str) -> NDArray[np.bool_]:
    low, high = month_index(start), month_index(end)
    return np.array([low <= month_index(p) <= high for p in periods], dtype=np.bool_)


def window_indices(periods: Sequence[str], name: str, specification: Specification) -> IndexArray:
    """Indices into ``periods`` for a named window; the complement removes the bull era."""
    if name == FULL_WINDOW:
        return np.arange(len(periods), dtype=np.intp)
    eras = {era.name: era for era in specification.sample_policy.eras}
    if name not in eras:
        raise ConditionalStackError(f"unknown window {name!r}")
    keep = _in_range(periods, eras[name].start, eras[name].end)
    if name == COMPLEMENT_WINDOW:
        bull = eras[BULL_ERA]
        keep &= ~_in_range(periods, bull.start, bull.end)
    return np.flatnonzero(keep).astype(np.intp)


@dataclass(slots=True, kw_only=True)
class WindowGap:
    """One arm against one control on one window: gap, HAC interval, floor, log gap."""

    window: str
    months: int
    gap_pp_yr: float
    hac_se_pp_yr: float
    hac_interval: tuple[float, float]
    hac_p: float
    hac_lags: int
    mde_pp_yr: float
    years_to_distinguish: float
    tracking_error_pct: float
    log_growth_gap_pp_yr: float
    bootstrap_interval: tuple[float, float] | None = None
    bootstrap_p: float | None = None
    fraction_on: float | None = None
    switches: int | None = None
    adjusted_p: float | None = None
    band_range: tuple[float, float] | None = None
    status: str = "reported"
    clause: str = ""

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "window": self.window,
            "months": self.months,
            "gap_pp_yr": _round(self.gap_pp_yr),
            "hac_se_pp_yr": _round(self.hac_se_pp_yr),
            "hac_interval_pp_yr": [_round(self.hac_interval[0]), _round(self.hac_interval[1])],
            "hac_p_value": _round(self.hac_p, 5),
            "hac_lags": self.hac_lags,
            "mde_80pc_power_pp_yr": _round(self.mde_pp_yr),
            "years_to_distinguish_at_80pc_power": _round(self.years_to_distinguish, 1),
            "tracking_error_pct": _round(self.tracking_error_pct),
            "log_growth_gap_pp_yr": _round(self.log_growth_gap_pp_yr),
            "bootstrap_interval_pp_yr": (
                None
                if self.bootstrap_interval is None
                else [_round(self.bootstrap_interval[0]), _round(self.bootstrap_interval[1])]
            ),
            "bootstrap_p_value": None if self.bootstrap_p is None else _round(self.bootstrap_p, 5),
            "fraction_on": None if self.fraction_on is None else _round(self.fraction_on, 3),
            "switches": self.switches,
            "benjamini_hochberg_adjusted_p": (
                None if self.adjusted_p is None else _round(self.adjusted_p, 5)
            ),
            "band_gap_range_pp_yr": (
                None
                if self.band_range is None
                else [_round(self.band_range[0]), _round(self.band_range[1])]
            ),
            "status": self.status,
            "falsifier_clause": self.clause,
        }


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _round(value: float, digits: int = 4) -> float | None:
    finite = _finite(value)
    # ``+ 0.0`` turns a rounded negative zero into a plain zero.
    return None if finite is None else round(finite, digits) + 0.0


def window_gap(
    arm_total: FloatArray,
    control_total: FloatArray,
    *,
    window: str,
    indices: IndexArray | None = None,
    bootstrap: IndexArray | None = None,
    confidence: float = 0.95,
) -> WindowGap:
    """Arithmetic gap with a Newey-West interval and floor; bootstrap when given."""
    if arm_total.shape != control_total.shape:
        raise ConditionalStackError("arm and control must cover the same months")
    a = arm_total if indices is None else arm_total[indices]
    c = control_total if indices is None else control_total[indices]
    d = a - c
    if d.size < 2:
        raise ConditionalStackError(f"window {window!r} holds {d.size} months")
    hac = hac_mean(d)
    scale = MONTHS_PER_YEAR * 100.0
    gap = hac.mean * scale
    se = hac.standard_error * scale
    # A rule that never switched on is identical to its control: no test, p = 1.
    p_value = hac.p_value if math.isfinite(hac.p_value) else 1.0
    out = WindowGap(
        window=window,
        months=int(d.size),
        gap_pp_yr=gap,
        hac_se_pp_yr=se,
        hac_interval=(gap - Z_95 * se, gap + Z_95 * se),
        hac_p=p_value,
        hac_lags=hac.n_lags,
        mde_pp_yr=minimum_detectable_effect(d),
        years_to_distinguish=years_to_distinguish(gap, d),
        tracking_error_pct=_volatility(d) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
        log_growth_gap_pp_yr=annualised_log_growth(a) - annualised_log_growth(c),
    )
    if bootstrap is not None:
        if bootstrap.shape[1] != d.size:
            raise ConditionalStackError("bootstrap indices do not match the window length")
        resampled = d[bootstrap].mean(axis=1) * scale
        tail = (1.0 - confidence) / 2.0
        low, high = np.quantile(resampled, [tail, 1.0 - tail])
        exceed = int(np.sum(np.abs(resampled - gap) >= abs(gap)))
        out.bootstrap_interval = (float(low), float(high))
        out.bootstrap_p = float((exceed + 1) / (resampled.size + 1))
    return out


def _apply_falsifier(gap: WindowGap, *, q: float) -> None:
    if gap.gap_pp_yr <= 0.0:
        gap.status, gap.clause = "rejected", "(a) gap at or below zero"
        return
    if abs(gap.gap_pp_yr) < gap.mde_pp_yr:
        gap.status, gap.clause = (
            "unresolved",
            f"(b) the gap {gap.gap_pp_yr:+.2f} pp/yr is inside this design's own "
            f"{gap.mde_pp_yr:.2f} pp/yr detection floor at 80% power",
        )
        return
    if gap.adjusted_p is not None and gap.adjusted_p > q:
        gap.status, gap.clause = (
            "unresolved",
            f"(c) Benjamini-Hochberg adjusted p = {gap.adjusted_p:.3f} exceeds q = {q:.2f}",
        )
        return
    if gap.band_range is not None and gap.band_range[0] <= 0.0:
        gap.status, gap.clause = (
            "unresolved",
            f"(d) the gap changes sign on the cost band, reaching {gap.band_range[0]:+.2f} pp/yr",
        )
        return
    gap.status, gap.clause = "exploratory", "(e) survived every clause"


# --------------------------------------------------------------------------- #
# Regret
# --------------------------------------------------------------------------- #


def regret_gap_pp_yr(
    *,
    points: float,
    term_premium_pp_yr: float,
    certain_cost_pp_yr: float,
    fraction_on: float,
    rho: float,
    sigma_bond: float,
    sigma_portfolio: float,
    switching_cost_pp_yr: float,
) -> float:
    """Expected annual log-growth gap of a financed leg held a fraction of the time.

    ``f * [w tp - cost - (w^2 sigma_b^2 + 2 w rho sigma_p sigma_b) / 2] - switching``,
    with premiums and costs in percentage points and volatilities as fractions.
    """
    carry = points * term_premium_pp_yr - certain_cost_pp_yr
    variance = (points**2 * sigma_bond**2 + 2.0 * points * rho * sigma_portfolio * sigma_bond) / 2.0
    return fraction_on * (carry - variance * 100.0) - switching_cost_pp_yr


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class ArmReport:
    run: ArmRun
    gaps: dict[str, dict[str, WindowGap]] = field(default_factory=dict)
    descriptive: dict[str, JsonValue] = field(default_factory=dict)


def _bond_regime(
    panel: BasisPanel, *, indices: IndexArray, state: FloatArray | None
) -> dict[str, JsonValue]:
    b = panel.column("treasury")[indices]
    e = panel.column("equity")[indices]
    row: dict[str, JsonValue] = {
        "months": int(indices.size),
        "bond_equity_correlation": _round(float(np.corrcoef(b, e)[0, 1]), 3)
        if indices.size > 2
        else None,
        "bond_excess_pp_yr": _round(float(np.mean(b)) * MONTHS_PER_YEAR * 100.0, 2),
        "bond_volatility_pct": _round(_volatility(b) * math.sqrt(MONTHS_PER_YEAR) * 100.0, 2)
        if indices.size > 2
        else None,
        "equity_excess_pp_yr": _round(float(np.mean(e)) * MONTHS_PER_YEAR * 100.0, 2),
    }
    if state is not None:
        s = state[indices]
        for label, mask in (("on", s > 0.5), ("off", s <= 0.5)):
            k = int(np.count_nonzero(mask))
            row[f"{label}_months"] = k
            row[f"{label}_bond_excess_pp_yr"] = (
                _round(float(np.mean(b[mask])) * MONTHS_PER_YEAR * 100.0, 2) if k else None
            )
            row[f"{label}_realised_correlation"] = (
                _round(float(np.corrcoef(b[mask], e[mask])[0, 1]), 3) if k > 2 else None
            )
        row["fraction_on"] = _round(float(np.mean(s)), 3)
    return row


def _scored_point_gaps(
    panel: BasisPanel,
    *,
    specification: Specification,
    wrappers: Mapping[str, Wrapper],
    arms: Mapping[str, Arm],
    rules: Mapping[str, RuleSpec],
    states: Mapping[str, FloatArray],
    rates: FinancingRates,
    switching_cost_bp: float,
    points: float,
    stack_wrapper: str,
    funded_from: str,
    reference: str,
    unconditional: str,
    scored_controls: Sequence[str],
    scored_windows: Sequence[str],
) -> dict[tuple[str, str, str], float]:
    runs = simulate_all(
        panel,
        specification=specification,
        wrappers=wrappers,
        arms=arms,
        rules=rules,
        states=states,
        rates=rates,
        switching_cost_bp=switching_cost_bp,
        points=points,
        stack_wrapper=stack_wrapper,
        funded_from=funded_from,
        reference=reference,
        unconditional=unconditional,
    )
    out: dict[tuple[str, str, str], float] = {}
    for name in rules:
        run = runs[name]
        for control in scored_controls:
            for window in scored_windows:
                keep = window_indices(run.periods, window, specification)
                if keep.size < 2:
                    continue
                d = run.total[keep] - run.controls[control][keep]
                out[name, control, window] = float(np.mean(d)) * MONTHS_PER_YEAR * 100.0
    return out


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    parameters = _mapping(specification.parameters, where="parameters")
    costs_block = _mapping(specification.cost_model, where="cost_model")
    raw = load_series(specification)
    legs = build_legs(raw, specification)
    panel = build_panel(legs)
    history = build_signal_history(legs)
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = read_rates(specification)
    rules, primary, points, stack_wrapper, funded_from = read_rules(specification)
    episodes = read_episodes(specification)
    reference = next(n for n, a in arms.items() if a.role.startswith("reference"))
    unconditional = next(n for n, a in arms.items() if a.role.startswith("unconditional"))
    switching_bp = _number(costs_block, "switching_cost_one_way_basis_points", where="cost_model")
    scored_controls = [
        str(x) for x in _sequence(_at(parameters, "scored_controls", where="p"), where="c")
    ]
    scored_windows = [
        str(x) for x in _sequence(_at(parameters, "scored_windows", where="p"), where="w")
    ]
    reported_windows = [
        str(x) for x in _sequence(_at(parameters, "reported_windows", where="p"), where="w")
    ]
    minimum_months = int(_number(parameters, "minimum_window_months", where="parameters"))
    contribution = _number(parameters, "contribution_per_month_of_starting_balance", where="p")
    tail = _number(parameters, "tail_quantile", where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")

    states = {name: state_on_panel(history, panel, rule) for name, rule in rules.items()}
    runs = simulate_all(
        panel,
        specification=specification,
        wrappers=wrappers,
        arms=arms,
        rules=rules,
        states=states,
        rates=rates,
        switching_cost_bp=switching_bp,
        points=points,
        stack_wrapper=stack_wrapper,
        funded_from=funded_from,
        reference=reference,
        unconditional=unconditional,
    )

    indices_by_length: dict[int, IndexArray] = {}

    def bootstrap(length: int) -> IndexArray:
        if length not in indices_by_length:
            indices_by_length[length] = stationary_bootstrap_indices(
                length, block, specification.inference.resamples, context.rng
            )
        return indices_by_length[length]

    # Gaps: every arm, every control, every reported window; bootstrap on the scored ones.
    reports: dict[str, ArmReport] = {}
    for name, arm_run in runs.items():
        report = ArmReport(run=arm_run)
        conditioned = name in rules
        for control, control_total in arm_run.controls.items():
            report.gaps[control] = {}
            for window in reported_windows:
                keep = window_indices(arm_run.periods, window, specification)
                if keep.size < minimum_months:
                    continue
                scored = control in scored_controls and window in scored_windows
                gap = window_gap(
                    arm_run.total,
                    control_total,
                    window=window,
                    indices=keep,
                    bootstrap=bootstrap(int(keep.size)) if scored else None,
                    confidence=specification.inference.confidence_level,
                )
                if conditioned:
                    gap.fraction_on = float(np.mean(arm_run.state[keep]))
                    gap.switches = int(np.count_nonzero(np.diff(arm_run.state[keep])))
                report.gaps[control][window] = gap
        reports[name] = report

    # Benjamini-Hochberg within each (control, window) family across the four arms.
    families: dict[str, list[str]] = {}
    for control in scored_controls:
        for window in scored_windows:
            members = [n for n in rules if window in reports[n].gaps.get(control, {})]
            if not members:
                continue
            p_values = [reports[n].gaps[control][window].hac_p for n in members]
            adjusted = benjamini_hochberg(p_values, alpha=q)
            for n, value in zip(members, adjusted.adjusted_p_values, strict=True):
                reports[n].gaps[control][window].adjusted_p = float(value)
            families[f"{control}:{window}"] = members

    # Cost bands: switching cost and Treasury basis, point gaps only.
    sensitivity = _mapping(
        _at(parameters, "financing_sensitivity", where="parameters"), where="sensitivity"
    )
    band_values: dict[tuple[str, str, str], list[float]] = {}
    band_records: dict[str, JsonValue] = {}
    for key, label in (
        ("switching_cost_basis_points", "switching_cost"),
        ("treasury_basis_points", "treasury_basis"),
    ):
        grid = _numbers(_at(sensitivity, key, where="sensitivity"), where=key)
        rows: dict[str, JsonValue] = {}
        for point in grid:
            gaps = _scored_point_gaps(
                panel,
                specification=specification,
                wrappers=wrappers,
                arms=arms,
                rules=rules,
                states=states,
                rates=(
                    rates
                    if label == "switching_cost"
                    else dataclasses.replace(rates, treasury=point)
                ),
                switching_cost_bp=point if label == "switching_cost" else switching_bp,
                points=points,
                stack_wrapper=stack_wrapper,
                funded_from=funded_from,
                reference=reference,
                unconditional=unconditional,
                scored_controls=scored_controls,
                scored_windows=scored_windows,
            )
            for cell, value in gaps.items():
                band_values.setdefault(cell, []).append(value)
            rows[str(int(point))] = {
                f"{n}|{c}|{w}": _round(v) for (n, c, w), v in sorted(gaps.items())
            }
        band_records[label] = {"grid_basis_points": list(grid), "gap_pp_yr_by_point": rows}
    for (name, control, window), values in band_values.items():
        banded = reports[name].gaps.get(control, {}).get(window)
        if banded is not None:
            banded.band_range = (min(values), max(values))

    for name in rules:
        for control in scored_controls:
            for window in scored_windows:
                judged = reports[name].gaps.get(control, {}).get(window)
                if judged is not None:
                    _apply_falsifier(judged, q=q)

    # Descriptives.
    episode_windows = {e.name: (e.start, e.end) for e in episodes}
    equity_leg = panel.column("equity")
    reference_run = runs[reference]
    unconditional_run = runs[unconditional]
    for name, report in reports.items():
        arm_run = report.run
        first = arm_run.first
        total = arm_run.total
        curve = np.cumprod(1.0 + total)
        dd = drawdown_summary(curve)
        excess_std = _volatility(arm_run.excess)
        ref_total = reference_run.total[first:]
        unc_total = unconditional_run.total[first:]
        terminal = contribution_terminal_wealth(total, contribution=contribution)
        row: dict[str, JsonValue] = {
            "first_scored_month": arm_run.periods[0],
            "months": int(total.size),
            "notional_on": arm_run.notional_on.to_json(),
            "notional_off": arm_run.notional_off.to_json(),
            "fraction_on": _round(float(np.mean(arm_run.state)), 3),
            "switches": arm_run.switches,
            "growth_log_pp_yr": _round(annualised_log_growth(total)),
            "arithmetic_mean_pp_yr": _round(float(np.mean(total)) * MONTHS_PER_YEAR * 100.0),
            "volatility_pct": _round(_volatility(total) * math.sqrt(MONTHS_PER_YEAR) * 100.0),
            "sharpe": _round(
                float(np.mean(arm_run.excess)) / excess_std * math.sqrt(MONTHS_PER_YEAR)
                if excess_std > 0.0
                else 0.0
            ),
            "max_drawdown_pct": _round(dd.max_drawdown * 100.0, 2),
            "time_under_water_months": dd.max_time_under_water,
            "weighted_fee_bp": _round(arm_run.weighted_fee_bp, 2),
            "annual_turnover_pct": _round(arm_run.annual_turnover * 100.0, 3),
            "terminal_wealth_ratio_vs_reference": _round(
                terminal / contribution_terminal_wealth(ref_total, contribution=contribution), 4
            ),
            "terminal_wealth_ratio_vs_unconditional": _round(
                terminal / contribution_terminal_wealth(unc_total, contribution=contribution), 4
            ),
            "reference_max_drawdown_pct_same_window": _round(
                drawdown_summary(np.cumprod(1.0 + ref_total)).max_drawdown * 100.0, 2
            ),
            "unconditional_max_drawdown_pct_same_window": _round(
                drawdown_summary(np.cumprod(1.0 + unc_total)).max_drawdown * 100.0, 2
            ),
        }
        if name in rules:
            spells = _spells(arm_run.state)
            on_spells = [(s, e) for s, e, v in spells if v == 1]
            off_spells = [(s, e) for s, e, v in spells if v == 0]
            row["on_spells"] = [
                {"start": arm_run.periods[s], "end": arm_run.periods[e], "months": e - s + 1}
                for s, e in on_spells
            ]
            row["mean_on_spell_months"] = (
                _round(float(np.mean([e - s + 1 for s, e in on_spells])), 1) if on_spells else None
            )
            row["longest_on_spell_months"] = (
                max(e - s + 1 for s, e in on_spells) if on_spells else 0
            )
            row["mean_off_spell_months"] = (
                _round(float(np.mean([e - s + 1 for s, e in off_spells])), 1)
                if off_spells
                else None
            )
            row["longest_off_spell_months"] = (
                max(e - s + 1 for s, e in off_spells) if off_spells else 0
            )
            # The mechanism: did the trailing correlation predict anything?
            regime: dict[str, JsonValue] = {}
            for window in reported_windows:
                keep = window_indices(arm_run.periods, window, specification)
                if keep.size >= minimum_months:
                    regime[window] = _bond_regime(panel, indices=keep + first, state=states[name])
            row["bond_regime_by_window"] = regime
        for label, other in (("vs_reference", ref_total), ("vs_unconditional", unc_total)):
            if _volatility(total - other) == 0.0:
                row[f"worst_decile_offset_{label}"] = None
                continue
            dependence = tail_dependence(equity_leg[first:], total - other, quantile=tail)
            row[f"worst_decile_offset_{label}"] = {
                "months": dependence.months_low,
                "offset_mean_pp_month": _round(dependence.mean_low * 100.0, 3),
                "offset_hit_rate": _round(dependence.hit_rate_low, 3),
                "offset_worst_pp_month": _round(dependence.worst_low * 100.0, 3),
            }
        arm_ep = episode_returns(arm_run.periods, total, windows=episode_windows)
        ref_ep = episode_returns(arm_run.periods, ref_total, windows=episode_windows)
        unc_ep = episode_returns(arm_run.periods, unc_total, windows=episode_windows)
        episode_rows: dict[str, JsonValue] = {}
        for i, episode in enumerate(episodes):
            a = arm_ep[i]
            if not a.covered:
                episode_rows[episode.name] = {"kind": episode.kind, "covered": False}
                continue
            mask = _in_range(arm_run.periods, episode.start, episode.end)
            episode_rows[episode.name] = {
                "kind": episode.kind,
                "covered": True,
                "partial": a.partial,
                "months": a.months,
                "arm_cumulative_pct": _round(a.cumulative_return * 100.0, 2),
                "reference_cumulative_pct": _round(ref_ep[i].cumulative_return * 100.0, 2),
                "offset_vs_reference_pp": _round(
                    (a.cumulative_return - ref_ep[i].cumulative_return) * 100.0, 2
                ),
                "offset_vs_unconditional_pp": _round(
                    (a.cumulative_return - unc_ep[i].cumulative_return) * 100.0, 2
                ),
                "fraction_on": _round(float(np.mean(arm_run.state[mask])), 3),
            }
        row["episodes"] = episode_rows
        report.descriptive = row

    # Effective trials across the four arms, and the primary arm's deflated Sharpe.
    latest_first = max(runs[n].first for n in rules)
    difference_columns: list[FloatArray] = []
    sharpes: list[float] = []
    for name in rules:
        arm_run = runs[name]
        offset = latest_first - arm_run.first
        d = arm_run.total[offset:] - arm_run.controls["reference"][offset:]
        difference_columns.append(d)
        sd = _volatility(d)
        sharpes.append(float(np.mean(d)) / sd if sd > 0.0 else 0.0)
    matrix = np.column_stack(difference_columns)
    live = [i for i in range(matrix.shape[1]) if _volatility(matrix[:, i]) > 0.0]
    rho_bar = (
        mean_off_diagonal_correlation(matrix[:, live], allow_rank_deficient=True)
        if len(live) > 1
        else 0.0
    )
    n_effective = effective_number_of_trials(len(rules), rho_bar)
    primary_index = list(rules).index(primary)
    primary_d = difference_columns[primary_index]
    dispersion = trial_dispersion_from_sharpes(sharpes)
    deflation: dict[str, JsonValue] = {
        "arms": list(rules),
        "common_months": int(matrix.shape[0]),
        "common_first_month": runs[primary].periods[latest_first - runs[primary].first],
        "mean_off_diagonal_correlation_of_paired_differences": _round(rho_bar, 3),
        "effective_number_of_trials": _round(n_effective, 2),
        "effective_trials_note": (
            "linear reading N = M (1 - rho) + rho, marked UNVERIFIED in inference/deflated_sharpe"
        ),
        "trial_sharpes_monthly": [_round(s, 4) for s in sharpes],
        "trial_dispersion": _round(dispersion, 4),
        "primary_arm": primary,
        "primary_observed_sharpe_monthly": _round(sharpes[primary_index], 4),
        "primary_observed_sharpe_annualised": _round(
            sharpes[primary_index] * math.sqrt(MONTHS_PER_YEAR), 4
        ),
        "deflated_sharpe_by_trial_count": {},
    }
    dsr_rows: dict[str, JsonValue] = {}
    skew = float(stats.skew(primary_d))
    kurt = float(stats.kurtosis(primary_d, fisher=False))
    for label, count in (
        ("effective", n_effective),
        ("declared_4", 4.0),
        ("100", 100.0),
    ):
        result = deflated_sharpe_ratio(
            sharpes[primary_index],
            trial_dispersion=dispersion,
            n_trials=count,
            n_observations=primary_d.size,
            skewness=skew,
            kurtosis=kurt,
        )
        dsr_rows[label] = {
            "n_trials": _round(count, 2),
            "sharpe_threshold_monthly": _round(result.sharpe_threshold, 4),
            "deflated_significance": _round(result.deflated_significance, 4),
        }
    deflation["deflated_sharpe_by_trial_count"] = dsr_rows

    # Regret: arithmetic on the declared grid and the run's realised inputs.
    regret_block = _mapping(_at(parameters, "regret", where="parameters"), where="regret")
    grid = _numbers(_at(regret_block, "term_premium_grid_pp_yr", where="regret"), where="tp")
    primary_run = runs[primary]
    primary_regime_full = _bond_regime(
        panel, indices=np.arange(primary_run.first, panel.months, dtype=np.intp), state=None
    )
    stack = wrappers[stack_wrapper]
    core = wrappers[funded_from]
    certain_cost_bp = points * (
        stack.fee_bp + sum(v * rates.for_leg(k) for k, v in stack.financed.items())
    ) - points * (core.fee_bp + sum(v * rates.for_leg(k) for k, v in core.financed.items()))
    certain_cost = certain_cost_bp / 100.0
    full_keep = window_indices(primary_run.periods, FULL_WINDOW, specification)
    on_mask = primary_run.state > 0.5
    bond = panel.column("treasury")[primary_run.first :]
    equity = equity_leg[primary_run.first :]
    rho_full = float(np.corrcoef(bond, equity)[0, 1])
    rho_on = float(np.corrcoef(bond[on_mask], equity[on_mask])[0, 1]) if on_mask.sum() > 2 else 0.0
    after = window_indices(primary_run.periods, "after_bond_bull", specification)
    rho_after = float(np.corrcoef(bond[after], equity[after])[0, 1]) if after.size > 2 else rho_full
    sigma_b = _volatility(bond) * math.sqrt(MONTHS_PER_YEAR)
    sigma_p = _volatility(reference_run.total[primary_run.first :]) * math.sqrt(MONTHS_PER_YEAR)
    fraction_on = float(np.mean(primary_run.state[full_keep]))
    years = full_keep.size / MONTHS_PER_YEAR
    switching_pp_yr = primary_run.switches * 2.0 * points * switching_bp / 10_000.0 * 100.0 / years
    regret_inputs: dict[str, JsonValue] = {
        "points": points,
        "certain_cost_pp_yr_while_on": _round(certain_cost, 4),
        "fraction_on_full_window": _round(fraction_on, 3),
        "switching_cost_pp_yr_realised": _round(switching_pp_yr, 4),
        "rho_full_window": _round(rho_full, 3),
        "rho_on_state_realised": _round(rho_on, 3),
        "rho_after_bond_bull": _round(rho_after, 3),
        "sigma_bond_pct": _round(sigma_b * 100.0, 2),
        "sigma_reference_pct": _round(sigma_p * 100.0, 2),
        "bond_excess_full_window_pp_yr": primary_regime_full["bond_excess_pp_yr"],
    }
    scenarios: dict[str, dict[str, float]] = {
        "persists": {"cond_f": 0.0, "cond_rho": rho_after, "unc_rho": rho_after},
        "reverts": {"cond_f": fraction_on, "cond_rho": rho_on, "unc_rho": rho_full},
    }
    cells: list[dict[str, JsonValue]] = []
    worst: dict[str, float] = {"conditioned": 0.0, "unconditional": 0.0, "neither": 0.0}
    for state_name, inputs in scenarios.items():
        for tp in grid:
            cond = regret_gap_pp_yr(
                points=points,
                term_premium_pp_yr=tp,
                certain_cost_pp_yr=certain_cost,
                fraction_on=inputs["cond_f"],
                rho=inputs["cond_rho"],
                sigma_bond=sigma_b,
                sigma_portfolio=sigma_p,
                switching_cost_pp_yr=switching_pp_yr if inputs["cond_f"] > 0.0 else 0.0,
            )
            unc = regret_gap_pp_yr(
                points=points,
                term_premium_pp_yr=tp,
                certain_cost_pp_yr=certain_cost,
                fraction_on=1.0,
                rho=inputs["unc_rho"],
                sigma_bond=sigma_b,
                sigma_portfolio=sigma_p,
                switching_cost_pp_yr=0.0,
            )
            cell_gaps = {"conditioned": cond, "unconditional": unc, "neither": 0.0}
            best = max(cell_gaps.values())
            regrets = {k: best - v for k, v in cell_gaps.items()}
            for k, v in regrets.items():
                worst[k] = max(worst[k], v)
            cells.append(
                {
                    "state": state_name,
                    "term_premium_pp_yr": tp,
                    "gap_bp_yr": {k: _round(v * 100.0, 1) for k, v in cell_gaps.items()},
                    "regret_bp_yr": {k: _round(v * 100.0, 1) for k, v in regrets.items()},
                }
            )
    minimax = min(worst, key=lambda k: worst[k])
    regret: dict[str, JsonValue] = {
        "inputs": regret_inputs,
        "cells": cells,
        "max_regret_bp_yr": {k: _round(v * 100.0, 1) for k, v in worst.items()},
        "minimax_action": minimax,
        "note": "Arithmetic on stated inputs; no interval, no status.",
    }

    # Estimates and the verdict.
    estimates: list[Estimate] = []
    resolved: list[str] = []
    for name in rules:
        for control in scored_controls:
            for window in scored_windows:
                scored_gap = reports[name].gaps.get(control, {}).get(window)
                if scored_gap is None:
                    continue
                gap = scored_gap
                label = f"{name} vs {control} on {window}"
                if gap.status == "exploratory":
                    resolved.append(label)
                estimates.append(
                    Estimate(
                        name=f"arithmetic_gap[{label}]",
                        value=gap.gap_pp_yr,
                        units="percentage points per year",
                        interval=gap.hac_interval,
                        interval_method=(
                            f"Newey-West HAC, {gap.hac_lags} lags, 95% normal interval; "
                            "block bootstrap interval in the diagnostics"
                        ),
                        cost_basis=CostBasis.NET_PESSIMISTIC,
                        n_obs=gap.months,
                        notes=(
                            f"{gap.status}: {gap.clause}. Tracking error "
                            f"{gap.tracking_error_pct:.2f}%; on {gap.fraction_on or 0.0:.0%} of "
                            f"months; {gap.switches} switches; log-growth gap "
                            f"{gap.log_growth_gap_pp_yr:+.2f}."
                        ),
                    )
                )
                estimates.append(
                    Estimate(
                        name=f"minimum_detectable_effect[{label}]",
                        value=gap.mde_pp_yr,
                        units="percentage points per year",
                        cost_basis=CostBasis.NOT_APPLICABLE,
                        n_obs=gap.months,
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

    primary_full = reports[primary].gaps["reference"][FULL_WINDOW]
    primary_comp = reports[primary].gaps["reference"].get(COMPLEMENT_WINDOW)
    unc_full = reports[unconditional].gaps["reference"][FULL_WINDOW]
    comp_text = (
        f" and {primary_comp.gap_pp_yr:+.2f} [{primary_comp.hac_interval[0]:+.2f}, "
        f"{primary_comp.hac_interval[1]:+.2f}] against a {primary_comp.mde_pp_yr:.2f} floor on "
        f"the {primary_comp.months} months outside the bond bull market"
        if primary_comp is not None
        else ""
    )
    summary = (
        f"{len(estimates) // 2} scored comparisons: four conditioned arms against the reference "
        f"and the unconditional stack on the full window and its complement. {len(resolved)} "
        f"separate from their control by more than the design can resolve. The primary arm "
        f"({primary}) reads {primary_full.gap_pp_yr:+.2f} [{primary_full.hac_interval[0]:+.2f}, "
        f"{primary_full.hac_interval[1]:+.2f}] pp/yr against the reference on "
        f"{primary_full.months} months against a {primary_full.mde_pp_yr:.2f} floor{comp_text}, "
        f"on {primary_full.fraction_on or 0.0:.0%} of months with {primary_full.switches} "
        f"switches; the unconditional stack reads {unc_full.gap_pp_yr:+.2f} on the same panel. "
        "Regret table: "
        f"minimax action across the term-premium grid is `{minimax}`."
    )
    freeze_note = (
        "WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS. The bond leg is a ~20-year "
        "bond whose history contains the 1981-2020 bull market. The signal is the trailing "
        "correlation of equity and Treasury excess returns through month t-1, applied to "
        "month t. Four rules on one signal were declared before the run with one primary; "
        "every mean gap was predicted `unresolved`. No TIPS series exists before 2003 in the "
        "panel and none was built. The regret table is arithmetic on stated inputs."
    )
    header = [
        "# Experiment 020: a bond-regime-conditioned Treasury stack",
        "",
        f"Run `{context.run_id}`; specification hash `{specification.spec_hash}`.",
        "",
        freeze_note,
        "",
        f"Panel {panel.periods[0]}..{panel.periods[-1]}, {panel.months} months. Trend-book "
        f"volatility scalar {legs.trend_scalar:.4f} (realised "
        f"{legs.trend_book_realised_volatility_pct:.2f}% on {legs.trend_book_window[0]}.."
        f"{legs.trend_book_window[1]}, target 12.38%). Switching cost {switching_bp:.0f} bp "
        f"one-way on each dollar moved; certain cost of the leg while on {certain_cost:.3f} pp/yr.",
        "",
        "Gap cells read: point estimate [95% Newey-West interval] MDE at 80% power, years to "
        "distinguish, status; scored cells also carry the block-bootstrap interval.",
    ]
    tables = render_tables(reports, rules=rules, header=header, deflation=deflation, regret=regret)

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in raw.provenance],
        "source_findings": list(raw.findings),
        "panel": {
            "window": f"{panel.periods[0]}..{panel.periods[-1]}",
            "months": panel.months,
            "signal_history": f"{history.periods[0]}..{history.periods[-1]}",
        },
        "trend_book": {
            "scalar": round(legs.trend_scalar, 6),
            "realised_volatility_pct_on_primary_window": round(
                legs.trend_book_realised_volatility_pct, 4
            ),
            "primary_window": list(legs.trend_book_window),
        },
        "financing_rates_basis_points": {
            "equity": rates.equity,
            "treasury": rates.treasury,
            "switching_one_way": switching_bp,
        },
        "rules": {
            n: {
                "rule": r.rule,
                "window_months": r.window_months,
                "threshold": r.threshold,
                "median_window_months": r.median_window_months,
                "note": r.note,
            }
            for n, r in rules.items()
        },
        "primary_arm": primary,
        "arms": [
            {
                "arm": name,
                "role": report.run.role,
                **report.descriptive,
                "gaps": {
                    control: {w: g.to_json() for w, g in by_window.items()}
                    for control, by_window in report.gaps.items()
                },
                "control_definitions": dict(report.run.control_definition),
            }
            for name, report in reports.items()
        ],
        "multiple_testing_families": families,
        "cost_bands": band_records,
        "deflation": deflation,
        "regret": regret,
        "resolved_comparisons": resolved,
        "tips_before_2003": (
            "The only real-yield series in this repository is FRED FII10 from 2003-01. No "
            "pre-2003 TIPS proxy exists in the panel and none was built: a modelled one would "
            "be realised inflation dressed as a bond, and the 1970-81 window it would be built "
            "for is the one where that substitution decides the answer."
        ),
        "markdown_tables": tables,
    }
    caveats = (
        "Wrappers are assumed exposure vectors. This ranks constructions and cannot rank funds.",
        "The bond leg (Goyal-Welch ltr) is a ~20-year bond and its window contains the "
        "1981-2020 bull market; read every gap beside the era and on/off tables.",
        "Four rules on one signal; the effective trial count is reported and marked unverified.",
        "The complement window joins two disjoint eras; the HAC and bootstrap treat the join "
        "as adjacent months.",
        "The regret table is arithmetic on stated inputs and carries no interval.",
        "No pre-2003 TIPS series exists in the panel and none was built.",
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
# Markdown tables
# --------------------------------------------------------------------------- #


def _cell(gap: WindowGap | None) -> str:
    if gap is None:
        return "n/a"
    years = (
        "inf" if not math.isfinite(gap.years_to_distinguish) else f"{gap.years_to_distinguish:.0f}y"
    )
    text = (
        f"{gap.gap_pp_yr:+.2f} [{gap.hac_interval[0]:+.2f}, {gap.hac_interval[1]:+.2f}] "
        f"MDE {gap.mde_pp_yr:.2f} {years} `{gap.status}`"
    )
    if gap.bootstrap_interval is not None:
        text += f" boot [{gap.bootstrap_interval[0]:+.2f}, {gap.bootstrap_interval[1]:+.2f}]"
    return text


def _map(value: JsonValue) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ConditionalStackError(f"expected a mapping, got {type(value).__name__}")
    return value


def _seq(value: JsonValue) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ConditionalStackError(f"expected a list, got {type(value).__name__}")
    return value


def _state_table(reports: Mapping[str, ArmReport]) -> list[str]:
    lines = [
        "\n### Arms: state, notional, growth, drawdown (descriptive)\n",
        "| arm | first month | months | on | switches | mean on-spell | longest off-spell | "
        "gross on/off | arith pp/yr | log growth | vol % | Sharpe | max DD % | ref max DD % | "
        "months under water | TW vs ref | TW vs unconditional |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: "
        "| ---: | ---: | ---: | ---: |",
    ]
    for name, report in reports.items():
        d = report.descriptive
        n_on, n_off = report.run.notional_on, report.run.notional_off
        lines.append(
            f"| `{name}` | {d['first_scored_month']} | {d['months']} | {d['fraction_on']} | "
            f"{d['switches']} | {d.get('mean_on_spell_months', '--')} | "
            f"{d.get('longest_off_spell_months', '--')} | {n_on.gross:.3f}/{n_off.gross:.3f} | "
            f"{d['arithmetic_mean_pp_yr']} | {d['growth_log_pp_yr']} | {d['volatility_pct']} | "
            f"{d['sharpe']} | {d['max_drawdown_pct']} | "
            f"{d['reference_max_drawdown_pct_same_window']} | {d['time_under_water_months']} | "
            f"{d['terminal_wealth_ratio_vs_reference']} | "
            f"{d['terminal_wealth_ratio_vs_unconditional']} |"
        )
    return lines


def _gap_tables(reports: Mapping[str, ArmReport], *, windows: Sequence[str]) -> list[str]:
    lines: list[str] = []
    for control in (
        "reference",
        "unconditional_stack",
        "cheap",
        "leverage_matched",
        "volatility_matched_expost",
    ):
        lines.append(
            f"\n### Arithmetic gap against `{control}` by window: gap [95% HAC interval] "
            "MDE years status (boot interval on scored cells); on-fraction in the second row\n"
        )
        lines.append("| arm | " + " | ".join(windows) + " |")
        lines.append("| --- | " + " | ".join("---" for _ in windows) + " |")
        for name, report in reports.items():
            by_window = report.gaps.get(control)
            if by_window is None:
                continue
            lines.append(
                f"| `{name}` | " + " | ".join(_cell(by_window.get(w)) for w in windows) + " |"
            )
            extras: list[str] = []
            for w in windows:
                g = by_window.get(w)
                if g is None:
                    extras.append("")
                else:
                    on = (
                        ""
                        if g.fraction_on is None
                        else f"on {g.fraction_on:.0%}, {g.switches} sw; "
                    )
                    extras.append(
                        f"{on}log {g.log_growth_gap_pp_yr:+.2f}; TE {g.tracking_error_pct:.2f}"
                    )
            lines.append(f"| `{name}` detail | " + " | ".join(extras) + " |")
    return lines


def _regime_table(reports: Mapping[str, ArmReport], rules: Mapping[str, RuleSpec]) -> list[str]:
    lines = [
        "\n### The mechanism: bond excess return and realised correlation in on-months and "
        "off-months (descriptive)\n",
        "| arm | window | months | on | on bond excess pp/yr | on corr | off bond excess pp/yr | "
        "off corr | all bond excess | all corr |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in rules:
        regime = _map(reports[name].descriptive["bond_regime_by_window"])
        for window, raw_row in regime.items():
            r = _map(raw_row)
            lines.append(
                f"| `{name}` | {window} | {r['months']} | {r['fraction_on']} | "
                f"{r['on_bond_excess_pp_yr']} | {r['on_realised_correlation']} | "
                f"{r['off_bond_excess_pp_yr']} | {r['off_realised_correlation']} | "
                f"{r['bond_excess_pp_yr']} | {r['bond_equity_correlation']} |"
            )
    return lines


def _episode_table(reports: Mapping[str, ArmReport]) -> list[str]:
    first = next(iter(reports.values()))
    names = list(_map(first.descriptive["episodes"]))
    lines = [
        "\n### Crisis episodes: arm cumulative return % (offset vs reference pp; offset vs "
        "unconditional pp; fraction on); * partial, n/c not covered\n",
        "| arm | " + " | ".join(names) + " |",
        "| --- | " + " | ".join("---:" for _ in names) + " |",
    ]
    for name, report in reports.items():
        episodes = _map(report.descriptive["episodes"])
        cells: list[str] = []
        for episode_name in names:
            e = _map(episodes[episode_name])
            if not e.get("covered"):
                cells.append("n/c")
                continue
            star = "*" if e.get("partial") else ""
            cells.append(
                f"{e['arm_cumulative_pct']}{star} ({e['offset_vs_reference_pp']}; "
                f"{e['offset_vs_unconditional_pp']}; on {e['fraction_on']})"
            )
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    return lines


def _spell_table(reports: Mapping[str, ArmReport], rules: Mapping[str, RuleSpec]) -> list[str]:
    lines = ["\n### On-spells of each conditioned arm\n"]
    for name in rules:
        spells = _seq(reports[name].descriptive["on_spells"])
        text = ", ".join(f"{_map(s)['start']}..{_map(s)['end']}" for s in spells)
        lines.append(f"- `{name}`: {text}")
    return lines


def _deflation_table(deflation: Mapping[str, JsonValue]) -> list[str]:
    lines = [
        "\n### Deflation across the four arms\n",
        f"Mean off-diagonal correlation of the paired differences "
        f"{deflation['mean_off_diagonal_correlation_of_paired_differences']} on "
        f"{deflation['common_months']} common months from {deflation['common_first_month']}; "
        f"effective trials {deflation['effective_number_of_trials']} of "
        f"{len(_seq(deflation['arms']))} (linear reading, UNVERIFIED). Primary arm monthly "
        f"Sharpe of the paired difference {deflation['primary_observed_sharpe_monthly']} "
        f"(annualised {deflation['primary_observed_sharpe_annualised']}); trial dispersion "
        f"{deflation['trial_dispersion']}.\n",
        "| trials | SR* (monthly) | deflated significance |",
        "| --- | ---: | ---: |",
    ]
    for label, raw_row in _map(deflation["deflated_sharpe_by_trial_count"]).items():
        r = _map(raw_row)
        lines.append(
            f"| {label} ({r['n_trials']}) | {r['sharpe_threshold_monthly']} | "
            f"{r['deflated_significance']} |"
        )
    return lines


def _regret_table(regret: Mapping[str, JsonValue]) -> list[str]:
    inputs = _map(regret["inputs"])
    lines = [
        "\n### Regret, bp/yr of expected log growth (arithmetic on stated inputs; no status)\n",
        "Inputs from the run: " + ", ".join(f"{k} {v}" for k, v in inputs.items()) + ".\n",
        "| state | term premium pp/yr | gap: conditioned | unconditional | neither | "
        "regret: conditioned | unconditional | neither |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for raw_cell in _seq(regret["cells"]):
        c = _map(raw_cell)
        g, r = _map(c["gap_bp_yr"]), _map(c["regret_bp_yr"])
        lines.append(
            f"| {c['state']} | {c['term_premium_pp_yr']} | {g['conditioned']} | "
            f"{g['unconditional']} | {g['neither']} | {r['conditioned']} | "
            f"{r['unconditional']} | {r['neither']} |"
        )
    worst = _map(regret["max_regret_bp_yr"])
    lines.append(
        f"\nMax regret: conditioned {worst['conditioned']}, unconditional "
        f"{worst['unconditional']}, neither {worst['neither']}; minimax action "
        f"`{regret['minimax_action']}`."
    )
    return lines


def render_tables(
    reports: Mapping[str, ArmReport],
    *,
    rules: Mapping[str, RuleSpec],
    header: Sequence[str],
    deflation: Mapping[str, JsonValue],
    regret: Mapping[str, JsonValue],
) -> str:
    windows: list[str] = []
    for report in reports.values():
        for by_window in report.gaps.values():
            for w in by_window:
                if w not in windows:
                    windows.append(w)
    lines: list[str] = list(header)
    lines.extend(_state_table(reports))
    lines.extend(_gap_tables(reports, windows=windows))
    lines.extend(_regime_table(reports, rules))
    lines.extend(_episode_table(reports))
    lines.extend(_spell_table(reports, rules))
    lines.extend(_deflation_table(deflation))
    lines.extend(_regret_table(regret))
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


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
        prog="python -m portfolio_edge.experiments.exp_020_conditional_treasury_stack",
        description="Score a bond-regime-conditioned Treasury stack inside the construction.",
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
