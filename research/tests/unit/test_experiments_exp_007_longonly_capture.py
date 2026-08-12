"""Unit tests for the logic Experiment 007 adds.

Everything borrowed from Experiment 001 -- the minimum detectable effect, the
one-sided p-value, the windowing -- is tested there and is not retested here.
What is new, and therefore what this file tests, is:

* the reconstruction check and the exact boundary behaviour of its tolerance,
  because a residual equal to half a printed digit is the normal case and an
  off-by-one comparison there voids the whole experiment;
* the JOINT ratio bootstrap, its degenerate-denominator accounting, and the
  demonstration that a ratio's point estimate can fall outside its own interval
  when the denominator is near zero;
* the capture cell's arithmetic, including its invariance to annualisation;
* the algebraic identity that makes the size-neutral definition near one half,
  which is asserted here on constructed data rather than asserted in prose;
* the definitional spread and the frozen rejection rule, on every branch;
* the measured rebalance cost, against a hand-computed turnover;
* the capitalisation-share arithmetic and its invariance to the unstated scale
  of the source's average-market-cap table.

Expected values are computed in this file with plain NumPy or by hand, never by
calling the code under test.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pytest

from portfolio_edge.data.table import ParsedTable
from portfolio_edge.experiments.exp_001_factor_decay import MonthlySeries
from portfolio_edge.experiments.exp_007_longonly_capture import (
    FALSIFIER_ERAS,
    PRIMARY_DEFINITIONS,
    SIZE_NEUTRAL,
    AlignedBlock,
    CaptureCell,
    CaptureDefinition,
    InferenceSettings,
    LongOnlyCaptureError,
    ReconstructionCheck,
    _capitalisation_shares,
    _derive_value_columns,
    align_series,
    apply_rejection_rule,
    capture_cell,
    check_reconstruction,
    default_specification_path,
    definitional_spread,
    joint_ratio_bootstrap,
    portfolio_risk,
    rebalance_cost,
)
from portfolio_edge.experiments.periods import shift_period
from portfolio_edge.experiments.result import ResultStatus
from portfolio_edge.experiments.specification import JsonValue, load_specification

TOLERANCE = 0.00015


def settings(*, resamples: int = 400, spread_threshold: float = 0.30) -> InferenceSettings:
    return InferenceSettings(
        frozen_block_length=12.0,
        neighbour_block_lengths=(6.0, 24.0),
        n_resamples=resamples,
        power_target=0.80,
        materiality_annual_percent=2.0,
        assumed_capture=0.40,
        spread_threshold=spread_threshold,
    )


def periods(start: str, count: int) -> tuple[str, ...]:
    return tuple(shift_period(start, offset) for offset in range(count))


def as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


def definition(identifier: str, *, primary: bool = True) -> CaptureDefinition:
    return CaptureDefinition(
        identifier=identifier,
        long_only="L",
        benchmark="B",
        denominator="HML",
        reading="fixture",
        in_primary_family=primary,
    )


# --------------------------------------------------------------------------- #
# The reconstruction check, which is clause (0)
# --------------------------------------------------------------------------- #


def test_a_residual_exactly_equal_to_the_tolerance_passes() -> None:
    """The bound is the largest value rounding can produce, not the first defect.

    The real HML reconstruction lands exactly on half a printed digit, so an
    exclusive comparison here would void the experiment on every run.
    """
    published = np.zeros(10, dtype=np.float64)
    reconstructed = np.full(10, TOLERANCE, dtype=np.float64)
    check = check_reconstruction(
        reconstructed,
        published,
        identity="fixture",
        formula="f",
        checked_against="fixture",
        tolerance=TOLERANCE,
    )
    assert check.max_absolute == pytest.approx(TOLERANCE)
    assert check.passed


def test_a_residual_above_the_tolerance_fails_and_reports_all_three_moments() -> None:
    published = np.zeros(4, dtype=np.float64)
    reconstructed = np.asarray([0.0, 0.0, 0.0, 2.0 * TOLERANCE], dtype=np.float64)
    check = check_reconstruction(
        reconstructed,
        published,
        identity="fixture",
        formula="f",
        checked_against="fixture",
        tolerance=TOLERANCE,
    )
    assert not check.passed
    assert check.max_absolute == pytest.approx(2.0 * TOLERANCE)
    assert check.mean_residual == pytest.approx(0.5 * TOLERANCE)
    assert check.root_mean_square == pytest.approx(TOLERANCE)


def test_mismatched_lengths_are_refused_rather_than_broadcast() -> None:
    with pytest.raises(LongOnlyCaptureError, match="reconstructed months"):
        check_reconstruction(
            np.zeros(5),
            np.zeros(4),
            identity="fixture",
            formula="f",
            checked_against="fixture",
            tolerance=TOLERANCE,
        )


# --------------------------------------------------------------------------- #
# The algebra the size-neutral definition rests on
# --------------------------------------------------------------------------- #


def test_hml_is_exactly_the_difference_of_the_two_halves() -> None:
    generator = np.random.default_rng(7)
    columns = {
        name: generator.normal(0.01, 0.05, size=64)
        for name in ("SMALL LoBM", "ME1 BM2", "SMALL HiBM", "BIG LoBM", "ME2 BM2", "BIG HiBM")
    }
    block = AlignedBlock(
        name="fixture", periods=periods("2000-01", 64), columns=columns, dropped_months=0
    )
    derived = _derive_value_columns(block)
    expected = 0.5 * (columns["SMALL HiBM"] + columns["BIG HiBM"]) - 0.5 * (
        columns["SMALL LoBM"] + columns["BIG LoBM"]
    )
    np.testing.assert_allclose(derived["hml_reconstructed"], expected, rtol=0, atol=0)
    np.testing.assert_allclose(
        derived["hml_reconstructed"],
        derived["value_halves"] - derived["growth_halves"],
        rtol=0,
        atol=0,
    )


def test_the_size_neutral_capture_is_exactly_one_half_when_the_middle_is_the_midpoint() -> None:
    """The structural claim, asserted on data built to satisfy its premise.

    If the middle book-to-market bucket sits exactly at the midpoint of the outer
    two, then the long leg's excess over the equal-weighted six is exactly half
    the spread, whatever the outer buckets do. That is why the real figure lands
    near one half, and it is arithmetic rather than evidence.
    """
    generator = np.random.default_rng(11)
    small_low = generator.normal(0.01, 0.05, size=120)
    small_high = generator.normal(0.012, 0.05, size=120)
    big_low = generator.normal(0.009, 0.04, size=120)
    big_high = generator.normal(0.011, 0.04, size=120)
    columns = {
        "SMALL LoBM": small_low,
        "SMALL HiBM": small_high,
        "BIG LoBM": big_low,
        "BIG HiBM": big_high,
        "ME1 BM2": 0.5 * (small_low + small_high),
        "ME2 BM2": 0.5 * (big_low + big_high),
    }
    block = AlignedBlock(
        name="fixture", periods=periods("2000-01", 120), columns=columns, dropped_months=0
    )
    derived = _derive_value_columns(block)
    excess = derived["value_halves"] - derived["size_neutral_six"]
    np.testing.assert_allclose(excess, 0.5 * derived["hml_reconstructed"], rtol=1e-12, atol=0)


def test_the_long_and_short_leg_shares_sum_to_one_by_construction() -> None:
    generator = np.random.default_rng(13)
    columns = {
        name: generator.normal(0.01, 0.05, size=90)
        for name in ("SMALL LoBM", "ME1 BM2", "SMALL HiBM", "BIG LoBM", "ME2 BM2", "BIG HiBM")
    }
    block = AlignedBlock(
        name="fixture", periods=periods("2000-01", 90), columns=columns, dropped_months=0
    )
    derived = _derive_value_columns(block)
    spread = derived["hml_reconstructed"]
    long_share = float(np.mean(derived["value_halves"] - derived["size_neutral_six"])) / float(
        np.mean(spread)
    )
    short_share = float(np.mean(derived["size_neutral_six"] - derived["growth_halves"])) / float(
        np.mean(spread)
    )
    assert long_share + short_share == pytest.approx(1.0, abs=1e-12)


# --------------------------------------------------------------------------- #
# The joint ratio bootstrap
# --------------------------------------------------------------------------- #


def test_the_ratio_bootstrap_point_estimate_is_the_ratio_of_the_sample_means() -> None:
    generator = np.random.default_rng(17)
    denominator = generator.normal(0.004, 0.02, size=240)
    numerator = 0.5 * denominator + generator.normal(0.0, 0.001, size=240)
    interval = joint_ratio_bootstrap(
        numerator,
        denominator,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=500,
        rng=np.random.default_rng(1),
    )
    assert interval.point_estimate == pytest.approx(
        float(np.mean(numerator)) / float(np.mean(denominator))
    )
    assert interval.lower_90 <= interval.median <= interval.upper_90
    assert interval.lower_95 <= interval.lower_90
    assert interval.upper_95 >= interval.upper_90


def test_a_healthy_denominator_produces_a_stable_interval() -> None:
    """A denominator far from zero must not be marked unstable."""
    generator = np.random.default_rng(19)
    denominator = generator.normal(0.05, 0.005, size=300)
    numerator = 0.5 * denominator
    interval = joint_ratio_bootstrap(
        numerator,
        denominator,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=500,
        rng=np.random.default_rng(2),
    )
    assert interval.near_zero_denominator_resamples == 0
    assert interval.sign_flipped_denominator_resamples == 0
    assert not interval.unstable
    assert interval.point_estimate == pytest.approx(0.5)


def test_a_near_zero_denominator_is_counted_and_marked_unstable() -> None:
    """Fieller's problem, made visible rather than solved.

    With a denominator whose mean is a fraction of its own standard error, the
    resampled denominator changes sign often, the replicate distribution has
    heavy tails, and the point estimate can fall outside its own interval. The
    specification requires all of that to be reported, not repaired.
    """
    generator = np.random.default_rng(23)
    raw = generator.normal(0.0, 0.03, size=120)
    # Force the sample mean to a hundredth of a standard deviation, so the
    # denominator is positive but indistinguishable from zero.
    denominator = raw - float(np.mean(raw)) + 0.0003
    numerator = 0.5 * denominator + generator.normal(0.0005, 0.01, size=120)
    interval = joint_ratio_bootstrap(
        numerator,
        denominator,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=2000,
        rng=np.random.default_rng(3),
    )
    assert interval.sign_flipped_denominator_resamples > 0.20 * interval.n_resamples
    assert interval.near_zero_denominator_resamples > 0
    assert interval.unstable
    assert interval.upper_90 - interval.lower_90 > 1.0, "a degenerate ratio is not precise"


def test_the_bootstrap_is_joint_and_therefore_reproduces_a_deterministic_ratio() -> None:
    """One index draw applied to both series keeps an exact ratio exact.

    When the numerator is a fixed multiple of the denominator, every resample
    must return that multiple. An independent draw per series could not, which
    is precisely why the specification forbids one.
    """
    generator = np.random.default_rng(29)
    denominator = generator.normal(0.01, 0.02, size=200)
    numerator = 0.37 * denominator
    interval = joint_ratio_bootstrap(
        numerator,
        denominator,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=300,
        rng=np.random.default_rng(4),
    )
    assert interval.lower_90 == pytest.approx(0.37)
    assert interval.upper_90 == pytest.approx(0.37)
    assert interval.standard_error == pytest.approx(0.0, abs=1e-12)


def test_the_ratio_bootstrap_refuses_mismatched_lengths() -> None:
    with pytest.raises(LongOnlyCaptureError, match="equal lengths"):
        joint_ratio_bootstrap(
            np.zeros(5),
            np.zeros(6),
            block_length=12.0,
            block_length_source="frozen",
            n_resamples=10,
            rng=np.random.default_rng(0),
        )


# --------------------------------------------------------------------------- #
# The capture cell
# --------------------------------------------------------------------------- #


def _cell(scale: float = 1.0, *, months: int = 240) -> CaptureCell:
    generator = np.random.default_rng(31)
    denominator = generator.normal(0.004, 0.02, size=months)
    long_only = generator.normal(0.008, 0.04, size=months)
    benchmark = long_only - 0.5 * denominator
    return capture_cell(
        long_only * scale,
        benchmark * scale,
        denominator * scale,
        periods("1990-01", months),
        definition=definition("fixture"),
        era_name="fixture_era",
        start="1990-01",
        end=shift_period("1990-01", months - 1),
        settings=settings(resamples=200),
        rng=np.random.default_rng(5),
        with_neighbours=False,
    )


def test_the_capture_cell_reports_the_spread_in_annualised_percentage_points() -> None:
    cell = _cell()
    assert cell.months == 240
    assert cell.spread_annual_percent == pytest.approx(
        cell.capture_fraction * cell.denominator_annual_percent
    )
    assert cell.long_only_annual_percent - cell.benchmark_annual_percent == pytest.approx(
        cell.spread_annual_percent
    )


def test_the_capture_fraction_is_invariant_to_a_common_rescaling() -> None:
    """A ratio of two means cannot depend on the units both are quoted in.

    The specification asserts this rather than assuming it, because a capture
    fraction quietly computed on one series in percent and another in decimal
    would be wrong by a factor of a hundred and would look entirely plausible.
    """
    assert _cell(1.0).capture_fraction == pytest.approx(_cell(12.0).capture_fraction)
    assert _cell(1.0).capture_fraction == pytest.approx(_cell(0.01).capture_fraction)


def test_a_window_shorter_than_two_years_is_refused() -> None:
    with pytest.raises(LongOnlyCaptureError, match="shorter than two years"):
        capture_cell(
            np.zeros(12),
            np.zeros(12),
            np.ones(12),
            periods("2020-01", 12),
            definition=definition("fixture"),
            era_name="short",
            start="2020-01",
            end="2020-12",
            settings=settings(resamples=50),
            rng=np.random.default_rng(6),
            with_neighbours=False,
        )


# --------------------------------------------------------------------------- #
# The definitional spread and the frozen rejection rule
# --------------------------------------------------------------------------- #


def _grid(values: dict[str, float]) -> dict[str, list[CaptureCell]]:
    """Cells whose capture fractions are exactly ``values``, over both eras."""
    months = 240
    cells: dict[str, list[CaptureCell]] = {}
    for era in FALSIFIER_ERAS:
        row = []
        for identifier, fraction in values.items():
            generator = np.random.default_rng(37)
            denominator = generator.normal(0.004, 0.01, size=months)
            long_only = fraction * denominator
            row.append(
                capture_cell(
                    long_only,
                    np.zeros(months),
                    denominator,
                    periods("1990-01", months),
                    definition=definition(
                        identifier, primary=identifier in PRIMARY_DEFINITIONS
                    ),
                    era_name=era,
                    start="1990-01",
                    end="2009-12",
                    settings=settings(resamples=100),
                    rng=np.random.default_rng(7),
                    with_neighbours=False,
                )
            )
        cells[era] = row
    return cells


def _passing_checks() -> list[ReconstructionCheck]:
    return [
        check_reconstruction(
            np.zeros(10),
            np.zeros(10),
            identity="hml_from_6_portfolios_2x3",
            formula="f",
            checked_against="fixture",
            tolerance=TOLERANCE,
        )
    ]


def test_the_definitional_spread_is_over_the_primary_family_only() -> None:
    grid = _grid(
        {
            SIZE_NEUTRAL: 0.50,
            "value_halves_vs_market": 0.95,
            "big_value_vs_market": 0.63,
            "big_value_vs_big_third": 0.44,
            "small_value_vs_market": 1.29,
            "partial_tilt_50_vs_market": 5.0,  # outside the family, must be ignored
        }
    )
    spread, widest, narrowest = definitional_spread(grid[FALSIFIER_ERAS[0]])
    assert spread == pytest.approx(1.29 - 0.44, abs=1e-9)
    assert widest == "small_value_vs_market"
    assert narrowest == "big_value_vs_big_third"


def test_clause_zero_voids_everything_when_a_required_identity_fails() -> None:
    failing = [
        check_reconstruction(
            np.full(10, 10.0 * TOLERANCE),
            np.zeros(10),
            identity="hml_from_6_portfolios_2x3",
            formula="f",
            checked_against="fixture",
            tolerance=TOLERANCE,
        )
    ]
    verdict = apply_rejection_rule(failing, _grid({SIZE_NEUTRAL: 0.5}), settings=settings())
    assert verdict.status is ResultStatus.UNRESOLVED
    assert not verdict.clause_zero_passed
    assert verdict.clause_two == "not reached"
    assert verdict.spread_by_era == {}


def test_a_check_marked_not_required_cannot_fire_clause_zero() -> None:
    """The five-factor SMB disagreement is expected and must not void the run."""
    checks = [
        *_passing_checks(),
        check_reconstruction(
            np.full(10, 100.0 * TOLERANCE),
            np.zeros(10),
            identity="smb_from_6_portfolios_2x3_against_five_factor",
            formula="f",
            checked_against="fixture",
            tolerance=TOLERANCE,
            expected_to_pass=False,
        ),
    ]
    verdict = apply_rejection_rule(
        checks,
        _grid(dict.fromkeys(PRIMARY_DEFINITIONS, 0.50)),
        settings=settings(),
    )
    assert verdict.clause_zero_passed


def test_clause_one_fires_when_the_definitions_disagree() -> None:
    grid = _grid(
        {
            SIZE_NEUTRAL: 0.50,
            "value_halves_vs_market": 0.95,
            "big_value_vs_market": 0.63,
            "big_value_vs_big_third": 0.44,
            "small_value_vs_market": 1.29,
        }
    )
    verdict = apply_rejection_rule(_passing_checks(), grid, settings=settings())
    assert verdict.clause_one_rejected
    assert verdict.status is ResultStatus.REJECTED
    for era in FALSIFIER_ERAS:
        assert verdict.spread_by_era[era] > 0.30
    assert "no benchmark-free" in verdict.reasoning


def test_clause_one_holds_when_the_definitions_agree() -> None:
    grid = _grid(dict.fromkeys(PRIMARY_DEFINITIONS, 0.50))
    verdict = apply_rejection_rule(_passing_checks(), grid, settings=settings())
    assert not verdict.clause_one_rejected
    for era in FALSIFIER_ERAS:
        assert verdict.spread_by_era[era] == pytest.approx(0.0, abs=1e-9)


def test_clause_two_rejects_when_the_interval_sits_entirely_below_the_assumption() -> None:
    grid = _grid(dict.fromkeys(PRIMARY_DEFINITIONS, 0.20))
    verdict = apply_rejection_rule(_passing_checks(), grid, settings=settings())
    assert verdict.clause_two.startswith("rejected")
    assert verdict.status is ResultStatus.REJECTED


def test_clause_two_supports_when_the_interval_sits_entirely_above_the_assumption() -> None:
    grid = _grid(dict.fromkeys(PRIMARY_DEFINITIONS, 0.80))
    verdict = apply_rejection_rule(_passing_checks(), grid, settings=settings())
    assert verdict.clause_two.startswith("supported")
    assert verdict.status is ResultStatus.EXPLORATORY
    assert verdict.what_would_fire == ""


def test_a_straddling_interval_leaves_the_run_unresolved_and_says_what_would_fire() -> None:
    grid = _grid(dict.fromkeys(PRIMARY_DEFINITIONS, 0.40))
    verdict = apply_rejection_rule(_passing_checks(), grid, settings=settings())
    assert verdict.clause_two.startswith("straddles")
    assert verdict.status is ResultStatus.UNRESOLVED
    assert "would be supported" in verdict.what_would_fire


# --------------------------------------------------------------------------- #
# Risk of a long-only portfolio
# --------------------------------------------------------------------------- #


def test_portfolio_risk_reproduces_a_hand_computed_drawdown() -> None:
    returns = np.asarray([0.10, -0.20, -0.10, 0.05, 0.50], dtype=np.float64)
    labels = periods("2000-01", 5)
    risk = portfolio_risk(returns, labels, name="fixture")
    # Wealth: 1.10, 0.88, 0.792, 0.8316, 1.2474. Peak 1.10 at index 1, trough
    # 0.792 at index 3, so the drawdown is 0.792 / 1.10 - 1 = -0.28.
    assert risk.max_drawdown_percent == pytest.approx(-28.0)
    assert risk.max_time_under_water_months == 3
    assert risk.drawdown_peak_period == "2000-01"
    assert risk.drawdown_trough_period == "2000-03"
    terminal = float(np.prod(1.0 + returns))
    assert risk.geometric_annual_percent == pytest.approx(
        (terminal ** (12.0 / 5.0) - 1.0) * 100.0
    )


def test_a_drawdown_still_open_at_the_end_is_counted() -> None:
    returns = np.asarray([0.20, -0.05, -0.05, -0.05], dtype=np.float64)
    risk = portfolio_risk(returns, periods("2000-01", 4), name="fixture")
    assert risk.open_at_end
    assert risk.max_time_under_water_months == 3


# --------------------------------------------------------------------------- #
# The one cost that is measured
# --------------------------------------------------------------------------- #


def test_the_measured_rebalance_cost_matches_a_hand_computed_turnover() -> None:
    """Two halves that diverge by a known amount, rebalanced once.

    After a month in which the first half returns 10% and the second 0%, a
    portfolio held at 50/50 sits at 0.55 / 1.05 = 0.5238..., so the one-sided
    turnover of restoring it is |0.5238 - 0.5| = 0.0238..., and at k = 1 the cost
    is that many percent times one basis point.
    """
    first = np.asarray([0.10, 0.0], dtype=np.float64)
    second = np.asarray([0.0, 0.0], dtype=np.float64)
    result = rebalance_cost(first, second, frequency="monthly", k=1.0)
    expected_turnover = abs(0.55 / 1.05 - 0.5)
    assert result.rebalances == 1
    assert result.mean_one_sided_turnover_percent_per_rebalance == pytest.approx(
        100.0 * expected_turnover
    )
    assert result.cost_percent_per_year > 0.0
    assert result.net_geometric_annual_percent < result.gross_geometric_annual_percent


def test_two_identical_halves_never_drift_and_therefore_cost_nothing() -> None:
    returns = np.asarray([0.01, -0.02, 0.03, 0.00] * 6, dtype=np.float64)
    result = rebalance_cost(returns, returns.copy(), frequency="monthly", k=1.7)
    assert result.total_one_sided_turnover_percent_per_year == pytest.approx(0.0)
    assert result.cost_percent_per_year == pytest.approx(0.0, abs=1e-12)


def test_an_annual_rebalance_trades_less_often_than_a_monthly_one() -> None:
    generator = np.random.default_rng(41)
    first = generator.normal(0.01, 0.05, size=120)
    second = generator.normal(0.008, 0.04, size=120)
    monthly = rebalance_cost(first, second, frequency="monthly", k=1.7)
    annual = rebalance_cost(first, second, frequency="annual", k=1.7)
    assert monthly.rebalances > annual.rebalances
    assert monthly.cost_percent_per_year > annual.cost_percent_per_year


# --------------------------------------------------------------------------- #
# The microcap arithmetic
# --------------------------------------------------------------------------- #


def _share_table(name: str, values: list[list[float]], columns: tuple[str, ...]) -> ParsedTable:
    return ParsedTable(
        table_id=name,
        banner=name,
        columns=columns,
        periods=periods("2000-01", len(values)),
        values=tuple(tuple(row) for row in values),
        frequency="monthly",
        source_units="count",
        units="count",
        unit_transform="identity",
    )


def test_capitalisation_shares_are_invariant_to_the_unstated_scale() -> None:
    """The average-market-cap table states no currency and no scale.

    Only a share is reported, and a share of ``firms * average cap`` cannot
    depend on a scale common to every column. This asserts that rather than
    trusting it, because assuming a scale is exactly how the 25-portfolio file
    turns into nonsense.
    """
    columns = tuple(
        ["SMALL LoBM", "ME1 BM2", "ME1 BM3", "ME1 BM4", "SMALL HiBM"]
        + [f"ME{size} BM{value}" for size in (2, 3, 4) for value in range(1, 6)]
        + ["BIG LoBM", "ME5 BM2", "ME5 BM3", "ME5 BM4", "BIG HiBM"]
    )
    counts = [[100.0] * 25, [100.0] * 25]
    caps = [[1.0] * 24 + [1000.0], [1.0] * 24 + [1000.0]]
    scaled = [[value * 1e6 for value in row] for row in caps]

    plain = _capitalisation_shares(
        _share_table("firms", counts, columns),
        _share_table("caps", caps, columns),
        start="2000-01",
        end="2000-02",
    )
    rescaled = _capitalisation_shares(
        _share_table("firms", counts, columns),
        _share_table("caps", scaled, columns),
        start="2000-01",
        end="2000-02",
    )
    assert plain["per_cell"] == rescaled["per_cell"]

    corner = as_mapping(plain["small_value_corner_cell"])
    assert corner["mean_share_of_firm_count_percent"] == pytest.approx(4.0)
    # ME1 x BM5 holds a unit of average cap against a total of 24 + 1000.
    assert corner["mean_share_of_market_cap_percent"] == pytest.approx(100.0 / 1024.0)

    quintile = as_mapping(plain["smallest_size_quintile"])
    assert set(as_sequence(quintile["cells"])) == {
        "SMALL LoBM",
        "ME1 BM2",
        "ME1 BM3",
        "ME1 BM4",
        "SMALL HiBM",
    }
    assert quintile["mean_share_of_firm_count_percent"] == pytest.approx(20.0)


def test_capitalisation_shares_refuse_an_empty_window() -> None:
    columns = ("SMALL LoBM", "SMALL HiBM")
    with pytest.raises(LongOnlyCaptureError, match="no 5x5 count/cap months"):
        _capitalisation_shares(
            _share_table("firms", [[1.0, 1.0]], columns),
            _share_table("caps", [[1.0, 1.0]], columns),
            start="2010-01",
            end="2010-12",
        )


# --------------------------------------------------------------------------- #
# Alignment
# --------------------------------------------------------------------------- #


def series(name: str, start: str, count: int) -> MonthlySeries:
    return MonthlySeries(
        name=name,
        periods=periods(start, count),
        values=np.arange(count, dtype=np.float64),
        source_dataset_id="fixture",
        source_column=name,
    )


def test_alignment_intersects_and_reports_what_the_intersection_cost() -> None:
    block = align_series(
        "fixture", {"a": series("a", "2000-01", 24), "b": series("b", "2000-07", 24)}
    )
    assert block.months == 18
    assert block.periods[0] == "2000-07"
    assert block.periods[-1] == "2001-12"
    assert block.dropped_months == 12
    np.testing.assert_allclose(block["a"], np.arange(6, 24, dtype=np.float64))
    np.testing.assert_allclose(block["b"], np.arange(0, 18, dtype=np.float64))


def test_a_window_keeps_every_column_aligned() -> None:
    block = align_series(
        "fixture", {"a": series("a", "2000-01", 36), "b": series("b", "2000-01", 36)}
    ).window(start="2001-01", end="2001-12")
    assert block.months == 12
    assert block.periods[0] == "2001-01"
    np.testing.assert_allclose(block["a"], block["b"])


def test_an_unknown_column_names_the_ones_that_exist() -> None:
    block = align_series("fixture", {"a": series("a", "2000-01", 24)})
    with pytest.raises(LongOnlyCaptureError, match="no series 'b'"):
        _ = block["b"]


def test_a_pair_with_no_common_months_is_refused() -> None:
    with pytest.raises(LongOnlyCaptureError, match="common to all series"):
        align_series(
            "fixture", {"a": series("a", "2000-01", 12), "b": series("b", "2010-01", 12)}
        )


# --------------------------------------------------------------------------- #
# The committed specification
# --------------------------------------------------------------------------- #


def test_the_committed_specification_declares_what_this_module_implements() -> None:
    specification = load_specification(default_specification_path())
    parameters = as_mapping(specification.parameters)
    family = [
        as_mapping(item)
        for item in as_sequence(as_mapping(parameters["primary_definitions"])["family"])
    ]
    assert tuple(str(item["id"]) for item in family) == PRIMARY_DEFINITIONS
    assert family[0]["id"] == SIZE_NEUTRAL, "the size-neutral definition leads the family"
    assert parameters["assumed_capture_under_test"] == 0.40
    assert parameters["spread_threshold"] == 0.30

    identities = [
        as_mapping(item)
        for item in as_sequence(
            as_mapping(parameters["reconstruction_identities"])["identities"]
        )
    ]
    assert {item["tolerance_decimal_per_month"] for item in identities} == {TOLERANCE}, (
        "every reconstruction tolerance is the one uniformly derived rounding bound"
    )

    era_names = {era.name for era in specification.sample_policy.eras}
    assert set(FALSIFIER_ERAS) <= era_names
    assert "recent" in era_names, "reported, and excluded from the falsifier in advance"


def test_the_inherited_eras_match_experiment_001_exactly() -> None:
    """Restating a boundary is how two experiments drift apart."""
    ours = load_specification(default_specification_path())
    theirs = load_specification(
        default_specification_path().parent / "exp_001_factor_decay.yaml"
    )
    mine = {era.name: (era.start, era.end) for era in ours.sample_policy.eras}
    other = {era.name: (era.start, era.end) for era in theirs.sample_policy.eras}
    shared = set(mine) & set(other)
    assert shared, "this experiment inherits eras and must share some names"
    for name in sorted(shared):
        assert mine[name] == other[name], name


def test_the_specification_prices_costs_rather_than_refusing_to() -> None:
    """Unlike Experiments 001 and 005, a long-only portfolio can be priced."""
    cost_model = as_mapping(load_specification(default_specification_path()).cost_model)
    assert cost_model["applied"] is True
    measured = as_mapping(cost_model["measured_component"])
    assert measured["frequencies_reported"] == ("monthly", "annual")
    assumed = as_mapping(cost_model["assumed_components"])
    assert assumed["coefficient_k"] == (1.0, 1.7)
    expense = as_mapping(assumed["expense_ratio_percent_per_year"])
    assert math.isclose(float(str(expense["shelf_median"])), 0.15)
