"""Independent arithmetic and conditioning checks for funded full portfolios."""

import numpy as np
import pytest

from portfolio_edge.experiments.exp_016_construction_tournament import (
    BasisPanel,
    CostSettings,
    FundMapping,
)
from portfolio_edge.experiments.exp_029_funded_fund_substitutions import (
    US_FUNDS,
    apply_costs,
    outcomes,
    scenario_panel,
    simulate,
    substituted_weights,
)


def mapping(ticker: str, beta: float) -> FundMapping:
    return FundMapping(
        ticker=ticker,
        coefficients={"us_mkt": beta},
        expense_ratio_bp=0,
        futures_notional=0,
        spread_region="us",
        alpha_less_pedestal_pp_yr=99,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=False,
    )


def panel() -> BasisPanel:
    return BasisPanel(
        periods=("2000-01", "2000-02", "2000-03"),
        series={"us_mkt": np.array([0.10, -0.20, 0.05]), "us_hml": np.array([-0.05, 0.10, 0.02])},
        cash=np.array([0.001, 0.001, 0.001]),
        provenance=(),
        findings=(),
    )


def test_substitution_conserves_capital_and_funding() -> None:
    weights = {"VTI": 9.5, "VTV": 7.5, "SCHP": 83}
    assert substituted_weights(weights, value=True, momentum_percent=2.5) == {
        "VTI": 7,
        "AVUV": 7.5,
        "SPMO": 2.5,
        "SCHP": 83,
    }
    assert weights == {"VTI": 9.5, "VTV": 7.5, "SCHP": 83}
    with pytest.raises(ValueError, match="funded"):
        substituted_weights(weights, value=False, momentum_percent=10)
    with pytest.raises(ValueError, match="sum"):
        substituted_weights({"VTI": 99}, value=False, momentum_percent=5)


def test_full_funded_path_retains_beta_drift_covariance_and_cash_once() -> None:
    p = panel()
    maps = {"VTI": mapping("VTI", 1), "SPMO": mapping("SPMO", 2)}
    costs = CostSettings(
        equity_futures_basis=0, trend_book_financing=0, round_trip_spread={"us": 0}
    )
    result = simulate(p, maps, costs, {"VTI": 50, "SPMO": 50})
    # Independently carry two initial half-dollar positions: annual rebalancing
    # does not rebalance this three-month path. Alpha=99 is deliberately ignored.
    vti = 0.5 * np.cumprod([1.101, 0.801, 1.051])
    spmo = 0.5 * np.cumprod([1.201, 0.601, 1.101])
    wealth = np.concatenate(([1.0], vti + spmo))
    np.testing.assert_allclose(result, wealth[1:] / wealth[:-1] - 1, atol=1e-14)
    assert result[0] == pytest.approx(0.151)


def test_scenario_means_preserve_all_covariances_and_dont_mutate() -> None:
    p = panel()
    shifted = scenario_panel(p, "null", market_pp=5, trend_pp=1)
    assert shifted.series["us_mkt"].mean() == pytest.approx(5 / 1200)
    assert shifted.series["us_hml"].mean() == pytest.approx(0, abs=1e-16)
    np.testing.assert_allclose(
        np.cov(list(p.series.values())), np.cov(list(shifted.series.values())), atol=1e-16
    )
    np.testing.assert_array_equal(p.cash, shifted.cash)
    np.testing.assert_array_equal(p.series["us_mkt"], [0.1, -0.2, 0.05])


def test_cost_units_and_no_intercept_credit() -> None:
    maps = {t: mapping(t, 1) for t in US_FUNDS}
    low, high = apply_costs(maps, 0), apply_costs(maps, 1.7)
    assert low["SPMO"].expense_ratio_bp == pytest.approx(12.929)
    assert high["SPMO"].expense_ratio_bp == pytest.approx(87.729)
    assert high["AVUV"].expense_ratio_bp == pytest.approx(34.739)
    assert maps["SPMO"].expense_ratio_bp == 0


def test_drawdown_includes_initial_capital_and_growth_units() -> None:
    result = outcomes(np.array([-0.2, 0.25]))
    assert result["max_drawdown_pct"] == pytest.approx(-20)
    assert result["cagr_pct"] == pytest.approx(0)
    assert result["log_growth_pp_yr"] == pytest.approx(0)
    with pytest.raises(ValueError, match="solvent"):
        outcomes(np.array([-1.0, 0.3]))
