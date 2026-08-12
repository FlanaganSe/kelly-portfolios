"""Experiment 005: regional replication of the post-publication factor premia.

Experiment 001 left HML, UMD and RMW ``unresolved`` because 16 of its 20 cells
held a premium smaller than their own window could detect at 80% power. More
United States history cannot fix that; the US post-publication window is the
length it is. Independent regions are the only way to add effective sample size
without waiting decades, so this experiment re-runs Experiment 001's
post-publication grid for HML, RMW and CMA across the US, developed-ex-US and
emerging files, over the *same* frozen eras, and pools them.

What this experiment measures, and why it is the point
------------------------------------------------------
Three regions of ``T`` months supply ``3T`` independent region-months only if
they are uncorrelated. They are not. **The effective sample size that pooling
actually buys is measured here rather than assumed**, and it decides the frozen
falsifier's branch (b): if the measured pooled minimum detectable effect is
still above the 2.0 pp/yr materiality threshold, no currently available public
factor data can sign these premia, and the factor programme closes on public
data rather than staying ``unresolved``.

Deliberate reuse of Experiment 001
----------------------------------
Every per-cell statistic is computed by importing
:func:`~portfolio_edge.experiments.exp_001_factor_decay.compute_cell` and its
settings object rather than by re-deriving them. That is not laziness: it is the
only way to guarantee the regional numbers are comparable to the published US
grid cell for cell. The era boundaries are read from this experiment's own
frozen specification and asserted against Experiment 001's, so a boundary cannot
drift between the two.

Three constraints inherited from upstream
-----------------------------------------
1. **The Phase 1 gate came back UNRESOLVED, not PASS.** US HML and US RMW carry
   a systematic band of 3.03% and 5.09% on their volatility. It is carried
   through everything that divides by a volatility, including the pooled MDE that
   decides branch (b), and reported separately from every sampling interval.
2. **The two regional files were never gated against any printed table.** Their
   second moments are *unmeasured*, which is weaker than a band of zero.
3. **Power is the point.** Every cell reports what it could have detected, and
   every pooled cell reports the effective sample size it actually achieved.

Run it::

    uv run python -m portfolio_edge.experiments.exp_005_regional_replication --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.core.statistics import sharpe_standard_error
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.exp_001_factor_decay import (
    CellStatistics,
    InferenceSettings,
    MonthlySeries,
    Window,
    compute_cell,
    minimum_detectable_effect,
    one_sided_p_value,
    power_to_detect,
    window_series,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_count, month_index
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.runner import RunOutcome, run_experiment
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import optimal_block_length, stationary_bootstrap_indices
from portfolio_edge.inference.hac import hac_mean, long_run_variance, newey_west_lag_count
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "ERA_ROLES",
    "FACTORS",
    "REGIONS",
    "EffectiveSampleSize",
    "FactorVerdict",
    "PanelInterval",
    "PooledCell",
    "RegionalGridCell",
    "RegionalReplicationError",
    "apply_rejection_rule",
    "build_registry",
    "calendar_year_contributions",
    "cross_region_bootstrap",
    "default_specification_path",
    "effective_sample_size",
    "joint_panel_bootstrap",
    "main",
    "pooled_composite",
    "resolve_grid",
    "run",
]

ENTRY_POINT: Final = "exp_005_regional_replication"

#: The three factors under test. UMD is absent because this repository manifests
#: no regional momentum file; see the specification's `umd_is_not_covered`.
FACTORS: Final = ("HML", "RMW", "CMA")

#: The three non-overlapping regions, in the order the specification lists them.
#: `developed_ex_us` and not `developed`: the latter file INCLUDES the US.
REGIONS: Final = ("us", "developed_ex_us", "emerging")

#: The three post-publication era roles. `common_period` is excluded on purpose:
#: for RMW and CMA it is byte-for-byte `full_post_publication`, and a
#: multiple-testing family that holds one test twice is not a family.
ERA_ROLES: Final = ("first_post_publication", "full_post_publication", "recent")

MONTHS_PER_YEAR: Final = 12.0

#: Harvey, Liu and Zhu (2016)'s structural estimate of the mean return of a
#: genuinely true factor, 0.55%/month gross at an imposed 15% volatility.
TRUE_FACTOR_REFERENCE_ANNUAL_PERCENT: Final = 6.6

FloatArray = NDArray[np.float64]


class RegionalReplicationError(RuntimeError):
    """The experiment could not be attempted against the declared vintages."""


def _json_float(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``."""
    return None if math.isnan(value) or math.isinf(value) else value


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise RegionalReplicationError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise RegionalReplicationError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise RegionalReplicationError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise RegionalReplicationError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise RegionalReplicationError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    return tuple(str(item) for item in items)


def _integers(values: Sequence[JsonValue], *, where: str) -> tuple[int, ...]:
    out: list[int] = []
    for index, item in enumerate(values):
        if isinstance(item, bool) or not isinstance(item, int):
            raise RegionalReplicationError(f"{where}[{index}] must be an integer, got {item!r}")
        out.append(item)
    return tuple(out)


# --------------------------------------------------------------------------- #
# The grid
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionalGridCell:
    """One predeclared (factor, region, era role) cell of the 27-cell family."""

    factor: str
    region: str
    era_role: str
    era_name: str
    start: str
    end: str

    @property
    def key(self) -> str:
        return f"{self.factor}/{self.region}/{self.era_role}"


