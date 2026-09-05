"""Experiment 026: engines on the bond line of the published cautious portfolio.

What this is
------------
Decision 0014 publishes a cautious construction, SCHP 50 / RSST 15 / stocks 35,
whose bond line is 50 points of an unlevered ten-year Treasury and whose worst
measured episode is 1977-81. Every trend test in this repository funded trend
from stocks. This module funds an engine from the BOND line instead, three ways,
at 10, 20 and 30 points, and scores each whole construction against the
published cautious portfolio itself: an RSBT-like wrapper (bond kept, trend
stacked on top), a standalone trend fund (bond sold), and a GDE-like wrapper
(equity kept, gold stacked on top of the stock line). It runs on 025's 1929-2025
primary panel, on the 1968-05 gold sub-window, and on 016f's 1990-11 fund-list
panel, and reads freeze note 6 of its specification mechanically.

What this is NOT
----------------
**It does not score funds.** Every holding is an assumed per-dollar exposure
vector and a fee, or 016f's basis expression.

**The bond line is a nominal ten-year Treasury on every scored panel.** No TIPS
series exists before 2003; freeze note 4 of the specification says what that
assumes.

Run it::

    uv run python -m portfolio_edge.experiments.exp_026_trend_from_the_bond_line --view-results
"""

from __future__ import annotations

import argparse
import itertools
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import lbma
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
    _price_returns,
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
    _bond_regime,
    _compare,
    _crisis_table,
    _describe,
    _episode_table,
    _gap_table,
    _manifest_hashes,
    _panel_json,
    _point_gaps,
    _read_weighted,
    _regime_table,
    _round,
    _volatility,
    _window_table,
    read_arms,
)
from portfolio_edge.experiments.exp_024_working_default import (
    build_legs as build_core_legs,
)
from portfolio_edge.experiments.exp_024_working_default import (
    load_series as load_core_series,
)
from portfolio_edge.experiments.exp_025_cautious_constructions import (
    _drawdown_era_table,
    drawdown_by_era,
    leverage_matched_targets,
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

FloatArray = NDArray[np.float64]
MonthSeries = dict[str, float]

ENTRY_POINT: Final = "exp_026_trend_from_the_bond_line"

#: The legs a wrapper may expose. ``gold`` exists on the gold panels only.
LEGS: Final = ("equity", "treasury", "tsy10", "trend", "gold")
BOND_LEGS: Final = frozenset({"treasury", "tsy10"})
#: The legs a wrapper may finance; the keys :class:`FinancingRates` knows.
FINANCED_LEGS: Final = frozenset({"equity", "treasury", "gold", "tips"})
#: 016f's equity legs, for the tournament notional decomposition.
_EQUITY_BASIS: Final = frozenset({"us_mkt", "dxus_mkt", "em_mkt"})

__all__ = [
    "ENTRY_POINT",
    "LEGS",
    "BondLineLegs",
    "PanelSpec",
    "TrendFromBondLineError",
    "arm_notional",
    "build_registry",
    "default_specification_path",
    "freeze_note_reading",
    "gde_regret_pp_yr",
    "gold_notional",
    "main",
    "read_arm_families",
    "read_panels",
    "read_wrappers",
    "rsbt_regret_pp_yr",
    "run",
    "tournament_notional",
    "trend_fund_regret_pp_yr",
]


class TrendFromBondLineError(Exception):
    """The experiment refused to run, or an input did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_026_trend_from_the_bond_line.yaml"


# --------------------------------------------------------------------------- #
# Wrappers, arms, notional
# --------------------------------------------------------------------------- #


def read_wrappers(specification: Specification) -> dict[str, Wrapper]:
    """025's reader with the ``gold`` leg admitted and financed legs checked against the rates."""
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
        for leg in exposures:
            if leg not in LEGS:
                raise TrendFromBondLineError(f"wrappers.{ticker} exposes unknown leg {leg!r}")
        for leg in financed:
            if leg not in FINANCED_LEGS:
                raise TrendFromBondLineError(f"wrappers.{ticker} finances unpriced leg {leg!r}")
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
    """Capital weights times per-dollar exposures, leg by leg; gold counts in the gross."""
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


def gold_notional(
    tickers: Sequence[str], weights: Sequence[float], wrappers: Mapping[str, Wrapper]
) -> float:
    return sum(
        weight * wrappers[ticker].exposures.get("gold", 0.0)
        for ticker, weight in zip(tickers, weights, strict=True)
    )


def read_arm_families(specification: Specification) -> dict[str, tuple[str, ...]]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "arm_families", where="parameters"), where="arm_families")
    return {
        family: tuple(str(x) for x in _sequence(block[family], where=f"arm_families.{family}"))
        for family in block
    }


# --------------------------------------------------------------------------- #
# Series, legs, panels
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BondLineLegs:
    """024's legs plus 018's LBMA gold leg."""

    core: Legs
    gold: MonthSeries
    gold_provenance: tuple[Mapping[str, JsonValue], ...]
    gold_findings: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PanelSpec:
    id: str
    legs: tuple[str, ...]
    start: str | None
    arms: tuple[str, ...]
    note: str


def _pin(specification: Specification, file_id: str) -> Mapping[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    for item in _sequence(_at(block, "files", where="source_pin"), where="source_pin.files"):
        pin = _mapping(item, where="source_pin.files[]")
        if _text(pin, "id", where="source_pin.files[]") == file_id:
            return pin
    raise TrendFromBondLineError(f"source_pin.files has no entry {file_id!r}")


def load_series(
    specification: Specification,
) -> tuple[RawSeries, MonthSeries, tuple[Mapping[str, JsonValue], ...], tuple[str, ...]]:
    """024's five pinned sources, then the LBMA PM fix by digest; never download."""
    raw = load_core_series(specification)
    cache = RawCache()
    dataset = lbma.get_dataset("lbma_gold_pm")
    entry, record = _require_cached(cache, dataset.url, _pin(specification, "lbma_gold_pm"))
    findings: list[str] = []
    if record["committed_manifest_raw_hash_matches"] is False:
        findings.append(
            f"lbma_gold_pm: the pinned file ({record['sha256_raw']}) is a different vintage "
            "from the one the committed manifest records; recorded, not hidden (018's note)."
        )
    if record["index_superseded_by_sha256"] is not None:
        findings.append(
            f"lbma_gold_pm: the cache index now points at {record['index_superseded_by_sha256']}; "
            f"the pinned blob {record['sha256_raw']} was read by digest instead."
        )
    levels = dict(lbma.month_end_usd(lbma.parse(cache, entry, dataset=dataset)))
    record["first_observation"], record["last_observation"] = min(levels), max(levels)
    return raw, levels, (record,), tuple(findings)


def build_legs(
    raw: RawSeries,
    gold_levels: MonthSeries,
    specification: Specification,
    *,
    provenance: tuple[Mapping[str, JsonValue], ...] = (),
    findings: tuple[str, ...] = (),
) -> BondLineLegs:
    """024's legs; gold as 018 builds it, spot change less the one-month bill."""
    core = build_core_legs(raw, specification)
    returns = _price_returns(gold_levels)
    gold = {p: returns[p] - raw.cash[p] for p in returns if p in raw.cash}
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "gold_leg", where="parameters"), where="gold_leg")
    first = _text(block, "first_return_month", where="gold_leg")
    if min(gold) != first:
        raise TrendFromBondLineError(f"the gold leg begins {min(gold)}, not the declared {first}")
    return BondLineLegs(core=core, gold=gold, gold_provenance=provenance, gold_findings=findings)


def read_panels(specification: Specification) -> tuple[PanelSpec, ...]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "panels", where="parameters"), where="panels")
    out: list[PanelSpec] = []
    for panel_id in block:
        entry = _mapping(block[panel_id], where=f"panels.{panel_id}")
        legs = tuple(str(x) for x in _sequence(_at(entry, "legs", where=panel_id), where="legs"))
        for leg in legs:
            if leg not in LEGS:
                raise TrendFromBondLineError(f"panels.{panel_id} names unknown leg {leg!r}")
        start = entry.get("start")
        out.append(
            PanelSpec(
                id=panel_id,
                legs=legs,
                start=None if start is None else str(start),
                arms=tuple(
                    str(x) for x in _sequence(_at(entry, "arms", where=panel_id), where="a")
                ),
                note=str(entry.get("note") or ""),
            )
        )
    return tuple(out)


