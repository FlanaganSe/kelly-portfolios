"""Unit tests for Experiment 021, leveraged ETFs and the 200-day moving average.

Every expected value here is computed in this file by hand or with plain NumPy,
never by calling the code under test on the same inputs.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest

import portfolio_edge.experiments.exp_021_leveraged_etf_rules as module
from portfolio_edge.experiments.exp_021_leveraged_etf_rules import (
    DAYS_PER_YEAR,
    Comparison,
    GapStatistics,
    LeveragedEtfRulesError,
    apply_falsifier,
    calendar_day_gaps,
    compound_monthly,
    default_specification_path,
    describe,
    episode_summary,
    exposure_matched_returns,
    gap_statistics,
    levered_fund_returns,
    moving_average_signal,
    positions_from_signal,
    read_arms,
    read_costs,
    read_rule,
    rebalanced_mix,
    round_trip_count,
    rule_returns,
    total_return_levels,
)
from portfolio_edge.experiments.specification import Specification, load_specification

SPEC_PATH = default_specification_path()


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(SPEC_PATH)


# --------------------------------------------------------------------------- #
# Daily-reset compounding, by hand
# --------------------------------------------------------------------------- #


def test_daily_reset_three_times_compounds_below_three_times_the_index() -> None:
    """+10%, -10%, +5% at 3x: 1.3 * 0.7 * 1.15 = 1.0465, against 3 * (1.1 * 0.9 * 1.05 - 1)."""
    market = np.array([0.10, -0.10, 0.05])
    cash = np.zeros(3)
    fund = levered_fund_returns(market, cash, [1, 1, 1], leverage=3.0, fee_bp=0.0, spread_bp=0.0)
    assert fund.tolist() == pytest.approx([0.30, -0.30, 0.15])
    reset = float(np.prod(1.0 + fund)) - 1.0
    assert reset == pytest.approx(1.3 * 0.7 * 1.15 - 1.0)
    unreset = 3.0 * (1.1 * 0.9 * 1.05 - 1.0)
    assert reset == pytest.approx(0.0465) and unreset == pytest.approx(0.1185)
    assert reset < unreset  # the volatility drag of daily reset, from compounding alone


def test_fee_and_spread_accrue_per_calendar_day_on_the_borrowed_notional() -> None:
    market = np.array([0.01, 0.00, -0.02])
    cash = np.array([0.0001, 0.0001, 0.0001])
    gaps = [1, 1, 3]  # the third row follows a weekend
    fund = levered_fund_returns(market, cash, gaps, leverage=2.0, fee_bp=100.0, spread_bp=50.0)
    charge = (1.0 * 50.0 + 100.0) / 10_000.0 / DAYS_PER_YEAR
    expected = [
        0.0001 + 0.02 - charge,
        0.0001 + 0.00 - charge,
        0.0001 - 0.04 - 3.0 * charge,
    ]
    assert fund.tolist() == pytest.approx(expected, abs=1e-15)
    # An unlevered fund borrows nothing and pays only its fee.
    index = levered_fund_returns(market, cash, gaps, leverage=1.0, fee_bp=3.0, spread_bp=50.0)
    assert index[0] == pytest.approx(0.0001 + 0.01 - 3.0 / 10_000.0 / DAYS_PER_YEAR)


def test_calendar_day_gaps_count_the_weekend() -> None:
    gaps = calendar_day_gaps(["2024-01-05", "2024-01-08", "2024-01-09"])
    assert gaps.tolist() == [1, 3, 1]
    with pytest.raises(LeveragedEtfRulesError, match="strictly increasing"):
        calendar_day_gaps(["2024-01-05", "2024-01-05"])


def test_total_return_levels_and_the_price_proxy() -> None:
    market = np.array([0.01, 0.02])
    cash = np.array([0.001, 0.001])
    levels = total_return_levels(market, cash)
    assert levels.tolist() == pytest.approx([1.011, 1.011 * 1.021])
    proxy = total_return_levels(market, cash, day_gaps=[1, 1], dividend_yield=0.025)
    daily = 0.025 / DAYS_PER_YEAR
    assert proxy.tolist() == pytest.approx([1.011 - daily, (1.011 - daily) * (1.021 - daily)])
    assert proxy[-1] < levels[-1]


# --------------------------------------------------------------------------- #
# The signal, by hand
# --------------------------------------------------------------------------- #


def test_moving_average_signal_without_a_band() -> None:
    levels = [1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0]
    signal = moving_average_signal(levels, window=3)
    # i=2: avg 2, 3 > 2 -> 1; i=3: avg 2.333, 2 < -> 0; i=4: avg 2, 1 -> 0;
    # i=5: avg 1.667, 2 -> 1; i=6: avg 2, 3 -> 1.
    assert np.isnan(signal[:2]).all()
    assert signal[2:].tolist() == [1.0, 0.0, 0.0, 1.0, 1.0]


def test_moving_average_signal_with_a_band_is_a_hysteresis() -> None:
    levels = [1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0]
    signal = moving_average_signal(levels, window=3, band=0.2)
    # i=2 first formed, plain comparison -> 1; i=3: 2 is not below 2.333*0.8=1.867 -> stays 1;
    # i=4: 1 < 2*0.8 -> 0; i=5: 2 is not above 1.667*1.2=2.0 -> stays 0; i=6: 3 > 2.4 -> 1.
    assert signal[2:].tolist() == [1.0, 1.0, 0.0, 0.0, 1.0]
    with pytest.raises(LeveragedEtfRulesError, match="window"):
        moving_average_signal(levels, window=1)


def test_positions_lag_the_signal_and_cannot_see_the_return_they_earn() -> None:
    signal = np.array([np.nan, np.nan, 1.0, 0.0, 1.0, 1.0])
    lag0 = positions_from_signal(signal, lag=0)
    lag1 = positions_from_signal(signal, lag=1)
    assert np.isnan(lag0[:3]).all() and lag0[3:].tolist() == [1.0, 0.0, 1.0]
    assert np.isnan(lag1[:4]).all() and lag1[4:].tolist() == [1.0, 0.0]
    # Perturbing a later close cannot move an earlier position.
    levels = np.cumprod(1.0 + np.full(400, 0.001))
    before = positions_from_signal(moving_average_signal(levels, window=200), lag=1)
    levels[350] *= 0.5
    after = positions_from_signal(moving_average_signal(levels, window=200), lag=1)
    assert np.array_equal(before[:352], after[:352], equal_nan=True)
    assert not np.array_equal(before, after, equal_nan=True)


# --------------------------------------------------------------------------- #
# Rule accounting, by hand
# --------------------------------------------------------------------------- #


def test_rule_returns_charge_each_switch_and_not_the_first_entry() -> None:
    fund = np.array([0.02, -0.01, 0.03, 0.01])
    cash = np.full(4, 0.001)
    position = np.array([np.nan, 1.0, 0.0, 1.0])
    out = rule_returns(fund, cash, position, one_way_cost=0.001)
    assert math.isnan(out[0])
    assert out[1:].tolist() == pytest.approx([-0.01, 0.001 - 0.001, 0.01 - 0.001])


def test_exposure_matched_control_is_w_times_the_fund_plus_bills() -> None:
    fund = np.array([0.02, -0.01, 0.03, 0.01])
    cash = np.full(4, 0.001)
    position = np.array([np.nan, 1.0, 0.0, 1.0])
    control, w = exposure_matched_returns(fund, cash, position)
    assert w == pytest.approx(2.0 / 3.0)
    assert control[1:].tolist() == pytest.approx([w * r + (1.0 - w) * 0.001 for r in fund[1:]])
    assert round_trip_count(np.array([1.0, 1.0, 0.0, 0.0, 1.0, 0.0])) == 2


# --------------------------------------------------------------------------- #
# Monthly arithmetic for HFEA, by hand
# --------------------------------------------------------------------------- #


def test_compound_monthly_drops_a_month_with_a_nan_day() -> None:
    dates = ["2020-01-30", "2020-01-31", "2020-02-03", "2020-02-04", "2020-03-02"]
    returns = [0.01, 0.02, np.nan, 0.01, 0.05]
    months, values = compound_monthly(dates, returns)
    assert months == ("2020-01", "2020-02", "2020-03")
    assert values[0] == pytest.approx(1.01 * 1.02 - 1.0)
    assert math.isnan(values[1])
    assert values[2] == pytest.approx(0.05)


def test_rebalanced_mix_drifts_then_pays_the_cost_on_traded_notional() -> None:
    legs = np.array([[0.10, 0.0], [0.10, 0.0], [0.0, 0.0]])
    out = rebalanced_mix(legs, (0.5, 0.5), every=2, one_way_cost=0.01)
    # t0: 0.55 + 0.5 -> +5%. t1: no rebalance, 0.605 + 0.5 = 1.105 -> 0.055 / 1.05.
    # t2: rebalance 1.105 to 0.5525 each, traded 0.0525 + 0.0525, cost 0.00105.
    assert out[0] == pytest.approx(0.05)
    assert out[1] == pytest.approx(0.055 / 1.05)
    assert out[2] == pytest.approx(-0.00105 / 1.105)
    with pytest.raises(LeveragedEtfRulesError, match="sum to one"):
        rebalanced_mix(legs, (0.6, 0.5), every=2, one_way_cost=0.0)


# --------------------------------------------------------------------------- #
# Statistics and descriptives
# --------------------------------------------------------------------------- #


def test_gap_statistics_annualise_by_rows_per_year_and_floor_by_the_hac_error() -> None:
    rng = np.random.default_rng(0)
    difference = rng.normal(0.0002, 0.01, 3000)
    stats = gap_statistics(
        difference, rows_per_year=252.0, n_lags=0, rng=rng, block=21.0, resamples=400, chunk=100
    )
    assert stats.gap_pp_yr == pytest.approx(float(np.mean(difference)) * 252.0 * 100.0)
    # With zero lags the HAC error is sd / sqrt(T) on the 1/T divisor.
    se = float(np.sqrt(np.mean((difference - difference.mean()) ** 2) / 3000)) * 252.0 * 100.0
    assert stats.hac_standard_error_pp_yr == pytest.approx(se, rel=1e-9)
    assert stats.mde_pp_yr == pytest.approx(2.801585 * se, rel=1e-9)
    assert stats.hac_interval[0] < stats.gap_pp_yr < stats.hac_interval[1]
    assert stats.bootstrap_interval[0] < stats.gap_pp_yr < stats.bootstrap_interval[1]
    assert stats.rows == 3000 and stats.years == pytest.approx(3000 / 252.0)


def test_describe_on_a_constant_path() -> None:
    total = np.full(24, 0.01)
    cash = np.full(24, 0.002)
    position = np.array([1.0] * 12 + [0.0] * 6 + [1.0] * 6)
    d = describe(total, cash, years=2.0, position=position)
    assert d.cagr_pct == pytest.approx((1.01**12 - 1.0) * 100.0)
    assert d.arithmetic_mean_pct == pytest.approx(12.0)
    assert d.max_drawdown_pct == 0.0 and d.time_under_water_rows == 0
    assert d.time_in_market == pytest.approx(0.75)
    assert d.round_trips_per_year == pytest.approx(0.5)


def test_episode_summary_reports_coverage_and_peak_to_trough() -> None:
    labels = ["2020-02-18", "2020-02-19", "2020-02-20", "2020-02-21"]
    total = np.array([0.01, -0.10, -0.10, 0.50])
    out = episode_summary(labels, total, start="2020-02-19", end="2020-02-21")
    assert out["covered"] is True and out["partial"] is False and out["rows"] == 3
    assert out["cumulative_pct"] == pytest.approx((0.9 * 0.9 * 1.5 - 1.0) * 100.0, abs=0.01)
    assert out["peak_to_trough_pct"] == pytest.approx(-19.0, abs=0.01)
    assert episode_summary(labels, total, start="1929-09-03", end="1932-06-30") == {
        "covered": False
    }
    assert episode_summary(labels, total, start="2020-02-20", end="2020-03-23")["partial"] is True


def _stats(gap: float, mde: float, p: float = 0.5) -> GapStatistics:
    return GapStatistics(
        gap_pp_yr=gap,
        hac_standard_error_pp_yr=mde / 2.801585,
        hac_interval=(gap - 1.0, gap + 1.0),
        bootstrap_interval=(gap - 1.0, gap + 1.0),
        mde_pp_yr=mde,
        p_value=p,
        tracking_error_pct=10.0,
        rows=100,
        years=1.0,
        years_to_distinguish=1.0,
    )


def test_falsifier_clauses_fire_in_order() -> None:
    c = Comparison(control="cheap", definition="x", gap=_stats(-0.1, 1.0))
    apply_falsifier(c, q=0.10)
    assert c.status == "rejected" and c.clause.startswith("(a)")
    c = Comparison(control="cheap", definition="x", gap=_stats(0.5, 1.0))
    apply_falsifier(c, q=0.10)
    assert c.status == "unresolved" and c.clause.startswith("(b)")
    c = Comparison(control="cheap", definition="x", gap=_stats(2.0, 1.0), adjusted_p=0.2)
    apply_falsifier(c, q=0.10)
    assert c.status == "unresolved" and c.clause.startswith("(c)")
    c = Comparison(
        control="cheap",
        definition="x",
        gap=_stats(2.0, 1.0),
        adjusted_p=0.01,
        stress_gap_pp_yr=-0.5,
    )
    apply_falsifier(c, q=0.10)
    assert c.status == "unresolved" and c.clause.startswith("(d)")
    c = Comparison(
        control="cheap", definition="x", gap=_stats(2.0, 1.0), adjusted_p=0.01, stress_gap_pp_yr=0.5
    )
    apply_falsifier(c, q=0.10)
    assert c.status == "exploratory"
    c = Comparison(control="cheap", definition="x", gap=None, identical=True)
    apply_falsifier(c, q=0.10)
    assert c.status == "not-scored"


# --------------------------------------------------------------------------- #
# The specification says what the module reads
# --------------------------------------------------------------------------- #


def test_specification_costs_rule_and_arms(specification: Specification) -> None:
    costs = read_costs(specification)
    assert (costs.fee_2x_bp, costs.fee_3x_bp, costs.fee_index_bp) == (89.0, 89.0, 3.0)
    assert costs.fee_130_bp == pytest.approx(0.85 * 3.0 + 0.15 * 89.0)
    assert (costs.spread_bp, costs.stress_spread_bp) == (40.0, 80.0)
    assert costs.one_way_cost == pytest.approx(0.001)
    rule = read_rule(specification)
    assert (rule.lookback, rule.band, rule.lag, rule.lag_sensitivity) == (200, 0.01, 1, 0)
    arms = read_arms(specification)
    assert {a.construction for a in arms.values()} == {"buy_and_hold", "constant_130", "sma"}
    assert arms["sma200_3x"].leverage == 3.0 and arms["sma200_3x"].band == 0.0
    assert arms["sma200_3x_band"].band == 0.01
    assert arms["lev_130"].leverage == pytest.approx(1.3)


def test_specification_floor_arithmetic_was_computed_before_the_run(
    specification: Specification,
) -> None:
    """The pre-run floor per point of tracking error is 2.801585 / sqrt(years)."""
    parameters = specification.parameters
    assert isinstance(parameters, Mapping)
    mde = parameters["minimum_detectable_effect"]
    assert isinstance(mde, Mapping)
    assert mde["multiplier"] == 2.801585
    full = mde["floor_at_assumed_tracking_error_full"]
    modern = mde["floor_at_assumed_tracking_error_modern"]
    assert isinstance(full, Mapping) and isinstance(modern, Mapping)
    for table, years in ((full, 99.2), (modern, 35.7)):
        for tracking_error, floor in table.items():
            assert isinstance(floor, float)
            assert floor == pytest.approx(
                2.801585 * float(tracking_error) / math.sqrt(years), abs=0.02
            )
    assert "unresolved" in specification.hypothesis
    assert "EVERY MEAN GAP" in specification.hypothesis


# --------------------------------------------------------------------------- #
# The whole experiment on synthetic data
# --------------------------------------------------------------------------- #


def _synthetic_raw_series() -> module.RawSeries:
    rng = np.random.default_rng(20260902)
    days = np.arange(
        np.datetime64("1988-01-04"), np.datetime64("1996-01-01"), np.timedelta64(1, "D")
    )
    dates = tuple(str(d) for d in days if d.astype("datetime64[D]").item().weekday() < 5)
    n = len(dates)
    market = rng.standard_t(4, n) * 0.008 + 0.0004
    cash = np.full(n, 0.0002)
    months = sorted({d[:7] for d in dates})
    monthly_rf = {m: 0.0002 * 21 for m in months}
    ltr = {m: float(v) for m, v in zip(months, rng.normal(0.006, 0.025, len(months)), strict=True)}
    return module.RawSeries(
        dates=dates,
        market_excess=np.asarray(market, dtype=np.float64),
        cash=cash,
        monthly_rf=monthly_rf,
        ltr=ltr,
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

    windows = result.diagnostics["windows"]
    assert isinstance(windows, Sequence)
    by_id = {str(w["id"]): w for w in windows if isinstance(w, Mapping)}
    assert set(by_id) == {"full_daily", "modern_daily", "full_monthly", "modern_monthly"}
    arms = read_arms(specification)
    for window in by_id.values():
        rows = window["arms"]
        assert isinstance(rows, Mapping)
        for name, row in rows.items():
            assert isinstance(row, Mapping)
            if window["frequency"] == "daily":
                assert name in arms
            d = row["descriptives"]
            assert isinstance(d, Mapping)
            assert d["max_drawdown_pct"] is not None and d["cagr_pct"] is not None
            assert isinstance(row["episodes"], Mapping)
            comparisons = row["comparisons"]
            assert isinstance(comparisons, Mapping)
            for control, comparison in comparisons.items():
                assert isinstance(comparison, Mapping)
                if comparison["identical_construction"]:
                    assert comparison["status"] == "not-scored", (name, control)
                    continue
                # A gap never appears without its floor, its control, its stress case or
                # its status.
                assert comparison["gap_pp_yr"] is not None
                assert comparison["mde_80pc_power_pp_yr"] is not None
                assert comparison["stress_spread_gap_pp_yr"] is not None
                assert comparison["control_definition"]
                assert comparison["status"] in {"exploratory", "unresolved", "rejected"}
    # Buy-and-hold arms are their own exposure match; timed arms are scored against it.
    full = by_id["full_daily"]["arms"]
    assert isinstance(full, Mapping)
    hold = full["hold_3x"]
    timed = full["sma200_3x"]
    assert isinstance(hold, Mapping) and isinstance(timed, Mapping)
    hold_c, timed_c = hold["comparisons"], timed["comparisons"]
    assert isinstance(hold_c, Mapping) and isinstance(timed_c, Mapping)
    hold_match, timed_match = hold_c["exposure_matched"], timed_c["exposure_matched"]
    assert isinstance(hold_match, Mapping) and isinstance(timed_match, Mapping)
    assert hold_match["identical_construction"] is True
    assert timed_match["identical_construction"] is False
    deflation = result.diagnostics["deflation"]
    assert isinstance(deflation, Mapping)
    dropped = deflation["rules_dropped_for_no_timing_content"]
    assert isinstance(dropped, Sequence)
    assert int(str(deflation["rules"])) + len(dropped) == 28
    candidates = deflation["candidates"]
    assert isinstance(candidates, Mapping) and "sma200_3x_band0" in candidates
    tax = result.diagnostics["after_tax"]
    assert isinstance(tax, Mapping)
    rows_tax = tax["rows"]
    assert isinstance(rows_tax, Mapping)
    assert "sma200_3x|top|step_up" in rows_tax
    entry = rows_tax["sma200_3x|top|step_up"]
    assert isinstance(entry, Mapping) and "tax_cost_of_the_arm_pp_yr" in entry
    assert (tmp_path / "artifacts" / outcome.run_id / "summary.md").is_file()
