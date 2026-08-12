"""Phase 1 published-result reproduction gate.

Reproduces Fama and French (2015), *Journal of Financial Economics* 116(1),
1--22, **Table 4, Panel A, "2 x 3 Factors" block** -- the monthly mean, standard
deviation and t-statistic of ``Mkt-RF``, ``SMB``, ``HML``, ``RMW`` and ``CMA``
over July 1963 to December 2013, 606 months -- from the file this repository
actually downloaded, through the real cache, the real parser and the real
statistics functions.

The commissioning brief named "Table 1". Table 1 of that paper is the average
excess returns of the 25 Size-B/M, Size-OP and Size-Inv portfolios. The factor
summary statistics it described are Table 4. The specification records the
correction; this module targets Table 4.

What is deliberately awkward here
---------------------------------
* **The raw bytes are pinned by sha256 and the check is a hard abort**, not a
  graded result. The specification's falsifier clause (a) only requires a
  ``rejected`` status; aborting is stricter, and stricter than declared is always
  allowed. A summary statistic computed from an unrecognised file is worse than
  no statistic, because it looks exactly like a good one.
* **The derived table's canonical hash is checked against the committed
  manifest.** That catches a parser change that leaves the downloaded bytes
  identical, which the raw hash cannot see.
* **``RF`` is never subtracted.** All five series are already excess or
  long-short returns. :func:`portfolio_edge.core.statistics.sharpe_ratio` is
  called with an explicit ``risk_free=0.0`` so the treatment is a stated argument
  rather than a default, and the "what if we had subtracted it" hostile test
  measures how large that mistake would have been instead of asserting it absent.
* **Units make a round trip.** The file is in percent, the parser converts to
  decimal, and this module converts back to percent to compare with the printed
  table. Running the comparison through the parser rather than re-reading the CSV
  is the point: a factor of 100 in either direction is the likeliest silent error
  in this path, and the printed table is what catches it.

Run it::

    uv run python -m portfolio_edge.experiments.exp_phase1_ff_reproduction --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.core.returns import Frequency
from portfolio_edge.core.statistics import (
    mean_return,
    sharpe_ratio,
    volatility,
)
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.ledger import Ledger, Origin
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
from portfolio_edge.inference.hac import hac_mean, newey_west_lag_count

__all__ = [
    "ENTRY_POINT",
    "FACTORS",
    "GATED_STATISTICS",
    "EraComparison",
    "FactorStatistics",
    "ReproductionError",
    "build_registry",
    "default_specification_path",
    "main",
    "run",
]

ENTRY_POINT: Final = "phase1_ff_reproduction"

#: Column names in the source file, in the order the file writes them. The
#: printed table calls the first one ``RM - RF``; the specification carries the
#: mapping so the rename is recorded rather than assumed.
FACTORS: Final = ("Mkt-RF", "SMB", "HML", "RMW", "CMA")

#: The three statistics the target table prints, and therefore the only ones the
#: gate can be decided on.
GATED_STATISTICS: Final = ("mean", "std_dev", "t_statistic")

#: Two-sided normal quantile for the 95% intervals attached to reported means.
_Z_95: Final = 1.959963984540054

FloatArray = NDArray[np.float64]


class ReproductionError(RuntimeError):
    """The reproduction could not be attempted against the declared vintage."""


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ReproductionError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ReproductionError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise ReproductionError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise ReproductionError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ReproductionError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _integer(data: Mapping[str, JsonValue], key: str, *, where: str) -> int:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReproductionError(f"{where}.{key} must be an integer, got {value!r}")
    return value


def _flag(data: Mapping[str, JsonValue], key: str, *, where: str) -> bool:
    value = _at(data, key, where=where)
    if not isinstance(value, bool):
        raise ReproductionError(f"{where}.{key} must be true or false, got {value!r}")
    return value


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    return tuple(str(item) for item in items)


# --------------------------------------------------------------------------- #
# Period arithmetic on ``YYYY-MM`` labels
# --------------------------------------------------------------------------- #


def _month_index(period: str) -> int:
    """Months since year 0, so differences and shifts are plain integers."""
    try:
        year, month = period.split("-")
        return int(year) * 12 + (int(month) - 1)
    except ValueError as exc:
        raise ReproductionError(f"not a YYYY-MM period label: {period!r}") from exc


def _period_from_index(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _shift_period(period: str, months: int) -> str:
    return _period_from_index(_month_index(period) + months)


def _expected_month_count(start: str, end: str) -> int:
    return _month_index(end) - _month_index(start) + 1


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorStatistics:
    """Every statistic this gate reports for one series over one window.

    All return quantities are in **percent per month or per year**, matching the
    printed table. The series arrives as decimals from the parser and is scaled
    by 100 here; nothing else rescales anything.
    """

    factor: str
    observations: int
    mean_percent_per_month: float
    std_dev_percent_per_month: float
    conventional_standard_error: float
    conventional_t_statistic: float
    hac_standard_error: float
    hac_t_statistic: float
    hac_lag_count: int
    annualised_premium_percent: float
    annualised_volatility_percent: float
    sharpe_monthly: float
    sharpe_annualised: float
    sharpe_standard_error_monthly: float
    risk_free_treatment: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "factor": self.factor,
            "observations": self.observations,
            "mean_percent_per_month": self.mean_percent_per_month,
            "std_dev_percent_per_month": self.std_dev_percent_per_month,
            "conventional_standard_error": self.conventional_standard_error,
            "conventional_t_statistic": self.conventional_t_statistic,
            "hac_standard_error": self.hac_standard_error,
            "hac_t_statistic": self.hac_t_statistic,
            "hac_lag_count": self.hac_lag_count,
            "annualised_premium_percent": self.annualised_premium_percent,
            "annualised_volatility_percent": self.annualised_volatility_percent,
            "sharpe_monthly": self.sharpe_monthly,
            "sharpe_annualised": self.sharpe_annualised,
            "sharpe_standard_error_monthly": self.sharpe_standard_error_monthly,
            "risk_free_treatment": self.risk_free_treatment,
        }

    def statistic(self, name: str) -> float:
        if name == "mean":
            return self.mean_percent_per_month
        if name == "std_dev":
            return self.std_dev_percent_per_month
        if name == "t_statistic":
            return self.conventional_t_statistic
        raise ReproductionError(f"no gating statistic called {name!r}")


def compute_factor_statistics(series_decimal: FloatArray, *, factor: str) -> FactorStatistics:
    """Summary statistics for one already-excess monthly series.

    ``series_decimal`` is in decimal units, as the parser produces it. The
    risk-free rate is passed as an explicit ``0.0``: these series are excess or
    long-short returns by construction and subtracting ``RF`` a second time is the
    classic error in this exercise.
    """
    percent = series_decimal * 100.0
    observations = int(percent.size)
    mean = mean_return(percent)
    sigma = volatility(percent, ddof=1)
    conventional_se = sigma / math.sqrt(observations)

    hac = hac_mean(percent, n_lags=newey_west_lag_count(observations))
    sharpe = sharpe_ratio(
        percent,
        frequency=Frequency.MONTHLY,
        risk_free=0.0,
    )

    return FactorStatistics(
        factor=factor,
        observations=observations,
        mean_percent_per_month=mean,
        std_dev_percent_per_month=sigma,
        conventional_standard_error=conventional_se,
        conventional_t_statistic=mean / conventional_se,
        hac_standard_error=hac.standard_error,
        hac_t_statistic=hac.t_statistic,
        hac_lag_count=hac.n_lags,
        annualised_premium_percent=12.0 * mean,
        annualised_volatility_percent=math.sqrt(12.0) * sigma,
        sharpe_monthly=sharpe.sharpe_per_period,
        sharpe_annualised=sharpe.annualised_sharpe,
        sharpe_standard_error_monthly=sharpe.standard_error_per_period,
        risk_free_treatment=(
            "risk_free=0.0 passed explicitly; the series is already excess or "
            f"long-short, so RF is not subtracted. {sharpe.risk_free_treatment}"
        ),
    )


# --------------------------------------------------------------------------- #
# Windowing and boundary checks
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Window:
    """A contiguous slice of a parsed table, with its boundary findings."""

    start: str
    end: str
    periods: tuple[str, ...]
    columns: Mapping[str, FloatArray]
    findings: tuple[str, ...]

    @property
    def observations(self) -> int:
        return len(self.periods)


def window_table(
    table: ParsedTable,
    *,
    start: str,
    end: str,
    columns: Sequence[str],
    expected_observations: int | None = None,
) -> Window:
    """Slice ``table`` to ``[start, end]`` and check the boundary properties.

    Findings are returned rather than raised so that the caller can decide
    whether they reject the run; nothing is repaired, filled or dropped.
    """
    first, last = _month_index(start), _month_index(end)
    selected = [
        index
        for index, period in enumerate(table.periods)
        if first <= _month_index(period) <= last
    ]
    periods = tuple(table.periods[index] for index in selected)

    findings: list[str] = []
    if expected_observations is not None and len(periods) != expected_observations:
        findings.append(
            f"window {start}..{end} holds {len(periods)} observations, "
            f"expected {expected_observations}"
        )
    implied = _expected_month_count(start, end)
    if len(periods) != implied:
        findings.append(
            f"window {start}..{end} spans {implied} calendar months but holds "
            f"{len(periods)} rows; months are missing from the file, not empty in it"
        )
    if periods:
        if periods[0] != start:
            findings.append(f"window starts at {periods[0]}, not the frozen {start}")
        if periods[-1] != end:
            findings.append(f"window ends at {periods[-1]}, not the frozen {end}")
        indices = [_month_index(period) for period in periods]
        if any(later <= earlier for earlier, later in pairwise(indices)):
            findings.append("period labels are not strictly increasing inside the window")
        duplicates = sorted({p for p in periods if periods.count(p) > 1})
        if duplicates:
            findings.append(f"duplicate period labels inside the window: {duplicates[:5]}")
        gaps = [
            f"{periods[i]}->{periods[i + 1]}"
            for i in range(len(periods) - 1)
            if indices[i + 1] - indices[i] != 1
        ]
        if gaps:
            findings.append(f"{len(gaps)} month gaps inside the window: {gaps[:5]}")
    else:
        findings.append(f"window {start}..{end} selected no rows at all")

    extracted: dict[str, FloatArray] = {}
    for name in columns:
        if name not in table.columns:
            findings.append(f"column {name!r} is absent from the parsed table")
            continue
        values = table.column(name)
        missing = [periods[i] for i, index in enumerate(selected) if values[index] is None]
        if missing:
            findings.append(
                f"column {name!r} has {len(missing)} missing values inside the "
                f"window: {missing[:5]}. They are reported, never imputed"
            )
        extracted[name] = np.asarray(
            [values[index] for index in selected if values[index] is not None],
            dtype=np.float64,
        )

    return Window(
        start=start,
        end=end,
        periods=periods,
        columns=extracted,
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# Comparison against the printed table
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class CellComparison:
    """One printed cell versus one computed cell."""

    era: str
    gating: bool
    factor: str
    statistic: str
    published: float
    computed: float
    difference: float
    tolerance: float
    within_gate: bool
    within_print_exact: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "era": self.era,
            "gating": self.gating,
            "factor": self.factor,
            "statistic": self.statistic,
            "published": self.published,
            "computed": self.computed,
            "difference": self.difference,
            "tolerance": self.tolerance,
            "within_gate": self.within_gate,
            "within_print_exact": self.within_print_exact,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class EraComparison:
    """Everything computed for one frozen era."""

    era: str
    gating: bool
    start: str
    end: str
    observations: int
    statistics: Mapping[str, FactorStatistics]
    cells: tuple[CellComparison, ...]
    boundary_findings: tuple[str, ...]

    @property
    def failed_cells(self) -> tuple[CellComparison, ...]:
        return tuple(cell for cell in self.cells if not cell.within_gate)

    @property
    def print_exact_cells(self) -> tuple[CellComparison, ...]:
        return tuple(cell for cell in self.cells if cell.within_print_exact)


def _tolerance_for(statistic: str, band: Mapping[str, JsonValue], *, where: str) -> float:
    key = {
        "mean": "mean_percent_per_month",
        "std_dev": "std_dev_percent_per_month",
        "t_statistic": "t_statistic",
    }[statistic]
    return _number(band, key, where=where)


def compare_era(
    table: ParsedTable,
    target: Mapping[str, JsonValue],
    *,
    start: str,
    end: str,
    gate_band: Mapping[str, JsonValue],
    print_band: Mapping[str, JsonValue],
) -> EraComparison:
    """Compute one era's statistics and compare them with its printed table."""
    era = _text(target, "era", where="published_targets[]")
    where = f"published_targets[{era}]"
    gating = _flag(target, "gating", where=where)
    expected = _integer(target, "observations", where=where)
    published = _mapping(_at(target, "factors", where=where), where=f"{where}.factors")

    window = window_table(
        table,
        start=start,
        end=end,
        columns=FACTORS,
        expected_observations=expected,
    )

    statistics: dict[str, FactorStatistics] = {}
    cells: list[CellComparison] = []
    for factor in FACTORS:
        series = window.columns.get(factor)
        if series is None or series.size < 2:
            continue
        stats = compute_factor_statistics(series, factor=factor)
        statistics[factor] = stats
        printed = _mapping(
            _at(published, factor, where=f"{where}.factors"),
            where=f"{where}.factors.{factor}",
        )
        for statistic in GATED_STATISTICS:
            key = {"mean": "mean", "std_dev": "std_dev", "t_statistic": "t_statistic"}[statistic]
            target_value = _number(printed, key, where=f"{where}.factors.{factor}")
            computed = stats.statistic(statistic)
            difference = computed - target_value
            gate = _tolerance_for(statistic, gate_band, where="tolerances.gate")
            exact = _tolerance_for(statistic, print_band, where="tolerances.print_exact_diagnostic")
            cells.append(
                CellComparison(
                    era=era,
                    gating=gating,
                    factor=factor,
                    statistic=statistic,
                    published=target_value,
                    computed=computed,
                    difference=difference,
                    tolerance=gate,
                    within_gate=abs(difference) <= gate,
                    within_print_exact=abs(difference) <= exact,
                )
            )

    return EraComparison(
        era=era,
        gating=gating,
        start=start,
        end=end,
        observations=window.observations,
        statistics=statistics,
        cells=tuple(cells),
        boundary_findings=window.findings,
    )


