"""Experiment 023: the tilt complex out of sample, on AQR's VME factors.

What this is
------------
016e's one resolvable whole-portfolio result is the tilt complex against the
cheap same-split index, +0.80 pp/yr on 1990-11..2026-05. Most of that edge
comes from French developed ex-US and emerging panels that begin 1990-11 and
have no out-of-sample period. AQR's Value and Momentum Everywhere workbook
carries stock-selection value and momentum for the US, UK, continental Europe
and Japan from the 1970s, so the same complex can be scored on the years before
the French ex-US panels exist. That is what this module does, with the same
loadings, the same costs and the same inference machinery, and it reports the
basis check on the overlapping window beside the out-of-sample result.

What this is NOT
----------------
**It scores no fund.** Every fund is 016e's basis expression, carried onto VME
legs where a counterpart exists and dropped where none does. **It fits
nothing.** The loadings are 016e's, the bridge slopes are pinned in the
specification, and nothing is estimated on the out-of-sample window.
**Its estimand is the arithmetic active-leg gap**, not 016e's simulated
log-growth gap, because no non-US market series exists before 1990-07; the
difference is priced on the overlap window and reported.

Run it::

    uv run python -m portfolio_edge.experiments.exp_023_tilts_out_of_sample --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_016_construction_tournament import (
    MDE_MULTIPLIER,
    MONTHS_PER_YEAR,
    _at,
    _load_pinned_file,
    _mapping,
    _number,
    _numbers,
    _sequence,
    _text,
    underperformance,
    workspace_root,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_index, period_from_index
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
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.inference.multiple_testing import benjamini_hochberg

FloatArray = NDArray[np.float64]

ENTRY_POINT: Final = "exp_023_tilts_out_of_sample"

#: French legs that consume capital. They cancel between the two portfolios up
#: to the regional residual, which is priced on the French basis only.
MARKET_LEGS: Final = frozenset({"us_mkt", "dxus_mkt", "em_mkt"})

#: The three VME legs and the workbook columns each is the equal-weighted mean of.
VME_COLUMNS: Final[Mapping[str, tuple[str, ...]]] = {
    "us_val": ("VALLS_VME_US90",),
    "dev_val": ("VALLS_VME_UK90", "VALLS_VME_ROE90", "VALLS_VME_JP90"),
    "dev_mom": ("MOMLS_VME_UK90", "MOMLS_VME_ROE90", "MOMLS_VME_JP90"),
}

#: French legs read for the basis check, the bridge and the unmapped-leg price.
FRENCH_COLUMNS: Final[Mapping[str, tuple[str, str]]] = {
    "us_mkt": ("french_us_ff5", "Mkt-RF"),
    "us_hml": ("french_us_ff5", "HML"),
    "dxus_mkt": ("french_developed_ex_us_ff5", "Mkt-RF"),
    "dxus_smb": ("french_developed_ex_us_ff5", "SMB"),
    "dxus_hml": ("french_developed_ex_us_ff5", "HML"),
    "dxus_rmw": ("french_developed_ex_us_ff5", "RMW"),
    "dxus_cma": ("french_developed_ex_us_ff5", "CMA"),
    "dxus_umd": ("french_developed_ex_us_momentum", "WML"),
    "em_mkt": ("french_emerging_ff5", "Mkt-RF"),
    "em_hml": ("french_emerging_ff5", "HML"),
}

__all__ = [
    "ENTRY_POINT",
    "Arm",
    "ArmResult",
    "GapSummary",
    "SeriesStore",
    "active_exposure",
    "aligned",
    "apply_falsifier",
    "build_registry",
    "cost_difference_bp",
    "default_specification_path",
    "gap_summary",
    "main",
    "read_arms",
    "read_mappings",
    "run",
]


class TiltsOutOfSampleError(Exception):
    """The experiment refused to run, or a source did not match its pin."""


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_023_tilts_out_of_sample.yaml"


# --------------------------------------------------------------------------- #
# Series
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class SeriesStore:
    """Monthly series keyed by name, each a ``period -> value`` mapping.

    Series start on different dates, so nothing is intersected until an arm
    asks for a window; :func:`aligned` does that per arm and refuses a window
    with a gap in it.
    """

    series: Mapping[str, Mapping[str, float]]
    provenance: tuple[Mapping[str, JsonValue], ...] = ()
    findings: tuple[str, ...] = ()

    def first(self, name: str) -> str:
        return min(self.series[name], key=month_index)

    def last(self, name: str) -> str:
        return max(self.series[name], key=month_index)


def aligned(
    store: SeriesStore, names: Sequence[str], *, start: str, end: str
) -> tuple[tuple[str, ...], FloatArray]:
    """The named series on ``start..end`` as a ``(T, len(names))`` matrix.

    Every month in the window must be present in every named series; a missing
    month is an error rather than a silently shorter sample.
    """
    first, last = month_index(start), month_index(end)
    periods = tuple(period_from_index(index) for index in range(first, last + 1))
    columns: list[FloatArray] = []
    for name in names:
        try:
            values = store.series[name]
        except KeyError:
            raise TiltsOutOfSampleError(f"no series {name!r}") from None
        missing = [period for period in periods if period not in values]
        if missing:
            raise TiltsOutOfSampleError(
                f"series {name!r} is missing {len(missing)} month(s) in {start}..{end}, "
                f"first {missing[0]}"
            )
        columns.append(np.array([values[period] for period in periods], dtype=np.float64))
    matrix = np.column_stack(columns) if columns else np.zeros((len(periods), 0))
    return periods, matrix


def load_series(specification: Specification) -> SeriesStore:
    """Read the pinned files and build the VME legs and the French legs."""
    parameters = _mapping(specification.parameters, where="parameters")
    pin_block = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    entries = _sequence(_at(pin_block, "files", where="source_pin"), where="source_pin.files")
    cache = RawCache()

    tables = {}
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []
    for item in entries:
        pin = _mapping(item, where="source_pin.files[]")
        table, record, table_findings = _load_pinned_file(pin, cache=cache)
        tables[str(record["id"])] = table
        provenance.append(record)
        findings.extend(f"{record['id']}: {finding}" for finding in table_findings)

    def column(file_id: str, name: str) -> dict[str, float]:
        table = tables[file_id]
        return {
            period: float(value)
            for period, value in zip(table.periods, table.column(name), strict=True)
            if value is not None
        }

    series: dict[str, Mapping[str, float]] = {}
    for leg, columns in VME_COLUMNS.items():
        parts = [column("aqr_vme_factors", name) for name in columns]
        for name, part in zip(columns, parts, strict=True):
            findings.append(
                f"{name}: first {min(part, key=month_index)}, last {max(part, key=month_index)}, "
                f"{len(part)} observations"
            )
        common = set(parts[0])
        for part in parts[1:]:
            common &= set(part)
        series[leg] = {
            period: float(np.mean([part[period] for part in parts])) for period in common
        }
    for leg, (file_id, name) in FRENCH_COLUMNS.items():
        series[leg] = column(file_id, name)
    findings.append(
        "nothing was read from the VME asset-allocation columns; only the seven pinned "
        "stock-selection columns entered"
    )
    return SeriesStore(series=series, provenance=tuple(provenance), findings=tuple(findings))


# --------------------------------------------------------------------------- #
# Mapping: fund weights and French coefficients -> net active exposure by leg
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Mappings:
    complex_weights: Mapping[str, float]
    control_weights: Mapping[str, float]
    french: Mapping[str, Mapping[str, float]]
    """ticker -> French leg -> coefficient."""
    french_to_vme: Mapping[str, str | None]
    fees_bp: Mapping[str, float]
    bridge: Mapping[str, float]
    spread_difference_bp: float


def read_mappings(specification: Specification) -> Mappings:
    parameters = _mapping(specification.parameters, where="parameters")
    portfolios = _mapping(_at(parameters, "portfolios", where="parameters"), where="portfolios")
    mapping_block = _mapping(
        _at(parameters, "fund_mapping", where="parameters"), where="fund_mapping"
    )
    funds = _sequence(_at(mapping_block, "funds", where="fund_mapping"), where="funds")
    french: dict[str, Mapping[str, float]] = {}
    for index, item in enumerate(funds):
        entry = _mapping(item, where=f"fund_mapping.funds[{index}]")
        ticker = _text(entry, "ticker", where=f"fund_mapping.funds[{index}]")
        coefficients = _mapping(_at(entry, "french", where=ticker), where=f"{ticker}.french")
        french[ticker] = {leg: _number(coefficients, leg, where=ticker) for leg in coefficients}
    translation = _mapping(
        _at(mapping_block, "french_to_vme", where="fund_mapping"), where="french_to_vme"
    )
    french_to_vme: dict[str, str | None] = {}
    for leg in translation:
        target = translation[leg]
        french_to_vme[leg] = None if target is None else str(target)
    costs = _mapping(specification.cost_model, where="cost_model")
    fees = _mapping(_at(costs, "fund_expense_ratio_basis_points", where="cost_model"), where="fees")
    bridge = _mapping(_at(parameters, "bridge", where="parameters"), where="bridge")
    slopes = _mapping(_at(bridge, "slopes", where="bridge"), where="bridge.slopes")

    def weights(name: str) -> dict[str, float]:
        block = _mapping(_at(portfolios, name, where="portfolios"), where=name)
        return {ticker: _number(block, ticker, where=name) for ticker in block}

    return Mappings(
        complex_weights=weights("complex"),
        control_weights=weights("control"),
        french=french,
        french_to_vme=french_to_vme,
        fees_bp={ticker: _number(fees, ticker, where="fees") for ticker in fees},
        bridge={leg: _number(slopes, leg, where="bridge.slopes") for leg in slopes},
        spread_difference_bp=_number(
            costs, "rebalancing_spread_difference_bp_per_year", where="cost_model"
        ),
    )


def _net_french_exposure(
    mappings: Mappings, *, aves: str, loading_delta: float = 0.0
) -> dict[str, float]:
    """Complex minus control, French leg by French leg.

    ``aves`` is ``dropped`` (AVES scored as VXUS), ``developed_value`` (its
    ``em_hml`` carried as ``dxus_hml``) or ``emerging_value`` (as 016e).
    """
    exposure: dict[str, float] = {}
    for weights, sign in ((mappings.complex_weights, 1.0), (mappings.control_weights, -1.0)):
        for ticker, weight in weights.items():
            effective = ticker
            if ticker == "AVES" and aves == "dropped":
                effective = "VXUS"
            for leg, raw in mappings.french[effective].items():
                coefficient = raw
                if leg not in MARKET_LEGS and loading_delta:
                    coefficient += loading_delta * math.copysign(1.0, raw)
                target = leg
                if effective == "AVES" and leg == "em_hml" and aves == "developed_value":
                    target = "dxus_hml"
                exposure[target] = exposure.get(target, 0.0) + sign * weight * coefficient
    return exposure


def active_exposure(
    mappings: Mappings,
    *,
    basis: str,
    aves: str,
    scaling: str = "unscaled",
    complete: bool = False,
    loading_delta: float = 0.0,
) -> dict[str, float]:
    """Net active exposure of the complex over the control, by basis leg.

    On the ``vme`` basis each French factor leg is carried onto its VME leg or
    dropped; market legs never enter. On the ``french`` basis the mapped factor
    legs enter, and ``complete`` adds the unmapped legs and the market residual.
    """
    if aves not in {"dropped", "developed_value", "emerging_value"}:
        raise TiltsOutOfSampleError(f"unknown AVES treatment {aves!r}")
    if basis == "vme" and aves == "emerging_value":
        raise TiltsOutOfSampleError("the VME basis has no emerging value leg")
    if basis == "french" and aves == "developed_value":
        raise TiltsOutOfSampleError("the French basis carries AVES on em_hml, not dxus_hml")
    french = _net_french_exposure(mappings, aves=aves, loading_delta=loading_delta)
    out: dict[str, float] = {}
    for leg, value in french.items():
        if basis == "vme":
            target = mappings.french_to_vme.get(leg)
            if target is None:
                continue
            scale = 1.0
            if scaling == "bridged":
                scale = mappings.bridge[target]
            elif scaling != "unscaled":
                raise TiltsOutOfSampleError(f"unknown scaling {scaling!r}")
            out[target] = out.get(target, 0.0) + value * scale
        elif basis == "french":
            mapped = mappings.french_to_vme.get(leg) is not None
            if mapped or complete:
                out[leg] = out.get(leg, 0.0) + value
        else:
            raise TiltsOutOfSampleError(f"unknown basis {basis!r}")
    return {leg: value for leg, value in out.items() if abs(value) > 1e-12}


def cost_difference_bp(mappings: Mappings, *, aves: str) -> float:
    """Complex fee less control fee, plus the spread constant, in bp/yr."""
    total = 0.0
    for weights, sign in ((mappings.complex_weights, 1.0), (mappings.control_weights, -1.0)):
        for ticker, weight in weights.items():
            effective = "VXUS" if ticker == "AVES" and aves == "dropped" else ticker
            total += sign * weight * mappings.fees_bp[effective]
    return total + mappings.spread_difference_bp


# --------------------------------------------------------------------------- #
# Arms
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Arm:
    name: str
    role: str
    window: str
    start: str
    end: str
    basis: str
    scaling: str
    aves: str
    complete: bool = False
    note: str = ""


def read_arms(specification: Specification) -> dict[str, Arm]:
    parameters = _mapping(specification.parameters, where="parameters")
    eras = {era.name: era for era in specification.sample_policy.eras}
    block = _mapping(_at(parameters, "arms", where="parameters"), where="arms")
    arms: dict[str, Arm] = {}
    for name in block:
        entry = _mapping(block[name], where=f"arms.{name}")
        window = _text(entry, "window", where=name)
        if window not in eras:
            raise TiltsOutOfSampleError(f"arm {name!r} names undeclared window {window!r}")
        arms[name] = Arm(
            name=name,
            role=_text(entry, "role", where=name),
            window=window,
            start=eras[window].start,
            end=eras[window].end,
            basis=_text(entry, "basis", where=name),
            scaling=_text(entry, "scaling", where=name),
            aves=_text(entry, "aves", where=name),
            complete=bool(entry.get("complete", False)),
            note=str(entry.get("note") or ""),
        )
    return arms


# --------------------------------------------------------------------------- #
# Statistics on one paired difference series
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class GapSummary:
    gap_pp_yr: float
    hac_interval: tuple[float, float]
    hac_se_pp_yr: float
    hac_t: float
    hac_p: float
    hac_lags: int
    bootstrap_interval: tuple[float, float]
    bootstrap_p: float
    mde_iid_pp_yr: float
    mde_hac_pp_yr: float
    mde_bootstrap_pp_yr: float
    tracking_error_pct: float
    years_to_distinguish: float
    months: int


def gap_summary(
    difference: FloatArray, *, indices: NDArray[np.intp], confidence: float
) -> GapSummary:
    """Mean gap in pp/yr with HAC and block-bootstrap intervals and three floors."""
    n = difference.size
    if n < 3:
        raise TiltsOutOfSampleError("a gap needs at least three months")
    scale = 100.0 * MONTHS_PER_YEAR
    gap = float(np.mean(difference)) * scale
    hac = hac_mean(difference)
    hac_se = hac.standard_error * scale
    z = 1.959963984540054
    resampled = difference[indices].mean(axis=1) * scale
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(resampled, [tail, 1.0 - tail])
    centred = resampled - gap
    exceed = int(np.sum(np.abs(centred) >= abs(gap)))
    sd = float(np.std(difference, ddof=1))
    annual_sigma = sd * math.sqrt(MONTHS_PER_YEAR) * 100.0
    years = n / MONTHS_PER_YEAR
    return GapSummary(
        gap_pp_yr=gap,
        hac_interval=(gap - z * hac_se, gap + z * hac_se),
        hac_se_pp_yr=hac_se,
        hac_t=hac.t_statistic,
        hac_p=hac.p_value,
        hac_lags=hac.n_lags,
        bootstrap_interval=(float(low), float(high)),
        bootstrap_p=(exceed + 1) / (resampled.size + 1),
        mde_iid_pp_yr=MDE_MULTIPLIER * annual_sigma / math.sqrt(years),
        mde_hac_pp_yr=MDE_MULTIPLIER * hac_se,
        mde_bootstrap_pp_yr=MDE_MULTIPLIER * float(np.std(resampled, ddof=1)),
        tracking_error_pct=annual_sigma,
        years_to_distinguish=(
            float("inf") if gap == 0.0 else (MDE_MULTIPLIER * annual_sigma / abs(gap)) ** 2
        ),
        months=n,
    )


@dataclass(slots=True, kw_only=True)
class ArmResult:
    arm: Arm
    exposure: Mapping[str, float]
    cost_bp: float
    summary: GapSummary
    contributions: Mapping[str, float]
    sub_periods: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    best_month_removed: float = math.nan
    worst_month_removed: float = math.nan
    perturbation_range: tuple[float, float] = (math.nan, math.nan)
    block_robustness: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    p_underperform: Mapping[str, float] = field(default_factory=dict)
    shortfall_pp_yr: Mapping[str, float] = field(default_factory=dict)
    adjusted_p: float | None = None
    status: str = "not-scored"
    clause: str = ""

    def to_json(self) -> dict[str, JsonValue]:
        s = self.summary
        return {
            "arm": self.arm.name,
            "role": self.arm.role,
            "window": f"{self.arm.start}..{self.arm.end}",
            "basis": self.arm.basis,
            "scaling": self.arm.scaling,
            "aves": self.arm.aves,
            "months": s.months,
            "exposure": {k: round(v, 5) for k, v in sorted(self.exposure.items())},
            "cost_bp_per_year": round(self.cost_bp, 4),
            "gap_pp_yr": round(s.gap_pp_yr, 4),
            "hac_interval_pp_yr": [round(s.hac_interval[0], 4), round(s.hac_interval[1], 4)],
            "hac_t": round(s.hac_t, 3),
            "hac_p": round(s.hac_p, 5),
            "hac_lags": s.hac_lags,
            "bootstrap_interval_pp_yr": [
                round(s.bootstrap_interval[0], 4),
                round(s.bootstrap_interval[1], 4),
            ],
            "bootstrap_p": round(s.bootstrap_p, 5),
            "mde_80pc_power_iid_pp_yr": round(s.mde_iid_pp_yr, 4),
            "mde_80pc_power_hac_pp_yr": round(s.mde_hac_pp_yr, 4),
            "mde_80pc_power_block_bootstrap_pp_yr": round(s.mde_bootstrap_pp_yr, 4),
            "tracking_error_pct": round(s.tracking_error_pct, 4),
            "years_to_distinguish_at_80pc_power": round(s.years_to_distinguish, 1),
            "contributions_pp_yr": {k: round(v, 4) for k, v in self.contributions.items()},
            "sub_periods": {
                era: {k: round(v, 4) for k, v in values.items()}
                for era, values in self.sub_periods.items()
            },
            "gap_best_month_removed_pp_yr": round(self.best_month_removed, 4),
            "gap_worst_month_removed_pp_yr": round(self.worst_month_removed, 4),
            "perturbation_gap_range_pp_yr": [
                round(self.perturbation_range[0], 4),
                round(self.perturbation_range[1], 4),
            ],
            "bootstrap_interval_by_block_months": {
                k: [round(v[0], 4), round(v[1], 4)] for k, v in self.block_robustness.items()
            },
            "p_underperform": {k: round(v, 4) for k, v in self.p_underperform.items()},
            "median_shortfall_if_underperforming_pp_yr": {
                k: round(v, 4) for k, v in self.shortfall_pp_yr.items()
            },
            "benjamini_hochberg_adjusted_p": (
                None if self.adjusted_p is None else round(self.adjusted_p, 5)
            ),
            "status": self.status,
            "falsifier_clause": self.clause,
            "note": self.arm.note,
        }


def apply_falsifier(result: ArmResult) -> None:
    """Clauses (a) to (e) of the frozen specification, in order."""
    s = result.summary
    if s.gap_pp_yr <= 0.0:
        result.status, result.clause = "rejected", "(a) gap at or below zero"
        return
    if s.gap_pp_yr < s.mde_iid_pp_yr:
        result.status, result.clause = (
            "unresolved",
            f"(b) the gap {s.gap_pp_yr:+.2f} pp/yr is inside this arm's own "
            f"{s.mde_iid_pp_yr:.2f} pp/yr i.i.d. detection floor at 80% power "
            f"(HAC {s.mde_hac_pp_yr:.2f}, block bootstrap {s.mde_bootstrap_pp_yr:.2f})",
        )
        return
    if s.bootstrap_interval[0] <= 0.0 or s.hac_interval[0] <= 0.0:
        result.status, result.clause = (
            "unresolved",
            "(c) a 95% interval includes zero: block bootstrap "
            f"[{s.bootstrap_interval[0]:+.2f}, {s.bootstrap_interval[1]:+.2f}], HAC "
            f"[{s.hac_interval[0]:+.2f}, {s.hac_interval[1]:+.2f}]",
        )
        return
    halves = [v["gap_pp_yr"] for v in result.sub_periods.values()]
    if result.perturbation_range[0] <= 0.0 or any(h <= 0.0 for h in halves):
        result.status, result.clause = (
            "unresolved",
            f"(d) the sign is not stable: perturbation range "
            f"[{result.perturbation_range[0]:+.2f}, {result.perturbation_range[1]:+.2f}], "
            f"sub-periods {[round(h, 2) for h in halves]}",
        )
        return
    result.status, result.clause = "exploratory", "(e) survived every clause"


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def _difference(
    store: SeriesStore, exposure: Mapping[str, float], *, cost_bp: float, start: str, end: str
) -> tuple[tuple[str, ...], FloatArray, dict[str, float]]:
    """The paired monthly difference and each leg's mean contribution in pp/yr."""
    legs = sorted(exposure)
    periods, matrix = aligned(store, legs, start=start, end=end)
    weights = np.array([exposure[leg] for leg in legs], dtype=np.float64)
    monthly_cost = cost_bp / 10_000.0 / MONTHS_PER_YEAR
    difference = matrix @ weights - monthly_cost
    contributions = {
        leg: float(np.mean(matrix[:, i])) * exposure[leg] * 1200.0 for i, leg in enumerate(legs)
    }
    contributions["cost"] = -cost_bp / 100.0
    return periods, difference, contributions


