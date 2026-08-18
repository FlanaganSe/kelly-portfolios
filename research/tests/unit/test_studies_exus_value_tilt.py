"""The ex-US tilt arithmetic, against fixtures computed independently of it.

Four expectations below are computed without calling the code under test.
:func:`test_signability_worked_on_paper` enumerates the four clause combinations by hand;
:func:`test_the_two_ratios_against_hand_arithmetic` rebuilds both ranking ratios from the
tilt's own definition rather than from its output;
:func:`test_the_alpha_charge_worked_on_paper` works the charge and both refusals out on
paper; and :func:`test_premium_cell_detection_floor_from_the_normal_quantiles` recomputes
the 80%-power floor from the two standard normal quantiles printed in any table, with no
call to :func:`minimum_detectable_effect`.

A fixture that disagrees with the implementation is a finding, not a tolerance to loosen.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies._exus_value_tilt_tables import premium_cell
from portfolio_edge.studies.exus_value_tilt import (
    MATERIALITY_PERCENT,
    PremiumEvidence,
    alpha_charged_edge,
    growth_per_unit_tracking_error,
    signability,
    tracking_error_per_unit_exposure,
)
from portfolio_edge.studies.value_tilt import TiltInputs, tilt_verdict

Z_ONE_SIDED_95 = 1.6448536269514722
Z_POWER_80 = 0.8416212335729143
"""The two standard normal quantiles ``MDE = (z_alpha + z_power) * se`` is built from.

Written out so the fixture below does not import the function it is checking.
"""


def a_tilt(**overrides: float) -> TiltInputs:
    """AVDV against VEA on the common 2022-04..2025-12 window, unless overridden."""
    fields: dict[str, float] = {
        "weight": 0.08,
        "fund_hml_loading": 0.437,
        "benchmark_hml_loading": -0.0252,
        "hml_premium": 5.071,
        "fund_fee": 0.36,
        "benchmark_fee": 0.03,
        "fund_turnover_percent": 4.0,
        "benchmark_turnover_percent": 4.0,
        "turnover_coefficient": 1.7,
        "fund_volatility": 17.067,
        "benchmark_volatility": 16.598,
        "correlation": 0.955,
    }
    fields.update(overrides)
    return TiltInputs(**fields)


# --------------------------------------------------------------------------------
# Signability: the clause that decides whether an exposure is worth buying
# --------------------------------------------------------------------------------


def test_signability_worked_on_paper() -> None:
    """All four combinations of the two clauses, with the ex-US numbers as the anchors."""
    both = signability(point=5.071, low=1.453, high=9.048, mde80=3.670)
    assert both.signable
    assert both.interval_excludes_zero
    assert both.exceeds_detection_floor
    assert both.material

    neither = signability(point=0.489, low=-1.547, high=2.564, mde80=2.849)
    assert not neither.signable
    assert not neither.interval_excludes_zero
    assert not neither.exceeds_detection_floor
    assert not neither.material
    assert "contains zero" in neither.reason
    assert "detection floor" in neither.reason

    floor_only = signability(point=4.0, low=-1.0, high=9.0, mde80=3.0)
    assert not floor_only.signable
    assert floor_only.exceeds_detection_floor
    assert "contains zero" in floor_only.reason

    interval_only = signability(point=2.5, low=0.1, high=4.9, mde80=3.0)
    assert not interval_only.signable
    assert interval_only.interval_excludes_zero
    assert "could not have found it" in interval_only.reason


def test_signability_is_symmetric_in_sign() -> None:
    """A reliably negative premium is signable. The verdict is about evidence, not sign."""
    negative = signability(point=-4.0, low=-7.0, high=-1.0, mde80=3.0)
    assert negative.signable
    assert negative.material


def test_materiality_is_not_part_of_the_verdict() -> None:
    """A premium can be signable and too small to matter, and the two must not merge."""
    small = signability(point=1.0, low=0.5, high=1.5, mde80=0.8)
    assert small.signable
    assert not small.material
    assert MATERIALITY_PERCENT == 2.0


def test_a_premium_must_name_its_panel() -> None:
    """`An ex-US loading without its panel named is not a number` — nor is a premium."""
    with pytest.raises(ValueError, match="name the panel"):
        PremiumEvidence(
            label="HML", panel="  ", window="1994-01..2025-12", months=384,
            point=5.071, low=1.453, high=9.048, mde80=3.670,
        )


def test_an_inverted_interval_is_refused() -> None:
    with pytest.raises(ValueError, match="inverted"):
        PremiumEvidence(
            label="HML", panel="developed_ex_us", window="1994-01..2025-12", months=384,
            point=5.071, low=9.048, high=1.453, mde80=3.670,
        )


# --------------------------------------------------------------------------------
# The two ranking ratios
# --------------------------------------------------------------------------------


def test_the_two_ratios_against_hand_arithmetic() -> None:
    """Both ratios rebuilt from the tilt's definitions rather than from its output.

    ``sd(fund - benchmark) = sqrt(sf^2 + sb^2 - 2 rho sf sb)`` and the delivered loading
    is ``h_fund - h_benchmark``; the growth contribution is ``w * edge`` less half the
    variance the substitution adds, in percent per year. Neither expectation below calls
    anything in :mod:`portfolio_edge.studies.exus_value_tilt`.
    """
    inputs = a_tilt()
    fund, benchmark, rho = 17.067, 16.598, 0.955
    sleeve = math.sqrt(fund**2 + benchmark**2 - 2.0 * rho * fund * benchmark)
    delivered = 0.437 - (-0.0252)
    assert tracking_error_per_unit_exposure(inputs) == pytest.approx(sleeve / delivered)

    weight = 0.08
    covariance = rho * fund * benchmark
    tilted = (
        (1.0 - weight) ** 2 * benchmark**2
        + 2.0 * weight * (1.0 - weight) * covariance
        + weight**2 * fund**2
    )
    edge = delivered * 5.071 - (0.36 - 0.03)
    growth = weight * edge - (tilted - benchmark**2) / 200.0
    expected = growth * 100.0 / (weight * sleeve / 0.01)
    assert growth_per_unit_tracking_error(tilt_verdict(inputs)) == pytest.approx(expected)


def test_both_ratios_are_invariant_to_the_weight() -> None:
    """Edge and tracking error are both linear in the weight, so the ratio ranks funds.

    The growth ratio is only *nearly* invariant, because the variance term is quadratic;
    across the 4% to 12% range this repository would consider, it moves by under 1%.
    """
    ratios = [
        growth_per_unit_tracking_error(tilt_verdict(a_tilt(weight=weight)))
        for weight in (0.04, 0.08, 0.12)
    ]
    assert max(ratios) - min(ratios) < 0.01 * max(ratios)
    exposures = [
        tracking_error_per_unit_exposure(a_tilt(weight=weight)) for weight in (0.04, 0.12)
    ]
    assert exposures[0] == pytest.approx(exposures[1])


def test_a_swap_that_buys_no_exposure_has_no_ratio() -> None:
    with pytest.raises(ZeroDivisionError, match="no exposure"):
        tracking_error_per_unit_exposure(a_tilt(fund_hml_loading=-0.0252))


# --------------------------------------------------------------------------------
# The alpha charge
# --------------------------------------------------------------------------------


def test_the_alpha_charge_worked_on_paper() -> None:
    """DFIV: -4.111 against a +0.311 pedestal and a 3.521 floor, charged at 8%.

    ``0.08 * (-4.111 - 0.311) = -0.35376`` percent per year, which is -35.376 basis
    points, taking a +27.132 bp edge to **-8.244**.
    """
    charged = alpha_charged_edge(
        weight=0.08,
        portfolio_edge_basis_points=27.132,
        fund_alpha=-4.111,
        benchmark_alpha=0.311,
        alpha_mde80=3.521,
    )
    assert charged == pytest.approx(27.132 + 0.08 * (-4.111 - 0.311) * 100.0)
    assert charged == pytest.approx(-8.244, abs=1e-3)


def test_an_unmeasurable_alpha_is_neither_charged_nor_credited() -> None:
    """IVLU: -2.532 against a 2.632 floor. Below it, so the edge is returned unchanged."""
    assert alpha_charged_edge(
        weight=0.08,
        portfolio_edge_basis_points=19.417,
        fund_alpha=-2.532,
        benchmark_alpha=0.311,
        alpha_mde80=2.632,
    ) == pytest.approx(19.417)


def test_a_positive_alpha_is_never_credited() -> None:
    """AVDV's +2.472 exceeds nothing it is tested against, and would not count if it did.

    Paying a fund for skill is how a shelf audit turns into manager selection, so the
    charge is one-directional by construction: a fund whose alpha clears its floor **and**
    is positive still gets its edge back unchanged.
    """
    assert alpha_charged_edge(
        weight=0.08,
        portfolio_edge_basis_points=16.124,
        fund_alpha=2.472,
        benchmark_alpha=0.311,
        alpha_mde80=3.960,
    ) == pytest.approx(16.124)
    assert alpha_charged_edge(
        weight=0.08,
        portfolio_edge_basis_points=16.124,
        fund_alpha=9.0,
        benchmark_alpha=0.311,
        alpha_mde80=3.960,
    ) == pytest.approx(16.124)


def test_the_pedestal_and_not_zero_is_what_the_alpha_is_measured_from() -> None:
    """A fund matching the comparator's own model misfit is charged nothing at all."""
    assert alpha_charged_edge(
        weight=0.08,
        portfolio_edge_basis_points=20.0,
        fund_alpha=-4.0,
        benchmark_alpha=-4.0,
        alpha_mde80=1.0,
    ) == pytest.approx(20.0)


