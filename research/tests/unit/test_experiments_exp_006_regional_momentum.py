"""Unit tests for Experiment 006's own machinery.

Everything Experiment 006 shares with Experiment 005 -- the panel alignment, the
cross-region joint bootstrap, the effective sample size, the pooled cell and the
falsifier -- is tested in ``test_experiments_exp_005_regional_replication.py`` and
is imported here rather than reimplemented, so it is deliberately not retested.
What is tested here is what this experiment adds: the single-factor grid, the
momentum-specific crash statistics, and the cost schedule.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import yaml

from portfolio_edge.core.costs import K_FLOOR, K_PESSIMISTIC
from portfolio_edge.experiments.exp_001_factor_decay import MonthlySeries
from portfolio_edge.experiments.exp_006_regional_momentum import (
    CARHART_ALTERNATIVE_END,
    CARHART_ALTERNATIVE_START,
    NAMED_BEST_YEAR,
    NAMED_CRASH_YEAR,
    RegionalMomentumError,
    co_extreme_rate,
    cost_sensitivity,
    default_specification_path,
    drop_calendar_year,
    resolve_grid,
    tail_correlation,
    verify_momentum_coverage,
)
from portfolio_edge.experiments.specification import (
    Specification,
    load_specification,
    specification_from_mapping,
)


def committed() -> Specification:
    return load_specification(default_specification_path())


def altered(mutate: Any) -> Specification:
    raw: Any = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    mutate(raw)
    return specification_from_mapping(raw, source_path=default_specification_path())


def series(periods: tuple[str, ...]) -> MonthlySeries:
    return MonthlySeries(
        name="UMD",
        periods=periods,
        values=np.zeros(len(periods), dtype=np.float64),
        source_dataset_id="fixture",
        source_column="WML",
    )


# --------------------------------------------------------------------------- #
# The grid
# --------------------------------------------------------------------------- #


def test_the_grid_is_one_factor_three_regions_and_three_eras() -> None:
    grid = resolve_grid(committed())
    assert len(grid) == 9
    assert {cell.factor for cell in grid} == {"UMD"}
    assert {cell.region for cell in grid} == {"us", "developed_ex_us", "emerging"}
    assert {cell.era_role for cell in grid} == {
        "first_post_publication",
        "full_post_publication",
        "recent",
    }
    full = {cell.region: cell for cell in grid if cell.era_role == "full_post_publication"}
    assert {(cell.start, cell.end) for cell in full.values()} == {("1994-01", "2025-12")}


def test_a_grid_naming_an_era_the_sample_policy_does_not_define_is_refused() -> None:
    def mutate(raw: Any) -> None:
        raw["parameters"]["primary_grid"]["cells"]["UMD"]["recent"] = "not_an_era"

    with pytest.raises(RegionalMomentumError, match="which sample_policy does not define"):
        resolve_grid(altered(mutate))


def test_a_grid_that_adds_a_second_factor_is_refused() -> None:
    def mutate(raw: Any) -> None:
        raw["parameters"]["primary_grid"]["cells"]["HML"] = raw["parameters"]["primary_grid"][
            "cells"
        ]["UMD"]

    with pytest.raises(RegionalMomentumError, match="tests UMD and nothing else"):
        resolve_grid(altered(mutate))


def test_a_region_that_starts_after_an_era_aborts_rather_than_truncating() -> None:
    grid = resolve_grid(committed())
    late = {
        "us": series(("1927-01",)),
        "developed_ex_us": series(("1990-11",)),
        "emerging": series(("1999-01",)),
    }
    with pytest.raises(RegionalMomentumError, match="silently truncated"):
        verify_momentum_coverage(late, grid)


def test_the_coverage_check_records_the_head_room_it_measured() -> None:
    grid = resolve_grid(committed())
    payload: Any = verify_momentum_coverage(
        {
            "us": series(("1927-01",)),
            "developed_ex_us": series(("1990-11",)),
            "emerging": series(("1990-01",)),
        },
        grid,
    )
    head_room = {
        row["region"]: row["months_of_head_room"]
        for row in payload["rows"]
        if row["era_start"] == "1994-01"
    }
    assert head_room == {"us": 804, "developed_ex_us": 38, "emerging": 48}
    assert "FALSE of the data" in payload["verdict"]


# --------------------------------------------------------------------------- #
# Episode and crash statistics
# --------------------------------------------------------------------------- #


def test_dropping_the_best_and_worst_calendar_year_picks_the_right_year() -> None:
    periods = tuple(f"{year}-{month:02d}" for year in (2007, 2008, 2009) for month in range(1, 13))
    values = np.zeros(36, dtype=np.float64)
    values[:12] = 0.01  # 2007 compounds up
    values[12:24] = -0.02  # 2008 compounds down hardest
    values[24:] = 0.005  # 2009 compounds up a little

    kept, best = drop_calendar_year(values, periods, best=True)
    assert best == "2007"
    assert kept.size == 24

    kept, worst = drop_calendar_year(values, periods, best=False)
    assert worst == "2008"
    assert kept.size == 24
    assert float(np.mean(kept)) > 0.0


def test_dropping_a_year_from_a_single_year_window_drops_nothing() -> None:
    periods = tuple(f"2009-{month:02d}" for month in range(1, 13))
    values = np.linspace(-0.1, 0.1, 12)
    kept, year = drop_calendar_year(values, periods, best=False)
    assert year is None
    assert kept.size == 12


def test_the_co_extreme_rate_is_the_independence_rate_for_independent_regions() -> None:
    """Three independent regions should co-tail at roughly 0.1 ** 3."""
    generator = np.random.default_rng(20260812)
    panel = generator.normal(size=(20000, 3))
    measured, independent = co_extreme_rate(panel, fraction=0.10)
    assert independent == pytest.approx(0.001)
    assert measured == pytest.approx(0.001, abs=0.001)


def test_the_co_extreme_rate_is_the_tail_fraction_when_the_regions_are_identical() -> None:
    column = np.random.default_rng(1).normal(size=(500, 1))
    panel = np.repeat(column, 3, axis=1)
    measured, independent = co_extreme_rate(panel, fraction=0.10)
    assert measured == pytest.approx(0.10, abs=0.005)
    assert measured > independent * 50


def test_the_tail_correlation_of_identical_regions_is_one() -> None:
    column = np.random.default_rng(2).normal(size=(400, 1))
    panel = np.repeat(column, 3, axis=1)
    composite = panel.mean(axis=1)
    assert tail_correlation(panel, composite, fraction=0.10) == pytest.approx(1.0)


def test_the_tail_correlation_of_independent_regions_is_pushed_negative() -> None:
    """Selecting on the composite conditions on a collider, which is the point.

    Given that the sum is extreme the components trade off against one another,
    so the within-tail sample correlation of *independent* regions is well below
    zero. Any reading of the measured figure without its matched null is wrong in
    a direction most readers do not expect.
    """
    generator = np.random.default_rng(20260812)
    panel = generator.normal(size=(400, 3))
    composite = panel.mean(axis=1)
    assert tail_correlation(panel, composite, fraction=0.10) < -0.15


def test_the_tail_correlation_refuses_a_window_it_cannot_measure() -> None:
    panel = np.random.default_rng(3).normal(size=(6, 3))
    assert np.isnan(tail_correlation(panel, panel.mean(axis=1), fraction=1.0))


# --------------------------------------------------------------------------- #
# Cost, as a schedule rather than a number
# --------------------------------------------------------------------------- #


def test_the_cost_schedule_is_linear_in_turnover_and_uses_the_core_coefficients() -> None:
    payload: Any = cost_sensitivity(committed())
    assert payload["k_optimistic"] == K_FLOOR
    assert payload["k_pessimistic"] == K_PESSIMISTIC
    for row in payload["schedule"]:
        turnover = row["one_sided_monthly_turnover_percent"]
        assert row["annual_turnover_one_sided_percent"] == pytest.approx(12.0 * turnover)
        assert row["cost_percent_per_year_at_k_1_0"] == pytest.approx(
            12.0 * K_FLOOR * turnover / 100.0
        )
        assert row["cost_percent_per_year_at_k_1_7"] == pytest.approx(
            12.0 * K_PESSIMISTIC * turnover / 100.0
        )


def test_the_cost_schedule_names_no_long_only_turnover_and_says_why() -> None:
    """The error this block exists to prevent, stated in the payload itself."""
    payload: Any = cost_sensitivity(committed())
    long_only = payload["long_only_implementation"]
    assert long_only["one_sided_monthly_turnover_percent"] is None
    assert "UNMEASURED" in long_only["why_none"]
    assert "order of magnitude" in long_only["why_none"]
    academic = payload["academic_long_short_factor"]
    assert academic["one_sided_monthly_turnover_percent"] == [27.5, 91.5]
    assert academic["inside_retail_limit"] == [True, False]
    assert "ASSUMPTION" in academic["status"]


def test_a_cost_coefficient_that_drifts_from_core_costs_is_refused() -> None:
    def mutate(raw: Any) -> None:
        raw["parameters"]["cost_sensitivity"]["k_pessimistic"] = 2.5

    with pytest.raises(RegionalMomentumError, match="has drifted"):
        cost_sensitivity(altered(mutate))


# --------------------------------------------------------------------------- #
# The named constants are the ones the frozen record justifies
# --------------------------------------------------------------------------- #


def test_the_named_episodes_are_the_ones_the_specification_freezes() -> None:
    parameters: Any = committed().parameters
    assert parameters["crash_state_dependence"]["named_crash_year"] == NAMED_CRASH_YEAR
    assert NAMED_BEST_YEAR in str(parameters["episode_concentration"]["why"])
    assert CARHART_ALTERNATIVE_START == "1998-01"
    assert CARHART_ALTERNATIVE_END == "2025-12"