def _slice(periods: Sequence[str], difference: FloatArray, *, start: str, end: str) -> FloatArray:
    first, last = month_index(start), month_index(end)
    keep = [i for i, p in enumerate(periods) if first <= month_index(p) <= last]
    return difference[np.asarray(keep, dtype=np.intp)]


def _bridge_check(
    store: SeriesStore, pinned: Mapping[str, float], *, start: str, end: str
) -> dict[str, JsonValue]:
    pairs = {"us_val": "us_hml", "dev_val": "dxus_hml", "dev_mom": "dxus_umd"}
    out: dict[str, JsonValue] = {}
    for vme_leg, french_leg in pairs.items():
        _, matrix = aligned(store, [french_leg, vme_leg], start=start, end=end)
        french, vme = matrix[:, 0], matrix[:, 1]
        slope = float(np.cov(french, vme)[0, 1] / np.var(vme, ddof=1))
        out[vme_leg] = {
            "french_leg": french_leg,
            "pinned_slope": pinned[vme_leg],
            "recomputed_slope": round(slope, 4),
            "drift": round(slope - pinned[vme_leg], 4),
            "correlation": round(float(np.corrcoef(french, vme)[0, 1]), 4),
            "french_mean_pp_yr": round(float(np.mean(french)) * 1200.0, 4),
            "vme_mean_pp_yr": round(float(np.mean(vme)) * 1200.0, 4),
            "french_vol_pct": round(float(np.std(french, ddof=1)) * math.sqrt(12) * 100.0, 4),
            "vme_vol_pct": round(float(np.std(vme, ddof=1)) * math.sqrt(12) * 100.0, 4),
        }
    return out


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    parameters = _mapping(specification.parameters, where="parameters")
    store = load_series(specification)
    mappings = read_mappings(specification)
    arms = read_arms(specification)
    eras = {era.name: era for era in specification.sample_policy.eras}
    primary_name = _text(parameters, "primary_arm", where="parameters")
    if primary_name not in arms:
        raise TiltsOutOfSampleError(f"primary arm {primary_name!r} is not declared")

    block_months = _number(parameters, "bootstrap_block_months", where="parameters")
    robustness = _numbers(
        _at(parameters, "bootstrap_block_robustness_months", where="parameters"), where="blocks"
    )
    deltas = _numbers(
        _at(
            _mapping(_at(parameters, "loading_perturbation", where="parameters"), where="p"),
            "factor_loading_delta",
            where="loading_perturbation",
        ),
        where="factor_loading_delta",
    )
    sub_periods = _mapping(
        _at(parameters, "sub_periods_by_window", where="parameters"), where="sub_periods"
    )
    horizons = _mapping(
        _at(parameters, "underperformance_horizons_years", where="parameters"), where="horizons"
    )
    confidence = specification.inference.confidence_level
    resamples = specification.inference.resamples
    rng = context.rng
    indices_by_length: dict[tuple[int, float], NDArray[np.intp]] = {}

    def indices(n: int, block: float) -> NDArray[np.intp]:
        key = (n, block)
        if key not in indices_by_length:
            indices_by_length[key] = stationary_bootstrap_indices(n, block, resamples, rng)
        return indices_by_length[key]

    results: dict[str, ArmResult] = {}
    for name, arm in arms.items():
        exposure = active_exposure(
            mappings, basis=arm.basis, aves=arm.aves, scaling=arm.scaling, complete=arm.complete
        )
        cost = cost_difference_bp(mappings, aves=arm.aves)
        periods, difference, contributions = _difference(
            store, exposure, cost_bp=cost, start=arm.start, end=arm.end
        )
        summary = gap_summary(
            difference, indices=indices(difference.size, block_months), confidence=confidence
        )
        result = ArmResult(
            arm=arm, exposure=exposure, cost_bp=cost, summary=summary, contributions=contributions
        )
        # Sub-periods declared for this window.
        declared = sub_periods.get(arm.window)
        eras_here = (
            [] if declared is None else [str(e) for e in _sequence(declared, where=arm.window)]
        )
        subs: dict[str, dict[str, float]] = {}
        for era_name in eras_here:
            era = eras[era_name]
            part = _slice(periods, difference, start=era.start, end=era.end)
            subs[era_name] = {
                "gap_pp_yr": float(np.mean(part)) * 1200.0,
                "months": float(part.size),
                "mde_iid_pp_yr": (
                    MDE_MULTIPLIER
                    * float(np.std(part, ddof=1))
                    * math.sqrt(MONTHS_PER_YEAR)
                    * 100.0
                    / math.sqrt(part.size / MONTHS_PER_YEAR)
                ),
            }
        result.sub_periods = subs
        # Leave-one-out extremes.
        order = np.argsort(difference)
        result.best_month_removed = float(np.mean(np.delete(difference, order[-1]))) * 1200.0
        result.worst_month_removed = float(np.mean(np.delete(difference, order[0]))) * 1200.0
        # Loading perturbation.
        grid: list[float] = []
        for delta in deltas:
            shifted = active_exposure(
                mappings,
                basis=arm.basis,
                aves=arm.aves,
                scaling=arm.scaling,
                complete=arm.complete,
                loading_delta=delta,
            )
            _, shifted_difference, _ = _difference(
                store, shifted, cost_bp=cost, start=arm.start, end=arm.end
            )
            grid.append(float(np.mean(shifted_difference)) * 1200.0)
        result.perturbation_range = (min(grid), max(grid))
        # Block-length robustness.
        robust: dict[str, tuple[float, float]] = {}
        for block in robustness:
            alt = gap_summary(
                difference, indices=indices(difference.size, block), confidence=confidence
            )
            robust[f"{int(block)}m"] = alt.bootstrap_interval
        result.block_robustness = robust
        # Trailing probabilities on the declared horizons.
        declared_h = horizons.get(arm.window)
        probabilities: dict[str, float] = {}
        shortfalls: dict[str, float] = {}
        if declared_h is not None:
            for years in _numbers(declared_h, where=arm.window):
                if int(years) * MONTHS_PER_YEAR > difference.size:
                    continue
                # log1p(expm1(d)) - log1p(0) = d, so the log-based helper scores
                # the arithmetic difference exactly.
                zeros = np.zeros_like(difference)
                probability, magnitude = underperformance(
                    np.expm1(difference),
                    zeros,
                    years=int(years),
                    rng=rng,
                    block_months=block_months,
                    draws=10_000,
                )
                probabilities[f"{int(years)}y"] = probability
                shortfalls[f"{int(years)}y"] = magnitude
        result.p_underperform = probabilities
        result.shortfall_pp_yr = shortfalls
        results[name] = result

    # Benjamini-Hochberg over the secondary arms, for information only.
    secondary = [name for name in results if name != primary_name]
    adjusted = benjamini_hochberg([results[n].summary.bootstrap_p for n in secondary], alpha=0.10)
    for name, value in zip(secondary, adjusted.adjusted_p_values, strict=True):
        results[name].adjusted_p = float(value)
    for result in results.values():
        apply_falsifier(result)

    # Leg-level figures on each leg's own longest pre-1990-11 window.
    leg_windows = _mapping(_at(parameters, "leg_windows", where="parameters"), where="leg_windows")
    primary_exposure = results[primary_name].exposure
    legs_json: dict[str, JsonValue] = {}
    for leg in leg_windows:
        era = eras[str(leg_windows[leg])]
        _, matrix = aligned(store, [leg], start=era.start, end=era.end)
        series = matrix[:, 0]
        exposure_here = primary_exposure.get(leg, 0.0)
        contribution = series * exposure_here
        leg_summary = gap_summary(
            contribution, indices=indices(contribution.size, block_months), confidence=confidence
        )
        premium = gap_summary(
            series, indices=indices(series.size, block_months), confidence=confidence
        )
        legs_json[leg] = {
            "window": f"{era.start}..{era.end}",
            "months": series.size,
            "exposure": round(exposure_here, 5),
            "premium_pp_yr": round(premium.gap_pp_yr, 4),
            "premium_hac_interval_pp_yr": [round(x, 4) for x in premium.hac_interval],
            "premium_mde_iid_pp_yr": round(premium.mde_iid_pp_yr, 4),
            "contribution_pp_yr": round(leg_summary.gap_pp_yr, 4),
            "contribution_hac_interval_pp_yr": [round(x, 4) for x in leg_summary.hac_interval],
            "contribution_mde_iid_pp_yr": round(leg_summary.mde_iid_pp_yr, 4),
        }

    # Basis check pieces on the overlap window, French basis.
    reference = _mapping(_at(parameters, "reference_016e", where="parameters"), where="reference")
    overlap = eras["overlap_with_016e"]
    bridge = _mapping(_at(parameters, "bridge", where="parameters"), where="bridge")
    tolerance = _number(bridge, "drift_tolerance", where="bridge")
    bridge_check = _bridge_check(store, mappings.bridge, start=overlap.start, end=overlap.end)
    drifted = [
        leg
        for leg, row in bridge_check.items()
        if isinstance(row, Mapping) and abs(float(str(row["drift"]))) > tolerance
    ]
    complete = active_exposure(mappings, basis="french", aves="emerging_value", complete=True)
    mapped_only = active_exposure(mappings, basis="french", aves="emerging_value")
    residual = {leg: complete[leg] for leg in complete if leg in MARKET_LEGS}
    unmapped = {
        leg: complete[leg] for leg in complete if leg not in MARKET_LEGS and leg not in mapped_only
    }
    _, residual_diff, residual_contrib = _difference(
        store, residual, cost_bp=0.0, start=overlap.start, end=overlap.end
    )
    _, unmapped_diff, unmapped_contrib = _difference(
        store, unmapped, cost_bp=0.0, start=overlap.start, end=overlap.end
    )
    ref_gap = _number(reference, "growth_gap_pp_yr", where="reference_016e")
    sigma_complex = _number(reference, "complex_volatility_pct", where="reference_016e") / 100.0
    sigma_control = _number(reference, "control_volatility_pct", where="reference_016e") / 100.0
    variance_drag = (sigma_control**2 - sigma_complex**2) / 2.0 * 100.0
    french_complete = results["tilts_overlap_french_complete"].summary.gap_pp_yr
    basis_check: dict[str, JsonValue] = {
        "reference_016e_growth_gap_pp_yr": ref_gap,
        "reference_016e_interval_pp_yr": _at(reference, "interval_pp_yr", where="r"),
        "reference_016e_mde_iid_pp_yr": _number(reference, "mde_iid_pp_yr", where="r"),
        "reference_016e_mde_block_bootstrap_pp_yr": _number(
            reference, "mde_block_bootstrap_pp_yr", where="r"
        ),
        "french_complete_arithmetic_gap_pp_yr": round(french_complete, 4),
        "variance_drag_arithmetic_minus_growth_pp_yr": round(variance_drag, 4),
        "french_complete_less_reference_pp_yr": round(french_complete - ref_gap, 4),
        "french_mapped_legs_only_gap_pp_yr": round(
            results["tilts_overlap_french"].summary.gap_pp_yr, 4
        ),
        "vme_unscaled_gap_pp_yr": round(results["tilts_overlap_vme"].summary.gap_pp_yr, 4),
        "vme_bridged_gap_pp_yr": round(results["tilts_overlap_vme_bridged"].summary.gap_pp_yr, 4),
        "regional_residual_exposure": {k: round(v, 5) for k, v in sorted(residual.items())},
        "regional_residual_pp_yr": round(float(np.mean(residual_diff)) * 1200.0, 4),
        "regional_residual_by_leg_pp_yr": {
            k: round(v, 4) for k, v in residual_contrib.items() if k != "cost"
        },
        "unmapped_exposure": {k: round(v, 5) for k, v in sorted(unmapped.items())},
        "unmapped_legs_pp_yr": round(float(np.mean(unmapped_diff)) * 1200.0, 4),
        "unmapped_by_leg_pp_yr": {
            k: round(v, 4) for k, v in unmapped_contrib.items() if k != "cost"
        },
        "bridge": bridge_check,
        "bridge_drift_beyond_tolerance": drifted,
    }

    primary = results[primary_name]
    hurdle = _number(parameters, "hlz_hurdle_t", where="parameters")
    status = {
        "rejected": ResultStatus.REJECTED,
        "unresolved": ResultStatus.UNRESOLVED,
        "exploratory": ResultStatus.EXPLORATORY,
    }[primary.status]
    ps = primary.summary
    summary_text = (
        f"PRIMARY, {primary.arm.start}..{primary.arm.end} ({ps.months} months), VME basis, "
        f"unscaled loadings, AVES dropped: the tilt complex's after-cost arithmetic gap over "
        f"the cheap 65/35 index is {ps.gap_pp_yr:+.2f} pp/yr, HAC 95% "
        f"[{ps.hac_interval[0]:+.2f}, {ps.hac_interval[1]:+.2f}], block bootstrap "
        f"[{ps.bootstrap_interval[0]:+.2f}, {ps.bootstrap_interval[1]:+.2f}], against floors of "
        f"{ps.mde_iid_pp_yr:.2f} (i.i.d.), {ps.mde_hac_pp_yr:.2f} (HAC) and "
        f"{ps.mde_bootstrap_pp_yr:.2f} (block bootstrap); tracking error "
        f"{ps.tracking_error_pct:.2f}%; implied HAC t {ps.hac_t:.2f} against a "
        f"{hurdle:.0f} hurdle. Status {primary.status}: {primary.clause}. "
        f"Basis check on {overlap.start}..{overlap.end}: VME unscaled "
        f"{results['tilts_overlap_vme'].summary.gap_pp_yr:+.2f}, VME bridged "
        f"{results['tilts_overlap_vme_bridged'].summary.gap_pp_yr:+.2f}, French complete "
        f"{french_complete:+.2f} against 016e's {ref_gap:+.2f}."
    )
    caveats = (
        "Every fund is 016e's basis expression; no fund return enters. On the VME basis the "
        "French loadings are applied UNSCALED to a rank-weighted long/short book they were not "
        "fitted on; the bridged arms carry the pinned overlap slopes and the pair brackets the "
        "translation.",
        "VME carries no size, profitability or investment factor. AVDV's small-cap half and "
        "IDMO's CMA leg are unmapped; their French-basis price on the overlap window is in "
        "`basis_check.unmapped_legs_pp_yr`.",
        "The primary window is 112 months, set by the first developed VME value observation. "
        "Its floor is about twice 016e's and the test is underpowered for a full-size "
        "replication; the specification says so before the run.",
        "The estimand is the arithmetic active-leg gap, not 016e's simulated log-growth gap; "
        "the regional residual and the variance-drag difference are priced on the overlap "
        "window in `basis_check`.",
        "Nothing was read from the VME asset-allocation legs. The stock-selection series are "
        "vendor-authored, reconstructed on every update, and gross of every implementation "
        "cost, as the French series are.",
        "The design was chosen after reading the 1990-2026 result. The window is out of "
        "sample for the data; nothing here is out of sample for the design.",
    )
    arms_json: list[JsonValue] = [results[name].to_json() for name in arms]
    diagnostics: dict[str, JsonValue] = {
        "freeze_note": (
            "Primary outcome predeclared: arithmetic-mean gap of the tilt complex over the "
            "cheap index on 1981-07..1990-10, VME basis, unscaled loadings, AVES dropped. "
            "Predicted +0.4 to +1.2 pp/yr and unresolved against a floor near 1.0."
        ),
        "primary_arm": primary_name,
        "arms": arms_json,
        "leg_level_on_longest_oos_windows": legs_json,
        "basis_check": basis_check,
        "hlz_hurdle_t": hurdle,
        "provenance": list(store.provenance),
        "series_findings": list(store.findings),
        "markdown_tables": render_tables(results, legs_json, basis_check, primary_name),
    }
    return ExperimentResult(
        status=status,
        summary=summary_text,
        estimates=_build_estimates(results),
        diagnostics=diagnostics,
        caveats=caveats,
    )


