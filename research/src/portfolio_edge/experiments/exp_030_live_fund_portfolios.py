"""Complete live-fund portfolio paths, fixed substitutions and explicit execution."""

from __future__ import annotations

import argparse
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.experiments.exp_028_tilt_estimand_audit import RecordingCache
from portfolio_edge.experiments.ledger import Ledger
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import CostBasis, Estimate, ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import JsonValue, Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.studies._loading_windows_tables import Fund, fund_returns

ENTRY_POINT = "exp_030_live_fund_portfolios"
FloatArray = NDArray[np.float64]


def mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ValueError("expected a mapping")
    return value


def numbers(value: JsonValue) -> dict[str, float]:
    return {key: float(str(item)) for key, item in mapping(value).items()}


def month_grid(first: str, last: str) -> tuple[str, ...]:
    def index(value: str) -> int:
        if len(value) != 7 or value[4] != "-":
            raise ValueError("months must use YYYY-MM")
        year, month = int(value[:4]), int(value[5:])
        if not 1 <= month <= 12:
            raise ValueError("month outside 1..12")
        return year * 12 + month - 1

    start, end = index(first), index(last)
    if end < start:
        raise ValueError("reversed month window")
    return tuple(f"{i // 12:04d}-{i % 12 + 1:02d}" for i in range(start, end + 1))


def complete_panel(
    returns: Mapping[str, Mapping[str, float]], tickers: Sequence[str], months: Sequence[str]
) -> FloatArray:
    """Never silently shorten a fixed window or fill a missing fund observation."""
    missing = [
        f"{ticker}:{month}"
        for ticker in tickers
        for month in months
        if month not in returns.get(ticker, {})
    ]
    if missing:
        raise ValueError("missing declared fund months: " + ", ".join(missing))
    panel = np.asarray([[returns[ticker][month] for ticker in tickers] for month in months])
    if not np.isfinite(panel).all() or np.any(panel <= -1):
        raise ValueError("fund returns must be finite decimal simple returns above -1")
    return panel


def substitutions(base: Mapping[str, float], spmo_weight: float) -> dict[str, dict[str, float]]:
    if spmo_weight <= 0 or spmo_weight > base.get("VTI", 0) or base.get("VTV", 0) <= 0:
        raise ValueError("substitution must be funded by positive VTI and VTV allocations")
    arms: dict[str, dict[str, float]] = {}
    for name in ("unchanged", "avuv", "spmo", "both"):
        weights = dict(base)
        if name in ("avuv", "both"):
            weights["AVUV"] = weights.get("AVUV", 0) + weights.pop("VTV")
        if name in ("spmo", "both"):
            weights["VTI"] -= spmo_weight
            weights["SPMO"] = weights.get("SPMO", 0) + spmo_weight
        arms[name] = weights
    return arms


@dataclass(frozen=True)
class Paths:
    """Batch paths: decimals, wealth initialised at one, and pre-trade capital fractions."""

    returns: FloatArray
    wealth: FloatArray
    costs: FloatArray
    turnover: FloatArray


