"""Experiment 011: a financed overlay of non-equity engines, against the honest control.

Every marginal-sleeve result this repository has produced so far was funded by
*selling* something. Experiment 004 sold a 60/40 base pro rata; Experiment 010 sold a
100% equity base pro rata. :mod:`portfolio_edge.studies.overlay_growth` derives what
that choice costs — equation (3), ``sigma_p**2 (L_p* - 1)`` — and shows it is a
property of the base position alone, worth more than two percentage points a year at
plausible equity inputs. This experiment is the first here to test the other funding
rule on real returns: sell nothing, finance the notional, and pay for it.

**The comparison that decides is not the one that flatters.** Equation (5) of
``overlay_growth``: at matched volatility the ``-V/2`` terms are identical by
construction, so the growth difference collapses to ``sigma_p (S_portfolio - S_base)``
and *only the Sharpe ratio decides*. An overlay that raises growth over the unlevered
equity control while lowering the portfolio's Sharpe ratio has bought its gain with
leverage. So the leverage-matched controls, ``equity_levered_135`` and
``equity_levered_150``, are the primary benchmark, and they are charged the borrow
spread on exactly the terms the overlay portfolios are. Charging financing to an
overlay's geometric return but not to its Sharpe ratio, or charging it to the overlay
but not to the levered control, changes the sign of the answer; both are forbidden by
the frozen specification and neither is available through this module's API.

**The two benchmarks are never combined.** The unlevered control answers "what does an
investor who will not borrow give up"; the levered control answers "is this alpha or is
it beta". :func:`require_one_benchmark` raises rather than pooling them, for the same
reason ``aggregate()`` in :mod:`portfolio_edge.studies.outperformance_horizon` does.

What this experiment is, stated negatively
------------------------------------------
* **Exploratory, and it cannot be promoted.** The panel's sample moments were examined
  before the specification existed. The weight vectors and the haircut grid were chosen
  after that inspection. No re-run converts that into a confirmatory result.
* **A vendor-series evaluation.** The trend and commodity legs are AQR-authored series,
  reconstructed in full on every update, published by a firm that sells the strategies.
  Neither workbook states a fee, transaction-cost, slippage, roll-cost or financing
  basis anywhere, so both are gross of the vendor's own trading costs *by omission*.
* **Not a commodity total return.** The AQR commodity series is excess of cash. Nothing
  here adds a cash rate to it and no figure derived from it is a collateralised return.
* **Not an optimiser.** Six weight vectors are enumerated in the frozen specification.
  Nothing searches a weight space and nothing is fitted to the panel.

Run it::

    uv run python -m portfolio_edge.experiments.exp_011_overlay_stack --view-results
"""

from __future__ import annotations

import argparse
import itertools
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import norm

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import aqr, french, goyal_welch
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table

# The CRRA certainty equivalent and the calendar-year compounding rule were written
# once, for Experiment 003, and decision 0008 requires every experiment that reports a
# certainty equivalent to report *that* one. Importing is the only way to keep a single
# canonical definition; a second copy here would be a second definition.
from portfolio_edge.experiments.exp_003_rebalancing import (
    calendar_year_gross_returns,
    crra_certainty_equivalent,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_index
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
    SamplePolicy,
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import (
    optimal_block_length,
    stationary_bootstrap_indices,
)
from portfolio_edge.studies.overlay_growth import (
    OverlayInputs,
    sharpe_admission_threshold,
)

__all__ = [
    "ENTRY_POINT",
    "MONTHS_PER_YEAR",
    "AdmissionVerdict",
    "CostModel",
    "HaircutPoint",
    "MatchedVolatilityComparison",
    "OverlayStackError",
    "Panel",
    "PortfolioSummary",
    "admission_verdicts",
    "break_even_haircut",
    "build_registry",
    "correlation_matrix",
    "default_specification_path",
    "haircut_sweep",
    "load_panel",
    "main",
    "matched_volatility_comparison",
    "minimum_detectable_effect",
    "require_one_benchmark",
    "run",
    "simulate_portfolio",
    "sleeve_moments",
]

ENTRY_POINT: Final = "exp_011_overlay_stack"

MONTHS_PER_YEAR: Final = 12

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.intp]

#: Chunk size for the bootstrap, so that a 10000-by-485 index matrix never has to exist
#: alongside a resampled copy of every series at once.
_BOOTSTRAP_CHUNK: Final = 1000