def _build_estimates(results: Mapping[str, ArmResult]) -> tuple[Estimate, ...]:
    estimates: list[Estimate] = []
    for name in results:
        r = results[name]
        s = r.summary
        window = f"{r.arm.start}..{r.arm.end}"
        note = (
            f"{r.arm.role}; window {window}; basis {r.arm.basis}, {r.arm.scaling}, AVES "
            f"{r.arm.aves}; floors i.i.d. {s.mde_iid_pp_yr:.2f}, HAC {s.mde_hac_pp_yr:.2f}, "
            f"block bootstrap {s.mde_bootstrap_pp_yr:.2f} pp/yr; tracking error "
            f"{s.tracking_error_pct:.2f}%; {s.years_to_distinguish:.0f} years to distinguish; "
            f"status {r.status}; {r.clause}"
        )
        estimates.append(
            Estimate(
                name=f"arithmetic_gap[{name}]",
                value=s.gap_pp_yr,
                units="percentage points per year",
                interval=s.bootstrap_interval,
                interval_method=(
                    "stationary block bootstrap of the paired difference, mean block 12 "
                    "months, 10000 resamples, 95% percentile"
                ),
                cost_basis=CostBasis.NET_PESSIMISTIC,
                n_obs=s.months,
                notes=note,
            )
        )
        estimates.append(
            Estimate(
                name=f"arithmetic_gap_hac[{name}]",
                value=s.gap_pp_yr,
                units="percentage points per year",
                interval=s.hac_interval,
                interval_method=(
                    f"Newey-West HAC, {s.hac_lags} lags by the automatic rule, 95% normal"
                ),
                cost_basis=CostBasis.NET_PESSIMISTIC,
                n_obs=s.months,
                notes=f"same point estimate as arithmetic_gap[{name}]; HAC t {s.hac_t:.2f}",
            )
        )
        estimates.append(
            Estimate(
                name=f"minimum_detectable_effect_iid[{name}]",
                value=s.mde_iid_pp_yr,
                units="percentage points per year",
                n_obs=s.months,
                notes=(
                    f"80% power, two-sided 0.05; HAC {s.mde_hac_pp_yr:.4f}, block bootstrap "
                    f"{s.mde_bootstrap_pp_yr:.4f}"
                ),
                uncertainty_unavailable_reason=(
                    "a detection floor is a property of the design, not an estimate of a "
                    "quantity in the world, so it carries no interval"
                ),
            )
        )
    return tuple(estimates)


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #


def _f(value: float, digits: int = 2, sign: bool = True) -> str:
    if not math.isfinite(value):
        return "n/a"
    return f"{value:+.{digits}f}" if sign else f"{value:.{digits}f}"


def render_tables(
    results: Mapping[str, ArmResult],
    legs: Mapping[str, JsonValue],
    basis_check: Mapping[str, JsonValue],
    primary_name: str,
) -> str:
    lines: list[str] = ["## Arms", ""]
    lines.append(
        "| Arm | Window | Months | Basis | Gap, pp/yr | HAC 95% | Bootstrap 95% | "
        "Floor i.i.d. | Floor HAC | Floor boot | TE | Years | t | Status |"
    )
    lines.append("| --- | --- | ---: | --- | ---: | :---: | :---: " + "| ---: " * 6 + "| --- |")
    for name, r in results.items():
        s = r.summary
        label = f"**{name}**" if name == primary_name else name
        basis = f"{r.arm.basis}, {r.arm.scaling}, AVES {r.arm.aves}"
        lines.append(
            f"| {label} | {r.arm.start}..{r.arm.end} | {s.months} | {basis} | {_f(s.gap_pp_yr)} | "
            f"[{_f(s.hac_interval[0])}, {_f(s.hac_interval[1])}] | "
            f"[{_f(s.bootstrap_interval[0])}, {_f(s.bootstrap_interval[1])}] | "
            f"{_f(s.mde_iid_pp_yr, sign=False)} | {_f(s.mde_hac_pp_yr, sign=False)} | "
            f"{_f(s.mde_bootstrap_pp_yr, sign=False)} | {s.tracking_error_pct:.2f}% | "
            f"{s.years_to_distinguish:.0f} | {s.hac_t:.2f} | {r.status} |"
        )
    lines.extend(["", "## Attribution, pp/yr", ""])
    all_legs = sorted({leg for r in results.values() for leg in r.contributions})
    lines.append("| Arm | " + " | ".join(all_legs) + " | Total |")
    lines.append("| --- | " + " | ".join("---:" for _ in all_legs) + " | ---: |")
    for name, r in results.items():
        cells = [
            _f(r.contributions.get(leg, 0.0)) if leg in r.contributions else "" for leg in all_legs
        ]
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {_f(r.summary.gap_pp_yr)} |")
    lines.extend(["", "## Sub-periods, hostile arms and trailing probabilities", ""])
    lines.append(
        "| Arm | Sub-period gaps (months, floor) | Best month removed | Worst month removed | "
        "Perturbation range | Boot 6m | Boot 24m | P(trail) | Median shortfall |"
    )
    lines.append("| --- | --- | ---: | ---: | :---: | :---: | :---: | --- | --- |")
    for name, r in results.items():
        subs = "; ".join(
            f"{era} {_f(v['gap_pp_yr'])} ({int(v['months'])}, {v['mde_iid_pp_yr']:.2f})"
            for era, v in r.sub_periods.items()
        )
        boot6 = r.block_robustness.get("6m", (math.nan, math.nan))
        boot24 = r.block_robustness.get("24m", (math.nan, math.nan))
        trail = ", ".join(f"{k} {v:.1%}" for k, v in r.p_underperform.items()) or "n/a"
        short = ", ".join(f"{k} {_f(v)}" for k, v in r.shortfall_pp_yr.items()) or "n/a"
        lines.append(
            f"| {name} | {subs or 'none declared'} | {_f(r.best_month_removed)} | "
            f"{_f(r.worst_month_removed)} | [{_f(r.perturbation_range[0])}, "
            f"{_f(r.perturbation_range[1])}] | [{_f(boot6[0])}, {_f(boot6[1])}] | "
            f"[{_f(boot24[0])}, {_f(boot24[1])}] | {trail} | {short} |"
        )
    lines.extend(["", "## Each leg on its own longest pre-1990-11 window", ""])
    lines.append(
        "| Leg | Window | Months | Exposure | Premium, pp/yr | HAC 95% | Floor | "
        "Contribution, pp/yr | HAC 95% | Floor |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | :---: | ---: | ---: | :---: | ---: |")
    for leg, raw in legs.items():
        row = raw if isinstance(raw, Mapping) else {}
        p_int = row["premium_hac_interval_pp_yr"]
        c_int = row["contribution_hac_interval_pp_yr"]
        assert isinstance(p_int, Sequence) and isinstance(c_int, Sequence)
        lines.append(
            f"| {leg} | {row['window']} | {row['months']} | {float(str(row['exposure'])):+.4f} | "
            f"{float(str(row['premium_pp_yr'])):+.2f} | [{float(str(p_int[0])):+.2f}, "
            f"{float(str(p_int[1])):+.2f}] | {float(str(row['premium_mde_iid_pp_yr'])):.2f} | "
            f"{float(str(row['contribution_pp_yr'])):+.2f} | [{float(str(c_int[0])):+.2f}, "
            f"{float(str(c_int[1])):+.2f}] | {float(str(row['contribution_mde_iid_pp_yr'])):.2f} |"
        )
    lines.extend(["", "## Basis check, 1990-11..2026-05", ""])
    lines.append("| Quantity | pp/yr |")
    lines.append("| --- | ---: |")
    for key in (
        "reference_016e_growth_gap_pp_yr",
        "french_complete_arithmetic_gap_pp_yr",
        "variance_drag_arithmetic_minus_growth_pp_yr",
        "french_complete_less_reference_pp_yr",
        "french_mapped_legs_only_gap_pp_yr",
        "vme_unscaled_gap_pp_yr",
        "vme_bridged_gap_pp_yr",
        "regional_residual_pp_yr",
        "unmapped_legs_pp_yr",
    ):
        lines.append(f"| {key} | {float(str(basis_check[key])):+.4f} |")
    lines.extend(["", "### Bridge slopes, French factor on VME leg", ""])
    lines.append(
        "| VME leg | French leg | Pinned | Recomputed | Drift | Correlation | "
        "French mean | VME mean | French vol | VME vol |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    bridge = basis_check["bridge"]
    assert isinstance(bridge, Mapping)
    for leg, raw in bridge.items():
        row = raw if isinstance(raw, Mapping) else {}
        lines.append(
            f"| {leg} | {row['french_leg']} | {row['pinned_slope']} | {row['recomputed_slope']} | "
            f"{row['drift']} | {row['correlation']} | {row['french_mean_pp_yr']} | "
            f"{row['vme_mean_pp_yr']} | {row['french_vol_pct']} | {row['vme_vol_pct']} |"
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _manifest_hashes(specification: Specification) -> tuple[str, ...]:
    hashes: list[str] = []
    for source in specification.data_sources:
        if not isinstance(source, Mapping):
            continue
        location = source.get("manifest")
        if isinstance(location, str):
            path = workspace_root() / location
            if path.is_file():
                hashes.append(read_manifest(path).sha256_manifest())
    return tuple(hashes)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_023_tilts_out_of_sample",
        description="Score the tilt complex on AQR's VME factors before 1990-11.",
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument("--view-results", action="store_true")
    arguments = parser.parse_args(argv)
    specification = load_specification(arguments.specification)
    ledger = Ledger(arguments.ledger)
    outcome: RunOutcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=_manifest_hashes(specification),
    )
    result = outcome.result
    assert result is not None
    root = (
        Path(arguments.artifact_root) if arguments.artifact_root is not None else Path("artifacts")
    )
    tables_path = root / outcome.run_id / "tables.md"
    tables_path.write_text(str(result.diagnostics["markdown_tables"]), encoding="utf-8")
    print(f"run_id       {outcome.run_id}")
    print(f"spec_hash    {outcome.spec_hash}")
    print(f"result       {result.status.value}")
    print(f"git_commit   {outcome.git_state.commit} (dirty={outcome.git_state.dirty})")
    print(f"tables       {tables_path}")
    if arguments.view_results:
        ledger.record_results_viewed(
            outcome.run_id, origin=Origin(arguments.origin), notes="printed by --view-results"
        )
        print()
        print(result.summary)
        print()
        print(str(result.diagnostics["markdown_tables"]))
        for caveat in result.caveats:
            print(f"- {caveat}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
