"""Independent fixtures for carry calibration, funding and path diagnostics."""

from dataclasses import replace

import numpy as np
import pytest

from portfolio_edge.experiments import exp_019_carry_engine as base
from portfolio_edge.experiments.exp_016_construction_tournament import BasisPanel
from portfolio_edge.experiments.exp_027_selective_carry import (
    calibrate_carry,
    costed_carry,
    default_specification_path,
    paired_metrics,
    read_panels,
    rolling_underperformance,
)
from portfolio_edge.experiments.specification import load_specification


def calibration_fixture() -> dict[str, dict[str, float]]:
    periods = ["2020-01", "2020-02", "2020-03", "2020-04", "2020-05"]
    return {
        "a": dict(zip(periods, [-0.01, 0.01, -0.01, 0.01, 0.1], strict=True)),
        "b": dict(zip(periods, [-0.02, 0.02, -0.02, 0.02, 0.2], strict=True)),
    }


def fit(series: dict[str, dict[str, float]]) -> tuple[dict[str, float], dict[str, float]]:
    return calibrate_carry(
        series, ["a", "b"], start="2020-01", end="2020-04", months=4, target_volatility=0.12
    )


def test_calibration_independent_fixture_units_and_no_future_leakage() -> None:
    # Sample annual vol .04/.08; perfectly correlated legs; target .12.
    series = calibration_fixture()
    values, coefficients = fit(series)
    assert coefficients == pytest.approx({"a": 1.5, "b": 0.75})
    assert values["2020-01"] == pytest.approx(-0.03)
    assert values["2020-05"] == pytest.approx(0.3)
    series["a"]["2020-05"] = -100.0
    assert fit(series)[1] == coefficients


def test_missing_evaluation_month_is_not_zero_filled() -> None:
    series = calibration_fixture()
    del series["a"]["2020-05"]
    assert "2020-05" not in fit(series)[0]


@pytest.mark.parametrize("defect", ["missing", "zero", "nan"])
def test_bad_calibration_rejected(defect: str) -> None:
    series = calibration_fixture()
    if defect == "missing":
        del series["a"]["2020-03"]
    elif defect == "zero":
        series["a"] = dict.fromkeys(series["a"], 0.0)
    else:
        series["a"]["2020-03"] = float("nan")
    with pytest.raises(ValueError):
        fit(series)


def test_cost_loading_order_and_annualisation() -> None:
    # 12% gross minus 2% cost at half loading = 5% per year.
    assert costed_carry({"x": 0.01}, loading=0.5, cost_pp_yr=2)["x"] * 1200 == pytest.approx(5)
    assert costed_carry({"x": 0.01}, loading=0, cost_pp_yr=2)["x"] == 0
    with pytest.raises(ValueError):
        costed_carry({"x": 0.01}, loading=1.1, cost_pp_yr=2)


def test_funding_and_cost_identities_independent_fixture() -> None:
    spec = load_specification(default_specification_path())
    wrappers, arms, rates = base.read_wrappers(spec), base.read_arms(spec), base.read_rates(spec)
    costs = replace(base._cost_settings(spec, rates), round_trip_spread={"us_equity": 0.0})
    panel = BasisPanel(
        periods=("2020-01",),
        cash=np.zeros(1),
        provenance=(),
        findings=(),
        series={
            "equity": np.array([0.06 / 12]),
            "trend": np.array([0.04 / 12]),
            "carry": np.array([0.12 / 12]),
        },
    )
    paths = {
        name: base.simulate_arm(
            panel, wrappers, rates, costs, tickers=arm.tickers, targets=np.array(arm.weights)
        )
        for name, arm in arms.items()
    }
    reference = paths["base_trend30"].total[0]
    expected = {"stack10": 0.010885, "sell_equity10": 0.00518, "replace_trend15": 0.012}
    for name, gap in expected.items():
        assert (paths[name].total[0] - reference) * 12 == pytest.approx(gap, abs=1e-12)
    notionals = {
        name: base.arm_notional(arm.tickers, arm.weights, wrappers) for name, arm in arms.items()
    }
    assert notionals["stack10"].equity == pytest.approx(1.0216)
    assert notionals["sell_equity10"].equity == pytest.approx(0.9216)
    assert notionals["replace_trend15"].equity == pytest.approx(1.0216)
    assert notionals["replace_trend15"].trend == pytest.approx(0.15)


def test_rolling_wealth_is_relative_compounded_wealth() -> None:
    arm, control = np.array([0.1, -0.1, 0.1]), np.zeros(3)
    result = rolling_underperformance(arm, control, window=2)
    assert result["windows"] == 2
    assert result["frequency"] == 1
    assert result["worst_shortfall_pct"] == pytest.approx(-1.0)
    assert result["median_relative_wealth"] == pytest.approx(0.99)
    assert rolling_underperformance(arm, control)["frequency"] is None
    with pytest.raises(ValueError):
        rolling_underperformance(np.array([-1.0]), np.zeros(1))


def test_paired_log_growth_not_arithmetic_return() -> None:
    spec = load_specification(default_specification_path())
    arm = np.tile(np.array([0.1, -0.1]), 60)
    metrics = paired_metrics(arm, np.zeros(120), specification=spec, rng=np.random.default_rng(12))
    assert isinstance(metrics["arithmetic"], dict)
    assert isinstance(metrics["log_growth"], dict)
    assert metrics["arithmetic"]["gap_pp_yr"] == pytest.approx(0.0)
    assert metrics["log_growth"]["gap_pp_yr"] == pytest.approx(600 * np.log(0.99))


def test_selective_panel_sources_and_common_start() -> None:
    spec = load_specification(default_specification_path())
    panels = read_panels(spec)
    assert len(panels) == 27
    assert len({p.carry_source for p in panels}) == 9
    assert all(p.start is not None and p.start > "1973-12" for p in panels)
    assert {p.trend_source for p in panels} == {"own_4_asset_book", "aqr_tsmom"}
