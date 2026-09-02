"""Unit tests for Experiment 022, the excess-CAPE-yield rule run sheltered-only.

Every expected value here is computed in this file by hand or with plain NumPy,
never by calling the code under test on the same inputs. The signal fixture is
three rows copied from the Shiller workbook (sha256 71c3636d...) with the
published ``Excess_CAPE_Yield`` beside the inputs that produce it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest

import portfolio_edge.experiments.exp_022_ecy_rule as module
from portfolio_edge.experiments.exp_016_construction_tournament import MDE_MULTIPLIER
from portfolio_edge.experiments.exp_022_ecy_rule import (
    RebalanceClock,
    construction_implication,
    default_specification_path,
    episode_table,
    expanding_percentile,
    gap_stats,
    read_arms,
    regret_table,
    rolling_window_stats,
    rule_weights,
    shiller_excess_cape_yield_pp,
    walk,
)
from portfolio_edge.experiments.specification import Specification, load_specification
from portfolio_edge.studies.valuation_conditioning import (
    ConditionalWeightRule,
    conditional_weight,
)

SPEC_PATH = default_specification_path()


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(SPEC_PATH)


# --------------------------------------------------------------------------- #
# The signal, against the workbook's own column
# --------------------------------------------------------------------------- #

#: (row, CAPE, GS10 %, CPI_t, CPI_{t-120}, published Excess_CAPE_Yield as a decimal)
WORKBOOK_ROWS = (
    ("1921-01", 5.122184146887375, 5.09, 19.0, 9.229089256, 0.21920796290222025),
    ("1999-12", 44.19793976104056, 6.28, 168.3, 126.1, -0.010886526695300772),
    ("2026-08", 41.17762140136851, 4.75, 333.07374999999996, 240.849, 0.009735644305289917),
)


def test_signal_reproduces_the_workbook_column_from_its_components() -> None:
    """``100/CAPE - (GS10 - 100 ((CPI_t/CPI_{t-120})^(1/10) - 1))`` is Shiller's definition."""
    for row, cape, gs10, cpi_now, cpi_then, published in WORKBOOK_ROWS:
        # Build a 121-row array with the lagged CPI at position 0 and the row at 120.
        cape_arr = np.full(121, np.nan)
        gs_arr = np.full(121, np.nan)
        cpi_arr = np.full(121, np.nan)
        cape_arr[120], gs_arr[120], cpi_arr[120], cpi_arr[0] = cape, gs10, cpi_now, cpi_then
        got = shiller_excess_cape_yield_pp(cape_arr, gs_arr, cpi_arr)
        by_hand = 100.0 / cape - (gs10 - 100.0 * ((cpi_now / cpi_then) ** 0.1 - 1.0))
        assert got[120] == pytest.approx(by_hand, abs=1e-12), row
        assert got[120] / 100.0 == pytest.approx(published, abs=1e-12), row
        assert np.isnan(got[:120]).all()


def test_signal_is_nan_where_the_trailing_window_or_an_input_is_missing() -> None:
    cape = np.full(125, 20.0)
    gs = np.full(125, 4.0)
    cpi = np.linspace(100.0, 130.0, 125)
    gs[122] = np.nan
    out = shiller_excess_cape_yield_pp(cape, gs, cpi)
    assert np.isnan(out[:120]).all()
    assert np.isfinite(out[120]) and np.isfinite(out[121])
    assert np.isnan(out[122])


# --------------------------------------------------------------------------- #
# The expanding percentile and the rule
# --------------------------------------------------------------------------- #