class OverlayStackError(RuntimeError):
    """The experiment could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise OverlayStackError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise OverlayStackError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise OverlayStackError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise OverlayStackError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise OverlayStackError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[str] = []
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise OverlayStackError(f"{where}.{key} must hold non-empty strings, got {item!r}")
        out.append(item.strip())
    return tuple(out)


def _numbers(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[float, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[float] = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise OverlayStackError(f"{where}.{key} must hold numbers, got {item!r}")
        out.append(float(item))
    return tuple(out)


def default_specification_path() -> Path:
    return _workspace_root() / "experiments" / "exp_011_overlay_stack.yaml"


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


# --------------------------------------------------------------------------- #
# The panel
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Panel:
    """A rectangular monthly panel of sleeve **excess** returns, plus the cash rate.

    Every column is an excess return over cash in decimal. ``cash`` is the funding
    rate that turns any of them into a funded total return; it is a column of the
    panel rather than a separate object because the intersection that defines the
    window includes it.
    """

    periods: tuple[str, ...]
    sleeves: tuple[str, ...]
    excess: FloatArray
    """Shape ``(T, N)``, monthly excess returns over cash, in decimal."""
    cash: FloatArray
    """Shape ``(T,)``, the monthly cash return, in decimal."""
    provenance: tuple[Mapping[str, JsonValue], ...]
    findings: tuple[str, ...]

    @property
    def months(self) -> int:
        return len(self.periods)

    @property
    def years(self) -> float:
        return self.months / MONTHS_PER_YEAR

    def index_of(self, sleeve: str) -> int:
        try:
            return self.sleeves.index(sleeve)
        except ValueError:
            raise OverlayStackError(
                f"no sleeve {sleeve!r} in the panel; it holds {list(self.sleeves)}"
            ) from None

    def column(self, sleeve: str) -> FloatArray:
        return np.asarray(self.excess[:, self.index_of(sleeve)], dtype=np.float64)

    def window(self, *, start: str, end: str) -> Panel:
        first, last = month_index(start), month_index(end)
        keep = [
            i for i, period in enumerate(self.periods) if first <= month_index(period) <= last
        ]
        if not keep:
            raise OverlayStackError(f"the window {start}..{end} selects no months")
        return Panel(
            periods=tuple(self.periods[i] for i in keep),
            sleeves=self.sleeves,
            excess=self.excess[keep, :],
            cash=self.cash[keep],
            provenance=self.provenance,
            findings=self.findings,
        )


def _load_pinned_table(pin: Mapping[str, JsonValue], *, cache: RawCache) -> tuple[
    ParsedTable, dict[str, JsonValue], list[str]
]:
    """Fetch, hash-pin, parse and validate one source file.

    A raw-hash mismatch aborts. All three sources rewrite their entire history on
    every release, so an unrecognised hash is a **new vintage** rather than a
    corrupted download, and a result computed from an unrecognised file looks
    exactly like a good one.
    """
    where = "parameters.source_pin.series[]"
    source = _text(pin, "source", where=where)
    dataset_id = _text(pin, "dataset_id", where=where)
    table_id = _text(pin, "table_id", where=where)

    if source == "french":
        french_dataset = french.get_dataset(dataset_id)
        url, parser_version = french_dataset.url, french.PARSER_VERSION
        entry = french.download(cache, french_dataset)
        _abort_on_raw_mismatch(pin, entry.sha256, url=url, where=where)
        table = french.parse(cache, entry, dataset=french_dataset).table(table_id)
    elif source == "goyal_welch":
        gw_dataset = goyal_welch.get_dataset(dataset_id)
        url, parser_version = gw_dataset.url, goyal_welch.PARSER_VERSION
        entry = goyal_welch.download(cache, gw_dataset)
        _abort_on_raw_mismatch(pin, entry.sha256, url=url, where=where)
        table = goyal_welch.parse(cache, entry, dataset=gw_dataset).table(table_id)
    elif source == "aqr":
        aqr_dataset = aqr.get_dataset(dataset_id)
        url, parser_version = aqr_dataset.url, aqr.PARSER_VERSION
        entry = aqr.download(cache, aqr_dataset)
        _abort_on_raw_mismatch(pin, entry.sha256, url=url, where=where)
        table = aqr.parse(cache, entry, dataset=aqr_dataset).table
        if table.table_id != table_id:
            raise OverlayStackError(
                f"{dataset_id}: the parsed table is {table.table_id!r} but the "
                f"specification pins {table_id!r}. The vendor's observation frequency "
                "has changed; freeze a new specification rather than reading it anyway."
            )
    else:
        raise OverlayStackError(
            f"{where}.source is {source!r}; known readers are french, goyal_welch, aqr"
        )

    columns = _strings(pin, "columns", where=where)
    report = validate_table(table, dataset_id=dataset_id, expected_frequency="monthly")
    findings = list(report.summary())
    if not report.ok:
        raise OverlayStackError(
            "a source table failed validation before any statistic was computed: "
            + "; ".join(findings)
        )

    expected_normalized = _text(pin, "expected_sha256_normalized", where=where)
    if table.sha256_normalized() != expected_normalized:
        raise OverlayStackError(
            f"{dataset_id}: the derived table hashes to {table.sha256_normalized()}, "
            f"but the specification pins {expected_normalized}. The raw bytes matched, "
            "so the parser changed behaviour. That is a finding, not a hash to update."
        )

    missing = [name for name in columns if name not in table.columns]
    if missing:
        raise OverlayStackError(
            f"{dataset_id}: column(s) {missing} are not in the parsed table, whose "
            f"columns are {list(table.columns)}. The source has renamed a series."
        )

    manifest_hash: str | None = None
    manifest_path = _workspace_root() / _text(pin, "committed_manifest", where=where)
    if manifest_path.is_file():
        manifest = read_manifest(manifest_path)
        manifest_hash = manifest.sha256_manifest()
        if manifest.sha256_raw != entry.sha256:
            raise OverlayStackError(
                f"{manifest_path} records sha256_raw {manifest.sha256_raw}, which is "
                f"not the {entry.sha256} that was actually read"
            )

    record: dict[str, JsonValue] = {
        "series": _text(pin, "name", where=where),
        "source": source,
        "dataset_id": dataset_id,
        "table_id": table.table_id,
        "columns": list(columns),
        "combination": _text(pin, "combination", where=where),
        "source_url": url,
        "sha256_raw": entry.sha256,
        "sha256_normalized": table.sha256_normalized(),
        "retrieved_utc": entry.retrieved_utc,
        "source_last_modified": entry.last_modified,
        "parser_version": parser_version,
        "committed_manifest_sha256": manifest_hash,
        "rows_in_file": table.rows,
        "first_observation": table.first_observation,
        "last_observation": table.last_observation,
        "units": table.units,
        "unit_transform": table.unit_transform,
        "validation_findings": findings,
    }
    return table, record, findings


def _abort_on_raw_mismatch(
    pin: Mapping[str, JsonValue], observed: str, *, url: str, where: str
) -> None:
    expected = _text(pin, "expected_sha256_raw", where=where)
    if observed != expected:
        raise OverlayStackError(
            f"the file at {url} now hashes to {observed}, but this specification is "
            f"frozen against {expected}. Ken French rebuilds from each CRSP vintage, "
            "AQR reconstructs its full history on every update, and Goyal-Welch "
            "rebuilds the whole file on each annual release, so this is a NEW VINTAGE "
            "rather than a corrupted download. Freeze a new specification against it "
            "instead of reporting numbers from an unrecognised file."
        )


def load_panel(specification: Specification) -> Panel:
    """Build the frozen panel of excess returns from the pinned source files."""
    parameters = _mapping(specification.parameters, where="parameters")
    pin_block = _mapping(
        _at(parameters, "source_pin", where="parameters"), where="parameters.source_pin"
    )
    entries = _sequence(_at(pin_block, "series", where="source_pin"), where="source_pin.series")

    cache = RawCache()
    start, end = specification.sample_policy.start, specification.sample_policy.end
    first, last = month_index(start), month_index(end)

    series: dict[str, dict[str, float]] = {}
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []
    order: list[str] = []

    for item in entries:
        pin = _mapping(item, where="source_pin.series[]")
        table, record, table_findings = _load_pinned_table(pin, cache=cache)
        name = str(record["series"])
        if name in series:
            raise OverlayStackError(f"series {name!r} is pinned twice")
        combination = str(record["combination"])
        columns = _strings(pin, "columns", where="source_pin.series[]")
        if combination == "identity":
            if len(columns) != 1:
                raise OverlayStackError(
                    f"{name}: combination 'identity' needs exactly one column, got {columns}"
                )
            values = table.column(columns[0])
            built = {
                period: value
                for period, value in zip(table.periods, values, strict=True)
                if value is not None
            }
        elif combination == "difference":
            if len(columns) != 2:
                raise OverlayStackError(
                    f"{name}: combination 'difference' needs exactly two columns, got {columns}"
                )
            left, right = table.column(columns[0]), table.column(columns[1])
            built = {
                period: a - b
                for period, a, b in zip(table.periods, left, right, strict=True)
                if a is not None and b is not None
            }
        else:
            raise OverlayStackError(
                f"{name}: unknown combination {combination!r}; known: identity, difference"
            )

        series[name] = {
            period: value
            for period, value in built.items()
            if first <= month_index(period) <= last
        }
        order.append(name)
        provenance.append(record)
        findings.extend(f"{name}: {finding}" for finding in table_findings)

    if "cash" not in series:
        raise OverlayStackError("the specification must pin a series named 'cash'")

    sleeves = tuple(name for name in order if name != "cash")
    common = set(series["cash"])
    for name in sleeves:
        common &= set(series[name])
    periods = tuple(sorted(common))
    if not periods:
        raise OverlayStackError(
            "the pinned series have no month in common inside the frozen window"
        )

    excess = np.array(
        [[series[name][period] for name in sleeves] for period in periods], dtype=np.float64
    )
    cash = np.array([series["cash"][period] for period in periods], dtype=np.float64)
    if not np.all(np.isfinite(excess)) or not np.all(np.isfinite(cash)):
        raise OverlayStackError("the intersected panel holds a non-finite value")

    findings.append(
        f"the intersected panel is {len(periods)} months, {periods[0]}..{periods[-1]}. "
        "Both boundaries are properties of single files -- the trend series begins "
        f"{min(series['trend']) if 'trend' in series else 'n/a'} and the commodity "
        f"series ends {max(series['commodity']) if 'commodity' in series else 'n/a'} -- "
        "and neither was chosen."
    )
    return Panel(
        periods=periods,
        sleeves=sleeves,
        excess=excess,
        cash=cash,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# Moments
# --------------------------------------------------------------------------- #


def _annualised_mean(monthly: FloatArray) -> float:
    return float(np.mean(monthly)) * MONTHS_PER_YEAR


def _annualised_volatility(monthly: FloatArray) -> float:
    return float(np.std(monthly, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)


def sleeve_moments(panel: Panel) -> dict[str, dict[str, float]]:
    """Annualised arithmetic mean, volatility and Sharpe ratio, per sleeve.

    Every figure is on the **excess** return, so the Sharpe ratio is the mean divided
    by the volatility with no cash subtraction left to do and no cash rate smuggled
    into the denominator.
    """
    out: dict[str, dict[str, float]] = {}
    for index, sleeve in enumerate(panel.sleeves):
        column = np.asarray(panel.excess[:, index], dtype=np.float64)
        mean = _annualised_mean(column)
        volatility = _annualised_volatility(column)
        out[sleeve] = {
            "arithmetic_excess_return": mean,
            "volatility": volatility,
            "sharpe": mean / volatility,
            "skewness": float(_standardised_moment(column, 3)),
            "excess_kurtosis": float(_standardised_moment(column, 4) - 3.0),
            "months": float(panel.months),
        }
    return out


def _standardised_moment(values: FloatArray, order: int) -> float:
    centred = values - float(np.mean(values))
    scale = float(np.std(values, ddof=0))
    if scale == 0.0:
        return 0.0
    return float(np.mean(centred**order)) / scale**order


def correlation_matrix(panel: Panel) -> dict[str, dict[str, float]]:
    matrix = np.atleast_2d(np.corrcoef(panel.excess.T))
    return {
        row: {column: float(matrix[i, j]) for j, column in enumerate(panel.sleeves)}
        for i, row in enumerate(panel.sleeves)
    }


# --------------------------------------------------------------------------- #
# Costs and portfolios
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class CostModel:
    """Annual charges, all levied on **notional** and all charged inside the simulation.

    ``sleeve_fee`` is a management fee on the absolute notional of each sleeve.
    ``borrow_spread`` is the financing spread paid over cash on gross notional above
    1.0. Both are divided by twelve and subtracted from the portfolio's monthly excess
    return before any statistic is computed, so neither can appear as a post-hoc
    haircut on an annual figure.

    **The borrow spread applies to the leverage-matched controls too.** A levered
    equity position finances the same way an overlay does, and exempting it would make
    the control cheaper than the thing it is controlling for. There is no flag here to
    turn that off, on purpose.
    """

    sleeve_fee: Mapping[str, float]
    borrow_spread: float

    def __post_init__(self) -> None:
        if self.borrow_spread < 0.0:
            raise OverlayStackError(
                f"the borrow spread cannot be negative, got {self.borrow_spread}"
            )
        for sleeve, fee in self.sleeve_fee.items():
            if fee < 0.0:
                raise OverlayStackError(f"the fee on {sleeve!r} cannot be negative, got {fee}")

    def fee_for(self, sleeve: str) -> float:
        if sleeve not in self.sleeve_fee:
            raise OverlayStackError(
                f"no fee is declared for sleeve {sleeve!r}; declared: "
                f"{sorted(self.sleeve_fee)}. An undeclared fee would silently be zero."
            )
        return self.sleeve_fee[sleeve]

    def annual_charge(self, sleeves: Sequence[str], weights: Sequence[float]) -> float:
        """Total annual charge on one weight vector, in decimal."""
        if len(sleeves) != len(weights):
            raise OverlayStackError("sleeves and weights must have the same length")
        fee = sum(abs(w) * self.fee_for(s) for s, w in zip(sleeves, weights, strict=True))
        gross = sum(abs(w) for w in weights)
        return fee + self.borrow_spread * max(0.0, gross - 1.0)


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioSummary:
    """One weight vector simulated over one window, with everything it decides.

    ``volatility`` is the volatility of the **excess** return and is the one used in
    the Sharpe ratio, so that equation (5)'s identity holds exactly.
    ``total_return_volatility`` is reported separately because it differs whenever the
    cash rate moves, and because putting one in the numerator and the other in the
    denominator is how a matched-volatility comparison silently stops holding.
    """

    name: str
    sleeves: tuple[str, ...]
    weights: tuple[float, ...]
    gross_notional: float
    annual_cost: float
    months: int
    arithmetic_excess_return: float
    volatility: float
    total_return_volatility: float
    sharpe: float
    geometric_return: float
    max_drawdown: float
    months_under_water: int
    certainty_equivalent: float | None
    certainty_equivalent_years: int
    growth_over_calendar_years: float | None
    excess: FloatArray = field(repr=False)
    total: FloatArray = field(repr=False)

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "weights": {s: w for s, w in zip(self.sleeves, self.weights, strict=True)},
            "gross_notional": self.gross_notional,
            "annual_cost_charged_on_notional": self.annual_cost,
            "months": self.months,
            "arithmetic_excess_return": self.arithmetic_excess_return,
            "volatility_of_excess_return": self.volatility,
            "volatility_of_total_return": self.total_return_volatility,
            "sharpe": self.sharpe,
            "geometric_return": self.geometric_return,
            "max_drawdown": self.max_drawdown,
            "months_under_water": self.months_under_water,
            "certainty_equivalent_gamma_3": self.certainty_equivalent,
            "growth_over_calendar_years": self.growth_over_calendar_years,
            "certainty_equivalent_years": self.certainty_equivalent_years,
        }


def simulate_portfolio(
    panel: Panel,
    *,
    name: str,
    sleeves: Sequence[str],
    weights: Sequence[float],
    costs: CostModel,
    gamma: float = 3.0,
    calendar_year_range: tuple[int, int] | None = None,
    mean_shift: Mapping[str, float] | None = None,
) -> PortfolioSummary:
    """Simulate one constant-weight financed overlay portfolio over ``panel``.

    The excess return in month ``t`` is ``sum_i w_i x_{i,t}`` less one twelfth of the
    annual charge, and the total return adds the panel's cash rate. The equity weight
    is *not* reduced to fund the sleeves: this is the overlay funding rule, which is
    the whole point of the experiment.

    ``mean_shift`` subtracts a constant annual rate from a named sleeve's monthly
    observations before the portfolio is formed. It exists for the haircut sweep and
    is applied **inside** the simulation, so the sweep's volatility, correlations and
    drawdowns are those of the shifted series rather than of the original.
    """
    if len(sleeves) != len(weights):
        raise OverlayStackError("sleeves and weights must have the same length")
    columns = [panel.index_of(sleeve) for sleeve in sleeves]
    matrix = np.asarray(panel.excess[:, columns], dtype=np.float64).copy()
    for position, sleeve in enumerate(sleeves):
        shift = (mean_shift or {}).get(sleeve, 0.0)
        if shift:
            matrix[:, position] -= shift / MONTHS_PER_YEAR

    weight_vector = np.asarray(weights, dtype=np.float64)
    charge = costs.annual_charge(sleeves, weights)
    excess = matrix @ weight_vector - charge / MONTHS_PER_YEAR
    total = excess + panel.cash

    curve = np.cumprod(1.0 + total)
    if np.any(curve <= 0.0):
        raise OverlayStackError(
            f"portfolio {name!r} reaches non-positive wealth; that is insolvency, not "
            "a low return, and no growth rate may be quoted for it"
        )
    summary = drawdown_summary(curve)
    volatility = _annualised_volatility(excess)

    certainty_equivalent: float | None = None
    growth: float | None = None
    years = 0
    if calendar_year_range is not None:
        annual = _calendar_year_returns(panel, total, calendar_year_range)
        if annual.size:
            years = int(annual.size)
            certainty_equivalent = crra_certainty_equivalent(annual, gamma=gamma)
            growth = crra_certainty_equivalent(annual, gamma=1.0)

    return PortfolioSummary(
        name=name,
        sleeves=tuple(sleeves),
        weights=tuple(float(w) for w in weights),
        gross_notional=float(np.sum(np.abs(weight_vector))),
        annual_cost=charge,
        months=panel.months,
        arithmetic_excess_return=_annualised_mean(excess),
        volatility=volatility,
        total_return_volatility=_annualised_volatility(total),
        sharpe=_annualised_mean(excess) / volatility,
        geometric_return=float(curve[-1]) ** (MONTHS_PER_YEAR / panel.months) - 1.0,
        max_drawdown=summary.max_drawdown,
        months_under_water=summary.max_time_under_water,
        certainty_equivalent=certainty_equivalent,
        certainty_equivalent_years=years,
        growth_over_calendar_years=growth,
        excess=excess,
        total=total,
    )


def _calendar_year_returns(
    panel: Panel, total: FloatArray, calendar_year_range: tuple[int, int]
) -> FloatArray:
    """Non-overlapping calendar-year gross returns over whole years only.

    The panel ends in May, so the final partial year cannot form an observation. It is
    dropped here rather than annualised, because annualising five months into a year is
    an invented observation.
    """
    low, high = calendar_year_range
    keep: list[int] = []
    for year in range(low, high + 1):
        rows = [i for i, period in enumerate(panel.periods) if period[:4] == f"{year:04d}"]
        if len(rows) == MONTHS_PER_YEAR:
            keep.extend(rows)
    if not keep:
        return np.empty(0, dtype=np.float64)
    return calendar_year_gross_returns(np.asarray(total[keep], dtype=np.float64))


# --------------------------------------------------------------------------- #
# The comparison that decides
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class MatchedVolatilityComparison:
    """Equation (5): at matched volatility only the Sharpe ratio decides.

    ``gap`` is ``sigma_portfolio (S_portfolio - S_benchmark)``, the growth the
    portfolio adds over the benchmark levered to the portfolio's own volatility. It is
    **not** the gain over the unlevered benchmark, and the two are different numbers
    answering different questions; ``benchmark`` is carried on every instance so that
    they cannot be mixed by accident.
    """

    portfolio: str
    benchmark: str
    portfolio_volatility: float
    benchmark_volatility: float
    portfolio_sharpe: float
    benchmark_sharpe: float
    gap: float
    minimum_detectable_effect: float
    interval: tuple[float, float] | None
    interval_method: str
    months: int
    difference: FloatArray = field(repr=False)

    @property
    def resolved(self) -> bool:
        """Whether the gap is larger than the smallest effect the sample could see."""
        return abs(self.gap) >= self.minimum_detectable_effect

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "portfolio": self.portfolio,
            "benchmark": self.benchmark,
            "portfolio_volatility": self.portfolio_volatility,
            "benchmark_volatility": self.benchmark_volatility,
            "portfolio_sharpe": self.portfolio_sharpe,
            "benchmark_sharpe": self.benchmark_sharpe,
            "gap": self.gap,
            "minimum_detectable_effect": self.minimum_detectable_effect,
            "resolved": self.resolved,
            "interval": list(self.interval) if self.interval is not None else None,
            "interval_method": self.interval_method,
            "months": self.months,
        }


def minimum_detectable_effect(
    difference: FloatArray, *, power: float = 0.80, alpha: float = 0.05
) -> float:
    """The smallest annualised mean difference this sample could detect, at ``power``.

    ``(z_{1 - alpha/2} + z_power) * 12 * sd / sqrt(n)`` on the monthly paired
    difference. Reported beside every gap because a positive point estimate below this
    floor is not evidence of an effect, and this repository has already read one as
    though it were.
    """
    values = np.asarray(difference, dtype=np.float64)
    if values.size < 2:
        raise OverlayStackError("need at least two observations for a detectable effect")
    multiplier = float(norm.ppf(1.0 - alpha / 2.0) + norm.ppf(power))
    return multiplier * MONTHS_PER_YEAR * float(np.std(values, ddof=1)) / math.sqrt(values.size)


def _gap_from_excess(portfolio: FloatArray, benchmark: FloatArray) -> tuple[float, FloatArray]:
    """``sigma_p (S_p - S_b)`` and the paired difference series whose mean it is.

    Writing the gap as the mean of ``r_p - (sigma_p / sigma_b) r_b`` is the same
    number by construction and is what makes an interval and a detectable effect
    computable at all: the scaling ratio is a plug-in estimate treated as known, which
    understates the interval slightly and is recorded rather than corrected.
    """
    sigma_p = float(np.std(portfolio, ddof=1))
    sigma_b = float(np.std(benchmark, ddof=1))
    if sigma_b <= 0.0:
        raise OverlayStackError("the benchmark has zero volatility; no scaling exists")
    difference = np.asarray(portfolio - (sigma_p / sigma_b) * benchmark, dtype=np.float64)
    return _annualised_mean(difference), difference


def _gaps_over_resamples(
    portfolio: FloatArray, benchmark: FloatArray, indices: IntArray
) -> FloatArray:
    """:func:`_gap_from_excess` evaluated on every row of a resample index matrix.

    Vectorised rather than looped because the paired resample has to be drawn tens of
    thousands of times for each of eight portfolio-benchmark pairs, and a Python loop
    over rows turns a two-second interval into a two-minute one.
    """
    drawn_p = portfolio[indices]
    drawn_b = benchmark[indices]
    sigma_p = np.std(drawn_p, ddof=1, axis=1)
    sigma_b = np.std(drawn_b, ddof=1, axis=1)
    if np.any(sigma_b <= 0.0):  # pragma: no cover - defensive
        raise OverlayStackError("a resample gave the benchmark zero volatility")
    difference = drawn_p - (sigma_p / sigma_b)[:, None] * drawn_b
    return np.asarray(np.mean(difference, axis=1) * MONTHS_PER_YEAR, dtype=np.float64)


def matched_volatility_comparison(
    portfolio: PortfolioSummary,
    benchmark: PortfolioSummary,
    *,
    rng: np.random.Generator | None = None,
    resamples: int = 0,
    mean_block_length: float = 12.0,
    confidence_level: float = 0.95,
) -> MatchedVolatilityComparison:
    """Compare one portfolio with one benchmark at matched volatility.

    Passing ``resamples > 0`` and a generator attaches a stationary block-bootstrap
    percentile interval, resampling the **paired** monthly series so the two arms stay
    aligned month by month.
    """
    if portfolio.months != benchmark.months:
        raise OverlayStackError(
            f"{portfolio.name} has {portfolio.months} months and {benchmark.name} has "
            f"{benchmark.months}; they were not simulated over the same window"
        )
    gap, difference = _gap_from_excess(portfolio.excess, benchmark.excess)

    interval: tuple[float, float] | None = None
    method = ""
    if resamples > 0:
        if rng is None:
            raise OverlayStackError("a bootstrap needs a generator")
        draws: list[FloatArray] = []
        remaining = resamples
        while remaining > 0:
            size = min(_BOOTSTRAP_CHUNK, remaining)
            indices = stationary_bootstrap_indices(
                portfolio.months, mean_block_length, size, rng
            )
            draws.append(_gaps_over_resamples(portfolio.excess, benchmark.excess, indices))
            remaining -= size
        tail = (1.0 - confidence_level) / 2.0
        low, high = np.quantile(np.concatenate(draws), [tail, 1.0 - tail])
        interval = (float(low), float(high))
        method = (
            f"stationary block bootstrap, {confidence_level:.0%} percentile, mean block "
            f"{mean_block_length:g}m, {resamples} resamples, paired rows"
        )

    return MatchedVolatilityComparison(
        portfolio=portfolio.name,
        benchmark=benchmark.name,
        portfolio_volatility=portfolio.volatility,
        benchmark_volatility=benchmark.volatility,
        portfolio_sharpe=portfolio.sharpe,
        benchmark_sharpe=benchmark.sharpe,
        gap=gap,
        minimum_detectable_effect=minimum_detectable_effect(difference),
        interval=interval,
        interval_method=method,
        months=portfolio.months,
        difference=difference,
    )


def require_one_benchmark(
    comparisons: Sequence[MatchedVolatilityComparison],
) -> str:
    """Return the shared benchmark, or raise. Never sum across benchmarks.

    The unlevered control and the leverage-matched control are two different
    counterfactuals. Adding, averaging or tabulating them as one line is the
    double-counting error ``aggregate()`` in
    :mod:`portfolio_edge.studies.outperformance_horizon` raises on, and it is the error
    this repository has actually made.
    """
    if not comparisons:
        raise OverlayStackError("no comparisons to check")
    benchmarks = {item.benchmark for item in comparisons}
    if len(benchmarks) != 1:
        raise OverlayStackError(
            "these comparisons are measured against different benchmarks and may not "
            f"be combined: {', '.join(sorted(benchmarks))}. A cheap index, a levered "
            "index and the reader's own counterfactual are three different claims."
        )
    return next(iter(benchmarks))


# --------------------------------------------------------------------------- #
# The haircut sweep
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class HaircutPoint:
    """One point of the sweep: what the overlay is worth once the sleeve's mean falls."""

    haircut: float
    gap: float
    geometric_return: float
    sharpe: float
    benchmark: str


