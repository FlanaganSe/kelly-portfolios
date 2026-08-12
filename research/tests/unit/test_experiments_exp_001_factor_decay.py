"""Tests for the non-trivial logic of Experiment 001.

Everything checked here is either hand-computed in the assertion's own docstring
or computed with plain NumPy in the test body. Nothing is checked against a
second call to the code under test.

The three things worth testing hardest, because they are the three the write-up
leans on: the era grid comes from the frozen specification rather than from a
loop, the minimum detectable effect is a real power calculation rather than a
rearranged confidence interval, and the rejection rule is the frozen falsifier
rather than whatever the numbers suggested afterwards.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pytest
import yaml

from portfolio_edge.experiments.exp_001_factor_decay import (
    ERA_ROLES,
    FACTORS,
    CellStatistics,
    FactorDecayError,
    InferenceSettings,
    MonthlySeries,
    _clip_to_sample_policy,
    _drop_best_calendar_year,
    _drop_best_month,
    _normal_quantile,
    _second_moment_band,
    alternative_date_eras,
    apply_rejection_rule,
    compute_cell,
    correct_grid,
    cost_illustration,
    default_specification_path,
    minimum_detectable_effect,
    one_sided_p_value,
    power_to_detect,
    resolve_grid,
    standard_normal_cdf,
    window_series,
    worst_rolling_return,
)
from portfolio_edge.experiments.periods import shift_period
from portfolio_edge.experiments.result import CONFIRMATORY_ONLY_STATUSES, ResultStatus
from portfolio_edge.experiments.specification import (
    Specification,
    load_specification,
    specification_from_mapping,
)


@pytest.fixture(scope="module")
def committed_spec() -> Specification:
    return load_specification(default_specification_path())


def settings(**overrides: object) -> InferenceSettings:
    """Small, fast inference settings. Resamples are cut to keep unit tests quick."""
    base: dict[str, object] = {
        "frozen_block_length": 12.0,
        "neighbour_block_lengths": (6.0,),
        "n_resamples": 200,
        "method": "stationary block bootstrap",
        "power_target": 0.80,
        "materiality_annual_percent": 2.0,
        "true_factor_reference_annual_percent": 6.6,
        "rolling_windows_months": (12, 36),
        "second_moment_bands": {"HML": 0.0303, "RMW": 0.0509, "CMA": 0.0, "UMD": 0.0},
        "second_moment_measured": {"HML": True, "RMW": True, "CMA": True, "UMD": False},
    }
    base.update(overrides)
    return InferenceSettings(**base)  # type: ignore[arg-type]


def monthly_series(
    name: str, *, start: str, months: int, mean: float, sigma: float, seed: int
) -> MonthlySeries:
    """A series whose realised mean and standard deviation are EXACTLY as asked.

    The noise is standardised before the moments are imposed, so a test of the
    rejection rule exercises the rule rather than the draw. A test that says
    "a 3 pp/yr premium on 16% volatility over 384 months is unresolved" is only
    a test of that statement if the series really has those moments.
    """
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(months)
    noise = (noise - noise.mean()) / noise.std(ddof=1)
    return MonthlySeries(
        name=name,
        periods=tuple(shift_period(start, offset) for offset in range(months)),
        values=np.asarray(mean + sigma * noise, dtype=np.float64),
        source_dataset_id="fixture",
        source_column=name,
    )


def cell_from(
    series: MonthlySeries, *, factor: str, era_role: str, seed: int = 7
) -> CellStatistics:
    window = window_series(series, start=series.periods[0], end=series.periods[-1])
    return compute_cell(
        window,
        factor=factor,
        era_role=era_role,
        era_name=f"fixture_{era_role}",
        settings=settings(),
        rng=np.random.default_rng(seed),
    )


# --------------------------------------------------------------------------- #
# The normal distribution, in closed form
# --------------------------------------------------------------------------- #


def test_standard_normal_cdf_matches_known_values() -> None:
    """Phi(0) = 0.5, Phi(1.6448536) = 0.95, Phi(1.959964) = 0.975, Phi(-1) = 1 - Phi(1)."""
    assert standard_normal_cdf(0.0) == pytest.approx(0.5)
    assert standard_normal_cdf(1.6448536269514722) == pytest.approx(0.95, abs=1e-12)
    assert standard_normal_cdf(1.959963984540054) == pytest.approx(0.975, abs=1e-12)
    assert standard_normal_cdf(-1.0) == pytest.approx(1.0 - standard_normal_cdf(1.0))


def test_one_sided_p_value_is_the_upper_tail() -> None:
    """p(0) = 0.5, p(1.6448536) = 0.05, p(1.959964) = 0.025."""
    assert one_sided_p_value(0.0) == pytest.approx(0.5)
    assert one_sided_p_value(1.6448536269514722) == pytest.approx(0.05, abs=1e-12)
    assert one_sided_p_value(1.959963984540054) == pytest.approx(0.025, abs=1e-12)


def test_an_untabulated_quantile_raises_rather_than_guessing() -> None:
    assert _normal_quantile(0.95) == pytest.approx(1.6448536269514722)
    with pytest.raises(ValueError, match="no exact normal quantile"):
        _normal_quantile(0.90)


# --------------------------------------------------------------------------- #
# Power
# --------------------------------------------------------------------------- #


def test_minimum_detectable_effect_is_the_textbook_closed_form() -> None:
    """(z_0.95 + z_0.80) * SE = (1.6448536 + 0.8416212) * SE = 2.4864749 * SE.

    Two-sided replaces z_0.95 with z_0.975: (1.9599640 + 0.8416212) = 2.8015852.
    """
    assert minimum_detectable_effect(standard_error=1.0, one_sided=True) == pytest.approx(
        2.4864748605243866, abs=1e-12
    )
    assert minimum_detectable_effect(standard_error=1.0, one_sided=False) == pytest.approx(
        2.8015852181129683, abs=1e-12
    )
    assert minimum_detectable_effect(standard_error=0.25, one_sided=True) == pytest.approx(
        0.6216187151310966, abs=1e-12
    )


def test_a_two_sided_test_needs_a_larger_effect_than_a_one_sided_one() -> None:
    one = minimum_detectable_effect(standard_error=0.3, one_sided=True)
    two = minimum_detectable_effect(standard_error=0.3, one_sided=False)
    assert two > one


def test_minimum_detectable_effect_scales_with_the_standard_error() -> None:
    """The MDE is linear in SE, so halving SE halves the detectable effect.

    Because SE = sigma / sqrt(T), that is the same statement as: quadrupling the
    sample halves the smallest premium the window can see.
    """
    assert minimum_detectable_effect(standard_error=0.5) == pytest.approx(
        2.0 * minimum_detectable_effect(standard_error=0.25)
    )


def test_power_to_detect_exactly_inverts_the_minimum_detectable_effect() -> None:
    """Feeding the MDE back in must return the power it was computed for."""
    for power in (0.80,):
        for standard_error in (0.1, 0.5, 2.0):
            effect = minimum_detectable_effect(standard_error=standard_error, power=power)
            assert power_to_detect(effect, standard_error=standard_error) == pytest.approx(
                power, abs=1e-12
            )


def test_power_against_a_zero_effect_is_the_test_size() -> None:
    """A test of a true null rejects with probability alpha, by construction."""
    assert power_to_detect(0.0, standard_error=1.0, alpha=0.05) == pytest.approx(0.05, abs=1e-12)
    assert power_to_detect(0.0, standard_error=1.0, alpha=0.05, one_sided=False) == pytest.approx(
        0.025, abs=1e-12
    )


def test_power_rises_with_the_effect_and_falls_with_the_standard_error() -> None:
    assert power_to_detect(1.0, standard_error=0.5) > power_to_detect(0.5, standard_error=0.5)
    assert power_to_detect(1.0, standard_error=0.5) > power_to_detect(1.0, standard_error=1.0)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"standard_error": 0.0}, "standard_error"),
        ({"standard_error": -1.0}, "standard_error"),
        ({"standard_error": 1.0, "power": 0.0}, "power"),
        ({"standard_error": 1.0, "power": 1.0}, "power"),
        ({"standard_error": 1.0, "alpha": 0.0}, "alpha"),
    ],
)
def test_degenerate_power_inputs_are_refused(kwargs: dict[str, float], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        minimum_detectable_effect(**kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Rolling windows
# --------------------------------------------------------------------------- #


def test_worst_rolling_return_compounds_rather_than_sums() -> None:
    """Hand fixture: r = [0.1, -0.5, 0.1, 0.1], 2-month windows.

    Compounded: (1.1)(0.5) - 1 = -0.45; (0.5)(1.1) - 1 = -0.45; (1.1)(1.1) - 1 = 0.21.
    The worst is -0.45, at periods 1..2. Summing would give -0.40, which is not a
    two-month return, and the gap grows with the window length.
    """
    values = np.asarray([0.1, -0.5, 0.1, 0.1], dtype=np.float64)
    periods = ("2000-01", "2000-02", "2000-03", "2000-04")
    result = worst_rolling_return(values, periods, 2)
    assert result.worst_return == pytest.approx(-0.45)
    assert (result.start, result.end) == ("2000-01", "2000-02")
    assert result.windows_available == 3
    assert result.worst_return != pytest.approx(float(np.sum(values[:2])))


def test_worst_rolling_return_over_the_whole_series_is_the_terminal_return() -> None:
    values = np.asarray([0.02, -0.01, 0.03], dtype=np.float64)
    periods = ("1990-01", "1990-02", "1990-03")
    result = worst_rolling_return(values, periods, 3)
    assert result.worst_return == pytest.approx(float(np.prod(1.0 + values) - 1.0))
    assert result.windows_available == 1


def test_a_window_longer_than_the_era_is_reported_as_unavailable_not_as_zero() -> None:
    values = np.asarray([0.01] * 11, dtype=np.float64)
    periods = tuple(shift_period("2020-01", i) for i in range(11))
    result = worst_rolling_return(values, periods, 12)
    assert result.worst_return is None
    assert result.windows_available == 0
    assert "fewer than" in result.unavailable_reason


def test_a_non_positive_rolling_window_is_a_programming_error() -> None:
    with pytest.raises(ValueError, match="window_months"):
        worst_rolling_return(np.asarray([0.1]), ("2000-01",), 0)


# --------------------------------------------------------------------------- #
# Windowing
# --------------------------------------------------------------------------- #


def test_window_series_selects_the_frozen_window_and_reports_nothing_when_clean() -> None:
    series = monthly_series("HML", start="1990-01", months=60, mean=0.004, sigma=0.03, seed=1)
    window = window_series(series, start="1991-01", end="1992-12")
    assert window.observations == 24
    assert (window.periods[0], window.periods[-1]) == ("1991-01", "1992-12")
    assert window.findings == ()


def test_a_window_reaching_before_the_file_starts_is_reported_not_padded() -> None:
    """UMD starts 1927-01 and FF5 starts 1963-07; asking for more is a real case."""
    series = monthly_series("RMW", start="1963-07", months=48, mean=0.002, sigma=0.02, seed=2)
    window = window_series(series, start="1960-01", end="1965-06")
    assert window.observations == 24
    assert any("does not reach back that far" in finding for finding in window.findings)
    assert any("spans 66 calendar months" in finding for finding in window.findings)


def test_a_gap_inside_a_window_is_found_and_never_filled() -> None:
    series = monthly_series("CMA", start="2000-01", months=36, mean=0.003, sigma=0.02, seed=3)
    punched = MonthlySeries(
        name=series.name,
        periods=series.periods[:10] + series.periods[12:],
        values=np.concatenate([series.values[:10], series.values[12:]]),
        source_dataset_id="fixture",
        source_column="CMA",
    )
    window = window_series(punched, start="2000-01", end="2002-12")
    assert window.observations == 34
    assert any("month gaps inside the window" in finding for finding in window.findings)


def test_a_series_is_clipped_to_the_sample_policy_before_any_statistic() -> None:
    """The holdout is enforced once, at the boundary, not in twenty windows."""
    series = monthly_series("HML", start="2024-01", months=30, mean=0.0, sigma=0.02, seed=4)
    clipped = _clip_to_sample_policy(series, end="2025-12")
    assert clipped.last_observation == "2025-12"
    assert clipped.values.size == 24
    assert np.array_equal(clipped.values, series.values[:24])


def test_a_window_shorter_than_two_years_is_refused_rather_than_summarised() -> None:
    series = monthly_series("HML", start="2020-01", months=18, mean=0.004, sigma=0.03, seed=5)
    window = window_series(series, start="2020-01", end="2021-06")
    with pytest.raises(FactorDecayError, match="refuses to summarise"):
        compute_cell(
            window,
            factor="HML",
            era_role="fixture",
            era_name="fixture",
            settings=settings(),
            rng=np.random.default_rng(0),
        )


# --------------------------------------------------------------------------- #
# The frozen grid
# --------------------------------------------------------------------------- #


def test_the_grid_comes_from_the_committed_specification(committed_spec: Specification) -> None:
    grid = resolve_grid(committed_spec)
    assert len(grid) == 20, "the multiple-testing family is 4 factors x 5 era roles"
    assert {cell.factor for cell in grid} == set(FACTORS)
    assert {cell.era_role for cell in grid} == set(ERA_ROLES)
    by_key = {cell.key: cell for cell in grid}
    assert by_key["HML/full_post_publication"].era_name == "hml_full_post_publication"
    assert by_key["HML/full_post_publication"].start == "1994-01"
    assert by_key["UMD/original_sample"].start == "1965-01"
    assert by_key["RMW/first_post_publication"].era_name == "rmw_cma_first_post_publication"
    assert by_key["CMA/common_period"].era_name == "common_period"
    # RMW and CMA share every era, which is why the correction is a lower bound.
    for role in ERA_ROLES:
        assert by_key[f"RMW/{role}"].era_name == by_key[f"CMA/{role}"].era_name


def test_no_primary_era_reads_past_the_frozen_sample_end(committed_spec: Specification) -> None:
    end = committed_spec.sample_policy.end
    for cell in resolve_grid(committed_spec):
        assert cell.end <= end, f"{cell.key} would read past the holdout"


def test_alternative_publication_dates_sit_outside_the_family(
    committed_spec: Specification,
) -> None:
    """They test the same hypothesis under a different date; counting them twice
    would inflate the family and understate the correction."""
    alternatives = alternative_date_eras(committed_spec)
    assert {factor for factor, _ in alternatives} == {"HML", "UMD"}
    names = {era.name for _, era in alternatives}
    assert names == {"hml_post_rosenberg_alternative", "umd_post_carhart_alternative"}
    assert names.isdisjoint({cell.era_name for cell in resolve_grid(committed_spec)})


def test_a_grid_naming_an_undefined_era_is_refused() -> None:
    """Loading the real YAML means this breaks if the committed grid drifts."""
    raw = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    raw["parameters"]["primary_grid"]["cells"]["HML"]["recent"] = "an_era_that_does_not_exist"
    broken = specification_from_mapping(raw, source_path=default_specification_path())
    with pytest.raises(FactorDecayError, match="which sample_policy does not define"):
        resolve_grid(broken)


def test_a_grid_whose_roles_drift_from_the_code_is_refused() -> None:
    raw = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    raw["parameters"]["primary_grid"]["era_roles"] = ["original_sample", "recent"]
    broken = specification_from_mapping(raw, source_path=default_specification_path())
    with pytest.raises(FactorDecayError, match="this module implements"):
        resolve_grid(broken)


# --------------------------------------------------------------------------- #
# Cell statistics
# --------------------------------------------------------------------------- #


def test_cell_statistics_match_an_independent_numpy_computation() -> None:
    series = monthly_series("HML", start="1994-01", months=360, mean=0.003, sigma=0.028, seed=11)
    cell = cell_from(series, factor="HML", era_role="full_post_publication")

    percent = series.values * 100.0
    mean = float(np.mean(percent))
    sigma = float(np.std(percent, ddof=1))

    assert cell.observations == 360
    assert cell.mean_percent_per_month == pytest.approx(mean)
    assert cell.annualised_premium_percent == pytest.approx(12.0 * mean)
    assert cell.volatility_percent_per_month == pytest.approx(sigma)
    assert cell.annualised_volatility_percent == pytest.approx(math.sqrt(12.0) * sigma)
    assert cell.sharpe_annualised == pytest.approx(mean / sigma * math.sqrt(12.0))
    assert cell.conventional_t_statistic == pytest.approx(mean / (sigma / math.sqrt(360)))
    assert cell.conventional_standard_error_annual == pytest.approx(12.0 * sigma / math.sqrt(360))


def test_the_geometric_contribution_reproduces_the_terminal_wealth_path() -> None:
    """(1 + g)^T - 1 must equal the compounded return, or g is not a geometric mean."""
    series = monthly_series("CMA", start="1994-01", months=240, mean=0.002, sigma=0.02, seed=12)
    cell = cell_from(series, factor="CMA", era_role="full_post_publication")
    g = cell.geometric_mean_percent_per_month / 100.0
    assert (1.0 + g) ** 240 == pytest.approx(float(np.prod(1.0 + series.values)))
    assert cell.terminal_growth_multiple == pytest.approx(float(np.prod(1.0 + series.values)))
    # Variance drag: the geometric contribution is below the arithmetic premium.
    assert cell.arithmetic_geometric_gap_percent > 0.0


def test_the_minimum_detectable_effect_of_a_cell_uses_that_cells_own_window() -> None:
    """A short window must require a larger premium than a long one at equal vol."""
    short = cell_from(
        monthly_series("RMW", start="2014-01", months=72, mean=0.002, sigma=0.02, seed=13),
        factor="RMW",
        era_role="first_post_publication",
    )
    long = cell_from(
        monthly_series("RMW", start="1963-07", months=606, mean=0.002, sigma=0.02, seed=13),
        factor="RMW",
        era_role="original_sample",
    )
    assert short.mde_one_sided_percent_per_year > long.mde_one_sided_percent_per_year
    assert short.power_at_materiality < long.power_at_materiality
    assert 0.0 < short.power_at_materiality < 1.0


def test_the_hac_minimum_detectable_effect_is_reported_beside_the_iid_one() -> None:
    """They differ exactly when the series is autocorrelated, which is the point."""
    rng = np.random.default_rng(14)
    innovations = rng.normal(0.002, 0.02, size=400)
    values = np.zeros(400)
    for t in range(1, 400):
        values[t] = 0.4 * values[t - 1] + innovations[t]
    series = MonthlySeries(
        name="UMD",
        periods=tuple(shift_period("1990-01", i) for i in range(400)),
        values=values,
        source_dataset_id="fixture",
        source_column="Mom",
    )
    cell = cell_from(series, factor="UMD", era_role="full_post_publication")
    assert cell.mde_one_sided_hac_percent_per_year > cell.mde_one_sided_percent_per_year
    assert cell.effective_sample_size < cell.observations


def test_every_declared_block_length_is_bootstrapped_and_labelled() -> None:
    series = monthly_series("HML", start="1994-01", months=200, mean=0.003, sigma=0.03, seed=15)
    cell = cell_from(series, factor="HML", era_role="full_post_publication")
    premium = [b for b in cell.bootstraps if b.statistic == "annualised_premium_percent"]
    sources = [b.block_length_source for b in premium]
    assert sources == ["frozen", "predeclared-neighbour", "politis-white-automatic"]
    assert premium[0].block_length == 12.0
    assert premium[-1].block_length >= 1.0
    for interval in premium:
        assert interval.lower_95 <= interval.lower_90 <= interval.upper_90 <= interval.upper_95
        assert interval.one_sided_lower_95 == pytest.approx(interval.lower_90)
    assert any(b.statistic == "annualised_sharpe" for b in cell.bootstraps)


# --------------------------------------------------------------------------- #
# The Phase 1 second-moment band
# --------------------------------------------------------------------------- #


def test_the_phase_1_band_moves_sharpe_and_volatility_but_never_the_mean() -> None:
    """HML's band is 3.03%: sigma in [0.9697, 1.0303] x sigma, Sharpe inverted."""
    band = _second_moment_band(
        "HML", annual_volatility=10.0, annual_sharpe=0.5, mde=3.0, settings=settings()
    )
    assert band is not None and band.measured
    assert band.volatility_low == pytest.approx(10.0 * (1 - 0.0303))
    assert band.volatility_high == pytest.approx(10.0 * (1 + 0.0303))
    assert band.sharpe_low == pytest.approx(0.5 / 1.0303)
    assert band.sharpe_high == pytest.approx(0.5 / 0.9697)
    assert band.mde_low == pytest.approx(3.0 * 0.9697)
    assert "systematic, not sampling" in band.note


