"""The value-tilt arithmetic, against fixtures computed independently of it.

Three of the expectations below are computed without calling the module under test:
:func:`test_capture_identity_against_hand_arithmetic` works identity (C) out on paper,
:func:`test_capture_identity_holds_for_an_independent_least_squares_fit` fits an OLS with
``numpy.linalg.lstsq`` rather than with anything in this repository and checks the
identity against the realised ratio, and
:func:`test_the_superseded_chain_and_the_corrected_one` re-derives both the published
15.2 bp figure and its replacement from their stated inputs. A fixture that disagrees
with the implementation is a finding, not a tolerance to loosen.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.value_tilt import (
    CaptureDoubleCountError,
    TiltInputs,
    capture_from_regression,
    certainty_equivalent_contribution,
    marginal_growth_contribution,
    portfolio_tracking_error,
    sleeve_edge,
    substitution_variance_change,
    terminal_wealth_multiple,
    tilt_verdict,
    turnover_cost_percent,
    variance_drag,
)


def a_tilt(**overrides: float) -> TiltInputs:
    """AVUV against VTI on Experiment 013's window, unless a field is overridden."""
    fields: dict[str, float] = {
        "weight": 0.20,
        "fund_hml_loading": 0.536759,
        "benchmark_hml_loading": 0.024697,
        "hml_premium": 4.74,
        "fund_fee": 0.25,
        "benchmark_fee": 0.03,
        "fund_turnover_percent": 6.0,
        "benchmark_turnover_percent": 3.0,
        "turnover_coefficient": 1.7,
        "fund_volatility": 26.9562,
        "benchmark_volatility": 17.7483,
        "correlation": 0.8346,
    }
    fields.update(overrides)
    return TiltInputs(**fields)


# --------------------------------------------------------------------------------
# Identity (C): a capture fraction is a loading plus a residue
# --------------------------------------------------------------------------------


def test_capture_identity_against_hand_arithmetic() -> None:
    """Worked on paper: a spread loading 0.5 on HML whose ratio reads 0.85.

    ``excess = 0.3 + 0.5*4.0 + 0.2*2.0 + 0.1*7.0 = 3.4`` and ``3.4 / 4.0 = 0.85``.
    The residue is ``0.85 - 0.5 = 0.35``, of which ``0.3/4 = 0.075`` is alpha and
    ``(0.4 + 0.7)/4 = 0.275`` is the other factors.
    """
    decomposition = capture_from_regression(
        hml_loading=0.5,
        alpha=0.3,
        other_loadings={"SMB": 0.2, "Mkt-RF": 0.1},
        factor_means={"SMB": 2.0, "Mkt-RF": 7.0, "HML": 4.0},
        hml_premium=4.0,
    )
    assert decomposition.long_only_excess == pytest.approx(3.4)
    assert decomposition.capture == pytest.approx(0.85)
    assert decomposition.hml_loading == pytest.approx(0.5)
    assert decomposition.residue == pytest.approx(0.35)
    assert decomposition.alpha_contribution == pytest.approx(0.075)
    assert decomposition.other_factor_contribution == pytest.approx(0.275)
    assert decomposition.share_that_is_exposure() == pytest.approx(0.5 / 0.85)


def test_capture_identity_holds_for_an_independent_least_squares_fit() -> None:
    """The algebraic claim, not the arithmetic: fit an OLS here and reproduce the ratio.

    The fit uses ``numpy.linalg.lstsq`` rather than ``inference.hac``, so nothing in this
    repository is checked against itself. Because OLS residuals have zero mean by
    construction, ``mean(spread) / mean(HML)`` must equal ``h + residue`` exactly — which
    is the whole reason a capture fraction may not multiply a loading.
    """
    rng = np.random.default_rng(20260817)
    months = 720
    market = rng.normal(0.0060, 0.045, months)
    size = rng.normal(0.0018, 0.030, months)
    hml = rng.normal(0.0029, 0.030, months)
    noise = rng.normal(0.0, 0.010, months)
    spread = 0.0012 + 0.489 * hml + 0.022 * size + 0.018 * market + noise

    design = np.column_stack([np.ones(months), market, size, hml])
    coefficients, *_ = np.linalg.lstsq(design, spread, rcond=None)
    intercept, market_beta, size_beta, hml_beta = (float(value) for value in coefficients)

    scale = 1200.0
    decomposition = capture_from_regression(
        hml_loading=hml_beta,
        alpha=intercept * scale,
        other_loadings={"Mkt-RF": market_beta, "SMB": size_beta},
        factor_means={
            "Mkt-RF": float(market.mean()) * scale,
            "SMB": float(size.mean()) * scale,
        },
        hml_premium=float(hml.mean()) * scale,
    )
    realised_ratio = float(spread.mean()) / float(hml.mean())
    assert decomposition.capture == pytest.approx(realised_ratio, rel=1e-10)
    assert decomposition.hml_loading == pytest.approx(hml_beta)
    assert decomposition.capture != pytest.approx(decomposition.hml_loading, abs=1e-6)