def build_panel(legs: BondLineLegs, spec: PanelSpec) -> BasisPanel:
    """Intersect the legs a panel names, from its declared start."""
    sources: dict[str, MonthSeries] = {
        "equity": legs.core.equity,
        "treasury": legs.core.treasury,
        "tsy10": legs.core.tsy10,
        "trend": legs.core.trend,
        "gold": legs.gold,
    }
    chosen = {leg: sources[leg] for leg in spec.legs}
    common = set(legs.core.cash)
    for series in chosen.values():
        common &= set(series)
    periods = sorted(common)
    if spec.start is not None:
        periods = [p for p in periods if month_index(p) >= month_index(spec.start)]
    if len(periods) < 3 * MONTHS_PER_YEAR:
        raise TrendFromBondLineError(f"panel {spec.id} holds {len(periods)} months")
    for earlier, later in itertools.pairwise(periods):
        if month_index(later) - month_index(earlier) != 1:
            raise TrendFromBondLineError(f"panel {spec.id} has a gap at {earlier}..{later}")
    return BasisPanel(
        periods=tuple(periods),
        series={n: np.array([s[p] for p in periods], dtype=np.float64) for n, s in chosen.items()},
        cash=np.array([legs.core.cash[p] for p in periods], dtype=np.float64),
        provenance=(),
        findings=(f"panel {spec.id}: {len(periods)} months, {periods[0]}..{periods[-1]}",),
    )


# --------------------------------------------------------------------------- #
# The primary panels: arms and four controls
# --------------------------------------------------------------------------- #


def simulate_panel(
    panel: BasisPanel,
    *,
    arms: Mapping[str, Arm],
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    costs: CostSettings,
    reference: str,
    cheap60_40: tuple[tuple[str, ...], tuple[float, ...]],
) -> dict[str, ArmPaths]:
    """Every arm with the cheap, cheap 60/40, leverage-matched and reference controls."""
    cheap = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.0]))
    mix = simulate_arm(
        panel,
        wrappers,
        rates,
        costs,
        tickers=cheap60_40[0],
        targets=np.asarray(cheap60_40[1], dtype=np.float64),
    )
    paths: dict[str, PortfolioPath] = {
        name: simulate_arm(
            panel,
            wrappers,
            rates,
            costs,
            tickers=arm.tickers,
            targets=np.asarray(arm.weights, dtype=np.float64),
        )
        for name, arm in arms.items()
    }
    if reference not in paths:
        raise TrendFromBondLineError(f"reference arm {reference!r} is not on this panel")
    mix_definition = " + ".join(f"{w:.2f} x {t}" for t, w in zip(*cheap60_40, strict=True))
    out: dict[str, ArmPaths] = {}
    for name, arm in arms.items():
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        controls: dict[str, PortfolioPath] = {"cheap": cheap, "cheap60_40": mix}
        first: dict[str, int] = {"cheap": 0, "cheap60_40": 0}
        definition: dict[str, str] = {"cheap": "100% CORE", "cheap60_40": mix_definition}
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
        if name != reference:
            controls["reference"] = paths[reference]
            first["reference"] = 0
            definition["reference"] = f"the {reference} arm, the published cautious construction"
        out[name] = ArmPaths(
            arm=arm,
            notional=notional,
            path=paths[name],
            controls=controls,
            control_first_month=first,
            control_definition=definition,
        )
    return out


@dataclass(slots=True, kw_only=True)
class PanelResult:
    spec: PanelSpec
    panel: BasisPanel
    arms: dict[str, ArmPaths]
    gold: dict[str, float]
    comparisons: dict[str, dict[str, Comparison]]
    descriptives: dict[str, dict[str, JsonValue]]
    regime: list[dict[str, JsonValue]]
    financing: dict[str, JsonValue]
    families: dict[str, list[str]]
    windows: list[tuple[str, str, str]]
    drawdown_eras: list[dict[str, JsonValue]]


def _era_specs(
    specification: Specification, periods: Sequence[str], *, wanted: Sequence[str]
) -> list[tuple[str, str, str]]:
    windows = [("full", periods[0], periods[-1])]
    declared = {e.name: (e.start, e.end) for e in specification.sample_policy.eras}
    for name in wanted:
        if name == "full":
            continue
        if name not in declared:
            raise TrendFromBondLineError(f"drawdown era {name!r} is not a declared era")
        start, end = declared[name]
        keep = _slice(periods, start, end)
        if keep.size >= MONTHS_PER_YEAR and periods[int(keep[0])] != periods[0]:
            windows.append((name, periods[int(keep[0])], periods[int(keep[-1])]))
    return windows


def _drawdowns_with_difference(
    totals: Mapping[str, FloatArray],
    *,
    periods: Sequence[str],
    eras: Sequence[tuple[str, str, str]],
    reference: str,
) -> list[dict[str, JsonValue]]:
    rows = drawdown_by_era(totals, periods=periods, eras=eras)
    for row in rows:
        arms = row["arms"]
        assert isinstance(arms, Mapping)
        ref = arms[reference]
        assert isinstance(ref, Mapping)
        ref_fall = float(str(ref["max_drawdown_pct"]))
        for value in arms.values():
            assert isinstance(value, dict)
            fall = value["max_drawdown_pct"]
            value["minus_reference_pp"] = (
                None if fall is None else _round(float(str(fall)) - ref_fall, 2)
            )
    return rows


def _regime_with_gold(
    panel: BasisPanel, windows: Sequence[tuple[str, str, str]]
) -> list[dict[str, JsonValue]]:
    rows = _bond_regime(panel, windows)
    if "gold" not in panel.series:
        return rows
    gold = panel.column("gold")
    equity = panel.column("equity")
    for row in rows:
        window = str(row["window"]).split("..")
        keep = _slice(panel.periods, window[0], window[1])
        row["gold_excess_pp_yr"] = _round(float(np.mean(gold[keep])) * MONTHS_PER_YEAR * 100.0, 2)
        row["gold_equity_correlation"] = _round(
            float(np.corrcoef(gold[keep], equity[keep])[0, 1]), 3
        )
    return rows


