"""Experiment 006: regional replication of the post-publication momentum premium.

Experiment 005 pooled HML, RMW and CMA across the US, developed-ex-US and
emerging Ken French files and resolved all three. It could not touch UMD, and it
recorded why: "the Ken French dataset registry in this repository holds exactly
one momentum file ... which is US only". That was **true of this repository and
false of the data**. Ken French publishes ``Developed_Mom_Factor_CSV.zip``,
``Developed_ex_US_Mom_Factor_CSV.zip`` and ``Emerging_MOM_Factor_CSV.zip``, all
monthly, all beginning before UMD's 1994-01 post-publication boundary. They had
never been downloaded. This experiment registers, pins and manifests them, and
runs Experiment 005's design on UMD unchanged.

Deliberate reuse, not reimplementation
--------------------------------------
The cross-region joint block bootstrap, the pooled cell, the four
effective-sample-size definitions and the two-branch falsifier are **imported
from** :mod:`~portfolio_edge.experiments.exp_005_regional_replication` rather than
written again, and every per-region statistic comes from
:func:`~portfolio_edge.experiments.exp_001_factor_decay.compute_cell`. That is
what makes these numbers comparable to both published grids cell for cell. The
one place this module adds machinery is the momentum-specific crash test below.

Why momentum needs a test the other factors did not
---------------------------------------------------
Daniel and Moskowitz (2016) show momentum crashes are **state-dependent**: they
occur in market rebounds after bear markets, when the short leg has become a
portfolio of high-beta distressed stocks. Bear markets and their rebounds are
global. If the three regional momentum series crash in the *same* months, they
are markedly fewer than three independent looks in exactly the tail that decides
whether the premium is worth holding, and a mean correlation computed over all
months understates that. The predeclared crash block measures it directly, and
compares the measured tail correlation with what the identical selection produces
from a Gaussian panel of the same covariance, so that the selection artefact is
separated from genuine tail dependence.

Three constraints inherited from upstream
-----------------------------------------
1. **No momentum file, in any region, has ever been gated against a printed
   table.** Every volatility, Sharpe ratio and minimum detectable effect here
   rests on an **unmeasured** second moment. That is weaker than a band of zero
   and the output says so rather than quoting agreement.
2. **Power is the point.** Every cell reports what it could have detected, and
   every pooled cell reports the effective sample size it actually achieved.
3. **Cost is a function of turnover, not a number.** The academic long-short
   momentum factor rebalances monthly; a long-only product does not. Applying the
   first one's turnover to the second overstates cost by about an order of
   magnitude, and this module refuses to do it.

Run it::

    uv run python -m portfolio_edge.experiments.exp_006_regional_momentum --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.core.costs import (
    K_FLOOR,
    K_PESSIMISTIC,
    MAX_RETAIL_MONTHLY_TURNOVER_PCT,
    TurnoverCostModel,
    is_retail_implementable,
)
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
    window_series,
)
from portfolio_edge.experiments.exp_005_regional_replication import (
    ERA_ROLES,
    REGIONS,
    AlignedPanel,
    BootstrapSummary,
    FamilyInference,
    PooledCell,
    RegionalGridCell,
    align_panel,
    apply_rejection_rule,
    calendar_year_contributions,
    compute_pooled,
    correct_family,
    cross_region_bootstrap,
    effective_sample_size,
    pooled_composite,
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

__all__ = [
    "CARHART_ALTERNATIVE_END",
    "CARHART_ALTERNATIVE_START",
    "ENTRY_POINT",
    "FACTOR",
    "NAMED_BEST_YEAR",
    "NAMED_CRASH_YEAR",
    "RegionalMomentumError",
    "build_registry",
    "co_extreme_rate",
    "cost_sensitivity",
    "crash_alignment",
    "default_specification_path",
    "drop_calendar_year",
    "main",
    "resolve_grid",
    "run",
    "tail_correlation",
    "verify_momentum_coverage",
]

ENTRY_POINT: Final = "exp_006_regional_momentum"

#: The single factor under test. Everything else in the grid is a region or an era.
FACTOR: Final = "UMD"

#: The calendar year Experiment 001 measured as UMD's best US post-publication
#: year. Named in the frozen specification and evaluated in every region *by
#: name*, so the episode test cannot be fitted after the fact.
NAMED_BEST_YEAR: Final = "1999"

#: The momentum crash. Experiment 001 measured UMD's worst US post-publication
#: rolling year as -56.6% over 2008-12..2009-11, the episode Daniel and Moskowitz
#: (2016) study. Named in advance for the same reason.
NAMED_CRASH_YEAR: Final = "2009"

#: Experiment 001's predeclared alternative momentum publication date, the first
#: January after Carhart (1997). Copied from ``umd_post_carhart_alternative`` in
#: ``exp_001_factor_decay.yaml``; a committed test compares the two so it cannot
#: drift. It is a hostile test here and is never substituted for the primary era.
CARHART_ALTERNATIVE_START: Final = "1998-01"
CARHART_ALTERNATIVE_END: Final = "2025-12"

MONTHS_PER_YEAR: Final = 12.0

#: Harvey, Liu and Zhu (2016)'s structural estimate of the mean return of a
#: genuinely true factor, 0.55%/month gross at an imposed 15% volatility.
TRUE_FACTOR_REFERENCE_ANNUAL_PERCENT: Final = 6.6

#: The fraction of pooled months treated as the crash tail, and the number of
#: individual worst months listed. Both are frozen here rather than chosen after
#: looking at the series.
TAIL_FRACTION: Final = 0.10
WORST_MONTHS_LISTED: Final = 10

FloatArray = NDArray[np.float64]


class RegionalMomentumError(RuntimeError):
    """The experiment could not be attempted against the declared vintages."""


def _json_float(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``."""
    return None if math.isnan(value) or math.isinf(value) else value


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise RegionalMomentumError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise RegionalMomentumError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise RegionalMomentumError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise RegionalMomentumError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise RegionalMomentumError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _integer(data: Mapping[str, JsonValue], key: str, *, where: str) -> int:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RegionalMomentumError(f"{where}.{key} must be an integer, got {value!r}")
    return value


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    return tuple(str(item) for item in items)


