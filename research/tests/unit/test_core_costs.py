"""Tests for :mod:`portfolio_edge.core.costs`."""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.core.costs import (
    IMPACT_COEFFICIENT_US_STOCKS_BP,
    K_FLOOR,
    K_PESSIMISTIC,
    NegativeWealthAfterCostsError,
    ProportionalCostModel,
    SquareRootImpactModel,
    TurnoverCostModel,
    apply_trade_costs,
    implied_turnover_coefficient,
    is_retail_implementable,
    one_sided_turnover,
    participation_from_notional,
    trades_from_weights,
)

# Novy-Marx and Velikov (2016), value-weighted decile long/short, 1963-2012, as
# tabulated in docs/research/portfolio-edge-research-framework.md, "Factors and
# manager alpha". Columns: one-sided monthly turnover range (%), gross bp/mo, net bp/mo.
NMV_TIERS: dict[str, tuple[float, float, float, float, float]] = {
    # name: (turnover_low, turnover_high, gross_bp, net_bp, published_k)
    "low": (1.2, 7.2, 42.8, 35.4, 1.70),
    "mid": (14.0, 35.0, 89.8, 42.8, 1.71),
    "high": (90.0, 94.0, 99.7, -44.0, 1.57),
}


def test_one_sided_turnover_is_half_the_absolute_weight_change() -> None:
    before = [0.6, 0.4]
    after = [0.5, 0.5]
    assert one_sided_turnover(before, after) == pytest.approx(0.10, rel=0.0, abs=1e-15)


def test_one_sided_turnover_of_an_unchanged_portfolio_is_zero() -> None:
    assert one_sided_turnover([0.3, 0.3, 0.4], [0.3, 0.3, 0.4]) == 0.0


def test_trades_from_weights_move_the_portfolio_to_the_target() -> None:
    trades = trades_from_weights([0.6, 0.4], [0.5, 0.5], 1000.0)
    assert trades == pytest.approx([-100.0, 100.0], rel=0.0, abs=1e-12)
    assert float(np.sum(trades)) == pytest.approx(0.0, rel=0.0, abs=1e-12)


# --------------------------------------------------------------------------------------
# The cost-by-turnover rule
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("tier", list(NMV_TIERS))
def test_published_k_implies_a_mean_turnover_inside_its_published_tier_range(
    tier: str,
) -> None:
    """k = cost / turnover, fitted across the Novy-Marx-Velikov tier means.

    The framework reports k = 1.70 (low), 1.71 (mid), 1.57 (high) but does not print
    the tier *mean* turnover, only the min-max range. The check that is available is
    therefore the inverse one: the mean turnover each published k implies must fall
    inside the published range for that tier. It does, for all three.

    Note for the record: only the high tier reproduces its k from the range midpoint
    (143.7 / 92 = 1.562); the low and mid midpoints give 1.762 and 1.918. The tier
    means are not midpoints, which is consistent but not independently verifiable
    from the published table alone.
    """
    low, high, gross, net, published_k = NMV_TIERS[tier]
    cost_bp = gross - net
    implied_turnover_pct = cost_bp / published_k
    assert low <= implied_turnover_pct <= high


def test_high_tier_k_reproduces_from_the_published_range_midpoint() -> None:
    low, high, gross, net, published_k = NMV_TIERS["high"]
    midpoint = 0.5 * (low + high)
    # 143.7 / 92 = 1.5620 against a published 1.57: within 0.01, which is the
    # accuracy the range midpoint can support. The low and mid tiers do not
    # reproduce this way (1.762 and 1.918 against 1.70 and 1.71).
    assert implied_turnover_coefficient(gross - net, midpoint) == pytest.approx(
        published_k, rel=0.0, abs=1e-2
    )


def test_the_published_k_values_bracket_the_configured_constants() -> None:
    published = [k for *_, k in NMV_TIERS.values()]
    assert min(published) > K_FLOOR
    assert pytest.approx(1.7, rel=0.0, abs=1e-12) == K_PESSIMISTIC
    assert min(published) <= K_PESSIMISTIC <= max(published)


def test_turnover_cost_model_is_linear_in_turnover() -> None:
    model = TurnoverCostModel(k=K_PESSIMISTIC)
    assert model.cost_bp_per_period(10.0) == pytest.approx(17.0, rel=0.0, abs=1e-12)
    assert model.cost_bp_per_period(20.0) == pytest.approx(34.0, rel=0.0, abs=1e-12)
    assert model.cost_bp_per_period(0.0) == 0.0


def test_the_optimistic_and_pessimistic_columns_differ_by_the_k_ratio() -> None:
    """Report gross, net-optimistic (k = 1.0) and net-pessimistic (k = 1.7) from one
    turnover input, so the spread between columns is the visible model uncertainty."""
    optimistic = TurnoverCostModel(k=K_FLOOR)
    pessimistic = TurnoverCostModel(k=K_PESSIMISTIC)
    turnover_pct = 25.0
    assert pessimistic.cost_bp_per_period(turnover_pct) == pytest.approx(
        optimistic.cost_bp_per_period(turnover_pct) * K_PESSIMISTIC / K_FLOOR,
        rel=1e-14,
        abs=0.0,
    )


def test_turnover_cost_from_a_trade_vector_matches_the_turnover_rule() -> None:
    model = TurnoverCostModel(k=1.7)
    value = 1_000_000.0
    trades = trades_from_weights([0.6, 0.4], [0.5, 0.5], value)
    # One-sided turnover is 10% of the portfolio, so 17 bp of value.
    assert model.cost(trades, value) == pytest.approx(value * 17.0 / 1e4, rel=1e-12, abs=0.0)