# --------------------------------------------------------------------------------
# The premium cell, whose detection floor decides every signability verdict
# --------------------------------------------------------------------------------


def test_premium_cell_detection_floor_from_the_normal_quantiles() -> None:
    """The floor rebuilt from ``(z_0.95 + z_0.80) * se``, with no call to the function.

    A deterministic 480-month series stands in for a factor: its mean and standard
    deviation are computed here with ``numpy`` alone, annualised by 12 and by 100, and
    the floor follows from the two quantiles written at the top of this file.
    """
    months = 480
    series = np.sin(np.arange(months, dtype=np.float64)) * 0.02 + 0.0025
    evidence, diagnostics = premium_cell(
        series, label="synthetic", panel="none", window="synthetic"
    )
    assert evidence.months == months
    assert evidence.point == pytest.approx(float(series.mean()) * 1200.0)
    standard_error = float(series.std(ddof=1)) * 100.0 / math.sqrt(months)
    assert evidence.mde80 == pytest.approx(
        12.0 * (Z_ONE_SIDED_95 + Z_POWER_80) * standard_error
    )
    assert diagnostics["volatility"] == pytest.approx(
        float(series.std(ddof=1)) * math.sqrt(12.0) * 100.0
    )
    assert evidence.low < evidence.point < evidence.high


def test_premium_cell_is_deterministic() -> None:
    """The bootstrap is seeded, so two calls on the same input agree exactly."""
    series = np.cos(np.arange(300, dtype=np.float64)) * 0.03
    first, _ = premium_cell(series, label="a", panel="none", window="w")
    second, _ = premium_cell(series, label="a", panel="none", window="w")
    assert (first.low, first.high) == (second.low, second.high)