def haircut_sweep(
    panel: Panel,
    *,
    sleeve: str,
    portfolio_sleeves: Sequence[str],
    weights: Sequence[float],
    benchmark: PortfolioSummary,
    costs: CostModel,
    grid: Sequence[float],
    name: str,
) -> tuple[HaircutPoint, ...]:
    """Subtract a constant annual rate from ``sleeve`` and re-simulate at each grid point.

    The shift is applied inside the simulation, so it moves the mean and nothing else:
    volatility, every correlation and the benchmark are unchanged. That makes the gap
    fall **linearly** at exactly the sleeve's weight per unit of haircut, which is why
    the break-even can be interpolated exactly rather than searched for.
    """
    points: list[HaircutPoint] = []
    for haircut in grid:
        summary = simulate_portfolio(
            panel,
            name=f"{name}@{haircut:g}",
            sleeves=portfolio_sleeves,
            weights=weights,
            costs=costs,
            mean_shift={sleeve: haircut},
        )
        gap, _ = _gap_from_excess(summary.excess, benchmark.excess)
        points.append(
            HaircutPoint(
                haircut=haircut,
                gap=gap,
                geometric_return=summary.geometric_return,
                sharpe=summary.sharpe,
                benchmark=benchmark.name,
            )
        )
    return tuple(points)