def _bands(
    specification: Specification, *, panel_legs: Sequence[str], wrappers: Mapping[str, Wrapper]
) -> list[tuple[str, list[float]]]:
    """The financing bands that touch a leg some wrapper on this panel finances."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "financing_sensitivity", where="parameters"), where="f")
    financed = {leg for w in wrappers.values() for leg in w.financed}
    out: list[tuple[str, list[float]]] = []
    for key, leg in (
        ("equity_basis_points", "equity"),
        ("treasury_basis_points", "treasury"),
        ("gold_basis_points", "gold"),
    ):
        if leg == "gold" and "gold" not in panel_legs:
            continue
        if leg not in financed and leg != "equity":
            continue
        out.append((leg, list(_numbers(_at(block, key, where="financing_sensitivity"), where=key))))
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
    contribution = _number(parameters, "contribution_per_month_of_starting_balance", where="p")
    tail = _number(parameters, "tail_quantile", where="parameters")
    q = _number(parameters, "multiple_testing_q", where="parameters")
    block = _number(parameters, "bootstrap_block_months", where="parameters")
    mix = _read_weighted(
        _mapping(_at(parameters, "cheap60_40_weights", where="parameters"), where="cheap60_40"),
        where="cheap60_40_weights",
    )
    on_panel = {name: arms[name] for name in spec.arms}
    for name in spec.arms:
        if name not in arms:
            raise TrendFromBondLineError(f"panel {spec.id} names unknown arm {name!r}")
        for ticker in arms[name].tickers:
            for leg in wrappers[ticker].exposures:
                if leg not in spec.legs:
                    raise TrendFromBondLineError(
                        f"panel {spec.id}: arm {name} holds {ticker}, which exposes {leg!r}, "
                        "a leg this panel does not carry"
                    )
    costs = _engine_costs(specification, rates)
    simulated = simulate_panel(
        panel,
        arms=on_panel,
        wrappers=wrappers,
        rates=rates,
        costs=costs,
        reference=reference,
        cheap60_40=mix,
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
        band_range: dict[str, dict[str, list[float]]] = {}
        band_json: dict[str, JsonValue] = {}
        for leg, grid in _bands(specification, panel_legs=spec.legs, wrappers=wrappers):
            per_point: dict[str, dict[str, list[float]]] = {}
            for point in grid:
                shifted = FinancingRates(
                    equity=point if leg == "equity" else rates.equity,
                    treasury=point if leg == "treasury" else rates.treasury,
                    gold=point if leg == "gold" else rates.gold,
                    tips=rates.tips,
                )
                gaps = _point_gaps(
                    simulate_panel(
                        panel,
                        arms=on_panel,
                        wrappers=wrappers,
                        rates=shifted,
                        costs=_engine_costs(specification, shifted),
                        reference=reference,
                        cheap60_40=mix,
                    )
                )
                for name, by_control in gaps.items():
                    for control, value in by_control.items():
                        per_point.setdefault(name, {}).setdefault(control, []).append(value)
                        band_range.setdefault(name, {}).setdefault(control, []).append(value)
            signs: dict[str, JsonValue] = {}
            for name in on_panel:
                values = per_point.get(name, {}).get("reference", [])
                signs[name] = {
                    "gaps_pp_yr": [_round(v) for v in values],
                    "sign_stable": bool(values)
                    and all((v > 0.0) == (values[0] > 0.0) for v in values),
                }
            band_json[leg] = {
                "grid_basis_points": list(grid),
                "gaps_pp_yr": {
                    n: {c: [_round(v) for v in vs] for c, vs in by_control.items()}
                    for n, by_control in per_point.items()
                },
                "arm_against_reference_by_point": signs,
            }
        financing = {"bands": band_json}
        for name in on_panel:
            for control, comparison in comparisons[name].items():
                values = band_range.get(name, {}).get(control, [])
                if values:
                    comparison.financing_band_range = (min(values), max(values))

    for name in on_panel:
        for comparison in comparisons[name].values():
            _apply_falsifier(comparison, q=q)
            if comparison.clause.startswith("(d)"):
                comparison.clause = comparison.clause.replace(
                    "the equity-financing band", "a declared financing band"
                )

    descriptives = _describe(
        simulated,
        panel=panel,
        reference=reference,
        episodes=read_episodes(specification),
        contribution=contribution,
        tail=tail,
        comparisons=comparisons,
    )
    gold = {n: gold_notional(a.tickers, a.weights, wrappers) for n, a in on_panel.items()}
    for name in on_panel:
        descriptives[name]["gold_notional"] = _round(gold[name])
    reporting = _mapping(
        _at(parameters, "drawdown_reporting", where="parameters"), where="drawdown_reporting"
    )
    wanted = [
        str(x)
        for x in _sequence(
            _at(reporting, "eras_for_drawdown_table", where="drawdown_reporting"), where="eras"
        )
    ]
    eras = _era_specs(specification, panel.periods, wanted=wanted)
    totals = {n: item.path.total for n, item in simulated.items()}
    totals["control_cheap"] = simulated[reference].controls["cheap"].total
    totals["control_cheap60_40"] = simulated[reference].controls["cheap60_40"].total
    drawdown_eras = _drawdowns_with_difference(
        totals, periods=panel.periods, eras=eras, reference=reference
    )
    return PanelResult(
        spec=spec,
        panel=panel,
        arms=simulated,
        gold=gold,
        comparisons=comparisons,
        descriptives=descriptives,
        regime=_regime_with_gold(panel, windows),
        financing=financing,
        families=families,
        windows=windows,
        drawdown_eras=drawdown_eras,
    )


# --------------------------------------------------------------------------- #
# The tournament panel: 016f plus the ten-year line, the gold leg and three wrappers
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class TournamentInputs:
    panel: BasisPanel
    mappings: Mapping[str, FundMapping]
    costs: CostSettings
    specification_hash: str
    findings: tuple[str, ...]


def _assumed_mapping(ticker: str, coefficients: Mapping[str, float], fee_bp: float) -> FundMapping:
    return FundMapping(
        ticker=ticker,
        coefficients=dict(coefficients),
        expense_ratio_bp=fee_bp,
        futures_notional=0.0,
        spread_region="us_equity",
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=True,
        fee_assumed=False,
    )


def load_tournament_inputs(
    specification: Specification,
    legs: BondLineLegs,
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
) -> TournamentInputs:
    """016f's panel, mapping and costs, hash-checked, with the ten-year and gold legs added."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "tournament_panel", where="parameters"), where="tournament")
    path = workspace_root() / _text(block, "specification_path", where="tournament_panel")
    tournament = load_specification(path)
    expected = _text(block, "expected_specification_hash", where="tournament_panel")
    if tournament.spec_hash != expected:
        raise TrendFromBondLineError(
            f"{path.name} hashes to {tournament.spec_hash}, not the pinned {expected}. The "
            "tournament panel is defined by that file; a new 016f needs a new 026."
        )
    base = load_basis_panel(tournament)
    mappings = dict(_build_mappings(tournament))
    costs = _tournament_costs(tournament)
    if "CASH" not in mappings:
        raise TrendFromBondLineError("016f's mapping has no CASH ticker for sub-unity controls")
    mappings["TSY10"] = _assumed_mapping("TSY10", {"treasury": 1.0}, wrappers["TSY10"].fee_bp)
    rsbt, fund, gde = wrappers["RSBT_LIKE"], wrappers["TREND_FUND"], wrappers["GDE_LIKE"]
    # 016f's simulator charges one basis on one futures-notional field, so each
    # wrapper's financing is folded into its fee; the arithmetic is identical.
    mappings["RSBT_LIKE"] = _assumed_mapping(
        "RSBT_LIKE",
        {"treasury": rsbt.exposures["tsy10"], "trend": rsbt.exposures["trend"]},
        rsbt.fee_bp + rsbt.financed["treasury"] * rates.treasury,
    )
    mappings["TREND_FUND"] = _assumed_mapping(
        "TREND_FUND", {"trend": fund.exposures["trend"]}, fund.fee_bp
    )
    mappings["GDE_LIKE"] = _assumed_mapping(
        "GDE_LIKE",
        {"us_mkt": gde.exposures["equity"], "gold": gde.exposures["gold"]},
        gde.fee_bp + gde.financed["gold"] * rates.gold,
    )
    keep = [i for i, p in enumerate(base.periods) if p in legs.core.tsy10]
    if len(keep) < 3 * MONTHS_PER_YEAR:
        raise TrendFromBondLineError("the ten-year leg covers too little of the tournament")
    index = np.asarray(keep, dtype=np.intp)
    periods = tuple(base.periods[i] for i in keep)
    gold_returns = _price_returns({p: v for p, v in legs.gold.items()})  # excess; rebuilt below
    missing = [p for p in periods if p not in legs.gold]
    if missing:
        raise TrendFromBondLineError(
            f"the gold leg does not cover {len(missing)} tournament month(s), first {missing[0]}; "
            "a panel cut by the gold leg would move the reproduction pair"
        )
    del gold_returns
    series = {name: values[index] for name, values in base.series.items()}
    series["treasury"] = np.array([legs.core.tsy10[p] for p in periods], dtype=np.float64)
    # 018's gold leg is spot change less the French bill; the tournament's cash is
    # the same bill, so the excess series carries over unchanged.
    series["gold"] = np.array([legs.gold[p] for p in periods], dtype=np.float64)
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
) -> tuple[Notional, float]:
    """024's decomposition on 016f's basis expressions, bonds and gold counted."""
    equity = trend = bond = gold = cash = 0.0
    for ticker, weight in zip(tickers, weights, strict=True):
        held = 0.0
        for name, value in mappings[ticker].coefficients.items():
            if name in _EQUITY_BASIS:
                equity += weight * value
                held += value
            elif name == "trend":
                trend += weight * value
                held += value
            elif name == "treasury":
                bond += weight * value
                held += value
            elif name == "gold":
                gold += weight * value
                held += value
        cash += weight * max(0.0, 1.0 - held)
    return (
        Notional(
            gross=equity + trend + bond + gold, equity=equity, trend=trend, bond=bond, cash=cash
        ),
        gold,
    )


@dataclass(slots=True, kw_only=True)
class TournamentResult:
    inputs: TournamentInputs
    arms: dict[str, ArmPaths]
    gold: dict[str, float]
    comparisons: dict[str, dict[str, Comparison]]
    descriptives: dict[str, dict[str, JsonValue]]
    families: dict[str, list[str]]
    reproduction: dict[str, JsonValue]
    windows: list[tuple[str, str, str]]
    drawdown_eras: list[dict[str, JsonValue]]


