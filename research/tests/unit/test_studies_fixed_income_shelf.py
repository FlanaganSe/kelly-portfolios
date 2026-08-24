"""The fixed-income arithmetic, against fixtures computed independently of it.

The two that carry the most weight:

* :func:`test_par_bond_risk_matches_numerical_differentiation` differentiates the exact
  par-bond price function numerically at four yields, **including a negative one**, and
  requires the closed form back. This is the check the exp_004 copy of the same helper
  did not have: its unit test asserted the implementation's own output and so pinned a
  factor-of-two convexity error rather than catching it.
* :func:`test_par_bond_risk_agrees_with_the_exp_010_copy` holds this module's function
  against the frozen experiment's, so the two cannot drift where their domains overlap.

Nothing here is recorded from a run.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.experiments.exp_010_marginal_sleeve_value import (
    par_bond_risk as exp_010_par_bond_risk,
)
from portfolio_edge.studies.fixed_income_shelf import (
    FIXED_INCOME_SHELF,
    REF_CPI_LAG_MONTHS,
    annualised,
    correlation_stability,
    correlation_standard_error,
    months_between,
    par_bond_risk,
    par_bond_total_returns,
    tips_nominal_total_return,
)


def _par_bond_price(*, coupon_rate: float, yield_to_maturity: float, periods: float) -> float:
    """Exact price per 1 of face of a semiannual par-structure bond. Not the module's."""
    half_yield = yield_to_maturity / 2.0
    half_coupon = coupon_rate / 2.0
    count = int(periods)
    price = sum(half_coupon / (1.0 + half_yield) ** k for k in range(1, count + 1))
    return price + 1.0 / (1.0 + half_yield) ** count


@pytest.mark.parametrize("annual_yield", [0.04, 0.10, 0.0005, -0.0107])
def test_par_bond_risk_matches_numerical_differentiation(annual_yield: float) -> None:
    periods = 20.0
    step = 1e-6
    up = _par_bond_price(
        coupon_rate=annual_yield, yield_to_maturity=annual_yield + step, periods=periods
    )
    down = _par_bond_price(
        coupon_rate=annual_yield, yield_to_maturity=annual_yield - step, periods=periods
    )
    middle = _par_bond_price(
        coupon_rate=annual_yield, yield_to_maturity=annual_yield, periods=periods
    )
    numerical_modified = -(up - down) / (2.0 * step * middle)
    numerical_convexity = (up - 2.0 * middle + down) / (step**2 * middle)

    modified, convexity = par_bond_risk(annual_yield, periods=periods)
    assert modified == pytest.approx(numerical_modified, rel=1e-6)
    assert convexity == pytest.approx(numerical_convexity, rel=1e-4)


def test_par_bond_risk_at_zero_is_the_limit_not_a_division_by_zero() -> None:
    """A zero real yield is a par bond with no coupon: duration equals maturity."""
    modified, convexity = par_bond_risk(0.0, periods=20.0)
    assert modified == pytest.approx(10.0)
    assert convexity == pytest.approx(105.0)
    # Just outside the limit branch the closed form must agree with the limit. The
    # threshold sits four orders of magnitude below the 0.01% the Treasury quotes the
    # real curve to, so no real observation is ever inside it.
    approaching = par_bond_risk(4e-6, periods=20.0)
    assert approaching[0] == pytest.approx(modified, rel=1e-3)
    assert approaching[1] == pytest.approx(convexity, rel=1e-3)


@pytest.mark.parametrize("annual_yield", [0.02, 0.04, 0.08])
def test_par_bond_risk_agrees_with_the_exp_010_copy(annual_yield: float) -> None:
    assert par_bond_risk(annual_yield, periods=20.0) == pytest.approx(
        exp_010_par_bond_risk(annual_yield, periods=20.0)
    )


def test_par_bond_risk_refuses_a_yield_that_cannot_be_discounted() -> None:
    with pytest.raises(ValueError, match="discount factor"):
        par_bond_risk(-2.5, periods=20.0)