def execute(
    panel: FloatArray, target: FloatArray, *, roundtrip_bp: float, rebalance_every: int = 12
) -> Paths:
    """Execute shape (paths, months, assets), with all investor costs paid from wealth.

    A 5 bp roundtrip is 2.5 bp per dollar bought or sold. Rebalancing solves for
    after-cost wealth before scaling target holdings; no unfinanced fee deduction.
    """
    if panel.ndim != 3 or panel.shape[1] == 0 or panel.shape[2] != target.size:
        raise ValueError("panel needs paths, months and matching assets")
    if target.ndim != 1 or not np.isfinite(target).all() or np.any(target < 0):
        raise ValueError("target weights must be finite nonnegative decimals")
    if not math.isclose(float(target.sum()), 1, abs_tol=1e-12):
        raise ValueError("fully funded decimal target weights must sum to one")
    if not np.isfinite(panel).all() or np.any(panel <= -1):
        raise ValueError("finite decimal simple returns greater than -1 required")
    if not math.isfinite(roundtrip_bp) or not 0 <= roundtrip_bp < 20_000:
        raise ValueError("roundtrip cost must be basis points in [0,20000)")
    if not isinstance(rebalance_every, int) or rebalance_every < 1:
        raise ValueError("rebalance interval must be positive whole months")
    batch, months, _ = panel.shape
    c = roundtrip_bp / 20_000
    weights = np.broadcast_to(target, (batch, target.size)).copy()
    realised = np.zeros((batch, months))
    costs = np.zeros_like(realised)
    turnover = np.zeros_like(realised)
    for t in range(months):
        q = np.ones(batch)
        if t == 0:
            q[:] = 1 / (1 + c)
            turnover[:, t] = q  # cash buys, with no corresponding fund sale
        elif t % rebalance_every == 0:
            if c:
                low, high = np.zeros(batch), np.ones(batch)
                for _ in range(55):
                    mid = (low + high) / 2
                    trade = np.abs(mid[:, None] * target - weights).sum(axis=1)
                    below = mid + c * trade < 1
                    low = np.where(below, mid, low)
                    high = np.where(below, high, mid)
                q = (low + high) / 2
            turnover[:, t] = np.abs(q[:, None] * target - weights).sum(axis=1)
            weights[:] = target
        costs[:, t] = 1 - q
        gross = 1 + (weights * panel[:, t, :]).sum(axis=1)
        realised[:, t] = q * gross - 1
        weights *= (1 + panel[:, t, :]) / gross[:, None]
    wealth = np.concatenate((np.ones((batch, 1)), np.cumprod(1 + realised, axis=1)), axis=1)
    return Paths(returns=realised, wealth=wealth, costs=costs, turnover=turnover)


def metrics(path: Paths) -> dict[str, float]:
    r, wealth = path.returns[0], path.wealth[0]
    log = float(np.mean(np.log1p(r))) * 12
    return {
        "log_growth_pp_yr": 100 * log,
        "cagr_percent": 100 * math.expm1(log),
        "arithmetic_pp_yr": 1200 * float(np.mean(r)),
        "max_drawdown_percent": 100 * drawdown_summary(wealth).max_drawdown,
        "terminal_wealth": float(wealth[-1]),
        "execution_cost_percent_initial_wealth": 100 * float(np.sum(path.costs[0] * wealth[:-1])),
        "traded_fraction_per_year": float(path.turnover[0].sum()) * 12 / len(r),
    }


def comparison(arm: Paths, control: Paths) -> dict[str, float]:
    difference = np.log1p(arm.returns[0]) - np.log1p(control.returns[0])
    n = difference.size
    if n < 12:
        raise ValueError("a rolling year needs at least twelve monthly returns")
    rolling = np.convolve(difference, np.ones(12), mode="valid")
    return {
        "log_gap_pp_yr": 1200 * float(difference.mean()),
        "terminal_wealth_ratio": float(arm.wealth[0, -1] / control.wealth[0, -1]),
        "tracking_error_pp_yr": 100
        * math.sqrt(12)
        * float(np.std(arm.returns[0] - control.returns[0], ddof=1)),
        "rolling_12m_underperformance_fraction": float(np.mean(rolling < 0)),
        "rolling_12m_worst_wealth_ratio": float(np.exp(rolling.min())),
        "rolling_12m_windows": float(rolling.size),
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
    lines = ["# Live fund portfolio comparisons", "", "All comparisons are exploratory.", ""]
    raw_costs = parameters["execution_roundtrip_bp"]
    if not isinstance(raw_costs, Sequence) or isinstance(raw_costs, str):
        raise ValueError("execution costs must be a sequence")
    for name, raw in portfolios.items():
        definition = mapping(raw)
        months = month_grid(str(definition["first"]), str(definition["last"]))
        arms = substitutions(numbers(definition["weights"]), float(str(definition["spmo_weight"])))
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
                for benchmark in ("unchanged", "cheap"):
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
        summary="Fixed fund substitutions evaluated inside three complete published portfolios "
        "using filed NAV total returns, drifting weights and paid annual execution. Short common "
        "histories and descriptive intervals cannot establish a future winner.",
        estimates=tuple(estimates),
        diagnostics={
            "portfolios": output,
            "source_artifacts": list(cache.sources.values()),
            "tables": "\n".join(lines),
        },
        caveats=(
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
