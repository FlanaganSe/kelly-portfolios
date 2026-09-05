"""Selective carry in whole portfolios, reusing Experiment 019's funding machinery.

The new estimand compares fixed carry definitions under identical funding. The
only new construction is a risk calibration using 1969-73 observations. These
are vendor factor returns, not futures contracts or available ETF portfolios.
"""

from __future__ import annotations

import argparse
import math
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.experiments import exp_019_carry_engine as carry
from portfolio_edge.experiments.exp_016_construction_tournament import (
    GapStatistics,
    _mapping,
    _number,
    _sequence,
    _text,
    gap_statistics,
    workspace_root,
)
from portfolio_edge.experiments.exp_018_defensive_engines import arithmetic_gap
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_index
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import CostBasis, Estimate, ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import JsonValue, Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices

FloatArray = NDArray[np.float64]
ENTRY_POINT = "exp_027_selective_carry"


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / f"{ENTRY_POINT}.yaml"


def calibrate_carry(
    series: Mapping[str, Mapping[str, float]],
    columns: Sequence[str],
    *,
    start: str,
    end: str,
    months: int,
    target_volatility: float,
) -> tuple[dict[str, float], dict[str, float]]:
    """Equal component risk, then blend risk; freeze all coefficients after calibration.

    Zero volatility, missing calibration months and non-finite values are errors.
    Missing evaluation months are absent, never backfilled or treated as zeros.
    """
    if not columns or len(set(columns)) != len(columns):
        raise ValueError("carry columns must be nonempty and unique")
    if months < 3 or not math.isfinite(target_volatility) or target_volatility <= 0:
        raise ValueError("calibration requires at least three months and positive risk")
    if month_index(end) - month_index(start) + 1 != months:
        raise ValueError("calibration dates disagree with declared month count")
    common = set(series[columns[0]])
    for column in columns:
        common &= set(series[column])
    calibration = sorted(p for p in common if start <= p <= end)
    if len(calibration) != months:
        raise ValueError("missing calibration observations")
    matrix = np.array([[series[c][p] for c in columns] for p in calibration], dtype=np.float64)
    if not np.all(np.isfinite(matrix)):
        raise ValueError("non-finite calibration return")
    vol = np.std(matrix, axis=0, ddof=1) * math.sqrt(12)
    if np.any(vol <= 0):
        raise ValueError("zero component volatility")
    weights = 1.0 / vol / len(columns)
    blend_vol = float(np.std(matrix @ weights, ddof=1)) * math.sqrt(12)
    if blend_vol <= 0:
        raise ValueError("zero blend volatility")
    weights *= target_volatility / blend_vol
    coefficients = dict(zip(columns, (float(v) for v in weights), strict=True))
    values = {p: sum(coefficients[c] * series[c][p] for c in columns) for p in sorted(common)}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("non-finite evaluation return")
    return values, coefficients


def costed_carry(
    series: Mapping[str, float], *, loading: float, cost_pp_yr: float
) -> dict[str, float]:
    """Costs per delivered risk unit; fixed wrapper fees are charged separately."""
    if not math.isfinite(loading) or not 0 <= loading <= 1:
        raise ValueError("loading must be finite and between zero and one")
    if not math.isfinite(cost_pp_yr) or cost_pp_yr < 0:
        raise ValueError("cost must be finite and nonnegative")
    return {p: loading * (v - cost_pp_yr / 1200) for p, v in series.items()}


def build_selective_legs(
    raw: carry.RawSeries, specification: Specification
) -> tuple[carry.LegLibrary, dict[str, JsonValue]]:
    legs = carry.build_legs(raw, specification)
    parameters = _mapping(specification.parameters, where="parameters")
    calibration = _mapping(parameters["carry_calibration"], where="carry_calibration")
    variants = _mapping(calibration["variants"], where="variants")
    scenarios = _mapping(parameters["carry_scenarios"], where="carry_scenarios")
    sources = {"All Macro Carry": raw.carry, **raw.carry_components}
    results: dict[str, dict[str, float]] = {}
    records: dict[str, JsonValue] = {}
    for variant, raw_columns in variants.items():
        columns = tuple(str(c) for c in _sequence(raw_columns, where=variant))
        values, coefficients = calibrate_carry(
            sources,
            columns,
            start=_text(calibration, "start", where="calibration"),
            end=_text(calibration, "end", where="calibration"),
            months=int(_number(calibration, "months", where="calibration")),
            target_volatility=_number(calibration, "target_volatility_percent", where="cal") / 100,
        )
        records[variant] = {
            "coefficients": dict(coefficients),
            "first": min(values),
            "last": max(values),
        }
        for scenario, raw_settings in scenarios.items():
            settings = _mapping(raw_settings, where=scenario)
            results[f"{variant}_{scenario}"] = costed_carry(
                values,
                loading=_number(settings, "loading", where=scenario),
                cost_pp_yr=_number(settings, "cost_pp_yr", where=scenario),
            )
    return replace(legs, carry=results), records


