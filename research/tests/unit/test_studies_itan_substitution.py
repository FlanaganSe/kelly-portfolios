"""Tests for :mod:`portfolio_edge.studies.itan_substitution`.

No data dependency and no randomness. Three kinds of test: independently computed
fixtures written out longhand, identities that must hold for every input, and the
refusals that keep a substitution from describing a portfolio nobody proposed.
"""

from __future__ import annotations

import math

import pytest

from portfolio_edge.studies.itan_substitution import (
    PUBLISHED_VECTOR,
    SUBSTITUTION_WEIGHT,
    NcenLendingYear,
    lending_median_bp,
    substitution_return_change,
    tracking_error_after_substitution,
    vector_after_substitution,
)
from portfolio_edge.studies.untested_tilts import portfolio_return_change, sleeve_edge
from portfolio_edge.studies.value_tilt import CaptureDoubleCountError

# --------------------------------------------------------------------------- #
# Independently computed fixtures
# --------------------------------------------------------------------------- #


def test_the_substitution_against_a_hand_computed_fixture() -> None:
    """ITAN over VTV on the own-panel US premia, every term written out longhand.

    Loadings are the difference regression's on 54 months; premia are the repository's
    own-panel US figures; cost is the worse end of the bracket: a 50 bp fee less VTV's
    2.705 bp net cost, plus 23 points of excess turnover at k = 1.7.
    """
    delivered = {"HML": -0.154, "SMB": -0.146, "RMW": -0.381, "CMA": -0.246, "UMD": -0.221}
    premia = {"HML": 1.57, "SMB": 0.33, "RMW": 0.0, "CMA": 0.0, "UMD": 4.19}
    cost = (50.0 - 2.705) / 100.0 + 1.7 * 23.0 / 100.0
    gross = -0.154 * 1.57 - 0.146 * 0.33 - 0.381 * 0.0 - 0.246 * 0.0 - 0.221 * 4.19
    expected = 0.05 * (gross - cost)
    assert gross == pytest.approx(-1.2160, abs=5e-4)
    assert cost == pytest.approx(0.86395, abs=5e-5)
    assert substitution_return_change(
        weight=0.05, delivered=delivered, premia=premia, incremental_cost=cost
    ) == pytest.approx(expected)
    assert expected == pytest.approx(-0.1040, abs=5e-4)


def test_the_substitution_is_weight_times_the_sleeve_edge() -> None:
    delivered = {"HML": 0.3, "UMD": -0.1}
    premia = {"HML": 2.0, "UMD": 4.0}
    edge = sleeve_edge(delivered=delivered, premia=premia, incremental_cost=0.25)
    assert substitution_return_change(
        weight=0.15, delivered=delivered, premia=premia, incremental_cost=0.25
    ) == pytest.approx(portfolio_return_change(weight=0.15, edge=edge))


def test_a_capture_fraction_cannot_reach_the_substitution() -> None:
    """The refusal lives in ``sleeve_edge``; this checks the new path has no way round it."""
    with pytest.raises(CaptureDoubleCountError):
        sleeve_edge(delivered={"HML": 0.2}, premia={"HML": 1.0}, incremental_cost=0.0, capture=0.5)
    assert "capture" not in substitution_return_change.__code__.co_varnames


def test_lending_median_against_the_filed_figures() -> None:
    """ITAN's five N-CEN fiscal years, each ratio computed by hand in basis points."""
    filed = (
        ("2022-05-31", 6.00, 2_598_304.24),
        ("2023-05-31", 1_332.78, 9_831_388.54),
        ("2024-05-31", 266.00, 30_463_140.63),
        ("2025-05-31", 175.67, 36_955_931.83),
        ("2026-05-31", 5.03, 61_182_308.765),
    )
    years = tuple(
        NcenLendingYear(fiscal_year_end=end, net_income=income, average_net_assets=assets)
        for end, income, assets in filed
    )
    by_hand = sorted(income / assets * 1e4 for _, income, assets in filed)
    assert by_hand[2] == pytest.approx(0.04753, abs=1e-5)
    assert lending_median_bp(years) == pytest.approx(by_hand[2])
    # The 2023 year is 1.36 bp, thirty times the median; a mean would have followed it.
    assert years[1].basis_points == pytest.approx(1.3556, abs=1e-3)


