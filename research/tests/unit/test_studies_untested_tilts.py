"""Tests for :mod:`portfolio_edge.studies.untested_tilts`.

The module has no data dependency and no randomness, so a failure here is a changed input
or a bug, never noise. Four kinds of test, kept apart:

* **The refusals.** Three of them are the reason the module exists rather than four lines
  in a table script: a capture fraction may not multiply a loading, a fee may not stand in
  for a net cost, and two after-tax tables from different periods may not subtract. Each
  guard is worth more than any number the module produces.
* **Independently computed fixtures**, written out longhand in the test so a passing
  assertion is arithmetic and not a second call to the implementation.
* **Identities**, where a property must hold for every input rather than one.
* **Delegation**, checking that the marginal verdict really is
  ``stacking.marginal_contribution`` and not a second definition of it.
"""

from __future__ import annotations

import math

import pytest

from portfolio_edge.studies.stacking import Sleeve, marginal_contribution
from portfolio_edge.studies.untested_tilts import (
    TURNOVER_COEFFICIENT_HIGH,
    TURNOVER_COEFFICIENT_LOW,
    AfterTaxReturns,
    FundCost,
    MismatchedTaxPeriodError,
    UnmeasuredCostError,
    UnpricedFactorError,
    annualise_monthly,
    edge_standard_error,
    effective_bets_of_pair,
    incremental_cost_bracket,
    incremental_distribution_tax_drag,
    marginal_tilt,
    portfolio_return_change,
    sleeve_edge,
    tracking_error_from_monthly,
)
from portfolio_edge.studies.value_tilt import CaptureDoubleCountError

# --------------------------------------------------------------------------- #
# The refusals
# --------------------------------------------------------------------------- #


def test_a_capture_fraction_may_not_multiply_a_loading() -> None:
    with pytest.raises(CaptureDoubleCountError, match=r"discounts it twice|applies it twice"):
        sleeve_edge(
            delivered={"HML": 0.5},
            premia={"HML": 4.0},
            incremental_cost=0.2,
            capture=0.6,
        )


def test_a_fund_with_no_lending_figure_has_no_net_cost() -> None:
    fund = FundCost(
        ticker="AVDV", fee_bp=36.0, securities_lending_bp=None, turnover_percent=4.0
    )
    assert not fund.lending_was_read
    with pytest.raises(UnmeasuredCostError, match="no securities-lending income"):
        _ = fund.net_cost_bp


def test_a_fund_with_a_lending_figure_has_one() -> None:
    fund = FundCost(
        ticker="VTI", fee_bp=3.0, securities_lending_bp=1.84, turnover_percent=3.0
    )
    assert fund.lending_was_read
    assert fund.net_cost_bp == pytest.approx(1.16)
    low, high = fund.cost_bracket_bp()
    assert low == pytest.approx(1.16)
    assert high == pytest.approx(3.0)


def test_an_unmeasured_fund_brackets_at_its_own_fee() -> None:
    """Lending can only lower a cost, so the fee is an upper bound and the bracket sits on it."""
    fund = FundCost(
        ticker="MTUM", fee_bp=15.0, securities_lending_bp=None, turnover_percent=116.0
    )
    assert fund.cost_bracket_bp() == (15.0, 15.0)


def test_an_unread_turnover_refuses_a_trading_charge() -> None:
    fund = FundCost(ticker="X", fee_bp=30.0, securities_lending_bp=None, turnover_percent=None)
    incumbent = FundCost(ticker="VTI", fee_bp=3.0, securities_lending_bp=1.84, turnover_percent=3.0)
    with pytest.raises(UnmeasuredCostError, match="no portfolio turnover was read"):
        incremental_cost_bracket(fund=fund, incumbent=incumbent)


def test_after_tax_tables_from_different_periods_do_not_subtract() -> None:
    fund = AfterTaxReturns(
        ticker="MTUM",
        period="5 years to 2024-12",
        before_tax=11.77,
        after_tax_on_distributions=11.46,
    )
    incumbent = AfterTaxReturns(
        ticker="VTI",
        period="5 years to 2025-12",
        before_tax=13.08,
        after_tax_on_distributions=12.69,
    )
    with pytest.raises(MismatchedTaxPeriodError, match="do not subtract"):
        incremental_distribution_tax_drag(fund=fund, incumbent=incumbent)


def test_a_factor_with_no_premium_raises_rather_than_being_charged_zero() -> None:
    with pytest.raises(UnpricedFactorError, match="RMW"):
        sleeve_edge(
            delivered={"HML": 0.5, "RMW": 0.4},
            premia={"HML": 4.0},
            incremental_cost=0.0,
        )
    with pytest.raises(UnpricedFactorError, match="SMB"):
        edge_standard_error(
            delivered={"HML": 0.5, "SMB": 0.6}, minimum_detectable_premia={"HML": 3.67}
        )


# --------------------------------------------------------------------------- #
# Independently computed fixtures
# --------------------------------------------------------------------------- #


