"""Actual trend wrapper funding alternatives with explicit investor execution."""

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

ENTRY_POINT = "exp_034_live_trend_funding"


def substitutions(base: Mapping[str, float]) -> dict[str, dict[str, float]]:
    """Compare capital-funded wrappers without imposing equal derivative risk."""
    if any(not np.isfinite(w) or w < 0 for w in base.values()) or not np.isclose(
        sum(base.values()), 1, rtol=0, atol=1e-12
    ):
        raise ValueError("base weights must be finite nonnegative and sum to one")
    stacked, bond = base.get("RSST", 0), base.get("SCHP", 0)
    if stacked <= 0 or bond <= 0:
        raise ValueError("positive RSST and SCHP funding required")
    if any(base.get(t, 0) for t in ("DBMF", "KMLM", "SGOV")):
        raise ValueError("base must not already hold the alternative funds")
    plain = dict(base)
    plain.pop("RSST")
    plain["VTI"] = plain.get("VTI", 0) + stacked
    arms = {"unchanged": dict(base), "no_trend": plain}
    available = min(stacked, bond)
    for source, amount in (("direct", stacked), ("bond", available)):
        for implementation, dbmf_share in (("dbmf", 1.0), ("kmlm", 0.0), ("mix", 0.5)):
            weights = dict(base if source == "direct" else plain)
            if source == "direct":
                weights.pop("RSST")
            else:
                weights["SCHP"] -= amount
            if dbmf_share:
                weights["DBMF"] = amount * dbmf_share
            if dbmf_share < 1:
                weights["KMLM"] = amount * (1 - dbmf_share)
            arms[f"{source}_{implementation}"] = weights
    cash = dict(plain)
    cash["SCHP"] -= available
    cash["SGOV"] = available
    arms["bond_cash"] = cash
    return arms


def intended_capital(weights: Mapping[str, float]) -> dict[str, float]:
    """Capital at targets, not fitted beta or total derivative notional."""
    return {
        "stock_capital": sum(
            weights.get(t, 0) for t in ("VTI", "VXUS", "VTV", "AVDV", "IDMO", "AVES", "RSST")
        ),
        "schp_capital": weights.get("SCHP", 0),
        "cash_fund_capital": weights.get("SGOV", 0),
        "standalone_trend_capital": weights.get("DBMF", 0) + weights.get("KMLM", 0),
        "stacked_trend_capital": weights.get("RSST", 0),
    }


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
        "# Trend wrapper and funding portfolio comparisons",
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
        arms = substitutions(numbers(definition["weights"]))
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
                "| Arm | Intended stock % | SCHP % | SGOV % | "
                "Standalone trend % | Stacked trend % |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
            for arm, weights in arms.items():
                exposure = intended_capital(weights)
                lines.append(
                    f"| {arm} | "
                    + " | ".join(f"{100 * value:.1f}" for value in exposure.values())
                    + " |"
                )
            lines += [
                "",
                "Stock includes RSST's intended stock capital. Stacked trend overlaps "
                "that capital; other columns are funded allocations, not matched risk.",
                "",
            ]
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
                    "intended_capital": intended_capital(arms[arm]),
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
                for benchmark in ("unchanged", "cheap", "no_trend", "bond_cash"):
                    if benchmark == "bond_cash" and arm not in (
                        "bond_dbmf",
                        "bond_kmlm",
                        "bond_mix",
                    ):
                        continue
                    if benchmark == "no_trend" and arm == "unchanged":
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
        summary="Fixed trend wrapper funding evaluated inside complete portfolios "
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
            str(parameters["funding_rule"]),
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
