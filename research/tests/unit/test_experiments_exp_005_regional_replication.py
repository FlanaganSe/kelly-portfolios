"""Unit tests for the logic Experiment 005 adds on top of Experiment 001.

Everything Experiment 005 borrows from Experiment 001 -- the per-cell statistics,
the minimum detectable effect, the windowing -- is already tested there and is
not retested here. What is new, and therefore what this file tests, is:

* the measured effective sample size, against closed forms with known answers;
* the cross-region JOINT block bootstrap, and the demonstration that resampling
  regions independently is narrower on correlated data;
* calendar-year contributions and the episode-concentration arithmetic;
* the frozen rejection rule, exercised on every branch it can take.

Expected values are computed in this file with plain NumPy or by hand, never by
calling the code under test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.experiments.exp_001_factor_decay import (
    CellStatistics,
    InferenceSettings,
    Window,
    compute_cell,
)
from portfolio_edge.experiments.exp_005_regional_replication import (
    ERA_ROLES,
    FACTORS,
    REGIONS,
    AlignedPanel,
    PooledCell,
    RegionalReplicationError,
    align_panel,
    apply_rejection_rule,
    calendar_year_contributions,
    compute_pooled,
    cross_region_bootstrap,
    effective_sample_size,
    pooled_composite,
    resolve_grid,
)
from portfolio_edge.experiments.periods import shift_period
from portfolio_edge.experiments.result import ResultStatus
from portfolio_edge.experiments.specification import load_specification

EQUAL_WEIGHTS = np.full(3, 1.0 / 3.0)


def settings(*, resamples: int = 400) -> InferenceSettings:
    return InferenceSettings(
        frozen_block_length=12.0,
        neighbour_block_lengths=(6.0, 24.0),
        n_resamples=resamples,
        method="stationary block bootstrap",
        power_target=0.80,
        materiality_annual_percent=2.0,
        true_factor_reference_annual_percent=6.6,
        rolling_windows_months=(12, 36, 60, 120),
        second_moment_bands={},
        second_moment_measured=dict.fromkeys(FACTORS, False),
    )


def periods(start: str, count: int) -> tuple[str, ...]:
    return tuple(shift_period(start, offset) for offset in range(count))


def panel_from(columns: list[np.ndarray], *, start: str = "1994-01") -> AlignedPanel:
    values = np.column_stack(columns)
    return AlignedPanel(
        factor="HML",
        era_name="hml_full_post_publication",
        regions=REGIONS,
        periods=periods(start, values.shape[0]),
        values=np.asarray(values, dtype=np.float64),
        dropped_months=0,
        per_region_available={region: int(values.shape[0]) for region in REGIONS},
        findings=(),
    )


# --------------------------------------------------------------------------- #
# Effective sample size
# --------------------------------------------------------------------------- #


def test_three_identical_regions_are_worth_exactly_one() -> None:
    """Perfect correlation buys nothing. This is the degenerate end of the scale."""
    column = np.asarray([0.01, -0.02, 0.03, 0.00, -0.01, 0.02] * 8, dtype=np.float64)
    panel = np.column_stack([column, column, column])
    sample = effective_sample_size(panel, pooled_composite(panel, EQUAL_WEIGHTS))
    assert sample.effective_regions == pytest.approx(1.0)
    assert sample.effective_region_months_iid == pytest.approx(float(column.size))
    assert sample.naive_region_months == 3 * column.size
    assert sample.inflation_avoided_iid == pytest.approx(3.0)
    assert sample.mean_pairwise_correlation == pytest.approx(1.0)


def test_three_orthogonal_regions_are_worth_exactly_three() -> None:
    """Exactly orthogonal, equal-variance columns: the answer must be k, not k-ish.

    The three columns are mutually orthogonal and mean-zero by construction, so
    ``mean var_i / var(composite) = (4/3) / (4/9) = 3`` exactly, with no sampling
    slack for the assertion to hide in.
    """
    panel = np.asarray(
        [[1.0, 1.0, 1.0], [-1.0, 1.0, -1.0], [1.0, -1.0, -1.0], [-1.0, -1.0, 1.0]],
        dtype=np.float64,
    )
    composite = pooled_composite(panel, EQUAL_WEIGHTS)
    sample = effective_sample_size(panel, composite)
    assert sample.mean_pairwise_correlation == pytest.approx(0.0, abs=1e-12)
    assert sample.effective_regions == pytest.approx(3.0)
    assert sample.effective_region_months_iid == pytest.approx(12.0)
    assert sample.naive_region_months == 12


def test_effective_regions_matches_the_equicorrelation_closed_form() -> None:
    """``k / (1 + (k - 1) rho)``, checked against the realised sample correlation."""
    rng = np.random.default_rng(20260812)
    common = rng.normal(size=600)
    panel = np.column_stack(
        [0.8 * common + 0.6 * rng.normal(size=600) for _ in range(3)]
    )
    composite = pooled_composite(panel, EQUAL_WEIGHTS)
    sample = effective_sample_size(panel, composite)

    correlation = np.atleast_2d(np.asarray(np.corrcoef(panel, rowvar=False)))
    rho = float(np.mean(correlation[np.triu_indices(3, k=1)]))
    variances = np.var(panel, axis=0, ddof=1)
    # The closed form holds exactly only for equal variances, so compare against
    # the general definition and check the closed form to a loose tolerance.
    assert sample.effective_regions == pytest.approx(
        float(np.mean(variances)) / float(np.var(composite, ddof=1))
    )
    assert sample.effective_regions == pytest.approx(3.0 / (1.0 + 2.0 * rho), rel=0.02)
    assert 1.0 < sample.effective_regions < 3.0


def test_the_hac_variant_is_reported_and_is_a_different_number() -> None:
    """Serial dependence is folded in separately, never silently into the iid figure."""
    rng = np.random.default_rng(7)
    base = rng.normal(size=400)
    persistent = np.empty(400)
    persistent[0] = base[0]
    for index in range(1, 400):
        persistent[index] = 0.6 * persistent[index - 1] + base[index]
    panel = np.column_stack([persistent, persistent + rng.normal(size=400), persistent * 0.5])
    sample = effective_sample_size(panel, pooled_composite(panel, EQUAL_WEIGHTS))
    assert sample.composite_long_run_variance > sample.composite_variance
    assert sample.effective_region_months_hac < sample.effective_region_months_iid


def test_a_panel_that_is_not_two_dimensional_is_refused() -> None:
    with pytest.raises(RegionalReplicationError, match="2-dimensional"):
        effective_sample_size(np.zeros(10), np.zeros(10))


# --------------------------------------------------------------------------- #
# The cross-region bootstrap
# --------------------------------------------------------------------------- #


def test_the_joint_bootstrap_resamples_one_time_index_for_every_region() -> None:
    """With identical regions the joint composite must equal the single series.

    If the implementation drew a separate index per region this identity would
    fail, so it is the direct test that the draw is shared.
    """
    rng = np.random.default_rng(11)
    column = rng.normal(0.002, 0.03, size=240)
    panel = np.column_stack([column, column, column])
    joint = cross_region_bootstrap(
        panel,
        EQUAL_WEIGHTS,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=500,
        rng=np.random.default_rng(3),
        joint=True,
    )
    single = cross_region_bootstrap(
        column[:, None],
        np.ones(1),
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=500,
        rng=np.random.default_rng(3),
        joint=True,
    )
    assert joint.point_estimate == pytest.approx(single.point_estimate)
    assert joint.lower_90 == pytest.approx(single.lower_90)
    assert joint.upper_90 == pytest.approx(single.upper_90)
    assert joint.valid is True
    assert joint.scheme == "cross-region-joint"


def test_independent_resampling_is_narrower_on_correlated_regions() -> None:
    """The error this experiment exists to avoid, measured rather than asserted."""
    rng = np.random.default_rng(20260812)
    common = rng.normal(0.002, 0.03, size=360)
    panel = np.column_stack(
        [common + rng.normal(0.0, 0.008, size=360) for _ in range(3)]
    )
    joint = cross_region_bootstrap(
        panel,
        EQUAL_WEIGHTS,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=2000,
        rng=np.random.default_rng(5),
        joint=True,
    )
    independent = cross_region_bootstrap(
        panel,
        EQUAL_WEIGHTS,
        block_length=12.0,
        block_length_source="frozen",
        n_resamples=2000,
        rng=np.random.default_rng(5),
        joint=False,
    )
    assert independent.valid is False
    assert "INVALID" in independent.scheme
    assert independent.standard_error < joint.standard_error
    assert (independent.upper_90 - independent.lower_90) < (joint.upper_90 - joint.lower_90)


def test_the_composite_is_the_declared_linear_combination() -> None:
    panel = np.asarray([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
    assert pooled_composite(panel, EQUAL_WEIGHTS) == pytest.approx([2.0, 5.0])
    assert pooled_composite(panel, np.asarray([1.0, 0.0, 0.0])) == pytest.approx([1.0, 4.0])
    with pytest.raises(RegionalReplicationError, match="weights for"):
        pooled_composite(panel, np.ones(2))


# --------------------------------------------------------------------------- #
# Episode concentration
# --------------------------------------------------------------------------- #


def test_calendar_year_contributions_sum_to_one() -> None:
    rng = np.random.default_rng(2)
    values = rng.normal(0.005, 0.03, size=36)
    labels = periods("2000-01", 36)
    rows = calendar_year_contributions(values, labels)
    assert [year for year, _, _ in rows] == ["2000", "2001", "2002"]
    assert sum(share for _, _, share in rows) == pytest.approx(1.0)
    first = values[:12]
    assert rows[0][1] == pytest.approx(float(np.prod(1.0 + first) - 1.0))
    assert rows[0][2] == pytest.approx(float(np.sum(first) / np.sum(values)))


def test_a_premium_that_lives_in_one_year_shows_up_as_a_share_above_one() -> None:
    """The arithmetic is signed on purpose: the honest reading of concentration."""
    values = np.zeros(24)
    values[3] = 0.20
    values[15] = -0.05
    rows = calendar_year_contributions(values, periods("2000-01", 24))
    shares = {year: share for year, _, share in rows}
    assert shares["2000"] > 1.0
    assert shares["2001"] < 0.0


# --------------------------------------------------------------------------- #
# The frozen rejection rule, on every branch
# --------------------------------------------------------------------------- #


def alternating(mean_monthly: float, amplitude: float, count: int) -> np.ndarray:
    """A deterministic series with an exact mean and an exact standard deviation."""
    signs = np.asarray([1.0 if index % 2 == 0 else -1.0 for index in range(count)])
    return mean_monthly + amplitude * signs


def regional_cells(
    means: list[float], amplitude: float, count: int
) -> dict[str, CellStatistics]:
    out: dict[str, CellStatistics] = {}
    for region, mean in zip(REGIONS, means, strict=True):
        values = alternating(mean, amplitude, count)
        window = Window(
            name=region,
            start="1994-01",
            end=shift_period("1994-01", count - 1),
            periods=periods("1994-01", count),
            values=values,
            findings=(),
        )
        out[region] = compute_cell(
            window,
            factor="HML",
            era_role="full_post_publication",
            era_name="hml_full_post_publication",
            settings=settings(),
            rng=np.random.default_rng(1),
            with_bootstrap=False,
        )
    return out


def pooled_from(
    means: list[float], amplitude: float, count: int, seed: int = 4
) -> PooledCell:
    panel = panel_from([alternating(mean, amplitude, count) for mean in means])
    return compute_pooled(
        panel,
        era_role="full_post_publication",
        start="1994-01",
        end=shift_period("1994-01", count - 1),
        weights=EQUAL_WEIGHTS,
        weighting="equal",
        settings=settings(),
        rng=np.random.default_rng(seed),
        us_band=0.0,
    )


def test_branch_b_fires_when_the_measured_pooled_window_cannot_detect_materiality() -> None:
    """An underpowered pooled window closes the factor rather than deferring it."""
    pooled = pooled_from([0.0005, 0.0005, 0.0005], amplitude=0.05, count=384)
    verdict = apply_rejection_rule(
        "HML", pooled, regional_cells([0.0005] * 3, 0.05, 384), materiality=2.0
    )
    assert pooled.mde_one_sided_percent_per_year > 2.0
    assert verdict.status is ResultStatus.REJECTED
    assert verdict.branch == "(b) closed on public data"
    assert "not a request for more research" in verdict.reasoning


def test_branch_a_advances_a_powered_positive_stable_unconcentrated_premium() -> None:
    pooled = pooled_from([0.004, 0.004, 0.004], amplitude=0.01, count=384)
    verdict = apply_rejection_rule(
        "HML", pooled, regional_cells([0.004] * 3, 0.01, 384), materiality=2.0
    )
    assert pooled.mde_one_sided_percent_per_year < 2.0
    assert verdict.status is ResultStatus.EXPLORATORY
    assert verdict.branch == "(a) advance"
    assert verdict.clauses_failed == ()
    assert len(verdict.clauses_passed) == 5


def test_a_powered_window_that_measures_a_negative_premium_is_rejected_not_unresolved() -> None:
    pooled = pooled_from([-0.002, -0.002, -0.002], amplitude=0.01, count=384)
    verdict = apply_rejection_rule(
        "CMA", pooled, regional_cells([-0.002] * 3, 0.01, 384), materiality=2.0
    )
    assert pooled.mde_one_sided_percent_per_year < 2.0
    assert verdict.status is ResultStatus.REJECTED
    assert verdict.branch == "(a) failed in a powered window"


def test_a_powered_material_premium_carried_by_one_region_is_unresolved_and_says_why() -> None:
    """The only legitimate `unresolved` here, and it must name what would fire."""
    pooled = pooled_from([0.010, -0.0015, -0.0015], amplitude=0.01, count=384)
    verdict = apply_rejection_rule(
        "HML",
        pooled,
        regional_cells([0.010, -0.0015, -0.0015], 0.01, 384),
        materiality=2.0,
    )
    assert pooled.annualised_premium_percent > 2.0
    assert pooled.mde_one_sided_percent_per_year < 2.0
    assert verdict.status is ResultStatus.UNRESOLVED
    assert any("(a4)" in item for item in verdict.clauses_failed)
    assert verdict.what_would_fire
    assert "(a4)" in verdict.what_would_fire


# --------------------------------------------------------------------------- #
# Alignment and the grid
# --------------------------------------------------------------------------- #


def test_alignment_intersects_and_reports_the_loss_rather_than_filling_it() -> None:
    windows = {
        "us": Window(
            name="us",
            start="1994-01",
            end="1994-06",
            periods=periods("1994-01", 6),
            values=np.arange(6, dtype=np.float64),
            findings=(),
        ),
        "developed_ex_us": Window(
            name="developed_ex_us",
            start="1994-01",
            end="1994-06",
            periods=periods("1994-03", 4),
            values=np.arange(4, dtype=np.float64),
            findings=("developed_ex_us: window starts at 1994-03",),
        ),
        "emerging": Window(
            name="emerging",
            start="1994-01",
            end="1994-06",
            periods=periods("1994-01", 6),
            values=np.arange(6, dtype=np.float64),
            findings=(),
        ),
    }
    panel = align_panel(windows, factor="HML", era_name="era", regions=REGIONS)
    assert panel.periods == periods("1994-03", 4)
    assert panel.months == 4
    assert panel.dropped_months == 2
    assert any("intersection dropped 2" in item for item in panel.findings)
    assert any("starts at 1994-03" in item for item in panel.findings)
    assert panel.values.shape == (4, 3)


def test_the_committed_specification_produces_the_frozen_twenty_seven_cell_family() -> None:
    from portfolio_edge.experiments.exp_005_regional_replication import (
        default_specification_path,
    )

    grid = resolve_grid(load_specification(default_specification_path()))
    assert len(grid) == len(FACTORS) * len(REGIONS) * len(ERA_ROLES) == 27
    assert len({cell.key for cell in grid}) == 27
    # RMW and CMA share every era, which is why the family is dependent.
    by_factor = {
        factor: {cell.era_role: (cell.start, cell.end) for cell in grid if cell.factor == factor}
        for factor in FACTORS
    }
    assert by_factor["RMW"] == by_factor["CMA"]
    assert by_factor["HML"]["full_post_publication"] == ("1994-01", "2025-12")
    assert by_factor["RMW"]["full_post_publication"] == ("2014-01", "2025-12")
    # `common_period` is deliberately not a role: it is the same window as
    # `full_post_publication` for RMW and CMA.
    assert "common_period" not in {cell.era_role for cell in grid}


def test_the_pooled_cell_refuses_a_window_shorter_than_two_years() -> None:
    panel = panel_from([alternating(0.001, 0.01, 12) for _ in range(3)])
    with pytest.raises(RegionalReplicationError, match="shorter than two years"):
        compute_pooled(
            panel,
            era_role="full_post_publication",
            start="1994-01",
            end="1994-12",
            weights=EQUAL_WEIGHTS,
            weighting="equal",
            settings=settings(),
            rng=np.random.default_rng(1),
            us_band=0.0,
        )


def test_the_us_volatility_band_moves_the_pooled_mde_but_not_the_pooled_premium() -> None:
    """Phase 1 reproduced every mean, so the band may only move second moments."""
    means = [0.002, 0.002, 0.002]
    without = pooled_from(means, amplitude=0.02, count=384, seed=9)
    panel = panel_from([alternating(mean, 0.02, 384) for mean in means])
    with_band = compute_pooled(
        panel,
        era_role="full_post_publication",
        start="1994-01",
        end=shift_period("1994-01", 383),
        weights=EQUAL_WEIGHTS,
        weighting="equal",
        settings=settings(),
        rng=np.random.default_rng(9),
        us_band=0.0303,
    )
    assert with_band.annualised_premium_percent == pytest.approx(
        without.annualised_premium_percent
    )
    assert with_band.band_mde is not None and with_band.band_sharpe is not None
    low, high = with_band.band_mde
    assert low < with_band.mde_one_sided_percent_per_year < high
    assert math.isfinite(with_band.band_sharpe[0])