def resolve_grid(specification: Specification) -> tuple[RegionalGridCell, ...]:
    """Build the predeclared 3 x 3 x 3 grid from the frozen specification.

    The family is read from the frozen document rather than constructed here so
    that the multiple-testing correction applies to what was declared, not to
    whatever the code happened to loop over.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    grid = _mapping(_at(parameters, "primary_grid", where="parameters"), where="primary_grid")
    roles = _strings(grid, "era_roles", where="primary_grid")
    if roles != ERA_ROLES:
        raise RegionalReplicationError(
            f"primary_grid.era_roles is {roles}, but this module implements {ERA_ROLES}"
        )
    regions = _strings(grid, "regions", where="primary_grid")
    if regions != REGIONS:
        raise RegionalReplicationError(
            f"primary_grid.regions is {regions}, but this module implements {REGIONS}"
        )
    cells_by_factor = _mapping(_at(grid, "cells", where="primary_grid"), where="primary_grid.cells")
    eras = {era.name: era for era in specification.sample_policy.eras}

    cells: list[RegionalGridCell] = []
    for factor in FACTORS:
        if factor not in cells_by_factor:
            raise RegionalReplicationError(f"primary_grid.cells has no entry for {factor!r}")
        by_role = _mapping(cells_by_factor[factor], where=f"primary_grid.cells.{factor}")
        for role in ERA_ROLES:
            era_name = _text(by_role, role, where=f"primary_grid.cells.{factor}")
            era = eras.get(era_name)
            if era is None:
                raise RegionalReplicationError(
                    f"primary_grid.cells.{factor}.{role} names era {era_name!r}, "
                    f"which sample_policy does not define; known: {sorted(eras)}"
                )
            for region in REGIONS:
                cells.append(
                    RegionalGridCell(
                        factor=factor,
                        region=region,
                        era_role=role,
                        era_name=era.name,
                        start=era.start,
                        end=era.end,
                    )
                )
    expected = len(FACTORS) * len(ERA_ROLES) * len(REGIONS)
    if len(cells) != expected:
        raise RegionalReplicationError(f"expected {expected} cells, built {len(cells)}")
    return tuple(cells)


# --------------------------------------------------------------------------- #
# Pooling
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class AlignedPanel:
    """Three regional series of one factor, on the months all three are observed.

    ``values`` is ``(months, regions)`` in decimal units. Nothing is
    forward-filled: a month absent from any region is absent from the panel, and
    ``dropped_months`` records how many that was rather than repairing it.
    """

    factor: str
    era_name: str
    regions: tuple[str, ...]
    periods: tuple[str, ...]
    values: FloatArray
    dropped_months: int
    per_region_available: Mapping[str, int]
    findings: tuple[str, ...]

    @property
    def months(self) -> int:
        return len(self.periods)


def align_panel(
    windows: Mapping[str, Window], *, factor: str, era_name: str, regions: Sequence[str]
) -> AlignedPanel:
    """Intersect the regional windows on their period labels, reporting the loss."""
    if not regions:
        raise RegionalReplicationError("a panel needs at least one region")
    by_region = {region: dict(zip(windows[region].periods, windows[region].values, strict=True))
                 for region in regions}
    common = sorted(set.intersection(*(set(item) for item in by_region.values())))
    union = set().union(*(set(item) for item in by_region.values()))
    values = np.asarray(
        [[by_region[region][period] for region in regions] for period in common],
        dtype=np.float64,
    ).reshape(len(common), len(regions))

    findings: list[str] = []
    for region in regions:
        findings.extend(windows[region].findings)
    if len(common) != len(union):
        findings.append(
            f"{factor}/{era_name}: the cross-region intersection dropped "
            f"{len(union) - len(common)} of {len(union)} months; the regions do not "
            "cover the same calendar here"
        )
    return AlignedPanel(
        factor=factor,
        era_name=era_name,
        regions=tuple(regions),
        periods=tuple(common),
        values=values,
        dropped_months=len(union) - len(common),
        per_region_available={region: len(by_region[region]) for region in regions},
        findings=tuple(findings),
    )


def pooled_composite(panel: FloatArray, weights: FloatArray) -> FloatArray:
    """The weighted cross-region composite, ``(months,)`` from ``(months, regions)``."""
    if panel.ndim != 2:
        raise RegionalReplicationError(f"panel must be 2-dimensional, got shape {panel.shape}")
    if weights.size != panel.shape[1]:
        raise RegionalReplicationError(
            f"{weights.size} weights for {panel.shape[1]} regions"
        )
    return np.asarray(panel @ weights, dtype=np.float64)


@dataclass(frozen=True, slots=True, kw_only=True)
class EffectiveSampleSize:
    """How much independent evidence pooling correlated regions actually bought.

    The decisive measurement of this experiment. ``naive_region_months`` is what
    treating the regions as independent samples would have claimed; every other
    figure is measured from the realised sample.
    """

    months: int
    regions: int
    mean_pairwise_correlation: float
    mean_region_variance: float
    composite_variance: float
    composite_long_run_variance: float
    effective_regions: float
    effective_region_months_iid: float
    effective_region_months_hac: float
    naive_region_months: int
    inflation_avoided_iid: float
    inflation_avoided_hac: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "months": self.months,
            "regions": self.regions,
            "mean_pairwise_cross_region_correlation": _json_float(
                self.mean_pairwise_correlation
            ),
            "mean_region_variance_percent_squared": self.mean_region_variance,
            "composite_variance_percent_squared": self.composite_variance,
            "composite_long_run_variance_percent_squared": self.composite_long_run_variance,
            "effective_regions": _json_float(self.effective_regions),
            "effective_region_months_iid": _json_float(self.effective_region_months_iid),
            "effective_region_months_hac": _json_float(self.effective_region_months_hac),
            "naive_region_months_if_independent": self.naive_region_months,
            "inflation_avoided_iid": _json_float(self.inflation_avoided_iid),
            "inflation_avoided_hac": _json_float(self.inflation_avoided_hac),
        }


def effective_sample_size(panel: FloatArray, composite: FloatArray) -> EffectiveSampleSize:
    """Measure the independent evidence in a correlated regional panel.

    ``effective_regions = mean_i var(r_i) / var(composite)``. With equal weights
    and equal variances this is exactly ``k / (1 + (k - 1) * rho_bar)``: it
    returns ``k`` when the regions are uncorrelated and ``1`` when they move
    together. Multiplying by the month count expresses the same thing in
    independent single-region months, which is directly comparable to an
    Experiment 001 observation count.

    The HAC variant divides by the composite's Newey-West long-run variance
    instead of its sample variance, folding serial dependence in as well. It is
    the honest measure and is normally the smallest of the three.

    **This is a sample statistic, not a constant.** ``k`` is its value under zero
    *population* correlation, and a finite sample whose regions happen to
    correlate negatively returns more than ``k``. That is why
    :func:`joint_panel_bootstrap` puts an interval on it rather than reporting
    the point estimate alone.
    """
    if panel.ndim != 2:
        raise RegionalReplicationError(f"panel must be 2-dimensional, got shape {panel.shape}")
    months, regions = panel.shape
    if months < 2 or regions < 1:
        raise RegionalReplicationError(
            f"need at least two months and one region, got {months} x {regions}"
        )
    region_variances = np.var(panel, axis=0, ddof=1)
    mean_region_variance = float(np.mean(region_variances))
    composite_variance = float(np.var(composite, ddof=1))
    centred = composite - float(np.mean(composite))
    long_run = long_run_variance(centred, n_lags=newey_west_lag_count(months))

    if regions > 1:
        correlation = np.atleast_2d(np.asarray(np.corrcoef(panel, rowvar=False), dtype=np.float64))
        upper = correlation[np.triu_indices(regions, k=1)]
        mean_correlation = float(np.mean(upper)) if upper.size else float("nan")
    else:
        mean_correlation = float("nan")

    effective_regions = (
        mean_region_variance / composite_variance if composite_variance > 0.0 else float("nan")
    )
    effective_iid = months * effective_regions
    effective_hac = (
        months * mean_region_variance / long_run if long_run > 0.0 else float("nan")
    )
    naive = regions * months
    return EffectiveSampleSize(
        months=months,
        regions=regions,
        mean_pairwise_correlation=mean_correlation,
        mean_region_variance=mean_region_variance,
        composite_variance=composite_variance,
        composite_long_run_variance=long_run,
        effective_regions=effective_regions,
        effective_region_months_iid=effective_iid,
        effective_region_months_hac=effective_hac,
        naive_region_months=naive,
        inflation_avoided_iid=naive / effective_iid if effective_iid > 0.0 else float("nan"),
        inflation_avoided_hac=naive / effective_hac if effective_hac > 0.0 else float("nan"),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class BootstrapSummary:
    """One resampling of the pooled premium, at one block length, one scheme."""

    scheme: str
    valid: bool
    block_length: float
    block_length_source: str
    point_estimate: float
    lower_90: float
    upper_90: float
    lower_95: float
    upper_95: float
    one_sided_lower_95: float
    standard_error: float
    n_resamples: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "scheme": self.scheme,
            "valid": self.valid,
            "block_length": self.block_length,
            "block_length_source": self.block_length_source,
            "point_estimate": self.point_estimate,
            "two_sided_90": [self.lower_90, self.upper_90],
            "two_sided_95": [self.lower_95, self.upper_95],
            "one_sided_lower_95": self.one_sided_lower_95,
            "bootstrap_standard_error": self.standard_error,
            "n_resamples": self.n_resamples,
        }


def _summarise_replicates(
    replicates: FloatArray,
    *,
    scheme: str,
    valid: bool,
    block_length: float,
    block_length_source: str,
    point_estimate: float,
    n_resamples: int,
) -> BootstrapSummary:
    quantiles = np.asarray(
        np.quantile(replicates, [0.05, 0.95, 0.025, 0.975]), dtype=np.float64
    )
    low_90, high_90, low_95, high_95 = (float(value) for value in quantiles)
    return BootstrapSummary(
        scheme=scheme,
        valid=valid,
        block_length=block_length,
        block_length_source=block_length_source,
        point_estimate=point_estimate,
        lower_90=low_90,
        upper_90=high_90,
        lower_95=low_95,
        upper_95=high_95,
        one_sided_lower_95=low_90,
        standard_error=float(np.std(replicates, ddof=1)),
        n_resamples=n_resamples,
    )


def cross_region_bootstrap(
    panel: FloatArray,
    weights: FloatArray,
    *,
    block_length: float,
    block_length_source: str,
    n_resamples: int,
    rng: np.random.Generator,
    joint: bool,
) -> BootstrapSummary:
    """Block-bootstrap the pooled annualised premium, jointly or independently.

    ``joint=True`` draws **one** set of time indices and applies it to every
    region at once, so contemporaneous cross-region dependence survives the
    resample. Because the composite is a fixed linear combination of
    contemporaneous rows, resampling the composite series with those indices is
    algebraically identical to resampling the panel and then compositing, and
    that identity is what the implementation uses.

    ``joint=False`` draws an independent index set per region. **That is
    invalid** for correlated regions: it destroys the contemporaneous
    correlation, makes the composite behave like an average of independent
    samples and narrows the interval. It is computed only so the size of that
    error can be reported rather than asserted.
    """
    months, regions = panel.shape
    composite = pooled_composite(panel, weights)
    point = float(np.mean(composite)) * MONTHS_PER_YEAR * 100.0

    if joint:
        indices = stationary_bootstrap_indices(months, block_length, n_resamples, rng)
        means = composite[indices].mean(axis=1)
    else:
        means = np.zeros(n_resamples, dtype=np.float64)
        for column in range(regions):
            indices = stationary_bootstrap_indices(months, block_length, n_resamples, rng)
            means = means + weights[column] * panel[:, column][indices].mean(axis=1)

    replicates = np.asarray(means, dtype=np.float64) * MONTHS_PER_YEAR * 100.0
    return _summarise_replicates(
        replicates,
        scheme="cross-region-joint" if joint else "per-region-independent-INVALID",
        valid=joint,
        block_length=block_length,
        block_length_source=block_length_source,
        point_estimate=point,
        n_resamples=n_resamples,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PanelInterval:
    """A joint block-bootstrap interval for a statistic of the whole panel."""

    statistic: str
    point_estimate: float
    lower_90: float
    upper_90: float
    standard_error: float
    block_length: float
    n_resamples: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "statistic": self.statistic,
            "point_estimate": _json_float(self.point_estimate),
            "two_sided_90": [_json_float(self.lower_90), _json_float(self.upper_90)],
            "bootstrap_standard_error": _json_float(self.standard_error),
            "block_length": self.block_length,
            "n_resamples": self.n_resamples,
        }


def joint_panel_bootstrap(
    panel: FloatArray,
    weights: FloatArray,
    statistic: object,
    *,
    name: str,
    block_length: float,
    n_resamples: int,
    rng: np.random.Generator,
) -> PanelInterval:
    """Block-bootstrap a statistic of the whole ``(months, regions)`` panel, jointly.

    The same block of time indices is applied to every region, so the resampled
    panel keeps its contemporaneous cross-region structure. This is what puts an
    interval on the effective sample size and on the pooled minimum detectable
    effect, both of which are functions of the panel's covariance rather than of
    the composite alone, and neither of which is a constant.
    """
    months = panel.shape[0]
    indices = stationary_bootstrap_indices(months, block_length, n_resamples, rng)
    call = statistic  # a plain callable; typed loosely so a closure can be passed
    replicates = np.asarray(
        [call(panel[row], weights) for row in indices],  # type: ignore[operator]
        dtype=np.float64,
    )
    finite = replicates[np.isfinite(replicates)]
    low, high = (
        (float(np.quantile(finite, 0.05)), float(np.quantile(finite, 0.95)))
        if finite.size > 1
        else (float("nan"), float("nan"))
    )
    return PanelInterval(
        statistic=name,
        point_estimate=float(call(panel, weights)),  # type: ignore[operator]
        lower_90=low,
        upper_90=high,
        standard_error=float(np.std(finite, ddof=1)) if finite.size > 1 else float("nan"),
        block_length=block_length,
        n_resamples=n_resamples,
    )


def _effective_regions_statistic(panel: FloatArray, weights: FloatArray) -> float:
    composite = pooled_composite(panel, weights)
    denominator = float(np.var(composite, ddof=1))
    if denominator <= 0.0:
        return float("nan")
    return float(np.mean(np.var(panel, axis=0, ddof=1))) / denominator


def _mde_statistic(panel: FloatArray, weights: FloatArray) -> float:
    """The pooled 80%-power MDE in pp/yr, as a function of the panel alone."""
    composite = pooled_composite(panel, weights) * 100.0
    sigma = float(np.std(composite, ddof=1))
    if sigma <= 0.0:
        return float("nan")
    return MONTHS_PER_YEAR * minimum_detectable_effect(
        standard_error=sigma / math.sqrt(composite.size), power=0.80, one_sided=True
    )


# --------------------------------------------------------------------------- #
# Episode concentration
# --------------------------------------------------------------------------- #


def calendar_year_contributions(
    values: FloatArray, periods: Sequence[str]
) -> tuple[tuple[str, float, float], ...]:
    """Per calendar year: its compounded return and its share of the total premium.

    The share is that year's contribution to ``12 * mean(values)``, i.e.
    ``sum of the year's monthly returns / sum of all monthly returns``. It is
    signed and can exceed 1 or be negative, which is the honest arithmetic when a
    premium lives in one year.
    """
    total = float(np.sum(values))
    years = sorted({period[:4] for period in periods})
    out: list[tuple[str, float, float]] = []
    for year in years:
        mask = np.asarray([period[:4] == year for period in periods], dtype=bool)
        compounded = float(np.prod(1.0 + values[mask]) - 1.0)
        share = float(np.sum(values[mask]) / total) if total != 0.0 else float("nan")
        out.append((year, compounded, share))
    return tuple(out)


def _drop_best_calendar_year(
    values: FloatArray, periods: Sequence[str]
) -> tuple[FloatArray, str | None]:
    years = sorted({period[:4] for period in periods})
    if len(years) < 2:
        return values, None
    best_year: str | None = None
    best_return = -math.inf
    for year in years:
        mask = np.asarray([period[:4] == year for period in periods], dtype=bool)
        total = float(np.prod(1.0 + values[mask]) - 1.0)
        if total > best_return:
            best_return, best_year = total, year
    keep = np.asarray([period[:4] != best_year for period in periods], dtype=bool)
    return values[keep], best_year


def _annualised_premium_percent(series: FloatArray) -> float:
    return float(np.mean(series)) * MONTHS_PER_YEAR * 100.0


# --------------------------------------------------------------------------- #
# The pooled cell
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PooledCell:
    """Everything reported for one factor pooled across regions over one era."""

    factor: str
    era_role: str
    era_name: str
    start: str
    end: str
    regions: tuple[str, ...]
    weights: tuple[float, ...]
    weighting: str
    months: int
    first_observation: str
    last_observation: str
    dropped_months: int
    findings: tuple[str, ...]

    annualised_premium_percent: float
    annualised_volatility_percent: float
    sharpe_annualised: float
    sharpe_standard_error_annualised: float

    conventional_standard_error_annual: float
    hac_standard_error_annual: float
    hac_t_statistic: float
    hac_lag_count: int
    one_sided_p_value_hac: float

    mde_one_sided_percent_per_year: float
    mde_one_sided_hac_percent_per_year: float
    power_at_materiality: float
    power_at_true_factor_reference: float

    sample: EffectiveSampleSize
    bootstraps: tuple[BootstrapSummary, ...]
    panel_intervals: tuple[PanelInterval, ...]
    per_region_premium: Mapping[str, float]
    year_contributions: tuple[tuple[str, float, float], ...]
    best_calendar_year: str | None
    premium_without_best_year: float | None
    band_sharpe: tuple[float, float] | None
    band_mde: tuple[float, float] | None

    @property
    def joint_bootstrap(self) -> BootstrapSummary:
        for item in self.bootstraps:
            if item.valid and item.block_length_source == "frozen":
                return item
        raise RegionalReplicationError(f"{self.factor}/{self.era_name} has no joint bootstrap")

    def panel_interval_named(self, statistic: str) -> PanelInterval | None:
        for item in self.panel_intervals:
            if item.statistic == statistic:
                return item
        return None

    @property
    def key(self) -> str:
        return f"{self.factor}/pooled/{self.era_role}"

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "era_role": self.era_role,
            "era": self.era_name,
            "start": self.start,
            "end": self.end,
            "regions": list(self.regions),
            "weights": list(self.weights),
            "weighting": self.weighting,
            "months": self.months,
            "first_observation": self.first_observation,
            "last_observation": self.last_observation,
            "months_dropped_by_intersection": self.dropped_months,
            "boundary_findings": list(self.findings),
            "annualised_premium_percent": self.annualised_premium_percent,
            "annualised_volatility_percent": self.annualised_volatility_percent,
            "sharpe_annualised": self.sharpe_annualised,
            "sharpe_standard_error_annualised": self.sharpe_standard_error_annualised,
            "conventional_standard_error_annual": self.conventional_standard_error_annual,
            "hac_standard_error_annual": self.hac_standard_error_annual,
            "hac_t_statistic": self.hac_t_statistic,
            "hac_lag_count": self.hac_lag_count,
            "one_sided_p_value_hac": self.one_sided_p_value_hac,
            "mde_one_sided_percent_per_year": self.mde_one_sided_percent_per_year,
            "mde_one_sided_hac_percent_per_year": self.mde_one_sided_hac_percent_per_year,
            "power_at_materiality": self.power_at_materiality,
            "power_at_true_factor_reference": self.power_at_true_factor_reference,
            "effective_sample_size": self.sample.to_json(),
            "panel_intervals": [item.to_json() for item in self.panel_intervals],
            "bootstraps": [item.to_json() for item in self.bootstraps],
            "per_region_annualised_premium_percent": dict(self.per_region_premium),
            "calendar_year_contributions": [
                {"year": year, "compounded_return": compounded, "share_of_premium": share}
                for year, compounded, share in self.year_contributions
            ],
            "best_calendar_year": self.best_calendar_year,
            "premium_without_best_calendar_year": self.premium_without_best_year,
            "sharpe_systematic_band_from_us_leg": (
                list(self.band_sharpe) if self.band_sharpe else None
            ),
            "mde_systematic_band_from_us_leg": list(self.band_mde) if self.band_mde else None,
        }


def _band_scaled_panel(
    panel: FloatArray, *, region_index: int, relative: float
) -> FloatArray:
    """One leg's deviations rescaled by ``1 + relative``, its mean untouched.

    A relative error ``u`` in a volatility is exactly a scale error of that size
    on the deviations. Phase 1 reproduced every mean, so the mean must not move.
    """
    scaled = panel.copy()
    column = scaled[:, region_index]
    centre = float(np.mean(column))
    scaled[:, region_index] = centre + (column - centre) * (1.0 + relative)
    return scaled


def compute_pooled(
    panel: AlignedPanel,
    *,
    era_role: str,
    start: str,
    end: str,
    weights: FloatArray,
    weighting: str,
    settings: InferenceSettings,
    rng: np.random.Generator,
    us_band: float,
    with_bootstrap: bool = True,
) -> PooledCell:
    """Every statistic this experiment reports for one pooled factor-era cell."""
    if panel.months < 24:
        raise RegionalReplicationError(
            f"{panel.factor}/{panel.era_name} holds {panel.months} aligned months; "
            "this experiment refuses to summarise a window shorter than two years"
        )
    values = panel.values
    composite = pooled_composite(values, weights)
    percent = composite * 100.0
    months = panel.months

    mean_month = float(np.mean(percent))
    sigma_month = float(np.std(percent, ddof=1))
    annual_premium = MONTHS_PER_YEAR * mean_month
    annual_volatility = math.sqrt(MONTHS_PER_YEAR) * sigma_month
    sharpe_month = mean_month / sigma_month if sigma_month > 0.0 else 0.0
    sharpe_annual = sharpe_month * math.sqrt(MONTHS_PER_YEAR)

    conventional_se_month = sigma_month / math.sqrt(months)
    hac = hac_mean(percent, n_lags=newey_west_lag_count(months))

    mde = MONTHS_PER_YEAR * minimum_detectable_effect(
        standard_error=conventional_se_month, power=settings.power_target, one_sided=True
    )
    mde_hac = MONTHS_PER_YEAR * minimum_detectable_effect(
        standard_error=hac.standard_error, power=settings.power_target, one_sided=True
    )

    sample = effective_sample_size(values * 100.0, percent)

    bootstraps: list[BootstrapSummary] = []
    panel_intervals: list[PanelInterval] = []
    if with_bootstrap:
        for name, function in (
            ("effective_regions", _effective_regions_statistic),
            ("pooled_mde_one_sided_percent_per_year", _mde_statistic),
        ):
            panel_intervals.append(
                joint_panel_bootstrap(
                    values,
                    weights,
                    function,
                    name=name,
                    block_length=settings.frozen_block_length,
                    n_resamples=settings.n_resamples,
                    rng=rng,
                )
            )
        automatic = optimal_block_length(composite)
        lengths: list[tuple[float, str]] = [(settings.frozen_block_length, "frozen")]
        lengths.extend(
            (length, "predeclared-neighbour") for length in settings.neighbour_block_lengths
        )
        lengths.append((automatic.stationary, "politis-white-automatic"))
        for length, source in lengths:
            bootstraps.append(
                cross_region_bootstrap(
                    values,
                    weights,
                    block_length=length,
                    block_length_source=source,
                    n_resamples=settings.n_resamples,
                    rng=rng,
                    joint=True,
                )
            )
        bootstraps.append(
            cross_region_bootstrap(
                values,
                weights,
                block_length=settings.frozen_block_length,
                block_length_source="frozen",
                n_resamples=settings.n_resamples,
                rng=rng,
                joint=False,
            )
        )

    without_best, best_year = _drop_best_calendar_year(composite, panel.periods)

    band_sharpe: tuple[float, float] | None = None
    band_mde: tuple[float, float] | None = None
    if us_band > 0.0 and "us" in panel.regions:
        index = panel.regions.index("us")
        low_high: list[tuple[float, float]] = []
        for signed in (-us_band, us_band):
            scaled = _band_scaled_panel(values, region_index=index, relative=signed)
            scaled_percent = pooled_composite(scaled, weights) * 100.0
            scaled_sigma = float(np.std(scaled_percent, ddof=1))
            scaled_sharpe = (
                float(np.mean(scaled_percent)) / scaled_sigma * math.sqrt(MONTHS_PER_YEAR)
                if scaled_sigma > 0.0
                else 0.0
            )
            scaled_mde = MONTHS_PER_YEAR * minimum_detectable_effect(
                standard_error=scaled_sigma / math.sqrt(months),
                power=settings.power_target,
                one_sided=True,
            )
            low_high.append((scaled_sharpe, scaled_mde))
        sharpes = sorted(item[0] for item in low_high)
        mdes = sorted(item[1] for item in low_high)
        band_sharpe = (sharpes[0], sharpes[-1])
        band_mde = (mdes[0], mdes[-1])

    per_region = {
        region: _annualised_premium_percent(values[:, index])
        for index, region in enumerate(panel.regions)
    }

    return PooledCell(
        factor=panel.factor,
        era_role=era_role,
        era_name=panel.era_name,
        start=start,
        end=end,
        regions=panel.regions,
        weights=tuple(float(value) for value in weights),
        weighting=weighting,
        months=months,
        first_observation=panel.periods[0],
        last_observation=panel.periods[-1],
        dropped_months=panel.dropped_months,
        findings=panel.findings,
        annualised_premium_percent=annual_premium,
        annualised_volatility_percent=annual_volatility,
        sharpe_annualised=sharpe_annual,
        sharpe_standard_error_annualised=(
            sharpe_standard_error(sharpe_month, months) * math.sqrt(MONTHS_PER_YEAR)
        ),
        conventional_standard_error_annual=MONTHS_PER_YEAR * conventional_se_month,
        hac_standard_error_annual=MONTHS_PER_YEAR * hac.standard_error,
        hac_t_statistic=hac.t_statistic,
        hac_lag_count=hac.n_lags,
        one_sided_p_value_hac=one_sided_p_value(hac.t_statistic),
        mde_one_sided_percent_per_year=mde,
        mde_one_sided_hac_percent_per_year=mde_hac,
        power_at_materiality=power_to_detect(
            settings.materiality_annual_percent / MONTHS_PER_YEAR,
            standard_error=conventional_se_month,
            one_sided=True,
        ),
        power_at_true_factor_reference=power_to_detect(
            TRUE_FACTOR_REFERENCE_ANNUAL_PERCENT / MONTHS_PER_YEAR,
            standard_error=conventional_se_month,
            one_sided=True,
        ),
        sample=sample,
        bootstraps=tuple(bootstraps),
        panel_intervals=tuple(panel_intervals),
        per_region_premium=per_region,
        year_contributions=calendar_year_contributions(composite, panel.periods),
        best_calendar_year=best_year,
        premium_without_best_year=(
            _annualised_premium_percent(without_best) if best_year else None
        ),
        band_sharpe=band_sharpe,
        band_mde=band_mde,
    )


# --------------------------------------------------------------------------- #
# The predeclared decision, per factor
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorVerdict:
    """The frozen rejection rule applied to one factor."""

    factor: str
    status: ResultStatus
    branch: str
    clauses_passed: tuple[str, ...]
    clauses_failed: tuple[str, ...]
    reasoning: str
    what_would_fire: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "status": self.status.value,
            "falsifier_branch": self.branch,
            "clauses_passed": list(self.clauses_passed),
            "clauses_failed": list(self.clauses_failed),
            "reasoning": self.reasoning,
            "what_would_fire": self.what_would_fire,
        }


def apply_rejection_rule(
    factor: str,
    pooled: PooledCell,
    regional: Mapping[str, CellStatistics],
    *,
    materiality: float,
) -> FactorVerdict:
    """Exactly the falsifier and rejection rule frozen in the specification.

    Branch (a) advances a factor only when all five clauses hold. Branch (b)
    closes the factor programme on public data when the *measured* pooled minimum
    detectable effect is still above the materiality threshold, which says that
    adding every independent region the library distributes did not buy the power
    to sign the premium. Neither branch is a statement that a premium is zero.
    """
    interval = pooled.joint_bootstrap
    premium = pooled.annualised_premium_percent
    mde = pooled.mde_one_sided_percent_per_year

    sign = 1.0 if premium > 0.0 else (-1.0 if premium < 0.0 else 0.0)
    agreeing = [
        region
        for region, cell in regional.items()
        if sign != 0.0 and math.copysign(1.0, cell.annualised_premium_percent) == sign
    ]

    passed: list[str] = []
    failed: list[str] = []

    def record(ok: bool, message: str) -> bool:
        (passed if ok else failed).append(message)
        return ok

    a1 = record(premium > 0.0, f"(a1) pooled premium {premium:+.2f} pp/yr is positive")
    a2 = record(
        premium >= materiality,
        f"(a2) pooled premium {premium:+.2f} pp/yr against the "
        f"{materiality:.1f} pp/yr materiality threshold",
    )
    record(
        interval.one_sided_lower_95 > 0.0,
        f"(a3) one-sided 95% lower bound of the cross-region JOINT interval is "
        f"{interval.one_sided_lower_95:+.2f} pp/yr",
    )
    record(
        len(agreeing) >= 2,
        f"(a4) the sign of the pooled premium is shared by {len(agreeing)} of "
        f"{len(regional)} regions ({', '.join(sorted(agreeing)) or 'none'})",
    )
    without = pooled.premium_without_best_year
    record(
        without is not None and without > 0.0 and without >= materiality,
        f"(a5) dropping the best calendar year ({pooled.best_calendar_year}) leaves "
        f"{without:+.2f} pp/yr" if without is not None else "(a5) not computable",
    )

    if pooled.months < 24 or pooled.dropped_months > 0:
        return FactorVerdict(
            factor=factor,
            status=ResultStatus.UNRESOLVED,
            branch="(0) the pooled cell could not be computed cleanly",
            clauses_passed=tuple(passed),
            clauses_failed=tuple(failed),
            reasoning=(
                f"the pooled window holds {pooled.months} aligned months and the "
                f"cross-region intersection dropped {pooled.dropped_months}, so the "
                "cell is not the window the specification froze"
            ),
            what_would_fire="a complete pooled window over the frozen era",
        )

    if not failed:
        return FactorVerdict(
            factor=factor,
            status=ResultStatus.EXPLORATORY,
            branch="(a) advance",
            clauses_passed=tuple(passed),
            clauses_failed=(),
            reasoning=(
                "every clause of branch (a) holds: the pooled post-publication "
                f"premium is {premium:+.2f} pp/yr, at or above materiality, its "
                "joint cross-region interval excludes zero, its sign is shared by "
                "at least two regions and it survives dropping its best calendar "
                "year. That permits an investable implementation to be TESTED and "
                "permits nothing else."
            ),
            what_would_fire="",
        )

    if mde > materiality:
        mde_interval = pooled.panel_interval_named("pooled_mde_one_sided_percent_per_year")
        interval_note = (
            f" Its joint-bootstrap 90% interval is "
            f"[{mde_interval.lower_90:.2f}, {mde_interval.upper_90:.2f}] pp/yr, "
            + (
                "entirely above the threshold."
                if mde_interval.lower_90 > materiality
                else "which reaches below the threshold, so the point estimate carries "
                "the verdict here."
            )
            if mde_interval is not None
            else ""
        )
        return FactorVerdict(
            factor=factor,
            status=ResultStatus.REJECTED,
            branch="(b) closed on public data",
            clauses_passed=tuple(passed),
            clauses_failed=tuple(failed),
            reasoning=(
                f"the MEASURED pooled minimum detectable effect is {mde:.2f} pp/yr at "
                f"80% power, above the {materiality:.1f} pp/yr materiality threshold."
                f"{interval_note} "
                f"Pooling three regions over {pooled.months} months bought "
                f"{pooled.sample.effective_region_months_iid:.0f} independent "
                f"single-region months against the "
                f"{pooled.sample.naive_region_months} that independence would have "
                f"claimed, an effective "
                f"{pooled.sample.effective_regions:.2f} regions out of "
                f"{pooled.sample.regions}. Adding every independent region the public "
                "library distributes does not make this premium detectable, so no "
                "currently available public data can sign it. This is a permanent "
                "verdict on this evidence base, not a request for more research."
            ),
            what_would_fire="",
        )

    if not a1 or not a2:
        return FactorVerdict(
            factor=factor,
            status=ResultStatus.REJECTED,
            branch="(a) failed in a powered window",
            clauses_passed=tuple(passed),
            clauses_failed=tuple(failed),
            reasoning=(
                f"the pooled window IS powered - its minimum detectable effect is "
                f"{mde:.2f} pp/yr, at or below the {materiality:.1f} pp/yr threshold - "
                f"and it measured {premium:+.2f} pp/yr. A powered window measured a "
                "premium that is not worth having."
            ),
            what_would_fire="",
        )

    return FactorVerdict(
        factor=factor,
        status=ResultStatus.UNRESOLVED,
        branch="(a) partially satisfied in a powered window",
        clauses_passed=tuple(passed),
        clauses_failed=tuple(failed),
        reasoning=(
            f"the pooled window is powered ({mde:.2f} pp/yr MDE) and the premium is "
            f"positive and material at {premium:+.2f} pp/yr, but "
            + "; ".join(failed)
            + ". Neither branch fires cleanly."
        ),
        what_would_fire=(
            "branch (a) would fire if the failing clause(s) above held: "
            + "; ".join(failed)
            + ". Branch (b) would fire if the pooled MDE rose above "
            f"{materiality:.1f} pp/yr."
        ),
    )


# --------------------------------------------------------------------------- #
# Loading the pinned sources
# --------------------------------------------------------------------------- #


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def _series_from_table(table: ParsedTable, name: str, *, dataset_id: str) -> MonthlySeries:
    """Pull one column out, dropping missing months and recording that it happened."""
    if name not in table.columns:
        raise RegionalReplicationError(
            f"column {name!r} is absent from table {table.table_id!r} of "
            f"{dataset_id}; found {list(table.columns)}"
        )
    raw = table.column(name)
    periods: list[str] = []
    values: list[float] = []
    for period, value in zip(table.periods, raw, strict=True):
        if value is None:
            continue
        periods.append(period)
        values.append(value)
    return MonthlySeries(
        name=name,
        periods=tuple(periods),
        values=np.asarray(values, dtype=np.float64),
        source_dataset_id=dataset_id,
        source_column=name,
    )


def _clip_to_sample_policy(series: MonthlySeries, *, end: str) -> MonthlySeries:
    """Drop everything after the sample policy's end, before any statistic."""
    limit = month_index(end)
    keep = [index for index, period in enumerate(series.periods) if month_index(period) <= limit]
    return MonthlySeries(
        name=series.name,
        periods=tuple(series.periods[index] for index in keep),
        values=series.values[np.asarray(keep, dtype=np.intp)],
        source_dataset_id=series.source_dataset_id,
        source_column=series.source_column,
    )