def break_even_haircut(points: Sequence[HaircutPoint]) -> float | None:
    """Where the gap crosses zero, by linear interpolation. ``None`` if it never does.

    Exact for this construction: a constant subtracted from the sleeve's mean moves the
    gap by minus the sleeve's weight times the haircut and moves nothing else, so the
    sweep is a straight line and interpolation is not an approximation.
    """
    ordered = sorted(points, key=lambda point: point.haircut)
    for first, second in itertools.pairwise(ordered):
        if first.gap >= 0.0 > second.gap:
            span = first.gap - second.gap
            if span == 0.0:  # pragma: no cover - defensive
                return first.haircut
            return first.haircut + (second.haircut - first.haircut) * first.gap / span
    return None


# --------------------------------------------------------------------------- #
# The admission test
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionVerdict:
    """Equation (4): ``S_d > L rho sigma_p``, one sleeve at one base exposure."""

    sleeve: str
    base_exposure: float
    gross_excess_return: float
    net_excess_return: float
    volatility: float
    correlation: float
    net_sharpe: float
    threshold_sharpe: float
    margin: float
    admitted: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "sleeve": self.sleeve,
            "base_exposure": self.base_exposure,
            "gross_excess_return": self.gross_excess_return,
            "net_excess_return": self.net_excess_return,
            "volatility": self.volatility,
            "correlation_with_equity": self.correlation,
            "net_sharpe": self.net_sharpe,
            "threshold_sharpe": self.threshold_sharpe,
            "margin": self.margin,
            "admitted": self.admitted,
        }