def test_rmw_carries_the_larger_band_and_cma_carries_none() -> None:
    rmw = _second_moment_band(
        "RMW", annual_volatility=8.0, annual_sharpe=0.4, mde=2.0, settings=settings()
    )
    cma = _second_moment_band(
        "CMA", annual_volatility=7.0, annual_sharpe=0.5, mde=2.0, settings=settings()
    )
    assert rmw is not None and rmw.relative_band == pytest.approx(0.0509)
    assert cma is None, "CMA reproduced inside the Phase 1 gate, so it carries no band"


def test_umd_is_recorded_as_unmeasured_rather_than_as_a_band_of_zero() -> None:
    """The momentum file was never gated against a printed table."""
    band = _second_moment_band(
        "UMD", annual_volatility=16.0, annual_sharpe=0.5, mde=4.0, settings=settings()
    )
    assert band is not None
    assert band.measured is False
    assert math.isnan(band.relative_band)
    assert "UNMEASURED" in band.note


def test_a_cell_carries_its_factors_band(committed_spec: Specification) -> None:
    series = monthly_series("RMW", start="1963-07", months=606, mean=0.002, sigma=0.022, seed=16)
    cell = cell_from(series, factor="RMW", era_role="original_sample")
    band = cell.second_moment_band
    assert band is not None
    assert band.sharpe_low < cell.sharpe_annualised < band.sharpe_high
    assert band.volatility_low < cell.annualised_volatility_percent < band.volatility_high


