"""Experiment 024: the working default, scored as one object.

What this is
------------
``docs/research/portfolio-for-one-investor.md`` section 7 names a working default
for the investor: a 25% RSST-like wrapper, 70 points of unlevered equity and a
5-point unlevered ten-year Treasury or TIPS line, against the published 30%
wrapper and 70 points of equity. Experiment 016f scored 25 against 30 with no
defensive line; Experiment 018 scored 10-point substitutions beside a 30%
wrapper. This module scores the default as one object on 018's 1929-2025 panel
and machinery, with the wrapper cut and the bond line separated by companion
arms, and runs the same pair on 016f's 1990-11 fund-list panel so the two can
be read side by side. A regret table prices the pair at forward premia.

What this is NOT
----------------
**It does not score funds.** Every holding is an assumed per-dollar exposure
vector and a fee, or 016f's basis expression.

**The TIPS line is a nominal ten-year Treasury.** No TIPS series exists before
2003; the modelled ten-year par bond stands in, and the specification's freeze
note 3 says what that assumes.

**The primary pair was predicted ``rejected`` before the run**, as a leverage
result at the panel's realised premia; the forward-premium reading is the regret
table, not the sign.

Run it::

    uv run python -m portfolio_edge.experiments.exp_024_working_default --view-results
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
from portfolio_edge.data import aqr, fred, french, goyal_welch, shiller
from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MONTHS_PER_YEAR,
    BasisPanel,
    CostSettings,
    FundMapping,
    GapStatistics,
    PortfolioPath,
    _at,
    _build_mappings,
    _mapping,
    _number,
    _numbers,
    _sequence,
    _text,
    annualised_log_growth,
    constant_weight_path,
    load_basis_panel,
    minimum_detectable_effect,
    workspace_root,
)
from portfolio_edge.experiments.exp_016_construction_tournament import (
    _cost_settings as _tournament_costs,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    Episode,
    FinancingRates,
    Wrapper,
    _era_windows,
    _require_cached,
    _slice,
    arithmetic_gap,
    build_trend_book,
    contribution_terminal_wealth,
    read_episodes,
    read_rates,
    simulate_arm,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    _cost_settings as _engine_costs,
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
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.inference.multiple_testing import benjamini_hochberg
from portfolio_edge.studies.fixed_income_shelf import par_bond_total_returns
from portfolio_edge.studies.stress_dependence import episode_returns, tail_dependence
from portfolio_edge.studies.time_series_momentum import TimeSeriesMomentumSpec

FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]
MonthSeries = dict[str, float]

ENTRY_POINT: Final = "exp_024_working_default"

#: The legs a wrapper may name on the primary panel. ``tsy10`` is the modelled
#: ten-year par bond; ``treasury`` is Goyal-Welch's ~20-year total return.
LEGS: Final = ("equity", "treasury", "tsy10", "trend")
BOND_LEGS: Final = frozenset({"treasury", "tsy10"})

#: 016's notional legs plus the ten-year leg, for the tournament panel's gross.
TOURNAMENT_NOTIONAL_LEGS: Final = frozenset({"us_mkt", "dxus_mkt", "em_mkt", "trend", "treasury"})

Z_95: Final = 1.959964

__all__ = [
    "ENTRY_POINT",
    "LEGS",
    "Arm",
    "Notional",
    "WorkingDefaultError",
    "arm_notional",
    "build_registry",
    "default_specification_path",
    "main",
    "read_arms",
    "read_rates",
    "read_wrappers",
    "regret_gap_pp_yr",
    "run",
    "tournament_notional",
    "window_statistics",
]


class WorkingDefaultError(Exception):
    """The experiment refused to run, or an input did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_024_working_default.yaml"


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
    """What an arm holds per dollar of capital, by leg. ``cash`` is not notional."""

    gross: float
    equity: float
    trend: float
    bond: float
    cash: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "gross": round(self.gross, 4),
            "equity": round(self.equity, 4),
            "trend": round(self.trend, 4),
            "bond": round(self.bond, 4),
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
                raise WorkingDefaultError(f"wrappers.{ticker} names unknown leg {leg!r}")
        out[ticker] = Wrapper(
            ticker=ticker,
            exposures={leg: _number(exposures, leg, where="exposures") for leg in exposures},
            fee_bp=_number(fees, ticker, where="cost_model.wrapper_expense_ratio_basis_points"),
            financed={leg: _number(financed, leg, where="financed") for leg in financed},
            note=str(entry.get("note") or ""),
        )
    return out


def _read_weighted(
    block: Mapping[str, JsonValue], *, where: str
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    tickers = tuple(block)
    weights = tuple(_number(block, t, where=where) for t in tickers)
    if abs(sum(weights) - 1.0) > 1e-9:
        raise WorkingDefaultError(
            f"{where}: capital weights sum to {sum(weights):.4f}, not 1. Leverage lives "
            "inside the wrappers, never in the capital weights."
        )
    return tickers, weights


def read_arms(specification: Specification) -> dict[str, Arm]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "contestants", where="parameters"), where="contestants")
    out: dict[str, Arm] = {}
    for name in block:
        entry = _mapping(block[name], where=f"contestants.{name}")
        raw = _mapping(_at(entry, "weights", where=f"contestants.{name}"), where="weights")
        tickers, weights = _read_weighted(raw, where=f"contestants.{name}.weights")
        out[name] = Arm(
            name=name,
            role=str(entry.get("role") or "candidate"),
            tickers=tickers,
            weights=weights,
            note=str(entry.get("note") or ""),
        )
    return out


def arm_notional(
    tickers: Sequence[str], weights: Sequence[float], wrappers: Mapping[str, Wrapper]
) -> Notional:
    """Capital weights times per-dollar exposures, leg by leg; bonds count as notional."""
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
        bond=sum(by_leg[leg] for leg in BOND_LEGS),
        cash=cash,
    )


def tournament_notional(
    tickers: Sequence[str], weights: Sequence[float], mappings: Mapping[str, FundMapping]
) -> Notional:
    """The same decomposition on 016f's basis expressions, bonds counted."""
    equity = trend = bond = cash = 0.0
    for ticker, weight in zip(tickers, weights, strict=True):
        coefficients = mappings[ticker].coefficients
        held = 0.0
        for name, value in coefficients.items():
            if name in ("us_mkt", "dxus_mkt", "em_mkt"):
                equity += weight * value
                held += value
            elif name == "trend":
                trend += weight * value
                held += value
            elif name == "treasury":
                bond += weight * value
                held += value
        cash += weight * max(0.0, 1.0 - held)
    return Notional(gross=equity + trend + bond, equity=equity, trend=trend, bond=bond, cash=cash)


# --------------------------------------------------------------------------- #
# Series and the primary panel
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RawSeries:
    equity: MonthSeries
    cash: MonthSeries
    ltr: MonthSeries
    corpr: MonthSeries
    gw_rfree: MonthSeries
    commodity: MonthSeries
    shiller_gs10_pct: MonthSeries
    fred_gs10: MonthSeries
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


