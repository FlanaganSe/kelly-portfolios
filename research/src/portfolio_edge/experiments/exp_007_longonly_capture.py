"""Experiment 007: the long-only capture fraction, and the small-value corner.

Every factor premium this repository has measured is an academic long-short
spread. A retail investor cannot hold one. What they can hold is a long-only
fund that overweights the high-scoring stocks, so what reaches them is the long
leg's excess over whatever they would otherwise have held. The ratio of the two
is the **capture fraction**, and it is the multiplier between everything
Experiments 001 and 005 measured and anything anyone can own. The edge
decomposition budgets the factor line by *assuming* it is 0.40, and the
framework page records four separate times that no source read there establishes
the number.

Why it is computable rather than a matter of opinion
----------------------------------------------------
Ken French publishes the long-only portfolios the factor is a difference of.
With ``SL, SM, SH, BL, BM, BH`` the six value-weighted size x book-to-market
portfolios::

    HML = 0.5 * (SH + BH) - 0.5 * (SL + BL)

exactly. So ``L = 0.5 * (SH + BH)`` is a portfolio, ``L - benchmark`` is a
long-only excess, and the capture fraction is ``mean(L - benchmark) / mean(HML)``
over the same months. Reproducing the published HML column from those six
portfolios is this module's integration test and clause (0) of the frozen
rejection rule: if it fails, nothing downstream means anything.

The benchmark is the whole argument
-----------------------------------
A three-bucket sort is symmetric, so ``L`` minus the equal-weighted average of
all six is arithmetically near ``HML / 2`` almost whatever the data do. Against
a *capitalisation*-weighted market the same ``L`` is a different object, because
weighting the small and big halves equally is a large size tilt relative to a
market that is overwhelmingly big. This module therefore computes the capture
fraction under five predeclared definitions and reports the spread, and the
frozen falsifier reads that spread first.

Run it::

    uv run python -m portfolio_edge.experiments.exp_007_longonly_capture --view-results
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
    MAX_RETAIL_MONTHLY_TURNOVER_PCT,
    TurnoverCostModel,
    apply_trade_costs,
    is_retail_implementable,
    one_sided_turnover,
    trades_from_weights,
)
from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.wealth import equity_curve
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.exp_001_factor_decay import (
    MonthlySeries,
    minimum_detectable_effect,
    one_sided_p_value,
    power_to_detect,
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
from portfolio_edge.inference.hac import hac_mean, hac_ols, newey_west_lag_count
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "FALSIFIER_ERAS",
    "PRIMARY_DEFINITIONS",
    "CaptureCell",
    "CaptureDefinition",
    "LongOnlyCaptureError",
    "ReconstructionCheck",
    "apply_rejection_rule",
    "build_registry",
    "capture_cell",
    "check_reconstruction",
    "default_specification_path",
    "definitional_spread",
    "joint_ratio_bootstrap",
    "main",
    "run",
]

ENTRY_POINT: Final = "exp_007_longonly_capture"

MONTHS_PER_YEAR: Final = 12.0

#: The two eras the frozen falsifier reads. Every other era is reported and
#: decides nothing, which is stated in the specification rather than here.
FALSIFIER_ERAS: Final = ("full_sample_since_1963", "hml_full_post_publication")

#: The predeclared family whose point-estimate spread clause (1) reads. Fixing
#: it in code AND in the specification means a definition cannot be added to
#: widen the spread or dropped to narrow it without changing the spec hash.
PRIMARY_DEFINITIONS: Final = (
    "value_halves_vs_size_neutral",
    "value_halves_vs_market",
    "big_value_vs_market",
    "big_value_vs_big_third",
    "small_value_vs_market",
)

#: The size-neutral definition. The one the specification names primary and the
#: only one clause (2) reads against the assumed 0.40.
SIZE_NEUTRAL: Final = "value_halves_vs_size_neutral"

# Column names, exactly as Ken French writes them.
S_LO, S_MID, S_HI = "SMALL LoBM", "ME1 BM2", "SMALL HiBM"
B_LO, B_MID, B_HI = "BIG LoBM", "ME2 BM2", "BIG HiBM"
_2X3_VALUE: Final = (S_LO, S_MID, S_HI, B_LO, B_MID, B_HI)

M_LO, M_MID, M_HI = "SMALL LoPRIOR", "ME1 PRIOR2", "SMALL HiPRIOR"
MB_LO, MB_MID, MB_HI = "BIG LoPRIOR", "ME2 PRIOR2", "BIG HiPRIOR"
_2X3_MOMENTUM: Final = (M_LO, M_MID, M_HI, MB_LO, MB_MID, MB_HI)

#: The 5x5 corner cells. ``SMALL HiBM`` is ME1 x BM5 and ``BIG HiBM`` is ME5 x BM5.
CELL_SMALL_VALUE: Final = "SMALL HiBM"
CELL_BIG_VALUE: Final = "BIG HiBM"
CELL_ME2_VALUE: Final = "ME2 BM5"

FloatArray = NDArray[np.float64]


class LongOnlyCaptureError(RuntimeError):
    """The experiment could not be attempted against the declared vintages."""


def _json_float(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``."""
    return None if math.isnan(value) or math.isinf(value) else value


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise LongOnlyCaptureError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise LongOnlyCaptureError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise LongOnlyCaptureError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise LongOnlyCaptureError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LongOnlyCaptureError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _numbers(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[float, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[float] = []
    for index, item in enumerate(items):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise LongOnlyCaptureError(f"{where}.{key}[{index}] must be a number, got {item!r}")
        out.append(float(item))
    return tuple(out)


def _optional_strings(data: Mapping[str, JsonValue], key: str) -> tuple[str, ...] | None:
    if key not in data:
        return None
    items = _sequence(data[key], where=key)
    return tuple(str(item) for item in items)


# --------------------------------------------------------------------------- #
# Loading the pinned sources
# --------------------------------------------------------------------------- #


def _series_from_table(table: ParsedTable, name: str, *, dataset_id: str) -> MonthlySeries:
    """Pull one column out, dropping missing months and recording that it happened."""
    if name not in table.columns:
        raise LongOnlyCaptureError(
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


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedTable:
    """One pinned, validated table and everything provenance needs from it."""

    source_id: str
    dataset_id: str
    table: ParsedTable
    provenance: Mapping[str, JsonValue]

    def series(self, column: str) -> MonthlySeries:
        return _series_from_table(self.table, column, dataset_id=self.dataset_id)


def _load_sources(specification: Specification) -> tuple[dict[str, LoadedTable], RawCache]:
    """Fetch, pin, parse and validate every file the specification names.

    A hash mismatch ABORTS. Ken French rebuilds the whole history from each new
    vintage, so an unrecognised hash is a new vintage, and a capture fraction
    computed from an unrecognised file looks exactly like a good one. The
    derived table is additionally checked against the ``sha256_normalized`` in
    the committed manifest, so a parser change is caught even when the raw
    bytes are unchanged.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="parameters.source_pin")
    entries = _sequence(_at(pin, "series", where="source_pin"), where="source_pin.series")

    cache = RawCache()
    loaded: dict[str, LoadedTable] = {}

    for index, item in enumerate(entries):
        where = f"source_pin.series[{index}]"
        spec_entry = _mapping(item, where=where)
        source_id = _text(spec_entry, "id", where=where)
        dataset = french.get_dataset(_text(spec_entry, "dataset_id", where=where))
        cached = french.download(cache, dataset)

        expected_raw = _text(spec_entry, "expected_sha256_raw", where=where)
        if cached.sha256 != expected_raw:
            raise LongOnlyCaptureError(
                f"the file at {dataset.url} now hashes to {cached.sha256}, but this "
                f"specification is frozen against {expected_raw}. Ken French rebuilds "
                "the whole history from each new vintage, so this is a new vintage, "
                "not a corrupted download. Freeze a new specification against it "
                "rather than reporting capture fractions from an unrecognised file."
            )

        parsed = french.parse(cache, cached, dataset=dataset)
        table = parsed.table(_text(spec_entry, "table_id", where=where))
        manifest_dataset_id = _text(spec_entry, "manifest_dataset_id", where=where)
        report = validate_table(
            table,
            dataset_id=manifest_dataset_id,
            expected_columns=_optional_strings(spec_entry, "expected_columns"),
            expected_frequency="monthly",
        )
        if not report.ok:
            raise LongOnlyCaptureError(
                f"{dataset.dataset_id}/{table.table_id} failed validation before any "
                "statistic was computed: " + "; ".join(report.summary())
            )

        first = _text(spec_entry, "expected_first_observation", where=where)
        if table.first_observation != first:
            raise LongOnlyCaptureError(
                f"{manifest_dataset_id} begins at {table.first_observation}, but the "
                f"specification pins {first}"
            )

        manifest_hash: str | None = None
        manifest_path = _workspace_root() / _text(spec_entry, "committed_manifest", where=where)
        if not manifest_path.is_file():
            raise LongOnlyCaptureError(
                f"{manifest_path} is missing. Every file this experiment reads must "
                "carry a committed manifest; an unmanifested byte is not evidence."
            )
        manifest = read_manifest(manifest_path)
        manifest_hash = manifest.sha256_manifest()
        if manifest.sha256_raw != expected_raw:
            raise LongOnlyCaptureError(
                f"{manifest_path} records sha256_raw {manifest.sha256_raw}, which is "
                f"not the pinned {expected_raw}"
            )
        if manifest.sha256_normalized != table.sha256_normalized():
            raise LongOnlyCaptureError(
                f"the derived table for {manifest_dataset_id} hashes to "
                f"{table.sha256_normalized()}, but the committed manifest records "
                f"{manifest.sha256_normalized}. The raw bytes matched, so the parser "
                "changed behaviour. That is a finding, not a hash to update."
            )

        loaded[source_id] = LoadedTable(
            source_id=source_id,
            dataset_id=dataset.dataset_id,
            table=table,
            provenance={
                "id": source_id,
                "dataset_id": dataset.dataset_id,
                "source_url": cached.url,
                "sha256_raw": cached.sha256,
                "sha256_normalized": table.sha256_normalized(),
                "size_bytes": cached.size_bytes,
                "retrieved_utc": cached.retrieved_utc,
                "source_last_modified": cached.last_modified,
                "parser_version": french.PARSER_VERSION,
                "committed_manifest": manifest_dataset_id,
                "committed_manifest_sha256": manifest_hash,
                "table_id": table.table_id,
                "table_banner": table.banner.strip(),
                "columns": list(table.columns),
                "rows_in_file": table.rows,
                "first_observation": table.first_observation,
                "last_observation": table.last_observation,
                "source_units": table.source_units,
                "units": table.units,
                "unit_transform": table.unit_transform,
                "preamble": parsed.preamble.strip(),
                "validation_findings": list(report.summary()),
            },
        )
    return loaded, cache


def _sibling_table(cache: RawCache, dataset_id: str, table_id: str) -> ParsedTable:
    """Another table out of an already-pinned file, read from the same cached bytes.

    The firm-count and average-market-cap tables live in the same zip as the
    25-portfolio returns, whose raw sha256 the specification already pins and
    :func:`_load_sources` has already verified. Reading a sibling table therefore
    reaches no network and adds no unpinned byte, and each one carries its own
    committed manifest.
    """
    dataset = french.get_dataset(dataset_id)
    entry = cache.require(dataset.url)
    return french.parse(cache, entry, dataset=dataset).table(table_id)


# --------------------------------------------------------------------------- #
# Aligned monthly panels
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class AlignedBlock:
    """Several monthly series on the months every one of them is observed.

    Nothing is forward-filled. ``dropped_months`` records what the intersection
    cost rather than repairing it.
    """

    name: str
    periods: tuple[str, ...]
    columns: Mapping[str, FloatArray]
    dropped_months: int

    @property
    def months(self) -> int:
        return len(self.periods)

    def __getitem__(self, key: str) -> FloatArray:
        if key not in self.columns:
            raise LongOnlyCaptureError(
                f"{self.name}: no series {key!r}; have {sorted(self.columns)}"
            )
        return self.columns[key]

    def window(self, *, start: str, end: str) -> AlignedBlock:
        """Slice to ``[start, end]`` inclusive, keeping every column aligned."""
        low, high = month_index(start), month_index(end)
        keep = [
            index
            for index, period in enumerate(self.periods)
            if low <= month_index(period) <= high
        ]
        selector = np.asarray(keep, dtype=np.intp)
        return AlignedBlock(
            name=f"{self.name}[{start}..{end}]",
            periods=tuple(self.periods[index] for index in keep),
            columns={key: values[selector] for key, values in self.columns.items()},
            dropped_months=0,
        )


def align_series(name: str, series: Mapping[str, MonthlySeries]) -> AlignedBlock:
    """Intersect several monthly series on their period labels."""
    if not series:
        raise LongOnlyCaptureError(f"{name}: nothing to align")
    by_key = {
        key: dict(zip(item.periods, item.values, strict=True)) for key, item in series.items()
    }
    common = sorted(set.intersection(*(set(item) for item in by_key.values())))
    union = set().union(*(set(item) for item in by_key.values()))
    if len(common) < 2:
        raise LongOnlyCaptureError(f"{name}: only {len(common)} months are common to all series")
    return AlignedBlock(
        name=name,
        periods=tuple(common),
        columns={
            key: np.asarray([values[period] for period in common], dtype=np.float64)
            for key, values in by_key.items()
        },
        dropped_months=len(union) - len(common),
    )


# --------------------------------------------------------------------------- #
# The integration test
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class ReconstructionCheck:
    """Whether a published factor rebuilds from the published portfolios.

    Clause (0) of the frozen rejection rule. ``tolerance`` is the printed
    precision of the source files, declared in the specification before the run
    and never widened afterwards.
    """

    identity: str
    formula: str
    checked_against: str
    months: int
    max_absolute: float
    mean_residual: float
    root_mean_square: float
    tolerance: float
    passed: bool
    expected_to_pass: bool
    note: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "identity": self.identity,
            "formula": self.formula,
            "checked_against": self.checked_against,
            "months": self.months,
            "max_absolute_residual_decimal_per_month": self.max_absolute,
            "max_absolute_residual_percentage_points_per_month": self.max_absolute * 100.0,
            "mean_residual_decimal_per_month": self.mean_residual,
            "root_mean_square_residual_decimal_per_month": self.root_mean_square,
            "tolerance_decimal_per_month": self.tolerance,
            "passed": self.passed,
            "expected_to_pass": self.expected_to_pass,
            "note": self.note,
        }


def check_reconstruction(
    reconstructed: FloatArray,
    published: FloatArray,
    *,
    identity: str,
    formula: str,
    checked_against: str,
    tolerance: float,
    expected_to_pass: bool = True,
    note: str = "",
) -> ReconstructionCheck:
    """Compare a rebuilt factor against its published column, term by term."""
    if reconstructed.size != published.size:
        raise LongOnlyCaptureError(
            f"{identity}: {reconstructed.size} reconstructed months against "
            f"{published.size} published months"
        )
    residual = reconstructed - published
    max_abs = float(np.max(np.abs(residual))) if residual.size else float("nan")
    return ReconstructionCheck(
        identity=identity,
        formula=formula,
        checked_against=checked_against,
        months=int(residual.size),
        max_absolute=max_abs,
        mean_residual=float(np.mean(residual)),
        root_mean_square=float(np.sqrt(np.mean(residual**2))),
        tolerance=tolerance,
        passed=bool(max_abs <= tolerance),
        expected_to_pass=expected_to_pass,
        note=note,
    )


# --------------------------------------------------------------------------- #
# The capture fraction
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RatioInterval:
    """A joint block-bootstrap interval for a ratio of two means.

    ``near_zero_denominator_resamples`` is not a diagnostic to be skimmed. A
    ratio whose denominator can approach zero has no finite variance and its
    bootstrap distribution can be bimodal, so an interval computed from such a
    replicate set is marked ``unstable`` and the specification forbids quoting
    it without that mark.
    """

    point_estimate: float
    lower_90: float
    upper_90: float
    lower_95: float
    upper_95: float
    median: float
    standard_error: float
    block_length: float
    block_length_source: str
    n_resamples: int
    near_zero_denominator_resamples: int
    sign_flipped_denominator_resamples: int
    unstable: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "point_estimate": _json_float(self.point_estimate),
            "two_sided_90": [_json_float(self.lower_90), _json_float(self.upper_90)],
            "two_sided_95": [_json_float(self.lower_95), _json_float(self.upper_95)],
            "bootstrap_median": _json_float(self.median),
            "bootstrap_standard_error": _json_float(self.standard_error),
            "block_length": self.block_length,
            "block_length_source": self.block_length_source,
            "n_resamples": self.n_resamples,
            "near_zero_denominator_resamples": self.near_zero_denominator_resamples,
            "sign_flipped_denominator_resamples": self.sign_flipped_denominator_resamples,
            "unstable": self.unstable,
        }


#: Fraction of resamples with a degenerate denominator above which an interval
#: is marked UNSTABLE. Frozen in the specification as 1%.
_INSTABILITY_FRACTION: Final = 0.01

#: A resampled denominator mean below this multiple of the full-sample value is
#: counted as near zero.
_NEAR_ZERO_MULTIPLE: Final = 0.1


def joint_ratio_bootstrap(
    numerator: FloatArray,
    denominator: FloatArray,
    *,
    block_length: float,
    block_length_source: str,
    n_resamples: int,
    rng: np.random.Generator,
) -> RatioInterval:
    """Block-bootstrap ``mean(numerator) / mean(denominator)``, drawn jointly.

    One set of time indices is drawn and applied to BOTH series, so the
    near-perfect contemporaneous dependence between a long leg and the spread it
    is half of survives the resample. Drawing separately would treat the ratio
    as a ratio of independent estimates; unlike Experiment 005's cross-region
    case there is no reading under which that is even approximately right, so
    the invalid variant is not computed at all.
    """
    if numerator.size != denominator.size:
        raise LongOnlyCaptureError(
            f"ratio bootstrap needs equal lengths, got {numerator.size} and {denominator.size}"
        )
    months = numerator.size
    indices = stationary_bootstrap_indices(months, block_length, n_resamples, rng)
    numerator_means = numerator[indices].mean(axis=1)
    denominator_means = denominator[indices].mean(axis=1)

    full_denominator = float(np.mean(denominator))
    threshold = _NEAR_ZERO_MULTIPLE * abs(full_denominator)
    near_zero = int(np.count_nonzero(np.abs(denominator_means) < threshold))
    flipped = (
        int(np.count_nonzero(np.sign(denominator_means) != math.copysign(1.0, full_denominator)))
        if full_denominator != 0.0
        else n_resamples
    )

    with np.errstate(divide="ignore", invalid="ignore"):
        replicates = np.asarray(numerator_means / denominator_means, dtype=np.float64)
    finite = replicates[np.isfinite(replicates)]
    if finite.size < 2:
        raise LongOnlyCaptureError("the ratio bootstrap produced no finite replicates")

    quantiles = np.quantile(finite, [0.05, 0.95, 0.025, 0.975, 0.5])
    point = (
        float(np.mean(numerator)) / full_denominator if full_denominator != 0.0 else float("nan")
    )
    return RatioInterval(
        point_estimate=point,
        lower_90=float(quantiles[0]),
        upper_90=float(quantiles[1]),
        lower_95=float(quantiles[2]),
        upper_95=float(quantiles[3]),
        median=float(quantiles[4]),
        standard_error=float(np.std(finite, ddof=1)),
        block_length=block_length,
        block_length_source=block_length_source,
        n_resamples=n_resamples,
        near_zero_denominator_resamples=near_zero,
        sign_flipped_denominator_resamples=flipped,
        unstable=bool(max(near_zero, flipped) > _INSTABILITY_FRACTION * n_resamples),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SpreadInterval:
    """A block-bootstrap interval for an annualised mean, in pp/yr."""

    point_estimate: float
    lower_90: float
    upper_90: float
    standard_error: float
    block_length: float
    n_resamples: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "point_estimate": _json_float(self.point_estimate),
            "two_sided_90": [_json_float(self.lower_90), _json_float(self.upper_90)],
            "bootstrap_standard_error": _json_float(self.standard_error),
            "block_length": self.block_length,
            "n_resamples": self.n_resamples,
        }


def _spread_bootstrap(
    series: FloatArray,
    *,
    block_length: float,
    n_resamples: int,
    rng: np.random.Generator,
) -> SpreadInterval:
    indices = stationary_bootstrap_indices(series.size, block_length, n_resamples, rng)
    replicates = series[indices].mean(axis=1) * MONTHS_PER_YEAR * 100.0
    low, high = (float(value) for value in np.quantile(replicates, [0.05, 0.95]))
    return SpreadInterval(
        point_estimate=float(np.mean(series)) * MONTHS_PER_YEAR * 100.0,
        lower_90=low,
        upper_90=high,
        standard_error=float(np.std(replicates, ddof=1)),
        block_length=block_length,
        n_resamples=n_resamples,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CaptureDefinition:
    """One long-only tilt, its benchmark, and the spread it is a fraction of."""

    identifier: str
    long_only: str
    benchmark: str
    denominator: str
    reading: str
    in_primary_family: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "id": self.identifier,
            "long_only": self.long_only,
            "benchmark": self.benchmark,
            "denominator": self.denominator,
            "reading": self.reading,
            "in_primary_family": self.in_primary_family,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CaptureCell:
    """Everything reported for one definition over one era."""

    definition: CaptureDefinition
    era_name: str
    start: str
    end: str
    months: int
    first_observation: str
    last_observation: str

    capture_fraction: float
    capture_interval: RatioInterval
    neighbour_intervals: tuple[RatioInterval, ...]

    long_only_annual_percent: float
    benchmark_annual_percent: float
    denominator_annual_percent: float
    spread_annual_percent: float
    spread_interval: SpreadInterval

    spread_volatility_annual_percent: float
    hac_standard_error_annual: float
    hac_t_statistic: float
    hac_lag_count: int
    one_sided_p_value_hac: float
    mde_one_sided_percent_per_year: float
    mde_one_sided_hac_percent_per_year: float
    power_at_materiality: float

    @property
    def key(self) -> str:
        return f"{self.definition.identifier}/{self.era_name}"

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "definition": self.definition.identifier,
            "in_primary_family": self.definition.in_primary_family,
            "long_only": self.definition.long_only,
            "benchmark": self.definition.benchmark,
            "denominator": self.definition.denominator,
            "era": self.era_name,
            "start": self.start,
            "end": self.end,
            "months": self.months,
            "first_observation": self.first_observation,
            "last_observation": self.last_observation,
            "capture_fraction": _json_float(self.capture_fraction),
            "capture_interval": self.capture_interval.to_json(),
            "capture_interval_block_length_neighbours": [
                item.to_json() for item in self.neighbour_intervals
            ],
            "long_only_annualised_percent": self.long_only_annual_percent,
            "benchmark_annualised_percent": self.benchmark_annual_percent,
            "denominator_annualised_percent": self.denominator_annual_percent,
            "long_only_excess_spread_percent_per_year": self.spread_annual_percent,
            "long_only_excess_spread_interval": self.spread_interval.to_json(),
            "spread_annualised_volatility_percent": self.spread_volatility_annual_percent,
            "hac_standard_error_annual": self.hac_standard_error_annual,
            "hac_t_statistic": _json_float(self.hac_t_statistic),
            "hac_lag_count": self.hac_lag_count,
            "one_sided_p_value_hac": _json_float(self.one_sided_p_value_hac),
            "mde_one_sided_percent_per_year": self.mde_one_sided_percent_per_year,
            "mde_one_sided_hac_percent_per_year": self.mde_one_sided_hac_percent_per_year,
            "power_at_materiality": self.power_at_materiality,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class InferenceSettings:
    """The frozen inference settings, read once from the specification."""

    frozen_block_length: float
    neighbour_block_lengths: tuple[float, ...]
    n_resamples: int
    power_target: float
    materiality_annual_percent: float
    assumed_capture: float
    spread_threshold: float


def capture_cell(
    long_only: FloatArray,
    benchmark: FloatArray,
    denominator: FloatArray,
    periods: Sequence[str],
    *,
    definition: CaptureDefinition,
    era_name: str,
    start: str,
    end: str,
    settings: InferenceSettings,
    rng: np.random.Generator,
    with_neighbours: bool = True,
) -> CaptureCell:
    """Every statistic this experiment reports for one definition and era."""
    months = long_only.size
    if months < 24:
        raise LongOnlyCaptureError(
            f"{definition.identifier}/{era_name} holds {months} months; this "
            "experiment refuses to summarise a window shorter than two years"
        )
    excess = long_only - benchmark
    percent = excess * 100.0

    mean_month = float(np.mean(percent))
    sigma_month = float(np.std(percent, ddof=1))
    conventional_se = sigma_month / math.sqrt(months)
    hac = hac_mean(percent, n_lags=newey_west_lag_count(months))

    interval = joint_ratio_bootstrap(
        excess,
        denominator,
        block_length=settings.frozen_block_length,
        block_length_source="frozen",
        n_resamples=settings.n_resamples,
        rng=rng,
    )
    neighbours: list[RatioInterval] = []
    if with_neighbours:
        automatic = optimal_block_length(excess)
        candidates: list[tuple[float, str]] = [
            (length, "predeclared-neighbour") for length in settings.neighbour_block_lengths
        ]
        candidates.append((automatic.stationary, "politis-white-automatic"))
        neighbours = [
            joint_ratio_bootstrap(
                excess,
                denominator,
                block_length=length,
                block_length_source=source,
                n_resamples=settings.n_resamples,
                rng=rng,
            )
            for length, source in candidates
        ]

    denominator_annual = float(np.mean(denominator)) * MONTHS_PER_YEAR * 100.0
    return CaptureCell(
        definition=definition,
        era_name=era_name,
        start=start,
        end=end,
        months=months,
        first_observation=periods[0],
        last_observation=periods[-1],
        capture_fraction=interval.point_estimate,
        capture_interval=interval,
        neighbour_intervals=tuple(neighbours),
        long_only_annual_percent=float(np.mean(long_only)) * MONTHS_PER_YEAR * 100.0,
        benchmark_annual_percent=float(np.mean(benchmark)) * MONTHS_PER_YEAR * 100.0,
        denominator_annual_percent=denominator_annual,
        spread_annual_percent=MONTHS_PER_YEAR * mean_month,
        spread_interval=_spread_bootstrap(
            excess,
            block_length=settings.frozen_block_length,
            n_resamples=settings.n_resamples,
            rng=rng,
        ),
        spread_volatility_annual_percent=math.sqrt(MONTHS_PER_YEAR) * sigma_month,
        hac_standard_error_annual=MONTHS_PER_YEAR * hac.standard_error,
        hac_t_statistic=hac.t_statistic,
        hac_lag_count=hac.n_lags,
        one_sided_p_value_hac=one_sided_p_value(hac.t_statistic),
        mde_one_sided_percent_per_year=MONTHS_PER_YEAR
        * minimum_detectable_effect(
            standard_error=conventional_se, power=settings.power_target, one_sided=True
        ),
        mde_one_sided_hac_percent_per_year=MONTHS_PER_YEAR
        * minimum_detectable_effect(
            standard_error=hac.standard_error, power=settings.power_target, one_sided=True
        ),
        power_at_materiality=power_to_detect(
            settings.materiality_annual_percent / MONTHS_PER_YEAR,
            standard_error=conventional_se,
            one_sided=True,
        ),
    )


def definitional_spread(cells: Sequence[CaptureCell]) -> tuple[float, str, str]:
    """The spread of point estimates across the predeclared primary family.

    Returns ``(spread, widest_definition, narrowest_definition)``. Clause (1) of
    the frozen falsifier reads the first element.
    """
    primary = [cell for cell in cells if cell.definition.in_primary_family]
    if not primary:
        raise LongOnlyCaptureError("no primary-family cells to spread")
    values = [(cell.capture_fraction, cell.definition.identifier) for cell in primary]
    finite = [item for item in values if math.isfinite(item[0])]
    if not finite:
        return (float("nan"), "", "")
    high = max(finite)
    low = min(finite)
    return (high[0] - low[0], high[1], low[1])


# --------------------------------------------------------------------------- #
# Risk of a long-only portfolio
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioRisk:
    """What a long-only portfolio actually did to a wealth path.

    Drawdown and time under water are properties of the *portfolio*, not of the
    excess return, which is why they are computed here from the total return and
    not from the spread. A long-short spread has no wealth path at all; a
    long-only portfolio does, which is the one respect in which this experiment
    can say more than Experiments 001 and 005.
    """

    name: str
    months: int
    geometric_annual_percent: float
    arithmetic_annual_percent: float
    volatility_annual_percent: float
    max_drawdown_percent: float
    max_time_under_water_months: int
    drawdown_peak_period: str
    drawdown_trough_period: str
    open_at_end: bool
    worst_rolling_12m_percent: float
    worst_rolling_120m_percent: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "portfolio": self.name,
            "months": self.months,
            "geometric_annual_percent": self.geometric_annual_percent,
            "arithmetic_annual_percent": self.arithmetic_annual_percent,
            "volatility_annual_percent": self.volatility_annual_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "max_time_under_water_months": self.max_time_under_water_months,
            "drawdown_peak_period": self.drawdown_peak_period,
            "drawdown_trough_period": self.drawdown_trough_period,
            "drawdown_open_at_end": self.open_at_end,
            "worst_rolling_12m_percent": _json_float(self.worst_rolling_12m_percent),
            "worst_rolling_120m_percent": _json_float(self.worst_rolling_120m_percent),
        }


def _worst_rolling(returns: FloatArray, window: int) -> float:
    if returns.size < window:
        return float("nan")
    growth = np.cumprod(1.0 + returns)
    padded = np.concatenate(([1.0], growth))
    ratios = padded[window:] / padded[:-window]
    return float(np.min(ratios) - 1.0) * 100.0


def portfolio_risk(returns: FloatArray, periods: Sequence[str], *, name: str) -> PortfolioRisk:
    """Geometric return, volatility, drawdown and time under water, in one pass."""
    curve = equity_curve(returns)
    summary = drawdown_summary(curve)
    months = returns.size
    terminal = float(curve[-1])

    def label(curve_index: int) -> str:
        """Map an index into the wealth path back to a period label.

        ``equity_curve`` prepends the initial wealth, so element ``t + 1`` is the
        wealth after return ``t``. Element 0 predates every observation and is
        labelled with the first period rather than with nothing.
        """
        return periods[min(max(curve_index - 1, 0), len(periods) - 1)]

    return PortfolioRisk(
        name=name,
        months=months,
        geometric_annual_percent=(terminal ** (MONTHS_PER_YEAR / months) - 1.0) * 100.0,
        arithmetic_annual_percent=float(np.mean(returns)) * MONTHS_PER_YEAR * 100.0,
        volatility_annual_percent=float(np.std(returns, ddof=1))
        * math.sqrt(MONTHS_PER_YEAR)
        * 100.0,
        max_drawdown_percent=summary.max_drawdown * 100.0,
        max_time_under_water_months=summary.max_time_under_water,
        drawdown_peak_period=label(summary.peak_index),
        drawdown_trough_period=label(summary.trough_index),
        open_at_end=summary.open_at_end,
        worst_rolling_12m_percent=_worst_rolling(returns, 12),
        worst_rolling_120m_percent=_worst_rolling(returns, 120),
    )


# --------------------------------------------------------------------------- #
# Costs, as a separate column
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class RebalanceCost:
    """The one turnover in this experiment that is measured, not assumed.

    Two halves held at 50/50 drift apart between rebalances, and restoring the
    weights is a trade. The trade is priced by ``core.costs`` and charged
    against the wealth path at the moment it happens, so it alters the
    compounded result rather than being deducted from a mean afterwards.
    """

    frequency: str
    k: float
    rebalances: int
    mean_one_sided_turnover_percent_per_rebalance: float
    total_one_sided_turnover_percent_per_year: float
    gross_geometric_annual_percent: float
    net_geometric_annual_percent: float
    cost_percent_per_year: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "rebalance_frequency": self.frequency,
            "turnover_coefficient_k": self.k,
            "rebalances": self.rebalances,
            "mean_one_sided_turnover_percent_per_rebalance": (
                self.mean_one_sided_turnover_percent_per_rebalance
            ),
            "one_sided_turnover_percent_per_year": (
                self.total_one_sided_turnover_percent_per_year
            ),
            "gross_geometric_annual_percent": self.gross_geometric_annual_percent,
            "net_geometric_annual_percent": self.net_geometric_annual_percent,
            "measured_rebalance_cost_percent_per_year": self.cost_percent_per_year,
        }


def rebalance_cost(
    first: FloatArray,
    second: FloatArray,
    *,
    frequency: str,
    k: float,
) -> RebalanceCost:
    """Run the 50/50 wealth path with rebalancing costs charged at each trade."""
    if first.size != second.size:
        raise LongOnlyCaptureError("the two halves must have the same length")
    step = 1 if frequency == "monthly" else 12
    model = TurnoverCostModel(k=k)
    target = np.asarray([0.5, 0.5], dtype=np.float64)

    def path(charge: bool) -> tuple[float, int, float]:
        wealth = 1.0
        weights = target.copy()
        rebalances = 0
        turnover_total = 0.0
        for index in range(first.size):
            growth = np.asarray([1.0 + first[index], 1.0 + second[index]], dtype=np.float64)
            values = weights * growth
            wealth *= float(np.sum(values))
            weights = values / float(np.sum(values))
            if (index + 1) % step == 0 and index + 1 < first.size:
                turnover_total += one_sided_turnover(weights, target)
                rebalances += 1
                if charge:
                    trades = trades_from_weights(weights, target, wealth)
                    wealth = apply_trade_costs(wealth, trades, model)
                weights = target.copy()
        return wealth, rebalances, turnover_total

    gross_wealth, rebalances, turnover_total = path(charge=False)
    net_wealth, _, _ = path(charge=True)
    years = first.size / MONTHS_PER_YEAR
    gross_annual = (gross_wealth ** (1.0 / years) - 1.0) * 100.0
    net_annual = (net_wealth ** (1.0 / years) - 1.0) * 100.0
    return RebalanceCost(
        frequency=frequency,
        k=k,
        rebalances=rebalances,
        mean_one_sided_turnover_percent_per_rebalance=(
            100.0 * turnover_total / rebalances if rebalances else 0.0
        ),
        total_one_sided_turnover_percent_per_year=100.0 * turnover_total / years,
        gross_geometric_annual_percent=gross_annual,
        net_geometric_annual_percent=net_annual,
        cost_percent_per_year=gross_annual - net_annual,
    )


def _assumed_cost_rows(
    *,
    label: str,
    turnovers: Sequence[float],
    expense_ratios: Sequence[float],
    coefficients: Sequence[float],
) -> list[JsonValue]:
    """Price the ASSUMED components. Every row says that it is an assumption."""
    rows: list[JsonValue] = []
    for turnover in turnovers:
        for k in coefficients:
            model = TurnoverCostModel(k=k)
            trading = model.cost_bp_per_period(turnover) / 100.0
            monthly = turnover / MONTHS_PER_YEAR
            for expense in expense_ratios:
                rows.append(
                    {
                        "sort": label,
                        "assumed_one_sided_turnover_percent_per_year": turnover,
                        "implied_one_sided_turnover_percent_per_month": monthly,
                        "turnover_coefficient_k": k,
                        "assumed_expense_ratio_percent_per_year": expense,
                        "trading_cost_percent_per_year": trading,
                        "total_assumed_cost_percent_per_year": trading + expense,
                        "retail_implementable_at_this_turnover": is_retail_implementable(monthly),
                        "retail_monthly_turnover_limit_percent": (
                            MAX_RETAIL_MONTHLY_TURNOVER_PCT
                        ),
                        "measured_or_assumed": "assumed",
                    }
                )
    return rows


# --------------------------------------------------------------------------- #
# The frozen decision
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Verdict:
    """The frozen rejection rule applied, clause by clause."""

    status: ResultStatus
    clause_zero_passed: bool
    clause_one_rejected: bool
    clause_two: str
    spread_by_era: Mapping[str, float]
    size_neutral_by_era: Mapping[str, JsonValue]
    clauses_passed: tuple[str, ...]
    clauses_failed: tuple[str, ...]
    reasoning: str
    what_would_fire: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "status": self.status.value,
            "clause_0_reconstruction_passed": self.clause_zero_passed,
            "clause_1_definitional_spread_rejects_well_definedness": self.clause_one_rejected,
            "clause_2_level_against_the_assumed_capture": self.clause_two,
            "definitional_spread_by_era": dict(self.spread_by_era),
            "size_neutral_capture_by_era": dict(self.size_neutral_by_era),
            "clauses_passed": list(self.clauses_passed),
            "clauses_failed": list(self.clauses_failed),
            "reasoning": self.reasoning,
            "what_would_fire": self.what_would_fire,
        }


def apply_rejection_rule(
    checks: Sequence[ReconstructionCheck],
    cells_by_era: Mapping[str, Sequence[CaptureCell]],
    *,
    settings: InferenceSettings,
) -> Verdict:
    """Exactly the rejection rule frozen in the specification, in its fixed order."""
    passed: list[str] = []
    failed: list[str] = []

    def record(ok: bool, message: str) -> bool:
        (passed if ok else failed).append(message)
        return ok

    required = [check for check in checks if check.expected_to_pass]
    clause_zero = all(check.passed for check in required)
    record(
        clause_zero,
        "(0) every reconstruction identity expected to hold reproduced its published "
        "column inside the source file's own printed precision: "
        + "; ".join(
            f"{check.identity} max |residual| {check.max_absolute * 100:.4f} pp/month "
            f"against {check.tolerance * 100:.4f}"
            for check in required
        ),
    )
    if not clause_zero:
        return Verdict(
            status=ResultStatus.UNRESOLVED,
            clause_zero_passed=False,
            clause_one_rejected=False,
            clause_two="not reached",
            spread_by_era={},
            size_neutral_by_era={},
            clauses_passed=tuple(passed),
            clauses_failed=tuple(failed),
            reasoning=(
                "the published factor could not be rebuilt from the published "
                "portfolios inside the source file's printed precision, so the long "
                "legs read here are not the legs of the factor measured elsewhere in "
                "this repository and no capture fraction may be reported at all"
            ),
            what_would_fire="a reconstruction that reproduces the published column",
        )

    spreads: dict[str, float] = {}
    for era in FALSIFIER_ERAS:
        spread, widest, narrowest = definitional_spread(cells_by_era[era])
        spreads[era] = spread
        record(
            spread <= settings.spread_threshold,
            f"(1) definitional spread over {era} is {spread:.3f} across the five "
            f"predeclared definitions ({widest} highest, {narrowest} lowest), against "
            f"the {settings.spread_threshold:.2f} threshold",
        )
    clause_one_rejected = any(
        value > settings.spread_threshold for value in spreads.values() if math.isfinite(value)
    )

    size_neutral: dict[str, JsonValue] = {}
    below: list[bool] = []
    above: list[bool] = []
    for era in FALSIFIER_ERAS:
        cell = next(
            item for item in cells_by_era[era] if item.definition.identifier == SIZE_NEUTRAL
        )
        interval = cell.capture_interval
        size_neutral[era] = {
            "capture_fraction": _json_float(cell.capture_fraction),
            "two_sided_90": [_json_float(interval.lower_90), _json_float(interval.upper_90)],
            "unstable": interval.unstable,
        }
        below.append(interval.upper_90 < settings.assumed_capture)
        above.append(interval.lower_90 > settings.assumed_capture)
        record(
            interval.lower_90 <= settings.assumed_capture <= interval.upper_90,
            f"(2) the size-neutral 90% interval over {era} is "
            f"[{interval.lower_90:.3f}, {interval.upper_90:.3f}] against the assumed "
            f"{settings.assumed_capture:.2f}",
        )

    if all(below):
        clause_two = "rejected: entirely below the assumed capture in both falsifier eras"
    elif all(above):
        clause_two = "supported: entirely above the assumed capture in both falsifier eras"
    else:
        clause_two = "straddles the assumed capture in at least one falsifier era"

    if clause_one_rejected or clause_two.startswith("rejected"):
        status = ResultStatus.REJECTED
    elif clause_two.startswith("supported"):
        status = ResultStatus.EXPLORATORY
    else:
        status = ResultStatus.UNRESOLVED

    reasons: list[str] = []
    if clause_one_rejected:
        worst = max(spreads.values())
        reasons.append(
            f"clause (1) fired: the five predeclared definitions spread {worst:.3f} "
            f"apart at the point estimate, above the {settings.spread_threshold:.2f} "
            "threshold. There is no benchmark-free long-only capture fraction, so no "
            "single number may be used as a multiplier, and every figure must be "
            "quoted with the benchmark that produced it"
        )
    else:
        reasons.append(
            f"clause (1) held: the five definitions agree to within "
            f"{max(spreads.values()):.3f}"
        )
    reasons.append(f"clause (2) {clause_two}")

    return Verdict(
        status=status,
        clause_zero_passed=True,
        clause_one_rejected=clause_one_rejected,
        clause_two=clause_two,
        spread_by_era=spreads,
        size_neutral_by_era=size_neutral,
        clauses_passed=tuple(passed),
        clauses_failed=tuple(failed),
        reasoning=". ".join(reasons)
        + ". The measurements themselves stand: what a rejection under clause (1) "
        "rejects is the use of one scalar as a multiplier, not the numbers behind it.",
        what_would_fire=(
            ""
            if status is ResultStatus.EXPLORATORY
            else (
                "clause (1) would hold if the five definitions agreed to within "
                f"{settings.spread_threshold:.2f}; clause (2) would be supported if the "
                "size-neutral interval sat entirely above "
                f"{settings.assumed_capture:.2f} in both falsifier eras"
            )
        ),
    )


# --------------------------------------------------------------------------- #
# Building the panels
# --------------------------------------------------------------------------- #


def _us_value_block(loaded: Mapping[str, LoadedTable]) -> AlignedBlock:
    """The six US 2x3 portfolios, the three- and five-factor columns, aligned."""
    portfolios = loaded["us_6_portfolios_2x3"]
    ff3 = loaded["us_ff3"]
    series: dict[str, MonthlySeries] = {
        column: portfolios.series(column) for column in _2X3_VALUE
    }
    for column in ("Mkt-RF", "SMB", "HML", "RF"):
        series[f"ff3_{column}"] = ff3.series(column)
    return align_series("us_value", series)


def _derive_value_columns(block: AlignedBlock) -> dict[str, FloatArray]:
    """The long-only tilts, benchmarks and reconstructed spreads of a 2x3 block."""
    small_low, small_mid, small_high = block[S_LO], block[S_MID], block[S_HI]
    big_low, big_mid, big_high = block[B_LO], block[B_MID], block[B_HI]
    value_halves = 0.5 * (small_high + big_high)
    growth_halves = 0.5 * (small_low + big_low)
    six = np.stack(
        [small_low, small_mid, small_high, big_low, big_mid, big_high], axis=1
    )
    return {
        "value_halves": value_halves,
        "growth_halves": growth_halves,
        "middle_halves": 0.5 * (small_mid + big_mid),
        "size_neutral_six": six.mean(axis=1),
        "big_third": (big_low + big_mid + big_high) / 3.0,
        "small_third": (small_low + small_mid + small_high) / 3.0,
        "hml_reconstructed": value_halves - growth_halves,
        "smb_reconstructed": (
            (small_low + small_mid + small_high) / 3.0 - (big_low + big_mid + big_high) / 3.0
        ),
    }


def _definitions() -> tuple[CaptureDefinition, ...]:
    """The predeclared definitions, matching the frozen specification exactly."""
    return (
        CaptureDefinition(
            identifier="value_halves_vs_size_neutral",
            long_only="0.5 * (SH + BH)",
            benchmark="(SL + SM + SH + BL + BM + BH) / 6",
            denominator="HML",
            reading=(
                "THE PRIMARY. The value tilt held at the same 50/50 size weighting as "
                "its own benchmark, so the difference is book-to-market and nothing "
                "else. Near one half for structural reasons: the long leg is one half "
                "of a symmetric three-bucket spread."
            ),
            in_primary_family=True,
        ),
        CaptureDefinition(
            identifier="value_halves_vs_market",
            long_only="0.5 * (SH + BH)",
            benchmark="Mkt-RF + RF",
            denominator="HML",
            reading=(
                "What a retail investor holding this instead of a total-market fund "
                "would have received. Contains a large size tilt as well as a value "
                "tilt, because weighting the small and big halves equally is a size "
                "bet against a market that is overwhelmingly big."
            ),
            in_primary_family=True,
        ),
        CaptureDefinition(
            identifier="big_value_vs_market",
            long_only="BH",
            benchmark="Mkt-RF + RF",
            denominator="HML",
            reading=(
                "The closest public analogue of a large-capitalisation value fund held "
                "instead of a total-market fund, and the most implementable member of "
                "the family."
            ),
            in_primary_family=True,
        ),
        CaptureDefinition(
            identifier="big_value_vs_big_third",
            long_only="BH",
            benchmark="(BL + BM + BH) / 3",
            denominator="HML",
            reading="The value tilt inside the large-capitalisation universe alone.",
            in_primary_family=True,
        ),
        CaptureDefinition(
            identifier="small_value_vs_market",
            long_only="SH",
            benchmark="Mkt-RF + RF",
            denominator="HML",
            reading=(
                "The small-value corner in its 2x3 form, held instead of a total-market "
                "fund. The least implementable member, and reported as such whatever it "
                "measures."
            ),
            in_primary_family=True,
        ),
        CaptureDefinition(
            identifier="partial_tilt_50_vs_market",
            long_only="0.5 * (Mkt-RF + RF) + 0.5 * 0.5 * (SH + BH)",
            benchmark="Mkt-RF + RF",
            denominator="HML",
            reading=(
                "Half the tilt. Exactly half of value_halves_vs_market by construction, "
                "which is why it is outside the family that clause (1) reads; it is "
                "here because real funds are not fully tilted and the capture scales "
                "linearly with the tilt."
            ),
            in_primary_family=False,
        ),
        CaptureDefinition(
            identifier="growth_halves_short_leg_vs_size_neutral",
            long_only="(SL + SM + SH + BL + BM + BH) / 6",
            benchmark="0.5 * (SL + BL)",
            denominator="HML",
            reading=(
                "The SHORT leg's share, not a long-only tilt. It must sum with the "
                "primary to one by construction, which is a second integration test of "
                "the arithmetic and of the claim that the primary is near one half for "
                "structural rather than empirical reasons."
            ),
            in_primary_family=False,
        ),
    )


def _definition_columns(
    definition: CaptureDefinition,
    derived: Mapping[str, FloatArray],
    market: FloatArray,
    denominator: FloatArray,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Resolve a definition into its (long-only, benchmark, denominator) arrays."""
    table: dict[str, tuple[FloatArray, FloatArray]] = {
        "value_halves_vs_size_neutral": (derived["value_halves"], derived["size_neutral_six"]),
        "value_halves_vs_market": (derived["value_halves"], market),
        "big_value_vs_market": (derived[B_HI], market),
        "big_value_vs_big_third": (derived[B_HI], derived["big_third"]),
        "small_value_vs_market": (derived[S_HI], market),
        "partial_tilt_50_vs_market": (
            0.5 * market + 0.5 * derived["value_halves"],
            market,
        ),
        "growth_halves_short_leg_vs_size_neutral": (
            derived["size_neutral_six"],
            derived["growth_halves"],
        ),
    }
    if definition.identifier not in table:
        raise LongOnlyCaptureError(f"no columns wired for definition {definition.identifier!r}")
    long_only, benchmark = table[definition.identifier]
    return long_only, benchmark, denominator


# --------------------------------------------------------------------------- #
# The microcap question
# --------------------------------------------------------------------------- #


def _capitalisation_shares(
    counts: ParsedTable, caps: ParsedTable, *, start: str, end: str
) -> dict[str, JsonValue]:
    """Firm-count and capitalisation shares of every 5x5 cell over a window.

    The capitalisation share is ``(firms * average cap)`` normalised across
    cells. That ratio is INVARIANT to the average-cap table's scale, which the
    file never states and which ``data/french.py`` records as unknown, so no
    absolute figure is reported and none could be.
    """
    low, high = month_index(start), month_index(end)
    count_rows = {
        period: dict(zip(counts.columns, row, strict=True))
        for period, row in zip(counts.periods, counts.values, strict=True)
        if low <= month_index(period) <= high
    }
    cap_rows = {
        period: dict(zip(caps.columns, row, strict=True))
        for period, row in zip(caps.periods, caps.values, strict=True)
        if low <= month_index(period) <= high
    }
    periods = sorted(set(count_rows) & set(cap_rows))
    if not periods:
        raise LongOnlyCaptureError(f"no 5x5 count/cap months inside {start}..{end}")

    columns = list(counts.columns)
    count_share: dict[str, list[float]] = {column: [] for column in columns}
    cap_share: dict[str, list[float]] = {column: [] for column in columns}
    for period in periods:
        firms = {c: count_rows[period].get(c) for c in columns}
        caps_row = {c: cap_rows[period].get(c) for c in columns}
        if any(value is None for value in firms.values()):
            continue
        if any(value is None for value in caps_row.values()):
            continue
        total_firms = sum(float(firms[c] or 0.0) for c in columns)
        weights = {c: float(firms[c] or 0.0) * float(caps_row[c] or 0.0) for c in columns}
        total_cap = sum(weights.values())
        if total_firms <= 0.0 or total_cap <= 0.0:
            continue
        for column in columns:
            count_share[column].append(100.0 * float(firms[column] or 0.0) / total_firms)
            cap_share[column].append(100.0 * weights[column] / total_cap)

    smallest_row = [c for c in columns if c in (S_HI, S_LO) or c.startswith("ME1 ")]
    return {
        "window": f"{periods[0]}..{periods[-1]}",
        "months": len(periods),
        "scale_note": (
            "The average-market-cap table states neither currency nor scale, so "
            "data/french.py records its units as unknown and leaves it untransformed. "
            "Only SHARES are reported here, and a share of (firms * average cap) is "
            "invariant to any common scale. No absolute capitalisation is reported "
            "because none can be."
        ),
        "per_cell": [
            {
                "cell": column,
                "mean_share_of_firm_count_percent": float(np.mean(count_share[column])),
                "mean_share_of_market_cap_percent": float(np.mean(cap_share[column])),
                "final_share_of_firm_count_percent": count_share[column][-1],
                "final_share_of_market_cap_percent": cap_share[column][-1],
            }
            for column in columns
        ],
        "smallest_size_quintile": {
            "cells": smallest_row,
            "mean_share_of_firm_count_percent": float(
                np.sum([np.mean(count_share[c]) for c in smallest_row])
            ),
            "mean_share_of_market_cap_percent": float(
                np.sum([np.mean(cap_share[c]) for c in smallest_row])
            ),
            "final_share_of_firm_count_percent": float(
                np.sum([count_share[c][-1] for c in smallest_row])
            ),
            "final_share_of_market_cap_percent": float(
                np.sum([cap_share[c][-1] for c in smallest_row])
            ),
        },
        "small_value_corner_cell": {
            "cell": CELL_SMALL_VALUE,
            "mean_share_of_firm_count_percent": float(np.mean(count_share[CELL_SMALL_VALUE])),
            "mean_share_of_market_cap_percent": float(np.mean(cap_share[CELL_SMALL_VALUE])),
            "final_share_of_firm_count_percent": count_share[CELL_SMALL_VALUE][-1],
            "final_share_of_market_cap_percent": cap_share[CELL_SMALL_VALUE][-1],
        },
        "hou_xue_zhang_reference": (
            "Hou, Xue and Zhang (2020) put microcaps at 3.2% of market capitalisation "
            "and 60.7% of the stock count and attribute much of the anomaly literature "
            "to them. The shares above are this repository's own measurement of the "
            "same phenomenon in the cells the small-value corner actually lives in."
        ),
    }


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


def _settings(specification: Specification) -> InferenceSettings:
    parameters = _mapping(specification.parameters, where="parameters")
    return InferenceSettings(
        frozen_block_length=12.0,
        neighbour_block_lengths=(6.0, 24.0),
        n_resamples=specification.inference.resamples,
        power_target=_number(parameters, "power_target", where="parameters"),
        materiality_annual_percent=_number(
            parameters, "materiality_threshold_annual_percent", where="parameters"
        ),
        assumed_capture=_number(parameters, "assumed_capture_under_test", where="parameters"),
        spread_threshold=_number(parameters, "spread_threshold", where="parameters"),
    )


def _tolerances(specification: Specification) -> dict[str, float]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(
        _at(parameters, "reconstruction_identities", where="parameters"),
        where="parameters.reconstruction_identities",
    )
    items = _sequence(_at(block, "identities", where="reconstruction_identities"), where="ids")
    out: dict[str, float] = {}
    for index, item in enumerate(items):
        entry = _mapping(item, where=f"identities[{index}]")
        out[_text(entry, "id", where=f"identities[{index}]")] = _number(
            entry, "tolerance_decimal_per_month", where=f"identities[{index}]"
        )
    return out


def _assert_inherited_eras(specification: Specification) -> JsonValue:
    """Check the shared era boundaries against Experiment 001's own file.

    Restating a boundary is how two experiments drift apart. This reads the
    other specification rather than trusting this one's copy of it.
    """
    other = _workspace_root() / "experiments" / "exp_001_factor_decay.yaml"
    if not other.is_file():
        return {
            "checked": False,
            "reason": f"{other} is absent, so the inherited boundaries could not be verified",
        }
    inherited = load_specification(other)
    theirs = {era.name: (era.start, era.end) for era in inherited.sample_policy.eras}
    ours = {era.name: (era.start, era.end) for era in specification.sample_policy.eras}
    shared = sorted(set(theirs) & set(ours))
    disagreements = [name for name in shared if theirs[name] != ours[name]]
    if disagreements:
        raise LongOnlyCaptureError(
            "these era boundaries disagree with exp_001_factor_decay.yaml, which is "
            f"authoritative: {[(n, ours[n], theirs[n]) for n in disagreements]}"
        )
    return {
        "checked": True,
        "specification": "research/experiments/exp_001_factor_decay.yaml",
        "specification_hash": inherited.spec_hash,
        "shared_eras": shared,
        "all_agree": True,
    }


def _era_windows(specification: Specification) -> dict[str, tuple[str, str]]:
    return {era.name: (era.start, era.end) for era in specification.sample_policy.eras}


def _reconstruction_checks(
    block: AlignedBlock,
    derived: Mapping[str, FloatArray],
    loaded: Mapping[str, LoadedTable],
    tolerances: Mapping[str, float],
    *,
    sample_end: str,
) -> tuple[list[ReconstructionCheck], dict[str, JsonValue]]:
    """Clause (0), plus the two checks that exist to be reported, not to pass."""
    checks: list[ReconstructionCheck] = [
        check_reconstruction(
            derived["hml_reconstructed"],
            block["ff3_HML"],
            identity="hml_from_6_portfolios_2x3",
            formula="HML = 0.5 * (SH + BH) - 0.5 * (SL + BL)",
            checked_against="the HML column of french_us_ff3, 1926-07 onwards",
            tolerance=tolerances["hml_from_6_portfolios_2x3"],
            note=(
                "The whole experiment rests on this identity. It is checked over the "
                "longest window both files share, not over a convenient subsample."
            ),
        ),
        check_reconstruction(
            derived["smb_reconstructed"],
            block["ff3_SMB"],
            identity="smb_from_6_portfolios_2x3_against_three_factor",
            formula="SMB = (SL + SM + SH) / 3 - (BL + BM + BH) / 3",
            checked_against="the SMB column of french_us_ff3",
            tolerance=tolerances["smb_from_6_portfolios_2x3"],
            note=(
                "The three-factor SMB is built from exactly these six portfolios, so "
                "it must reconcile."
            ),
        ),
    ]

    # The five-factor comparison, run in order to be reported as a disagreement.
    ff5 = loaded["us_ff5"]
    ff5_block = align_series(
        "us_ff5_vs_6",
        {
            "SMB": ff5.series("SMB"),
            "HML": ff5.series("HML"),
            S_LO: loaded["us_6_portfolios_2x3"].series(S_LO),
            S_MID: loaded["us_6_portfolios_2x3"].series(S_MID),
            S_HI: loaded["us_6_portfolios_2x3"].series(S_HI),
            B_LO: loaded["us_6_portfolios_2x3"].series(B_LO),
            B_MID: loaded["us_6_portfolios_2x3"].series(B_MID),
            B_HI: loaded["us_6_portfolios_2x3"].series(B_HI),
        },
    ).window(start="1963-07", end=sample_end)
    ff5_derived = _derive_value_columns(ff5_block)
    checks.append(
        check_reconstruction(
            ff5_derived["hml_reconstructed"],
            ff5_block["HML"],
            identity="hml_from_6_portfolios_2x3_against_five_factor",
            formula="HML = 0.5 * (SH + BH) - 0.5 * (SL + BL)",
            checked_against="the HML column of french_us_ff5, 1963-07 onwards",
            tolerance=tolerances["hml_from_6_portfolios_2x3"],
            note=(
                "The five-factor HML is the series Experiments 001 and 005 measured. "
                "This check is what makes the denominator of every capture fraction "
                "here the same series they measured, and not a lookalike."
            ),
        )
    )
    checks.append(
        check_reconstruction(
            ff5_derived["smb_reconstructed"],
            ff5_block["SMB"],
            identity="smb_from_6_portfolios_2x3_against_five_factor",
            formula="SMB = (SL + SM + SH) / 3 - (BL + BM + BH) / 3",
            checked_against="the SMB column of french_us_ff5",
            tolerance=tolerances["smb_from_6_portfolios_2x3"],
            expected_to_pass=False,
            note=(
                "EXPECTED TO FAIL, and run so that the failure is on the record. The "
                "five-factor SMB averages the size legs of the book-to-market, "
                "profitability and investment sorts, so it is a different series from "
                "the three-factor SMB the six portfolios alone can rebuild. A reader "
                "who assumed the two SMBs were the same series would draw a false "
                "conclusion from this experiment."
            ),
        )
    )

    momentum_block = align_series(
        "us_momentum",
        {
            **{
                column: loaded["us_6_portfolios_me_prior_12_2"].series(column)
                for column in _2X3_MOMENTUM
            },
            "Mom": loaded["us_momentum"].series("Mom"),
        },
    ).window(start="1927-01", end=sample_end)
    umd_reconstructed = 0.5 * (momentum_block[M_HI] + momentum_block[MB_HI]) - 0.5 * (
        momentum_block[M_LO] + momentum_block[MB_LO]
    )
    checks.append(
        check_reconstruction(
            umd_reconstructed,
            momentum_block["Mom"],
            identity="umd_from_6_portfolios_me_prior_12_2",
            formula="UMD = 0.5 * (SHiPRIOR + BHiPRIOR) - 0.5 * (SLoPRIOR + BLoPRIOR)",
            checked_against="the Mom column of french_us_momentum",
            tolerance=tolerances["umd_from_6_portfolios_me_prior_12_2"],
            note=(
                "Run so that the value result is not the only one whose arithmetic was "
                "checked. The momentum sort is reconstituted monthly and the two files "
                "are rounded independently, which is why its declared tolerance is one "
                "and a half printed digits rather than one."
            ),
        )
    )
    return checks, {
        "ff5_window": f"{ff5_block.periods[0]}..{ff5_block.periods[-1]}",
        "momentum_window": f"{momentum_block.periods[0]}..{momentum_block.periods[-1]}",
    }


def _capture_grid(
    block: AlignedBlock,
    eras: Mapping[str, tuple[str, str]],
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> dict[str, list[CaptureCell]]:
    """Every definition over every era, on the aligned US block."""
    definitions = _definitions()
    by_era: dict[str, list[CaptureCell]] = {}
    for era_name, (start, end) in eras.items():
        if era_name.startswith("umd_"):
            continue
        window = block.window(start=start, end=end)
        if window.months < 24:
            continue
        derived = _derive_value_columns(window)
        derived = {**derived, S_HI: window[S_HI], B_HI: window[B_HI]}
        market = window["ff3_Mkt-RF"] + window["ff3_RF"]
        denominator = derived["hml_reconstructed"]
        cells: list[CaptureCell] = []
        for definition in definitions:
            long_only, benchmark, spread = _definition_columns(
                definition, derived, market, denominator
            )
            cells.append(
                capture_cell(
                    long_only,
                    benchmark,
                    spread,
                    window.periods,
                    definition=definition,
                    era_name=era_name,
                    start=start,
                    end=end,
                    settings=settings,
                    rng=rng,
                    with_neighbours=era_name in FALSIFIER_ERAS,
                )
            )
        by_era[era_name] = cells
    return by_era


def _corner_block(
    loaded: Mapping[str, LoadedTable],
    market_series: Mapping[str, MonthlySeries],
    cache: RawCache,
    *,
    start: str,
    end: str,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> dict[str, JsonValue]:
    """The 5x5 corner: capture, risk, loadings, microcaps, and the ex-ME1 rerun."""
    table = loaded["us_25_portfolios_5x5"].table
    columns = list(table.columns)
    series = {
        column: _series_from_table(table, column, dataset_id="french_us_25_portfolios_5x5")
        for column in columns
    }
    block = align_series("us_25", {**series, **market_series}).window(start=start, end=end)

    market = block["Mkt-RF"] + block["RF"]
    equal_25 = np.stack([block[column] for column in columns], axis=1).mean(axis=1)
    corner = 0.5 * (block[CELL_SMALL_VALUE] + block[CELL_BIG_VALUE])
    corner_ex_me1 = 0.5 * (block[CELL_ME2_VALUE] + block[CELL_BIG_VALUE])
    hml = block["HML"]

    def cell(
        identifier: str, long_only: FloatArray, benchmark: FloatArray, reading: str
    ) -> CaptureCell:
        definition = CaptureDefinition(
            identifier=identifier,
            long_only=identifier,
            benchmark="see reading",
            denominator="HML",
            reading=reading,
            in_primary_family=False,
        )
        return capture_cell(
            long_only,
            benchmark,
            hml,
            block.periods,
            definition=definition,
            era_name="corner",
            start=start,
            end=end,
            settings=settings,
            rng=rng,
            with_neighbours=False,
        )

    corner_cells = [
        cell(
            "corner_5x5_value_halves_vs_market",
            corner,
            market,
            "0.5 * (ME1 BM5 + ME5 BM5) from the 5x5 file, against the total market.",
        ),
        cell(
            "corner_5x5_value_halves_vs_equal_weighted_25",
            corner,
            equal_25,
            "The same corner against the equal-weighted average of all 25 cells.",
        ),
        cell(
            "small_value_cell_5x5_vs_market",
            block[CELL_SMALL_VALUE],
            market,
            "The pure small-value cell, ME1 x BM5, against the total market.",
        ),
        cell(
            "corner_5x5_ex_smallest_quintile_vs_market",
            corner_ex_me1,
            market,
            (
                "The identical corner computation with the ME1 size quintile dropped "
                "entirely and ME2 used as the small leg. The direct test of whether "
                "the corner depends on the smallest quintile."
            ),
        ),
    ]

    # Loadings on the three factors, HAC, on the excess return of the corner cell.
    design = np.column_stack([block["Mkt-RF"], block["SMB"], block["HML"]])
    loadings: list[JsonValue] = []
    for name, returns in (
        (CELL_SMALL_VALUE, block[CELL_SMALL_VALUE]),
        ("corner_halves", corner),
        (CELL_ME2_VALUE, block[CELL_ME2_VALUE]),
    ):
        fit = hac_ols(returns - block["RF"], design, n_lags=newey_west_lag_count(block.months))
        loadings.append(
            {
                "portfolio": name,
                "alpha_percent_per_year": float(fit.coefficients[0]) * MONTHS_PER_YEAR * 100.0,
                "alpha_hac_standard_error_percent_per_year": (
                    float(fit.standard_errors[0]) * MONTHS_PER_YEAR * 100.0
                ),
                "alpha_t_statistic": _json_float(float(fit.t_statistics[0])),
                "beta_mkt_rf": float(fit.coefficients[1]),
                "beta_mkt_rf_hac_standard_error": float(fit.standard_errors[1]),
                "loading_smb": float(fit.coefficients[2]),
                "loading_smb_hac_standard_error": float(fit.standard_errors[2]),
                "loading_hml": float(fit.coefficients[3]),
                "loading_hml_hac_standard_error": float(fit.standard_errors[3]),
                "hac_lag_count": fit.n_lags,
                "months": fit.n_observations,
                "note": (
                    "Alpha is annualised by multiplying the monthly intercept by 12, "
                    "and its standard error by 12 as well, never by sqrt(12)."
                ),
            }
        )

    risks = [
        portfolio_risk(block[CELL_SMALL_VALUE], block.periods, name=CELL_SMALL_VALUE).to_json(),
        portfolio_risk(corner, block.periods, name="corner_halves").to_json(),
        portfolio_risk(block[CELL_ME2_VALUE], block.periods, name=CELL_ME2_VALUE).to_json(),
        portfolio_risk(market, block.periods, name="total_market").to_json(),
    ]

    shares = _capitalisation_shares(
        _sibling_table(
            cache, "french_us_25_portfolios_5x5", "number_of_firms_in_portfolios_monthly"
        ),
        _sibling_table(cache, "french_us_25_portfolios_5x5", "average_market_cap_monthly"),
        start=start,
        end=end,
    )

    return {
        "window": f"{block.periods[0]}..{block.periods[-1]}",
        "months": block.months,
        "capture_cells": [item.to_json() for item in corner_cells],
        "risk": risks,
        "factor_loadings": loadings,
        "capitalisation_and_firm_count_shares": shares,
        "dependence_on_the_smallest_quintile": {
            "with_me1_vs_market": corner_cells[0].capture_fraction,
            "without_me1_vs_market": corner_cells[3].capture_fraction,
            "with_me1_spread_percent_per_year": corner_cells[0].spread_annual_percent,
            "without_me1_spread_percent_per_year": corner_cells[3].spread_annual_percent,
            "difference_percent_per_year": (
                corner_cells[0].spread_annual_percent - corner_cells[3].spread_annual_percent
            ),
        },
    }


def _momentum_block(
    loaded: Mapping[str, LoadedTable],
    market_series: Mapping[str, MonthlySeries],
    eras: Mapping[str, tuple[str, str]],
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> dict[str, JsonValue]:
    """The same question asked of momentum, whose sort is reconstituted monthly."""
    portfolios = loaded["us_6_portfolios_me_prior_12_2"]
    series = {column: portfolios.series(column) for column in _2X3_MOMENTUM}
    series["Mom"] = loaded["us_momentum"].series("Mom")
    block_full = align_series("us_momentum_capture", {**series, **market_series})

    rows: list[JsonValue] = []
    for era_name in ("full_sample_since_1963", "umd_full_post_publication", "umd_original_sample"):
        if era_name not in eras:
            continue
        start, end = eras[era_name]
        window = block_full.window(start=start, end=end)
        if window.months < 24:
            continue
        market = window["Mkt-RF"] + window["RF"]
        winners = 0.5 * (window[M_HI] + window[MB_HI])
        six = np.stack([window[column] for column in _2X3_MOMENTUM], axis=1).mean(axis=1)
        umd = window["Mom"]
        for identifier, benchmark, reading in (
            (
                "momentum_winner_halves_vs_size_neutral",
                six,
                "The winner halves against the equal-weighted six of the same sort.",
            ),
            (
                "momentum_winner_halves_vs_market",
                market,
                "The winner halves against the total market.",
            ),
        ):
            definition = CaptureDefinition(
                identifier=identifier,
                long_only="0.5 * (SHiPRIOR + BHiPRIOR)",
                benchmark="see reading",
                denominator="Mom",
                reading=reading,
                in_primary_family=False,
            )
            rows.append(
                capture_cell(
                    winners,
                    benchmark,
                    umd,
                    window.periods,
                    definition=definition,
                    era_name=era_name,
                    start=start,
                    end=end,
                    settings=settings,
                    rng=rng,
                    with_neighbours=False,
                ).to_json()
            )
    return {
        "why": (
            "The value answer must not be read as universal. The prior-return sort is "
            "reconstituted MONTHLY, so its turnover is an order of magnitude above the "
            "annually rebalanced book-to-market sort and the two capture fractions are "
            "not comparable without that stated."
        ),
        "cells": rows,
    }


def _size_block(
    loaded: Mapping[str, LoadedTable],
    market_series: Mapping[str, MonthlySeries],
    eras: Mapping[str, tuple[str, str]],
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> dict[str, JsonValue]:
    """The size premium test the design map records as never having been run."""
    table = loaded["us_portfolios_formed_on_me"].table
    wanted = ("Lo 20", "Hi 20", "Lo 10", "Hi 10")
    series = {
        column: _series_from_table(
            table, column, dataset_id="french_us_portfolios_formed_on_me"
        )
        for column in wanted
    }
    block_full = align_series("us_size", {**series, **market_series})

    rows: list[JsonValue] = []
    premia: list[JsonValue] = []
    for era_name in ("full_sample_since_1963", "hml_full_post_publication"):
        start, end = eras[era_name]
        window = block_full.window(start=start, end=end)
        market = window["Mkt-RF"] + window["RF"]
        quintile_spread = window["Lo 20"] - window["Hi 20"]
        decile_spread = window["Lo 10"] - window["Hi 10"]
        for identifier, long_only, spread, reading in (
            (
                "small_quintile_vs_market",
                window["Lo 20"],
                quintile_spread,
                "The smallest value-weighted size quintile held instead of the market.",
            ),
            (
                "small_decile_vs_market",
                window["Lo 10"],
                decile_spread,
                "The smallest value-weighted size decile held instead of the market.",
            ),
        ):
            definition = CaptureDefinition(
                identifier=identifier,
                long_only=identifier,
                benchmark="Mkt-RF + RF",
                denominator="small minus big, same sort",
                reading=reading,
                in_primary_family=False,
            )
            rows.append(
                capture_cell(
                    long_only,
                    market,
                    spread,
                    window.periods,
                    definition=definition,
                    era_name=era_name,
                    start=start,
                    end=end,
                    settings=settings,
                    rng=rng,
                    with_neighbours=False,
                ).to_json()
            )
        for label, spread in (("quintile", quintile_spread), ("decile", decile_spread)):
            hac = hac_mean(spread * 100.0, n_lags=newey_west_lag_count(window.months))
            interval = _spread_bootstrap(
                spread,
                block_length=settings.frozen_block_length,
                n_resamples=settings.n_resamples,
                rng=rng,
            )
            premia.append(
                {
                    "era": era_name,
                    "sort": label,
                    "months": window.months,
                    "long_short_premium_percent_per_year": interval.point_estimate,
                    "two_sided_90": [interval.lower_90, interval.upper_90],
                    "hac_t_statistic": _json_float(hac.t_statistic),
                    "one_sided_p_value_hac": _json_float(one_sided_p_value(hac.t_statistic)),
                    "mde_one_sided_percent_per_year": MONTHS_PER_YEAR
                    * minimum_detectable_effect(
                        standard_error=float(np.std(spread * 100.0, ddof=1))
                        / math.sqrt(window.months),
                        power=settings.power_target,
                        one_sided=True,
                    ),
                }
            )
    return {
        "why": (
            "The design map records that size 'was never tested as a premium' in this "
            "repository. This is that test, and it is a LONG-ONLY test by construction: "
            "the smallest quintile and decile of a value-weighted size sort are "
            "portfolios, and their excess over the market is what a small-cap fund "
            "delivers. The long-short spread beneath them is reported beside it."
        ),
        "not_the_ff_smb": (
            "The small-minus-big spread computed here is a plain quintile or decile "
            "difference from Portfolios_Formed_on_ME. It is NOT the Fama-French SMB, "
            "which is a size leg averaged across book-to-market, profitability and "
            "investment sorts, and the two must not be quoted as the same number."
        ),
        "long_only_cells": rows,
        "long_short_premia": premia,
    }


def _regional_block(
    loaded: Mapping[str, LoadedTable],
    eras: Mapping[str, tuple[str, str]],
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
    sample_end: str,
) -> dict[str, JsonValue]:
    """The same computation on files that share no security with the US one."""
    regions = (
        ("developed_ex_us", "developed_ex_us_6_portfolios_2x3", "developed_ex_us_ff5"),
        ("emerging", "emerging_6_portfolios_2x3", "emerging_ff5"),
    )
    rows: list[JsonValue] = []
    checks: list[JsonValue] = []
    for region, portfolio_id, factor_id in regions:
        portfolios = loaded[portfolio_id]
        factors = loaded[factor_id]
        series: dict[str, MonthlySeries] = {
            column: portfolios.series(column) for column in _2X3_VALUE
        }
        for column in ("Mkt-RF", "HML", "RF"):
            series[column] = factors.series(column)
        block = align_series(f"{region}_value", series)
        for era_name in ("hml_full_post_publication", "recent"):
            start, end = eras[era_name]
            window = block.window(start=start, end=end)
            if window.months < 24:
                continue
            derived = _derive_value_columns(window)
            derived = {**derived, S_HI: window[S_HI], B_HI: window[B_HI]}
            market = window["Mkt-RF"] + window["RF"]
            denominator = derived["hml_reconstructed"]
            if era_name == "hml_full_post_publication":
                checks.append(
                    check_reconstruction(
                        denominator,
                        window["HML"],
                        identity=f"hml_from_6_portfolios_2x3_{region}",
                        formula="HML = 0.5 * (SH + BH) - 0.5 * (SL + BL)",
                        checked_against=f"the HML column of {factors.dataset_id}",
                        tolerance=0.0005,
                        expected_to_pass=False,
                        note=(
                            "REPORTED, NOT REQUIRED. The regional factor files are built "
                            "on a different breakpoint scheme from a Bloomberg vintage "
                            "and Ken French does not document the regional HML as a "
                            "difference of these six portfolios, so a residual here is "
                            "information about the regional construction rather than a "
                            "defect. The tolerance is deliberately loose and the check "
                            "is marked not-required so that it cannot fire clause (0)."
                        ),
                    ).to_json()
                )
            for identifier, long_only, benchmark, reading in (
                (
                    "value_halves_vs_size_neutral",
                    derived["value_halves"],
                    derived["size_neutral_six"],
                    "The size-neutral definition, computed on the regional sort.",
                ),
                (
                    "value_halves_vs_market",
                    derived["value_halves"],
                    market,
                    "The value halves against the regional market, USD and unhedged.",
                ),
                (
                    "small_value_vs_market",
                    derived[S_HI],
                    market,
                    "The regional small-value half against the regional market.",
                ),
            ):
                definition = CaptureDefinition(
                    identifier=f"{region}/{identifier}",
                    long_only=identifier,
                    benchmark="see reading",
                    denominator="HML reconstructed from the regional six",
                    reading=reading,
                    in_primary_family=False,
                )
                rows.append(
                    capture_cell(
                        long_only,
                        benchmark,
                        denominator,
                        window.periods,
                        definition=definition,
                        era_name=era_name,
                        start=start,
                        end=end,
                        settings=settings,
                        rng=rng,
                        with_neighbours=False,
                    ).to_json()
                )
    _ = sample_end
    return {
        "why_not_the_developed_file": (
            "Developed_6_Portfolios and Developed_25_Portfolios INCLUDE the United "
            "States, exactly as Developed_5_Factors does, so neither can serve as an "
            "ex-US check. The ex-US files of the same sorts are used instead. "
            "Experiment 005 measured the overlap on the factor files: regressing the "
            "Developed market factor on the US and developed-ex-US ones gives 0.460 "
            "and 0.549."
        ),
        "no_emerging_corner": (
            "There is no 25-portfolio emerging file. The library distributes emerging "
            "markets as 2x3 sixes and 2x2 fours only, published under the prefix "
            "Emerging_Markets_ rather than the Emerging_ prefix the emerging factor "
            "files use. Emerging_25_Portfolios_ME_BE-ME_CSV.zip returns HTTP 404. "
            "There is therefore no emerging small-value CORNER to test."
        ),
        "regional_reconstruction_checks": checks,
        "cells": rows,
    }


def _cost_block(
    block: AlignedBlock,
    specification: Specification,
    *,
    start: str,
    end: str,
) -> dict[str, JsonValue]:
    """Costs as a separate column: one measured component and two assumed ones."""
    cost_model = _mapping(specification.cost_model, where="cost_model")
    measured = _mapping(_at(cost_model, "measured_component", where="cost_model"), where="m")
    assumed = _mapping(_at(cost_model, "assumed_components", where="cost_model"), where="a")
    expense = _mapping(
        _at(assumed, "expense_ratio_percent_per_year", where="assumed_components"), where="e"
    )
    turnover = _mapping(
        _at(assumed, "internal_sort_turnover_one_sided_percent_per_year", where="assumed"),
        where="t",
    )
    expense_ratios = (
        _number(expense, "shelf_median", where="expense_ratio"),
        _number(expense, "small_value_product", where="expense_ratio"),
    )
    coefficients = _numbers(assumed, "coefficient_k", where="assumed_components")

    window = block.window(start=start, end=end)
    measured_rows = [
        rebalance_cost(window[S_HI], window[B_HI], frequency=frequency, k=k).to_json()
        for frequency in ("monthly", "annual")
        for k in coefficients
    ]
    rebalanced = portfolio_risk(
        0.5 * (window[S_HI] + window[B_HI]), window.periods, name="rebalanced_every_month"
    )
    # A never-rebalanced 50/50 is the sum of two half-sized wealth paths, so its
    # monthly return is the growth of that sum. Both curves carry the leading
    # initial-wealth element, which cancels in the ratio.
    drifting = np.asarray(
        equity_curve(window[S_HI]) + equity_curve(window[B_HI]), dtype=np.float64
    )
    drift_growth = np.asarray(drifting[1:] / drifting[:-1] - 1.0, dtype=np.float64)
    buy_and_hold = portfolio_risk(
        drift_growth, window.periods, name="never_rebalanced_buy_and_hold"
    )

    return {
        "window": f"{window.periods[0]}..{window.periods[-1]}",
        "principle": (
            "Costs are a SEPARATE COLUMN and never a haircut folded into the gross "
            "figure. The one turnover that is measured is charged against the wealth "
            "path at the moment of the trade, so it alters the compounded result "
            "rather than being deducted from a mean afterwards."
        ),
        "measured_component": {
            "what": _text(measured, "what", where="measured_component"),
            "rows": measured_rows,
            "reading": (
                "This is the whole cost of the 50/50 rebalance between the small-value "
                "and big-value halves, and it is small. Saying so is the point: the "
                "cost that matters for a long-only tilt is the fee and the internal "
                "reconstitution of the sort, neither of which is recoverable from a "
                "return series and both of which are therefore assumed below."
            ),
        },
        "rebalancing_choice": {
            "monthly_rebalance": rebalanced.to_json(),
            "never_rebalanced": buy_and_hold.to_json(),
            "note": (
                "The 50/50 weighting is a choice this experiment imposes, so the cost "
                "of imposing it is shown. A portfolio that never rebalances drifts "
                "towards whichever half compounded faster and is a different portfolio "
                "by the end of the window."
            ),
        },
        "assumed_components": {
            "warning": (
                "ASSUMPTIONS, and the weakest numbers in this experiment. Turnover "
                "cannot be recovered from a return series. Every row below is an "
                "illustration and none is a measurement."
            ),
            "rows": [
                *_assumed_cost_rows(
                    label="annual book-to-market reconstitution",
                    turnovers=_numbers(turnover, "value_sorts", where="turnover"),
                    expense_ratios=expense_ratios,
                    coefficients=coefficients,
                ),
                *_assumed_cost_rows(
                    label="monthly prior-return reconstitution",
                    turnovers=_numbers(turnover, "momentum_sorts", where="turnover"),
                    expense_ratios=expense_ratios,
                    coefficients=coefficients,
                ),
            ],
        },
    }


def _calibration(
    numerator: FloatArray,
    denominator: FloatArray,
    *,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> dict[str, JsonValue]:
    """The identical ratio machinery on zero-mean noise of matched covariance.

    The calibration check the framework demands. Both means are zero by
    construction, so the true capture fraction does not exist; whatever
    interval this produces is what the machinery produces from nothing.
    """
    panel = np.stack([numerator, denominator], axis=1)
    covariance = np.cov(panel, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(np.atleast_2d(covariance))
    factor = eigenvectors @ np.diag(np.sqrt(np.clip(eigenvalues, 0.0, None)))
    draws = rng.normal(size=(numerator.size, 2)) @ factor.T
    interval = joint_ratio_bootstrap(
        np.asarray(draws[:, 0], dtype=np.float64),
        np.asarray(draws[:, 1], dtype=np.float64),
        block_length=settings.frozen_block_length,
        block_length_source="frozen",
        n_resamples=settings.n_resamples,
        rng=rng,
    )
    return {
        "description": (
            "A zero-mean Gaussian pair of the same length and the same measured "
            "covariance as the real numerator and denominator, put through the "
            "identical joint ratio bootstrap. Both means are zero by construction, so "
            "no capture fraction exists; whatever this produces is what the machinery "
            "produces from correlated nothing, and it shows directly how wide a ratio "
            "interval becomes once the denominator carries no signal."
        ),
        "months": int(numerator.size),
        "matched_correlation": float(
            np.atleast_2d(np.asarray(np.corrcoef(panel, rowvar=False), dtype=np.float64))[0, 1]
        ),
        "interval": interval.to_json(),
    }


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #


def _estimates_for(
    cells_by_era: Mapping[str, Sequence[CaptureCell]], verdict: Verdict
) -> tuple[Estimate, ...]:
    estimates: list[Estimate] = []
    for era in FALSIFIER_ERAS:
        for cell in cells_by_era[era]:
            if not cell.definition.in_primary_family:
                continue
            interval = cell.capture_interval
            degenerate = max(
                interval.near_zero_denominator_resamples,
                interval.sign_flipped_denominator_resamples,
            )
            unstable = (
                " UNSTABLE: the denominator was near zero or sign-flipped in "
                f"{degenerate} of {interval.n_resamples} resamples, so this interval "
                "may not be quoted without that mark."
                if interval.unstable
                else ""
            )
            estimates.append(
                Estimate(
                    name=f"capture fraction, {cell.definition.identifier}, {era}",
                    value=cell.capture_fraction,
                    units="dimensionless ratio of long-only excess to long-short premium",
                    interval=(interval.lower_90, interval.upper_90),
                    interval_method=(
                        f"JOINT stationary block bootstrap of the ratio, two-sided 90%, "
                        f"mean block {interval.block_length:.0f}m, "
                        f"{interval.n_resamples} resamples"
                    ),
                    cost_basis=CostBasis.GROSS,
                    n_obs=cell.months,
                    notes=(
                        f"long-only {cell.definition.long_only} against "
                        f"{cell.definition.benchmark}; the long-only excess is "
                        f"{cell.spread_annual_percent:+.2f} pp/yr against an HML of "
                        f"{cell.denominator_annual_percent:+.2f} pp/yr. Gross, and "
                        "these are research portfolios, not products." + unstable
                    ),
                )
            )
            estimates.append(
                Estimate(
                    name=f"long-only excess spread, {cell.definition.identifier}, {era}",
                    value=cell.spread_annual_percent,
                    units="percentage points per year",
                    interval=(
                        cell.spread_interval.lower_90,
                        cell.spread_interval.upper_90,
                    ),
                    interval_method=(
                        f"stationary block bootstrap, two-sided 90%, mean block "
                        f"{cell.spread_interval.block_length:.0f}m, "
                        f"{cell.spread_interval.n_resamples} resamples"
                    ),
                    cost_basis=CostBasis.GROSS,
                    n_obs=cell.months,
                    notes=(
                        "detectable at 80% power only above "
                        f"{cell.mde_one_sided_percent_per_year:.2f} pp/yr; the HAC "
                        f"reading is {cell.mde_one_sided_hac_percent_per_year:.2f}."
                    ),
                )
            )
    for era, spread in verdict.spread_by_era.items():
        estimates.append(
            Estimate(
                name=f"definitional spread of the capture fraction, {era}",
                value=spread,
                units="dimensionless ratio",
                interval=None,
                uncertainty_unavailable_reason=(
                    "This is the range of five point estimates, not an estimate of a "
                    "population quantity. An interval on it would suggest it is a "
                    "sampling object; it is a statement about how much the researcher's "
                    "choice of benchmark moves the answer, and the five underlying "
                    "estimates each carry their own interval."
                ),
                cost_basis=CostBasis.NOT_APPLICABLE,
                notes=(
                    "Clause (1) of the frozen falsifier reads this against a threshold "
                    "of 0.30, which is three quarters of the 0.40 the edge "
                    "decomposition assumes."
                ),
            )
        )
    return tuple(estimates)


def _frames(
    cells_by_era: Mapping[str, Sequence[CaptureCell]],
    checks: Sequence[ReconstructionCheck],
) -> dict[str, pd.DataFrame]:
    capture = pd.DataFrame(
        [cell.to_json() for cells in cells_by_era.values() for cell in cells]
    )
    reconstruction = pd.DataFrame([check.to_json() for check in checks])
    return {"capture_cells": capture, "reconstruction_checks": reconstruction}


def _summary_line(
    verdict: Verdict,
    cells_by_era: Mapping[str, Sequence[CaptureCell]],
    settings: InferenceSettings,
) -> str:
    parts: list[str] = []
    ranges: list[str] = []
    for era in FALSIFIER_ERAS:
        cell = next(
            item for item in cells_by_era[era] if item.definition.identifier == SIZE_NEUTRAL
        )
        parts.append(
            f"{era} {cell.capture_fraction:.3f} "
            f"[{cell.capture_interval.lower_90:.3f}, {cell.capture_interval.upper_90:.3f}]"
        )
        family = [
            item.capture_fraction
            for item in cells_by_era[era]
            if item.definition.in_primary_family
        ]
        ranges.append(f"{era} {min(family):.3f} to {max(family):.3f}")
    spreads = ", ".join(
        f"{era} {value:.3f}" for era, value in verdict.spread_by_era.items()
    )
    return (
        f"The size-neutral long-only capture fraction of HML is {', '.join(parts)}. "
        f"Across the five predeclared benchmark definitions it ranges "
        f"{'; '.join(ranges)}, a spread of {spreads} against the "
        f"{settings.spread_threshold:.2f} threshold. Clause (1) "
        + ("FIRED" if verdict.clause_one_rejected else "held")
        + f"; clause (2) {verdict.clause_two}. All figures are gross and these are "
        "research portfolios, not products."
    )


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 007."""
    settings = _settings(specification)
    tolerances = _tolerances(specification)
    eras = _era_windows(specification)
    sample_end = specification.sample_policy.end
    rng = context.rng

    loaded, cache = _load_sources(specification)
    inheritance = _assert_inherited_eras(specification)

    block = _us_value_block(loaded).window(
        start=specification.sample_policy.start, end=sample_end
    )
    derived = _derive_value_columns(block)

    checks, reconstruction_windows = _reconstruction_checks(
        block, derived, loaded, tolerances, sample_end=sample_end
    )

    cells_by_era = _capture_grid(block, eras, settings=settings, rng=rng)
    verdict = apply_rejection_rule(checks, cells_by_era, settings=settings)

    market_series = {
        "Mkt-RF": loaded["us_ff5"].series("Mkt-RF"),
        "SMB": loaded["us_ff5"].series("SMB"),
        "HML": loaded["us_ff5"].series("HML"),
        "RF": loaded["us_ff5"].series("RF"),
    }
    primary_start, primary_end = eras["full_sample_since_1963"]

    corner = _corner_block(
        loaded,
        market_series,
        cache,
        start=primary_start,
        end=primary_end,
        settings=settings,
        rng=rng,
    )
    momentum = _momentum_block(loaded, market_series, eras, settings=settings, rng=rng)
    size = _size_block(loaded, market_series, eras, settings=settings, rng=rng)
    regional = _regional_block(
        loaded, eras, settings=settings, rng=rng, sample_end=sample_end
    )
    costs = _cost_block(block, specification, start=primary_start, end=primary_end)

    primary_window = block.window(start=primary_start, end=primary_end)
    primary_derived = _derive_value_columns(primary_window)
    calibration = _calibration(
        primary_derived["value_halves"] - primary_derived["size_neutral_six"],
        primary_derived["hml_reconstructed"],
        settings=settings,
        rng=rng,
    )

    # Multiple testing over the frozen family: five definitions x two eras, on the
    # one-sided HAC p-value that the long-only excess SPREAD is positive.
    family_keys: list[str] = []
    family_p: list[float] = []
    for era in FALSIFIER_ERAS:
        for cell in cells_by_era[era]:
            if cell.definition.in_primary_family:
                family_keys.append(cell.key)
                family_p.append(cell.one_sided_p_value_hac)
    alpha = _number(
        _mapping(specification.parameters, where="parameters"),
        "benjamini_hochberg_alpha",
        where="parameters",
    )
    bh = benjamini_hochberg(family_p, alpha=alpha)
    holm = holm_bonferroni(family_p, alpha=alpha)

    risk_rows = [
        portfolio_risk(
            primary_derived["value_halves"], primary_window.periods, name="value_halves"
        ).to_json(),
        portfolio_risk(
            primary_window[S_HI], primary_window.periods, name="small_value_half"
        ).to_json(),
        portfolio_risk(
            primary_window[B_HI], primary_window.periods, name="big_value_half"
        ).to_json(),
        portfolio_risk(
            primary_derived["size_neutral_six"],
            primary_window.periods,
            name="size_neutral_six",
        ).to_json(),
        portfolio_risk(
            primary_window["ff3_Mkt-RF"] + primary_window["ff3_RF"],
            primary_window.periods,
            name="total_market",
        ).to_json(),
    ]

    chain = _edge_chain(cells_by_era, settings)

    diagnostics: dict[str, JsonValue] = {
        "sources": [item.provenance for item in loaded.values()],
        "sample_policy": {
            "start": specification.sample_policy.start,
            "end": sample_end,
            "held_out_after": sample_end,
            "aligned_us_window": f"{block.periods[0]}..{block.periods[-1]}",
            "months_dropped_by_intersection": block.dropped_months,
            "months_available_beyond_holdout": max(
                0,
                month_count(
                    sample_end,
                    loaded["us_6_portfolios_2x3"].table.last_observation or sample_end,
                )
                - 1,
            ),
        },
        "inherited_era_check": inheritance,
        "reconstruction_checks": [check.to_json() for check in checks],
        "reconstruction_windows": reconstruction_windows,
        "definitions": [item.to_json() for item in _definitions()],
        "capture_cells": [
            cell.to_json() for cells in cells_by_era.values() for cell in cells
        ],
        "verdict": verdict.to_json(),
        "long_only_risk": risk_rows,
        "small_value_corner": corner,
        "momentum": momentum,
        "size": size,
        "regional": regional,
        "costs": costs,
        "edge_chain": chain,
        "inference": {
            "family": "five primary definitions x two falsifier eras",
            "alpha": alpha,
            "note": (
                "The correction is applied to the one-sided HAC p-value that the "
                "long-only excess SPREAD is positive, not to the capture fractions. A "
                "capture fraction's null is 0.40 rather than zero, and a family of "
                "ratios sharing one denominator is close to the same test repeated; "
                "Holm-Bonferroni is reported because it is valid under exactly that "
                "kind of dependence."
            ),
            "cells": [
                {
                    "cell": key,
                    "one_sided_p_uncorrected": p,
                    "benjamini_hochberg_adjusted_p": float(bh_p),
                    "benjamini_hochberg_rejected": bool(bh_ok),
                    "holm_bonferroni_adjusted_p": float(holm_p),
                    "holm_bonferroni_rejected": bool(holm_ok),
                }
                for key, p, bh_p, bh_ok, holm_p, holm_ok in zip(
                    family_keys,
                    family_p,
                    bh.adjusted_p_values,
                    bh.rejected,
                    holm.adjusted_p_values,
                    holm.rejected,
                    strict=True,
                )
            ],
        },
        "hostile_tests": {
            "long_and_short_leg_shares_sum_to_one": _leg_symmetry(cells_by_era),
            "calibration_on_correlated_noise": calibration,
            "near_zero_denominator_era": _recent_era_note(cells_by_era),
            "block_length_neighbours": {
                "description": (
                    "The frozen 12-month block, the predeclared 6- and 24-month "
                    "neighbours, and the corrected Politis-White automatic length, for "
                    "every primary cell in the two falsifier eras."
                ),
                "rows": [
                    {
                        "cell": cell.key,
                        "intervals_by_block_length": [
                            {
                                "block_length": item.block_length,
                                "source": item.block_length_source,
                                "two_sided_90": [item.lower_90, item.upper_90],
                                "unstable": item.unstable,
                            }
                            for item in (cell.capture_interval, *cell.neighbour_intervals)
                        ],
                    }
                    for era in FALSIFIER_ERAS
                    for cell in cells_by_era[era]
                    if cell.definition.in_primary_family
                ],
            },
        },
    }

    caveats = (
        "THE CAPTURE FRACTION IS NOT ONE NUMBER. It is a ratio whose numerator "
        "depends entirely on which benchmark is subtracted, and the five defensible "
        "benchmarks predeclared here do not agree. Any figure taken from this "
        "experiment must carry the benchmark that produced it, and the size-neutral "
        "one is the only one entitled to be called a VALUE capture, because every "
        "other member of the family also contains the return to weighting small and "
        "big equally against a market that is overwhelmingly big.",
        "These are research portfolios and not products. They carry no fee, no "
        "spread, no tax and no capacity limit, they are reconstituted on a schedule "
        "no fund follows, and the smallest of them are dominated by stocks a retail "
        "investor cannot buy in size. Every figure here is gross and is an UPPER "
        "BOUND of unknown tightness.",
        "The long legs read here are TOTAL returns, so the market comparator is "
        "Mkt-RF + RF and not Mkt-RF. Subtracting a market factor already net of the "
        "one-month bill would have understated the benchmark by the entire bill rate "
        "and flattered every capture fraction in this experiment.",
        "A capture fraction is a ratio of two means and has no finite variance when "
        "its denominator can approach zero. That is Fieller's problem and it is not "
        "solved here, only reported: every interval carries the count of resamples in "
        "which the denominator went near zero or changed sign, and an interval so "
        "marked may not be quoted without the mark.",
        "The near-one-half size-neutral reading is STRUCTURAL, not empirical. The "
        "long leg is one half of a symmetric three-bucket spread, so subtracting the "
        "equal-weighted six recovers close to half the spread almost whatever the "
        "data do. It is reported as the defensible value capture precisely because it "
        "is the definition that contains nothing but book-to-market, and its "
        "structural character is the reason it is stable, not a reason to distrust it.",
        "The cost column is an illustration. Only the 50/50 rebalance turnover is "
        "measured; the fee and the internal reconstitution turnover of the sorts are "
        "ASSUMED, and turnover cannot be recovered from a return series at all.",
        "The regional legs use the ex-US files. The Developed files INCLUDE the "
        "United States and cannot be an ex-US check. There is no emerging "
        "25-portfolio file, so there is no emerging small-value corner to test.",
        "Momentum and value are not comparable on turnover. The prior-return sort is "
        "reconstituted monthly and the book-to-market sort annually, so their capture "
        "fractions describe portfolios with an order of magnitude difference in "
        "trading, and this experiment prices neither.",
        "Nothing here establishes that a long-only tilt is worth holding. The capture "
        "fraction is one term of `premium x delivered loading x capture - cost`, and "
        "this experiment measures that term and nothing else.",
    )

    return ExperimentResult(
        status=verdict.status,
        summary=_summary_line(verdict, cells_by_era, settings),
        estimates=_estimates_for(cells_by_era, verdict),
        diagnostics=diagnostics,
        caveats=caveats,
        frames=_frames(cells_by_era, checks),
    )


def _leg_symmetry(cells_by_era: Mapping[str, Sequence[CaptureCell]]) -> JsonValue:
    """The long and short shares of a symmetric spread must sum to one."""
    rows: list[JsonValue] = []
    for era, cells in cells_by_era.items():
        long_leg = next(
            (c for c in cells if c.definition.identifier == SIZE_NEUTRAL), None
        )
        short_leg = next(
            (
                c
                for c in cells
                if c.definition.identifier == "growth_halves_short_leg_vs_size_neutral"
            ),
            None,
        )
        if long_leg is None or short_leg is None:
            continue
        total = long_leg.capture_fraction + short_leg.capture_fraction
        rows.append(
            {
                "era": era,
                "long_leg_share": _json_float(long_leg.capture_fraction),
                "short_leg_share": _json_float(short_leg.capture_fraction),
                "sum": _json_float(total),
                "deviation_from_one": _json_float(total - 1.0),
            }
        )
    return {
        "description": (
            "By construction the long leg's share against the equal-weighted six and "
            "the short leg's share against the same benchmark must sum to exactly one, "
            "because their difference is the spread and their benchmark cancels. A "
            "deviation is a defect in this experiment, not a finding about the data."
        ),
        "rows": rows,
    }


def _recent_era_note(cells_by_era: Mapping[str, Sequence[CaptureCell]]) -> JsonValue:
    """What a near-zero denominator does to a ratio, shown rather than asserted."""
    if "recent" not in cells_by_era:
        return {"available": False}
    rows = [
        {
            "definition": cell.definition.identifier,
            "capture_fraction": _json_float(cell.capture_fraction),
            "two_sided_90": [
                _json_float(cell.capture_interval.lower_90),
                _json_float(cell.capture_interval.upper_90),
            ],
            "denominator_annualised_percent": cell.denominator_annual_percent,
            "unstable": cell.capture_interval.unstable,
            "near_zero_denominator_resamples": (
                cell.capture_interval.near_zero_denominator_resamples
            ),
            "sign_flipped_denominator_resamples": (
                cell.capture_interval.sign_flipped_denominator_resamples
            ),
        }
        for cell in cells_by_era["recent"]
    ]
    return {
        "description": (
            "Experiment 001 measured US HML at -0.44 pp/yr over 2016-01..2025-12. A "
            "capture fraction whose denominator is that close to zero is a number "
            "without meaning, and the specification excluded this era from the "
            "falsifier in advance for that reason. It is computed and shown so that a "
            "reader can see directly what a near-zero denominator does, rather than "
            "being told."
        ),
        "available": True,
        "rows": rows,
    }


#: Terms quoted from other experiments' published results rather than recomputed
#: here. Each is labelled with where it came from, because a number that entered
#: this module by hand is a cross-reference and not a measurement, and the chain
#: below is arithmetic on cross-references plus the one term this experiment
#: actually measures.
_QUOTED_PREMIA: Final[Mapping[str, tuple[float, str]]] = {
    "pooled_three_region": (
        4.74,
        "Experiment 005's pooled post-publication HML across the US, developed-ex-US "
        "and emerging files, +4.74 pp/yr. QUOTED, not recomputed here.",
    ),
}

_QUOTED_LOADINGS: Final[Mapping[str, float]] = {
    "VTV large value": 0.337,
    "IWD large value": 0.350,
    "IWN small value": 0.392,
    "VBR small value": 0.410,
    "TILT multifactor": 0.148,
}


def _edge_chain(
    cells_by_era: Mapping[str, Sequence[CaptureCell]], settings: InferenceSettings
) -> JsonValue:
    """`premium x delivered loading x capture - cost`, with the middle term supplied.

    The premium and the loadings are QUOTED from Experiments 005 and 002 and are
    labelled as such; the capture fraction is the term this experiment measures.
    The measured US post-publication HML is carried beside the pooled figure so
    that a reader can see how much of the chain rests on the two non-US regions.
    """
    rows: list[JsonValue] = []
    pooled_premium, pooled_note = _QUOTED_PREMIA["pooled_three_region"]
    measured_us = next(
        cell.denominator_annual_percent
        for cell in cells_by_era["hml_full_post_publication"]
        if cell.definition.identifier == SIZE_NEUTRAL
    )
    for era in FALSIFIER_ERAS:
        for cell in cells_by_era[era]:
            if not cell.definition.in_primary_family:
                continue
            for product, loading in _QUOTED_LOADINGS.items():
                rows.append(
                    {
                        "era": era,
                        "capture_definition": cell.definition.identifier,
                        "product": product,
                        "delivered_loading_quoted_from_exp_002": loading,
                        "capture_fraction_measured_here": _json_float(cell.capture_fraction),
                        "pooled_premium_quoted_from_exp_005": pooled_premium,
                        "on_pooled_premium_percent_per_year": _json_float(
                            pooled_premium * loading * cell.capture_fraction
                        ),
                        "us_only_premium_measured_here": measured_us,
                        "on_us_only_premium_percent_per_year": _json_float(
                            measured_us * loading * cell.capture_fraction
                        ),
                    }
                )
    return {
        "description": (
            "Experiment 002's chain `premium x delivered loading - cost` with the "
            "middle term this experiment supplies inserted: "
            "`premium x delivered loading x capture - cost`. Two premia are carried "
            "side by side and never averaged: the pooled three-region figure quoted "
            "from Experiment 005, and the US-only post-publication HML measured here "
            "from the pinned file. The gap between the two columns is how much of the "
            "chain rests on the two non-US regions, where shorting is hardest and no "
            "product in Experiment 002's shelf operates."
        ),
        "pooled_premium_provenance": pooled_note,
        "loadings_provenance": (
            "Experiment 002's measured sign-adjusted HML loadings for four products on "
            "its screened shelf. QUOTED, not recomputed here."
        ),
        "us_only_premium_provenance": (
            "The HML this experiment reconstructed from the pinned six portfolios over "
            "1994-01..2025-12, which is the denominator of its own capture fractions."
        ),
        "assumed_capture_this_replaces": settings.assumed_capture,
        "why_it_matters": (
            "The edge decomposition budgets 21 bp/yr for the factor line as "
            "6.6%/yr gross long-short x 0.42 post-publication retention x 0.40 "
            "long-only capture x 0.30 portfolio exposure, minus 12 bp of incremental "
            "fee. The 0.40 is the term measured here, and it was assumed rather than "
            "established."
        ),
        "cost_is_not_in_this_arithmetic": (
            "These rows are the product of three terms and stop there. The fourth "
            "term, cost, is in the `costs` block and is deliberately not subtracted "
            "here, because folding it in would produce a net figure from two quoted "
            "numbers and two assumed turnovers."
        ),
        "rows": rows,
    }


def build_registry() -> ExperimentRegistry:
    """A registry holding exactly this experiment."""
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return _workspace_root() / "experiments" / "exp_007_longonly_capture.yaml"


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    lines = [result.summary, "", "RECONSTRUCTION (clause 0)"]
    lines.append(f"{'identity':<52}{'n':>6}{'max|res| pp/m':>15}{'tol':>10}{'pass':>7}")
    checks = result.diagnostics.get("reconstruction_checks")
    if isinstance(checks, Sequence) and not isinstance(checks, str):
        for item in checks:
            if not isinstance(item, Mapping):
                continue
            expected = "" if item.get("expected_to_pass") else "  (not required)"
            lines.append(
                f"{item.get('identity')!s:<52}"
                f"{int(str(item.get('months'))):>6}"
                f"{float(str(item.get('max_absolute_residual_percentage_points_per_month'))):>15.5f}"
                f"{float(str(item.get('tolerance_decimal_per_month'))) * 100:>10.5f}"
                f"{item.get('passed')!s:>7}{expected}"
            )

    lines.extend(["", "CAPTURE FRACTION, by definition and era"])
    lines.append(
        f"{'definition':<44}{'era':<28}{'n':>5}{'capture':>9}{'90% low':>9}"
        f"{'90% high':>10}{'excess':>9}{'HML':>8}{'unst':>6}"
    )
    cells = result.diagnostics.get("capture_cells")
    if isinstance(cells, Sequence) and not isinstance(cells, str):
        for item in cells:
            if not isinstance(item, Mapping):
                continue
            interval = item.get("capture_interval")
            bounds = interval.get("two_sided_90") if isinstance(interval, Mapping) else None
            low, high = (
                (float(str(bounds[0])), float(str(bounds[1])))
                if isinstance(bounds, Sequence) and not isinstance(bounds, str)
                else (float("nan"), float("nan"))
            )
            unstable = (
                "YES"
                if isinstance(interval, Mapping) and interval.get("unstable")
                else ""
            )
            star = "*" if item.get("in_primary_family") else " "
            lines.append(
                f"{star}{item.get('definition')!s:<43}{item.get('era')!s:<28}"
                f"{int(str(item.get('months'))):>5}"
                f"{float(str(item.get('capture_fraction'))):>9.3f}"
                f"{low:>9.3f}{high:>10.3f}"
                f"{float(str(item.get('long_only_excess_spread_percent_per_year'))):>9.2f}"
                f"{float(str(item.get('denominator_annualised_percent'))):>8.2f}"
                f"{unstable:>6}"
            )
    lines.append("  * = member of the predeclared five-definition family clause (1) reads")

    verdict = result.diagnostics.get("verdict")
    if isinstance(verdict, Mapping):
        lines.extend(["", f"VERDICT: {verdict.get('status')}"])
        spread = verdict.get("definitional_spread_by_era")
        if isinstance(spread, Mapping):
            for era, value in spread.items():
                lines.append(f"  definitional spread, {era}: {float(str(value)):.3f}")
        fired = verdict.get("clause_1_definitional_spread_rejects_well_definedness")
        lines.append(f"  clause (1) rejected: {fired}")
        lines.append(f"  clause (2): {verdict.get('clause_2_level_against_the_assumed_capture')}")
        lines.append(f"  {verdict.get('reasoning')}")
        if verdict.get("what_would_fire"):
            lines.append(f"  WOULD FIRE: {verdict.get('what_would_fire')}")

    corner = result.diagnostics.get("small_value_corner")
    if isinstance(corner, Mapping):
        lines.extend(["", "SMALL-VALUE CORNER (5x5)"])
        shares = corner.get("capitalisation_and_firm_count_shares")
        if isinstance(shares, Mapping):
            cell_share = shares.get("small_value_corner_cell")
            quintile = shares.get("smallest_size_quintile")
            if isinstance(cell_share, Mapping):
                lines.append(
                    f"  ME1 x BM5 cell: "
                    f"{float(str(cell_share.get('final_share_of_firm_count_percent'))):.2f}% of "
                    f"listed firms, "
                    f"{float(str(cell_share.get('final_share_of_market_cap_percent'))):.3f}% "
                    "of market capitalisation, at the last month of the window"
                )
            if isinstance(quintile, Mapping):
                lines.append(
                    f"  whole ME1 quintile: "
                    f"{float(str(quintile.get('final_share_of_firm_count_percent'))):.2f}% of "
                    f"firms, "
                    f"{float(str(quintile.get('final_share_of_market_cap_percent'))):.3f}% of "
                    "capitalisation"
                )
        depends = corner.get("dependence_on_the_smallest_quintile")
        if isinstance(depends, Mapping):
            lines.append(
                f"  corner excess with ME1 "
                f"{float(str(depends.get('with_me1_spread_percent_per_year'))):+.2f} pp/yr, "
                f"without ME1 "
                f"{float(str(depends.get('without_me1_spread_percent_per_year'))):+.2f}, "
                f"difference "
                f"{float(str(depends.get('difference_percent_per_year'))):+.2f}"
            )
        risks = corner.get("risk")
        if isinstance(risks, Sequence) and not isinstance(risks, str):
            lines.append(
                f"  {'portfolio':<24}{'geo%':>8}{'vol%':>8}{'maxDD%':>9}{'TUW':>6}"
            )
            for item in risks:
                if isinstance(item, Mapping):
                    lines.append(
                        f"  {item.get('portfolio')!s:<24}"
                        f"{float(str(item.get('geometric_annual_percent'))):>8.2f}"
                        f"{float(str(item.get('volatility_annual_percent'))):>8.2f}"
                        f"{float(str(item.get('max_drawdown_percent'))):>9.1f}"
                        f"{int(str(item.get('max_time_under_water_months'))):>6}"
                    )
        loadings = corner.get("factor_loadings")
        if isinstance(loadings, Sequence) and not isinstance(loadings, str):
            lines.append(f"  {'portfolio':<24}{'alpha%':>9}{'Mkt':>8}{'SMB':>8}{'HML':>8}")
            for item in loadings:
                if isinstance(item, Mapping):
                    lines.append(
                        f"  {item.get('portfolio')!s:<24}"
                        f"{float(str(item.get('alpha_percent_per_year'))):>9.2f}"
                        f"{float(str(item.get('beta_mkt_rf'))):>8.3f}"
                        f"{float(str(item.get('loading_smb'))):>8.3f}"
                        f"{float(str(item.get('loading_hml'))):>8.3f}"
                    )

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
    """Run Experiment 007 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_007_longonly_capture",
        description=(
            "Measure what fraction of the HML long-short premium a long-only value "
            "tilt delivers, under every defensible benchmark, and price the "
            "small-value corner, writing a ledger entry for the attempt."
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
                "exp_007_longonly_capture"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