# --------------------------------------------------------------------------- #
# Cost illustration
# --------------------------------------------------------------------------- #


def test_cost_illustration_is_the_repository_turnover_rule_applied_to_declared_turnover(
    committed_spec: Specification,
) -> None:
    """HML: k=1.0 x 1.2% = 1.2 bp/month = 0.144 pp/yr optimistic;
    k=1.7 x 7.2% = 12.24 bp/month = 1.4688 pp/yr pessimistic.
    UMD: 1.0 x 27.5 = 27.5 bp/month = 3.30 pp/yr; 1.7 x 91.5 = 155.55 bp = 18.666 pp/yr.
    """
    parameters = committed_spec.parameters
    assert isinstance(parameters, Mapping)

    hml = cost_illustration("HML", parameters)
    assert hml.cost_optimistic_annual_percent == pytest.approx(0.144)
    assert hml.cost_pessimistic_annual_percent == pytest.approx(1.4688)
    assert hml.retail_implementable_at_pessimistic is True

    umd = cost_illustration("UMD", parameters)
    assert umd.cost_optimistic_annual_percent == pytest.approx(3.30)
    assert umd.cost_pessimistic_annual_percent == pytest.approx(18.666)
    assert umd.retail_implementable_at_optimistic is True
    assert umd.retail_implementable_at_pessimistic is False, (
        "91.5% one-sided monthly turnover is far above the retail limit"
    )
    assert umd.cost_pessimistic_annual_percent > 10.0 * hml.cost_pessimistic_annual_percent