# --------------------------------------------------------------------------- #
# Hostile tests
# --------------------------------------------------------------------------- #


def _hostile_wrong_risk_free(
    table: ParsedTable, *, start: str, end: str
) -> dict[str, JsonValue]:
    """Measure the classic error: subtracting ``RF`` from series that are already excess."""
    window = window_table(table, start=start, end=end, columns=(*FACTORS, "RF"))
    cash = window.columns.get("RF")
    shifted: dict[str, JsonValue] = {}
    if cash is None or cash.size == 0:
        return {"error": "RF column unavailable in the window"}
    for factor in FACTORS:
        series = window.columns.get(factor)
        if series is None or series.size != cash.size:
            continue
        correct = float(np.mean(series) * 100.0)
        wrong = float(np.mean(series - cash) * 100.0)
        shifted[factor] = {
            "correct_mean_percent_per_month": correct,
            "if_rf_subtracted_percent_per_month": wrong,
            "error_percent_per_month": wrong - correct,
        }
    return {
        "description": (
            "Every factor here is already an excess or long-short return. This is "
            "how far each printed mean would move if RF were subtracted again."
        ),
        "by_factor": shifted,
    }


def _hostile_annual_table(
    parsed: french.FrenchFile, *, start_year: str, end_year: str
) -> dict[str, JsonValue]:
    """Confirm the annual table in the same file does not match the monthly target."""
    try:
        annual = parsed.table("annual")
    except KeyError:
        return {"error": "no annual table in this file"}
    selected = [
        index
        for index, period in enumerate(annual.periods)
        if start_year <= period <= end_year
    ]
    values = annual.column("Mkt-RF")
    numbers = np.asarray(
        [value for index in selected if (value := values[index]) is not None],
        dtype=np.float64,
    )
    if numbers.size == 0:
        return {"error": "annual Mkt-RF column empty over the window"}
    return {
        "description": (
            "The file holds two tables. Selecting the annual one by position "
            "instead of by id would produce this, which the printed monthly "
            "target rejects immediately."
        ),
        "annual_mkt_rf_mean_percent_per_year": float(np.mean(numbers) * 100.0),
        "observations": int(numbers.size),
    }


