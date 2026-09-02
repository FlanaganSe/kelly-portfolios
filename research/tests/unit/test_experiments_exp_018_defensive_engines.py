"""Unit tests for Experiment 018, defensive engines inside the leveraged construction.

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

import portfolio_edge.experiments.exp_018_defensive_engines as module
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    BasisPanel,
    CostSettings,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    Comparison,
    FinancingRates,
    Wrapper,
    _apply_falsifier,
    arithmetic_gap,
    arm_notional,
    build_trend_book,
    contribution_terminal_wealth,
    default_specification_path,
    read_arms,
    read_rates,
    read_wrappers,
    simulate_arm,
    wrapper_excess,
)
from portfolio_edge.experiments.specification import (
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.studies.time_series_momentum import TimeSeriesMomentumSpec

SPEC_PATH = default_specification_path()


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


EXPECTED_NOTIONAL = {
    # arm: (gross, equity, trend, bond, gold, cash)
    "base_trend30": (0.70 + 0.30 * 2.072, 0.70 + 0.30 * 1.072, 0.30, 0.0, 0.0, 0.0),
    "base_no_trend": (1.0, 1.0, 0.0, 0.0, 0.0, 0.0),
    "trend30_bondstack20": (
        0.50 + 0.30 * 2.072 + 0.20 * 2.0,
        0.50 + 0.30 * 1.072 + 0.20,
        0.30,
        0.20,
        0.0,
        0.0,
    ),
    "trend30_bondstack40": (
        0.30 + 0.30 * 2.072 + 0.40 * 2.0,
        0.30 + 0.30 * 1.072 + 0.40,
        0.30,
        0.40,
        0.0,
        0.0,
    ),
    "trend20_rsbt10": (
        0.70 + 0.20 * 2.072 + 0.10 * 2.0,
        0.70 + 0.20 * 1.072,
        0.20 + 0.10,
        0.10,
        0.0,
        0.0,
    ),
    "ntsx100": (1.5, 0.9, 0.0, 0.6, 0.0, 0.0),
    "trend30_goldstack10": (
        0.60 + 0.30 * 2.072 + 0.10 * 1.8,
        0.60 + 0.30 * 1.072 + 0.09,
        0.30,
        0.0,
        0.09,
        0.0,
    ),
    "trend30_cash10": (0.60 + 0.30 * 2.072, 0.60 + 0.30 * 1.072, 0.30, 0.0, 0.0, 0.10),
    "trend30_ltbond10": (0.60 + 0.30 * 2.072 + 0.10, 0.60 + 0.30 * 1.072, 0.30, 0.10, 0.0, 0.0),
    "trend30_tipsstack20": (
        0.50 + 0.30 * 2.072 + 0.20 * 2.0,
        0.50 + 0.30 * 1.072 + 0.20,
        0.30,
        0.20,
        0.0,
        0.0,
    ),
}


def test_every_arm_in_the_specification_derives_the_notional_the_design_states(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    assert set(arms) == set(EXPECTED_NOTIONAL)
    for name, arm in arms.items():
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        gross, equity, trend, bond, gold, cash = EXPECTED_NOTIONAL[name]
        assert notional.gross == pytest.approx(gross, abs=1e-12), name
        assert notional.equity == pytest.approx(equity, abs=1e-12), name
        assert notional.trend == pytest.approx(trend, abs=1e-12), name
        assert notional.bond == pytest.approx(bond, abs=1e-12), name
        assert notional.gold == pytest.approx(gold, abs=1e-12), name
        assert notional.cash == pytest.approx(cash, abs=1e-12), name
    # The task's stated figures for the reference and the RSBT arm, to four places.
    assert arm_notional(
        arms["base_trend30"].tickers, arms["base_trend30"].weights, wrappers
    ).equity == pytest.approx(1.0216)
    assert arm_notional(
        arms["trend20_rsbt10"].tickers, arms["trend20_rsbt10"].weights, wrappers
    ).equity == pytest.approx(0.9144)


def test_capital_weights_must_sum_to_one(specification: Specification) -> None:
    arms = read_arms(specification)
    for arm in arms.values():
        assert sum(arm.weights) == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Financing accrues against the holder
# --------------------------------------------------------------------------- #


def test_wrapper_financing_and_fee_are_subtracted_on_the_notional_they_apply_to() -> None:
    rates = FinancingRates(equity=62.0, treasury=15.0, gold=30.0, tips=15.0)
    rssb = Wrapper(
        ticker="RSSB_LIKE",
        exposures={"equity": 1.0, "treasury": 1.0},
        fee_bp=39.0,
        financed={"equity": 0.10, "treasury": 1.0},
    )
    panel = _panel(3, legs={"equity": [0.0, 0.0, 0.0], "treasury": [0.0, 0.0, 0.0]}, cash=[0.0] * 3)
    excess = wrapper_excess(panel, rssb, rates)
    expected = -(39.0 + 0.10 * 62.0 + 1.0 * 15.0) / 10_000.0 / 12.0
    assert excess == pytest.approx(np.full(3, expected))
    assert expected < 0.0
    # Doubling the financed Treasury notional doubles only that charge.
    heavier = Wrapper(
        ticker="X", exposures={"treasury": 2.0}, fee_bp=39.0, financed={"treasury": 2.0}
    )
    assert wrapper_excess(panel, heavier, rates)[0] == pytest.approx(
        -(39.0 + 2.0 * 15.0) / 10_000.0 / 12.0
    )


def test_a_levered_control_pays_the_equity_basis_on_its_debt() -> None:
    """1.5x CORE on a month with zero market return: the debt costs 62 bp/12 on 0.5."""
    rates = FinancingRates(equity=62.0, treasury=15.0, gold=30.0, tips=15.0)
    wrappers = {"CORE": Wrapper(ticker="CORE", exposures={"equity": 1.0}, fee_bp=3.0, financed={})}
    costs = CostSettings(
        equity_futures_basis=rates.equity / 10_000.0,
        trend_book_financing=0.0,
        round_trip_spread={"us_equity": 0.0},
    )
    panel = _panel(2, legs={"equity": [0.0, 0.0]}, cash=[0.0, 0.0])
    path = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.5]))
    fee_month = 3.0 / 10_000.0 / 12.0
    expected = 1.5 * (1.0 - fee_month) - 0.5 * (1.0 + 0.0062 / 12.0) - 1.0
    assert path.total[0] == pytest.approx(expected, abs=1e-12)
    assert expected < 0.0
    # An unlevered holding has no debt and pays only the fee.
    flat = simulate_arm(panel, wrappers, rates, costs, tickers=("CORE",), targets=np.array([1.0]))
    assert flat.total[0] == pytest.approx(-fee_month, abs=1e-12)


# --------------------------------------------------------------------------- #
# A two-period fixture for a bond-stack arm, computed by hand
# --------------------------------------------------------------------------- #


def test_bond_stack_arm_two_period_fixture(specification: Specification) -> None:
    """50% CORE + 30% RSST_LIKE + 20% RSSB_LIKE over two months, spreads off.

    With monthly rebalancing to capital weights summing to one there is no debt,
    so each month's total return is ``cash + sum_i w_i * excess_i`` and the
    wealth path compounds those two numbers.
    """
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    rates = read_rates(specification)
    arm = arms["trend30_bondstack20"]
    costs = CostSettings(
        equity_futures_basis=rates.equity / 10_000.0,
        trend_book_financing=0.0,
        round_trip_spread={"us_equity": 0.0},
    )
    equity = [0.02, -0.03]
    treasury = [0.01, 0.004]
    trend = [-0.005, 0.012]
    cash = [0.003, 0.002]
    panel = _panel(2, legs={"equity": equity, "treasury": treasury, "trend": trend}, cash=cash)
    path = simulate_arm(
        panel,
        wrappers,
        rates,
        costs,
        tickers=arm.tickers,
        targets=np.asarray(arm.weights),
    )

    def per_dollar(t: int) -> dict[str, float]:
        core = equity[t] - 3.0 / 120_000.0
        rsst = 1.072 * equity[t] + trend[t] - (99.0 + 0.331 * 62.0) / 120_000.0
        rssb = equity[t] + treasury[t] - (39.0 + 0.10 * 62.0 + 1.0 * 15.0) / 120_000.0
        return {"CORE": core, "RSST_LIKE": rsst, "RSSB_LIKE": rssb}

    expected = []
    for t in range(2):
        legs = per_dollar(t)
        expected.append(
            cash[t] + 0.50 * legs["CORE"] + 0.30 * legs["RSST_LIKE"] + 0.20 * legs["RSSB_LIKE"]
        )
    assert path.total == pytest.approx(np.asarray(expected), abs=1e-12)
    assert float(np.prod(1.0 + path.total)) == pytest.approx(
        (1.0 + expected[0]) * (1.0 + expected[1]), abs=1e-12
    )


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def test_arithmetic_gap_matches_the_formula() -> None:
    rng = np.random.default_rng(3)
    arm = rng.normal(0.006, 0.04, 240)
    bench = rng.normal(0.005, 0.04, 240)
    indices = stationary_bootstrap_indices(240, 12.0, 500, rng)
    stats = arithmetic_gap(arm, bench, indices=indices, confidence=0.95)
    d = arm - bench
    assert stats.gap_pp_yr == pytest.approx(float(np.mean(d)) * 1200.0)
    assert stats.mde_pp_yr == pytest.approx(
        MDE_MULTIPLIER * float(np.std(d, ddof=1)) / math.sqrt(240) * 1200.0
    )
    assert stats.tracking_error_pct == pytest.approx(
        float(np.std(d, ddof=1)) * math.sqrt(12) * 100.0
    )
    assert stats.interval[0] <= stats.gap_pp_yr <= stats.interval[1]
    assert stats.years_to_distinguish == pytest.approx(
        (MDE_MULTIPLIER * float(np.std(d, ddof=1)) * math.sqrt(12) * 100.0 / stats.gap_pp_yr) ** 2
    )


def test_contribution_weighted_terminal_wealth_by_hand() -> None:
    total = np.array([0.10, -0.05])
    expected = ((1.0 + 0.01) * 1.10 + 0.01) * 0.95
    assert contribution_terminal_wealth(total, contribution=0.01) == pytest.approx(expected)


def test_falsifier_clauses_fire_in_order() -> None:
    def comparison(gap: float, mde: float) -> Comparison:
        from portfolio_edge.experiments.exp_016_construction_tournament import GapStatistics

        return Comparison(
            control="cheap",
            definition="",
            gap=GapStatistics(
                gap_pp_yr=gap,
                interval=(gap - 1.0, gap + 1.0),
                mde_pp_yr=mde,
                mde_bootstrap_pp_yr=mde,
                p_value=0.01,
                tracking_error_pct=2.0,
                months=120,
                years_to_distinguish=10.0,
            ),
        )

    negative = comparison(-0.5, 1.0)
    _apply_falsifier(negative, q=0.10)
    assert negative.status == "rejected"
    inside = comparison(0.5, 1.0)
    _apply_falsifier(inside, q=0.10)
    assert inside.status == "unresolved" and inside.clause.startswith("(b)")
    adjusted = comparison(2.0, 1.0)
    adjusted.adjusted_p = 0.5
    _apply_falsifier(adjusted, q=0.10)
    assert adjusted.clause.startswith("(c)")
    band = comparison(2.0, 1.0)
    band.adjusted_p = 0.01
    band.financing_band_range = (-0.1, 2.0)
    _apply_falsifier(band, q=0.10)
    assert band.clause.startswith("(d)")
    survives = comparison(2.0, 1.0)
    survives.adjusted_p = 0.01
    survives.financing_band_range = (1.0, 2.0)
    _apply_falsifier(survives, q=0.10)
    assert survives.status == "exploratory"


def test_trend_book_is_nan_inside_the_burn_in_and_cut_at_end() -> None:
    rng = np.random.default_rng(1)
    months = [f"{1990 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(80)]
    a = {m: float(v) for m, v in zip(months, rng.normal(0.005, 0.03, 80), strict=True)}
    b = {m: float(v) for m, v in zip(months, rng.normal(0.002, 0.02, 80), strict=True)}
    book = build_trend_book(
        (a, b), spec=TimeSeriesMomentumSpec(), minimum_instruments=2, end="1995-06"
    )
    assert min(book) == months[36]
    assert max(book) == "1995-06"
    assert all(math.isfinite(v) for v in book.values())


# --------------------------------------------------------------------------- #
# The whole experiment on a short synthetic history
# --------------------------------------------------------------------------- #


def _synthetic_raw_series() -> module.RawSeries:
    rng = np.random.default_rng(20260901)
    months = [f"{1988 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(216)]
    equity = rng.normal(0.006, 0.045, 216)
    bond = rng.normal(0.002, 0.025, 216)
    cash = np.full(216, 0.003)

    def series(values: NDArray[np.float64]) -> dict[str, float]:
        return {m: float(v) for m, v in zip(months, values, strict=True)}

    gold = np.cumprod(1.0 + rng.normal(0.003, 0.05, 216)) * 400.0
    cpi = np.cumprod(1.0 + rng.normal(0.002, 0.002, 216)) * 100.0
    return module.RawSeries(
        equity=series(equity),
        cash=series(cash),
        ltr=series(bond + cash),
        corpr=series(bond + cash + rng.normal(0.0005, 0.01, 216)),
        gw_rfree=series(cash),
        commodity=series(rng.normal(0.002, 0.05, 216)),
        tsmom=series(rng.normal(0.008, 0.035, 216)),
        gold_levels=series(gold),
        gs10_yield=series(np.clip(0.05 + rng.normal(0.0, 0.003, 216), 0.01, 0.15)),
        fii10_yield=series(0.02 + rng.normal(0.0, 0.002, 216)),
        cpi=series(cpi),
        provenance=({"id": "synthetic"},),
        findings=("synthetic",),
    )


def test_the_whole_experiment_runs_and_reports_what_the_contract_requires(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, specification: Specification
) -> None:
    from portfolio_edge.experiments.ledger import Ledger, RunStatus
    from portfolio_edge.experiments.result import ResultStatus
    from portfolio_edge.experiments.runner import run_experiment

    monkeypatch.setattr(module, "load_series", lambda _spec: _synthetic_raw_series())
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
    assert {"primary", "primary_gold_subwindow", "secondary", "tertiary_check"} <= set(by_id)
    arms = read_arms(specification)
    for panel in by_id.values():
        rows = panel["arms"]
        assert isinstance(rows, Sequence)
        for row in rows:
            assert isinstance(row, Mapping)
            assert str(row["arm"]) in arms
            notional = row["notional"]
            assert isinstance(notional, Mapping)
            assert {"gross", "equity", "trend", "bond", "gold", "cash"} <= set(notional)
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
                # A gap never appears without its floor, its control or its status.
                assert comparison["gap_pp_yr"] is not None
                assert comparison["mde_80pc_power_pp_yr"] is not None
                assert comparison["control_definition"]
                assert comparison["status"] in {"exploratory", "unresolved", "rejected"}
                assert isinstance(comparison["era_gaps_pp_yr"], Mapping)
        assert isinstance(panel["bond_equity_regime_by_era"], Sequence)

    gaps = {e.name for e in result.estimates if e.name.startswith("arithmetic_gap[")}
    floors = {
        e.name.replace("minimum_detectable_effect[", "arithmetic_gap[")
        for e in result.estimates
        if e.name.startswith("minimum_detectable_effect[")
    }
    assert gaps and gaps == floors
    tables = result.diagnostics["markdown_tables"]
    assert isinstance(tables, str)
    for name in arms:
        assert f"`{name}`" in tables
    assert "1971-08..1974-12" in str(result.diagnostics["freeze_note"])
    assert isinstance(result.diagnostics["bond_series_sensitivity"], Mapping)
    assert len(ledger.read()) >= 2
