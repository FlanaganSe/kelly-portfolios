"""Offline tests for the currency-hedging arithmetic.

The load-bearing test in this file is
``test_the_forward_hedge_matches_an_independently_derived_payoff``. Everything the page
concludes rests on one identity — hedged equals unhedged less the currency give-up — and
that identity is checked here against a forward contract's payoff written out from
scratch, not against a rearrangement of the same expression.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.data import fred, macrohistory
from portfolio_edge.studies.currency_hedging import (
    HEDGE_RATIO_GRID,
    CurrencyPanel,
    currency_excess_return,
    effective_sample_size,
    forward_hedged_return,
    hedge_comparison,
    hedge_give_up,
    hedge_ratio_grid,
    implied_local_return,
    minimum_regret_ratio,
    usd_return,
    variance_minimising_hedge_ratio,
    weighted_basket,
)


def test_the_dollar_return_keeps_the_cross_term() -> None:
    """A 10% local gain in a currency that rises 5% is 15.5% in dollars, not 15%."""
    assert usd_return([0.10], [0.05])[0] == pytest.approx(0.155)
    # The half-point difference is the currency exposure of the equity's own gain, and
    # it is the reason a notional hedge cannot be exact.
    assert usd_return([0.10], [0.05])[0] - (0.10 + 0.05) == pytest.approx(0.005)


def test_the_local_return_inverts_the_dollar_return_exactly() -> None:
    local = np.array([0.10, -0.20, 0.03, 0.0])
    currency = np.array([0.05, 0.12, -0.07, 0.02])
    dollars = usd_return(local, currency)

    assert implied_local_return(dollars, currency) == pytest.approx(local)


def test_a_currency_that_lost_everything_cannot_be_divided_out() -> None:
    with pytest.raises(ValueError, match="-100%"):
        implied_local_return([0.1], [-1.0])


def test_the_currency_excess_return_is_foreign_cash_funded_in_dollars() -> None:
    """``(1.02)(1.05) - 1.04 = 0.031``, computed by hand."""
    assert currency_excess_return([0.05], [0.02], [0.04])[0] == pytest.approx(0.031)


def test_the_give_up_is_the_spot_move_less_the_forward_premium() -> None:
    """Two algebraically distinct forms of the same quantity must agree.

    A desk writes the give-up as ``(1 + s) - (1 + i_d)/(1 + i_f)``; this module computes
    it as the currency excess return divided by the foreign gross rate. If those two
    ever disagree the implementation has picked up a stray factor.
    """
    spot, foreign, domestic = 0.05, 0.02, 0.04
    desk_form = (1.0 + spot) - (1.0 + domestic) / (1.0 + foreign)

    assert hedge_give_up([spot], [foreign], [domestic])[0] == pytest.approx(desk_form)


def test_the_forward_hedge_matches_an_independently_derived_payoff() -> None:
    """Write the forward contract's payoff out and compare, without reusing the module.

    Start with one unit of foreign currency invested in a foreign asset. At maturity the
    position is worth ``S1 (1 + r_L)`` dollars per unit of ``S0``, and the short forward
    on the beginning notional pays ``F - S1``. Under CIP ``F = S0 (1 + i_d)/(1 + i_f)``.
    Nothing below refers to a currency excess return.
    """
    local, spot, foreign, domestic = 0.10, 0.05, 0.02, 0.04
    s0 = 1.0
    s1 = s0 * (1.0 + spot)
    forward = s0 * (1.0 + domestic) / (1.0 + foreign)
    terminal = s1 * (1.0 + local) + (forward - s1)
    expected = terminal / s0 - 1.0

    dollars = usd_return([local], [spot])
    hedged = forward_hedged_return(dollars, [spot], [foreign], [domestic])

    assert expected == pytest.approx(0.12460784313725, abs=1e-12)
    assert hedged[0] == pytest.approx(expected, abs=1e-15)


def test_a_full_hedge_is_the_unhedged_return_less_the_give_up() -> None:
    """The identity the whole page rests on, over a vector rather than one period."""
    rng = np.random.default_rng(20260822)
    local = rng.normal(0.005, 0.04, 200)
    spot = rng.normal(0.0, 0.025, 200)
    foreign = np.full(200, 0.002)
    domestic = np.full(200, 0.003)
    dollars = usd_return(local, spot)

    hedged = forward_hedged_return(dollars, spot, foreign, domestic)

    assert hedged == pytest.approx(dollars - hedge_give_up(spot, foreign, domestic))


def test_hedging_a_flat_currency_leaves_only_the_interest_differential() -> None:
    """With ``s = 0`` the hedged return is ``r_L`` plus ``i_d - i_f``, compounded."""
    hedged = forward_hedged_return(usd_return([0.10], [0.0]), [0.0], [0.02], [0.05])
    assert hedged[0] == pytest.approx(0.10 + (1.05 / 1.02 - 1.0))


def test_a_zero_hedge_ratio_changes_nothing_and_a_half_hedge_removes_half() -> None:
    dollars = usd_return([0.10], [0.05])
    full = forward_hedged_return(dollars, [0.05], [0.02], [0.04], hedge_ratio=1.0)
    half = forward_hedged_return(dollars, [0.05], [0.02], [0.04], hedge_ratio=0.5)
    none = forward_hedged_return(dollars, [0.05], [0.02], [0.04], hedge_ratio=0.0)

    assert none[0] == pytest.approx(dollars[0])
    assert half[0] == pytest.approx((dollars[0] + full[0]) / 2.0)


def test_a_basket_is_the_weighted_mean_of_its_legs_and_renormalises() -> None:
    series = {"EUR": [0.02, -0.01], "JPY": [-0.03, 0.04]}
    equal = weighted_basket({"EUR": 1.0, "JPY": 1.0}, series)
    unnormalised = weighted_basket({"EUR": 30.0, "JPY": 30.0}, series)

    assert equal == pytest.approx([-0.005, 0.015])
    assert unnormalised == pytest.approx(equal)


def test_a_basket_refuses_a_key_mismatch_rather_than_reweighting_silently() -> None:
    with pytest.raises(ValueError, match="missing series"):
        weighted_basket({"EUR": 1.0, "JPY": 1.0}, {"EUR": [0.01]})
    with pytest.raises(ValueError, match="unweighted series"):
        weighted_basket({"EUR": 1.0}, {"EUR": [0.01], "JPY": [0.02]})


def test_a_basket_refuses_a_negative_or_empty_weight_set() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        weighted_basket({"EUR": -0.5, "JPY": 1.5}, {"EUR": [0.01], "JPY": [0.02]})
    with pytest.raises(ValueError, match="weights is empty"):
        weighted_basket({}, {})


def test_a_non_finite_observation_is_refused_rather_than_filled() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        usd_return([0.1, float("nan")], [0.0, 0.0])


def test_misaligned_series_are_refused() -> None:
    with pytest.raises(ValueError, match="must be aligned"):
        usd_return([0.1, 0.2], [0.0])


def test_effective_sample_size_recovers_t_for_white_noise() -> None:
    rng = np.random.default_rng(7)
    white = rng.normal(0.0, 1.0, 4000)

    assert effective_sample_size(white) == pytest.approx(4000, rel=0.15)


def test_positive_autocorrelation_costs_effective_observations() -> None:
    """An AR(1) with phi = 0.6 is worth far fewer than T independent draws."""
    rng = np.random.default_rng(11)
    shocks = rng.normal(0.0, 1.0, 4000)
    series = np.zeros(4000)
    for index in range(1, 4000):
        series[index] = 0.6 * series[index - 1] + shocks[index]

    effective = effective_sample_size(series)

    assert effective < 4000 * 0.6
    # Theory: n_eff -> T (1 - phi) / (1 + phi) = T / 4 for phi = 0.6.
    assert effective == pytest.approx(4000 * 0.25, rel=0.35)


def test_a_constant_series_has_no_effective_sample_size() -> None:
    with pytest.raises(ValueError, match="constant series"):
        effective_sample_size([0.01] * 20)


def test_the_variance_minimising_ratio_is_the_regression_slope() -> None:
    """Build ``U = 2 cx + noise`` and check the ratio recovers the 2."""
    rng = np.random.default_rng(3)
    excess = rng.normal(0.0, 0.02, 5000)
    unhedged = 2.0 * excess + rng.normal(0.0, 0.001, 5000)

    assert variance_minimising_hedge_ratio(unhedged, excess) == pytest.approx(2.0, rel=0.02)


def test_a_currency_leg_that_hedges_the_equity_gives_a_ratio_below_one() -> None:
    """Negative covariance between the local leg and the currency leg is the whole case
    for staying unhedged on risk grounds, so the sign must come through."""
    rng = np.random.default_rng(5)
    excess = rng.normal(0.0, 0.02, 5000)
    local = -1.0 * excess + rng.normal(0.0, 0.001, 5000)
    unhedged = local + excess

    assert variance_minimising_hedge_ratio(unhedged, excess) == pytest.approx(0.0, abs=0.05)


def _panel(
    unhedged: np.ndarray, excess: np.ndarray, *, periods_per_year: int = 12
) -> CurrencyPanel:
    labels = tuple(f"{2000 + i // 12}-{i % 12 + 1:02d}" for i in range(unhedged.size))
    return CurrencyPanel(
        label="test",
        periods=labels,
        periods_per_year=periods_per_year,
        unhedged=unhedged,
        currency_excess=excess,
    )


def test_a_panel_refuses_an_unusual_frequency_and_a_label_mismatch() -> None:
    values = np.zeros(3)
    with pytest.raises(ValueError, match="periods_per_year"):
        CurrencyPanel(
            label="x", periods=("a", "b", "c"), periods_per_year=52,
            unhedged=values, currency_excess=values,
        )
    with pytest.raises(ValueError, match="period labels"):
        CurrencyPanel(
            label="x", periods=("a", "b"), periods_per_year=12,
            unhedged=values, currency_excess=values,
        )


def test_the_hedged_leg_of_a_panel_is_unhedged_less_the_give_up() -> None:
    unhedged = np.array([0.02, -0.03, 0.01])
    excess = np.array([0.004, -0.002, 0.001])

    assert _panel(unhedged, excess).hedged == pytest.approx(unhedged - excess)


def test_the_comparison_annualises_and_reports_its_own_detection_floor() -> None:
    rng = np.random.default_rng(19)
    excess = rng.normal(0.0, 0.02, 360)
    unhedged = rng.normal(0.006, 0.045, 360) + excess

    result = hedge_comparison(_panel(unhedged, excess))

    assert result.n_periods == 360
    assert result.mean_unhedged == pytest.approx(float(np.mean(unhedged)) * 12)
    assert result.mean_difference == pytest.approx(float(np.mean(excess)) * 12)
    assert result.mean_hedged == pytest.approx(result.mean_unhedged - result.mean_difference)
    assert result.volatility_unhedged == pytest.approx(
        float(np.std(unhedged, ddof=1)) * math.sqrt(12)
    )
    assert result.mde_80 > 0.0
    # A zero-mean currency leg cannot be resolved, which is the point of the flag.
    assert result.mean_resolved is False


def test_a_large_true_currency_mean_is_resolved_by_a_long_panel() -> None:
    """The flag must be able to say `yes`, or it is not measuring anything."""
    rng = np.random.default_rng(23)
    excess = rng.normal(0.02, 0.02, 600)
    unhedged = rng.normal(0.006, 0.045, 600) + excess

    result = hedge_comparison(_panel(unhedged, excess))

    assert result.mean_difference > result.mde_80
    assert result.mean_resolved is True


def test_hedging_a_currency_correlated_with_the_equity_cuts_volatility() -> None:
    rng = np.random.default_rng(29)
    excess = rng.normal(0.0, 0.02, 400)
    unhedged = rng.normal(0.006, 0.04, 400) + excess

    result = hedge_comparison(_panel(unhedged, excess))

    assert result.volatility_hedged < result.volatility_unhedged
    assert 0.0 < result.volatility_reduction < 1.0
    assert result.variance_ratio < 1.0


def test_the_hedge_ratio_grid_is_monotone_in_the_mean_when_the_currency_paid() -> None:
    unhedged = np.array([0.03, 0.01, -0.02, 0.04] * 25)
    excess = np.array([0.01, 0.005, -0.004, 0.002] * 25)

    points = hedge_ratio_grid(_panel(unhedged, excess))

    assert tuple(p.hedge_ratio for p in points) == HEDGE_RATIO_GRID
    assert points[0].mean == pytest.approx(float(np.mean(unhedged)) * 12)
    means = [p.mean for p in points]
    assert means == sorted(means, reverse=True)
    assert points[-1].mean == pytest.approx(float(np.mean(unhedged - excess)) * 12)


def test_the_minimum_regret_ratio_is_a_half_and_says_why() -> None:
    assert minimum_regret_ratio() == 0.5
    assert "forecast" in (minimum_regret_ratio.__doc__ or "")


def test_an_annual_panel_does_not_annualise_by_twelve() -> None:
    unhedged = np.array([0.10, -0.05, 0.20, 0.03])
    excess = np.array([0.01, -0.02, 0.03, 0.0])

    result = hedge_comparison(_panel(unhedged, excess, periods_per_year=1))

    assert result.mean_unhedged == pytest.approx(float(np.mean(unhedged)))


class TestExchangeRateSources:
    """The two source-side facts a currency result silently depends on."""

    def test_the_h10_quote_convention_is_read_from_the_registry(self) -> None:
        """Both directions must produce the same sign for the same economic event.

        The yen weakening from 100 to 110 per dollar and the pound weakening from 1.30
        to 1.18 dollars are both losses for a US holder of that currency.
        """
        yen = fred.get_series("DEXJPUS")
        pound = fred.get_series("DEXUSUK")

        assert yen.quote_convention == "foreign_per_usd"
        assert pound.quote_convention == "usd_per_foreign"
        assert fred.foreign_currency_return(yen, 100.0, 110.0) == pytest.approx(
            100.0 / 110.0 - 1.0
        )
        assert fred.foreign_currency_return(pound, 1.30, 1.18) == pytest.approx(
            1.18 / 1.30 - 1.0
        )
        assert fred.foreign_currency_return(yen, 100.0, 110.0) < 0.0
        assert fred.foreign_currency_return(pound, 1.30, 1.18) < 0.0

    def test_a_series_that_is_not_an_exchange_rate_has_no_return(self) -> None:
        with pytest.raises(ValueError, match="not an exchange rate"):
            fred.foreign_currency_return(fred.get_series("TB3MS"), 1.0, 1.0)

    def test_a_foreign_cash_rate_is_not_interchangeable_with_the_us_one(self) -> None:
        """Same maturity, same frequency, same construction, different currency.

        Without the currency field these two differ in no attribute the registry
        records, and a study could difference a euro rate against a euro rate and
        report a carry of zero.
        """
        reasons = fred.check_interchangeable("IR3TIB01USM156N", "IR3TIB01DEM156N")

        assert any("currency differs" in reason for reason in reasons)

    def test_the_us_cash_rate_requirement_still_resolves_to_one_series(self) -> None:
        """Registering eleven foreign rates must not make the US requirement ambiguous."""
        requirement = fred.CashRateRequirement(
            maturity_months=3.0,
            frequency="monthly",
            construction="interbank_offered_rate",
        )

        assert fred.resolve_cash_rate(requirement).series_id == "IR3TIB01USM156N"

    def test_the_jst_exchange_rate_is_local_currency_per_dollar(self) -> None:
        """The direction check that made ``xrusd`` landable.

        The United States column must be exactly 1.0 in every year. If a future release
        inverted the column this is the assertion that fails, and it fails before any
        currency return is computed from it.
        """
        table_ids = [
            variable.table_id
            for variable in macrohistory.get_dataset("jst_macrohistory_r6").variables
        ]

        assert "exchange_rate_usd" in table_ids

    def test_the_jst_exchange_rate_column_carries_its_direction_warning(self) -> None:
        variables = {
            variable.column: variable
            for variable in macrohistory.get_dataset("jst_macrohistory_r6").variables
        }
        notes = " ".join(variables["xrusd"].notes)

        assert "LOCAL CURRENCY UNITS PER US DOLLAR" in notes
        assert "A RISE IS A STRONGER DOLLAR" in notes
        assert "REDENOMINATION" in notes.upper()
