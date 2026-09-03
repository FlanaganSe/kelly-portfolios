"""Experiment 025: cautious constructions scored as objects.

What this is
------------
The site's self-test tells a reader who could not sit through a fall of about
30% or 40% to hold fewer stocks and more bonds, and names no construction. The
repository holds the equity-share table, the notional ladder and a 10-point
substitution beside a 30% wrapper, on three different panels; nothing with a
bond line above 10 points has ever been scored as one object. This module scores
six cautious arms (two plain mixes, two trend arms at matched equity, the
notional ladder's -40% and -30% rows applied whole, each with a plain twin) on
024's 1929-2025 primary panel, on 016f's 1990-11 fund-list panel with the tilt
book scaled to each arm's equity, and, as a descriptive check, from 2003-02 with
018's modelled TIPS leg in place of the nominal ten-year.

The three primary comparisons are the paired differences trend arm minus plain
twin at matched equity. Drawdown by panel and by era is the reason the file
exists and carries no status.

What this is NOT
----------------
**It does not score funds.** Every holding is an assumed per-dollar exposure
vector and a fee, or 016f's basis expression.

**The bond line is a nominal ten-year Treasury on both scored panels.** No TIPS
series exists before 2003; freeze note 3 of the specification says what reading
it as TIPS assumes at 40 to 63 points of capital.

Run it::

    uv run python -m portfolio_edge.experiments.exp_025_cautious_constructions --view-results
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
from portfolio_edge.data import fred
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MONTHS_PER_YEAR,
    BasisPanel,
    CostSettings,
    FundMapping,
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
    workspace_root,
)
from portfolio_edge.experiments.exp_016_construction_tournament import (
    _cost_settings as _tournament_costs,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    FinancingRates,
    Wrapper,
    _era_windows,
    _require_cached,
    _slice,
    read_episodes,
    read_rates,
    simulate_arm,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    _cost_settings as _engine_costs,
)
from portfolio_edge.experiments.exp_024_working_default import (
    Arm,
    ArmPaths,
    Comparison,
    Legs,
    Notional,
    RawSeries,
    _apply_falsifier,
    _arm_table,
    _bond_regime,
    _compare,
    _crisis_table,
    _describe,
    _episode_table,
    _financing_table,
    _gap_table,
    _manifest_hashes,
    _panel_json,
    _point_gaps,
    _read_weighted,
    _regime_table,
    _round,
    _volatility,
    _window_table,
    build_primary_panel,
    read_arms,
    window_statistics,
)
from portfolio_edge.experiments.exp_024_working_default import (
    build_legs as build_core_legs,
)
from portfolio_edge.experiments.exp_024_working_default import (
    load_series as load_core_series,
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
from portfolio_edge.studies.fixed_income_shelf import (
    par_bond_total_returns,
    tips_nominal_total_return,
)

FloatArray = NDArray[np.float64]
MonthSeries = dict[str, float]

ENTRY_POINT: Final = "exp_025_cautious_constructions"

#: The legs a wrapper may name. ``tips`` exists on the check panel only.
LEGS: Final = ("equity", "treasury", "tsy10", "tips", "trend")
BOND_LEGS: Final = frozenset({"treasury", "tsy10", "tips"})

__all__ = [
    "ENTRY_POINT",
    "LEGS",
    "CautiousConstructionsError",
    "CautiousLegs",
    "arm_notional",
    "build_registry",
    "default_specification_path",
    "drawdown_by_era",
    "leverage_matched_targets",
    "main",
    "pair_regret_pp_yr",
    "plain_regret_pp_yr",
    "read_arms",
    "read_pairs",
    "read_wrappers",
    "run",
    "tolerance_reading",
]


class CautiousConstructionsError(Exception):
    """The experiment refused to run, or an input did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_025_cautious_constructions.yaml"


# --------------------------------------------------------------------------- #
# Wrappers, arms, pairs, notional
# --------------------------------------------------------------------------- #


def read_wrappers(specification: Specification) -> dict[str, Wrapper]:
    """024's reader with the ``tips`` leg admitted."""
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
                raise CautiousConstructionsError(f"wrappers.{ticker} names unknown leg {leg!r}")
        out[ticker] = Wrapper(
            ticker=ticker,
            exposures={leg: _number(exposures, leg, where="exposures") for leg in exposures},
            fee_bp=_number(fees, ticker, where="cost_model.wrapper_expense_ratio_basis_points"),
            financed={leg: _number(financed, leg, where="financed") for leg in financed},
            note=str(entry.get("note") or ""),
        )
    return out


def arm_notional(
    tickers: Sequence[str], weights: Sequence[float], wrappers: Mapping[str, Wrapper]
) -> Notional:
    """Capital weights times per-dollar exposures, leg by leg; every bond leg is notional."""
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


def read_pairs(specification: Specification) -> tuple[dict[str, str], dict[str, str]]:
    """``(primary, secondary)`` maps from trend arm to its plain twin."""
    parameters = _mapping(specification.parameters, where="parameters")
    out: list[dict[str, str]] = []
    for key in ("primary_pairs", "secondary_pairs"):
        pairs: dict[str, str] = {}
        for item in _sequence(_at(parameters, key, where="parameters"), where=key):
            entry = _mapping(item, where=f"{key}[]")
            pairs[_text(entry, "arm", where=key)] = _text(entry, "twin", where=key)
        out.append(pairs)
    return out[0], out[1]


def leverage_matched_targets(gross: float) -> tuple[tuple[str, ...], FloatArray]:
    """The core levered to ``gross`` above one, or scaled to it with bills below one."""
    if gross > 1.0:
        return ("CORE",), np.array([gross], dtype=np.float64)
    return ("CORE", "CASH"), np.array([gross, 1.0 - gross], dtype=np.float64)


# --------------------------------------------------------------------------- #
# Series and legs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class CautiousLegs:
    """024's legs plus 018's modelled TIPS leg, for the check panel."""

    core: Legs
    tips: MonthSeries
    tips_provenance: tuple[Mapping[str, JsonValue], ...]
    tips_findings: tuple[str, ...]


