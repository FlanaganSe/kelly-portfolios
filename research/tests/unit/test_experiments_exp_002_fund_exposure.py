"""Experiment 002: the arithmetic that decides whether an alpha means anything.

Two of these tests exist because getting them wrong manufactures skill rather
than destroying it, which makes them the errors least likely to be noticed:

* an annual alpha is TWELVE times a monthly intercept, so its standard error
  annualises by ``x12`` and never by ``sqrt(12)``;
* the shrinkage factor must come from each fund's OWN standard error.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from portfolio_edge.data.nport import FrameRow
from portfolio_edge.experiments.exp_002_fund_exposure import (
    FACTOR_SPECIFICATIONS,
    PRIMARY_SPECIFICATION,
    _bootstrap_coefficients,
    fit_exposure,
    minimum_detectable_alpha,
    replicating_weights,
    shrink_alpha,
)
from portfolio_edge.experiments.exp_002_universe import ProductFacts, ScreenedFund, screen_frame

MONTHS_PER_YEAR = 12


# --------------------------------------------------------------------------- #
# Shrinkage
# --------------------------------------------------------------------------- #


def test_the_frameworks_reference_shrinkage_fixture_reproduces_exactly() -> None:
    """1.25^2 / (1.25^2 + 3.36^2) = 0.1216, computed by hand, not by this code.

    1.25^2 = 1.5625; 3.36^2 = 11.2896; 1.5625 / 12.8521 = 0.12157... The research
    framework rounds it to 0.121 and states that an observed 5%/yr alpha implies a
    posterior near 0.6%/yr. Both are checked here.
    """
    posterior, factor = shrink_alpha(5.0, 3.36, dispersion_annual_percent=1.25)
    assert factor == pytest.approx(1.5625 / 12.8521, rel=1e-12)
    assert factor == pytest.approx(0.121, abs=0.001)
    assert posterior == pytest.approx(0.6079, abs=0.001)


def test_the_annualisation_trap_changes_the_answer_by_a_factor_of_three() -> None:
    """Annualising the standard error by sqrt(12) instead of 12 shrinks far too little.

    A monthly standard error of 0.28% is 3.36%/yr under the correct ``x12`` rule
    and only 0.970%/yr under the wrong ``sqrt(12)`` one. The wrong rule leaves a
    5%/yr observed alpha at 3.1%/yr instead of 0.6%/yr -- five times too large, in
    the direction that invents manager skill.
    """
    monthly_se = 0.28
    correct = monthly_se * MONTHS_PER_YEAR
    wrong = monthly_se * math.sqrt(MONTHS_PER_YEAR)
    assert correct == pytest.approx(3.36)
    assert wrong == pytest.approx(0.96995, abs=1e-4)

    right_posterior, right_factor = shrink_alpha(5.0, correct, dispersion_annual_percent=1.25)
    wrong_posterior, wrong_factor = shrink_alpha(5.0, wrong, dispersion_annual_percent=1.25)
    assert right_posterior == pytest.approx(0.608, abs=0.005)
    assert wrong_posterior == pytest.approx(3.121, abs=0.005)
    assert wrong_factor > 5.0 * right_factor


def test_shrinkage_is_monotone_and_bounded() -> None:
    """More precision means less shrinkage; the factor never leaves (0, 1)."""
    previous = 1.1
    for standard_error in (0.1, 0.5, 1.25, 3.36, 10.0, 50.0):
        _, factor = shrink_alpha(4.0, standard_error, dispersion_annual_percent=1.25)
        assert 0.0 < factor < 1.0
        assert factor < previous
        previous = factor


def test_a_zero_standard_error_leaves_the_estimate_alone() -> None:
    posterior, factor = shrink_alpha(4.0, 0.0, dispersion_annual_percent=1.25)
    assert factor == pytest.approx(1.0)
    assert posterior == pytest.approx(4.0)


def test_shrinkage_preserves_sign_and_never_overshoots_zero() -> None:
    posterior, _ = shrink_alpha(-8.0, 3.36, dispersion_annual_percent=1.25)
    assert -8.0 < posterior < 0.0


def test_a_non_positive_prior_is_refused() -> None:
    with pytest.raises(ValueError, match="dispersion_annual_percent"):
        shrink_alpha(1.0, 1.0, dispersion_annual_percent=0.0)


# --------------------------------------------------------------------------- #
# Power
# --------------------------------------------------------------------------- #


def test_the_minimum_detectable_effect_multiplier_is_2_8016() -> None:
    """``z_0.975 + z_0.80 = 1.959964 + 0.841621``, computed independently."""
    assert minimum_detectable_alpha(1.0, power=0.80) == pytest.approx(2.8015854, abs=1e-6)
    assert minimum_detectable_alpha(3.36, power=0.80) == pytest.approx(9.413, abs=1e-3)


def test_more_power_demands_a_larger_effect() -> None:
    assert minimum_detectable_alpha(1.0, power=0.95) > minimum_detectable_alpha(1.0, power=0.80)


def test_a_typical_72_month_standard_error_cannot_detect_a_plausible_alpha() -> None:
    """The whole reason this experiment expects `unresolved` on alpha.

    Against a 3.36%/yr standard error, only an alpha above 9.4%/yr would be found
    at 80% power. True cross-sectional dispersion is 1.25%/yr, so the window
    cannot see the effect it is looking for by a factor of about seven.
    """
    assert minimum_detectable_alpha(3.36) > 7.0 * 1.25


# --------------------------------------------------------------------------- #
# Replication by cheap broad funds
# --------------------------------------------------------------------------- #


def test_an_exact_combination_is_recovered_exactly() -> None:
    rng = np.random.default_rng(7)
    basis = rng.normal(size=(240, 3))
    truth = np.array([0.5, 0.2, 0.3])
    weights = replicating_weights(basis @ truth, basis)
    assert weights == pytest.approx(truth, abs=1e-6)


def test_weights_are_long_only_and_fully_invested() -> None:
    """The comparator has to be a portfolio someone could hold."""
    rng = np.random.default_rng(11)
    basis = rng.normal(size=(120, 4))
    # A target that a least-squares fit would want to short.
    target = basis @ np.array([1.6, -0.4, -0.1, -0.1])
    weights = replicating_weights(target, basis)
    assert np.all(weights >= -1e-9)
    assert float(weights.sum()) == pytest.approx(1.0, abs=1e-8)


def test_a_mismatched_basis_is_refused() -> None:
    with pytest.raises(ValueError, match="does not match"):
        replicating_weights(np.zeros(10), np.zeros((9, 2)))


# --------------------------------------------------------------------------- #
# The regression
# --------------------------------------------------------------------------- #


def _synthetic(
    alpha_monthly: float, betas: dict[str, float], n: int = 72, seed: int = 3
) -> tuple[NDArray[np.float64], NDArray[np.float64], tuple[str, ...]]:
    rng = np.random.default_rng(seed)
    names = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    design = rng.normal(scale=0.04, size=(n, len(names)))
    y = alpha_monthly + design @ np.array([betas[name] for name in names])
    y = y + rng.normal(scale=0.002, size=n)
    return y, design, names


def test_loadings_and_the_annualised_alpha_are_recovered_from_a_known_process() -> None:
    betas = {"Mkt-RF": 0.98, "SMB": 0.35, "HML": 0.45, "RMW": 0.10, "CMA": -0.05, "UMD": 0.02}
    y, design, names = _synthetic(0.0015, betas)
    fit = fit_exposure(
        ticker="TEST",
        specification=PRIMARY_SPECIFICATION,
        era="common_period",
        excess_returns=y,
        design=design,
        factor_names=names,
        n_lags=6,
        dispersion_annual_percent=1.25,
        power=0.80,
    )
    for name, value in betas.items():
        assert fit.loadings[name] == pytest.approx(value, abs=0.02)
    # 0.0015 per month is 1.8% per year: twelve times, not sqrt(12) times.
    assert fit.alpha_annual_percent == pytest.approx(1.8, abs=0.15)
    assert fit.n_observations == 72
    assert fit.n_lags == 6
    assert 0.0 <= fit.r_squared <= 1.0


def test_the_reported_alpha_standard_error_is_twelve_times_the_monthly_one() -> None:
    """Asserted against the HAC estimator directly, not against this function."""
    from portfolio_edge.inference.hac import hac_ols

    betas = dict.fromkeys(FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION], 0.5)
    y, design, names = _synthetic(0.001, betas)
    fit = fit_exposure(
        ticker="TEST",
        specification=PRIMARY_SPECIFICATION,
        era="common_period",
        excess_returns=y,
        design=design,
        factor_names=names,
        n_lags=6,
        dispersion_annual_percent=1.25,
        power=0.80,
    )
    direct = hac_ols(y, design, n_lags=6)
    assert fit.alpha_se_annual_percent == pytest.approx(
        float(direct.standard_errors[0]) * 12.0 * 100.0, rel=1e-12
    )
    assert fit.alpha_annual_percent == pytest.approx(
        float(direct.coefficients[0]) * 12.0 * 100.0, rel=1e-12
    )


def test_the_shrunk_alpha_uses_this_funds_own_standard_error() -> None:
    betas = dict.fromkeys(FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION], 0.5)
    y, design, names = _synthetic(0.004, betas)
    fit = fit_exposure(
        ticker="TEST",
        specification=PRIMARY_SPECIFICATION,
        era="common_period",
        excess_returns=y,
        design=design,
        factor_names=names,
        n_lags=6,
        dispersion_annual_percent=1.25,
        power=0.80,
    )
    expected, factor = shrink_alpha(
        fit.alpha_annual_percent, fit.alpha_se_annual_percent, dispersion_annual_percent=1.25
    )
    assert fit.shrunk_alpha_annual_percent == pytest.approx(expected, rel=1e-12)
    assert fit.shrinkage_factor == pytest.approx(factor, rel=1e-12)
    assert fit.minimum_detectable_alpha_percent == pytest.approx(
        minimum_detectable_alpha(fit.alpha_se_annual_percent, power=0.80), rel=1e-12
    )


def test_batched_bootstrap_coefficients_agree_with_a_plain_least_squares_fit() -> None:
    rng = np.random.default_rng(19)
    y = rng.normal(size=90)
    design = np.column_stack([np.ones(90), rng.normal(size=(90, 3))])
    indices = rng.integers(0, 90, size=(25, 90)).astype(np.intp)
    batched = _bootstrap_coefficients(y, design, indices)
    for row in range(25):
        rows = indices[row]
        expected, *_ = np.linalg.lstsq(design[rows], y[rows], rcond=None)
        assert batched[row] == pytest.approx(expected, abs=1e-8)


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


def _row(series_id: str, name: str, assets: float | None) -> FrameRow:
    return FrameRow(
        accession="a",
        series_id=series_id,
        series_name=name,
        report_date="2019-09-30",
        net_assets=assets,
        is_last_filing=False,
    )


def _facts(ticker: str, expense: float | None, inception: str, mandate: str) -> ProductFacts:
    return ProductFacts(
        ticker=ticker,
        net_expense_ratio_percent=expense,
        gross_expense_ratio_percent=expense,
        inception_date=inception,
        index_name="Index",
        index_provider="Provider",
        stated_mandate=mandate,
        source_url="https://example.invalid",
        date_read="2026-08-12",
    )


MANDATE = r"\b(value|growth|momentum|quality|small[- ]?cap)\b"
EXCLUSION = r"\b(bond|international|leveraged)\b"
FACTOR_MAP = {"value": ("HML", 1), "growth": ("HML", -1), "momentum": ("UMD", 1)}


def _screen(
    frame: dict[str, FrameRow],
    follow_up: dict[str, FrameRow],
    tickers: dict[str, list[tuple[str, str]]],
    flags: dict[str, tuple[bool, str]],
    facts: dict[str, ProductFacts],
) -> tuple[tuple[ScreenedFund, ...], int]:
    return screen_frame(
        frame=frame,
        follow_up=follow_up,
        class_tickers=tickers,
        exchange_flags=flags,
        facts=facts,
        mandate_pattern=MANDATE,
        exclusion_pattern=EXCLUSION,
        minimum_net_assets=1e9,
        maximum_expense_ratio=0.60,
        inception_on_or_before="2016-12-31",
        intended_factor_map=FACTOR_MAP,
    )


def test_a_fund_records_the_first_criterion_it_failed_not_an_arbitrary_one() -> None:
    """Order matters: a tiny international bond fund must fail on the mandate, not size."""
    frame = {"S1": _row("S1", "Acme International Value Bond Fund", 5.0)}
    screened, matches = _screen(frame, {}, {}, {}, {})
    assert matches == 1
    assert len(screened) == 1
    assert screened[0].failed_criterion == "exclusion_regex"


def test_every_mandate_matching_fund_is_recorded_including_the_rejections() -> None:
    """The multiple-testing denominator is the whole screen, so nothing is dropped."""
    frame = {
        "S1": _row("S1", "Big Value ETF", 5e9),
        "S2": _row("S2", "Small Value ETF", 1e8),
        "S3": _row("S3", "Leveraged Value ETF", 5e9),
        "S4": _row("S4", "Unlisted Value Fund", 5e9),
        "S5": _row("S5", "Core Bond Fund", 5e9),
    }
    tickers = {"S1": [("C1", "BIG")], "S2": [("C2", "SML")], "S3": [("C3", "LEV")]}
    flags = {"BIG": (True, "Big Value ETF"), "SML": (True, "Small"), "LEV": (True, "Lev")}
    facts = {
        "BIG": _facts("BIG", 0.15, "2013-01-01", "value"),
        "SML": _facts("SML", 0.15, "2013-01-01", "value"),
    }
    screened, matches = _screen(frame, {}, tickers, flags, facts)
    # "Core Bond Fund" never matched the mandate pattern, so it is not a rejection.
    assert matches == 4
    outcomes = {fund.series_name: fund.failed_criterion for fund in screened}
    assert outcomes["Big Value ETF"] is None
    assert outcomes["Small Value ETF"] == "minimum_net_assets"
    assert outcomes["Leveraged Value ETF"] == "exclusion_regex"
    assert outcomes["Unlisted Value Fund"] == "exchange_traded"


def test_an_unverified_expense_ratio_fails_the_screen_rather_than_passing_by_default() -> None:
    frame = {"S1": _row("S1", "Big Value ETF", 5e9)}
    tickers = {"S1": [("C1", "BIG")]}
    flags = {"BIG": (True, "Big Value ETF")}
    screened, _ = _screen(frame, {}, tickers, flags, {})
    assert screened[0].failed_criterion == "maximum_expense_ratio"
    assert "no net expense ratio was verified" in screened[0].failure_detail

    screened, _ = _screen(
        frame, {}, tickers, flags, {"BIG": _facts("BIG", 0.75, "2013-01-01", "value")}
    )
    assert screened[0].failed_criterion == "maximum_expense_ratio"

    screened, _ = _screen(
        frame, {}, tickers, flags, {"BIG": _facts("BIG", 0.15, "2018-01-01", "value")}
    )
    assert screened[0].failed_criterion == "inception_cutoff"


def test_a_growth_mandate_is_graded_on_a_negative_value_loading() -> None:
    """Growth is the short leg of value, not an independent factor."""
    frame = {"S1": _row("S1", "Big Growth ETF", 5e9)}
    tickers = {"S1": [("C1", "GRW")]}
    flags = {"GRW": (True, "Big Growth ETF")}
    facts = {"GRW": _facts("GRW", 0.04, "2004-01-01", "growth")}
    screened, _ = _screen(frame, {}, tickers, flags, facts)
    assert screened[0].passed is True
    assert screened[0].intended_factor == "HML"
    assert screened[0].intended_sign == -1


def test_a_mandate_outside_the_predeclared_map_cannot_slip_through_ungraded() -> None:
    frame = {"S1": _row("S1", "Big Quality ETF", 5e9)}
    tickers = {"S1": [("C1", "QLT")]}
    flags = {"QLT": (True, "Big Quality ETF")}
    facts = {"QLT": _facts("QLT", 0.15, "2013-01-01", "quality")}
    screened, _ = _screen(frame, {}, tickers, flags, facts)
    assert screened[0].passed is False
    assert "intended-factor map" in screened[0].failure_detail


def test_attrition_is_visible_because_the_frame_is_taken_at_the_start() -> None:
    """A fund present in 2019 and absent later is recorded, not silently dropped."""
    frame = {
        "S1": _row("S1", "Survivor Value ETF", 5e9),
        "S2": _row("S2", "Departed Value ETF", 2e9),
    }
    follow_up = {"S1": _row("S1", "Survivor Value ETF", 7e9)}
    tickers = {"S1": [("C1", "SUR")], "S2": [("C2", "DEP")]}
    flags = {"SUR": (True, "Survivor"), "DEP": (True, "Departed")}
    facts = {
        "SUR": _facts("SUR", 0.10, "2010-01-01", "value"),
        "DEP": _facts("DEP", 0.10, "2010-01-01", "value"),
    }
    screened, _ = _screen(frame, follow_up, tickers, flags, facts)
    by_ticker = {fund.ticker: fund for fund in screened}
    assert by_ticker["SUR"].still_filing_at_follow_up is True
    assert by_ticker["DEP"].still_filing_at_follow_up is False
    assert by_ticker["DEP"].passed is True, (
        "a fund that later died still passed the screen at the frame date; "
        "excluding it here would be exactly the survivorship bias being measured"
    )


# --------------------------------------------------------------------------- #
# The multiple-testing denominator
# --------------------------------------------------------------------------- #


def test_widening_the_denominator_can_only_remove_rejections() -> None:
    """Padding with p = 1 is conservative by construction; it must never add one."""
    from portfolio_edge.experiments.exp_002_fund_exposure import inflated_family

    observed = [0.001, 0.004, 0.02, 0.3, 0.7]
    narrow = inflated_family(observed, family_size=len(observed))
    wide = inflated_family(observed, family_size=300)
    assert narrow["tests_actually_run"] == 5
    assert wide["padded_with_p_equal_one"] == 295
    assert int(str(wide["rejected_benjamini_hochberg"])) <= int(
        str(narrow["rejected_benjamini_hochberg"])
    )
    assert int(str(wide["rejected_holm_bonferroni"])) <= int(
        str(narrow["rejected_holm_bonferroni"])
    )


def test_holm_never_rejects_more_than_benjamini_hochberg() -> None:
    """Holm controls the family-wise rate and is valid under arbitrary dependence."""
    from portfolio_edge.experiments.exp_002_fund_exposure import inflated_family

    result = inflated_family([0.001, 0.01, 0.03, 0.06, 0.2], family_size=5)
    assert int(str(result["rejected_holm_bonferroni"])) <= int(
        str(result["rejected_benjamini_hochberg"])
    )


def test_a_family_smaller_than_the_tests_run_is_refused() -> None:
    from portfolio_edge.experiments.exp_002_fund_exposure import inflated_family

    with pytest.raises(ValueError, match="smaller than"):
        inflated_family([0.1, 0.2, 0.3], family_size=2)


# --------------------------------------------------------------------------- #
# The model-misfit pedestal
# --------------------------------------------------------------------------- #


def test_a_fund_that_is_the_market_has_an_alpha_of_about_zero_by_construction() -> None:
    """The calibration every other alpha is read against.

    A portfolio whose excess return IS the market factor must price at alpha zero
    under any model containing that factor. If this ever fails, the fund alphas
    are measuring the data path rather than the funds.
    """
    from portfolio_edge.inference.hac import hac_ols

    rng = np.random.default_rng(23)
    names = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    design = rng.normal(scale=0.04, size=(72, len(names)))
    market_only = design[:, 0].copy()
    fit = hac_ols(market_only, design, n_lags=6)
    assert float(fit.coefficients[0]) * 12 * 100 == pytest.approx(0.0, abs=1e-8)
    assert float(fit.coefficients[1]) == pytest.approx(1.0, abs=1e-8)


def test_a_pedestal_shifts_every_alpha_by_the_same_amount() -> None:
    """Why the pedestal is subtracted from all funds or from none.

    Adding a constant to every fund's monthly return moves every intercept by
    twelve times that constant and leaves every loading untouched, so a shared
    model misfit is a common shift and not a per-fund effect.
    """
    betas = dict.fromkeys(FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION], 0.4)
    y, design, names = _synthetic(0.001, betas)
    shift = 0.0005
    base = fit_exposure(
        ticker="A", specification=PRIMARY_SPECIFICATION, era="common_period",
        excess_returns=y, design=design, factor_names=names, n_lags=6,
        dispersion_annual_percent=1.25, power=0.80,
    )
    shifted = fit_exposure(
        ticker="B", specification=PRIMARY_SPECIFICATION, era="common_period",
        excess_returns=y + shift, design=design, factor_names=names, n_lags=6,
        dispersion_annual_percent=1.25, power=0.80,
    )
    assert shifted.alpha_annual_percent - base.alpha_annual_percent == pytest.approx(
        shift * 12 * 100, rel=1e-10
    )
    for name in names:
        assert shifted.loadings[name] == pytest.approx(base.loadings[name], abs=1e-12)