def load_series(specification: Specification) -> RawSeries:
    """Read every pinned source from the cache by digest; never download."""
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
                f"{record['index_superseded_by_sha256']}; the pinned blob "
                f"{record['sha256_raw']} was read by digest instead."
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

    shiller_dataset = shiller.get_dataset("shiller_ie_data")
    entry, record = take("shiller_ie_data", shiller_dataset.url)
    shiller_table = shiller.parse(cache, entry, dataset=shiller_dataset).table
    gs10_pct = _column(shiller_table.periods, shiller_table.column("Long_Interest_Rate_GS10"))
    record["first_observation"], record["last_observation"] = min(gs10_pct), max(gs10_pct)

    gs10_url = fred.series_url("GS10")
    entry, record = take("fred_gs10", gs10_url)
    fred_table = fred.parse(cache, entry, "GS10")
    fred_gs10 = _column(fred_table.periods, fred_table.column("GS10"))
    record["first_observation"], record["last_observation"] = min(fred_gs10), max(fred_gs10)

    return RawSeries(
        equity=equity,
        cash=cash,
        ltr=ltr,
        corpr=corpr,
        gw_rfree=gw_rfree,
        commodity=commodity,
        shiller_gs10_pct=gs10_pct,
        fred_gs10=fred_gs10,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Legs:
    equity: MonthSeries
    cash: MonthSeries
    treasury: MonthSeries
    tsy10: MonthSeries
    trend: MonthSeries
    trend_scalar: float
    trend_book_realised_volatility_pct: float
    trend_book_window: tuple[str, str]
    yield_cross_check_max_bp: float
    yield_cross_check_months: int


def build_legs(raw: RawSeries, specification: Specification) -> Legs:
    """Excess-of-cash legs, the trend book scaled exactly as 018 scales it."""
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
    # 018's intersection, so the scalar is 018's scalar.
    primary = sorted(set(unscaled) & set(raw.equity) & set(raw.cash) & set(treasury))
    if len(primary) < 2 * MONTHS_PER_YEAR:
        raise WorkingDefaultError("the primary window is shorter than two years")
    realised = float(np.std([unscaled[p] for p in primary], ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    scalar = target / realised
    scaled = {p: v * scalar for p, v in unscaled.items()}

    ten_year_block = _mapping(_at(parameters, "ten_year_leg", where="parameters"), where="ten")
    maturity = _number(ten_year_block, "maturity_years", where="ten_year_leg")
    shiller_yields = {p: v / 100.0 for p, v in raw.shiller_gs10_pct.items()}
    overlap = sorted(set(shiller_yields) & set(raw.fred_gs10))
    largest = max(
        (abs(shiller_yields[p] - raw.fred_gs10[p]) for p in overlap), default=float("nan")
    )
    # FRED wherever it exists, Shiller before it: the specification's ten_year_leg.
    yields = {**shiller_yields, **raw.fred_gs10}
    tsy10_total = par_bond_total_returns(yields, maturity_years=maturity)
    tsy10 = {p: tsy10_total[p] - raw.cash[p] for p in tsy10_total if p in raw.cash}

    return Legs(
        equity=raw.equity,
        cash=raw.cash,
        treasury=treasury,
        tsy10=tsy10,
        trend=scaled,
        trend_scalar=scalar,
        trend_book_realised_volatility_pct=realised * 100.0,
        trend_book_window=(primary[0], primary[-1]),
        yield_cross_check_max_bp=largest * 10_000.0,
        yield_cross_check_months=len(overlap),
    )


def build_primary_panel(legs: Legs) -> BasisPanel:
    common = (
        set(legs.cash) & set(legs.equity) & set(legs.treasury) & set(legs.tsy10) & set(legs.trend)
    )
    periods = sorted(common)
    if len(periods) < 3 * MONTHS_PER_YEAR:
        raise WorkingDefaultError(f"the primary panel holds {len(periods)} months")
    for earlier, later in itertools.pairwise(periods):
        if month_index(later) - month_index(earlier) != 1:
            raise WorkingDefaultError(f"the primary panel has a gap between {earlier} and {later}")
    series = {
        "equity": legs.equity,
        "treasury": legs.treasury,
        "tsy10": legs.tsy10,
        "trend": legs.trend,
    }
    return BasisPanel(
        periods=tuple(periods),
        series={n: np.array([s[p] for p in periods], dtype=np.float64) for n, s in series.items()},
        cash=np.array([legs.cash[p] for p in periods], dtype=np.float64),
        provenance=(),
        findings=(f"primary panel: {len(periods)} months, {periods[0]}..{periods[-1]}",),
    )


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def _volatility(values: FloatArray) -> float:
    return float(np.std(values, ddof=1))


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _round(value: float, digits: int = 4) -> float | None:
    finite = _finite(value)
    return None if finite is None else round(finite, digits) + 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class WindowStatistics:
    """One paired series on one window: arithmetic gap, HAC interval, floor, log gap."""

    window: str
    months: int
    gap_pp_yr: float
    hac_se_pp_yr: float
    hac_interval: tuple[float, float]
    hac_lags: int
    mde_pp_yr: float
    tracking_error_pct: float
    log_growth_gap_pp_yr: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "window": self.window,
            "months": self.months,
            "gap_pp_yr": _round(self.gap_pp_yr),
            "hac_se_pp_yr": _round(self.hac_se_pp_yr),
            "hac_interval_pp_yr": [_round(self.hac_interval[0]), _round(self.hac_interval[1])],
            "hac_lags": self.hac_lags,
            "mde_80pc_power_pp_yr": _round(self.mde_pp_yr),
            "tracking_error_pct": _round(self.tracking_error_pct),
            "log_growth_gap_pp_yr": _round(self.log_growth_gap_pp_yr),
        }


def window_statistics(
    arm_total: FloatArray, control_total: FloatArray, *, window: str
) -> WindowStatistics:
    if arm_total.shape != control_total.shape:
        raise WorkingDefaultError("arm and control must cover the same months")
    d = arm_total - control_total
    if d.size < 2:
        raise WorkingDefaultError(f"window {window!r} holds {d.size} months")
    scale = MONTHS_PER_YEAR * 100.0
    hac = hac_mean(d)
    gap = hac.mean * scale
    se = hac.standard_error * scale
    return WindowStatistics(
        window=window,
        months=int(d.size),
        gap_pp_yr=gap,
        hac_se_pp_yr=se,
        hac_interval=(gap - Z_95 * se, gap + Z_95 * se),
        hac_lags=hac.n_lags,
        mde_pp_yr=minimum_detectable_effect(d),
        tracking_error_pct=_volatility(d) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
        log_growth_gap_pp_yr=annualised_log_growth(arm_total)
        - annualised_log_growth(control_total),
    )


@dataclass(slots=True, kw_only=True)
class Comparison:
    control: str
    definition: str
    gap: GapStatistics | None
    full: WindowStatistics | None
    identical: bool = False
    adjusted_p: float | None = None
    status: str = "not-scored"
    clause: str = ""
    financing_band_range: tuple[float, float] | None = None
    windows: dict[str, WindowStatistics] = field(default_factory=dict)

    def to_json(self) -> dict[str, JsonValue]:
        gap, full = self.gap, self.full
        return {
            "control": self.control,
            "control_definition": self.definition,
            "identical_construction": self.identical,
            "gap_pp_yr": None if gap is None else _round(gap.gap_pp_yr),
            "bootstrap_interval_pp_yr": (
                None if gap is None else [_round(gap.interval[0]), _round(gap.interval[1])]
            ),
            "hac_interval_pp_yr": (
                None
                if full is None
                else [_round(full.hac_interval[0]), _round(full.hac_interval[1])]
            ),
            "hac_lags": None if full is None else full.hac_lags,
            "log_growth_gap_pp_yr": None if full is None else _round(full.log_growth_gap_pp_yr),
            "mde_80pc_power_pp_yr": None if gap is None else _round(gap.mde_pp_yr),
            "tracking_error_pct": None if gap is None else _round(gap.tracking_error_pct),
            "years_to_distinguish_at_80pc_power": (
                None if gap is None else _round(gap.years_to_distinguish, 1)
            ),
            "bootstrap_p_value": None if gap is None else _round(gap.p_value, 5),
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
            "windows": {k: v.to_json() for k, v in self.windows.items()},
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


# --------------------------------------------------------------------------- #
# The primary panel, simulated and scored
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class ArmPaths:
    arm: Arm
    notional: Notional
    path: PortfolioPath
    controls: dict[str, PortfolioPath]
    control_first_month: dict[str, int]
    control_definition: dict[str, str]


def simulate_primary(
    panel: BasisPanel,
    *,
    specification: Specification,
    arms: Mapping[str, Arm],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    costs: CostSettings,
) -> dict[str, ArmPaths]:
    """Every arm with its cheap, levered, vol-matched, 85/15 and reference controls."""
    parameters = _mapping(specification.parameters, where="parameters")
    reference = _text(parameters, "reference_arm", where="parameters")
    window = int(_number(parameters, "volatility_match_window_months", where="parameters"))
    mix_block = _mapping(_at(parameters, "mix85_weights", where="parameters"), where="mix85")
    mix_tickers, mix_weights = _read_weighted(mix_block, where="parameters.mix85_weights")

    cheap = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.0]))
    mix = simulate_arm(
        panel, wrappers, rates, costs, tickers=mix_tickers, targets=np.asarray(mix_weights)
    )
    core_total = cheap.total
    out: dict[str, ArmPaths] = {}
    for name, arm in arms.items():
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
        for t in range(window, panel.months):
            window_arm = _volatility(path.total[t - window : t])
            window_core = _volatility(core_total[t - window : t])
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
            first_month=window,
        )
        first["volatility_matched_exante"] = window
        definition["volatility_matched_exante"] = (
            f"CORE scaled each month to the trailing {window}-month volatility ratio, "
            "remainder in CASH, excess above one financed at the equity basis"
        )
        controls["mix85"] = mix
        first["mix85"] = 0
        definition["mix85"] = " + ".join(
            f"{w:.2f} x {t}" for t, w in zip(mix_tickers, mix_weights, strict=True)
        )
        out[name] = ArmPaths(
            arm=arm,
            notional=notional,
            path=path,
            controls=controls,
            control_first_month=first,
            control_definition=definition,
        )
    if reference not in out:
        raise WorkingDefaultError(f"reference arm {reference!r} is not a contestant")
    for name, item in out.items():
        if name != reference:
            item.controls["reference"] = out[reference].path
            item.control_first_month["reference"] = 0
            item.control_definition["reference"] = f"the {reference} arm"
    return out