def test_sleeve_edge_against_a_hand_computed_fixture() -> None:
    """AVDV over VXUS on the own-panel premia, every term written out longhand."""
    delivered = {"HML": 0.464, "SMB": 0.639, "RMW": 0.703, "CMA": 0.089, "UMD": 0.006}
    premia = {"HML": 5.07125, "SMB": 0.49, "RMW": 1.681, "CMA": 0.533, "UMD": 8.351}
    expected = (
        0.464 * 5.07125
        + 0.639 * 0.49
        + 0.703 * 1.681
        + 0.089 * 0.533
        + 0.006 * 8.351
        - 0.346
    )
    assert sleeve_edge(
        delivered=delivered, premia=premia, incremental_cost=0.346
    ) == pytest.approx(expected)
    assert expected == pytest.approx(3.5995, abs=5e-4)


def test_a_null_premium_leaves_exactly_the_cost() -> None:
    delivered = {"HML": 0.464, "SMB": 0.639}
    assert sleeve_edge(
        delivered=delivered,
        premia=dict.fromkeys(delivered, 0.0),
        incremental_cost=0.346,
    ) == pytest.approx(-0.346)


def test_incremental_cost_bracket_against_a_hand_computed_fixture() -> None:
    """MTUM over VTI: 116%/yr against 3%, and the coefficient decides the verdict."""
    mtum = FundCost(
        ticker="MTUM", fee_bp=15.0, securities_lending_bp=None, turnover_percent=116.0
    )
    vti = FundCost(ticker="VTI", fee_bp=3.0, securities_lending_bp=1.84, turnover_percent=3.0)
    low, high = incremental_cost_bracket(fund=mtum, incumbent=vti)
    assert low == pytest.approx((15.0 - 3.0) / 100.0 + TURNOVER_COEFFICIENT_LOW * 113.0 / 100.0)
    assert high == pytest.approx(
        (15.0 - 1.16) / 100.0 + TURNOVER_COEFFICIENT_HIGH * 113.0 / 100.0
    )
    assert low == pytest.approx(1.250)
    assert high == pytest.approx(2.0594)


def test_a_candidate_that_trades_less_than_the_incumbent_gets_no_credit() -> None:
    quiet = FundCost(ticker="AVUV", fee_bp=25.0, securities_lending_bp=None, turnover_percent=6.0)
    busy = FundCost(ticker="VTV", fee_bp=3.0, securities_lending_bp=None, turnover_percent=8.0)
    low, high = incremental_cost_bracket(fund=quiet, incumbent=busy)
    assert low == high == pytest.approx(0.22)


def test_edge_standard_error_sums_rather_than_adding_in_quadrature() -> None:
    delivered = {"HML": 0.464, "SMB": 0.639}
    floors = {"HML": 3.67, "SMB": 2.83}
    multiplier = 1.6448536269514722 + 0.8416212335729143
    expected = 0.464 * 3.67 / multiplier + 0.639 * 2.83 / multiplier
    assert edge_standard_error(
        delivered=delivered, minimum_detectable_premia=floors
    ) == pytest.approx(expected)
    quadrature = math.hypot(0.464 * 3.67 / multiplier, 0.639 * 2.83 / multiplier)
    assert expected > quadrature


def test_the_standard_error_reads_the_size_of_a_loading_not_its_sign() -> None:
    positive = edge_standard_error(
        delivered={"SMB": 0.639}, minimum_detectable_premia={"SMB": 2.83}
    )
    negative = edge_standard_error(
        delivered={"SMB": -0.639}, minimum_detectable_premia={"SMB": 2.83}
    )
    assert positive == pytest.approx(negative)


def test_distribution_drag_is_the_gap_between_the_two_filed_rows() -> None:
    mtum = AfterTaxReturns(
        ticker="MTUM",
        period="5 years to 2024-12",
        before_tax=11.77,
        after_tax_on_distributions=11.46,
    )
    vti = AfterTaxReturns(
        ticker="VTI",
        period="5 years to 2024-12",
        before_tax=13.80,
        after_tax_on_distributions=13.38,
    )
    assert mtum.distribution_drag == pytest.approx(0.31)
    assert vti.distribution_drag == pytest.approx(0.42)
    # Negative: the momentum fund's distributions cost a taxable holder LESS than the
    # total-market fund's, despite turning over 116% of the portfolio a year.
    assert incremental_distribution_tax_drag(fund=mtum, incumbent=vti) == pytest.approx(-0.11)


# --------------------------------------------------------------------------- #
# Identities
# --------------------------------------------------------------------------- #


def test_portfolio_return_change_is_linear_in_weight() -> None:
    assert portfolio_return_change(weight=0.10, edge=3.6) == pytest.approx(
        2.0 * portfolio_return_change(weight=0.05, edge=3.6)
    )
    assert portfolio_return_change(weight=0.0, edge=3.6) == 0.0