def admission_verdicts(
    panel: Panel,
    *,
    base: str,
    sleeves: Sequence[str],
    costs: CostModel,
    base_exposures: Sequence[float],
) -> tuple[AdmissionVerdict, ...]:
    """Run every candidate sleeve through ``overlay_growth``'s admission bar.

    The algebra is not re-derived here: :class:`~portfolio_edge.studies.overlay_growth.
    OverlayInputs` owns it, and this function only supplies the measured moments. The
    threshold is negative wherever the correlation is, which is why the commodity leg
    can have a respectable standalone mean and still fail while the trend leg passes
    with a lower one.
    """
    base_column = panel.column(base)
    base_mean = _annualised_mean(base_column)
    base_volatility = _annualised_volatility(base_column)
    correlations = correlation_matrix(panel)

    verdicts: list[AdmissionVerdict] = []
    for sleeve in sleeves:
        column = panel.column(sleeve)
        inputs = OverlayInputs(
            base_excess_return=base_mean,
            base_volatility=base_volatility,
            diversifier_excess_return=_annualised_mean(column),
            diversifier_volatility=_annualised_volatility(column),
            correlation=correlations[base][sleeve],
            financing_spread=costs.borrow_spread,
            fee=costs.fee_for(sleeve),
        )
        for exposure in base_exposures:
            threshold = sharpe_admission_threshold(inputs, base_exposure=exposure)
            verdicts.append(
                AdmissionVerdict(
                    sleeve=sleeve,
                    base_exposure=float(exposure),
                    gross_excess_return=inputs.diversifier_excess_return,
                    net_excess_return=inputs.net_excess_return,
                    volatility=inputs.diversifier_volatility,
                    correlation=inputs.correlation,
                    net_sharpe=inputs.diversifier_sharpe,
                    threshold_sharpe=threshold,
                    margin=inputs.diversifier_sharpe - threshold,
                    admitted=inputs.diversifier_sharpe > threshold,
                )
            )
    return tuple(verdicts)


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class _Settings:
    """Everything the run needs, read once out of the frozen specification."""

    sleeves: tuple[str, ...]
    portfolio_sleeves: tuple[str, ...]
    portfolios: tuple[tuple[str, tuple[float, ...], str], ...]
    costs: CostModel
    gamma: float
    calendar_years: tuple[int, int]
    haircut_sleeve: str
    haircut_grid: tuple[float, ...]
    haircut_portfolio: str
    base_exposures: tuple[float, ...]
    materiality: float
    primary_benchmark: str
    secondary_benchmark: str
    resamples: int
    confidence_level: float
    block_lengths: tuple[float, ...]


def _read_settings(specification: Specification) -> _Settings:
    parameters = _mapping(specification.parameters, where="parameters")
    where = "parameters"

    cost_model = _mapping(specification.cost_model, where="cost_model")
    fees_raw = _mapping(
        _at(cost_model, "sleeve_fee_annual_percent", where="cost_model"),
        where="cost_model.sleeve_fee_annual_percent",
    )
    fees: dict[str, float] = {}
    for sleeve, value in fees_raw.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise OverlayStackError(f"cost_model fee for {sleeve!r} must be a number")
        fees[sleeve] = float(value) / 100.0
    costs = CostModel(
        sleeve_fee=fees,
        borrow_spread=_number(cost_model, "borrow_spread_annual_percent", where="cost_model")
        / 100.0,
    )

    portfolios: list[tuple[str, tuple[float, ...], str]] = []
    for item in _sequence(_at(parameters, "portfolios", where=where), where=f"{where}.portfolios"):
        entry = _mapping(item, where=f"{where}.portfolios[]")
        portfolios.append(
            (
                _text(entry, "name", where="portfolios[]"),
                _numbers(entry, "weights", where="portfolios[]"),
                _text(entry, "role", where="portfolios[]"),
            )
        )

    sweep = _mapping(_at(parameters, "haircut_sweep", where=where), where=f"{where}.haircut_sweep")
    start = _number(sweep, "start_percent_per_year", where="haircut_sweep") / 100.0
    stop = _number(sweep, "stop_percent_per_year", where="haircut_sweep") / 100.0
    step = _number(sweep, "step_percent_per_year", where="haircut_sweep") / 100.0
    if step <= 0.0 or stop < start:
        raise OverlayStackError("the haircut sweep grid is empty or has a non-positive step")
    count = round((stop - start) / step) + 1
    grid = tuple(start + step * i for i in range(count))

    admission = _mapping(
        _at(parameters, "admission_test", where=where), where=f"{where}.admission_test"
    )
    years = _numbers(parameters, "certainty_equivalent_years", where=where)
    if len(years) != 2:
        raise OverlayStackError("certainty_equivalent_years must be a pair of years")

    benchmark = _mapping(specification.benchmark, where="benchmark")
    primary = _mapping(_at(benchmark, "primary", where="benchmark"), where="benchmark.primary")
    secondary = _mapping(
        _at(benchmark, "secondary", where="benchmark"), where="benchmark.secondary"
    )

    return _Settings(
        sleeves=_strings(parameters, "sleeves", where=where),
        portfolio_sleeves=_strings(parameters, "portfolio_sleeve_order", where=where),
        portfolios=tuple(portfolios),
        costs=costs,
        gamma=_number(parameters, "crra_gamma", where=where),
        calendar_years=(int(years[0]), int(years[1])),
        haircut_sleeve=_text(sweep, "applies_to", where="haircut_sweep"),
        haircut_grid=grid,
        haircut_portfolio=_text(sweep, "portfolio", where="haircut_sweep"),
        base_exposures=_numbers(admission, "base_exposures", where="admission_test"),
        materiality=_number(parameters, "materiality_threshold_annual_percent", where=where)
        / 100.0,
        primary_benchmark=_text(primary, "id", where="benchmark.primary"),
        secondary_benchmark=_text(secondary, "id", where="benchmark.secondary"),
        resamples=specification.inference.resamples,
        confidence_level=specification.inference.confidence_level,
        block_lengths=(6.0, 12.0, 24.0),
    )