def test_expanding_percentile_counts_only_prior_observations() -> None:
    values = np.array([3.0, 1.0, 2.0, np.nan, 5.0, 2.0])
    got = expanding_percentile(values, burn_in_prior=2)
    # index 2: priors {3, 1}, value 2 -> 1 of 2 below.
    # index 3: NaN stays NaN and is not added to the history.
    # index 4: priors {3, 1, 2}, value 5 -> 3 of 3.
    # index 5: priors {3, 1, 2, 5}, value 2 -> strictly below: {1} -> 1 of 4.
    assert np.isnan(got[0]) and np.isnan(got[1]) and np.isnan(got[3])
    assert got[2] == pytest.approx(0.5)
    assert got[4] == pytest.approx(1.0)
    assert got[5] == pytest.approx(0.25)


def test_rule_weights_match_the_study_form_and_a_hand_value() -> None:
    pct = np.array([0.187, 0.5, 0.0, 1.0, np.nan])
    got = rule_weights(pct, base=0.80, sensitivity=0.4, floor=0.0, cap=1.0)
    assert got[0] == pytest.approx(0.80 + 0.4 * (0.187 - 0.5))  # 0.6748, the page's 0.675
    assert got[1] == pytest.approx(0.80)
    assert got[2] == pytest.approx(0.60)
    assert got[3] == pytest.approx(1.00)
    assert np.isnan(got[4])
    rule = ConditionalWeightRule(0.80, 0.4)
    for p, w in zip(pct[:4], got[:4], strict=True):
        assert w == pytest.approx(conditional_weight(rule, float(p)))


# --------------------------------------------------------------------------- #
# The walk, by hand
# --------------------------------------------------------------------------- #


def test_monthly_walk_two_period_fixture_with_execution_charged_on_the_sale() -> None:
    target = np.array([0.8, 0.6])
    equity = np.array([0.10, -0.05])
    bond = np.array([0.01, 0.02])
    clock = RebalanceClock(name="monthly", review_every_months=1, relative_band=0.0)
    result = walk(target, equity, bond, spread_bp=10.0, clock=clock)
    # Month 0: buy 0.8 free, earn 0.8*0.10 + 0.2*0.01.
    r0 = 0.8 * 0.10 + 0.2 * 0.01
    # Drift: equity 0.88, bond 0.202 -> held 0.88/1.082.
    held = 0.88 / 1.082
    # Month 1: trade to 0.6, cost |0.6 - held| * 10bp.
    change = abs(0.6 - held)
    r1 = 0.6 * -0.05 + 0.4 * 0.02 - change * 10.0 / 1e4
    assert result.returns == pytest.approx(np.array([r0, r1]), abs=1e-14)
    assert result.held_weights == pytest.approx(np.array([0.8, 0.6]))
    assert result.turnover_per_year == pytest.approx(change / (2 / 12))
    assert result.rebalances_per_year == pytest.approx(1 / (2 / 12))
    assert result.trades == 1


def test_annual_band_walk_trades_only_at_a_review_and_only_outside_the_band() -> None:
    clock = RebalanceClock(name="annual_band", review_every_months=12, relative_band=0.25)
    n = 25
    # Flat returns so weights never drift; the target moves at month 12 (inside the band)
    # and at month 24 (outside it).
    equity = np.zeros(n)
    bond = np.zeros(n)
    target = np.full(n, 0.80)
    target[12:] = 0.76  # bond 0.24 against 0.20 held: 20% relative, inside the band
    target[24:] = 0.70  # bond 0.30 against 0.20 held: 50% relative, outside
    result = walk(target, equity, bond, spread_bp=10.0, clock=clock)
    assert result.trades == 1
    assert result.held_weights[12] == pytest.approx(0.80)
    assert result.held_weights[24] == pytest.approx(0.70)
    assert result.returns[24] == pytest.approx(-0.10 * 10.0 / 1e4)
    assert result.turnover_per_year == pytest.approx(0.10 / (n / 12))