def test_the_cost_illustration_refuses_a_specification_that_drifts_from_the_code() -> None:
    raw = yaml.safe_load(default_specification_path().read_text(encoding="utf-8"))
    raw["parameters"]["cost_illustration"]["k_pessimistic"] = 2.5
    drifted = specification_from_mapping(raw, source_path=default_specification_path())
    parameters = drifted.parameters
    assert isinstance(parameters, Mapping)
    with pytest.raises(FactorDecayError, match="One of"):
        cost_illustration("HML", parameters)


# --------------------------------------------------------------------------- #
# The frozen rejection rule
# --------------------------------------------------------------------------- #


def roles(
    *, full_mean: float, original_mean: float, recent_mean: float, sigma: float, seed: int
) -> dict[str, CellStatistics]:
    """One cell per era role, with the three means the falsifier actually reads."""
    plan = {
        "original_sample": (original_mean, 342, "1963-07"),
        "first_post_publication": (full_mean, 120, "1994-01"),
        "full_post_publication": (full_mean, 384, "1994-01"),
        "recent": (recent_mean, 120, "2016-01"),
        "common_period": (recent_mean, 144, "2014-01"),
    }
    out: dict[str, CellStatistics] = {}
    for role, (mean, months, start) in plan.items():
        series = monthly_series(
            "HML", start=start, months=months, mean=mean, sigma=sigma, seed=seed
        )
        out[role] = cell_from(series, factor="HML", era_role=role, seed=seed)
    return out