def _hostile_shifted_windows(
    table: ParsedTable, *, start: str, end: str
) -> dict[str, JsonValue]:
    """Show that an off-by-one sample boundary is visible, not assumed away."""
    shifted: dict[str, JsonValue] = {}
    for offset in (-1, 1):
        moved_start = _shift_period(start, offset)
        moved_end = _shift_period(end, offset)
        window = window_table(table, start=moved_start, end=moved_end, columns=("Mkt-RF",))
        series = window.columns.get("Mkt-RF")
        shifted[f"{offset:+d}"] = {
            "start": moved_start,
            "end": moved_end,
            "observations": window.observations,
            "mkt_rf_mean_percent_per_month": (
                float(np.mean(series) * 100.0) if series is not None and series.size else None
            ),
            "boundary_findings": list(window.findings),
        }
    return {
        "description": (
            "The frozen window shifted by one month in each direction. A "
            "reproduction that matched under a shifted boundary would mean the "
            "boundary is not doing any work."
        ),
        "windows": shifted,
    }


def _hostile_full_file(table: ParsedTable) -> dict[str, JsonValue]:
    """The same statistics over every row in the file, so the window's effect is visible."""
    first, last = table.first_observation, table.last_observation
    if first is None or last is None:
        return {"error": "table has no rows"}
    window = window_table(table, start=first, end=last, columns=FACTORS)
    by_factor: dict[str, JsonValue] = {}
    for factor in FACTORS:
        series = window.columns.get(factor)
        if series is None or series.size < 2:
            continue
        stats = compute_factor_statistics(series, factor=factor)
        by_factor[factor] = {
            "mean_percent_per_month": stats.mean_percent_per_month,
            "std_dev_percent_per_month": stats.std_dev_percent_per_month,
            "t_statistic": stats.conventional_t_statistic,
        }
    return {
        "description": (
            "Every row in the distributed file, not the frozen window. Reported "
            "so the effect of the sample boundary itself is visible."
        ),
        "start": first,
        "end": last,
        "observations": window.observations,
        "by_factor": by_factor,
    }


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