def _pin(specification: Specification, file_id: str) -> Mapping[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    for item in _sequence(_at(block, "files", where="source_pin"), where="source_pin.files"):
        pin = _mapping(item, where="source_pin.files[]")
        if _text(pin, "id", where="source_pin.files[]") == file_id:
            return pin
    raise CautiousConstructionsError(f"source_pin.files has no entry {file_id!r}")


def _column(periods: Sequence[str], values: Sequence[float | None]) -> MonthSeries:
    return {p[:7]: float(v) for p, v in zip(periods, values, strict=True) if v is not None}


def load_series(
    specification: Specification,
) -> tuple[
    RawSeries, MonthSeries, MonthSeries, tuple[Mapping[str, JsonValue], ...], tuple[str, ...]
]:
    """024's five pinned sources, then FII10 and CPI-U by digest; never download."""
    raw = load_core_series(specification)
    cache = RawCache()
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []
    out: dict[str, MonthSeries] = {}
    for file_id, series_id in (("fred_fii10", "FII10"), ("fred_cpiaucns", "CPIAUCNS")):
        url = fred.series_url(series_id)
        entry, record = _require_cached(cache, url, _pin(specification, file_id))
        if record["index_superseded_by_sha256"] is not None:
            findings.append(
                f"{file_id}: the cache index now points at {record['index_superseded_by_sha256']}; "
                f"the pinned blob {record['sha256_raw']} was read by digest instead."
            )
        table = fred.parse(cache, entry, series_id)
        out[series_id] = _column(table.periods, table.column(series_id))
        record["first_observation"], record["last_observation"] = (
            min(out[series_id]),
            max(out[series_id]),
        )
        provenance.append(record)
    return raw, out["FII10"], out["CPIAUCNS"], tuple(provenance), tuple(findings)


def build_legs(
    raw: RawSeries,
    fii10_yield: MonthSeries,
    cpi: MonthSeries,
    specification: Specification,
    *,
    provenance: tuple[Mapping[str, JsonValue], ...] = (),
    findings: tuple[str, ...] = (),
) -> CautiousLegs:
    """024's legs; the TIPS leg exactly as 018 builds it."""
    core = build_core_legs(raw, specification)
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "tips_leg", where="parameters"), where="tips_leg")
    maturity = _number(block, "maturity_years", where="tips_leg")
    lag = int(_number(block, "cpi_lag_months", where="tips_leg"))
    real = par_bond_total_returns(fii10_yield, maturity_years=maturity)
    nominal = tips_nominal_total_return(real, cpi, lag_months=lag)
    tips = {p: nominal[p] - raw.cash[p] for p in nominal if p in raw.cash}
    return CautiousLegs(core=core, tips=tips, tips_provenance=provenance, tips_findings=findings)


def build_check_panel(legs: CautiousLegs, *, start: str) -> BasisPanel:
    """Every primary leg plus ``tips``, intersected, from ``start``."""
    core = legs.core
    common = (
        set(core.cash)
        & set(core.equity)
        & set(core.treasury)
        & set(core.tsy10)
        & set(core.trend)
        & set(legs.tips)
    )
    periods = sorted(p for p in common if month_index(p) >= month_index(start))
    if len(periods) < 3 * MONTHS_PER_YEAR:
        raise CautiousConstructionsError(f"the check panel holds {len(periods)} months")
    for earlier, later in itertools.pairwise(periods):
        if month_index(later) - month_index(earlier) != 1:
            raise CautiousConstructionsError(f"the check panel has a gap at {earlier}..{later}")
    series = {
        "equity": core.equity,
        "treasury": core.treasury,
        "tsy10": core.tsy10,
        "tips": legs.tips,
        "trend": core.trend,
    }
    return BasisPanel(
        periods=tuple(periods),
        series={n: np.array([s[p] for p in periods], dtype=np.float64) for n, s in series.items()},
        cash=np.array([core.cash[p] for p in periods], dtype=np.float64),
        provenance=(),
        findings=(f"check panel: {len(periods)} months, {periods[0]}..{periods[-1]}",),
    )


# --------------------------------------------------------------------------- #
# The primary panel: arms, controls, plain twins
# --------------------------------------------------------------------------- #