def test_clause_a_fires_on_a_non_positive_post_publication_premium() -> None:
    by_role = roles(
        full_mean=-0.002, original_mean=0.004, recent_mean=-0.003, sigma=0.03, seed=21
    )
    verdict = apply_rejection_rule("HML", by_role, materiality=2.0)
    assert verdict.status is ResultStatus.REJECTED
    assert any(clause.startswith("(a)") for clause in verdict.clauses_fired)


def test_clause_b_fires_when_even_a_favourable_draw_is_immaterial() -> None:
    """A tiny premium on a tiny volatility: positive, but negligible under any draw."""
    by_role = roles(
        full_mean=0.00005, original_mean=0.004, recent_mean=0.00005, sigma=0.0015, seed=22
    )
    verdict = apply_rejection_rule("HML", by_role, materiality=2.0)
    assert verdict.status is ResultStatus.REJECTED
    assert any(clause.startswith("(b)") for clause in verdict.clauses_fired)


def test_clause_c_fires_only_when_decay_is_both_large_and_continuing() -> None:
    large_decay_but_recent_positive = roles(
        full_mean=0.0005, original_mean=0.006, recent_mean=0.004, sigma=0.02, seed=23
    )
    fired = apply_rejection_rule("HML", large_decay_but_recent_positive, materiality=2.0)
    assert not any(clause.startswith("(c)") for clause in fired.clauses_fired), (
        "decay alone is not a falsifier; the recent era must also be non-positive"
    )

    both = roles(full_mean=0.0004, original_mean=0.006, recent_mean=-0.002, sigma=0.02, seed=23)
    verdict = apply_rejection_rule("HML", both, materiality=2.0)
    assert verdict.status is ResultStatus.REJECTED
    assert any(clause.startswith("(c)") for clause in verdict.clauses_fired)


