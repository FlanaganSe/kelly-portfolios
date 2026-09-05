"""Actual-NAV defensive allocations and purchasing power on observed CPI dates."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import fred
from portfolio_edge.experiments.exp_018_defensive_engines import _require_cached
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

ENTRY_POINT = "exp_033_cautious_defensive_budget"
FloatArray = NDArray[np.float64]


def sequence(value: JsonValue) -> Sequence[JsonValue]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("expected a sequence")
    return value


def defensive_weights(
    base: Mapping[str, float], sleeve: Mapping[str, float], *, no_trend: bool = False
) -> dict[str, float]:
    """Replace only SCHP capital; no-trend diagnostic separately replaces RSST with VTI."""
    for weights in (base, sleeve):
        if any(not math.isfinite(w) or w < 0 for w in weights.values()):
            raise ValueError("weights must be finite and nonnegative")
        if not math.isclose(sum(weights.values()), 1, abs_tol=1e-12):
            raise ValueError("weights must sum to one")
    if base.get("SCHP", 0) != 0.5:
        raise ValueError("this experiment replaces exactly the defensive half")
    out = dict(base)
    budget = out.pop("SCHP")
    for ticker, weight in sleeve.items():
        out[ticker] = out.get(ticker, 0) + budget * weight
    if no_trend:
        out["VTI"] = out.get("VTI", 0) + out.pop("RSST")
    return {ticker: weight for ticker, weight in out.items() if weight > 0}


def previous_month(month: str) -> str:
    month_grid(month, month)  # validate canonical year-month syntax
    index = int(month[:4]) * 12 + int(month[5:]) - 2
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def real_outcomes(
    wealth: FloatArray, months: Sequence[str], cpi: Mapping[str, float]
) -> dict[str, JsonValue]:
    """Endpoint growth needs endpoint CPI; path risk reports observed dates without filling."""
    if wealth.shape != (len(months) + 1,) or not len(months):
        raise ValueError("wealth must include initial capital and every month")
    if not np.isfinite(wealth).all() or np.any(wealth <= 0):
        raise ValueError("positive finite nominal wealth required")
    if wealth[0] != 1:
        raise ValueError("nominal wealth must start at one")
    first = previous_month(months[0])
    if first not in cpi or months[-1] not in cpi:
        raise ValueError("CPI start and terminal endpoints are required")
    dates = [first, *months]
    observed = [i for i, date in enumerate(dates) if date in cpi]
    levels = np.array([cpi[dates[i]] for i in observed])
    if not np.isfinite(levels).all() or np.any(levels <= 0):
        raise ValueError("CPI must be a positive finite index")
    real = wealth[observed] * cpi[first] / levels
    log_growth = math.log(float(real[-1] / real[0])) * 12 / len(months)
    return {
        "initial_cpi_month": first,
        "initial_cpi": cpi[first],
        "terminal_cpi_month": months[-1],
        "terminal_cpi": cpi[months[-1]],
        "missing_cpi_months": [date for date in months if date not in cpi],
        "observed_cpi_months": [date for date in months if date in cpi],
        "real_wealth_on_observed_dates": real.tolist(),
        "real_terminal_wealth": float(real[-1]),
        "real_log_growth_pp_yr": 100 * log_growth,
        "real_cagr_percent": 100 * math.expm1(log_growth),
        "real_drawdown_observed_cpi_dates_percent": 100 * drawdown_summary(real).max_drawdown,
        "nominal_drawdown_observed_cpi_dates_percent": 100
        * drawdown_summary(wealth[observed]).max_drawdown,
        "max_real_principal_shortfall_observed_percent": 100 * max(0, 1 - float(real.min())),
        "terminal_real_principal_shortfall_percent": 100 * max(0, 1 - float(real[-1])),
        "observed_dates_below_initial_real_capital_fraction": float(np.mean(real[1:] < real[0])),
    }


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    root = Path(__file__).resolve().parents[3]
    p = mapping(specification.parameters)
    for path_key, hash_key in (
        ("base_specification", "base_specification_sha256"),
        ("engine_path", "engine_sha256"),
        ("cpi_manifest", "cpi_manifest_file_sha256"),
    ):
        if hashlib.sha256((root / str(p[path_key])).read_bytes()).hexdigest() != p[hash_key]:
            raise ValueError(f"frozen dependency changed: {p[path_key]}")
    base_spec = load_specification(root / str(p["base_specification"]))
    base_p = mapping(base_spec.parameters)
    base = numbers(mapping(mapping(base_p["portfolios"])["cautious"])["weights"])
    sleeves = {arm: numbers(weights) for arm, weights in mapping(p["defensive_arms"]).items()}
    cache = RecordingCache()
    ticker_entry = cache.require(str(p["ticker_map_url"]))
    if ticker_entry.sha256 != p["ticker_map_sha256"]:
        raise ValueError("SEC ticker-map snapshot changed; source IDs require a new declaration")
    ticker_map = json.loads(cache.read(ticker_entry))
    index = {
        row[ticker_map["fields"].index("symbol")]: dict(zip(ticker_map["fields"], row, strict=True))
        for row in ticker_map["data"]
    }
    fund_ids = dict(mapping(base_p["fund_ids"]))
    for ticker, raw in mapping(p["additional_funds"]).items():
        identifiers = sequence(raw)
        if (index[ticker]["seriesId"], index[ticker]["classId"]) != tuple(identifiers[:2]):
            raise ValueError(f"wrong share class for {ticker}")
        fund_ids[ticker] = raw
    tickers = sorted(set(base) | {t for weights in sleeves.values() for t in weights})
    returns: dict[str, dict[str, float]] = {}
    for ticker in tickers:
        identifiers = sequence(fund_ids[ticker])
        fund = Fund(
            ticker=ticker,
            series_id=str(identifiers[0]),
            class_id=str(identifiers[1]),
            inception=str(identifiers[2]) if len(identifiers) == 3 else None,
        )
        returns[ticker] = fund_returns(cache, fund)
    cpi_entry, cpi_provenance = _require_cached(
        cache, fred.series_url("CPIAUCNS"), mapping(p["cpi_source_pin"])
    )
    cpi_table = fred.parse(cache, cpi_entry, "CPIAUCNS")
    cpi = {
        str(date)[:7]: float(value)
        for date, value in zip(cpi_table.periods, cpi_table.column("CPIAUCNS"), strict=True)
        if value is not None
    }
    rows: list[JsonValue] = []
    estimates: list[Estimate] = []
    lines = [
        "# Cautious defensive-budget comparisons",
        "",
        "Exploratory actual-NAV portfolios. Every candidate replaces only the defensive 50%.",
        "",
        "Nominal drawdown uses all fund-return months. Real drawdown/shortfall uses only "
        "observed CPI dates and misses 2025-10: it can understate full-month downside.",
        "",
        "Real endpoint wealth/growth uses observed CPI endpoints. CPI is a monthly price "
        "index, not a trading-date deflator. No interpolation or extra TIPS inflation return.",
        "",
        "No withdrawals: incomplete monthly CPI prevents the optional indexed-spending test. "
        "No retirement adequacy or future shortfall claim.",
        "",
        "5/25 bp roundtrip means 2.5/12.5 bp per dollar bought/sold, initial purchase and annual "
        "rebalance paid. NAV already includes internal costs; no taxes or terminal sale.",
        "",
        "Paired six-month-block/2000-draw bootstrap reruns all execution paths. Cheap control "
        "is 32.5% VTI / 17.5% VXUS / 50% SCHP, not risk-, beta- or leverage-matched.",
        "",
    ]
    for era in specification.sample_policy.eras:
        no_trend = era.name == "no_trend_diagnostic"
        arms = {
            arm: defensive_weights(base, weights, no_trend=no_trend)
            for arm, weights in sleeves.items()
        }
        arms["cheap"] = {"VTI": 0.325, "VXUS": 0.175, "SCHP": 0.5}
        needed = sorted({t for weights in arms.values() for t in weights})
        months = month_grid(era.start, era.end)
        missing_cpi = [month for month in months if month not in cpi]
        if missing_cpi != list(sequence(p["known_missing_cpi_months"])):
            raise ValueError("CPI missing dates differ from the frozen declaration")
        panel = complete_panel(returns, needed, months)
        indices = stationary_bootstrap_indices(
            len(months), 6, specification.inference.resamples, context.rng
        )
        joint = np.concatenate((panel[None], panel[indices]), axis=0)
        for raw_cost in sequence(base_p["execution_roundtrip_bp"]):
            cost = float(str(raw_cost))
            paths = {
                arm: execute(
                    joint,
                    np.array([weights.get(t, 0) for t in needed]),
                    roundtrip_bp=cost,
                    rebalance_every=int(str(base_p["rebalance_every_months"])),
                )
                for arm, weights in arms.items()
            }
            lines += [
                f"## {era.name}: {era.start} to {era.end}, {cost:g}bp",
                "",
                "RSST 15% becomes additional VTI 15% in every arm: a different portfolio."
                if no_trend
                else "Published Cautious non-defensive holdings, including RSST 15%, stay fixed.",
                "",
                "| Arm | Nominal CAGR% | Nominal DD% all months | Real terminal wealth | "
                "Real CAGR% | "
                "Real DD% observed CPI | Max real-principal shortfall% observed CPI |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
            comparisons: list[str] = []
            for arm, path in paths.items():
                nominal = metrics(path)
                real = real_outcomes(path.wealth[0], months, cpi)
                paired: dict[str, JsonValue] = {}
                for benchmark in ("schp", "cheap"):
                    stats = comparison(path, paths[benchmark])
                    bootstrap = 1200 * np.mean(
                        np.log1p(path.returns[1:]) - np.log1p(paths[benchmark].returns[1:]), axis=1
                    )
                    low, high = (float(x) for x in np.quantile(bootstrap, [0.025, 0.975]))
                    paired[benchmark] = {**stats, "log_gap_interval_pp_yr": [low, high]}
                    if arm == benchmark:
                        continue
                    estimates.append(
                        Estimate(
                            name=f"log_gap[{era.name}|{cost:g}bp|{arm} vs {benchmark}]",
                            value=stats["log_gap_pp_yr"],
                            units="percentage points per year",
                            interval=(low, high),
                            n_obs=len(months),
                            interval_method="paired joint fund-row stationary bootstrap; "
                            "reexecuted paths; 6-month blocks, 2000 draws, percentile 95%",
                            cost_basis=CostBasis.NET_OPTIMISTIC
                            if cost == 5
                            else CostBasis.NET_PESSIMISTIC,
                        )
                    )
                    comparisons.append(
                        f"| {arm} vs {benchmark} | {stats['log_gap_pp_yr']:+.3f} "
                        f"[{low:+.3f},{high:+.3f}] | {stats['terminal_wealth_ratio']:.4f} | "
                        f"{stats['tracking_error_pp_yr']:.3f} | "
                        f"{stats['rolling_12m_underperformance_fraction']:.1%} | "
                        f"{stats['rolling_12m_worst_wealth_ratio']:.4f} |"
                    )
                rows.append(
                    {
                        "construction": era.name,
                        "months": list(months),
                        "arm": arm,
                        "roundtrip_bp": cost,
                        "weights": dict(arms[arm]),
                        "nominal": nominal,
                        "real": real,
                        "comparisons": paired,
                        "wealth": path.wealth[0].tolist(),
                    }
                )
                lines.append(
                    f"| {arm} | {nominal['cagr_percent']:.3f} | "
                    f"{nominal['max_drawdown_percent']:.3f} | "
                    f"{float(str(real['real_terminal_wealth'])):.4f} | "
                    f"{float(str(real['real_cagr_percent'])):.3f} | "
                    f"{float(str(real['real_drawdown_observed_cpi_dates_percent'])):.3f} | "
                    f"{float(str(real['max_real_principal_shortfall_observed_percent'])):.3f} |"
                )
            lines += [
                "",
                "| Comparison | Log gap pp/yr[95%] | Wealth ratio | TE pp/yr | "
                "Losing rolling 12m | Worst rolling 12m ratio |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
                *comparisons,
                "",
            ]
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary="Fixed defensive-half substitutions in actual Cautious and a separately labelled "
        "longer no-trend portfolio, with paid execution and purchasing-power outcomes. "
        "No defensive allocation selected and no withdrawal adequacy tested.",
        estimates=tuple(estimates),
        diagnostics={
            "rows": rows,
            "source_artifacts": list(cache.sources.values()),
            "cpi_provenance": cpi_provenance,
            "tables": "\n".join(lines),
        },
        caveats=(
            "Actual Cautious: 30 months. The 54-month diagnostic replaces RSST with VTI.",
            "CPI 2025-10 missing: real downside only on observed dates, not complete-month risk.",
            "Endpoint real growth is measurable; CPI is monthly, not exact trading-date prices.",
            "No withdrawals, taxes, independent holdout or retirement-proof claim.",
            "Common realised inflation cancels from paired nominal/real growth gaps.",
            "Source hashes identify bytes, not point-in-time fund selection or availability.",
        ),
    )


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    spec = load_specification(root / "experiments" / f"{ENTRY_POINT}.yaml")
    ledger = Ledger()
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    outcome = run_experiment(spec, registry=registry, ledger=ledger)
    assert outcome.result is not None
    path = root / "artifacts" / outcome.run_id / "tables.md"
    path.write_text(str(outcome.result.diagnostics["tables"]), encoding="utf-8")
    ledger.record_results_viewed(outcome.run_id, notes="defensive funded comparisons inspected")
    print(f"run {outcome.run_id}: {path}")


if __name__ == "__main__":
    main()