def _load_source(
    specification: Specification,
) -> tuple[ParsedTable, french.FrenchFile, dict[str, JsonValue]]:
    """Fetch, pin, parse and validate the source table.

    Raises :class:`ReproductionError` when the bytes or the derived table are not
    the ones this specification was frozen against.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="parameters.source_pin")

    dataset = french.get_dataset(_text(pin, "dataset_id", where="source_pin"))
    cache = RawCache()
    entry = french.download(cache, dataset)

    expected_raw = _text(pin, "expected_sha256_raw", where="source_pin")
    if entry.sha256 != expected_raw:
        raise ReproductionError(
            f"the file at {dataset.url} now hashes to {entry.sha256}, but this "
            f"specification is frozen against {expected_raw}. Ken French rebuilds "
            "the whole history from each new CRSP vintage, so this is a new "
            "vintage, not a corrupted download. Freeze a new specification "
            "against it rather than reporting numbers from an unrecognised file."
        )

    parsed = french.parse(cache, entry, dataset=dataset)
    table = parsed.table(_text(pin, "table_id", where="source_pin"))

    expected_columns = _strings(pin, "expected_columns", where="source_pin")
    report = validate_table(
        table,
        dataset_id=_text(pin, "manifest_dataset_id", where="source_pin"),
        expected_columns=expected_columns,
        expected_frequency="monthly",
    )
    if not report.ok:
        raise ReproductionError(
            "the parsed table failed validation before any statistic was computed: "
            + "; ".join(report.summary())
        )

    expected_normalized = _text(pin, "expected_sha256_normalized", where="source_pin")
    if table.sha256_normalized() != expected_normalized:
        raise ReproductionError(
            f"the derived table hashes to {table.sha256_normalized()}, but the "
            f"specification pins {expected_normalized}. The raw bytes matched, so "
            "the parser changed behaviour. That is a finding, not a hash to update."
        )

    manifest_hash: str | None = None
    manifest_path = Path(_text(pin, "committed_manifest", where="source_pin"))
    resolved = _workspace_root() / manifest_path
    if resolved.is_file():
        manifest = read_manifest(resolved)
        manifest_hash = manifest.sha256_manifest()
        if manifest.sha256_raw != expected_raw:
            raise ReproductionError(
                f"{resolved} records sha256_raw {manifest.sha256_raw}, which is not "
                f"the pinned {expected_raw}"
            )

    preamble_vintage = _text(pin, "expected_crsp_vintage_in_preamble", where="source_pin")
    provenance: dict[str, JsonValue] = {
        "source_url": entry.url,
        "sha256_raw": entry.sha256,
        "sha256_normalized": table.sha256_normalized(),
        "size_bytes": entry.size_bytes,
        "retrieved_utc": entry.retrieved_utc,
        "http_status": entry.http_status,
        "content_type": entry.content_type,
        "source_last_modified": entry.last_modified,
        "source_etag": entry.etag,
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
        "crsp_vintage_declared_in_preamble": preamble_vintage,
        "crsp_vintage_found_in_preamble": preamble_vintage in parsed.preamble,
        "preamble": parsed.preamble.strip(),
        "validation_findings": list(report.summary()),
    }
    return table, parsed, provenance


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def _estimates_for(era: EraComparison) -> tuple[Estimate, ...]:
    """One block of estimates per factor, each carrying units and uncertainty."""
    estimates: list[Estimate] = []
    for factor in FACTORS:
        stats = era.statistics.get(factor)
        if stats is None:
            continue
        half = _Z_95 * stats.hac_standard_error
        hac_method = (
            f"normal 95% interval from a Newey-West HAC standard error, "
            f"Bartlett kernel, L={stats.hac_lag_count} from "
            f"floor(4*(T/100)**(2/9)) at T={stats.observations}"
        )
        estimates.append(
            Estimate(
                name=f"{factor} monthly mean",
                value=stats.mean_percent_per_month,
                units="percent per month",
                interval=(stats.mean_percent_per_month - half, stats.mean_percent_per_month + half),
                interval_method=hac_method,
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=stats.observations,
                notes=stats.risk_free_treatment,
            )
        )
        estimates.append(
            Estimate(
                name=f"{factor} annualised arithmetic premium",
                value=stats.annualised_premium_percent,
                units="percentage points per year",
                interval=(
                    12.0 * (stats.mean_percent_per_month - half),
                    12.0 * (stats.mean_percent_per_month + half),
                ),
                interval_method=f"12 x the monthly mean and its bounds; {hac_method}",
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=stats.observations,
                notes="arithmetic, not compound; 12 x the monthly mean",
            )
        )
        estimates.append(
            Estimate(
                name=f"{factor} annualised volatility",
                value=stats.annualised_volatility_percent,
                units="percentage points per year",
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=stats.observations,
                uncertainty_unavailable_reason=(
                    "no interval is computed for a volatility here: this experiment "
                    "resamples nothing, and a chi-squared interval would assume the "
                    "normality that monthly factor returns violate"
                ),
                notes="sqrt(12) x the monthly sample standard deviation, ddof=1",
            )
        )
        sharpe_half = _Z_95 * stats.sharpe_standard_error_monthly * math.sqrt(12.0)
        estimates.append(
            Estimate(
                name=f"{factor} annualised Sharpe ratio",
                value=stats.sharpe_annualised,
                units="ratio",
                interval=(
                    stats.sharpe_annualised - sharpe_half,
                    stats.sharpe_annualised + sharpe_half,
                ),
                interval_method=(
                    "normal 95% interval from sqrt((1 + SR^2/2)/T) on the monthly "
                    "Sharpe, scaled by sqrt(12); assumes i.i.d. normal returns, "
                    "which these are not"
                ),
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=stats.observations,
                notes=stats.risk_free_treatment,
            )
        )
        estimates.append(
            Estimate(
                name=f"{factor} difference from published monthly mean",
                value=next(
                    cell.difference
                    for cell in era.cells
                    if cell.factor == factor and cell.statistic == "mean"
                ),
                units="percentage points per month",
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=stats.observations,
                uncertainty_unavailable_reason=(
                    "the printed value is a constant, not a resamplable estimate; "
                    "the relevant uncertainty is the +/-0.005 printing precision, "
                    "which the declared tolerance carries"
                ),
            )
        )
    return tuple(estimates)


def _frames(eras: Sequence[EraComparison]) -> dict[str, pd.DataFrame]:
    comparison = pd.DataFrame(
        [cell.to_json() for era in eras for cell in era.cells]
    )
    statistics = pd.DataFrame(
        [
            {"era": era.era, **stats.to_json()}
            for era in eras
            for stats in era.statistics.values()
        ]
    )
    return {"comparison": comparison, "factor_statistics": statistics}


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute the Phase 1 reproduction gate.

    ``context`` carries identity and a seeded generator that this experiment does
    not use: the calculation is deterministic and nothing is resampled. The seed
    is still ledgered, which is the point of passing it.
    """
    del context  # deterministic; the seed is recorded by the runner, not used here

    parameters = _mapping(specification.parameters, where="parameters")
    tolerances = _mapping(
        _at(parameters, "tolerances", where="parameters"), where="parameters.tolerances"
    )
    gate_band = _mapping(_at(tolerances, "gate", where="tolerances"), where="tolerances.gate")
    print_band = _mapping(
        _at(tolerances, "print_exact_diagnostic", where="tolerances"),
        where="tolerances.print_exact_diagnostic",
    )
    implementation_band = _mapping(
        _at(tolerances, "implementation_error", where="tolerances"),
        where="tolerances.implementation_error",
    )
    implementation_limit = _number(
        implementation_band, "mean_percent_per_month", where="tolerances.implementation_error"
    )
    sign_must_match = _flag(
        implementation_band, "sign_must_match", where="tolerances.implementation_error"
    )

    table, parsed, provenance = _load_source(specification)

    eras_by_name = {era.name: era for era in specification.sample_policy.eras}
    targets = _sequence(
        _at(parameters, "published_targets", where="parameters"),
        where="parameters.published_targets",
    )

    comparisons: list[EraComparison] = []
    for index, item in enumerate(targets):
        target = _mapping(item, where=f"published_targets[{index}]")
        era_name = _text(target, "era", where=f"published_targets[{index}]")
        era = eras_by_name.get(era_name)
        if era is None:
            raise ReproductionError(
                f"published target {era_name!r} names no era in sample_policy; "
                f"known eras: {sorted(eras_by_name)}"
            )
        comparisons.append(
            compare_era(
                table,
                target,
                start=era.start,
                end=era.end,
                gate_band=gate_band,
                print_band=print_band,
            )
        )

    gating = [era for era in comparisons if era.gating]
    if len(gating) != 1:
        raise ReproductionError(
            f"exactly one gating era is required, found {len(gating)}: "
            f"{[era.era for era in gating]}"
        )
    primary = gating[0]

    # -- the predeclared decision --------------------------------------------- #
    boundary_failures = list(primary.boundary_findings)
    implementation_failures = [
        f"{cell.factor} mean differs by {cell.difference:+.4f} pp/month"
        for cell in primary.cells
        if cell.statistic == "mean"
        and (
            abs(cell.difference) > implementation_limit
            or (sign_must_match and cell.published * cell.computed < 0.0)
        )
    ]
    failed = primary.failed_cells

    if boundary_failures or implementation_failures:
        status = ResultStatus.REJECTED
        verdict = "FAIL"
    elif failed:
        status = ResultStatus.UNRESOLVED
        verdict = "UNRESOLVED"
    else:
        status = ResultStatus.SOURCE_REPRODUCED
        verdict = "PASS"

    exact = primary.print_exact_cells
    summary = (
        f"{verdict}: {len(primary.cells) - len(failed)} of {len(primary.cells)} gating "
        f"cells of Fama-French (2015) Table 4 Panel A (2x3 block, {primary.start}..{primary.end}, "
        f"{primary.observations} months) reproduce within the predeclared tolerance, and "
        f"{len(exact)} of {len(primary.cells)} round to the printed value exactly, from "
        f"the {provenance['crsp_vintage_declared_in_preamble']} CRSP vintage "
        f"(sha256 {str(provenance['sha256_raw'])[:12]}...)."
    )

    diagnostics: dict[str, JsonValue] = {
        "verdict": verdict,
        "source": provenance,
        "gate": {
            "gating_era": primary.era,
            "gating_cells": len(primary.cells),
            "cells_within_gate": len(primary.cells) - len(failed),
            "cells_within_print_exact": len(exact),
            "failed_cells": [cell.to_json() for cell in failed],
            "boundary_failures": boundary_failures,
            "implementation_error_failures": implementation_failures,
            "tolerances": {
                "gate": {key: gate_band[key] for key in sorted(gate_band)},
                "print_exact_diagnostic": {key: print_band[key] for key in sorted(print_band)},
                "implementation_error": {
                    key: implementation_band[key] for key in sorted(implementation_band)
                },
            },
        },
        "eras": [
            {
                "era": era.era,
                "gating": era.gating,
                "start": era.start,
                "end": era.end,
                "observations": era.observations,
                "boundary_findings": list(era.boundary_findings),
                "cells_within_gate": sum(1 for cell in era.cells if cell.within_gate),
                "cells": [cell.to_json() for cell in era.cells],
                "statistics": {
                    factor: stats.to_json() for factor, stats in era.statistics.items()
                },
            }
            for era in comparisons
        ],
        "hostile_tests": {
            "wrong_risk_free_treatment": _hostile_wrong_risk_free(
                table, start=primary.start, end=primary.end
            ),
            "annual_table_instead_of_monthly": _hostile_annual_table(
                parsed, start_year=primary.start[:4], end_year=primary.end[:4]
            ),
            "sample_window_shifted": _hostile_shifted_windows(
                table, start=primary.start, end=primary.end
            ),
            "whole_file_not_the_window": _hostile_full_file(table),
        },
    }

    caveats = (
        "Passing this gate does NOT verify portfolio accounting, rebalancing, "
        "transaction costs, tax lots, corporate actions, insolvency behaviour, "
        "missing-data handling, look-ahead protection, or optimisation "
        "constraints. None of them is exercised here.",
        "The published factor file already contains the authors' own calculated "
        "returns. Matching their table shows we read and summarised their numbers "
        "correctly; it does not show that we could have computed them.",
        "This check can match despite compensating errors. It is a necessary "
        "condition for trusting the ingestion path, not a sufficient one.",
        "Every figure is gross of transaction costs, shorting costs, fees and "
        "taxes, because the source series are. The long-short series are not "
        "investable and no premium here is achievable.",
        "Mkt-RF, SMB, HML, RMW and CMA are ALL already excess or long-short "
        "returns. RF was not subtracted from any of them. The "
        "wrong_risk_free_treatment diagnostic measures how far each mean would "
        "move if it had been.",
        "The file was built from a CRSP vintage roughly twelve years later than "
        "the one the authors used, and no vintage archive exists, so an exactly "
        "like-for-like reproduction is unavailable at any tolerance. A sha256 "
        "pins which file was used; it does not establish what was available in "
        "2014.",
        "sqrt(12) annualisation of volatility and of the Sharpe ratio assumes "
        "serially independent monthly returns, which these are not. The HAC "
        "standard error beside each conventional one is the size of that "
        "assumption.",
    )

    return ExperimentResult(
        status=status,
        summary=summary,
        estimates=_estimates_for(primary),
        diagnostics=diagnostics,
        caveats=caveats,
        frames=_frames(comparisons),
    )