def _load_sources(
    specification: Specification,
) -> tuple[dict[str, dict[str, MonthlySeries]], list[JsonValue]]:
    """Fetch, pin, parse and validate all three regional files.

    A hash mismatch ABORTS. Ken French rebuilds the whole history from each new
    vintage, so an unrecognised hash is a new vintage, and a premium computed
    from an unrecognised file looks exactly like a good one.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="parameters.source_pin")
    entries = _sequence(_at(pin, "series", where="source_pin"), where="source_pin.series")

    cache = RawCache()
    by_region: dict[str, dict[str, MonthlySeries]] = {}
    provenance: list[JsonValue] = []

    for index, item in enumerate(entries):
        where = f"source_pin.series[{index}]"
        spec_entry = _mapping(item, where=where)
        region = _text(spec_entry, "region", where=where)
        if region not in REGIONS:
            raise RegionalReplicationError(
                f"{where}.region is {region!r}, which is not one of {REGIONS}"
            )
        dataset = french.get_dataset(_text(spec_entry, "dataset_id", where=where))
        cached = french.download(cache, dataset)

        expected_raw = _text(spec_entry, "expected_sha256_raw", where=where)
        if cached.sha256 != expected_raw:
            raise RegionalReplicationError(
                f"the file at {dataset.url} now hashes to {cached.sha256}, but this "
                f"specification is frozen against {expected_raw}. Ken French rebuilds "
                "the whole history from each new vintage, so this is a new vintage, "
                "not a corrupted download. Freeze a new specification against it "
                "rather than reporting premia from an unrecognised file."
            )

        parsed = french.parse(cache, cached, dataset=dataset)
        table = parsed.table(_text(spec_entry, "table_id", where=where))
        report = validate_table(
            table,
            dataset_id=_text(spec_entry, "manifest_dataset_id", where=where),
            expected_columns=_strings(spec_entry, "expected_columns", where=where),
            expected_frequency="monthly",
        )
        if not report.ok:
            raise RegionalReplicationError(
                f"{dataset.dataset_id} failed validation before any statistic was "
                "computed: " + "; ".join(report.summary())
            )
        expected_normalized = _text(spec_entry, "expected_sha256_normalized", where=where)
        if table.sha256_normalized() != expected_normalized:
            raise RegionalReplicationError(
                f"the derived table for {dataset.dataset_id} hashes to "
                f"{table.sha256_normalized()}, but the specification pins "
                f"{expected_normalized}. The raw bytes matched, so the parser "
                "changed behaviour. That is a finding, not a hash to update."
            )

        manifest_hash: str | None = None
        manifest_path = _workspace_root() / _text(spec_entry, "committed_manifest", where=where)
        if manifest_path.is_file():
            manifest = read_manifest(manifest_path)
            manifest_hash = manifest.sha256_manifest()
            if manifest.sha256_raw != expected_raw:
                raise RegionalReplicationError(
                    f"{manifest_path} records sha256_raw {manifest.sha256_raw}, "
                    f"which is not the pinned {expected_raw}"
                )

        by_region[region] = {
            factor: _series_from_table(table, factor, dataset_id=dataset.dataset_id)
            for factor in FACTORS
        }
        provenance.append(
            {
                "region": region,
                "dataset_id": dataset.dataset_id,
                "source_url": cached.url,
                "sha256_raw": cached.sha256,
                "sha256_normalized": table.sha256_normalized(),
                "size_bytes": cached.size_bytes,
                "retrieved_utc": cached.retrieved_utc,
                "source_last_modified": cached.last_modified,
                "parser_version": french.PARSER_VERSION,
                "committed_manifest_sha256": manifest_hash,
                "table_id": table.table_id,
                "columns": list(table.columns),
                "rows_in_file": table.rows,
                "first_observation": table.first_observation,
                "last_observation": table.last_observation,
                "source_units": table.source_units,
                "units": table.units,
                "unit_transform": table.unit_transform,
                "preamble": parsed.preamble.strip(),
                "validation_findings": list(report.summary()),
            }
        )

    missing = [region for region in REGIONS if region not in by_region]
    if missing:
        raise RegionalReplicationError(f"the specification pinned no file for region(s) {missing}")
    return by_region, provenance


def verify_regional_coverage(
    series: Mapping[str, Mapping[str, MonthlySeries]],
    grid: Sequence[RegionalGridCell],
) -> JsonValue:
    """Check, from the loaded data, that no region starts after an era it must cover.

    Experiment 001 skipped regional data on the stated grounds that the files
    "start 1990-07 and 1989-07, so they are shorter than the post-publication
    windows". That is true only of the original-sample eras. This function tests
    the claim against the files themselves rather than restating it, and ABORTS
    on a silently truncated window, which would otherwise look exactly like a
    shorter one.
    """
    rows: list[JsonValue] = []
    problems: list[str] = []
    for cell in sorted(grid, key=lambda item: (item.region, item.factor, item.era_name)):
        first = series[cell.region][cell.factor].first_observation or "9999-99"
        covered = month_index(first) <= month_index(cell.start)
        if not covered:
            problems.append(
                f"{cell.region}/{cell.factor} starts {first}, after era "
                f"{cell.era_name} starts {cell.start}"
            )
        rows.append(
            {
                "region": cell.region,
                "factor": cell.factor,
                "first_observation": first,
                "era": cell.era_name,
                "era_start": cell.start,
                "covered": covered,
                "months_of_head_room": month_count(first, cell.start) - 1,
            }
        )
    if problems:
        raise RegionalReplicationError(
            "a region does not reach back to the start of an era it must cover, so "
            "the window would be silently truncated: " + "; ".join(problems)
        )
    return {
        "claim_tested": (
            "Experiment 001 skipped the regional files because they 'start 1990-07 "
            "and 1989-07, so they are shorter than the post-publication windows'."
        ),
        "verdict": (
            "FALSE for every era this experiment runs. Both regional files begin "
            "before every post-publication boundary, so the regional windows are "
            "exactly as long as the US ones. The statement holds only of the "
            "original-sample eras, which begin 1963-07 and are excluded here for "
            "that reason."
        ),
        "checked_against": "the loaded series, not this text",
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# Multiple testing
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FamilyInference:
    """Uncorrected and corrected inference over one predeclared family."""

    name: str
    keys: tuple[str, ...]
    p_values: tuple[float, ...]
    bh_adjusted: tuple[float, ...]
    bh_rejected: tuple[bool, ...]
    holm_adjusted: tuple[float, ...]
    holm_rejected: tuple[bool, ...]
    alpha: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "family": self.name,
            "alpha": self.alpha,
            "family_size": len(self.keys),
            "cells": [
                {
                    "cell": key,
                    "one_sided_p_uncorrected": p,
                    "benjamini_hochberg_adjusted_p": bh,
                    "benjamini_hochberg_rejected": bool(bh_ok),
                    "holm_bonferroni_adjusted_p": holm,
                    "holm_bonferroni_rejected": bool(holm_ok),
                }
                for key, p, bh, bh_ok, holm, holm_ok in zip(
                    self.keys,
                    self.p_values,
                    self.bh_adjusted,
                    self.bh_rejected,
                    self.holm_adjusted,
                    self.holm_rejected,
                    strict=True,
                )
            ],
        }


def correct_family(
    name: str, keys: Sequence[str], p_values: Sequence[float], *, alpha: float
) -> FamilyInference:
    """Benjamini-Hochberg over a frozen family, with Holm as the stricter reading."""
    bh = benjamini_hochberg(list(p_values), alpha=alpha)
    holm = holm_bonferroni(list(p_values), alpha=alpha)
    return FamilyInference(
        name=name,
        keys=tuple(keys),
        p_values=tuple(float(value) for value in p_values),
        bh_adjusted=tuple(float(value) for value in bh.adjusted_p_values),
        bh_rejected=tuple(bool(value) for value in bh.rejected),
        holm_adjusted=tuple(float(value) for value in holm.adjusted_p_values),
        holm_rejected=tuple(bool(value) for value in holm.rejected),
        alpha=alpha,
    )


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #


def _us_second_moment_bands(specification: Specification) -> Mapping[str, JsonValue]:
    """The Phase 1 relative volatility band, per factor, measured on the US file only."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(
        _at(parameters, "second_moment_uncertainty", where="parameters"),
        where="parameters.second_moment_uncertainty",
    )
    return _mapping(
        _at(block, "us_band", where="second_moment_uncertainty"),
        where="second_moment_uncertainty.us_band",
    )