def _tournament_arms(block: Mapping[str, JsonValue]) -> dict[str, Arm]:
    arms: dict[str, Arm] = {}
    for name, raw in _mapping(_at(block, "arms", where="tournament_panel"), where="arms").items():
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
    return arms


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
    mix_tickers, mix_weights = _read_weighted(
        _mapping(_at(controls_block, "cheap60_40", where="controls"), where="cheap60_40"),
        where="tournament_panel.controls.cheap60_40",
    )
    era_names = {
        str(x) for x in _sequence(_at(block_spec, "eras", where="tournament_panel"), where="eras")
    }
    panel, mappings, costs = inputs.panel, inputs.mappings, inputs.costs
    arms = _tournament_arms(block_spec)

    def path_for(tickers: Sequence[str], weights: Sequence[float]) -> PortfolioPath:
        return constant_weight_path(
            panel, mappings, costs, tickers=tickers, targets=np.asarray(weights, dtype=np.float64)
        )

    cheap = path_for(cheap_tickers, cheap_weights)
    mix = path_for(mix_tickers, mix_weights)
    paths = {name: path_for(arm.tickers, arm.weights) for name, arm in arms.items()}
    if reference not in paths:
        raise TrendFromBondLineError(f"tournament reference arm {reference!r} is not an arm")
    simulated: dict[str, ArmPaths] = {}
    gold: dict[str, float] = {}
    for name, arm in arms.items():
        notional, gold[name] = tournament_notional(arm.tickers, arm.weights, mappings)
        if notional.gross > 1.0:
            levered = path_for(cheap_tickers, [w * notional.gross for w in cheap_weights])
            levered_definition = (
                f"{notional.gross:.4f} x the cheap control, financed at the equity basis"
            )
        else:
            levered = path_for(
                (*cheap_tickers, "CASH"),
                [*(w * notional.gross for w in cheap_weights), 1.0 - notional.gross],
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
        if name != reference:
            controls["reference"] = paths[reference]
            first["reference"] = 0
            definition["reference"] = f"the {reference} arm, the published cautious construction"
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

    descriptives = _describe(
        simulated,
        panel=panel,
        reference=reference,
        episodes=read_episodes(specification),
        contribution=_number(parameters, "contribution_per_month_of_starting_balance", where="p"),
        tail=_number(parameters, "tail_quantile", where="parameters"),
        comparisons=comparisons,
    )
    for name in arms:
        descriptives[name]["gold_notional"] = _round(gold[name])

    repro_block = _mapping(_at(block_spec, "reproduction", where="tournament_panel"), where="r")
    expected = _number(repro_block, "expected_pp_yr", where="reproduction")
    tolerance = _number(repro_block, "tolerance_pp_yr", where="reproduction")
    published = path_for(
        *_read_weighted(
            _mapping(_at(repro_block, "published_weights", where="reproduction"), where="p"),
            where="reproduction.published_weights",
        )
    )
    rec25 = path_for(
        *_read_weighted(
            _mapping(_at(repro_block, "rec25_weights", where="reproduction"), where="r"),
            where="reproduction.rec25_weights",
        )
    )
    observed = annualised_log_growth(published.total) - annualised_log_growth(rec25.total)
    reproduction: dict[str, JsonValue] = {
        "pair": "016f rec30 minus rec25, log-growth gap",
        "expected_pp_yr": expected,
        "observed_pp_yr": _round(observed),
        "tolerance_pp_yr": tolerance,
        "reproduced": abs(observed - expected) <= tolerance,
    }
    totals = {n: item.path.total for n, item in simulated.items()}
    totals["control_cheap"] = cheap.total
    totals["control_cheap60_40"] = mix.total
    eras = _era_specs(specification, panel.periods, wanted=["full"])
    drawdown_eras = _drawdowns_with_difference(
        totals, periods=panel.periods, eras=eras, reference=reference
    )
    return TournamentResult(
        inputs=inputs,
        arms=simulated,
        gold=gold,
        comparisons=comparisons,
        descriptives=descriptives,
        families=families,
        reproduction=reproduction,
        windows=windows,
        drawdown_eras=drawdown_eras,
    )


# --------------------------------------------------------------------------- #
# Reproduction of 025's ladder40 on both panels
# --------------------------------------------------------------------------- #


def reproduce_exp_025(
    specification: Specification,
    *,
    primary: BasisPanel,
    wrappers: Mapping[str, Wrapper],
    rates: FinancingRates,
    tournament: TournamentInputs,
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "reproduction_of_exp_025", where="parameters"), where="r")
    tolerance = _number(block, "tolerance_pp_yr", where="reproduction_of_exp_025")
    dd_tolerance = _number(block, "tolerance_drawdown_pp", where="reproduction_of_exp_025")

    def describe(path: PortfolioPath) -> dict[str, float]:
        summary = drawdown_summary(np.cumprod(1.0 + path.total))
        return {
            "arithmetic_mean_pp_yr": float(np.mean(path.total)) * MONTHS_PER_YEAR * 100.0,
            "growth_log_pp_yr": annualised_log_growth(path.total),
            "max_drawdown_pct": summary.max_drawdown * 100.0,
        }

    def check(
        observed: Mapping[str, float], expected: Mapping[str, JsonValue]
    ) -> dict[str, JsonValue]:
        rows: dict[str, JsonValue] = {}
        ok = True
        for key, value in expected.items():
            want = float(str(value))
            got = observed[key]
            tol = dd_tolerance if key == "max_drawdown_pct" else tolerance
            within = abs(got - want) <= tol
            ok = ok and within
            rows[key] = {"expected": want, "observed": _round(got), "within_tolerance": within}
        rows["reproduced"] = ok
        return rows

    p_tickers, p_weights = _read_weighted(
        _mapping(_at(block, "primary_weights", where="r"), where="p"), where="primary_weights"
    )
    primary_path = simulate_arm(
        primary,
        wrappers,
        rates,
        _engine_costs(specification, rates),
        tickers=p_tickers,
        targets=np.asarray(p_weights, dtype=np.float64),
    )
    t_tickers, t_weights = _read_weighted(
        _mapping(_at(block, "tournament_weights", where="r"), where="t"), where="tournament_weights"
    )
    tournament_path = constant_weight_path(
        tournament.panel,
        tournament.mappings,
        tournament.costs,
        tickers=t_tickers,
        targets=np.asarray(t_weights, dtype=np.float64),
    )
    primary_check = check(
        describe(primary_path), _mapping(_at(block, "primary_expected", where="r"), where="e")
    )
    tournament_check = check(
        describe(tournament_path), _mapping(_at(block, "tournament_expected", where="r"), where="e")
    )
    return {
        "what": str(block.get("what") or ""),
        "primary": primary_check,
        "tournament": tournament_check,
        "reproduced": bool(primary_check["reproduced"]) and bool(tournament_check["reproduced"]),
    }


# --------------------------------------------------------------------------- #
# Regret at forward premia: three closed forms
# --------------------------------------------------------------------------- #


def rsbt_regret_pp_yr(
    *,
    points: float,
    trend_gross_pp_yr: float,
    rsbt_fee_pp_yr: float,
    treasury_financing_pp_yr: float,
    bond_line_fee_pp_yr: float,
) -> float:
    """``X x (t - fee - financing + bond_fee)``: bond kept, trend stacked on the bond line."""
    return points * (
        trend_gross_pp_yr - rsbt_fee_pp_yr - treasury_financing_pp_yr + bond_line_fee_pp_yr
    )


def trend_fund_regret_pp_yr(
    *,
    points: float,
    trend_gross_pp_yr: float,
    delivered_loading: float,
    trend_fund_fee_pp_yr: float,
    bond_line_fee_pp_yr: float,
    bond_excess_pp_yr: float,
) -> float:
    """``X x (lambda t - fee + bond_fee - b)``: the bond sold for an unlevered trend fund."""
    return points * (
        delivered_loading * trend_gross_pp_yr
        - trend_fund_fee_pp_yr
        + bond_line_fee_pp_yr
        - bond_excess_pp_yr
    )


def gde_regret_pp_yr(
    *,
    points: float,
    gold_excess_pp_yr: float,
    gde_fee_pp_yr: float,
    gold_financing_pp_yr: float,
    core_fee_pp_yr: float,
    bond_line_fee_pp_yr: float,
    bond_excess_pp_yr: float,
    wrapper_equity: float = 0.9,
    wrapper_gold: float = 0.9,
) -> float:
    """``X x (0.9 g - fee - 0.9 f_G + 0.9 core_fee + 0.1 bond_fee - 0.1 b)``.

    The wrapper's 0.9 of equity replaces 0.9 X of the core and its 0.1 of
    collateral replaces 0.1 X of the bond line, so equity cancels and a tenth of
    the bond's excess is forgone.
    """
    collateral = 1.0 - wrapper_equity
    return points * (
        wrapper_gold * gold_excess_pp_yr
        - gde_fee_pp_yr
        - wrapper_gold * gold_financing_pp_yr
        + wrapper_equity * core_fee_pp_yr
        + collateral * bond_line_fee_pp_yr
        - collateral * bond_excess_pp_yr
    )


def _variance_drag_pp_yr(arm_total: FloatArray, control_total: FloatArray) -> float:
    return -0.5 * (_volatility(arm_total) ** 2 - _volatility(control_total) ** 2) * 1200.0


