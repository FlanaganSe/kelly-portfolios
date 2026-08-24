"""Experiment 016: the construction tournament, run as a joint object.

What this is
------------
Fifteen specifications in this repository have scored one sleeve at a time.
None has ever scored a *portfolio*. Decision 0009 clause 4 unblocked this
experiment, three research pages say it should run, it needs no new data, and
until now nobody had run it.

It scores twenty-one constructions -- the investor's proposal under three
different stacked wrappers, the four candidates already in
``src/content/portfolios.ts``, the six weighting methods decision 0009 clause 4
names, three funding rules, and four constructions of this experiment's own
design -- against three benchmarks that are never combined.

What this is NOT
----------------
**It does not score funds.** No research-grade fund return series is committed
here (decision 0002), so every ticker is a BASIS EXPRESSION: a market leg, this
repository's own measured factor loadings, and a fee. The mapping is an
assumption. It is the largest single source of error in every number this module
produces, it is stated fund by fund in the frozen specification, and
:func:`perturbation_grid` measures how far the ranking moves when it is wrong.

**It cannot resolve most of what it measures.** The specification's MDE table is
arithmetic on the 427-month joint window and it was written before the data was
touched: an arm with 6 percentage points of tracking error cannot resolve an
effect below about 2.8 pp/yr here. The weighting-method comparisons track each
other closely and *are* resolvable; the stacked-wrapper comparisons are not.
That asymmetry is the most useful thing this experiment reports, and it is a
property of the design rather than a discovery.

**The trend leg is a vendor series.** AQR's TSMOM is author-maintained, rebuilt
in full on every update, and states no cost basis anywhere, so every trend
figure here is gross of the vendor's own trading costs by omission.

Run it::

    uv run python -m portfolio_edge.experiments.exp_016_construction_tournament \\
        --view-results
"""

from __future__ import annotations

import argparse
import itertools
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.portfolio import (
    equal_weights,
    inverse_volatility_weights,
    minimum_variance_weights,
    relative_risk_contributions,
)
from portfolio_edge.data import aqr, french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
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
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.multiple_testing import benjamini_hochberg

FloatArray = NDArray[np.float64]

ENTRY_POINT: Final = "exp_016_construction_tournament"
MONTHS_PER_YEAR: Final = 12

#: ``z(0.975) + z(0.80)``. Frozen in the specification; repeated here so that a
#: reader of either file sees the same constant.
MDE_MULTIPLIER: Final = 2.801585

#: MATE's prospectus contractual floor: 100% equity per dollar of capital, at
#: ``delta = 0.00``. The ``MATE`` arm prices the 2026-05-31 filing instead, at
#: 115.87% and ``delta = -0.159``. Both readings keep the whole funding-rule gap,
#: which is why the pair is run: the conclusion is robust where the point
#: estimate is not. The floor's futures leg is what the filing's 50.30% ETF
#: position leaves to make up, so 1.000 - 0.5030.
MATE_FLOOR_EQUITY: Final = 1.000
MATE_FLOOR_FUTURES: Final = 0.497

__all__ = [
    "ENTRY_POINT",
    "MDE_MULTIPLIER",
    "MONTHS_PER_YEAR",
    "ArmOutcome",
    "BasisPanel",
    "ConstructionTournamentError",
    "FundMapping",
    "build_registry",
    "constant_weight_path",
    "default_specification_path",
    "fund_excess_matrix",
    "gap_statistics",
    "ledoit_wolf_constant_correlation",
    "load_basis_panel",
    "main",
    "minimum_detectable_effect",
    "parse_basis_expression",
    "run",
    "walk_forward_weights",
]


class ConstructionTournamentError(Exception):
    """The tournament refused to run, or a source did not match its pin."""


# --------------------------------------------------------------------------- #
# Specification readers
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ConstructionTournamentError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ConstructionTournamentError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise ConstructionTournamentError(f"missing required key {where}.{key}")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise ConstructionTournamentError(f"{where}.{key} must be a non-empty string")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConstructionTournamentError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _optional_number(data: Mapping[str, JsonValue], key: str) -> float | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConstructionTournamentError(f"{key} must be a number or null, got {value!r}")
    return float(value)


def _numbers(value: JsonValue, *, where: str) -> tuple[float, ...]:
    items = _sequence(value, where=where)
    out: list[float] = []
    for index, item in enumerate(items):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ConstructionTournamentError(f"{where}[{index}] must be a number, got {item!r}")
        out.append(float(item))
    return tuple(out)


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_016_construction_tournament.yaml"


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


# --------------------------------------------------------------------------- #
# The basis panel
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BasisPanel:
    """Monthly basis series plus the cash rate, on one intersected window.

    Every series except ``cash`` is either an excess-of-cash return (the three
    regional market legs and the trend leg) or a self-financing long-short
    spread (every factor leg). Adding ``cash`` to a weighted combination of them
    gives a funded total return; nothing else in this module adds a cash rate
    anywhere.
    """

    periods: tuple[str, ...]
    series: Mapping[str, FloatArray]
    cash: FloatArray
    provenance: tuple[Mapping[str, JsonValue], ...]
    findings: tuple[str, ...]

    @property
    def months(self) -> int:
        return len(self.periods)

    @property
    def years(self) -> float:
        return self.months / MONTHS_PER_YEAR

    def column(self, name: str) -> FloatArray:
        try:
            return self.series[name]
        except KeyError:
            raise ConstructionTournamentError(
                f"no basis series {name!r}; the panel holds {sorted(self.series)}"
            ) from None

    def window(self, *, start: str, end: str) -> BasisPanel:
        first, last = month_index(start), month_index(end)
        keep = [i for i, p in enumerate(self.periods) if first <= month_index(p) <= last]
        if not keep:
            raise ConstructionTournamentError(f"the window {start}..{end} selects no months")
        index = np.asarray(keep, dtype=np.intp)
        return BasisPanel(
            periods=tuple(self.periods[i] for i in keep),
            series={name: values[index] for name, values in self.series.items()},
            cash=self.cash[index],
            provenance=self.provenance,
            findings=self.findings,
        )


