"""Independent funding and observed-CPI purchasing-power fixtures."""

import math

import numpy as np
import pytest

from portfolio_edge.experiments.exp_033_cautious_defensive_budget import (
    defensive_weights,
    previous_month,
    real_outcomes,
)


def test_only_defensive_half_changes_and_no_trend_is_a_distinct_funded_portfolio() -> None:
    base = {
        "SCHP": 0.5,
        "RSST": 0.15,
        "VTI": 0.095,
        "VXUS": 0.08,
        "VTV": 0.075,
        "AVDV": 0.05,
        "IDMO": 0.025,
        "AVES": 0.025,
    }
    weights = defensive_weights(base, {"STIP": 0.5, "SGOV": 0.5})
    assert weights["STIP"] == weights["SGOV"] == 0.25
    assert "SCHP" not in weights
    for ticker in base:
        if ticker != "SCHP":
            assert weights[ticker] == base[ticker]
    diagnostic = defensive_weights(base, {"IEF": 1}, no_trend=True)
    assert "RSST" not in diagnostic
    assert diagnostic["VTI"] == pytest.approx(0.245)
    assert diagnostic["IEF"] == 0.5
    assert sum(weights.values()) == pytest.approx(1)
    assert sum(diagnostic.values()) == pytest.approx(1)
    assert base["VTI"] == 0.095
    with pytest.raises(ValueError, match="sum to one"):
        defensive_weights(base, {"STIP": 50, "SGOV": 50})


def test_real_growth_deflates_nav_once_and_uses_prior_month_initial_cpi() -> None:
    months = ("2024-01", "2024-02", "2024-03")
    cpi = {"2023-12": 100, "2024-01": 110, "2024-02": 110, "2024-03": 121}
    result = real_outcomes(np.array([1, 1.1, 0.55, 1.331]), months, cpi)
    assert result["initial_cpi_month"] == "2023-12"
    assert result["real_wealth_on_observed_dates"] == pytest.approx([1, 1, 0.5, 1.1])
    assert result["real_terminal_wealth"] == pytest.approx(1.1)
    assert result["real_log_growth_pp_yr"] == pytest.approx(400 * math.log(1.1))
    assert result["real_cagr_percent"] == pytest.approx(100 * (1.1**4 - 1))
    assert result["real_drawdown_observed_cpi_dates_percent"] == pytest.approx(-50)
    assert result["max_real_principal_shortfall_observed_percent"] == pytest.approx(50)
    assert result["terminal_real_principal_shortfall_percent"] == 0


def test_missing_interior_cpi_is_reported_never_interpolated_or_read_as_complete_risk() -> None:
    months = ("2024-01", "2024-02", "2024-03")
    result = real_outcomes(
        np.array([1, 1.1, 0.55, 1.21]), months, {"2023-12": 100, "2024-01": 110, "2024-03": 121}
    )
    assert result["missing_cpi_months"] == ["2024-02"]
    assert result["observed_cpi_months"] == ["2024-01", "2024-03"]
    assert result["real_wealth_on_observed_dates"] == pytest.approx([1, 1, 1])
    assert result["real_drawdown_observed_cpi_dates_percent"] == pytest.approx(0, abs=1e-12)
    # A missing CPI date can hide a loss: this zero is intentionally NOT full-month risk.
    assert result["max_real_principal_shortfall_observed_percent"] == pytest.approx(0, abs=1e-12)
    assert result["real_terminal_wealth"] == pytest.approx(1)


def test_cpi_endpoints_units_and_calendar_rollover_are_checked() -> None:
    assert previous_month("2024-01") == "2023-12"
    for cpi in ({"2024-01": 100}, {"2023-12": 100}):
        with pytest.raises(ValueError, match="endpoints"):
            real_outcomes(np.array([1, 1.1]), ["2024-01"], cpi)
    with pytest.raises(ValueError, match="positive finite index"):
        real_outcomes(np.array([1, 1.1]), ["2024-01"], {"2023-12": 100, "2024-01": 0})
    with pytest.raises(ValueError, match="start at one"):
        real_outcomes(np.array([100, 110]), ["2024-01"], {"2023-12": 100, "2024-01": 110})
