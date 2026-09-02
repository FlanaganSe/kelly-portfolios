"""Experiment 022: the excess-CAPE-yield rule, frozen and run sheltered-only.

What this is
------------
``docs/research/valuation-and-the-allocation.md`` section 3 measured, as an
unregistered study, that tilting an 80/20 real equity/Treasury mix on the
expanding percentile of Shiller's excess CAPE yield at k = 0.4 earned about
+50 bp/yr gross against a constant mix. This module runs that rule under a
frozen specification: a one-month signal lag, no tax (the sheltered case),
three controls each on the arm's own rebalancing clock, HAC intervals with a
minimum detectable effect beside every gap, a six-arm Holm family, a
TIPS-spliced defensive leg, an annual-band rebalancing variant, the five
frozen crisis episodes, a regret table for today's position and the
arithmetic of the rule inside the traditional third.

What this is NOT
----------------
**It is not out of sample.** k = 0.4 was chosen on this workbook by the study
this run registers. The specification says so and the status ceiling is
``exploratory``.

**It is not point-in-time.** The workbook is revised on every release. The lag
removes the availability look-ahead and nothing removes the revision.

**Its equity price is a monthly average**, which understates every drawdown
and raises serial correlation; the French month-end panel is the check.

Run it::

    uv run python -m portfolio_edge.experiments.exp_022_ecy_rule --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import fred, french, shiller
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    workspace_root,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import CostBasis, Estimate, ExperimentResult, ResultStatus
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
from portfolio_edge.inference.hac import hac_mean, hac_ols
from portfolio_edge.inference.multiple_testing import holm_bonferroni
from portfolio_edge.studies.fixed_income_shelf import par_bond_total_returns
from portfolio_edge.studies.valuation_conditioning import (
    ConditionalWeightRule,
    conditional_weight,
    stambaugh_bias,
)

__all__ = [
    "ENTRY_POINT",
    "MONTHS_PER_YEAR",
    "Arm",
    "EcyRuleError",
    "GapStats",
    "Panel",
    "RawSeries",
    "RebalanceClock",
    "WalkResult",
    "build_panel",
    "build_registry",
    "construction_implication",
    "default_specification_path",
    "episode_table",
    "expanding_percentile",
    "gap_stats",
    "load_series",
    "read_arms",
    "regret_table",
    "rolling_window_stats",
    "rule_weights",
    "run",
    "shiller_excess_cape_yield_pp",
    "walk",
]

ENTRY_POINT: Final = "exp_022_ecy_rule"
MONTHS_PER_YEAR: Final = 12
FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]
MonthSeries = dict[str, float]

CONTROL_KINDS: Final = ("risk_matched", "equity100", "mix85")


class EcyRuleError(Exception):
    """A failure specific to this experiment's contract."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_022_ecy_rule.yaml"


# --------------------------------------------------------------------------- #
# Specification access
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise EcyRuleError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise EcyRuleError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise EcyRuleError(f"{where} is missing {key!r}")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise EcyRuleError(f"{where}.{key} must be a non-empty string")
    return value


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise EcyRuleError(f"{where}.{key} must be a number")
    return float(value)


def _integer(data: Mapping[str, JsonValue], key: str, *, where: str) -> int:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int):
        raise EcyRuleError(f"{where}.{key} must be an integer")
    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class Arm:
    name: str
    sensitivity: float
    defensive_leg: str
    signal: str
    role: str


def read_arms(specification: Specification) -> dict[str, Arm]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "arms", where="parameters"), where="parameters.arms")
    out: dict[str, Arm] = {}
    for name, raw in block.items():
        item = _mapping(raw, where=f"parameters.arms.{name}")
        role = item.get("role", "secondary")
        out[name] = Arm(
            name=name,
            sensitivity=_number(item, "sensitivity", where=name),
            defensive_leg=_text(item, "defensive_leg", where=name),
            signal=_text(item, "signal", where=name),
            role=str(role),
        )
    primaries = [a for a in out.values() if a.role == "primary"]
    if len(primaries) != 1:
        raise EcyRuleError(f"exactly one primary arm is required, found {len(primaries)}")
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class RebalanceClock:
    """How often the target is reviewed, and how far it may drift before a trade."""

    name: str
    review_every_months: int
    relative_band: float

    def __post_init__(self) -> None:
        if self.review_every_months < 1:
            raise EcyRuleError("review_every_months must be at least 1")
        if self.relative_band < 0.0:
            raise EcyRuleError("relative_band cannot be negative")


def _read_clocks(specification: Specification) -> dict[str, RebalanceClock]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "rebalancing", where="parameters"), where="rebalancing")
    out: dict[str, RebalanceClock] = {}
    for name, raw in block.items():
        item = _mapping(raw, where=f"rebalancing.{name}")
        out[name] = RebalanceClock(
            name=name,
            review_every_months=_integer(item, "review_every_months", where=name),
            relative_band=_number(item, "relative_band", where=name),
        )
    if "monthly" not in out:
        raise EcyRuleError("the specification must declare a `monthly` clock")
    return out


# --------------------------------------------------------------------------- #
# Signal arithmetic
# --------------------------------------------------------------------------- #


def shiller_excess_cape_yield_pp(
    cape: FloatArray, gs10_percent: FloatArray, cpi: FloatArray, *, trailing_months: int = 120
) -> FloatArray:
    """``100/CAPE - (GS10 - 100 * ((CPI_t / CPI_{t-120})**(1/10) - 1))``, in points.

    Shiller's own construction: the cyclically adjusted earnings yield over the
    nominal ten-year yield deflated by trailing ten-year annualised inflation.
    NaN where any input is missing or the trailing window does not exist. The
    unit test pins three workbook rows against the published column.
    """
    n = cape.size
    if gs10_percent.size != n or cpi.size != n:
        raise EcyRuleError("cape, gs10 and cpi must be aligned")
    years = trailing_months / MONTHS_PER_YEAR
    out = np.full(n, np.nan)
    for i in range(trailing_months, n):
        c, g, p1, p0 = cape[i], gs10_percent[i], cpi[i], cpi[i - trailing_months]
        if not (np.isfinite(c) and np.isfinite(g) and np.isfinite(p1) and np.isfinite(p0)):
            continue
        if c <= 0.0 or p0 <= 0.0:
            continue
        inflation = 100.0 * ((p1 / p0) ** (1.0 / years) - 1.0)
        out[i] = 100.0 / c - (g - inflation)
    return out


def expanding_percentile(values: FloatArray, *, burn_in_prior: int) -> FloatArray:
    """Share of PRIOR observations strictly below the current one.

    Strictly backward-looking. Defined only where at least ``burn_in_prior``
    finite prior observations exist; NaN before that. A NaN in the history is
    skipped, never counted.
    """
    n = values.size
    out = np.full(n, np.nan)
    history: list[float] = []
    for i in range(n):
        v = float(values[i])
        if len(history) >= burn_in_prior and np.isfinite(v):
            arr = np.asarray(history)
            out[i] = float(np.mean(arr < v))
        if np.isfinite(v):
            history.append(v)
    return out


def rule_weights(
    percentile: FloatArray, *, base: float, sensitivity: float, floor: float, cap: float
) -> FloatArray:
    """``clip(base + k (pct - 0.5), floor, cap)`` element-wise; NaN stays NaN."""
    rule = ConditionalWeightRule(base, sensitivity, floor, cap)
    out = np.full(percentile.size, np.nan)
    for i, p in enumerate(percentile):
        if np.isfinite(p):
            out[i] = conditional_weight(rule, float(p))
    return out