def test_capture_is_undefined_when_the_premium_is_zero() -> None:
    with pytest.raises(ZeroDivisionError, match="no value"):
        capture_from_regression(
            hml_loading=0.5,
            alpha=0.0,
            other_loadings={},
            factor_means={},
            hml_premium=0.0,
        )


def test_hml_may_not_appear_twice() -> None:
    with pytest.raises(ValueError, match="pass it as hml_loading"):
        capture_from_regression(
            hml_loading=0.5,
            alpha=0.0,
            other_loadings={"HML": 0.1},
            factor_means={"HML": 4.0},
            hml_premium=4.0,
        )


def test_a_missing_factor_mean_is_refused_rather_than_dropped() -> None:
    with pytest.raises(ValueError, match="no mean supplied for SMB"):
        capture_from_regression(
            hml_loading=0.5,
            alpha=0.0,
            other_loadings={"SMB": 0.2},
            factor_means={"HML": 4.0},
            hml_premium=4.0,
        )


# --------------------------------------------------------------------------------
# The refusal that is the point of the module
# --------------------------------------------------------------------------------


def test_a_capture_fraction_may_not_multiply_a_loading() -> None:
    with pytest.raises(CaptureDoubleCountError, match=r"0\.52"):
        sleeve_edge(a_tilt(), capture=0.52)


# --------------------------------------------------------------------------------
# The tilt
# --------------------------------------------------------------------------------


def test_turnover_cost_is_k_times_turnover_in_basis_points() -> None:
    """``1.7 * 6`` is 10.2 bp, which is 0.102 percent per year."""
    assert turnover_cost_percent(
        one_sided_turnover_percent=6.0, coefficient=1.7
    ) == pytest.approx(0.102)
    assert turnover_cost_percent(
        one_sided_turnover_percent=0.0, coefficient=1.7
    ) == pytest.approx(0.0)


def test_costs_are_charged_incrementally_over_the_incumbent() -> None:
    """``(0.25 - 0.03) + 1.7 * (6 - 3) / 100 = 0.22 + 0.051 = 0.271``."""
    assert a_tilt().incremental_cost == pytest.approx(0.271)


def test_delivered_loading_subtracts_the_incumbent_exposure() -> None:
    assert a_tilt().delivered_loading == pytest.approx(0.512062)


def test_the_superseded_chain_and_the_corrected_one() -> None:
    """Both figures re-derived from their inputs, so neither can drift unnoticed.

    Superseded: ``0.20 * 0.410 * 0.520 * 4.74 - 0.20 * 0.25`` percent per year, which is
    the 15.2 bp ``portfolio-recommendation.md`` §5 published. Corrected: the same weight
    and premium with VBR's loading replaced by AVUV's *delivered* loading, no capture
    term, and cost charged incrementally over VTI.
    """
    superseded = (0.20 * 0.410 * 0.520 * 4.74 - 0.20 * 0.25) / 0.01
    assert superseded == pytest.approx(15.2113, abs=1e-4)

    corrected = 0.20 * ((0.536759 - 0.024697) * 4.74 - 0.271) / 0.01
    assert corrected == pytest.approx(43.1235, abs=1e-4)
    assert tilt_verdict(a_tilt()).portfolio_edge_basis_points == pytest.approx(
        corrected, abs=1e-9
    )
    assert corrected / superseded == pytest.approx(2.834, abs=1e-3)


def test_the_edge_and_the_tracking_error_are_both_linear_in_weight() -> None:
    """So the probability of outperformance does not depend on the weight at all."""
    small = tilt_verdict(a_tilt(weight=0.10))
    large = tilt_verdict(a_tilt(weight=0.30))
    assert large.portfolio_edge_basis_points == pytest.approx(
        3.0 * small.portfolio_edge_basis_points
    )
    assert large.portfolio_tracking_error_basis_points == pytest.approx(
        3.0 * small.portfolio_tracking_error_basis_points
    )


def test_sleeve_tracking_error_is_the_two_asset_identity() -> None:
    """``sqrt(26.9562**2 + 17.7483**2 - 2 * 0.8346 * 26.9562 * 17.7483)``."""
    expected = math.sqrt(
        26.9562**2 + 17.7483**2 - 2.0 * 0.8346 * 26.9562 * 17.7483
    )
    assert a_tilt().sleeve_tracking_error == pytest.approx(expected)
    assert expected == pytest.approx(15.5904, abs=1e-3)
    assert portfolio_tracking_error(a_tilt()) == pytest.approx(0.20 * expected)