def test_par_bond_total_returns_skips_a_gap_rather_than_bridging_it() -> None:
    yields = {"2020-01": 0.02, "2020-02": 0.02, "2020-05": 0.02}
    returns = par_bond_total_returns(yields, maturity_years=10.0)
    assert sorted(returns) == ["2020-02"]
    # A flat yield earns exactly one month of coupon and no price change.
    assert returns["2020-02"] == pytest.approx(0.02 / 12.0)


def test_tips_nominal_total_return_applies_the_statutory_three_month_lag() -> None:
    """A CPI step must land three months later, which is the Ref CPI rule and not a guess."""
    prices = {
        "2019-11": 100.0,
        "2019-12": 100.0,
        "2020-01": 101.0,
        "2020-02": 101.0,
        "2020-03": 101.0,
        "2020-04": 101.0,
    }
    real = {month: 0.0 for month in ("2020-01", "2020-02", "2020-03", "2020-04")}
    # The 1% CPI step happens over 2019-12 to 2020-01, so with a three-month lag it
    # lands in 2020-04 and nowhere else.
    nominal = tips_nominal_total_return(real, prices, lag_months=REF_CPI_LAG_MONTHS)
    assert nominal["2020-04"] == pytest.approx(0.01)
    assert nominal["2020-03"] == pytest.approx(0.0)


def test_tips_nominal_total_return_compounds_rather_than_adds() -> None:
    prices = {"2019-12": 100.0, "2020-01": 110.0, "2020-02": 110.0}
    real = {"2020-04": 0.05}
    nominal = tips_nominal_total_return(real, prices, lag_months=3)
    assert nominal["2020-04"] == pytest.approx(1.05 * 1.10 - 1.0)


def test_months_between_counts_calendar_months() -> None:
    assert months_between("2019-12", "2020-01") == 1
    assert months_between("2020-01", "2019-12") == -1
    assert months_between("2019-01", "2020-01") == 12


def test_correlation_stability_recovers_a_planted_sign_flip() -> None:
    """Two blocks constructed to correlate +1 and -1 must read exactly that."""
    months = [f"2000-{month:02d}" for month in range(1, 13)]
    base = {month: float(index + 1) for index, month in enumerate(months)}
    series = {
        month: (base[month] if index < 6 else -base[month])
        for index, month in enumerate(months)
    }
    stability = correlation_stability(series, base, months, label="planted", block_months=6)
    assert [round(value, 9) for _, _, value in stability.blocks] == [1.0, -1.0]
    assert stability.span == pytest.approx(2.0)
    assert stability.flips_sign is True


def test_correlation_stability_drops_a_partial_trailing_block() -> None:
    months = [f"2000-{month:02d}" for month in range(1, 11)]
    base = {month: float(index) for index, month in enumerate(months)}
    series = {month: float(index) ** 2 for index, month in enumerate(months)}
    stability = correlation_stability(series, base, months, label="partial", block_months=6)
    assert len(stability.blocks) == 1
    assert stability.blocks[0][1] == "2000-06"


def test_correlation_stability_refuses_a_ragged_window() -> None:
    months = ["2000-01", "2000-02", "2000-03"]
    with pytest.raises(ValueError, match="missing"):
        correlation_stability(
            {"2000-01": 1.0, "2000-02": 2.0},
            {month: 1.0 for month in months},
            months,
            label="ragged",
            block_months=2,
        )


def test_correlation_standard_error_is_the_textbook_form() -> None:
    assert correlation_standard_error(0.0, 103) == pytest.approx(0.1)
    assert correlation_standard_error(0.5, 103) == pytest.approx(0.075)


def test_annualised_scales_the_mean_by_twelve_and_the_deviation_by_root_twelve() -> None:
    values = [0.01, -0.01] * 6
    mean, volatility = annualised(values)
    assert mean == pytest.approx(0.0)
    assert volatility == pytest.approx(
        float(np.std(values, ddof=1)) * math.sqrt(12.0)
    )


def test_the_shelf_has_one_base_and_no_duplicate_class_identifiers() -> None:
    assert sum(1 for entry in FIXED_INCOME_SHELF if entry.role == "base") == 1
    class_ids = [entry.class_id for entry in FIXED_INCOME_SHELF]
    assert len(set(class_ids)) == len(class_ids)
    series_ids = [entry.series_id for entry in FIXED_INCOME_SHELF]
    assert len(set(series_ids)) == len(series_ids)