def _settings(specification: Specification, *, region: str) -> InferenceSettings:
    """Experiment 001's settings object, with the band that region actually has.

    The Phase 1 band was measured on the US file and on no other. Applying it to
    a regional cell would claim a reproduction that never happened, so the
    regional settings carry no band and mark the second moment UNMEASURED, which
    is what Experiment 001's machinery reports for an ungated series.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    windows = _integers(
        _sequence(_at(parameters, "rolling_windows_months", where="parameters"), where="rolling"),
        where="rolling_windows_months",
    )
    us_bands_raw = _us_second_moment_bands(specification)
    bands = (
        {name: _number(us_bands_raw, name, where="us_band") for name in FACTORS}
        if region == "us"
        else {}
    )
    measured = {name: region == "us" for name in FACTORS}
    return InferenceSettings(
        frozen_block_length=12.0,
        neighbour_block_lengths=(6.0, 24.0),
        n_resamples=specification.inference.resamples,
        method=specification.inference.bootstrap,
        power_target=_number(parameters, "power_target", where="parameters"),
        materiality_annual_percent=_number(
            parameters, "materiality_threshold_annual_percent", where="parameters"
        ),
        true_factor_reference_annual_percent=TRUE_FACTOR_REFERENCE_ANNUAL_PERCENT,
        rolling_windows_months=windows,
        second_moment_bands=bands,
        second_moment_measured=measured,
    )


def _pooling_weights(specification: Specification) -> tuple[FloatArray, str]:
    parameters = _mapping(specification.parameters, where="parameters")
    pooling = _mapping(_at(parameters, "pooling", where="parameters"), where="parameters.pooling")
    weighting = _text(pooling, "weights", where="pooling")
    declared = _mapping(
        _at(pooling, "weight_values", where="pooling"), where="pooling.weight_values"
    )
    weights = np.asarray(
        [_number(declared, region, where="pooling.weight_values") for region in REGIONS],
        dtype=np.float64,
    )
    total = float(np.sum(weights))
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise RegionalReplicationError(
            f"the frozen pooling weights sum to {total!r}, not 1.0"
        )
    return weights, weighting


# --------------------------------------------------------------------------- #
# Hostile tests
# --------------------------------------------------------------------------- #


def _hostile_independent_resampling(pooled: Sequence[PooledCell]) -> JsonValue:
    rows: list[JsonValue] = []
    for cell in pooled:
        joint = cell.joint_bootstrap
        invalid = next((item for item in cell.bootstraps if not item.valid), None)
        if invalid is None:
            continue
        joint_width = joint.upper_90 - joint.lower_90
        invalid_width = invalid.upper_90 - invalid.lower_90
        rows.append(
            {
                "cell": cell.key,
                "joint_two_sided_90": [joint.lower_90, joint.upper_90],
                "independent_two_sided_90_INVALID": [invalid.lower_90, invalid.upper_90],
                "joint_width": joint_width,
                "independent_width": invalid_width,
                "narrowing_factor": (
                    joint_width / invalid_width if invalid_width > 0.0 else None
                ),
                "independent_interval_excludes_zero": bool(
                    invalid.lower_90 > 0.0 or invalid.upper_90 < 0.0
                ),
                "joint_interval_excludes_zero": bool(
                    joint.lower_90 > 0.0 or joint.upper_90 < 0.0
                ),
            }
        )
    return {
        "description": (
            "Resampling the three regions with independent index draws instead of "
            "one joint draw. It is INVALID for correlated regions and is computed "
            "only so the size of the error can be shown rather than asserted: it "
            "destroys contemporaneous cross-region dependence and narrows every "
            "interval by the factor reported here."
        ),
        "rows": rows,
    }


def _hostile_episode_sharing(
    regional: Mapping[str, CellStatistics],
    pooled: PooledCell,
    windows: Mapping[str, Window],
    named_episodes: Mapping[str, str],
) -> JsonValue:
    """Do the regions share an episode, and what do the US episodes do elsewhere?"""
    best_by_region: dict[str, str | None] = {}
    without_by_region: dict[str, float | None] = {}
    for region in regional:
        window = windows[region]
        remaining, best = _drop_best_calendar_year(window.values, window.periods)
        best_by_region[region] = best
        without_by_region[region] = (
            _annualised_premium_percent(remaining) if best else None
        )
    distinct = {value for value in best_by_region.values() if value is not None}

    named_year = named_episodes.get(pooled.factor)
    named: JsonValue = None
    if named_year is not None:
        shares: dict[str, JsonValue] = {}
        for region in regional:
            window = windows[region]
            contributions = calendar_year_contributions(window.values, window.periods)
            entry = next((item for item in contributions if item[0] == named_year), None)
            shares[region] = (
                {"compounded_return": entry[1], "share_of_premium": _json_float(entry[2])}
                if entry
                else None
            )
        pooled_entry = next(
            (item for item in pooled.year_contributions if item[0] == named_year), None
        )
        named = {
            "year": named_year,
            "why_this_year": (
                "Experiment 001 measured this calendar year as the single episode "
                f"carrying most of {pooled.factor}'s US post-publication premium. It "
                "is evaluated here BY NAME in every region rather than by whichever "
                "year turned out best, so the test cannot be fitted."
            ),
            "per_region": shares,
            "pooled": (
                {
                    "compounded_return": pooled_entry[1],
                    "share_of_premium": _json_float(pooled_entry[2]),
                }
                if pooled_entry
                else None
            ),
        }

    return {
        "cell": pooled.key,
        "best_calendar_year_by_region": best_by_region,
        "premium_without_best_calendar_year_by_region": without_by_region,
        "regions_share_the_same_best_year": len(distinct) == 1,
        "distinct_best_years": sorted(distinct),
        "pooled_best_calendar_year": pooled.best_calendar_year,
        "pooled_premium_without_best_year": pooled.premium_without_best_year,
        "named_episode_from_exp_001": named,
    }


def _hostile_alternative_pools(
    panels: Mapping[str, AlignedPanel],
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> JsonValue:
    """Inverse-variance weights, and a pool that excludes the US entirely."""
    rows: list[JsonValue] = []
    for key, panel in panels.items():
        values = panel.values
        variances = np.var(values, axis=0, ddof=1)
        inverse = 1.0 / variances
        inverse_weights = np.asarray(inverse / float(np.sum(inverse)), dtype=np.float64)
        inverse_composite = pooled_composite(values, inverse_weights)

        non_us = [index for index, region in enumerate(panel.regions) if region != "us"]
        ex_us_panel = values[:, non_us]
        ex_us_weights = np.full(len(non_us), 1.0 / len(non_us), dtype=np.float64)
        ex_us_composite = pooled_composite(ex_us_panel, ex_us_weights)
        ex_us_sample = effective_sample_size(ex_us_panel * 100.0, ex_us_composite * 100.0)
        ex_us_boot = cross_region_bootstrap(
            ex_us_panel,
            ex_us_weights,
            block_length=settings.frozen_block_length,
            block_length_source="frozen",
            n_resamples=settings.n_resamples,
            rng=rng,
            joint=True,
        )
        ex_us_sigma = float(np.std(ex_us_composite * 100.0, ddof=1))
        ex_us_mde = MONTHS_PER_YEAR * minimum_detectable_effect(
            standard_error=ex_us_sigma / math.sqrt(panel.months),
            power=settings.power_target,
            one_sided=True,
        )
        rows.append(
            {
                "cell": key,
                "months": panel.months,
                "equal_weighted_premium": _annualised_premium_percent(
                    pooled_composite(values, np.full(values.shape[1], 1.0 / values.shape[1]))
                ),
                "inverse_variance_weights": [float(value) for value in inverse_weights],
                "inverse_variance_premium": _annualised_premium_percent(inverse_composite),
                "ex_us_regions": [panel.regions[index] for index in non_us],
                "ex_us_premium": _annualised_premium_percent(ex_us_composite),
                "ex_us_two_sided_90": [ex_us_boot.lower_90, ex_us_boot.upper_90],
                "ex_us_mde_one_sided_percent_per_year": ex_us_mde,
                "ex_us_effective_regions": _json_float(ex_us_sample.effective_regions),
                "ex_us_effective_region_months_iid": _json_float(
                    ex_us_sample.effective_region_months_iid
                ),
            }
        )
    return {
        "description": (
            "Two pools the falsifier does not read. Inverse-variance weights show "
            "whether the equal weighting carries the result. The ex-US pool is the "
            "genuinely independent look at the United States finding, because it "
            "shares no security with the US file."
        ),
        "rows": rows,
    }


def _hostile_correlated_noise(
    panel: AlignedPanel,
    *,
    weights: FloatArray,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> JsonValue:
    """The identical pooled procedure on a zero-mean panel of matched covariance.

    The calibration check the framework demands, extended to the cross-region
    case: it shows what the machinery produces from noise that is correlated the
    same way the real regions are, so a reader can see how much of any reported
    structure is the procedure rather than the data.
    """
    values = panel.values
    covariance = np.cov(values, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(np.atleast_2d(covariance))
    factor = eigenvectors @ np.diag(np.sqrt(np.clip(eigenvalues, 0.0, None)))
    draws = rng.normal(size=(panel.months, values.shape[1])) @ factor.T
    composite = pooled_composite(np.asarray(draws, dtype=np.float64), weights)
    percent = composite * 100.0
    sample = effective_sample_size(np.asarray(draws, dtype=np.float64) * 100.0, percent)
    sigma = float(np.std(percent, ddof=1))
    boot = cross_region_bootstrap(
        np.asarray(draws, dtype=np.float64),
        weights,
        block_length=settings.frozen_block_length,
        block_length_source="frozen",
        n_resamples=settings.n_resamples,
        rng=rng,
        joint=True,
    )
    return {
        "description": (
            "A zero-mean Gaussian panel with the same length and the same measured "
            f"cross-region covariance as {panel.factor}/{panel.era_name}, put "
            "through the identical pooled procedure. Its premium is zero by "
            "construction; whatever interval and effective sample size it produces "
            "is what this machinery produces from correlated nothing."
        ),
        "matched_to": f"{panel.factor}/{panel.era_name}",
        "months": panel.months,
        "annualised_premium_percent": _annualised_premium_percent(composite),
        "two_sided_90_interval": [boot.lower_90, boot.upper_90],
        "mde_one_sided_percent_per_year": MONTHS_PER_YEAR
        * minimum_detectable_effect(
            standard_error=sigma / math.sqrt(panel.months),
            power=settings.power_target,
            one_sided=True,
        ),
        "effective_sample_size": sample.to_json(),
    }


def _cross_region_correlations(panel: AlignedPanel) -> JsonValue:
    matrix = np.atleast_2d(
        np.asarray(np.corrcoef(panel.values, rowvar=False), dtype=np.float64)
    )
    upper = matrix[np.triu_indices(len(panel.regions), k=1)]
    return {
        "factor": panel.factor,
        "era": panel.era_name,
        "window": f"{panel.periods[0]}..{panel.periods[-1]}",
        "months": panel.months,
        "regions": list(panel.regions),
        "matrix": [[float(value) for value in row] for row in matrix],
        "mean_pairwise_correlation": float(np.mean(upper)) if upper.size else None,
    }


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #

#: The two episodes Experiment 001 named in the US post-publication record, tested
#: here by name in every region so the concentration check cannot be fitted.
NAMED_EPISODES: Final[Mapping[str, str]] = {"HML": "2000", "RMW": "2021"}


def _estimates_for(pooled: Sequence[PooledCell]) -> tuple[Estimate, ...]:
    estimates: list[Estimate] = []
    for cell in pooled:
        interval = cell.joint_bootstrap
        estimates.append(
            Estimate(
                name=f"{cell.factor} pooled {cell.era_role} annualised premium",
                value=cell.annualised_premium_percent,
                units="percentage points per year",
                interval=(interval.lower_90, interval.upper_90),
                interval_method=(
                    f"CROSS-REGION JOINT stationary block bootstrap, two-sided 90%, "
                    f"mean block {interval.block_length:.0f}m, "
                    f"{interval.n_resamples} resamples"
                ),
                cost_basis=CostBasis.GROSS,
                n_obs=cell.months,
                notes=(
                    f"gross, long-short and not investable; detectable at 80% power "
                    f"only above {cell.mde_one_sided_percent_per_year:.2f} pp/yr. "
                    f"Measured effective sample size "
                    f"{cell.sample.effective_region_months_iid:.0f} independent "
                    f"single-region months against {cell.sample.naive_region_months} "
                    f"if the regions were independent."
                ),
            )
        )
        band_note = (
            f" SEPARATE systematic band propagated from the US leg's Phase 1 "
            f"volatility disagreement, not sampling error and not combined with the "
            f"interval: [{cell.band_sharpe[0]:.3f}, {cell.band_sharpe[1]:.3f}]."
            if cell.band_sharpe
            else " No band: CMA reproduced inside the Phase 1 gate. The two regional "
            "legs were never gated at all, so their second moments are UNMEASURED, "
            "which is weaker than a band of zero."
        )
        regions_interval = cell.panel_interval_named("effective_regions")
        estimates.append(
            Estimate(
                name=f"{cell.factor} pooled {cell.era_role} effective regions",
                value=cell.sample.effective_regions,
                units="independent regions out of three",
                interval=(
                    (regions_interval.lower_90, regions_interval.upper_90)
                    if regions_interval
                    else None
                ),
                interval_method=(
                    f"CROSS-REGION JOINT stationary block bootstrap of the panel "
                    f"covariance, two-sided 90%, mean block "
                    f"{regions_interval.block_length:.0f}m, "
                    f"{regions_interval.n_resamples} resamples"
                    if regions_interval
                    else ""
                ),
                uncertainty_unavailable_reason=(
                    "" if regions_interval else "bootstrap not run for this cell"
                ),
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=cell.months,
                notes=(
                    f"{cell.sample.effective_region_months_iid:.0f} independent "
                    f"single-region months against "
                    f"{cell.sample.naive_region_months} if the regions were "
                    f"independent, {cell.sample.effective_region_months_hac:.0f} once "
                    f"serial dependence is folded in, at a mean pairwise cross-region "
                    f"correlation of {cell.sample.mean_pairwise_correlation:.3f}."
                    + band_note
                ),
            )
        )
        mde_interval = cell.panel_interval_named("pooled_mde_one_sided_percent_per_year")
        estimates.append(
            Estimate(
                name=f"{cell.factor} pooled {cell.era_role} minimum detectable effect",
                value=cell.mde_one_sided_percent_per_year,
                units="percentage points per year",
                interval=(
                    (mde_interval.lower_90, mde_interval.upper_90) if mde_interval else None
                ),
                interval_method=(
                    f"CROSS-REGION JOINT stationary block bootstrap of the panel "
                    f"covariance, two-sided 90%, mean block "
                    f"{mde_interval.block_length:.0f}m, {mde_interval.n_resamples} "
                    "resamples"
                    if mde_interval
                    else ""
                ),
                uncertainty_unavailable_reason=(
                    "" if mde_interval else "bootstrap not run for this cell"
                ),
                cost_basis=CostBasis.GROSS,
                n_obs=cell.months,
                notes=(
                    "the smallest true premium this pooled window could reject a zero "
                    "mean for at 80% power, one-sided. Branch (b) of the frozen "
                    "falsifier reads this figure against the 2.0 pp/yr materiality "
                    "threshold; the HAC reading is "
                    f"{cell.mde_one_sided_hac_percent_per_year:.2f} pp/yr."
                ),
            )
        )
    return tuple(estimates)


def _frames(
    cells: Sequence[CellStatistics],
    regions: Sequence[str],
    pooled: Sequence[PooledCell],
    families: Sequence[FamilyInference],
) -> dict[str, pd.DataFrame]:
    regional = pd.DataFrame(
        [
            {"region": region, **cell.to_json()}
            for region, cell in zip(regions, cells, strict=True)
        ]
    )
    pooled_frame = pd.DataFrame([cell.to_json() for cell in pooled])
    inference = pd.DataFrame(
        [
            {
                "family": family.name,
                "cell": key,
                "p_uncorrected": p,
                "bh_adjusted": bh,
                "bh_rejected": bh_ok,
                "holm_adjusted": holm,
                "holm_rejected": holm_ok,
            }
            for family in families
            for key, p, bh, bh_ok, holm, holm_ok in zip(
                family.keys,
                family.p_values,
                family.bh_adjusted,
                family.bh_rejected,
                family.holm_adjusted,
                family.holm_rejected,
                strict=True,
            )
        ]
    )
    return {"regional_cells": regional, "pooled_cells": pooled_frame, "inference": inference}


def _overall_status(verdicts: Sequence[FactorVerdict]) -> ResultStatus:
    """The run's own status: the weakest thing any factor achieved."""
    statuses = {verdict.status for verdict in verdicts}
    if ResultStatus.UNRESOLVED in statuses:
        return ResultStatus.UNRESOLVED
    if statuses == {ResultStatus.REJECTED}:
        return ResultStatus.REJECTED
    return ResultStatus.EXPLORATORY


