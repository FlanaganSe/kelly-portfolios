"""Fixed small crash-hedge portfolios using the tested experiment030 execution engine."""

from __future__ import annotations

import argparse
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

ENTRY_POINT = "exp_035_funded_crash_hedges"


def sequence(value: JsonValue) -> Sequence[JsonValue]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("expected a sequence")
    return value


def funded_arms(
    base: Mapping[str, float], funding: str, hedges: Sequence[str], weight: float
) -> dict[str, dict[str, float]]:
    """Remove actual funding capital before adding any hedge or control."""
    if not 0 < weight < 1 or not np.isclose(sum(base.values()), 1):
        raise ValueError("fully funded positive sleeve required")
    if funding == "proportional":
        reduced = {t: w * (1 - weight) for t, w in base.items()}
    elif base.get(funding, 0) >= weight:
        reduced = dict(base)
        reduced[funding] -= weight
    else:
        raise ValueError("insufficient funding capital")
    sleeves = {
        **{t: {t: 1.0} for t in hedges},
        "bills": {"BIL": 1.0},
        "duration": {"IEF": 0.9, "BIL": 0.1},
    }
    arms = {"unchanged": dict(base)}
    for name, sleeve in sleeves.items():
        weights = dict(reduced)
        for ticker, fraction in sleeve.items():
            weights[ticker] = weights.get(ticker, 0) + weight * fraction
        arms[name] = weights
    return arms


def episodes(
    months: Sequence[str], path: Paths, definitions: Mapping[str, JsonValue]
) -> dict[str, JsonValue]:
    """Never compare partial episodes as complete; retain continuing portfolio weights."""
    result: dict[str, JsonValue] = {}
    for name, raw in definitions.items():
        assert isinstance(raw, Sequence) and not isinstance(raw, str)
        wanted = month_grid(str(raw[0]), str(raw[1]))
        present = [m for m in wanted if m in months]
        row: dict[str, JsonValue] = {
            "wanted": list(wanted),
            "present": present,
            "complete": len(present) == len(wanted),
        }
        if len(present) == len(wanted):
            first, last = months.index(wanted[0]), months.index(wanted[-1]) + 1
            row["return_percent"] = 100 * float(path.wealth[0, last] / path.wealth[0, first] - 1)
        result[name] = row
    return result


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    parameters = mapping(specification.parameters)
    portfolios = mapping(parameters["portfolios"])
    cache = RecordingCache()
    entry = cache.require(str(parameters["ticker_map_url"]))
    if entry.sha256 != parameters["ticker_map_sha256"]:
        raise ValueError("ticker map source changed")
    cache.read(entry)
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
        "# Funded crash hedge comparisons",
        "",
        "All comparisons are exploratory. Monthly NAV execution; no investor taxes."
        "\n\nOnly complete episodes have returns in result.json; partial episodes are flagged.",
        "",
    ]
    raw_costs = parameters["execution_roundtrip_bp"]
    if not isinstance(raw_costs, Sequence) or isinstance(raw_costs, str):
        raise ValueError("execution costs must be a sequence")
    for name, raw in portfolios.items():
        definition = mapping(raw)
        months = month_grid(str(definition["first"]), str(definition["last"]))
        arms = funded_arms(
            numbers(definition["weights"]),
            str(definition["funding"]),
            [str(x) for x in sequence(definition["hedges"])],
            float(str(parameters["hedge_weight"])),
        )
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
        for interval in (int(str(x)) for x in sequence(parameters["rebalance_every_months"])):
            for raw_cost in raw_costs:
                cost = float(str(raw_cost))
                paths = {
                    arm: execute(
                        joint,
                        np.asarray([weights.get(ticker, 0) for ticker in tickers]),
                        roundtrip_bp=cost,
                        rebalance_every=interval,
                    )
                    for arm, weights in arms.items()
                }
                key = f"{name}|{interval}m|{cost:g}bp"
                rows: dict[str, JsonValue] = {}
                lines += [
                    f"### {interval}-month resets, {cost:g} bp roundtrip execution",
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
                        "returns": path.returns[0].tolist(),
                        "episodes": episodes(months, path, mapping(parameters["episodes"])),
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
                    if arm in ("unchanged", "bills", "duration"):
                        continue
                    for benchmark in ("unchanged", "bills", "duration"):
                        if arm == benchmark:
                            continue
                        label = f"{arm} vs {benchmark}"
                        stats = comparison(paths[arm], paths[benchmark])
                        boot = 1200 * np.mean(
                            np.log1p(paths[arm].returns[1:])
                            - np.log1p(paths[benchmark].returns[1:]),
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
        summary="Fixed five percent crash hedge allocations compared with their actual funding "
        "and bill/duration controls. Net portfolio outcomes are not isolated option bleed; "
        "monthly surviving-fund history cannot establish a future winner.",
        estimates=tuple(estimates),
        diagnostics={
            "portfolios": output,
            "source_artifacts": list(cache.sources.values()),
            "fund_ids": parameters["fund_ids"],
            "tables": "\n".join(lines),
        },
        caveats=(
            "Current survivors selected after overlapping history; no holdout or promotion.",
            "TAIL longest common NPORT window starts February 2020, not inception; "
            "calendar 2020 incomplete.",
            "CAOS current ETF only from April 2023, with changing strategy: disclosed upper equity "
            "exposure 100% in 2023 and 120% by 2025. Predecessor excluded; no extra NAV split "
            "adjustment.",
            "BIL and 90/10 IEF/BIL controls preserve funding capital, not exact duration or "
            "equity beta.",
            "5/25 bp roundtrip execution is assumed; taxes omitted; no terminal liquidation.",
            "Fund NAV includes internal expenses, option purchases and recoveries; no "
            "double deduction.",
            "Monthly NAV boundary execution is a proxy; no intramonth drawdown or peak "
            "harvesting claim.",
            "Paired bootstrap and overlapping rolling frequencies are descriptive, not "
            "forecast odds.",
            "TAIL SEC 2025 NCSR contains rounded monthly total-return wealth back to 2017; "
            "not spliced in this NPORT design. https://www.sec.gov/Archives/edgar/data/1529390/"
            "000199937125008871/cambria_ncsr-043025.htm",
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