def test_a_wide_interval_containing_zero_is_unresolved_and_not_rejected() -> None:
    """The frozen rule says so explicitly: a failed 95% test is NOT a falsifier."""
    by_role = roles(
        full_mean=0.0025, original_mean=0.004, recent_mean=0.002, sigma=0.045, seed=24
    )
    verdict = apply_rejection_rule("HML", by_role, materiality=2.0)
    assert verdict.status is ResultStatus.UNRESOLVED
    assert verdict.clauses_fired == ()
    assert "cannot tell" in verdict.reasoning
    assert "80% power" in verdict.reasoning


def test_a_material_premium_whose_interval_excludes_zero_is_exploratory_and_no_more() -> None:
    by_role = roles(full_mean=0.005, original_mean=0.006, recent_mean=0.004, sigma=0.025, seed=25)
    verdict = apply_rejection_rule("HML", by_role, materiality=2.0)
    assert verdict.status is ResultStatus.EXPLORATORY
    assert verdict.status not in CONFIRMATORY_ONLY_STATUSES, (
        "an exploratory run may never promote its own finding"
    )
    assert "permits nothing else" in verdict.reasoning


# --------------------------------------------------------------------------- #
# Multiple testing over the family
# --------------------------------------------------------------------------- #


def make_cells(p_targets: Sequence[float]) -> list[CellStatistics]:
    """Cells whose HAC t-statistics land near the requested one-sided p-values."""
    cells: list[CellStatistics] = []
    for index, target in enumerate(p_targets):
        z = _normal_quantile(0.95) if target <= 0.05 else 0.0
        sigma = 0.03
        months = 240
        mean = z * sigma / math.sqrt(months) if target <= 0.05 else 0.0
        series = monthly_series(
            f"F{index}", start="1994-01", months=months, mean=mean, sigma=sigma, seed=100 + index
        )
        cells.append(cell_from(series, factor="HML", era_role=f"role{index}", seed=100 + index))
    return cells


