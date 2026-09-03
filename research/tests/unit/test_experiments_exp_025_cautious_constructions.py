"""Unit tests for Experiment 025, cautious constructions scored as objects.

Every expected value here is computed in this file by hand or with plain NumPy,
never by calling the code under test on the same inputs.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pytest

from portfolio_edge.experiments.exp_025_cautious_constructions import (
    arm_notional,
    default_specification_path,
    drawdown_by_era,
    leverage_matched_targets,
    pair_regret_pp_yr,
    plain_regret_pp_yr,
    read_arms,
    read_pairs,
    read_wrappers,
    tolerance_reading,
)
from portfolio_edge.experiments.specification import Specification, load_specification


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(default_specification_path())


# --------------------------------------------------------------------------- #
# Notional derivation, one row per arm, by hand
# --------------------------------------------------------------------------- #

RSST_EQUITY = 1.072
RSST_GROSS = RSST_EQUITY + 1.0

EXPECTED_NOTIONAL = {
    # arm: (gross, equity, trend, bond, cash)
    "published_trend30": (0.70 + 0.30 * RSST_GROSS, 0.70 + 0.30 * RSST_EQUITY, 0.30, 0.0, 0.0),
    "plain60_40": (1.0, 0.60, 0.0, 0.40, 0.0),
    "trend15_eq60": (0.44 + 0.15 * RSST_GROSS + 0.41, 0.44 + 0.15 * RSST_EQUITY, 0.15, 0.41, 0.0),
    "plain40_60": (1.0, 0.40, 0.0, 0.60, 0.0),
    "trend11_eq40": (0.28 + 0.11 * RSST_GROSS + 0.61, 0.28 + 0.11 * RSST_EQUITY, 0.11, 0.61, 0.0),
    "ladder40": (
        0.348 + 0.149 * RSST_GROSS + 0.503,
        0.348 + 0.149 * RSST_EQUITY,
        0.149,
        0.503,
        0.0,
    ),
    "ladder40_plain": (1.0, 0.508, 0.0, 0.492, 0.0),
    "ladder30": (
        0.258 + 0.110 * RSST_GROSS + 0.632,
        0.258 + 0.110 * RSST_EQUITY,
        0.110,
        0.632,
        0.0,
    ),
    "ladder30_plain": (1.0, 0.376, 0.0, 0.624, 0.0),
    "plain60_40_ltbond": (1.0, 0.60, 0.0, 0.40, 0.0),
}


def test_every_arm_derives_the_notional_the_specification_states(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    assert set(arms) == set(EXPECTED_NOTIONAL)
    for name, (gross, equity, trend, bond, cash) in EXPECTED_NOTIONAL.items():
        arm = arms[name]
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        assert notional.gross == pytest.approx(gross, abs=1e-9), name
        assert notional.equity == pytest.approx(equity, abs=1e-9), name
        assert notional.trend == pytest.approx(trend, abs=1e-9), name
        assert notional.bond == pytest.approx(bond, abs=1e-9), name
        assert notional.cash == pytest.approx(cash, abs=1e-9), name


def test_every_trend_arm_matches_its_plain_twin_on_equity(specification: Specification) -> None:
    """The primary pairs are at matched equity: the whole difference is the trend line."""
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    primary, secondary = read_pairs(specification)
    assert primary == {
        "trend15_eq60": "plain60_40",
        "ladder40": "ladder40_plain",
        "ladder30": "ladder30_plain",
    }
    assert secondary == {"trend11_eq40": "plain40_60", "plain60_40_ltbond": "plain60_40"}
    for arm_name, twin_name in {**primary, **secondary}.items():
        arm, twin = arms[arm_name], arms[twin_name]
        a = arm_notional(arm.tickers, arm.weights, wrappers)
        t = arm_notional(twin.tickers, twin.weights, wrappers)
        assert abs(a.equity - t.equity) < 0.003, (arm_name, a.equity, t.equity)


def test_the_bond_lines_are_unlevered_and_the_tips_leg_is_admitted(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    for ticker, leg in (("TSY10", "tsy10"), ("TIPS", "tips"), ("LTBOND", "treasury")):
        assert wrappers[ticker].exposures == {leg: 1.0}
        assert wrappers[ticker].financed == {}
        assert wrappers[ticker].fee_bp == 5.0
    assert wrappers["RSST_LIKE"].fee_bp == 99.0
    assert wrappers["RSST_LIKE"].financed == {"equity": 0.331}
    assert wrappers["CASH"].exposures == {}


# --------------------------------------------------------------------------- #
# The sub-unity leverage-matched control
# --------------------------------------------------------------------------- #


def test_leverage_matched_scales_below_one_with_bills_and_finances_above_one() -> None:
    tickers, targets = leverage_matched_targets(1.1608)
    assert tickers == ("CORE",)
    np.testing.assert_allclose(targets, [1.1608])
    tickers, targets = leverage_matched_targets(0.6)
    assert tickers == ("CORE", "CASH")
    np.testing.assert_allclose(targets, [0.6, 0.4])
    tickers, targets = leverage_matched_targets(1.0)
    assert tickers == ("CORE", "CASH")
    np.testing.assert_allclose(targets, [1.0, 0.0])


# --------------------------------------------------------------------------- #
# Regret closed forms, by hand
# --------------------------------------------------------------------------- #


def test_pair_regret_by_hand() -> None:
    """w = 0.15, trend 4.07, equity over bonds 3: 0.15 x (4.07 - 1.1952 + 0.072 x 3)."""
    gap = pair_regret_pp_yr(
        wrapper_weight=0.15,
        trend_gross_pp_yr=4.07,
        equity_premium_over_bonds_pp_yr=3.0,
        wrapper_equity=1.072,
        wrapper_cost_pp_yr=1.1952,
    )
    assert gap == pytest.approx(0.15 * (4.07 - 1.1952 + 0.216))
    # The break-even at E = 0 is the wrapper cost itself.
    zero = pair_regret_pp_yr(
        wrapper_weight=0.11,
        trend_gross_pp_yr=1.1952,
        equity_premium_over_bonds_pp_yr=0.0,
        wrapper_equity=1.072,
        wrapper_cost_pp_yr=1.1952,
    )
    assert zero == pytest.approx(0.0)


def test_plain_regret_by_hand() -> None:
    """A 60/40 at 8 bp weighted fee against a 3 bp core, equities 3 points over bonds."""
    fee_delta = (0.60 * 0.03 + 0.40 * 0.05) - 0.03
    gap = plain_regret_pp_yr(
        equity_notional=0.6, equity_premium_over_bonds_pp_yr=3.0, fee_delta_pp_yr=fee_delta
    )
    assert gap == pytest.approx(-0.4 * 3.0 - 0.008)
    assert plain_regret_pp_yr(
        equity_notional=0.6, equity_premium_over_bonds_pp_yr=0.0, fee_delta_pp_yr=fee_delta
    ) == pytest.approx(-0.008)


# --------------------------------------------------------------------------- #
# Drawdown by era and the tolerance reading, on a hand-built path
# --------------------------------------------------------------------------- #


def test_drawdown_by_era_starts_each_era_fresh() -> None:
    periods = tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(24))
    # Wealth 1.10, 0.88, 0.924, 1.0164, then flat: worst fall -20%, under water from month 2 on.
    total = np.array([0.10, -0.20, 0.05, 0.10] + [0.0] * 20, dtype=np.float64)
    flat = np.zeros(24, dtype=np.float64)
    rows = drawdown_by_era(
        {"a": total, "b": flat},
        periods=periods,
        eras=[("full", periods[0], periods[-1]), ("second_year", periods[12], periods[-1])],
    )
    assert [r["era"] for r in rows] == ["full", "second_year"]
    full = rows[0]["arms"]
    assert isinstance(full, Mapping)
    a = full["a"]
    assert isinstance(a, Mapping)
    assert a["max_drawdown_pct"] == pytest.approx(-20.0)
    assert a["time_under_water_months"] == 23
    second = rows[1]["arms"]
    assert isinstance(second, Mapping)
    a2 = second["a"]
    assert isinstance(a2, Mapping)
    # Started fresh in the second year, the path never falls.
    assert a2["max_drawdown_pct"] == pytest.approx(0.0)
    assert a2["time_under_water_months"] == 0


def test_tolerance_reading_picks_the_deepest_fall_within_each_tolerance() -> None:
    reading = tolerance_reading(
        {"a": -25.0, "b": -35.0, "c": -48.0, "d": -60.0}, [-30.0, -40.0, -50.0, -20.0]
    )
    assert reading["-30"] == {"arm": "a", "max_drawdown_pct": -25.0}
    assert reading["-40"] == {"arm": "b", "max_drawdown_pct": -35.0}
    assert reading["-50"] == {"arm": "c", "max_drawdown_pct": -48.0}
    assert reading["-20"] is None
