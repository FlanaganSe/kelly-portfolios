"""Experiment 001: factor persistence and decay across frozen eras.

Reads the Ken French US five-factor and momentum monthly files at the vintages
pinned in ``research/experiments/exp_001_factor_decay.yaml`` and reports, for
each of HML, UMD, RMW and CMA over each frozen era, what the long-short research
series did and how uncertain that is.

What this experiment is not
---------------------------
* It is **not** a test of whether publication caused anything. A before/after
  comparison across a publication date is descriptive and confounds publication
  with changing composition, valuation regimes, crowding and chance. The eras are
  frozen from the publication record so that the *description* is not tuned; that
  is all freezing them buys.
* It is **not** a net-of-cost result. These are academic zero-investment
  long-short portfolios, gross of transaction costs, shorting costs, borrow and
  fees, and a retail investor cannot hold most of them at all. Every figure is an
  upper bound of unknown tightness. The cost model appears in its own column and
  is never subtracted from a premium.
* It **cannot** conclude that a factor "works". The closed status taxonomy in
  :class:`~portfolio_edge.experiments.result.ResultStatus` has no such value.

Two constraints inherited from upstream
---------------------------------------
1. **The Phase 1 gate came back UNRESOLVED, not PASS.** Means, t-statistics and
   correlations reproduce Fama and French (2015) Table 4; the standard deviations
   of HML and RMW do not, by 3.03% and 5.09%, against two independently typeset
   vintages. That is a systematic denominator uncertainty which does not shrink
   with more data and is in no bootstrap interval. Every Sharpe ratio, volatility
   and minimum detectable effect for those two factors therefore carries a second
   band, reported *beside* the sampling interval and never merged into it.
2. **Power is the point.** For every cell the output reports the smallest true
   premium the window could have detected at 80% power. A cell whose interval
   contains zero is only evidence of absence if that number is small.

Run it::

    uv run python -m portfolio_edge.experiments.exp_001_factor_decay --view-results
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

from portfolio_edge.core.costs import (
    K_FLOOR,
    K_PESSIMISTIC,
    TurnoverCostModel,
    is_retail_implementable,
)
from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.returns import (
    Frequency,
    compound_simple,
    geometric_mean,
)
from portfolio_edge.core.statistics import mean_return, sharpe_ratio, volatility
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_count, month_index, shift_period
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.runner import RunOutcome, run_experiment
from portfolio_edge.experiments.specification import (
    Era,
    JsonValue,
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import (
    bootstrap_confidence_interval,
    optimal_block_length,
)
from portfolio_edge.inference.hac import hac_mean, long_run_variance, newey_west_lag_count
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "ERA_ROLES",
    "FACTORS",
    "CellStatistics",
    "FactorDecayError",
    "GridCell",
    "MonthlySeries",
    "build_registry",
    "default_specification_path",
    "main",
    "minimum_detectable_effect",
    "power_to_detect",
    "resolve_grid",
    "run",
    "window_series",
    "worst_rolling_return",
]

ENTRY_POINT: Final = "exp_001_factor_decay"

#: The four factors under test, in the order the specification lists them.
FACTORS: Final = ("HML", "UMD", "RMW", "CMA")

#: The five era roles that make up the predeclared 4 x 5 multiple-testing family.
ERA_ROLES: Final = (
    "original_sample",
    "first_post_publication",
    "full_post_publication",
    "recent",
    "common_period",
)

MONTHS_PER_YEAR: Final = 12.0

#: Standard normal quantiles, as constants rather than a scipy call, so that the
#: inference in this module has no dependency that could silently change.
_Z_80: Final = 0.8416212335729143  # Phi^-1(0.80), the power target
_Z_95: Final = 1.6448536269514722  # Phi^-1(0.95), one-sided 5%
_Z_975: Final = 1.959963984540054  # Phi^-1(0.975), two-sided 5%

FloatArray = NDArray[np.float64]


class FactorDecayError(RuntimeError):
    """The experiment could not be attempted against the declared vintages."""


def _json_float(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``.

    JSON has no NaN, and the artifact writer refuses one rather than emitting the
    non-standard literal. A statistic that could not be computed is absent, and
    ``null`` says that where ``NaN`` would only crash later.
    """
    return None if math.isnan(value) or math.isinf(value) else value


# --------------------------------------------------------------------------- #
# Normal distribution, in closed form
# --------------------------------------------------------------------------- #


def standard_normal_cdf(z: float) -> float:
    """``Phi(z)`` via ``erfc``, exact to double precision in both tails."""
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def one_sided_p_value(t_statistic: float) -> float:
    """``P(Z > t)`` — the p-value for the alternative "the premium is positive"."""
    return 0.5 * math.erfc(t_statistic / math.sqrt(2.0))


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise FactorDecayError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise FactorDecayError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise FactorDecayError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise FactorDecayError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise FactorDecayError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    return tuple(str(item) for item in items)


def _integers(values: Sequence[JsonValue], *, where: str) -> tuple[int, ...]:
    out: list[int] = []
    for index, item in enumerate(values):
        if isinstance(item, bool) or not isinstance(item, int):
            raise FactorDecayError(f"{where}[{index}] must be an integer, got {item!r}")
        out.append(item)
    return tuple(out)


# --------------------------------------------------------------------------- #
# Series and windows
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class MonthlySeries:
    """One factor's monthly return series, in decimal units, with its labels.

    ``periods`` and ``values`` are the same length and strictly month-by-month.
    Nothing is forward-filled: a month absent from the source file is absent
    here, and :func:`window_series` reports the shortfall rather than repairing
    it.
    """

    name: str
    periods: tuple[str, ...]
    values: FloatArray
    source_dataset_id: str
    source_column: str

    def __post_init__(self) -> None:
        if len(self.periods) != self.values.size:
            raise FactorDecayError(
                f"series {self.name!r} has {len(self.periods)} labels and "
                f"{self.values.size} values"
            )

    @property
    def first_observation(self) -> str | None:
        return self.periods[0] if self.periods else None

    @property
    def last_observation(self) -> str | None:
        return self.periods[-1] if self.periods else None


@dataclass(frozen=True, slots=True, kw_only=True)
class Window:
    """A contiguous slice of one series, with its boundary findings."""

    name: str
    start: str
    end: str
    periods: tuple[str, ...]
    values: FloatArray
    findings: tuple[str, ...]

    @property
    def observations(self) -> int:
        return self.values.size