def test_retail_implementability_limit() -> None:
    """Treat anything above 50% monthly one-sided turnover as not retail-implementable
    regardless of gross Sharpe (framework, "Factors and manager alpha")."""
    assert is_retail_implementable(35.0)
    assert is_retail_implementable(50.0)
    assert not is_retail_implementable(50.0001)
    high_tier_midpoint = 0.5 * (NMV_TIERS["high"][0] + NMV_TIERS["high"][1])
    assert not is_retail_implementable(high_tier_midpoint)


# --------------------------------------------------------------------------------------
# Square-root market impact
# --------------------------------------------------------------------------------------


def test_square_root_impact_reproduces_the_ten_percent_participation_figure() -> None:
    """bp = c sqrt(|Q/V|) with c ~= 11 for US stocks.

    Framework, "Factors and manager alpha": at 10% of daily volume a linear model
    gives 223 bp against an executed 32 bp, and Almgren et al. (2005) independently
    estimate 32-43 bp. c = 11 reproduces that only when |Q/V| is read as a
    *percentage* of daily volume: 11 * sqrt(10) = 34.79 bp, inside 32-43. Reading
    |Q/V| as a fraction would give 11 * sqrt(0.1) = 3.48 bp, an order of magnitude
    too small. The unit contract is therefore part of the model, not a detail.
    """
    model = SquareRootImpactModel()
    assert model.coefficient_bp == IMPACT_COEFFICIENT_US_STOCKS_BP
    derived = 11.0 * math.sqrt(10.0)
    assert derived == pytest.approx(34.785054, rel=0.0, abs=5e-7)
    assert model.impact_bp(10.0) == pytest.approx(derived, rel=1e-14, abs=0.0)
    assert 32.0 <= model.impact_bp(10.0) <= 43.0


def test_square_root_impact_is_negligible_at_retail_participation() -> None:
    """At retail scale trade/ADV is far below 0.1%, so the impact term vanishes and
    the spread binds instead."""
    model = SquareRootImpactModel()
    assert model.impact_bp(0.1) == pytest.approx(11.0 * math.sqrt(0.1), rel=1e-14, abs=0.0)
    assert model.impact_bp(0.1) < 4.0


def test_impact_is_concave_so_a_linear_model_overstates_large_orders() -> None:
    model = SquareRootImpactModel()
    linear_at_ten = model.impact_bp(1.0) * 10.0
    assert model.impact_bp(10.0) < linear_at_ten


def test_the_impact_exponent_is_configurable_within_the_stated_band() -> None:
    """Almgren et al. reject the 1/2 exponent in favour of 3/5, so treat it as
    0.5 +/- 0.1."""
    for exponent in (0.4, 0.5, 0.6):
        model = SquareRootImpactModel(exponent=exponent)
        assert model.impact_bp(10.0) == pytest.approx(
            11.0 * 10.0**exponent, rel=1e-14, abs=0.0
        )
    steeper = SquareRootImpactModel(exponent=0.6).impact_bp(10.0)
    assert steeper > SquareRootImpactModel(exponent=0.5).impact_bp(10.0)


def test_participation_from_notional_returns_a_percentage() -> None:
    assert participation_from_notional(50_000.0, 5_000_000.0) == pytest.approx(
        1.0, rel=0.0, abs=1e-12
    )


def test_impact_cost_prices_each_leg_against_its_own_volume() -> None:
    model = SquareRootImpactModel()
    trades = [100_000.0, -50_000.0]
    volumes = [10_000_000.0, 5_000_000.0]
    expected = sum(
        abs(q) * (11.0 * (100.0 * abs(q) / v) ** 0.5) / 1e4
        for q, v in zip(trades, volumes, strict=True)
    )
    assert model.impact_cost(trades, volumes) == pytest.approx(expected, rel=1e-13, abs=0.0)


# --------------------------------------------------------------------------------------
# Properties: costs never increase wealth; zero-value trades never change it
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model",
    [
        ProportionalCostModel(cost_bp=0.0),
        ProportionalCostModel(cost_bp=25.0),
        TurnoverCostModel(k=K_FLOOR),
        TurnoverCostModel(k=K_PESSIMISTIC),
    ],
)
def test_costs_never_increase_wealth(model: ProportionalCostModel | TurnoverCostModel) -> None:
    rng = np.random.default_rng(20260811)
    wealth = 100_000.0
    for _ in range(200):
        trades = rng.normal(0.0, 5_000.0, size=5)
        assert apply_trade_costs(wealth, trades, model) <= wealth


@pytest.mark.parametrize(
    "model",
    [
        ProportionalCostModel(cost_bp=25.0),
        TurnoverCostModel(k=K_PESSIMISTIC),
    ],
)
def test_zero_value_trades_do_not_change_wealth(
    model: ProportionalCostModel | TurnoverCostModel,
) -> None:
    wealth = 100_000.0
    assert apply_trade_costs(wealth, [0.0, 0.0, 0.0], model) == wealth
    assert model.cost([0.0, 0.0, 0.0], wealth) == 0.0


def test_a_cost_that_would_exhaust_wealth_is_rejected() -> None:
    with pytest.raises(NegativeWealthAfterCostsError):
        apply_trade_costs(100.0, [1_000_000.0], ProportionalCostModel(cost_bp=500.0))


def test_a_negative_cost_rate_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        ProportionalCostModel(cost_bp=-1.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        TurnoverCostModel(k=-0.5)