def build_registry() -> ExperimentRegistry:
    """A registry holding exactly this experiment.

    Constructed per call rather than at import: ``registry.py`` refuses a
    module-level default so that what executes cannot depend on import order.
    """
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return _workspace_root() / "experiments" / "phase1_ff_reproduction.yaml"


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    diagnostics = result.diagnostics
    lines = [result.summary, ""]
    eras = diagnostics.get("eras")
    if isinstance(eras, Sequence) and not isinstance(eras, str):
        for item in eras:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"era {item.get('era')} ({item.get('start')}..{item.get('end')}, "
                f"{item.get('observations')} months, gating={item.get('gating')})"
            )
            lines.append(
                f"  {'factor':<8}{'published':>10}{'computed':>11}{'diff':>9}   statistic"
            )
            cells = item.get("cells")
            if isinstance(cells, Sequence) and not isinstance(cells, str):
                for cell in cells:
                    if not isinstance(cell, Mapping):
                        continue
                    mark = "ok " if cell.get("within_gate") else "OUT"
                    exact = "=" if cell.get("within_print_exact") else " "
                    lines.append(
                        f"  {cell.get('factor')!s:<8}"
                        f"{float(str(cell.get('published'))):>10.4f}"
                        f"{float(str(cell.get('computed'))):>11.4f}"
                        f"{float(str(cell.get('difference'))):>+9.4f}"
                        f" {mark}{exact} {cell.get('statistic')}"
                    )
            lines.append("")
    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the reproduction through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_phase1_ff_reproduction",
        description=(
            "Reproduce Fama and French (2015) Table 4 Panel A from the pinned "
            "Ken French vintage, writing a ledger entry for the attempt."
        ),
    )
    parser.add_argument(
        "--specification",
        type=Path,
        default=default_specification_path(),
        help="path to the frozen specification YAML",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="path to the append-only ledger (default research/ledger.jsonl)",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=None,
        help="directory for run artifacts (default research/artifacts)",
    )
    parser.add_argument(
        "--origin",
        choices=[item.value for item in Origin],
        default=Origin.AI.value,
        help="who initiated this run",
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

    manifest_hashes: list[str] = []
    for source in specification.data_sources:
        if not isinstance(source, Mapping):
            continue
        location = source.get("manifest")
        if isinstance(location, str):
            path = _workspace_root() / location
            if path.is_file():
                manifest_hashes.append(read_manifest(path).sha256_manifest())

    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=tuple(manifest_hashes),
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
                "exp_phase1_ff_reproduction"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0 if outcome.result and outcome.result.status is ResultStatus.SOURCE_REPRODUCED else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