def _era(specification: Specification, name: str) -> tuple[str, str]:
    for era in specification.sample_policy.eras:
        if era.name == name:
            return (era.start, era.end)
    raise OverlayStackError(f"the specification declares no era named {name!r}")


def _simulate_all(
    panel: Panel, settings: _Settings, *, calendar_years: tuple[int, int] | None
) -> dict[str, PortfolioSummary]:
    return {
        name: simulate_portfolio(
            panel,
            name=name,
            sleeves=settings.portfolio_sleeves,
            weights=weights,
            costs=settings.costs,
            gamma=settings.gamma,
            calendar_year_range=calendar_years,
        )
        for name, weights, _role in settings.portfolios
    }


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 011 against the pinned sources."""
    settings = _read_settings(specification)
    panel = load_panel(specification)
    if set(panel.sleeves) != set(settings.sleeves):
        raise OverlayStackError(
            f"the panel holds {sorted(panel.sleeves)} but the specification declares "
            f"{sorted(settings.sleeves)}"
        )

    full = _simulate_all(panel, settings, calendar_years=settings.calendar_years)
    levered_controls = tuple(
        name for name, _w, role in settings.portfolios if "leverage-matched" in role
    )
    controls = tuple(name for name, _w, role in settings.portfolios if "control" in role)
    candidates = tuple(name for name, _w, _role in settings.portfolios if name not in controls)
    headline = settings.haircut_portfolio

    comparisons: dict[str, tuple[MatchedVolatilityComparison, ...]] = {}
    for benchmark_name in (settings.primary_benchmark, settings.secondary_benchmark):
        benchmark = full[benchmark_name]
        rows = tuple(
            matched_volatility_comparison(
                full[name],
                benchmark,
                rng=context.rng,
                resamples=settings.resamples,
                mean_block_length=12.0,
                confidence_level=settings.confidence_level,
            )
            for name in candidates
        )
        require_one_benchmark(rows)
        comparisons[benchmark_name] = rows

    # Robustness arm: the headline gap at 6- and 24-month blocks. Reported beside the
    # frozen 12-month figure and never merged with it.
    block_sensitivity: dict[str, JsonValue] = {}
    for block in settings.block_lengths:
        arm = matched_volatility_comparison(
            full[headline],
            full[settings.primary_benchmark],
            rng=context.rng,
            resamples=settings.resamples,
            mean_block_length=block,
            confidence_level=settings.confidence_level,
        )
        block_sensitivity[f"block_{block:g}m"] = {
            "gap": arm.gap,
            "interval": list(arm.interval) if arm.interval is not None else None,
        }

    era_gaps: dict[str, dict[str, dict[str, float]]] = {}
    eras: dict[str, JsonValue] = {}
    for era in specification.sample_policy.eras:
        if era.name == "no_trend_long_window":
            continue
        window = panel.window(start=era.start, end=era.end)
        summaries = _simulate_all(window, settings, calendar_years=None)
        gaps = {
            benchmark_name: {
                name: matched_volatility_comparison(summaries[name], summaries[benchmark_name]).gap
                for name in candidates
            }
            for benchmark_name in (settings.primary_benchmark, settings.secondary_benchmark)
        }
        era_gaps[era.name] = gaps
        eras[era.name] = {
            "start": era.start,
            "end": era.end,
            "months": window.months,
            "moments": {k: dict(v) for k, v in sleeve_moments(window).items()},
            "correlations": {k: dict(v) for k, v in correlation_matrix(window).items()},
            "portfolios": {name: item.to_json() for name, item in summaries.items()},
            "matched_volatility_gap": {
                benchmark_name: dict(row) for benchmark_name, row in gaps.items()
            },
        }

    long_start, long_end = _era(specification, "no_trend_long_window")
    long_panel = _load_long_window(
        specification, drop=settings.haircut_sleeve, start=long_start, end=long_end
    )
    long_window: dict[str, JsonValue] = {
        "window": f"{long_panel.periods[0]}..{long_panel.periods[-1]}",
        "months": long_panel.months,
        "sleeves": list(long_panel.sleeves),
        "full": {k: dict(v) for k, v in sleeve_moments(long_panel).items()},
        "before_1985": {
            k: dict(v)
            for k, v in sleeve_moments(
                long_panel.window(start=long_panel.periods[0], end="1984-12")
            ).items()
        },
        "from_1985": {
            k: dict(v)
            for k, v in sleeve_moments(
                long_panel.window(start="1985-01", end=long_panel.periods[-1])
            ).items()
        },
        "note": (
            "the trend leg does not exist on this window and no portfolio containing it "
            "is evaluated here. A bond Sharpe ratio measured only over 1985-2025 is a "
            "measurement of one bond bull market, which this split is here to show."
        ),
    }

    headline_weights = next(w for n, w, _r in settings.portfolios if n == headline)
    sweeps: dict[str, list[dict[str, float]]] = {}
    break_evens: dict[str, float | None] = {}
    for benchmark_name in (settings.primary_benchmark, settings.secondary_benchmark):
        points = haircut_sweep(
            panel,
            sleeve=settings.haircut_sleeve,
            portfolio_sleeves=settings.portfolio_sleeves,
            weights=headline_weights,
            benchmark=full[benchmark_name],
            costs=settings.costs,
            grid=settings.haircut_grid,
            name=headline,
        )
        sweeps[benchmark_name] = [
            {
                "haircut": point.haircut,
                "gap": point.gap,
                "geometric_return": point.geometric_return,
                "sharpe": point.sharpe,
            }
            for point in points
        ]
        break_evens[benchmark_name] = break_even_haircut(points)

    verdicts = admission_verdicts(
        panel,
        base="equity",
        sleeves=tuple(s for s in panel.sleeves if s != "equity"),
        costs=settings.costs,
        base_exposures=settings.base_exposures,
    )

    pre_start, pre_end = _era(specification, "pre_publication")
    post_start, post_end = _era(specification, "post_publication")
    pre_mean = sleeve_moments(panel.window(start=pre_start, end=pre_end))[
        settings.haircut_sleeve
    ]["arithmetic_excess_return"]
    post_mean = sleeve_moments(panel.window(start=post_start, end=post_end))[
        settings.haircut_sleeve
    ]["arithmetic_excess_return"]
    decay = pre_mean - post_mean

    headline_row = next(
        row for row in comparisons[settings.primary_benchmark] if row.portfolio == headline
    )
    status, verdict_note = _decide(
        headline=headline_row,
        pre_gap=era_gaps["pre_publication"][settings.primary_benchmark][headline],
        post_gap=era_gaps["post_publication"][settings.primary_benchmark][headline],
        decay=decay,
        break_even=break_evens[settings.primary_benchmark],
        levered_beats=any(
            full[name].sharpe >= full[headline].sharpe for name in levered_controls
        ),
    )

    diagnostics: dict[str, JsonValue] = {
        "window": f"{panel.periods[0]}..{panel.periods[-1]}",
        "months": panel.months,
        "sleeves": list(panel.sleeves),
        "moments_full_window": {k: dict(v) for k, v in sleeve_moments(panel).items()},
        "correlations_full_window": {k: dict(v) for k, v in correlation_matrix(panel).items()},
        "politis_white_stationary_block_length": {
            sleeve: float(optimal_block_length(panel.column(sleeve)).stationary)
            for sleeve in panel.sleeves
        },
        "portfolios_full_window": {name: item.to_json() for name, item in full.items()},
        "matched_volatility": {
            benchmark_name: [row.to_json() for row in rows]
            for benchmark_name, rows in comparisons.items()
        },
        "block_length_sensitivity": block_sensitivity,
        "eras": eras,
        "no_trend_long_window": long_window,
        "haircut_sweep": {k: list(v) for k, v in sweeps.items()},
        "break_even_haircut": dict(break_evens),
        "trend_pre_to_post_decay": decay,
        "admission_test": [item.to_json() for item in verdicts],
        "cost_model": {
            "sleeve_fee_annual": dict(settings.costs.sleeve_fee),
            "borrow_spread_annual": settings.costs.borrow_spread,
            "charged_uniformly_to_levered_controls": True,
        },
        "benchmarks": {
            "primary": settings.primary_benchmark,
            "secondary": settings.secondary_benchmark,
            "never_combined": True,
        },
        "provenance": list(panel.provenance),
        "data_findings": list(panel.findings),
        "verdict": verdict_note,
    }

    frames = {
        "portfolios": pd.DataFrame([item.to_json() for item in full.values()]),
        "haircut_sweep": pd.DataFrame(
            [
                {"benchmark": benchmark_name, **point}
                for benchmark_name, points in sweeps.items()
                for point in points
            ]
        ),
        "admission_test": pd.DataFrame([item.to_json() for item in verdicts]),
    }

    return ExperimentResult(
        status=status,
        summary=verdict_note,
        estimates=_build_estimates(full, comparisons, settings, break_evens, verdicts),
        diagnostics=diagnostics,
        caveats=_CAVEATS,
        frames=frames,
    )


def _load_long_window(specification: Specification, *, drop: str, start: str, end: str) -> Panel:
    """The panel without one sleeve, over the longer window that sleeve was truncating.

    Built by rewriting the frozen specification's series list rather than by filtering
    the loaded panel, so the second window goes through the same hash pins, the same
    validation and the same intersection rule as the first.
    """
    parameters = dict(_mapping(specification.parameters, where="parameters"))
    pin = dict(_mapping(parameters["source_pin"], where="source_pin"))
    pin["series"] = tuple(
        item
        for item in _sequence(_at(pin, "series", where="source_pin"), where="series")
        if _text(_mapping(item, where="series[]"), "name", where="series[]") != drop
    )
    parameters["source_pin"] = pin
    detached = replace(
        specification,
        parameters=parameters,
        sample_policy=SamplePolicy(
            start=start,
            end=end,
            eras=specification.sample_policy.eras,
            held_out=specification.sample_policy.held_out,
            embargo=specification.sample_policy.embargo,
        ),
    )
    return load_panel(detached)



_CAVEATS: Final = (
    "EXPLORATORY AND UNPROMOTABLE. The panel's sample moments were examined before this "
    "specification existed, and the weight vectors and haircut grid were chosen after "
    "that inspection. No re-run converts this into a confirmatory result.",
    "VENDOR-SERIES EVALUATION, NOT A REPLICATION. The trend and commodity legs are "
    "AQR-authored series reconstructed in full on every update by a firm that sells the "
    "strategies. Neither workbook states a fee, transaction-cost, slippage, roll-cost or "
    "financing basis anywhere, so every figure here is gross of the vendor's own trading "
    "costs BY OMISSION. That unpriced item is largest exactly where it matters most: "
    "rolling commodity futures.",
    "The commodity series is EXCESS OF CASH, not a collateralised total return. No "
    "figure here is a commodity total return and none may be quoted as one.",
    "The two benchmarks are never combined. The leverage-matched control answers whether "
    "this is alpha; the unlevered control answers what a non-borrowing investor gives up. "
    "A figure mixing them would be meaningless.",
    "The borrow spread is charged to the levered controls on the same terms as to the "
    "overlay portfolios. Charging financing to an overlay's geometric return but not to "
    "its Sharpe ratio flatters the overlay by exactly the financing cost, and equation "
    "(5) makes the Sharpe ratio the deciding statistic.",
    "Geometric growth decides and the gamma-3 certainty equivalent reports beside it "
    "(decision 0008). The certainty equivalent pays a candidate for de-risking, and no "
    "investor needs a sleeve to hold less equity.",
    "The window's two boundaries are properties of single files: the trend series begins "
    "in 1985 and the commodity series ends in 2025-05. Neither was chosen and neither is "
    "a holdout.",
    "PRETAX everywhere. The simulation holds no tax lots, so it cannot know a basis, so "
    "it may not price a realisation.",
    "No sleeve is promoted by this result and decision 0004 stands.",
)


def _decide(
    *,
    headline: MatchedVolatilityComparison,
    pre_gap: float,
    post_gap: float,
    decay: float,
    break_even: float | None,
    levered_beats: bool,
) -> tuple[ResultStatus, str]:
    """Apply the frozen falsifiers, in the order the specification states them."""
    gap_pp = headline.gap * 100.0
    if headline.gap <= 0.0:
        return (
            ResultStatus.REJECTED,
            f"falsifier (a): the matched-volatility gap of {headline.portfolio} against "
            f"{headline.benchmark} is {gap_pp:+.2f} pp/yr, at or below zero.",
        )
    if levered_beats:
        return (
            ResultStatus.REJECTED,
            "falsifier (b): a leverage-matched control attains a Sharpe ratio at or above "
            "the overlay portfolio's, so the gain is leveraged beta rather than alpha.",
        )
    if pre_gap > 0.0 and post_gap < 0.0:
        return (
            ResultStatus.REJECTED,
            f"falsifier (c): the pre-publication gap is {pre_gap * 100:+.2f} pp/yr and the "
            f"post-publication gap is {post_gap * 100:+.2f} pp/yr.",
        )
    if headline.interval is not None and headline.interval[0] <= 0.0 <= headline.interval[1]:
        return (
            ResultStatus.UNRESOLVED,
            f"the gap is {gap_pp:+.2f} pp/yr but its bootstrap interval "
            f"[{headline.interval[0] * 100:+.2f}, {headline.interval[1] * 100:+.2f}] "
            "includes zero.",
        )
    if not headline.resolved:
        return (
            ResultStatus.UNRESOLVED,
            f"the gap is {gap_pp:+.2f} pp/yr, below the minimum detectable effect of "
            f"{headline.minimum_detectable_effect * 100:.2f} pp/yr. A positive point estimate "
            "below the resolution of the instrument is not evidence of an effect.",
        )
    if break_even is not None and decay > break_even:
        return (
            ResultStatus.UNRESOLVED,
            f"the gap is {gap_pp:+.2f} pp/yr against {headline.benchmark} and its interval "
            f"excludes zero, but the sleeve's measured pre-to-post-publication decay of "
            f"{decay * 100:.2f} pp/yr EXCEEDS the {break_even * 100:.2f} pp/yr haircut at "
            "which the overlay stops paying. The full-window figure is a description of "
            "1985-2025, not a forecast.",
        )
    return (
        ResultStatus.EXPLORATORY,
        f"the gap is {gap_pp:+.2f} pp/yr against {headline.benchmark}, its interval excludes "
        "zero, and it survives the declared haircut. Exploratory only: see the freeze note.",
    )


def _build_estimates(
    portfolios: Mapping[str, PortfolioSummary],
    comparisons: Mapping[str, Sequence[MatchedVolatilityComparison]],
    settings: _Settings,
    break_evens: Mapping[str, float | None],
    verdicts: Sequence[AdmissionVerdict],
) -> tuple[Estimate, ...]:
    """One optimistic cost column only, and the reason is stated on every estimate.

    Four of the five sleeves carry a zero fee and neither vendor series is charged its
    own trading costs, so this is the **net-optimistic** column. There is no
    net-pessimistic column because the pessimistic assumption cannot be constructed:
    the vendor states no cost basis at all, so a pessimistic number would be invented.
    """
    basis = CostBasis.NET_OPTIMISTIC
    unpriced = (
        "net of the declared fee and borrow spread only; the vendor's own trading costs "
        "inside the AQR series are unpriced because no basis is published"
    )
    estimates: list[Estimate] = []
    for name, summary in portfolios.items():
        estimates.append(
            Estimate(
                name=f"net_geometric_return[{name}]",
                value=summary.geometric_return * 100.0,
                units="percent per year",
                cost_basis=basis,
                n_obs=summary.months,
                notes=(
                    f"gross notional {summary.gross_notional:.2f}x, annual charge "
                    f"{summary.annual_cost * 100:.3f}%; {unpriced}"
                ),
                uncertainty_unavailable_reason=(
                    "a geometric return over one realised path has no sampling interval "
                    "that is not a restatement of the arithmetic mean's; the interval "
                    "that decides is on the matched-volatility gap, which is reported"
                ),
            )
        )
        if summary.certainty_equivalent is not None:
            estimates.append(
                Estimate(
                    name=f"certainty_equivalent_gamma_{settings.gamma:g}[{name}]",
                    value=summary.certainty_equivalent * 100.0,
                    units="percent per year",
                    cost_basis=basis,
                    n_obs=summary.certainty_equivalent_years,
                    notes=(
                        "reported BESIDE growth and never instead of it (decision 0008); "
                        f"gamma-1 growth over the same {summary.certainty_equivalent_years} "
                        f"calendar years is "
                        f"{(summary.growth_over_calendar_years or 0.0) * 100:+.2f}%"
                    ),
                    uncertainty_unavailable_reason=(
                        f"computed exactly over {summary.certainty_equivalent_years} "
                        "non-overlapping calendar years; decision 0008 records that this "
                        "statistic pays a candidate for de-risking, so an interval on it "
                        "would give a misleading impression of precision about the wrong "
                        "quantity"
                    ),
                )
            )
    for benchmark, rows in comparisons.items():
        for row in rows:
            estimates.append(
                Estimate(
                    name=f"matched_volatility_gap[{row.portfolio} vs {benchmark}]",
                    value=row.gap * 100.0,
                    units="percentage points per year",
                    interval=(
                        (row.interval[0] * 100.0, row.interval[1] * 100.0)
                        if row.interval
                        else None
                    ),
                    interval_method=row.interval_method,
                    cost_basis=basis,
                    n_obs=row.months,
                    notes=(
                        f"minimum detectable effect at 80% power "
                        f"{row.minimum_detectable_effect * 100:.2f} pp/yr, so this gap is "
                        f"{'resolved' if row.resolved else 'BELOW the resolution of the sample'}"
                        f"; materiality threshold {settings.materiality * 100:.2f} pp/yr; "
                        f"{unpriced}"
                    ),
                )
            )
    for benchmark, value in break_evens.items():
        if value is None:
            continue
        estimates.append(
            Estimate(
                name=f"break_even_haircut_on_{settings.haircut_sleeve}[vs {benchmark}]",
                value=value * 100.0,
                units="percentage points per year",
                cost_basis=basis,
                n_obs=None,
                notes=(
                    "the constant annual amount that can be subtracted from the sleeve's "
                    "arithmetic mean before the overlay stops beating this benchmark"
                ),
                uncertainty_unavailable_reason=(
                    "a deterministic function of the sample mean; its uncertainty is the "
                    "gap's and is reported there"
                ),
            )
        )
    for item in verdicts:
        if item.base_exposure != 1.5:
            continue
        estimates.append(
            Estimate(
                name=f"admission_margin[{item.sleeve} at L=1.5]",
                value=item.margin,
                units="ratio",
                cost_basis=basis,
                n_obs=None,
                notes=(
                    f"net Sharpe {item.net_sharpe:+.3f} against threshold L rho sigma_p = "
                    f"{item.threshold_sharpe:+.3f} (rho = {item.correlation:+.3f}); "
                    f"{'admitted' if item.admitted else 'REFUSED'}"
                ),
                uncertainty_unavailable_reason=(
                    "a plug-in comparison of two sample moments treated as known, which is "
                    "the flattering assumption overlay_growth records; the interval that "
                    "decides is on the portfolio gap"
                ),
            )
        )
    return tuple(estimates)


# --------------------------------------------------------------------------- #
# Registry and CLI
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def _render_console_report(outcome: RunOutcome) -> str:
    result = outcome.result
    if result is None:  # pragma: no cover - defensive
        return "no result"
    diagnostics = result.diagnostics
    lines: list[str] = [
        f"Experiment 011 -- {result.status.value}",
        str(diagnostics.get("verdict", "")),
        "",
        f"Window {diagnostics.get('window')}  n={diagnostics.get('months')}",
        "",
        "Sleeve moments, full window, annualised, excess of cash",
        f"  {'sleeve':<12}{'mean':>9}{'vol':>9}{'sharpe':>9}",
    ]
    moments = diagnostics.get("moments_full_window")
    if isinstance(moments, Mapping):
        for sleeve, payload in moments.items():
            row = _mapping(payload, where="moments")
            lines.append(
                f"  {sleeve:<12}"
                f"{float(str(row['arithmetic_excess_return'])) * 100:>8.2f}%"
                f"{float(str(row['volatility'])) * 100:>8.2f}%"
                f"{float(str(row['sharpe'])):>9.3f}"
            )
    lines.append("")
    lines.append("Portfolios, net of the declared costs, full window")
    lines.append(
        f"  {'portfolio':<30}{'geo':>8}{'vol':>8}{'sharpe':>8}{'maxDD':>8}{'under':>7}{'gross':>7}"
    )
    portfolios = diagnostics.get("portfolios_full_window")
    if isinstance(portfolios, Mapping):
        for name, payload in portfolios.items():
            row = _mapping(payload, where="portfolios")
            lines.append(
                f"  {name:<30}"
                f"{float(str(row['geometric_return'])) * 100:>7.2f}%"
                f"{float(str(row['volatility_of_excess_return'])) * 100:>7.2f}%"
                f"{float(str(row['sharpe'])):>8.3f}"
                f"{float(str(row['max_drawdown'])) * 100:>7.1f}%"
                f"{int(str(row['months_under_water'])):>7d}"
                f"{float(str(row['gross_notional'])):>7.2f}"
            )
    lines.append("")
    matched = diagnostics.get("matched_volatility")
    if isinstance(matched, Mapping):
        for benchmark, rows in matched.items():
            lines.append(f"Matched-volatility gap against {benchmark} (never added to the other)")
            for item in _sequence(rows, where="matched"):
                row = _mapping(item, where="matched[]")
                interval = row.get("interval")
                span = (
                    f"[{float(str(_sequence(interval, where='i')[0])) * 100:+.2f}, "
                    f"{float(str(_sequence(interval, where='i')[1])) * 100:+.2f}]"
                    if isinstance(interval, Sequence) and not isinstance(interval, str)
                    else "no interval"
                )
                lines.append(
                    f"  {row['portfolio']!s:<30}"
                    f"{float(str(row['gap'])) * 100:>+7.2f} pp/yr  {span:>20}  "
                    f"MDE {float(str(row['minimum_detectable_effect'])) * 100:.2f}"
                )
            lines.append("")
    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 011 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_011_overlay_stack",
        description=(
            "Price a financed overlay of non-equity return engines against the "
            "leverage-matched control, writing a ledger entry for the attempt."
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
                "exp_011_overlay_stack"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
