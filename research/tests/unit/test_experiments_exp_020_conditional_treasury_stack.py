"""Unit tests for Experiment 020, the bond-regime-conditioned Treasury stack.

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

import portfolio_edge.experiments.exp_020_conditional_treasury_stack as module
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    BasisPanel,
    CostSettings,
)
from portfolio_edge.experiments.exp_018_defensive_engines import (
    arm_notional,
    read_arms,
    read_rates,
    read_wrappers,
    simulate_arm,
)
from portfolio_edge.experiments.exp_020_conditional_treasury_stack import (
    COMPLEMENT_WINDOW,
    FULL_WINDOW,
    RuleSpec,
    WindowGap,
    _apply_falsifier,
    default_specification_path,
    read_rules,
    regret_gap_pp_yr,
    rule_state,
    switch_cost_series,
    trailing_correlation,
    window_gap,
    window_indices,
)
from portfolio_edge.experiments.specification import Specification, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices

SPEC_PATH = default_specification_path()


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(SPEC_PATH)


def _panel(
    months: int, *, legs: Mapping[str, Sequence[float]], cash: Sequence[float], start: int = 2000
) -> BasisPanel:
    return BasisPanel(
        periods=tuple(f"{start + i // 12:04d}-{i % 12 + 1:02d}" for i in range(months)),
        series={k: np.asarray(v, dtype=np.float64) for k, v in legs.items()},
        cash=np.asarray(cash, dtype=np.float64),
        provenance=(),
        findings=(),
    )


# --------------------------------------------------------------------------- #
# The frozen design
# --------------------------------------------------------------------------- #


def test_the_specification_declares_four_arms_one_primary_and_the_stack(
    specification: Specification,
) -> None:
    rules, primary, points, stack_wrapper, funded_from = read_rules(specification)
    assert set(rules) == {
        "cond36_below0",
        "cond60_below0",
        "cond36_below_minus02",
        "cond36_below_median120",
    }
    assert primary == "cond36_below0"
    assert rules[primary].rule == "threshold"
    assert rules[primary].window_months == 36
    assert rules[primary].threshold == 0.0
    assert rules["cond60_below0"].window_months == 60
    assert rules["cond36_below_minus02"].threshold == -0.2
    assert rules["cond36_below_median120"].rule == "trailing_median"
    assert rules["cond36_below_median120"].median_window_months == 120
    assert points == 0.20
    assert (stack_wrapper, funded_from) == ("RSSB_LIKE", "CORE")
    # The prediction is written down before the run.
    assert "unresolved" in specification.hypothesis
    assert "2022" in specification.falsifier or "2022" in str(specification.parameters)


def test_the_on_and_off_notional_are_exp_018s_two_arms(specification: Specification) -> None:
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    off = arm_notional(arms["base_trend30"].tickers, arms["base_trend30"].weights, wrappers)
    on = arm_notional(
        arms["trend30_bondstack20"].tickers, arms["trend30_bondstack20"].weights, wrappers
    )
    assert off.gross == pytest.approx(0.70 + 0.30 * 2.072)
    assert on.gross == pytest.approx(0.50 + 0.30 * 2.072 + 0.20 * 2.0)
    assert on.equity == pytest.approx(off.equity)
    assert on.bond == pytest.approx(0.20) and off.bond == 0.0
    # The certain cost of the leg while on, by hand: 0.2 x (39 + 15 + 6.2) - 0.2 x 3 = 11.44 bp.
    rates = read_rates(specification)
    rssb = wrappers["RSSB_LIKE"]
    cost = 0.20 * (rssb.fee_bp + rates.treasury * 1.0 + rates.equity * 0.10) - 0.20 * 3.0
    assert cost == pytest.approx(11.44)


# --------------------------------------------------------------------------- #
# The signal: correlation through t-1, applied to t
# --------------------------------------------------------------------------- #


def test_trailing_correlation_uses_only_the_months_before_t() -> None:
    rng = np.random.default_rng(7)
    x = rng.normal(size=60)
    y = rng.normal(size=60)
    out = trailing_correlation(x, y, 12)
    assert np.all(np.isnan(out[:12]))
    # By hand at t = 12: the first twelve months, none of month 12 itself.
    expected = np.corrcoef(x[0:12], y[0:12])[0, 1]
    assert out[12] == pytest.approx(expected)
    # Changing month t must not move the signal at t.
    x2 = x.copy()
    x2[30] += 10.0
    assert trailing_correlation(x2, y, 12)[30] == pytest.approx(out[30])
    assert trailing_correlation(x2, y, 12)[31] != pytest.approx(out[31])


def test_threshold_and_median_rules_by_hand() -> None:
    signal = np.array([np.nan, np.nan, -0.5, 0.1, -0.1, 0.0, 0.3, -0.25, -0.2])
    below_zero = RuleSpec(
        name="a",
        rule="threshold",
        window_months=3,
        threshold=0.0,
        median_window_months=None,
        note="",
    )
    state = rule_state(signal, below_zero)
    assert np.isnan(state[0]) and np.isnan(state[1])
    assert state[2:].tolist() == [1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0]
    strict = RuleSpec(
        name="b",
        rule="threshold",
        window_months=3,
        threshold=-0.2,
        median_window_months=None,
        note="",
    )
    assert rule_state(signal, strict)[2:].tolist() == [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    median = RuleSpec(
        name="c",
        rule="trailing_median",
        window_months=3,
        threshold=None,
        median_window_months=3,
        note="",
    )
    m = rule_state(signal, median)
    # Defined from the first t with three finite values ending at t inclusive: t = 4.
    assert np.all(np.isnan(m[:4]))
    # t = 4: values [-0.5, 0.1, -0.1], median -0.1, signal -0.1 is not below -> off.
    # t = 5: [0.1, -0.1, 0.0], median 0.0, signal 0.0 -> off.
    # t = 6: [-0.1, 0.0, 0.3], median 0.0, signal 0.3 -> off.
    # t = 7: [0.0, 0.3, -0.25], median 0.0, signal -0.25 -> on.
    # t = 8: [0.3, -0.25, -0.2], median -0.2, signal -0.2 -> off.
    assert m[4:].tolist() == [0.0, 0.0, 0.0, 1.0, 0.0]


def test_switch_cost_is_two_legs_times_the_one_way_rate_on_each_change() -> None:
    state = np.array([0.0, 0.0, 1.0, 1.0, 0.0, 1.0])
    cost = switch_cost_series(state, one_way_bp=10.0, points=0.20)
    per_switch = 2.0 * 0.20 * 10.0 / 10_000.0
    assert cost.tolist() == pytest.approx([0.0, 0.0, per_switch, 0.0, per_switch, per_switch])
    assert per_switch == pytest.approx(0.0004)
    assert np.all(switch_cost_series(state, one_way_bp=0.0, points=0.20) == 0.0)


# --------------------------------------------------------------------------- #
# Two-period fixture: on then off, by hand
# --------------------------------------------------------------------------- #


def test_conditioned_arm_two_period_fixture(specification: Specification) -> None:
    """Month 1 on (50/30/20), month 2 off (70/30/0), spreads off, then the switch cost."""
    wrappers = read_wrappers(specification)
    rates = read_rates(specification)
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
    targets = np.array([[0.50, 0.30, 0.20], [0.70, 0.30, 0.0]])
    path = simulate_arm(
        panel,
        wrappers,
        rates,
        costs,
        tickers=("CORE", "RSST_LIKE", "RSSB_LIKE"),
        targets=targets,
    )

    def per_dollar(t: int) -> dict[str, float]:
        core = equity[t] - 3.0 / 120_000.0
        rsst = 1.072 * equity[t] + trend[t] - (99.0 + 0.331 * 62.0) / 120_000.0
        rssb = equity[t] + treasury[t] - (39.0 + 0.10 * 62.0 + 1.0 * 15.0) / 120_000.0
        return {"CORE": core, "RSST_LIKE": rsst, "RSSB_LIKE": rssb}

    legs0, legs1 = per_dollar(0), per_dollar(1)
    expected = [
        cash[0] + 0.50 * legs0["CORE"] + 0.30 * legs0["RSST_LIKE"] + 0.20 * legs0["RSSB_LIKE"],
        cash[1] + 0.70 * legs1["CORE"] + 0.30 * legs1["RSST_LIKE"],
    ]
    assert path.total == pytest.approx(np.asarray(expected), abs=1e-12)
    switch = switch_cost_series(np.array([1.0, 0.0]), one_way_bp=10.0, points=0.20)
    net = path.total - switch
    assert net[0] == pytest.approx(expected[0], abs=1e-12)
    assert net[1] == pytest.approx(expected[1] - 0.0004, abs=1e-12)


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def test_window_gap_matches_the_formulas() -> None:
    rng = np.random.default_rng(3)
    arm = rng.normal(0.006, 0.04, 240)
    bench = rng.normal(0.005, 0.04, 240)
    indices = stationary_bootstrap_indices(240, 12.0, 500, rng)
    gap = window_gap(arm, bench, window="full", bootstrap=indices)
    d = arm - bench
    assert gap.months == 240
    assert gap.gap_pp_yr == pytest.approx(float(np.mean(d)) * 1200.0)
    assert gap.mde_pp_yr == pytest.approx(
        MDE_MULTIPLIER * float(np.std(d, ddof=1)) / math.sqrt(240) * 1200.0
    )
    assert gap.tracking_error_pct == pytest.approx(float(np.std(d, ddof=1)) * math.sqrt(12) * 100.0)
    assert gap.hac_interval[0] <= gap.gap_pp_yr <= gap.hac_interval[1]
    assert gap.hac_interval[1] - gap.hac_interval[0] == pytest.approx(
        2 * 1.959964 * gap.hac_se_pp_yr
    )
    assert gap.log_growth_gap_pp_yr == pytest.approx(
        (float(np.mean(np.log1p(arm))) - float(np.mean(np.log1p(bench)))) * 1200.0
    )
    assert gap.bootstrap_interval is not None
    assert gap.bootstrap_interval[0] <= gap.gap_pp_yr <= gap.bootstrap_interval[1]
    # A sub-window selects only its months.
    keep = np.arange(100, 160, dtype=np.intp)
    sub = window_gap(arm, bench, window="sub", indices=keep)
    assert sub.months == 60
    assert sub.gap_pp_yr == pytest.approx(float(np.mean(d[100:160])) * 1200.0)


def test_complement_window_removes_the_bull_market_and_nothing_else(
    specification: Specification,
) -> None:
    periods = tuple(f"{1975 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(12 * 50))
    full = window_indices(periods, FULL_WINDOW, specification)
    assert full.size == len(periods)
    complement = window_indices(periods, COMPLEMENT_WINDOW, specification)
    bull = window_indices(periods, "bond_bull_market", specification)
    assert set(complement.tolist()) | set(bull.tolist()) == set(full.tolist())
    assert not set(complement.tolist()) & set(bull.tolist())
    # 1981-10 is the first bull month: 6 years and 9 months after 1975-01.
    assert periods[int(bull[0])] == "1981-10"
    assert periods[int(bull[-1])] == "2020-07"
    assert periods[int(complement[81])] == "2020-08"


def test_falsifier_clauses_fire_in_order() -> None:
    def gap(value: float, mde: float) -> WindowGap:
        return WindowGap(
            window="full",
            months=120,
            gap_pp_yr=value,
            hac_se_pp_yr=0.5,
            hac_interval=(value - 1.0, value + 1.0),
            hac_p=0.01,
            hac_lags=3,
            mde_pp_yr=mde,
            years_to_distinguish=10.0,
            tracking_error_pct=2.0,
            log_growth_gap_pp_yr=value,
        )

    negative = gap(-0.5, 1.0)
    _apply_falsifier(negative, q=0.10)
    assert negative.status == "rejected"
    inside = gap(0.5, 1.0)
    _apply_falsifier(inside, q=0.10)
    assert inside.status == "unresolved" and inside.clause.startswith("(b)")
    adjusted = gap(2.0, 1.0)
    adjusted.adjusted_p = 0.5
    _apply_falsifier(adjusted, q=0.10)
    assert adjusted.clause.startswith("(c)")
    band = gap(2.0, 1.0)
    band.adjusted_p = 0.01
    band.band_range = (-0.1, 2.0)
    _apply_falsifier(band, q=0.10)
    assert band.clause.startswith("(d)")
    survives = gap(2.0, 1.0)
    survives.adjusted_p = 0.01
    survives.band_range = (1.0, 2.0)
    _apply_falsifier(survives, q=0.10)
    assert survives.status == "exploratory"


def test_regret_gap_by_hand() -> None:
    """20 points at a 1.0 pp premium, 11.44 bp cost, rho -0.15, always on, no switching."""
    sigma_b, sigma_p, rho = 0.085, 0.19, -0.15
    variance = (0.04 * sigma_b**2 + 2.0 * 0.20 * rho * sigma_p * sigma_b) / 2.0
    expected = 0.20 * 1.0 - 0.1144 - variance * 100.0
    got = regret_gap_pp_yr(
        points=0.20,
        term_premium_pp_yr=1.0,
        certain_cost_pp_yr=0.1144,
        fraction_on=1.0,
        rho=rho,
        sigma_bond=sigma_b,
        sigma_portfolio=sigma_p,
        switching_cost_pp_yr=0.0,
    )
    assert got == pytest.approx(expected)
    assert variance < 0.0  # a negative correlation is a gain
    # Half the time on, with a switching cost, is half the gap less the cost.
    half = regret_gap_pp_yr(
        points=0.20,
        term_premium_pp_yr=1.0,
        certain_cost_pp_yr=0.1144,
        fraction_on=0.5,
        rho=rho,
        sigma_bond=sigma_b,
        sigma_portfolio=sigma_p,
        switching_cost_pp_yr=0.01,
    )
    assert half == pytest.approx(0.5 * expected - 0.01)


# --------------------------------------------------------------------------- #
# The whole experiment on a short synthetic history
# --------------------------------------------------------------------------- #


def _synthetic_raw_series() -> module.RawSeries:
    """216 months from 1975-01: the complement (to 1981-09) and the bull market both exist."""
    rng = np.random.default_rng(20260902)
    months = [f"{1975 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(216)]
    equity = rng.normal(0.006, 0.045, 216)
    # A bond leg whose correlation with equity flips sign half way, so both states occur.
    noise = rng.normal(0.0, 0.02, 216)
    sign = np.where(np.arange(216) < 108, 0.4, -0.4)
    bond = 0.002 + sign * equity + noise
    cash = np.full(216, 0.003)

    def series(values: NDArray[np.float64]) -> dict[str, float]:
        return {m: float(v) for m, v in zip(months, values, strict=True)}

    return module.RawSeries(
        equity=series(equity),
        cash=series(cash),
        ltr=series(bond + cash),
        corpr=series(bond + cash + rng.normal(0.0005, 0.01, 216)),
        gw_rfree=series(cash),
        commodity=series(rng.normal(0.002, 0.05, 216)),
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

    rules, primary, _, _, _ = read_rules(specification)
    arms = result.diagnostics["arms"]
    assert isinstance(arms, Sequence)
    by_name = {str(a["arm"]): a for a in arms if isinstance(a, Mapping)}
    assert set(by_name) == set(rules) | {"base_trend30", "trend30_bondstack20"}
    for name, row in by_name.items():
        assert {"gross", "equity", "trend", "bond", "gold", "cash"} <= set(
            row["notional_on"]  # type: ignore[arg-type]
        )
        assert row["max_drawdown_pct"] is not None
        assert isinstance(row["episodes"], Mapping)
        gaps = row["gaps"]
        assert isinstance(gaps, Mapping)
        for control, by_window in gaps.items():
            assert isinstance(by_window, Mapping)
            for window, cell in by_window.items():
                assert isinstance(cell, Mapping)
                # A gap never appears without its floor, its interval or its status.
                assert cell["gap_pp_yr"] is not None, (name, control, window)
                assert cell["mde_80pc_power_pp_yr"] is not None
                assert cell["hac_interval_pp_yr"] is not None
                assert cell["log_growth_gap_pp_yr"] is not None
                if name in rules:
                    assert cell["fraction_on"] is not None
                    assert cell["switches"] is not None
                if (
                    name in rules
                    and control in {"reference", "unconditional_stack"}
                    and window
                    in {
                        FULL_WINDOW,
                        COMPLEMENT_WINDOW,
                    }
                ):
                    assert cell["status"] in {"exploratory", "unresolved", "rejected"}
                    assert cell["bootstrap_interval_pp_yr"] is not None
                    assert cell["band_gap_range_pp_yr"] is not None
                else:
                    assert cell["status"] == "reported"
        if name in rules:
            assert isinstance(row["on_spells"], Sequence)
            assert isinstance(row["bond_regime_by_window"], Mapping)
    # The primary arm is scored on the full window and the complement exists on this history.
    primary_gaps = by_name[primary]["gaps"]
    assert isinstance(primary_gaps, Mapping)
    reference_gaps = primary_gaps["reference"]
    assert isinstance(reference_gaps, Mapping)
    assert FULL_WINDOW in reference_gaps and COMPLEMENT_WINDOW in reference_gaps
    # The synthetic bond leg flips from positive to negative correlation at month 108:
    # the 36-month rule must be off early and on late.
    primary_row = by_name[primary]
    assert isinstance(primary_row["fraction_on"], float)
    assert 0.0 < float(primary_row["fraction_on"]) < 1.0
    assert int(str(primary_row["switches"])) >= 1

    gap_names = {e.name for e in result.estimates if e.name.startswith("arithmetic_gap[")}
    floor_names = {
        e.name.replace("minimum_detectable_effect[", "arithmetic_gap[")
        for e in result.estimates
        if e.name.startswith("minimum_detectable_effect[")
    }
    assert gap_names and gap_names == floor_names
    deflation = result.diagnostics["deflation"]
    assert isinstance(deflation, Mapping)
    assert 1.0 <= float(str(deflation["effective_number_of_trials"])) <= 4.0
    regret = result.diagnostics["regret"]
    assert isinstance(regret, Mapping)
    assert str(regret["minimax_action"]) in {"conditioned", "unconditional", "neither"}
    cells = regret["cells"]
    assert isinstance(cells, Sequence) and len(cells) == 10
    assert "2003" in str(result.diagnostics["tips_before_2003"])
    tables = result.diagnostics["markdown_tables"]
    assert isinstance(tables, str)
    for name in rules:
        assert f"`{name}`" in tables
    assert len(ledger.read()) >= 2