def test_tracking_error_after_substitution_by_hand() -> None:
    """sqrt(2.5^2 + (0.05 * 9.6)^2 + 2 * 0.3 * 2.5 * 0.05 * 9.6)."""
    expected = math.sqrt(2.5**2 + 0.48**2 + 2 * 0.3 * 2.5 * 0.48)
    assert tracking_error_after_substitution(
        held_tracking_error=2.5, weight=0.05, candidate_tracking_error=9.6, correlation=0.3
    ) == pytest.approx(expected)
    assert expected == pytest.approx(2.6834, abs=5e-4)


# --------------------------------------------------------------------------- #
# Identities
# --------------------------------------------------------------------------- #


def test_an_uncorrelated_leg_adds_in_quadrature_and_a_perfect_one_adds_linearly() -> None:
    assert tracking_error_after_substitution(
        held_tracking_error=3.0, weight=0.5, candidate_tracking_error=8.0, correlation=0.0
    ) == pytest.approx(5.0)
    assert tracking_error_after_substitution(
        held_tracking_error=3.0, weight=0.5, candidate_tracking_error=8.0, correlation=1.0
    ) == pytest.approx(7.0)
    assert tracking_error_after_substitution(
        held_tracking_error=3.0, weight=0.5, candidate_tracking_error=8.0, correlation=-1.0
    ) == pytest.approx(1.0)


def test_a_substitution_funds_itself() -> None:
    after = vector_after_substitution(PUBLISHED_VECTOR, sell="VTV", buy="ITAN", weight=0.05)
    assert sum(after.values()) == pytest.approx(sum(PUBLISHED_VECTOR.values()))
    assert after["VTV"] == pytest.approx(0.10)
    assert after["ITAN"] == pytest.approx(0.05)
    untouched = {k: v for k, v in after.items() if k not in ("VTV", "ITAN")}
    assert untouched == {k: v for k, v in PUBLISHED_VECTOR.items() if k != "VTV"}


def test_the_published_vector_and_the_proposed_weight_are_the_ones_on_the_page() -> None:
    assert sum(PUBLISHED_VECTOR.values()) == pytest.approx(1.0)
    assert PUBLISHED_VECTOR["VTV"] == pytest.approx(0.15)
    assert pytest.approx(0.05) == SUBSTITUTION_WEIGHT


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


def test_selling_more_than_is_held_is_refused() -> None:
    with pytest.raises(ValueError, match="cannot move"):
        vector_after_substitution(PUBLISHED_VECTOR, sell="VTV", buy="ITAN", weight=0.20)
    with pytest.raises(ValueError, match="positive weight"):
        vector_after_substitution(PUBLISHED_VECTOR, sell="VTV", buy="ITAN", weight=0.0)


def test_an_empty_lending_record_is_not_zero() -> None:
    with pytest.raises(ValueError, match="cannot be read from nothing"):
        lending_median_bp(())
    with pytest.raises(ValueError, match="must be positive"):
        NcenLendingYear(fiscal_year_end="2022-05-31", net_income=1.0, average_net_assets=0.0)


@pytest.mark.parametrize(
    ("held", "weight", "candidate", "correlation"),
    [(-1.0, 0.05, 1.0, 0.0), (1.0, 1.5, 1.0, 0.0), (1.0, 0.05, 1.0, 1.2)],
)
def test_impossible_tracking_error_inputs_are_refused(
    held: float, weight: float, candidate: float, correlation: float
) -> None:
    with pytest.raises(ValueError):
        tracking_error_after_substitution(
            held_tracking_error=held,
            weight=weight,
            candidate_tracking_error=candidate,
            correlation=correlation,
        )
