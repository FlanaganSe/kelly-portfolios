"""Frozen funding choices and independent arithmetic for the allocation grid."""

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments.exp_030_live_fund_portfolios import (
    execute,
    mapping,
    month_grid,
    numbers,
)
from portfolio_edge.experiments.exp_031_live_equity_allocation_grid import (
    allocation_grid,
    paired_result,
    sequence,
)
from portfolio_edge.experiments.specification import load_specification


def test_fixed_grid_funding_has_independent_weights_and_untouched_other_assets() -> None:
    base = {"VTI": 0.49, "VTV": 0.15, "VXUS": 0.16, "AVDV": 0.1, "IDMO": 0.05, "AVES": 0.05}
    grid, excluded = allocation_grid(
        base,
        {"none": [0, 0], "add": [1, 1], "split": [0.5, 0.5]},
        momentum_step=0.05,
        momentum_multipliers=[0, 1, 2],
    )
    assert not excluded
    assert grid["none_m0"]["VTI"] == pytest.approx(0.64)
    assert grid["none_m2"]["VTI"] == pytest.approx(0.54)
    assert grid["add_m2"]["VTI"] == pytest.approx(0.24)
    assert grid["add_m2"]["VTV"] == grid["add_m2"]["AVUV"] == 0.15
    assert grid["add_m2"]["SPMO"] == 0.10
    assert grid["split_m0"]["VTV"] == grid["split_m0"]["AVUV"] == 0.075
    assert grid["split_m0"]["VTI"] == pytest.approx(0.49)
    for weights in grid.values():
        assert sum(weights.values()) == pytest.approx(1)
        for ticker in ("VXUS", "AVDV", "IDMO", "AVES"):
            assert weights[ticker] == base[ticker]
    assert base["VTI"] == 0.49  # no mutation of the reference portfolio


def test_infeasible_cautious_allocations_are_recorded_not_refunded_elsewhere() -> None:
    base = {"VTI": 0.095, "VTV": 0.075, "SCHP": 0.5, "RSST": 0.15, "VXUS": 0.18}
    grid, excluded = allocation_grid(
        base,
        {"add": [1, 1]},
        momentum_step=0.025,
        momentum_multipliers=[0, 1, 2],
    )
    assert list(grid) == ["add_m0"]
    assert grid["add_m0"]["VTI"] == pytest.approx(0.02)
    assert [row["arm"] for row in excluded] == ["add_m1", "add_m2"]
    assert excluded[0]["unfunded_weight"] == pytest.approx(0.005)
    assert excluded[1]["unfunded_weight"] == pytest.approx(0.03)
    assert grid["add_m0"]["SCHP"] == 0.5
    assert grid["add_m0"]["RSST"] == 0.15


def test_frozen_grid_size_baseline_and_calendar_halves() -> None:
    spec = load_specification(Path("experiments/exp_031_live_equity_allocation_grid.yaml"))
    p = mapping(spec.parameters)
    base_spec = load_specification(str(p["base_specification"]))
    base_p = mapping(base_spec.parameters)
    patterns = {
        name: [float(str(x)) for x in sequence(raw)]
        for name, raw in mapping(p["value_patterns"]).items()
    }
    for portfolio, raw in mapping(base_p["portfolios"]).items():
        definition = mapping(raw)
        base = numbers(definition["weights"])
        grid, excluded = allocation_grid(
            base,
            patterns,
            momentum_step=float(str(definition["spmo_weight"])),
            momentum_multipliers=[0, 1, 2],
        )
        assert len(grid) == (24 if portfolio == "value-lean" else 22)
        assert len(excluded) == (0 if portfolio == "value-lean" else 2)
        assert grid[str(p["baseline_arm"])] == pytest.approx(base)
        periods = {}
        for label, bounds in mapping(mapping(p["windows"])[portfolio]).items():
            ends = sequence(bounds)
            periods[label] = month_grid(str(ends[0]), str(ends[1]))
        assert periods["early"] + periods["late"] == periods["full"]
        assert (
            len(periods["early"])
            == len(periods["late"])
            == (27 if portfolio == "value-lean" else 15)
        )


def test_paired_growth_interval_uses_path_pairs_and_annual_percentage_points() -> None:
    arm = execute(np.full((4, 24, 1), 0.01), np.ones(1), roundtrip_bp=5)
    benchmark = execute(np.zeros((4, 24, 1)), np.ones(1), roundtrip_bp=5)
    result = paired_result(arm, benchmark)
    expected = 1200 * np.log1p(0.01)
    assert result["log_gap_pp_yr"] == pytest.approx(expected)
    assert result["interval_pp_yr"] == pytest.approx([expected, expected])
    assert result["resolution80_pp_yr"] == pytest.approx(0, abs=1e-12)
    assert result["terminal_wealth_ratio"] == pytest.approx(1.01**24)
    assert result["rolling_12m_underperformance_fraction"] == 0
    assert paired_result(arm, arm)["log_gap_pp_yr"] == 0


@pytest.mark.parametrize("pattern", [[-1, 0], [float("nan"), 1], [1]])
def test_invalid_value_patterns_fail_before_data_access(pattern: list[float]) -> None:
    with pytest.raises(ValueError, match="pattern"):
        allocation_grid(
            {"VTI": 0.85, "VTV": 0.15},
            {"bad": pattern},
            momentum_step=0.05,
            momentum_multipliers=[0],
        )
