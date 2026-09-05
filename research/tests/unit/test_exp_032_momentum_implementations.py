"""Funded momentum alternatives and an independent drifting mixture fixture."""

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments.exp_030_live_fund_portfolios import execute, mapping, numbers
from portfolio_edge.experiments.exp_032_momentum_implementations import substitutions
from portfolio_edge.experiments.specification import load_specification


def test_frozen_windows_weights_and_equal_funding_match_030() -> None:
    original = load_specification(Path("experiments/exp_030_live_fund_portfolios.yaml"))
    spec = load_specification(Path("experiments/exp_032_momentum_implementations.yaml"))
    definitions = mapping(mapping(spec.parameters)["portfolios"])
    assert spec.inference == original.inference
    for name, raw in definitions.items():
        definition = mapping(raw)
        old = mapping(mapping(mapping(original.parameters)["portfolios"])[name])
        assert definition["weights"] == old["weights"]
        assert (definition["first"], definition["last"]) == (old["first"], old["last"])
        base = numbers(definition["weights"])
        capital = 0.025 if name == "cautious" else 0.05
        arms = substitutions(base, capital)
        for arm, weights in arms.items():
            assert sum(weights.values()) == pytest.approx(1)
            assert min(weights.values()) >= 0
            assert weights["VTV"] == base["VTV"]
            if arm != "unchanged":
                assert weights["VTI"] == pytest.approx(base["VTI"] - capital)
                assert weights.get("SPMO", 0) + weights.get("MTUM", 0) == capital
        assert arms["equal_mix"]["SPMO"] == capital / 2
        assert arms["equal_mix"]["MTUM"] == capital / 2


def test_mixture_holds_each_fund_and_drifts_instead_of_averaging_monthly_returns() -> None:
    # Start with 90 dollars VTI, 5 SPMO and 5 MTUM. SPMO doubles, then MTUM
    # halves: holdings end at 90,10,2.5. Initial purchase costs scale all holdings.
    panel = np.zeros((1, 12, 3))
    panel[0, 0, 1] = 1
    panel[0, 1, 2] = -0.5
    arms = substitutions({"VTI": 1.0}, 0.1)
    weights = np.array([arms["equal_mix"].get(t, 0) for t in ("VTI", "SPMO", "MTUM")])
    path = execute(panel, weights, roundtrip_bp=5)
    assert path.wealth[0, -1] == pytest.approx(1.025 / 1.00025)
    assert path.turnover[0, 1:].sum() == 0


@pytest.mark.parametrize("capital", [-0.1, 0, 1.1, float("nan"), float("inf")])
def test_unfunded_or_nonfinite_momentum_allocation_fails(capital: float) -> None:
    with pytest.raises(ValueError, match="funding"):
        substitutions({"VTI": 1}, capital)


def test_invalid_base_and_existing_momentum_fail() -> None:
    with pytest.raises(ValueError, match="base weights"):
        substitutions({"VTI": 1, "VTV": -0.1}, 0.05)
    with pytest.raises(ValueError, match="already hold"):
        substitutions({"VTI": 0.9, "SPMO": 0.1}, 0.05)
