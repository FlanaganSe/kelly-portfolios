"""A fixed allocation grid inside each published portfolio's US equity capital budget."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

from portfolio_edge.experiments.exp_028_tilt_estimand_audit import RecordingCache
from portfolio_edge.experiments.exp_030_live_fund_portfolios import (
    Paths,
    comparison,
    complete_panel,
    execute,
    mapping,
    metrics,
    month_grid,
    numbers,
)
from portfolio_edge.experiments.ledger import Ledger
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import CostBasis, Estimate, ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import JsonValue, Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.studies._loading_windows_tables import Fund, fund_returns

ENTRY_POINT = "exp_031_live_equity_allocation_grid"
RESOLUTION_MULTIPLIER = 2.801585


def sequence(value: JsonValue) -> Sequence[JsonValue]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("expected a sequence")
    return value


def allocation_grid(
    base: Mapping[str, float],
    patterns: Mapping[str, Sequence[float]],
    *,
    momentum_step: float,
    momentum_multipliers: Sequence[float],
) -> tuple[dict[str, dict[str, float]], list[dict[str, JsonValue]]]:
    """Generate fixed funded weights; record infeasible choices before observing returns."""
    if not all(math.isfinite(w) and w >= 0 for w in base.values()):
        raise ValueError("base weights must be finite nonnegative decimals")
    if not math.isclose(sum(base.values()), 1, abs_tol=1e-12):
        raise ValueError("base weights must sum to one")
    if base.get("AVUV", 0) or base.get("SPMO", 0):
        raise ValueError("frozen starting portfolio must have no AVUV or SPMO")
    if base.get("VTV", 0) <= 0 or not math.isfinite(momentum_step) or momentum_step <= 0:
        raise ValueError("positive original VTV and momentum step required")
    value = base["VTV"]
    budget = base.get("VTI", 0) + value
    arms: dict[str, dict[str, float]] = {}
    excluded: list[dict[str, JsonValue]] = []
    for pattern, ratio in patterns.items():
        if len(ratio) != 2 or any(not math.isfinite(x) or x < 0 for x in ratio):
            raise ValueError("value pattern needs two finite nonnegative multiples")
        vtv, avuv = (value * x for x in ratio)
        for multiple in momentum_multipliers:
            if not math.isfinite(multiple) or multiple < 0:
                raise ValueError("momentum multiple must be finite and nonnegative")
            name = f"{pattern}_m{multiple:g}"
            if name in arms:
                raise ValueError("duplicate grid arm")
            spmo = momentum_step * multiple
            vti = budget - vtv - avuv - spmo
            if vti < -1e-12:
                excluded.append(
                    {"arm": name, "VTV": vtv, "AVUV": avuv, "SPMO": spmo, "unfunded_weight": -vti}
                )
                continue
            weights = {t: w for t, w in base.items() if t not in ("VTI", "VTV")}
            weights.update({"VTI": max(0, vti), "VTV": vtv, "AVUV": avuv, "SPMO": spmo})
            arms[name] = {t: w for t, w in weights.items() if w > 0}
    return arms, excluded


def paired_result(arm: Paths, benchmark: Paths) -> dict[str, JsonValue]:
    """Actual complete-path metrics and conditional paired resampling uncertainty."""
    actual = comparison(arm, benchmark)
    boot = 1200 * np.mean(np.log1p(arm.returns[1:]) - np.log1p(benchmark.returns[1:]), axis=1)
    low, high = (float(x) for x in np.quantile(boot, [0.025, 0.975]))
    return {
        **actual,
        "interval_pp_yr": [low, high],
        "resolution80_pp_yr": RESOLUTION_MULTIPLIER * float(np.std(boot, ddof=1)),
    }


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    root = Path(__file__).resolve().parents[3]
    p = mapping(specification.parameters)
    for file_key, hash_key in (
        ("base_specification", "base_specification_sha256"),
        ("engine_path", "engine_sha256"),
    ):
        dependency_bytes = (root / str(p[file_key])).read_bytes()
        if hashlib.sha256(dependency_bytes).hexdigest() != p[hash_key]:
            raise ValueError(f"frozen dependency changed: {p[file_key]}")
    base_specification = load_specification(root / str(p["base_specification"]))
    base_parameters = mapping(base_specification.parameters)
    patterns = {
        name: [float(str(x)) for x in sequence(raw)]
        for name, raw in mapping(p["value_patterns"]).items()
    }
    multiples = [float(str(x)) for x in sequence(p["momentum_multipliers"])]
    costs = [float(str(x)) for x in sequence(base_parameters["execution_roundtrip_bp"])]
    definitions = mapping(base_parameters["portfolios"])
    grids: dict[str, dict[str, dict[str, float]]] = {}
    omitted: dict[str, JsonValue] = {}
    for portfolio, raw in definitions.items():
        definition = mapping(raw)
        grids[portfolio], exclusions = allocation_grid(
            numbers(definition["weights"]),
            patterns,
            momentum_step=float(str(definition["spmo_weight"])),
            momentum_multipliers=multiples,
        )
        expected = int(str(mapping(p["expected_feasible_arm_counts"])[portfolio]))
        if len(grids[portfolio]) != expected:
            raise ValueError("grid no longer matches predeclared feasible arm count")
        omitted[portfolio] = list(exclusions)
    cache = RecordingCache()
    returns: dict[str, dict[str, float]] = {}
    for ticker, raw in mapping(base_parameters["fund_ids"]).items():
        identifiers = sequence(raw)
        fund = Fund(
            ticker=ticker,
            series_id=str(identifiers[0]),
            class_id=str(identifiers[1]),
            inception=str(identifiers[2]) if len(identifiers) == 3 else None,
        )
        returns[ticker] = fund_returns(cache, fund)
    records: list[JsonValue] = []
    estimates: list[Estimate] = []
    baseline = str(p["baseline_arm"])
    lines = [
        "# Fixed US equity allocation grid",
        "",
        "Exploratory historical comparisons, no "
        "selected winner. Non-US, trend and bond holdings remain fixed within each grid.",
        "",
        "NAV includes internal fund costs. Investor execution is 5/25 bp roundtrip, "
        "half per traded dollar, with paid initial purchase and annual rebalancing.",
        "",
        "Each calendar slice resets initial purchase and annual clock. Slices are previously "
        "observed, not independent holdouts. Month-end drawdown misses intramonth lows.",
        "",
        "Paired intervals rerun joint six-month stationary bootstrap paths (2000 draws). "
        "They are descriptive, unadjusted across the grid and not forecast probabilities.",
        "",
        "The cheap control is a separate 65/35 VTI/VXUS mix scaled to SCHP capital; "
        "it is not beta-, leverage- or risk-matched. 'No value' removes VTV/AVUV only; "
        "other holdings retain their own value exposure.",
        "",
        "## Predeclared arms",
        "",
    ]
    for portfolio, weights in grids.items():
        lines.extend(
            [
                f"### {portfolio}",
                "",
                "| Arm | VTI % | VTV % | AVUV % | SPMO % |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for arm, w in weights.items():
            lines.append(
                f"| {arm} | "
                + " | ".join(f"{100 * w.get(t, 0):g}" for t in ("VTI", "VTV", "AVUV", "SPMO"))
                + " |"
            )
        lines.extend(["", f"Infeasible before returns: `{omitted[portfolio]}`.", ""])
    for portfolio, grid in grids.items():
        definition = mapping(definitions[portfolio])
        bond = float(str(definition["bond_weight"]))
        us = float(str(base_parameters["cheap_equity_us_share"]))
        arms = dict(grid)
        arms["cheap"] = {"VTI": (1 - bond) * us, "VXUS": (1 - bond) * (1 - us)}
        if bond:
            arms["cheap"]["SCHP"] = bond
        tickers = sorted({ticker for w in arms.values() for ticker in w})
        windows = mapping(mapping(p["windows"])[portfolio])
        for window, raw in windows.items():
            bounds = sequence(raw)
            months = month_grid(str(bounds[0]), str(bounds[1]))
            panel = complete_panel(returns, tickers, months)
            indices = stationary_bootstrap_indices(
                len(months), 6, specification.inference.resamples, context.rng
            )
            joint = np.concatenate((panel[None], panel[indices]), axis=0)
            for cost in costs:
                paths = {
                    arm: execute(
                        joint,
                        np.array([w.get(t, 0) for t in tickers]),
                        roundtrip_bp=cost,
                        rebalance_every=int(str(base_parameters["rebalance_every_months"])),
                    )
                    for arm, w in arms.items()
                }
                lines.extend(
                    [
                        f"## {portfolio} / {window} / {cost:g} bp",
                        "",
                        f"{months[0]} to {months[-1]}, {len(months)} months.",
                        "",
                        "| Arm | CAGR % | Drawdown % | Log gap vs unchanged pp/yr [95%] | "
                        "Resolution80 pp/yr | Wealth ratio | TE pp/yr | Losing rolling12m | "
                        "Worst rolling12m ratio | Log gap vs cheap pp/yr [95%] |",
                        "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
                    ]
                )
                for arm, path in paths.items():
                    measured = metrics(path)
                    primary = paired_result(path, paths[baseline])
                    cheap = paired_result(path, paths["cheap"])
                    records.append(
                        {
                            "portfolio": portfolio,
                            "window": window,
                            "roundtrip_bp": cost,
                            "months": list(months),
                            "arm": arm,
                            "weights": dict(arms[arm]),
                            "metrics": measured,
                            "vs_unchanged": primary,
                            "vs_cheap": cheap,
                            "wealth": path.wealth[0].tolist(),
                        }
                    )
                    for label, paired in (("unchanged", primary), ("cheap", cheap)):
                        if (arm == baseline and label == "unchanged") or arm == label:
                            continue
                        interval = sequence(paired["interval_pp_yr"])
                        estimates.append(
                            Estimate(
                                name=f"log_gap[{portfolio}|{window}|{cost:g}bp|{arm} vs {label}]",
                                value=float(str(paired["log_gap_pp_yr"])),
                                units="percentage points per year",
                                n_obs=len(months),
                                interval=(float(str(interval[0])), float(str(interval[1]))),
                                interval_method="joint-row stationary bootstrap; reexecuted paths; "
                                "6-month mean blocks, 2000 draws, unadjusted percentile 95%",
                                cost_basis=CostBasis.NET_OPTIMISTIC
                                if cost == 5
                                else CostBasis.NET_PESSIMISTIC,
                            )
                        )

                    def gap_text(paired: Mapping[str, JsonValue]) -> str:
                        interval = sequence(paired["interval_pp_yr"])
                        return (
                            f"{float(str(paired['log_gap_pp_yr'])):+.3f} "
                            f"[{float(str(interval[0])):+.3f}, {float(str(interval[1])):+.3f}]"
                        )

                    lines.append(
                        f"| {arm} | {measured['cagr_percent']:.3f} | "
                        f"{measured['max_drawdown_percent']:.3f} | {gap_text(primary)} | "
                        f"{float(str(primary['resolution80_pp_yr'])):.3f} | "
                        f"{float(str(primary['terminal_wealth_ratio'])):.4f} | "
                        f"{float(str(primary['tracking_error_pp_yr'])):.3f} | "
                        f"{float(str(primary['rolling_12m_underperformance_fraction'])):.1%} | "
                        f"{float(str(primary['rolling_12m_worst_wealth_ratio'])):.4f} | "
                        f"{gap_text(cheap)} |"
                    )
                lines.append("")
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=f"{len(records)} fixed arm/cost/calendar-slice outcomes. All feasible choices "
        "reported; none selected or promoted. Actual NAV and paid execution preserve full "
        "portfolio covariance while varying only the original US equity capital budget.",
        estimates=tuple(estimates),
        diagnostics={
            "source_artifacts": list(cache.sources.values()),
            "grids": grids,
            "omitted_infeasible": omitted,
            "rows": records,
            "tables": "\n".join(lines),
        },
        caveats=(
            "Previously observed 54/30-month histories and 27/15-month halves are not holdouts.",
            "Grid intervals are unadjusted; no confidence attaches to a retrospectively best arm.",
            "Every slice restarts initial purchase and annual clock; not a switching strategy.",
            "Only VTI,VTV,AVUV,SPMO change; other funds can retain value/momentum exposure.",
            "Cheap controls are not risk-, beta- or leverage-matched; no investor taxes.",
            "Source bytes are identified; this is not point-in-time fund-universe selection.",
        ),
    )


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    specification = load_specification(root / "experiments" / f"{ENTRY_POINT}.yaml")
    ledger = Ledger()
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    outcome = run_experiment(specification, registry=registry, ledger=ledger)
    assert outcome.result is not None
    directory = root / "artifacts" / outcome.run_id
    (directory / "tables.md").write_text(
        str(outcome.result.diagnostics["tables"]), encoding="utf-8"
    )
    ledger.record_results_viewed(outcome.run_id, notes="fixed allocation grid tables inspected")
    print(f"run {outcome.run_id}: {directory / 'tables.md'}")


if __name__ == "__main__":
    main()
