"""Funding, scheduled harvesting and partial-episode contracts independent of returns."""

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments.exp_030_live_fund_portfolios import execute, mapping, month_grid
from portfolio_edge.experiments.exp_035_funded_crash_hedges import episodes, funded_arms
from portfolio_edge.experiments.specification import load_specification


def test_proportional_funding_preserves_stock_split_and_control_capital() -> None:
    arms = funded_arms({"VTI": 0.65, "VXUS": 0.35}, "proportional", ["TAIL", "CAOS"], 0.05)
    assert arms["TAIL"] == pytest.approx({"VTI": 0.6175, "VXUS": 0.3325, "TAIL": 0.05})
    assert arms["duration"] == pytest.approx(
        {"VTI": 0.6175, "VXUS": 0.3325, "IEF": 0.045, "BIL": 0.005}
    )
    assert all(sum(w.values()) == pytest.approx(1) for w in arms.values())


def test_bond_funding_does_not_sell_stocks_and_refuses_unfunded_sleeve() -> None:
    arms = funded_arms({"SCHP": 0.5, "RSST": 0.15, "VTI": 0.35}, "SCHP", ["TAIL"], 0.05)
    assert arms["TAIL"] == pytest.approx({"SCHP": 0.45, "RSST": 0.15, "VTI": 0.35, "TAIL": 0.05})
    with pytest.raises(ValueError, match="insufficient"):
        funded_arms({"SCHP": 0.01, "VTI": 0.99}, "SCHP", ["TAIL"], 0.05)


def test_quarterly_harvest_is_scheduled_and_self_financing() -> None:
    panel = np.zeros((1, 4, 2))
    panel[0, 0, 1] = 1
    panel[0, 3, 1] = -0.5
    quarterly = execute(panel, np.array([0.95, 0.05]), roundtrip_bp=0, rebalance_every=3)
    annual = execute(panel, np.array([0.95, 0.05]), roundtrip_bp=0, rebalance_every=12)
    assert quarterly.wealth[0, -1] == pytest.approx(1.05 * 0.975)
    assert annual.wealth[0, -1] == pytest.approx(1)
    assert quarterly.turnover[0, 1:3].sum() == 0


def test_partial_episodes_have_no_return_and_complete_ones_use_continuing_path() -> None:
    months = month_grid("2020-02", "2020-04")
    path = execute(np.full((1, 3, 1), 0.1), np.ones(1), roundtrip_bp=0)
    out = episodes(
        months, path, {"partial": ["2020-01", "2020-03"], "full": ["2020-03", "2020-04"]}
    )
    assert mapping(out["partial"])["complete"] is False
    assert "return_percent" not in mapping(out["partial"])
    assert mapping(out["full"])["return_percent"] == pytest.approx(21)


def test_frozen_windows_do_not_admit_caos_predecessor_or_partial_rsst_month() -> None:
    spec = load_specification(Path("experiments/exp_035_funded_crash_hedges.yaml"))
    portfolios = mapping(mapping(spec.parameters)["portfolios"])
    assert mapping(portfolios["tail_long"])["first"] == "2020-02"
    assert mapping(portfolios["current_etfs"])["first"] == "2023-04"
    assert mapping(portfolios["cautious"])["first"] == "2023-10"
