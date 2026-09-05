"""Unit tests for Experiment 026, engines on the bond line of the cautious portfolio.

Every expected value here is computed in this file by hand or with plain NumPy,
never by calling the code under test on the same inputs.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pytest

from portfolio_edge.experiments.exp_016_construction_tournament import BasisPanel
from portfolio_edge.experiments.exp_026_trend_from_the_bond_line import (
    PanelSpec,
    _drawdowns_with_difference,
    _regime_with_gold,
    arm_notional,
    default_specification_path,
    gde_regret_pp_yr,
    gold_notional,
    read_arm_families,
    read_arms,
    read_panels,
    read_wrappers,
    rsbt_regret_pp_yr,
    trend_fund_regret_pp_yr,
)
from portfolio_edge.experiments.specification import Specification, load_specification


@pytest.fixture(scope="module")
def specification() -> Specification:
    return load_specification(default_specification_path())


# --------------------------------------------------------------------------- #
# Notional, one row per arm, by hand
# --------------------------------------------------------------------------- #

RSST_EQUITY = 1.072
CAUTIOUS_EQUITY = 0.35 + 0.15 * RSST_EQUITY

EXPECTED = {
    # arm: (gross, equity, trend, bond, gold)
    "cautious": (CAUTIOUS_EQUITY + 0.15 + 0.50, CAUTIOUS_EQUITY, 0.15, 0.50, 0.0),
    "rsbt10": (CAUTIOUS_EQUITY + 0.25 + 0.50, CAUTIOUS_EQUITY, 0.25, 0.50, 0.0),
    "rsbt20": (CAUTIOUS_EQUITY + 0.35 + 0.50, CAUTIOUS_EQUITY, 0.35, 0.50, 0.0),
    "rsbt30": (CAUTIOUS_EQUITY + 0.45 + 0.50, CAUTIOUS_EQUITY, 0.45, 0.50, 0.0),
    "trendfund10": (CAUTIOUS_EQUITY + 0.25 + 0.40, CAUTIOUS_EQUITY, 0.25, 0.40, 0.0),
    "trendfund20": (CAUTIOUS_EQUITY + 0.35 + 0.30, CAUTIOUS_EQUITY, 0.35, 0.30, 0.0),
    "trendfund30": (CAUTIOUS_EQUITY + 0.45 + 0.20, CAUTIOUS_EQUITY, 0.45, 0.20, 0.0),
    "gde10": (CAUTIOUS_EQUITY + 0.15 + 0.49 + 0.09, CAUTIOUS_EQUITY, 0.15, 0.49, 0.09),
    "gde20": (CAUTIOUS_EQUITY + 0.15 + 0.48 + 0.18, CAUTIOUS_EQUITY, 0.15, 0.48, 0.18),
    "gde30": (CAUTIOUS_EQUITY + 0.15 + 0.47 + 0.27, CAUTIOUS_EQUITY, 0.15, 0.47, 0.27),
}


def test_every_arm_derives_the_notional_the_specification_states(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    assert set(arms) == set(EXPECTED)
    for name, (gross, equity, trend, bond, gold) in EXPECTED.items():
        arm = arms[name]
        notional = arm_notional(arm.tickers, arm.weights, wrappers)
        assert notional.gross == pytest.approx(gross, abs=1e-9), name
        assert notional.equity == pytest.approx(equity, abs=1e-9), name
        assert notional.trend == pytest.approx(trend, abs=1e-9), name
        assert notional.bond == pytest.approx(bond, abs=1e-9), name
        assert notional.cash == pytest.approx(0.0, abs=1e-9), name
        assert gold_notional(arm.tickers, arm.weights, wrappers) == pytest.approx(gold), name


def test_every_candidate_matches_the_reference_on_equity_and_differs_on_one_line(
    specification: Specification,
) -> None:
    """The whole difference against `cautious` is the engine and what it displaces."""
    wrappers = read_wrappers(specification)
    arms = read_arms(specification)
    reference = arm_notional(arms["cautious"].tickers, arms["cautious"].weights, wrappers)
    families = read_arm_families(specification)
    assert set(families) == {"rsbt", "trendfund", "gde"}
    for family, members in families.items():
        for name in members:
            arm = arms[name]
            n = arm_notional(arm.tickers, arm.weights, wrappers)
            assert abs(n.equity - reference.equity) < 1e-9, name
            if family == "rsbt":
                assert n.bond == pytest.approx(reference.bond), name
                assert n.trend > reference.trend
            elif family == "trendfund":
                assert n.bond < reference.bond
                assert n.trend - reference.trend == pytest.approx(reference.bond - n.bond)
            else:
                assert n.trend == pytest.approx(reference.trend), name
                assert gold_notional(arm.tickers, arm.weights, wrappers) > 0.0


def test_the_wrappers_finance_what_they_say_and_price_every_financed_leg(
    specification: Specification,
) -> None:
    wrappers = read_wrappers(specification)
    assert wrappers["RSBT_LIKE"].exposures == {"tsy10": 1.0, "trend": 1.0}
    assert wrappers["RSBT_LIKE"].financed == {"treasury": 1.0}
    assert wrappers["RSBT_LIKE"].fee_bp == 97.0
    assert wrappers["TREND_FUND"].exposures == {"trend": 1.0}
    assert wrappers["TREND_FUND"].financed == {}
    assert wrappers["TREND_FUND"].fee_bp == 85.0
    assert wrappers["GDE_LIKE"].exposures == {"equity": 0.9, "gold": 0.9}
    assert wrappers["GDE_LIKE"].financed == {"gold": 0.9}
    assert wrappers["GDE_LIKE"].fee_bp == 20.0
    assert wrappers["TSY10"].financed == {}


def test_the_gold_arms_run_only_where_gold_exists(specification: Specification) -> None:
    panels = read_panels(specification)
    by_id = {p.id: p for p in panels}
    assert "gold" not in by_id["primary"].legs
    assert "gold" in by_id["primary_gold"].legs
    assert by_id["primary_gold"].start == "1968-05"
    assert not any(a.startswith("gde") for a in by_id["primary"].arms)
    assert {"gde10", "gde20", "gde30"} <= set(by_id["primary_gold"].arms)
    # Every trend arm is re-run on the gold window so all nine can be read together.
    assert set(by_id["primary"].arms) <= set(by_id["primary_gold"].arms)


# --------------------------------------------------------------------------- #
# Regret closed forms, by hand
# --------------------------------------------------------------------------- #


def test_rsbt_regret_by_hand() -> None:
    """X = 0.2, t = 4.07: 0.2 x (4.07 - 0.97 - 0.15 + 0.05) = 0.2 x 3.00."""
    gap = rsbt_regret_pp_yr(
        points=0.2,
        trend_gross_pp_yr=4.07,
        rsbt_fee_pp_yr=0.97,
        treasury_financing_pp_yr=0.15,
        bond_line_fee_pp_yr=0.05,
    )
    assert gap == pytest.approx(0.6)
    # Break-even at the wrapper's net cost.
    assert rsbt_regret_pp_yr(
        points=0.3,
        trend_gross_pp_yr=1.07,
        rsbt_fee_pp_yr=0.97,
        treasury_financing_pp_yr=0.15,
        bond_line_fee_pp_yr=0.05,
    ) == pytest.approx(0.0)


def test_trend_fund_regret_by_hand() -> None:
    """X = 0.1, lambda = 0.671, t = 4.07, b = 0.8: 0.1 x (2.731 - 0.85 + 0.05 - 0.8)."""
    gap = trend_fund_regret_pp_yr(
        points=0.1,
        trend_gross_pp_yr=4.07,
        delivered_loading=0.671,
        trend_fund_fee_pp_yr=0.85,
        bond_line_fee_pp_yr=0.05,
        bond_excess_pp_yr=0.8,
    )
    assert gap == pytest.approx(0.1 * (0.671 * 4.07 - 0.85 + 0.05 - 0.8))
    # The sold arm's hurdle is the fee plus the bond it gives up: at full loading 1.60.
    assert trend_fund_regret_pp_yr(
        points=0.3,
        trend_gross_pp_yr=1.6,
        delivered_loading=1.0,
        trend_fund_fee_pp_yr=0.85,
        bond_line_fee_pp_yr=0.05,
        bond_excess_pp_yr=0.8,
    ) == pytest.approx(0.0)


def test_gde_regret_by_hand() -> None:
    """X = 0.1, g = 2: 0.1 x (1.8 - 0.20 - 0.27 + 0.027 + 0.005 - 0.08)."""
    gap = gde_regret_pp_yr(
        points=0.1,
        gold_excess_pp_yr=2.0,
        gde_fee_pp_yr=0.20,
        gold_financing_pp_yr=0.30,
        core_fee_pp_yr=0.03,
        bond_line_fee_pp_yr=0.05,
        bond_excess_pp_yr=0.8,
    )
    assert gap == pytest.approx(0.1 * (1.8 - 0.20 - 0.27 + 0.027 + 0.005 - 0.08))
    # At zero gold premium the cell is the cost, and it is negative.
    assert (
        gde_regret_pp_yr(
            points=0.1,
            gold_excess_pp_yr=0.0,
            gde_fee_pp_yr=0.20,
            gold_financing_pp_yr=0.30,
            core_fee_pp_yr=0.03,
            bond_line_fee_pp_yr=0.05,
            bond_excess_pp_yr=0.8,
        )
        < 0.0
    )


# --------------------------------------------------------------------------- #
# Drawdown differences and the gold regime, on hand-built series
# --------------------------------------------------------------------------- #


def test_drawdown_difference_is_arm_minus_reference_in_points() -> None:
    periods = tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(24))
    reference = np.array([0.10, -0.20] + [0.0] * 22, dtype=np.float64)  # -20%
    shallower = np.array([0.10, -0.10] + [0.0] * 22, dtype=np.float64)  # -10%
    deeper = np.array([0.10, -0.30] + [0.0] * 22, dtype=np.float64)  # -30%
    rows = _drawdowns_with_difference(
        {"ref": reference, "a": shallower, "b": deeper},
        periods=periods,
        eras=[("full", periods[0], periods[-1])],
        reference="ref",
    )
    arms = rows[0]["arms"]
    assert isinstance(arms, Mapping)
    a, b, ref = arms["a"], arms["b"], arms["ref"]
    assert isinstance(a, Mapping) and isinstance(b, Mapping) and isinstance(ref, Mapping)
    assert a["minus_reference_pp"] == pytest.approx(10.0)
    assert b["minus_reference_pp"] == pytest.approx(-10.0)
    assert ref["minus_reference_pp"] == pytest.approx(0.0)


def test_gold_regime_reports_gold_excess_only_when_the_panel_carries_it() -> None:
    periods = tuple(f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(36))
    rng = np.random.default_rng(3)
    base = {
        "equity": rng.normal(0.005, 0.04, 36),
        "tsy10": rng.normal(0.001, 0.015, 36),
        "treasury": rng.normal(0.001, 0.02, 36),
        "trend": rng.normal(0.004, 0.03, 36),
    }
    cash = np.full(36, 0.002)
    without = BasisPanel(periods=periods, series=base, cash=cash, provenance=(), findings=())
    rows = _regime_with_gold(without, [])
    assert "gold_excess_pp_yr" not in rows[0]
    gold = np.full(36, 0.01)
    with_gold = BasisPanel(
        periods=periods, series={**base, "gold": gold}, cash=cash, provenance=(), findings=()
    )
    rows = _regime_with_gold(with_gold, [])
    # 1% a month is 12 pp/yr, exactly.
    assert rows[0]["gold_excess_pp_yr"] == pytest.approx(12.0)


def test_panel_spec_is_a_plain_record() -> None:
    spec = PanelSpec(id="x", legs=("equity",), start=None, arms=("cautious",), note="")
    assert spec.start is None and spec.arms == ("cautious",)