# --------------------------------------------------------------------------- #
# The walk
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class WalkResult:
    returns: FloatArray
    """Monthly simple real return of the portfolio, net of execution."""
    held_weights: FloatArray
    """Equity weight held during each month, after any trade."""
    turnover_per_year: float
    rebalances_per_year: float
    trades: int


def walk(
    target: FloatArray,
    equity: FloatArray,
    bond: FloatArray,
    *,
    spread_bp: float,
    clock: RebalanceClock,
) -> WalkResult:
    """Drive a two-asset portfolio toward ``target`` on ``clock``.

    ``equity`` and ``bond`` are monthly SIMPLE returns. The first month buys the
    target for free (every arm starts from a common portfolio). At a review
    month the portfolio trades to the target if the held BOND weight differs
    from the target bond weight by more than ``relative_band`` of the target
    bond weight (a band of zero means always). Execution is charged on the
    traded fraction. Between trades the weights drift.
    """
    n = target.size
    if equity.size != n or bond.size != n:
        raise EcyRuleError("target, equity and bond must be aligned")
    if not np.all(np.isfinite(target)):
        raise EcyRuleError("target contains NaN; restrict to the decision window first")
    held = float(target[0])
    out = np.empty(n)
    weights = np.empty(n)
    traded = 0.0
    trades = 0
    for i in range(n):
        cost = 0.0
        if i > 0 and i % clock.review_every_months == 0:
            desired = float(target[i])
            bond_target = 1.0 - desired
            bond_held = 1.0 - held
            deviation = abs(bond_held - bond_target) / max(bond_target, 1e-12)
            if clock.relative_band <= 0.0 or deviation > clock.relative_band:
                change = abs(desired - held)
                if change > 0.0:
                    traded += change
                    trades += 1
                    cost = change * spread_bp / 1e4
                held = desired
        weights[i] = held
        gross = held * equity[i] + (1.0 - held) * bond[i]
        out[i] = gross - cost
        grown_equity = held * (1.0 + equity[i])
        grown_bond = (1.0 - held) * (1.0 + bond[i])
        held = grown_equity / (grown_equity + grown_bond)
    years = n / MONTHS_PER_YEAR
    return WalkResult(
        returns=out,
        held_weights=weights,
        turnover_per_year=traded / years,
        rebalances_per_year=trades / years,
        trades=trades,
    )


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class GapStats:
    gap_pp_yr: float
    log_gap_pp_yr: float
    standard_error_pp_yr: float
    t_statistic: float
    p_value: float
    interval: tuple[float, float]
    mde_pp_yr: float
    tracking_error_pct: float
    months: int
    years_to_distinguish: float


def gap_stats(arm: FloatArray, control: FloatArray, *, hac_lags: int) -> GapStats:
    """Arithmetic and log gaps with a Newey-West interval and an 80%-power floor."""
    if arm.shape != control.shape:
        raise EcyRuleError("arm and control must cover the same months")
    difference = arm - control
    scale = 100.0 * MONTHS_PER_YEAR
    hac = hac_mean(difference, n_lags=hac_lags)
    gap = hac.mean * scale
    se = hac.standard_error * scale
    sigma = float(np.std(difference, ddof=1))
    n = difference.size
    mde = MDE_MULTIPLIER * sigma / math.sqrt(n) * scale
    annual_sigma = sigma * math.sqrt(MONTHS_PER_YEAR) * 100.0
    years = (MDE_MULTIPLIER * annual_sigma / abs(gap)) ** 2 if gap != 0.0 else math.inf
    log_gap = float(np.mean(np.log1p(arm) - np.log1p(control))) * scale
    return GapStats(
        gap_pp_yr=gap,
        log_gap_pp_yr=log_gap,
        standard_error_pp_yr=se,
        t_statistic=hac.t_statistic,
        p_value=hac.p_value,
        interval=(gap - 1.959964 * se, gap + 1.959964 * se),
        mde_pp_yr=mde,
        tracking_error_pct=annual_sigma,
        months=n,
        years_to_distinguish=years,
    )


def rolling_window_stats(
    arm: FloatArray, control: FloatArray, *, window_months: int
) -> dict[str, float]:
    """Annualised arithmetic gap over every rolling window; share ahead and quantiles."""
    if arm.size < window_months:
        return {"n_windows": 0.0, "n_independent": 0.0}
    difference = arm - control
    cumulative = np.concatenate([[0.0], np.cumsum(difference)])
    sums = cumulative[window_months:] - cumulative[:-window_months]
    gaps_bp = sums / window_months * MONTHS_PER_YEAR * 1e4
    return {
        "n_windows": float(gaps_bp.size),
        "n_independent": gaps_bp.size / window_months,
        "share_ahead": float(np.mean(gaps_bp > 0.0)),
        "median_bp": float(np.median(gaps_bp)),
        "p10_bp": float(np.percentile(gaps_bp, 10)),
        "p90_bp": float(np.percentile(gaps_bp, 90)),
    }


def _wealth(returns: FloatArray) -> FloatArray:
    return np.concatenate([[1.0], np.cumprod(1.0 + returns)])


def _drawdown(returns: FloatArray) -> dict[str, float]:
    summary = drawdown_summary(_wealth(returns))
    return {
        "max_drawdown_pct": 100.0 * summary.max_drawdown,
        "time_under_water_months": float(summary.max_time_under_water),
    }


def _slice(periods: Sequence[str], start: str, end: str) -> IndexArray:
    labels = np.asarray(periods)
    return np.flatnonzero((labels >= start) & (labels <= end))


def episode_table(
    periods: Sequence[str],
    series: Mapping[str, FloatArray],
    weights: FloatArray,
    episodes: Sequence[tuple[str, str, str]],
) -> list[dict[str, JsonValue]]:
    """Cumulative return and worst drawdown inside each episode, per series."""
    rows: list[dict[str, JsonValue]] = []
    for name, start, end in episodes:
        idx = _slice(periods, start, end)
        row: dict[str, JsonValue] = {"episode": name, "start": start, "end": end}
        if idx.size == 0:
            row["covered"] = False
            rows.append(row)
            continue
        row["covered"] = True
        row["months"] = int(idx.size)
        row["entry_equity_weight"] = round(float(weights[idx[0]]), 4)
        for label, values in series.items():
            path = values[idx]
            row[f"{label}_cumulative_pct"] = round(100.0 * (float(np.prod(1.0 + path)) - 1.0), 2)
            row[f"{label}_worst_drawdown_pct"] = round(_drawdown(path)["max_drawdown_pct"], 2)
        rows.append(row)
    return rows