def simulate_panel(
    panel: BasisPanel,
    *,
    arms: Mapping[str, Arm],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    costs: CostSettings,
    reference: str,
    twins: Mapping[str, str],
    window: int,
) -> dict[str, ArmPaths]:
    """Every arm with cheap, leverage-, volatility-matched, plain-twin and reference controls."""
    cheap = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.0]))
    core_total = cheap.total
    paths: dict[str, PortfolioPath] = {}
    for name, arm in arms.items():
        paths[name] = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=arm.tickers,
            targets=np.asarray(arm.weights, dtype=np.float64),
        )
    if reference not in paths:
        raise CautiousConstructionsError(f"reference arm {reference!r} is not a contestant")
    for name, twin in twins.items():
        if name not in paths or twin not in paths:
            raise CautiousConstructionsError(f"pair {name} / {twin} names an unknown arm")

    out: dict[str, ArmPaths] = {}
    for name, arm in arms.items():
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        path = paths[name]
        controls: dict[str, PortfolioPath] = {"cheap": cheap}
        first: dict[str, int] = {"cheap": 0}
        definition: dict[str, str] = {"cheap": "100% CORE"}

        if name in twins:
            controls["plain_twin"] = paths[twins[name]]
            first["plain_twin"] = 0
            definition["plain_twin"] = f"the {twins[name]} arm, the same equity with no trend line"

        tickers, targets = leverage_matched_targets(notional.gross)
        controls["leverage_matched"] = simulate_arm(
            panel, wrappers, rates, costs, tickers=tickers, targets=targets
        )
        first["leverage_matched"] = 0
        definition["leverage_matched"] = (
            f"{notional.gross:.4f} x CORE, financed at the equity basis"
            if notional.gross > 1.0
            else f"{notional.gross:.4f} x CORE + {1.0 - notional.gross:.4f} x CASH"
        )

        scale = _volatility(path.total) / _volatility(core_total)
        v_tickers, v_targets = leverage_matched_targets(scale)
        controls["volatility_matched_expost"] = simulate_arm(
            panel, wrappers, rates, costs, tickers=v_tickers, targets=v_targets
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
        if name != reference:
            controls["reference"] = paths[reference]
            first["reference"] = 0
            definition["reference"] = f"the {reference} arm"
        out[name] = ArmPaths(
            arm=arm,
            notional=notional,
            path=path,
            controls=controls,
            control_first_month=first,
            control_definition=definition,
        )
    return out


# --------------------------------------------------------------------------- #
# Drawdown by era: the reason the file exists
# --------------------------------------------------------------------------- #


def drawdown_by_era(
    totals: Mapping[str, FloatArray],
    *,
    periods: Sequence[str],
    eras: Sequence[tuple[str, str, str]],
) -> list[dict[str, JsonValue]]:
    """Worst fall and months under water per arm, per era, each era started fresh."""
    out: list[dict[str, JsonValue]] = []
    for era_name, start, end in eras:
        keep = _slice(periods, start, end)
        if keep.size < MONTHS_PER_YEAR:
            continue
        rows: dict[str, JsonValue] = {}
        for name, total in totals.items():
            summary = drawdown_summary(np.cumprod(1.0 + total[keep]))
            rows[name] = {
                "max_drawdown_pct": _round(summary.max_drawdown * 100.0, 2),
                "time_under_water_months": summary.max_time_under_water,
                "growth_log_pp_yr": _round(annualised_log_growth(total[keep])),
            }
        out.append(
            {
                "era": era_name,
                "window": f"{periods[int(keep[0])]}..{periods[int(keep[-1])]}",
                "months": int(keep.size),
                "arms": rows,
            }
        )
    return out


def tolerance_reading(
    drawdowns: Mapping[str, float], tolerances: Sequence[float]
) -> dict[str, JsonValue]:
    """For each tolerance, the arm whose worst fall is closest to it without exceeding it."""
    out: dict[str, JsonValue] = {}
    for tolerance in tolerances:
        within = {n: d for n, d in drawdowns.items() if d >= tolerance}
        if not within:
            out[f"{tolerance:.0f}"] = None
            continue
        chosen = min(within, key=lambda n: within[n])
        out[f"{tolerance:.0f}"] = {"arm": chosen, "max_drawdown_pct": _round(within[chosen], 2)}
    return out


def _era_specs(
    specification: Specification, periods: Sequence[str], *, wanted: Sequence[str]
) -> list[tuple[str, str, str]]:
    windows = [("full", periods[0], periods[-1])]
    declared = {e.name: (e.start, e.end) for e in specification.sample_policy.eras}
    for name in wanted:
        if name == "full":
            continue
        if name not in declared:
            raise CautiousConstructionsError(f"drawdown era {name!r} is not a declared era")
        start, end = declared[name]
        keep = _slice(periods, start, end)
        if keep.size >= MONTHS_PER_YEAR:
            windows.append((name, periods[int(keep[0])], periods[int(keep[-1])]))
    return windows


# --------------------------------------------------------------------------- #
# Scoring the primary panel
# --------------------------------------------------------------------------- #


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
    drawdown_eras: list[dict[str, JsonValue]]


def score_primary(
    panel: BasisPanel,
    *,
    specification: Specification,
    arms: Mapping[str, Arm],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    twins: Mapping[str, str],
    rng: np.random.Generator,
    full: bool,
) -> PanelResult:
    parameters = _mapping(specification.parameters, where="parameters")
    reference = _text(parameters, "reference_arm", where="parameters")
    contribution = _number(parameters, "contribution_per_month_of_starting_balance", where="p")
    tail = _number(parameters, "tail_quantile", where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")
    window = int(_number(parameters, "volatility_match_window_months", where="parameters"))
    costs = _engine_costs(specification, rates)
    simulated = simulate_panel(
        panel,
        arms=arms,
        wrappers=wrappers,
        rates=rates,
        costs=costs,
        reference=reference,
        twins=twins,
        window=window,
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
                simulate_panel(
                    panel,
                    arms=arms,
                    wrappers=wrappers,
                    rates=shifted,
                    costs=_engine_costs(specification, shifted),
                    reference=reference,
                    twins=twins,
                    window=window,
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
        pair_signs: dict[str, JsonValue] = {}
        for name in twins:
            values: list[float] = per_point.get(name, {}).get("plain_twin") or []
            pair_signs[name] = {
                "gaps_pp_yr": [_round(v) for v in values],
                "sign_stable": bool(values) and all((v > 0.0) == (values[0] > 0.0) for v in values),
            }
        financing = {
            "grid_basis_points": list(grid),
            "gaps_pp_yr": {
                n: {c: [_round(v) for v in vs] for c, vs in by_control.items()}
                for n, by_control in per_point.items()
            },
            "ordering_against_reference_by_point": ordering,
            "ordering_against_reference_stable": all(o == ordering[0] for o in ordering),
            "trend_arm_against_plain_twin_by_point": pair_signs,
        }
        for name in arms:
            for control, comparison in comparisons[name].items():
                band = per_point.get(name, {}).get(control)
                if band:
                    comparison.financing_band_range = (min(band), max(band))

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
    reporting = _mapping(
        _at(parameters, "drawdown_reporting", where="parameters"), where="drawdown_reporting"
    )
    wanted = [
        str(x)
        for x in _sequence(
            _at(reporting, "eras_for_drawdown_table", where="drawdown_reporting"), where="eras"
        )
    ]
    tolerances = _numbers(
        _at(reporting, "tolerance_rows_pct", where="drawdown_reporting"), where="tolerances"
    )
    eras = _era_specs(specification, panel.periods, wanted=wanted)
    totals = {n: item.path.total for n, item in simulated.items()}
    totals["control_cheap"] = simulated[reference].controls["cheap"].total
    drawdown_eras = drawdown_by_era(totals, periods=panel.periods, eras=eras)
    for row in drawdown_eras:
        arms_block = row["arms"]
        assert isinstance(arms_block, Mapping)
        falls = {
            n: float(str(v["max_drawdown_pct"]))
            for n, v in arms_block.items()
            if isinstance(v, Mapping) and v["max_drawdown_pct"] is not None
        }
        row["tolerance_reading"] = tolerance_reading(falls, tolerances)
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
        drawdown_eras=drawdown_eras,
    )


# --------------------------------------------------------------------------- #
# The check panel: nominal ten-year against modelled TIPS, 2003-02 onward
# --------------------------------------------------------------------------- #


def score_check_panel(
    panel: BasisPanel,
    *,
    specification: Specification,
    arms: Mapping[str, Arm],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
) -> dict[str, JsonValue]:
    """Every check-panel arm twice, ``TSY10`` and ``TIPS`` in the bond line. Descriptive."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "check_panel", where="parameters"), where="check_panel")
    names = [str(x) for x in _sequence(_at(block, "arms", where="check_panel"), where="arms")]
    costs = _engine_costs(specification, rates)
    episodes = {e.name: (e.start, e.end) for e in read_episodes(specification)}
    rate_shock = episodes.get("rate_shock_2022")
    rows: dict[str, JsonValue] = {}
    totals_nominal: dict[str, FloatArray] = {}
    totals_tips: dict[str, FloatArray] = {}
    for name in names:
        if name not in arms:
            raise CautiousConstructionsError(f"check_panel.arms names unknown arm {name!r}")
        arm = arms[name]
        nominal = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=arm.tickers,
            targets=np.asarray(arm.weights, dtype=np.float64),
        )
        substituted = tuple("TIPS" if t == "TSY10" else t for t in arm.tickers)
        real = simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=substituted,
            targets=np.asarray(arm.weights, dtype=np.float64),
        )
        totals_nominal[name] = nominal.total
        totals_tips[name] = real.total
        identical = substituted == tuple(arm.tickers)

        def describe(path: PortfolioPath) -> dict[str, JsonValue]:
            summary = drawdown_summary(np.cumprod(1.0 + path.total))
            row: dict[str, JsonValue] = {
                "arithmetic_mean_pp_yr": _round(float(np.mean(path.total)) * MONTHS_PER_YEAR * 100),
                "growth_log_pp_yr": _round(annualised_log_growth(path.total)),
                "volatility_pct": _round(
                    _volatility(path.total) * math.sqrt(MONTHS_PER_YEAR) * 100
                ),
                "max_drawdown_pct": _round(summary.max_drawdown * 100.0, 2),
                "time_under_water_months": summary.max_time_under_water,
            }
            if rate_shock is not None:
                keep = _slice(panel.periods, *rate_shock)
                if keep.size:
                    row["rate_shock_2022_cumulative_pct"] = _round(
                        (float(np.prod(1.0 + path.total[keep])) - 1.0) * 100.0, 2
                    )
            return row

        entry: dict[str, JsonValue] = {
            "bond_line_tsy10": describe(nominal),
            "bond_line_tips": describe(real),
            "identical": identical,
        }
        if not identical:
            stats = window_statistics(real.total, nominal.total, window="check")
            entry["tips_minus_tsy10"] = stats.to_json()
        rows[name] = entry
    eras = _era_specs(specification, panel.periods, wanted=["full"])
    return {
        "window": f"{panel.periods[0]}..{panel.periods[-1]}",
        "months": panel.months,
        "arms": rows,
        "drawdown_by_era_tsy10": drawdown_by_era(totals_nominal, periods=panel.periods, eras=eras),
        "drawdown_by_era_tips": drawdown_by_era(totals_tips, periods=panel.periods, eras=eras),
        "note": (
            "Descriptive; no status. The TIPS leg is 018's modelled FII10 par bond grossed up by "
            "lagged CPI-U; one era of bond-equity correlation."
        ),
    }


# --------------------------------------------------------------------------- #
# The tournament panel: 016f's machinery plus the ten-year line, plain twins
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class TournamentInputs:
    panel: BasisPanel
    mappings: Mapping[str, FundMapping]
    costs: CostSettings
    specification_hash: str
    findings: tuple[str, ...]


def load_tournament_inputs(specification: Specification, legs: Legs) -> TournamentInputs:
    """016f's panel, mapping and costs, hash-checked, with the ten-year leg added (024's splice)."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "tournament_panel", where="parameters"), where="tournament")
    path = workspace_root() / _text(block, "specification_path", where="tournament_panel")
    tournament = load_specification(path)
    expected = _text(block, "expected_specification_hash", where="tournament_panel")
    if tournament.spec_hash != expected:
        raise CautiousConstructionsError(
            f"{path.name} hashes to {tournament.spec_hash}, not the pinned {expected}. The "
            "tournament panel is defined by that file; a new 016f needs a new 025."
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
    if "CASH" not in mappings:
        raise CautiousConstructionsError("016f's mapping has no CASH ticker for sub-unity controls")
    keep = [i for i, p in enumerate(base.periods) if p in legs.tsy10]
    if len(keep) < 3 * MONTHS_PER_YEAR:
        raise CautiousConstructionsError("the ten-year leg covers too little of the tournament")
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


def tournament_notional(
    tickers: Sequence[str], weights: Sequence[float], mappings: Mapping[str, FundMapping]
) -> Notional:
    """024's decomposition on 016f's basis expressions, bonds counted."""
    equity = trend = bond = cash = 0.0
    for ticker, weight in zip(tickers, weights, strict=True):
        held = 0.0
        for name, value in mappings[ticker].coefficients.items():
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


@dataclass(slots=True, kw_only=True)
class TournamentResult:
    inputs: TournamentInputs
    arms: dict[str, ArmPaths]
    comparisons: dict[str, dict[str, Comparison]]
    descriptives: dict[str, dict[str, JsonValue]]
    families: dict[str, list[str]]
    reproduction: dict[str, JsonValue]
    windows: list[tuple[str, str, str]]
    drawdown_eras: list[dict[str, JsonValue]]


def score_tournament(
    inputs: TournamentInputs,
    *,
    specification: Specification,
    twins: Mapping[str, str],
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
    mix_tickers, mix_weights = _read_weighted(
        _mapping(_at(controls_block, "cheap60_40", where="controls"), where="cheap60_40"),
        where="tournament_panel.controls.cheap60_40",
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
    mix = constant_weight_path(
        panel, mappings, costs, tickers=mix_tickers, targets=np.asarray(mix_weights)
    )
    paths = {
        name: constant_weight_path(
            panel, mappings, costs, tickers=arm.tickers, targets=np.asarray(arm.weights)
        )
        for name, arm in arms.items()
    }
    if reference not in paths:
        raise CautiousConstructionsError(f"tournament reference arm {reference!r} is not an arm")
    simulated: dict[str, ArmPaths] = {}
    for name, arm in arms.items():
        notional = tournament_notional(arm.tickers, arm.weights, mappings)
        if notional.gross > 1.0:
            levered = constant_weight_path(
                panel,
                mappings,
                costs,
                tickers=cheap_tickers,
                targets=np.asarray(cheap_weights) * notional.gross,
            )
            levered_definition = (
                f"{notional.gross:.4f} x the cheap control, financed at the equity basis"
            )
        else:
            levered = constant_weight_path(
                panel,
                mappings,
                costs,
                tickers=(*cheap_tickers, "CASH"),
                targets=np.asarray(
                    [*(w * notional.gross for w in cheap_weights), 1.0 - notional.gross]
                ),
            )
            levered_definition = (
                f"{notional.gross:.4f} x the cheap control + {1.0 - notional.gross:.4f} x CASH"
            )
        controls: dict[str, PortfolioPath] = {
            "cheap": cheap,
            "cheap60_40": mix,
            "leverage_matched": levered,
        }
        first = {"cheap": 0, "cheap60_40": 0, "leverage_matched": 0}
        definition = {
            "cheap": "65% VTI + 35% VXUS, unlevered, annual rebalancing",
            "cheap60_40": "39% VTI + 21% VXUS + 40% TSY10, unlevered, annual rebalancing",
            "leverage_matched": levered_definition,
        }
        if name in twins and twins[name] in paths:
            controls["plain_twin"] = paths[twins[name]]
            first["plain_twin"] = 0
            definition["plain_twin"] = f"the {twins[name]} arm, the same equity with no trend line"
        if name != reference:
            controls["reference"] = paths[reference]
            first["reference"] = 0
            definition["reference"] = f"the {reference} arm"
        simulated[name] = ArmPaths(
            arm=arm,
            notional=notional,
            path=paths[name],
            controls=controls,
            control_first_month=first,
            control_definition=definition,
        )

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
    eras = _era_specs(specification, panel.periods, wanted=["full", "from_2003_02"])
    totals = {n: item.path.total for n, item in simulated.items()}
    totals["control_cheap"] = cheap.total
    totals["control_cheap60_40"] = mix.total
    drawdown_eras = drawdown_by_era(totals, periods=panel.periods, eras=eras)
    reporting = _mapping(
        _at(parameters, "drawdown_reporting", where="parameters"), where="drawdown_reporting"
    )
    tolerances = _numbers(
        _at(reporting, "tolerance_rows_pct", where="drawdown_reporting"), where="tolerances"
    )
    for row in drawdown_eras:
        arms_block = row["arms"]
        assert isinstance(arms_block, Mapping)
        falls = {
            n: float(str(v["max_drawdown_pct"]))
            for n, v in arms_block.items()
            if isinstance(v, Mapping) and v["max_drawdown_pct"] is not None
        }
        row["tolerance_reading"] = tolerance_reading(falls, tolerances)
    return TournamentResult(
        inputs=inputs,
        arms=simulated,
        comparisons=comparisons,
        descriptives=descriptives,
        families=families,
        reproduction=reproduction,
        windows=windows,
        drawdown_eras=drawdown_eras,
    )


# --------------------------------------------------------------------------- #
# Regret at forward premia: the two closed forms of parameters.regret
# --------------------------------------------------------------------------- #


def pair_regret_pp_yr(
    *,
    wrapper_weight: float,
    trend_gross_pp_yr: float,
    equity_premium_over_bonds_pp_yr: float,
    wrapper_equity: float,
    wrapper_cost_pp_yr: float,
) -> float:
    """``w x (t - cost + (wrapper_equity - 1) x E)``: trend arm minus plain twin at matched equity.

    The plain twin holds ``(wrapper_equity - 1) x w`` more of the bond line, which
    cancels the wrapper's extra equity against the bond's excess over cash and
    leaves the equity premium over bonds. Positive means the trend arm wins.
    """
    extra_equity = wrapper_equity - 1.0
    return wrapper_weight * (
        trend_gross_pp_yr - wrapper_cost_pp_yr + extra_equity * equity_premium_over_bonds_pp_yr
    )


def plain_regret_pp_yr(
    *, equity_notional: float, equity_premium_over_bonds_pp_yr: float, fee_delta_pp_yr: float
) -> float:
    """``-(1 - e) x E - fee_delta``: a plain arm against the cheap 100%-equity control."""
    return -(1.0 - equity_notional) * equity_premium_over_bonds_pp_yr - fee_delta_pp_yr


def _variance_drag_pp_yr(arm_total: FloatArray, control_total: FloatArray) -> float:
    """Half the difference of realised variances, the constant a log cell adds."""
    return -0.5 * (_volatility(arm_total) ** 2 - _volatility(control_total) ** 2) * 1200.0


def regret_tables(
    specification: Specification,
    *,
    primary: PanelResult,
    twins: Mapping[str, str],
    wrappers: Mapping[str, Wrapper],
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "regret", where="parameters"), where="regret")
    trend_grid = _numbers(_at(block, "trend_gross_premium_grid_pp_yr", where="regret"), where="t")
    equity_grid = _numbers(
        _at(block, "equity_premium_over_bonds_grid_pp_yr", where="regret"), where="e"
    )
    bond = _number(block, "bond_excess_over_cash_pp_yr", where="regret")
    wrapper_equity = _number(block, "wrapper_equity_per_dollar", where="regret")
    wrapper_cost = _number(block, "wrapper_cost_pp_yr", where="regret")
    bond_fee = _number(block, "bond_line_fee_pp_yr", where="regret")
    core_fee = _number(block, "core_fee_pp_yr", where="regret")
    central = _number(block, "trend_central_pp_yr", where="regret")
    extra_equity = wrapper_equity - 1.0

    pairs: list[JsonValue] = []
    for arm_name, twin_name in twins.items():
        item = primary.arms[arm_name]
        w = item.notional.trend
        drag = _variance_drag_pp_yr(item.path.total, primary.arms[twin_name].path.total)
        rows: list[JsonValue] = []
        for t in trend_grid:
            cells: list[JsonValue] = []
            for e in equity_grid:
                arithmetic = pair_regret_pp_yr(
                    wrapper_weight=w,
                    trend_gross_pp_yr=t,
                    equity_premium_over_bonds_pp_yr=e,
                    wrapper_equity=wrapper_equity,
                    wrapper_cost_pp_yr=wrapper_cost,
                )
                cells.append(
                    {
                        "equity_premium_over_bonds_pp_yr": e,
                        "arithmetic_gap_pp_yr": _round(arithmetic, 3),
                        "log_growth_gap_pp_yr": _round(arithmetic + drag, 3),
                    }
                )
            rows.append({"trend_gross_pp_yr": t, "central": t == central, "cells": cells})
        break_even: list[JsonValue] = []
        for e in equity_grid:
            arithmetic_t = wrapper_cost - extra_equity * e
            log_t = arithmetic_t - (drag / w if w > 0.0 else 0.0)
            break_even.append(
                {
                    "equity_premium_over_bonds_pp_yr": e,
                    "arithmetic_break_even_trend_pp_yr": _round(arithmetic_t, 3),
                    "log_break_even_trend_pp_yr": _round(log_t, 3),
                }
            )
        pairs.append(
            {
                "arm": arm_name,
                "twin": twin_name,
                "wrapper_weight": _round(w, 4),
                "variance_drag_pp_yr": _round(drag, 4),
                "rows": rows,
                "break_even_trend_premium_by_equity_premium": break_even,
            }
        )

    plain: list[JsonValue] = []
    cheap_total = next(iter(primary.arms.values())).controls["cheap"].total
    for name, item in primary.arms.items():
        if item.notional.trend > 0.0:
            continue
        fee_delta = (
            sum(
                weight * wrappers[ticker].fee_bp / 100.0
                for ticker, weight in zip(item.arm.tickers, item.arm.weights, strict=True)
            )
            - core_fee
        )
        drag = _variance_drag_pp_yr(item.path.total, cheap_total)
        cells = []
        for e in equity_grid:
            arithmetic = plain_regret_pp_yr(
                equity_notional=item.notional.equity,
                equity_premium_over_bonds_pp_yr=e,
                fee_delta_pp_yr=fee_delta,
            )
            cells.append(
                {
                    "equity_premium_over_bonds_pp_yr": e,
                    "arithmetic_gap_pp_yr": _round(arithmetic, 3),
                    "log_growth_gap_pp_yr": _round(arithmetic + drag, 3),
                }
            )
        plain.append(
            {
                "arm": name,
                "equity_notional": _round(item.notional.equity, 4),
                "fee_delta_pp_yr": _round(fee_delta, 4),
                "variance_drag_pp_yr": _round(drag, 4),
                "cells": cells,
            }
        )
    return {
        "what": str(block.get("what") or ""),
        "bond_excess_over_cash_pp_yr": bond,
        "bond_line_fee_pp_yr": bond_fee,
        "trend_arm_minus_plain_twin": pairs,
        "plain_arm_minus_cheap": plain,
        "note": (
            "Pair cells are trend arm minus plain twin, pp/yr, positive when the trend arm "
            "wins; the log cell adds half the realised variance difference on the primary "
            "panel. Plain cells are the arm minus the cheap 100%-equity control at each equity "
            "premium over bonds: the price of the drawdown if equities beat bonds by that much."
        ),
    }


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #


def _fmt(value: float | None, digits: int = 2) -> str:
    return "--" if value is None else f"{value:+.{digits}f}"


def _drawdown_era_table(rows: Sequence[Mapping[str, JsonValue]], *, title: str) -> list[str]:
    lines = [f"\n### {title}: worst fall % (months under water) per era, each era started fresh\n"]
    if not rows:
        return lines
    first_arms = rows[0]["arms"]
    assert isinstance(first_arms, Mapping)
    names = list(first_arms)
    lines.append(
        "| era | window | "
        + " | ".join(f"`{n}`" for n in names)
        + " | closest arm at -30 / -40 / -50 |"
    )
    lines.append("| --- | --- | " + " | ".join("---:" for _ in names) + " | --- |")
    for row in rows:
        arms = row["arms"]
        assert isinstance(arms, Mapping)
        cells = []
        for n in names:
            v = arms[n]
            assert isinstance(v, Mapping)
            cells.append(f"{v['max_drawdown_pct']} ({v['time_under_water_months']})")
        reading = row.get("tolerance_reading")
        reading_text = "--"
        if isinstance(reading, Mapping):
            parts = []
            for tol, chosen in reading.items():
                parts.append(
                    f"{tol}: none"
                    if not isinstance(chosen, Mapping)
                    else f"{tol}: `{chosen['arm']}` {chosen['max_drawdown_pct']}"
                )
            reading_text = "; ".join(parts)
        lines.append(
            f"| {row['era']} | {row['window']} | " + " | ".join(cells) + f" | {reading_text} |"
        )
    return lines


def _check_table(check: Mapping[str, JsonValue]) -> list[str]:
    arms = check["arms"]
    assert isinstance(arms, Mapping)
    lines = [
        f"\n## Panel `check_2003`: {check['window']}, {check['months']} months, nominal ten-year "
        "against modelled TIPS in the bond line (descriptive, no status)\n",
        "| arm | TSY10: arith / log / vol / max DD (months) / 2022 | TIPS: the same | "
        "TIPS minus TSY10 pp/yr [HAC 95%] MDE |",
        "| --- | --- | --- | --- |",
    ]
    for name, entry in arms.items():
        assert isinstance(entry, Mapping)

        def cell(block: JsonValue) -> str:
            assert isinstance(block, Mapping)
            return (
                f"{block['arithmetic_mean_pp_yr']} / {block['growth_log_pp_yr']} / "
                f"{block['volatility_pct']} / {block['max_drawdown_pct']} "
                f"({block['time_under_water_months']}) / "
                f"{block.get('rate_shock_2022_cumulative_pct', '--')}"
            )

        diff = entry.get("tips_minus_tsy10")
        diff_text = "identical"
        if isinstance(diff, Mapping):
            interval = diff["hac_interval_pp_yr"]
            assert isinstance(interval, Sequence)
            diff_text = (
                f"{diff['gap_pp_yr']} [{interval[0]}, {interval[1]}] "
                f"MDE {diff['mde_80pc_power_pp_yr']}"
            )
        lines.append(
            f"| `{name}` | {cell(entry['bond_line_tsy10'])} | {cell(entry['bond_line_tips'])} | "
            f"{diff_text} |"
        )
    return lines


def _regret_markdown(regret: Mapping[str, JsonValue]) -> list[str]:
    lines = [
        "\n### Regret at forward premia, trend arm minus plain twin, pp/yr, arithmetic / log "
        "(positive means the trend arm wins)\n",
        f"Bond excess over cash {regret['bond_excess_over_cash_pp_yr']} pp/yr "
        "(cancels inside the pair).\n",
    ]
    pairs = regret["trend_arm_minus_plain_twin"]
    assert isinstance(pairs, Sequence)
    for pair in pairs:
        assert isinstance(pair, Mapping)
        rows = pair["rows"]
        assert isinstance(rows, Sequence)
        first = rows[0]
        assert isinstance(first, Mapping)
        cells0 = first["cells"]
        assert isinstance(cells0, Sequence)
        equity = [
            str(c["equity_premium_over_bonds_pp_yr"]) for c in cells0 if isinstance(c, Mapping)
        ]
        lines.append(
            f"\n`{pair['arm']}` minus `{pair['twin']}`, wrapper weight {pair['wrapper_weight']}, "
            f"variance-drag constant {pair['variance_drag_pp_yr']} pp/yr on every log cell.\n"
        )
        lines.append(
            "| gross trend premium pp/yr | "
            + " | ".join(f"equity over bonds {e}" for e in equity)
            + " |"
        )
        lines.append("| --- | " + " | ".join("---:" for _ in equity) + " |")
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
        breaks = pair["break_even_trend_premium_by_equity_premium"]
        assert isinstance(breaks, Sequence)
        lines.append("\nBreak-even gross trend premium (the trend arm wins above it):\n")
        lines.append("| equity over bonds pp/yr | arithmetic | log |")
        lines.append("| ---: | ---: | ---: |")
        for b in breaks:
            assert isinstance(b, Mapping)
            lines.append(
                f"| {b['equity_premium_over_bonds_pp_yr']} | "
                f"{b['arithmetic_break_even_trend_pp_yr']} | {b['log_break_even_trend_pp_yr']} |"
            )
    plain = regret["plain_arm_minus_cheap"]
    assert isinstance(plain, Sequence)
    lines.append(
        "\n### The price of the drawdown at forward premia: plain arm minus the cheap 100%-equity "
        "control, pp/yr, arithmetic / log\n"
    )
    first_plain = plain[0] if plain else None
    if isinstance(first_plain, Mapping):
        cells0 = first_plain["cells"]
        assert isinstance(cells0, Sequence)
        equity = [
            str(c["equity_premium_over_bonds_pp_yr"]) for c in cells0 if isinstance(c, Mapping)
        ]
        lines.append(
            "| arm | equity notional | fee delta pp/yr | variance drag pp/yr | "
            + " | ".join(f"equity over bonds {e}" for e in equity)
            + " |"
        )
        lines.append("| --- | ---: | ---: | ---: | " + " | ".join("---:" for _ in equity) + " |")
        for row in plain:
            assert isinstance(row, Mapping)
            cells = row["cells"]
            assert isinstance(cells, Sequence)
            lines.append(
                f"| `{row['arm']}` | {row['equity_notional']} | {row['fee_delta_pp_yr']} | "
                f"{row['variance_drag_pp_yr']} | "
                + " | ".join(
                    f"{_fmt(float(str(c['arithmetic_gap_pp_yr'])))} / "
                    f"{_fmt(float(str(c['log_growth_gap_pp_yr'])))}"
                    for c in cells
                    if isinstance(c, Mapping)
                )
                + " |"
            )
    return lines


def render_tables(
    primary: PanelResult,
    tournament: TournamentResult,
    check: Mapping[str, JsonValue],
    regret: Mapping[str, JsonValue],
    *,
    header: Sequence[str],
    bond_fee_sensitivity: Sequence[str],
) -> str:
    lines: list[str] = list(header)
    p = primary.panel
    lines.append(
        f"\n## Panel `primary`: {p.periods[0]}..{p.periods[-1]}, {p.months} months, own trend "
        "book, nominal ten-year bond line, monthly rebalancing\n"
    )
    lines.extend(_arm_table(primary.arms, primary.descriptives))
    lines.extend(_drawdown_era_table(primary.drawdown_eras, title="Drawdown by era, primary panel"))
    lines.extend(
        _gap_table(
            primary.comparisons,
            [
                "plain_twin",
                "cheap",
                "reference",
                "leverage_matched",
                "volatility_matched_expost",
                "volatility_matched_exante",
            ],
        )
    )
    window_names = [w[0] for w in primary.windows]
    lines.extend(_window_table(primary.comparisons, control="plain_twin", windows=window_names))
    lines.extend(_window_table(primary.comparisons, control="cheap", windows=window_names))
    lines.extend(
        _window_table(
            primary.comparisons, control="volatility_matched_expost", windows=window_names
        )
    )
    lines.extend(_crisis_table(primary.descriptives))
    lines.extend(_episode_table(primary.descriptives))
    lines.extend(_regime_table(primary.regime))
    if primary.financing:
        lines.extend(_financing_table(primary.financing))
    lines.extend(_regret_markdown(regret))
    lines.append("\n### Bond-line fee sensitivity (closed form)\n")
    lines.extend(bond_fee_sensitivity)
    lines.extend(_check_table(check))
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
    lines.extend(
        _drawdown_era_table(tournament.drawdown_eras, title="Drawdown by era, tournament panel")
    )
    lines.extend(
        _gap_table(
            tournament.comparisons,
            ["plain_twin", "cheap", "cheap60_40", "reference", "leverage_matched"],
        )
    )
    lines.extend(
        _window_table(
            tournament.comparisons, control="plain_twin", windows=[w[0] for w in tournament.windows]
        )
    )
    lines.extend(
        _window_table(
            tournament.comparisons, control="cheap", windows=[w[0] for w in tournament.windows]
        )
    )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# The publication rule of freeze note 6, read mechanically
# --------------------------------------------------------------------------- #


def _publication_reading(
    *,
    primary: PanelResult,
    tournament: TournamentResult,
    check: Mapping[str, JsonValue],
    twins: Mapping[str, str],
    tolerances: Sequence[float],
) -> dict[str, JsonValue]:
    """Which arms land within 5 pp of each tolerance on every scored panel; trend-line rule."""

    def falls(rows: Sequence[Mapping[str, JsonValue]], era: str) -> dict[str, float]:
        for row in rows:
            if row["era"] == era:
                arms = row["arms"]
                assert isinstance(arms, Mapping)
                return {
                    n: float(str(v["max_drawdown_pct"]))
                    for n, v in arms.items()
                    if isinstance(v, Mapping) and v["max_drawdown_pct"] is not None
                }
        return {}

    check_rows = check["drawdown_by_era_tsy10"]
    assert isinstance(check_rows, Sequence)
    panels = {
        "primary_full": falls(primary.drawdown_eras, "full"),
        "primary_from_1990_11": falls(primary.drawdown_eras, "from_1990_11"),
        "tournament_full": falls(tournament.drawdown_eras, "full"),
        "check_2003": falls([r for r in check_rows if isinstance(r, Mapping)], "full"),
    }
    by_tolerance: dict[str, JsonValue] = {}
    candidate_names = [n for n in primary.arms if n != "published_trend30"]
    for tolerance in tolerances:
        rows: dict[str, JsonValue] = {}
        for name in candidate_names:
            per_panel = {panel: fall.get(name) for panel, fall in panels.items() if name in fall}
            within = {
                p: (v is not None and abs(v - tolerance) <= 5.0) for p, v in per_panel.items()
            }
            rows[name] = {
                "worst_fall_by_panel": {
                    p: _round(v, 2) if v is not None else None for p, v in per_panel.items()
                },
                "within_5pp_by_panel": within,
                "within_5pp_on_every_scored_panel": all(
                    within.get(p, False) for p in ("primary_full", "tournament_full")
                ),
                "deeper_than_45_on_96_years": (
                    per_panel.get("primary_full") is not None
                    and float(per_panel["primary_full"] or 0.0) < -45.0
                ),
            }
        by_tolerance[f"{tolerance:.0f}"] = rows
    trend_rule: dict[str, JsonValue] = {}
    for arm_name, twin_name in twins.items():
        pair = primary.comparisons[arm_name].get("plain_twin")
        deeper: dict[str, JsonValue] = {}
        for panel, fall in panels.items():
            if arm_name in fall and twin_name in fall:
                deeper[panel] = _round(fall[arm_name] - fall[twin_name], 2)
        trend_rule[arm_name] = {
            "twin": twin_name,
            "pair_status_primary": None if pair is None else pair.status,
            "arm_minus_twin_worst_fall_pp_by_panel": deeper,
            "within_2pp_of_twin_on_every_panel": all(
                isinstance(v, float) and v >= -2.0 for v in deeper.values()
            ),
            "trend_line_survives": (
                pair is not None
                and pair.status != "rejected"
                and all(isinstance(v, float) and v >= -2.0 for v in deeper.values())
            ),
        }
    return {
        "rule": (
            "Freeze note 6: publish a cautious construction for a tolerance only if some arm's "
            "worst fall lands within 5 pp of it on every scored panel, with its growth cost "
            "printed; keep the trend line only if its pair is not rejected on the primary panel "
            "and its worst fall is not deeper than the twin's by more than 2 pp on any panel; "
            "an arm deeper than -45% on 96 years may not be labelled for -30%."
        ),
        "panels_read": {p: sorted(f) for p, f in panels.items()},
        "by_tolerance": by_tolerance,
        "trend_line": trend_rule,
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
    raw, fii10, cpi, tips_provenance, tips_findings = load_series(specification)
    legs = build_legs(
        raw, fii10, cpi, specification, provenance=tips_provenance, findings=tips_findings
    )
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = read_rates(specification)
    primary_pairs, secondary_pairs = read_pairs(specification)
    twins = {**primary_pairs, **secondary_pairs}
    reference = _text(parameters, "reference_arm", where="parameters")
    in_estimates = tuple(
        str(x)
        for x in _sequence(_at(parameters, "controls_in_estimates", where="parameters"), where="c")
    )
    findings = [*raw.findings, *tips_findings]

    book_block = _mapping(_at(parameters, "trend_book", where="parameters"), where="trend_book")
    expected_scalar = _number(book_block, "expected_scalar_from_exp_018", where="trend_book")
    scalar_matches = abs(legs.core.trend_scalar - expected_scalar) < 5e-4
    if not scalar_matches:
        findings.append(
            f"trend-book scalar {legs.core.trend_scalar:.4f} does not reproduce 018's "
            f"{expected_scalar}"
        )

    panel = build_primary_panel(legs.core)
    primary = score_primary(
        panel,
        specification=specification,
        arms=arms,
        wrappers=wrappers,
        rates=rates,
        twins=twins,
        rng=context.rng,
        full=True,
    )
    check_block = _mapping(_at(parameters, "check_panel", where="parameters"), where="check")
    check_panel = build_check_panel(legs, start=_text(check_block, "start", where="check_panel"))
    check = score_check_panel(
        check_panel, specification=specification, arms=arms, wrappers=wrappers, rates=rates
    )
    inputs = load_tournament_inputs(specification, legs.core)
    tournament = score_tournament(
        inputs, specification=specification, twins=twins, rng=context.rng, full=True
    )
    findings.extend(inputs.findings)
    if not tournament.reproduction["reproduced"]:
        findings.append(
            "016f's rec30 minus rec25 log gap did NOT reproduce: "
            f"{tournament.reproduction['observed_pp_yr']} against "
            f"{tournament.reproduction['expected_pp_yr']}"
        )

    regret = regret_tables(specification, primary=primary, twins=twins, wrappers=wrappers)

    # The bond-fee sensitivity, closed form on the largest bond line.
    largest = max(arms.values(), key=lambda a: arm_notional(a.tickers, a.weights, wrappers).bond)
    bond_points = arm_notional(largest.tickers, largest.weights, wrappers).bond
    fee_lines = [
        f"Largest bond line: `{largest.name}` at {bond_points:.3f} of capital. Charged at 5 bp. "
        f"At 3 bp (SCHP-like) the arm earns {2.0 * bond_points:+.2f} bp/yr more; at 18 bp "
        f"(TIP-like) it earns {-13.0 * bond_points:+.2f} bp/yr less. Every gap in this file moves "
        "by less than that."
    ]

    # Estimates and the verdict.
    estimates: list[Estimate] = []
    resolved: list[str] = []
    scored = 0
    panels: list[tuple[str, Mapping[str, Mapping[str, Comparison]], tuple[str, ...]]] = [
        ("primary", primary.comparisons, in_estimates),
        (
            "tournament_1990",
            tournament.comparisons,
            ("plain_twin", "cheap", "cheap60_40", "reference", "leverage_matched"),
        ),
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
                            f"{f.hac_lags} lags; log-growth gap {f.log_growth_gap_pp_yr:+.3f}; "
                            f"tracking error {g.tracking_error_pct:.2f}%; years to distinguish "
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

    reporting = _mapping(
        _at(parameters, "drawdown_reporting", where="parameters"), where="drawdown_reporting"
    )
    tolerances = _numbers(
        _at(reporting, "tolerance_rows_pct", where="drawdown_reporting"), where="tolerances"
    )
    publication = _publication_reading(
        primary=primary, tournament=tournament, check=check, twins=twins, tolerances=tolerances
    )

    pair_lines: list[str] = []
    for arm_name, twin_name in primary_pairs.items():
        pair = primary.comparisons[arm_name]["plain_twin"]
        assert pair.gap is not None and pair.full is not None
        d_a = primary.descriptives[arm_name]
        d_t = primary.descriptives[twin_name]
        pair_lines.append(
            f"{arm_name} minus {twin_name}: {pair.gap.gap_pp_yr:+.2f} pp/yr "
            f"[{pair.gap.interval[0]:+.2f}, {pair.gap.interval[1]:+.2f}], floor "
            f"{pair.gap.mde_pp_yr:.2f}, `{pair.status}`; worst fall {d_a['max_drawdown_pct']}% "
            f"against {d_t['max_drawdown_pct']}%"
        )
    cheap_falls = primary.descriptives[reference]["controls"]
    assert isinstance(cheap_falls, Mapping)
    cheap_row = cheap_falls["cheap"]
    assert isinstance(cheap_row, Mapping)
    tournament_full = tournament.drawdown_eras[0]["arms"]
    assert isinstance(tournament_full, Mapping)
    tournament_cheap = tournament_full["control_cheap"]
    assert isinstance(tournament_cheap, Mapping)
    summary = (
        f"Cautious constructions on the {panel.months}-month primary panel, where the cheap "
        f"100%-equity control fell {cheap_row['max_drawdown_pct']}%. Primary pairs, trend arm "
        f"minus plain twin at matched equity: " + "; ".join(pair_lines) + ". Plain 60/40 fell "
        f"{primary.descriptives['plain60_40']['max_drawdown_pct']}% and plain 40/60 "
        f"{primary.descriptives['plain40_60']['max_drawdown_pct']}% on 96 years; on the "
        f"{inputs.panel.months}-month tournament panel "
        f"{tournament.descriptives['plain60_40']['max_drawdown_pct']}% and "
        f"{tournament.descriptives['plain40_60']['max_drawdown_pct']}% against the cheap 65/35's "
        f"{tournament_cheap['max_drawdown_pct']}%. {scored} comparisons scored on two panels; "
        f"{len(resolved)} separate from their control by more than the design can resolve. "
        "Drawdown, episode and terminal-wealth tables are descriptive and carry no significance "
        "claim; the publication reading is in the diagnostics."
    )
    freeze_note = (
        "WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS; the tournament panel's "
        "tickers are 016f's basis expressions. THE BOND LINE IS A NOMINAL TEN-YEAR TREASURY on "
        "both scored panels, modelled as a rolled par bond on FRED GS10 from 1953-04 and "
        "Shiller's long rate before it, because no TIPS series exists before 2003; at 40 to 63 "
        "points of capital that overstates the line's 1973-74 and 1977-81 losses relative to a "
        "TIPS book. The 2003-02 check panel carries 018's modelled TIPS leg beside it and is "
        "descriptive. The trend leg is the repository's own 4-asset book scaled by one "
        "full-window constant and charged no trading; AQR's TSMOM on the tournament panel is "
        "gross of the vendor's trading costs. Drawdown by era is the reason this file exists and "
        "carries no status."
    )
    header = [
        "# Experiment 025: cautious constructions scored as objects",
        "",
        f"Run `{context.run_id}`; specification hash `{specification.spec_hash}`.",
        "",
        freeze_note,
        "",
        f"Trend-book volatility scalar {legs.core.trend_scalar:.4f} (realised "
        f"{legs.core.trend_book_realised_volatility_pct:.2f}% on {legs.core.trend_book_window[0]}.."
        f"{legs.core.trend_book_window[1]}, target 12.38%; 018's {expected_scalar}, reproduced "
        f"`{scalar_matches}`). Shiller long rate against FRED GS10 on "
        f"{legs.core.yield_cross_check_months} overlapping months: largest difference "
        f"{legs.core.yield_cross_check_max_bp:.2f} bp.",
        "",
        "Gap cells read: point estimate, bootstrap and HAC 95% intervals, MDE at 80% power, "
        "log-growth gap, years to distinguish, falsifier status. Descriptive tables carry no "
        "status.",
    ]
    tables = render_tables(
        primary, tournament, check, regret, header=header, bond_fee_sensitivity=fee_lines
    )

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in (*raw.provenance, *tips_provenance)],
        "source_findings": findings,
        "trend_book": {
            "scalar": round(legs.core.trend_scalar, 6),
            "expected_from_exp_018": expected_scalar,
            "reproduced": scalar_matches,
            "realised_volatility_pct_on_primary_window": round(
                legs.core.trend_book_realised_volatility_pct, 4
            ),
            "primary_window": list(legs.core.trend_book_window),
        },
        "ten_year_leg": {
            "cross_check_overlap_months": legs.core.yield_cross_check_months,
            "largest_yield_difference_bp": _round(legs.core.yield_cross_check_max_bp, 3),
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
        "pairs": {"primary": dict(primary_pairs), "secondary": dict(secondary_pairs)},
        "panels": [
            {
                "id": "primary",
                "window": f"{panel.periods[0]}..{panel.periods[-1]}",
                "months": panel.months,
                "panel_findings": list(panel.findings),
                "arms": _panel_json(primary.arms, primary.comparisons, primary.descriptives),
                "drawdown_by_era": list(primary.drawdown_eras),
                "ten_year_regime_by_era": list(primary.regime),
                "financing_sensitivity": primary.financing,
                "multiple_testing_families": {k: sorted(v) for k, v in primary.families.items()},
            },
            {
                "id": "check_2003",
                **dict(check),
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
                "drawdown_by_era": list(tournament.drawdown_eras),
                "multiple_testing_families": {k: sorted(v) for k, v in tournament.families.items()},
            },
        ],
        "primary_pairs": {
            arm_name: {
                "panel": "primary",
                "arm": arm_name,
                "control": "plain_twin",
                **primary.comparisons[arm_name]["plain_twin"].to_json(),
            }
            for arm_name in primary_pairs
        },
        "regret": regret,
        "bond_fee_sensitivity": fee_lines,
        "publication_reading": publication,
        "resolved_comparisons": resolved,
        "markdown_tables": tables,
    }
    caveats = (
        "Wrappers are assumed exposure vectors; the tournament tickers are 016f's basis "
        "expressions. This ranks constructions and cannot rank funds.",
        "The bond line is a nominal ten-year Treasury modelled as a rolled par bond on both "
        "scored panels; no TIPS series exists before 2003. At 40 to 63 points of capital the "
        "1973-74 and 1977-81 episodes read worse than a TIPS book would have.",
        "The own 4-asset trend book is scaled by one full-window constant and charged no "
        "trading cost; AQR's TSMOM is gross of the vendor's trading costs by omission.",
        "A rejected gap against the cheap control is the price of a drawdown constraint, not a "
        "verdict on the reader who holds it; the regret tables price it at forward premia.",
        "Drawdown, months under water, worst-decile, episode and terminal-wealth figures "
        "describe one realised history and carry no significance claim.",
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_025_cautious_constructions",
        description="Score bond-heavy cautious constructions as objects on 024's panels.",
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