def read_panels(specification: Specification) -> tuple[carry.PanelSpec, ...]:
    """Read selective source names without 019's closed legacy-variant whitelist."""
    parameters = _mapping(specification.parameters, where="parameters")
    calibration = _mapping(parameters["carry_calibration"], where="calibration")
    variants = _mapping(calibration["variants"], where="variants")
    scenarios = _mapping(parameters["carry_scenarios"], where="scenarios")
    allowed = {f"{v}_{s}" for v in variants for s in scenarios}
    out: list[carry.PanelSpec] = []
    for value in _sequence(parameters["panels"], where="panels"):
        entry = _mapping(value, where="panel")
        source = _text(entry, "carry_source", where="panel")
        if source not in allowed:
            raise ValueError(f"unknown selective carry source {source!r}")
        out.append(
            carry.PanelSpec(
                id=_text(entry, "id", where="panel"),
                role=_text(entry, "role", where="panel"),
                trend_source=_text(entry, "trend_source", where="panel"),
                carry_source=source,
                legs=tuple(str(v) for v in _sequence(entry["legs"], where="legs")),
                arms=tuple(str(v) for v in _sequence(entry["arms"], where="arms")),
                start=str(entry["start"]) if entry.get("start") is not None else None,
                end=str(entry["end"]) if entry.get("end") is not None else None,
                note=str(entry.get("note") or ""),
            )
        )
    return tuple(out)


def rolling_underperformance(
    arm: FloatArray, control: FloatArray, *, window: int = 120
) -> dict[str, JsonValue]:
    """Overlapping realised window frequencies, never independent forecast odds."""
    if arm.shape != control.shape or arm.ndim != 1 or window < 1:
        raise ValueError("paired one-dimensional paths and a positive window required")
    if not np.all(np.isfinite(arm)) or not np.all(np.isfinite(control)):
        raise ValueError("non-finite path")
    if np.any(arm <= -1) or np.any(control <= -1):
        raise ValueError("log-relative wealth undefined after ruin")
    if len(arm) < window:
        return {
            "window_months": window,
            "windows": 0,
            "frequency": None,
            "worst_shortfall_pct": None,
        }
    difference = np.log1p(arm) - np.log1p(control)
    cumulative = np.concatenate(([0.0], np.cumsum(difference)))
    gaps = cumulative[window:] - cumulative[:-window]
    return {
        "window_months": window,
        "windows": len(gaps),
        "frequency": float(np.mean(gaps < 0)),
        "worst_shortfall_pct": float(min(0.0, np.expm1(np.min(gaps))) * 100),
        "median_relative_wealth": float(np.exp(np.median(gaps))),
    }


def gap_record(gap: GapStatistics) -> dict[str, JsonValue]:
    return {
        "gap_pp_yr": gap.gap_pp_yr,
        "interval_pp_yr": list(gap.interval),
        "mde_pp_yr": gap.mde_pp_yr,
        "mde_block_bootstrap_pp_yr": gap.mde_bootstrap_pp_yr,
        "tracking_error_pct": gap.tracking_error_pct,
        "months": gap.months,
    }


def paired_metrics(
    arm: FloatArray,
    control: FloatArray,
    *,
    specification: Specification,
    rng: np.random.Generator,
) -> dict[str, JsonValue]:
    if np.any(arm <= -1) or np.any(control <= -1):
        raise ValueError("cannot compare log growth after ruin")
    indices = stationary_bootstrap_indices(len(arm), 12, specification.inference.resamples, rng)
    return {
        "arithmetic": gap_record(arithmetic_gap(arm, control, indices=indices, confidence=0.95)),
        "log_growth": gap_record(gap_statistics(arm, control, indices=indices, confidence=0.95)),
        "rolling_10year": rolling_underperformance(arm, control),
    }


