"""Complete live-fund portfolio paths, fixed substitutions and explicit execution."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

from portfolio_edge.experiments.exp_028_tilt_estimand_audit import RecordingCache
from portfolio_edge.experiments.exp_030_live_fund_portfolios import (
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

ENTRY_POINT = "exp_032_momentum_implementations"


def substitutions(base: Mapping[str, float], momentum_weight: float) -> dict[str, dict[str, float]]:
    """Allocate the same funded capital to either implementation or their equal mixture."""
    if not np.isfinite(momentum_weight) or not 0 < momentum_weight <= base.get("VTI", 0):
        raise ValueError("momentum allocation requires positive available VTI funding")
    if any(not np.isfinite(w) or w < 0 for w in base.values()) or not np.isclose(
        sum(base.values()), 1, rtol=0, atol=1e-12
    ):
        raise ValueError("base weights must be finite nonnegative and sum to one")
    if base.get("SPMO", 0) or base.get("MTUM", 0):
        raise ValueError("base must not already hold the momentum implementations")
    arms = {"unchanged": dict(base)}
    for name, spmo_share in (("spmo", 1.0), ("mtum", 0.0), ("equal_mix", 0.5)):
        weights = dict(base)
        weights["VTI"] -= momentum_weight
        if spmo_share:
            weights["SPMO"] = momentum_weight * spmo_share
        if spmo_share < 1:
            weights["MTUM"] = momentum_weight * (1 - spmo_share)
        arms[name] = weights
    return arms


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    parameters = mapping(specification.parameters)
    portfolios = mapping(parameters["portfolios"])
    cache = RecordingCache()
    funds: dict[str, Fund] = {}
    for ticker, raw in mapping(parameters["fund_ids"]).items():
        if not isinstance(raw, Sequence) or isinstance(raw, str) or len(raw) not in (2, 3):
            raise ValueError("fund ids require series, class and optional inception")
        funds[ticker] = Fund(
            ticker=ticker,
            series_id=str(raw[0]),
            class_id=str(raw[1]),
            inception=str(raw[2]) if len(raw) == 3 else None,
        )
    returns = {ticker: fund_returns(cache, fund) for ticker, fund in funds.items()}
    estimates: list[Estimate] = []
    output: dict[str, JsonValue] = {}
    lines = [
        "# Momentum implementation portfolio comparisons",
        "",
        "All comparisons are exploratory.",
        "",
    ]
    raw_costs = parameters["execution_roundtrip_bp"]
    if not isinstance(raw_costs, Sequence) or isinstance(raw_costs, str):
        raise ValueError("execution costs must be a sequence")
    for name, raw in portfolios.items():
        definition = mapping(raw)
        months = month_grid(str(definition["first"]), str(definition["last"]))
        arms = substitutions(
            numbers(definition["weights"]), float(str(definition["momentum_weight"]))
        )
        bond = float(str(definition["bond_weight"]))
        us = float(str(parameters["cheap_equity_us_share"]))
        arms["cheap"] = {"VTI": (1 - bond) * us, "VXUS": (1 - bond) * (1 - us)}
        if bond:
            arms["cheap"]["SCHP"] = bond
        tickers = sorted({ticker for weights in arms.values() for ticker in weights})
        panel = complete_panel(returns, tickers, months)
        indices = stationary_bootstrap_indices(
            len(months),
            n_resamples=specification.inference.resamples,
            mean_block_length=6,
            rng=context.rng,
        )
        joint = np.concatenate((panel[None, :, :], panel[indices]), axis=0)
        lines += [f"## {name}: {months[0]} to {months[-1]} ({len(months)} months)", ""]
        for raw_cost in raw_costs:
            cost = float(str(raw_cost))
            paths = {
                arm: execute(
                    joint,
                    np.asarray([weights.get(ticker, 0) for ticker in tickers]),
                    roundtrip_bp=cost,
                    rebalance_every=int(str(parameters["rebalance_every_months"])),
                )
                for arm, weights in arms.items()
            }
            key = f"{name}|{cost:g}bp"
            rows: dict[str, JsonValue] = {}
            lines += [
                f"### {cost:g} bp roundtrip execution",
                "",
                "| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
            for arm, path in paths.items():
                measured = metrics(path)
                rows[arm] = {
                    "weights": dict(arms[arm]),
                    "metrics": dict(measured),
                    "wealth": path.wealth[0].tolist(),
                }
                lines.append(
                    f"| {arm} | {measured['log_growth_pp_yr']:+.3f} | "
                    f"{measured['cagr_percent']:+.3f} | {measured['arithmetic_pp_yr']:+.3f} | "
                    f"{measured['max_drawdown_percent']:.3f} |"
                )
            lines += [
                "",
                "| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | "
                "Rolling 12m losing fraction | Worst 12m wealth ratio |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
            paired: dict[str, JsonValue] = {}
            for arm in arms:
                if arm == "cheap":
                    continue
                for benchmark in ("unchanged", "cheap", "spmo", "mtum"):
                    if benchmark in ("spmo", "mtum") and arm in ("unchanged", "spmo"):
                        continue
                    if arm == benchmark:
                        continue
                    label = f"{arm} vs {benchmark}"
                    stats = comparison(paths[arm], paths[benchmark])
                    boot = 1200 * np.mean(
                        np.log1p(paths[arm].returns[1:]) - np.log1p(paths[benchmark].returns[1:]),
                        axis=1,
                    )
                    lo, hi = (float(x) for x in np.quantile(boot, [0.025, 0.975]))
                    paired[label] = {**stats, "log_gap_interval": [lo, hi]}
                    estimates.append(
                        Estimate(
                            name=f"log_growth_gap[{key}|{label}]",
                            value=stats["log_gap_pp_yr"],
                            units="percentage points per year",
                            interval=(lo, hi),
                            n_obs=len(months),
                            interval_method="paired stationary bootstrap, joint fund rows; "
                            "reexecuted paths; mean block 6 months, 2000 draws, percentile 95%",
                            cost_basis=CostBasis.NET_OPTIMISTIC
                            if cost == 5
                            else CostBasis.NET_PESSIMISTIC,
                        )
                    )
                    lines.append(
                        f"| {label} | {stats['log_gap_pp_yr']:+.3f} "
                        f"[{lo:+.3f}, {hi:+.3f}] | {stats['terminal_wealth_ratio']:.4f} | "
                        f"{stats['tracking_error_pp_yr']:.3f} | "
                        f"{stats['rolling_12m_underperformance_fraction']:.1%} | "
                        f"{stats['rolling_12m_worst_wealth_ratio']:.4f} |"
                    )
            lines.append("")
            output[key] = {"months": list(months), "arms": rows, "comparisons": paired}
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary="Fixed momentum implementations evaluated inside complete published portfolios "
        "using filed NAV total returns, drifting weights and paid annual execution. Short common "
        "histories and descriptive intervals cannot establish a future winner.",
        estimates=tuple(estimates),
        diagnostics={
            "portfolios": output,
            "source_artifacts": list(cache.sources.values()),
            "fund_ids": parameters["fund_ids"],
            "methodology_sources": parameters["methodology_sources"],
            "chronology_limit": parameters["chronology_limit"],
            "tables": "\n".join(lines),
        },
        caveats=(
            str(parameters["chronology_limit"]),
            "Current surviving products selected after inspecting overlapping history; no holdout.",
            "Broad 65/35 controls preserve SCHP capital weights, not risk, beta or leverage.",
            "Returns include fund internal costs; investor execution is assumed, taxes omitted.",
            "Roundtrip 5/25 bp means 2.5/12.5 bp per dollar on each side; no exit sale.",
            "Initial purchase cost enters first return and first rolling twelve-month window.",
            "Month-end drawdown misses intramonth lows; only 30 or 54 months cover few regimes.",
            "Rolling underperformance describes overlapping realised windows, not forecast odds.",
            "Source hashes identify exact bytes, not historical availability of revised filings.",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--specification", type=Path, default=Path("experiments") / f"{ENTRY_POINT}.yaml"
    )
    args = parser.parse_args()
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    ledger = Ledger()
    outcome = run_experiment(
        load_specification(args.specification), registry=registry, ledger=ledger
    )
    assert outcome.result is not None
    (Path("artifacts") / outcome.run_id / "tables.md").write_text(
        str(outcome.result.diagnostics["tables"]), encoding="utf-8"
    )
    ledger.record_results_viewed(outcome.run_id, notes="live-fund comparison tables inspected")
    print(f"run {outcome.run_id}: artifacts/{outcome.run_id}/tables.md")


if __name__ == "__main__":
    main()