def regret_tables(
    specification: Specification,
    *,
    panels: Mapping[str, PanelResult],
    scored_panel: Mapping[str, str],
    families: Mapping[str, tuple[str, ...]],
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "regret", where="parameters"), where="regret")
    reference = _text(parameters, "reference_arm", where="parameters")
    trend_grid = _numbers(_at(block, "trend_gross_premium_grid_pp_yr", where="regret"), where="t")
    trend_central = _number(block, "trend_central_pp_yr", where="regret")
    loadings = _numbers(_at(block, "delivered_trend_loadings", where="regret"), where="l")
    gold_grid = _numbers(_at(block, "gold_excess_grid_pp_yr", where="regret"), where="g")
    gold_central = _number(block, "gold_central_pp_yr", where="regret")
    b = _number(block, "bond_excess_over_cash_pp_yr", where="regret")
    f_t = _number(block, "treasury_financing_pp_yr", where="regret")
    f_g = _number(block, "gold_financing_pp_yr", where="regret")
    rsbt_fee = _number(block, "rsbt_fee_pp_yr", where="regret")
    fund_fee = _number(block, "trend_fund_fee_pp_yr", where="regret")
    gde_fee = _number(block, "gde_fee_pp_yr", where="regret")
    bond_fee = _number(block, "bond_line_fee_pp_yr", where="regret")
    core_fee = _number(block, "core_fee_pp_yr", where="regret")

    def drag_for(arm: str) -> float:
        result = panels[scored_panel[arm]]
        return _variance_drag_pp_yr(result.arms[arm].path.total, result.arms[reference].path.total)

    def points_for(arm: str, attribute: str) -> float:
        result = panels[scored_panel[arm]]
        item, ref = result.arms[arm], result.arms[reference]
        if attribute == "gold":
            return result.gold[arm] - result.gold[reference]
        return float(getattr(item.notional, attribute)) - float(getattr(ref.notional, attribute))

    tables: dict[str, JsonValue] = {}
    central: dict[str, JsonValue] = {}

    rsbt_rows: list[JsonValue] = []
    for arm in families.get("rsbt", ()):
        x = points_for(arm, "trend")
        drag = drag_for(arm)
        cells = []
        for t in trend_grid:
            gap = rsbt_regret_pp_yr(
                points=x,
                trend_gross_pp_yr=t,
                rsbt_fee_pp_yr=rsbt_fee,
                treasury_financing_pp_yr=f_t,
                bond_line_fee_pp_yr=bond_fee,
            )
            cells.append(
                {
                    "trend_gross_pp_yr": t,
                    "central": t == trend_central,
                    "arithmetic_gap_pp_yr": _round(gap, 3),
                    "log_growth_gap_pp_yr": _round(gap + drag, 3),
                }
            )
            if t == trend_central:
                central[arm] = {
                    "arithmetic_gap_pp_yr": _round(gap, 3),
                    "log_growth_gap_pp_yr": _round(gap + drag, 3),
                }
        rsbt_rows.append(
            {
                "arm": arm,
                "points": _round(x, 4),
                "variance_drag_pp_yr": _round(drag, 4),
                "cells": cells,
                "break_even_trend_pp_yr": _round(rsbt_fee + f_t - bond_fee, 3),
                "break_even_trend_log_pp_yr": _round(rsbt_fee + f_t - bond_fee - drag / x, 3),
            }
        )
    tables["rsbt"] = {
        "formula": "X x (t - 0.97 - f_T + 0.05); bond notional unchanged so the bond cancels",
        "rows": rsbt_rows,
    }

    fund_rows: list[JsonValue] = []
    for arm in families.get("trendfund", ()):
        x = points_for(arm, "trend")
        drag = drag_for(arm)
        by_loading: list[JsonValue] = []
        for lam in loadings:
            cells = []
            for t in trend_grid:
                gap = trend_fund_regret_pp_yr(
                    points=x,
                    trend_gross_pp_yr=t,
                    delivered_loading=lam,
                    trend_fund_fee_pp_yr=fund_fee,
                    bond_line_fee_pp_yr=bond_fee,
                    bond_excess_pp_yr=b,
                )
                cells.append(
                    {
                        "trend_gross_pp_yr": t,
                        "central": t == trend_central,
                        "arithmetic_gap_pp_yr": _round(gap, 3),
                        "log_growth_gap_pp_yr": _round(gap + drag, 3),
                    }
                )
                if t == trend_central and lam == 1.0:
                    central[arm] = {
                        "arithmetic_gap_pp_yr": _round(gap, 3),
                        "log_growth_gap_pp_yr": _round(gap + drag, 3),
                    }
            by_loading.append(
                {
                    "delivered_loading": lam,
                    "cells": cells,
                    "break_even_trend_pp_yr": _round((fund_fee - bond_fee + b) / lam, 3),
                }
            )
        fund_rows.append(
            {
                "arm": arm,
                "points": _round(x, 4),
                "variance_drag_pp_yr": _round(drag, 4),
                "by_loading": by_loading,
            }
        )
    tables["trendfund"] = {
        "formula": "X x (lambda t - 0.85 + 0.05 - b); the bond sold forgoes its excess b",
        "bond_excess_over_cash_pp_yr": b,
        "rows": fund_rows,
    }

    gde_rows: list[JsonValue] = []
    for arm in families.get("gde", ()):
        if arm not in scored_panel:
            continue
        x = points_for(arm, "gold") / 0.9
        drag = drag_for(arm)
        cells = []
        for g in gold_grid:
            gap = gde_regret_pp_yr(
                points=x,
                gold_excess_pp_yr=g,
                gde_fee_pp_yr=gde_fee,
                gold_financing_pp_yr=f_g,
                core_fee_pp_yr=core_fee,
                bond_line_fee_pp_yr=bond_fee,
                bond_excess_pp_yr=b,
            )
            cells.append(
                {
                    "gold_excess_pp_yr": g,
                    "central": g == gold_central,
                    "arithmetic_gap_pp_yr": _round(gap, 3),
                    "log_growth_gap_pp_yr": _round(gap + drag, 3),
                }
            )
            if g == gold_central:
                central[arm] = {
                    "arithmetic_gap_pp_yr": _round(gap, 3),
                    "log_growth_gap_pp_yr": _round(gap + drag, 3),
                }
        break_even = (gde_fee + 0.9 * f_g - 0.9 * core_fee - 0.1 * bond_fee + 0.1 * b) / 0.9
        gde_rows.append(
            {
                "arm": arm,
                "points": _round(x, 4),
                "variance_drag_pp_yr": _round(drag, 4),
                "cells": cells,
                "break_even_gold_pp_yr": _round(break_even, 3),
            }
        )
    tables["gde"] = {
        "formula": "X x (0.9 g - 0.20 - 0.9 f_G + 0.9 x 0.03 + 0.1 x 0.05 - 0.1 b); equity cancels",
        "bond_excess_over_cash_pp_yr": b,
        "rows": gde_rows,
    }
    return {
        "what": str(block.get("what") or ""),
        "central_premia": {
            "trend_gross_pp_yr": trend_central,
            "gold_excess_pp_yr": gold_central,
            "bond_excess_over_cash_pp_yr": b,
            "delivered_trend_loading": 1.0,
        },
        "tables": tables,
        "central_gap_by_arm": central,
        "note": (
            "Cells are candidate minus `cautious`, pp/yr, positive when the candidate wins; the "
            "log cell adds half the realised variance difference on the arm's scored primary "
            "panel. No simulation."
        ),
    }


# --------------------------------------------------------------------------- #
# Freeze note 6, read mechanically
# --------------------------------------------------------------------------- #


