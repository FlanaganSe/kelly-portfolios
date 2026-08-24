"""Experiment 008: do US-listed managed-futures ETFs deliver trend exposure?

Two things are going on in this module and they must not be confused.

**Part A** is a fund-implementation audit of the exchange-traded managed-futures
shelf, built from the SEC N-PORT census with a predeclared mechanical screen, in
the shape of Experiment 002. Every product is measured against AQR's published
time-series-momentum index -- the exact series Experiment 004 evaluated -- so that
the owner's question, "does Experiment 004's verdict transfer to these products?",
is answered rather than assumed.

**Part B** re-runs Experiment 004's *decision* under both readings of its clause
(d). It re-runs no data. Experiment 004's specification, its ledger entries and its
recorded status are untouched; this is a second, differently-specified look, and
the ledger shows both.

Why this experiment exists
--------------------------
Experiment 004 rejected the hypothesis that AQR's TSMOM **index** adds material
marginal value a simpler exposure cannot reproduce. That verdict was then repeated
to the project owner as if it applied to KMLM, DBMF and CTA. It does not: those
products were never tested, they have different construction, and DBMF is an
explicit *replication* strategy, which is directly interesting given Experiment
004's finding that a static replica captured 44% of the index's benefit. Separately,
the Bhardwaj-Gorton-Rouwenhorst (2014) evidence -- CTA net excess returns
insignificantly different from zero over 1994-2012 against 6.1% gross, with fee
income around 4% of assets -- was applied as though it transferred to an 0.66-0.98%
ETF. It does not transfer, and this module measures each fund's actual fee from its
own SEC-filed prospectus instead of assuming one.

Exposure delivery versus alpha
------------------------------
**Exposure delivery is answerable on this window. Alpha is not.** Exposure delivery
is a loading and a difference of means against a named benchmark, and 45 to 78
months can measure it. Alpha is a small residual mean, and the minimum detectable
alpha at 80% power over a window this short is larger than any plausible true value.
Every intercept here is shrunk by the fund's own factor computed from its own
standard error, printed beside its raw value and its detection threshold, and never
quoted alone. The distinction is restated at every point a number is produced,
because collapsing it is the specific error this experiment exists to correct.

Run it::

    uv run python -m portfolio_edge.experiments.exp_008_managed_futures --build-universe
    uv run python -m portfolio_edge.experiments.exp_008_managed_futures --view-results
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.data import aqr, fred, nport
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.exp_002_fund_exposure import (
    FACTOR_SPECIFICATIONS,
    ExposureFit,
    FundSeries,
    fetch_fund_series,
    fit_exposure,
    inflated_family,
    load_factor_panel,
    minimum_detectable_alpha,
)
from portfolio_edge.experiments.exp_002_universe import resolve_ticker, workspace_root
from portfolio_edge.experiments.exp_004_trend_marginal_value import (
    certainty_equivalent_annual,
    ewma_annualised_covariance,
    ewma_annualised_volatility,
    expanding_annualised_volatility,
)
from portfolio_edge.experiments.exp_008_universe import (
    ProductTaxFacts,
    ScreenedProduct,
    build_universe,
    load_product_facts,
    load_universe,
    universe_manifests,
    universe_path,
    write_universe,
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
    Specification,
    load_specification,
    plain_json,
)
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "MONTHS_PER_YEAR",
    "SPECIFICATION_NAMES",
    "ClauseDReading",
    "ManagedFuturesError",
    "ProductOutcome",
    "TrackingFit",
    "build_registry",
    "clause_d_readings",
    "default_specification_path",
    "effective_independent_blocks",
    "main",
    "run",
    "tracking_difference",
]

ENTRY_POINT: Final = "exp_008_managed_futures_products"

MONTHS_PER_YEAR: Final = 12
TRADING_DAYS_PER_MONTH: Final = 21.0

#: The three attribution specifications every usable fund is estimated under. The
#: multiple-testing family is every fund times every one of these, never the one
#: that happens to be reported.
SPECIFICATION_NAMES: Final = ("aqr_tsmom_tracking", "static_exposure_set", "ff5_umd")

#: Experiment 004's decisive design, unchanged, in the order it prints.
STATIC_SET_NAMES: Final = (
    "market_excess_return",
    "volatility_scaled_market_excess_return",
    "absolute_market_excess_return",
    "lagged_market_excess_return",
)

FloatArray = NDArray[np.float64]


class ManagedFuturesError(RuntimeError):
    """The audit could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ManagedFuturesError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise ManagedFuturesError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise ManagedFuturesError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ManagedFuturesError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def intended_exposure_map(specification: Specification) -> dict[str, str]:
    """The frozen mandate-to-benchmark map, as a plain mapping."""
    universe = _mapping(specification.universe, where="universe")
    block = _mapping(_at(universe, "intended_exposure_map", where="universe"), where="universe")
    mapping = _mapping(_at(block, "mapping", where="intended_exposure_map"), where="mapping")
    out: dict[str, str] = {}
    for mandate, entry in mapping.items():
        record = _mapping(entry, where=f"mapping.{mandate}")
        out[str(mandate)] = _text(record, "target", where=f"mapping.{mandate}")
    return out


# --------------------------------------------------------------------------- #
# Statistics this experiment adds, each with its own unit test
# --------------------------------------------------------------------------- #