def _load_pinned_file(
    pin: Mapping[str, JsonValue], *, cache: RawCache
) -> tuple[ParsedTable, dict[str, JsonValue], list[str]]:
    """Fetch, hash-pin, parse and validate one source file."""
    where = "parameters.source_pin.files[]"
    source = _text(pin, "source", where=where)
    dataset_id = _text(pin, "dataset_id", where=where)
    table_id = _text(pin, "table_id", where=where)

    if source == "french":
        dataset = french.get_dataset(dataset_id)
        url, parser_version = dataset.url, french.PARSER_VERSION
        entry = french.download(cache, dataset)
        _abort_on_raw_mismatch(pin, entry.sha256, url=url)
        table = french.parse(cache, entry, dataset=dataset).table(table_id)
    elif source == "aqr":
        aqr_dataset = aqr.get_dataset(dataset_id)
        url, parser_version = aqr_dataset.url, aqr.PARSER_VERSION
        entry = aqr.download(cache, aqr_dataset)
        _abort_on_raw_mismatch(pin, entry.sha256, url=url)
        table = aqr.parse(cache, entry, dataset=aqr_dataset).table
        if table.table_id != table_id:
            raise ConstructionTournamentError(
                f"{dataset_id}: the parsed table is {table.table_id!r} but the "
                f"specification pins {table_id!r}. The vendor's observation frequency "
                "has changed; freeze a new specification rather than reading it anyway."
            )
    else:
        raise ConstructionTournamentError(
            f"{where}.source is {source!r}; this experiment reads french and aqr"
        )

    report = validate_table(table, dataset_id=dataset_id, expected_frequency="monthly")
    findings = list(report.summary())
    if not report.ok:
        raise ConstructionTournamentError(
            "a source table failed validation before any statistic was computed: "
            + "; ".join(findings)
        )

    expected_normalized = _text(pin, "expected_sha256_normalized", where=where)
    if table.sha256_normalized() != expected_normalized:
        raise ConstructionTournamentError(
            f"{dataset_id}: the derived table hashes to {table.sha256_normalized()}, "
            f"but the specification pins {expected_normalized}. The raw bytes matched, "
            "so the parser changed behaviour. That is a finding, not a hash to update."
        )

    columns = tuple(str(name) for name in _sequence(_at(pin, "columns", where=where), where=where))
    missing = [name for name in columns if name not in table.columns]
    if missing:
        raise ConstructionTournamentError(
            f"{dataset_id}: column(s) {missing} are not in the parsed table, whose "
            f"columns are {list(table.columns)}. The source has renamed a series."
        )

    manifest_hash: str | None = None
    manifest_path = workspace_root() / _text(pin, "committed_manifest", where=where)
    if manifest_path.is_file():
        manifest = read_manifest(manifest_path)
        manifest_hash = manifest.sha256_manifest()
        if manifest.sha256_raw != entry.sha256:
            raise ConstructionTournamentError(
                f"{manifest_path} records sha256_raw {manifest.sha256_raw}, which is "
                f"not the {entry.sha256} that was actually read"
            )

    record: dict[str, JsonValue] = {
        "id": _text(pin, "id", where=where),
        "source": source,
        "dataset_id": dataset_id,
        "table_id": table.table_id,
        "columns": list(columns),
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


def _abort_on_raw_mismatch(pin: Mapping[str, JsonValue], observed: str, *, url: str) -> None:
    expected = _text(pin, "expected_sha256_raw", where="parameters.source_pin.files[]")
    if observed != expected:
        raise ConstructionTournamentError(
            f"the file at {url} now hashes to {observed}, but this specification is "
            f"frozen against {expected}. Ken French rebuilds from each CRSP vintage and "
            "AQR reconstructs its full history on every update, so this is a NEW VINTAGE "
            "rather than a corrupted download. Freeze a new specification against it "
            "instead of reporting numbers from an unrecognised file."
        )


#: Which pinned file and column supplies each basis series. The mapping is
#: fixed by the specification's ``universe.basis_series`` block; it is written
#: here as data so that the loader is a loop rather than sixteen branches.
_BASIS_SOURCES: Final[dict[str, tuple[str, str]]] = {
    "us_mkt": ("french_us_ff5", "Mkt-RF"),
    "us_smb": ("french_us_ff5", "SMB"),
    "us_hml": ("french_us_ff5", "HML"),
    "us_rmw": ("french_us_ff5", "RMW"),
    "us_cma": ("french_us_ff5", "CMA"),
    "us_umd": ("french_us_momentum", "Mom"),
    "dxus_mkt": ("french_developed_ex_us_ff5", "Mkt-RF"),
    "dxus_smb": ("french_developed_ex_us_ff5", "SMB"),
    "dxus_hml": ("french_developed_ex_us_ff5", "HML"),
    "dxus_rmw": ("french_developed_ex_us_ff5", "RMW"),
    "dxus_cma": ("french_developed_ex_us_ff5", "CMA"),
    "dxus_umd": ("french_developed_ex_us_momentum", "WML"),
    "em_mkt": ("french_emerging_ff5", "Mkt-RF"),
    "em_hml": ("french_emerging_ff5", "HML"),
    "trend": ("aqr_tsmom_factors", "TSMOM"),
}

_CASH_SOURCE: Final = ("french_us_ff5", "RF")


def load_basis_panel(specification: Specification) -> BasisPanel:
    """Build the intersected basis panel from the pinned source files."""
    parameters = _mapping(specification.parameters, where="parameters")
    pin_block = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    entries = _sequence(_at(pin_block, "files", where="source_pin"), where="source_pin.files")

    cache = RawCache()
    start, end = specification.sample_policy.start, specification.sample_policy.end
    first, last = month_index(start), month_index(end)

    tables: dict[str, ParsedTable] = {}
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []
    for item in entries:
        pin = _mapping(item, where="source_pin.files[]")
        table, record, table_findings = _load_pinned_file(pin, cache=cache)
        file_id = str(record["id"])
        if file_id in tables:
            raise ConstructionTournamentError(f"file {file_id!r} is pinned twice")
        tables[file_id] = table
        provenance.append(record)
        findings.extend(f"{file_id}: {finding}" for finding in table_findings)

    def read(file_id: str, column: str) -> dict[str, float]:
        if file_id not in tables:
            raise ConstructionTournamentError(f"basis series needs unpinned file {file_id!r}")
        table = tables[file_id]
        values = table.column(column)
        return {
            period: float(value)
            for period, value in zip(table.periods, values, strict=True)
            if value is not None and first <= month_index(period) <= last
        }

    built = {name: read(*where) for name, where in _BASIS_SOURCES.items()}
    cash_series = read(*_CASH_SOURCE)

    common = set(cash_series)
    for observations in built.values():
        common &= set(observations)
    periods = tuple(sorted(common))
    if not periods:
        raise ConstructionTournamentError("the pinned series have no month in common")

    series = {
        name: np.array([values[period] for period in periods], dtype=np.float64)
        for name, values in built.items()
    }
    cash = np.array([cash_series[period] for period in periods], dtype=np.float64)
    for name, column in series.items():
        if not np.all(np.isfinite(column)):
            raise ConstructionTournamentError(f"basis series {name!r} holds a non-finite value")
    if not np.all(np.isfinite(cash)):
        raise ConstructionTournamentError("the cash series holds a non-finite value")

    starts = {name: min(built[name]) for name in built}
    ends = {name: max(built[name]) for name in built}
    binding_start = max(starts, key=lambda name: month_index(starts[name]))
    binding_end = min(ends, key=lambda name: month_index(ends[name]))
    findings.append(
        f"the intersected panel is {len(periods)} months, {periods[0]}..{periods[-1]}. "
        f"The start is set by {binding_start} ({starts[binding_start]}) and the end by "
        f"{binding_end} ({ends[binding_end]}). Neither boundary was chosen."
    )
    return BasisPanel(
        periods=periods,
        series=series,
        cash=cash,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# The mapping layer: ticker -> basis expression
# --------------------------------------------------------------------------- #

_TERM: Final = re.compile(r"([+-]?)\s*([0-9]*\.?[0-9]+)\s*\*\s*([A-Za-z_][A-Za-z0-9_]*)")

#: Basis legs that consume capital and therefore count towards gross notional.
#: A long-short factor spread does not; a market leg and the trend leg do.
_NOTIONAL_LEGS: Final = frozenset({"us_mkt", "dxus_mkt", "em_mkt", "trend"})


def parse_basis_expression(expression: str, *, where: str) -> dict[str, float]:
    """Parse ``1.000 * us_mkt + 0.322 * us_hml`` into coefficients.

    The coefficients live in the frozen specification and therefore in its hash,
    which is the point: a mapping change is a specification change.
    """
    text = " ".join(expression.split())
    coefficients: dict[str, float] = {}
    consumed = 0
    for match in _TERM.finditer(text):
        sign, magnitude, name = match.groups()
        if name in coefficients:
            raise ConstructionTournamentError(f"{where}: series {name!r} appears twice")
        coefficients[name] = (-1.0 if sign == "-" else 1.0) * float(magnitude)
        consumed += len(text[match.start() : match.end()])
    leftover = _TERM.sub("", text).replace("+", "").replace("-", "").strip()
    if leftover or not coefficients:
        raise ConstructionTournamentError(
            f"{where}: could not parse basis expression {expression!r}; the grammar is "
            "'<number> * <series>' terms joined by + or -"
        )
    unknown = sorted(set(coefficients) - set(_BASIS_SOURCES))
    if unknown:
        raise ConstructionTournamentError(
            f"{where}: expression names series {unknown} that the panel does not hold"
        )
    return coefficients


@dataclass(frozen=True, slots=True, kw_only=True)
class FundMapping:
    """One ticker's basis expression and its costs.

    ``alpha_less_pedestal_pp_yr`` is ``None`` when no alpha was measured for the
    fund anywhere in this repository. ``None`` and ``0.0`` are different claims
    and the artifact prints them differently.
    """

    ticker: str
    coefficients: Mapping[str, float]
    expense_ratio_bp: float
    futures_notional: float
    spread_region: str
    alpha_less_pedestal_pp_yr: float | None
    distribution_tax_drag_pp_yr: float | None
    incremental_tax_drag_bp: float | None
    structure_assumed: bool
    fee_assumed: bool

    @property
    def gross_notional(self) -> float:
        return sum(abs(c) for name, c in self.coefficients.items() if name in _NOTIONAL_LEGS)


def _build_mappings(specification: Specification) -> dict[str, FundMapping]:
    """Read every fund's mapping out of the frozen specification."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "fund_mapping", where="parameters"), where="fund_mapping")
    entries = _sequence(_at(block, "funds", where="fund_mapping"), where="fund_mapping.funds")
    costs = _mapping(specification.cost_model, where="cost_model")
    fees = _mapping(_at(costs, "fund_expense_ratio_basis_points", where="cost_model"), where="fees")
    regions = _mapping(_at(costs, "spread_region_by_ticker", where="cost_model"), where="regions")
    alphas = _mapping(
        _at(costs, "measured_alpha_less_pedestal_pp_yr", where="cost_model"), where="alphas"
    )
    drags = _mapping(_at(costs, "distribution_tax_drag_pp_yr", where="cost_model"), where="drags")
    incremental = _mapping(
        _at(costs, "incremental_distribution_tax_drag_bp", where="cost_model"), where="incremental"
    )
    assumed_fee_grid = _mapping(
        _at(parameters, "assumed_fee_grid", where="parameters"), where="assumed_fee_grid"
    )

    mappings: dict[str, FundMapping] = {}
    for index, item in enumerate(entries):
        entry = _mapping(item, where=f"fund_mapping.funds[{index}]")
        ticker = _text(entry, "ticker", where=f"fund_mapping.funds[{index}]")
        coefficients = parse_basis_expression(
            _text(entry, "expression", where=f"fund_mapping.funds[{index}]"),
            where=f"fund_mapping.funds[{index}]",
        )
        mappings[ticker] = FundMapping(
            ticker=ticker,
            coefficients=coefficients,
            expense_ratio_bp=_number(fees, ticker, where="cost_model.fund_expense_ratio"),
            futures_notional=_optional_number(entry, "futures_notional_for_financing") or 0.0,
            spread_region=_text(regions, ticker, where="cost_model.spread_region_by_ticker"),
            alpha_less_pedestal_pp_yr=_optional_number(alphas, ticker),
            distribution_tax_drag_pp_yr=_optional_number(drags, ticker),
            incremental_tax_drag_bp=_optional_number(incremental, ticker),
            structure_assumed=bool(entry.get("structure_assumed", False)),
            fee_assumed=ticker in assumed_fee_grid,
        )

    # Three synthetic holdings the tournament needs and no filing describes.
    # Each is declared in the specification's fee table and region map, so none
    # of them can carry a cost that is not in the hash.
    mate = mappings["MATE"]
    floor = dict(mate.coefficients)
    floor["us_mkt"] = MATE_FLOOR_EQUITY
    mappings["MATE_FLOOR"] = FundMapping(
        ticker="MATE_FLOOR",
        coefficients=floor,
        expense_ratio_bp=_number(fees, "MATE_FLOOR", where="cost_model.fund_expense_ratio"),
        futures_notional=MATE_FLOOR_FUTURES,
        spread_region=_text(regions, "MATE_FLOOR", where="cost_model.spread_region_by_ticker"),
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=True,
        fee_assumed=False,
    )
    mappings["TREND"] = FundMapping(
        ticker="TREND",
        coefficients={"trend": 1.0},
        expense_ratio_bp=_number(fees, "TREND", where="cost_model.fund_expense_ratio"),
        futures_notional=0.0,
        spread_region=_text(regions, "TREND", where="cost_model.spread_region_by_ticker"),
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=True,
    )
    mappings["CASH"] = FundMapping(
        ticker="CASH",
        coefficients={},
        expense_ratio_bp=_number(fees, "CASH", where="cost_model.fund_expense_ratio"),
        futures_notional=0.0,
        spread_region=_text(regions, "CASH", where="cost_model.spread_region_by_ticker"),
        alpha_less_pedestal_pp_yr=None,
        distribution_tax_drag_pp_yr=None,
        incremental_tax_drag_bp=None,
        structure_assumed=False,
        fee_assumed=False,
    )
    return mappings


@dataclass(frozen=True, slots=True, kw_only=True)
class CostSettings:
    """Every cost this experiment charges, read from the frozen specification."""

    equity_futures_basis: float
    """Annual decimal, charged on futures notional."""
    trend_book_financing: float
    round_trip_spread: Mapping[str, float]
    """Basis points, by region key."""

    def spread_for(self, region: str) -> float:
        try:
            return self.round_trip_spread[region]
        except KeyError:
            raise ConstructionTournamentError(f"no round-trip spread for {region!r}") from None


def _cost_settings(specification: Specification) -> CostSettings:
    costs = _mapping(specification.cost_model, where="cost_model")
    spreads = _mapping(
        _at(costs, "round_trip_spread_basis_points", where="cost_model"), where="spreads"
    )
    return CostSettings(
        equity_futures_basis=(
            _number(costs, "equity_index_futures_basis_annual_percent", where="cost_model") / 100.0
        ),
        trend_book_financing=(
            _number(costs, "trend_book_financing_annual_percent", where="cost_model") / 100.0
        ),
        round_trip_spread={
            key: _number(spreads, key, where="cost_model.round_trip_spread")
            for key in spreads
        },
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class MappingShift:
    """One point of the perturbation grid. All zeros is the central mapping."""

    loading_delta: float = 0.0
    trend_multiplier: float = 1.0
    vxus_developed_share: float | None = None
    trend_haircut_pp_yr: float = 0.0
    value_haircut_pp_yr: float = 0.0
    equity_haircut_pp_yr: float = 0.0
    """Subtracted from every regional market leg, so that a forward-premium
    substitution can be made CONSISTENTLY.

    Replacing one premium with a forward estimate while leaving another at its
    realised value is a fitted comparator deciding a verdict, which
    `docs/research/search-coverage.md` already lists among the designs not worth
    repeating. Whatever is done to the trend leg has to be doable to the equity
    leg in the same sweep, and this is the parameter that makes it possible.
    """
    charge_measured_alpha: bool = False
    fee_override_bp: Mapping[str, float] = field(default_factory=dict)
    financing_basis_annual_percent: float | None = None
    """Replaces the equity-index-futures basis everywhere it is charged.

    Nobody discloses a cleared-futures wrapper's financing cost and nobody
    structurally can, because it lives in the contract's basis rather than in the
    income statement. It is therefore the one load-bearing cost in this
    tournament that is unobservable rather than merely unmeasured, and the arm
    ordering has to be reported across a band of it rather than at a point.
    """

    @property
    def is_central(self) -> bool:
        return (
            self.loading_delta == 0.0
            and self.trend_multiplier == 1.0
            and self.vxus_developed_share is None
            and self.trend_haircut_pp_yr == 0.0
            and self.value_haircut_pp_yr == 0.0
            and self.equity_haircut_pp_yr == 0.0
            and not self.charge_measured_alpha
            and not self.fee_override_bp
            and self.financing_basis_annual_percent is None
        )

    def label(self) -> str:
        if self.is_central:
            return "central"
        parts = []
        if self.loading_delta:
            parts.append(f"loading{self.loading_delta:+.2f}")
        if self.trend_multiplier != 1.0:
            parts.append(f"trendx{self.trend_multiplier:.2f}")
        if self.vxus_developed_share is not None:
            parts.append(f"vxus{self.vxus_developed_share:.2f}")
        if self.trend_haircut_pp_yr:
            parts.append(f"trendcut{self.trend_haircut_pp_yr:.1f}")
        if self.value_haircut_pp_yr:
            parts.append(f"valuecut{self.value_haircut_pp_yr:.1f}")
        if self.equity_haircut_pp_yr:
            parts.append(f"equitycut{self.equity_haircut_pp_yr:.1f}")
        if self.charge_measured_alpha:
            parts.append("alpha-charged")
        for ticker, fee in sorted(self.fee_override_bp.items()):
            parts.append(f"{ticker}fee{fee:.0f}")
        if self.financing_basis_annual_percent is not None:
            parts.append(f"financing{self.financing_basis_annual_percent:.2f}")
        return ",".join(parts)

    def applied_to(self, costs: CostSettings) -> CostSettings:
        """The cost settings this shift implies. Identity unless it overrides financing."""
        if self.financing_basis_annual_percent is None:
            return costs
        return replace(
            costs, equity_futures_basis=self.financing_basis_annual_percent / 100.0
        )


_VALUE_LEGS: Final = frozenset({"us_hml", "dxus_hml", "em_hml"})
_MARKET_LEGS: Final = frozenset({"us_mkt", "dxus_mkt", "em_mkt"})


def fund_excess_matrix(
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    *,
    tickers: Sequence[str],
    shift: MappingShift,
) -> FloatArray:
    """Monthly excess-of-cash returns for each ticker, net of its own costs.

    Shape ``(T, len(tickers))``. Each column is
    ``sum_k c_k * basis_k - fee/12 - futures_basis * futures_notional / 12``,
    with the perturbation ``shift`` applied to the coefficients and to the two
    haircut legs before anything is summed.
    """
    costs = shift.applied_to(costs)
    columns: list[FloatArray] = []
    for ticker in tickers:
        try:
            mapping = mappings[ticker]
        except KeyError:
            raise ConstructionTournamentError(f"no mapping for ticker {ticker!r}") from None
        total = np.zeros(panel.months, dtype=np.float64)
        for name, raw in mapping.coefficients.items():
            coefficient = raw
            if name == "trend":
                coefficient *= shift.trend_multiplier
            elif name not in _MARKET_LEGS and shift.loading_delta:
                coefficient += shift.loading_delta * math.copysign(1.0, raw)
            if ticker == "VXUS" and shift.vxus_developed_share is not None:
                if name == "dxus_mkt":
                    coefficient = shift.vxus_developed_share
                elif name == "em_mkt":
                    coefficient = 1.0 - shift.vxus_developed_share
            leg = panel.column(name)
            if name == "trend" and shift.trend_haircut_pp_yr:
                leg = leg - shift.trend_haircut_pp_yr / (100.0 * MONTHS_PER_YEAR)
            elif name in _VALUE_LEGS and shift.value_haircut_pp_yr:
                leg = leg - shift.value_haircut_pp_yr / (100.0 * MONTHS_PER_YEAR)
            elif name in _MARKET_LEGS and shift.equity_haircut_pp_yr:
                leg = leg - shift.equity_haircut_pp_yr / (100.0 * MONTHS_PER_YEAR)
            total = total + coefficient * leg

        fee_bp = shift.fee_override_bp.get(ticker, mapping.expense_ratio_bp)
        annual_charge = fee_bp / 10_000.0
        annual_charge += costs.equity_futures_basis * mapping.futures_notional
        annual_charge += costs.trend_book_financing * abs(
            mapping.coefficients.get("trend", 0.0) * shift.trend_multiplier
        )
        if shift.charge_measured_alpha and mapping.alpha_less_pedestal_pp_yr is not None:
            annual_charge -= mapping.alpha_less_pedestal_pp_yr / 100.0
        columns.append(total - annual_charge / MONTHS_PER_YEAR)
    return np.column_stack(columns) if columns else np.zeros((panel.months, 0), dtype=np.float64)


# --------------------------------------------------------------------------- #
# Contestants
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Contestant:
    """One arm of the tournament."""

    name: str
    role: str
    benchmark: str
    tickers: tuple[str, ...]
    weights: tuple[float, ...]
    """Target weights. They sum to more than one exactly when the arm borrows."""
    method: str = ""
    engines: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    gross_notional_cap: float | None = None
    note: str = ""

    @property
    def is_estimated(self) -> bool:
        return bool(self.method)

    @property
    def capital_leverage(self) -> float:
        return float(sum(self.weights))


def _read_contestants(specification: Specification) -> dict[str, Contestant]:
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "contestants", where="parameters"), where="contestants")
    out: dict[str, Contestant] = {}
    for name in block:
        entry = _mapping(block[name], where=f"contestants.{name}")
        raw_method = entry.get("method")
        method = str(raw_method) if isinstance(raw_method, str) else ""
        leverage = _optional_number(entry, "leverage") or 1.0
        tickers: tuple[str, ...] = ()
        weights: tuple[float, ...] = ()
        engines: dict[str, Mapping[str, float]] = {}
        if "weights" in entry:
            raw = _mapping(entry["weights"], where=f"contestants.{name}.weights")
            tickers = tuple(raw)
            weights = tuple(
                _number(raw, ticker, where=f"contestants.{name}.weights") * leverage
                for ticker in tickers
            )
        elif "sleeves" in entry:
            tickers = tuple(
                str(item)
                for item in _sequence(entry["sleeves"], where=f"contestants.{name}.sleeves")
            )
            weights = tuple(1.0 / len(tickers) for _ in tickers)
        elif "engines" in entry:
            raw_engines = _mapping(entry["engines"], where=f"contestants.{name}.engines")
            for engine in raw_engines:
                members = _mapping(raw_engines[engine], where=f"engines.{engine}")
                engines[engine] = {
                    ticker: _number(members, ticker, where=f"engines.{engine}")
                    for ticker in members
                }
            tickers = tuple(
                dict.fromkeys(
                    ticker for members in engines.values() for ticker in members
                )
            )
            weights = tuple(1.0 / len(tickers) for _ in tickers)
        else:
            raise ConstructionTournamentError(
                f"contestants.{name} declares neither weights, sleeves nor engines"
            )
        out[name] = Contestant(
            name=name,
            role=str(entry.get("role") or "candidate"),
            benchmark=str(entry.get("benchmark") or ""),
            tickers=tickers,
            weights=weights,
            method=method,
            engines=engines,
            gross_notional_cap=_optional_number(entry, "gross_notional_cap"),
            note=str(entry.get("note") or ""),
        )
    return out


# --------------------------------------------------------------------------- #
# Weighting methods
# --------------------------------------------------------------------------- #


def ledoit_wolf_constant_correlation(returns: FloatArray) -> tuple[FloatArray, float]:
    """Linear shrinkage of the sample covariance to a constant-correlation target.

    Ledoit and Wolf (2003, 2004). The target keeps every sample variance and
    replaces every correlation by the average sample correlation; the intensity
    is the estimated ratio of the target's dispersion to its distance from the
    sample matrix, clipped to ``[0, 1]``. Returns the shrunk matrix and the
    intensity, because an intensity of 1 means the sample matrix contributed
    nothing and that is worth seeing.
    """
    if returns.ndim != 2:
        raise ConstructionTournamentError("shrinkage needs a (T, N) return matrix")
    n_obs, n_assets = returns.shape
    if n_obs < 2 or n_assets < 2:
        raise ConstructionTournamentError("shrinkage needs at least two rows and two columns")
    centred = returns - returns.mean(axis=0, keepdims=True)
    sample = (centred.T @ centred) / n_obs
    variances = np.diag(sample).copy()
    sigmas = np.sqrt(variances)
    outer = np.outer(sigmas, sigmas)
    correlations = sample / outer
    off_diagonal = ~np.eye(n_assets, dtype=bool)
    mean_correlation = float(correlations[off_diagonal].mean())
    target = mean_correlation * outer
    np.fill_diagonal(target, variances)

    # pi: sum of asymptotic variances of the sample covariance entries.
    squared = centred**2
    pi_matrix = (squared.T @ squared) / n_obs - sample**2
    pi = float(pi_matrix.sum())

    # rho: covariance between the sample entries and the target's estimation error.
    theta = np.zeros((n_assets, n_assets), dtype=np.float64)
    for i in range(n_assets):
        cross = (centred[:, i : i + 1] ** 2 * centred).mean(axis=0) - variances[i] * sample[i]
        theta[i, :] = cross
    rho = float(np.diag(pi_matrix).sum())
    for i in range(n_assets):
        for j in range(n_assets):
            if i == j:
                continue
            rho += (
                mean_correlation
                * 0.5
                * (
                    (sigmas[j] / sigmas[i]) * theta[i, j]
                    + (sigmas[i] / sigmas[j]) * theta[j, i]
                )
            )

    gamma = float(((target - sample) ** 2).sum())
    intensity = 0.0 if gamma <= 0.0 else float(np.clip((pi - rho) / gamma / n_obs, 0.0, 1.0))
    shrunk = intensity * target + (1.0 - intensity) * sample
    return np.asarray(shrunk, dtype=np.float64), intensity


def _unit_scaled(covariance: FloatArray) -> FloatArray:
    """``Sigma`` divided by its mean variance, so its diagonal is order one.

    Every weighting method here is scale-invariant: multiplying ``Sigma`` by a
    constant multiplies the solution by a constant and normalising removes it.
    Monthly covariances of equity returns have entries around 2e-3, and the
    equal-risk-contribution solver's convergence tolerance is ABSOLUTE, so on
    the raw matrix it is asking for a gradient a billion times smaller than the
    one it would ask for on an annualised matrix. Scaling makes the tolerance
    mean the same thing at any units. This is a conditioning fix and not a
    loosened tolerance: the tolerance itself is untouched.
    """
    mean_variance = float(np.mean(np.diag(covariance)))
    if mean_variance <= 0.0:
        raise ConstructionTournamentError("a covariance matrix with no variance on it")
    return np.asarray(covariance / mean_variance, dtype=np.float64)


def _method_weights(method: str, returns: FloatArray) -> tuple[FloatArray, float]:
    """Long-only weights for one estimation window. Returns weights and shrinkage."""
    n_assets = returns.shape[1]
    if method == "equal_weight":
        return equal_weights(n_assets), 0.0
    covariance = np.cov(returns, rowvar=False, ddof=1)
    if method == "inverse_volatility":
        return inverse_volatility_weights(covariance), 0.0
    if method == "minimum_variance_long_only":
        return minimum_variance_weights(_unit_scaled(covariance), long_only=True), 0.0
    if method == "minimum_variance_shrunk":
        shrunk, intensity = ledoit_wolf_constant_correlation(returns)
        return minimum_variance_weights(_unit_scaled(shrunk), long_only=True), intensity
    if method in {"equal_risk_contribution", "equal_risk_contribution_engines"}:
        return _verified_erc(_unit_scaled(covariance)), 0.0
    raise ConstructionTournamentError(f"unknown weighting method {method!r}")


#: How far the risk contributions of the returned weights may spread. This is the
#: quantity the method is named after, and it is checked directly on every call.
_ERC_RISK_SPREAD_TOLERANCE: Final = 1e-8
_ERC_MAX_SWEEPS: Final = 5_000
_ERC_STEP_TOLERANCE: Final = 1e-14


def _verified_erc(covariance: FloatArray) -> FloatArray:
    """Equal-risk-contribution weights by cyclical coordinate descent, verified.

    ``portfolio_edge.core.portfolio.equal_risk_contribution_weights`` is the
    canonical definition and it solves the same fixed point by Newton descent on
    the log barrier. Its convergence bound is an ABSOLUTE 1e-12 on
    ``max|Sigma x - 1/x|``, and on this panel that bound is not attainable in
    float64 for every one of the several thousand estimation windows the
    perturbation grid asks for: a handful fail, always at the same conditioning.
    Loosening that bound to obtain a pass is the move this repository forbids,
    so it is not loosened. Instead the same stationarity condition
    ``x_i (Sigma x)_i = 1`` is solved coordinate by coordinate -- for each ``i``
    the condition is a quadratic in ``x_i`` with one positive root -- which is
    unconditionally stable for positive semi-definite ``Sigma``, and the answer
    is then checked on the risk contributions themselves. A unit test pins this
    solver against the canonical one wherever the canonical one converges.
    """
    n_assets = covariance.shape[0]
    variances = np.diag(covariance)
    if np.any(variances <= 0.0):
        raise ConstructionTournamentError("a covariance matrix with a non-positive variance")
    x = 1.0 / (np.sqrt(variances) * n_assets)
    for _ in range(_ERC_MAX_SWEEPS):
        previous = x.copy()
        for i in range(n_assets):
            others = float(covariance[i] @ x) - float(covariance[i, i] * x[i])
            a = float(variances[i])
            x[i] = (-others + math.sqrt(others * others + 4.0 * a)) / (2.0 * a)
        if float(np.max(np.abs(x - previous))) <= _ERC_STEP_TOLERANCE * float(np.max(x)):
            break
    else:  # pragma: no cover - defensive
        raise ConstructionTournamentError(
            f"equal risk contribution did not settle in {_ERC_MAX_SWEEPS} sweeps"
        )
    weights = np.asarray(x / float(np.sum(x)), dtype=np.float64)
    contributions = relative_risk_contributions(weights, covariance)
    spread = float(np.max(contributions) - np.min(contributions))
    if spread > _ERC_RISK_SPREAD_TOLERANCE:
        raise ConstructionTournamentError(
            f"equal risk contribution returned weights whose risk contributions "
            f"spread by {spread:.3e}, above the {_ERC_RISK_SPREAD_TOLERANCE:.0e} this "
            "experiment requires"
        )
    return weights


def walk_forward_weights(
    excess: FloatArray,
    *,
    method: str,
    minimum_months: int,
    reapply_every: int,
) -> tuple[FloatArray, int, tuple[float, ...]]:
    """Target weights per month from an expanding estimation window.

    Returns ``(targets, first_scored_month, shrinkage_intensities)``. The
    estimate for month ``t`` uses data through ``t - 1`` only, and is held for
    ``reapply_every`` months. No month is ever scored by a covariance matrix
    that saw it.
    """
    n_obs, n_assets = excess.shape
    if n_obs <= minimum_months:
        raise ConstructionTournamentError(
            f"{n_obs} months cannot support a {minimum_months}-month estimation window"
        )
    targets = np.zeros((n_obs, n_assets), dtype=np.float64)
    intensities: list[float] = []
    current = np.zeros(n_assets, dtype=np.float64)
    for t in range(minimum_months, n_obs):
        if (t - minimum_months) % reapply_every == 0:
            current, intensity = _method_weights(method, excess[:t, :])
            intensities.append(intensity)
        targets[t, :] = current
    return targets, minimum_months, tuple(intensities)


# --------------------------------------------------------------------------- #
# Simulation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioPath:
    """One arm's funded monthly path and the burden of running it."""

    total: FloatArray
    """Monthly funded total return, net of every charged cost."""
    excess: FloatArray
    gross_notional: float
    annual_turnover: float
    weighted_fee_bp: float
    n_funds: int


def constant_weight_path(
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    *,
    tickers: Sequence[str],
    targets: FloatArray,
    first_month: int = 0,
    rebalance_every: int = MONTHS_PER_YEAR,
) -> PortfolioPath:
    """Simulate an arm, letting weights drift and rebalancing on a fixed clock.

    ``targets`` is either a one-dimensional vector of constant targets or a
    ``(T, N)`` matrix of walk-forward targets. Weights drift with returns
    between rebalances, because a constant-weight simulation that silently
    rebalances every month at no charge is not a portfolio anyone holds.
    """
    excess = fund_excess_matrix(panel, mappings, costs, tickers=tickers, shift=MappingShift())
    return _simulate(
        panel,
        mappings,
        costs,
        tickers=tickers,
        excess=excess,
        targets=targets,
        first_month=first_month,
        rebalance_every=rebalance_every,
    )


def _simulate(
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    *,
    tickers: Sequence[str],
    excess: FloatArray,
    targets: FloatArray,
    first_month: int,
    rebalance_every: int,
) -> PortfolioPath:
    """Carry absolute positions and absolute debt, not weights.

    Weights are the wrong state variable for a levered portfolio. A trading cost
    is paid out of the positions and leaves the borrowing untouched, so a
    simulation that renormalises weights after charging a cost quietly changes
    the leverage; a drawdown raises gross exposure and a rebalancing cost does
    not, and only one of those two is a real property of the construction.
    Positions and debt make both come out right by construction:

        positions[t+1] = positions[t] * (1 + cash + excess)
        debt[t+1]      = debt[t] * (1 + cash + financing spread)
        equity         = sum(positions) - debt
    """
    n_obs = panel.months
    n_assets = len(tickers)
    constant = targets.ndim == 1
    if constant and targets.shape != (n_assets,):
        raise ConstructionTournamentError("constant targets must have one entry per ticker")
    if not constant and targets.shape != (n_obs, n_assets):
        raise ConstructionTournamentError("walk-forward targets must be (T, N)")

    spreads = np.array(
        [costs.spread_for(mappings[t].spread_region) / 10_000.0 for t in tickers],
        dtype=np.float64,
    )
    fees = np.array([mappings[t].expense_ratio_bp for t in tickers], dtype=np.float64)
    notionals = np.array([mappings[t].gross_notional for t in tickers], dtype=np.float64)
    monthly_spread = costs.equity_futures_basis / MONTHS_PER_YEAR

    total = np.zeros(n_obs, dtype=np.float64)
    excess_path = np.zeros(n_obs, dtype=np.float64)
    positions = np.zeros(n_assets, dtype=np.float64)
    debt = 0.0
    equity = 1.0
    turnover_total = 0.0
    fee_accumulator = 0.0
    notional_accumulator = 0.0
    scored = 0

    for t in range(first_month, n_obs):
        target = np.asarray(targets if constant else targets[t, :], dtype=np.float64)
        opening = equity
        if (t - first_month) % rebalance_every == 0:
            wanted = target * equity
            trade = np.abs(wanted - positions)
            # The entry trade is not charged: every arm is scored from a common
            # starting portfolio and the trade that establishes it is not part of
            # the comparison. Every later rebalance is charged in full.
            cost = 0.0 if t == first_month else float(np.sum(trade * spreads) / 2.0)
            turnover_total += 0.0 if t == first_month else 0.5 * float(np.sum(trade)) / equity
            # The cost is paid by selling assets pro rata: gross exposure and
            # equity both fall by it, and the borrowing does not move.
            gross = float(np.sum(wanted))
            positions = wanted - (cost * wanted / gross if gross > 0.0 else 0.0)
            debt = float(np.sum(positions)) - (equity - cost)
            equity -= cost

        weights = positions / equity
        fee_accumulator += float(weights @ fees)
        notional_accumulator += float(weights @ notionals)
        scored += 1

        positions = positions * (1.0 + panel.cash[t] + excess[t, :])
        debt = debt * (1.0 + panel.cash[t] + max(0.0, monthly_spread))
        equity = float(np.sum(positions)) - debt
        if equity <= 0.0:
            raise ConstructionTournamentError(
                f"arm equity went non-positive at {panel.periods[t]}"
            )
        total[t] = equity / opening - 1.0
        excess_path[t] = total[t] - panel.cash[t]

    if scored == 0:  # pragma: no cover - defensive
        raise ConstructionTournamentError("the arm scored no months")
    years = scored / MONTHS_PER_YEAR
    absolute = np.abs(np.asarray(targets, dtype=np.float64))
    held = absolute if constant else absolute.max(axis=0)
    held_count = int(np.sum(held > 1e-9))
    return PortfolioPath(
        total=total[first_month:],
        excess=excess_path[first_month:],
        gross_notional=notional_accumulator / scored,
        annual_turnover=turnover_total / years,
        weighted_fee_bp=fee_accumulator / scored,
        n_funds=held_count,
    )


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def annualised_log_growth(total: FloatArray) -> float:
    """Annualised continuously compounded growth, in percentage points."""
    if np.any(total <= -1.0):
        raise ConstructionTournamentError("a monthly total return of -100% or worse")
    return float(np.mean(np.log1p(total))) * MONTHS_PER_YEAR * 100.0


def minimum_detectable_effect(difference: FloatArray) -> float:
    """``2.801585 * sigma_gap / sqrt(years)`` in pp/yr, from the paired series.

    Identical to ``1200 * sd(d) / sqrt(T)``: the annualisation in the numerator
    and the year count in the denominator cancel to a factor of twelve.
    """
    n = difference.size
    if n < 2:
        raise ConstructionTournamentError("MDE needs at least two observations")
    standard_error = float(np.std(difference, ddof=1)) / math.sqrt(n)
    return MDE_MULTIPLIER * 100.0 * MONTHS_PER_YEAR * standard_error


def years_to_distinguish(gap_pp_yr: float, difference: FloatArray) -> float:
    """Holding period at which this design's floor falls to ``gap_pp_yr``.

    The inversion of the minimum-detectable-effect formula:
    ``years = (2.801585 sigma_gap / gap)**2``. It answers the question an
    investor actually faces. A figure beyond a human investing horizon means the
    ranking is a ranking of expected values whose differences are unobservable to
    the person holding them.
    """
    if gap_pp_yr == 0.0:
        return float("inf")
    annual_sigma = float(np.std(difference, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0
    return (MDE_MULTIPLIER * annual_sigma / abs(gap_pp_yr)) ** 2


@dataclass(frozen=True, slots=True, kw_only=True)
class GapStatistics:
    """One arm-against-benchmark comparison, with everything a verdict needs."""

    gap_pp_yr: float
    interval: tuple[float, float]
    mde_pp_yr: float
    mde_bootstrap_pp_yr: float
    p_value: float
    tracking_error_pct: float
    months: int
    years_to_distinguish: float


def gap_statistics(
    arm_total: FloatArray,
    benchmark_total: FloatArray,
    *,
    indices: NDArray[np.intp],
    confidence: float,
) -> GapStatistics:
    """The growth gap, its bootstrap interval, its MDE and its p-value."""
    if arm_total.shape != benchmark_total.shape:
        raise ConstructionTournamentError("arm and benchmark must cover the same months")
    difference = np.log1p(arm_total) - np.log1p(benchmark_total)
    gap = float(np.mean(difference)) * MONTHS_PER_YEAR * 100.0
    resampled = difference[indices].mean(axis=1) * MONTHS_PER_YEAR * 100.0
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(resampled, [tail, 1.0 - tail])
    centred = resampled - gap
    exceed = int(np.sum(np.abs(centred) >= abs(gap)))
    p_value = (exceed + 1) / (resampled.size + 1)
    return GapStatistics(
        gap_pp_yr=gap,
        interval=(float(low), float(high)),
        mde_pp_yr=minimum_detectable_effect(difference),
        mde_bootstrap_pp_yr=MDE_MULTIPLIER * float(np.std(resampled, ddof=1)),
        p_value=float(p_value),
        tracking_error_pct=float(np.std(difference, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
        months=difference.size,
        years_to_distinguish=years_to_distinguish(gap, difference),
    )


def underperformance(
    arm_total: FloatArray,
    benchmark_total: FloatArray,
    *,
    years: int,
    rng: np.random.Generator,
    block_months: float,
    draws: int,
) -> tuple[float, float]:
    """``P(underperform over the horizon)`` and the median annualised shortfall.

    A probability without its magnitude is half a result, so both come back
    together and the artifact prints them in the same row.
    """
    difference = np.log1p(arm_total) - np.log1p(benchmark_total)
    horizon = years * MONTHS_PER_YEAR
    if horizon > difference.size:
        raise ConstructionTournamentError(
            f"a {years}-year horizon needs {horizon} months; the sample holds {difference.size}"
        )
    starts = rng.integers(0, difference.size, size=(draws, horizon))
    restart = rng.random((draws, horizon)) < 1.0 / block_months
    restart[:, 0] = True
    positions = np.broadcast_to(np.arange(horizon), (draws, horizon))
    last = np.maximum.accumulate(np.where(restart, positions, -1), axis=1)
    block_start = np.take_along_axis(starts, last, axis=1)
    index = (block_start + (positions - last)) % difference.size
    paths = difference[index].mean(axis=1) * MONTHS_PER_YEAR * 100.0
    losing = paths[paths < 0.0]
    probability = float(losing.size) / float(draws)
    magnitude = float(np.median(losing)) if losing.size else 0.0
    return probability, magnitude


# --------------------------------------------------------------------------- #
# Arm outcomes and the falsifier
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True)
class ArmOutcome:
    """Everything reported for one arm. Mutable while the run assembles it."""

    name: str
    role: str
    benchmark: str
    growth_pp_yr: float
    volatility_pct: float
    sharpe: float
    max_drawdown_pct: float
    time_under_water_months: int
    gross_notional: float
    weighted_fee_bp: float
    annual_turnover_pct: float
    n_funds: int
    months: int
    window: tuple[str, str]
    gap: GapStatistics | None = None
    adjusted_p: float | None = None
    status: str = "not-scored"
    clause: str = ""
    perturbation_range: tuple[float, float] | None = None
    max_regret_pp_yr: float | None = None
    p_underperform: Mapping[str, float] = field(default_factory=dict)
    shortfall_pp_yr: Mapping[str, float] = field(default_factory=dict)
    after_tax_gap_pp_yr: float | None = None
    after_tax_note: str = "not measured"
    break_even_trend_haircut_pp_yr: float | None = None
    break_even_value_haircut_pp_yr: float | None = None
    era_gaps: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    note: str = ""

    def to_json(self) -> dict[str, JsonValue]:
        gap = self.gap
        return {
            "arm": self.name,
            "role": self.role,
            "benchmark": self.benchmark,
            "status": self.status,
            "falsifier_clause": self.clause,
            "window": list(self.window),
            "months": self.months,
            "growth_pp_yr": round(self.growth_pp_yr, 4),
            "volatility_pct": round(self.volatility_pct, 4),
            "sharpe": round(self.sharpe, 4),
            "max_drawdown_pct": round(self.max_drawdown_pct, 3),
            "time_under_water_months": self.time_under_water_months,
            "gross_notional": round(self.gross_notional, 4),
            "weighted_fee_bp": round(self.weighted_fee_bp, 2),
            "annual_turnover_pct": round(self.annual_turnover_pct * 100.0, 3),
            "n_funds": self.n_funds,
            "growth_gap_pp_yr": None if gap is None else round(gap.gap_pp_yr, 4),
            "gap_interval_pp_yr": (
                None if gap is None else [round(gap.interval[0], 4), round(gap.interval[1], 4)]
            ),
            "mde_80pc_power_pp_yr": None if gap is None else round(gap.mde_pp_yr, 4),
            "mde_80pc_power_block_bootstrap_pp_yr": (
                None if gap is None else round(gap.mde_bootstrap_pp_yr, 4)
            ),
            "tracking_error_pct": None if gap is None else round(gap.tracking_error_pct, 4),
            "years_to_distinguish_at_80pc_power": (
                None if gap is None else round(gap.years_to_distinguish, 1)
            ),
            "p_value": None if gap is None else round(gap.p_value, 5),
            "benjamini_hochberg_adjusted_p": (
                None if self.adjusted_p is None else round(self.adjusted_p, 5)
            ),
            "perturbation_gap_range_pp_yr": (
                None
                if self.perturbation_range is None
                else [round(self.perturbation_range[0], 4), round(self.perturbation_range[1], 4)]
            ),
            "max_regret_pp_yr": (
                None if self.max_regret_pp_yr is None else round(self.max_regret_pp_yr, 4)
            ),
            "p_underperform": {k: round(v, 4) for k, v in self.p_underperform.items()},
            "median_shortfall_if_underperforming_pp_yr": {
                k: round(v, 4) for k, v in self.shortfall_pp_yr.items()
            },
            "after_tax_growth_gap_pp_yr": (
                None if self.after_tax_gap_pp_yr is None else round(self.after_tax_gap_pp_yr, 4)
            ),
            "after_tax_note": self.after_tax_note,
            "break_even_trend_haircut_pp_yr": self.break_even_trend_haircut_pp_yr,
            "break_even_value_haircut_pp_yr": self.break_even_value_haircut_pp_yr,
            "era_gaps_pp_yr": {
                era: {k: round(v, 4) for k, v in values.items()}
                for era, values in self.era_gaps.items()
            },
            "note": self.note,
        }


def _apply_falsifier(
    outcome: ArmOutcome,
    *,
    q: float,
    sharpe_of_levered_control: float | None,
) -> None:
    """Falsifier clauses (a) to (f) of the frozen specification, in order."""
    gap = outcome.gap
    if gap is None:
        outcome.status, outcome.clause = "not-scored", ""
        return
    if gap.gap_pp_yr <= 0.0:
        outcome.status, outcome.clause = "rejected", "(a) gap at or below zero"
        return
    if (
        sharpe_of_levered_control is not None
        and outcome.benchmark == "control_capweight"
        and outcome.gross_notional > 1.0
        and sharpe_of_levered_control >= outcome.sharpe
    ):
        outcome.status, outcome.clause = (
            "rejected",
            "(b) the leverage-matched control matches or beats this arm's Sharpe ratio, "
            "so the gain is leveraged beta",
        )
        return
    if abs(gap.gap_pp_yr) < gap.mde_pp_yr:
        outcome.status, outcome.clause = (
            "unresolved",
            f"(c) the gap {gap.gap_pp_yr:+.2f} pp/yr is inside this design's own "
            f"{gap.mde_pp_yr:.2f} pp/yr detection floor at 80% power",
        )
        return
    if outcome.adjusted_p is not None and outcome.adjusted_p > q:
        outcome.status, outcome.clause = (
            "unresolved",
            f"(d) Benjamini-Hochberg adjusted p = {outcome.adjusted_p:.3f} exceeds q = {q:.2f}",
        )
        return
    if outcome.perturbation_range is not None and outcome.perturbation_range[0] <= 0.0:
        outcome.status, outcome.clause = (
            "unresolved",
            f"(e) the gap changes sign on the mapping-perturbation grid, reaching "
            f"{outcome.perturbation_range[0]:+.2f} pp/yr",
        )
        return
    outcome.status, outcome.clause = "exploratory", "(f) survived every clause"


def _break_even(points: Sequence[tuple[float, float]]) -> float | None:
    """Linear interpolation to where a gap crosses zero, or ``None``."""
    for (x0, y0), (x1, y1) in itertools.pairwise(points):
        if y0 > 0.0 >= y1:
            if y0 == y1:  # pragma: no cover - defensive
                return x0
            return x0 + (x1 - x0) * y0 / (y0 - y1)
    return None


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def _all_tickers(contestants: Mapping[str, Contestant]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for contestant in contestants.values():
        for ticker in contestant.tickers:
            seen.setdefault(ticker, None)
    return tuple(seen)


def _path_for(
    contestant: Contestant,
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    *,
    excess_all: FloatArray,
    ticker_index: Mapping[str, int],
    shift: MappingShift,
    minimum_months: int,
    reapply_every: int,
) -> tuple[PortfolioPath, int, tuple[float, ...]]:
    """Simulate one contestant, returning its path and its first scored month."""
    costs = shift.applied_to(costs)
    columns = np.asarray([ticker_index[t] for t in contestant.tickers], dtype=np.intp)
    excess = excess_all[:, columns]
    if not contestant.is_estimated:
        targets = np.asarray(contestant.weights, dtype=np.float64)
        return (
            _simulate(
                panel,
                mappings,
                costs,
                tickers=contestant.tickers,
                excess=excess,
                targets=targets,
                first_month=0,
                rebalance_every=MONTHS_PER_YEAR,
            ),
            0,
            (),
        )

    if contestant.method == "equal_risk_contribution_engines":
        engine_names = tuple(contestant.engines)
        engine_columns = []
        for engine in engine_names:
            members = contestant.engines[engine]
            block = np.zeros(panel.months, dtype=np.float64)
            for ticker, share in members.items():
                block = block + share * excess_all[:, ticker_index[ticker]]
            engine_columns.append(block)
        engine_excess = np.column_stack(engine_columns)
        engine_targets, first, intensities = walk_forward_weights(
            engine_excess,
            method=contestant.method,
            minimum_months=minimum_months,
            reapply_every=reapply_every,
        )
        targets = np.zeros((panel.months, len(contestant.tickers)), dtype=np.float64)
        for e, engine in enumerate(engine_names):
            for ticker, share in contestant.engines[engine].items():
                position = contestant.tickers.index(ticker)
                targets[:, position] += engine_targets[:, e] * share
        if contestant.gross_notional_cap is not None:
            rows = targets.sum(axis=1)
            scale = np.divide(
                contestant.gross_notional_cap, rows, out=np.zeros_like(rows), where=rows > 0
            )
            targets = targets * scale[:, None]
        return (
            _simulate(
                panel,
                mappings,
                costs,
                tickers=contestant.tickers,
                excess=excess,
                targets=targets,
                first_month=first,
                rebalance_every=reapply_every,
            ),
            first,
            intensities,
        )

    targets, first, intensities = walk_forward_weights(
        excess,
        method=contestant.method,
        minimum_months=minimum_months,
        reapply_every=reapply_every,
    )
    return (
        _simulate(
            panel,
            mappings,
            costs,
            tickers=contestant.tickers,
            excess=excess,
            targets=targets,
            first_month=first,
            rebalance_every=reapply_every,
        ),
        first,
        intensities,
    )


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Run the tournament and apply the frozen falsifier arm by arm."""
    parameters = _mapping(specification.parameters, where="parameters")
    panel = load_basis_panel(specification)
    mappings = _build_mappings(specification)
    costs = _cost_settings(specification)
    contestants = _read_contestants(specification)
    tickers = _all_tickers(contestants)
    ticker_index = {ticker: i for i, ticker in enumerate(tickers)}

    estimation = _mapping(
        _at(parameters, "weighting_method_estimation", where="parameters"), where="estimation"
    )
    minimum_months = int(_number(estimation, "minimum_estimation_months", where="estimation"))
    reapply_every = int(_number(estimation, "reapply_every_months", where="estimation"))
    block_months = _number(parameters, "bootstrap_block_months", where="parameters")
    q_value = _number(
        _mapping(_at(parameters, "multiple_testing_family", where="parameters"), where="family"),
        "q",
        where="multiple_testing_family",
    )
    horizons = [
        int(years)
        for years in _numbers(
            _at(parameters, "underperformance_horizons_years", where="parameters"),
            where="underperformance_horizons_years",
        )
    ]

    central = MappingShift()
    excess_all = fund_excess_matrix(panel, mappings, costs, tickers=tickers, shift=central)

    paths: dict[str, PortfolioPath] = {}
    first_months: dict[str, int] = {}
    shrinkage: dict[str, tuple[float, ...]] = {}
    for name, contestant in contestants.items():
        path, first, intensities = _path_for(
            contestant,
            panel,
            mappings,
            costs,
            excess_all=excess_all,
            ticker_index=ticker_index,
            shift=central,
            minimum_months=minimum_months,
            reapply_every=reapply_every,
        )
        paths[name] = path
        first_months[name] = first
        if intensities:
            shrinkage[name] = intensities

    rng = context.rng
    indices_full = stationary_bootstrap_indices(
        panel.months, block_months, specification.inference.resamples, rng
    )
    walk_start = max(first_months.values())
    indices_walk = stationary_bootstrap_indices(
        panel.months - walk_start, block_months, specification.inference.resamples, rng
    )

    outcomes: dict[str, ArmOutcome] = {}
    for name, contestant in contestants.items():
        path = paths[name]
        first = first_months[name]
        equity = np.cumprod(1.0 + path.total)
        drawdown = drawdown_summary(equity)
        excess_std = float(np.std(path.excess, ddof=1))
        outcomes[name] = ArmOutcome(
            name=name,
            role=contestant.role,
            benchmark=contestant.benchmark,
            growth_pp_yr=annualised_log_growth(path.total),
            volatility_pct=float(np.std(path.total, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
            sharpe=(
                float(np.mean(path.excess)) / excess_std * math.sqrt(MONTHS_PER_YEAR)
                if excess_std > 0
                else 0.0
            ),
            max_drawdown_pct=drawdown.max_drawdown * 100.0,
            time_under_water_months=drawdown.max_time_under_water,
            gross_notional=path.gross_notional,
            weighted_fee_bp=path.weighted_fee_bp,
            annual_turnover_pct=path.annual_turnover,
            n_funds=path.n_funds,
            months=path.total.size,
            window=(panel.periods[first], panel.periods[-1]),
            note=contestant.note,
        )

    levered_sharpe = outcomes["control_capweight_levered"].sharpe

    def scored_slice(name: str, benchmark: str) -> tuple[FloatArray, FloatArray, NDArray[np.intp]]:
        """Align an arm and its benchmark on the arm's own scored window."""
        first = first_months[name]
        arm = paths[name].total
        bench = paths[benchmark].total[first - first_months[benchmark] :]
        if arm.size != bench.size:  # pragma: no cover - defensive
            raise ConstructionTournamentError(f"{name} and {benchmark} disagree on length")
        return arm, bench, (indices_full if first == 0 else indices_walk)

    families: dict[str, list[str]] = {}
    for name, contestant in contestants.items():
        if not contestant.benchmark:
            continue
        arm, bench, indices = scored_slice(name, contestant.benchmark)
        stats = gap_statistics(
            arm, bench, indices=indices, confidence=specification.inference.confidence_level
        )
        outcomes[name].gap = stats
        key = f"{contestant.benchmark}|{'walk' if first_months[name] else 'full'}"
        families.setdefault(key, []).append(name)

    for members in families.values():
        scored_gaps = [outcomes[name].gap for name in members]
        p_values = [gap.p_value for gap in scored_gaps if gap is not None]
        adjusted = benjamini_hochberg(p_values, alpha=q_value)
        for name, value in zip(members, adjusted.adjusted_p_values, strict=True):
            outcomes[name].adjusted_p = float(value)

    # Perturbation grid: 27 points, every arm re-simulated at each.
    perturbation = _mapping(
        _at(parameters, "mapping_perturbation", where="parameters"), where="perturbation"
    )
    grid_gaps: dict[str, list[float]] = {name: [] for name in contestants}
    grid_growth: list[GridPoint] = []
    for loading_delta in _numbers(
        _at(perturbation, "factor_loading_delta", where="perturbation"), where="loading"
    ):
        for trend_multiplier in _numbers(
            _at(perturbation, "trend_beta_multiplier", where="perturbation"), where="trend"
        ):
            for vxus_share in _numbers(
                _at(perturbation, "vxus_developed_share", where="perturbation"), where="vxus"
            ):
                shift = MappingShift(
                    loading_delta=loading_delta,
                    trend_multiplier=trend_multiplier,
                    vxus_developed_share=vxus_share,
                )
                point = _growth_at(
                    shift,
                    panel=panel,
                    mappings=mappings,
                    costs=costs,
                    contestants=contestants,
                    tickers=tickers,
                    ticker_index=ticker_index,
                    minimum_months=minimum_months,
                    reapply_every=reapply_every,
                    walk_start=walk_start,
                )
                grid_growth.append(point)
                for name, contestant in contestants.items():
                    if contestant.benchmark:
                        grid_gaps[name].append(point.gap(name, contestant.benchmark))

    for name, contestant in contestants.items():
        if not contestant.benchmark:
            continue
        values = grid_gaps[name]
        outcomes[name].perturbation_range = (min(values), max(values))
        # Regret is taken on the walk-forward window, the only one every arm
        # shares, so that an estimated arm and a constant-weight one are compared
        # over the same months rather than over the months each happens to own.
        outcomes[name].max_regret_pp_yr = max(
            point.best_common - point.common[name] for point in grid_growth
        )

    for name, contestant in contestants.items():
        _apply_falsifier(
            outcomes[name],
            q=q_value,
            sharpe_of_levered_control=levered_sharpe if contestant.benchmark else None,
        )

    # Horizon risk, per the charter's common core.
    for name, contestant in contestants.items():
        if not contestant.benchmark:
            continue
        arm, bench, _ = scored_slice(name, contestant.benchmark)
        probabilities: dict[str, float] = {}
        shortfalls: dict[str, float] = {}
        for years in horizons:
            if years * MONTHS_PER_YEAR > arm.size:
                continue
            probability, magnitude = underperformance(
                arm, bench, years=years, rng=rng, block_months=block_months, draws=10_000
            )
            probabilities[f"{years}y"] = probability
            shortfalls[f"{years}y"] = magnitude
        outcomes[name].p_underperform = probabilities
        outcomes[name].shortfall_pp_yr = shortfalls

    # After tax, only where a fund publishes a drag.
    for name, contestant in contestants.items():
        outcome = outcomes[name]
        if outcome.gap is None:
            continue
        drag = 0.0
        measured = False
        for ticker, weight in zip(contestant.tickers, contestant.weights, strict=True):
            incremental = mappings[ticker].incremental_tax_drag_bp
            if incremental is not None:
                drag += weight * incremental / 100.0
                measured = True
        if measured:
            outcome.after_tax_gap_pp_yr = outcome.gap.gap_pp_yr - drag
            outcome.after_tax_note = (
                f"incremental distribution tax drag {drag:.4f} pp/yr, from the only "
                "fund-published after-tax table in this tournament"
            )

    # Haircut sweeps.
    haircuts = _mapping(_at(parameters, "haircut_sweep", where="parameters"), where="haircut")
    trend_grid = _numbers(
        _at(haircuts, "trend_arithmetic_mean_percent_per_year", where="haircut"), where="trend"
    )
    value_grid = _numbers(
        _at(haircuts, "value_premium_percent_per_year", where="haircut"), where="value"
    )
    trend_curves: dict[str, list[tuple[float, float]]] = {name: [] for name in contestants}
    for haircut in trend_grid:
        point = _growth_at(
            MappingShift(trend_haircut_pp_yr=haircut),
            panel=panel,
            mappings=mappings,
            costs=costs,
            contestants=contestants,
            tickers=tickers,
            ticker_index=ticker_index,
            minimum_months=minimum_months,
            reapply_every=reapply_every,
            walk_start=walk_start,
        )
        for name, contestant in contestants.items():
            if contestant.benchmark:
                trend_curves[name].append((haircut, point.gap(name, contestant.benchmark)))
    value_curves: dict[str, list[tuple[float, float]]] = {name: [] for name in contestants}
    for haircut in value_grid:
        point = _growth_at(
            MappingShift(value_haircut_pp_yr=haircut),
            panel=panel,
            mappings=mappings,
            costs=costs,
            contestants=contestants,
            tickers=tickers,
            ticker_index=ticker_index,
            minimum_months=minimum_months,
            reapply_every=reapply_every,
            walk_start=walk_start,
        )
        for name, contestant in contestants.items():
            if contestant.benchmark:
                value_curves[name].append((haircut, point.gap(name, contestant.benchmark)))
    for name in contestants:
        outcomes[name].break_even_trend_haircut_pp_yr = _break_even(trend_curves[name])
        outcomes[name].break_even_value_haircut_pp_yr = _break_even(value_curves[name])

    # Eras.
    for era in specification.sample_policy.eras:
        sliced = panel.window(start=era.start, end=era.end)
        era_excess = fund_excess_matrix(
            sliced, mappings, costs, tickers=tickers, shift=central
        )
        era_growth: dict[str, float] = {}
        for name, contestant in contestants.items():
            if contestant.is_estimated:
                continue
            columns = np.asarray([ticker_index[t] for t in contestant.tickers], dtype=np.intp)
            path = _simulate(
                sliced,
                mappings,
                costs,
                tickers=contestant.tickers,
                excess=era_excess[:, columns],
                targets=np.asarray(contestant.weights, dtype=np.float64),
                first_month=0,
                rebalance_every=MONTHS_PER_YEAR,
            )
            era_growth[name] = annualised_log_growth(path.total)
        for name, contestant in contestants.items():
            if name not in era_growth or not contestant.benchmark:
                continue
            if contestant.benchmark not in era_growth:
                continue
            existing = dict(outcomes[name].era_gaps)
            existing[era.name] = {
                "growth_pp_yr": era_growth[name],
                "gap_pp_yr": era_growth[name] - era_growth[contestant.benchmark],
                "months": sliced.months,
            }
            outcomes[name].era_gaps = existing

    premium_surface = _premium_surface(
        parameters=parameters,
        panel=panel,
        mappings=mappings,
        costs=costs,
        contestants=contestants,
        tickers=tickers,
        ticker_index=ticker_index,
        minimum_months=minimum_months,
        reapply_every=reapply_every,
        walk_start=walk_start,
    )

    financing_band = _financing_band(
        parameters=parameters,
        panel=panel,
        mappings=mappings,
        costs=costs,
        contestants=contestants,
        tickers=tickers,
        ticker_index=ticker_index,
        minimum_months=minimum_months,
        reapply_every=reapply_every,
        walk_start=walk_start,
    )

    # One window every arm can be read on. The walk-forward arms cannot be scored
    # before 2000-11, and a weighting-method gap measured on 307 months must not
    # be put in the same column as a constant-weight gap measured on 427.
    common_window: dict[str, JsonValue] = {}
    for name, contestant in contestants.items():
        total = paths[name].total[walk_start - first_months[name] :]
        growth = annualised_log_growth(total)
        entry: dict[str, JsonValue] = {"growth_pp_yr": round(growth, 4)}
        if contestant.benchmark:
            bench = paths[contestant.benchmark].total[
                walk_start - first_months[contestant.benchmark] :
            ]
            stats = gap_statistics(
                total,
                bench,
                indices=indices_walk,
                confidence=specification.inference.confidence_level,
            )
            entry["gap_pp_yr"] = round(stats.gap_pp_yr, 4)
            entry["mde_80pc_power_pp_yr"] = round(stats.mde_pp_yr, 4)
            entry["interval_pp_yr"] = [
                round(stats.interval[0], 4),
                round(stats.interval[1], 4),
            ]
        common_window[name] = entry

    # Hostile arms and diagnostics.
    hostile = _hostile_arms(
        panel=panel,
        mappings=mappings,
        costs=costs,
        contestants=contestants,
        tickers=tickers,
        ticker_index=ticker_index,
        minimum_months=minimum_months,
        reapply_every=reapply_every,
        walk_start=walk_start,
        parameters=parameters,
    )
    block_robustness = _block_robustness(
        specification=specification,
        contestants=contestants,
        paths=paths,
        first_months=first_months,
        rng=rng,
        panel_months=panel.months,
        walk_start=walk_start,
        parameters=parameters,
    )
    lookahead = _lookahead_ceiling(
        panel=panel,
        mappings=mappings,
        costs=costs,
        contestants=contestants,
        ticker_index=ticker_index,
        excess_all=excess_all,
    )

    ranked = sorted(
        (o for o in outcomes.values() if o.gap is not None),
        key=lambda o: o.gap.gap_pp_yr if o.gap else 0.0,
        reverse=True,
    )
    resolved = [o for o in ranked if o.status == "exploratory"]
    status = ResultStatus.EXPLORATORY if resolved else ResultStatus.UNRESOLVED

    if not ranked:  # pragma: no cover - defensive
        raise ConstructionTournamentError("no arm carried a benchmark; nothing was scored")
    leader = ranked[0]
    leader_gap = leader.gap
    assert leader_gap is not None
    summary = (
        f"{len(ranked)} constructions scored on {panel.months} months "
        f"({panel.periods[0]}..{panel.periods[-1]}), on BASIS-MAPPED funds rather than "
        f"fund returns. The largest after-cost growth gap is {leader.name} at "
        f"{leader_gap.gap_pp_yr:+.2f} pp/yr against {leader.benchmark}, against its own "
        f"{leader_gap.mde_pp_yr:.2f} pp/yr detection floor at 80% power. "
        f"{len(resolved)} of {len(ranked)} arms separate from their benchmark by more "
        "than this design can resolve. Every other arm is `unresolved`, which is a "
        "statement about a 427-month joint sample and not about the constructions."
    )

    estimates = _build_estimates(outcomes)
    diagnostics: dict[str, JsonValue] = {
        "freeze_note": (
            "FUNDS ARE BASIS-MAPPED, NOT SIMULATED FROM FUND RETURNS. Every ticker is a "
            "linear combination of Ken French factor series and AQR's TSMOM, less a fee. "
            "The mapping is an assumption; see parameters.fund_mapping in the "
            "specification and the perturbation range beside every gap. AQR's TSMOM is a "
            "vendor series, gross of the vendor's own trading costs by omission. JPFP has "
            "filed no holdings report; its structure here is RSST's, copied."
        ),
        "window": f"{panel.periods[0]}..{panel.periods[-1]}",
        "months": panel.months,
        "walk_forward_window": (
            f"{panel.periods[walk_start]}..{panel.periods[-1]} "
            f"({panel.months - walk_start} months)"
        ),
        "panel_findings": list(panel.findings),
        "provenance": [dict(record) for record in panel.provenance],
        "mapping_table": _mapping_table(mappings),
        "arms": [outcomes[name].to_json() for name in contestants],
        "ranking_by_gap": [o.name for o in ranked],
        "funding_wedge": _funding_wedge(outcomes, contestants),
        "financing_basis_band": financing_band,
        "premium_surface": premium_surface,
        "panel_moments": _panel_moments(panel),
        "regret_basis": (
            "max_regret_pp_yr is `best arm's growth - this arm's growth`, maximised over "
            "the 27-point mapping-perturbation grid and measured on the walk-forward "
            "window, the only window every arm shares."
        ),
        "resolvable_arms": [o.name for o in resolved],
        "hostile_arms": hostile,
        "block_length_robustness": block_robustness,
        "lookahead_ceiling": lookahead,
        "common_walk_forward_window": {
            "what_this_is": (
                "Every arm re-read on the 307 months from 2000-11, the only window on "
                "which a walk-forward weighting method and a constant-weight portfolio "
                "can be compared. The full-window column above is the right one for the "
                "constant-weight arms and the wrong one for the estimated arms."
            ),
            "arms": common_window,
        },
        "shrinkage_intensities": {
            name: [round(value, 4) for value in values] for name, values in shrinkage.items()
        },
        "multiple_testing_families": {key: sorted(members) for key, members in families.items()},
        "what_this_cannot_resolve": (
            "An arm's detection floor scales with its tracking error. Over 427 months a "
            "gap below 0.47 pp/yr is invisible at 1% tracking error and a gap below "
            "4.70 pp/yr is invisible at 10%. The stacked arms track their benchmarks at "
            "several percentage points, so nothing this experiment reports about them is "
            "resolvable; the weighting-method arms track at one to three points and are."
        ),
    }
    caveats = (
        "Funds are basis-mapped. This experiment ranks CONSTRUCTIONS and cannot rank funds.",
        "AQR's TSMOM is a vendor series and is gross of its own trading costs by omission.",
        "JPFP has filed no N-PORT; its structure is RSST's, copied, and is an assumption.",
        "AVES's fee appears nowhere in this repository and is a declared assumption.",
        "Fund alphas are not charged in the headline arms; the hostile arm charges them.",
        "Only RSST publishes a distribution tax drag. Every other after-tax cell is not measured.",
        "The 427-month joint sample is the binding constraint on every conclusion here.",
        "No sleeve, fund or portfolio is promoted. Decision 0004's non-promotion stands.",
    )
    return ExperimentResult(
        status=status,
        summary=summary,
        estimates=estimates,
        diagnostics=diagnostics,
        caveats=caveats,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class GridPoint:
    """Every arm's growth at one point of a sensitivity grid, on two windows.

    ``scored`` is each arm's growth over its OWN window, which is the full panel
    for a constant-weight arm and the walk-forward window for an estimated one.
    ``common`` is every arm's growth over the walk-forward window, the only one
    they share. A gap between two arms must be taken from one of these and never
    across both; ``gaps`` and ``best`` enforce that.
    """

    scored: Mapping[str, float]
    common: Mapping[str, float]
    estimated: frozenset[str]

    def gap(self, arm: str, benchmark: str) -> float:
        table = self.common if arm in self.estimated else self.scored
        return table[arm] - table[benchmark]

    def gaps(self, contestants: Mapping[str, Contestant]) -> dict[str, float]:
        return {
            name: round(self.gap(name, contestant.benchmark), 4)
            for name, contestant in contestants.items()
            if contestant.benchmark
        }

    @property
    def best_common(self) -> float:
        """The best growth any arm achieved, on the one window all of them share."""
        return max(self.common.values())


def _growth_at(
    shift: MappingShift,
    *,
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    contestants: Mapping[str, Contestant],
    tickers: Sequence[str],
    ticker_index: Mapping[str, int],
    minimum_months: int,
    reapply_every: int,
    walk_start: int,
) -> GridPoint:
    """Every arm's growth at one point of a sensitivity grid."""
    excess_all = fund_excess_matrix(panel, mappings, costs, tickers=tickers, shift=shift)
    scored: dict[str, float] = {}
    common: dict[str, float] = {}
    estimated: set[str] = set()
    for name, contestant in contestants.items():
        path, first, _ = _path_for(
            contestant,
            panel,
            mappings,
            costs,
            excess_all=excess_all,
            ticker_index=ticker_index,
            shift=shift,
            minimum_months=minimum_months,
            reapply_every=reapply_every,
        )
        scored[name] = annualised_log_growth(path.total)
        common[name] = annualised_log_growth(path.total[walk_start - first :])
        if contestant.is_estimated:
            estimated.add(name)
    return GridPoint(scored=scored, common=common, estimated=frozenset(estimated))


def _panel_moments(panel: BasisPanel) -> dict[str, JsonValue]:
    """Annualised arithmetic mean and volatility of every basis series.

    Reported so that a haircut quoted as a fraction of a series' own mean can be
    checked against the artifact instead of against a reader's memory. These are
    REALISED moments of one window, not forecasts of anything.
    """
    rows: dict[str, JsonValue] = {}
    for name in sorted(panel.series):
        column = panel.column(name)
        rows[name] = {
            "arithmetic_mean_pp_yr": round(float(np.mean(column)) * MONTHS_PER_YEAR * 100.0, 4),
            "volatility_pct": round(
                float(np.std(column, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0, 4
            ),
        }
    rows["cash"] = {
        "arithmetic_mean_pp_yr": round(float(np.mean(panel.cash)) * MONTHS_PER_YEAR * 100.0, 4),
        "volatility_pct": round(
            float(np.std(panel.cash, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0, 4
        ),
    }
    return rows


def _premium_surface(
    *,
    parameters: Mapping[str, JsonValue],
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    contestants: Mapping[str, Contestant],
    tickers: Sequence[str],
    ticker_index: Mapping[str, int],
    minimum_months: int,
    reapply_every: int,
    walk_start: int,
) -> dict[str, JsonValue]:
    """The break-even trend premium as a function of the assumed equity premium.

    Haircutting one premium towards a forward estimate while holding another at
    its realised value lets the untouched input decide the verdict. This sweeps
    both together: at each assumed equity premium it finds the trend haircut at
    which each arm's gap crosses zero, and converts that haircut into the GROSS
    TREND PREMIUM the arm requires. The realised trend mean it is subtracted from
    is reported in ``panel_moments`` so the conversion can be checked.
    """
    block = parameters.get("premium_surface")
    if not isinstance(block, Mapping):
        return {"declared": False}
    equity_cuts = _numbers(
        _at(block, "equity_haircut_pp_yr", where="premium_surface"), where="equity"
    )
    trend_cuts = _numbers(
        _at(block, "trend_haircut_pp_yr", where="premium_surface"), where="trend"
    )
    watch = tuple(
        str(name)
        for name in _sequence(_at(block, "watch_arms", where="premium_surface"), where="watch")
    )
    missing = [name for name in watch if name not in contestants]
    if missing:
        raise ConstructionTournamentError(f"premium_surface watches unknown arms {missing}")

    realised_trend = float(np.mean(panel.column("trend"))) * MONTHS_PER_YEAR * 100.0
    realised_equity = float(np.mean(panel.column("us_mkt"))) * MONTHS_PER_YEAR * 100.0

    curves: dict[str, dict[str, list[tuple[float, float]]]] = {
        name: {} for name in watch
    }
    grid: dict[str, JsonValue] = {}
    for equity_cut in equity_cuts:
        label = f"equity_{realised_equity - equity_cut:.2f}pp"
        for trend_cut in trend_cuts:
            point = _growth_at(
                MappingShift(
                    equity_haircut_pp_yr=equity_cut, trend_haircut_pp_yr=trend_cut
                ),
                panel=panel,
                mappings=mappings,
                costs=costs,
                contestants=contestants,
                tickers=tickers,
                ticker_index=ticker_index,
                minimum_months=minimum_months,
                reapply_every=reapply_every,
                walk_start=walk_start,
            )
            for name in watch:
                curves[name].setdefault(label, []).append(
                    (trend_cut, point.gap(name, contestants[name].benchmark))
                )
        grid[label] = {
            "assumed_equity_premium_pp_yr": round(realised_equity - equity_cut, 4),
            "equity_haircut_pp_yr": round(equity_cut, 4),
        }

    required: dict[str, JsonValue] = {}
    for name in watch:
        rows: dict[str, JsonValue] = {}
        for label, points in curves[name].items():
            break_even = _break_even(points)
            rows[label] = {
                "break_even_trend_haircut_pp_yr": (
                    "beyond the swept grid" if break_even is None else round(break_even, 4)
                ),
                "required_gross_trend_premium_pp_yr": (
                    "beyond the swept grid"
                    if break_even is None
                    else round(realised_trend - break_even, 4)
                ),
                "gap_at_zero_trend_haircut_pp_yr": round(points[0][1], 4),
            }
        required[name] = rows

    return {
        "declared": True,
        "what_this_is": (
            "The break-even GROSS trend premium each arm needs, as a function of the "
            "equity premium assumed. Both premia are haircut in the same sweep, because "
            "substituting a forward estimate for one while holding the other at its "
            "realised value lets the untouched input decide the verdict."
        ),
        "realised_trend_arithmetic_mean_pp_yr": round(realised_trend, 4),
        "realised_us_equity_arithmetic_mean_pp_yr": round(realised_equity, 4),
        "conversion": (
            "required gross trend premium = realised trend mean - break-even haircut. "
            "The trend series is AQR's TSMOM: a vendor series, gross of its own trading "
            "costs by omission and internally volatility-scaled. A premium quoted for a "
            "retail managed-futures PRODUCT is a different object at a different risk "
            "level, and the two may not be compared without a stated scaling."
        ),
        "equity_grid": grid,
        "required_gross_trend_premium": required,
    }


def _financing_band(
    *,
    parameters: Mapping[str, JsonValue],
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    contestants: Mapping[str, Contestant],
    tickers: Sequence[str],
    ticker_index: Mapping[str, int],
    minimum_months: int,
    reapply_every: int,
    walk_start: int,
) -> dict[str, JsonValue]:
    """Re-rank every arm across a band of the unobservable financing cost.

    A cleared-futures wrapper's financing lives in the contract's basis rather
    than in its income statement, so no filing discloses it and no filing can.
    It is the one load-bearing cost here that is unobservable rather than merely
    unmeasured, which means an ordering quoted at a point estimate of it is not
    an ordering. This reports whether the ordering survives the band.
    """
    block = parameters.get("financing_basis_band")
    if not isinstance(block, Mapping):
        return {"declared": False}
    grid = _numbers(_at(block, "annual_percent", where="financing_basis_band"), where="grid")
    watch = tuple(
        str(name)
        for name in _sequence(_at(block, "watch_arms", where="financing_basis_band"), where="watch")
    )
    missing = [name for name in watch if name not in contestants]
    if missing:
        raise ConstructionTournamentError(f"financing_basis_band watches unknown arms {missing}")

    gaps: dict[str, JsonValue] = {}
    orderings: list[tuple[str, ...]] = []
    watched_orderings: list[tuple[str, ...]] = []
    for basis in grid:
        point = _growth_at(
            MappingShift(financing_basis_annual_percent=basis),
            panel=panel,
            mappings=mappings,
            costs=costs,
            contestants=contestants,
            tickers=tickers,
            ticker_index=ticker_index,
            minimum_months=minimum_months,
            reapply_every=reapply_every,
            walk_start=walk_start,
        )
        table = point.gaps(contestants)
        gaps[f"{basis:.2f}%"] = dict(table)
        orderings.append(tuple(sorted(table, key=lambda name: -table[name])))
        watched = {name: table[name] for name in watch}
        watched_orderings.append(tuple(sorted(watched, key=lambda name: -watched[name])))

    return {
        "declared": True,
        "what_this_is": (
            "The equity-index-futures basis swept across a band, with every arm re-scored "
            "at each point. Financing is charged to the leverage-matched control on the "
            "same terms as to every wrapper, so a rise in the basis does not move all arms "
            "in the same direction: it moves each one in proportion to its own futures "
            "notional, and the levered control carries more of that than any wrapper does."
        ),
        "grid_annual_percent": list(grid),
        "gaps_pp_yr": gaps,
        "ordering_over_all_arms_is_stable": len(set(orderings)) == 1,
        "watched_arms": list(watch),
        "watched_ordering_is_stable": len(set(watched_orderings)) == 1,
        "watched_orderings": [list(order) for order in watched_orderings],
    }


def _funding_wedge(
    outcomes: Mapping[str, ArmOutcome], contestants: Mapping[str, Contestant]
) -> dict[str, JsonValue]:
    """What the funding rule alone is worth, with the portfolio held fixed.

    ``fund_overlay_30`` and ``fund_prorata_30`` carry the SAME 30% of trend
    notional. The overlay keeps the whole base and finances the sleeve; the
    pro-rata arm sells 30% of the base to pay for it. The difference in growth is
    therefore the funding rule and nothing else, and it is the average-versus-sum
    distinction realised on a wealth path rather than asserted: under
    substitution the base's contribution is scaled by 0.70 and under the overlay
    it is not.
    """
    overlay = outcomes["fund_overlay_30"].growth_pp_yr
    pro_rata = outcomes["fund_prorata_30"].growth_pp_yr
    cash_arm = outcomes["fund_cash_30"]
    return {
        "what_this_is": (
            "The same trend notional, funded three ways. Two of the three arms hold "
            "the IDENTICAL portfolio and differ only in the benchmark they are scored "
            "against, which is the cleanest demonstration in this experiment that a "
            "funding rule is a statement about a counterfactual."
        ),
        "overlay_growth_pp_yr": round(overlay, 4),
        "pro_rata_growth_pp_yr": round(pro_rata, 4),
        "wedge_pp_yr": round(overlay - pro_rata, 4),
        "wedge_per_unit_of_base_sold_pp_yr": round((overlay - pro_rata) / 0.30, 4),
        "identical_portfolio_pair": {
            "arms": ["fund_prorata_30", "fund_cash_30"],
            "growth_pp_yr": round(cash_arm.growth_pp_yr, 4),
            "gap_against_hundred_percent_equity_pp_yr": round(
                outcomes["fund_prorata_30"].gap.gap_pp_yr, 4
            )
            if outcomes["fund_prorata_30"].gap
            else None,
            "gap_against_the_cash_holder_pp_yr": round(cash_arm.gap.gap_pp_yr, 4)
            if cash_arm.gap
            else None,
            "reading": (
                "One portfolio, two benchmarks, two different answers. Charter, "
                "'benchmarks and funding': the funding rule is part of the hypothesis "
                "and neither of these is the universally correct frame."
            ),
        },
        "trend_weight_span": {
            name: round(outcomes[name].growth_pp_yr, 4)
            for name in ("fund_overlay_216", "fund_overlay_30")
            if name in outcomes and contestants[name].benchmark
        },
    }


def _hostile_arms(
    *,
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    contestants: Mapping[str, Contestant],
    tickers: Sequence[str],
    ticker_index: Mapping[str, int],
    minimum_months: int,
    reapply_every: int,
    walk_start: int,
    parameters: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """The three hostile arms the specification names, as gap tables."""
    central = _growth_at(
        MappingShift(),
        panel=panel,
        mappings=mappings,
        costs=costs,
        contestants=contestants,
        tickers=tickers,
        ticker_index=ticker_index,
        minimum_months=minimum_months,
        reapply_every=reapply_every,
        walk_start=walk_start,
    )

    alpha_point = _growth_at(
        MappingShift(charge_measured_alpha=True),
        panel=panel,
        mappings=mappings,
        costs=costs,
        contestants=contestants,
        tickers=tickers,
        ticker_index=ticker_index,
        minimum_months=minimum_months,
        reapply_every=reapply_every,
        walk_start=walk_start,
    )

    fee_grid = _mapping(_at(parameters, "assumed_fee_grid", where="parameters"), where="fees")
    fee_arms: dict[str, JsonValue] = {}
    for ticker in fee_grid:
        entry = fee_grid[ticker]
        if isinstance(entry, str) or not isinstance(entry, Sequence):
            continue  # the block's prose rationale, not a fee grid
        for fee in _numbers(entry, where=f"assumed_fee_grid.{ticker}"):
            point = _growth_at(
                MappingShift(fee_override_bp={ticker: fee * 100.0}),
                panel=panel,
                mappings=mappings,
                costs=costs,
                contestants=contestants,
                tickers=tickers,
                ticker_index=ticker_index,
                minimum_months=minimum_months,
                reapply_every=reapply_every,
                walk_start=walk_start,
            )
            fee_arms[f"{ticker}@{fee:.2f}%"] = point.gaps(contestants)

    return {
        "central_gaps_pp_yr": central.gaps(contestants),
        "charge_measured_alpha_gaps_pp_yr": alpha_point.gaps(contestants),
        "charge_measured_alpha_note": (
            "Every tilt fund charged `alpha - pedestal` from src/content/shelf.ts. Each "
            "figure sits inside its own detection floor, so this arm charges noise on "
            "purpose to show what the ranking would look like if the noise were real. "
            "DFIV's -3.80 pp/yr is the number most capable of reversing the proposal."
        ),
        "assumed_fee_gaps_pp_yr": fee_arms,
    }


def _block_robustness(
    *,
    specification: Specification,
    contestants: Mapping[str, Contestant],
    paths: Mapping[str, PortfolioPath],
    first_months: Mapping[str, int],
    rng: np.random.Generator,
    panel_months: int,
    walk_start: int,
    parameters: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """The primary gap's interval at the two predeclared neighbouring block lengths."""
    out: dict[str, JsonValue] = {}
    for block in _numbers(
        _at(parameters, "bootstrap_block_robustness_months", where="parameters"), where="blocks"
    ):
        full = stationary_bootstrap_indices(
            panel_months, block, specification.inference.resamples, rng
        )
        walk = stationary_bootstrap_indices(
            panel_months - walk_start, block, specification.inference.resamples, rng
        )
        table: dict[str, JsonValue] = {}
        for name, contestant in contestants.items():
            if not contestant.benchmark:
                continue
            first = first_months[name]
            arm = paths[name].total
            bench = paths[contestant.benchmark].total[first - first_months[contestant.benchmark] :]
            stats = gap_statistics(
                arm,
                bench,
                indices=full if first == 0 else walk,
                confidence=specification.inference.confidence_level,
            )
            table[name] = [round(stats.interval[0], 4), round(stats.interval[1], 4)]
        out[f"mean_block_{int(block)}m"] = table
    return out


def _lookahead_ceiling(
    *,
    panel: BasisPanel,
    mappings: Mapping[str, FundMapping],
    costs: CostSettings,
    contestants: Mapping[str, Contestant],
    ticker_index: Mapping[str, int],
    excess_all: FloatArray,
) -> dict[str, JsonValue]:
    """In-sample minimum variance, as a diagnostic that scores nothing."""
    contestant = contestants["wm_min_variance"]
    columns = np.asarray([ticker_index[t] for t in contestant.tickers], dtype=np.intp)
    excess = excess_all[:, columns]
    covariance = np.cov(excess, rowvar=False, ddof=1)
    weights = minimum_variance_weights(covariance, long_only=True)
    path = _simulate(
        panel,
        mappings,
        costs,
        tickers=contestant.tickers,
        excess=excess,
        targets=np.asarray(weights, dtype=np.float64),
        first_month=0,
        rebalance_every=MONTHS_PER_YEAR,
    )
    control = contestants["control_capweight"]
    control_path = _simulate(
        panel,
        mappings,
        costs,
        tickers=control.tickers,
        excess=excess_all[
            :, np.asarray([ticker_index[t] for t in control.tickers], dtype=np.intp)
        ],
        targets=np.asarray(control.weights, dtype=np.float64),
        first_month=0,
        rebalance_every=MONTHS_PER_YEAR,
    )
    return {
        "what_this_is": (
            "Minimum-variance weights fitted on the WHOLE window and then scored on it. "
            "It is a look-ahead and it scores nothing. It is reported so that the reader "
            "can see the size of the gap between an optimiser that knows the answer and "
            "the walk-forward arm that does not."
        ),
        "in_sample_weights": {
            ticker: round(float(weight), 4)
            for ticker, weight in zip(contestant.tickers, weights, strict=True)
        },
        "in_sample_growth_pp_yr": round(annualised_log_growth(path.total), 4),
        "in_sample_gap_vs_control_pp_yr": round(
            annualised_log_growth(path.total) - annualised_log_growth(control_path.total), 4
        ),
    }


def _mapping_table(mappings: Mapping[str, FundMapping]) -> list[JsonValue]:
    rows: list[JsonValue] = []
    for ticker in sorted(mappings):
        mapping = mappings[ticker]
        rows.append(
            {
                "ticker": ticker,
                "coefficients": {k: round(v, 4) for k, v in sorted(mapping.coefficients.items())},
                "gross_notional": round(mapping.gross_notional, 4),
                "expense_ratio_bp": mapping.expense_ratio_bp,
                "fee_is_assumed": mapping.fee_assumed,
                "structure_is_assumed": mapping.structure_assumed,
                "futures_notional_charged_financing": mapping.futures_notional,
                "alpha_less_pedestal_pp_yr": (
                    "not measured"
                    if mapping.alpha_less_pedestal_pp_yr is None
                    else mapping.alpha_less_pedestal_pp_yr
                ),
                "distribution_tax_drag_pp_yr": (
                    "not measured"
                    if mapping.distribution_tax_drag_pp_yr is None
                    else mapping.distribution_tax_drag_pp_yr
                ),
            }
        )
    return rows


def _gap_note(outcome: ArmOutcome, gap: GapStatistics) -> str:
    """The one line that must never appear without its detection floor."""
    parts = [
        f"status {outcome.status}",
        f"MDE80 {gap.mde_pp_yr:.2f} pp/yr",
        f"tracking error {gap.tracking_error_pct:.2f}%",
        f"{gap.years_to_distinguish:.0f} years to distinguish at 80% power",
    ]
    if outcome.perturbation_range is not None:
        low, high = outcome.perturbation_range
        parts.append(f"perturbation range [{low:+.2f}, {high:+.2f}] pp/yr")
    if outcome.clause:
        parts.append(outcome.clause)
    return "; ".join(parts)


def _build_estimates(outcomes: Mapping[str, ArmOutcome]) -> tuple[Estimate, ...]:
    estimates: list[Estimate] = []
    for name in sorted(outcomes):
        outcome = outcomes[name]
        gap = outcome.gap
        if gap is None:
            continue
        estimates.append(
            Estimate(
                name=f"growth_gap[{name} vs {outcome.benchmark}]",
                value=gap.gap_pp_yr,
                units="percentage points per year",
                interval=gap.interval,
                interval_method=(
                    "stationary block bootstrap on the joint panel, whole rows, mean "
                    "block 12 months, 10000 resamples, 95% percentile"
                ),
                cost_basis=CostBasis.NET_PESSIMISTIC,
                n_obs=gap.months,
                notes=_gap_note(outcome, gap),
            )
        )
        estimates.append(
            Estimate(
                name=f"minimum_detectable_effect[{name} vs {outcome.benchmark}]",
                value=gap.mde_pp_yr,
                units="percentage points per year",
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=gap.months,
                notes=(
                    "80% power, two-sided at 0.05, from this arm's own paired difference "
                    "series. Decision 0009 clause 1: a verdict may not be stronger than "
                    "the instrument that produced it."
                ),
                uncertainty_unavailable_reason=(
                    "a detection floor is a property of the design, not an estimate of a "
                    "quantity in the world, so it carries no interval"
                ),
            )
        )
    return tuple(estimates)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _render_console_report(outcome: RunOutcome) -> str:
    result = outcome.result
    if result is None:  # pragma: no cover - defensive
        return "no result"
    diagnostics = result.diagnostics
    lines: list[str] = [str(diagnostics["freeze_note"]), "", result.summary, ""]
    lines.append(
        f"Window {diagnostics['window']}  n={diagnostics['months']}   "
        f"walk-forward {diagnostics['walk_forward_window']}"
    )
    lines.append("")
    header = (
        f"{'arm':30s}{'from':>9s}{'growth':>8s}{'gap':>8s}{'MDE':>7s}{'lo':>8s}{'hi':>8s}"
        f"{'BHp':>7s}{'TE':>6s}{'yrs':>7s}{'MDD':>7s}{'gross':>7s}{'status':>12s}"
    )
    lines.append(header)
    arms = diagnostics["arms"]
    assert isinstance(arms, Sequence)
    rows = [row for row in arms if isinstance(row, Mapping)]
    rows.sort(key=lambda row: -(float(str(row["growth_pp_yr"]))))
    for row in rows:
        gap = row["growth_gap_pp_yr"]
        interval = row["gap_interval_pp_yr"]
        mde = row["mde_80pc_power_pp_yr"]
        adjusted = row["benjamini_hochberg_adjusted_p"]
        te = row["tracking_error_pct"]
        years = row["years_to_distinguish_at_80pc_power"]
        window = row["window"]
        assert isinstance(window, Sequence)
        lines.append(
            f"{row['arm']!s:30s}"
            f"{window[0]!s:>9s}"
            f"{float(str(row['growth_pp_yr'])):>8.2f}"
            f"{'      --' if gap is None else f'{float(str(gap)):>8.2f}'}"
            f"{'     --' if mde is None else f'{float(str(mde)):>7.2f}'}"
            f"{'      --' if interval is None else f'{float(str(interval[0])):>8.2f}'}"  # type: ignore[index]
            f"{'      --' if interval is None else f'{float(str(interval[1])):>8.2f}'}"  # type: ignore[index]
            f"{'     --' if adjusted is None else f'{float(str(adjusted)):>7.3f}'}"
            f"{'    --' if te is None else f'{float(str(te)):>6.1f}'}"
            f"{'     --' if years is None else f'{float(str(years)):>7.0f}'}"
            f"{float(str(row['max_drawdown_pct'])):>7.1f}"
            f"{float(str(row['gross_notional'])):>7.2f}"
            f"{row['status']!s:>12s}"
        )
    lines.append("")
    lines.append(
        "`from` is the first month each arm is scored on. A growth figure from "
        "1990-11 and one from 2000-11 are not comparable and the gap column, not "
        "the growth column, is the one that is."
    )
    lines.append("")
    lines.append(str(diagnostics["what_this_cannot_resolve"]))
    lines.append("")
    for caveat in result.caveats:
        lines.append(f"- {caveat}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 016 through the runner and the ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_016_construction_tournament",
        description=(
            "Score twenty-one portfolio constructions against three benchmarks on "
            "basis-mapped funds, writing a ledger entry for the attempt."
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
            path = workspace_root() / location
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
                "exp_016_construction_tournament"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