@pytest.mark.parametrize("weight", [-0.01, 1.01])
def test_a_weight_outside_the_unit_interval_is_refused(weight: float) -> None:
    with pytest.raises(ValueError, match="weight must lie"):
        portfolio_return_change(weight=weight, edge=1.0)


def test_two_uncorrelated_sleeves_are_two_bets_and_two_identical_ones_are_one() -> None:
    assert effective_bets_of_pair(0.0) == pytest.approx(2.0)
    assert effective_bets_of_pair(1.0) == pytest.approx(1.0)
    # The measured MTUM/IDMO correlation: two momentum tickers, fewer than two bets.
    assert effective_bets_of_pair(0.554) == pytest.approx(1.2870, abs=5e-4)


def test_effective_bets_fall_monotonically_in_correlation() -> None:
    previous = math.inf
    for step in range(-9, 11):
        current = effective_bets_of_pair(step / 10.0)
        assert current < previous
        previous = current


def test_a_perfectly_negative_correlation_has_no_finite_breadth() -> None:
    with pytest.raises(ValueError, match="correlation must lie"):
        effective_bets_of_pair(-1.0)


def test_annualisation_helpers() -> None:
    assert annualise_monthly(0.001) == pytest.approx(1.2)
    assert tracking_error_from_monthly(0.02) == pytest.approx(2.0 * math.sqrt(12.0))
    with pytest.raises(ValueError, match="cannot be negative"):
        tracking_error_from_monthly(-0.01)


def test_a_negative_fee_or_turnover_is_refused() -> None:
    with pytest.raises(ValueError, match="a fee cannot be negative"):
        FundCost(ticker="X", fee_bp=-1.0, securities_lending_bp=None, turnover_percent=1.0)
    with pytest.raises(ValueError, match="turnover cannot be negative"):
        FundCost(ticker="X", fee_bp=1.0, securities_lending_bp=None, turnover_percent=-1.0)


# --------------------------------------------------------------------------- #
# Delegation
# --------------------------------------------------------------------------- #


def test_marginal_tilt_is_exactly_the_stacking_modules_verdict() -> None:
    """One definition of ``alpha_k / omega_k`` in the repository, not two."""
    direct = marginal_contribution(
        label="AVDV",
        candidate=Sleeve(label="AVDV", weight=0.05, edge=3.603, tracking_error=5.59),
        held_edge=0.221,
        held_tracking_error=1.31,
        correlation_to_held=0.396,
    )
    delegated = marginal_tilt(
        ticker="AVDV",
        weight=0.05,
        candidate_edge=3.603,
        candidate_tracking_error=5.59,
        held_edge=0.221,
        held_tracking_error=1.31,
        correlation_to_held=0.396,
    )
    assert delegated == direct


def test_a_candidate_uncorrelated_with_what_is_held_keeps_its_whole_edge() -> None:
    verdict = marginal_tilt(
        ticker="X",
        weight=0.05,
        candidate_edge=3.0,
        candidate_tracking_error=6.0,
        held_edge=0.5,
        held_tracking_error=1.5,
        correlation_to_held=0.0,
    )
    assert verdict.beta == pytest.approx(0.0)
    assert verdict.alpha == pytest.approx(3.0)
    assert verdict.appraisal_ratio == pytest.approx(0.5)


def test_a_duplicate_of_what_is_held_adds_nothing_however_good_alone() -> None:
    """The investor's own objection, made exact: overlap can take the whole case away."""
    held_edge, held_error = 1.0, 2.0
    correlation, candidate_error = 0.8, 5.0
    beta = correlation * candidate_error / held_error
    verdict = marginal_tilt(
        ticker="X",
        weight=0.05,
        candidate_edge=beta * held_edge,
        candidate_tracking_error=candidate_error,
        held_edge=held_edge,
        held_tracking_error=held_error,
        correlation_to_held=correlation,
    )
    assert verdict.alpha == pytest.approx(0.0)
    assert verdict.appraisal_ratio == pytest.approx(0.0)
    assert not verdict.earns_its_place


def test_a_hand_computed_marginal_fixture() -> None:
    """AVDV against the portfolio's own active position, every term written out."""
    candidate_edge, candidate_error = 3.603, 5.59
    held_edge, held_error, correlation = 0.221, 1.31, 0.396
    beta = correlation * candidate_error / held_error
    alpha = candidate_edge - beta * held_edge
    residual = candidate_error * math.sqrt(1.0 - correlation**2)
    verdict = marginal_tilt(
        ticker="AVDV",
        weight=0.05,
        candidate_edge=candidate_edge,
        candidate_tracking_error=candidate_error,
        held_edge=held_edge,
        held_tracking_error=held_error,
        correlation_to_held=correlation,
    )
    assert verdict.beta == pytest.approx(beta)
    assert verdict.alpha == pytest.approx(alpha)
    assert verdict.residual_tracking_error == pytest.approx(residual)
    assert verdict.appraisal_ratio == pytest.approx(alpha / residual)
    assert alpha == pytest.approx(3.2296, abs=5e-4)