def tracking_difference(fund_excess: FloatArray, benchmark: FloatArray) -> tuple[float, float]:
    """Annualised mean difference and tracking error, in percentage points a year.

    The difference of means is annualised by ``x12`` because it is a repeated mean,
    and the dispersion by ``xsqrt(12)`` because it is a sum of shocks. Getting those
    two the same way round is the whole arithmetic content of this function, and it
    is the reason it exists as a named thing with a fixture rather than as two lines
    inside a loop.

    This is the RAW difference. It does not adjust for the fund holding less of the
    benchmark's exposure than one unit, which is why the beta-adjusted intercept is
    always reported beside it: a fund that delivers 0.6 of the exposure and a fund
    that delivers 1.0 of it and loses 3% a year are different products with the same
    raw tracking difference.
    """
    left = np.asarray(fund_excess, dtype=np.float64)
    right = np.asarray(benchmark, dtype=np.float64)
    if left.shape != right.shape or left.ndim != 1:
        raise ValueError("fund_excess and benchmark must be one-dimensional and the same length")
    if left.size < 2:
        raise ValueError("a tracking difference needs at least two observations")
    difference = left - right
    return (
        float(np.mean(difference)) * MONTHS_PER_YEAR * 100.0,
        float(np.std(difference, ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
    )


def effective_independent_blocks(n_observations: int, mean_block_months: float) -> float:
    """Observations divided by the mean block length.

    A crude but honest count. Printed beside every fund figure because "54 months"
    sounds like evidence and "9 effective blocks" does not, and the second is closer
    to what a serially dependent monthly series supplies.
    """
    if n_observations < 0:
        raise ValueError("n_observations cannot be negative")
    if mean_block_months <= 0.0:
        raise ValueError("mean_block_months must be positive")
    return n_observations / mean_block_months


@dataclass(frozen=True, slots=True, kw_only=True)
class ClauseDReading:
    """One reading of Experiment 004's falsifier clause (d), and its verdict."""

    name: str
    clause_text: str
    quantity_name: str
    quantity: float
    threshold: float
    fires: bool
    verdict: str
    reasoning: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "reading": self.name,
            "clause_as_read": self.clause_text,
            "deciding_quantity": self.quantity_name,
            "value_percentage_points_per_year": self.quantity,
            "threshold_percentage_points_per_year": self.threshold,
            "clause_fires": self.fires,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
        }


def clause_d_readings(
    *,
    sleeve_marginal: float,
    replica_marginal: float,
    materiality: float,
) -> tuple[ClauseDReading, ClauseDReading]:
    """Both readings of Experiment 004's clause (d), computed side by side.

    The frozen clause reads: *"an attribution on static asset exposures plus a
    volatility-scaled market position leaves a marginal benefit below the materiality
    threshold, i.e. a simpler static exposure explains it."*

    The sentence does not say **whose** marginal benefit.

    * **Absolute**: the replica's own marginal benefit is at or above the threshold,
      so a simpler exposure reproduces a material amount, so reject. This is what
      Experiment 004 implemented.
    * **Relative**: what the attribution *leaves* is the sleeve's benefit **less**
      the replica's. If that residue clears the threshold, the exposures have not
      explained the result and the clause does not fire.

    Both are computed from the same two numbers. Neither is inferred from the other,
    and the function returns both rather than a preferred one, because a rule that
    only fires on the reading its author preferred after seeing the answer is not a
    rule.
    """
    if materiality <= 0.0:
        raise ValueError(f"materiality must be positive, got {materiality}")
    margin = sleeve_marginal - replica_marginal
    absolute = ClauseDReading(
        name="absolute",
        clause_text=(
            "the REPLICA's own marginal benefit is at or above the materiality "
            "threshold, so a simpler static exposure reproduces a material amount"
        ),
        quantity_name="replica marginal certainty equivalent",
        quantity=replica_marginal,
        threshold=materiality,
        fires=replica_marginal >= materiality,
        verdict="rejected" if replica_marginal >= materiality else "not-rejected",
        reasoning=(
            f"the replica delivers {replica_marginal:+.3f} pp/yr against a "
            f"{materiality:.2f} pp/yr threshold"
        ),
    )
    relative = ClauseDReading(
        name="relative",
        clause_text=(
            "what the attribution LEAVES -- the sleeve's marginal benefit less the "
            "replica's -- is below the materiality threshold"
        ),
        quantity_name="sleeve's margin over its own replica",
        quantity=margin,
        threshold=materiality,
        fires=margin < materiality,
        verdict="rejected" if margin < materiality else "not-rejected",
        reasoning=(
            f"the sleeve delivers {sleeve_marginal:+.3f} pp/yr and the replica "
            f"{replica_marginal:+.3f}, leaving {margin:+.3f} pp/yr against a "
            f"{materiality:.2f} pp/yr threshold"
        ),
    )
    return absolute, relative


def clause_d_monotonicity(
    *, replica_share: float, materiality: float, scales: Sequence[float]
) -> list[dict[str, JsonValue]]:
    """How each reading behaves as the effect grows at a FIXED explained share.

    This is the argument for the relative reading, made computable. Hold the share
    of the sleeve that the replica reproduces constant and scale both numbers up.
    The share explained has not changed, so a clause about *explanation* should not
    change either.

    * The **absolute** reading goes from not-firing to firing: a bigger sleeve
      mechanically enlarges the fitted replica that reproduces part of it, so the
      bar gets EASIER to clear as the effect gets better. That is the wrong
      monotonicity for a falsifier.
    * The **relative** reading goes from firing to not-firing, which is the right
      direction: a result whose unexplained residue is large has not been explained.

    NEITHER reading is literally scale-free, because both compare a level in
    percentage points against an absolute bar. A clause that was actually
    scale-free would have named a SHARE -- "the replica reproduces more than 60% of
    the benefit" -- and that is the specification lesson, not a third reading to
    apply retrospectively.
    """
    if not 0.0 <= replica_share <= 1.0:
        raise ValueError(f"replica_share must lie in [0, 1], got {replica_share}")
    rows: list[dict[str, JsonValue]] = []
    for scale in scales:
        absolute, relative = clause_d_readings(
            sleeve_marginal=scale,
            replica_marginal=scale * replica_share,
            materiality=materiality,
        )
        rows.append(
            {
                "sleeve_marginal": scale,
                "replica_marginal": scale * replica_share,
                "share_explained": replica_share,
                "absolute_reading_fires": absolute.fires,
                "relative_reading_fires": relative.fires,
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class BenchmarkPanel:
    """The AQR trend index and the cash rate, on the factor panel's month grid."""

    periods: tuple[str, ...]
    tsmom: FloatArray
    cash: FloatArray
    provenance: Mapping[str, JsonValue]


def load_benchmark_panel(
    specification: Specification, periods: Sequence[str]
) -> BenchmarkPanel:
    """Load the pinned AQR TSMOM series and the FRED cash rate onto ``periods``.

    A raw-hash mismatch on AQR **aborts**. The vendor reconstructs its whole history
    on every update, so an unrecognised hash is a new vintage rather than a corrupted
    download, and a tracking difference computed against an unrecognised file looks
    exactly like a good one.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "aqr_source_pin", where="parameters"), where="aqr_source_pin")
    cache = RawCache()
    dataset = aqr.get_dataset(_text(pin, "dataset_id", where="aqr_source_pin"))
    entry = aqr.download(cache, dataset)
    expected = _text(pin, "expected_sha256_raw", where="aqr_source_pin")
    if entry.sha256 != expected:
        raise ManagedFuturesError(
            f"the AQR workbook at {dataset.url} now hashes to {entry.sha256}, but this "
            f"specification is frozen against {expected}. AQR reconstructs the full "
            "history each time the returns are updated, so this is a new vintage, not "
            "a corrupted download. Freeze a new specification against it rather than "
            "reporting a tracking difference against an unrecognised file."
        )
    parsed = aqr.parse(cache, entry, dataset=dataset)
    sheet = _text(pin, "sheet", where="aqr_source_pin")
    if parsed.data_sheet != sheet:
        raise ManagedFuturesError(
            f"the specification pins sheet {sheet!r} but the parser read {parsed.data_sheet!r}"
        )
    report = validate_table(
        parsed.table,
        dataset_id="aqr_tsmom_factors_monthly",
        expected_columns=dataset.expected_columns,
        expected_frequency="monthly",
    )
    if not report.ok:
        raise ManagedFuturesError(
            "the AQR table failed validation before any statistic was computed: "
            + "; ".join(report.summary())
        )
    column = _text(pin, "column", where="aqr_source_pin")
    available = {
        str(period)[:7]: value
        for period, value in zip(parsed.table.periods, parsed.table.column(column), strict=True)
        if value is not None
    }
    missing = [period for period in periods if period not in available]
    if missing:
        raise ManagedFuturesError(
            f"the AQR series is missing {len(missing)} month(s) of the window, first "
            f"{missing[0]}. Nothing is forward-filled: a hole patched silently is a "
            "hole that reappears as an unexplained number."
        )

    cash_entry = fred.download(cache, "TB3MS")
    cash_table = fred.parse(cache, cash_entry, "TB3MS")
    if cash_table.units != "decimal_per_year":
        raise ManagedFuturesError(
            f"FRED TB3MS parsed to units {cash_table.units!r}, not 'decimal_per_year'; "
            "refusing to divide a series whose units have changed"
        )
    monthly: dict[str, float] = {}
    for label, row in zip(cash_table.periods, cash_table.values, strict=True):
        if row[0] is not None:
            monthly[str(label)[:7]] = float(row[0]) / MONTHS_PER_YEAR
    cash_missing = [period for period in periods if period not in monthly]
    if cash_missing:
        raise ManagedFuturesError(
            f"FRED TB3MS is missing {len(cash_missing)} month(s) of the window, first "
            f"{cash_missing[0]}"
        )

    return BenchmarkPanel(
        periods=tuple(periods),
        tsmom=np.asarray([available[period] for period in periods], dtype=np.float64),
        cash=np.asarray([monthly[period] for period in periods], dtype=np.float64),
        provenance={
            "aqr": {
                "dataset_id": dataset.dataset_id,
                "source_url": entry.url,
                "workbook_sheet": parsed.data_sheet,
                "column": column,
                "sha256_raw": entry.sha256,
                "sha256_normalized": parsed.table.sha256_normalized(),
                "retrieved_utc": entry.retrieved_utc,
                "source_last_modified": entry.last_modified,
                "parser_version": aqr.PARSER_VERSION,
                "first_observation": parsed.table.first_observation,
                "last_observation": parsed.table.last_observation,
                "series_kind": "vendor excess return, GROSS of the vendor's own costs by omission",
                "committed_manifest_sha256": _manifest_hash(pin),
                "warning": (
                    "This is the SAME vendor series Experiment 004 evaluated, chosen so "
                    "the two experiments are commensurable. It is maintained by a firm "
                    "that sells the strategy, its cost basis is UNESTABLISHED, and it is "
                    "therefore a HARD benchmark for a fund that charges a real fee. That "
                    "direction is the conservative one for a tracking test."
                ),
            },
            "fred_tb3ms": {
                "source_url": cash_entry.url,
                "sha256_raw": cash_entry.sha256,
                "retrieved_utc": cash_entry.retrieved_utc,
                "parser_version": fred.PARSER_VERSION,
                "units": cash_table.units,
            },
        },
    )


def _manifest_hash(pin: Mapping[str, JsonValue]) -> str | None:
    location = pin.get("committed_manifest")
    if not isinstance(location, str):
        return None
    path = workspace_root() / location
    return read_manifest(path).sha256_manifest() if path.is_file() else None


def fetch_reinvestment(
    cache: RawCache, *, series_id: str, start: str, end: str
) -> dict[str, JsonValue]:
    """Reinvested distributions as a fraction of net assets, month by month.

    A **LOWER BOUND** on distributions and not a tax figure. A shareholder who takes
    a distribution in cash contributes nothing to ``reinvestment``, and Form N-PORT
    carries no split between ordinary income, short-term gain and long-term gain --
    which is exactly the split that decides the tax bill on a managed-futures fund
    whose commodity exposure runs through a Cayman subsidiary. The prospectus
    after-tax table in the committed product facts is the measure that can speak to
    tax; this one speaks only to whether distributions happened and roughly how big
    they were.
    """
    refs = [
        ref
        for ref in nport.filing_index(cache, series_id)
        if ref.form_type.startswith("NPORT-P")
    ]
    filings = [nport.fetch_filing(cache, ref) for ref in refs]
    flows = nport.build_flow_table(filings)
    assets = {
        period: filing.net_assets
        for filing in filings
        for period in nport.months_covered(filing.report_period_end)
        if filing.net_assets
    }
    rows: list[dict[str, JsonValue]] = []
    for period in sorted(flows):
        if not start <= period <= end:
            continue
        flow = flows[period]
        base = assets.get(period)
        rows.append(
            {
                "period": period,
                "reinvestment_usd": flow.reinvestment,
                "net_assets_usd": base,
                "reinvestment_fraction_of_net_assets": (
                    None
                    if flow.reinvestment is None or not base
                    else flow.reinvestment / base
                ),
            }
        )
    fractions = [
        float(str(row["reinvestment_fraction_of_net_assets"]))
        for row in rows
        if row["reinvestment_fraction_of_net_assets"] is not None
    ]
    months_with_reinvestment = sum(1 for value in fractions if value > 0.0)
    total = float(np.sum(fractions)) if fractions else 0.0
    years = len(fractions) / MONTHS_PER_YEAR if fractions else 0.0
    return {
        "months_observed": len(rows),
        "months_with_a_reinvested_distribution": months_with_reinvestment,
        "reinvested_percent_of_net_assets_per_year": (
            100.0 * total / years if years > 0.0 else None
        ),
        "largest_single_month_percent_of_net_assets": (
            100.0 * max(fractions) if fractions else None
        ),
        "is_a_lower_bound": True,
        "why": (
            "Form N-PORT Item B.6 reports the dollar value of distributions REINVESTED "
            "in shares. A distribution taken in cash never appears in it, and the form "
            "carries no split between ordinary income, short-term gain and long-term "
            "gain. This figure is therefore a lower bound on distributions and says "
            "nothing at all about their tax character."
        ),
        "monthly": rows,
    }


# --------------------------------------------------------------------------- #
# Fits
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class TrackingFit:
    """One fund against the AQR trend index: exposure delivered, and at what cost."""

    ticker: str
    n_observations: int
    first_period: str
    last_period: str
    loading: float
    loading_se: float
    loading_t: float
    loading_interval: tuple[float, float]
    loading_intervals_by_block: Mapping[str, tuple[float, float]]
    alpha_annual_percent: float
    alpha_se_annual_percent: float
    alpha_p: float
    shrunk_alpha_annual_percent: float
    shrinkage_factor: float
    minimum_detectable_alpha_percent: float
    r_squared: float
    correlation: float
    raw_tracking_difference_percent: float
    tracking_error_percent: float
    first_half_loading: float
    second_half_loading: float
    rolling_minimum: float
    rolling_maximum: float
    rolling_sign_changes: int
    rolling_windows: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "n_observations": self.n_observations,
            "window": f"{self.first_period}..{self.last_period}",
            "aqr_tsmom_loading": self.loading,
            "loading_hac_se": self.loading_se,
            "loading_hac_t": self.loading_t,
            "loading_95_interval": list(self.loading_interval),
            "loading_intervals_by_block": {
                name: list(value) for name, value in self.loading_intervals_by_block.items()
            },
            "beta_adjusted_alpha_annual_percent": self.alpha_annual_percent,
            "alpha_se_annual_percent": self.alpha_se_annual_percent,
            "alpha_p": self.alpha_p,
            "shrunk_alpha_annual_percent": self.shrunk_alpha_annual_percent,
            "shrinkage_factor": self.shrinkage_factor,
            "minimum_detectable_alpha_percent": self.minimum_detectable_alpha_percent,
            "r_squared": self.r_squared,
            "correlation_with_aqr_tsmom": self.correlation,
            "raw_tracking_difference_annual_percent": self.raw_tracking_difference_percent,
            "tracking_error_annual_percent": self.tracking_error_percent,
            "loading_first_half": self.first_half_loading,
            "loading_second_half": self.second_half_loading,
            "rolling_loading_minimum": self.rolling_minimum,
            "rolling_loading_maximum": self.rolling_maximum,
            "rolling_sign_changes": self.rolling_sign_changes,
            "rolling_windows": self.rolling_windows,
        }


@dataclass(slots=True, kw_only=True)
class ProductOutcome:
    """The per-fund verdict, with every falsifier clause that fired."""

    ticker: str
    series_name: str
    status: str
    clauses_fired: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "series_name": self.series_name,
            "status": self.status,
            "falsifier_clauses_fired": list(self.clauses_fired),
            "notes": list(self.notes),
        }


def _rows_for(periods: Sequence[str], wanted: Sequence[str]) -> NDArray[np.intp]:
    index = {period: position for position, period in enumerate(periods)}
    return np.asarray([index[period] for period in wanted], dtype=np.intp)


def _static_design(
    market_excess: FloatArray, scaled_market_excess: FloatArray
) -> FloatArray:
    """Experiment 004's decisive design, minus its constant, one row shorter.

    The first observation is consumed by the lag, exactly as in Experiment 004, so
    the two experiments' static-set coefficients mean the same thing.
    """
    return np.column_stack(
        [
            market_excess[1:],
            scaled_market_excess[1:],
            np.abs(market_excess[1:]),
            market_excess[:-1],
        ]
    )


def _bootstrap_loading_intervals(
    *,
    response: FloatArray,
    design: FloatArray,
    column: int,
    rng: np.random.Generator,
    resamples: int,
    confidence: float,
    blocks: Sequence[float],
) -> dict[str, tuple[float, float]]:
    """Stationary block-bootstrap intervals on one coefficient.

    Rows are resampled JOINTLY across the response and the whole design, so the
    dependence between regressors and errors that HAC exists for survives inside each
    resample. Resampling residuals alone would assume the very independence the block
    length is there to avoid assuming.
    """
    lower_q = 100.0 * (1.0 - confidence) / 2.0
    upper_q = 100.0 - lower_q
    out: dict[str, tuple[float, float]] = {}
    ridge = 1e-12 * np.eye(design.shape[1])
    for block in blocks:
        indices = stationary_bootstrap_indices(response.size, block, resamples, rng)
        y_batch = response[indices]
        x_batch = design[indices]
        xtx = np.einsum("btk,btl->bkl", x_batch, x_batch)
        xty = np.einsum("btk,bt->bk", x_batch, y_batch)
        solved = np.linalg.solve(xtx + ridge, xty[:, :, None])[:, column, 0]
        out[f"block_{int(block)}"] = (
            float(np.percentile(solved, lower_q)),
            float(np.percentile(solved, upper_q)),
        )
    return out


def _fit_tracking(
    *,
    ticker: str,
    periods: Sequence[str],
    fund_excess: FloatArray,
    tsmom: FloatArray,
    hac_lags: int,
    dispersion: float,
    power: float,
    rng: np.random.Generator,
    resamples: int,
    confidence: float,
    blocks: Sequence[float],
    primary_block: float,
    halves: Mapping[str, tuple[str, str]],
    rolling_window: int,
) -> TrackingFit:
    """Regress one fund's excess return on the AQR trend index."""
    fit = hac_ols(fund_excess, tsmom[:, None], n_lags=hac_lags, add_constant=True)
    alpha_annual = float(fit.coefficients[0]) * MONTHS_PER_YEAR * 100.0
    alpha_se_annual = float(fit.standard_errors[0]) * MONTHS_PER_YEAR * 100.0
    prior = dispersion**2
    shrinkage = prior / (prior + alpha_se_annual**2)
    total = float(np.sum((fund_excess - fund_excess.mean()) ** 2))
    r_squared = 1.0 - float(np.sum(fit.residuals**2)) / total if total > 0.0 else float("nan")

    design = np.column_stack([np.ones(fund_excess.size), tsmom])
    intervals = _bootstrap_loading_intervals(
        response=fund_excess,
        design=design,
        column=1,
        rng=rng,
        resamples=resamples,
        confidence=confidence,
        blocks=blocks,
        )
    difference, error = tracking_difference(fund_excess, tsmom)

    half_loadings: dict[str, float] = {}
    for name, (start, end) in halves.items():
        mask = np.asarray(
            [month_index(start) <= month_index(period) <= month_index(end) for period in periods],
            dtype=bool,
        )
        # Four observations is the least an OLS slope with a constant can be
        # estimated from without the estimate being an artefact of the fit; a half a
        # fund does not cover is reported as NaN, never extrapolated.
        if int(np.count_nonzero(mask)) < 4:
            half_loadings[name] = float("nan")
            continue
        half = hac_ols(
            fund_excess[mask], tsmom[mask][:, None], n_lags=1, add_constant=True
        )
        half_loadings[name] = float(half.coefficients[1])

    rolling: list[float] = []
    if fund_excess.size >= rolling_window:
        for stop in range(rolling_window, fund_excess.size + 1):
            window = slice(stop - rolling_window, stop)
            beta, *_ = np.linalg.lstsq(design[window], fund_excess[window], rcond=None)
            rolling.append(float(beta[1]))

    return TrackingFit(
        ticker=ticker,
        n_observations=int(fit.n_observations),
        first_period=periods[0],
        last_period=periods[-1],
        loading=float(fit.coefficients[1]),
        loading_se=float(fit.standard_errors[1]),
        loading_t=float(fit.t_statistics[1]),
        loading_interval=intervals[f"block_{int(primary_block)}"],
        loading_intervals_by_block=intervals,
        alpha_annual_percent=alpha_annual,
        alpha_se_annual_percent=alpha_se_annual,
        alpha_p=float(fit.p_values[0]),
        shrunk_alpha_annual_percent=shrinkage * alpha_annual,
        shrinkage_factor=shrinkage,
        minimum_detectable_alpha_percent=minimum_detectable_alpha(alpha_se_annual, power=power),
        r_squared=r_squared,
        correlation=float(np.corrcoef(fund_excess, tsmom)[0, 1]),
        raw_tracking_difference_percent=difference,
        tracking_error_percent=error,
        first_half_loading=half_loadings.get("first_half", float("nan")),
        second_half_loading=half_loadings.get("second_half", float("nan")),
        rolling_minimum=min(rolling) if rolling else float("nan"),
        rolling_maximum=max(rolling) if rolling else float("nan"),
        rolling_sign_changes=sum(
            1 for i in range(1, len(rolling)) if rolling[i] * rolling[i - 1] < 0.0
        ),
        rolling_windows=len(rolling),
    )


def _fit_static_set(
    *,
    ticker: str,
    fund_excess: FloatArray,
    market_excess: FloatArray,
    scaled_market_excess: FloatArray,
    hac_lags: int,
    dispersion: float,
    power: float,
) -> ExposureFit:
    """Experiment 004's decisive static-exposure attribution, on one series."""
    return fit_exposure(
        ticker=ticker,
        specification="static_exposure_set",
        era="common_period",
        excess_returns=fund_excess[1:],
        design=_static_design(market_excess, scaled_market_excess),
        factor_names=STATIC_SET_NAMES,
        n_lags=hac_lags,
        dispersion_annual_percent=dispersion,
        power=power,
    )


# --------------------------------------------------------------------------- #
# The marginal-contribution arm: Experiment 004's five-way structure
# --------------------------------------------------------------------------- #


def _marginal_certainty_equivalent(
    *,
    sleeve_excess: FloatArray,
    equity_total: FloatArray,
    cash: FloatArray,
    gamma: float,
    sleeve_weight: float,
    equity_weight: float,
    centre_of_mass_months: float,
    reported_from: int = 0,
) -> dict[str, JsonValue]:
    """Experiment 004's construction, on a whole number of calendar years.

    The treatment is the passive benchmark with a ``sleeve_weight`` sleeve funded pro
    rata from both legs; the comparator is the same benchmark levered to a MATCHED
    ex-ante risk budget with cash, computed from lagged volatilities and a lagged
    covariance only. The comparator is the whole point: measuring the sleeve against
    the fully invested benchmark would credit it with de-risking.

    **The risk match only exists once the estimator is warm, and that is the weak
    joint here.** Experiment 004 had sixty months of burn-in before its reported
    window; a fund with four years of filings has whatever its own history supplies.
    So the arrays passed in cover the fund's WHOLE filed history and the certainty
    equivalent is computed only on ``[reported_from:]``, which must be a whole number
    of calendar years. The count of months inside that span in which the volatility
    estimator was still unwarmed -- and in which the comparator is therefore NOT
    risk-matched -- is returned with the value, because an unmatched comparator makes
    the number an artefact rather than a comparison.

    At six years or fewer this is a description, not an inference, and it is labelled
    as one wherever it is printed.
    """
    n = sleeve_excess.size
    passive = equity_weight * equity_total + (1.0 - equity_weight) * cash
    sleeve_total = sleeve_excess + cash
    passive_volatility = ewma_annualised_volatility(
        passive, centre_of_mass_months=centre_of_mass_months, minimum_observations=12
    )
    sleeve_volatility = ewma_annualised_volatility(
        sleeve_total, centre_of_mass_months=centre_of_mass_months, minimum_observations=12
    )
    covariance = ewma_annualised_covariance(
        passive, sleeve_total, centre_of_mass_months=centre_of_mass_months,
        minimum_observations=12,
    )
    combined_variance = (
        (1.0 - sleeve_weight) ** 2 * passive_volatility**2
        + sleeve_weight**2 * sleeve_volatility**2
        + 2.0 * sleeve_weight * (1.0 - sleeve_weight) * covariance
    )
    combined_volatility = np.sqrt(np.maximum(combined_variance, 0.0))
    unwarmed = np.isnan(passive_volatility) | np.isnan(combined_volatility)
    with np.errstate(divide="ignore", invalid="ignore"):
        matched = np.nan_to_num(combined_volatility / passive_volatility, nan=1.0)

    treatment = (
        (1.0 - sleeve_weight) * passive + sleeve_weight * sleeve_total
    )
    equity_leg = equity_weight * matched
    comparator = equity_leg * equity_total + (1.0 - equity_leg) * cash

    reported = max(0, min(reported_from, n))
    span = n - reported
    years = span // MONTHS_PER_YEAR
    if years < 2:
        return {
            "available": False,
            "reason": (
                f"{span} reportable month(s) is fewer than two whole calendar years, "
                "and a certainty equivalent computed from one annual observation is "
                "that observation"
            ),
        }
    usable = years * MONTHS_PER_YEAR
    window = slice(n - usable, n)
    left = np.prod(1.0 + treatment[window].reshape(years, MONTHS_PER_YEAR), axis=1)
    right = np.prod(1.0 + comparator[window].reshape(years, MONTHS_PER_YEAR), axis=1)
    marginal = 100.0 * (
        certainty_equivalent_annual(left, gamma=gamma)
        - certainty_equivalent_annual(right, gamma=gamma)
    )
    unwarmed_months = int(np.count_nonzero(unwarmed[window]))
    return {
        "available": True,
        "whole_calendar_years": years,
        "marginal_certainty_equivalent_percentage_points_per_year": marginal,
        "treatment": f"{equity_weight:.0%}/{1 - equity_weight:.0%} equity/cash with a "
        f"{sleeve_weight:.0%} sleeve funded pro rata",
        "comparator": "the same benchmark at a MATCHED ex-ante risk budget, funded with cash",
        "mean_comparator_exposure": float(np.mean(matched[window])),
        "estimator_warm_up_months_available": reported,
        "months_in_the_window_with_an_unwarmed_estimator": unwarmed_months,
        "risk_match_holds": unwarmed_months == 0,
        "unwarmed_warning": (
            ""
            if unwarmed_months == 0
            else (
                f"{unwarmed_months} of {usable} reported months fall before the "
                "volatility estimator has enough observations, so the comparator runs "
                "at full exposure in them and is NOT risk-matched. The figure is an "
                "artefact to that extent. Experiment 004 had sixty months of burn-in; "
                "a fund with this much filed history does not."
            )
        ),
        "uncertainty": (
            "NONE REPORTED, deliberately. A certainty equivalent on "
            f"{years} annual observations has no interval worth printing; a bootstrap "
            "of it would imply a precision the sample does not have. This is a "
            "DESCRIPTION of the window, not an inference about the fund."
        ),
    }


# --------------------------------------------------------------------------- #
# Part B: Experiment 004's clause (d), re-run under both readings
# --------------------------------------------------------------------------- #


def _clause_d_block(specification: Specification) -> dict[str, JsonValue]:
    """Re-run Experiment 004's decision. No data of Experiment 004's is recomputed.

    The three deciding quantities are quoted in this experiment's frozen
    specification so that the decision is reproducible from Git alone -- artifacts
    are not in Git. When Experiment 004's artifact is present it is read and the
    quoted values are VERIFIED against it; a mismatch beyond the frozen tolerance
    aborts, because a decision re-run against numbers that have drifted is not a
    re-run of that decision.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(_at(parameters, "clause_d_rerun", where="parameters"), where="clause_d_rerun")
    where = "clause_d_rerun"
    sleeve = _number(block, "expected_sleeve_marginal_percentage_points_per_year", where=where)
    replica = _number(block, "expected_replica_marginal_percentage_points_per_year", where=where)
    residual = _number(block, "expected_residual_marginal_percentage_points_per_year", where=where)
    materiality = _number(block, "materiality_threshold_annual_percent", where=where)
    tolerance = _number(block, "verification_tolerance", where=where)
    artifact = workspace_root() / _text(block, "source_artifact", where=where)

    verification: dict[str, JsonValue] = {"artifact": str(artifact), "present": artifact.is_file()}
    if artifact.is_file():
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        diagnostics = payload["result"]["diagnostics"]
        found_replica = float(
            diagnostics["hostile_tests"]["static_and_volatility_exposure_replica"][
                "replica_marginal_percentage_points_per_year"
            ]
        )
        found_residual = float(
            diagnostics["hostile_tests"]["static_and_volatility_exposure_replica"][
                "residual_only_marginal_percentage_points_per_year"
            ]
        )
        primary = next(
            row
            for row in diagnostics["marginal_results"]
            if row["treatment_portfolio"] == "passive_plus_trend"
            and row["window"] == "full_period"
        )
        found_sleeve = float(primary["marginal_percentage_points_per_year"])
        drift = {
            "sleeve": abs(found_sleeve - sleeve),
            "replica": abs(found_replica - replica),
            "residual": abs(found_residual - residual),
        }
        if max(drift.values()) > tolerance:
            raise ManagedFuturesError(
                "Experiment 004's ledgered artifact disagrees with the values frozen "
                f"in this specification by {max(drift.values()):.9f}, above the "
                f"{tolerance:g} tolerance: {drift}. That is a finding about which run "
                "produced which number, not a value to update silently."
            )
        verification.update(
            {
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "run_id": str(payload.get("run_id", "")),
                "spec_hash": str(payload.get("spec_hash", "")),
                "verified": True,
                "maximum_absolute_drift": max(drift.values()),
                "sleeve_from_artifact": found_sleeve,
                "replica_from_artifact": found_replica,
                "residual_from_artifact": found_residual,
            }
        )
    else:
        verification["verified"] = False
        verification["note"] = (
            "Experiment 004's artifact is absent from this working tree, which is "
            "normal: artifacts are not in Git. The frozen quoted values are used and "
            "the run is reproducible from Git alone; re-run Experiment 004 to restore "
            "the verification."
        )

    absolute, relative = clause_d_readings(
        sleeve_marginal=sleeve, replica_marginal=replica, materiality=materiality
    )
    return {
        "what_this_is": (
            "A re-run of Experiment 004's DECISION, not of its data. Experiment 004's "
            "frozen specification, its ledger entries and its recorded `rejected` "
            "status are untouched and stand as recorded. This is a second, "
            "differently-specified look at the same clause, and the ledger shows both."
        ),
        "source": {
            "run_id": block.get("source_run_id"),
            "spec_hash": block.get("source_spec_hash"),
            "verification": verification,
        },
        "clause_as_frozen": (
            "(d) an attribution on static asset exposures plus a volatility-scaled "
            "market position leaves a marginal benefit below the materiality "
            "threshold, i.e. a simpler static exposure explains it"
        ),
        "the_ambiguity": (
            "The sentence does not say WHOSE marginal benefit. Under the ABSOLUTE "
            "reading the deciding quantity is the replica's own marginal benefit; "
            "under the RELATIVE reading it is what the attribution LEAVES, the "
            "sleeve's benefit less the replica's. Both are computed from the same two "
            "numbers and both are reported."
        ),
        "inputs_percentage_points_per_year": {
            "sleeve_marginal": sleeve,
            "replica_marginal": replica,
            "residual_only_marginal": residual,
            "sleeve_margin_over_replica": sleeve - replica,
            "replica_share_of_sleeve": replica / sleeve if sleeve else None,
            "materiality_threshold": materiality,
        },
        "readings": [absolute.to_json(), relative.to_json()],
        "verdicts_differ": absolute.verdict != relative.verdict,
        "experiment_004_applied": "absolute",
        "third_reading_considered_and_rejected": (
            "A reading in which the RESIDUAL after the attribution must clear the "
            f"threshold is degenerate: the residual delivers {residual:+.3f} pp/yr and "
            "an OLS residual is mean-zero by construction, so that reading fires "
            "whatever the data say. It is recorded as considered, not applied."
        ),
        "judgement": (
            "The RELATIVE reading is better justified, on what the clause was for "
            "rather than on which answer it gives. Clause (d) was frozen to catch the "
            "Goyal-Jegadeesh (2018) failure mode: that time-series momentum is a "
            "time-varying market position wearing a forecasting costume. The claim "
            "that failure mode makes is that the exposures EXPLAIN the result -- and "
            "'explains' is inherently a share, not a level. The absolute reading has a "
            "property no falsifier should have: its bar gets EASIER to clear as the "
            "sleeve gets better, because a larger sleeve benefit mechanically enlarges "
            "the fitted replica that reproduces part of it. Taken to its limit, a "
            "sleeve delivering 100 pp/yr with a replica delivering 0.31 would be "
            "rejected for being 0.3% explained. That is not a rule anyone would have "
            "written down knowing what it did. The relative reading has the opposite "
            "and correct monotonicity: it asks how much of the result SURVIVES the "
            "explanation, so a larger unexplained residue is harder to reject, which "
            "is what a falsifier should do. NEITHER reading is literally scale-free -- "
            "both compare a level in percentage points against an absolute bar -- and "
            "that is the deeper defect: a clause about explanation should have named a "
            "SHARE."
        ),
        "monotonicity_demonstration": clause_d_monotonicity(
            replica_share=replica / sleeve if sleeve else 0.0,
            materiality=materiality,
            scales=(0.5, 1.0, 1.341825315439782, 5.0, 50.0),
        ),
        "but_the_honest_answer": (
            "BOTH READINGS ARE DEFENSIBLE ON THE TEXT AS WRITTEN, and that is the "
            "finding. The clause named a threshold and a quantity that the sentence "
            "does not uniquely identify. Experiment 004 applied the absolute reading "
            "as frozen, disclosed the ambiguity in its own write-up, and reported the "
            "number the other reading needs -- which is the correct behaviour and the "
            "reason this re-run is possible at all. The defect is one of "
            "SPECIFICATION QUALITY, not of conduct: a falsifier must name its "
            "deciding quantity as an expression, not as a description in prose, and "
            "must be stated in units that do not move with the size of the effect."
        ),
        "what_this_changes_and_what_it_does_not": (
            "Under the relative reading Experiment 004's status becomes `unresolved` "
            "rather than `rejected`, which is exactly what its own write-up said it "
            "would. `unresolved` is not a promotion: the vendor's cost basis is still "
            "unestablished, the post-publication interval still contains zero and "
            "still fails Holm, the standalone Sharpe still fell 1.34 to 0.18, and the "
            "evidence class still caps the result at `exploratory`. Nothing about the "
            "trend sleeve becomes investable because a clause was read the other way."
        ),
    }


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_008_managed_futures_products.yaml"


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _era(specification: Specification, name: str) -> tuple[str, str]:
    for era in specification.sample_policy.eras:
        if era.name == name:
            return era.start, era.end
    raise ManagedFuturesError(f"the frozen sample policy declares no era named {name!r}")


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Audit the screened managed-futures shelf, and re-run clause (d)."""
    parameters = _mapping(specification.parameters, where="parameters")
    minimum_loading = _number(parameters, "minimum_intended_loading", where="parameters")
    stability_floor = _number(parameters, "loading_stability_floor", where="parameters")
    tolerance = _number(
        parameters, "tracking_difference_tolerance_annual_percent", where="parameters"
    )
    minimum_months = int(_number(parameters, "minimum_monthly_observations", where="parameters"))
    hac_lags = int(_number(parameters, "hac_lags", where="parameters"))
    power = _number(parameters, "power_target", where="parameters")
    rolling_window = int(_number(parameters, "rolling_window_months", where="parameters"))
    shrinkage_block = _mapping(
        _at(parameters, "alpha_shrinkage", where="parameters"), where="alpha_shrinkage"
    )
    dispersion = _number(shrinkage_block, "sigma_true_annual_percent", where="alpha_shrinkage")
    gamma = _number(parameters, "crra_gamma", where="parameters")
    sleeve_weight = _number(parameters, "sleeve_weight", where="parameters")
    equity_weight = _number(parameters, "equity_weight", where="parameters")
    lookback_days = _number(parameters, "volatility_lookback_days", where="parameters")
    centre_of_mass = lookback_days / TRADING_DAYS_PER_MONTH

    universe = load_universe()
    panel = load_factor_panel(specification)
    benchmark = load_benchmark_panel(specification, panel.periods)
    cache = RawCache()

    common_start, common_end = _era(specification, "common_period")
    halves = {
        "first_half": _era(specification, "first_half"),
        "second_half": _era(specification, "second_half"),
    }
    whole_start, whole_end = _era(specification, "whole_years")

    # --- the volatility-scaled market leg, built exactly as Experiment 004 does ---
    market_excess = panel.factors["Mkt-RF"]
    equity_total = market_excess + panel.risk_free
    market_volatility = ewma_annualised_volatility(
        market_excess, centre_of_mass_months=centre_of_mass, minimum_observations=12
    )
    market_target = expanding_annualised_volatility(market_excess, minimum_observations=12)
    with np.errstate(divide="ignore", invalid="ignore"):
        exposure = np.clip(market_target / market_volatility, 0.0, 1.5)
    scaled_market_excess = np.nan_to_num(exposure, nan=1.0) * market_excess

    # --- fetch every fund that PASSED the screen, plus the pedestal ------------
    comparator = "VTI"
    wanted: dict[str, tuple[str, str]] = {
        product.ticker: (product.series_id, product.class_id) for product in universe.passing
    }
    if comparator not in wanted:
        series_id, class_id, _name = resolve_ticker(cache, comparator)
        wanted[comparator] = (series_id, class_id)

    series: dict[str, FundSeries] = {}
    fetch_failures: list[dict[str, JsonValue]] = []
    for ticker, (series_id, class_id) in sorted(wanted.items()):
        try:
            series[ticker] = fetch_fund_series(
                cache,
                ticker=ticker,
                series_id=series_id,
                class_id=class_id,
                start=common_start,
                end=common_end,
            )
        except Exception as exc:
            fetch_failures.append(
                {"ticker": ticker, "series_id": series_id, "reason": f"{type(exc).__name__}: {exc}"}
            )

    coverage: list[dict[str, JsonValue]] = []
    usable: list[ScreenedProduct] = []
    for product in universe.passing:
        record = series.get(product.ticker)
        if record is None:
            coverage.append(
                {"ticker": product.ticker, "usable": False, "reason": "no filings retrieved"}
            )
            continue
        months = len(record.periods)
        enough = months >= minimum_months
        coverage.append(
            {
                "ticker": product.ticker,
                "usable": enough,
                "months_filed_in_window": months,
                "first_filed_month": record.periods[0] if record.periods else None,
                "last_filed_month": record.periods[-1] if record.periods else None,
                "months_missing_inside_the_filed_span": [
                    period
                    for period in record.missing_months
                    if record.periods and record.periods[0] <= period <= record.periods[-1]
                ],
                "filings": record.filing_count,
                "amendments": record.amendment_count,
                "filings_held_out_after_window": record.filings_held_out,
                "prospectus_inception": (
                    None if product.facts is None else product.facts.inception_date
                ),
                "reason": ""
                if enough
                else f"{months} filed months is below the frozen minimum of {minimum_months}",
            }
        )
        if enough:
            usable.append(product)

    # --- the three attributions, per fund -------------------------------------
    rng = context.rng
    resamples = specification.inference.resamples
    confidence = specification.inference.confidence_level
    tracking: dict[str, TrackingFit] = {}
    exposure_fits: list[ExposureFit] = []
    marginal: dict[str, JsonValue] = {}
    distributions: dict[str, JsonValue] = {}

    for product in usable:
        record = series[product.ticker]
        rows = _rows_for(panel.periods, record.periods)
        fund_excess = record.returns - panel.risk_free[rows]
        tracking[product.ticker] = _fit_tracking(
            ticker=product.ticker,
            periods=record.periods,
            fund_excess=fund_excess,
            tsmom=benchmark.tsmom[rows],
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            rng=rng,
            resamples=resamples,
            confidence=confidence,
            blocks=(3.0, 6.0, 12.0),
            primary_block=6.0,
            halves=halves,
            rolling_window=rolling_window,
        )
        exposure_fits.append(
            _fit_static_set(
                ticker=product.ticker,
                fund_excess=fund_excess,
                market_excess=market_excess[rows],
                scaled_market_excess=scaled_market_excess[rows],
                hac_lags=hac_lags,
                dispersion=dispersion,
                power=power,
            )
        )
        exposure_fits.append(
            fit_exposure(
                ticker=product.ticker,
                specification="ff5_umd",
                era="common_period",
                excess_returns=fund_excess,
                design=panel.design(FACTOR_SPECIFICATIONS["FF5+UMD"], rows),
                factor_names=FACTOR_SPECIFICATIONS["FF5+UMD"],
                n_lags=hac_lags,
                dispersion_annual_percent=dispersion,
                power=power,
            )
        )
        # The estimator is warmed on the fund's WHOLE filed history and the
        # certainty equivalent is computed only on the whole calendar years inside
        # it. Warming on the reported window alone would leave the comparator
        # unmatched for the first year of every fund.
        reportable = [
            period for period in record.periods if whole_start <= period <= whole_end
        ]
        reported_from = (
            record.periods.index(reportable[0]) if reportable else len(record.periods)
        )
        marginal[product.ticker] = _marginal_certainty_equivalent(
            sleeve_excess=fund_excess,
            equity_total=equity_total[rows],
            cash=benchmark.cash[rows],
            gamma=gamma,
            sleeve_weight=sleeve_weight,
            equity_weight=equity_weight,
            centre_of_mass_months=centre_of_mass,
            reported_from=reported_from,
        )
        distributions[product.ticker] = fetch_reinvestment(
            cache, series_id=product.series_id, start=common_start, end=common_end
        )

    # --- pedestals -------------------------------------------------------------
    pedestals = _pedestals(
        comparator=comparator,
        series=series,
        panel=panel,
        benchmark=benchmark,
        market_excess=market_excess,
        scaled_market_excess=scaled_market_excess,
        hac_lags=hac_lags,
        dispersion=dispersion,
        power=power,
    )

    # --- tax ------------------------------------------------------------------
    _, tax_facts = load_product_facts()
    tax = _tax_block(usable, tax_facts)

    # --- multiple testing ------------------------------------------------------
    alpha_p = [tracking[product.ticker].alpha_p for product in usable]
    alpha_p += [fit.alpha_p for fit in exposure_fits]
    correction = _correction(
        alpha_p=alpha_p,
        usable=len(usable),
        screened=len(universe.products),
    )

    # --- verdicts --------------------------------------------------------------
    outcomes = _verdicts(
        usable=usable,
        tracking=tracking,
        minimum_loading=minimum_loading,
        stability_floor=stability_floor,
        tolerance=tolerance,
    )

    clause_d = _clause_d_block(specification)

    diagnostics: dict[str, JsonValue] = {
        "what_is_answerable": {
            "exposure_delivery": (
                "ANSWERABLE on this window. It is a loading on a named benchmark and a "
                "difference of means against it, and 45 to 78 months can measure both."
            ),
            "alpha": (
                "NOT ANSWERABLE on this window, in either direction. The minimum "
                "detectable alpha at 80% power is reported beside every intercept and "
                "is larger than any plausible true value. Every intercept here is a "
                "statement about the window."
            ),
            "the_error_being_corrected": (
                "Experiment 004 evaluated AQR's TSMOM INDEX. Its `rejected` verdict was "
                "then repeated as if it applied to KMLM, DBMF and CTA -- products that "
                "were never tested and are differently constructed, one of which (DBMF) "
                "is an explicit replication strategy. It did not apply to them and this "
                "experiment is what testing them looks like."
            ),
            "the_second_error": (
                "Bhardwaj, Gorton and Rouwenhorst (2014) measure 1994-2012 hedge-fund "
                "CTAs whose fee income was around 4% of assets and whose net excess "
                "returns were insignificantly different from zero against 6.1% gross. "
                "That evidence does not transfer to an exchange-traded fund charging "
                "0.66% to 0.98%, and it was wrongly applied as though it did. Every fee "
                "here is read from the fund's own SEC-filed summary prospectus."
            ),
        },
        "universe": {
            "committed_file": str(universe_path().relative_to(workspace_root())),
            "sha256": _sha256_file(universe_path()),
            "frame": f"union of {universe.frame_quarter} and {universe.follow_up_quarter}",
            "union_series_count": universe.union_series_count,
            "mandate_matches": universe.mandate_matches,
            "screened_and_recorded": len(universe.products),
            "passed_screen": len(universe.passing),
            "usable_returns": len(usable),
            "attrition": plain_json(dict(universe.attrition)),
        },
        "screen": plain_json([product.to_json() for product in universe.products]),
        "coverage": coverage,
        "fetch_failures": fetch_failures,
        "factor_provenance": dict(panel.provenance),
        "benchmark_provenance": dict(benchmark.provenance),
        "tracking_against_the_aqr_index": [item.to_json() for item in tracking.values()],
        "attributions": [fit.to_json() for fit in exposure_fits],
        "marginal_contribution": marginal,
        "distributions_from_filings": distributions,
        "tax_character": tax,
        "pedestals": pedestals,
        "multiple_testing": correction,
        "shrinkage": _shrinkage_block(tracking, exposure_fits),
        "outcomes": [item.to_json() for item in outcomes],
        "clause_d_rerun": clause_d,
        "unobservable": {
            "distribution_tax_character": (
                "NOT IN FORM N-PORT. The form reports one total return and one "
                "reinvestment dollar figure per month, with no split between ordinary "
                "income, short-term gain and long-term gain. The prospectus after-tax "
                "table is the only measure here that speaks to tax, and it is the "
                "fund's own SEC-standardised computation, not this repository's."
            ),
            "bid_ask_and_brokerage": "NOT MODELLED. Nothing here is a net-of-everything return.",
            "subsidiary_level_detail": (
                "Every fund here holds commodity exposure through a Cayman subsidiary "
                "whose income is ordinary. The subsidiary's own trading is inside the "
                "fund's filed return and is not separable from it."
            ),
        },
    }

    summary = _summary(universe, usable, outcomes, tracking, clause_d)
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=summary,
        estimates=tuple(_estimates(usable, tracking, marginal)),
        diagnostics=diagnostics,
        caveats=tuple(_caveats(universe, usable, tracking, exposure_fits)),
        frames=_frames(universe, tracking, exposure_fits, outcomes, coverage),
    )


# --------------------------------------------------------------------------- #
# Blocks the run assembles
# --------------------------------------------------------------------------- #


def _pedestals(
    *,
    comparator: str,
    series: Mapping[str, FundSeries],
    panel: object,
    benchmark: BenchmarkPanel,
    market_excess: FloatArray,
    scaled_market_excess: FloatArray,
    hac_lags: int,
    dispersion: float,
    power: float,
) -> dict[str, JsonValue]:
    """The two controls that make every other number readable.

    **VTI** is a cap-weighted total-market fund, so it IS the market portfolio and
    under a correctly specified model its alpha should be about minus its
    three-basis-point fee. Whatever it is instead is model misfit carried by every
    fund priced by the same factors over the same window, and every alpha in this
    experiment is a distance from it rather than from zero.

    **The AQR index put through the identical machinery** is the second control. Run
    against itself it must show a loading of exactly 1.000 and a tracking difference
    of exactly zero, which confirms the machinery carries no offset; that limb is
    degenerate by construction and is printed for exactly that reason. Its loadings
    under the static exposure set over the SAME short window are the substantive
    control: each fund's static-set loadings are distances from what a
    definitionally-trend series shows on these months, not from zero.
    """
    from portfolio_edge.experiments.exp_002_fund_exposure import FactorPanel

    assert isinstance(panel, FactorPanel)
    out: dict[str, JsonValue] = {}

    record = series.get(comparator)
    if record is None:
        out["market_model_pedestal"] = {
            "available": False,
            "reason": f"{comparator} has no usable filed history",
        }
    else:
        rows = _rows_for(panel.periods, record.periods)
        excess = record.returns - panel.risk_free[rows]
        by_specification: dict[str, JsonValue] = {}
        for name, factors in FACTOR_SPECIFICATIONS.items():
            fit = fit_exposure(
                ticker=comparator,
                specification=name,
                era="common_period",
                excess_returns=excess,
                design=panel.design(factors, rows),
                factor_names=factors,
                n_lags=hac_lags,
                dispersion_annual_percent=dispersion,
                power=power,
            )
            by_specification[name] = {
                "alpha_annual_percent": fit.alpha_annual_percent,
                "alpha_se_annual_percent": fit.alpha_se_annual_percent,
                "alpha_t": fit.alpha_t,
                "market_beta": fit.loadings["Mkt-RF"],
                "r_squared": fit.r_squared,
            }
        static = _fit_static_set(
            ticker=comparator,
            fund_excess=excess,
            market_excess=market_excess[rows],
            scaled_market_excess=scaled_market_excess[rows],
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        by_specification["static_exposure_set"] = static.to_json()
        out["market_model_pedestal"] = {
            "available": True,
            "comparator": comparator,
            "months": len(record.periods),
            "by_specification": by_specification,
            "interpretation": (
                f"{comparator} holds the market portfolio at a three-basis-point fee, so "
                "under a correctly specified model its alpha should be about -0.03 "
                "pp/yr. The distance from that is model misfit shared by every fund "
                "priced by the same factors over the same window. Read every alpha in "
                "this experiment as a distance from this pedestal, never from zero."
            ),
        }

    # The definitional control: the benchmark, put through its own machinery.
    tsmom = benchmark.tsmom
    self_fit = hac_ols(tsmom, tsmom[:, None], n_lags=hac_lags, add_constant=True)
    difference, error = tracking_difference(tsmom, tsmom)
    static_on_index = _fit_static_set(
        ticker="AQR_TSMOM",
        fund_excess=tsmom,
        market_excess=market_excess,
        scaled_market_excess=scaled_market_excess,
        hac_lags=hac_lags,
        dispersion=dispersion,
        power=power,
    )
    out["definitional_pedestal"] = {
        "series": "the AQR TSMOM index itself",
        "months": int(tsmom.size),
        "self_loading": float(self_fit.coefficients[1]),
        "self_alpha_annual_percent": float(self_fit.coefficients[0]) * MONTHS_PER_YEAR * 100.0,
        "self_raw_tracking_difference_annual_percent": difference,
        "self_tracking_error_annual_percent": error,
        "degenerate_by_construction": True,
        "why_it_is_printed": (
            "Regressed on itself the index must show a loading of exactly 1.000 and a "
            "tracking difference of exactly zero. Printing it confirms the machinery "
            "carries no offset. A control that cannot fail is worth one line and no more."
        ),
        "static_exposure_set_on_the_index": static_on_index.to_json(),
        "the_substantive_control": (
            "The static-set loadings above are what a DEFINITIONALLY-TREND series shows "
            "over these same short months. Each fund's static-set loadings are read as "
            "distances from these, not from zero: a fund whose static market beta "
            "matches the index's is behaving like trend, and one whose beta is far from "
            "it is not, whatever its own t-statistics say."
        ),
    }
    return out


def _tax_block(
    usable: Sequence[ScreenedProduct], tax_facts: Mapping[str, ProductTaxFacts]
) -> dict[str, JsonValue]:
    rows: list[dict[str, JsonValue]] = []
    for product in usable:
        facts = tax_facts.get(product.ticker)
        if facts is None:
            rows.append({"ticker": product.ticker, "available": False})
            continue
        rows.append(
            {
                "ticker": product.ticker,
                "available": True,
                "as_of": facts.as_of,
                "source_url": facts.source_url,
                "rows": [row.to_json() for row in facts.rows],
                "longest_period_tax_drag_percent": facts.rows[-1].distribution_tax_drag_percent,
                "longest_period": facts.rows[-1].period,
            }
        )
    return {
        "measured_not_modelled": (
            "These are the funds' OWN SEC-standardised after-tax returns, computed at "
            "the highest individual federal marginal rates with no state or local tax, "
            "for a taxable account. They are irrelevant to an IRA or a 401(k). No "
            "figure here is applied as a haircut to any return in this experiment."
        ),
        "not_in_any_falsifier_clause": (
            "DELIBERATELY. These figures were read while the product facts were "
            "assembled, so a threshold placed on them now would be a threshold chosen "
            "after seeing the quantity. They are measured and reported and decide "
            "nothing. This is a limitation, recorded rather than repaired by inventing "
            "a bar."
        ),
        "as_of_dates_differ": (
            "Sponsors file summary prospectuses on their own fiscal calendars, so the "
            "tables end on different dates. They are never averaged across funds and "
            "the as-of date is printed with every row."
        ),
        "rows": rows,
    }


def _correction(*, alpha_p: Sequence[float], usable: int, screened: int) -> dict[str, JsonValue]:
    values = np.asarray(list(alpha_p), dtype=np.float64)
    if values.size == 0:
        return {"family_size": 0, "note": "no usable fund produced a test"}
    bh = benjamini_hochberg(values, alpha=0.10)
    holm = holm_bonferroni(values, alpha=0.10)
    return {
        "family_definition": (
            "every fund with usable filed returns times every attribution "
            "specification estimated -- AQR-index tracking, the static exposure set, "
            "and FF5+UMD -- not the funds or the specification anyone chose to report"
        ),
        "family_size": int(values.size),
        "funds": usable,
        "specifications": list(SPECIFICATION_NAMES),
        "denominator_reported": int(values.size),
        "rejected_uncorrected_at_0_05": int(np.sum(values <= 0.05)),
        "rejected_uncorrected_at_0_10": int(np.sum(values <= 0.10)),
        "rejected_benjamini_hochberg_at_0_10": int(np.sum(bh.rejected)),
        "rejected_holm_bonferroni_at_0_10": int(np.sum(holm.rejected)),
        "which_correction_is_defensible": (
            "HOLM. These tests are not independent: three nested-in-data "
            "specifications per fund on the same months, and every fund trades the same "
            "futures markets. Benjamini-Hochberg assumes independence or positive "
            "regression dependence and its count is therefore an OPTIMISTIC bound."
        ),
        "denominator_hostile_test": {
            "why": (
                "A screened fund that failed the screen was never regressed and so has "
                "no p-value, but the search still passed over it. Padding the family to "
                "its full width with p = 1.0 cannot create a rejection and strictly "
                "tightens both corrections, so this is the most pessimistic honest "
                "accounting of how much looking was done."
            ),
            "every_screened_series_times_three_specifications": inflated_family(
                list(values), family_size=max(int(values.size), screened * len(SPECIFICATION_NAMES))
            ),
        },
        "what_a_rejection_here_would_and_would_not_mean": (
            "These are tests on INTERCEPTS. A rejection would mean the window could "
            "resolve a residual mean, not that the fund has skill; the sign of every "
            "surviving intercept, its shrunk value and its detection threshold are "
            "printed beside it. No falsifier clause in this experiment reads a "
            "p-value, by design."
        ),
    }


def _shrinkage_block(
    tracking: Mapping[str, TrackingFit], exposure_fits: Sequence[ExposureFit]
) -> dict[str, JsonValue]:
    factors = [item.shrinkage_factor for item in tracking.values()]
    factors += [fit.shrinkage_factor for fit in exposure_fits]
    return {
        "sigma_true_annual_percent": 1.25,
        "measured_not_assumed": (
            "Each fund's factor is computed from its OWN annualised HAC standard error, "
            "never from the framework's 0.121 reference value, which is the factor at a "
            "reference standard error of 3.36%/yr and would be wrong for every fund "
            "here. Experiment 002 measured a median of 0.431 on index funds; this shelf "
            "measures its own."
        ),
        "realised_minimum": float(np.min(factors)) if factors else None,
        "realised_median": float(np.median(factors)) if factors else None,
        "realised_maximum": float(np.max(factors)) if factors else None,
        "annualisation": (
            "An annual alpha is TWELVE times a monthly intercept, so its standard error "
            "annualises by x12 and never by sqrt(12). Using sqrt(12) would divide every "
            "standard error by 3.46 and shrink far too little, which is the direction "
            "that manufactures skill."
        ),
        "prior_is_transferred": (
            "sigma_true = 1.25%/yr comes from Fama and French (2010), a bootstrap of US "
            "ACTIVE EQUITY MUTUAL FUNDS over 1984-2006, applied here to managed-futures "
            "ETFs. That transfer is an assumption and it decides every shrunk number."
        ),
    }


def _verdicts(
    *,
    usable: Sequence[ScreenedProduct],
    tracking: Mapping[str, TrackingFit],
    minimum_loading: float,
    stability_floor: float,
    tolerance: float,
) -> list[ProductOutcome]:
    """Apply the frozen falsifier, clause by clause, and record which ones fired."""
    outcomes: list[ProductOutcome] = []
    for product in usable:
        fit = tracking.get(product.ticker)
        outcome = ProductOutcome(
            ticker=product.ticker, series_name=product.series_name, status="unresolved"
        )
        if fit is None:
            outcome.notes.append("no tracking fit; nothing to decide")
            outcomes.append(outcome)
            continue

        if fit.loading < minimum_loading:
            outcome.clauses_fired.append(
                f"(a) loading on the AQR TSMOM index is {fit.loading:+.3f}, below "
                f"{minimum_loading:.2f}: the fund does not deliver the exposure"
            )
        halves = (fit.first_half_loading, fit.second_half_loading)
        if all(math.isfinite(value) for value in halves):
            if min(halves) < stability_floor:
                outcome.clauses_fired.append(
                    f"(b) the loading falls to {min(halves):+.3f} in one fixed half "
                    f"({fit.first_half_loading:+.3f} then {fit.second_half_loading:+.3f}), "
                    f"below the {stability_floor:.2f} stability floor"
                )
            elif halves[0] * halves[1] < 0.0:
                outcome.clauses_fired.append(
                    f"(b) the loading changes sign across the fixed halves: "
                    f"{halves[0]:+.3f} then {halves[1]:+.3f}"
                )
        else:
            outcome.notes.append(
                "the fixed-halves test could not run: the fund's filed history does "
                "not cover both halves of the frozen split"
            )
        fee = 0.0 if product.facts is None else (product.facts.net_expense_ratio_percent or 0.0)
        shortfall = -fit.raw_tracking_difference_percent - fee
        if shortfall > tolerance:
            outcome.clauses_fired.append(
                f"(c) the fund trailed the AQR index by "
                f"{-fit.raw_tracking_difference_percent:+.2f} pp/yr against its own "
                f"{fee:.2f}% fee, a shortfall of {shortfall:+.2f} pp/yr above the "
                f"{tolerance:.2f} tolerance"
            )
        outcome.notes.append(
            f"raw tracking difference {fit.raw_tracking_difference_percent:+.2f} pp/yr, "
            f"fee {fee:.2f}%, shortfall {shortfall:+.2f} pp/yr, tracking error "
            f"{fit.tracking_error_percent:.2f} pp/yr"
        )

        low, high = fit.loading_interval
        if outcome.clauses_fired:
            outcome.status = "rejected"
        elif low <= minimum_loading <= high:
            outcome.status = "unresolved"
            outcome.notes.append(
                f"the 95% interval [{low:+.3f}, {high:+.3f}] contains the "
                f"{minimum_loading:.2f} threshold, which is what a "
                f"{fit.n_observations}-month window is expected to produce"
            )
        else:
            outcome.status = "exploratory"
        outcomes.append(outcome)
    return outcomes


def _summary(
    universe: object,
    usable: Sequence[ScreenedProduct],
    outcomes: Sequence[ProductOutcome],
    tracking: Mapping[str, TrackingFit],
    clause_d: Mapping[str, JsonValue],
) -> str:
    from portfolio_edge.experiments.exp_008_universe import ManagedFuturesUniverse

    assert isinstance(universe, ManagedFuturesUniverse)
    delivered = sum(1 for item in outcomes if item.status == "exploratory")
    rejected = sum(1 for item in outcomes if item.status == "rejected")
    unresolved = sum(1 for item in outcomes if item.status == "unresolved")
    months = [fit.n_observations for fit in tracking.values()]
    readings = clause_d.get("readings")
    differ = clause_d.get("verdicts_differ")
    return (
        f"Screened {universe.mandate_matches} mandate-matching series from the union of "
        f"the {universe.frame_quarter} and {universe.follow_up_quarter} N-PORT censuses; "
        f"{len(universe.passing)} passed the frozen screen and {len(usable)} had enough "
        f"filed monthly returns, over {min(months) if months else 0} to "
        f"{max(months) if months else 0} months. {delivered} product(s) reached "
        f"`exploratory` on EXPOSURE DELIVERY, {rejected} were `rejected` on the frozen "
        f"falsifier and {unresolved} are `unresolved`. Alpha is not answerable on a "
        "window this short and no clause reads one. Experiment 004's clause (d) was "
        f"re-decided under both readings and the verdicts "
        f"{'DIFFER' if differ else 'agree'}"
        f"{f' across {len(readings)} readings' if isinstance(readings, Sequence) else ''}. "
        "The binding constraint is decision 0002's data contract and the window, not "
        "the evidence."
    )


def _estimates(
    usable: Sequence[ScreenedProduct],
    tracking: Mapping[str, TrackingFit],
    marginal: Mapping[str, JsonValue],
) -> list[Estimate]:
    out: list[Estimate] = []
    for product in usable:
        fit = tracking.get(product.ticker)
        if fit is None:
            continue
        out.append(
            Estimate(
                name=f"{product.ticker} loading on the AQR TSMOM index",
                value=fit.loading,
                units="loading (dimensionless)",
                interval=fit.loading_interval,
                interval_method=(
                    "stationary block bootstrap, 95%, mean block 6m, joint resampling "
                    "of the fund return and the whole design"
                ),
                cost_basis=CostBasis.NET_OPTIMISTIC,
                n_obs=fit.n_observations,
                notes=(
                    "EXPOSURE DELIVERY, the question this window can answer. The fund's "
                    "return is already net of its ongoing expenses; the AQR index is "
                    "gross of the vendor's own costs by omission."
                ),
            )
        )
        out.append(
            Estimate(
                name=f"{product.ticker} tracking difference against the AQR TSMOM index",
                value=fit.raw_tracking_difference_percent,
                units="percentage points per year",
                interval=None,
                uncertainty_unavailable_reason=(
                    "A raw difference of means over "
                    f"{fit.n_observations} months whose tracking error is "
                    f"{fit.tracking_error_percent:.2f} pp/yr is not resolvable to "
                    "anything near a percentage point. It is a decision input applied "
                    "as frozen, not a measurement, and the beta-adjusted intercept "
                    f"{fit.alpha_annual_percent:+.2f} pp/yr with detection threshold "
                    f"{fit.minimum_detectable_alpha_percent:.2f} is printed beside it."
                ),
                cost_basis=CostBasis.NET_OPTIMISTIC,
                n_obs=fit.n_observations,
                notes="negative means the fund trailed the index",
            )
        )
        block = marginal.get(product.ticker)
        if isinstance(block, Mapping) and block.get("available"):
            years = block["whole_calendar_years"]
            out.append(
                Estimate(
                    name=f"{product.ticker} marginal certainty equivalent vs risk-matched cash",
                    value=float(
                        str(
                            block["marginal_certainty_equivalent_percentage_points_per_year"]
                        )
                    ),
                    units="percentage points per year",
                    interval=None,
                    uncertainty_unavailable_reason=(
                        f"Computed from {years} non-overlapping calendar-year gross "
                        "returns. An interval on that many annual observations would "
                        "imply a precision the sample does not have. This is a "
                        "DESCRIPTION of the window, not an inference about the fund."
                    ),
                    cost_basis=CostBasis.NET_OPTIMISTIC,
                    n_obs=int(str(years)) * MONTHS_PER_YEAR,
                    notes="Experiment 004's five-way structure, at the same 15% sleeve weight",
                )
            )
    return out


def _caveats(
    universe: object,
    usable: Sequence[ScreenedProduct],
    tracking: Mapping[str, TrackingFit],
    exposure_fits: Sequence[ExposureFit],
) -> list[str]:
    from portfolio_edge.experiments.exp_008_universe import ManagedFuturesUniverse

    assert isinstance(universe, ManagedFuturesUniverse)
    mdes = [fit.minimum_detectable_alpha_percent for fit in tracking.values()]
    mdes += [fit.minimum_detectable_alpha_percent for fit in exposure_fits]
    months = [fit.n_observations for fit in tracking.values()]
    return [
        "EXPLORATORY. Decision 0002 stands: nothing here may promote a sleeve or "
        "appear in the app as a finding.",
        "EXPOSURE DELIVERY AND ALPHA ARE DIFFERENT QUESTIONS. This window answers the "
        f"first and not the second: the median minimum detectable alpha at 80% power is "
        f"{float(np.median(mdes)):.2f} pp/yr across "
        f"{len(mdes)} fund-by-specification tests, larger than any plausible true "
        "value, so every interval containing zero is a statement about the window.",
        f"Effective samples run {min(months) if months else 0} to "
        f"{max(months) if months else 0} months. At a 6-month mean block that is "
        f"{effective_independent_blocks(min(months) if months else 0, 6.0):.1f} to "
        f"{effective_independent_blocks(max(months) if months else 0, 6.0):.1f} "
        "effective independent observations, and they are not equal across funds, so "
        "no two funds' figures carry the same weight.",
        "The benchmark is a VENDOR SERIES maintained by a firm that sells the strategy, "
        "whose cost basis is unestablished and which is gross of its own trading costs "
        "by omission. That makes it a HARD benchmark for a fund charging a real fee, "
        "which is the conservative direction for a tracking test and the wrong "
        "direction for any claim that a fund 'beat' it.",
        "The frame is the UNION of two censuses and is NOT survivorship-free. Public "
        "N-PORT filings begin in 2019, so a managed-futures fund that closed before "
        "2019Q4 is invisible. The measured attrition is a lower bound.",
        "Item B.5 returns are fund-reported and unaudited, and Form N-PORT General "
        "Instruction G lets each filer use its own internal methodology, so two funds' "
        "returns are not guaranteed to be computed identically. No independent "
        "cross-check of any return was obtained.",
        "Reinvested distributions from Form N-PORT are a LOWER BOUND on distributions "
        "and say nothing about tax character. The prospectus after-tax figures are the "
        "funds' own SEC-standardised computation at the highest federal marginal rates, "
        "are irrelevant in a tax-deferred account, and are applied to no return here.",
        "The prospectus after-tax figures were read BEFORE any return was downloaded "
        "but were visible to the author, so no falsifier clause reads them. That is a "
        "limitation of this specification, recorded rather than repaired.",
        f"{len(usable)} of {len(universe.passing)} passing funds had enough filed "
        "months. Nothing was interpolated and no history was extended past what the "
        "filings carry.",
        "The Bhardwaj-Gorton-Rouwenhorst hedge-fund CTA fee evidence does NOT transfer "
        "to these products and is not used. Every fee here is read from the fund's own "
        "SEC-filed summary prospectus.",
    ]


def _frames(
    universe: object,
    tracking: Mapping[str, TrackingFit],
    exposure_fits: Sequence[ExposureFit],
    outcomes: Sequence[ProductOutcome],
    coverage: Sequence[Mapping[str, JsonValue]],
) -> dict[str, pd.DataFrame]:
    from portfolio_edge.experiments.exp_008_universe import ManagedFuturesUniverse

    assert isinstance(universe, ManagedFuturesUniverse)
    screen_rows = [
        {
            "ticker": product.ticker,
            "series_name": product.series_name,
            "passed": product.passed,
            "failed_criterion": product.failed_criterion or "",
            "failure_detail": product.failure_detail,
            "net_assets_maximum_usd": product.net_assets_maximum,
            "in_frame_quarter": product.in_frame_quarter,
            "in_follow_up_quarter": product.in_follow_up_quarter,
            "net_expense_ratio_percent": (
                None if product.facts is None else product.facts.net_expense_ratio_percent
            ),
            "inception_date": (
                None if product.facts is None else product.facts.inception_date
            ),
        }
        for product in universe.products
    ]
    attribution_rows: list[dict[str, object]] = []
    for fit in exposure_fits:
        row: dict[str, object] = {
            "ticker": fit.ticker,
            "specification": fit.specification,
            "alpha_annual_percent": fit.alpha_annual_percent,
            "alpha_se_annual_percent": fit.alpha_se_annual_percent,
            "alpha_t": fit.alpha_t,
            "shrunk_alpha_annual_percent": fit.shrunk_alpha_annual_percent,
            "shrinkage_factor": fit.shrinkage_factor,
            "mde_alpha_annual_percent": fit.minimum_detectable_alpha_percent,
            "r_squared": fit.r_squared,
            "n_observations": fit.n_observations,
        }
        row.update({f"beta_{name}": value for name, value in fit.loadings.items()})
        attribution_rows.append(row)
    return {
        "screen": pd.DataFrame(screen_rows),
        "tracking": pd.DataFrame([item.to_json() for item in tracking.values()]),
        "attributions": pd.DataFrame(attribution_rows),
        "outcomes": pd.DataFrame([item.to_json() for item in outcomes]),
        "coverage": pd.DataFrame(list(coverage)),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _build_universe_command(specification: Specification) -> int:
    """Screen the union census and write the committed universe, before any return."""
    parameters = _mapping(specification.parameters, where="parameters")
    patterns = _mapping(
        _at(parameters, "screening_patterns", where="parameters"), where="screening_patterns"
    )
    cache = RawCache()
    universe = build_universe(
        cache=cache,
        mandate_pattern=_text(patterns, "mandate_regex", where="screening_patterns"),
        exclusion_pattern=_text(patterns, "exclusion_regex", where="screening_patterns"),
        minimum_net_assets=_number(parameters, "minimum_net_assets_usd", where="parameters"),
        maximum_expense_ratio=_number(
            parameters, "maximum_net_expense_ratio_percent", where="parameters"
        ),
        inception_on_or_before=_text(parameters, "inception_on_or_before", where="parameters"),
        intended_exposure_map=intended_exposure_map(specification),
    )
    path = write_universe(universe)
    manifests = workspace_root() / "data-manifests"
    for manifest in universe_manifests(cache):
        manifest.write(manifests)

    print(f"universe written to {path}")
    print(
        f"  union frame {universe.frame_quarter}+{universe.follow_up_quarter}: "
        f"{universe.union_series_count} series"
    )
    print(f"  mandate matches: {universe.mandate_matches}")
    print(f"  screened and recorded: {len(universe.products)}")
    print(f"  passed: {len(universe.passing)}")
    counts: dict[str, int] = {}
    for product in universe.products:
        if product.failed_criterion:
            counts[product.failed_criterion] = counts.get(product.failed_criterion, 0) + 1
    for criterion, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"    failed {criterion}: {count}")
    for product in universe.products:
        mark = "PASS" if product.passed else "    "
        print(
            f"  {mark} {product.ticker:<6} {(product.net_assets_maximum or 0) / 1e6:9.1f}m  "
            f"{product.series_name[:52]:<54}{product.failed_criterion or ''}"
        )
    return 0


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    diagnostics = result.diagnostics
    lines = [result.summary, ""]

    universe = diagnostics.get("universe")
    if isinstance(universe, Mapping):
        lines.append(
            f"Universe: {universe['frame']}, {universe['union_series_count']} series, "
            f"{universe['mandate_matches']} mandate matches, "
            f"{universe['screened_and_recorded']} screened, "
            f"{universe['passed_screen']} passed, {universe['usable_returns']} usable."
        )
        lines.append("")

    screen = diagnostics.get("screen")
    if isinstance(screen, Sequence):
        lines.append("The screen, every series with the FIRST criterion it failed:")
        for item in screen:
            if not isinstance(item, Mapping):
                continue
            assets = item.get("net_assets_maximum_usd")
            lines.append(
                f"  {'PASS' if item['passed'] else '    '} {item['ticker']!s:<6}"
                f"{(float(str(assets)) if assets else 0.0) / 1e6:>10.1f}m  "
                f"{str(item['series_name'])[:48]:<50}{item.get('failed_criterion') or ''}"
            )
        lines.append("")

    tracking = diagnostics.get("tracking_against_the_aqr_index")
    if isinstance(tracking, Sequence):
        header = (
            f"{'ticker':<7}{'n':>4}{'window':>18}{'beta':>8}{'HACse':>7}"
            f"{'  95% bootstrap':<20}{'H1':>7}{'H2':>7}{'corr':>7}{'R2':>7}"
            f"{'TD':>8}{'TE':>7}{'MDE80':>8}"
        )
        lines.extend(["EXPOSURE DELIVERY against the AQR TSMOM index", header, "-" * len(header)])
        for item in tracking:
            if not isinstance(item, Mapping):
                continue
            interval = item["loading_95_interval"]
            assert isinstance(interval, Sequence)
            lines.append(
                f"{item['ticker']!s:<7}{int(str(item['n_observations'])):>4}"
                f"{item['window']!s:>18}"
                f"{float(str(item['aqr_tsmom_loading'])):>+8.3f}"
                f"{float(str(item['loading_hac_se'])):>7.3f}"
                f"  [{float(str(interval[0])):+.3f},{float(str(interval[1])):+.3f}]"
                f"{float(str(item['loading_first_half'])):>+7.2f}"
                f"{float(str(item['loading_second_half'])):>+7.2f}"
                f"{float(str(item['correlation_with_aqr_tsmom'])):>+7.2f}"
                f"{float(str(item['r_squared'])):>7.3f}"
                f"{float(str(item['raw_tracking_difference_annual_percent'])):>+8.2f}"
                f"{float(str(item['tracking_error_annual_percent'])):>7.2f}"
                f"{float(str(item['minimum_detectable_alpha_percent'])):>8.2f}"
            )
        lines.append("")
        lines.append(
            "beta is the loading on the AQR index, TD the raw annualised tracking "
            "difference, TE its dispersion, MDE80 the smallest intercept this window "
            "could have detected at 80% power. TD is a decision input; MDE80 says "
            "whether any intercept is measurable at all."
        )
        lines.append("")

    outcomes = diagnostics.get("outcomes")
    if isinstance(outcomes, Sequence):
        lines.append("Verdicts on the frozen falsifier:")
        for item in outcomes:
            if not isinstance(item, Mapping):
                continue
            lines.append(f"  {item['ticker']!s:<7}{item['status']}")
            for clause in item["falsifier_clauses_fired"]:  # type: ignore[union-attr]
                lines.append(f"          {clause}")
            for note in item["notes"]:  # type: ignore[union-attr]
                lines.append(f"          note: {note}")
        lines.append("")

    attributions = diagnostics.get("attributions")
    if isinstance(attributions, Sequence):
        lines.append("Static exposure set (Experiment 004's decisive design):")
        header = (
            f"{'ticker':<10}{'mkt':>9}{'volscaled':>11}{'|mkt|':>9}{'lagmkt':>9}"
            f"{'alphaR':>9}{'alphaS':>9}{'MDE80':>8}{'R2':>7}"
        )
        lines.extend([header, "-" * len(header)])
        for item in attributions:
            if not isinstance(item, Mapping) or item["specification"] != "static_exposure_set":
                continue
            loadings = item["loadings"]
            assert isinstance(loadings, Mapping)
            lines.append(
                f"{item['ticker']!s:<10}"
                + "".join(
                    f"{float(str(loadings[name])):>+9.3f}"
                    if name != "volatility_scaled_market_excess_return"
                    else f"{float(str(loadings[name])):>+11.3f}"
                    for name in STATIC_SET_NAMES
                )
                + f"{float(str(item['alpha_annual_percent'])):>+9.2f}"
                f"{float(str(item['shrunk_alpha_annual_percent'])):>+9.2f}"
                f"{float(str(item['minimum_detectable_alpha_percent'])):>8.2f}"
                f"{float(str(item['r_squared'])):>7.3f}"
            )
        lines.append("")

    pedestals = diagnostics.get("pedestals")
    if isinstance(pedestals, Mapping):
        market = pedestals.get("market_model_pedestal")
        if isinstance(market, Mapping) and market.get("available"):
            specs = market["by_specification"]
            assert isinstance(specs, Mapping)
            rendered = ", ".join(
                f"{name} {float(str(dict(block)['alpha_annual_percent'])):+.2f}"
                for name, block in specs.items()
                if isinstance(block, Mapping)
            )
            lines.append(
                f"MODEL-MISFIT PEDESTAL. {market['comparator']} IS the market portfolio, "
                f"so its alpha should be about -0.03 pp/yr. It is: {rendered}. Read "
                "every alpha above as a distance from this, not from zero."
            )
        definitional = pedestals.get("definitional_pedestal")
        if isinstance(definitional, Mapping):
            static = definitional["static_exposure_set_on_the_index"]
            assert isinstance(static, Mapping)
            loadings = static["loadings"]
            assert isinstance(loadings, Mapping)
            lines.append(
                "DEFINITIONAL PEDESTAL. The AQR index on itself: loading "
                f"{float(str(definitional['self_loading'])):.3f}, tracking difference "
                f"{float(str(definitional['self_raw_tracking_difference_annual_percent'])):.3f} "
                "pp/yr, both exact by construction. Under the static exposure set over "
                "these same months it shows market "
                f"{float(str(loadings['market_excess_return'])):+.3f}, vol-scaled "
                f"{float(str(loadings['volatility_scaled_market_excess_return'])):+.3f}, "
                f"convexity {float(str(loadings['absolute_market_excess_return'])):+.3f}, "
                f"R2 {float(str(static['r_squared'])):.3f}."
            )
        lines.append("")

    marginal = diagnostics.get("marginal_contribution")
    if isinstance(marginal, Mapping):
        lines.append("Marginal contribution, Experiment 004's five-way structure:")
        for ticker, block in marginal.items():
            if not isinstance(block, Mapping):
                continue
            if not block.get("available"):
                lines.append(f"  {ticker:<7}unavailable: {block.get('reason')}")
                continue
            lines.append(
                f"  {ticker:<7}"
                f"{float(str(block['marginal_certainty_equivalent_percentage_points_per_year'])):+.3f}"
                f" pp/yr on {block['whole_calendar_years']} whole calendar years "
                "(a description, not an inference)"
            )
        lines.append("")

    tax = diagnostics.get("tax_character")
    if isinstance(tax, Mapping):
        rows = tax["rows"]
        assert isinstance(rows, Sequence)
        lines.append("Tax character, from each fund's own prospectus after-tax table:")
        for item in rows:
            if not isinstance(item, Mapping) or not item.get("available"):
                continue
            lines.append(
                f"  {item['ticker']!s:<7}as of {item['as_of']}, "
                f"{item['longest_period']} tax drag "
                f"{float(str(item['longest_period_tax_drag_percent'])):+.2f} pp/yr"
            )
        lines.append("  " + str(tax["not_in_any_falsifier_clause"]))
        lines.append("")

    distributions = diagnostics.get("distributions_from_filings")
    if isinstance(distributions, Mapping):
        lines.append("Reinvested distributions from the filings (a LOWER BOUND):")
        for ticker, block in distributions.items():
            if not isinstance(block, Mapping):
                continue
            rate = block.get("reinvested_percent_of_net_assets_per_year")
            lines.append(
                f"  {ticker:<7}{float(str(rate)) if rate is not None else float('nan'):>6.2f}%/yr "
                f"across {block['months_observed']} months, "
                f"{block['months_with_a_reinvested_distribution']} with a reinvestment"
            )
        lines.append("")

    correction = diagnostics.get("multiple_testing")
    if isinstance(correction, Mapping):
        lines.append(
            f"Multiple testing over {correction['family_size']} tests "
            f"({correction['funds']} funds x {len(SPECIFICATION_NAMES)} specifications): "
            f"uncorrected p<=0.05 {correction['rejected_uncorrected_at_0_05']}, "
            f"BH at 0.10 {correction['rejected_benjamini_hochberg_at_0_10']}, "
            f"Holm at 0.10 {correction['rejected_holm_bonferroni_at_0_10']}."
        )
        hostile = correction.get("denominator_hostile_test")
        if isinstance(hostile, Mapping):
            block = hostile["every_screened_series_times_three_specifications"]
            assert isinstance(block, Mapping)
            lines.append(
                f"  denominator widened to {block['family_size']}: BH "
                f"{block['rejected_benjamini_hochberg']}, Holm "
                f"{block['rejected_holm_bonferroni']}"
            )
        lines.append("")

    shrinkage = diagnostics.get("shrinkage")
    if isinstance(shrinkage, Mapping):
        lines.append(
            "Shrinkage factors MEASURED, not assumed: "
            f"min {float(str(shrinkage['realised_minimum'])):.3f}, median "
            f"{float(str(shrinkage['realised_median'])):.3f}, max "
            f"{float(str(shrinkage['realised_maximum'])):.3f}. Experiment 002 measured "
            "0.431 on index funds; the framework's 0.121 reference is used nowhere."
        )
        lines.append("")

    clause = diagnostics.get("clause_d_rerun")
    if isinstance(clause, Mapping):
        inputs = clause["inputs_percentage_points_per_year"]
        readings = clause["readings"]
        assert isinstance(inputs, Mapping) and isinstance(readings, Sequence)
        lines.append("PART B -- Experiment 004's clause (d), re-decided under both readings")
        lines.append(
            f"  sleeve {float(str(inputs['sleeve_marginal'])):+.3f}, replica "
            f"{float(str(inputs['replica_marginal'])):+.3f} "
            f"({float(str(inputs['replica_share_of_sleeve'])) * 100:.0f}% of the sleeve), "
            f"margin {float(str(inputs['sleeve_margin_over_replica'])):+.3f}, threshold "
            f"{float(str(inputs['materiality_threshold'])):.2f} pp/yr"
        )
        for item in readings:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"  {item['reading']!s:<9}{'FIRES' if item['clause_fires'] else 'does not fire'}"
                f"  -> Experiment 004 would be `{item['verdict']}`  ({item['reasoning']})"
            )
        source = clause["source"]
        assert isinstance(source, Mapping)
        verification = source["verification"]
        assert isinstance(verification, Mapping)
        lines.append(
            f"  source run_id {source['run_id']}, artifact "
            f"{'verified' if verification.get('verified') else 'ABSENT, frozen values used'}"
        )
        lines.append(f"  judgement: {clause['judgement']}")
        lines.append(f"  honest answer: {clause['but_the_honest_answer']}")
        lines.append("")

    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Build the universe, or run Experiment 008 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_008_managed_futures",
        description=(
            "Audit the exposure delivery and cost of screened managed-futures ETFs, "
            "and re-decide Experiment 004's clause (d) under both readings, writing a "
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
        "--build-universe",
        action="store_true",
        help=(
            "screen the union N-PORT census and write the committed product universe. "
            "MUST be run before the audit: the universe is fixed before any return is "
            "downloaded, and the audit refuses to rebuild it."
        ),
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

    if arguments.build_universe:
        return _build_universe_command(specification)

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
                "exp_008_managed_futures"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