def _floats(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[float, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[float] = []
    for index, item in enumerate(items):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise RegionalMomentumError(f"{where}.{key}[{index}] must be a number, got {item!r}")
        out.append(float(item))
    return tuple(out)


def _integers(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[int, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[int] = []
    for index, item in enumerate(items):
        if isinstance(item, bool) or not isinstance(item, int):
            raise RegionalMomentumError(f"{where}.{key}[{index}] must be an integer, got {item!r}")
        out.append(item)
    return tuple(out)


# --------------------------------------------------------------------------- #
# The grid
# --------------------------------------------------------------------------- #


def resolve_grid(specification: Specification) -> tuple[RegionalGridCell, ...]:
    """Build the predeclared 1 x 3 x 3 grid from the frozen specification.

    The family is read from the frozen document rather than constructed here, so
    that the multiple-testing correction applies to what was declared and not to
    whatever the code happened to loop over.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    grid = _mapping(_at(parameters, "primary_grid", where="parameters"), where="primary_grid")
    roles = _strings(grid, "era_roles", where="primary_grid")
    if roles != ERA_ROLES:
        raise RegionalMomentumError(
            f"primary_grid.era_roles is {roles}, but this module implements {ERA_ROLES}"
        )
    regions = _strings(grid, "regions", where="primary_grid")
    if regions != REGIONS:
        raise RegionalMomentumError(
            f"primary_grid.regions is {regions}, but this module implements {REGIONS}"
        )
    cells_by_factor = _mapping(_at(grid, "cells", where="primary_grid"), where="primary_grid.cells")
    if set(cells_by_factor) != {FACTOR}:
        raise RegionalMomentumError(
            f"primary_grid.cells names {sorted(cells_by_factor)}; this experiment tests "
            f"{FACTOR} and nothing else"
        )
    by_role = _mapping(cells_by_factor[FACTOR], where=f"primary_grid.cells.{FACTOR}")
    eras = {era.name: era for era in specification.sample_policy.eras}

    cells: list[RegionalGridCell] = []
    for role in ERA_ROLES:
        era_name = _text(by_role, role, where=f"primary_grid.cells.{FACTOR}")
        era = eras.get(era_name)
        if era is None:
            raise RegionalMomentumError(
                f"primary_grid.cells.{FACTOR}.{role} names era {era_name!r}, which "
                f"sample_policy does not define; known: {sorted(eras)}"
            )
        for region in REGIONS:
            cells.append(
                RegionalGridCell(
                    factor=FACTOR,
                    region=region,
                    era_role=role,
                    era_name=era.name,
                    start=era.start,
                    end=era.end,
                )
            )
    expected = len(ERA_ROLES) * len(REGIONS)
    if len(cells) != expected:
        raise RegionalMomentumError(f"expected {expected} cells, built {len(cells)}")
    return tuple(cells)


# --------------------------------------------------------------------------- #
# Loading the pinned sources
# --------------------------------------------------------------------------- #


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def _series_from_table(
    table: ParsedTable, *, source_column: str, dataset_id: str
) -> MonthlySeries:
    """Pull one column out under the name UMD, dropping months the file omits.

    The US file calls the series ``Mom`` and both international files call it
    ``WML``. The rename to ``UMD`` is the same one Experiment 001 made, and the
    source column comes from the frozen specification rather than from a guess.
    """
    if source_column not in table.columns:
        raise RegionalMomentumError(
            f"column {source_column!r} is absent from table {table.table_id!r} of "
            f"{dataset_id}; found {list(table.columns)}"
        )
    raw = table.column(source_column)
    periods: list[str] = []
    values: list[float] = []
    for period, value in zip(table.periods, raw, strict=True):
        if value is None:
            continue
        periods.append(period)
        values.append(value)
    return MonthlySeries(
        name=FACTOR,
        periods=tuple(periods),
        values=np.asarray(values, dtype=np.float64),
        source_dataset_id=dataset_id,
        source_column=source_column,
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
) -> tuple[dict[str, MonthlySeries], list[JsonValue]]:
    """Fetch, pin, parse and validate all three regional momentum files.

    A hash mismatch ABORTS. Ken French rebuilds the whole history from each new
    vintage, so an unrecognised hash is a new vintage, and a premium computed from
    an unrecognised file looks exactly like a good one.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="parameters.source_pin")
    entries = _sequence(_at(pin, "series", where="source_pin"), where="source_pin.series")

    cache = RawCache()
    by_region: dict[str, MonthlySeries] = {}
    provenance: list[JsonValue] = []

    for index, item in enumerate(entries):
        where = f"source_pin.series[{index}]"
        spec_entry = _mapping(item, where=where)
        region = _text(spec_entry, "region", where=where)
        if region not in REGIONS:
            raise RegionalMomentumError(
                f"{where}.region is {region!r}, which is not one of {REGIONS}"
            )
        dataset = french.get_dataset(_text(spec_entry, "dataset_id", where=where))
        cached = french.download(cache, dataset)

        expected_raw = _text(spec_entry, "expected_sha256_raw", where=where)
        if cached.sha256 != expected_raw:
            raise RegionalMomentumError(
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
            raise RegionalMomentumError(
                f"{dataset.dataset_id} failed validation before any statistic was "
                "computed: " + "; ".join(report.summary())
            )
        expected_normalized = _text(spec_entry, "expected_sha256_normalized", where=where)
        if table.sha256_normalized() != expected_normalized:
            raise RegionalMomentumError(
                f"the derived table for {dataset.dataset_id} hashes to "
                f"{table.sha256_normalized()}, but the specification pins "
                f"{expected_normalized}. The raw bytes matched, so the parser changed "
                "behaviour. That is a finding, not a hash to update."
            )
        expected_rows = _integer(spec_entry, "expected_rows", where=where)
        if table.rows != expected_rows:
            raise RegionalMomentumError(
                f"{dataset.dataset_id} holds {table.rows} monthly rows, not the pinned "
                f"{expected_rows}"
            )
        expected_first = _text(spec_entry, "expected_first_observation", where=where)
        if table.first_observation != expected_first:
            raise RegionalMomentumError(
                f"{dataset.dataset_id} begins {table.first_observation}, not the pinned "
                f"{expected_first}"
            )

        manifest_hash: str | None = None
        manifest_path = _workspace_root() / _text(spec_entry, "committed_manifest", where=where)
        if manifest_path.is_file():
            manifest = read_manifest(manifest_path)
            manifest_hash = manifest.sha256_manifest()
            if manifest.sha256_raw != expected_raw:
                raise RegionalMomentumError(
                    f"{manifest_path} records sha256_raw {manifest.sha256_raw}, which is "
                    f"not the pinned {expected_raw}"
                )

        source_column = _text(spec_entry, "source_column", where=where)
        by_region[region] = _series_from_table(
            table, source_column=source_column, dataset_id=dataset.dataset_id
        )
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
                "frequency": table.frequency,
                "columns": list(table.columns),
                "source_column": source_column,
                "renamed_to": FACTOR,
                "rows_in_file": table.rows,
                "first_observation": table.first_observation,
                "last_observation": table.last_observation,
                "source_units": table.source_units,
                "units": table.units,
                "unit_transform": table.unit_transform,
                "gated_against_a_printed_table": False,
                "preamble": parsed.preamble.strip(),
                "validation_findings": list(report.summary()),
            }
        )

    missing = [region for region in REGIONS if region not in by_region]
    if missing:
        raise RegionalMomentumError(f"the specification pinned no file for region(s) {missing}")
    return by_region, provenance


def verify_momentum_coverage(
    series: Mapping[str, MonthlySeries], grid: Sequence[RegionalGridCell]
) -> JsonValue:
    """Check, from the loaded data, that no region starts after an era it must cover.

    Experiment 005 stated that UMD could not be tested because no regional
    momentum file exists. This function tests the corrected claim against the
    files themselves rather than restating it, and ABORTS on a silently truncated
    window, which would otherwise look exactly like a shorter one.
    """
    rows: list[JsonValue] = []
    problems: list[str] = []
    for cell in sorted(grid, key=lambda item: (item.region, item.era_name)):
        first = series[cell.region].first_observation or "9999-99"
        covered = month_index(first) <= month_index(cell.start)
        if not covered:
            problems.append(
                f"{cell.region} starts {first}, after era {cell.era_name} starts {cell.start}"
            )
        rows.append(
            {
                "region": cell.region,
                "factor": FACTOR,
                "first_observation": first,
                "era": cell.era_name,
                "era_start": cell.start,
                "covered": covered,
                "months_of_head_room": month_count(first, cell.start) - 1,
            }
        )
    if problems:
        raise RegionalMomentumError(
            "a region does not reach back to the start of an era it must cover, so the "
            "window would be silently truncated: " + "; ".join(problems)
        )
    return {
        "claim_tested": (
            "Experiment 005 reported that UMD 'could not be tested because no regional "
            "momentum file exists in this repository'."
        ),
        "verdict": (
            "TRUE of the repository at the time and FALSE of the data. Ken French "
            "publishes three regional momentum files, all monthly. This experiment "
            "downloaded, pinned and manifested them. Both non-US files begin before "
            "UMD's 1994-01 post-publication boundary, so the regional windows are "
            "exactly as long as the US one. They begin later than the corresponding "
            "five-factor files because a 2-12 month prior return cannot be formed "
            "until twelve months of history exist."
        ),
        "checked_against": "the loaded series, not this text",
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# Episode and crash concentration
# --------------------------------------------------------------------------- #


def _annualised_premium_percent(series: FloatArray) -> float:
    return float(np.mean(series)) * MONTHS_PER_YEAR * 100.0


def _calendar_year_total(values: FloatArray, periods: Sequence[str], year: str) -> float:
    mask = np.asarray([period[:4] == year for period in periods], dtype=bool)
    if not mask.any():
        return float("nan")
    return float(np.prod(1.0 + values[mask]) - 1.0)


def drop_calendar_year(
    values: FloatArray, periods: Sequence[str], *, best: bool
) -> tuple[FloatArray, str | None]:
    """Drop the single best or single worst compounded calendar year.

    ``best=True`` reproduces Experiment 005's clause (a5) helper exactly; the
    ``best=False`` branch is the momentum-specific mirror image, because for
    momentum the year that decides whether the premium is holdable is the crash
    year and not the winning one.
    """
    years = sorted({period[:4] for period in periods})
    if len(years) < 2:
        return values, None
    chosen: str | None = None
    extreme = -math.inf if best else math.inf
    for year in years:
        total = _calendar_year_total(values, periods, year)
        if (best and total > extreme) or (not best and total < extreme):
            extreme, chosen = total, year
    keep = np.asarray([period[:4] != chosen for period in periods], dtype=bool)
    return values[keep], chosen


def tail_correlation(panel: FloatArray, composite: FloatArray, *, fraction: float) -> float:
    """Mean pairwise cross-region correlation on the worst ``fraction`` of months.

    **Meaningless on its own, and not in the direction most readers expect.**
    The composite is the sum of the regions, so conditioning on it being extreme
    conditions on a *collider*: given that the sum is very negative, the regions
    trade off against one another, and the within-tail sample correlation is
    pushed **down**, not up. On a matched Gaussian panel the artefact is worth
    several tenths of a correlation unit. The figure is therefore reported only
    beside the same statistic computed from a zero-mean Gaussian panel of the
    identical covariance under the identical selection, and only the gap between
    them carries information.

    :func:`co_extreme_rate` is the cleaner reading and does not condition on a
    collider; both are reported.
    """
    months, regions = panel.shape
    if regions < 2:
        return float("nan")
    count = max(regions + 1, round(months * fraction))
    if count >= months:
        return float("nan")
    order = np.argsort(composite)[:count]
    subset = panel[order]
    if float(np.min(np.var(subset, axis=0, ddof=1))) <= 0.0:
        return float("nan")
    matrix = np.atleast_2d(np.asarray(np.corrcoef(subset, rowvar=False), dtype=np.float64))
    upper = matrix[np.triu_indices(regions, k=1)]
    return float(np.mean(upper)) if upper.size else float("nan")


def co_extreme_rate(panel: FloatArray, *, fraction: float) -> tuple[float, float]:
    """How often all regions are in their **own** worst ``fraction`` in one month.

    Returns ``(measured_rate, rate_under_independence)``. Each region's tail is
    defined by its own quantile, so nothing is conditioned on a sum and the
    collider that distorts :func:`tail_correlation` does not arise. Under
    independence the rate is ``fraction ** regions``; a measured rate well above
    it is direct evidence that the regions crash in the same months.
    """
    months, regions = panel.shape
    if months < 1 or regions < 1:
        return (float("nan"), float("nan"))
    thresholds = np.quantile(panel, fraction, axis=0)
    together = np.all(panel <= thresholds, axis=1)
    return (float(np.mean(together)), float(fraction**regions))


def crash_alignment(
    panel: AlignedPanel, weights: FloatArray, *, rng: np.random.Generator
) -> JsonValue:
    """Do the three regional momentum series crash together?

    Five readings, none of which enters the falsifier:

    1. the worst calendar year of each region and of the pooled composite, and
       whether the regions share it;
    2. the calendar year 2009, named in advance, evaluated in every region;
    3. the ten worst pooled months, with how many regions were also negative in
       each, against the unconditional rate at which a region is negative;
    4. how often all three regions are in their **own** worst decile in the same
       month, against the rate independence would give
       (:func:`co_extreme_rate`) — the cleanest of the five, because it
       conditions on nothing;
    5. the tail correlation, against the same statistic computed from a Gaussian
       panel of matched covariance, which is the null for the selection effect.
       Reading 4 was added while implementing the frozen specification's crash
       block, before any real crash number was computed, because reading 5 alone
       conditions on a collider and is uninterpretable without its null.

    If the regions crash together, the effective sample size measured over all
    months **overstates** the independent evidence available in the tail, and the
    pooled minimum detectable effect is an upper bound on what was learned rather
    than a measurement of it.
    """
    values = panel.values
    composite = pooled_composite(values, weights)
    months, regions = values.shape

    worst_by_region: dict[str, str | None] = {}
    premium_without_worst: dict[str, float | None] = {}
    for index, region in enumerate(panel.regions):
        remaining, worst = drop_calendar_year(values[:, index], panel.periods, best=False)
        worst_by_region[region] = worst
        premium_without_worst[region] = (
            _annualised_premium_percent(remaining) if worst else None
        )
    pooled_remaining, pooled_worst = drop_calendar_year(composite, panel.periods, best=False)
    distinct = {value for value in worst_by_region.values() if value is not None}

    named: dict[str, JsonValue] = {}
    for index, region in enumerate(panel.regions):
        contributions = calendar_year_contributions(values[:, index], panel.periods)
        entry = next((item for item in contributions if item[0] == NAMED_CRASH_YEAR), None)
        named[region] = (
            {"compounded_return": entry[1], "share_of_premium": _json_float(entry[2])}
            if entry
            else None
        )
    pooled_entry = next(
        (
            item
            for item in calendar_year_contributions(composite, panel.periods)
            if item[0] == NAMED_CRASH_YEAR
        ),
        None,
    )

    order = np.argsort(composite)[:WORST_MONTHS_LISTED]
    worst_months: list[JsonValue] = []
    for row in order:
        negatives = [
            panel.regions[column] for column in range(regions) if values[row, column] < 0.0
        ]
        worst_months.append(
            {
                "month": panel.periods[int(row)],
                "pooled_return_percent": float(composite[row]) * 100.0,
                "regions_negative": len(negatives),
                "which": negatives,
                "per_region_return_percent": {
                    panel.regions[column]: float(values[row, column]) * 100.0
                    for column in range(regions)
                },
            }
        )
    unconditional_negative_rate = {
        panel.regions[column]: float(np.mean(values[:, column] < 0.0)) for column in range(regions)
    }
    all_three_negative_rate = float(np.mean(np.all(values < 0.0, axis=1)))
    independent_all_three_rate = float(
        np.prod([unconditional_negative_rate[region] for region in panel.regions])
    )

    matrix = np.atleast_2d(np.asarray(np.corrcoef(values, rowvar=False), dtype=np.float64))
    upper = matrix[np.triu_indices(regions, k=1)]
    all_month_correlation = float(np.mean(upper)) if upper.size else float("nan")
    measured_tail = tail_correlation(values, composite, fraction=TAIL_FRACTION)
    co_extreme, co_extreme_if_independent = co_extreme_rate(values, fraction=TAIL_FRACTION)

    covariance = np.cov(values, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(np.atleast_2d(covariance))
    loading = eigenvectors @ np.diag(np.sqrt(np.clip(eigenvalues, 0.0, None)))
    synthetic_tail: list[float] = []
    synthetic_all: list[float] = []
    for _ in range(200):
        draws = np.asarray(rng.normal(size=(months, regions)) @ loading.T, dtype=np.float64)
        synthetic_tail.append(
            tail_correlation(draws, pooled_composite(draws, weights), fraction=TAIL_FRACTION)
        )
        synthetic_matrix = np.atleast_2d(
            np.asarray(np.corrcoef(draws, rowvar=False), dtype=np.float64)
        )
        synthetic_all.append(float(np.mean(synthetic_matrix[np.triu_indices(regions, k=1)])))
    synthetic_tail_array = np.asarray(synthetic_tail, dtype=np.float64)
    finite_tail = synthetic_tail_array[np.isfinite(synthetic_tail_array)]

    crash_together = bool(
        len(distinct) == 1
        or all_three_negative_rate > independent_all_three_rate * 1.5
        or co_extreme > co_extreme_if_independent * 2.0
        or (finite_tail.size > 0 and measured_tail > float(np.quantile(finite_tail, 0.95)))
    )

    return {
        "cell": f"{FACTOR}/pooled/{panel.era_name}",
        "months": months,
        "worst_calendar_year_by_region": worst_by_region,
        "premium_without_worst_calendar_year_by_region": premium_without_worst,
        "regions_share_the_same_worst_year": len(distinct) == 1,
        "distinct_worst_years": sorted(distinct),
        "pooled_worst_calendar_year": pooled_worst,
        "pooled_premium_without_worst_year": (
            _annualised_premium_percent(pooled_remaining) if pooled_worst else None
        ),
        "named_crash_year_from_daniel_moskowitz": {
            "year": NAMED_CRASH_YEAR,
            "why_this_year": (
                "Experiment 001 measured UMD's worst US post-publication rolling year "
                "as -56.6% over 2008-12..2009-11, the momentum crash Daniel and "
                "Moskowitz (2016) study. The year is named in the frozen specification "
                "and evaluated in every region BY NAME, so the test cannot be fitted."
            ),
            "per_region": named,
            "pooled": (
                {
                    "compounded_return": pooled_entry[1],
                    "share_of_premium": _json_float(pooled_entry[2]),
                }
                if pooled_entry
                else None
            ),
        },
        "worst_pooled_months": worst_months,
        "unconditional_monthly_negative_rate_by_region": unconditional_negative_rate,
        "all_three_regions_negative_rate": all_three_negative_rate,
        "all_three_negative_rate_if_independent": independent_all_three_rate,
        "mean_pairwise_correlation_all_months": _json_float(all_month_correlation),
        "mean_pairwise_correlation_worst_decile": _json_float(measured_tail),
        "all_regions_in_own_worst_decile_rate": _json_float(co_extreme),
        "all_regions_in_own_worst_decile_rate_if_independent": _json_float(
            co_extreme_if_independent
        ),
        "why_the_own_decile_rate_is_the_cleaner_reading": (
            "Each region's tail is defined by its own quantile, so nothing is "
            "conditioned on a sum. The worst-decile CORRELATION below conditions on the "
            "composite, which is a collider: given that the sum is extreme the regions "
            "trade off against one another and the within-tail correlation is pushed "
            "DOWN, not up. That is why it is reported only against a matched null."
        ),
        "tail_correlation_null": {
            "description": (
                "The identical worst-decile selection applied to 200 zero-mean Gaussian "
                "panels with this cell's measured covariance. Selecting on the composite "
                "is conditioning on a collider and DEPRESSES the within-tail sample "
                "correlation, so this null normally sits well below the all-month "
                "figure; only the gap between the measured tail correlation and this "
                "null carries information. The measured all-month correlation is "
                "reproduced as a check that the synthetic covariance is right."
            ),
            "synthetic_mean_tail_correlation": _json_float(
                float(np.mean(finite_tail)) if finite_tail.size else float("nan")
            ),
            "synthetic_tail_correlation_95th_percentile": _json_float(
                float(np.quantile(finite_tail, 0.95)) if finite_tail.size else float("nan")
            ),
            "synthetic_mean_all_month_correlation": _json_float(
                float(np.mean(np.asarray(synthetic_all, dtype=np.float64)))
            ),
            "n_synthetic_panels": len(synthetic_tail),
        },
        "regions_crash_together": crash_together,
        "how_that_was_decided": (
            "TRUE if any of: the three regions share the same worst calendar year; all "
            "three are negative together more than 1.5x as often as independence would "
            "imply; all three are in their OWN worst decile in the same month more than "
            "2x as often as independence would imply; or the measured worst-decile "
            "cross-region correlation exceeds the 95th percentile of the matched "
            "Gaussian null. Each component is reported above so the reader can apply a "
            "different rule."
        ),
        "consequence": (
            "This test does not enter the falsifier. It qualifies the effective sample "
            "size: if the regions crash together, the effective region count measured "
            "over ALL months OVERSTATES the independent evidence available in the tail, "
            "and the pooled minimum detectable effect is an upper bound on what was "
            "learned rather than a measurement of it."
        ),
    }


def _episode_sharing(panel: AlignedPanel, pooled: PooledCell) -> JsonValue:
    """The upside mirror of :func:`crash_alignment`, and the input to clause (a5)."""
    values = panel.values
    best_by_region: dict[str, str | None] = {}
    without_by_region: dict[str, float | None] = {}
    named: dict[str, JsonValue] = {}
    for index, region in enumerate(panel.regions):
        remaining, best = drop_calendar_year(values[:, index], panel.periods, best=True)
        best_by_region[region] = best
        without_by_region[region] = _annualised_premium_percent(remaining) if best else None
        entry = next(
            (
                item
                for item in calendar_year_contributions(values[:, index], panel.periods)
                if item[0] == NAMED_BEST_YEAR
            ),
            None,
        )
        named[region] = (
            {"compounded_return": entry[1], "share_of_premium": _json_float(entry[2])}
            if entry
            else None
        )
    distinct = {value for value in best_by_region.values() if value is not None}
    pooled_named = next(
        (item for item in pooled.year_contributions if item[0] == NAMED_BEST_YEAR), None
    )
    return {
        "cell": pooled.key,
        "best_calendar_year_by_region": best_by_region,
        "premium_without_best_calendar_year_by_region": without_by_region,
        "regions_share_the_same_best_year": len(distinct) == 1,
        "distinct_best_years": sorted(distinct),
        "pooled_best_calendar_year": pooled.best_calendar_year,
        "pooled_premium_without_best_year": pooled.premium_without_best_year,
        "named_episode_from_exp_001": {
            "year": NAMED_BEST_YEAR,
            "why_this_year": (
                "Experiment 001 measured 1999 as the calendar year whose removal cost "
                "UMD's US post-publication premium the most, taking it from +4.19 to "
                "+3.46 pp/yr. It is evaluated here BY NAME in every region rather than "
                "by whichever year turned out best, so the test cannot be fitted."
            ),
            "per_region": named,
            "pooled": (
                {
                    "compounded_return": pooled_named[1],
                    "share_of_premium": _json_float(pooled_named[2]),
                }
                if pooled_named
                else None
            ),
        },
    }


# --------------------------------------------------------------------------- #
# Cost, as a function of turnover
# --------------------------------------------------------------------------- #


def cost_sensitivity(specification: Specification) -> JsonValue:
    """Cost in pp/yr as a function of stated one-sided monthly turnover.

    Not a haircut and never subtracted from a premium. Turnover cannot be
    recovered from a return series, so a single cost figure for "momentum" does
    not exist; what exists is a schedule, plus a statement of which turnover
    assumption belongs to which object. The academic long-short factor rebalances
    monthly. A long-only product rebalancing semi-annually cannot have the same
    monthly turnover, and this function asserts no figure for it.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(
        _at(parameters, "cost_sensitivity", where="parameters"),
        where="parameters.cost_sensitivity",
    )
    grid = _floats(block, "turnover_grid_one_sided_monthly_percent", where="cost_sensitivity")
    k_optimistic = _number(block, "k_optimistic", where="cost_sensitivity")
    k_pessimistic = _number(block, "k_pessimistic", where="cost_sensitivity")
    if not math.isclose(k_optimistic, K_FLOOR) or not math.isclose(k_pessimistic, K_PESSIMISTIC):
        raise RegionalMomentumError(
            f"the frozen cost coefficients ({k_optimistic}, {k_pessimistic}) are not "
            f"core.costs' ({K_FLOOR}, {K_PESSIMISTIC}); one of the two has drifted"
        )
    optimistic = TurnoverCostModel(k=k_optimistic)
    pessimistic = TurnoverCostModel(k=k_pessimistic)

    rows: list[JsonValue] = []
    for turnover in grid:
        low = MONTHS_PER_YEAR * optimistic.cost_bp_per_period(turnover) / 100.0
        high = MONTHS_PER_YEAR * pessimistic.cost_bp_per_period(turnover) / 100.0
        rows.append(
            {
                "one_sided_monthly_turnover_percent": turnover,
                "annual_turnover_one_sided_percent": turnover * MONTHS_PER_YEAR,
                "cost_percent_per_year_at_k_1_0": low,
                "cost_percent_per_year_at_k_1_7": high,
                "inside_retail_implementability_limit": is_retail_implementable(turnover),
            }
        )

    which = _mapping(
        _at(block, "which_turnover_belongs_to_what", where="cost_sensitivity"),
        where="cost_sensitivity.which_turnover_belongs_to_what",
    )
    academic = _mapping(
        _at(which, "academic_long_short_factor", where="which_turnover_belongs_to_what"),
        where="academic_long_short_factor",
    )
    academic_turnover = _mapping(
        _at(academic, "turnover_one_sided_monthly_percent", where="academic_long_short_factor"),
        where="academic_long_short_factor.turnover",
    )
    academic_low = _number(academic_turnover, "optimistic", where="academic")
    academic_high = _number(academic_turnover, "pessimistic", where="academic")

    return {
        "description": (
            "cost_bp_per_month = k * one_sided_monthly_turnover_percent, from "
            "core.costs.TurnoverCostModel, fitted by Novy-Marx and Velikov (2016). "
            "Reported as a SCHEDULE because turnover is the input that decides cost "
            "and turnover cannot be recovered from a return series. Nothing here is "
            "subtracted from any premium."
        ),
        "k_optimistic": k_optimistic,
        "k_pessimistic": k_pessimistic,
        "retail_implementability_limit_one_sided_monthly_percent": (
            MAX_RETAIL_MONTHLY_TURNOVER_PCT
        ),
        "schedule": rows,
        "academic_long_short_factor": {
            "applies_to": (
                "the gross long-short premia this experiment reports, in all three "
                "regions"
            ),
            "one_sided_monthly_turnover_percent": [academic_low, academic_high],
            "cost_percent_per_year": [
                MONTHS_PER_YEAR * optimistic.cost_bp_per_period(academic_low) / 100.0,
                MONTHS_PER_YEAR * pessimistic.cost_bp_per_period(academic_high) / 100.0,
            ],
            "basis": str(_at(academic, "basis", where="academic_long_short_factor")).strip(),
            "status": (
                "an ASSUMPTION declared before the run, inherited from Experiment 001, "
                "not a measurement"
            ),
            "inside_retail_limit": [
                is_retail_implementable(academic_low),
                is_retail_implementable(academic_high),
            ],
        },
        "long_only_implementation": {
            "one_sided_monthly_turnover_percent": None,
            "why_none": (
                "UNMEASURED, and this experiment refuses to assert one. A long-only "
                "momentum fund rebalancing semi-annually cannot have the monthly "
                "turnover of a monthly-rebalanced long-short factor: if it turns over x "
                "percent one-sided at each of two rebalances a year, its one-sided "
                "monthly-equivalent turnover is 2x/12 = x/6. That is arithmetic, not a "
                "measurement, and x is not measured anywhere in this repository. "
                "Applying the academic long-short range of "
                f"{academic_low:.1f}-{academic_high:.1f}% per month to such a fund "
                "overstates its cost by roughly an order of magnitude, and that error "
                "has been made in this repository before."
            ),
            "read_the_schedule_instead": (
                "For any long-only turnover a reader can state, the schedule above "
                "gives the cost. The experiment supplies the function; the turnover is "
                "a separate measurement."
            ),
        },
        "published_outcome_to_keep_in_view": (
            "Novy-Marx and Velikov (2016) measure a 17% haircut in the low-turnover "
            "tier and 144% in the high-turnover tier, where four of six strategies had "
            "strictly negative net returns. The ordering of factors by GROSS premium is "
            "not their ordering by NET premium, and this experiment cannot establish "
            "the latter."
        ),
    }


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #


def _settings(specification: Specification) -> InferenceSettings:
    """Experiment 001's settings object, carrying no second-moment band at all.

    No momentum file in any region was ever gated against a printed table, so the
    band is **unmeasured** rather than zero, and ``second_moment_measured`` says
    exactly that. Experiment 001's machinery then reports the absence instead of
    quoting agreement.
    """
    parameters = _mapping(specification.parameters, where="parameters")
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
        rolling_windows_months=_integers(parameters, "rolling_windows_months", where="parameters"),
        second_moment_bands={},
        second_moment_measured={FACTOR: False},
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
        raise RegionalMomentumError(f"the frozen pooling weights sum to {total!r}, not 1.0")
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
            "Resampling the three regions with independent index draws instead of one "
            "joint draw. It is INVALID for correlated regions and is computed only so "
            "the size of the error can be shown rather than asserted. Experiment 005 "
            "measured it at roughly a factor of 1.5 on HML's interval width and found "
            "one cell where the invalid procedure excluded zero and the valid one did "
            "not."
        ),
        "rows": rows,
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
                "inverse_variance_premium": _annualised_premium_percent(
                    pooled_composite(values, inverse_weights)
                ),
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
            "genuinely independent look at the United States finding, because it shares "
            "no security with the US file."
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
    """The identical pooled procedure on a zero-mean panel of matched covariance."""
    values = panel.values
    covariance = np.cov(values, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(np.atleast_2d(covariance))
    loading = eigenvectors @ np.diag(np.sqrt(np.clip(eigenvalues, 0.0, None)))
    draws = np.asarray(
        rng.normal(size=(panel.months, values.shape[1])) @ loading.T, dtype=np.float64
    )
    composite = pooled_composite(draws, weights)
    percent = composite * 100.0
    sample = effective_sample_size(draws * 100.0, percent)
    sigma = float(np.std(percent, ddof=1))
    boot = cross_region_bootstrap(
        draws,
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
            f"cross-region covariance as {panel.factor}/{panel.era_name}, put through "
            "the identical pooled procedure. Its premium is zero by construction; "
            "whatever interval and effective sample size it produces is what this "
            "machinery produces from correlated nothing."
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


def _hostile_carhart_alternative(
    series: Mapping[str, MonthlySeries],
    *,
    weights: FloatArray,
    settings: InferenceSettings,
    rng: np.random.Generator,
) -> JsonValue:
    """The pooled full post-publication cell on Experiment 001's alternative date.

    Momentum has two candidate publication dates: Jegadeesh and Titman (1993),
    which the frozen era uses, and Carhart (1997), which is when momentum entered
    the standard factor model. Experiment 001 predeclared 1998-01 as the
    alternative and reported both. It is reported beside the primary era here and
    never substituted for it.
    """
    windows = {
        region: window_series(
            series[region], start=CARHART_ALTERNATIVE_START, end=CARHART_ALTERNATIVE_END
        )
        for region in REGIONS
    }
    panel = align_panel(
        windows,
        factor=FACTOR,
        era_name="umd_post_carhart_alternative",
        regions=REGIONS,
    )
    composite = pooled_composite(panel.values, weights)
    boot = cross_region_bootstrap(
        panel.values,
        weights,
        block_length=settings.frozen_block_length,
        block_length_source="frozen",
        n_resamples=settings.n_resamples,
        rng=rng,
        joint=True,
    )
    sample = effective_sample_size(panel.values * 100.0, composite * 100.0)
    sigma = float(np.std(composite * 100.0, ddof=1))
    return {
        "description": (
            "The pooled cell recomputed from 1998-01, the first January after Carhart "
            "(1997). Experiment 001 predeclared this alternative publication date and "
            "reported both; it is never substituted for the primary era."
        ),
        "window": f"{CARHART_ALTERNATIVE_START}..{CARHART_ALTERNATIVE_END}",
        "months": panel.months,
        "pooled_premium_percent_per_year": _annualised_premium_percent(composite),
        "two_sided_90_interval": [boot.lower_90, boot.upper_90],
        "mde_one_sided_percent_per_year": MONTHS_PER_YEAR
        * minimum_detectable_effect(
            standard_error=sigma / math.sqrt(panel.months),
            power=settings.power_target,
            one_sided=True,
        ),
        "effective_regions": _json_float(sample.effective_regions),
        "effective_region_months_iid": _json_float(sample.effective_region_months_iid),
        "per_region_premium_percent_per_year": {
            region: _annualised_premium_percent(panel.values[:, index])
            for index, region in enumerate(panel.regions)
        },
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


def _estimates_for(pooled: Sequence[PooledCell]) -> tuple[Estimate, ...]:
    estimates: list[Estimate] = []
    for cell in pooled:
        interval: BootstrapSummary = cell.joint_bootstrap
        estimates.append(
            Estimate(
                name=f"UMD pooled {cell.era_role} annualised premium",
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
                    f"gross, long-short and not investable; detectable at 80% power only "
                    f"above {cell.mde_one_sided_percent_per_year:.2f} pp/yr. Measured "
                    f"effective sample size "
                    f"{cell.sample.effective_region_months_iid:.0f} independent "
                    f"single-region months against {cell.sample.naive_region_months} if "
                    "the regions were independent. The academic construction rebalances "
                    "monthly, so this gross figure is the loosest upper bound of any "
                    "factor in this repository."
                ),
            )
        )
        regions_interval = cell.panel_interval_named("effective_regions")
        estimates.append(
            Estimate(
                name=f"UMD pooled {cell.era_role} effective regions",
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
                    f"single-region months against {cell.sample.naive_region_months} if "
                    f"the regions were independent, "
                    f"{cell.sample.effective_region_months_hac:.0f} once serial "
                    f"dependence is folded in, at a mean pairwise cross-region "
                    f"correlation of {cell.sample.mean_pairwise_correlation:.3f}. NO "
                    "momentum file in ANY region was ever gated against a printed "
                    "table, so every second moment behind this figure is UNMEASURED, "
                    "which is weaker than a band of zero."
                ),
            )
        )
        mde_interval = cell.panel_interval_named("pooled_mde_one_sided_percent_per_year")
        estimates.append(
            Estimate(
                name=f"UMD pooled {cell.era_role} minimum detectable effect",
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


def _summary_line(
    verdict_status: ResultStatus,
    branch: str,
    family: FamilyInference,
    cells: Sequence[CellStatistics],
    pooled_full: PooledCell,
    crash_together: bool,
) -> str:
    survivors = sum(1 for value in family.bh_rejected if value)
    uncorrected = sum(1 for value in family.p_values if value <= 0.05)
    underpowered = sum(
        1
        for cell in cells
        if cell.annualised_premium_percent < cell.mde_one_sided_percent_per_year
    )
    return (
        f"UMD: {verdict_status.value} under falsifier branch {branch}. Of the "
        f"{len(family.keys)} predeclared regional cells, {uncorrected} have a one-sided "
        f"HAC p-value at or below 0.05 uncorrected and {survivors} survive "
        f"Benjamini-Hochberg at {family.alpha:.2f}; {underpowered} hold a premium "
        "smaller than what their own window could detect at 80% power. Over the full "
        f"post-publication era the pooled premium is "
        f"{pooled_full.annualised_premium_percent:+.2f} pp/yr, pooling three regions "
        f"bought an effective {pooled_full.sample.effective_regions:.2f} regions out of "
        f"3 and {pooled_full.sample.effective_region_months_iid:.0f} independent "
        f"single-region months against {pooled_full.sample.naive_region_months}, leaving "
        f"a minimum detectable effect of "
        f"{pooled_full.mde_one_sided_percent_per_year:.2f} pp/yr. The three regions "
        f"{'DO' if crash_together else 'do not'} crash together. All figures are gross, "
        "long-short, monthly-rebalanced and not investable, and every second moment "
        "behind them is unmeasured."
    )


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 006."""
    parameters = _mapping(specification.parameters, where="parameters")
    materiality = _number(
        parameters, "materiality_threshold_annual_percent", where="parameters"
    )
    alpha = _number(parameters, "benjamini_hochberg_alpha", where="parameters")
    rng = context.rng

    raw, provenance = _load_sources(specification)
    sample_end = specification.sample_policy.end
    series = {
        region: _clip_to_sample_policy(item, end=sample_end) for region, item in raw.items()
    }

    grid = resolve_grid(specification)
    coverage = verify_momentum_coverage(series, grid)

    settings = _settings(specification)
    weights, weighting = _pooling_weights(specification)

    windows: dict[str, Window] = {}
    cells: list[CellStatistics] = []
    cell_regions: list[str] = []
    for item in grid:
        window = window_series(series[item.region], start=item.start, end=item.end)
        windows[item.key] = window
        cells.append(
            compute_cell(
                window,
                factor=FACTOR,
                era_role=item.era_role,
                era_name=item.era_name,
                settings=settings,
                rng=rng,
            )
        )
        cell_regions.append(item.region)

    panels: dict[str, AlignedPanel] = {}
    pooled: list[PooledCell] = []
    for role in ERA_ROLES:
        declared = next(cell for cell in grid if cell.era_role == role)
        panel = align_panel(
            {region: windows[f"{FACTOR}/{region}/{role}"] for region in REGIONS},
            factor=FACTOR,
            era_name=declared.era_name,
            regions=REGIONS,
        )
        panels[f"{FACTOR}/{role}"] = panel
        pooled.append(
            compute_pooled(
                panel,
                era_role=role,
                start=declared.start,
                end=declared.end,
                weights=weights,
                weighting=weighting,
                settings=settings,
                rng=rng,
                us_band=0.0,
            )
        )

    regional_family = correct_family(
        "regional_cells",
        [
            f"{region}/{cell.factor}/{cell.era_role}"
            for region, cell in zip(cell_regions, cells, strict=True)
        ],
        [cell.one_sided_p_value_hac for cell in cells],
        alpha=alpha,
    )
    pooled_family = correct_family(
        "pooled_cells",
        [cell.key for cell in pooled],
        [cell.one_sided_p_value_hac for cell in pooled],
        alpha=alpha,
    )

    regional_full = {
        region: cell
        for region, cell in zip(cell_regions, cells, strict=True)
        if cell.era_role == "full_post_publication"
    }
    pooled_full = next(cell for cell in pooled if cell.era_role == "full_post_publication")
    verdict = apply_rejection_rule(
        FACTOR, pooled_full, regional_full, materiality=materiality
    )

    full_panel = panels[f"{FACTOR}/full_post_publication"]
    crash_rows = [
        crash_alignment(panels[f"{FACTOR}/{role}"], weights, rng=rng) for role in ERA_ROLES
    ]
    crash_full = crash_rows[ERA_ROLES.index("full_post_publication")]
    crash_together = bool(
        isinstance(crash_full, Mapping) and crash_full.get("regions_crash_together") is True
    )

    diagnostics: dict[str, JsonValue] = {
        "sources": provenance,
        "what_this_experiment_corrects": {
            "claim": (
                "Experiment 005 and docs/research/factor-persistence.md stated that UMD "
                "could not be tested regionally because no regional momentum file "
                "exists. The narrow form was true of this repository; the broad form is "
                "false of the data."
            ),
            "files_now_registered_pinned_and_manifested": [
                {
                    "dataset_id": "french_developed_ex_us_momentum",
                    "frequency": "monthly",
                    "rows": 428,
                    "coverage": "1990-11..2026-06",
                },
                {
                    "dataset_id": "french_emerging_momentum",
                    "frequency": "monthly",
                    "rows": 438,
                    "coverage": "1990-01..2026-06",
                },
                {
                    "dataset_id": "french_developed_momentum",
                    "frequency": "monthly",
                    "rows": 428,
                    "coverage": "1990-11..2026-06",
                    "used": False,
                    "why_not": (
                        "it INCLUDES the United States, so pooling it beside the US file "
                        "would count the US twice; registered so the exclusion is a "
                        "recorded choice rather than an absence"
                    ),
                },
            ],
            "registered_french_datasets": sorted(french.DATASETS),
        },
        "sample_policy": {
            "start": specification.sample_policy.start,
            "end": sample_end,
            "held_out_after": sample_end,
            "months_available_beyond_holdout": {
                region: max(
                    0,
                    month_count(sample_end, raw[region].last_observation or sample_end) - 1,
                )
                for region in REGIONS
            },
        },
        "regional_coverage_check": coverage,
        "second_moment_status": {
            "gated_against_a_printed_table": {region: False for region in REGIONS},
            "statement": (
                "NO momentum file, in ANY region, has ever been gated against a printed "
                "table in this repository. The Phase 1 ingestion gate covered the US "
                "five-factor file, and its band applies to HML and RMW only. Every "
                "volatility, Sharpe ratio and minimum detectable effect below therefore "
                "rests on an UNMEASURED second moment. That is a weaker statement than a "
                "band of zero and must not be read as agreement."
            ),
            "consequence_for_branch_b": (
                "Branch (b) reads the pooled MDE, which is proportional to the "
                "composite's volatility. Experiment 005 could bound the effect of its "
                "band because the band was measured. Here it cannot be bounded at all, "
                "and that is reported as an unquantified sensitivity rather than omitted."
            ),
        },
        "regional_cells": [
            {"region": region, **cell.to_json()}
            for region, cell in zip(cell_regions, cells, strict=True)
        ],
        "pooled_cells": [cell.to_json() for cell in pooled],
        "inference": [regional_family.to_json(), pooled_family.to_json()],
        "verdicts": [verdict.to_json()],
        "cross_region_correlations": [
            _cross_region_correlations(panel) for panel in panels.values()
        ],
        "cost_sensitivity": cost_sensitivity(specification),
        "hostile_tests": {
            "independent_versus_joint_resampling": _hostile_independent_resampling(pooled),
            "episode_sharing_across_regions": {
                "description": (
                    "Whether the three regions share the same best calendar year, and "
                    "what the episode Experiment 001 named in the US - 1999 - did in "
                    "every region. Regions that co-move through the same episode are not "
                    "three independent looks."
                ),
                "rows": [
                    _episode_sharing(panels[f"{FACTOR}/{cell.era_role}"], cell)
                    for cell in pooled
                ],
            },
            "do_the_regions_crash_together": {
                "description": (
                    "The momentum-specific test, predeclared in the specification. "
                    "Daniel and Moskowitz (2016) show momentum crashes are "
                    "state-dependent and occur in rebounds after bear markets, which are "
                    "global events. If the regions crash together they are fewer than "
                    "three independent looks in exactly the tail that decides whether "
                    "the premium is holdable."
                ),
                "rows": crash_rows,
            },
            "alternative_pools": _hostile_alternative_pools(
                panels, settings=settings, rng=rng
            ),
            "correlated_synthetic_noise": _hostile_correlated_noise(
                full_panel, weights=weights, settings=settings, rng=rng
            ),
            "carhart_alternative_publication_date": _hostile_carhart_alternative(
                series, weights=weights, settings=settings, rng=rng
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
                    "pinned file over the same windows as Experiment 001's UMD rows, so "
                    "they must reproduce its published figures. A disagreement is a "
                    "defect here. Experiment 001 published, for UMD: first "
                    "post-publication +10.53 pp/yr at 19.70 volatility and MDE 15.49; "
                    "full post-publication +4.19 at 16.55 and MDE 7.27; recent +0.37 at "
                    "13.30 and MDE 10.46."
                ),
                "rows": [
                    {
                        "cell": f"{cell.factor}/{cell.era_role}",
                        "annualised_premium_percent": cell.annualised_premium_percent,
                        "annualised_volatility_percent": cell.annualised_volatility_percent,
                        "observations": cell.observations,
                        "mde_one_sided_percent_per_year": cell.mde_one_sided_percent_per_year,
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
        "cannot implement them at all, and emerging-market shorting is harder and dearer "
        "than US shorting, so a POOLED gross premium is a looser upper bound than a US "
        "one, not a tighter one. Every figure here is an UPPER BOUND of unknown "
        "tightness.",
        "Momentum is the worst case for that gap in this repository. The Ken French "
        "construction re-forms its portfolios EVERY MONTH, so the academic long-short "
        "series carries the highest turnover of any factor here. Cost is reported as a "
        "SCHEDULE in stated turnover and is never subtracted from a premium; the "
        "academic turnover assumption belongs to this series alone and must not be "
        "applied to any long-only product, whose turnover is UNMEASURED.",
        "NO momentum file, in ANY region, was ever gated against a printed table. Every "
        "second moment here is UNMEASURED, which is a weaker statement than a band of "
        "zero and must not be read as agreement. Unlike Experiment 005, this experiment "
        "cannot bound the effect of that uncertainty on the minimum detectable effect "
        "that branch (b) reads.",
        "The three regions are the same 30/70 prior-return construction in globally "
        "correlated universes. They are NOT three independent samples, and the effective "
        "sample size reported here is the measurement of exactly how far short of "
        "independence they fall. Whether they also crash together is reported "
        "separately, because a shared crash means the all-month effective sample size "
        "overstates the independent evidence in the tail.",
        "All three files are USD and unhedged. For a within-region long-short spread the "
        "exchange rate is multiplicative, spread_usd = (1 + f) * spread_local, so "
        "currency moves the second moment first-order and the mean only through the "
        "covariance E[f * spread_local], which is not zero a priori and is NOT measured "
        "here.",
        "A before/after comparison across a publication date is DESCRIPTIVE. Adding "
        "regions adds sample, not identification, and this experiment does not claim to "
        "identify a publication effect.",
        "The currently distributed files apply the current source vintage and the "
        "current construction to the whole history. The international momentum files are "
        "built from a Bloomberg vintage rather than CRSP.",
        "Both multiple-testing families are strongly dependent: three regions of one "
        "factor share global risk factors and `recent` nests inside "
        "`full_post_publication`. Benjamini-Hochberg treats them as independent, so the "
        "corrected p-values are a LOWER bound on the true correction; Holm-Bonferroni is "
        "reported because it is valid under arbitrary dependence. This 9-cell family is "
        "separate from Experiment 001's 20 and Experiment 005's 27 and is not merged "
        "with either; the three US cells are a reproduction check, not a new discovery.",
    )

    return ExperimentResult(
        status=verdict.status,
        summary=_summary_line(
            verdict.status, verdict.branch, regional_family, cells, pooled_full, crash_together
        ),
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
    return _workspace_root() / "experiments" / "exp_006_regional_momentum.yaml"


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    lines = [result.summary, "", "REGIONAL CELLS"]
    lines.append(
        f"{'region':<17}{'era role':<24}{'n':>5}{'ann%':>9}{'vol%':>8}{'SR':>7}"
        f"{'MDE80':>8}{'p':>9}{'BH p':>9}{'Holm p':>9}"
    )
    adjusted: dict[str, tuple[float, float]] = {}
    families = result.diagnostics.get("inference")
    if isinstance(families, Sequence) and not isinstance(families, str):
        for family in families:
            if not isinstance(family, Mapping):
                continue
            rows = family.get("cells")
            if isinstance(rows, Sequence) and not isinstance(rows, str):
                for row in rows:
                    if isinstance(row, Mapping):
                        adjusted[str(row.get("cell"))] = (
                            float(str(row.get("benjamini_hochberg_adjusted_p"))),
                            float(str(row.get("holm_bonferroni_adjusted_p"))),
                        )
    regional = result.diagnostics.get("regional_cells")
    if isinstance(regional, Sequence) and not isinstance(regional, str):
        for item in regional:
            if not isinstance(item, Mapping):
                continue
            key = f"{item.get('region')}/{item.get('factor')}/{item.get('era_role')}"
            bh, holm = adjusted.get(key, (float("nan"), float("nan")))
            lines.append(
                f"{item.get('region')!s:<17}{item.get('era_role')!s:<24}"
                f"{int(str(item.get('observations'))):>5}"
                f"{float(str(item.get('annualised_premium_percent'))):>9.2f}"
                f"{float(str(item.get('annualised_volatility_percent'))):>8.2f}"
                f"{float(str(item.get('sharpe_annualised'))):>7.3f}"
                f"{float(str(item.get('mde_one_sided_percent_per_year'))):>8.2f}"
                f"{float(str(item.get('one_sided_p_value_hac'))):>9.4f}"
                f"{bh:>9.4f}{holm:>9.4f}"
            )

    lines.extend(["", "POOLED CELLS (cross-region joint bootstrap)"])
    lines.append(
        f"{'era role':<24}{'months':>7}{'ann%':>9}{'90% low':>9}{'90% high':>10}"
        f"{'MDE80':>8}{'MDElo':>8}{'MDEhi':>8}{'MDEhac':>8}{'effReg':>8}{'effN':>8}"
        f"{'naiveN':>8}{'rho':>7}"
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
                        bounds = boot.get("two_sided_90")
                        if isinstance(bounds, Sequence) and not isinstance(bounds, str):
                            low, high = float(str(bounds[0])), float(str(bounds[1]))
            mde_low = mde_high = float("nan")
            panel_intervals = item.get("panel_intervals")
            if isinstance(panel_intervals, Sequence) and not isinstance(panel_intervals, str):
                for entry in panel_intervals:
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
                f"{item.get('era_role')!s:<24}{int(str(item.get('months'))):>7}"
                f"{float(str(item.get('annualised_premium_percent'))):>9.2f}"
                f"{low:>9.2f}{high:>10.2f}"
                f"{float(str(item.get('mde_one_sided_percent_per_year'))):>8.2f}"
                f"{mde_low:>8.2f}{mde_high:>8.2f}"
                f"{float(str(item.get('mde_one_sided_hac_percent_per_year'))):>8.2f}"
                f"{float(str(sample_map.get('effective_regions'))):>8.2f}"
                f"{float(str(sample_map.get('effective_region_months_iid'))):>8.0f}"
                f"{int(str(sample_map.get('naive_region_months_if_independent'))):>8}"
                f"{float(str(sample_map.get('mean_pairwise_cross_region_correlation'))):>7.3f}"
            )

    hostile = result.diagnostics.get("hostile_tests")
    if isinstance(hostile, Mapping):
        crash = hostile.get("do_the_regions_crash_together")
        if isinstance(crash, Mapping):
            rows = crash.get("rows")
            if isinstance(rows, Sequence) and not isinstance(rows, str):
                lines.extend(["", "DO THE REGIONS CRASH TOGETHER?"])
                for row in rows:
                    if not isinstance(row, Mapping):
                        continue
                    null = row.get("tail_correlation_null")
                    null_map = null if isinstance(null, Mapping) else {}
                    lines.append(
                        f"  {row.get('cell')}: {row.get('regions_crash_together')}  "
                        f"worst years {row.get('distinct_worst_years')}  "
                        f"rho(all)={row.get('mean_pairwise_correlation_all_months')}  "
                        f"rho(worst decile)="
                        f"{row.get('mean_pairwise_correlation_worst_decile')}  "
                        f"null rho(worst decile)="
                        f"{null_map.get('synthetic_mean_tail_correlation')}  "
                        f"all-in-own-worst-decile="
                        f"{row.get('all_regions_in_own_worst_decile_rate')} vs "
                        f"{row.get('all_regions_in_own_worst_decile_rate_if_independent')}"
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
                for clause in ("clauses_passed", "clauses_failed"):
                    entries = verdict.get(clause)
                    if isinstance(entries, Sequence) and not isinstance(entries, str):
                        for entry in entries:
                            mark = "PASS" if clause == "clauses_passed" else "FAIL"
                            lines.append(f"  {mark} {entry}")
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
    """Run Experiment 006 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_006_regional_momentum",
        description=(
            "Replicate Experiment 001's post-publication momentum grid across three "
            "regions, measure the effective sample size pooling actually buys, and test "
            "whether the regions crash together, writing a ledger entry for the attempt."
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
                "exp_006_regional_momentum"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
