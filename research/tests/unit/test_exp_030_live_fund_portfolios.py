"""Independent financing fixtures and the frozen live-portfolio construction contract."""

from pathlib import Path

import numpy as np
import pytest

from portfolio_edge.experiments.exp_030_live_fund_portfolios import (
    comparison,
    complete_panel,
    execute,
    mapping,
    metrics,
    month_grid,
    numbers,
    substitutions,
)
from portfolio_edge.experiments.specification import load_specification


def test_initial_buy_pays_half_roundtrip_without_unfinanced_cash() -> None:
    result = execute(np.zeros((1, 12, 1)), np.ones(1), roundtrip_bp=5)
    expected_wealth = 1 / 1.00025
    assert result.wealth[0, -1] == pytest.approx(expected_wealth, abs=1e-15)
    assert result.costs[0, 0] == pytest.approx(0.00025 / 1.00025, abs=1e-15)
    assert result.turnover[0, 0] == pytest.approx(expected_wealth)
    assert result.costs[0, 1:].sum() == 0
    measured = metrics(result)
    assert measured["arithmetic_pp_yr"] == pytest.approx(100 * (expected_wealth - 1))
    assert measured["max_drawdown_percent"] == pytest.approx(100 * (expected_wealth - 1))


def test_buyhold_drift_and_anniversary_rebalance_have_independent_wealth_fixtures() -> None:
    panel = np.zeros((1, 14, 2))
    panel[0, 0, 0] = 1  # first asset doubles: held weights become 2/3 and 1/3
    panel[0, 13, 0] = 1
    target = np.array([0.5, 0.5])
    annual = execute(panel, target, roundtrip_bp=100, rebalance_every=12)
    buyhold = execute(panel, target, roundtrip_bp=100, rebalance_every=120)
    initial = 1 / 1.005
    rebalance = 1 - 0.005 / 3  # total buy+sell dollars are exactly one third of capital
    assert annual.turnover[0, 12] == pytest.approx(1 / 3, abs=1e-14)
    assert annual.costs[0, 12] == pytest.approx(0.005 / 3, abs=1e-14)
    assert annual.wealth[0, -1] == pytest.approx(initial * 1.5 * rebalance * 1.5)
    assert buyhold.wealth[0, -1] == pytest.approx(initial * 2.5)
    assert annual.costs[0, 1:12].sum() == 0
    assert annual.turnover[0, 13] == 0


def test_return_units_are_decimal_and_weights_cannot_be_percentages() -> None:
    panel = np.full((1, 12, 1), 0.01)
    result = execute(panel, np.ones(1), roundtrip_bp=0)
    measured = metrics(result)
    assert measured["terminal_wealth"] == pytest.approx(1.01**12)
    assert measured["arithmetic_pp_yr"] == pytest.approx(12)
    assert measured["cagr_percent"] == pytest.approx(100 * (1.01**12 - 1))
    with pytest.raises(ValueError, match="sum to one"):
        execute(panel, np.array([100.0]), roundtrip_bp=0)


def test_missing_months_are_not_dropped_or_filled() -> None:
    months = month_grid("2023-12", "2024-02")
    assert months == ("2023-12", "2024-01", "2024-02")
    with pytest.raises(ValueError, match="A:2024-01"):
        complete_panel({"A": {"2023-12": 0.1, "2024-02": 0.2}}, ["A"], months)
    with pytest.raises(ValueError, match="month outside"):
        month_grid("2024-13", "2025-01")
    with pytest.raises(ValueError, match="reversed"):
        month_grid("2025-01", "2024-01")


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_invalid_nav_simple_returns_fail(bad: float) -> None:
    with pytest.raises(ValueError, match="returns"):
        execute(np.full((1, 12, 1), bad), np.ones(1), roundtrip_bp=5)


def test_paired_metrics_compare_complete_wealth_and_keep_realised_windows() -> None:
    arm = execute(np.full((1, 24, 1), 0.01), np.ones(1), roundtrip_bp=5)
    control = execute(np.zeros((1, 24, 1)), np.ones(1), roundtrip_bp=5)
    measured = comparison(arm, control)
    assert measured["terminal_wealth_ratio"] == pytest.approx(1.01**24)
    assert measured["log_gap_pp_yr"] == pytest.approx(1200 * np.log1p(0.01))
    assert measured["rolling_12m_underperformance_fraction"] == 0
    assert measured["rolling_12m_windows"] == 13
    assert measured["rolling_12m_worst_wealth_ratio"] == pytest.approx(1.01**12)


def test_frozen_weights_match_independent_published_snapshot_and_funding() -> None:
    spec = load_specification(Path("experiments/exp_030_live_fund_portfolios.yaml"))
    parameters = mapping(spec.parameters)
    assert len(str(parameters["portfolio_source_sha256"])) == 64
    # Transcribed independently from the site snapshot, in percent rather than decimals.
    expected: dict[str, dict[str, float]] = {
        "value-lean": {"VTI": 49, "VXUS": 16, "VTV": 15, "AVDV": 10, "IDMO": 5, "AVES": 5},
        "with-trend": {
            "RSST": 25,
            "VTI": 19,
            "VXUS": 16,
            "VTV": 15,
            "AVDV": 10,
            "IDMO": 5,
            "AVES": 5,
            "SCHP": 5,
        },
        "cautious": {
            "SCHP": 50,
            "RSST": 15,
            "VTI": 9.5,
            "VXUS": 8,
            "VTV": 7.5,
            "AVDV": 5,
            "IDMO": 2.5,
            "AVES": 2.5,
        },
    }
    for name, raw in mapping(parameters["portfolios"]).items():
        definition = mapping(raw)
        base = numbers(definition["weights"])
        assert base == pytest.approx(
            {ticker: weight / 100 for ticker, weight in expected[name].items()}
        )
        momentum = 0.025 if name == "cautious" else 0.05
        arms = substitutions(base, momentum)
        for weights in arms.values():
            assert sum(weights.values()) == pytest.approx(1)
            assert all(weight >= 0 for weight in weights.values())
        assert "VTV" not in arms["avuv"]
        assert arms["avuv"]["AVUV"] == base["VTV"]
        assert arms["spmo"]["SPMO"] == momentum
        assert arms["spmo"]["VTI"] == pytest.approx(base["VTI"] - momentum)
        assert arms["both"]["AVUV"] == base["VTV"]
        assert arms["both"]["SPMO"] == momentum


def test_substitution_cannot_use_unfunded_capital() -> None:
    with pytest.raises(ValueError, match="funded"):
        substitutions({"VTI": 0.02, "VTV": 0.98}, 0.05)