def test_the_correction_is_applied_to_the_whole_family_and_never_loosens_a_p_value() -> None:
    cells = make_cells([0.01, 0.01, 0.5, 0.5, 0.5])
    grid = correct_grid(cells, alpha=0.10)
    assert len(grid.keys) == 5
    for raw, bh, holm in zip(grid.p_values, grid.bh_adjusted, grid.holm_adjusted, strict=True):
        assert bh >= raw - 1e-12, "an adjusted p-value can never be smaller than the raw one"
        assert holm >= bh - 1e-12, "Holm controls FWER, so it is never more permissive than BH"
    assert sum(grid.holm_rejected) <= sum(grid.bh_rejected)


def test_the_family_is_the_twenty_predeclared_cells(committed_spec: Specification) -> None:
    """The correction must not be applied to whichever subset happened to survive."""
    grid = resolve_grid(committed_spec)
    assert len(grid) == 20
    assert len({cell.key for cell in grid}) == 20


# --------------------------------------------------------------------------- #
# Hostile-test helpers
# --------------------------------------------------------------------------- #


def test_dropping_the_best_month_removes_exactly_the_largest_observation() -> None:
    values = np.asarray([0.01, 0.09, -0.02, 0.03], dtype=np.float64)
    periods = ("2000-01", "2000-02", "2000-03", "2000-04")
    remaining, dropped = _drop_best_month(values, periods)
    assert dropped == "2000-02"
    assert remaining.tolist() == pytest.approx([0.01, -0.02, 0.03])


def test_dropping_the_best_calendar_year_uses_the_compounded_year_not_the_best_month() -> None:
    """2000 holds the single best month; 2001 compounds to more. The year wins.

    2000: (1.09)(0.90) - 1 = -0.019.  2001: (1.05)(1.05) - 1 = +0.1025.
    """
    values = np.asarray([0.09, -0.10, 0.05, 0.05], dtype=np.float64)
    periods = ("2000-01", "2000-02", "2001-01", "2001-02")
    remaining, year = _drop_best_calendar_year(values, periods)
    assert year == "2001"
    assert remaining.tolist() == pytest.approx([0.09, -0.10])


def test_a_single_year_era_has_no_best_year_to_drop() -> None:
    values = np.asarray([0.01, 0.02], dtype=np.float64)
    remaining, year = _drop_best_calendar_year(values, ("2000-01", "2000-02"))
    assert year is None
    assert remaining.tolist() == pytest.approx([0.01, 0.02])
