"""Unit tests for Experiment 024, the working default scored as one object.

Every expected value here is computed in this file by hand or with plain NumPy,
never by calling the code under test on the same inputs.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

import portfolio_edge.experiments.exp_024_working_default as module
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    BasisPanel,
    CostSettings,
    FundMapping,
    _build_mappings,
    _cost_settings,
    workspace_root,
)
from portfolio_edge.experiments.exp_018_defensive_engines import simulate_arm
from portfolio_edge.experiments.exp_024_working_default import (
    arm_notional,
    default_specification_path,
    read_arms,
    read_wrappers,
    regret_gap_pp_yr,
    tournament_notional,
    window_statistics,
)
from portfolio_edge.experiments.specification import Specification, load_specification
from portfolio_edge.inference.hac import hac_mean

SPEC_PATH = default_specification_path()
TOURNAMENT_SPEC_PATH = workspace_root() / "experiments" / "exp_016f_matched_pairs.yaml"


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(SPEC_PATH)


def _panel(
    months: int, *, legs: Mapping[str, Sequence[float]], cash: Sequence[float]
) -> BasisPanel:
    return BasisPanel(
        periods=tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(months)),
        series={k: np.asarray(v, dtype=np.float64) for k, v in legs.items()},
        cash=np.asarray(cash, dtype=np.float64),
        provenance=(),
        findings=(),
    )


# --------------------------------------------------------------------------- #
# Notional derivation, one row per arm, by hand
# --------------------------------------------------------------------------- #

RSST_GROSS = 1.072 + 1.0

EXPECTED_NOTIONAL = {
    # arm: (gross, equity, trend, bond, cash)
    "published_trend30": (0.70 + 0.30 * RSST_GROSS, 0.70 + 0.30 * 1.072, 0.30, 0.0, 0.0),
    "working_default": (0.70 + 0.25 * RSST_GROSS + 0.05, 0.70 + 0.25 * 1.072, 0.25, 0.05, 0.0),
    "trend25_cash5": (0.70 + 0.25 * RSST_GROSS, 0.70 + 0.25 * 1.072, 0.25, 0.0, 0.05),
    "trend25_ltbond5": (0.70 + 0.25 * RSST_GROSS + 0.05, 0.70 + 0.25 * 1.072, 0.25, 0.05, 0.0),
    "trend25_core75": (0.75 + 0.25 * RSST_GROSS, 0.75 + 0.25 * 1.072, 0.25, 0.0, 0.0),
}


def test_every_arm_derives_the_notional_the_specification_states(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    assert set(arms) == set(EXPECTED_NOTIONAL)
    for name, arm in arms.items():
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        gross, equity, trend, bond, cash = EXPECTED_NOTIONAL[name]
        assert notional.gross == pytest.approx(gross, abs=1e-12), name
        assert notional.equity == pytest.approx(equity, abs=1e-12), name
        assert notional.trend == pytest.approx(trend, abs=1e-12), name
        assert notional.bond == pytest.approx(bond, abs=1e-12), name
        assert notional.cash == pytest.approx(cash, abs=1e-12), name
    # The page's stated figures for the two vectors, to four places.
    working = arm_notional(
        arms["working_default"].tickers, arms["working_default"].weights, wrappers
    )
    assert working.gross == pytest.approx(1.268)
    assert working.equity == pytest.approx(0.968)
    published = arm_notional(
        arms["published_trend30"].tickers, arms["published_trend30"].weights, wrappers
    )
    assert published.gross == pytest.approx(1.3216)
    # The working default and the published construction differ by five points of
    # wrapper moved into the bond line and by nothing else.
    assert dict(
        zip(arms["published_trend30"].tickers, arms["published_trend30"].weights, strict=True)
    ) == {
        "CORE": 0.70,
        "RSST_LIKE": 0.30,
    }
    assert dict(
        zip(arms["working_default"].tickers, arms["working_default"].weights, strict=True)
    ) == {
        "CORE": 0.70,
        "RSST_LIKE": 0.25,
        "TSY10": 0.05,
    }


def test_the_ten_year_line_is_unlevered_and_charged_five_basis_points(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    tsy = wrappers["TSY10"]
    assert tsy.exposures == {"tsy10": 1.0}
    assert tsy.financed == {}
    assert tsy.fee_bp == 5.0
    assert wrappers["RSST_LIKE"].fee_bp == 99.0
    assert wrappers["RSST_LIKE"].financed == {"equity": 0.331}


# --------------------------------------------------------------------------- #
# A two-period fixture for the working default, computed by hand
# --------------------------------------------------------------------------- #


def test_working_default_two_period_fixture(specification: Specification) -> None:
    """70% CORE + 25% RSST_LIKE + 5% TSY10 over two months, spreads off.

    Capital weights sum to one, so there is no debt: each month's total return
    is ``cash + sum_i w_i * excess_i`` and the wealth path compounds the two.
    """
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = module.read_rates(specification)
    arm = arms["working_default"]
    costs = CostSettings(
        equity_futures_basis=rates.equity / 10_000.0,
        trend_book_financing=0.0,
        round_trip_spread={"us_equity": 0.0},
    )
    equity = [0.02, -0.03]
    tsy10 = [0.004, 0.011]
    treasury = [0.006, 0.015]
    trend = [-0.005, 0.012]
    cash = [0.003, 0.002]
    panel = _panel(
        2,
        legs={"equity": equity, "tsy10": tsy10, "treasury": treasury, "trend": trend},
        cash=cash,
    )
    path = simulate_arm(
        panel, wrappers, rates, costs, tickers=arm.tickers, targets=np.asarray(arm.weights)
    )

    expected = []
    for t in range(2):
        core = equity[t] - 3.0 / 120_000.0
        rsst = 1.072 * equity[t] + trend[t] - (99.0 + 0.331 * 62.0) / 120_000.0
        bond = tsy10[t] - 5.0 / 120_000.0
        expected.append(cash[t] + 0.70 * core + 0.25 * rsst + 0.05 * bond)
    assert path.total == pytest.approx(np.asarray(expected), abs=1e-12)
    assert float(np.prod(1.0 + path.total)) == pytest.approx(
        (1.0 + expected[0]) * (1.0 + expected[1]), abs=1e-12
    )
    # The paired difference against the published construction is exactly five
    # points of (bond - wrapper) per dollar, plus the 5.73 bp/yr certain saving.
    published = simulate_arm(
        panel,
        wrappers,
        rates,
        costs,
        tickers=arms["published_trend30"].tickers,
        targets=np.asarray(arms["published_trend30"].weights),
    )
    for t in range(2):
        rsst = 1.072 * equity[t] + trend[t] - (99.0 + 0.331 * 62.0) / 120_000.0
        bond = tsy10[t] - 5.0 / 120_000.0
        assert path.total[t] - published.total[t] == pytest.approx(0.05 * (bond - rsst), abs=1e-12)
    saving_bp_yr = 0.05 * (99.0 + 0.331 * 62.0 - 5.0)
    assert saving_bp_yr == pytest.approx(5.7261)


def test_tournament_notional_counts_bonds_and_not_cash() -> None:
    mappings: dict[str, FundMapping] = dict(
        _build_mappings(load_specification(TOURNAMENT_SPEC_PATH))
    )
    mappings["TSY10"] = FundMapping(
        ticker="TSY10",
        coefficients={"treasury": 1.0},
        expense_ratio_bp=5.0,
        futures_notional=0.0,
        spread_region="us_equity",
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=True,
    )
    tickers = ("RSST", "VTI", "VTV", "VXUS", "AVDV", "IDMO", "AVES", "TSY10")
    weights = (0.25, 0.19, 0.15, 0.16, 0.10, 0.05, 0.05, 0.05)
    n = tournament_notional(tickers, weights, mappings)
    # Every equity fund maps 1.000 to a market leg; RSST maps 1.072 + 1.0 trend.
    assert n.equity == pytest.approx(0.70 + 0.25 * 1.072)
    assert n.trend == pytest.approx(0.25)
    assert n.bond == pytest.approx(0.05)
    assert n.gross == pytest.approx(1.268)
    assert n.cash == pytest.approx(0.0)
    cash_variant = tournament_notional(
        ("RSST", "VTI", "VTV", "VXUS", "AVDV", "IDMO", "AVES", "CASH"), weights, mappings
    )
    assert cash_variant.gross == pytest.approx(1.218)
    assert cash_variant.cash == pytest.approx(0.05)


# --------------------------------------------------------------------------- #
# Statistics and the regret arithmetic
# --------------------------------------------------------------------------- #


def test_window_statistics_match_the_formulae() -> None:
    rng = np.random.default_rng(7)
    arm = rng.normal(0.006, 0.04, 240)
    control = rng.normal(0.005, 0.04, 240)
    stats = window_statistics(arm, control, window="full")
    d = arm - control
    assert stats.gap_pp_yr == pytest.approx(float(np.mean(d)) * 1200.0)
    assert stats.mde_pp_yr == pytest.approx(
        MDE_MULTIPLIER * float(np.std(d, ddof=1)) / math.sqrt(240) * 1200.0
    )
    hac = hac_mean(d)
    assert stats.hac_se_pp_yr == pytest.approx(hac.standard_error * 1200.0)
    assert stats.hac_interval[0] == pytest.approx(stats.gap_pp_yr - 1.959964 * stats.hac_se_pp_yr)
    assert stats.log_growth_gap_pp_yr == pytest.approx(
        (float(np.mean(np.log1p(arm))) - float(np.mean(np.log1p(control)))) * 1200.0
    )
    assert stats.tracking_error_pct == pytest.approx(
        float(np.std(d, ddof=1)) * math.sqrt(12) * 100.0
    )


def test_regret_arithmetic_by_hand() -> None:
    """Five points from a wrapper (1.072 equity + trend at 119.52 bp) into a bond at 5 bp."""
    kwargs = {
        "bond_excess_pp_yr": 0.8,
        "points": 0.05,
        "wrapper_equity": 1.072,
        "wrapper_cost_pp_yr": 1.1952,
        "bond_fee_pp_yr": 0.05,
    }
    # Trend 4.07, equity 3.0 over bonds: equity excess 3.8.
    forgone = 1.072 * 3.8 + 4.07 - 1.1952
    earned = 0.8 - 0.05
    assert regret_gap_pp_yr(
        trend_gross_pp_yr=4.07, equity_premium_over_bonds_pp_yr=3.0, **kwargs
    ) == pytest.approx(0.05 * (earned - forgone))
    assert 0.05 * (earned - forgone) == pytest.approx(-0.3099, abs=5e-4)
    # No premia anywhere: the pair is the certain cost saving less the bond fee.
    assert regret_gap_pp_yr(
        trend_gross_pp_yr=0.0,
        equity_premium_over_bonds_pp_yr=0.0,
        **{**kwargs, "bond_excess_pp_yr": 0.0},
    ) == pytest.approx(0.05 * (1.1952 - 0.05))
    # Linear in the trend premium with slope -points.
    a = regret_gap_pp_yr(trend_gross_pp_yr=1.0, equity_premium_over_bonds_pp_yr=1.5, **kwargs)
    b = regret_gap_pp_yr(trend_gross_pp_yr=2.0, equity_premium_over_bonds_pp_yr=1.5, **kwargs)
    assert b - a == pytest.approx(-0.05)


# --------------------------------------------------------------------------- #
# The whole experiment on a short synthetic history
# --------------------------------------------------------------------------- #


def _synthetic_raw_series() -> module.RawSeries:
    rng = np.random.default_rng(20260902)
    months = [f"{1988 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(216)]
    equity = rng.normal(0.006, 0.045, 216)
    bond = rng.normal(0.002, 0.025, 216)
    cash = np.full(216, 0.003)

    def series(values: NDArray[np.float64]) -> dict[str, float]:
        return {m: float(v) for m, v in zip(months, values, strict=True)}

    yields = np.clip(0.05 + np.cumsum(rng.normal(0.0, 0.002, 216)), 0.01, 0.15)
    return module.RawSeries(
        equity=series(equity),
        cash=series(cash),
        ltr=series(bond + cash),
        corpr=series(bond + cash + rng.normal(0.0005, 0.01, 216)),
        gw_rfree=series(cash),
        commodity=series(rng.normal(0.002, 0.05, 216)),
        shiller_gs10_pct=series(yields * 100.0),
        fred_gs10=series(yields),
        provenance=({"id": "synthetic"},),
        findings=("synthetic",),
    )


def _synthetic_tournament_inputs(legs: module.Legs) -> module.TournamentInputs:
    rng = np.random.default_rng(3)
    periods = sorted(legs.tsy10)
    n = len(periods)
    names = [
        "us_mkt", "us_smb", "us_hml", "us_rmw", "us_cma", "us_umd",
        "dxus_mkt", "dxus_smb", "dxus_hml", "dxus_rmw", "dxus_cma", "dxus_umd",
        "em_mkt", "em_hml", "trend",
    ]  # fmt: skip
    series = {name: rng.normal(0.004, 0.04, n) for name in names}
    series["treasury"] = np.array([legs.tsy10[p] for p in periods], dtype=np.float64)
    tournament = load_specification(TOURNAMENT_SPEC_PATH)
    mappings = dict(_build_mappings(tournament))
    mappings["TSY10"] = FundMapping(
        ticker="TSY10",
        coefficients={"treasury": 1.0},
        expense_ratio_bp=5.0,
        futures_notional=0.0,
        spread_region="us_equity",
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=True,
    )
    return module.TournamentInputs(
        panel=BasisPanel(
            periods=tuple(periods),
            series=series,
            cash=np.array([legs.cash[p] for p in periods], dtype=np.float64),
            provenance=(),
            findings=("synthetic tournament panel",),
        ),
        mappings=mappings,
        costs=_cost_settings(tournament),
        specification_hash=tournament.spec_hash,
        findings=("synthetic tournament panel",),
    )


def test_the_whole_experiment_runs_and_reports_what_the_contract_requires(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, specification: Specification
) -> None:
    from portfolio_edge.experiments.ledger import Ledger, RunStatus
    from portfolio_edge.experiments.result import ResultStatus
    from portfolio_edge.experiments.runner import run_experiment

    monkeypatch.setattr(module, "load_series", lambda _spec: _synthetic_raw_series())
    monkeypatch.setattr(
        module, "load_tournament_inputs", lambda _spec, legs: _synthetic_tournament_inputs(legs)
    )
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        specification,
        registry=module.build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    result = outcome.result
    assert result is not None
    assert result.status in {ResultStatus.EXPLORATORY, ResultStatus.UNRESOLVED}

    panels = result.diagnostics["panels"]
    assert isinstance(panels, Sequence)
    by_id = {str(p["id"]): p for p in panels if isinstance(p, Mapping)}
    assert set(by_id) == {"primary", "tournament_1990"}
    arms = read_arms(specification)
    primary = by_id["primary"]
    rows = primary["arms"]
    assert isinstance(rows, Sequence)
    seen: set[str] = set()
    for row in rows:
        assert isinstance(row, Mapping)
        seen.add(str(row["arm"]))
        notional = row["notional"]
        assert isinstance(notional, Mapping)
        assert {"gross", "equity", "trend", "bond", "cash"} <= set(notional)
        assert row["max_drawdown_pct"] is not None
        assert row["time_under_water_months"] is not None
        assert isinstance(row["episodes"], Mapping)
        comparisons = row["comparisons"]
        assert isinstance(comparisons, Mapping)
        for control, comparison in comparisons.items():
            assert isinstance(comparison, Mapping)
            if comparison["identical_construction"]:
                assert comparison["status"] == "not-scored", (row["arm"], control)
                continue
            # A gap never appears without both intervals, its floor, its control or its status.
            assert comparison["gap_pp_yr"] is not None
            assert comparison["bootstrap_interval_pp_yr"] is not None
            assert comparison["hac_interval_pp_yr"] is not None
            assert comparison["mde_80pc_power_pp_yr"] is not None
            assert comparison["log_growth_gap_pp_yr"] is not None
            assert comparison["control_definition"]
            assert comparison["status"] in {"exploratory", "unresolved", "rejected"}
            assert isinstance(comparison["windows"], Mapping)
    assert seen == set(arms)
    assert isinstance(primary["ten_year_regime_by_era"], Sequence)
    assert isinstance(primary["financing_sensitivity"], Mapping)

    tournament = by_id["tournament_1990"]
    assert isinstance(tournament["reproduction"], Mapping)
    t_rows = tournament["arms"]
    assert isinstance(t_rows, Sequence)
    assert {str(r["arm"]) for r in t_rows if isinstance(r, Mapping)} == {
        "published",
        "working_default",
        "trend25_cash5",
        "rec25",
    }

    pair = result.diagnostics["primary_pair"]
    assert isinstance(pair, Mapping)
    assert pair["arm"] == "working_default" and pair["control"] == "reference"
    regret = result.diagnostics["regret"]
    assert isinstance(regret, Mapping)
    rows_r = regret["rows"]
    assert isinstance(rows_r, Sequence) and len(rows_r) == 7
    breaks = regret["break_even_trend_premium_by_equity_premium"]
    assert isinstance(breaks, Sequence) and len(breaks) == 4

    gaps = {e.name for e in result.estimates if e.name.startswith("arithmetic_gap[")}
    floors = {
        e.name.replace("minimum_detectable_effect[", "arithmetic_gap[")
        for e in result.estimates
        if e.name.startswith("minimum_detectable_effect[")
    }
    assert gaps and gaps == floors
    assert "arithmetic_gap[primary:working_default vs reference]" in gaps
    assert "arithmetic_gap[tournament_1990:working_default vs reference]" in gaps
    tables = result.diagnostics["markdown_tables"]
    assert isinstance(tables, str)
    for name in arms:
        assert f"`{name}`" in tables
    assert "Regret at forward premia" in tables
    assert "NOMINAL TEN-YEAR TREASURY" in str(result.diagnostics["freeze_note"])
    assert len(ledger.read()) >= 2