def test_walk_refuses_a_nan_target() -> None:
    clock = RebalanceClock(name="monthly", review_every_months=1, relative_band=0.0)
    with pytest.raises(module.EcyRuleError):
        walk(np.array([0.8, np.nan]), np.zeros(2), np.zeros(2), spread_bp=0.0, clock=clock)


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def test_gap_stats_matches_the_formulas() -> None:
    rng = np.random.default_rng(22)
    arm = rng.normal(0.006, 0.04, 360)
    control = rng.normal(0.005, 0.04, 360)
    stats = gap_stats(arm, control, hac_lags=12)
    d = arm - control
    assert stats.gap_pp_yr == pytest.approx(float(np.mean(d)) * 1200.0)
    assert stats.log_gap_pp_yr == pytest.approx(
        float(np.mean(np.log1p(arm) - np.log1p(control))) * 1200.0
    )
    assert stats.mde_pp_yr == pytest.approx(
        MDE_MULTIPLIER * float(np.std(d, ddof=1)) / math.sqrt(360) * 1200.0
    )
    assert stats.tracking_error_pct == pytest.approx(float(np.std(d, ddof=1)) * math.sqrt(12) * 100)
    assert stats.interval[0] <= stats.gap_pp_yr <= stats.interval[1]
    assert stats.interval[1] - stats.interval[0] == pytest.approx(
        2 * 1.959964 * stats.standard_error_pp_yr
    )
    assert stats.months == 360


def test_rolling_window_stats_by_hand() -> None:
    arm = np.array([0.01, 0.02, 0.00, 0.03])
    control = np.array([0.00, 0.01, 0.02, 0.01])
    got = rolling_window_stats(arm, control, window_months=2)
    d = arm - control  # [0.01, 0.01, -0.02, 0.02]
    windows = np.array([d[0:2].mean(), d[1:3].mean(), d[2:4].mean()]) * 12 * 1e4
    assert got["n_windows"] == 3.0
    assert got["n_independent"] == pytest.approx(1.5)
    assert got["share_ahead"] == pytest.approx(np.mean(windows > 0))
    assert got["median_bp"] == pytest.approx(float(np.median(windows)))


def test_episode_table_reports_entry_weight_and_cumulative_return() -> None:
    periods = ["2000-01", "2000-02", "2000-03", "2000-04"]
    series = {"rule": np.array([0.01, -0.10, 0.05, 0.02])}
    weights = np.array([0.8, 0.7, 0.7, 0.6])
    rows = episode_table(
        periods, series, weights, [("x", "2000-02", "2000-03"), ("y", "1990-01", "1990-02")]
    )
    assert rows[0]["covered"] is True
    assert rows[0]["entry_equity_weight"] == pytest.approx(0.7)
    assert rows[0]["rule_cumulative_pct"] == pytest.approx(100 * (0.9 * 1.05 - 1), abs=1e-2)
    assert rows[0]["rule_worst_drawdown_pct"] == pytest.approx(-10.0)
    assert rows[1]["covered"] is False


def _as_float(value: object) -> float:
    assert isinstance(value, int | float)
    return float(value)


def test_regret_table_closed_form() -> None:
    rows = regret_table(
        position_weight=0.85,
        counterfactual_weight=1.0,
        premia_pp_yr=[0.0, 3.0],
        equity_volatility=0.16,
        bond_volatility=0.08,
        correlation=0.1,
        horizons_years=[30],
    )

    def variance(w: float) -> float:
        return w**2 * 0.16**2 + (1 - w) ** 2 * 0.08**2 + 2 * w * (1 - w) * 0.1 * 0.16 * 0.08

    for row, m in zip(rows, (0.0, 3.0), strict=True):
        gap = (0.85 * m / 100 - 0.5 * variance(0.85)) - (1.0 * m / 100 - 0.5 * variance(1.0))
        assert row["arithmetic_cost_bp_yr"] == pytest.approx(1e4 * 0.15 * m / 100, abs=0.05)
        assert row["log_growth_gap_bp_yr"] == pytest.approx(1e4 * gap, abs=0.05)
        assert row["terminal_wealth_ratio_30y_pct"] == pytest.approx(
            100 * (math.exp(gap * 30) - 1), abs=0.01
        )
    # At a zero premium the lower-variance position is the better action.
    assert rows[0]["regret_of_position_bp_yr"] == 0.0
    assert _as_float(rows[0]["regret_of_counterfactual_bp_yr"]) > 0.0
    # At three points the cut costs more than the variance it saves.
    assert _as_float(rows[1]["regret_of_position_bp_yr"]) > 0.0


