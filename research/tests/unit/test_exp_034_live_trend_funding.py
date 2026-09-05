"""Independent capital conservation and trend funding fixtures."""

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments.exp_030_live_fund_portfolios import execute, mapping, numbers
from portfolio_edge.experiments.exp_034_live_trend_funding import intended_capital, substitutions
from portfolio_edge.experiments.specification import load_specification


def test_frozen_weights_and_funding_preserve_stated_capital_not_trend_risk() -> None:
    spec = load_specification(Path("experiments/exp_034_live_trend_funding.yaml"))
    original = load_specification(Path("experiments/exp_030_live_fund_portfolios.yaml"))
    definitions = mapping(mapping(spec.parameters)["portfolios"])
    old = mapping(mapping(original.parameters)["portfolios"])
    assert set(definitions) == {"with-trend", "cautious"}
    for name, raw in definitions.items():
        definition = mapping(raw)
        base = numbers(definition["weights"])
        assert base == numbers(mapping(old[name])["weights"])
        assert (definition["first"], definition["last"]) == ("2023-10", "2026-03")
        arms = substitutions(base)
        assert len(arms) == 9
        stacked = 0.25 if name == "with-trend" else 0.15
        budget = 0.05 if name == "with-trend" else 0.15
        stock = 0.95 if name == "with-trend" else 0.5
        for arm, weights in arms.items():
            assert sum(weights.values()) == pytest.approx(1)
            assert min(weights.values()) >= 0
            assert all(weights[t] == base[t] for t in ("VXUS", "VTV", "AVDV", "IDMO", "AVES"))
            capital = intended_capital(weights)
            if arm.startswith("direct"):
                assert capital["stock_capital"] == pytest.approx(stock - stacked)
                assert capital["schp_capital"] == base["SCHP"]
                assert capital["standalone_trend_capital"] == stacked
            else:
                assert capital["stock_capital"] == pytest.approx(stock)
            if arm.startswith("bond"):
                assert capital["schp_capital"] == pytest.approx(base["SCHP"] - budget)
        assert arms["bond_mix"]["DBMF"] == arms["bond_mix"]["KMLM"] == budget / 2
        assert arms["bond_cash"]["SGOV"] == budget
        assert "RSST" not in arms["no_trend"]
        assert arms["no_trend"]["VTI"] == base["VTI"] + stacked


def test_independent_mix_path_pays_initial_cost_and_drifts() -> None:
    # Initially $50 equity, $35 TIPS, $7.5 each trend fund after funding.
    # DBMF doubles and KMLM halves: total = 50+35+15+3.75 =103.75.
    weights = substitutions({"VTI": 0.35, "RSST": 0.15, "SCHP": 0.5})["bond_mix"]
    tickers = ["VTI", "SCHP", "DBMF", "KMLM"]
    panel = np.zeros((1, 12, 4))
    panel[0, 0, 2] = 1
    panel[0, 1, 3] = -0.5
    path = execute(panel, np.array([weights[t] for t in tickers]), roundtrip_bp=5)
    assert path.wealth[0, -1] == pytest.approx(1.0375 / 1.00025)
    assert path.turnover[0, 1:].sum() == 0


@pytest.mark.parametrize(
    "base",
    [
        {"VTI": 0.9, "RSST": 0.1},
        {"VTI": 0.9, "SCHP": 0.1},
        {"VTI": 0.5, "RSST": 0.1, "SCHP": 0.5},
        {"VTI": float("nan"), "RSST": 0.1, "SCHP": 0.5},
        {"VTI": 0.3, "RSST": 0.1, "SCHP": 0.5, "DBMF": 0.1},
    ],
)
def test_invalid_funding_fails_before_returns(base: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        substitutions(base)
