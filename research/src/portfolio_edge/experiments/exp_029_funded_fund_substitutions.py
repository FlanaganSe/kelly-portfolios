"""Fixed portfolio substitutions: backward exposure projections, never fund backtests."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import replace

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.experiments.exp_016_construction_tournament import (
    BasisPanel,
    CostSettings,
    FundMapping,
    _mapping,
    _number,
    _sequence,
    constant_weight_path,
    gap_statistics,
    workspace_root,
)
from portfolio_edge.experiments.exp_027_selective_carry import gap_record, rolling_underperformance
from portfolio_edge.experiments.exp_028_tilt_estimand_audit import RecordingCache
from portfolio_edge.experiments.ledger import Ledger
from portfolio_edge.experiments.periods import month_index
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import JsonValue, Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.reporting.site_series import (
    SITE_PORTFOLIOS,
    load_panels,
    tournament_targets,
)
from portfolio_edge.studies._loading_windows_tables import fund_returns, load_french_panel
from portfolio_edge.studies._untested_tilts_tables import COSTS, FACTORS, FUNDS, PREMIA, regress

FloatArray = NDArray[np.float64]
ENTRY_POINT = "exp_029_funded_fund_substitutions"
US_FUNDS = ("VTI", "VTV", "AVUV", "SPMO")
FACTOR_NAMES = {"Mkt-RF": "us_mkt", **{f: f"us_{f.lower()}" for f in FACTORS[1:]}}


def substituted_weights(
    weights: Mapping[str, float], *, value: bool, momentum_percent: float
) -> dict[str, float]:
    """Targets in percentage points of capital; fully funded substitutions."""
    out = dict(weights)
    if not all(math.isfinite(w) and w >= 0 for w in out.values()):
        raise ValueError("weights must be finite and nonnegative")
    if not math.isclose(sum(out.values()), 100.0, abs_tol=1e-9):
        raise ValueError("weights must sum to 100")
    if not math.isfinite(momentum_percent) or not 0 <= momentum_percent <= out.get("VTI", 0):
        raise ValueError("momentum must be fully funded from VTI")
    if value:
        out["AVUV"] = out.get("AVUV", 0.0) + out.pop("VTV")
    if momentum_percent:
        out["VTI"] -= momentum_percent
        out["SPMO"] = out.get("SPMO", 0.0) + momentum_percent
    return {t: w for t, w in out.items() if w > 0}


def scenario_panel(
    panel: BasisPanel, name: str, *, market_pp: float, trend_pp: float
) -> BasisPanel:
    """Shift means once on the full history; retain covariance exactly."""
    if name == "historical":
        return panel
    targets = {
        f"{prefix}_{f.lower()}": premium
        for region, prefix in (("us", "us"), ("exus", "dxus"))
        for f, premium in PREMIA[name][region].items()
    }
    targets.update(dict.fromkeys(("us_mkt", "dxus_mkt", "em_mkt"), market_pp))
    targets["trend"] = trend_pp
    return replace(
        panel,
        series={
            key: v - np.mean(v) + targets[key] / 1200 if key in targets else v.copy()
            for key, v in panel.series.items()
        },
    )


def fitted_mappings(
    original: Mapping[str, FundMapping], specification: Specification
) -> tuple[dict[str, dict[str, FundMapping]], list[JsonValue], list[JsonValue]]:
    cache = RecordingCache()
    panel = load_french_panel(cache, "us")
    returns = {f.ticker: fund_returns(cache, f) for f in FUNDS if f.ticker in US_FUNDS}
    parameters = _mapping(specification.parameters, where="parameters")
    variants: dict[str, dict[str, FundMapping]] = {}
    rows: list[JsonValue] = []
    for label, raw in _mapping(parameters["loading_windows"], where="windows").items():
        window = _mapping(raw, where=label)
        start, end = str(window["start"]), str(window["end"])
        fitted = dict(original)
        for ticker in US_FUNDS:
            report = regress(
                label=ticker,
                panel=panel,
                panel_name="us",
                series=returns[ticker],
                first=start,
                last=end,
                subtract_cash=True,
            )
            if (
                report.window.first != start
                or report.window.last != end
                or report.months != month_index(end) - month_index(start) + 1
            ):
                raise ValueError(f"{ticker} missing frozen common loading months")
            coefficients = {FACTOR_NAMES[f]: report.loadings[f].value for f in FACTORS}
            fitted[ticker] = replace(
                original.get(ticker, original["VTI"]),
                ticker=ticker,
                coefficients=coefficients,
                alpha_less_pedestal_pp_yr=None,
            )
            rows.append(
                {
                    "window": label,
                    "ticker": ticker,
                    "start": start,
                    "end": end,
                    "months": report.months,
                    "coefficients": coefficients,
                    "alpha_pp_yr_omitted": report.alpha,
                    "alpha_interval_pp_yr": list(report.alpha_interval),
                }
            )
        variants[label] = fitted
    return variants, rows, list(cache.sources.values())


def apply_costs(mappings: Mapping[str, FundMapping], k: float) -> dict[str, FundMapping]:
    """Internal-cost assumption; the simulator charges external investor trades."""
    if not math.isfinite(k) or k < 0:
        raise ValueError("invalid turnover coefficient")
    out = dict(mappings)
    for ticker in US_FUNDS:
        c = COSTS[ticker]
        assert c.securities_lending_bp is not None and c.turnover_percent is not None
        out[ticker] = replace(
            out[ticker],
            expense_ratio_bp=(c.fee_bp - c.securities_lending_bp + k * c.turnover_percent),
        )
    return out


def simulate(
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    weights: Mapping[str, float],
) -> FloatArray:
    tickers, targets = tournament_targets(
        weights, mappings=mappings, vt_proxy={"VTI": 0.65, "VXUS": 0.35}
    )
    return constant_weight_path(
        panel,
        mappings,
        costs,
        tickers=tickers,
        targets=targets,
    ).total


def outcomes(total: FloatArray) -> dict[str, JsonValue]:
    if total.ndim != 1 or not np.all(np.isfinite(total)) or np.any(total <= -1):
        raise ValueError("finite solvent monthly path required")
    log = float(np.mean(np.log1p(total))) * 12
    dd = drawdown_summary(np.concatenate(([1.0], np.cumprod(1 + total))))
    return {
        "log_growth_pp_yr": log * 100,
        "cagr_pct": math.expm1(log) * 100,
        "max_drawdown_pct": dd.max_drawdown * 100,
        "months_under_water": dd.max_time_under_water,
        "worst_month_pct": float(np.min(total)) * 100,
        "volatility_pct": float(np.std(total, ddof=1)) * math.sqrt(12) * 100,
    }


def comparison(
    total: FloatArray, control: FloatArray, indices: NDArray[np.intp]
) -> dict[str, JsonValue]:
    return {
        **gap_record(gap_statistics(total, control, indices=indices, confidence=0.95)),
        "rolling_10year": rolling_underperformance(total, control),
    }


def render(
    rows: list[dict[str, JsonValue]],
    fits: list[JsonValue],
    weights: Mapping[str, JsonValue],
    baseline: list[JsonValue],
    costs: list[JsonValue],
) -> str:
    lines = [
        "# Experiment 029: funded substitutions in complete portfolios",
        "",
        "Exposure projections, not fund histories. Annual rebalancing, nominal returns, "
        "no taxes; intervals condition on fitted loadings and assumed means. Residual return "
        "and risk omitted. MDE is resolution, not an allocation threshold. Ten-year windows "
        "overlap; their losing frequencies are scenario diagnostics, not forecast odds.",
        "",
        f"Frozen holdings (percent): `{weights}`.",
        "",
        "## US loading fits and costs",
        "",
        "All six coefficients include market beta. Alpha is diagnostic and omitted from paths.",
        "",
    ]
    lines.extend(f"- `{row}`" for row in fits)
    lines += [
        "",
        "Costs in annual basis points (fee minus lending plus assumed k times turnover):",
        "",
    ]
    lines.extend(f"- `{row}`" for row in costs)
    lines += [
        "",
        "## Baseline mapping bridge",
        "",
        "Same printed weights on historical panel: original inherited truncated mappings versus "
        "full refits and k=0 fee less lending. This bridge also changes cost assumptions.",
        "",
    ]
    lines.extend(f"- `{row}`" for row in baseline)
    lines += [
        "",
        "## All scenarios",
        "",
        "Assumed scenarios set all three market excess means to 5% and gross trend to 1% "
        "a year. Own-panel, half and null shift US/developed style means; emerging style "
        "and Treasury means remain historical. Full-history means are shifted before era "
        "slicing. k=0,1,1.7 are cost assumptions, not validated bounds. Each arm's funded "
        "gap uses its exact unchanged portfolio. World65/35 and60/40 are separate comparisons.",
        "",
        "| window/scenario/k/era | portfolio/arm | CAGR | drawdown | worst month | "
        "funded log gap [95%], MDE | world gap / TE | 60/40 gap / TE | "
        "funded losing 10y / worst shortfall | interaction pp/yr |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |",
    ]

    def number(v: JsonValue) -> str:
        return f"{float(str(v)):.3f}"

    for row in rows:
        m, p, world, mix = (
            _mapping(row[k], where=k) for k in ("outcomes", "funded", "world", "sixty_forty")
        )
        lo, hi = _sequence(p["interval_pp_yr"], where="interval")
        roll = _mapping(p["rolling_10year"], where="rolling")
        lines.append(
            f"| {row['window']}/{row['scenario']}/{row['k']}/{row['era']} | "
            f"{row['portfolio']}/{row['arm']} | {number(m['cagr_pct'])} | "
            f"{number(m['max_drawdown_pct'])} | {number(m['worst_month_pct'])} | "
            f"{number(p['gap_pp_yr'])} [{number(lo)}, {number(hi)}], {number(p['mde_pp_yr'])} | "
            f"{number(world['gap_pp_yr'])} / {number(world['tracking_error_pct'])} | "
            f"{number(mix['gap_pp_yr'])} / {number(mix['tracking_error_pct'])} | "
            f"{roll['frequency']} / {roll['worst_shortfall_pct']} | "
            f"{number(row['interaction_pp_yr'])} |"
        )
    return "\n".join(lines) + "\n"


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    p = _mapping(specification.parameters, where="parameters")
    for filename, digest in _mapping(p["dependency_sha256"], where="pins").items():
        if hashlib.sha256((workspace_root() / filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f"frozen dependency changed: {filename}")
    weights = _mapping(p["portfolios"], where="portfolios")
    for published in SITE_PORTFOLIOS:
        if published.id in weights and published.weights != weights[published.id]:
            raise ValueError("printed portfolio drifted from frozen weights")
    panels = load_panels()
    fitted, fit_rows, sources = fitted_mappings(panels.mappings, specification)
    rows: list[dict[str, JsonValue]] = []
    bridge: list[JsonValue] = []
    cost_rows: list[JsonValue] = []
    for window, raw_mappings in fitted.items():
        for raw_k in _sequence(p["turnover_cost_coefficients"], where="costs"):
            k = float(str(raw_k))
            mappings = apply_costs(raw_mappings, k)
            cost_rows.append(
                {
                    "window": window,
                    "k": k,
                    "annual_bp": {t: mappings[t].expense_ratio_bp for t in US_FUNDS},
                }
            )
            for raw_scenario in _sequence(p["premium_scenarios"], where="scenarios"):
                scenario = str(raw_scenario)
                full = scenario_panel(
                    panels.tournament,
                    scenario,
                    market_pp=_number(p, "scenario_market_premium_pp_yr", where="p"),
                    trend_pp=_number(p, "scenario_trend_gross_premium_pp_yr", where="p"),
                )
                for era in specification.sample_policy.eras:
                    panel = full.window(start=era.start, end=era.end)
                    indices = stationary_bootstrap_indices(
                        panel.months, 12, specification.inference.resamples, context.rng
                    )
                    world = simulate(
                        panel, mappings, panels.tournament_costs, {"VTI": 65, "VXUS": 35}
                    )
                    mix = simulate(
                        panel,
                        mappings,
                        panels.tournament_costs,
                        {"VTI": 39, "VXUS": 21, "SCHP": 40},
                    )
                    for portfolio, raw_weights in weights.items():
                        held = {
                            t: float(str(w)) for t, w in _mapping(raw_weights, where="w").items()
                        }
                        momentum = _number(
                            _mapping(p["spmo_weight_percent"], where="spmo"),
                            portfolio,
                            where="spmo",
                        )
                        paths = {
                            name: simulate(
                                panel,
                                mappings,
                                panels.tournament_costs,
                                substituted_weights(held, value=value, momentum_percent=mom),
                            )
                            for name, value, mom in (
                                ("baseline", False, 0.0),
                                ("value", True, 0.0),
                                ("momentum", False, momentum),
                                ("both", True, momentum),
                            )
                        }
                        base = paths["baseline"]
                        g = {a: float(np.mean(np.log1p(v))) * 1200 for a, v in paths.items()}
                        interaction = g["both"] - g["value"] - g["momentum"] + g["baseline"]
                        if scenario == "historical" and k == 0 and era.name == "full":
                            bridge.append(
                                {
                                    "window": window,
                                    "portfolio": portfolio,
                                    "original": outcomes(
                                        simulate(
                                            panel, panels.mappings, panels.tournament_costs, held
                                        )
                                    ),
                                    "refitted": outcomes(base),
                                }
                            )
                        for name, total in paths.items():
                            rows.append(
                                {
                                    "window": window,
                                    "scenario": scenario,
                                    "k": k,
                                    "era": era.name,
                                    "start": panel.periods[0],
                                    "end": panel.periods[-1],
                                    "portfolio": portfolio,
                                    "arm": name,
                                    "outcomes": outcomes(total),
                                    "funded": comparison(total, base, indices),
                                    "world": comparison(total, world, indices),
                                    "sixty_forty": comparison(total, mix, indices),
                                    "interaction_pp_yr": interaction if name == "both" else 0.0,
                                }
                            )
    tables = render(rows, fit_rows, weights, bridge, cost_rows)
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=f"{len(rows)} full-portfolio scenario rows; fixed funded substitutions, "
        "two loading windows and explicit costs/premia. No fund selected or promoted.",
        diagnostics={
            "source_artifacts": sources,
            "panel_provenance": [dict(x) for x in panels.tournament.provenance],
            "manifest_hashes": list(panels.manifests),
            "fits": fit_rows,
            "costs": cost_rows,
            "baseline_mapping_bridge": bridge,
            "rows": rows,
            "markdown_tables": tables,
        },
        caveats=(
            "Recent fund exposures projected backward; residual risk and return omitted.",
            "Previously examined data and choices; no untouched holdout.",
            "Intervals exclude loading and assumed-premium uncertainty.",
            "No investor taxes, transition gains, or executable internal trading rule.",
            "Nominal Treasury proxies SCHP; AQR gross trend proxies RSST's trend leg.",
            "Benchmark gaps are distinct comparisons, never additive.",
        ),
    )


def main() -> None:
    spec = load_specification(workspace_root() / "experiments" / f"{ENTRY_POINT}.yaml")
    ledger = Ledger()
    outcome = run_experiment(spec, registry=ExperimentRegistry({ENTRY_POINT: run}), ledger=ledger)
    assert outcome.result is not None
    path = workspace_root() / "artifacts" / outcome.run_id / "tables.md"
    path.write_text(str(outcome.result.diagnostics["markdown_tables"]))
    ledger.record_results_viewed(outcome.run_id, notes="Full portfolio scenarios inspected")
    print(f"run {outcome.run_id}: {outcome.result.summary}\n{path}")


if __name__ == "__main__":
    main()
