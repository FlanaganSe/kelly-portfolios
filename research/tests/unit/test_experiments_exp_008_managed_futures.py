"""Experiment 008: the arithmetic, the screen, and the clause (d) re-reading.

Offline. Nothing here downloads a filing or a factor file. Three things are pinned
because getting them wrong would leave every downstream number plausible:

* the annualisation of a tracking difference, which is ``x12`` on the mean and
  ``xsqrt(12)`` on the dispersion, and never the same factor on both;
* which criterion a screened fund fails first, because the funnel only adds up if
  the order is fixed;
* the two readings of Experiment 004's clause (d), including the opposite
  monotonicity in the size of the effect that decides which of them is defensible.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import ClassVar

import numpy as np
import pytest

from portfolio_edge.data.nport import FrameRow
from portfolio_edge.experiments.exp_002_universe import ProductFacts
from portfolio_edge.experiments.exp_008_managed_futures import (
    STATIC_SET_NAMES,
    ManagedFuturesError,
    ProductOutcome,
    TrackingFit,
    _marginal_certainty_equivalent,
    _static_design,
    _verdicts,
    clause_d_monotonicity,
    clause_d_readings,
    effective_independent_blocks,
    intended_exposure_map,
    tracking_difference,
)
from portfolio_edge.experiments.exp_008_universe import (
    CRITERION_ORDER,
    ScreenedProduct,
    screen_union_frame,
)
from portfolio_edge.experiments.specification import load_specification

SPEC = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "exp_008_managed_futures_products.yaml"
)


# --------------------------------------------------------------------------- #
# Tracking difference: the annualisation is the whole content
# --------------------------------------------------------------------------- #


def test_a_constant_monthly_gap_annualises_by_twelve_and_has_no_dispersion() -> None:
    """A fund one basis point behind every month is 12 bp behind a year.

    Computed independently of the implementation: 0.0001 * 12 * 100 = 0.12 pp/yr,
    with a tracking error of exactly zero because nothing varies.
    """
    benchmark = np.array([0.01, -0.02, 0.03, 0.00, 0.05, -0.01], dtype=np.float64)
    fund = benchmark - 0.0001
    difference, error = tracking_difference(fund, benchmark)
    assert difference == pytest.approx(-0.12)
    assert error == pytest.approx(0.0, abs=1e-12)


def test_the_dispersion_annualises_by_the_square_root_and_the_mean_does_not() -> None:
    """The two must not share a factor, and the fixture is computed by hand.

    Differences alternate -0.01 and +0.01 over eight months, so the mean is zero and
    the sample standard deviation is 0.01 * sqrt(8/7) = 0.0106904. Annualised: 0
    pp/yr on the mean, and 0.0106904 * sqrt(12) * 100 = 3.7032804 pp/yr on the
    dispersion. Using ``x12`` on the dispersion would print 12.83, and ``xsqrt(12)``
    on the mean would understate every shortfall by a factor of 3.46.
    """
    benchmark = np.zeros(8, dtype=np.float64)
    fund = np.array([-0.01, 0.01] * 4, dtype=np.float64)
    difference, error = tracking_difference(fund, benchmark)
    assert difference == pytest.approx(0.0, abs=1e-12)
    # The sample standard deviation carries ddof=1, so it is 0.01 * sqrt(8/7).
    assert error == pytest.approx(0.01 * math.sqrt(8.0 / 7.0) * math.sqrt(12.0) * 100.0)
    assert error == pytest.approx(3.703280399226616)


def test_a_tracking_difference_refuses_mismatched_or_degenerate_input() -> None:
    with pytest.raises(ValueError):
        tracking_difference(np.zeros(4), np.zeros(5))
    with pytest.raises(ValueError):
        tracking_difference(np.zeros(1), np.zeros(1))


def test_effective_blocks_is_months_over_the_block_length() -> None:
    assert effective_independent_blocks(78, 6.0) == pytest.approx(13.0)
    assert effective_independent_blocks(46, 6.0) == pytest.approx(46 / 6)
    with pytest.raises(ValueError):
        effective_independent_blocks(12, 0.0)


# --------------------------------------------------------------------------- #
# Experiment 004's decisive design, reproduced exactly
# --------------------------------------------------------------------------- #


def test_the_static_design_drops_the_lagged_row_and_keeps_experiment_004s_order() -> None:
    """A different column order would silently rename every coefficient."""
    market = np.array([0.01, -0.02, 0.03, 0.04], dtype=np.float64)
    scaled = np.array([0.10, 0.20, 0.30, 0.40], dtype=np.float64)
    design = _static_design(market, scaled)
    assert design.shape == (3, 4)
    assert len(STATIC_SET_NAMES) == design.shape[1]
    np.testing.assert_allclose(design[:, 0], market[1:])
    np.testing.assert_allclose(design[:, 1], scaled[1:])
    np.testing.assert_allclose(design[:, 2], np.abs(market[1:]))
    np.testing.assert_allclose(design[:, 3], market[:-1])


# --------------------------------------------------------------------------- #
# Clause (d), both readings
# --------------------------------------------------------------------------- #


def test_both_readings_on_experiment_004s_own_numbers_disagree() -> None:
    """The reason this experiment exists, pinned as a fixture.

    Experiment 004 ledgered a sleeve marginal of +1.3418 pp/yr and a replica
    marginal of +0.5862 against a 0.30 pp/yr threshold. Absolute: the replica clears
    the bar, so reject. Relative: the sleeve's margin over its replica is +0.7556,
    which also clears the bar, so the exposures have not explained the result.
    """
    absolute, relative = clause_d_readings(
        sleeve_marginal=1.341825315439782,
        replica_marginal=0.5862468980901259,
        materiality=0.30,
    )
    assert absolute.fires is True
    assert absolute.verdict == "rejected"
    assert relative.fires is False
    assert relative.verdict == "not-rejected"
    assert relative.quantity == pytest.approx(0.7555784173496561)


def test_the_two_readings_have_opposite_monotonicity_in_the_size_of_the_effect() -> None:
    """This is the argument for the relative reading, expressed as a test.

    Hold the SHARE the replica explains fixed at 44% -- Experiment 004's own figure --
    and scale the effect up. The share explained has not changed, so a clause about
    explanation should not change its mind. Both do, in opposite directions:

    * the ABSOLUTE reading goes from not-firing to firing as the sleeve gets better,
      because a bigger sleeve mechanically enlarges the fitted replica. A falsifier
      that is easier to trip the larger the effect is measuring size;
    * the RELATIVE reading goes from firing to not-firing, which is the right
      direction: a large unexplained residue has not been explained.

    Neither is scale-free, because both compare a level against an absolute bar.
    That is the specification lesson, and it is asserted here rather than only
    asserted in prose.
    """
    rows = clause_d_monotonicity(
        replica_share=0.44, materiality=0.30, scales=(0.5, 1.0, 5.0, 50.0)
    )
    assert [row["absolute_reading_fires"] for row in rows] == [False, True, True, True]
    assert [row["relative_reading_fires"] for row in rows] == [True, False, False, False]


def test_the_monotonicity_helper_refuses_a_share_outside_zero_to_one() -> None:
    with pytest.raises(ValueError):
        clause_d_monotonicity(replica_share=1.5, materiality=0.30, scales=(1.0,))


def test_a_replica_that_explains_almost_everything_fires_the_relative_reading() -> None:
    absolute, relative = clause_d_readings(
        sleeve_marginal=1.00, replica_marginal=0.95, materiality=0.30
    )
    assert absolute.fires is True
    assert relative.fires is True
    assert relative.verdict == "rejected"


def test_a_non_positive_materiality_is_refused() -> None:
    with pytest.raises(ValueError):
        clause_d_readings(sleeve_marginal=1.0, replica_marginal=0.5, materiality=0.0)


# --------------------------------------------------------------------------- #
# The frozen falsifier
# --------------------------------------------------------------------------- #


def _product(ticker: str, *, fee: float | None = 0.80) -> ScreenedProduct:
    return ScreenedProduct(
        ticker=ticker,
        series_id=f"S-{ticker}",
        class_id=f"C-{ticker}",
        series_name=f"{ticker} Managed Futures Strategy ETF",
        security_name=ticker,
        passed=True,
        failed_criterion=None,
        failure_detail="",
        net_assets_frame=None,
        net_assets_follow_up=5.0e8,
        net_assets_maximum=5.0e8,
        in_frame_quarter=False,
        in_follow_up_quarter=True,
        final_filing_flag_seen=False,
        exchange_listed_now=True,
        facts=ProductFacts(
            ticker=ticker,
            net_expense_ratio_percent=fee,
            gross_expense_ratio_percent=fee,
            inception_date="2020-01-01",
            index_name="",
            index_provider="",
            stated_mandate="diversified_managed_futures",
            source_url="https://example.invalid",
            date_read="2026-08-12",
        ),
        intended_target="aqr_tsmom",
    )


def _fit(
    ticker: str,
    *,
    loading: float,
    interval: tuple[float, float],
    first_half: float,
    second_half: float,
    tracking: float = 0.0,
) -> TrackingFit:
    return TrackingFit(
        ticker=ticker,
        n_observations=60,
        first_period="2021-01",
        last_period="2025-12",
        loading=loading,
        loading_se=0.1,
        loading_t=loading / 0.1,
        loading_interval=interval,
        loading_intervals_by_block={"block_6": interval},
        alpha_annual_percent=0.0,
        alpha_se_annual_percent=4.0,
        alpha_p=0.5,
        shrunk_alpha_annual_percent=0.0,
        shrinkage_factor=0.09,
        minimum_detectable_alpha_percent=11.2,
        r_squared=0.5,
        correlation=0.7,
        raw_tracking_difference_percent=tracking,
        tracking_error_percent=10.0,
        first_half_loading=first_half,
        second_half_loading=second_half,
        rolling_minimum=loading,
        rolling_maximum=loading,
        rolling_sign_changes=0,
        rolling_windows=25,
    )


def _decide(fit: TrackingFit, *, fee: float | None = 0.80) -> ProductOutcome:
    product = _product(fit.ticker, fee=fee)
    return _verdicts(
        usable=[product],
        tracking={fit.ticker: fit},
        minimum_loading=0.50,
        stability_floor=0.50,
        tolerance=1.00,
    )[0]


def test_a_fund_that_delivers_the_exposure_stably_reaches_exploratory() -> None:
    outcome = _decide(
        _fit("AAA", loading=0.67, interval=(0.51, 0.83), first_half=0.59, second_half=0.73)
    )
    assert outcome.clauses_fired == []
    assert outcome.status == "exploratory"


def test_clause_a_fires_on_the_point_estimate_of_the_loading() -> None:
    outcome = _decide(
        _fit("BBB", loading=0.24, interval=(-0.15, 0.45), first_half=0.60, second_half=0.60)
    )
    assert outcome.status == "rejected"
    assert any(clause.startswith("(a)") for clause in outcome.clauses_fired)


def test_clause_b_fires_when_a_half_falls_below_the_stability_floor() -> None:
    outcome = _decide(
        _fit("CCC", loading=0.60, interval=(0.55, 0.70), first_half=0.30, second_half=0.85)
    )
    assert outcome.status == "rejected"
    assert any("stability floor" in clause for clause in outcome.clauses_fired)


def test_clause_b_reports_a_sign_flip_as_a_sign_flip_when_the_floor_is_negative() -> None:
    """Both limbs of clause (b) are reachable; the floor limb takes precedence."""
    outcome = _verdicts(
        usable=[_product("DDD")],
        tracking={
            "DDD": _fit(
                "DDD", loading=0.60, interval=(0.55, 0.70), first_half=-0.20, second_half=0.90
            )
        },
        minimum_loading=0.50,
        stability_floor=-1.00,
        tolerance=1.00,
    )[0]
    assert any("changes sign" in clause for clause in outcome.clauses_fired)


def test_clause_c_fires_only_when_the_shortfall_exceeds_the_fee_plus_the_tolerance() -> None:
    """A fund behind the index by its own fee has not failed anything.

    Trailing by 1.50 pp/yr on an 0.80% fee is a shortfall of 0.70, inside the 1.00
    tolerance. Trailing by 2.50 is a shortfall of 1.70 and fires.
    """
    inside = _decide(
        _fit(
            "EEE", loading=0.70, interval=(0.60, 0.80), first_half=0.70, second_half=0.70,
            tracking=-1.50,
        )
    )
    assert inside.clauses_fired == []
    outside = _decide(
        _fit(
            "FFF", loading=0.70, interval=(0.60, 0.80), first_half=0.70, second_half=0.70,
            tracking=-2.50,
        )
    )
    assert any(clause.startswith("(c)") for clause in outside.clauses_fired)


def test_an_interval_straddling_the_threshold_is_unresolved_not_a_pass() -> None:
    outcome = _decide(
        _fit("GGG", loading=0.55, interval=(0.40, 0.70), first_half=0.55, second_half=0.55)
    )
    assert outcome.status == "unresolved"
    assert any("contains the 0.50 threshold" in note for note in outcome.notes)


def test_an_uncovered_half_is_recorded_rather_than_extrapolated() -> None:
    outcome = _decide(
        _fit(
            "HHH", loading=0.70, interval=(0.60, 0.80),
            first_half=float("nan"), second_half=0.70,
        )
    )
    assert not any(clause.startswith("(b)") for clause in outcome.clauses_fired)
    assert any("does not cover both halves" in note for note in outcome.notes)


# --------------------------------------------------------------------------- #
# The marginal-contribution arm
# --------------------------------------------------------------------------- #


def test_the_marginal_arm_refuses_a_window_shorter_than_two_whole_years() -> None:
    n = 18
    block = _marginal_certainty_equivalent(
        sleeve_excess=np.zeros(n),
        equity_total=np.full(n, 0.005),
        cash=np.full(n, 0.001),
        gamma=3.0,
        sleeve_weight=0.15,
        equity_weight=0.60,
        centre_of_mass_months=60.0 / 21.0,
    )
    assert block["available"] is False


def test_a_sleeve_identical_to_cash_adds_nothing_once_the_estimator_is_warm() -> None:
    """The null case that proves the comparator is sized correctly.

    A zero-excess sleeve IS cash, so the treatment and the risk-matched comparator
    are the same portfolio and the marginal benefit must be zero. It is -- but only
    where the volatility estimator is warm. With a warm-up prefix the residue is
    numerical; without one the first year runs a fully invested comparator against a
    de-risked treatment and the arm reports a benefit that is an artefact. Both
    branches are asserted, because the second is the defect the ``reported_from``
    argument exists to expose.
    """
    rng = np.random.default_rng(7)
    warm_up, reported = 24, 48
    equity = 0.005 + 0.04 * rng.standard_normal(warm_up + reported)
    kwargs = {
        "sleeve_excess": np.zeros(warm_up + reported),
        "equity_total": equity,
        "cash": np.full(warm_up + reported, 0.002),
        "gamma": 3.0,
        "sleeve_weight": 0.15,
        "equity_weight": 0.60,
        "centre_of_mass_months": 60.0 / 21.0,
    }
    warm = _marginal_certainty_equivalent(**kwargs, reported_from=warm_up)  # type: ignore[arg-type]
    assert warm["available"] is True
    assert warm["whole_calendar_years"] == 4
    assert warm["months_in_the_window_with_an_unwarmed_estimator"] == 0
    assert warm["risk_match_holds"] is True
    value = warm["marginal_certainty_equivalent_percentage_points_per_year"]
    assert isinstance(value, float)
    assert value == pytest.approx(0.0, abs=1e-6)

    cold = _marginal_certainty_equivalent(**kwargs, reported_from=0)  # type: ignore[arg-type]
    assert cold["months_in_the_window_with_an_unwarmed_estimator"] == 12
    assert cold["risk_match_holds"] is False
    assert "NOT risk-matched" in str(cold["unwarmed_warning"])


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


def _row(series_id: str, name: str, assets: float | None) -> FrameRow:
    return FrameRow(
        accession=f"acc-{series_id}",
        series_id=series_id,
        series_name=name,
        report_date="2025-09-30",
        net_assets=assets,
        is_last_filing=False,
    )


def _facts(ticker: str, *, fee: float, inception: str, mandate: str) -> ProductFacts:
    return ProductFacts(
        ticker=ticker,
        net_expense_ratio_percent=fee,
        gross_expense_ratio_percent=fee,
        inception_date=inception,
        index_name="",
        index_provider="",
        stated_mandate=mandate,
        source_url="https://example.invalid",
        date_read="2026-08-12",
    )


def _screen(
    frame: dict[str, FrameRow],
    follow_up: dict[str, FrameRow],
    class_tickers: dict[str, list[tuple[str, str]]],
    exchange_flags: dict[str, tuple[bool, str]],
    facts: dict[str, ProductFacts],
) -> dict[str, ScreenedProduct]:
    screened, _ = screen_union_frame(
        frame=frame,
        follow_up=follow_up,
        class_tickers=class_tickers,
        exchange_flags=exchange_flags,
        facts=facts,
        mandate_pattern=r"\b(managed\s+futures|trend)\b",
        exclusion_pattern=r"\b(equit\w*|bond\w*)\b",
        minimum_net_assets=100_000_000.0,
        maximum_expense_ratio=1.50,
        inception_on_or_before="2022-12-31",
        intended_exposure_map={"diversified_managed_futures": "aqr_tsmom"},
    )
    return {item.series_id: item for item in screened}


def test_the_union_frame_admits_a_fund_that_launched_after_the_first_census() -> None:
    """The whole reason the frame is a union rather than a single quarter."""
    frame = {"S1": _row("S1", "Old Managed Futures ETF", 5.0e8)}
    follow_up = {
        "S1": _row("S1", "Old Managed Futures ETF", 4.0e8),
        "S2": _row("S2", "New Managed Futures ETF", 6.0e8),
    }
    out = _screen(
        frame,
        follow_up,
        {"S1": [("C1", "OLD")], "S2": [("C2", "NEW")]},
        {"OLD": (True, "Old"), "NEW": (True, "New")},
        {
            "OLD": _facts("OLD", fee=0.8, inception="2015-01-01",
                          mandate="diversified_managed_futures"),
            "NEW": _facts("NEW", fee=0.8, inception="2021-01-01",
                          mandate="diversified_managed_futures"),
        },
    )
    assert out["S2"].passed is True
    assert out["S2"].in_frame_quarter is False


def test_a_fund_that_died_inside_the_window_is_still_screened_and_recorded() -> None:
    """A single late frame would delete it; the union keeps it visible."""
    frame = {"S3": _row("S3", "Dead Managed Futures ETF", 9.0e8)}
    out = _screen(
        frame,
        {},
        {"S3": [("C3", "DEAD")]},
        {"DEAD": (True, "Dead")},
        {
            "DEAD": _facts("DEAD", fee=0.8, inception="2015-01-01",
                           mandate="diversified_managed_futures")
        },
    )
    assert out["S3"].in_follow_up_quarter is False
    assert out["S3"].passed is True


def test_the_asset_floor_uses_the_larger_of_the_two_census_observations() -> None:
    """A fund that reached the floor and then shrank is not selected out."""
    frame = {"S4": _row("S4", "Shrinking Trend ETF", 9.0e8)}
    follow_up = {"S4": _row("S4", "Shrinking Trend ETF", 1.0e7)}
    out = _screen(
        frame,
        follow_up,
        {"S4": [("C4", "SHR")]},
        {"SHR": (True, "Shr")},
        {
            "SHR": _facts("SHR", fee=0.8, inception="2015-01-01",
                          mandate="diversified_managed_futures")
        },
    )
    assert out["S4"].net_assets_maximum == pytest.approx(9.0e8)
    assert out["S4"].passed is True


def test_only_the_first_failing_criterion_is_recorded_and_the_order_is_fixed() -> None:
    """A sub-floor fund with no fee on file must fail on ASSETS, not on the fee.

    That ordering is what stops a gathering gap masquerading as a screen decision,
    which is the defect Experiment 002 had to repair mid-flight.
    """
    follow_up = {"S5": _row("S5", "Tiny Managed Futures ETF", 1.0e6)}
    out = _screen(
        {}, follow_up, {"S5": [("C5", "TIN")]}, {"TIN": (True, "Tin")}, {}
    )
    assert out["S5"].failed_criterion == "minimum_net_assets"
    assert CRITERION_ORDER.index("minimum_net_assets") < CRITERION_ORDER.index(
        "maximum_expense_ratio"
    )


def test_a_mutual_fund_fails_on_the_exchange_flag_not_on_its_mandate() -> None:
    follow_up = {"S6": _row("S6", "Big Managed Futures Fund", 4.0e9)}
    out = _screen(
        {},
        follow_up,
        {"S6": [("C6", "BIGFX")]},
        {},
        {},
    )
    assert out["S6"].failed_criterion == "exchange_traded"


def test_a_single_asset_class_trend_product_is_excluded_by_name() -> None:
    follow_up = {"S7": _row("S7", "Somebody Equity Trend ETF", 4.0e8)}
    out = _screen({}, follow_up, {"S7": [("C7", "EQT")]}, {"EQT": (True, "Eqt")}, {})
    assert out["S7"].failed_criterion == "exclusion_regex"


def test_a_mandate_outside_the_frozen_map_is_recorded_not_dropped() -> None:
    follow_up = {"S8": _row("S8", "Full Cycle Trend ETF", 4.0e8)}
    out = _screen(
        {},
        follow_up,
        {"S8": [("C8", "FCY")]},
        {"FCY": (True, "Fcy")},
        {
            "FCY": _facts(
                "FCY", fee=0.85, inception="2020-01-01",
                mandate="equity_and_gold_full_cycle_rotation",
            )
        },
    )
    assert out["S8"].failed_criterion == "mandate_in_map"
    assert out["S8"].passed is False


# --------------------------------------------------------------------------- #
# The frozen specification itself
# --------------------------------------------------------------------------- #


def test_the_frozen_specification_loads_and_declares_what_it_claims_to_be() -> None:
    specification = load_specification(SPEC)
    assert specification.entry_point == "exp_008_managed_futures_products"
    assert specification.run_kind.value == "exploratory"
    assert specification.evidence_class.value == "fund-implementation-audit"
    assert specification.consumes_final_holdout is False
    assert intended_exposure_map(specification) == {
        "diversified_managed_futures": "aqr_tsmom",
        "managed_futures_replication": "aqr_tsmom",
        "trend_following": "aqr_tsmom",
    }


def test_the_specification_refuses_a_missing_parameter_loudly() -> None:
    class Fake:
        universe: ClassVar[dict[str, object]] = {"intended_exposure_map": {}}

    with pytest.raises(ManagedFuturesError):
        intended_exposure_map(Fake())  # type: ignore[arg-type]