def test_swapping_into_an_identical_fund_changes_no_variance() -> None:
    """A perfectly correlated fund of the same volatility is the same portfolio."""
    identical = a_tilt(fund_volatility=17.7483, correlation=1.0)
    assert substitution_variance_change(identical) == pytest.approx(0.0, abs=1e-9)
    assert identical.sleeve_tracking_error == pytest.approx(0.0, abs=1e-6)
    assert marginal_growth_contribution(identical) == pytest.approx(
        0.20 * sleeve_edge(identical)
    )


def test_substitution_variance_change_against_the_hand_computed_portfolio() -> None:
    """``V(0.2) - V(0)`` for 80% of a 17.7483 vol asset and 20% of a 26.9562 vol asset."""
    covariance = 0.8346 * 26.9562 * 17.7483
    tilted = (
        0.8**2 * 17.7483**2 + 2.0 * 0.2 * 0.8 * covariance + 0.2**2 * 26.9562**2
    )
    expected = tilted - 17.7483**2
    assert substitution_variance_change(a_tilt()) == pytest.approx(expected)
    assert expected == pytest.approx(43.44, abs=0.01)


def test_growth_and_the_certainty_equivalent_differ_only_by_gamma() -> None:
    """Decision 0008's whole point, expressed as an identity rather than as prose."""
    tilt = a_tilt()
    growth = marginal_growth_contribution(tilt)
    assert certainty_equivalent_contribution(tilt, gamma=1.0) == pytest.approx(growth)
    charge = variance_drag(tilt, gamma=1.0)
    assert certainty_equivalent_contribution(tilt, gamma=3.0) == pytest.approx(
        growth - 2.0 * charge
    )


def test_the_variance_drag_carries_the_percent_conversion() -> None:
    """``43.44 / 200`` is 0.2172 pp/yr, not 21.72. Dropping the 100 was the first bug."""
    assert variance_drag(a_tilt(), gamma=1.0) == pytest.approx(0.2174, abs=1e-3)


def test_growth_is_the_edge_less_the_variance_drag() -> None:
    """``0.20 * 2.15617 - 0.2174 = 0.2140`` percent per year."""
    assert marginal_growth_contribution(a_tilt()) == pytest.approx(0.2140, abs=1e-3)
    assert certainty_equivalent_contribution(a_tilt(), gamma=3.0) == pytest.approx(
        -0.2204, abs=1e-3
    )


def test_terminal_wealth_multiple_is_the_exponential_of_the_growth_rate() -> None:
    """``exp(0.2140 / 100 * 30) = 1.0663``."""
    assert terminal_wealth_multiple(
        growth_contribution=0.2140, years=30.0
    ) == pytest.approx(math.exp(0.002140 * 30.0))
    assert terminal_wealth_multiple(
        growth_contribution=0.2140, years=30.0
    ) == pytest.approx(1.0663, abs=1e-4)
    assert terminal_wealth_multiple(
        growth_contribution=5.0, years=0.0
    ) == pytest.approx(1.0)


def test_a_negative_premium_makes_every_figure_negative() -> None:
    """The US post-publication interval reaches -2.28, so this corner is live."""
    verdict = tilt_verdict(a_tilt(hml_premium=-2.28))
    assert verdict.portfolio_edge_basis_points < 0.0
    assert verdict.growth_contribution_percent < 0.0
    assert verdict.terminal_wealth_multiple_30y < 1.0


# --------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("weight", 1.4, "weight must lie"),
        ("weight", -0.1, "weight must lie"),
        ("fund_volatility", 0.0, "volatilities must be positive"),
        ("benchmark_volatility", -1.0, "volatilities must be positive"),
        ("correlation", 1.4, "correlation must lie"),
    ],
)
def test_impossible_inputs_are_refused(field: str, value: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        a_tilt(**{field: value})


def test_gamma_must_be_positive() -> None:
    with pytest.raises(ValueError, match="gamma must be positive"):
        certainty_equivalent_contribution(a_tilt(), gamma=0.0)


def test_a_negative_turnover_is_refused() -> None:
    with pytest.raises(ValueError, match="turnover cannot be negative"):
        turnover_cost_percent(one_sided_turnover_percent=-1.0, coefficient=1.7)
    with pytest.raises(ValueError, match="coefficient cannot be negative"):
        turnover_cost_percent(one_sided_turnover_percent=6.0, coefficient=-1.0)


def test_a_negative_horizon_is_refused() -> None:
    with pytest.raises(ValueError, match="years cannot be negative"):
        terminal_wealth_multiple(growth_contribution=0.2, years=-1.0)