def _extra_tables(rows: Sequence[Mapping[str, JsonValue]], *, title: str) -> str:
    lines = [
        f"\n## {title}\n",
        "| panel | arm | comparator | arithmetic gap, pp/yr | MDE | log gap [95%], pp/yr | "
        "losing 10-year windows | worst 10-year shortfall |",
        "| --- | --- | --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in rows:
        arithmetic = _mapping(row["arithmetic"], where="arithmetic")
        growth = _mapping(row["log_growth"], where="growth")
        rolling = _mapping(row["rolling_10year"], where="rolling")
        interval = _sequence(growth["interval_pp_yr"], where="interval")
        frequency = rolling["frequency"]
        shortfall = rolling["worst_shortfall_pct"]
        losing = "n/a" if frequency is None else f"{float(str(frequency)):.1%}"
        worst = "n/a" if shortfall is None else f"{float(str(shortfall)):.2f}%"
        lines.append(
            f"| {row['panel']} | {row['arm']} | {row['comparator']} | "
            f"{float(str(arithmetic['gap_pp_yr'])):+.3f} | "
            f"{float(str(arithmetic['mde_pp_yr'])):.3f} | "
            f"{float(str(growth['gap_pp_yr'])):+.3f} [{float(str(interval[0])):+.3f}, "
            f"{float(str(interval[1])):+.3f}] | {losing} | {worst} |"
        )
    lines.append(
        "\nWindow frequencies overlap heavily and are historical descriptions, "
        "not probabilities of future success.\n"
    )
    return "\n".join(lines)


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    raw = carry.load_series(specification)
    legs, calibration = build_selective_legs(raw, specification)
    wrappers = carry.read_wrappers(specification)
    arms = carry.read_arms(specification)
    rates = carry.read_rates(specification)
    results: list[carry.PanelResult] = []
    comparisons: list[dict[str, JsonValue]] = []
    estimates: list[Estimate] = []
    parameters = _mapping(specification.parameters, where="parameters")
    calibration_settings = _mapping(parameters["carry_calibration"], where="calibration")
    calibration_end = _text(calibration_settings, "end", where="calibration")
    for panel_spec in read_panels(specification):
        panel = carry.build_panel(legs, panel_spec)
        if panel.periods[0] <= calibration_end:
            raise ValueError("evaluation overlaps carry calibration")
        result = carry.score_panel(
            panel_spec,
            panel,
            specification=specification,
            arms=arms,
            wrappers=wrappers,
            rates=rates,
            rng=context.rng,
            full=True,
        )
        results.append(result)
        for name, item in result.arms.items():
            if name == "base_trend30":
                continue
            for comparator in ("reference", "cheap"):
                metrics = paired_metrics(
                    item.path.total,
                    item.controls[comparator].total,
                    specification=specification,
                    rng=context.rng,
                )
                row: dict[str, JsonValue] = {
                    "panel": panel_spec.id,
                    "arm": name,
                    "comparator": comparator,
                    **metrics,
                }
                comparisons.append(row)
                growth = _mapping(metrics["log_growth"], where="log_growth")
                interval = _sequence(growth["interval_pp_yr"], where="interval")
                estimates.append(
                    Estimate(
                        name=f"log_growth[{panel_spec.id}:{name} vs {comparator}]",
                        value=_number(growth, "gap_pp_yr", where="log_growth"),
                        interval=(float(str(interval[0])), float(str(interval[1]))),
                        interval_method=(
                            "paired stationary block bootstrap, mean block 12 months, "
                            "2000 resamples, 95%"
                        ),
                        units="percentage points per year",
                        n_obs=panel.months,
                        cost_basis=CostBasis.NET_OPTIMISTIC
                        if panel_spec.id.endswith("_gross")
                        else CostBasis.NET_PESSIMISTIC,
                        notes=(
                            "Gross omits internal trading costs; other variants assume them; "
                            "no tax or delivery validation."
                        ),
                    )
                )
    by_id = {result.spec.id: result for result in results}
    cross: list[dict[str, JsonValue]] = []
    for result in results:
        if result.spec.id.startswith("all_macro_"):
            continue
        prefix = (
            "bond_commodity_" if result.spec.id.startswith("bond_commodity_") else "commodity_only_"
        )
        comparator_id = "all_macro_" + result.spec.id.removeprefix(prefix)
        other_result = by_id[comparator_id]
        if result.panel.periods != other_result.panel.periods:
            raise ValueError("carry variants must be compared on identical months")
        for name, item in result.arms.items():
            if name == "base_trend30":
                continue
            metrics = paired_metrics(
                item.path.total,
                other_result.arms[name].path.total,
                specification=specification,
                rng=context.rng,
            )
            cross.append(
                {"panel": result.spec.id, "arm": name, "comparator": comparator_id, **metrics}
            )
    header = [
        "# Experiment 027: selective carry in whole portfolios",
        "",
        f"Run `{context.run_id}`; specification `{specification.spec_hash}`.",
        "",
        "Vendor gross factors, hypothetical wrappers, pre-1974 carry risk calibration. "
        "Reference is 019's 70/30 proxy, not the current published portfolios. "
        "No retail delivery, independent replication, tax or promotion claim. "
        "Own trend retains 019's full-window scalar; internal trading costs are omitted. "
        "The 2013+ window is inside the 2021 vendor reconstruction, not untouched evidence. "
        "Frozen inherited source prose saying components enter no arm is superseded "
        "by explicit variant definitions. Haircuts are assumptions, not cost evidence. "
        "MDE measures resolution, not an allocation rule. "
        "Partial crisis coverage is flagged; it does not represent the complete event.",
        "",
        f"Carry calibration: `{calibration}`.",
        "",
        "Gross omits INTERNAL carry costs; wrapper fees and financing are always charged. "
        "Costed assumes 2 pp/yr; costed_loading multiplies gross return AND internal costs "
        "by 0.681, with wrapper fees unchanged.",
    ]
    tables = carry.render_tables(results, header=header, components={})
    tables += _extra_tables(comparisons, title="Paired growth and historical ten-year outcomes")
    tables += _extra_tables(
        cross, title="Selective carry against all-macro carry, identical funding"
    )
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary="Three carry definitions, funding rules, windows and cost/loading "
        f"scenarios: {len(results)} panels. {len(cross)} paired selective-versus-all-macro "
        "comparisons; no winner selected or fund promoted. Results report growth, tail offsets, "
        "drawdowns and overlapping ten-year shortfalls beside mean-gap detection floors.",
        estimates=tuple(estimates),
        diagnostics={
            "provenance": [dict(v) for v in raw.provenance],
            "source_findings": list(raw.findings),
            "calibration": calibration,
            "panels": [carry._panel_json(result) for result in results],
            "paired_metrics": comparisons,
            "cross_variant_comparisons": cross,
            "markdown_tables": tables,
        },
        caveats=(
            "Earlier component results motivated selection; no untouched holdout.",
            "All Macro Carry calibration has three classes; evaluation has four.",
            "1969-73 risk scaling is one short calibration, not stable delivered ETF exposure.",
            "Cost 2 pp/yr and loading 0.681 are assumptions, not bounds on actual implementation.",
            "Vendor reconstructs history, including years after 2013; no point-in-time claim.",
            "Notionals label risk units, not measured futures gearing or margin.",
            "Trend trading and all taxes omitted; tail and rolling-window results descriptive.",
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--view-results", action="store_true")
    arguments = parser.parse_args(argv)
    specification = load_specification(arguments.specification)
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    ledger = Ledger()
    outcome = run_experiment(
        specification,
        registry=registry,
        ledger=ledger,
        dataset_manifest_hashes=carry._manifest_hashes(specification),
        origin=Origin.AI,
    )
    assert outcome.result is not None
    path = workspace_root() / "artifacts" / outcome.run_id / "tables.md"
    path.write_text(str(outcome.result.diagnostics["markdown_tables"]), encoding="utf-8")
    if arguments.view_results:
        ledger.record_results_viewed(
            outcome.run_id, origin=Origin.AI, notes="CLI summary inspected"
        )
    print(f"run {outcome.run_id}: {outcome.result.status.value}\n{outcome.result.summary}\n{path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