def test_construction_implication_sells_the_wrapper_line_only() -> None:
    got = construction_implication(
        published_vector={
            "RSST": 30,
            "VTI": 19,
            "VTV": 15,
            "VXUS": 16,
            "AVDV": 10,
            "IDMO": 5,
            "AVES": 5,
        },
        traditional_third={"RSST": 30.0, "IDMO": 3.3},
        third_size_pp=33.3,
        equity_weight_today=0.85,
    )
    assert got["bond_pp_of_portfolio"] == pytest.approx(0.15 * 33.3, abs=0.01)
    assert got["rsst_after_pp"] == pytest.approx(30.0 - 0.15 * 33.3, abs=0.01)
    assert got["idmo_unchanged_pp"] == 3.3
    assert got["equity_notional_cut_pp"] == pytest.approx(1.072 * 0.15 * 33.3, abs=0.02)
    assert got["gross_exposure_before"] == pytest.approx(0.70 + 0.30 * 2.072, abs=1e-4)
    assert got["published_vector_sums_to"] == 100


# --------------------------------------------------------------------------- #
# The specification
# --------------------------------------------------------------------------- #


def test_specification_declares_one_primary_arm_and_the_six_arm_family(
    specification: Specification,
) -> None:
    arms = read_arms(specification)
    assert set(arms) == {
        "k02_treasury",
        "k04_treasury",
        "k06_treasury",
        "k02_tips",
        "k04_tips",
        "k06_tips",
    }
    primary = [a for a in arms.values() if a.role == "primary"]
    assert len(primary) == 1 and primary[0].name == "k04_treasury"
    assert primary[0].sensitivity == 0.4
    parameters = specification.parameters
    assert isinstance(parameters, Mapping)
    rule = parameters["rule"]
    assert isinstance(rule, Mapping)
    assert rule["base_weight"] == 0.80 and rule["signal_lag_months"] == 1
    assert specification.run_kind.value == "exploratory"
    assert "chosen on this data" in specification.notes


# --------------------------------------------------------------------------- #
# The whole experiment on a short synthetic history
# --------------------------------------------------------------------------- #