def freeze_note_reading(
    *,
    specification: Specification,
    panels: Mapping[str, PanelResult],
    scored_panel: Mapping[str, str],
    tournament: TournamentResult,
    regret: Mapping[str, JsonValue],
    candidates: Sequence[str],
) -> dict[str, JsonValue]:
    parameters = _mapping(specification.parameters, where="parameters")
    reference = _text(parameters, "reference_arm", where="parameters")
    reporting = _mapping(_at(parameters, "drawdown_reporting", where="parameters"), where="d")
    tolerance = _number(reporting, "deeper_than_reference_tolerance_pp", where="drawdown_reporting")
    episodes_block = _mapping(_at(parameters, "crisis_episodes", where="parameters"), where="e")
    decision_episodes = [
        str(x) for x in _sequence(_at(episodes_block, "decision_episodes", where="e"), where="d")
    ]
    central = regret["central_gap_by_arm"]
    assert isinstance(central, Mapping)

    def fall_difference(
        rows: Sequence[Mapping[str, JsonValue]], era: str, arm: str
    ) -> float | None:
        for row in rows:
            if row["era"] == era:
                arms = row["arms"]
                assert isinstance(arms, Mapping)
                value = arms.get(arm)
                if isinstance(value, Mapping) and value["minus_reference_pp"] is not None:
                    return float(str(value["minus_reference_pp"]))
        return None

    out: dict[str, JsonValue] = {}
    for arm in candidates:
        result = panels[scored_panel[arm]]
        primary_pair = result.comparisons[arm]["reference"]
        tournament_pair = tournament.comparisons[arm]["reference"]
        a1 = primary_pair.status == "exploratory" and tournament_pair.status == "exploratory"

        falls: dict[str, JsonValue] = {}
        for era in ("full", "from_1934"):
            value = fall_difference(result.drawdown_eras, era, arm)
            if value is not None:
                falls[f"{result.spec.id}:{era}"] = value
        t_value = fall_difference(tournament.drawdown_eras, "full", arm)
        if t_value is not None:
            falls["tournament_1990:full"] = t_value
        a2 = all(isinstance(v, float) and v >= -tolerance for v in falls.values())

        episodes: dict[str, JsonValue] = {}
        a3 = True
        arm_episodes = result.descriptives[arm]["episodes"]
        assert isinstance(arm_episodes, Mapping)
        for name in decision_episodes:
            entry = arm_episodes.get(name)
            if not isinstance(entry, Mapping) or not entry.get("covered"):
                a3 = False
                episodes[name] = None
                continue
            offset = float(str(entry["offset_vs_reference_pp"]))
            episodes[name] = _round(offset, 2)
            a3 = a3 and offset >= 0.0

        gap = primary_pair.gap
        floor = None if gap is None else gap.mde_pp_yr
        forward = central.get(arm)
        forward_gap = (
            None
            if not isinstance(forward, Mapping)
            else float(str(forward["arithmetic_gap_pp_yr"]))
        )
        a4 = forward_gap is not None and floor is not None and forward_gap > floor

        if a1 and a2 and a3 and a4:
            outcome = "a"
            text = "PROPOSED to replace the published cautious vector (draft decision 0015)"
        elif a1 and a2 and a3:
            outcome = "b"
            text = (
                "PROPOSED as a printed option beside the published cautious vector, with its "
                "regret row; the vector is unchanged"
            )
        else:
            outcome = "c"
            text = "leaves decision 0014 as it stands; a scoped result with its floor"
        out[arm] = {
            "scored_primary_panel": result.spec.id,
            "a1_exploratory_on_both_panels": a1,
            "primary_status": primary_pair.status,
            "primary_gap_pp_yr": None if gap is None else _round(gap.gap_pp_yr),
            "primary_floor_pp_yr": None if floor is None else _round(floor),
            "tournament_status": tournament_pair.status,
            "tournament_gap_pp_yr": (
                None if tournament_pair.gap is None else _round(tournament_pair.gap.gap_pp_yr)
            ),
            "tournament_floor_pp_yr": (
                None if tournament_pair.gap is None else _round(tournament_pair.gap.mde_pp_yr)
            ),
            "a2_not_deeper_than_reference_by_more_than_tolerance": a2,
            "worst_fall_minus_reference_pp": falls,
            "a3_decision_episodes_not_below_reference": a3,
            "decision_episode_offsets_pp": episodes,
            "a4_forward_gap_above_floor": a4,
            "forward_gap_at_central_premia_pp_yr": None
            if forward_gap is None
            else _round(forward_gap),
            "outcome": outcome,
            "reading": text,
        }
    return {
        "rule": (
            "Freeze note 6: (a) replace the vector only if the pair is exploratory on both "
            "panels, the fall is not deeper by more than the tolerance on any read window, the "
            "decision episodes are not below the reference, and the forward closed-form gap "
            "clears the arm's own floor; (b) a printed option if all but the forward clause "
            "hold; (c) otherwise 0014 stands."
        ),
        "reference": reference,
        "tolerance_pp": tolerance,
        "decision_episodes": decision_episodes,
        "by_arm": out,
    }


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #


def _fmt(value: float | None, digits: int = 2) -> str:
    return "--" if value is None else f"{value:+.{digits}f}"


def _optional(row: Mapping[str, JsonValue], key: str) -> float | None:
    value = row[key]
    return None if value is None else float(str(value))


def _arm_table(
    arms: Mapping[str, ArmPaths],
    gold: Mapping[str, float],
    descriptives: Mapping[str, Mapping[str, JsonValue]],
) -> list[str]:
    lines = [
        "\n### Arms: notional, growth, drawdown (descriptive)\n",
        "| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | "
        "Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: "
        "| ---: | ---: |",
    ]
    for name, item in arms.items():
        d = descriptives[name]
        n = item.notional
        lines.append(
            f"| `{name}` | {n.gross:.3f} | {n.equity:.3f} | {n.trend:.3f} | {n.bond:.3f} | "
            f"{gold[name]:.3f} | {n.cash:.3f} | {d['arithmetic_mean_pp_yr']} | "
            f"{d['growth_log_pp_yr']} | {d['volatility_pct']} | {d.get('sharpe', '--')} | "
            f"{d['max_drawdown_pct']} | {d['time_under_water_months']} | "
            f"{d.get('terminal_wealth_ratio_vs_reference', '--')} | "
            f"{d.get('terminal_wealth_ratio_vs_cheap', '--')} |"
        )
    return lines


def _difference_table(rows: Sequence[Mapping[str, JsonValue]], *, reference: str) -> list[str]:
    lines = ["\n### Worst fall minus `cautious`, pp, per era (negative is deeper)\n"]
    if not rows:
        return lines
    first = rows[0]["arms"]
    assert isinstance(first, Mapping)
    names = [n for n in first if n != reference and not n.startswith("control_")]
    lines.append("| era | " + " | ".join(f"`{n}`" for n in names) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in names) + " |")
    for row in rows:
        arms = row["arms"]
        assert isinstance(arms, Mapping)
        cells = []
        for n in names:
            v = arms[n]
            assert isinstance(v, Mapping)
            d = v.get("minus_reference_pp")
            cells.append("--" if d is None else f"{float(str(d)):+.2f}")
        lines.append(f"| {row['era']} | " + " | ".join(cells) + " |")
    return lines


def _band_tables(financing: Mapping[str, JsonValue]) -> list[str]:
    bands = financing.get("bands")
    if not isinstance(bands, Mapping):
        return []
    lines: list[str] = []
    for leg, band in bands.items():
        assert isinstance(band, Mapping)
        grid_raw = band["grid_basis_points"]
        assert isinstance(grid_raw, Sequence)
        grid = [str(int(float(str(g)))) for g in grid_raw]
        lines.append(
            f"\n### Financing sensitivity, {leg} basis (bp): gap against `cautious` at each point, "
            "then against the cheap control\n"
        )
        lines.append("| arm | " + " | ".join(grid) + " | sign stable | vs cheap at each point |")
        lines.append("| --- | " + " | ".join("---:" for _ in grid) + " | --- | --- |")
        gaps = band["gaps_pp_yr"]
        signs = band["arm_against_reference_by_point"]
        assert isinstance(gaps, Mapping) and isinstance(signs, Mapping)
        for name, by_control in gaps.items():
            assert isinstance(by_control, Mapping)
            ref = by_control.get("reference")
            cheap = by_control.get("cheap")
            sign = signs.get(name)
            stable = sign["sign_stable"] if isinstance(sign, Mapping) else "--"
            ref_cells = (
                " | ".join(_fmt(float(str(v))) for v in ref)
                if isinstance(ref, Sequence)
                else " | ".join("--" for _ in grid)
            )
            cheap_cells = (
                ", ".join(_fmt(float(str(v))) for v in cheap)
                if isinstance(cheap, Sequence)
                else "--"
            )
            lines.append(f"| `{name}` | {ref_cells} | `{stable}` | {cheap_cells} |")
    return lines