def _summary_line(
    verdicts: Sequence[FactorVerdict],
    family: FamilyInference,
    cells: Sequence[CellStatistics],
    pooled: Sequence[PooledCell],
) -> str:
    by_status: dict[str, list[str]] = {}
    for verdict in verdicts:
        by_status.setdefault(verdict.status.value, []).append(verdict.factor)
    parts = ", ".join(
        f"{status}: {', '.join(sorted(names))}" for status, names in sorted(by_status.items())
    )
    survivors = sum(1 for value in family.bh_rejected if value)
    uncorrected = sum(1 for value in family.p_values if value <= 0.05)
    underpowered = sum(
        1
        for cell in cells
        if cell.annualised_premium_percent < cell.mde_one_sided_percent_per_year
    )
    full = [cell for cell in pooled if cell.era_role == "full_post_publication"]
    worst = max(cell.mde_one_sided_percent_per_year for cell in full)
    best = min(cell.mde_one_sided_percent_per_year for cell in full)
    effective = ", ".join(
        f"{cell.factor} {cell.sample.effective_regions:.2f}" for cell in full
    )
    return (
        f"{parts}. Of the {len(family.keys)} predeclared regional cells, {uncorrected} "
        f"have a one-sided HAC p-value at or below 0.05 uncorrected and {survivors} "
        f"survive Benjamini-Hochberg at {family.alpha:.2f}; {underpowered} hold a "
        "premium smaller than what their own window could detect at 80% power. "
        f"Pooling three regions bought an effective {effective} regions out of 3, "
        f"leaving pooled minimum detectable effects of {best:.2f} to {worst:.2f} "
        "pp/yr on the full post-publication eras. All figures are gross, long-short "
        "and not investable."
    )


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 005."""
    parameters = _mapping(specification.parameters, where="parameters")
    materiality = _number(
        parameters, "materiality_threshold_annual_percent", where="parameters"
    )
    alpha = _number(parameters, "benjamini_hochberg_alpha", where="parameters")
    rng = context.rng

    raw, provenance = _load_sources(specification)
    sample_end = specification.sample_policy.end
    series = {
        region: {
            factor: _clip_to_sample_policy(item, end=sample_end)
            for factor, item in by_factor.items()
        }
        for region, by_factor in raw.items()
    }

    grid = resolve_grid(specification)
    coverage = verify_regional_coverage(series, grid)

    settings_by_region = {
        region: _settings(specification, region=region) for region in REGIONS
    }
    weights, weighting = _pooling_weights(specification)
    us_bands = _us_second_moment_bands(specification)

    windows: dict[str, Window] = {}
    cells: list[CellStatistics] = []
    cell_regions: list[str] = []
    for item in grid:
        source = series[item.region][item.factor]
        window = window_series(source, start=item.start, end=item.end)
        windows[item.key] = window
        cells.append(
            compute_cell(
                window,
                factor=item.factor,
                era_role=item.era_role,
                era_name=item.era_name,
                settings=settings_by_region[item.region],
                rng=rng,
            )
        )
        cell_regions.append(item.region)

    panels: dict[str, AlignedPanel] = {}
    pooled: list[PooledCell] = []
    for factor in FACTORS:
        for role in ERA_ROLES:
            declared = next(
                cell for cell in grid if cell.factor == factor and cell.era_role == role
            )
            panel = align_panel(
                {
                    region: windows[f"{factor}/{region}/{role}"]
                    for region in REGIONS
                },
                factor=factor,
                era_name=declared.era_name,
                regions=REGIONS,
            )
            panels[f"{factor}/{role}"] = panel
            pooled.append(
                compute_pooled(
                    panel,
                    era_role=role,
                    start=declared.start,
                    end=declared.end,
                    weights=weights,
                    weighting=weighting,
                    settings=settings_by_region["us"],
                    rng=rng,
                    us_band=_number(us_bands, factor, where="us_band"),
                )
            )

    regional_family = correct_family(
        "regional_cells",
        [f"{region}/{cell.factor}/{cell.era_role}" for region, cell in
         zip(cell_regions, cells, strict=True)],
        [cell.one_sided_p_value_hac for cell in cells],
        alpha=alpha,
    )
    pooled_family = correct_family(
        "pooled_cells",
        [cell.key for cell in pooled],
        [cell.one_sided_p_value_hac for cell in pooled],
        alpha=alpha,
    )

    by_factor_region: dict[str, dict[str, CellStatistics]] = {}
    for region, cell in zip(cell_regions, cells, strict=True):
        if cell.era_role == "full_post_publication":
            by_factor_region.setdefault(cell.factor, {})[region] = cell
    pooled_full = {
        cell.factor: cell for cell in pooled if cell.era_role == "full_post_publication"
    }
    verdicts = tuple(
        apply_rejection_rule(
            factor,
            pooled_full[factor],
            by_factor_region[factor],
            materiality=materiality,
        )
        for factor in FACTORS
    )

    episode_rows = [
        _hostile_episode_sharing(
            by_factor_region[factor],
            pooled_full[factor],
            {
                region: windows[f"{factor}/{region}/full_post_publication"]
                for region in REGIONS
            },
            NAMED_EPISODES,
        )
        for factor in FACTORS
    ]

    band_effects: list[JsonValue] = []
    for pooled_cell in pooled:
        interval = pooled_cell.panel_interval_named("pooled_mde_one_sided_percent_per_year")
        band = pooled_cell.band_mde
        band_effects.append(
            {
                "cell": pooled_cell.key,
                "mde_one_sided_percent_per_year": (
                    pooled_cell.mde_one_sided_percent_per_year
                ),
                "mde_sampling_interval_90": (
                    [interval.lower_90, interval.upper_90] if interval else None
                ),
                "mde_systematic_band": list(band) if band else None,
                "branch_b_fires_at_point_estimate": (
                    pooled_cell.mde_one_sided_percent_per_year > materiality
                ),
                "branch_b_fires_across_the_whole_systematic_band": (
                    min(band) > materiality if band else None
                ),
                "branch_b_fires_across_the_whole_sampling_interval": (
                    interval.lower_90 > materiality if interval else None
                ),
            }
        )

    diagnostics: dict[str, JsonValue] = {
        "sources": provenance,
        "sample_policy": {
            "start": specification.sample_policy.start,
            "end": sample_end,
            "held_out_after": sample_end,
            "months_available_beyond_holdout": {
                region: max(
                    0,
                    month_count(
                        sample_end,
                        max(
                            (item.last_observation or sample_end)
                            for item in raw[region].values()
                        ),
                    )
                    - 1,
                )
                for region in REGIONS
            },
        },
        "regional_coverage_check": coverage,
        "umd_not_covered": {
            "covered": False,
            "reason": (
                "This repository's Ken French dataset registry holds exactly one "
                "momentum file, F-F_Momentum_Factor_CSV.zip, which is US only, and "
                "no committed manifest exists for any regional momentum file. A "
                "regional momentum test therefore requires acquiring and pinning a "
                "file this repository does not have, which is outside the frozen "
                "specification. UMD's Experiment 001 status of `unresolved` is "
                "untouched by this experiment."
            ),
            "registered_french_datasets": sorted(french.DATASETS),
        },
        "regional_cells": [
            {"region": region, **cell.to_json()}
            for region, cell in zip(cell_regions, cells, strict=True)
        ],
        "pooled_cells": [cell.to_json() for cell in pooled],
        "inference": [regional_family.to_json(), pooled_family.to_json()],
        "verdicts": [verdict.to_json() for verdict in verdicts],
        "cross_region_correlations": [
            _cross_region_correlations(panel) for panel in panels.values()
        ],
        "second_moment_band_effects": {
            "description": (
                "The Phase 1 band was measured on the US file only, so it is "
                "propagated into a pooled statistic by rescaling the US leg's "
                "deviations by (1 +/- u) and recomputing. Means are unaffected, "
                "because Phase 1 reproduced every mean. The band therefore cannot "
                "move a premium; it can only move a volatility, a Sharpe ratio and "
                "the minimum detectable effect that branch (b) reads. The two "
                "regional legs carry NO measured band, which is weaker than a band "
                "of zero and must not be read as agreement."
            ),
            "rows": band_effects,
        },
        "hostile_tests": {
            "independent_versus_joint_resampling": _hostile_independent_resampling(pooled),
            "episode_sharing_across_regions": {
                "description": (
                    "Whether the three regions share the same best calendar year, "
                    "and what the episodes Experiment 001 named in the US - 2000 for "
                    "HML and 2021 for RMW - did in every region. Regions that "
                    "co-move through the same episode are not three independent "
                    "looks, and this test says so rather than assuming otherwise."
                ),
                "rows": episode_rows,
            },
            "alternative_pools": _hostile_alternative_pools(
                panels, settings=settings_by_region["us"], rng=rng
            ),
            "correlated_synthetic_noise": _hostile_correlated_noise(
                panels["HML/full_post_publication"],
                weights=weights,
                settings=settings_by_region["us"],
                rng=rng,
            ),
            "block_length_neighbours": {
                "description": (
                    "The frozen 12-month block, the predeclared 6- and 24-month "
                    "neighbours, and the corrected Politis-White automatic length "
                    "computed from each pooled composite. All four are in the "
                    "`pooled_cells` payload for every cell."
                ),
                "rows": [
                    {
                        "cell": cell.key,
                        "intervals_by_block_length": [
                            {
                                "block_length": item.block_length,
                                "source": item.block_length_source,
                                "scheme": item.scheme,
                                "two_sided_90": [item.lower_90, item.upper_90],
                            }
                            for item in cell.bootstraps
                        ],
                    }
                    for cell in pooled
                ],
            },
            "us_cells_reproduce_experiment_001": {
                "description": (
                    "The US cells of this experiment read the same column of the same "
                    "pinned file over the same windows as Experiment 001, so they must "
                    "reproduce its published figures. A disagreement is a defect here."
                ),
                "rows": [
                    {
                        "cell": f"{cell.factor}/{cell.era_role}",
                        "annualised_premium_percent": cell.annualised_premium_percent,
                        "annualised_volatility_percent": cell.annualised_volatility_percent,
                        "observations": cell.observations,
                        "mde_one_sided_percent_per_year": (
                            cell.mde_one_sided_percent_per_year
                        ),
                    }
                    for region, cell in zip(cell_regions, cells, strict=True)
                    if region == "us"
                ],
            },
        },
    }

    caveats = (
        "These are academic zero-investment long-short research portfolios, gross of "
        "transaction costs, shorting costs, borrow, fees and taxes. A retail investor "
        "cannot implement them at all, and emerging-market shorting is harder and "
        "dearer than US shorting, so a POOLED gross premium is a looser upper bound "
        "than a US one, not a tighter one. Every figure here is an UPPER BOUND of "
        "unknown tightness.",
        "The developed-ex-US and emerging files were NEVER gated against any printed "
        "table. Their second moments are UNMEASURED, which is a weaker statement than "
        "a band of zero and must not be read as agreement. The Phase 1 band on US HML "
        "and US RMW is carried separately and is in no bootstrap interval.",
        "UMD is NOT covered. This repository manifests only a US momentum file, so a "
        "regional momentum test needs data it does not have. UMD's Experiment 001 "
        "status of `unresolved` is untouched.",
        "The three regions are the same construction on the same accounting variables "
        "in globally correlated universes. They are NOT three independent samples, and "
        "the effective sample size reported here is the measurement of exactly how far "
        "short of independence they fall.",
        "All three files are USD and unhedged. For a within-region long-short spread "
        "the exchange rate is multiplicative, spread_usd = (1 + f) * spread_local, so "
        "currency moves the second moment first-order and the mean only through the "
        "covariance E[f * spread_local], which is not zero a priori and is NOT "
        "measured here.",
        "A before/after comparison across a publication date is DESCRIPTIVE. Adding "
        "regions adds sample, not identification, and this experiment does not claim "
        "to identify a publication effect.",
        "The currently distributed files apply the current source vintage and the "
        "current construction to the whole history. The international files are built "
        "from a Bloomberg vintage rather than CRSP.",
        "Both multiple-testing families are strongly dependent: three regions of one "
        "factor share global risk factors, `recent` nests inside "
        "`full_post_publication`, and RMW and CMA share every era. "
        "Benjamini-Hochberg treats them as independent, so the corrected p-values are "
        "a LOWER bound on the true correction; Holm-Bonferroni is reported because it "
        "is valid under arbitrary dependence.",
    )

    return ExperimentResult(
        status=_overall_status(verdicts),
        summary=_summary_line(verdicts, regional_family, cells, pooled),
        estimates=_estimates_for(pooled),
        diagnostics=diagnostics,
        caveats=caveats,
        frames=_frames(cells, cell_regions, pooled, (regional_family, pooled_family)),
    )


def build_registry() -> ExperimentRegistry:
    """A registry holding exactly this experiment."""
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return _workspace_root() / "experiments" / "exp_005_regional_replication.yaml"


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    lines = [result.summary, "", "REGIONAL CELLS"]
    lines.append(
        f"{'factor':<5}{'region':<17}{'era role':<24}{'n':>5}{'ann%':>9}{'vol%':>8}"
        f"{'SR':>7}{'MDE80':>8}{'p':>9}{'BH p':>9}"
    )
    adjusted: dict[str, float] = {}
    families = result.diagnostics.get("inference")
    if isinstance(families, Sequence) and not isinstance(families, str):
        for family in families:
            if not isinstance(family, Mapping):
                continue
            rows = family.get("cells")
            if isinstance(rows, Sequence) and not isinstance(rows, str):
                for row in rows:
                    if isinstance(row, Mapping):
                        adjusted[str(row.get("cell"))] = float(
                            str(row.get("benjamini_hochberg_adjusted_p"))
                        )
    regional = result.diagnostics.get("regional_cells")
    if isinstance(regional, Sequence) and not isinstance(regional, str):
        for item in regional:
            if not isinstance(item, Mapping):
                continue
            key = f"{item.get('region')}/{item.get('factor')}/{item.get('era_role')}"
            lines.append(
                f"{item.get('factor')!s:<5}{item.get('region')!s:<17}"
                f"{item.get('era_role')!s:<24}"
                f"{int(str(item.get('observations'))):>5}"
                f"{float(str(item.get('annualised_premium_percent'))):>9.2f}"
                f"{float(str(item.get('annualised_volatility_percent'))):>8.2f}"
                f"{float(str(item.get('sharpe_annualised'))):>7.3f}"
                f"{float(str(item.get('mde_one_sided_percent_per_year'))):>8.2f}"
                f"{float(str(item.get('one_sided_p_value_hac'))):>9.4f}"
                f"{adjusted.get(key, float('nan')):>9.4f}"
            )

    lines.extend(["", "POOLED CELLS (cross-region joint bootstrap)"])
    lines.append(
        f"{'factor':<5}{'era role':<24}{'months':>7}{'ann%':>9}{'90% low':>9}"
        f"{'90% high':>10}{'MDE80':>8}{'MDElo':>8}{'MDEhi':>8}{'MDEhac':>8}"
        f"{'effReg':>8}{'effN':>8}{'naiveN':>8}"
    )
    pooled = result.diagnostics.get("pooled_cells")
    if isinstance(pooled, Sequence) and not isinstance(pooled, str):
        for item in pooled:
            if not isinstance(item, Mapping):
                continue
            low = high = float("nan")
            boots = item.get("bootstraps")
            if isinstance(boots, Sequence) and not isinstance(boots, str):
                for boot in boots:
                    if (
                        isinstance(boot, Mapping)
                        and boot.get("valid") is True
                        and boot.get("block_length_source") == "frozen"
                    ):
                        interval = boot.get("two_sided_90")
                        if isinstance(interval, Sequence) and not isinstance(interval, str):
                            low, high = float(str(interval[0])), float(str(interval[1]))
            mde_low = mde_high = float("nan")
            panels = item.get("panel_intervals")
            if isinstance(panels, Sequence) and not isinstance(panels, str):
                for entry in panels:
                    if (
                        isinstance(entry, Mapping)
                        and entry.get("statistic") == "pooled_mde_one_sided_percent_per_year"
                    ):
                        bounds = entry.get("two_sided_90")
                        if isinstance(bounds, Sequence) and not isinstance(bounds, str):
                            mde_low = float(str(bounds[0]))
                            mde_high = float(str(bounds[1]))
            sample = item.get("effective_sample_size")
            sample_map = sample if isinstance(sample, Mapping) else {}
            lines.append(
                f"{item.get('factor')!s:<5}{item.get('era_role')!s:<24}"
                f"{int(str(item.get('months'))):>7}"
                f"{float(str(item.get('annualised_premium_percent'))):>9.2f}"
                f"{low:>9.2f}{high:>10.2f}"
                f"{float(str(item.get('mde_one_sided_percent_per_year'))):>8.2f}"
                f"{mde_low:>8.2f}{mde_high:>8.2f}"
                f"{float(str(item.get('mde_one_sided_hac_percent_per_year'))):>8.2f}"
                f"{float(str(sample_map.get('effective_regions'))):>8.2f}"
                f"{float(str(sample_map.get('effective_region_months_iid'))):>8.0f}"
                f"{int(str(sample_map.get('naive_region_months_if_independent'))):>8}"
            )

    lines.append("")
    verdicts = result.diagnostics.get("verdicts")
    if isinstance(verdicts, Sequence) and not isinstance(verdicts, str):
        for verdict in verdicts:
            if isinstance(verdict, Mapping):
                lines.append(
                    f"{verdict.get('factor')}: {verdict.get('status')}  "
                    f"[{verdict.get('falsifier_branch')}]"
                )
                lines.append(f"  {verdict.get('reasoning')}")
                if verdict.get("what_would_fire"):
                    lines.append(f"  WOULD FIRE: {verdict.get('what_would_fire')}")
    lines.append("")
    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def _manifest_hashes(specification: Specification) -> tuple[str, ...]:
    hashes: list[str] = []
    parameters = specification.parameters
    if not isinstance(parameters, Mapping):
        return ()
    pin = parameters.get("source_pin")
    if not isinstance(pin, Mapping):
        return ()
    entries = pin.get("series")
    if not isinstance(entries, Iterable) or isinstance(entries, str | Mapping):
        return ()
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        location = entry.get("committed_manifest")
        if isinstance(location, str):
            path = _workspace_root() / location
            if path.is_file():
                hashes.append(read_manifest(path).sha256_manifest())
    return tuple(hashes)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 005 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_005_regional_replication",
        description=(
            "Replicate Experiment 001's post-publication grid across three regions "
            "and measure the effective sample size pooling actually buys, writing a "
            "ledger entry for the attempt."
        ),
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument(
        "--view-results",
        action="store_true",
        help=(
            "print the computed numbers AND append a results_viewed entry to the "
            "ledger. Looking is an event with consequences, so it is recorded."
        ),
    )
    arguments = parser.parse_args(argv)

    specification = load_specification(arguments.specification)
    ledger = Ledger(arguments.ledger)

    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=_manifest_hashes(specification),
    )

    print(f"run_id       {outcome.run_id}")
    print(f"spec_hash    {outcome.spec_hash}")
    print(f"status       {outcome.status.value}")
    print(f"result       {outcome.result.status.value if outcome.result else 'none'}")
    print(f"git_commit   {outcome.git_state.commit} (dirty={outcome.git_state.dirty})")
    for record in outcome.artifacts:
        print(f"artifact     {record.path}  {record.sha256}  {record.size_bytes}B")

    if arguments.view_results:
        print()
        print(_render_console_report(outcome))
        ledger.record_results_viewed(
            outcome.run_id,
            origin=Origin(arguments.origin),
            notes=(
                "numbers printed to the console by the --view-results flag of "
                "exp_005_regional_replication"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