def window_series(series: MonthlySeries, *, start: str, end: str) -> Window:
    """Slice ``series`` to ``[start, end]`` and record every boundary problem.

    Findings are returned, never raised and never repaired. A window that is
    short because the file starts later is a fact about the data; a window that
    is short because months are missing from the middle is a fact about the file,
    and the two are reported differently.
    """
    first, last = month_index(start), month_index(end)
    selected = [
        index for index, period in enumerate(series.periods) if first <= month_index(period) <= last
    ]
    periods = tuple(series.periods[index] for index in selected)
    values = series.values[np.asarray(selected, dtype=np.intp)] if selected else np.empty(0)

    findings: list[str] = []
    if not periods:
        findings.append(f"{series.name}: window {start}..{end} selected no rows at all")
    else:
        span = month_count(start, end)
        if len(periods) != span:
            findings.append(
                f"{series.name}: window {start}..{end} spans {span} calendar months "
                f"but holds {len(periods)} rows"
            )
        if periods[0] != start:
            findings.append(
                f"{series.name}: window starts at {periods[0]}, not the frozen {start}; "
                "the source file does not reach back that far"
            )
        if periods[-1] != end:
            findings.append(f"{series.name}: window ends at {periods[-1]}, not the frozen {end}")
        indices = [month_index(period) for period in periods]
        gaps = [
            f"{periods[i]}->{periods[i + 1]}"
            for i in range(len(periods) - 1)
            if indices[i + 1] - indices[i] != 1
        ]
        if gaps:
            findings.append(f"{series.name}: {len(gaps)} month gaps inside the window: {gaps[:5]}")
        if not np.all(np.isfinite(values)):
            findings.append(f"{series.name}: non-finite values inside the window")

    return Window(
        name=series.name,
        start=start,
        end=end,
        periods=periods,
        values=np.asarray(values, dtype=np.float64),
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# Power
# --------------------------------------------------------------------------- #


def minimum_detectable_effect(
    *,
    standard_error: float,
    power: float = 0.80,
    alpha: float = 0.05,
    one_sided: bool = True,
) -> float:
    """The smallest true mean a test of this size and power could reject zero for.

    ``MDE = (z_{1-alpha'} + z_{power}) * standard_error`` where ``alpha'`` is
    ``alpha`` one-sided or ``alpha / 2`` two-sided. Supplying the *standard error*
    rather than a volatility and a sample size is deliberate: it is the only form
    that stays correct when the standard error is HAC rather than
    ``sigma / sqrt(T)``, and monthly factor returns are autocorrelated enough that
    the difference matters.

    The result is in the units of ``standard_error``.
    """
    if standard_error <= 0.0:
        raise ValueError(f"standard_error must be positive, got {standard_error}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must lie in (0, 1), got {power}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must lie in (0, 1), got {alpha}")
    z_alpha = _normal_quantile(1.0 - (alpha if one_sided else alpha / 2.0))
    z_power = _normal_quantile(power)
    return (z_alpha + z_power) * standard_error


def power_to_detect(
    effect: float,
    *,
    standard_error: float,
    alpha: float = 0.05,
    one_sided: bool = True,
) -> float:
    """Probability of rejecting a zero mean when the true mean is ``effect``.

    The exact inverse of :func:`minimum_detectable_effect`: feeding it that
    function's output returns ``power``. Uses the normal approximation, which is
    what the closed-form MDE assumes, so the two are consistent by construction
    rather than approximately.
    """
    if standard_error <= 0.0:
        raise ValueError(f"standard_error must be positive, got {standard_error}")
    z_alpha = _normal_quantile(1.0 - (alpha if one_sided else alpha / 2.0))
    return standard_normal_cdf(effect / standard_error - z_alpha)


def _normal_quantile(p: float) -> float:
    """``Phi^-1(p)`` for the handful of probabilities this module uses.

    A lookup rather than an implementation: the experiment needs exactly three
    quantiles, and a table of exact constants cannot drift with a library
    version. Anything else is a programming error, not a runtime input.
    """
    table = {0.80: _Z_80, 0.95: _Z_95, 0.975: _Z_975}
    for probability, quantile in table.items():
        if math.isclose(p, probability, rel_tol=0.0, abs_tol=1e-12):
            return quantile
    raise ValueError(
        f"no exact normal quantile tabulated for p={p!r}; this module uses only "
        f"{sorted(table)} and adding one means adding a constant, not a solver"
    )


# --------------------------------------------------------------------------- #
# Rolling windows
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RollingWorst:
    """The worst compounded return over any window of a fixed length."""

    window_months: int
    worst_return: float | None
    start: str | None
    end: str | None
    windows_available: int
    unavailable_reason: str = ""


def worst_rolling_return(
    values: FloatArray, periods: Sequence[str], window_months: int
) -> RollingWorst:
    """Worst *compounded* return over any contiguous window of ``window_months``.

    Compounded, not summed: a sum of monthly returns is not a return over the
    window, and the difference grows with the window length, which is exactly the
    range these statistics are read over.
    """
    if window_months < 1:
        raise ValueError(f"window_months must be positive, got {window_months}")
    n = values.size
    if n < window_months:
        return RollingWorst(
            window_months=window_months,
            worst_return=None,
            start=None,
            end=None,
            windows_available=0,
            unavailable_reason=(
                f"the era holds {n} months, fewer than the {window_months}-month window"
            ),
        )
    growth = np.cumprod(1.0 + values)
    padded = np.concatenate(([1.0], growth))
    windows = padded[window_months:] / padded[:-window_months] - 1.0
    index = int(np.argmin(windows))
    return RollingWorst(
        window_months=window_months,
        worst_return=float(windows[index]),
        start=periods[index],
        end=periods[index + window_months - 1],
        windows_available=int(windows.size),
    )


# --------------------------------------------------------------------------- #
# The grid
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class GridCell:
    """One predeclared (factor, era role) cell of the multiple-testing family."""

    factor: str
    era_role: str
    era_name: str
    start: str
    end: str

    @property
    def key(self) -> str:
        return f"{self.factor}/{self.era_role}"


def resolve_grid(specification: Specification) -> tuple[GridCell, ...]:
    """Build the predeclared grid from ``parameters.primary_grid`` and the eras.

    The grid is read from the specification rather than constructed here so that
    the multiple-testing family is fixed by the frozen document, not by whatever
    the code happened to loop over.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    grid = _mapping(_at(parameters, "primary_grid", where="parameters"), where="primary_grid")
    roles = _strings(grid, "era_roles", where="primary_grid")
    if tuple(roles) != ERA_ROLES:
        raise FactorDecayError(
            f"primary_grid.era_roles is {roles}, but this module implements {ERA_ROLES}"
        )
    cells_by_factor = _mapping(_at(grid, "cells", where="primary_grid"), where="primary_grid.cells")
    eras = {era.name: era for era in specification.sample_policy.eras}

    cells: list[GridCell] = []
    for factor in FACTORS:
        if factor not in cells_by_factor:
            raise FactorDecayError(f"primary_grid.cells has no entry for {factor!r}")
        by_role = _mapping(cells_by_factor[factor], where=f"primary_grid.cells.{factor}")
        for role in ERA_ROLES:
            era_name = _text(by_role, role, where=f"primary_grid.cells.{factor}")
            era = eras.get(era_name)
            if era is None:
                raise FactorDecayError(
                    f"primary_grid.cells.{factor}.{role} names era {era_name!r}, "
                    f"which sample_policy does not define; known: {sorted(eras)}"
                )
            cells.append(
                GridCell(
                    factor=factor,
                    era_role=role,
                    era_name=era.name,
                    start=era.start,
                    end=era.end,
                )
            )
    expected = len(FACTORS) * len(ERA_ROLES)
    if len(cells) != expected:
        raise FactorDecayError(f"expected {expected} cells, built {len(cells)}")
    return tuple(cells)


def alternative_date_eras(specification: Specification) -> tuple[tuple[str, Era], ...]:
    """The predeclared alternative-publication-date eras, and the factor each tests.

    These sit OUTSIDE the multiple-testing family by construction: they exist to
    show how much the answer moves when the discovery date moves, and counting
    them as discoveries would be counting the same hypothesis twice.
    """
    mapping = {
        "hml_post_rosenberg_alternative": "HML",
        "umd_post_carhart_alternative": "UMD",
    }
    eras = {era.name: era for era in specification.sample_policy.eras}
    out: list[tuple[str, Era]] = []
    for era_name, factor in mapping.items():
        era = eras.get(era_name)
        if era is None:
            raise FactorDecayError(f"the specification no longer defines era {era_name!r}")
        out.append((factor, era))
    return tuple(out)


# --------------------------------------------------------------------------- #
# Cell statistics
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BootstrapSummary:
    """One block-bootstrap resampling of one statistic, at one block length."""

    statistic: str
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
            "statistic": self.statistic,
            "block_length": self.block_length,
            "block_length_source": self.block_length_source,
            "point_estimate": self.point_estimate,
            "two_sided_90": [self.lower_90, self.upper_90],
            "two_sided_95": [self.lower_95, self.upper_95],
            "one_sided_lower_95": self.one_sided_lower_95,
            "bootstrap_standard_error": self.standard_error,
            "n_resamples": self.n_resamples,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class SecondMomentBand:
    """The Phase 1 systematic uncertainty in a factor's volatility.

    Kept separate from every sampling interval on purpose. It is not sampling
    error, it does not shrink with more data, and adding it in quadrature to a
    bootstrap interval would present a systematic disagreement between two data
    vintages as if it were noise.
    """

    factor: str
    relative_band: float
    measured: bool
    volatility_low: float
    volatility_high: float
    sharpe_low: float
    sharpe_high: float
    mde_low: float
    mde_high: float
    note: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "relative_band_on_volatility": _json_float(self.relative_band),
            "measured": self.measured,
            "annualised_volatility_percent": [self.volatility_low, self.volatility_high],
            "annualised_sharpe": [self.sharpe_low, self.sharpe_high],
            "mde_one_sided_percent_per_year": [self.mde_low, self.mde_high],
            "note": self.note,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CostIllustration:
    """What a tradable strategy of comparable turnover would have paid.

    Never subtracted from anything in this experiment. The French series have no
    turnover, no holdings and no tradable form, so there is no net figure for
    them to be computed; this is the size of the gap between the gross number and
    any number an investor could have earned.
    """

    factor: str
    turnover_optimistic_pct: float
    turnover_pessimistic_pct: float
    cost_optimistic_annual_percent: float
    cost_pessimistic_annual_percent: float
    retail_implementable_at_optimistic: bool
    retail_implementable_at_pessimistic: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "one_sided_monthly_turnover_percent": [
                self.turnover_optimistic_pct,
                self.turnover_pessimistic_pct,
            ],
            "illustrative_cost_percent_per_year": [
                self.cost_optimistic_annual_percent,
                self.cost_pessimistic_annual_percent,
            ],
            "retail_implementable": [
                self.retail_implementable_at_optimistic,
                self.retail_implementable_at_pessimistic,
            ],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CellStatistics:
    """Everything reported for one factor over one era."""

    factor: str
    era_role: str
    era_name: str
    start: str
    end: str
    observations: int
    first_observation: str
    last_observation: str
    boundary_findings: tuple[str, ...]

    mean_percent_per_month: float
    annualised_premium_percent: float
    volatility_percent_per_month: float
    annualised_volatility_percent: float

    geometric_mean_percent_per_month: float
    geometric_annual_percent: float
    arithmetic_geometric_gap_percent: float
    terminal_growth_multiple: float

    sharpe_monthly: float
    sharpe_annualised: float
    sharpe_standard_error_annualised: float

    conventional_standard_error_annual: float
    conventional_t_statistic: float
    hac_standard_error_annual: float
    hac_t_statistic: float
    hac_lag_count: int
    effective_sample_size: float

    one_sided_p_value_hac: float
    two_sided_p_value_hac: float

    mde_one_sided_percent_per_year: float
    mde_two_sided_percent_per_year: float
    mde_one_sided_hac_percent_per_year: float
    power_at_materiality: float
    power_at_true_factor_reference: float

    max_drawdown: float
    max_time_under_water_months: int
    drawdown_open_at_end: bool

    rolling: tuple[RollingWorst, ...]
    bootstraps: tuple[BootstrapSummary, ...]
    second_moment_band: SecondMomentBand | None

    @property
    def primary_bootstrap(self) -> BootstrapSummary:
        for item in self.bootstraps:
            if (
                item.statistic == "annualised_premium_percent"
                and item.block_length_source == "frozen"
            ):
                return item
        raise FactorDecayError(f"{self.factor}/{self.era_name} has no primary bootstrap")

    def bootstrap_named(self, statistic: str, source: str) -> BootstrapSummary | None:
        for item in self.bootstraps:
            if item.statistic == statistic and item.block_length_source == source:
                return item
        return None

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "era_role": self.era_role,
            "era": self.era_name,
            "start": self.start,
            "end": self.end,
            "observations": self.observations,
            "first_observation": self.first_observation,
            "last_observation": self.last_observation,
            "boundary_findings": list(self.boundary_findings),
            "mean_percent_per_month": self.mean_percent_per_month,
            "annualised_premium_percent": self.annualised_premium_percent,
            "volatility_percent_per_month": self.volatility_percent_per_month,
            "annualised_volatility_percent": self.annualised_volatility_percent,
            "geometric_mean_percent_per_month": self.geometric_mean_percent_per_month,
            "geometric_annual_percent": self.geometric_annual_percent,
            "arithmetic_geometric_gap_percent": self.arithmetic_geometric_gap_percent,
            "terminal_growth_multiple": self.terminal_growth_multiple,
            "sharpe_monthly": self.sharpe_monthly,
            "sharpe_annualised": self.sharpe_annualised,
            "sharpe_standard_error_annualised": self.sharpe_standard_error_annualised,
            "conventional_standard_error_annual": self.conventional_standard_error_annual,
            "conventional_t_statistic": self.conventional_t_statistic,
            "hac_standard_error_annual": self.hac_standard_error_annual,
            "hac_t_statistic": self.hac_t_statistic,
            "hac_lag_count": self.hac_lag_count,
            "effective_sample_size": _json_float(self.effective_sample_size),
            "one_sided_p_value_hac": self.one_sided_p_value_hac,
            "two_sided_p_value_hac": self.two_sided_p_value_hac,
            "mde_one_sided_percent_per_year": self.mde_one_sided_percent_per_year,
            "mde_two_sided_percent_per_year": self.mde_two_sided_percent_per_year,
            "mde_one_sided_hac_percent_per_year": self.mde_one_sided_hac_percent_per_year,
            "power_at_materiality": self.power_at_materiality,
            "power_at_true_factor_reference": self.power_at_true_factor_reference,
            "max_drawdown": self.max_drawdown,
            "max_time_under_water_months": self.max_time_under_water_months,
            "drawdown_open_at_end": self.drawdown_open_at_end,
            "worst_rolling": [
                {
                    "window_months": item.window_months,
                    "worst_return": item.worst_return,
                    "start": item.start,
                    "end": item.end,
                    "windows_available": item.windows_available,
                    "unavailable_reason": item.unavailable_reason,
                }
                for item in self.rolling
            ],
            "bootstraps": [item.to_json() for item in self.bootstraps],
            "second_moment_band": (
                self.second_moment_band.to_json() if self.second_moment_band else None
            ),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class InferenceSettings:
    """Everything the frozen specification says about how to draw an interval."""

    frozen_block_length: float
    neighbour_block_lengths: tuple[float, ...]
    n_resamples: int
    method: str
    power_target: float
    materiality_annual_percent: float
    true_factor_reference_annual_percent: float
    rolling_windows_months: tuple[int, ...]
    second_moment_bands: Mapping[str, float]
    second_moment_measured: Mapping[str, bool]


def _bootstrap(
    values: FloatArray,
    *,
    statistic_name: str,
    statistic: object,
    block_length: float,
    block_length_source: str,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> BootstrapSummary:
    """One resampling, from which all three declared intervals are read.

    Drawing once and reading the 5th, 95th, 2.5th and 97.5th percentiles out of
    the same replicate distribution is not a shortcut: it keeps the one-sided and
    two-sided statements consistent with each other, which separate draws would
    not be.
    """
    interval = bootstrap_confidence_interval(
        values,
        statistic,  # type: ignore[arg-type]
        rng=rng,
        method="stationary",
        block_length=block_length,
        n_resamples=settings.n_resamples,
        confidence_level=0.90,
        interval="percentile",
    )
    quantiles = np.asarray(
        np.quantile(interval.replicates, [0.05, 0.95, 0.025, 0.975, 0.05]), dtype=np.float64
    )
    low_90, high_90, low_95, high_95, one_sided = (float(value) for value in quantiles)
    return BootstrapSummary(
        statistic=statistic_name,
        block_length=block_length,
        block_length_source=block_length_source,
        point_estimate=interval.point_estimate,
        lower_90=low_90,
        upper_90=high_90,
        lower_95=low_95,
        upper_95=high_95,
        one_sided_lower_95=one_sided,
        standard_error=interval.standard_error,
        n_resamples=settings.n_resamples,
    )


def _annualised_premium_percent(series: FloatArray) -> float:
    return float(np.mean(series)) * MONTHS_PER_YEAR * 100.0


def _annualised_sharpe(series: FloatArray) -> float:
    sigma = float(np.std(series, ddof=1))
    if sigma <= 0.0:
        return 0.0
    return float(np.mean(series)) / sigma * math.sqrt(MONTHS_PER_YEAR)


def compute_cell(
    window: Window,
    *,
    factor: str,
    era_role: str,
    era_name: str,
    settings: InferenceSettings,
    rng: np.random.Generator,
    with_bootstrap: bool = True,
) -> CellStatistics:
    """Every statistic this experiment reports for one factor over one era.

    ``window.values`` is in decimal units, as the parser produces it. Percentages
    are produced here and nowhere else, so a factor of 100 has exactly one place
    to go wrong.
    """
    values = window.values
    observations = values.size
    if observations < 24:
        raise FactorDecayError(
            f"{factor}/{era_name} holds {observations} months; this experiment "
            "refuses to summarise a window shorter than two years"
        )

    percent = values * 100.0
    mean_month = mean_return(percent)
    sigma_month = volatility(percent, ddof=1)
    annual_premium = MONTHS_PER_YEAR * mean_month
    annual_volatility = math.sqrt(MONTHS_PER_YEAR) * sigma_month

    conventional_se_month = sigma_month / math.sqrt(observations)
    hac = hac_mean(percent, n_lags=newey_west_lag_count(observations))
    long_run = long_run_variance(percent, n_lags=newey_west_lag_count(observations))
    effective_sample = (
        observations * float(sigma_month**2) / long_run if long_run > 0.0 else float("nan")
    )

    sharpe = sharpe_ratio(percent, frequency=Frequency.MONTHLY, risk_free=0.0)

    geometric_month = geometric_mean(values)
    terminal = compound_simple(values)
    geometric_annual = (1.0 + geometric_month) ** MONTHS_PER_YEAR - 1.0

    equity = np.cumprod(1.0 + values)
    drawdown = drawdown_summary(equity)

    hac_t = hac.t_statistic
    one_sided_p = one_sided_p_value(hac_t)
    two_sided_p = 2.0 * one_sided_p_value(abs(hac_t))

    mde_one_sided = MONTHS_PER_YEAR * minimum_detectable_effect(
        standard_error=conventional_se_month, power=settings.power_target, one_sided=True
    )
    mde_two_sided = MONTHS_PER_YEAR * minimum_detectable_effect(
        standard_error=conventional_se_month, power=settings.power_target, one_sided=False
    )
    mde_hac = MONTHS_PER_YEAR * minimum_detectable_effect(
        standard_error=hac.standard_error, power=settings.power_target, one_sided=True
    )
    power_materiality = power_to_detect(
        settings.materiality_annual_percent / MONTHS_PER_YEAR,
        standard_error=conventional_se_month,
        one_sided=True,
    )
    power_reference = power_to_detect(
        settings.true_factor_reference_annual_percent / MONTHS_PER_YEAR,
        standard_error=conventional_se_month,
        one_sided=True,
    )

    rolling = tuple(
        worst_rolling_return(values, window.periods, months)
        for months in settings.rolling_windows_months
    )

    bootstraps: list[BootstrapSummary] = []
    if with_bootstrap:
        automatic = optimal_block_length(values)
        lengths: list[tuple[float, str]] = [(settings.frozen_block_length, "frozen")]
        lengths.extend(
            (length, "predeclared-neighbour") for length in settings.neighbour_block_lengths
        )
        lengths.append((automatic.stationary, "politis-white-automatic"))
        for length, source in lengths:
            bootstraps.append(
                _bootstrap(
                    values,
                    statistic_name="annualised_premium_percent",
                    statistic=_annualised_premium_percent,
                    block_length=length,
                    block_length_source=source,
                    settings=settings,
                    rng=rng,
                )
            )
        for length, source in (
            (settings.frozen_block_length, "frozen"),
            (automatic.stationary, "politis-white-automatic"),
        ):
            bootstraps.append(
                _bootstrap(
                    values,
                    statistic_name="annualised_sharpe",
                    statistic=_annualised_sharpe,
                    block_length=length,
                    block_length_source=source,
                    settings=settings,
                    rng=rng,
                )
            )

    band = _second_moment_band(
        factor,
        annual_volatility=annual_volatility,
        annual_sharpe=sharpe.annualised_sharpe,
        mde=mde_one_sided,
        settings=settings,
    )

    return CellStatistics(
        factor=factor,
        era_role=era_role,
        era_name=era_name,
        start=window.start,
        end=window.end,
        observations=observations,
        first_observation=window.periods[0],
        last_observation=window.periods[-1],
        boundary_findings=window.findings,
        mean_percent_per_month=mean_month,
        annualised_premium_percent=annual_premium,
        volatility_percent_per_month=sigma_month,
        annualised_volatility_percent=annual_volatility,
        geometric_mean_percent_per_month=100.0 * geometric_month,
        geometric_annual_percent=100.0 * geometric_annual,
        arithmetic_geometric_gap_percent=annual_premium - 100.0 * geometric_annual,
        terminal_growth_multiple=1.0 + terminal,
        sharpe_monthly=sharpe.sharpe_per_period,
        sharpe_annualised=sharpe.annualised_sharpe,
        sharpe_standard_error_annualised=(
            sharpe.standard_error_per_period * math.sqrt(MONTHS_PER_YEAR)
        ),
        conventional_standard_error_annual=MONTHS_PER_YEAR * conventional_se_month,
        conventional_t_statistic=mean_month / conventional_se_month,
        hac_standard_error_annual=MONTHS_PER_YEAR * hac.standard_error,
        hac_t_statistic=hac_t,
        hac_lag_count=hac.n_lags,
        effective_sample_size=effective_sample,
        one_sided_p_value_hac=one_sided_p,
        two_sided_p_value_hac=min(1.0, two_sided_p),
        mde_one_sided_percent_per_year=mde_one_sided,
        mde_two_sided_percent_per_year=mde_two_sided,
        mde_one_sided_hac_percent_per_year=mde_hac,
        power_at_materiality=power_materiality,
        power_at_true_factor_reference=power_reference,
        max_drawdown=drawdown.max_drawdown,
        max_time_under_water_months=drawdown.max_time_under_water,
        drawdown_open_at_end=drawdown.open_at_end,
        rolling=rolling,
        bootstraps=tuple(bootstraps),
        second_moment_band=band,
    )


def _second_moment_band(
    factor: str,
    *,
    annual_volatility: float,
    annual_sharpe: float,
    mde: float,
    settings: InferenceSettings,
) -> SecondMomentBand | None:
    """Apply the Phase 1 volatility disagreement to everything that divides by sigma."""
    band = settings.second_moment_bands.get(factor)
    if band is None or band <= 0.0:
        if settings.second_moment_measured.get(factor, True):
            return None
        return SecondMomentBand(
            factor=factor,
            relative_band=float("nan"),
            measured=False,
            volatility_low=annual_volatility,
            volatility_high=annual_volatility,
            sharpe_low=annual_sharpe,
            sharpe_high=annual_sharpe,
            mde_low=mde,
            mde_high=mde,
            note=(
                "this series comes from a file that was never gated against a "
                "printed table, so its second moment is UNMEASURED rather than "
                "verified. No band is quoted because none has been established, "
                "which is a weaker statement than a band of zero."
            ),
        )
    return SecondMomentBand(
        factor=factor,
        relative_band=band,
        measured=True,
        volatility_low=annual_volatility * (1.0 - band),
        volatility_high=annual_volatility * (1.0 + band),
        sharpe_low=annual_sharpe / (1.0 + band),
        sharpe_high=annual_sharpe / (1.0 - band),
        mde_low=mde * (1.0 - band),
        mde_high=mde * (1.0 + band),
        note=(
            f"systematic, not sampling: this repository's {factor} standard "
            f"deviation differs from the printed Fama-French (2015) Table 4 value "
            f"by {band:.2%}, and the disagreement survives against two "
            "independently typeset vintages. It does not shrink with more data "
            "and is in no bootstrap interval. Applied symmetrically because the "
            "direction of the error is unknown."
        ),
    )


def cost_illustration(factor: str, parameters: Mapping[str, JsonValue]) -> CostIllustration:
    """The declared turnover assumptions run through the repository's cost rule."""
    illustration = _mapping(
        _at(parameters, "cost_illustration", where="parameters"), where="cost_illustration"
    )
    by_factor = _mapping(
        _at(illustration, "one_sided_monthly_turnover_percent", where="cost_illustration"),
        where="cost_illustration.one_sided_monthly_turnover_percent",
    )
    entry = _mapping(_at(by_factor, factor, where="turnover"), where=f"turnover.{factor}")
    optimistic = _number(entry, "optimistic", where=f"turnover.{factor}")
    pessimistic = _number(entry, "pessimistic", where=f"turnover.{factor}")
    k_optimistic = _number(illustration, "k_optimistic", where="cost_illustration")
    k_pessimistic = _number(illustration, "k_pessimistic", where="cost_illustration")
    if not math.isclose(k_optimistic, K_FLOOR) or not math.isclose(k_pessimistic, K_PESSIMISTIC):
        raise FactorDecayError(
            f"the specification declares k = {k_optimistic}/{k_pessimistic} but "
            f"portfolio_edge.core.costs carries {K_FLOOR}/{K_PESSIMISTIC}. One of "
            "them moved; reconcile them rather than reporting either."
        )
    low = TurnoverCostModel(k=k_optimistic).cost_bp_per_period(optimistic)
    high = TurnoverCostModel(k=k_pessimistic).cost_bp_per_period(pessimistic)
    return CostIllustration(
        factor=factor,
        turnover_optimistic_pct=optimistic,
        turnover_pessimistic_pct=pessimistic,
        cost_optimistic_annual_percent=low * MONTHS_PER_YEAR / 100.0,
        cost_pessimistic_annual_percent=high * MONTHS_PER_YEAR / 100.0,
        retail_implementable_at_optimistic=is_retail_implementable(optimistic),
        retail_implementable_at_pessimistic=is_retail_implementable(pessimistic),
    )


# --------------------------------------------------------------------------- #
# Loading the pinned sources
# --------------------------------------------------------------------------- #


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def _load_sources(
    specification: Specification,
) -> tuple[dict[str, MonthlySeries], dict[str, MonthlySeries], list[JsonValue]]:
    """Fetch, pin, parse and validate every pinned file.

    Returns the factor series, the reference series, and one provenance record
    per file. A hash mismatch ABORTS: Ken French rebuilds the whole history from
    each new CRSP vintage, so an unrecognised hash is a new vintage, and a
    premium computed from an unrecognised file looks exactly like a good one.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="parameters.source_pin")
    entries = _sequence(_at(pin, "series", where="source_pin"), where="source_pin.series")

    cache = RawCache()
    factors: dict[str, MonthlySeries] = {}
    references: dict[str, MonthlySeries] = {}
    provenance: list[JsonValue] = []

    for index, item in enumerate(entries):
        where = f"source_pin.series[{index}]"
        spec_entry = _mapping(item, where=where)
        dataset = french.get_dataset(_text(spec_entry, "dataset_id", where=where))
        cached = french.download(cache, dataset)

        expected_raw = _text(spec_entry, "expected_sha256_raw", where=where)
        if cached.sha256 != expected_raw:
            raise FactorDecayError(
                f"the file at {dataset.url} now hashes to {cached.sha256}, but this "
                f"specification is frozen against {expected_raw}. Ken French rebuilds "
                "the whole history from each new CRSP vintage, so this is a new "
                "vintage, not a corrupted download. Freeze a new specification "
                "against it rather than reporting premia from an unrecognised file."
            )

        parsed = french.parse(cache, cached, dataset=dataset)
        table = parsed.table(_text(spec_entry, "table_id", where=where))
        expected_columns = _strings(spec_entry, "expected_columns", where=where)
        report = validate_table(
            table,
            dataset_id=_text(spec_entry, "manifest_dataset_id", where=where),
            expected_columns=expected_columns,
            expected_frequency="monthly",
        )
        if not report.ok:
            raise FactorDecayError(
                f"{dataset.dataset_id} failed validation before any statistic was "
                "computed: " + "; ".join(report.summary())
            )
        expected_normalized = _text(spec_entry, "expected_sha256_normalized", where=where)
        if table.sha256_normalized() != expected_normalized:
            raise FactorDecayError(
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
                raise FactorDecayError(
                    f"{manifest_path} records sha256_raw {manifest.sha256_raw}, "
                    f"which is not the pinned {expected_raw}"
                )

        for name in _strings(spec_entry, "factor_columns", where=where):
            factors[name] = _series_from_table(table, name, dataset_id=dataset.dataset_id)
        for name in _strings(spec_entry, "reference_columns", where=where):
            references[name] = _series_from_table(table, name, dataset_id=dataset.dataset_id)

        provenance.append(
            {
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
    return factors, references, provenance


_COLUMN_ALIASES: Final[Mapping[str, str]] = {"UMD": "Mom"}


def _series_from_table(table: ParsedTable, name: str, *, dataset_id: str) -> MonthlySeries:
    """Pull one column out, dropping missing months and recording that it happened."""
    column = _COLUMN_ALIASES.get(name, name)
    if column not in table.columns:
        raise FactorDecayError(
            f"column {column!r} (for factor {name!r}) is absent from table "
            f"{table.table_id!r} of {dataset_id}; found {list(table.columns)}"
        )
    raw = table.column(column)
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
        source_column=column,
    )


def _clip_to_sample_policy(series: MonthlySeries, *, end: str) -> MonthlySeries:
    """Drop everything after the sample policy's end date, before any statistic.

    The holdout is enforced here rather than trusted to every window: observations
    after ``end`` are never read by this experiment under any circumstance, and
    doing that once at the boundary is cheaper to verify than doing it in twenty
    places.
    """
    limit = month_index(end)
    keep = [index for index, period in enumerate(series.periods) if month_index(period) <= limit]
    return MonthlySeries(
        name=series.name,
        periods=tuple(series.periods[index] for index in keep),
        values=series.values[np.asarray(keep, dtype=np.intp)],
        source_dataset_id=series.source_dataset_id,
        source_column=series.source_column,
    )


# --------------------------------------------------------------------------- #
# Multiple testing over the frozen grid
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class GridInference:
    """Uncorrected and corrected inference over the predeclared 20-cell family."""

    keys: tuple[str, ...]
    p_values: tuple[float, ...]
    bh_adjusted: tuple[float, ...]
    bh_rejected: tuple[bool, ...]
    holm_adjusted: tuple[float, ...]
    holm_rejected: tuple[bool, ...]
    alpha: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
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


def correct_grid(cells: Sequence[CellStatistics], *, alpha: float = 0.10) -> GridInference:
    """Benjamini-Hochberg over the frozen family, with Holm as the stricter reading.

    The p-values are one-sided and HAC-based: the alternative of interest is "the
    premium is positive", and monthly factor returns are autocorrelated enough
    that a conventional standard error overstates the evidence.
    """
    keys = tuple(f"{cell.factor}/{cell.era_role}" for cell in cells)
    p_values = tuple(cell.one_sided_p_value_hac for cell in cells)
    bh = benjamini_hochberg(list(p_values), alpha=alpha)
    holm = holm_bonferroni(list(p_values), alpha=alpha)
    return GridInference(
        keys=keys,
        p_values=p_values,
        bh_adjusted=tuple(float(value) for value in bh.adjusted_p_values),
        bh_rejected=tuple(bool(value) for value in bh.rejected),
        holm_adjusted=tuple(float(value) for value in holm.adjusted_p_values),
        holm_rejected=tuple(bool(value) for value in holm.rejected),
        alpha=alpha,
    )


# --------------------------------------------------------------------------- #
# The predeclared decision, per factor
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorVerdict:
    """The frozen rejection rule applied to one factor."""

    factor: str
    status: ResultStatus
    clauses_fired: tuple[str, ...]
    reasoning: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "status": self.status.value,
            "falsifier_clauses_fired": list(self.clauses_fired),
            "reasoning": self.reasoning,
        }


def apply_rejection_rule(
    factor: str,
    by_role: Mapping[str, CellStatistics],
    *,
    materiality: float,
) -> FactorVerdict:
    """Exactly the falsifier and rejection rule frozen in the specification.

    (a) full post-publication point estimate <= 0.
    (b) upper end of the two-sided 90% interval for that premium < materiality.
    (c) full post-publication estimate < 25% of the original-sample estimate AND
        the recent-era estimate <= 0.

    A one-sided 95% test failing to exclude zero is explicitly NOT a falsifier.
    """
    full = by_role["full_post_publication"]
    original = by_role["original_sample"]
    recent = by_role["recent"]
    interval = full.primary_bootstrap

    fired: list[str] = []
    if full.annualised_premium_percent <= 0.0:
        fired.append(
            f"(a) full post-publication premium is "
            f"{full.annualised_premium_percent:+.2f} pp/yr, not positive"
        )
    if interval.upper_90 < materiality:
        fired.append(
            f"(b) the upper end of the two-sided 90% interval is "
            f"{interval.upper_90:+.2f} pp/yr, below the {materiality:.1f} pp/yr "
            "materiality threshold, so the factor is economically negligible even "
            "under a favourable draw"
        )
    decayed = (
        original.annualised_premium_percent > 0.0
        and full.annualised_premium_percent < 0.25 * original.annualised_premium_percent
    )
    if decayed and recent.annualised_premium_percent <= 0.0:
        fired.append(
            f"(c) the full post-publication premium "
            f"({full.annualised_premium_percent:+.2f}) is below 25% of the "
            f"original-sample premium ({original.annualised_premium_percent:+.2f}) "
            f"AND the recent era is {recent.annualised_premium_percent:+.2f}, so "
            "decay is both large and continuing"
        )

    if fired:
        status = ResultStatus.REJECTED
        reasoning = "the predeclared falsifier fired: " + "; ".join(fired)
    elif interval.lower_90 <= 0.0 <= interval.upper_90:
        status = ResultStatus.UNRESOLVED
        reasoning = (
            f"no falsifier clause fired, but the two-sided 90% interval "
            f"[{interval.lower_90:+.2f}, {interval.upper_90:+.2f}] pp/yr contains "
            f"zero. The window could only have detected a premium of "
            f"{full.mde_one_sided_percent_per_year:.2f} pp/yr at 80% power, so this "
            "is 'cannot tell', not 'no premium'."
        )
    else:
        status = ResultStatus.EXPLORATORY
        reasoning = (
            f"no falsifier clause fired and the two-sided 90% interval "
            f"[{interval.lower_90:+.2f}, {interval.upper_90:+.2f}] pp/yr excludes "
            "zero. That permits an investable implementation to be TESTED in "
            "exp_002 and permits nothing else."
        )
    return FactorVerdict(
        factor=factor, status=status, clauses_fired=tuple(fired), reasoning=reasoning
    )


# --------------------------------------------------------------------------- #
# Hostile tests
# --------------------------------------------------------------------------- #


def _drop_best_month(values: FloatArray, periods: Sequence[str]) -> tuple[FloatArray, str]:
    index = int(np.argmax(values))
    keep = np.ones(values.size, dtype=bool)
    keep[index] = False
    return values[keep], periods[index]


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


def _hostile_drop_best(cells: Sequence[CellStatistics], windows: Mapping[str, Window]) -> JsonValue:
    rows: list[JsonValue] = []
    for cell in cells:
        window = windows[f"{cell.factor}/{cell.era_name}"]
        without_month, dropped_month = _drop_best_month(window.values, window.periods)
        without_year, dropped_year = _drop_best_calendar_year(window.values, window.periods)
        rows.append(
            {
                "cell": f"{cell.factor}/{cell.era_role}",
                "premium_percent_per_year": cell.annualised_premium_percent,
                "dropped_best_month": dropped_month,
                "premium_without_best_month": _annualised_premium_percent(without_month),
                "dropped_best_calendar_year": dropped_year,
                "premium_without_best_year": (
                    _annualised_premium_percent(without_year) if dropped_year else None
                ),
            }
        )
    return {
        "description": (
            "A premium that lives in one month or one year is a description of that "
            "month or year, not of a factor."
        ),
        "rows": rows,
    }


def _hostile_shifted_boundaries(
    series: Mapping[str, MonthlySeries],
    cells: Sequence[CellStatistics],
    *,
    sample_end: str,
    months: int = 24,
) -> JsonValue:
    rows: list[JsonValue] = []
    for cell in cells:
        source = series[cell.factor]
        shifted: dict[str, JsonValue] = {}
        for offset in (-months, months):
            start = shift_period(cell.start, offset)
            end = shift_period(cell.end, offset)
            if month_index(end) > month_index(sample_end):
                shifted[f"{offset:+d}"] = {
                    "refused": (
                        f"shifting to {end} would read past the frozen sample end "
                        f"{sample_end}, which this experiment never does"
                    )
                }
                continue
            window = window_series(source, start=start, end=end)
            shifted[f"{offset:+d}"] = {
                "start": window.start,
                "end": window.end,
                "observations": window.observations,
                "premium_percent_per_year": (
                    _annualised_premium_percent(window.values)
                    if window.observations >= 24
                    else None
                ),
            }
        rows.append(
            {
                "cell": f"{cell.factor}/{cell.era_role}",
                "premium_percent_per_year": cell.annualised_premium_percent,
                "shifted": shifted,
            }
        )
    return {
        "description": (
            "Every era boundary moved by plus and minus 24 months. A conclusion "
            "that only holds at the frozen boundary is a conclusion about the "
            "boundary. Shifts that would read past the frozen sample end are "
            "refused rather than truncated, because the holdout is not negotiable."
        ),
        "rows": rows,
    }


def _hostile_synthetic_noise(
    reference: CellStatistics,
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> JsonValue:
    """Run the whole procedure on a zero-mean random walk of matched volatility.

    This is the calibration check the framework demands: it shows what the
    machinery produces from noise of the same size and length, so a reader can
    see how much of any reported structure is the procedure rather than the data.
    """
    sigma = reference.volatility_percent_per_month / 100.0
    draws = rng.normal(loc=0.0, scale=sigma, size=reference.observations)
    periods = tuple(
        shift_period(reference.first_observation, offset) for offset in range(draws.size)
    )
    window = Window(
        name="synthetic",
        start=periods[0],
        end=periods[-1],
        periods=periods,
        values=np.asarray(draws, dtype=np.float64),
        findings=(),
    )
    cell = compute_cell(
        window,
        factor="SYNTHETIC",
        era_role="synthetic",
        era_name="synthetic_matched_noise",
        settings=settings,
        rng=rng,
    )
    return {
        "description": (
            "A zero-mean Gaussian series with the same length and volatility as "
            f"{reference.factor}/{reference.era_role}, put through the identical "
            "procedure. Its premium is zero by construction; whatever interval, "
            "drawdown and worst-rolling figure it produces is what this machinery "
            "produces from nothing."
        ),
        "matched_to": f"{reference.factor}/{reference.era_role}",
        "observations": cell.observations,
        "premium_percent_per_year": cell.annualised_premium_percent,
        "annualised_volatility_percent": cell.annualised_volatility_percent,
        "two_sided_90_interval": [
            cell.primary_bootstrap.lower_90,
            cell.primary_bootstrap.upper_90,
        ],
        "mde_one_sided_percent_per_year": cell.mde_one_sided_percent_per_year,
        "max_drawdown": cell.max_drawdown,
        "max_time_under_water_months": cell.max_time_under_water_months,
        "worst_rolling_120m": next(
            (item.worst_return for item in cell.rolling if item.window_months == 120), None
        ),
    }


def _correlations(
    series: Mapping[str, MonthlySeries], *, start: str, end: str
) -> JsonValue:
    """Pairwise correlations over the common period, and nowhere else.

    The frozen specification restricts every cross-factor statement to the one
    window in which all four factors are simultaneously post-publication. That is
    a restriction against reporting whichever correlation window is convenient,
    so it is enforced here rather than observed by habit.
    """
    windows = {name: window_series(series[name], start=start, end=end) for name in FACTORS}
    lengths = {name: window.observations for name, window in windows.items()}
    if len(set(lengths.values())) != 1:
        return {"error": f"unequal observation counts across factors: {lengths}"}
    matrix = np.vstack([windows[name].values for name in FACTORS])
    correlation = np.atleast_2d(np.asarray(np.corrcoef(matrix), dtype=np.float64))
    return {
        "window": f"{start}..{end}",
        "observations": next(iter(lengths.values())),
        "factors": list(FACTORS),
        "matrix": [[float(value) for value in row] for row in correlation],
        "note": (
            "Computed only over the common period, per the frozen specification. "
            "A correlation over a longer window would mix pre- and "
            "post-publication regimes for at least one factor."
        ),
    }


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


def _settings(specification: Specification) -> InferenceSettings:
    parameters = _mapping(specification.parameters, where="parameters")
    windows = _integers(
        _sequence(_at(parameters, "rolling_windows_months", where="parameters"), where="rolling"),
        where="rolling_windows_months",
    )
    second_moment = _mapping(
        _at(parameters, "second_moment_uncertainty", where="parameters"),
        where="second_moment_uncertainty",
    )
    bands_raw = _mapping(
        _at(second_moment, "relative_band_on_volatility", where="second_moment_uncertainty"),
        where="second_moment_uncertainty.relative_band_on_volatility",
    )
    bands = {
        name: _number(bands_raw, name, where="relative_band_on_volatility")
        for name in FACTORS
        if name in bands_raw
    }
    # UMD comes from a file that was never gated against a printed table.
    measured = {name: name != "UMD" for name in FACTORS}
    return InferenceSettings(
        frozen_block_length=12.0,
        neighbour_block_lengths=(6.0, 24.0),
        n_resamples=specification.inference.resamples,
        method=specification.inference.bootstrap,
        power_target=_number(parameters, "power_target", where="parameters"),
        materiality_annual_percent=_number(
            parameters, "materiality_threshold_annual_percent", where="parameters"
        ),
        true_factor_reference_annual_percent=6.6,
        rolling_windows_months=windows,
        second_moment_bands=bands,
        second_moment_measured=measured,
    )


def _estimates_for(cells: Sequence[CellStatistics]) -> tuple[Estimate, ...]:
    """One premium and one Sharpe estimate per cell, each carrying its uncertainty."""
    estimates: list[Estimate] = []
    for cell in cells:
        premium = cell.primary_bootstrap
        estimates.append(
            Estimate(
                name=f"{cell.factor} {cell.era_role} annualised premium",
                value=cell.annualised_premium_percent,
                units="percentage points per year",
                interval=(premium.lower_90, premium.upper_90),
                interval_method=(
                    f"stationary block bootstrap, two-sided 90%, mean block "
                    f"{premium.block_length:.0f}m, {premium.n_resamples} resamples"
                ),
                cost_basis=CostBasis.GROSS,
                n_obs=cell.observations,
                notes=(
                    f"gross and not investable; detectable at 80% power only above "
                    f"{cell.mde_one_sided_percent_per_year:.2f} pp/yr in this window"
                ),
            )
        )
        sharpe = cell.bootstrap_named("annualised_sharpe", "frozen")
        band = cell.second_moment_band
        band_note = ""
        if band is not None and band.measured:
            band_note = (
                f" SEPARATE systematic band from the Phase 1 gate, not sampling "
                f"error and not combined with the interval: "
                f"[{band.sharpe_low:.3f}, {band.sharpe_high:.3f}]."
            )
        elif band is not None:
            band_note = " Second moment unmeasured: this file was never gated."
        estimates.append(
            Estimate(
                name=f"{cell.factor} {cell.era_role} annualised Sharpe",
                value=cell.sharpe_annualised,
                units="ratio",
                interval=(sharpe.lower_90, sharpe.upper_90) if sharpe else None,
                interval_method=(
                    f"stationary block bootstrap, two-sided 90%, mean block "
                    f"{sharpe.block_length:.0f}m, {sharpe.n_resamples} resamples"
                    if sharpe
                    else ""
                ),
                cost_basis=CostBasis.GROSS,
                n_obs=cell.observations,
                uncertainty_unavailable_reason=(
                    "" if sharpe else "bootstrap not run for this cell"
                ),
                notes=(
                    "risk_free=0.0 passed explicitly; the series is already a "
                    "long-short spread." + band_note
                ),
            )
        )
    return tuple(estimates)


def _frames(
    cells: Sequence[CellStatistics], grid: GridInference
) -> dict[str, pd.DataFrame]:
    summary = pd.DataFrame([cell.to_json() for cell in cells])
    bootstraps = pd.DataFrame(
        [
            {"factor": cell.factor, "era_role": cell.era_role, **item.to_json()}
            for cell in cells
            for item in cell.bootstraps
        ]
    )
    inference = pd.DataFrame(
        [
            {
                "cell": key,
                "p_uncorrected": p,
                "bh_adjusted": bh,
                "bh_rejected": bh_ok,
                "holm_adjusted": holm,
                "holm_rejected": holm_ok,
            }
            for key, p, bh, bh_ok, holm, holm_ok in zip(
                grid.keys,
                grid.p_values,
                grid.bh_adjusted,
                grid.bh_rejected,
                grid.holm_adjusted,
                grid.holm_rejected,
                strict=True,
            )
        ]
    )
    return {"cells": summary, "bootstraps": bootstraps, "grid_inference": inference}


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 001."""
    parameters = _mapping(specification.parameters, where="parameters")
    settings = _settings(specification)
    rng = context.rng

    raw_factors, references, provenance = _load_sources(specification)
    sample_end = specification.sample_policy.end
    factors = {
        name: _clip_to_sample_policy(series, end=sample_end)
        for name, series in raw_factors.items()
    }
    references = {
        name: _clip_to_sample_policy(series, end=sample_end)
        for name, series in references.items()
    }

    grid = resolve_grid(specification)
    windows: dict[str, Window] = {}
    cells: list[CellStatistics] = []
    for item in grid:
        source = factors.get(item.factor)
        if source is None:
            raise FactorDecayError(f"no series loaded for factor {item.factor!r}")
        window = window_series(source, start=item.start, end=item.end)
        windows[f"{item.factor}/{item.era_name}"] = window
        cells.append(
            compute_cell(
                window,
                factor=item.factor,
                era_role=item.era_role,
                era_name=item.era_name,
                settings=settings,
                rng=rng,
            )
        )

    alternatives: list[CellStatistics] = []
    for factor, era in alternative_date_eras(specification):
        window = window_series(factors[factor], start=era.start, end=era.end)
        alternatives.append(
            compute_cell(
                window,
                factor=factor,
                era_role="alternative_publication_date",
                era_name=era.name,
                settings=settings,
                rng=rng,
            )
        )

    inference = correct_grid(cells, alpha=0.10)

    by_factor: dict[str, dict[str, CellStatistics]] = {}
    for cell in cells:
        by_factor.setdefault(cell.factor, {})[cell.era_role] = cell
    verdicts = tuple(
        apply_rejection_rule(
            factor, by_factor[factor], materiality=settings.materiality_annual_percent
        )
        for factor in FACTORS
    )

    costs = {factor: cost_illustration(factor, parameters) for factor in FACTORS}

    common = next(era for era in specification.sample_policy.eras if era.name == "common_period")
    correlations = _correlations(factors, start=common.start, end=common.end)

    market = references.get("Mkt-RF")
    market_reference: JsonValue = None
    if market is not None:
        market_window = window_series(market, start=common.start, end=common.end)
        market_reference = {
            "window": f"{common.start}..{common.end}",
            "observations": market_window.observations,
            "annualised_premium_percent": _annualised_premium_percent(market_window.values),
            "note": (
                "Descriptive only. The market factor is not a portfolio this "
                "experiment claims to hold, and a long-short spread has no "
                "investable benchmark."
            ),
        }

    band_effects = _band_sensitivity(cells)
    status = _overall_status(verdicts)
    summary = _summary_line(verdicts, inference, cells)

    diagnostics: dict[str, JsonValue] = {
        "sources": provenance,
        "sample_policy": {
            "start": specification.sample_policy.start,
            "end": sample_end,
            "held_out_after": sample_end,
            "months_available_beyond_holdout": {
                name: max(
                    0,
                    month_count(sample_end, series.last_observation or sample_end) - 1,
                )
                for name, series in raw_factors.items()
            },
        },
        "cells": [cell.to_json() for cell in cells],
        "alternative_publication_dates": [cell.to_json() for cell in alternatives],
        "grid_inference": inference.to_json(),
        "verdicts": [verdict.to_json() for verdict in verdicts],
        "cost_illustration": {
            factor: illustration.to_json() for factor, illustration in costs.items()
        },
        "correlations_common_period": correlations,
        "market_reference": market_reference,
        "second_moment_band_effects": band_effects,
        "hostile_tests": {
            "drop_best_month_and_year": _hostile_drop_best(cells, windows),
            "shift_era_boundaries_24_months": _hostile_shifted_boundaries(
                factors, cells, sample_end=sample_end
            ),
            "bootstrap_block_length_neighbours": {
                "description": (
                    "The frozen 12-month block, the predeclared 6- and 24-month "
                    "neighbours, and the corrected Politis-White automatic length "
                    "computed from each cell's own series. All four are in the "
                    "`bootstraps` frame for every cell."
                ),
                "rows": [
                    {
                        "cell": f"{cell.factor}/{cell.era_role}",
                        "intervals_by_block_length": [
                            {
                                "block_length": item.block_length,
                                "source": item.block_length_source,
                                "two_sided_90": [item.lower_90, item.upper_90],
                            }
                            for item in cell.bootstraps
                            if item.statistic == "annualised_premium_percent"
                        ],
                    }
                    for cell in cells
                ],
            },
            "synthetic_matched_noise": _hostile_synthetic_noise(
                by_factor["HML"]["full_post_publication"], settings=settings, rng=rng
            ),
            "equal_weighted_source_portfolios": {
                "run": False,
                "reason": (
                    "NOT RUN. The Ken French library distributes no equal-weighted "
                    "variant of the five-factor or momentum factor files, so this "
                    "hostile test cannot be performed from the pinned sources. Hou, "
                    "Xue and Zhang (2020) find the value-weighted / equal-weighted "
                    "choice moves anomaly replication rates from 35% to 58.6%, so "
                    "this is a material untested sensitivity, not an omission of "
                    "convenience. It requires the underlying sorted portfolios."
                ),
            },
        },
    }

    caveats = (
        "These are academic zero-investment long-short research portfolios, gross "
        "of transaction costs, shorting costs, borrow, fees and taxes. A retail "
        "investor cannot implement most of them at all. Every figure here is an "
        "UPPER BOUND of unknown tightness and no factor may be described as "
        "working on this evidence.",
        "The Phase 1 ingestion gate is UNRESOLVED, not passed. The HML and RMW "
        "standard deviations do not reproduce Fama and French (2015) Table 4, by "
        "3.03% and 5.09%, against two independently typeset vintages. Every Sharpe "
        "ratio, volatility and minimum detectable effect for those two factors "
        "carries a systematic band that is reported separately and is NOT in any "
        "bootstrap interval.",
        "UMD comes from the momentum file, which was never gated against a printed "
        "table. Its second moment is unmeasured rather than verified, which is a "
        "weaker statement than a band of zero.",
        "A before/after comparison across a publication date is DESCRIPTIVE. It "
        "confounds publication with changing composition, valuation regimes, "
        "crowding and chance, and this experiment does not claim to identify a "
        "publication effect.",
        "The currently distributed files apply the current CRSP vintage and the "
        "current construction to the whole history, including the pre-publication "
        "eras. The original-sample figures are therefore NOT the authors' original "
        "series, and a difference from their printed table is expected.",
        "The 20 cells of the multiple-testing family are strongly dependent: eras "
        "nest, RMW and CMA share every era, and all four factors are spreads over "
        "overlapping holdings of one universe. Benjamini-Hochberg treats them as "
        "independent, so the corrected p-values are a LOWER bound on the true "
        "correction.",
        "The cost column is an ILLUSTRATION of the implementation gap for a "
        "tradable strategy of comparable turnover. It is never subtracted from a "
        "premium, because the French series have no turnover and no tradable form. "
        "Novy-Marx and Velikov's haircut is 17% in the low-turnover tier and 144% "
        "in the high-turnover tier, where four of six strategies were net negative.",
        "The equal-weighted robustness test was not run: the library distributes "
        "no equal-weighted variant of these files. That sensitivity is untested.",
    )

    return ExperimentResult(
        status=status,
        summary=summary,
        estimates=_estimates_for(cells),
        diagnostics=diagnostics,
        caveats=caveats,
        frames=_frames(cells, inference),
    )


def _band_sensitivity(cells: Sequence[CellStatistics]) -> JsonValue:
    """Where the Phase 1 volatility band changes a reading, and where it cannot."""
    rows: list[JsonValue] = []
    for cell in cells:
        band = cell.second_moment_band
        if band is None or not band.measured:
            continue
        detectable = cell.annualised_premium_percent >= cell.mde_one_sided_percent_per_year
        detectable_low = cell.annualised_premium_percent >= band.mde_low
        detectable_high = cell.annualised_premium_percent >= band.mde_high
        rows.append(
            {
                "cell": f"{cell.factor}/{cell.era_role}",
                "sharpe": cell.sharpe_annualised,
                "sharpe_systematic_band": [band.sharpe_low, band.sharpe_high],
                "premium_exceeds_mde": detectable,
                "premium_exceeds_mde_across_band": detectable_low == detectable_high == detectable,
            }
        )
    return {
        "description": (
            "The falsifier and every premium in this experiment are functions of "
            "the MEAN, which the Phase 1 gate reproduced for all five factors. The "
            "band therefore CANNOT flip a rejection or a survival. It moves the "
            "Sharpe ratio, the volatility and the minimum detectable effect, which "
            "is where any conclusion that leans on those can flip."
        ),
        "rows": rows,
    }


def _overall_status(verdicts: Sequence[FactorVerdict]) -> ResultStatus:
    """The run's own status: the weakest thing any factor achieved.

    An exploratory run may never claim a confirmatory rung, and a run that
    rejected some factors while leaving others unresolved has not resolved
    anything, so the run reports ``unresolved`` unless every factor was decided.
    """
    statuses = {verdict.status for verdict in verdicts}
    if ResultStatus.UNRESOLVED in statuses:
        return ResultStatus.UNRESOLVED
    if statuses == {ResultStatus.REJECTED}:
        return ResultStatus.REJECTED
    return ResultStatus.EXPLORATORY


def _summary_line(
    verdicts: Sequence[FactorVerdict],
    inference: GridInference,
    cells: Sequence[CellStatistics],
) -> str:
    by_status: dict[str, list[str]] = {}
    for verdict in verdicts:
        by_status.setdefault(verdict.status.value, []).append(verdict.factor)
    parts = ", ".join(
        f"{status}: {', '.join(sorted(names))}" for status, names in sorted(by_status.items())
    )
    survivors = sum(1 for value in inference.bh_rejected if value)
    uncorrected = sum(1 for value in inference.p_values if value <= 0.05)
    underpowered = sum(
        1
        for cell in cells
        if cell.annualised_premium_percent < cell.mde_one_sided_percent_per_year
    )
    return (
        f"{parts}. Of the {len(inference.keys)} predeclared cells, {uncorrected} have a "
        f"one-sided HAC p-value at or below 0.05 uncorrected and {survivors} survive "
        f"Benjamini-Hochberg at 0.10; {underpowered} hold a premium smaller than what "
        "their own window could detect at 80% power. All figures are gross of every "
        "cost and are not investable."
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
    return _workspace_root() / "experiments" / "exp_001_factor_decay.yaml"


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    lines = [result.summary, ""]
    header = (
        f"{'factor':<6}{'era role':<24}{'n':>5}{'mean%/mo':>10}{'ann%':>9}"
        f"{'vol%':>8}{'SR':>7}{'90% low':>9}{'90% high':>10}{'MDE80':>8}{'p':>8}{'BH p':>8}"
    )
    lines.append(header)
    cells = result.diagnostics.get("cells")
    grid = result.diagnostics.get("grid_inference")
    adjusted: dict[str, float] = {}
    if isinstance(grid, Mapping):
        rows = grid.get("cells")
        if isinstance(rows, Sequence) and not isinstance(rows, str):
            for row in rows:
                if isinstance(row, Mapping):
                    adjusted[str(row.get("cell"))] = float(
                        str(row.get("benjamini_hochberg_adjusted_p"))
                    )
    if isinstance(cells, Sequence) and not isinstance(cells, str):
        for item in cells:
            if not isinstance(item, Mapping):
                continue
            boots = item.get("bootstraps")
            low = high = float("nan")
            if isinstance(boots, Sequence) and not isinstance(boots, str):
                for boot in boots:
                    if (
                        isinstance(boot, Mapping)
                        and boot.get("statistic") == "annualised_premium_percent"
                        and boot.get("block_length_source") == "frozen"
                    ):
                        interval = boot.get("two_sided_90")
                        if isinstance(interval, Sequence) and not isinstance(interval, str):
                            low, high = float(str(interval[0])), float(str(interval[1]))
            key = f"{item.get('factor')}/{item.get('era_role')}"
            lines.append(
                f"{item.get('factor')!s:<6}{item.get('era_role')!s:<24}"
                f"{int(str(item.get('observations'))):>5}"
                f"{float(str(item.get('mean_percent_per_month'))):>10.4f}"
                f"{float(str(item.get('annualised_premium_percent'))):>9.2f}"
                f"{float(str(item.get('annualised_volatility_percent'))):>8.2f}"
                f"{float(str(item.get('sharpe_annualised'))):>7.3f}"
                f"{low:>9.2f}{high:>10.2f}"
                f"{float(str(item.get('mde_one_sided_percent_per_year'))):>8.2f}"
                f"{float(str(item.get('one_sided_p_value_hac'))):>8.4f}"
                f"{adjusted.get(key, float('nan')):>8.4f}"
            )
    lines.append("")
    verdicts = result.diagnostics.get("verdicts")
    if isinstance(verdicts, Sequence) and not isinstance(verdicts, str):
        for verdict in verdicts:
            if isinstance(verdict, Mapping):
                lines.append(f"{verdict.get('factor')}: {verdict.get('status')}")
                lines.append(f"  {verdict.get('reasoning')}")
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
    """Run Experiment 001 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_001_factor_decay",
        description=(
            "Measure factor persistence and decay across the frozen eras of "
            "exp_001_factor_decay.yaml, writing a ledger entry for the attempt."
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
                "exp_001_factor_decay"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