def regret_table(
    *,
    position_weight: float,
    counterfactual_weight: float,
    premia_pp_yr: Sequence[float],
    equity_volatility: float,
    bond_volatility: float,
    correlation: float,
    horizons_years: Sequence[int],
) -> list[dict[str, JsonValue]]:
    """Log-growth regret of two actions across premium states; no forecast.

    Growth of weight ``w`` at arithmetic premium ``m`` over the bond:
    ``g(w) = w m - 0.5 var(w)`` up to the common bond return, with
    ``var(w) = w**2 s_e**2 + (1-w)**2 s_b**2 + 2 w (1-w) rho s_e s_b``. Regret of
    an action in a state is the better action's growth less its own.
    """
    if not 0.0 <= position_weight <= counterfactual_weight <= 1.0:
        raise EcyRuleError("need 0 <= position <= counterfactual <= 1")

    def variance(w: float) -> float:
        return (
            w**2 * equity_volatility**2
            + (1.0 - w) ** 2 * bond_volatility**2
            + 2.0 * w * (1.0 - w) * correlation * equity_volatility * bond_volatility
        )

    rows: list[dict[str, JsonValue]] = []
    for m in premia_pp_yr:
        premium = m / 100.0
        growth_position = position_weight * premium - 0.5 * variance(position_weight)
        growth_counter = counterfactual_weight * premium - 0.5 * variance(counterfactual_weight)
        gap = growth_position - growth_counter
        best = max(growth_position, growth_counter)
        row: dict[str, JsonValue] = {
            "premium_over_bond_pp_yr": m,
            "arithmetic_cost_bp_yr": round(
                1e4 * (counterfactual_weight - position_weight) * premium, 1
            ),
            "log_growth_gap_bp_yr": round(1e4 * gap, 1),
            "regret_of_position_bp_yr": round(1e4 * (best - growth_position), 1),
            "regret_of_counterfactual_bp_yr": round(1e4 * (best - growth_counter), 1),
        }
        for years in horizons_years:
            row[f"terminal_wealth_ratio_{years}y_pct"] = round(
                100.0 * (math.exp(gap * years) - 1.0), 2
            )
        rows.append(row)
    return rows


