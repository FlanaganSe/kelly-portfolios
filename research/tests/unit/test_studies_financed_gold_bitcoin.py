"""Unit tests for :mod:`portfolio_edge.studies.financed_gold_bitcoin`.

No market data. The financed-stack arithmetic is checked against figures worked by hand
in the comments below, which share nothing with the module's own loops, and the
break-even is checked both by hand and by round-tripping: a bitcoin premium set to the
break-even must make the stack's expected gap exactly zero when pushed back through the
wrapper algebra.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.financed_gold_bitcoin import (
    Wrapper,
    break_even_bitcoin_excess,
    compare,
    growth_penalty_pp_yr,
    notional,
    portfolio_total,
    track,
    wrapper_excess,
)

#: An RSSX-like stack: one dollar of equity, 0.65 gold and 0.35 bitcoin per dollar, at
#: 67 bp, financing the gold and bitcoin notional at each leg's basis.
RSSX_LIKE = Wrapper(
    ticker="RSSX_LIKE",
    exposures={"equity": 1.0, "gold": 0.65, "bitcoin": 0.35},
    fee_bp=67.0,
    financed={"gold": 0.65, "bitcoin": 0.35},
)
CORE = Wrapper(ticker="CORE", exposures={"equity": 1.0}, fee_bp=3.0, financed={})
BASIS = {"equity": 62.0, "gold": 30.0, "bitcoin": 62.0}


# ------------------------------------------------------------------ wrapper arithmetic


def test_wrapper_excess_matches_a_hand_computed_month() -> None:
    legs = {
        "equity": [0.01, -0.02],
        "gold": [0.005, 0.01],
        "bitcoin": [0.10, -0.20],
    }
    out = wrapper_excess(legs, RSSX_LIKE, BASIS)
    # Annual charge: 67 bp fee + 0.65 * 30 bp + 0.35 * 62 bp
    #              = 0.0067 + 0.00195 + 0.00217 = 0.01082; monthly 0.000901667.
    # Month 1: 0.01 + 0.65 * 0.005 + 0.35 * 0.10 = 0.04825; less charge = 0.047348333.
    # Month 2: -0.02 + 0.0065 - 0.07 = -0.0835; less charge = -0.084401667.
    assert out[0] == pytest.approx(0.047348333, abs=1e-9)
    assert out[1] == pytest.approx(-0.084401667, abs=1e-9)


def test_wrapper_excess_ignores_legs_it_does_not_hold_and_refuses_a_missing_basis() -> None:
    legs = {"equity": [0.01], "gold": [0.02], "bitcoin": [0.03], "trend": [0.04]}
    out = wrapper_excess(legs, CORE, BASIS)
    assert out[0] == pytest.approx(0.01 - 0.0003 / 12.0)
    with pytest.raises(ValueError, match="no basis"):
        wrapper_excess(legs, RSSX_LIKE, {"gold": 30.0})
    with pytest.raises(ValueError, match="not supplied"):
        wrapper_excess({"equity": [0.01]}, RSSX_LIKE, BASIS)
    with pytest.raises(ValueError, match="not aligned"):
        wrapper_excess({"equity": [0.01, 0.02], "gold": [0.01]}, CORE, BASIS)


def test_portfolio_total_is_cash_plus_weighted_excess_and_refuses_bad_weights() -> None:
    cash = [0.001, 0.002]
    excess = {"CORE": [0.01, -0.01], "RSSX_LIKE": [0.05, -0.08]}
    out = portfolio_total(cash, {"CORE": 0.9, "RSSX_LIKE": 0.1}, excess)
    # 0.001 + 0.9 * 0.01 + 0.1 * 0.05 = 0.015; 0.002 - 0.009 - 0.008 = -0.015.
    assert out.tolist() == pytest.approx([0.015, -0.015])
    with pytest.raises(ValueError, match="sum to"):
        portfolio_total(cash, {"CORE": 0.9, "RSSX_LIKE": 0.2}, excess)
    with pytest.raises(ValueError, match="no excess series"):
        portfolio_total(cash, {"CORE": 1.0}, {"RSSX_LIKE": [0.0, 0.0]})


def test_notional_adds_exposure_per_dollar_across_holdings() -> None:
    rsst = Wrapper(
        ticker="RSST_LIKE",
        exposures={"equity": 1.072, "trend": 1.0},
        fee_bp=99.0,
        financed={"equity": 0.331},
    )
    wrappers = {"CORE": CORE, "RSST_LIKE": rsst, "RSSX_LIKE": RSSX_LIKE}
    n = notional({"CORE": 0.6, "RSST_LIKE": 0.3, "RSSX_LIKE": 0.1}, wrappers)
    assert n["equity"] == pytest.approx(0.6 + 0.3 * 1.072 + 0.1)
    assert n["trend"] == pytest.approx(0.3)
    assert n["gold"] == pytest.approx(0.065)
    assert n["bitcoin"] == pytest.approx(0.035)
    assert n["gross"] == pytest.approx(0.6 + 0.3216 + 0.1 + 0.3 + 0.065 + 0.035)


# ------------------------------------------------------------------------- break-even


def test_break_even_bitcoin_excess_by_hand() -> None:
    # Charges per dollar of stack over the core: (67 - 3) bp + 0.65 * 30 + 0.35 * 62
    #   = 64 + 19.5 + 21.7 = 105.2 bp = 1.052 pp/yr.
    # Gold covers 0.65 * 1.75 = 1.1375 pp/yr. Bitcoin must cover the rest:
    #   (1.052 - 1.1375) / 0.35 = -0.244286 pp/yr.
    assert break_even_bitcoin_excess(
        RSSX_LIKE, core_fee_bp=3.0, basis_bp=BASIS, gold_excess_pp_yr=1.75
    ) == pytest.approx(-0.244286, abs=1e-6)
    # With gold at zero: 1.052 / 0.35 = 3.005714.
    assert break_even_bitcoin_excess(
        RSSX_LIKE, core_fee_bp=3.0, basis_bp=BASIS, gold_excess_pp_yr=0.0
    ) == pytest.approx(3.005714, abs=1e-6)
    # A growth penalty of 0.7 pp/yr raises it by 0.7 / 0.35 = 2.0.
    assert break_even_bitcoin_excess(
        RSSX_LIKE, core_fee_bp=3.0, basis_bp=BASIS, gold_excess_pp_yr=0.0, growth_penalty=0.7
    ) == pytest.approx(5.005714, abs=1e-6)


def test_break_even_round_trips_through_the_wrapper_algebra() -> None:
    """At the break-even, one dollar of stack earns exactly what one dollar of core does."""
    mu_gold, mu_equity = 1.75, 5.0
    mu_btc = break_even_bitcoin_excess(
        RSSX_LIKE,
        core_fee_bp=3.0,
        basis_bp=BASIS,
        gold_excess_pp_yr=mu_gold,
        equity_excess_pp_yr=mu_equity,
    )
    # Feed constant monthly legs equal to the annual premia / 1200 through the algebra.
    legs = {
        "equity": [mu_equity / 1200.0] * 12,
        "gold": [mu_gold / 1200.0] * 12,
        "bitcoin": [mu_btc / 1200.0] * 12,
    }
    stack = wrapper_excess(legs, RSSX_LIKE, BASIS)
    core = wrapper_excess(legs, CORE, BASIS)
    assert float(np.sum(stack - core)) == pytest.approx(0.0, abs=1e-12)


def test_break_even_uses_the_equity_mismatch_and_refuses_a_stack_without_bitcoin() -> None:
    gde = Wrapper(
        ticker="GDE_LIKE",
        exposures={"equity": 0.9, "gold": 0.9},
        fee_bp=20.0,
        financed={"gold": 0.9},
    )
    with pytest.raises(ValueError, match="no bitcoin"):
        break_even_bitcoin_excess(gde, core_fee_bp=3.0, basis_bp=BASIS, gold_excess_pp_yr=1.0)
    lean = Wrapper(
        ticker="LEAN",
        exposures={"equity": 0.9, "bitcoin": 0.5},
        fee_bp=3.0,
        financed={},
    )
    # No charges; the missing 0.1 of equity at 6 pp/yr costs 0.6, so bitcoin needs 1.2.
    assert break_even_bitcoin_excess(
        lean, core_fee_bp=3.0, basis_bp=BASIS, gold_excess_pp_yr=0.0, equity_excess_pp_yr=6.0
    ) == pytest.approx(1.2)


def test_growth_penalty_is_half_the_added_variance_per_unit_weight() -> None:
    n = 120
    ref = np.full(n, 0.005)
    d = np.where(np.arange(n) % 2 == 0, 0.02, -0.02)
    # var(ref) = 0; var(w d) with ddof=1 = w^2 * 0.02^2 * n / (n - 1).
    w = 0.1
    expected = 0.5 * (w**2 * 0.02**2 * n / (n - 1)) * 1200.0 / w
    assert growth_penalty_pp_yr(ref, d, weight=w) == pytest.approx(expected, rel=1e-12)
    with pytest.raises(ValueError, match="positive"):
        growth_penalty_pp_yr(ref, d, weight=0.0)


# ------------------------------------------------------------------------ comparison


def _panel() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = 120
    rng = np.random.default_rng(3)
    equity = rng.normal(0.005, 0.04, n)
    ref = np.full(n, 0.004)
    # The arm beats the reference by 10 bp a month on average, alternating +/- 60 bp, so
    # its own months alternate +1.1% and -0.1%.
    d = 0.001 + np.where(np.arange(n) % 2 == 0, 0.006, -0.006)
    return equity, ref, ref + d


def test_compare_reports_the_planted_gap_floor_and_drawdowns() -> None:
    equity, ref, arm = _panel()
    n = len(ref)
    indices = np.tile(np.arange(n), (5, 1))  # identity resamples: degenerate interval
    result = compare("planted", arm, ref, equity_excess=equity, indices=indices)
    assert result.months == n
    assert result.arithmetic_gap_pp_yr == pytest.approx(1200.0 * 0.001, abs=1e-9)
    assert result.arithmetic_interval == pytest.approx((1.2, 1.2), abs=1e-9)
    # MDE = 2.801585 * 1200 * sd(d) / sqrt(n), sd(d) = 0.006 * sqrt(n / (n - 1)).
    sd = 0.006 * math.sqrt(n / (n - 1))
    assert result.mde_pp_yr == pytest.approx(2.801585 * 1200.0 * sd / math.sqrt(n), rel=1e-9)
    assert result.tracking_error_pct == pytest.approx(sd * math.sqrt(12) * 100.0, rel=1e-9)
    # A constant positive reference never draws down; the arm's worst run is one -0.1% month.
    assert result.reference_max_drawdown == 0.0
    assert result.arm_max_drawdown == pytest.approx(-0.001)
    assert result.reference_log_growth_pp_yr == pytest.approx(1200.0 * math.log1p(0.004))
    assert result.log_growth_gap_pp_yr == pytest.approx(
        result.arm_log_growth_pp_yr - result.reference_log_growth_pp_yr
    )
    # The offset is independent of equity by construction: worst-decile mean near the
    # unconditional +0.1 pp/month, hit rate near one half, betas near zero.
    assert result.worst_decile_months == 12
    assert abs(result.worst_decile_offset_pp_month - 0.1) < 0.5
    assert 0.0 <= result.worst_decile_hit_rate <= 1.0
    assert abs(result.up_beta) < 0.2
    assert abs(result.down_beta) < 0.4


def test_compare_refuses_misaligned_inputs() -> None:
    equity, ref, arm = _panel()
    indices = np.tile(np.arange(len(ref)), (3, 1))
    with pytest.raises(ValueError, match="same months"):
        compare("x", arm[:-1], ref, equity_excess=equity, indices=indices)
    with pytest.raises(ValueError, match="indices must be"):
        compare("x", arm, ref, equity_excess=equity, indices=indices[:, :-1])


# -------------------------------------------------------------------------- tracking


def test_track_reports_cumulative_returns_and_the_mean_gap() -> None:
    fund = np.array([0.02, -0.01, 0.03, 0.00])
    model = np.array([0.01, -0.02, 0.02, 0.01])
    out = track(fund, model)
    assert out.months == 4
    assert out.fund_cumulative == pytest.approx(1.02 * 0.99 * 1.03 - 1.0)
    assert out.model_cumulative == pytest.approx(1.01 * 0.98 * 1.02 * 1.01 - 1.0)
    # Differences: +1, +1, +1, -1 pp; mean +0.5 pp, sd = 1 pp, se = 0.5 pp.
    assert out.mean_difference_pp_month == pytest.approx(0.5)
    assert out.difference_standard_error_pp_month == pytest.approx(0.5)
    assert -1.0 <= out.correlation <= 1.0
    with pytest.raises(ValueError, match="at least three"):
        track([0.01, 0.02], [0.01, 0.02])