def _synthetic_raw_series() -> module.RawSeries:
    rng = np.random.default_rng(20260902)
    n = 480 + 12 * 60  # forty years of burn-in plus sixty years of decisions
    periods = tuple(f"{1871 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(n))
    equity_log = rng.normal(0.005, 0.045, n - 1)
    bond_log = rng.normal(0.0015, 0.02, n - 1)
    cape = np.exp(np.cumsum(rng.normal(0.0, 0.03, n)) * 0.5) * 15.0
    gs10 = np.clip(4.0 + np.cumsum(rng.normal(0.0, 0.05, n)), 1.0, 15.0)
    cpi = np.cumprod(1.0 + rng.normal(0.002, 0.003, n)) * 10.0
    inflation = np.full(n, np.nan)
    inflation[120:] = 100.0 * ((cpi[120:] / cpi[:-120]) ** 0.1 - 1.0)
    workbook_ecy = (100.0 / cape - (gs10 - inflation)) / 100.0
    fii_months = [p for p in periods if p >= "1911-01"]
    fii10 = {p: 0.01 + 0.003 * float(rng.normal()) for p in fii_months}  # decimal, FRED's
    french_months = [p for p in periods if p >= "1900-07"]
    french_market = {p: float(rng.normal(0.006, 0.045)) for p in french_months}
    french_rf = {p: 0.002 for p in french_months}
    return module.RawSeries(
        periods=periods,
        cape=cape,
        gs10=gs10,
        cpi=cpi,
        real_equity_index=np.concatenate([[100.0], 100.0 * np.exp(np.cumsum(equity_log))]),
        real_bond_index=np.concatenate([[10.0], 10.0 * np.exp(np.cumsum(bond_log))]),
        workbook_ecy=workbook_ecy,
        fii10=fii10,
        french_market=french_market,
        french_rf=french_rf,
        provenance=({"id": "synthetic"},),
        findings=("synthetic",),
    )


def _synthetic_specification(specification: Specification) -> Specification:
    """The committed specification with its windows moved on to the synthetic calendar."""
    from portfolio_edge.experiments.specification import plain_json, specification_from_mapping

    raw = plain_json(specification.canonical_form())
    assert isinstance(raw, dict)
    raw.pop("schema_version")
    parameters = raw["parameters"]
    assert isinstance(parameters, dict)
    parameters["windows"] = [
        {"id": "full", "start": "1921-01", "end": "1970-11"},
        {"id": "modern", "start": "1950-01", "end": "1970-11"},
    ]
    parameters["crisis_episodes"] = [
        {"name": "a", "start": "1930-01", "end": "1930-06"},
        {"name": "b", "start": "1990-01", "end": "1990-06"},
    ]
    parameters["rolling_window_years"] = 5
    inference = raw["inference"]
    assert isinstance(inference, dict)
    inference["resamples"] = 200
    raw["sample_policy"]["eras"] = [
        {"name": "first", "start": "1921-01", "end": "1949-12", "rationale": "synthetic"},
        {"name": "second", "start": "1950-01", "end": "1970-11", "rationale": "synthetic"},
    ]
    return specification_from_mapping(raw, source_path=Path("synthetic.yaml"))


def test_build_panel_reconstructs_the_legs_and_the_french_real_return_by_hand(
    specification: Specification,
) -> None:
    raw = _synthetic_raw_series()
    panel = module.build_panel(raw, specification)
    i = 600  # a row inside every series' coverage
    later = raw.periods[i + 1]
    assert panel.equity[i] == pytest.approx(
        raw.real_equity_index[i + 1] / raw.real_equity_index[i] - 1.0
    )
    assert panel.legs["treasury"][i] == pytest.approx(
        raw.real_bond_index[i + 1] / raw.real_bond_index[i] - 1.0
    )
    # French: decimal nominal total return deflated by the CPI ratio of the two rows.
    nominal = 1.0 + raw.french_market[later] + raw.french_rf[later]
    assert panel.french_equity[i] == pytest.approx(nominal / (raw.cpi[i + 1] / raw.cpi[i]) - 1.0)
    # The TIPS signal replaces the real-yield proxy with FII10 where FII10 exists.
    assert panel.signals["tips_spliced"][i] == pytest.approx(
        100.0 / raw.cape[i] - 100.0 * raw.fii10[raw.periods[i]]
    )
    # The TIPS leg is a ten-year par bond on the decimal real yield: coupon accrual,
    # duration and convexity terms from the shelf's own `par_bond_risk`.
    from portfolio_edge.studies.fixed_income_shelf import par_bond_risk

    y0, y1 = raw.fii10[raw.periods[i]], raw.fii10[later]
    modified, convexity = par_bond_risk(y0, periods=20.0)
    assert panel.legs["tips_spliced"][i] == pytest.approx(
        y0 / 12.0 - modified * (y1 - y0) + 0.5 * convexity * (y1 - y0) ** 2
    )
    assert panel.signals["shiller"][i] == pytest.approx(100.0 * raw.workbook_ecy[i])
    assert panel.tips_first_month == "1911-02"


def test_the_whole_experiment_runs_and_reports_what_the_contract_requires(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, specification: Specification
) -> None:
    from portfolio_edge.experiments.ledger import Ledger, RunStatus
    from portfolio_edge.experiments.result import ResultStatus
    from portfolio_edge.experiments.runner import run_experiment

    monkeypatch.setattr(module, "load_series", lambda _spec: _synthetic_raw_series())
    synthetic = _synthetic_specification(specification)
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        synthetic,
        registry=module.build_registry(),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    assert outcome.status is RunStatus.SUCCEEDED
    result = outcome.result
    assert result is not None
    assert result.status in {
        ResultStatus.EXPLORATORY,
        ResultStatus.UNRESOLVED,
        ResultStatus.REJECTED,
    }

    comparisons = result.diagnostics["comparisons"]
    assert isinstance(comparisons, Sequence)
    seen: set[tuple[str, str, str, str]] = set()
    for row in comparisons:
        assert isinstance(row, Mapping)
        seen.add((str(row["window"]), str(row["clock"]), str(row["arm"]), str(row["control"])))
        gaps = row["gaps"]
        assert isinstance(gaps, Mapping)
        assert set(gaps) == {"gross", "net_optimistic", "net_pessimistic"}
        for basis in gaps.values():
            assert isinstance(basis, Mapping)
            # A gap never appears without its floor, its interval and its months.
            assert basis["mde_80pc_power_pp_yr"] is not None
            assert isinstance(basis["interval_95"], Sequence)
            assert basis["months"]
        assert row["status"] in {"exploratory", "unresolved", "rejected"}
        assert str(row["clause"]).startswith("(")
    windows = {w for w, _, _, _ in seen}
    clocks = {c for _, c, _, _ in seen}
    arms = {a for _, _, a, _ in seen}
    controls = {k for _, _, _, k in seen}
    assert windows == {"full", "modern"}
    assert clocks == {"monthly", "annual_band"}
    assert {
        "k04_treasury",
        "sens_french",
        "sens_shiller_french_window",
        "sens_lag_zero",
        "sens_tips_signal",
    } <= arms
    assert controls == {"risk_matched", "equity100", "mix85"}

    gap_names = {e.name for e in result.estimates if e.name.startswith("arithmetic_gap[")}
    floor_names = {
        e.name.replace("minimum_detectable_effect[", "arithmetic_gap[")
        for e in result.estimates
        if e.name.startswith("minimum_detectable_effect[")
    }
    assert gap_names and gap_names == floor_names
    assert any(e.name == "bootstrap_check[primary]" for e in result.estimates)

    holm = result.diagnostics["holm"]
    assert isinstance(holm, Mapping)
    by_window = holm["adjusted_p_by_window"]
    assert isinstance(by_window, Mapping)
    for window in by_window.values():
        assert isinstance(window, Mapping)
        assert len(window) == 6
        for p in window.values():
            assert isinstance(p, float) and 0.0 <= p <= 1.0
    deflated = result.diagnostics["deflated_sharpe"]
    assert isinstance(deflated, Mapping)
    assert deflated["nominal_trials"] == 6
    episodes = result.diagnostics["crisis_episodes"]
    assert isinstance(episodes, Sequence)
    covered = {str(e["episode"]): e["covered"] for e in episodes if isinstance(e, Mapping)}
    assert covered == {"a": True, "b": False}
    today = result.diagnostics["today"]
    assert isinstance(today, Mapping)
    assert {"shiller", "tips_spliced"} <= set(today)
    regret = result.diagnostics["regret"]
    assert isinstance(regret, Mapping) and isinstance(regret["rows"], Sequence)
    assert len(regret["rows"]) == 4
    construction = result.diagnostics["construction"]
    assert isinstance(construction, Mapping)
    assert construction["line_sold"] == "RSST"
    assert isinstance(result.diagnostics["markdown_tables"], str)
    assert "selected on this data" in str(
        result.diagnostics["freeze_note"]
    ) or "chosen on this" in str(result.diagnostics["freeze_note"])
    assert len(ledger.read()) >= 2