def construction_implication(
    *,
    published_vector: Mapping[str, float],
    traditional_third: Mapping[str, float],
    third_size_pp: float,
    equity_weight_today: float,
) -> dict[str, JsonValue]:
    """Arithmetic: the rule applied only inside the traditional third."""
    bond_pp = round((1.0 - equity_weight_today) * third_size_pp, 2)
    rsst = traditional_third.get("RSST", 0.0)
    if bond_pp > rsst:
        raise EcyRuleError("the rule asks for more bond than the wrapper line can fund")
    new_rsst = round(rsst - bond_pp, 2)
    equity_notional_cut = round(1.072 * bond_pp, 2)
    trend_cut = round(bond_pp, 2)
    # RSST-like: 2.072 of exposure per dollar (1.072 equity, 1.0 trend), exp_018's mapping.
    gross_before = round((100.0 - rsst) / 100.0 + rsst / 100.0 * 2.072, 4)
    gross_after = round((100.0 - new_rsst) / 100.0 + new_rsst / 100.0 * 2.072, 4)
    total = sum(published_vector.values())
    return {
        "third_size_pp": third_size_pp,
        "rule_equity_weight_today": round(equity_weight_today, 4),
        "bond_pp_of_portfolio": bond_pp,
        "line_sold": "RSST",
        "rsst_before_pp": rsst,
        "rsst_after_pp": new_rsst,
        "idmo_unchanged_pp": traditional_third.get("IDMO", 0.0),
        "equity_notional_cut_pp": equity_notional_cut,
        "trend_notional_cut_pp": trend_cut,
        "published_vector_sums_to": total,
        "gross_exposure_before": gross_before,
        "gross_exposure_after": gross_after,
        "note": (
            "Selling the wrapper line keeps IDMO, which the rebalancing page says to keep, "
            "and moves no taxable line, so headroom is unchanged; the cost is the trend "
            "notional the wrapper carried on the sold capital."
        ),
    }


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RawSeries:
    periods: tuple[str, ...]
    cape: FloatArray
    gs10: FloatArray
    cpi: FloatArray
    real_equity_index: FloatArray
    real_bond_index: FloatArray
    workbook_ecy: FloatArray
    fii10: MonthSeries
    """Ten-year TIPS real yield as a DECIMAL per year, the FRED loader's convention."""
    french_market: MonthSeries
    french_rf: MonthSeries
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
    """The entry holding the PINNED bytes, read by digest if the index moved on."""
    where = "source_pin.files[]"
    expected = _text(pin, "expected_sha256_raw", where=where)
    entry = cache.entry_for(url)
    superseded: str | None = None
    if entry is None or entry.sha256 != expected:
        if not cache.has(expected):
            observed = "absent" if entry is None else entry.sha256
            raise EcyRuleError(
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


def _column(periods: Sequence[str], values: Sequence[float | None]) -> MonthSeries:
    """Key by ``YYYY-MM``; FRED labels a monthly series by its first day."""
    return {p[:7]: float(v) for p, v in zip(periods, values, strict=True) if v is not None}


def _array(periods: Sequence[str], values: Sequence[float | None]) -> FloatArray:
    if len(values) != len(periods):
        raise EcyRuleError("column length does not match the period index")
    return np.asarray([np.nan if v is None else float(v) for v in values], dtype=np.float64)


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
                f"{file_id}: the pinned file ({record['sha256_raw']}) differs from the "
                "committed manifest's vintage; recorded, not hidden."
            )
        if record["index_superseded_by_sha256"] is not None:
            findings.append(
                f"{file_id}: the cache index now points at "
                f"{record['index_superseded_by_sha256']}; the pinned blob "
                f"{record['sha256_raw']} was read by digest instead."
            )
        provenance.append(record)
        return entry, record

    dataset = shiller.get_dataset("shiller_ie_data")
    entry, record = take("shiller_ie_data", dataset.url)
    parsed = shiller.parse(cache, entry, dataset=dataset)
    table = parsed.table
    periods = tuple(table.periods)
    record["first_observation"], record["last_observation"] = periods[0], periods[-1]
    record["footnotes"] = list(parsed.footnotes)

    fii = fred.get_series("FII10")
    entry, record = take("fred_fii10", fii.url)
    fii_table = fred.parse(cache, entry, "FII10")
    fii10 = _column(fii_table.periods, fii_table.column("FII10"))
    record["first_observation"], record["last_observation"] = min(fii10), max(fii10)

    ff3 = french.get_dataset("french_us_ff3")
    entry, record = take("french_us_ff3", ff3.url)
    market = french.parse(cache, entry, dataset=ff3).table("monthly")
    french_market = _column(market.periods, market.column("Mkt-RF"))
    french_rf = _column(market.periods, market.column("RF"))
    record["first_observation"], record["last_observation"] = min(french_market), max(french_market)

    return RawSeries(
        periods=periods,
        cape=_array(periods, table.column("CAPE")),
        gs10=_array(periods, table.column("Long_Interest_Rate_GS10")),
        cpi=_array(periods, table.column("CPI")),
        real_equity_index=_array(periods, table.column("Real_Total_Return_Price")),
        real_bond_index=_array(periods, table.column("Real_Total_Bond_Returns")),
        workbook_ecy=_array(periods, table.column("Excess_CAPE_Yield")),
        fii10=fii10,
        french_market=french_market,
        french_rf=french_rf,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# The panel: signals per row, returns per row pair
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Panel:
    """Everything aligned on the workbook's rows.

    ``periods[i]`` labels row ``i``. ``equity[i]`` is the simple real return from
    row ``i`` to row ``i+1`` (length ``n-1``). ``signals[s][i]`` is the signal on
    row ``i``; ``percentiles[s][i]`` its expanding percentile. A weight for
    return ``i`` is read from the percentile at row ``i - lag``.
    """

    periods: tuple[str, ...]
    equity: FloatArray
    legs: Mapping[str, FloatArray]
    signals: Mapping[str, FloatArray]
    percentiles: Mapping[str, FloatArray]
    french_equity: FloatArray
    """French month-end real return for the month of row ``i+1``; NaN where absent."""
    tips_first_month: str | None
    signal_reconstruction_max_abs_error: float


def build_panel(raw: RawSeries, specification: Specification) -> Panel:
    parameters = _mapping(specification.parameters, where="parameters")
    rule = _mapping(_at(parameters, "rule", where="parameters"), where="rule")
    burn_in = _integer(rule, "burn_in_prior_months", where="rule")
    periods = raw.periods
    n = len(periods)

    equity = np.exp(np.diff(np.log(raw.real_equity_index))) - 1.0
    treasury = np.exp(np.diff(np.log(raw.real_bond_index))) - 1.0
    if not (np.all(np.isfinite(equity)) and np.all(np.isfinite(treasury))):
        raise EcyRuleError("the Shiller real indices contain gaps")

    signal = shiller_excess_cape_yield_pp(raw.cape, raw.gs10, raw.cpi)
    reconstruction = signal / 100.0 - raw.workbook_ecy
    reconstruction_error = float(np.nanmax(np.abs(reconstruction)))
    if reconstruction_error > 1e-9:
        raise EcyRuleError(
            f"the reconstructed excess CAPE yield differs from the workbook column by "
            f"{reconstruction_error:.3e}; the definition has changed"
        )

    # TIPS signal: 100/CAPE - FII10 from the first FII10 month, spliced on to Shiller before.
    tips_signal = signal.copy()
    for i, period in enumerate(periods):
        if period in raw.fii10 and np.isfinite(raw.cape[i]) and raw.cape[i] > 0.0:
            # The FRED loader converts percent to decimal; the signal is in points.
            tips_signal[i] = 100.0 / raw.cape[i] - 100.0 * raw.fii10[period]

    # TIPS leg: ten-year par bond on the real yield, real return, spliced on to the Treasury.
    tips_returns = par_bond_total_returns(dict(raw.fii10), maturity_years=10.0)
    tips_leg = treasury.copy()
    tips_first_return: str | None = None
    for i in range(n - 1):
        later = periods[i + 1]
        if later in tips_returns:
            tips_leg[i] = tips_returns[later]
            if tips_first_return is None:
                tips_first_return = later

    # French month-end real return for the month of row i+1, deflated by the Shiller CPI.
    french_equity = np.full(n - 1, np.nan)
    for i in range(n - 1):
        later = periods[i + 1]
        if later in raw.french_market and np.isfinite(raw.cpi[i]) and np.isfinite(raw.cpi[i + 1]):
            # The French loader already converts percent to decimal.
            nominal = 1.0 + raw.french_market[later] + raw.french_rf[later]
            french_equity[i] = nominal / (raw.cpi[i + 1] / raw.cpi[i]) - 1.0

    percentiles = {
        "shiller": expanding_percentile(signal, burn_in_prior=burn_in),
        "tips_spliced": expanding_percentile(tips_signal, burn_in_prior=burn_in),
    }
    return Panel(
        periods=periods,
        equity=equity,
        legs={"treasury": treasury, "tips_spliced": tips_leg},
        signals={"shiller": signal, "tips_spliced": tips_signal},
        percentiles=percentiles,
        french_equity=french_equity,
        tips_first_month=tips_first_return,
        signal_reconstruction_max_abs_error=reconstruction_error,
    )


def _target_weights(
    panel: Panel, *, signal: str, sensitivity: float, lag: int, rule: Mapping[str, JsonValue]
) -> FloatArray:
    """Weight for return ``i`` from the percentile at row ``i - lag``; length ``n-1``."""
    pct = panel.percentiles[signal]
    n_returns = panel.equity.size
    shifted = np.full(n_returns, np.nan)
    for i in range(n_returns):
        j = i - lag
        if j >= 0:
            shifted[i] = pct[j]
    return rule_weights(
        shifted,
        base=_number(rule, "base_weight", where="rule"),
        sensitivity=sensitivity,
        floor=_number(rule, "floor", where="rule"),
        cap=_number(rule, "cap", where="rule"),
    )


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class Comparison:
    window: str
    arm: str
    control: str
    clock: str
    control_weight: float
    gaps: dict[str, GapStats]
    """Keyed by cost basis: gross, net_optimistic, net_pessimistic."""
    status: str = "unresolved"
    clause: str = ""
    holm_adjusted_p: float | None = None
    rolling: dict[str, float] | None = None

    def to_json(self) -> dict[str, JsonValue]:
        gaps: dict[str, JsonValue] = {}
        for basis, g in self.gaps.items():
            gaps[basis] = {
                "gap_pp_yr": round(g.gap_pp_yr, 4),
                "log_gap_pp_yr": round(g.log_gap_pp_yr, 4),
                "hac_se_pp_yr": round(g.standard_error_pp_yr, 4),
                "hac_t": round(g.t_statistic, 3),
                "hac_p": round(g.p_value, 4),
                "interval_95": [round(g.interval[0], 4), round(g.interval[1], 4)],
                "mde_80pc_power_pp_yr": round(g.mde_pp_yr, 4),
                "tracking_error_pct": round(g.tracking_error_pct, 4),
                "years_to_distinguish": None
                if not math.isfinite(g.years_to_distinguish)
                else round(g.years_to_distinguish, 1),
                "months": g.months,
            }
        return {
            "window": self.window,
            "arm": self.arm,
            "control": self.control,
            "clock": self.clock,
            "control_equity_weight": round(self.control_weight, 4),
            "gaps": gaps,
            "status": self.status,
            "clause": self.clause,
            "holm_adjusted_p": None
            if self.holm_adjusted_p is None
            else round(self.holm_adjusted_p, 4),
            "rolling_30y": None
            if self.rolling is None
            else {k: round(v, 4) for k, v in self.rolling.items()},
        }


def _clause_for(
    gap: GapStats, *, holm_p: float | None, alpha: float, sign_check: bool | None
) -> tuple[str, str]:
    if gap.gap_pp_yr <= 0.0:
        return "rejected", "(a) mean gap at or below zero"
    if gap.gap_pp_yr < gap.mde_pp_yr:
        return "unresolved", "(b) gap inside its own 80%-power floor"
    if holm_p is not None and holm_p > alpha:
        return "unresolved", f"(c) Holm-adjusted p {holm_p:.3f} above {alpha}"
    if sign_check is False:
        return "unresolved", "(d) opposite sign on the French month-end panel"
    return "exploratory", "(e) clears every clause; ceiling is exploratory"


@dataclass(slots=True, kw_only=True)
class ArmRun:
    name: str
    window: str
    clock: str
    target: FloatArray
    walks: dict[str, WalkResult]
    """Keyed by cost basis."""
    mean_weight: float
    controls: dict[str, dict[str, WalkResult]]
    """control -> cost basis -> walk."""


def _cost_bases(specification: Specification) -> dict[str, float]:
    block = _mapping(specification.cost_model, where="cost_model")
    bps = _mapping(
        _at(block, "execution_basis_points_on_traded_fraction", where="cost_model"),
        where="cost_model.execution",
    )
    return {k: _number(bps, k, where="cost_model.execution") for k in bps}


_BASIS_TO_COST: Final = {
    "gross": CostBasis.GROSS,
    "net_optimistic": CostBasis.NET_OPTIMISTIC,
    "net_pessimistic": CostBasis.NET_PESSIMISTIC,
}


def _run_arm(
    *,
    name: str,
    window: str,
    idx: IndexArray,
    target_full: FloatArray,
    equity_full: FloatArray,
    bond_full: FloatArray,
    clock: RebalanceClock,
    bases: Mapping[str, float],
    mix85: float,
) -> ArmRun:
    target = target_full[idx]
    equity = equity_full[idx]
    bond = bond_full[idx]
    if not np.all(np.isfinite(target)):
        raise EcyRuleError(f"{name}: the target has NaN inside the {window} window")
    walks = {b: walk(target, equity, bond, spread_bp=bp, clock=clock) for b, bp in bases.items()}
    mean_weight = float(np.mean(target))
    controls: dict[str, dict[str, WalkResult]] = {}
    for kind, weight in (
        ("risk_matched", mean_weight),
        ("equity100", 1.0),
        ("mix85", mix85),
    ):
        constant = np.full(target.size, weight)
        controls[kind] = {
            b: walk(constant, equity, bond, spread_bp=bp, clock=clock) for b, bp in bases.items()
        }
    return ArmRun(
        name=name,
        window=window,
        clock=clock.name,
        target=target,
        walks=walks,
        mean_weight=mean_weight,
        controls=controls,
    )


def _compare(run_: ArmRun, *, hac_lags: int, rolling_months: int | None) -> dict[str, Comparison]:
    out: dict[str, Comparison] = {}
    for kind, by_basis in run_.controls.items():
        gaps = {
            basis: gap_stats(run_.walks[basis].returns, by_basis[basis].returns, hac_lags=hac_lags)
            for basis in run_.walks
        }
        weight = {
            "risk_matched": run_.mean_weight,
            "equity100": 1.0,
            "mix85": float(by_basis["gross"].held_weights[0]),
        }[kind]
        comparison = Comparison(
            window=run_.window,
            arm=run_.name,
            control=kind,
            clock=run_.clock,
            control_weight=weight,
            gaps=gaps,
        )
        if rolling_months is not None:
            comparison.rolling = rolling_window_stats(
                run_.walks["gross"].returns, by_basis["gross"].returns, window_months=rolling_months
            )
        out[kind] = comparison
    return out


def _stambaugh(signal_lagged: FloatArray, response: FloatArray) -> dict[str, float]:
    """The one-month predictive slope of the lagged signal and its small-sample bias.

    ``response[t]`` is regressed on ``signal_lagged[t]``; the predictor's own AR(1)
    innovation at ``t`` is paired with the predictive residual at ``t`` (both from
    ``t = 1`` on), exactly as ``studies/_valuation_conditioning_tables.stambaugh_table``.
    """
    predictive = hac_ols(response, signal_lagged, n_lags=0)
    autoregression = hac_ols(signal_lagged[1:], signal_lagged[:-1], n_lags=0)
    root = float(autoregression.coefficients[1])
    innovations = autoregression.residuals
    residuals = predictive.residuals[1:]
    bias = stambaugh_bias(
        innovation_covariance=float(np.cov(residuals, innovations, ddof=0)[0, 1]),
        predictor_innovation_variance=float(np.var(innovations, ddof=0)),
        autoregressive_root=root,
        n_observations=response.size,
    )
    fitted = float(predictive.coefficients[1])
    return {
        "autoregressive_root_monthly": root,
        "innovation_correlation": float(np.corrcoef(residuals, innovations)[0, 1]),
        "slope_monthly_per_pp": fitted,
        "bias_monthly_per_pp": bias,
        "bias_share_of_slope": bias / fitted if fitted != 0.0 else math.nan,
        "slope_annualised_uncorrected": MONTHS_PER_YEAR * fitted,
        "slope_annualised_corrected": MONTHS_PER_YEAR * (fitted - bias),
        "n_observations": float(response.size),
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _gap_cell(g: GapStats) -> str:
    return (
        f"{g.gap_pp_yr:+.2f} [{g.interval[0]:+.2f}, {g.interval[1]:+.2f}] floor {g.mde_pp_yr:.2f}"
    )


def _arm_table(
    window: str,
    clock: str,
    runs: Mapping[str, ArmRun],
    comparisons: Mapping[str, Mapping[str, Comparison]],
) -> list[str]:
    lines = [
        f"**{window}, {clock} clock.** Gap in pp/yr, gross, HAC 95% interval, MDE80 floor "
        "beside it; net at 10 bp in the last column against the risk-matched control.",
        "",
        "| arm | mean w | turnover/yr | rebal/yr | vs risk_matched | vs equity100 | vs mix85 "
        "| net10 vs risk_matched | log gap vs rm | status |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for name, run_ in runs.items():
        c = comparisons[name]
        rm = c["risk_matched"]
        lines.append(
            f"| `{name}` | {run_.mean_weight:.3f} | "
            f"{run_.walks['gross'].turnover_per_year:.3f} | "
            f"{run_.walks['gross'].rebalances_per_year:.2f} | "
            f"{_gap_cell(rm.gaps['gross'])} | {_gap_cell(c['equity100'].gaps['gross'])} | "
            f"{_gap_cell(c['mix85'].gaps['gross'])} | "
            f"{rm.gaps['net_pessimistic'].gap_pp_yr:+.2f} | "
            f"{rm.gaps['gross'].log_gap_pp_yr:+.2f} | {rm.status} {rm.clause} |"
        )
    return lines


def _rolling_table(comparisons: Mapping[str, Mapping[str, Comparison]]) -> list[str]:
    lines = [
        "| arm | control | windows | independent | share ahead | median bp | p10 bp | p90 bp |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, by_control in comparisons.items():
        for control, c in by_control.items():
            r = c.rolling
            if not r or r.get("n_windows", 0.0) == 0.0:
                continue
            lines.append(
                f"| `{name}` | {control} | {int(r['n_windows'])} | {r['n_independent']:.2f} | "
                f"{r['share_ahead']:.3f} | {r['median_bp']:+.1f} | {r['p10_bp']:+.1f} | "
                f"{r['p90_bp']:+.1f} |"
            )
    return lines


def _descriptive_table(rows: Sequence[Mapping[str, JsonValue]]) -> list[str]:
    if not rows:
        return []
    keys = list(rows[0].keys())
    lines = ["| " + " | ".join(keys) + " |", "| " + " | ".join("---" for _ in keys) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |")
    return lines


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    parameters = _mapping(specification.parameters, where="parameters")
    rule = _mapping(_at(parameters, "rule", where="parameters"), where="rule")
    lag = _integer(rule, "signal_lag_months", where="rule")
    hac_lags = _integer(parameters, "hac_lags", where="parameters")
    block_months = _number(parameters, "bootstrap_block_months", where="parameters")
    rolling_years = _integer(parameters, "rolling_window_years", where="parameters")
    holm_alpha = _number(parameters, "holm_alpha", where="parameters")
    mix85 = _number(parameters, "mix85_equity_weight", where="parameters")
    family = [str(x) for x in _sequence(_at(parameters, "holm_family", where="p"), where="f")]
    arms = read_arms(specification)
    clocks = _read_clocks(specification)
    bases = _cost_bases(specification)
    primary_arm = next(a for a in arms.values() if a.role == "primary")

    raw = load_series(specification)
    panel = build_panel(raw, specification)
    n_returns = panel.equity.size
    return_periods = panel.periods[:n_returns]

    windows: list[tuple[str, str, str]] = []
    for item in _sequence(_at(parameters, "windows", where="parameters"), where="windows"):
        w = _mapping(item, where="windows[]")
        windows.append(
            (_text(w, "id", where="w"), _text(w, "start", where="w"), _text(w, "end", where="w"))
        )
    episodes: list[tuple[str, str, str]] = []
    for item in _sequence(_at(parameters, "crisis_episodes", where="parameters"), where="e"):
        if isinstance(item, Mapping):
            e = _mapping(item, where="crisis_episodes[]")
            episodes.append(
                (
                    _text(e, "name", where="e"),
                    _text(e, "start", where="e"),
                    _text(e, "end", where="e"),
                )
            )

    # Targets for every arm and the sensitivities, on the whole return index.
    targets: dict[str, FloatArray] = {}
    legs_for: dict[str, str] = {}
    equity_for: dict[str, FloatArray] = {}
    for name, arm in arms.items():
        targets[name] = _target_weights(
            panel, signal=arm.signal, sensitivity=arm.sensitivity, lag=lag, rule=rule
        )
        legs_for[name] = arm.defensive_leg
        equity_for[name] = panel.equity
    k = primary_arm.sensitivity
    targets["sens_tips_signal"] = _target_weights(
        panel, signal="tips_spliced", sensitivity=k, lag=lag, rule=rule
    )
    legs_for["sens_tips_signal"] = "treasury"
    equity_for["sens_tips_signal"] = panel.equity
    targets["sens_lag_zero"] = _target_weights(
        panel, signal="shiller", sensitivity=k, lag=0, rule=rule
    )
    legs_for["sens_lag_zero"] = "treasury"
    equity_for["sens_lag_zero"] = panel.equity
    targets["sens_french"] = targets[primary_arm.name]
    legs_for["sens_french"] = "treasury"
    equity_for["sens_french"] = panel.french_equity
    # The primary arm on the Shiller series restricted to the months the French
    # panel covers, so the French comparison is read on one window.
    targets["sens_shiller_french_window"] = targets[primary_arm.name]
    legs_for["sens_shiller_french_window"] = "treasury"
    equity_for["sens_shiller_french_window"] = panel.equity

    all_runs: dict[tuple[str, str], dict[str, ArmRun]] = {}
    all_comparisons: dict[tuple[str, str], dict[str, dict[str, Comparison]]] = {}
    for window_id, start, end in windows:
        idx = _slice(return_periods, start, end)
        if idx.size == 0:
            raise EcyRuleError(f"window {window_id} is empty")
        for clock in clocks.values():
            runs: dict[str, ArmRun] = {}
            comparisons: dict[str, dict[str, Comparison]] = {}
            for name in targets:
                equity_series = equity_for[name]
                window_idx = idx
                if name in ("sens_french", "sens_shiller_french_window"):
                    window_idx = idx[np.isfinite(panel.french_equity[idx])]
                    if window_idx.size == 0:
                        continue
                run_ = _run_arm(
                    name=name,
                    window=window_id,
                    idx=window_idx,
                    target_full=targets[name],
                    equity_full=equity_series,
                    bond_full=panel.legs[legs_for[name]],
                    clock=clock,
                    bases=bases,
                    mix85=mix85,
                )
                runs[name] = run_
                comparisons[name] = _compare(
                    run_,
                    hac_lags=hac_lags,
                    rolling_months=rolling_years * MONTHS_PER_YEAR
                    if clock.name == "monthly"
                    else None,
                )
            # Holm within the family against the risk-matched control, gross.
            p_values = [comparisons[a]["risk_matched"].gaps["gross"].p_value for a in family]
            holm = holm_bonferroni(p_values, alpha=holm_alpha)
            for a, adjusted in zip(family, holm.adjusted_p_values, strict=True):
                comparisons[a]["risk_matched"].holm_adjusted_p = float(adjusted)
            french_sign = None
            if "sens_french" in comparisons:
                french_sign = (
                    comparisons["sens_french"]["risk_matched"].gaps["gross"].gap_pp_yr > 0.0
                )
            for name, by_control in comparisons.items():
                for control, c in by_control.items():
                    g = c.gaps["gross"]
                    c.status, c.clause = _clause_for(
                        g,
                        holm_p=c.holm_adjusted_p if control == "risk_matched" else None,
                        alpha=holm_alpha,
                        sign_check=french_sign
                        if name == primary_arm.name and control == "risk_matched"
                        else None,
                    )
            all_runs[(window_id, clock.name)] = runs
            all_comparisons[(window_id, clock.name)] = comparisons

    # The primary comparison, its bootstrap check and its deflated Sharpe.
    primary_key = (windows[0][0], "monthly")
    primary = all_comparisons[primary_key][primary_arm.name]["risk_matched"]
    primary_run = all_runs[primary_key][primary_arm.name]
    difference = (
        primary_run.walks["gross"].returns - primary_run.controls["risk_matched"]["gross"].returns
    )
    indices = stationary_bootstrap_indices(
        difference.size, block_months, specification.inference.resamples, context.rng
    )
    resampled = difference[indices].mean(axis=1) * MONTHS_PER_YEAR * 100.0
    bootstrap_interval = (
        float(np.percentile(resampled, 2.5)),
        float(np.percentile(resampled, 97.5)),
    )
    active = np.column_stack(
        [
            all_runs[primary_key][a].walks["gross"].returns
            - all_runs[primary_key][a].controls["risk_matched"]["gross"].returns
            for a in family
        ]
    )
    sharpes = active.mean(axis=0) / active.std(axis=0, ddof=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", LinearDependenceWarning)
        rho = mean_off_diagonal_correlation(active)
    n_eff = effective_number_of_trials(len(family), rho)
    dispersion = trial_dispersion_from_sharpes(sharpes)
    primary_sharpe = float(sharpes[family.index(primary_arm.name)])
    primary_active = active[:, family.index(primary_arm.name)]
    skew = float(np.mean(((primary_active - primary_active.mean()) / primary_active.std()) ** 3))
    kurt = float(np.mean(((primary_active - primary_active.mean()) / primary_active.std()) ** 4))
    deflated = {
        str(label): deflated_sharpe_ratio(
            primary_sharpe,
            trial_dispersion=dispersion,
            n_trials=count,
            n_observations=primary_active.size,
            skewness=skew,
            kurtosis=kurt,
        ).deflated_significance
        for label, count in (
            ("nominal_6", float(len(family))),
            ("effective", n_eff),
            ("100", 100.0),
        )
    }

    # Stambaugh on the primary signal's one-month predictive slope, full window,
    # in the page's alignment (row-t signal, t -> t+1 return) and in this run's
    # lagged alignment. The bias lives in the first; the rule trades on the second.
    full_idx = _slice(return_periods, windows[0][1], windows[0][2])
    response = panel.equity[full_idx] - panel.legs["treasury"][full_idx]
    stambaugh_rows: list[dict[str, JsonValue]] = []
    for alignment, shift in (("row_t_page_convention", 0), (f"lag_{lag}_as_traded", lag)):
        predictor = np.array(
            [panel.signals["shiller"][i - shift] for i in full_idx], dtype=np.float64
        )
        row_s: dict[str, JsonValue] = {"alignment": alignment}
        row_s.update({k_: round(v, 6) for k_, v in _stambaugh(predictor, response).items()})
        stambaugh_rows.append(row_s)

    # Descriptives: drawdown and episodes on the full window, monthly clock, gross.
    full_runs = all_runs[primary_key]
    descriptives: list[dict[str, JsonValue]] = []
    for name, run_ in full_runs.items():
        row: dict[str, JsonValue] = {"arm": name, "mean_weight": round(run_.mean_weight, 4)}
        row.update({k: round(v, 2) for k, v in _drawdown(run_.walks["gross"].returns).items()})
        for control in CONTROL_KINDS:
            dd = _drawdown(run_.controls[control]["gross"].returns)
            row[f"{control}_max_drawdown_pct"] = round(dd["max_drawdown_pct"], 2)
        row["min_weight"] = round(float(np.min(run_.target)), 4)
        row["max_weight"] = round(float(np.max(run_.target)), 4)
        descriptives.append(row)
    episode_rows = episode_table(
        [return_periods[i] for i in full_idx],
        {
            "rule": primary_run.walks["gross"].returns,
            "risk_matched": primary_run.controls["risk_matched"]["gross"].returns,
            "equity100": primary_run.controls["equity100"]["gross"].returns,
            "mix85": primary_run.controls["mix85"]["gross"].returns,
        },
        primary_run.walks["gross"].held_weights,
        episodes,
    )

    # Era table for the primary arm against the risk-matched control, gross.
    era_rows: list[dict[str, JsonValue]] = []
    full_diff = difference
    full_labels = [return_periods[i] for i in full_idx]
    for era in specification.sample_policy.eras:
        e_idx = _slice(full_labels, era.start, era.end)
        if e_idx.size == 0:
            continue
        era_rows.append(
            {
                "era": era.name,
                "months": int(e_idx.size),
                "gap_vs_risk_matched_bp_yr": round(float(np.mean(full_diff[e_idx])) * 1.2e5, 1),
                "mean_weight": round(float(np.mean(primary_run.target[e_idx])), 4),
            }
        )

    # Today's reading under both signals.
    last = len(panel.periods) - 1
    base = _number(rule, "base_weight", where="rule")
    today: dict[str, JsonValue] = {"row": panel.periods[last]}
    for sig in ("shiller", "tips_spliced"):
        value = float(panel.signals[sig][last])
        pct = float(panel.percentiles[sig][last])
        weight = conditional_weight(ConditionalWeightRule(base, k), pct)
        today[sig] = {
            "signal_pp": round(value, 3),
            "expanding_percentile": round(pct, 4),
            f"weight_k{k}": round(weight, 4),
            "scaled_to_all_equity_divide": round(weight / base, 4),
            "scaled_to_all_equity_cut": round(1.0 - (base - weight), 4),
        }
    today["tips_first_return_month"] = panel.tips_first_month

    # Regret for today's position.
    regret_block = _mapping(_at(parameters, "regret", where="parameters"), where="regret")
    eq = panel.equity[full_idx]
    bd = panel.legs["treasury"][full_idx]
    s_e = float(np.std(eq, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    s_b = float(np.std(bd, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    rho_eb = float(np.corrcoef(eq, bd)[0, 1])
    regret_rows = regret_table(
        position_weight=_number(regret_block, "position_equity_weight", where="regret"),
        counterfactual_weight=_number(regret_block, "counterfactual_equity_weight", where="regret"),
        premia_pp_yr=[
            float(x)
            for x in _sequence(_at(regret_block, "premium_over_tips_pp_yr", where="r"), where="r")
            if isinstance(x, int | float)
        ],
        equity_volatility=s_e,
        bond_volatility=s_b,
        correlation=rho_eb,
        horizons_years=[
            int(x)
            for x in _sequence(_at(regret_block, "horizons_years", where="r"), where="r")
            if isinstance(x, int)
        ],
    )
    regret: dict[str, JsonValue] = {
        "rows": regret_rows,
        "equity_volatility_pct": round(100.0 * s_e, 2),
        "bond_volatility_pct": round(100.0 * s_b, 2),
        "correlation": round(rho_eb, 3),
        "realised_premium_pp_yr_full_window": round(
            float(np.mean(eq) - np.mean(bd)) * MONTHS_PER_YEAR * 100.0, 2
        ),
        "note": (
            "Second moments from the full window on an averaged price; the de-risking "
            "credit is understated with it. Drawdown reduction is in the episode table."
        ),
    }

    # Construction implication.
    cons = _mapping(_at(parameters, "construction", where="parameters"), where="construction")
    shiller_today = _mapping(today["shiller"], where="today")
    implied = construction_implication(
        published_vector={
            k_: float(v)
            for k_, v in _mapping(_at(cons, "published_vector", where="c"), where="c").items()
            if isinstance(v, int | float)
        },
        traditional_third={
            k_: float(v)
            for k_, v in _mapping(_at(cons, "traditional_third", where="c"), where="c").items()
            if isinstance(v, int | float)
        },
        third_size_pp=_number(cons, "third_size_pp", where="construction"),
        equity_weight_today=float(_number(shiller_today, "scaled_to_all_equity_divide", where="t")),
    )

    # Estimates.
    estimates: list[Estimate] = []
    for (window_id, clock_name), comparisons in all_comparisons.items():
        if clock_name != "monthly":
            continue
        for name, by_control in comparisons.items():
            for control, c in by_control.items():
                label = f"{window_id}:{name} vs {control}"
                for basis, g in c.gaps.items():
                    estimates.append(
                        Estimate(
                            name=f"arithmetic_gap[{label}]",
                            value=round(g.gap_pp_yr, 4),
                            units="percentage points per year",
                            interval=(round(g.interval[0], 4), round(g.interval[1], 4)),
                            interval_method=f"Newey-West HAC, {hac_lags} lags, 95% normal",
                            cost_basis=_BASIS_TO_COST[basis],
                            n_obs=g.months,
                            notes=(
                                f"{c.status}; {c.clause}; control equity weight "
                                f"{c.control_weight:.3f}"
                            ),
                        )
                    )
                g0 = c.gaps["gross"]
                estimates.append(
                    Estimate(
                        name=f"minimum_detectable_effect[{label}]",
                        value=round(g0.mde_pp_yr, 4),
                        units="percentage points per year",
                        n_obs=g0.months,
                        uncertainty_unavailable_reason=(
                            "a detection floor is a property of the design, not an estimate "
                            "of a quantity in the world, so it carries no interval"
                        ),
                    )
                )
    estimates.append(
        Estimate(
            name="bootstrap_check[primary]",
            value=round(primary.gaps["gross"].gap_pp_yr, 4),
            units="percentage points per year",
            interval=(round(bootstrap_interval[0], 4), round(bootstrap_interval[1], 4)),
            interval_method=(
                f"stationary block bootstrap, mean block {block_months:.0f} months, "
                f"{specification.inference.resamples} resamples, 95% percentile"
            ),
            cost_basis=CostBasis.GROSS,
            n_obs=difference.size,
        )
    )

    status = ResultStatus(primary.status)
    g = primary.gaps["gross"]
    modern_id = windows[1][0]
    modern = all_comparisons[(modern_id, "monthly")][primary_arm.name]["risk_matched"].gaps["gross"]
    versus_equity = all_comparisons[primary_key][primary_arm.name]["equity100"].gaps["gross"]
    summary = (
        f"Primary comparison ({primary_arm.name}, {windows[0][0]} window, monthly clock, gross, "
        f"against the risk-matched control at {primary.control_weight:.3f} equity): "
        f"{g.gap_pp_yr:+.2f} pp/yr [{g.interval[0]:+.2f}, {g.interval[1]:+.2f}] against a "
        f"{g.mde_pp_yr:.2f} pp/yr floor on {g.months} months; Holm-adjusted p "
        f"{primary.holm_adjusted_p:.3f}; status `{status.value}`, {primary.clause}. "
        f"Against 100% equity: {versus_equity.gap_pp_yr:+.2f} pp/yr. "
        f"Modern window ({modern_id}) against the risk-matched control: "
        f"{modern.gap_pp_yr:+.2f} pp/yr against a {modern.mde_pp_yr:.2f} floor. "
        "Every drawdown, episode, rolling-window, turnover, regret and construction figure is "
        "descriptive and carries no status."
    )

    freeze_note = (
        "k = 0.4 was chosen on this workbook by the study this run registers; the status "
        "ceiling is exploratory. The workbook is revised on every release and the equity "
        "price is a monthly average. The signal is lagged one month; no tax is charged."
    )

    # Markdown tables.
    lines: list[str] = [f"### Experiment 022 tables. {freeze_note}", ""]
    for (window_id, clock_name), comparisons in all_comparisons.items():
        lines.extend(
            _arm_table(window_id, clock_name, all_runs[(window_id, clock_name)], comparisons)
        )
        lines.append("")
    lines.append("**Holm within the six-arm family, risk-matched control, gross.**")
    lines.append("")
    lines.append("| window | arm | gap pp/yr | HAC p | Holm-adjusted p |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for (window_id, clock_name), comparisons in all_comparisons.items():
        if clock_name != "monthly":
            continue
        for a in family:
            c = comparisons[a]["risk_matched"]
            lines.append(
                f"| {window_id} | `{a}` | {c.gaps['gross'].gap_pp_yr:+.3f} | "
                f"{c.gaps['gross'].p_value:.4f} | {c.holm_adjusted_p:.4f} |"
            )
    lines.append("")
    lines.append(
        f"**Deflated Sharpe of the primary active return.** monthly SR {primary_sharpe:.4f}, "
        f"trial dispersion {dispersion:.4f}, mean off-diagonal rho {rho:.3f}, effective trials "
        f"{n_eff:.2f} of {len(family)}; DSR "
        + ", ".join(f"{k_}: {v:.3f}" for k_, v in deflated.items())
    )
    lines.append("")
    lines.append(f"**Rolling {rolling_years}-year windows, full window, monthly clock, gross.**")
    lines.append("")
    lines.extend(_rolling_table(all_comparisons[primary_key]))
    lines.append("")
    lines.append("**Drawdown, full window, monthly clock, gross (descriptive).**")
    lines.append("")
    lines.extend(_descriptive_table(descriptives))
    lines.append("")
    lines.append("**Crisis episodes, primary arm (descriptive).**")
    lines.append("")
    lines.extend(_descriptive_table(episode_rows))
    lines.append("")
    lines.append("**Eras, primary arm against the risk-matched control, gross.**")
    lines.append("")
    lines.extend(_descriptive_table(era_rows))
    lines.append("")
    lines.append("**Stambaugh bias of the signal's one-month predictive slope.**")
    lines.append("")
    lines.extend(_descriptive_table(stambaugh_rows))
    lines.append("")
    lines.append("**Regret of the 85/15 position against 100% equity (arithmetic, no forecast).**")
    lines.append("")
    lines.extend(_descriptive_table(regret_rows))
    lines.append("")
    lines.append(f"**Today.** {today}")
    lines.append("")
    lines.append(f"**Construction.** {implied}")
    tables = "\n".join(lines)

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in raw.provenance],
        "source_findings": list(raw.findings),
        "signal_reconstruction_max_abs_error": panel.signal_reconstruction_max_abs_error,
        "comparisons": [
            c.to_json()
            for comparisons in all_comparisons.values()
            for by_control in comparisons.values()
            for c in by_control.values()
        ],
        "turnover": [
            {
                "window": window_id,
                "clock": clock_name,
                "arm": name,
                "turnover_per_year": round(r.walks["gross"].turnover_per_year, 4),
                "rebalances_per_year": round(r.walks["gross"].rebalances_per_year, 4),
                "risk_matched_turnover_per_year": round(
                    r.controls["risk_matched"]["gross"].turnover_per_year, 4
                ),
            }
            for (window_id, clock_name), runs in all_runs.items()
            for name, r in runs.items()
        ],
        "holm": {
            "family": family,
            "alpha": holm_alpha,
            "adjusted_p_by_window": {
                window_id: {
                    a: all_comparisons[(window_id, "monthly")][a]["risk_matched"].holm_adjusted_p
                    for a in family
                }
                for window_id, _, _ in windows
            },
        },
        "deflated_sharpe": {
            "primary_monthly_sharpe": round(primary_sharpe, 5),
            "trial_dispersion": round(dispersion, 5),
            "mean_off_diagonal_correlation": round(rho, 4),
            "effective_trials": round(n_eff, 3),
            "nominal_trials": len(family),
            "deflated_significance": {k_: round(v, 4) for k_, v in deflated.items()},
            "note": (
                "effective_number_of_trials carries an UNVERIFIED interpolation; both counts shown"
            ),
        },
        "bootstrap_check_primary": {
            "interval_95": [round(x, 4) for x in bootstrap_interval],
            "hac_interval_95": [round(x, 4) for x in primary.gaps["gross"].interval],
        },
        "drawdown_full_window": descriptives,
        "crisis_episodes": episode_rows,
        "eras_primary": era_rows,
        "stambaugh_signal": stambaugh_rows,
        "independent_30y_windows_full": round(
            (full_idx.size - rolling_years * MONTHS_PER_YEAR + 1)
            / (rolling_years * MONTHS_PER_YEAR),
            3,
        ),
        "today": today,
        "regret": regret,
        "construction": implied,
        "markdown_tables": tables,
    }
    caveats = (
        "k = 0.4 was selected on this data by the study this run registers; nothing here is "
        "out of sample and the status ceiling is exploratory.",
        "The workbook is revised on every release and publishes no vintages; the one-month "
        "lag removes availability look-ahead and not revision.",
        "The equity price is a monthly average: every drawdown is understated and serial "
        "correlation is inflated; the French month-end panel is the check.",
        "Both defensive legs are modelled index-level series: no fund, no bid/ask, no roll.",
        "No tax is charged; this is the sheltered case only.",
        "Drawdown, episode, rolling-window, turnover, regret and construction figures describe "
        "one realised history or are arithmetic; they carry no significance claim.",
        "No rule, sleeve or portfolio is promoted.",
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
        prog="python -m portfolio_edge.experiments.exp_022_ecy_rule",
        description="Run the frozen excess-CAPE-yield rule, sheltered only.",
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