def _regret_markdown(regret: Mapping[str, JsonValue]) -> list[str]:
    tables = regret["tables"]
    assert isinstance(tables, Mapping)
    lines = [
        "\n## Regret at forward premia: candidate minus `cautious`, pp/yr, arithmetic / log "
        "(positive means the candidate wins; closed form, no simulation)\n"
    ]
    rsbt = tables["rsbt"]
    assert isinstance(rsbt, Mapping)
    rows = rsbt["rows"]
    assert isinstance(rows, Sequence)
    if rows:
        lines.append(f"\n### Trend stacked on the bond line: `{rsbt['formula']}`\n")
        first = rows[0]
        assert isinstance(first, Mapping)
        cells0 = first["cells"]
        assert isinstance(cells0, Sequence)
        heads = [
            f"t = {c['trend_gross_pp_yr']}" + (" (central)" if c["central"] else "")
            for c in cells0
            if isinstance(c, Mapping)
        ]
        lines.append(
            "| arm | points | drag | " + " | ".join(heads) + " | break-even t (arith / log) |"
        )
        lines.append("| --- | ---: | ---: | " + " | ".join("---:" for _ in heads) + " | ---: |")
        for row in rows:
            assert isinstance(row, Mapping)
            cells = row["cells"]
            assert isinstance(cells, Sequence)
            lines.append(
                f"| `{row['arm']}` | {row['points']} | {row['variance_drag_pp_yr']} | "
                + " | ".join(
                    f"{_fmt(float(str(c['arithmetic_gap_pp_yr'])))} / "
                    f"{_fmt(float(str(c['log_growth_gap_pp_yr'])))}"
                    for c in cells
                    if isinstance(c, Mapping)
                )
                + f" | {row['break_even_trend_pp_yr']} / {row['break_even_trend_log_pp_yr']} |"
            )
    fund = tables["trendfund"]
    assert isinstance(fund, Mapping)
    rows = fund["rows"]
    assert isinstance(rows, Sequence)
    if rows:
        lines.append(
            f"\n### Trend sold from the bond line: `{fund['formula']}`, b = "
            f"{fund['bond_excess_over_cash_pp_yr']}\n"
        )
        for row in rows:
            assert isinstance(row, Mapping)
            by_loading = row["by_loading"]
            assert isinstance(by_loading, Sequence)
            lines.append(
                f"\n`{row['arm']}`, points {row['points']}, variance drag "
                f"{row['variance_drag_pp_yr']} pp/yr on every log cell.\n"
            )
            first_l = by_loading[0]
            assert isinstance(first_l, Mapping)
            cells0 = first_l["cells"]
            assert isinstance(cells0, Sequence)
            heads = [
                f"t = {c['trend_gross_pp_yr']}" + (" (central)" if c["central"] else "")
                for c in cells0
                if isinstance(c, Mapping)
            ]
            lines.append("| delivered loading | " + " | ".join(heads) + " | break-even t |")
            lines.append("| ---: | " + " | ".join("---:" for _ in heads) + " | ---: |")
            for entry in by_loading:
                assert isinstance(entry, Mapping)
                cells = entry["cells"]
                assert isinstance(cells, Sequence)
                lines.append(
                    f"| {entry['delivered_loading']} | "
                    + " | ".join(
                        f"{_fmt(float(str(c['arithmetic_gap_pp_yr'])))} / "
                        f"{_fmt(float(str(c['log_growth_gap_pp_yr'])))}"
                        for c in cells
                        if isinstance(c, Mapping)
                    )
                    + f" | {entry['break_even_trend_pp_yr']} |"
                )
    gde = tables["gde"]
    assert isinstance(gde, Mapping)
    rows = gde["rows"]
    assert isinstance(rows, Sequence)
    if rows:
        lines.append(
            f"\n### Gold stacked on the stock line: `{gde['formula']}`, b = "
            f"{gde['bond_excess_over_cash_pp_yr']}\n"
        )
        first = rows[0]
        assert isinstance(first, Mapping)
        cells0 = first["cells"]
        assert isinstance(cells0, Sequence)
        heads = [
            f"g = {c['gold_excess_pp_yr']}" + (" (central)" if c["central"] else "")
            for c in cells0
            if isinstance(c, Mapping)
        ]
        lines.append("| arm | points | drag | " + " | ".join(heads) + " | break-even g |")
        lines.append("| --- | ---: | ---: | " + " | ".join("---:" for _ in heads) + " | ---: |")
        for row in rows:
            assert isinstance(row, Mapping)
            cells = row["cells"]
            assert isinstance(cells, Sequence)
            lines.append(
                f"| `{row['arm']}` | {row['points']} | {row['variance_drag_pp_yr']} | "
                + " | ".join(
                    f"{_fmt(float(str(c['arithmetic_gap_pp_yr'])))} / "
                    f"{_fmt(float(str(c['log_growth_gap_pp_yr'])))}"
                    for c in cells
                    if isinstance(c, Mapping)
                )
                + f" | {row['break_even_gold_pp_yr']} |"
            )
    return lines