@dataclass(slots=True, kw_only=True)
class PanelResult:
    id: str
    panel: BasisPanel
    arms: dict[str, ArmPaths]
    comparisons: dict[str, dict[str, Comparison]]
    descriptives: dict[str, dict[str, JsonValue]]
    regime: list[dict[str, JsonValue]]
    financing: dict[str, JsonValue]
    families: dict[str, list[str]]
    windows: list[tuple[str, str, str]]


def _point_gaps(simulated: Mapping[str, ArmPaths]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for name, item in simulated.items():
        out[name] = {}
        for control, path in item.controls.items():
            first = item.control_first_month[control]
            d = item.path.total[first:] - path.total
            out[name][control] = float(np.mean(d)) * MONTHS_PER_YEAR * 100.0
    return out


def _compare(
    simulated: Mapping[str, ArmPaths],
    *,
    periods: Sequence[str],
    windows: Sequence[tuple[str, str, str]],
    resamples: int,
    block: float,
    rng: np.random.Generator,
    confidence: float,
    q: float,
) -> tuple[dict[str, dict[str, Comparison]], dict[str, list[str]]]:
    cache: dict[int, IndexArray] = {}

    def draw(length: int) -> IndexArray:
        if length not in cache:
            cache[length] = stationary_bootstrap_indices(length, block, resamples, rng)
        return cache[length]

    comparisons: dict[str, dict[str, Comparison]] = {}
    families: dict[str, list[str]] = {}
    for name, item in simulated.items():
        comparisons[name] = {}
        for control, path in item.controls.items():
            first = item.control_first_month[control]
            arm_total = item.path.total[first:]
            identical = _volatility(arm_total - path.total) == 0.0
            stats = full = None
            if not identical:
                stats = arithmetic_gap(
                    arm_total, path.total, indices=draw(arm_total.size), confidence=confidence
                )
                full = window_statistics(arm_total, path.total, window="full")
            comparison = Comparison(
                control=control,
                definition=item.control_definition[control],
                gap=stats,
                full=full,
                identical=identical,
            )
            if not identical:
                for era_name, start, end in windows:
                    keep = _slice(periods[first:], start, end)
                    if keep.size >= MONTHS_PER_YEAR:
                        comparison.windows[era_name] = window_statistics(
                            arm_total[keep], path.total[keep], window=era_name
                        )
                families.setdefault(control, []).append(name)
            comparisons[name][control] = comparison

    for control, members in families.items():
        p_values: list[float] = []
        for n in members:
            gap = comparisons[n][control].gap
            assert gap is not None
            p_values.append(gap.p_value)
        adjusted = benjamini_hochberg(p_values, alpha=q)
        for n, value in zip(members, adjusted.adjusted_p_values, strict=True):
            comparisons[n][control].adjusted_p = float(value)
    return comparisons, families


def _describe(
    simulated: Mapping[str, ArmPaths],
    *,
    panel: BasisPanel,
    reference: str,
    episodes: Sequence[Episode],
    contribution: float,
    tail: float,
    comparisons: Mapping[str, Mapping[str, Comparison]],
) -> dict[str, dict[str, JsonValue]]:
    episode_windows = {e.name: (e.start, e.end) for e in episodes}
    equity_leg = panel.column("equity")
    reference_total = simulated[reference].path.total
    cheap_total = simulated[reference].controls["cheap"].total
    reference_terminal = contribution_terminal_wealth(reference_total, contribution=contribution)
    cheap_terminal = contribution_terminal_wealth(cheap_total, contribution=contribution)
    ref_episodes = episode_returns(panel.periods, reference_total, windows=episode_windows)
    cheap_episodes = episode_returns(panel.periods, cheap_total, windows=episode_windows)
    out: dict[str, dict[str, JsonValue]] = {}
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
            "terminal_wealth_ratio_vs_reference": _round(terminal / reference_terminal, 4),
        }
        if _volatility(total - reference_total) > 0.0:
            dependence = tail_dependence(equity_leg, total - reference_total, quantile=tail)
            row["worst_decile_offset_vs_reference"] = {
                "months": dependence.months_low,
                "equity_mean_pp_month": _round(dependence.base_mean_low * 100.0, 3),
                "offset_mean_pp_month": _round(dependence.mean_low * 100.0, 3),
                "offset_hit_rate": _round(dependence.hit_rate_low, 3),
                "offset_worst_pp_month": _round(dependence.worst_low * 100.0, 3),
                "best_decile_offset_mean_pp_month": _round(dependence.mean_high * 100.0, 3),
            }
        else:
            row["worst_decile_offset_vs_reference"] = None
        arm_episodes = episode_returns(panel.periods, total, windows=episode_windows)
        episode_rows: dict[str, JsonValue] = {}
        by_kind: dict[str, list[float]] = {}
        for i, episode in enumerate(episodes):
            a = arm_episodes[i]
            if not a.covered:
                episode_rows[episode.name] = {"kind": episode.kind, "covered": False}
                continue
            r, c = ref_episodes[i], cheap_episodes[i]
            offset = (a.cumulative_return - r.cumulative_return) * 100.0
            episode_rows[episode.name] = {
                "kind": episode.kind,
                "covered": True,
                "partial": a.partial,
                "months": a.months,
                "arm_cumulative_pct": _round(a.cumulative_return * 100.0, 2),
                "arm_peak_to_trough_pct": _round(a.peak_to_trough * 100.0, 2),
                "reference_cumulative_pct": _round(r.cumulative_return * 100.0, 2),
                "cheap_cumulative_pct": _round(c.cumulative_return * 100.0, 2),
                "offset_vs_reference_pp": _round(offset, 2),
                "offset_vs_cheap_pp": _round(
                    (a.cumulative_return - c.cumulative_return) * 100.0, 2
                ),
            }
            by_kind.setdefault(episode.kind, []).append(offset)
        row["episodes"] = episode_rows
        row["episode_type_mean_offset_vs_reference_pp"] = {
            kind: {"episodes": len(vals), "mean_pp": _round(float(np.mean(vals)), 2)}
            for kind, vals in by_kind.items()
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
        flat = comparisons[name].get("reference")
        row["flat_decade_gap_vs_reference_pp_yr"] = (
            None
            if flat is None or "flat_equity_decade" not in flat.windows
            else _round(flat.windows["flat_equity_decade"].gap_pp_yr)
        )
        out[name] = row
    return out


def _bond_regime(
    panel: BasisPanel, windows: Sequence[tuple[str, str, str]]
) -> list[dict[str, JsonValue]]:
    equity = panel.column("equity")
    tsy10 = panel.column("tsy10")
    ltr = panel.column("treasury")
    trend = panel.column("trend")
    out: list[dict[str, JsonValue]] = []
    for name, start, end in [("panel_full", panel.periods[0], panel.periods[-1]), *windows]:
        keep = _slice(panel.periods, start, end)
        b, e = tsy10[keep], equity[keep]
        out.append(
            {
                "era": name,
                "window": f"{start}..{end}",
                "months": int(keep.size),
                "tenyear_equity_correlation": _round(float(np.corrcoef(b, e)[0, 1]), 3),
                "tenyear_excess_pp_yr": _round(float(np.mean(b)) * MONTHS_PER_YEAR * 100.0, 2),
                "tenyear_volatility_pct": _round(
                    _volatility(b) * math.sqrt(MONTHS_PER_YEAR) * 100.0, 2
                ),
                "long_bond_excess_pp_yr": _round(
                    float(np.mean(ltr[keep])) * MONTHS_PER_YEAR * 100.0, 2
                ),
                "equity_excess_pp_yr": _round(float(np.mean(e)) * MONTHS_PER_YEAR * 100.0, 2),
                "trend_excess_pp_yr": _round(
                    float(np.mean(trend[keep])) * MONTHS_PER_YEAR * 100.0, 2
                ),
                "cash_pp_yr": _round(float(np.mean(panel.cash[keep])) * MONTHS_PER_YEAR * 100.0, 2),
            }
        )
    return out


def score_primary(
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
    contribution = _number(parameters, "contribution_per_month_of_starting_balance", where="p")
    tail = _number(parameters, "tail_quantile", where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")
    costs = _engine_costs(specification, rates)
    simulated = simulate_primary(
        panel, specification=specification, arms=arms, wrappers=wrappers, rates=rates, costs=costs
    )
    windows = _era_windows(specification, panel.periods)
    comparisons, families = _compare(
        simulated,
        periods=panel.periods,
        windows=windows,
        resamples=specification.inference.resamples if full else 200,
        block=block,
        rng=rng,
        confidence=specification.inference.confidence_level,
        q=q,
    )

    financing: dict[str, JsonValue] = {}
    if full:
        sensitivity = _mapping(
            _at(parameters, "financing_sensitivity", where="parameters"), where="financing"
        )
        grid = _numbers(_at(sensitivity, "equity_basis_points", where="financing"), where="grid")
        per_point: dict[str, dict[str, list[float]]] = {}
        for point in grid:
            shifted = FinancingRates(
                equity=point, treasury=rates.treasury, gold=rates.gold, tips=rates.tips
            )
            gaps = _point_gaps(
                simulate_primary(
                    panel,
                    specification=specification,
                    arms=arms,
                    wrappers=wrappers,
                    rates=shifted,
                    costs=_engine_costs(specification, shifted),
                )
            )
            for name, by_control in gaps.items():
                for control, value in by_control.items():
                    per_point.setdefault(name, {}).setdefault(control, []).append(value)
        ordering: list[list[str]] = []
        for i in range(len(grid)):
            ordering.append(
                sorted(
                    (n for n in arms if "reference" in per_point.get(n, {})),
                    key=lambda n: -per_point[n]["reference"][i],
                )
            )
        financing = {
            "grid_basis_points": list(grid),
            "gaps_pp_yr": {
                n: {c: [_round(v) for v in vs] for c, vs in by_control.items()}
                for n, by_control in per_point.items()
            },
            "ordering_against_reference_by_point": ordering,
            "ordering_against_reference_stable": all(o == ordering[0] for o in ordering),
        }
        for name in arms:
            for control, comparison in comparisons[name].items():
                values = per_point.get(name, {}).get(control)
                if values:
                    comparison.financing_band_range = (min(values), max(values))

    for name in arms:
        for comparison in comparisons[name].values():
            _apply_falsifier(comparison, q=q)

    descriptives = _describe(
        simulated,
        panel=panel,
        reference=reference,
        episodes=read_episodes(specification),
        contribution=contribution,
        tail=tail,
        comparisons=comparisons,
    )
    return PanelResult(
        id="primary",
        panel=panel,
        arms=simulated,
        comparisons=comparisons,
        descriptives=descriptives,
        regime=_bond_regime(panel, windows),
        financing=financing,
        families=families,
        windows=windows,
    )


# --------------------------------------------------------------------------- #
# The tournament panel: 016f's machinery plus the ten-year line
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class TournamentInputs:
    panel: BasisPanel
    mappings: Mapping[str, FundMapping]
    costs: CostSettings
    specification_hash: str
    findings: tuple[str, ...]


def load_tournament_inputs(specification: Specification, legs: Legs) -> TournamentInputs:
    """016f's panel, mapping and costs, hash-checked, with the ten-year leg added."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "tournament_panel", where="parameters"), where="tournament")
    path = workspace_root() / _text(block, "specification_path", where="tournament_panel")
    tournament = load_specification(path)
    expected = _text(block, "expected_specification_hash", where="tournament_panel")
    if tournament.spec_hash != expected:
        raise WorkingDefaultError(
            f"{path.name} hashes to {tournament.spec_hash}, not the pinned {expected}. The "
            "tournament panel is defined by that file; a new 016f needs a new 024."
        )
    base = load_basis_panel(tournament)
    mappings = dict(_build_mappings(tournament))
    costs = _tournament_costs(tournament)
    mappings["TSY10"] = FundMapping(
        ticker="TSY10",
        coefficients={"treasury": 1.0},
        expense_ratio_bp=read_wrappers(specification)["TSY10"].fee_bp,
        futures_notional=0.0,
        spread_region="us_equity",
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=True,
    )
    keep = [i for i, p in enumerate(base.periods) if p in legs.tsy10]
    if len(keep) < 3 * MONTHS_PER_YEAR:
        raise WorkingDefaultError("the ten-year leg covers too little of the tournament panel")
    index = np.asarray(keep, dtype=np.intp)
    periods = tuple(base.periods[i] for i in keep)
    series = {name: values[index] for name, values in base.series.items()}
    series["treasury"] = np.array([legs.tsy10[p] for p in periods], dtype=np.float64)
    findings = list(base.findings)
    if len(keep) != base.months:
        findings.append(
            f"the ten-year leg cut the tournament panel from {base.months} to {len(keep)} months"
        )
    return TournamentInputs(
        panel=BasisPanel(
            periods=periods,
            series=series,
            cash=base.cash[index],
            provenance=base.provenance,
            findings=tuple(findings),
        ),
        mappings=mappings,
        costs=costs,
        specification_hash=tournament.spec_hash,
        findings=tuple(findings),
    )


@dataclass(slots=True, kw_only=True)
class TournamentResult:
    inputs: TournamentInputs
    arms: dict[str, ArmPaths]
    comparisons: dict[str, dict[str, Comparison]]
    descriptives: dict[str, dict[str, JsonValue]]
    families: dict[str, list[str]]
    reproduction: dict[str, JsonValue]
    windows: list[tuple[str, str, str]]


def score_tournament(
    inputs: TournamentInputs,
    *,
    specification: Specification,
    rng: np.random.Generator,
    full: bool,
) -> TournamentResult:
    parameters = _mapping(specification.parameters, where="parameters")
    block_spec = _mapping(_at(parameters, "tournament_panel", where="parameters"), where="t")
    reference = _text(block_spec, "reference_arm", where="tournament_panel")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")
    controls_block = _mapping(_at(block_spec, "controls", where="tournament_panel"), where="c")
    cheap_tickers, cheap_weights = _read_weighted(
        _mapping(_at(controls_block, "cheap", where="controls"), where="cheap"),
        where="tournament_panel.controls.cheap",
    )
    era_names = {
        str(x) for x in _sequence(_at(block_spec, "eras", where="tournament_panel"), where="eras")
    }
    panel, mappings, costs = inputs.panel, inputs.mappings, inputs.costs

    arms: dict[str, Arm] = {}
    for name, raw in _mapping(
        _at(block_spec, "arms", where="tournament_panel"), where="arms"
    ).items():
        entry = _mapping(raw, where=f"tournament_panel.arms.{name}")
        tickers, weights = _read_weighted(
            _mapping(_at(entry, "weights", where=name), where="weights"), where=f"arms.{name}"
        )
        arms[name] = Arm(
            name=name,
            role="tournament",
            tickers=tickers,
            weights=weights,
            note=str(entry.get("note") or ""),
        )

    cheap = constant_weight_path(
        panel, mappings, costs, tickers=cheap_tickers, targets=np.asarray(cheap_weights)
    )
    simulated: dict[str, ArmPaths] = {}
    for name, arm in arms.items():
        notional = tournament_notional(arm.tickers, arm.weights, mappings)
        path = constant_weight_path(
            panel, mappings, costs, tickers=arm.tickers, targets=np.asarray(arm.weights)
        )
        levered = constant_weight_path(
            panel,
            mappings,
            costs,
            tickers=cheap_tickers,
            targets=np.asarray(cheap_weights) * notional.gross,
        )
        simulated[name] = ArmPaths(
            arm=arm,
            notional=notional,
            path=path,
            controls={"cheap": cheap, "leverage_matched": levered},
            control_first_month={"cheap": 0, "leverage_matched": 0},
            control_definition={
                "cheap": "65% VTI + 35% VXUS, unlevered, annual rebalancing",
                "leverage_matched": (
                    f"{notional.gross:.4f} x the cheap control, financed at the equity basis"
                ),
            },
        )
    if reference not in simulated:
        raise WorkingDefaultError(f"tournament reference arm {reference!r} is not an arm")
    for name, item in simulated.items():
        if name != reference:
            item.controls["reference"] = simulated[reference].path
            item.control_first_month["reference"] = 0
            item.control_definition["reference"] = f"the {reference} arm"

    windows = [
        w
        for w in _era_windows(specification, panel.periods)
        if w[0] in era_names or w[0].startswith("panel_")
    ]
    comparisons, families = _compare(
        simulated,
        periods=panel.periods,
        windows=windows,
        resamples=specification.inference.resamples if full else 200,
        block=block,
        rng=rng,
        confidence=specification.inference.confidence_level,
        q=q,
    )
    for name in arms:
        for comparison in comparisons[name].values():
            _apply_falsifier(comparison, q=q)

    descriptives: dict[str, dict[str, JsonValue]] = {}
    reference_total = simulated[reference].path.total
    for name, item in simulated.items():
        total = item.path.total
        summary = drawdown_summary(np.cumprod(1.0 + total))
        descriptives[name] = {
            "notional": item.notional.to_json(),
            "growth_log_pp_yr": _round(annualised_log_growth(total)),
            "arithmetic_mean_pp_yr": _round(float(np.mean(total)) * MONTHS_PER_YEAR * 100.0),
            "volatility_pct": _round(_volatility(total) * math.sqrt(MONTHS_PER_YEAR) * 100.0),
            "max_drawdown_pct": _round(summary.max_drawdown * 100.0, 2),
            "time_under_water_months": summary.max_time_under_water,
            "weighted_fee_bp": _round(item.path.weighted_fee_bp, 2),
            "annual_turnover_pct": _round(item.path.annual_turnover * 100.0, 3),
            "variance_minus_reference": _round(
                (_volatility(total) ** 2 - _volatility(reference_total) ** 2) * MONTHS_PER_YEAR, 6
            ),
        }

    repro_block = _mapping(_at(block_spec, "reproduction", where="tournament_panel"), where="r")
    expected = _number(repro_block, "expected_pp_yr", where="reproduction")
    tolerance = _number(repro_block, "tolerance_pp_yr", where="reproduction")
    observed = annualised_log_growth(simulated["published"].path.total) - annualised_log_growth(
        simulated["rec25"].path.total
    )
    reproduction: dict[str, JsonValue] = {
        "pair": "published (016f rec30) minus rec25, log-growth gap",
        "expected_pp_yr": expected,
        "observed_pp_yr": _round(observed),
        "tolerance_pp_yr": tolerance,
        "reproduced": abs(observed - expected) <= tolerance,
    }
    return TournamentResult(
        inputs=inputs,
        arms=simulated,
        comparisons=comparisons,
        descriptives=descriptives,
        families=families,
        reproduction=reproduction,
        windows=windows,
    )


# --------------------------------------------------------------------------- #
# Regret at forward premia
# --------------------------------------------------------------------------- #


def regret_gap_pp_yr(
    *,
    trend_gross_pp_yr: float,
    equity_premium_over_bonds_pp_yr: float,
    bond_excess_pp_yr: float,
    points: float,
    wrapper_equity: float,
    wrapper_cost_pp_yr: float,
    bond_fee_pp_yr: float,
) -> float:
    """Expected arithmetic gap, working default minus published, in pp/yr.

    ``points`` of capital leave a wrapper holding ``wrapper_equity`` of equity and
    one unit of trend per dollar, at ``wrapper_cost_pp_yr``, and buy one unit of
    bond at ``bond_fee_pp_yr``. Positive means the working default wins.
    """
    equity_excess = equity_premium_over_bonds_pp_yr + bond_excess_pp_yr
    forgone = wrapper_equity * equity_excess + trend_gross_pp_yr - wrapper_cost_pp_yr
    earned = bond_excess_pp_yr - bond_fee_pp_yr
    return points * (earned - forgone)


def regret_table(
    specification: Specification, *, variance_drag_pp_yr: float
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "regret", where="parameters"), where="regret")
    trend_grid = _numbers(_at(block, "trend_gross_premium_grid_pp_yr", where="regret"), where="t")
    equity_grid = _numbers(
        _at(block, "equity_premium_over_bonds_grid_pp_yr", where="regret"), where="e"
    )
    bond = _number(block, "bond_excess_over_cash_pp_yr", where="regret")
    points = _number(block, "points_moved", where="regret")
    wrapper_equity = _number(block, "wrapper_equity_per_dollar", where="regret")
    wrapper_cost = _number(block, "wrapper_cost_pp_yr", where="regret")
    bond_fee = _number(block, "bond_line_fee_pp_yr", where="regret")
    central = _number(block, "trend_central_pp_yr", where="regret")
    rows: list[JsonValue] = []
    for t in trend_grid:
        cells: list[JsonValue] = []
        for e in equity_grid:
            arithmetic = regret_gap_pp_yr(
                trend_gross_pp_yr=t,
                equity_premium_over_bonds_pp_yr=e,
                bond_excess_pp_yr=bond,
                points=points,
                wrapper_equity=wrapper_equity,
                wrapper_cost_pp_yr=wrapper_cost,
                bond_fee_pp_yr=bond_fee,
            )
            cells.append(
                {
                    "equity_premium_over_bonds_pp_yr": e,
                    "arithmetic_gap_pp_yr": _round(arithmetic, 3),
                    "log_growth_gap_pp_yr": _round(arithmetic + variance_drag_pp_yr, 3),
                }
            )
        rows.append({"trend_gross_pp_yr": t, "central": t == central, "cells": cells})
    break_even: list[JsonValue] = []
    for e in equity_grid:
        # Solve regret_gap_pp_yr == 0 for the trend premium; linear in t.
        arithmetic_t = bond - bond_fee - wrapper_equity * (e + bond) + wrapper_cost
        log_t = arithmetic_t + variance_drag_pp_yr / points
        break_even.append(
            {
                "equity_premium_over_bonds_pp_yr": e,
                "arithmetic_break_even_trend_pp_yr": _round(arithmetic_t, 3),
                "log_break_even_trend_pp_yr": _round(log_t, 3),
            }
        )
    return {
        "what": str(block.get("what") or ""),
        "bond_excess_over_cash_pp_yr": bond,
        "variance_drag_pp_yr": _round(variance_drag_pp_yr, 4),
        "rows": rows,
        "break_even_trend_premium_by_equity_premium": break_even,
        "note": (
            "Cells are working default minus published, pp/yr; positive means the working "
            "default wins. The log cell adds half the realised variance difference on the "
            "primary panel. The break-even is the gross trend premium at which the pair is "
            "zero; the working default wins below it."
        ),
    }


# --------------------------------------------------------------------------- #
# Markdown tables
# --------------------------------------------------------------------------- #


def _fmt(value: float | None, digits: int = 2) -> str:
    return "--" if value is None else f"{value:+.{digits}f}"


def _cell(comparison: Comparison | None) -> str:
    if comparison is None:
        return "--"
    if comparison.gap is None or comparison.full is None:
        return "identical" if comparison.identical else "--"
    g, f = comparison.gap, comparison.full
    years = "inf" if not math.isfinite(g.years_to_distinguish) else f"{g.years_to_distinguish:.0f}y"
    return (
        f"{g.gap_pp_yr:+.2f} boot [{g.interval[0]:+.2f}, {g.interval[1]:+.2f}] "
        f"HAC [{f.hac_interval[0]:+.2f}, {f.hac_interval[1]:+.2f}] MDE {g.mde_pp_yr:.2f} "
        f"log {f.log_growth_gap_pp_yr:+.2f} {years} `{comparison.status}`"
    )


def _arm_table(
    arms: Mapping[str, ArmPaths], descriptives: Mapping[str, Mapping[str, JsonValue]]
) -> list[str]:
    lines = [
        "\n### Arms: notional, growth, drawdown (descriptive)\n",
        "| arm | gross | equity | trend | bond | cash | arith pp/yr | log growth | vol % | Sharpe "
        "| max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: "
        "| ---: | ---: |",
    ]
    for name, item in arms.items():
        d = descriptives[name]
        n = item.notional
        lines.append(
            f"| `{name}` | {n.gross:.3f} | {n.equity:.3f} | {n.trend:.3f} | {n.bond:.3f} | "
            f"{n.cash:.3f} | {d['arithmetic_mean_pp_yr']} | {d['growth_log_pp_yr']} | "
            f"{d['volatility_pct']} | {d.get('sharpe', '--')} | {d['max_drawdown_pct']} | "
            f"{d['time_under_water_months']} | "
            f"{d.get('terminal_wealth_ratio_vs_reference', '--')} | "
            f"{d.get('terminal_wealth_ratio_vs_cheap', '--')} |"
        )
    return lines


def _gap_table(
    comparisons: Mapping[str, Mapping[str, Comparison]], controls: Sequence[str]
) -> list[str]:
    lines = [
        "\n### Arithmetic gaps against each control: gap, bootstrap and HAC intervals, MDE, "
        "log-growth gap, years-to-distinguish, status\n",
        "| arm | " + " | ".join(f"vs {c}" for c in controls) + " |",
        "| --- | " + " | ".join("---" for _ in controls) + " |",
    ]
    for name, by_control in comparisons.items():
        lines.append(
            f"| `{name}` | " + " | ".join(_cell(by_control.get(c)) for c in controls) + " |"
        )
    return lines


def _window_table(
    comparisons: Mapping[str, Mapping[str, Comparison]], *, control: str, windows: Sequence[str]
) -> list[str]:
    lines = [
        f"\n### Sub-windows against `{control}`: gap [HAC 95%] floor, per window\n",
        "| arm | " + " | ".join(windows) + " |",
        "| --- | " + " | ".join("---" for _ in windows) + " |",
    ]
    for name, by_control in comparisons.items():
        comparison = by_control.get(control)
        if comparison is None or comparison.identical:
            continue
        cells = []
        for w in windows:
            s = comparison.windows.get(w)
            cells.append(
                "--"
                if s is None
                else f"{s.gap_pp_yr:+.2f} [{s.hac_interval[0]:+.2f}, {s.hac_interval[1]:+.2f}] "
                f"MDE {s.mde_pp_yr:.2f} ({s.months}m)"
            )
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    return lines


def _crisis_table(descriptives: Mapping[str, Mapping[str, JsonValue]]) -> list[str]:
    lines = [
        "\n### Crisis behaviour against the reference arm (descriptive)\n",
        "| arm | worst-decile offset pp/month (hit rate) | deflationary episodes mean pp | "
        "inflation episodes mean pp | flat decade gap vs ref pp/yr |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, d in descriptives.items():
        wd = d.get("worst_decile_offset_vs_reference")
        kinds = d["episode_type_mean_offset_vs_reference_pp"]
        assert isinstance(kinds, Mapping)
        wd_text = (
            f"{wd['offset_mean_pp_month']} ({wd['offset_hit_rate']})"
            if isinstance(wd, Mapping)
            else "--"
        )

        def kind(value: JsonValue) -> str:
            return (
                f"{value['mean_pp']} ({value['episodes']} ep.)"
                if isinstance(value, Mapping)
                else "--"
            )

        flat = d.get("flat_decade_gap_vs_reference_pp_yr")
        lines.append(
            f"| `{name}` | {wd_text} | {kind(kinds.get('deflationary_or_growth'))} | "
            f"{kind(kinds.get('inflation_or_rate'))} | "
            f"{_fmt(float(flat) if isinstance(flat, int | float) else None)} |"
        )
    return lines


def _episode_table(descriptives: Mapping[str, Mapping[str, JsonValue]]) -> list[str]:
    first = next(iter(descriptives.values()))
    episodes_first = first["episodes"]
    assert isinstance(episodes_first, Mapping)
    names = list(episodes_first)
    lines = [
        "\n### Crisis episodes: arm cumulative return % (offset against reference, pp); "
        "* marks partial coverage, n/c not covered\n",
        "| arm | " + " | ".join(names) + " |",
        "| --- | " + " | ".join("---:" for _ in names) + " |",
    ]
    for name, d in descriptives.items():
        episodes = d["episodes"]
        assert isinstance(episodes, Mapping)
        cells = []
        for episode_name in names:
            e = episodes[episode_name]
            assert isinstance(e, Mapping)
            if not e.get("covered"):
                cells.append("n/c")
                continue
            star = "*" if e.get("partial") else ""
            offset = e.get("offset_vs_reference_pp")
            cells.append(
                f"{e['arm_cumulative_pct']}{star} "
                f"({_fmt(float(offset) if isinstance(offset, int | float) else None)})"
            )
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")
    return lines


def _regime_table(regime: Sequence[Mapping[str, JsonValue]]) -> list[str]:
    lines = [
        "\n### The ten-year leg by era (its realised history, to haircut against)\n",
        "| era | window | months | ten-year/equity corr | ten-year excess pp/yr | ten-year vol % | "
        "long bond excess pp/yr | equity excess pp/yr | trend excess pp/yr | cash pp/yr |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in regime:
        lines.append(
            f"| {r['era']} | {r['window']} | {r['months']} | {r['tenyear_equity_correlation']} | "
            f"{r['tenyear_excess_pp_yr']} | {r['tenyear_volatility_pct']} | "
            f"{r['long_bond_excess_pp_yr']} | {r['equity_excess_pp_yr']} | "
            f"{r['trend_excess_pp_yr']} | {r['cash_pp_yr']} |"
        )
    return lines


def _financing_table(financing: Mapping[str, JsonValue]) -> list[str]:
    grid_raw = financing["grid_basis_points"]
    assert isinstance(grid_raw, Sequence)
    grid = [str(int(float(str(g)))) for g in grid_raw]
    lines = [
        "\n### Financing sensitivity: gap against the reference arm at each equity basis (bp), "
        "then against the cheap control\n",
        "ordering against reference stable across the band: "
        f"`{financing['ordering_against_reference_stable']}`\n",
        "| arm | " + " | ".join(grid) + " | vs cheap at each point |",
        "| --- | " + " | ".join("---:" for _ in grid) + " | --- |",
    ]
    gaps = financing["gaps_pp_yr"]
    assert isinstance(gaps, Mapping)
    for name, by_control in gaps.items():
        assert isinstance(by_control, Mapping)
        ref = by_control.get("reference")
        cheap = by_control.get("cheap")
        ref_cells = (
            " | ".join(_fmt(float(str(v))) for v in ref)
            if isinstance(ref, Sequence)
            else " | ".join("--" for _ in grid)
        )
        cheap_cells = (
            ", ".join(_fmt(float(str(v))) for v in cheap) if isinstance(cheap, Sequence) else "--"
        )
        lines.append(f"| `{name}` | {ref_cells} | {cheap_cells} |")
    return lines


def _regret_markdown(regret: Mapping[str, JsonValue]) -> list[str]:
    rows = regret["rows"]
    assert isinstance(rows, Sequence)
    first = rows[0]
    assert isinstance(first, Mapping)
    cells0 = first["cells"]
    assert isinstance(cells0, Sequence)
    equity = [str(c["equity_premium_over_bonds_pp_yr"]) for c in cells0 if isinstance(c, Mapping)]
    lines = [
        "\n### Regret at forward premia: working default minus published, pp/yr, arithmetic / log "
        "(positive means the working default wins)\n",
        f"Bond excess over cash {regret['bond_excess_over_cash_pp_yr']} pp/yr; variance-drag "
        f"constant {regret['variance_drag_pp_yr']} pp/yr added to every log cell.\n",
        "| gross trend premium pp/yr | "
        + " | ".join(f"equity over bonds {e}" for e in equity)
        + " |",
        "| --- | " + " | ".join("---:" for _ in equity) + " |",
    ]
    for row in rows:
        assert isinstance(row, Mapping)
        cells = row["cells"]
        assert isinstance(cells, Sequence)
        label = f"{row['trend_gross_pp_yr']}" + (" (central)" if row["central"] else "")
        lines.append(
            f"| {label} | "
            + " | ".join(
                f"{_fmt(float(str(c['arithmetic_gap_pp_yr'])))} / "
                f"{_fmt(float(str(c['log_growth_gap_pp_yr'])))}"
                for c in cells
                if isinstance(c, Mapping)
            )
            + " |"
        )
    lines.append("\nBreak-even gross trend premium (the working default wins below it):\n")
    lines.append("| equity over bonds pp/yr | arithmetic | log |")
    lines.append("| ---: | ---: | ---: |")
    breaks = regret["break_even_trend_premium_by_equity_premium"]
    assert isinstance(breaks, Sequence)
    for b in breaks:
        assert isinstance(b, Mapping)
        lines.append(
            f"| {b['equity_premium_over_bonds_pp_yr']} | "
            f"{b['arithmetic_break_even_trend_pp_yr']} | "
            f"{b['log_break_even_trend_pp_yr']} |"
        )
    return lines


def render_tables(
    primary: PanelResult,
    tournament: TournamentResult,
    regret: Mapping[str, JsonValue],
    *,
    header: Sequence[str],
) -> str:
    lines: list[str] = list(header)
    p = primary.panel
    lines.append(
        f"\n## Panel `primary`: {p.periods[0]}..{p.periods[-1]}, {p.months} months, "
        "own trend book, "
        "monthly rebalancing\n"
    )
    lines.extend(_arm_table(primary.arms, primary.descriptives))
    lines.extend(
        _gap_table(
            primary.comparisons,
            [
                "reference",
                "cheap",
                "leverage_matched",
                "volatility_matched_expost",
                "volatility_matched_exante",
                "mix85",
            ],
        )
    )
    window_names = [w[0] for w in primary.windows]
    lines.extend(_window_table(primary.comparisons, control="reference", windows=window_names))
    lines.extend(_window_table(primary.comparisons, control="cheap", windows=window_names))
    lines.extend(_crisis_table(primary.descriptives))
    lines.extend(_episode_table(primary.descriptives))
    lines.extend(_regime_table(primary.regime))
    if primary.financing:
        lines.extend(_financing_table(primary.financing))
    lines.extend(_regret_markdown(regret))
    t = tournament.inputs.panel
    lines.append(
        f"\n## Panel `tournament_1990`: {t.periods[0]}..{t.periods[-1]}, {t.months} months, 016f's "
        "basis-mapped funds and AQR TSMOM, annual rebalancing\n"
    )
    lines.append(
        f"Reproduction of 016f's rec30 minus rec25 log gap: observed "
        f"{tournament.reproduction['observed_pp_yr']} against "
        f"{tournament.reproduction['expected_pp_yr']}, "
        f"reproduced `{tournament.reproduction['reproduced']}`.\n"
    )
    lines.extend(_arm_table(tournament.arms, tournament.descriptives))
    lines.extend(_gap_table(tournament.comparisons, ["reference", "cheap", "leverage_matched"]))
    lines.extend(
        _window_table(
            tournament.comparisons, control="reference", windows=[w[0] for w in tournament.windows]
        )
    )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def _panel_json(
    arms: Mapping[str, ArmPaths],
    comparisons: Mapping[str, Mapping[str, Comparison]],
    descriptives: Mapping[str, Mapping[str, JsonValue]],
) -> list[JsonValue]:
    rows: list[JsonValue] = []
    for name, item in arms.items():
        row: dict[str, JsonValue] = {
            "arm": name,
            "role": item.arm.role,
            "note": item.arm.note,
            "weights": {t: w for t, w in zip(item.arm.tickers, item.arm.weights, strict=True)},
        }
        row.update(descriptives[name])
        row["comparisons"] = {
            c: comparison.to_json() for c, comparison in comparisons[name].items()
        }
        rows.append(row)
    return rows


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
    reference = _text(parameters, "reference_arm", where="parameters")
    in_estimates = tuple(
        str(x)
        for x in _sequence(_at(parameters, "controls_in_estimates", where="parameters"), where="c")
    )
    findings = list(raw.findings)

    book_block = _mapping(_at(parameters, "trend_book", where="parameters"), where="trend_book")
    expected_scalar = _number(book_block, "expected_scalar_from_exp_018", where="trend_book")
    scalar_matches = abs(legs.trend_scalar - expected_scalar) < 5e-4
    if not scalar_matches:
        findings.append(
            f"trend-book scalar {legs.trend_scalar:.4f} does not reproduce 018's {expected_scalar}"
        )

    panel = build_primary_panel(legs)
    primary = score_primary(
        panel,
        specification=specification,
        arms=arms,
        wrappers=wrappers,
        rates=rates,
        rng=context.rng,
        full=True,
    )
    inputs = load_tournament_inputs(specification, legs)
    tournament = score_tournament(inputs, specification=specification, rng=context.rng, full=True)
    findings.extend(inputs.findings)
    if not tournament.reproduction["reproduced"]:
        findings.append(
            "016f's rec30 minus rec25 log gap did NOT reproduce: "
            f"{tournament.reproduction['observed_pp_yr']} against "
            f"{tournament.reproduction['expected_pp_yr']}"
        )

    working = primary.arms["working_default"].path.total
    published = primary.arms[reference].path.total
    drag = (
        -0.5 * (_volatility(working) ** 2 - _volatility(published) ** 2) * MONTHS_PER_YEAR * 100.0
    )
    regret = regret_table(specification, variance_drag_pp_yr=drag)

    # Estimates and the verdict.
    estimates: list[Estimate] = []
    resolved: list[str] = []
    scored = 0
    panels: list[tuple[str, Mapping[str, Mapping[str, Comparison]], tuple[str, ...]]] = [
        ("primary", primary.comparisons, in_estimates),
        ("tournament_1990", tournament.comparisons, ("reference", "cheap", "leverage_matched")),
    ]
    method = (
        "stationary block bootstrap on the joint panel, whole rows, mean block 12 months, "
        f"{specification.inference.resamples} resamples, 95% percentile; HAC interval in the notes"
    )
    for panel_id, by_arm, wanted in panels:
        for name, by_control in by_arm.items():
            for control, comparison in by_control.items():
                g, f = comparison.gap, comparison.full
                if g is None or f is None or comparison.identical:
                    continue
                if comparison.status == "exploratory":
                    resolved.append(f"{panel_id}:{name} vs {control}")
                if control not in wanted:
                    continue
                scored += 1
                label = f"{panel_id}:{name} vs {control}"
                estimates.append(
                    Estimate(
                        name=f"arithmetic_gap[{label}]",
                        value=g.gap_pp_yr,
                        units="percentage points per year",
                        interval=g.interval,
                        interval_method=method,
                        cost_basis=CostBasis.NET_PESSIMISTIC,
                        n_obs=g.months,
                        notes=(
                            f"{comparison.status}: {comparison.clause}. HAC 95% "
                            f"[{f.hac_interval[0]:+.3f}, {f.hac_interval[1]:+.3f}] at "
                            f"{f.hac_lags} lags; "
                            f"log-growth gap {f.log_growth_gap_pp_yr:+.3f}; tracking error "
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
                            "a detection floor is a property of the design, not an estimate of a "
                            "quantity in the world, so it carries no interval"
                        ),
                    )
                )
    status = ResultStatus.EXPLORATORY if resolved else ResultStatus.UNRESOLVED

    pair = primary.comparisons["working_default"]["reference"]
    pair_t = tournament.comparisons["working_default"]["reference"]
    assert pair.gap is not None and pair.full is not None
    assert pair_t.gap is not None and pair_t.full is not None
    cash_pair = primary.comparisons["trend25_cash5"]["reference"]
    assert cash_pair.gap is not None
    d_w = primary.descriptives["working_default"]
    d_p = primary.descriptives[reference]
    summary = (
        f"The working default against the published construction on the {panel.months}-month "
        f"primary panel: {pair.gap.gap_pp_yr:+.2f} pp/yr arithmetic, bootstrap "
        f"[{pair.gap.interval[0]:+.2f}, {pair.gap.interval[1]:+.2f}], HAC "
        f"[{pair.full.hac_interval[0]:+.2f}, {pair.full.hac_interval[1]:+.2f}], floor "
        f"{pair.gap.mde_pp_yr:.2f}, log-growth gap {pair.full.log_growth_gap_pp_yr:+.2f}, "
        f"`{pair.status}`. On 016f's {inputs.panel.months}-month panel: "
        f"{pair_t.gap.gap_pp_yr:+.2f} "
        f"[{pair_t.gap.interval[0]:+.2f}, {pair_t.gap.interval[1]:+.2f}], floor "
        f"{pair_t.gap.mde_pp_yr:.2f}, `{pair_t.status}`. The wrapper cut alone (cash arm) reads "
        f"{cash_pair.gap.gap_pp_yr:+.2f}. Maximum drawdown {d_w['max_drawdown_pct']}% against "
        f"{d_p['max_drawdown_pct']}%; months under water {d_w['time_under_water_months']} against "
        f"{d_p['time_under_water_months']}. {scored} comparisons scored on two panels; "
        f"{len(resolved)} separate from their control by more than the design can resolve. "
        "Drawdown, episode and terminal-wealth tables are descriptive and carry no "
        "significance claim."
    )
    freeze_note = (
        "WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS; the tournament panel's "
        "tickers are 016f's basis expressions. THE TIPS LINE IS A NOMINAL TEN-YEAR TREASURY "
        "modelled as a rolled par bond on FRED GS10 from 1953-04 and Shiller's long rate "
        "before it, because no TIPS series "
        "exists before 2003; reading it as TIPS assumes the real bond's excess, volatility and "
        "equity correlation resemble the nominal bond's, which is false in 1970-81 in the "
        "direction that flatters the nominal line's inflation-episode losses. The trend leg is "
        "the repository's own 4-asset book scaled by one full-window constant and charged no "
        "trading; AQR's TSMOM on the tournament panel is gross of the vendor's trading costs. "
        "The primary pair was predicted `rejected` before the run as a leverage result at "
        "realised premia; the forward reading is the regret table."
    )
    header = [
        "# Experiment 024: the working default scored as one object",
        "",
        f"Run `{context.run_id}`; specification hash `{specification.spec_hash}`.",
        "",
        freeze_note,
        "",
        f"Trend-book volatility scalar {legs.trend_scalar:.4f} (realised "
        f"{legs.trend_book_realised_volatility_pct:.2f}% on {legs.trend_book_window[0]}.."
        f"{legs.trend_book_window[1]}, target 12.38%; 018's {expected_scalar}, reproduced "
        f"`{scalar_matches}`). Shiller long rate against FRED GS10 on "
        f"{legs.yield_cross_check_months} "
        f"overlapping months: largest difference {legs.yield_cross_check_max_bp:.2f} bp.",
        "",
        "Gap cells read: point estimate, bootstrap and HAC 95% intervals, MDE at 80% power, "
        "log-growth gap, years to distinguish, falsifier status. Descriptive tables carry no "
        "status.",
    ]
    tables = render_tables(primary, tournament, regret, header=header)

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in raw.provenance],
        "source_findings": findings,
        "trend_book": {
            "scalar": round(legs.trend_scalar, 6),
            "expected_from_exp_018": expected_scalar,
            "reproduced": scalar_matches,
            "realised_volatility_pct_on_primary_window": round(
                legs.trend_book_realised_volatility_pct, 4
            ),
            "primary_window": list(legs.trend_book_window),
        },
        "ten_year_leg": {
            "cross_check_overlap_months": legs.yield_cross_check_months,
            "largest_yield_difference_bp": _round(legs.yield_cross_check_max_bp, 3),
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
        "panels": [
            {
                "id": "primary",
                "window": f"{panel.periods[0]}..{panel.periods[-1]}",
                "months": panel.months,
                "panel_findings": list(panel.findings),
                "arms": _panel_json(primary.arms, primary.comparisons, primary.descriptives),
                "ten_year_regime_by_era": list(primary.regime),
                "financing_sensitivity": primary.financing,
                "multiple_testing_families": {k: sorted(v) for k, v in primary.families.items()},
            },
            {
                "id": "tournament_1990",
                "window": f"{inputs.panel.periods[0]}..{inputs.panel.periods[-1]}",
                "months": inputs.panel.months,
                "exp_016f_specification_hash": inputs.specification_hash,
                "panel_findings": list(inputs.findings),
                "reproduction": tournament.reproduction,
                "arms": _panel_json(
                    tournament.arms, tournament.comparisons, tournament.descriptives
                ),
                "multiple_testing_families": {k: sorted(v) for k, v in tournament.families.items()},
            },
        ],
        "primary_pair": {
            "panel": "primary",
            "arm": "working_default",
            "control": "reference",
            **pair.to_json(),
        },
        "regret": regret,
        "resolved_comparisons": resolved,
        "markdown_tables": tables,
    }
    caveats = (
        "Wrappers are assumed exposure vectors; the tournament tickers are 016f's basis "
        "expressions. This ranks constructions and cannot rank funds.",
        "The TIPS line is a nominal ten-year Treasury modelled as a rolled par bond; no TIPS "
        "series exists before 2003. Read the 1970-81 episodes with that in mind.",
        "The own 4-asset trend book is scaled by one full-window constant and charged no "
        "trading cost; AQR's TSMOM is gross of the vendor's trading costs by omission.",
        "The primary pair's sign is a leverage result at realised premia; the regret table is "
        "the forward reading and it is arithmetic on assumed premia, not a measurement.",
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
        if isinstance(location, str) and location.startswith("data-manifests/"):
            path = workspace_root() / location
            if path.is_file():
                out.append(read_manifest(path).sha256_manifest())
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_024_working_default",
        description="Score the working default as one object against the published construction.",
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