def _reading_table(reading: Mapping[str, JsonValue]) -> list[str]:
    by_arm = reading["by_arm"]
    assert isinstance(by_arm, Mapping)
    lines = [
        "\n## Freeze note 6, read mechanically\n",
        str(reading["rule"]),
        "",
        "| arm | scored panel | primary gap / floor / status | tournament gap / floor / status | "
        "(a1) | fall minus ref, pp | (a2) | 1977-81 / 2022 offset pp | (a3) | forward gap | (a4) "
        "| outcome |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for arm, row in by_arm.items():
        assert isinstance(row, Mapping)
        falls = row["worst_fall_minus_reference_pp"]
        episodes = row["decision_episode_offsets_pp"]
        assert isinstance(falls, Mapping) and isinstance(episodes, Mapping)
        lines.append(
            f"| `{arm}` | {row['scored_primary_panel']} | {row['primary_gap_pp_yr']} / "
            f"{row['primary_floor_pp_yr']} / `{row['primary_status']}` | "
            f"{row['tournament_gap_pp_yr']} / {row['tournament_floor_pp_yr']} / "
            f"`{row['tournament_status']}` | {row['a1_exploratory_on_both_panels']} | "
            + "; ".join(f"{k} {v}" for k, v in falls.items())
            + f" | {row['a2_not_deeper_than_reference_by_more_than_tolerance']} | "
            + " / ".join(str(v) for v in episodes.values())
            + f" | {row['a3_decision_episodes_not_below_reference']} | "
            f"{row['forward_gap_at_central_premia_pp_yr']} | {row['a4_forward_gap_above_floor']} | "
            f"**{row['outcome']}**: {row['reading']} |"
        )
    return lines


def _reproduction_lines(repro: Mapping[str, JsonValue]) -> list[str]:
    lines = [f"\n## Reproduction of 025's `ladder40`: reproduced `{repro['reproduced']}`\n"]
    for panel in ("primary", "tournament"):
        block = repro[panel]
        assert isinstance(block, Mapping)
        parts = []
        for key, value in block.items():
            if isinstance(value, Mapping):
                parts.append(
                    f"{key} expected {value['expected']} observed {value['observed']} "
                    f"(`{value['within_tolerance']}`)"
                )
        lines.append(f"- {panel}: " + "; ".join(parts))
    return lines


def render_tables(
    panels: Sequence[PanelResult],
    tournament: TournamentResult,
    regret: Mapping[str, JsonValue],
    reading: Mapping[str, JsonValue],
    reproduction: Mapping[str, JsonValue],
    *,
    header: Sequence[str],
    reference: str,
) -> str:
    lines: list[str] = list(header)
    lines.extend(_reproduction_lines(reproduction))
    controls = ["reference", "cheap", "cheap60_40", "leverage_matched"]
    for result in panels:
        p = result.panel
        lines.append(
            f"\n## Panel `{result.spec.id}`: {p.periods[0]}..{p.periods[-1]}, {p.months} months, "
            "own trend book, nominal ten-year bond line, monthly rebalancing\n"
        )
        lines.append(result.spec.note + "\n")
        lines.extend(_arm_table(result.arms, result.gold, result.descriptives))
        lines.extend(
            _drawdown_era_table(result.drawdown_eras, title=f"Drawdown by era, {result.spec.id}")
        )
        lines.extend(_difference_table(result.drawdown_eras, reference=reference))
        lines.extend(_gap_table(result.comparisons, controls))
        names = [w[0] for w in result.windows]
        lines.extend(_window_table(result.comparisons, control="reference", windows=names))
        lines.extend(_window_table(result.comparisons, control="cheap", windows=names))
        lines.extend(_crisis_table(result.descriptives))
        lines.extend(_episode_table(result.descriptives))
        lines.extend(_regime_table(result.regime))
        lines.extend(_band_tables(result.financing))
    lines.extend(_regret_markdown(regret))
    t = tournament.inputs.panel
    lines.append(
        f"\n## Panel `tournament_1990`: {t.periods[0]}..{t.periods[-1]}, {t.months} months, 016f's "
        "basis-mapped funds, AQR TSMOM, LBMA gold, annual rebalancing\n"
    )
    lines.append(
        f"Reproduction of 016f's rec30 minus rec25 log gap: observed "
        f"{tournament.reproduction['observed_pp_yr']} against "
        f"{tournament.reproduction['expected_pp_yr']}, "
        f"reproduced `{tournament.reproduction['reproduced']}`.\n"
    )
    lines.extend(_arm_table(tournament.arms, tournament.gold, tournament.descriptives))
    lines.extend(
        _drawdown_era_table(tournament.drawdown_eras, title="Drawdown by era, tournament panel")
    )
    lines.extend(_difference_table(tournament.drawdown_eras, reference=reference))
    lines.extend(_gap_table(tournament.comparisons, controls))
    names = [w[0] for w in tournament.windows]
    lines.extend(_window_table(tournament.comparisons, control="reference", windows=names))
    lines.extend(_window_table(tournament.comparisons, control="cheap", windows=names))
    lines.extend(_crisis_table(tournament.descriptives))
    lines.extend(_episode_table(tournament.descriptives))
    lines.extend(_reading_table(reading))
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
    raw, gold_levels, gold_provenance, gold_findings = load_series(specification)
    legs = build_legs(
        raw, gold_levels, specification, provenance=gold_provenance, findings=gold_findings
    )
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = read_rates(specification)
    families = read_arm_families(specification)
    reference = _text(parameters, "reference_arm", where="parameters")
    in_estimates = tuple(
        str(x)
        for x in _sequence(_at(parameters, "controls_in_estimates", where="parameters"), where="c")
    )
    findings = [*raw.findings, *gold_findings]

    book_block = _mapping(_at(parameters, "trend_book", where="parameters"), where="trend_book")
    expected_scalar = _number(book_block, "expected_scalar_from_exp_018", where="trend_book")
    scalar_matches = abs(legs.core.trend_scalar - expected_scalar) < 5e-4
    if not scalar_matches:
        findings.append(
            f"trend-book scalar {legs.core.trend_scalar:.4f} does not reproduce 018's "
            f"{expected_scalar}"
        )

    panel_specs = read_panels(specification)
    built = {spec.id: build_panel(legs, spec) for spec in panel_specs}
    inputs = load_tournament_inputs(specification, legs, wrappers, rates)
    findings.extend(inputs.findings)

    # Reproduce 025 and 016f before any candidate is scored.
    reproduction = reproduce_exp_025(
        specification,
        primary=built[panel_specs[0].id],
        wrappers=wrappers,
        rates=rates,
        tournament=inputs,
    )
    if not reproduction["reproduced"]:
        findings.append("025's `ladder40` did NOT reproduce on both panels; see diagnostics")

    results: dict[str, PanelResult] = {}
    for spec in panel_specs:
        results[spec.id] = score_panel(
            spec,
            built[spec.id],
            specification=specification,
            arms=arms,
            wrappers=wrappers,
            rates=rates,
            rng=context.rng,
            full=True,
        )
        findings.extend(built[spec.id].findings)
    tournament = score_tournament(inputs, specification=specification, rng=context.rng, full=True)
    if not tournament.reproduction["reproduced"]:
        findings.append(
            "016f's rec30 minus rec25 log gap did NOT reproduce: "
            f"{tournament.reproduction['observed_pp_yr']} against "
            f"{tournament.reproduction['expected_pp_yr']}"
        )

    # Each candidate's scored primary panel: the first declared panel that carries it.
    candidates = [name for name in arms if name != reference]
    scored_panel: dict[str, str] = {}
    for name in candidates:
        for spec in panel_specs:
            if name in spec.arms:
                scored_panel[name] = spec.id
                break
        else:
            raise TrendFromBondLineError(f"arm {name!r} is on no declared panel")

    regret = regret_tables(
        specification, panels=results, scored_panel=scored_panel, families=families
    )
    reading = freeze_note_reading(
        specification=specification,
        panels=results,
        scored_panel=scored_panel,
        tournament=tournament,
        regret=regret,
        candidates=candidates,
    )

    estimates: list[Estimate] = []
    resolved: list[str] = []
    scored = 0
    method = (
        "stationary block bootstrap on the joint panel, whole rows, mean block 12 months, "
        f"{specification.inference.resamples} resamples, 95% percentile; HAC interval in the notes"
    )
    panel_comparisons: list[tuple[str, Mapping[str, Mapping[str, Comparison]]]] = [
        *((r.spec.id, r.comparisons) for r in results.values()),
        ("tournament_1990", tournament.comparisons),
    ]
    for panel_id, by_arm in panel_comparisons:
        for name, by_control in by_arm.items():
            for control, comparison in by_control.items():
                g, f = comparison.gap, comparison.full
                if g is None or f is None or comparison.identical:
                    continue
                if comparison.status == "exploratory":
                    resolved.append(f"{panel_id}:{name} vs {control}")
                if control not in in_estimates:
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

    reading_rows = reading["by_arm"]
    assert isinstance(reading_rows, Mapping)
    arm_lines: list[str] = []
    for name in candidates:
        row = reading_rows[name]
        assert isinstance(row, Mapping)
        arm_lines.append(
            f"{name}: {_fmt(_optional(row, 'primary_gap_pp_yr'))} pp/yr vs floor "
            f"{_fmt(_optional(row, 'primary_floor_pp_yr'))} `{row['primary_status']}` on "
            f"{row['scored_primary_panel']}, {_fmt(_optional(row, 'tournament_gap_pp_yr'))} vs "
            f"{_fmt(_optional(row, 'tournament_floor_pp_yr'))} `{row['tournament_status']}` on "
            f"the tournament panel, outcome ({row['outcome']})"
        )
    primary = results[panel_specs[0].id]
    ref_row = primary.descriptives[reference]
    summary = (
        f"Engines on the bond line of the published cautious portfolio (`{reference}`, worst fall "
        f"{ref_row['max_drawdown_pct']}% on the {primary.panel.months}-month primary panel, "
        f"{tournament.descriptives[reference]['max_drawdown_pct']}% on the "
        f"{inputs.panel.months}-month tournament panel). Candidate minus cautious: "
        + "; ".join(arm_lines)
        + f". {scored} comparisons scored on three panels; {len(resolved)} separate from their "
        "control by more than the design can resolve. Freeze note 6 outcomes: (a) replaces the "
        "vector, (b) a printed option, (c) 0014 stands. Drawdown, episode and terminal-wealth "
        "tables are descriptive and carry no significance claim."
    )
    freeze_note = (
        "WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS; the tournament panel's tickers "
        "are 016f's basis expressions plus three mapped wrappers. THE BOND LINE IS A NOMINAL "
        "TEN-YEAR TREASURY on every scored panel, modelled as a rolled par bond on FRED GS10 "
        "from 1953-04 and Shiller's long rate before it; at 47 to 50 points of capital that "
        "overstates the line's 1973-74 and 1977-81 losses relative to a TIPS book. The trend "
        "leg is the repository's own 4-asset book scaled by one full-window constant and charged "
        "no trading; AQR's TSMOM on the tournament panel is gross of the vendor's costs. The gold "
        "leg is the LBMA PM fix, spot excess of cash, from 1968-05, and its sub-window includes "
        "the 1971-74 end of the administered dollar price. Every gap names its control and its "
        "panel; drawdown by era is descriptive."
    )
    header = [
        "# Experiment 026: engines on the bond line of the published cautious portfolio",
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
        f"{legs.core.yield_cross_check_max_bp:.2f} bp. Gold leg "
        f"{min(legs.gold)}..{max(legs.gold)}.",
        "",
        "Gap cells read: point estimate, bootstrap and HAC 95% intervals, MDE at 80% power, "
        "log-growth gap, years to distinguish, falsifier status. Descriptive tables carry no "
        "status.",
    ]
    tables = render_tables(
        list(results.values()),
        tournament,
        regret,
        reading,
        reproduction,
        header=header,
        reference=reference,
    )

    diagnostics: dict[str, JsonValue] = {
        "freeze_note": freeze_note,
        "provenance": [dict(r) for r in (*raw.provenance, *gold_provenance)],
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
        "gold_leg": {"first_month": min(legs.gold), "last_month": max(legs.gold)},
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
        "arm_families": {k: list(v) for k, v in families.items()},
        "scored_primary_panel_by_arm": dict(scored_panel),
        "reproduction_of_exp_025": reproduction,
        "panels": [
            *(
                {
                    "id": r.spec.id,
                    "window": f"{r.panel.periods[0]}..{r.panel.periods[-1]}",
                    "months": r.panel.months,
                    "legs": list(r.spec.legs),
                    "panel_findings": list(r.panel.findings),
                    "arms": _panel_json(r.arms, r.comparisons, r.descriptives),
                    "drawdown_by_era": list(r.drawdown_eras),
                    "regime_by_era": list(r.regime),
                    "financing_sensitivity": r.financing,
                    "multiple_testing_families": {k: sorted(v) for k, v in r.families.items()},
                }
                for r in results.values()
            ),
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
        "primary_comparisons": {
            name: {
                "panel": scored_panel[name],
                "arm": name,
                "control": "reference",
                **results[scored_panel[name]].comparisons[name]["reference"].to_json(),
            }
            for name in candidates
        },
        "regret": regret,
        "freeze_note_6_reading": reading,
        "resolved_comparisons": resolved,
        "markdown_tables": tables,
    }
    caveats = (
        "Wrappers are assumed exposure vectors; the tournament tickers are 016f's basis "
        "expressions plus three mapped wrappers. This ranks constructions and cannot rank funds.",
        "The bond line is a nominal ten-year Treasury modelled as a rolled par bond on every "
        "scored panel; no TIPS series exists before 2003. At 47 to 50 points of capital the "
        "1973-74 and 1977-81 episodes read worse than a TIPS book would have.",
        "The own 4-asset trend book is scaled by one full-window constant and charged no "
        "trading cost; AQR's TSMOM is gross of the vendor's trading costs by omission.",
        "Gold is the LBMA PM fix from 1968-05, spot excess of cash, financed at an assumed 30 bp; "
        "the sub-window includes the 1971-74 end of the administered price.",
        "A rejected gap against the cheap control is the price of a drawdown constraint, not a "
        "verdict on the reader who holds it; the regret tables price every arm at forward premia.",
        "Drawdown, months under water, worst-decile, episode and terminal-wealth figures "
        "describe one realised history and carry no significance claim.",
        "No sleeve, fund or portfolio is promoted; any decision 0015 this licenses is PROPOSED.",
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
        prog="python -m portfolio_edge.experiments.exp_026_trend_from_the_bond_line",
        description="Score engines on the bond line of the published cautious portfolio.",
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
