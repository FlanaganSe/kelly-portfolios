"""Experiment 004: trend as marginal crisis diversification, vendor-series evaluation.

Reads AQR's published monthly time-series-momentum factor at the workbook, sheet
and vintage pinned in ``research/experiments/exp_004_trend_marginal_value.yaml``
and asks one question: what does adding a 15% trend sleeve do to a passive
portfolio that already exists, measured against a risk-matched increase in cash?

What this experiment is
-----------------------
A **vendor-series evaluation**. AQR maintains the series, sells the strategy, and
reconstructs the entire history on every update. A true reimplementation needs
contract-level futures histories, roll conventions, collateral returns, execution
assumptions and point-in-time market availability, none of which are inputs here.
Nothing produced by this module may be described as an independent replication,
and :class:`~portfolio_edge.experiments.specification.EvidenceClass` records that
in the frozen specification rather than leaving it to the write-up.

What it cannot do, stated before any number
--------------------------------------------
* **It cannot run the decisive published counter-test.** Kim, Tse and Wald (2016)
  collapse the pooled statistic from 4.34 to 1.68 by removing the per-instrument
  volatility scaling. The published series is an aggregate of 58 already-scaled
  instrument positions; it cannot be unwound, so that test is unavailable here.
* **It cannot establish the vendor's cost basis.** The archived workbook states no
  fee, transaction-cost, slippage or financing assumption anywhere. Its
  Definitions, Data Sources and Disclosures sheets ship their content as embedded
  pictures, and the text recovered from them describes the volatility model and
  the instrument universe while saying nothing about costs.
* **It cannot use an investable bond leg.** Decision record 0002 establishes that
  no free price source is research-grade. The primary benchmark is therefore 60%
  US equity / 40% cash, and the equity/bond form survives only as a declared
  robustness arm built from a modelled GS10 duration approximation.

The one question that decides it
--------------------------------
Goyal and Jegadeesh (2018) show the strategy carries a large embedded net-long
market position and that adding a time-varying market position to a
cross-sectional strategy reproduces the time-series result. So the attribution is
not a footnote: if a static market exposure plus a volatility-scaled market
position reproduces the sleeve, the forecasting mechanism is not doing the work
and falsifier clause (d) fires.

Run it::

    uv run python -m portfolio_edge.experiments.exp_004_trend_marginal_value --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.returns import Frequency, compound_simple, geometric_mean
from portfolio_edge.core.statistics import (
    InsufficientTailDataError,
    historical_expected_shortfall,
    sharpe_ratio,
)
from portfolio_edge.data import aqr, fred, french
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
    JsonValue,
    Specification,
    load_specification,
)
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.hac import hac_ols, newey_west_lag_count
from portfolio_edge.inference.multiple_testing import holm_bonferroni

__all__ = [
    "COMPARISON_IDS",
    "ENTRY_POINT",
    "MONTHS_PER_YEAR",
    "CostColumn",
    "MonthlySeries",
    "PanelInputs",
    "PortfolioPath",
    "TrendMarginalValueError",
    "bond_total_return_from_yield",
    "build_registry",
    "certainty_equivalent_annual",
    "default_specification_path",
    "ewma_annualised_covariance",
    "ewma_annualised_volatility",
    "expanding_annualised_volatility",
    "high_water_mark_performance_fee",
    "main",
    "par_bond_risk",
    "run",
]

ENTRY_POINT: Final = "exp_004_trend_marginal_value"

MONTHS_PER_YEAR: Final = 12
TRADING_DAYS_PER_MONTH: Final = 21.0

#: The five comparison portfolios, in the order the frozen specification lists
#: them. Every table in this experiment says which of these it refers to.
COMPARISON_IDS: Final = (
    "passive_benchmark",
    "volatility_scaled_passive",
    "trend_alone",
    "passive_plus_trend",
    "passive_plus_cash",
)

#: Asset ordering inside every weight vector: equity total return, cash, sleeve.
ASSET_NAMES: Final = ("equity", "cash", "sleeve")

FloatArray = NDArray[np.float64]


class TrendMarginalValueError(RuntimeError):
    """The experiment could not be attempted against the declared vintages."""


def _json_float(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``."""
    return None if math.isnan(value) or math.isinf(value) else value


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise TrendMarginalValueError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TrendMarginalValueError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise TrendMarginalValueError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise TrendMarginalValueError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TrendMarginalValueError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _numbers(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[float, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[float] = []
    for index, item in enumerate(items):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise TrendMarginalValueError(f"{where}.{key}[{index}] must be a number, got {item!r}")
        out.append(float(item))
    return tuple(out)


# --------------------------------------------------------------------------- #
# Statistics this experiment adds, each with its own unit test
# --------------------------------------------------------------------------- #


def certainty_equivalent_annual(annual_gross_returns: FloatArray, *, gamma: float) -> float:
    """The constant annual return whose CRRA utility equals the sample's mean utility.

    ``u(x) = x**(1 - gamma) / (1 - gamma)`` for ``gamma != 1``, so
    ``CE = (mean_y G_y**(1 - gamma))**(1 / (1 - gamma)) - 1``. ``gamma = 1`` is the
    geometric mean minus one.

    Inputs are wealth relatives over a whole year, not returns, and must be
    strictly positive: CRRA utility is undefined at zero wealth for ``gamma >= 1``,
    and a portfolio that reaches it is insolvent rather than unlucky. The same
    definition is used by exp_003; it is restated here so that the two experiments
    do not import each other's internals.
    """
    values = np.asarray(annual_gross_returns, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("annual_gross_returns must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(values)):
        raise ValueError("annual_gross_returns contains non-finite values")
    if np.any(values <= 0.0):
        raise ValueError(
            "CRRA utility is undefined at non-positive wealth; a gross return of "
            f"{float(np.min(values))!r} is insolvency, not a low return"
        )
    if math.isclose(gamma, 1.0):
        return float(np.exp(np.mean(np.log(values)))) - 1.0
    power = 1.0 - gamma
    return float(np.mean(values**power) ** (1.0 / power)) - 1.0


def _annual_gross_matrix(monthly: FloatArray) -> FloatArray:
    """Compound ``(..., 12 * Y)`` monthly returns into ``(..., Y)`` annual relatives."""
    values = np.asarray(monthly, dtype=np.float64)
    if values.shape[-1] % MONTHS_PER_YEAR != 0:
        raise ValueError(
            f"need a whole number of 12-month blocks, got {values.shape[-1]} months"
        )
    shaped = values.reshape(*values.shape[:-1], -1, MONTHS_PER_YEAR)
    return np.asarray(np.prod(1.0 + shaped, axis=-1), dtype=np.float64)


def _certainty_equivalent_rows(monthly: FloatArray, *, gamma: float) -> FloatArray:
    """Vectorised certainty equivalent for every row of a ``(R, T)`` return matrix.

    ``gamma = 1`` is the geometric mean minus one, the limit of the CRRA form as
    ``gamma -> 1``. It is branched on rather than computed, because ``1 - gamma``
    is the exponent and its reciprocal divides by zero. The scalar
    :func:`certainty_equivalent_annual` has carried this branch since it was
    written; this row-wise form did not, so a bootstrap on the geometric growth
    basis raised :class:`ZeroDivisionError` instead of answering. Decision record
    0008 makes that basis the one every threshold is decided on, so the branch is
    a prerequisite rather than a convenience.
    """
    annual = _annual_gross_matrix(monthly)
    if np.any(annual <= 0.0):
        raise ValueError("a resampled path reached non-positive wealth over a calendar year")
    if math.isclose(gamma, 1.0):
        return np.asarray(np.exp(np.mean(np.log(annual), axis=-1)) - 1.0, dtype=np.float64)
    power = 1.0 - gamma
    return np.asarray(np.mean(annual**power, axis=-1) ** (1.0 / power) - 1.0, dtype=np.float64)


def ewma_annualised_volatility(
    returns: FloatArray,
    *,
    centre_of_mass_months: float,
    periods_per_year: int = MONTHS_PER_YEAR,
    minimum_observations: int = 24,
) -> FloatArray:
    """Lagged exponentially weighted annualised volatility, in the vendor's own form.

    ``sigma_t`` uses observations strictly before ``t``, which is the vendor's
    stated look-ahead protection ("we use the volatility estimates at time t-1
    applied to time t returns throughout the analysis") and this repository's
    availability rule at once. Entries before ``minimum_observations`` have
    accumulated are ``NaN`` rather than a number computed from too little data.

    The weights are ``(1 - delta) delta**i`` with ``delta / (1 - delta)`` equal to
    ``centre_of_mass_months``, and the variance is ``E[r**2] - E[r]**2`` under
    those weights, annualised by ``periods_per_year``. The vendor applies exactly
    this form to daily returns with a 60-day centre of mass and a factor of 261;
    the public series is monthly, so the same calendar centre of mass is used at
    monthly frequency. That substitution is an approximation of the vendor's
    estimator and is recorded as one.
    """
    values = np.asarray(returns, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("returns must be one-dimensional")
    if centre_of_mass_months <= 0.0:
        raise ValueError(f"centre_of_mass_months must be positive, got {centre_of_mass_months}")
    decay = centre_of_mass_months / (1.0 + centre_of_mass_months)
    out = np.full(values.size, np.nan, dtype=np.float64)
    mean = 0.0
    mean_square = 0.0
    # ``index`` is also the number of observations already absorbed, which is what
    # ``minimum_observations`` gates on.
    for index in range(values.size):
        if index >= minimum_observations:
            variance = max(mean_square - mean * mean, 0.0)
            out[index] = math.sqrt(variance * periods_per_year)
        observation = float(values[index])
        if index == 0:
            mean, mean_square = observation, observation * observation
        else:
            mean = (1.0 - decay) * observation + decay * mean
            mean_square = (1.0 - decay) * observation * observation + decay * mean_square
    return out


def ewma_annualised_covariance(
    left: FloatArray,
    right: FloatArray,
    *,
    centre_of_mass_months: float,
    periods_per_year: int = MONTHS_PER_YEAR,
    minimum_observations: int = 24,
) -> FloatArray:
    """Lagged exponentially weighted annualised covariance, matching the volatility form."""
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("left and right must be one-dimensional and the same length")
    decay = centre_of_mass_months / (1.0 + centre_of_mass_months)
    out = np.full(a.size, np.nan, dtype=np.float64)
    mean_a = mean_b = mean_ab = 0.0
    for index in range(a.size):
        if index >= minimum_observations:
            out[index] = (mean_ab - mean_a * mean_b) * periods_per_year
        x, y = float(a[index]), float(b[index])
        if index == 0:
            mean_a, mean_b, mean_ab = x, y, x * y
        else:
            mean_a = (1.0 - decay) * x + decay * mean_a
            mean_b = (1.0 - decay) * y + decay * mean_b
            mean_ab = (1.0 - decay) * x * y + decay * mean_ab
    return out


def expanding_annualised_volatility(
    returns: FloatArray, *, minimum_observations: int = 24
) -> FloatArray:
    """Realised annualised volatility of everything strictly before ``t``.

    Used as the volatility target of the scaled passive comparator. A full-sample
    target would be a look-ahead normalisation and a fixed number would be a tuned
    parameter; an expanding window is neither.
    """
    values = np.asarray(returns, dtype=np.float64)
    out = np.full(values.size, np.nan, dtype=np.float64)
    for index in range(minimum_observations, values.size):
        out[index] = float(np.std(values[:index], ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    return out


def high_water_mark_performance_fee(
    returns: FloatArray, *, rate: float
) -> tuple[FloatArray, float]:
    """Charge a performance fee on gains above a high-water mark, month by month.

    Returns the net return series and the total fee as a fraction of starting
    wealth. A high-water mark is the standard contract and is strictly more
    favourable to the strategy than charging on every up month, which would take a
    fee twice for recovering the same ground. The favourable convention is chosen
    deliberately: the conclusion must not depend on an unnecessarily harsh model.
    """
    if not 0.0 <= rate < 1.0:
        raise ValueError(f"rate must lie in [0, 1), got {rate}")
    values = np.asarray(returns, dtype=np.float64)
    net = np.empty(values.size, dtype=np.float64)
    nav = 1.0
    high_water = 1.0
    total_fee = 0.0
    for index, gross in enumerate(values):
        before = nav * (1.0 + float(gross))
        fee = rate * max(before - high_water, 0.0)
        after = before - fee
        total_fee += fee
        net[index] = after / nav - 1.0
        nav = after
        high_water = max(high_water, after)
    return net, total_fee


def bond_total_return_from_yield(
    yields_annual: FloatArray, *, maturity_years: float = 10.0
) -> FloatArray:
    """A par-bond total return reconstructed from a constant-maturity yield.

    ``r_t = y_{t-1}/12 - D(y_{t-1}) (y_t - y_{t-1}) + 0.5 C(y_{t-1}) (y_t - y_{t-1})**2``
    with ``D`` and ``C`` the modified duration and convexity of a semi-annual par
    bond at the previous yield.

    This is a MODELLED series and is flagged as such everywhere it appears. It has
    no documented total-return contract, no coupon reinvestment convention and no
    transaction costs. It exists only so that the 2022 window, in which equities
    and bonds fell together, is not silently deleted from the experiment by the
    absence of an investable bond history. The first element is ``NaN``.
    """
    y = np.asarray(yields_annual, dtype=np.float64)
    if y.ndim != 1 or y.size < 2:
        raise ValueError("yields_annual must be one-dimensional with at least two entries")
    out = np.full(y.size, np.nan, dtype=np.float64)
    periods = 2.0 * maturity_years
    for index in range(1, y.size):
        previous = float(y[index - 1])
        change = float(y[index]) - previous
        if previous <= 0.0:
            # A non-positive par yield has no par-bond duration; leave it missing
            # rather than inventing one.
            continue
        modified, convexity = par_bond_risk(previous, periods=periods)
        out[index] = previous / MONTHS_PER_YEAR - modified * change + 0.5 * convexity * change**2
    return out


def par_bond_risk(annual_yield: float, *, periods: float) -> tuple[float, float]:
    """Modified duration and convexity, in years and years squared, of a par bond.

    For a semi-annual par bond priced at 1 with ``n`` periods and per-period yield
    ``i``, the coupon equals the yield, so ``P'(i)`` collapses to ``-(1 - v**n)/i``
    with ``v = 1 / (1 + i)``. Differentiating once more, with the COUPON HELD FIXED
    while the yield moves, gives ``P''(i) = 2[(1 - v**n)/i**2 - n v**(n+1)/i]``.
    Dividing by 2 and 4 converts the per-period derivatives to annual ones.

    At a 4% yield and ten years this returns 8.1757 and 78.8979, both confirmed
    against a numerical derivative of the exact price function in the unit test.

    CORRECTION, 2026-08-12. This function previously dropped the factor of two in
    ``P''(i)`` and returned 39.4490, exactly half the true convexity, and its unit
    test asserted that output rather than an independent value. The error was
    surfaced by exp_010, which carries the corrected form. Inside this experiment
    it reaches only the declared ``research_grade = False`` GS10 bond-proxy
    robustness arm, where the convexity term is second order in a monthly yield
    change; the correction and its effect on every published figure are ledgered
    rather than edited into the published numbers in place.
    """
    if annual_yield <= 0.0:
        raise ValueError(f"a par-bond yield must be positive, got {annual_yield}")
    if periods <= 0.0:
        raise ValueError(f"periods must be positive, got {periods}")
    half = annual_yield / 2.0
    discount = (1.0 + half) ** -periods
    modified = (1.0 - discount) / (2.0 * half)
    convexity = (
        (1.0 - discount) / half**2 - periods * discount / (half * (1.0 + half))
    ) / 2.0
    return modified, convexity


# --------------------------------------------------------------------------- #
# Series and windows
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class MonthlySeries:
    """One monthly series in decimal units, with its period labels."""

    name: str
    periods: tuple[str, ...]
    values: FloatArray
    source: str

    def __post_init__(self) -> None:
        if len(self.periods) != self.values.size:
            raise TrendMarginalValueError(
                f"series {self.name!r} has {len(self.periods)} labels and "
                f"{self.values.size} values"
            )

    def as_map(self) -> dict[str, float]:
        return dict(zip(self.periods, (float(v) for v in self.values), strict=True))


def _series_from_table(
    table: ParsedTable, column: str, *, name: str, source: str
) -> MonthlySeries:
    if column not in table.columns:
        raise TrendMarginalValueError(
            f"column {column!r} is absent from table {table.table_id!r} of {source}; "
            f"found {list(table.columns)}"
        )
    periods: list[str] = []
    values: list[float] = []
    for period, value in zip(table.periods, table.column(column), strict=True):
        if value is None:
            continue
        periods.append(period[:7])
        values.append(value)
    return MonthlySeries(
        name=name,
        periods=tuple(periods),
        values=np.asarray(values, dtype=np.float64),
        source=source,
    )


def _aligned(
    series: Mapping[str, MonthlySeries], *, start: str, end: str
) -> tuple[tuple[str, ...], dict[str, FloatArray], tuple[str, ...]]:
    """Intersect every series onto one contiguous monthly grid, reporting shortfalls.

    Nothing is forward-filled. A month that any series lacks is dropped from all of
    them and the drop is reported, because a hole silently patched is a hole that
    reappears as an unexplained number.
    """
    maps = {name: item.as_map() for name, item in series.items()}
    first, last = month_index(start), month_index(end)
    grid = [
        period
        for period in (
            shift_period(start, offset) for offset in range(max(0, last - first + 1))
        )
    ]
    findings: list[str] = []
    keep = [period for period in grid if all(period in table for table in maps.values())]
    if len(keep) != len(grid):
        missing = [period for period in grid if period not in keep]
        findings.append(
            f"{len(missing)} of {len(grid)} months in {start}..{end} are absent from at "
            f"least one input series and were dropped from all of them: {missing[:6]}"
        )
    for name, table in maps.items():
        available = sorted(table)
        if available and available[0] > start:
            findings.append(
                f"{name} begins at {available[0]}, after the requested {start}"
            )
        if available and available[-1] < end:
            findings.append(f"{name} ends at {available[-1]}, before the requested {end}")
    columns = {
        name: np.asarray([maps[name][period] for period in keep], dtype=np.float64)
        for name in maps
    }
    return (tuple(keep), columns, tuple(findings))


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PanelInputs:
    """Every monthly input on one grid, including the estimator burn-in.

    ``reported_from`` is the index of the first month the experiment is allowed to
    report. Everything before it exists only to warm the volatility and covariance
    estimators, so the first reported month already has a fully converged one.
    """

    periods: tuple[str, ...]
    equity_total: FloatArray
    equity_excess: FloatArray
    cash: FloatArray
    sleeve_excess: FloatArray
    bond_proxy: FloatArray
    french_rf: FloatArray
    reported_from: int
    findings: tuple[str, ...]
    provenance: tuple[JsonValue, ...]
    source_last_observations: tuple[tuple[str, str], ...]
    """Each input's own last month, BEFORE alignment clipped it to the holdout."""

    @property
    def reported_periods(self) -> tuple[str, ...]:
        return self.periods[self.reported_from :]


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_inputs(specification: Specification) -> PanelInputs:
    """Fetch, pin, parse and validate every input, then align them.

    A raw-hash mismatch on AQR or Ken French ABORTS. Both rebuild their entire
    history from the current vintage, so an unrecognised hash is a new vintage
    rather than a corrupted download, and a result computed from an unrecognised
    file looks exactly like a good one. FRED appends rather than rewrites, so its
    hash is reported without aborting.
    """
    parameters = _mapping(specification.parameters, where="parameters")
    pin = _mapping(_at(parameters, "source_pin", where="parameters"), where="source_pin")
    cache = RawCache()
    provenance: list[JsonValue] = []

    # --- AQR trend sleeve ---------------------------------------------------
    aqr_pin = _mapping(_at(pin, "aqr_tsmom", where="source_pin"), where="source_pin.aqr_tsmom")
    dataset = aqr.get_dataset(_text(aqr_pin, "dataset_id", where="source_pin.aqr_tsmom"))
    aqr_entry = aqr.download(cache, dataset)
    expected_raw = _text(aqr_pin, "expected_sha256_raw", where="source_pin.aqr_tsmom")
    if aqr_entry.sha256 != expected_raw:
        raise TrendMarginalValueError(
            f"the workbook at {dataset.url} now hashes to {aqr_entry.sha256}, but this "
            f"specification is frozen against {expected_raw}. AQR reconstructs the "
            "full history each time the returns are updated, so this is a new "
            "vintage, not a corrupted download. Freeze a new specification against "
            "it rather than reporting marginal utility from an unrecognised file."
        )
    aqr_file = aqr.parse(cache, aqr_entry, dataset=dataset)
    sheet = _text(aqr_pin, "sheet", where="source_pin.aqr_tsmom")
    if aqr_file.data_sheet != sheet:
        raise TrendMarginalValueError(
            f"the specification pins sheet {sheet!r} but the parser read "
            f"{aqr_file.data_sheet!r}"
        )
    aqr_report = validate_table(
        aqr_file.table,
        dataset_id="aqr_tsmom_factors_monthly",
        expected_columns=dataset.expected_columns,
        expected_frequency="monthly",
    )
    if not aqr_report.ok:
        raise TrendMarginalValueError(
            "the AQR table failed validation before any statistic was computed: "
            + "; ".join(aqr_report.summary())
        )
    expected_normalised = _text(
        aqr_pin, "expected_sha256_normalized", where="source_pin.aqr_tsmom"
    )
    if aqr_file.table.sha256_normalized() != expected_normalised:
        raise TrendMarginalValueError(
            f"the derived AQR table hashes to {aqr_file.table.sha256_normalized()}, "
            f"but the specification pins {expected_normalised}. The raw bytes "
            "matched, so the parser changed behaviour. That is a finding, not a "
            "hash to update."
        )
    sleeve_column = _text(aqr_pin, "column", where="source_pin.aqr_tsmom")
    sleeve = _series_from_table(
        aqr_file.table, sleeve_column, name="sleeve_excess", source=dataset.dataset_id
    )
    provenance.append(
        {
            "dataset_id": dataset.dataset_id,
            "source_url": aqr_entry.url,
            "workbook_sheet": aqr_file.data_sheet,
            "workbook_sheets_present": list(aqr_file.sheet_names),
            "column": sleeve_column,
            "sha256_raw": aqr_entry.sha256,
            "sha256_normalized": aqr_file.table.sha256_normalized(),
            "size_bytes": aqr_entry.size_bytes,
            "retrieved_utc": aqr_entry.retrieved_utc,
            "source_last_modified": aqr_entry.last_modified,
            "parser_version": aqr.PARSER_VERSION,
            "rows_in_file": aqr_file.table.rows,
            "first_observation": aqr_file.table.first_observation,
            "last_observation": aqr_file.table.last_observation,
            "units": aqr_file.table.units,
            "unit_transform": aqr_file.table.unit_transform,
            "preamble": aqr_file.preamble,
            "recovered_methodology_text": [
                {"part": part, "text": text} for part, text in aqr_file.narrative
            ],
            "validation_findings": list(aqr_report.summary()),
            "committed_manifest_sha256": _manifest_hash(
                aqr_pin, "committed_manifest", where="source_pin.aqr_tsmom"
            ),
        }
    )

    # --- Ken French US market ----------------------------------------------
    french_pin = _mapping(
        _at(pin, "french_us_market", where="source_pin"), where="source_pin.french_us_market"
    )
    french_dataset = french.get_dataset(
        _text(french_pin, "dataset_id", where="source_pin.french_us_market")
    )
    french_entry = french.download(cache, french_dataset)
    expected_french = _text(
        french_pin, "expected_sha256_raw", where="source_pin.french_us_market"
    )
    if french_entry.sha256 != expected_french:
        raise TrendMarginalValueError(
            f"the file at {french_dataset.url} now hashes to {french_entry.sha256}, "
            f"but this specification is frozen against {expected_french}. Ken French "
            "rebuilds the whole history from each new CRSP vintage, so this is a new "
            "vintage. Freeze a new specification against it."
        )
    french_file = french.parse(cache, french_entry, dataset=french_dataset)
    french_table = french_file.table(
        _text(french_pin, "table_id", where="source_pin.french_us_market")
    )
    french_report = validate_table(
        french_table,
        dataset_id="french_us_ff5_monthly",
        expected_columns=("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"),
        expected_frequency="monthly",
    )
    if not french_report.ok:
        raise TrendMarginalValueError(
            "the French table failed validation: " + "; ".join(french_report.summary())
        )
    market_excess = _series_from_table(
        french_table, "Mkt-RF", name="market_excess", source=french_dataset.dataset_id
    )
    french_rf = _series_from_table(
        french_table, "RF", name="french_rf", source=french_dataset.dataset_id
    )
    provenance.append(
        {
            "dataset_id": french_dataset.dataset_id,
            "source_url": french_entry.url,
            "table_id": french_table.table_id,
            "columns_used": ["Mkt-RF", "RF"],
            "construction": "equity total return = Mkt-RF + RF",
            "sha256_raw": french_entry.sha256,
            "sha256_normalized": french_table.sha256_normalized(),
            "retrieved_utc": french_entry.retrieved_utc,
            "source_last_modified": french_entry.last_modified,
            "parser_version": french.PARSER_VERSION,
            "rows_in_file": french_table.rows,
            "first_observation": french_table.first_observation,
            "last_observation": french_table.last_observation,
            "validation_findings": list(french_report.summary()),
            "committed_manifest_sha256": _manifest_hash(
                french_pin, "committed_manifest", where="source_pin.french_us_market"
            ),
        }
    )

    # --- FRED cash and the bond-proxy yield ---------------------------------
    cash_series_id = _text(parameters, "cash_series", where="parameters")
    cash_table, cash_record = _load_fred(cache, cash_series_id, pin, "fred_tb3ms")
    gs10_table, gs10_record = _load_fred(cache, "GS10", pin, "fred_gs10")
    provenance.extend((cash_record, gs10_record))

    cash_rate = _series_from_table(cash_table, cash_series_id, name="cash_rate", source="FRED")
    gs10 = _series_from_table(gs10_table, "GS10", name="gs10", source="FRED")

    # --- Alignment ----------------------------------------------------------
    burn_in_start = "1985-01"
    sample_start = specification.sample_policy.start
    sample_end = specification.sample_policy.end
    raw_series = {
        "market_excess": market_excess,
        "french_rf": french_rf,
        "sleeve_excess": sleeve,
        "cash_rate": cash_rate,
        "gs10": gs10,
    }
    periods, columns, alignment = _aligned(
        raw_series, start=burn_in_start, end=sample_end
    )
    if sample_start not in periods:
        raise TrendMarginalValueError(
            f"the frozen sample start {sample_start} is not on the aligned grid "
            f"{periods[:3]}..{periods[-3:]}"
        )
    reported_from = periods.index(sample_start)
    findings = list(alignment)
    if reported_from < 24:
        findings.append(
            f"only {reported_from} months of estimator burn-in are available before "
            f"{sample_start}; the volatility estimator will be NaN at the start of "
            "the reported window."
        )

    cash_monthly = columns["cash_rate"] / MONTHS_PER_YEAR
    equity_total = columns["market_excess"] + columns["french_rf"]
    bond = bond_total_return_from_yield(columns["gs10"])
    return PanelInputs(
        periods=periods,
        equity_total=equity_total,
        equity_excess=equity_total - cash_monthly,
        cash=cash_monthly,
        sleeve_excess=columns["sleeve_excess"],
        bond_proxy=bond,
        french_rf=columns["french_rf"],
        reported_from=reported_from,
        findings=tuple(findings),
        provenance=tuple(provenance),
        source_last_observations=tuple(
            (name, item.periods[-1] if item.periods else "")
            for name, item in sorted(raw_series.items())
        ),
    )


def _load_fred(
    cache: RawCache, series_id: str, pin: Mapping[str, JsonValue], pin_key: str
) -> tuple[ParsedTable, JsonValue]:
    entry = fred.download(cache, series_id)
    table = fred.parse(cache, entry, series_id)
    report = validate_table(
        table, dataset_id=f"fred_{series_id.lower()}", expected_columns=(series_id,)
    )
    if not report.ok:
        raise TrendMarginalValueError(
            f"the FRED {series_id} table failed validation: " + "; ".join(report.summary())
        )
    declared = pin.get(pin_key)
    expected = ""
    if isinstance(declared, Mapping):
        candidate = declared.get("expected_sha256_raw")
        expected = candidate if isinstance(candidate, str) else ""
    record: JsonValue = {
        "dataset_id": f"fred_{series_id.lower()}",
        "source_url": entry.url,
        "sha256_raw": entry.sha256,
        "sha256_raw_pinned": expected,
        "sha256_matches_pin": entry.sha256 == expected,
        "abort_on_mismatch": False,
        "why_no_abort": (
            "FRED appends observations rather than rewriting history, so the file "
            "hash changes on every release. The hash is recorded and reported; only "
            "the two sources that rebuild their history in place abort on a "
            "mismatch."
        ),
        "sha256_normalized": table.sha256_normalized(),
        "retrieved_utc": entry.retrieved_utc,
        "parser_version": fred.PARSER_VERSION,
        "rows_in_file": table.rows,
        "first_observation": table.first_observation,
        "last_observation": table.last_observation,
        "units": table.units,
        "validation_findings": list(report.summary()),
        "committed_manifest_sha256": (
            _manifest_hash(declared, "committed_manifest", where=f"source_pin.{pin_key}")
            if isinstance(declared, Mapping)
            else None
        ),
    }
    return table, record


def _manifest_hash(
    data: Mapping[str, JsonValue], key: str, *, where: str
) -> str | None:
    location = data.get(key)
    if not isinstance(location, str):
        return None
    path = _workspace_root() / location
    if not path.is_file():
        return None
    return read_manifest(path).sha256_manifest()


# --------------------------------------------------------------------------- #
# Cost columns
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class CostColumn:
    """One frozen cost assumption, applied identically to all five portfolios."""

    basis: CostBasis
    one_way_bps: float
    management_fee_annual: float
    performance_fee_rate: float

    def sleeve_net(self, sleeve_total: FloatArray) -> tuple[FloatArray, float]:
        """Apply the sleeve's investor-level fees, management first then performance."""
        after_management = sleeve_total - self.management_fee_annual / MONTHS_PER_YEAR
        if self.performance_fee_rate <= 0.0:
            return after_management, 0.0
        return high_water_mark_performance_fee(
            after_management, rate=self.performance_fee_rate
        )

    def doubled(self) -> CostColumn:
        """Every cost and fee assumption doubled, for the hostile test."""
        return CostColumn(
            basis=self.basis,
            one_way_bps=2.0 * self.one_way_bps,
            management_fee_annual=2.0 * self.management_fee_annual,
            performance_fee_rate=min(2.0 * self.performance_fee_rate, 0.99),
        )


def _cost_columns(specification: Specification) -> tuple[CostColumn, ...]:
    model = _mapping(specification.cost_model, where="cost_model")
    investor = _mapping(_at(model, "investor_level_costs", where="cost_model"), where="costs")
    spread = _mapping(_at(model, "spread_and_commission", where="cost_model"), where="spread")
    optimistic = _mapping(_at(investor, "net_optimistic", where="costs"), where="net_optimistic")
    pessimistic = _mapping(
        _at(investor, "net_pessimistic", where="costs"), where="net_pessimistic"
    )
    return (
        CostColumn(
            basis=CostBasis.GROSS,
            one_way_bps=0.0,
            management_fee_annual=0.0,
            performance_fee_rate=0.0,
        ),
        CostColumn(
            basis=CostBasis.NET_OPTIMISTIC,
            one_way_bps=_number(
                _mapping(_at(spread, "net_optimistic", where="spread"), where="spread"),
                "one_way_bps",
                where="spread.net_optimistic",
            ),
            management_fee_annual=_number(
                optimistic, "management_fee_annual_percent", where="net_optimistic"
            )
            / 100.0,
            performance_fee_rate=0.0,
        ),
        CostColumn(
            basis=CostBasis.NET_PESSIMISTIC,
            one_way_bps=_number(
                _mapping(_at(spread, "net_pessimistic", where="spread"), where="spread"),
                "one_way_bps",
                where="spread.net_pessimistic",
            ),
            management_fee_annual=_number(
                pessimistic, "management_fee_annual_percent", where="net_pessimistic"
            )
            / 100.0,
            performance_fee_rate=_number(
                pessimistic, "performance_fee_percent_of_gains", where="net_pessimistic"
            )
            / 100.0,
        ),
    )


# --------------------------------------------------------------------------- #
# Portfolio construction
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioPath:
    """One comparison portfolio's realised monthly path over the reported window."""

    portfolio_id: str
    basis: CostBasis
    periods: tuple[str, ...]
    returns: FloatArray
    weights: FloatArray
    turnover: FloatArray
    trading_cost: FloatArray

    @property
    def observations(self) -> int:
        return self.returns.size


def _run_weights(
    weights: FloatArray,
    asset_returns: FloatArray,
    *,
    one_way_bps: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Realise a weight path against asset returns, charging spread on each trade.

    ``weights[t]`` is the target weight vector held through month ``t``. The trade
    at ``t`` is the distance from the weights the previous month drifted to, so a
    portfolio whose targets never move still pays for the drift it corrects. The
    initial purchase is not charged: every portfolio starts from the same cash and
    charging an identical entry cost to all five cannot change a difference between
    them.
    """
    periods, assets = weights.shape
    if asset_returns.shape != (periods, assets):
        raise ValueError("weights and asset_returns must have the same shape")
    portfolio = np.empty(periods, dtype=np.float64)
    turnover = np.zeros(periods, dtype=np.float64)
    cost = np.zeros(periods, dtype=np.float64)
    drifted = weights[0].copy()
    for index in range(periods):
        target = weights[index]
        traded = float(np.sum(np.abs(target - drifted)))
        turnover[index] = 0.5 * traded
        cost[index] = traded * one_way_bps / 1e4
        gross = float(np.dot(target, asset_returns[index]))
        portfolio[index] = gross - cost[index]
        grown = target * (1.0 + asset_returns[index])
        total = float(np.sum(grown))
        drifted = grown / total if total > 0.0 else target.copy()
    return portfolio, turnover, cost


@dataclass(frozen=True, slots=True, kw_only=True)
class Scenario:
    """One fully specified way of building the five portfolios.

    Everything a hostile test varies lives here, so a hostile test is a different
    ``Scenario`` rather than a different code path. That is deliberate: a test that
    ran through its own branch could differ from the headline result for reasons
    nobody intended.
    """

    name: str
    sleeve_excess: FloatArray
    centre_of_mass_months: float
    exposure_cap: float
    sleeve_weight: float
    equity_weight: float
    use_bond_leg: bool = False


def _build_portfolios(
    inputs: PanelInputs, scenario: Scenario, column: CostColumn
) -> dict[str, PortfolioPath]:
    """Build all five comparison portfolios under one scenario and one cost column."""
    cash = inputs.cash
    equity = inputs.equity_total
    if scenario.use_bond_leg:
        bond = inputs.bond_proxy
        risky = np.where(np.isnan(bond), equity, 0.75 * equity + 0.25 * bond)
    else:
        risky = equity

    sleeve_total = scenario.sleeve_excess + cash
    sleeve_net, _ = column.sleeve_net(sleeve_total)
    assets = np.column_stack([risky, cash, sleeve_net])

    equity_weight = scenario.equity_weight
    cash_weight = 1.0 - equity_weight
    periods = inputs.periods
    n = len(periods)

    passive_returns = equity_weight * risky + cash_weight * cash
    passive_volatility = ewma_annualised_volatility(
        passive_returns, centre_of_mass_months=scenario.centre_of_mass_months
    )
    sleeve_volatility = ewma_annualised_volatility(
        sleeve_net, centre_of_mass_months=scenario.centre_of_mass_months
    )
    covariance = ewma_annualised_covariance(
        passive_returns, sleeve_net, centre_of_mass_months=scenario.centre_of_mass_months
    )
    target = expanding_annualised_volatility(passive_returns)

    weight = scenario.sleeve_weight
    combined_variance = (
        (1.0 - weight) ** 2 * passive_volatility**2
        + weight**2 * sleeve_volatility**2
        + 2.0 * weight * (1.0 - weight) * covariance
    )
    combined_volatility = np.sqrt(np.maximum(combined_variance, 0.0))

    with np.errstate(divide="ignore", invalid="ignore"):
        scaled_exposure = np.clip(target / passive_volatility, 0.0, scenario.exposure_cap)
        matched_exposure = np.clip(
            combined_volatility / passive_volatility, 0.0, scenario.exposure_cap
        )
    scaled_exposure = np.nan_to_num(scaled_exposure, nan=1.0)
    matched_exposure = np.nan_to_num(matched_exposure, nan=1.0)

    def two_asset(exposure: FloatArray) -> FloatArray:
        equity_leg = equity_weight * exposure
        return np.column_stack([equity_leg, 1.0 - equity_leg, np.zeros(n)])

    weight_paths: dict[str, FloatArray] = {
        "passive_benchmark": two_asset(np.ones(n)),
        "volatility_scaled_passive": two_asset(scaled_exposure),
        "trend_alone": np.column_stack([np.zeros(n), np.zeros(n), np.ones(n)]),
        "passive_plus_trend": np.column_stack(
            [
                np.full(n, (1.0 - weight) * equity_weight),
                np.full(n, (1.0 - weight) * cash_weight),
                np.full(n, weight),
            ]
        ),
        "passive_plus_cash": two_asset(matched_exposure),
    }

    out: dict[str, PortfolioPath] = {}
    start = inputs.reported_from
    for portfolio_id, path in weight_paths.items():
        returns, turnover, cost = _run_weights(
            path, assets, one_way_bps=column.one_way_bps
        )
        out[portfolio_id] = PortfolioPath(
            portfolio_id=portfolio_id,
            basis=column.basis,
            periods=periods[start:],
            returns=returns[start:],
            weights=path[start:],
            turnover=turnover[start:],
            trading_cost=cost[start:],
        )
    return out


# --------------------------------------------------------------------------- #
# Statistics on a path
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PathStatistics:
    """Everything reported for one portfolio over one window."""

    portfolio_id: str
    basis: CostBasis
    window: str
    observations: int
    certainty_equivalent_percent: float | None
    geometric_annual_percent: float
    arithmetic_annual_percent: float
    annualised_volatility_percent: float
    sharpe_annualised: float
    max_drawdown_percent: float
    expected_shortfall_percent: float | None
    expected_shortfall_note: str
    downside_beta: float | None
    correlation_to_passive: float | None
    mean_turnover_percent: float
    total_trading_cost_percent_per_year: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "portfolio": self.portfolio_id,
            "cost_basis": self.basis.value,
            "window": self.window,
            "observations": self.observations,
            "certainty_equivalent_percent_per_year": self.certainty_equivalent_percent,
            "geometric_annual_percent": self.geometric_annual_percent,
            "arithmetic_annual_percent": self.arithmetic_annual_percent,
            "annualised_volatility_percent": self.annualised_volatility_percent,
            "sharpe_annualised": _json_float(self.sharpe_annualised),
            "max_drawdown_percent": self.max_drawdown_percent,
            "expected_shortfall_5pct_percent_per_month": self.expected_shortfall_percent,
            "expected_shortfall_note": self.expected_shortfall_note,
            "downside_beta_to_passive": self.downside_beta,
            "correlation_to_passive": self.correlation_to_passive,
            "mean_one_sided_monthly_turnover_percent": self.mean_turnover_percent,
            "trading_cost_percent_per_year": self.total_trading_cost_percent_per_year,
        }


def _path_statistics(
    path: PortfolioPath,
    *,
    window: str,
    mask: NDArray[np.bool_],
    cash: FloatArray,
    passive_returns: FloatArray,
    gamma: float,
) -> PathStatistics:
    returns = path.returns[mask]
    observations = returns.size
    if observations == 0:
        raise TrendMarginalValueError(f"{path.portfolio_id}/{window} selected no months")

    certainty: float | None = None
    if observations % MONTHS_PER_YEAR == 0 and observations >= MONTHS_PER_YEAR:
        certainty = 100.0 * certainty_equivalent_annual(
            _annual_gross_matrix(returns), gamma=gamma
        )

    geometric = (1.0 + geometric_mean(returns)) ** MONTHS_PER_YEAR - 1.0
    volatility = float(np.std(returns, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    equity_curve = np.cumprod(1.0 + returns)
    drawdown = drawdown_summary(equity_curve)

    try:
        sharpe = sharpe_ratio(
            returns, frequency=Frequency.MONTHLY, risk_free=cash[mask]
        ).annualised_sharpe
    except ValueError:
        sharpe = float("nan")

    shortfall: float | None = None
    shortfall_note = ""
    try:
        shortfall = 100.0 * historical_expected_shortfall(returns, alpha=0.05).expected_shortfall
    except InsufficientTailDataError as exc:
        shortfall_note = str(exc)

    benchmark = passive_returns[mask]
    correlation: float | None = None
    downside: float | None = None
    if observations >= 3 and float(np.std(benchmark)) > 0.0 and float(np.std(returns)) > 0.0:
        correlation = float(np.corrcoef(returns, benchmark)[0, 1])
        down = benchmark < 0.0
        if int(np.count_nonzero(down)) >= 3 and float(np.std(benchmark[down])) > 0.0:
            downside = float(
                np.cov(returns[down], benchmark[down], ddof=1)[0, 1]
                / np.var(benchmark[down], ddof=1)
            )

    return PathStatistics(
        portfolio_id=path.portfolio_id,
        basis=path.basis,
        window=window,
        observations=observations,
        certainty_equivalent_percent=certainty,
        geometric_annual_percent=100.0 * geometric,
        arithmetic_annual_percent=100.0 * float(np.mean(returns)) * MONTHS_PER_YEAR,
        annualised_volatility_percent=100.0 * volatility,
        sharpe_annualised=sharpe,
        max_drawdown_percent=100.0 * drawdown.max_drawdown,
        expected_shortfall_percent=shortfall,
        expected_shortfall_note=shortfall_note,
        downside_beta=downside,
        correlation_to_passive=correlation,
        mean_turnover_percent=100.0 * float(np.mean(path.turnover[mask])),
        total_trading_cost_percent_per_year=(
            100.0 * float(np.mean(path.trading_cost[mask])) * MONTHS_PER_YEAR
        ),
    )


# --------------------------------------------------------------------------- #
# Marginal utility and its uncertainty
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class MarginalResult:
    """One paired marginal comparison, with its bootstrap interval."""

    label: str
    treatment: str
    comparator: str
    basis: CostBasis
    window: str
    observations: int
    effective_blocks: float
    marginal_percent: float
    lower_95: float
    upper_95: float
    lower_90: float
    upper_90: float
    one_sided_p_value: float
    block_length: float
    neighbours: tuple[tuple[float, float, float], ...]

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "comparison": self.label,
            "treatment_portfolio": self.treatment,
            "comparator_portfolio": self.comparator,
            "cost_basis": self.basis.value,
            "window": self.window,
            "observations": self.observations,
            "effective_independent_blocks": self.effective_blocks,
            "marginal_percentage_points_per_year": self.marginal_percent,
            "two_sided_95": [self.lower_95, self.upper_95],
            "two_sided_90": [self.lower_90, self.upper_90],
            "one_sided_p_value_marginal_is_positive": self.one_sided_p_value,
            "block_length_months": self.block_length,
            "neighbour_block_intervals": [
                {"block_length": length, "two_sided_95": [low, high]}
                for length, low, high in self.neighbours
            ],
        }


def _paired_bootstrap(
    treatment: FloatArray,
    comparator: FloatArray,
    *,
    rng: np.random.Generator,
    block_length: float,
    n_resamples: int,
    gamma: float,
    chunk: int = 2000,
) -> FloatArray:
    """Resample the joint panel and recompute the paired difference on every draw.

    The two series are resampled with the SAME indices. Resampling them
    independently would destroy the pairing and produce an interval for the
    difference of two unrelated portfolios, which is a much wider and entirely
    different statement.
    """
    n = treatment.size
    replicates = np.empty(n_resamples, dtype=np.float64)
    done = 0
    while done < n_resamples:
        size = min(chunk, n_resamples - done)
        indices = stationary_bootstrap_indices(n, block_length, size, rng)
        left = _certainty_equivalent_rows(treatment[indices], gamma=gamma)
        right = _certainty_equivalent_rows(comparator[indices], gamma=gamma)
        replicates[done : done + size] = 100.0 * (left - right)
        done += size
    return replicates


def _marginal(
    treatment: PortfolioPath,
    comparator: PortfolioPath,
    *,
    label: str,
    window: str,
    mask: NDArray[np.bool_],
    rng: np.random.Generator,
    gamma: float,
    block_length: float,
    neighbours: Sequence[float],
    n_resamples: int,
) -> MarginalResult:
    left = treatment.returns[mask]
    right = comparator.returns[mask]
    observations = left.size
    point = 100.0 * (
        certainty_equivalent_annual(_annual_gross_matrix(left), gamma=gamma)
        - certainty_equivalent_annual(_annual_gross_matrix(right), gamma=gamma)
    )
    replicates = _paired_bootstrap(
        left,
        right,
        rng=rng,
        block_length=block_length,
        n_resamples=n_resamples,
        gamma=gamma,
    )
    quantiles = np.quantile(replicates, [0.025, 0.975, 0.05, 0.95])
    neighbour_intervals: list[tuple[float, float, float]] = []
    for length in neighbours:
        draws = _paired_bootstrap(
            left,
            right,
            rng=rng,
            block_length=length,
            n_resamples=max(2000, n_resamples // 5),
            gamma=gamma,
        )
        low, high = np.quantile(draws, [0.025, 0.975])
        neighbour_intervals.append((float(length), float(low), float(high)))
    return MarginalResult(
        label=label,
        treatment=treatment.portfolio_id,
        comparator=comparator.portfolio_id,
        basis=treatment.basis,
        window=window,
        observations=observations,
        effective_blocks=observations / block_length,
        marginal_percent=point,
        lower_95=float(quantiles[0]),
        upper_95=float(quantiles[1]),
        lower_90=float(quantiles[2]),
        upper_90=float(quantiles[3]),
        one_sided_p_value=float(np.mean(replicates <= 0.0)),
        block_length=block_length,
        neighbours=tuple(neighbour_intervals),
    )


# --------------------------------------------------------------------------- #
# Windows
# --------------------------------------------------------------------------- #


def _mask_for(periods: Sequence[str], start: str, end: str) -> NDArray[np.bool_]:
    low, high = month_index(start), month_index(end)
    return np.asarray([low <= month_index(period) <= high for period in periods], dtype=bool)


def _crisis_windows(specification: Specification) -> tuple[tuple[str, str, str], ...]:
    parameters = _mapping(specification.parameters, where="parameters")
    items = _sequence(_at(parameters, "crisis_windows", where="parameters"), where="crisis")
    out: list[tuple[str, str, str]] = []
    for index, item in enumerate(items):
        entry = _mapping(item, where=f"crisis_windows[{index}]")
        out.append(
            (
                _text(entry, "name", where=f"crisis_windows[{index}]"),
                _text(entry, "start", where=f"crisis_windows[{index}]"),
                _text(entry, "end", where=f"crisis_windows[{index}]"),
            )
        )
    return tuple(out)


def _crisis_union_mask(
    periods: Sequence[str], windows: Sequence[tuple[str, str, str]]
) -> NDArray[np.bool_]:
    mask = np.zeros(len(periods), dtype=bool)
    for _, start, end in windows:
        mask |= _mask_for(periods, start, end)
    return mask


def _whole_year_mask(periods: Sequence[str], start: str, end: str) -> NDArray[np.bool_]:
    """A window mask that a calendar-year certainty equivalent can consume.

    Returns the mask only when the window is a whole number of complete calendar
    years aligned to January; otherwise the caller must fall back to a compounded
    window return, because chopping a partial year would silently drop months.
    """
    mask = _mask_for(periods, start, end)
    count = int(np.count_nonzero(mask))
    aligned = start.endswith("-01") and end.endswith("-12")
    if aligned and count % MONTHS_PER_YEAR == 0:
        return mask
    return np.zeros(len(periods), dtype=bool)


# --------------------------------------------------------------------------- #
# Attribution
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Attribution:
    """The sleeve regressed on static and time-varying market exposures."""

    names: tuple[str, ...]
    coefficients: tuple[float, ...]
    t_statistics: tuple[float, ...]
    p_values: tuple[float, ...]
    r_squared: float
    annualised_alpha_percent: float
    alpha_t_statistic: float
    fitted: FloatArray
    residuals: FloatArray
    n_lags: int
    observations: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "regressors": list(self.names),
            "coefficients": list(self.coefficients),
            "hac_t_statistics": list(self.t_statistics),
            "hac_p_values": list(self.p_values),
            "r_squared": self.r_squared,
            "annualised_alpha_percent": self.annualised_alpha_percent,
            "alpha_hac_t_statistic": self.alpha_t_statistic,
            "newey_west_lags": self.n_lags,
            "observations": self.observations,
        }


def _attribute(
    sleeve_excess: FloatArray,
    *,
    equity_excess: FloatArray,
    scaled_equity_excess: FloatArray,
) -> Attribution:
    """Regress the sleeve on the exposures Goyal and Jegadeesh say reproduce it.

    The design is a constant, a static market position, a volatility-scaled market
    position, the absolute market return as a convexity proxy, and the lagged
    market return for the slow signal. The first observation is dropped because the
    lag consumes it.
    """
    design = np.column_stack(
        [
            equity_excess[1:],
            scaled_equity_excess[1:],
            np.abs(equity_excess[1:]),
            equity_excess[:-1],
        ]
    )
    response = sleeve_excess[1:]
    if np.linalg.matrix_rank(np.column_stack([np.ones(response.size), design])) < 5:
        raise TrendMarginalValueError(
            "the attribution design is collinear: the static and volatility-scaled "
            "market legs carry no independent variation, so the decisive "
            "Goyal-Jegadeesh test cannot separate them. Refusing rather than "
            "reporting whichever split a pseudo-inverse happened to pick."
        )
    result = hac_ols(response, design, n_lags=newey_west_lag_count(response.size))
    fitted = np.concatenate(([np.nan], response - result.residuals))
    residuals = np.concatenate(([np.nan], result.residuals))
    total = float(np.sum((response - float(np.mean(response))) ** 2))
    explained = 1.0 - float(np.sum(result.residuals**2)) / total if total > 0.0 else float("nan")
    return Attribution(
        names=(
            "constant",
            "market_excess_return",
            "volatility_scaled_market_excess_return",
            "absolute_market_excess_return",
            "lagged_market_excess_return",
        ),
        coefficients=tuple(float(value) for value in result.coefficients),
        t_statistics=tuple(float(value) for value in result.t_statistics),
        p_values=tuple(float(value) for value in result.p_values),
        r_squared=explained,
        annualised_alpha_percent=100.0 * float(result.coefficients[0]) * MONTHS_PER_YEAR,
        alpha_t_statistic=float(result.t_statistics[0]),
        fitted=fitted,
        residuals=residuals,
        n_lags=result.n_lags,
        observations=response.size,
    )


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Settings:
    """Everything the frozen specification says about how to run this."""

    gamma: float
    materiality: float
    sleeve_weight: float
    equity_weight: float
    exposure_cap: float
    exposure_cap_half: float
    lookback_days: float
    lookback_alternatives_days: tuple[float, ...]
    block_length: float
    neighbours: tuple[float, ...]
    resamples: int


def _settings(specification: Specification) -> Settings:
    parameters = _mapping(specification.parameters, where="parameters")
    return Settings(
        gamma=_number(parameters, "crra_gamma", where="parameters"),
        materiality=_number(
            parameters, "materiality_threshold_annual_percent", where="parameters"
        ),
        sleeve_weight=_number(parameters, "sleeve_weight", where="parameters"),
        equity_weight=_number(parameters, "equity_weight", where="parameters"),
        exposure_cap=_number(parameters, "exposure_cap", where="parameters"),
        exposure_cap_half=_number(parameters, "exposure_cap_half", where="parameters"),
        lookback_days=_number(parameters, "volatility_lookback_days", where="parameters"),
        lookback_alternatives_days=_numbers(
            parameters, "volatility_lookback_alternatives_days", where="parameters"
        ),
        block_length=12.0,
        neighbours=(6.0, 24.0),
        resamples=specification.inference.resamples,
    )


def _centre_of_mass(days: float) -> float:
    """Translate the vendor's daily centre of mass to the monthly frequency available."""
    return days / TRADING_DAYS_PER_MONTH


def _base_scenario(inputs: PanelInputs, settings: Settings, *, name: str) -> Scenario:
    return Scenario(
        name=name,
        sleeve_excess=inputs.sleeve_excess,
        centre_of_mass_months=_centre_of_mass(settings.lookback_days),
        exposure_cap=settings.exposure_cap,
        sleeve_weight=settings.sleeve_weight,
        equity_weight=settings.equity_weight,
    )


def _marginal_point(
    portfolios: Mapping[str, PortfolioPath],
    *,
    mask: NDArray[np.bool_],
    gamma: float,
) -> float:
    """The headline marginal number without its interval, for the hostile grid."""
    treatment = portfolios["passive_plus_trend"].returns[mask]
    comparator = portfolios["passive_plus_cash"].returns[mask]
    return 100.0 * (
        certainty_equivalent_annual(_annual_gross_matrix(treatment), gamma=gamma)
        - certainty_equivalent_annual(_annual_gross_matrix(comparator), gamma=gamma)
    )


def _windows(
    specification: Specification, periods: Sequence[str]
) -> Iterator[tuple[str, NDArray[np.bool_], bool]]:
    """Every reported window: the eras, then the crisis union."""
    for era in specification.sample_policy.eras:
        if era.name == "crisis_conditional":
            continue
        mask = _whole_year_mask(periods, era.start, era.end)
        if not bool(mask.any()):
            mask = _mask_for(periods, era.start, era.end)
            yield (era.name, mask, False)
        else:
            yield (era.name, mask, True)
    yield ("crisis_union", _crisis_union_mask(periods, _crisis_windows(specification)), False)


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 004."""
    settings = _settings(specification)
    rng = context.rng
    inputs = _load_inputs(specification)
    periods = inputs.reported_periods
    cash = inputs.cash[inputs.reported_from :]
    equity_excess = inputs.equity_excess[inputs.reported_from :]
    columns = _cost_columns(specification)
    default_column = columns[-1]

    base = _base_scenario(inputs, settings, name="frozen")
    by_basis = {
        column.basis: _build_portfolios(inputs, base, column) for column in columns
    }
    headline = by_basis[default_column.basis]

    # --- descriptive statistics, every portfolio x window x cost basis -------
    statistics: list[PathStatistics] = []
    window_list = list(_windows(specification, periods))
    for column in columns:
        portfolios = by_basis[column.basis]
        benchmark = portfolios["passive_benchmark"].returns
        for window_name, mask, _ in window_list:
            for portfolio_id in COMPARISON_IDS:
                statistics.append(
                    _path_statistics(
                        portfolios[portfolio_id],
                        window=window_name,
                        mask=mask,
                        cash=cash,
                        passive_returns=benchmark,
                        gamma=settings.gamma,
                    )
                )

    # --- the primary marginal comparison and its family ---------------------
    full_mask = _whole_year_mask(periods, specification.sample_policy.start,
                                 specification.sample_policy.end)
    if not bool(full_mask.any()):
        raise TrendMarginalValueError(
            "the frozen sample is not a whole number of calendar years, so the "
            "certainty equivalent cannot be computed without dropping months"
        )

    marginals: list[MarginalResult] = []
    for portfolio_id in COMPARISON_IDS:
        if portfolio_id == "passive_plus_cash":
            continue
        marginals.append(
            _marginal(
                headline[portfolio_id],
                headline["passive_plus_cash"],
                label=f"{portfolio_id} minus risk-matched cash, full period",
                window="full_period",
                mask=full_mask,
                rng=rng,
                gamma=settings.gamma,
                block_length=settings.block_length,
                neighbours=settings.neighbours,
                n_resamples=settings.resamples,
            )
        )
    era_masks = {
        era.name: _whole_year_mask(periods, era.start, era.end)
        for era in specification.sample_policy.eras
        if era.name in {"pre_publication", "post_publication", "reconstructed_history"}
    }
    for era_name, mask in era_masks.items():
        if not bool(mask.any()):
            continue
        marginals.append(
            _marginal(
                headline["passive_plus_trend"],
                headline["passive_plus_cash"],
                label=f"passive_plus_trend minus risk-matched cash, {era_name}",
                window=era_name,
                mask=mask,
                rng=rng,
                gamma=settings.gamma,
                block_length=settings.block_length,
                neighbours=settings.neighbours,
                n_resamples=settings.resamples,
            )
        )
    primary = marginals[COMPARISON_IDS.index("passive_plus_trend")]

    holm = holm_bonferroni([item.one_sided_p_value for item in marginals], alpha=0.05)

    # --- crisis-conditional -------------------------------------------------
    crises = _crisis_windows(specification)
    crisis_rows = _crisis_table(headline, crises, periods=periods, columns=columns,
                                by_basis=by_basis)

    # --- attribution --------------------------------------------------------
    scaled_equity = _scaled_equity_excess(inputs, settings)
    attribution = _attribute(
        inputs.sleeve_excess[inputs.reported_from :],
        equity_excess=equity_excess,
        scaled_equity_excess=scaled_equity[inputs.reported_from :],
    )

    # --- hostile tests ------------------------------------------------------
    hostile = _hostile_tests(
        specification,
        inputs,
        settings,
        columns=columns,
        base=base,
        baseline=primary.marginal_percent,
        full_mask=full_mask,
        periods=periods,
        crises=crises,
        attribution=attribution,
        scaled_equity=scaled_equity,
        rng=rng,
    )

    verdict = _apply_rejection_rule(
        primary=primary,
        settings=settings,
        hostile=hostile,
        era_marginals={item.window: item for item in marginals},
    )

    diagnostics: dict[str, JsonValue] = {
        "evaluation_disclosure": _disclosure(specification),
        "sources": list(inputs.provenance),
        "alignment_findings": list(inputs.findings),
        "sample": {
            "burn_in_first_month": inputs.periods[0],
            "reported_first_month": periods[0],
            "reported_last_month": periods[-1],
            "reported_months": len(periods),
            "burn_in_months": inputs.reported_from,
            "months_available_beyond_the_holdout": _beyond_holdout(inputs, specification),
        },
        "cost_columns": [
            {
                "basis": column.basis.value,
                "one_way_bps_on_portfolio_trades": column.one_way_bps,
                "sleeve_management_fee_annual_percent": 100.0 * column.management_fee_annual,
                "sleeve_performance_fee_percent_of_gains_over_high_water_mark": (
                    100.0 * column.performance_fee_rate
                ),
            }
            for column in columns
        ],
        "portfolio_statistics": [item.to_json() for item in statistics],
        "marginal_results": [item.to_json() for item in marginals],
        "multiple_testing": {
            "method": holm.method,
            "alpha": holm.alpha,
            "family_size": len(marginals),
            "rows": [
                {
                    "comparison": item.label,
                    "p_uncorrected": item.one_sided_p_value,
                    "holm_adjusted_p": float(adjusted),
                    "holm_rejected": bool(rejected),
                }
                for item, adjusted, rejected in zip(
                    marginals, holm.adjusted_p_values, holm.rejected, strict=True
                )
            ],
            "dependence_warning": (
                "These comparisons all share the same passive benchmark, the same "
                "sleeve and overlapping windows, so they are strongly dependent. "
                "Holm is valid under arbitrary dependence, which is why it was "
                "chosen, but the family is far smaller than the number of numbers "
                "in this report and correcting only these seven is a LOWER bound on "
                "the correction the whole search would require."
            ),
        },
        "crisis_conditional": crisis_rows,
        "attribution": {
            **attribution.to_json(),
            "interpretation": _attribution_note(attribution),
        },
        "hostile_tests": hostile,
        "verdict": verdict,
        "unavailable_tests": _unavailable_tests(),
    }

    estimates = _estimates(primary, marginals, statistics, settings)
    return ExperimentResult(
        status=ResultStatus(str(verdict["status"])),
        summary=str(verdict["summary"]),
        estimates=estimates,
        diagnostics=diagnostics,
        caveats=_caveats(inputs, attribution),
        frames=_frames(statistics, marginals, crisis_rows),
    )


def _scaled_equity_excess(inputs: PanelInputs, settings: Settings) -> FloatArray:
    """A volatility-scaled long equity position, the Goyal-Jegadeesh comparison leg."""
    volatility = ewma_annualised_volatility(
        inputs.equity_excess, centre_of_mass_months=_centre_of_mass(settings.lookback_days)
    )
    target = expanding_annualised_volatility(inputs.equity_excess)
    with np.errstate(divide="ignore", invalid="ignore"):
        exposure = np.clip(target / volatility, 0.0, settings.exposure_cap)
    return np.nan_to_num(exposure, nan=1.0) * inputs.equity_excess


def _beyond_holdout(inputs: PanelInputs, specification: Specification) -> JsonValue:
    """How much data each source holds past the boundary, and is never read.

    Measured on each input's OWN last observation, before alignment clipped the
    grid, because the aligned grid stops at the boundary by construction and would
    otherwise always report zero.
    """
    end = specification.sample_policy.end
    per_source = {
        name: max(0, month_count(end, last) - 1) if last else 0
        for name, last in inputs.source_last_observations
    }
    return {
        "sample_end": end,
        "note": (
            "The archived AQR workbook reaches beyond the frozen sample end. Those "
            "months were clipped before any statistic was computed and are not read "
            "by this experiment under any circumstance."
        ),
        "aligned_grid_last_month": inputs.periods[-1],
        "source_last_observations": dict(inputs.source_last_observations),
        "months_beyond_the_holdout_by_source": per_source,
        "months_clipped": max(per_source.values()) if per_source else 0,
    }


def _disclosure(specification: Specification) -> JsonValue:
    parameters = _mapping(specification.parameters, where="parameters")
    return _at(parameters, "evaluation_disclosure", where="parameters")


def _crisis_table(
    headline: Mapping[str, PortfolioPath],
    crises: Sequence[tuple[str, str, str]],
    *,
    periods: Sequence[str],
    columns: Sequence[CostColumn],
    by_basis: Mapping[CostBasis, Mapping[str, PortfolioPath]],
) -> JsonValue:
    """Per-crisis compounded outcomes and the marginal difference inside each window.

    A certainty equivalent needs whole calendar years and no crisis window is one,
    so the crisis metric is the compounded window return and the within-window
    drawdown. Both are reported beside the number of months they rest on, because
    a two-month window is a description of two months.
    """
    rows: list[JsonValue] = []
    union = np.zeros(len(periods), dtype=bool)
    for name, start, end in crises:
        mask = _mask_for(periods, start, end)
        union |= mask
        observations = int(np.count_nonzero(mask))
        entry: dict[str, JsonValue] = {
            "crisis": name,
            "window": f"{start}..{end}",
            "observations": observations,
            "effective_independent_blocks_at_12m": observations / 12.0,
        }
        if observations == 0:
            entry["note"] = "no months of this window fall inside the reported sample"
            rows.append(entry)
            continue
        for column in columns:
            portfolios = by_basis[column.basis]
            per_portfolio = {
                portfolio_id: 100.0 * compound_simple(portfolios[portfolio_id].returns[mask])
                for portfolio_id in COMPARISON_IDS
            }
            treatment = portfolios["passive_plus_trend"].returns[mask]
            comparator = portfolios["passive_plus_cash"].returns[mask]
            entry[column.basis.value] = {
                "window_compound_return_percent": per_portfolio,
                "marginal_window_return_percentage_points": (
                    per_portfolio["passive_plus_trend"] - per_portfolio["passive_plus_cash"]
                ),
                # Drawdowns are signed and non-positive, so a REDUCTION is
                # treatment minus comparator: a shallower trough on the treatment
                # gives a positive number. The other order silently reports every
                # improvement as a deterioration.
                "marginal_drawdown_reduction_percentage_points": (
                    100.0
                    * (
                        drawdown_summary(np.cumprod(1.0 + treatment)).max_drawdown
                        - drawdown_summary(np.cumprod(1.0 + comparator)).max_drawdown
                    )
                ),
            }
        rows.append(entry)

    union_observations = int(np.count_nonzero(union))
    return {
        "note": (
            "The crisis windows were frozen from peak-to-trough equity drawdown "
            "dates before any result was examined. Every figure here is the "
            "compounded return over the window, not an annualised one, because "
            "annualising a two-month window manufactures precision."
        ),
        "per_crisis": rows,
        "union": {
            "observations": union_observations,
            "effective_independent_blocks_at_12m": union_observations / 12.0,
            "marginal_window_return_percentage_points": (
                100.0 * compound_simple(headline["passive_plus_trend"].returns[union])
                - 100.0 * compound_simple(headline["passive_plus_cash"].returns[union])
            ),
            "power_warning": (
                f"{union_observations} months at a 12-month mean block is about "
                f"{union_observations / 12.0:.1f} independent observations. Any "
                "interval computed here is nearly uninformative and is reported as "
                "unresolved rather than narrowed by changing the estimator."
            ),
        },
    }


def _attribution_note(attribution: Attribution) -> str:
    static = attribution.coefficients[1]
    scaled = attribution.coefficients[2]
    convexity = attribution.coefficients[3]
    return (
        f"The sleeve's static market beta is {static:+.3f} (t={attribution.t_statistics[1]:+.2f}), "
        f"its volatility-scaled market loading is {scaled:+.3f} "
        f"(t={attribution.t_statistics[2]:+.2f}) and its loading on the absolute "
        f"market return, the convexity proxy, is {convexity:+.3f} "
        f"(t={attribution.t_statistics[3]:+.2f}). These four exposures explain "
        f"{100.0 * attribution.r_squared:.1f}% of the sleeve's monthly variance, "
        f"leaving an annualised intercept of {attribution.annualised_alpha_percent:+.2f}% "
        f"with a Newey-West t of {attribution.alpha_t_statistic:+.2f}. Goyal and "
        "Jegadeesh (2018) predict a large embedded net-long market position; a small "
        "R-squared here does NOT vindicate the forecasting mechanism, because the "
        "regression can only see the US equity market and the sleeve trades 58 "
        "instruments across four asset classes."
    )


def _unavailable_tests() -> JsonValue:
    return [
        {
            "test": "Kim, Tse and Wald (2016): remove the volatility scaling",
            "run": False,
            "reason": (
                "NOT RUN, and not runnable. Removing the per-instrument volatility "
                "scaling collapses the published pooled t from 4.34 to 1.68, which "
                "makes it the single most informative test of this strategy. The "
                "public series is an aggregate of 58 already-scaled instrument "
                "positions and cannot be unwound, so the test requires "
                "contract-level data this experiment does not have. Its absence is "
                "a limit on what any conclusion here can mean."
            ),
        },
        {
            "test": "Huang et al. (2020): bootstrap of the pooled predictive t-statistic",
            "run": False,
            "reason": (
                "NOT RUN. It is an asset-level predictive-regression test on the 55 "
                "underlying instruments, not a test of a portfolio return series. "
                "Their finding stands as prior evidence against the forecasting "
                "mechanism and this experiment neither confirms nor rebuts it."
            ),
        },
        {
            "test": "Re-costing the vendor series from its own trades",
            "run": False,
            "reason": (
                "NOT RUN. The trades are not observable and the workbook states no "
                "fee, transaction-cost, slippage or financing basis anywhere, so the "
                "vendor's cost basis is UNESTABLISHED rather than known to be gross."
            ),
        },
        {
            "test": "Survivorship and backfill correction",
            "run": False,
            "reason": (
                "NOT APPLICABLE to a single vendor factor series, and unquantifiable "
                "for it. The published magnitude on comparable CTA data is 7.7 "
                "percentage points of annual return, Sharpe 0.73 to 0.09, which is "
                "larger than the strategy's entire gross premium. No correction of "
                "that size has been applied here because none can be estimated from "
                "one series."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# Hostile tests
# --------------------------------------------------------------------------- #


def _hostile_tests(
    specification: Specification,
    inputs: PanelInputs,
    settings: Settings,
    *,
    columns: Sequence[CostColumn],
    base: Scenario,
    baseline: float,
    full_mask: NDArray[np.bool_],
    periods: Sequence[str],
    crises: Sequence[tuple[str, str, str]],
    attribution: Attribution,
    scaled_equity: FloatArray,
    rng: np.random.Generator,
) -> JsonValue:
    """Every hostile test the frozen specification demands, favourable or not."""
    default = columns[-1]
    gamma = settings.gamma
    start = inputs.reported_from

    def marginal_for(scenario: Scenario, column: CostColumn = default) -> float:
        return _marginal_point(
            _build_portfolios(inputs, scenario, column), mask=full_mask, gamma=gamma
        )

    def replace_sleeve(name: str, sleeve: FloatArray) -> Scenario:
        return Scenario(
            name=name,
            sleeve_excess=sleeve,
            centre_of_mass_months=base.centre_of_mass_months,
            exposure_cap=base.exposure_cap,
            sleeve_weight=base.sleeve_weight,
            equity_weight=base.equity_weight,
        )

    # 1. remove the best trend month
    reported_sleeve = inputs.sleeve_excess[start:]
    best_index = int(np.argmax(reported_sleeve))
    without_best_month = inputs.sleeve_excess.copy()
    without_best_month[start + best_index] = 0.0
    best_month_marginal = marginal_for(replace_sleeve("drop_best_month", without_best_month))

    # 2. remove the best crisis
    crisis_effects: dict[str, float] = {}
    for name, low, high in crises:
        mask = _mask_for(periods, low, high)
        if not bool(mask.any()):
            continue
        crisis_effects[name] = float(np.sum(reported_sleeve[mask]))
    best_crisis = max(crisis_effects, key=lambda key: crisis_effects[key]) if crisis_effects else ""
    without_best_crisis = inputs.sleeve_excess.copy()
    if best_crisis:
        window = next(item for item in crises if item[0] == best_crisis)
        mask = _mask_for(periods, window[1], window[2])
        without_best_crisis[start:][mask] = 0.0
    best_crisis_marginal = (
        marginal_for(replace_sleeve("drop_best_crisis", without_best_crisis))
        if best_crisis
        else float("nan")
    )

    # 3. delay execution by one month
    delayed = np.concatenate(([0.0], inputs.sleeve_excess[:-1]))
    delayed_marginal = marginal_for(replace_sleeve("delayed_one_month", delayed))

    # 4. double every cost
    doubled = default.doubled()
    doubled_marginal = marginal_for(base, doubled)

    # 5. cap leverage
    cap_rows: list[JsonValue] = []
    for cap in (settings.exposure_cap, settings.exposure_cap_half):
        scenario = Scenario(
            name=f"cap_{cap}",
            sleeve_excess=inputs.sleeve_excess,
            centre_of_mass_months=base.centre_of_mass_months,
            exposure_cap=cap,
            sleeve_weight=base.sleeve_weight,
            equity_weight=base.equity_weight,
        )
        portfolios = _build_portfolios(inputs, scenario, default)
        exposure = portfolios["passive_plus_cash"].weights[:, 0] / base.equity_weight
        binding = int(np.count_nonzero(exposure >= cap - 1e-9))
        cap_rows.append(
            {
                "exposure_cap": cap,
                "marginal_percentage_points_per_year": _marginal_point(
                    portfolios, mask=full_mask, gamma=gamma
                ),
                "months_the_cap_binds_on_the_comparator": binding,
                "max_realised_comparator_exposure": float(np.max(exposure)),
                "mean_realised_comparator_exposure": float(np.mean(exposure)),
                "risk_match_broken": binding > 0,
                "reading": (
                    "VALID: the cap never binds, so the risk match holds and this is "
                    "a like-for-like marginal comparison."
                    if binding == 0
                    else (
                        f"NOT A VALID MARGINAL COMPARISON. The cap binds in {binding} "
                        "of the reported months, but it binds on the risk-matched "
                        "CASH COMPARATOR, not on the trend portfolio, which is "
                        "unlevered by construction. Forcing the comparator below its "
                        "matched exposure de-risks the control and inflates the "
                        "measured marginal benefit. Read this row as evidence about "
                        "where the cap bites, never as a stressed estimate of the "
                        "sleeve's value."
                    )
                ),
            }
        )

    # 6. gaps and reversals
    gaps = _gap_and_reversal_test(inputs, periods=periods)

    # 7. change the volatility lookback without retuning
    lookback_rows: list[JsonValue] = []
    for days in (settings.lookback_days, *settings.lookback_alternatives_days):
        scenario = Scenario(
            name=f"lookback_{days:g}d",
            sleeve_excess=inputs.sleeve_excess,
            centre_of_mass_months=_centre_of_mass(days),
            exposure_cap=base.exposure_cap,
            sleeve_weight=base.sleeve_weight,
            equity_weight=base.equity_weight,
        )
        lookback_rows.append(
            {
                "lookback_days_declared": days,
                "monthly_centre_of_mass": _centre_of_mass(days),
                "marginal_percentage_points_per_year": marginal_for(scenario),
            }
        )

    # 8. pre versus post publication is in marginal_results; summarised here.

    # 9. the fitted static-and-volatility replica.
    #
    # The replica that drives falsifier clause (d) is the EXPOSURE component only,
    # with the intercept removed. The frozen clause asks whether "a simpler static
    # exposure explains it", and an OLS intercept is by construction the part the
    # exposures do NOT explain. Leaving it in would build a near-riskless asset
    # paying the sleeve's whole alpha at a fraction of its volatility, which beats
    # the sleeve itself and would fire the clause on an artefact of the arithmetic
    # rather than on any exposure a portfolio could hold.
    intercept = float(attribution.coefficients[0])
    fitted = np.where(np.isnan(attribution.fitted), 0.0, attribution.fitted)
    exposures_only = fitted - intercept
    replica_full = inputs.sleeve_excess.copy()
    replica_full[start:] = exposures_only
    replica_marginal = marginal_for(replace_sleeve("exposures_only_replica", replica_full))
    with_intercept_full = inputs.sleeve_excess.copy()
    with_intercept_full[start:] = fitted
    with_intercept_marginal = marginal_for(
        replace_sleeve("fitted_with_intercept", with_intercept_full)
    )
    residual_full = inputs.sleeve_excess.copy()
    residual_full[start:] = np.where(np.isnan(attribution.residuals), 0.0, attribution.residuals)
    residual_marginal = marginal_for(replace_sleeve("residual_only", residual_full))

    # 10. a static long position at the same ex-ante risk, and a scaled one
    sleeve_volatility = ewma_annualised_volatility(
        inputs.sleeve_excess, centre_of_mass_months=base.centre_of_mass_months
    )
    equity_volatility = ewma_annualised_volatility(
        inputs.equity_excess, centre_of_mass_months=base.centre_of_mass_months
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        sizing = np.clip(
            np.nan_to_num(sleeve_volatility / equity_volatility, nan=0.0), 0.0, 10.0
        )
    static_long = sizing * inputs.equity_excess
    static_marginal = marginal_for(replace_sleeve("static_long_matched_risk", static_long))
    with np.errstate(divide="ignore", invalid="ignore"):
        scaled_sizing = np.clip(
            np.nan_to_num(
                sleeve_volatility
                / ewma_annualised_volatility(
                    scaled_equity, centre_of_mass_months=base.centre_of_mass_months
                ),
                nan=0.0,
            ),
            0.0,
            10.0,
        )
    scaled_long = scaled_sizing * scaled_equity
    scaled_long_marginal = marginal_for(replace_sleeve("scaled_long_matched_risk", scaled_long))

    # 11. the declared bond-proxy robustness arm
    bond_scenario = Scenario(
        name="bond_leg",
        sleeve_excess=inputs.sleeve_excess,
        centre_of_mass_months=base.centre_of_mass_months,
        exposure_cap=base.exposure_cap,
        sleeve_weight=base.sleeve_weight,
        equity_weight=base.equity_weight,
        use_bond_leg=True,
    )
    bond_marginal = marginal_for(bond_scenario)

    del rng, specification  # every hostile test above is deterministic
    return {
        "baseline_marginal_percentage_points_per_year": baseline,
        "baseline_cost_basis": default.basis.value,
        "remove_the_best_trend_month": {
            "month_removed": periods[best_index],
            "sleeve_excess_return_removed_percent": 100.0 * float(reported_sleeve[best_index]),
            "marginal_percentage_points_per_year": best_month_marginal,
            "share_of_baseline_lost": _share_lost(baseline, best_month_marginal),
            "method": (
                "the sleeve's excess return in that month is set to zero rather than "
                "the month being deleted, because the certainty equivalent needs "
                "whole calendar years and deleting a month would silently drop a year"
            ),
        },
        "remove_the_best_crisis": {
            "crisis_removed": best_crisis,
            "selection_rule": "the crisis in which the sleeve's summed excess return was largest",
            "sleeve_excess_summed_by_crisis_percent": {
                name: 100.0 * value for name, value in crisis_effects.items()
            },
            "marginal_percentage_points_per_year": best_crisis_marginal,
            "share_of_baseline_lost": _share_lost(baseline, best_crisis_marginal),
        },
        "delay_execution": {
            "delay_months": 1,
            "marginal_percentage_points_per_year": delayed_marginal,
            "share_of_baseline_lost": _share_lost(baseline, delayed_marginal),
            "note": (
                "The frozen one- and five-trading-day delays are not expressible in a "
                "monthly series. One month is the smallest implementable delay and is "
                "strictly more hostile than either, so this test cannot flatter the "
                "result."
            ),
        },
        "double_every_cost": {
            "one_way_bps": doubled.one_way_bps,
            "management_fee_annual_percent": 100.0 * doubled.management_fee_annual,
            "performance_fee_percent": 100.0 * doubled.performance_fee_rate,
            "marginal_percentage_points_per_year": doubled_marginal,
            "share_of_baseline_lost": _share_lost(baseline, doubled_marginal),
        },
        "cap_leverage": {
            "rows": cap_rows,
            "note": (
                "passive_plus_trend is unlevered by construction: the sleeve is "
                "funded pro rata from the two existing legs, so gross exposure stays "
                "at 1.0 and no leverage cap can bind on it. The cap binds only on the "
                "volatility-scaled comparators, which is itself the finding."
            ),
        },
        "gaps_and_reversals": gaps,
        "change_the_volatility_lookback": {
            "rows": lookback_rows,
            "note": (
                "Nothing else was retuned. Volatility scaling is the effect under "
                "dispute, not an implementation detail: Kim, Tse and Wald (2016) "
                "collapse the pooled statistic from 4.34 to 1.68 by removing it. "
                "READ THIS TEST NARROWLY. The lookback moves the volatility-scaled "
                "comparator and the risk match of the cash comparator; it does NOT "
                "touch the sleeve, whose scaling is the vendor's and is baked into "
                "the published aggregate. Insensitivity here is therefore evidence "
                "about this experiment's own estimator and says nothing about the "
                "sensitivity Kim, Tse and Wald measured."
            ),
        },
        "static_and_volatility_exposure_replica": {
            "replica_marginal_percentage_points_per_year": replica_marginal,
            "replica_definition": (
                "the sleeve's fitted value on a static market position, a "
                "volatility-scaled market position, the absolute market return and "
                "the lagged market return, with the INTERCEPT REMOVED. This is the "
                "series that drives falsifier clause (d)."
            ),
            "fitted_including_intercept_marginal": with_intercept_marginal,
            "intercept_annualised_percent": attribution.annualised_alpha_percent,
            "why_the_intercept_is_excluded": (
                "An OLS intercept is by construction the part the exposures do NOT "
                "explain, so including it in a test of whether exposures explain the "
                "result is a category error. Concretely, the fitted-with-intercept "
                "series pays the sleeve's whole alpha at roughly the square root of "
                f"its R-squared ({100.0 * attribution.r_squared:.1f}%) of its "
                "volatility, which beats the sleeve itself; that figure is reported "
                "above as a diagnostic and it is NOT an exposure any portfolio could "
                "hold."
            ),
            "residual_only_marginal_percentage_points_per_year": residual_marginal,
            "static_long_matched_risk_marginal": static_marginal,
            "volatility_scaled_long_matched_risk_marginal": scaled_long_marginal,
            "replica_r_squared": attribution.r_squared,
            "replica_is_fitted_in_sample": True,
            "interpretation": (
                "The replica is fitted on the same sample it is evaluated on, so its "
                "marginal benefit is an UPPER bound; that is the conservative "
                "direction, because the question is whether a simpler exposure COULD "
                "explain the result."
            ),
        },
        "bond_leg_robustness_arm": {
            "marginal_percentage_points_per_year": bond_marginal,
            "construction": (
                "the risky leg becomes 75% equity and 25% modelled ten-year Treasury "
                "total return, reconstructed from FRED GS10 by a duration and "
                "convexity approximation"
            ),
            "research_grade": False,
            "warning": (
                "The bond leg is MODELLED, not an investable total-return history. It "
                "exists so that the 2022 window, in which equities and bonds fell "
                "together, is not silently deleted by the absence of a bond leg. No "
                "conclusion rests on it."
            ),
        },
    }


def _share_lost(baseline: float, stressed: float) -> float | None:
    if math.isnan(stressed) or abs(baseline) < 1e-12:
        return None
    return float((baseline - stressed) / abs(baseline))


def _gap_and_reversal_test(inputs: PanelInputs, *, periods: Sequence[str]) -> JsonValue:
    """Does the sleeve help when a drawdown opens abruptly, or only when it develops?

    A slow signal cannot be short before the fall it never saw coming. The test
    splits the reported months into those where the equity market's first big loss
    follows a rising month — an abrupt onset, the closest a monthly series gets to a
    gap — and those where it follows at least two consecutive losses, a developed
    drawdown. It also isolates sharp reversals, where a large move follows a large
    move of the opposite sign, which is the regime that whipsaws a trend follower.
    """
    start = inputs.reported_from
    equity = inputs.equity_excess[start:]
    sleeve = inputs.sleeve_excess[start:]
    threshold = float(np.std(equity, ddof=1))

    abrupt = np.zeros(equity.size, dtype=bool)
    developed = np.zeros(equity.size, dtype=bool)
    reversal = np.zeros(equity.size, dtype=bool)
    for index in range(2, equity.size):
        if equity[index] < -threshold:
            if equity[index - 1] > 0.0:
                abrupt[index] = True
            elif equity[index - 1] < 0.0 and equity[index - 2] < 0.0:
                developed[index] = True
        if (
            abs(equity[index]) > threshold
            and abs(equity[index - 1]) > threshold
            and equity[index] * equity[index - 1] < 0.0
        ):
            reversal[index] = True

    def summarise(mask: NDArray[np.bool_], label: str) -> JsonValue:
        count = int(np.count_nonzero(mask))
        return {
            "regime": label,
            "months": count,
            "mean_sleeve_excess_percent_per_month": (
                100.0 * float(np.mean(sleeve[mask])) if count else None
            ),
            "mean_equity_excess_percent_per_month": (
                100.0 * float(np.mean(equity[mask])) if count else None
            ),
            "months_listed": [periods[int(i)] for i in np.flatnonzero(mask)][:12],
        }

    return {
        "threshold_percent_per_month": 100.0 * threshold,
        "threshold_definition": (
            "one standard deviation of the reported monthly equity excess return"
        ),
        "rows": [
            summarise(abrupt, "abrupt onset: a large equity loss straight after a rising month"),
            summarise(developed, "developed drawdown: a large equity loss after two losing months"),
            summarise(reversal, "sharp reversal: a large move against a large move"),
        ],
        "note": (
            "A monthly series cannot show an overnight gap at all. This is the "
            "closest available proxy and it understates the problem: within-month "
            "gaps are invisible here, and a strategy that rebalances monthly cannot "
            "react to one. The reversal row is the whipsaw regime, where a slow "
            "signal is positioned for the move that just ended."
        ),
    }


# --------------------------------------------------------------------------- #
# The predeclared decision
# --------------------------------------------------------------------------- #


def _apply_rejection_rule(
    *,
    primary: MarginalResult,
    settings: Settings,
    hostile: JsonValue,
    era_marginals: Mapping[str, MarginalResult],
) -> dict[str, JsonValue]:
    """Exactly the falsifier and rejection rule frozen in the specification.

    Precedence, stated because the frozen document leaves it implicit. Clauses (a)
    to (e) are measured on the vendor series' own properties, and the public series
    CAN answer them; a clause that fires therefore rejects *the hypothesis that
    this series adds material marginal value over a risk-matched cash comparator*,
    which is a narrower claim than "trend does not work" and is what is reported.
    The `unresolved` carve-out protects the opposite case — a benefit that looks
    positive but cannot be shown investable — and applies when no clause fires.
    """
    fired: list[str] = []
    hostile_map = _mapping(hostile, where="hostile_tests")
    materiality = settings.materiality

    if primary.marginal_percent < materiality:
        fired.append(
            f"(a) the marginal certainty-equivalent benefit over the risk-matched "
            f"cash comparator is {primary.marginal_percent:+.3f} pp/yr under the "
            f"net-pessimistic column, below the {materiality:.2f} pp/yr materiality "
            "threshold, so it is economically negligible"
        )

    crisis = _mapping(
        _at(hostile_map, "remove_the_best_crisis", where="hostile_tests"), where="crisis"
    )
    crisis_lost = crisis.get("share_of_baseline_lost")
    if isinstance(crisis_lost, float) and crisis_lost > 0.60:
        fired.append(
            f"(b) removing the single best crisis ({crisis.get('crisis_removed')}) "
            f"destroys {100.0 * crisis_lost:.0f}% of the full-period marginal "
            "benefit, more than the 60% concentration limit"
        )

    month = _mapping(
        _at(hostile_map, "remove_the_best_trend_month", where="hostile_tests"), where="month"
    )
    month_lost = month.get("share_of_baseline_lost")
    if isinstance(month_lost, float) and month_lost > 0.40:
        fired.append(
            f"(c) removing the single best trend month ({month.get('month_removed')}) "
            f"destroys {100.0 * month_lost:.0f}% of the marginal benefit, more than "
            "the 40% limit"
        )

    replica = _mapping(
        _at(hostile_map, "static_and_volatility_exposure_replica", where="hostile_tests"),
        where="replica",
    )
    replica_marginal = replica.get("replica_marginal_percentage_points_per_year")
    residual_marginal = replica.get("residual_only_marginal_percentage_points_per_year")
    if isinstance(replica_marginal, float) and replica_marginal >= materiality:
        share = (
            f", which is {100.0 * replica_marginal / primary.marginal_percent:.0f}% of "
            f"the sleeve's own {primary.marginal_percent:+.3f}"
            if abs(primary.marginal_percent) > 1e-12
            else ""
        )
        fired.append(
            f"(d) a replica built only from static and volatility-scaled market "
            f"exposures, with the intercept removed, delivers {replica_marginal:+.3f} "
            f"pp/yr{share}. That is at or above the {materiality:.2f} pp/yr "
            "threshold, so a simpler exposure reproduces a material part of the "
            "benefit"
        )

    pre = era_marginals.get("pre_publication")
    post = era_marginals.get("post_publication")
    if (
        pre is not None
        and post is not None
        and post.marginal_percent < 0.0 < pre.marginal_percent
        and not (post.lower_90 <= pre.marginal_percent <= post.upper_90)
    ):
        fired.append(
            f"(e) the post-publication marginal benefit is {post.marginal_percent:+.3f} "
            f"pp/yr against {pre.marginal_percent:+.3f} pre-publication, and the "
            "eras' intervals do not overlap at 90%"
        )

    interval_contains_zero = primary.lower_95 <= 0.0 <= primary.upper_95
    if fired:
        status = ResultStatus.REJECTED
        reasoning = (
            "The predeclared falsifier fired on the vendor series' own measured "
            "properties, which the public series can answer without settling "
            "investability: " + "; ".join(fired)
        )
    elif interval_contains_zero:
        status = ResultStatus.UNRESOLVED
        reasoning = (
            f"No falsifier clause fired, but the 95% interval "
            f"[{primary.lower_95:+.3f}, {primary.upper_95:+.3f}] pp/yr contains "
            "zero, and the vendor's fee and transaction-cost basis is unestablished "
            "from the archived workbook. This is 'cannot tell', not 'no benefit'."
        )
    else:
        status = ResultStatus.UNRESOLVED
        reasoning = (
            "No falsifier clause fired and the interval excludes zero, but the "
            "vendor's fee and transaction-cost basis cannot be established from the "
            "archived workbook, so investability is unanswered and the frozen rule "
            "requires `unresolved` rather than a stronger claim."
        )

    summary = (
        f"Vendor-series evaluation, NOT an independent replication. Marginal "
        f"certainty-equivalent benefit of adding a 15% AQR trend sleeve over a "
        f"risk-matched cash comparator: {primary.marginal_percent:+.3f} pp/yr "
        f"(95% [{primary.lower_95:+.3f}, {primary.upper_95:+.3f}], "
        f"n={primary.observations} months) on the net-pessimistic column. "
        f"{len(fired)} of five falsifier clauses fired. Status: {status.value}."
    )
    return {
        "status": status.value,
        "summary": summary,
        "falsifier_clauses_fired": list(fired),
        "reasoning": reasoning,
        "materiality_threshold_annual_percent": materiality,
        "clause_d_readings": {
            "note": (
                "The frozen clause reads: 'an attribution on static asset exposures "
                "plus a volatility-scaled market position leaves a marginal benefit "
                "below the materiality threshold'. That sentence admits two readings "
                "and BOTH are reported, because a rule that only fires on the reading "
                "the author preferred after seeing the answer is not a rule."
            ),
            "reading_implemented": (
                "the exposure replica itself clears the threshold, i.e. the exposures "
                "reproduce a material amount"
            ),
            "replica_marginal_percentage_points_per_year": replica_marginal,
            "reading_alternative": (
                "the residual left after the attribution falls below the threshold. "
                "This reading is degenerate: an OLS residual is mean-zero by "
                "construction, so it fires whatever the data say, and it is reported "
                "only so that a reader can see it was considered."
            ),
            "residual_only_marginal_percentage_points_per_year": residual_marginal,
            "what_would_change_the_verdict": (
                "The sleeve's margin over the replica is "
                f"{primary.marginal_percent - replica_marginal:+.3f} pp/yr, which "
                "itself clears the materiality threshold. A "
                "reader who thinks clause (d) should have been written as a RELATIVE "
                "share rather than an absolute one would reach `unresolved` instead. "
                "The clause was frozen in absolute form before any result was seen "
                "and is applied as frozen."
                if isinstance(replica_marginal, float)
                else "the replica could not be computed"
            ),
        },
        "precedence_note": (
            "Clauses (a) to (e) are measured on the series' own properties, so a "
            "clause that fires rejects the hypothesis that THIS SERIES adds material "
            "marginal value over a risk-matched cash comparator. It does not reject "
            "trend as a strategy, and it is not a statement about an investable "
            "product. The `unresolved` carve-out in the frozen rejection rule "
            "protects the opposite case and applies when no clause fires."
        ),
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def _estimates(
    primary: MarginalResult,
    marginals: Sequence[MarginalResult],
    statistics: Sequence[PathStatistics],
    settings: Settings,
) -> tuple[Estimate, ...]:
    out: list[Estimate] = [
        Estimate(
            name="marginal certainty-equivalent return over the risk-matched cash comparator",
            value=primary.marginal_percent,
            units="percentage points per year",
            interval=(primary.lower_95, primary.upper_95),
            interval_method=(
                f"paired stationary block bootstrap, two-sided 95%, mean block "
                f"{primary.block_length:.0f}m, {settings.resamples} resamples, "
                "resampling the joint monthly panel so the pairing is preserved"
            ),
            cost_basis=CostBasis.NET_PESSIMISTIC,
            n_obs=primary.observations,
            notes=(
                "passive_plus_trend minus passive_plus_cash, CRRA gamma=3, from "
                "non-overlapping calendar-year gross returns. Vendor-series "
                "evaluation, not an independent replication."
            ),
        )
    ]
    for item in marginals:
        if item is primary:
            continue
        out.append(
            Estimate(
                name=f"marginal CE, {item.label}",
                value=item.marginal_percent,
                units="percentage points per year",
                interval=(item.lower_95, item.upper_95),
                interval_method=(
                    f"paired stationary block bootstrap, two-sided 95%, mean block "
                    f"{item.block_length:.0f}m"
                ),
                cost_basis=item.basis,
                n_obs=item.observations,
                notes=f"treatment {item.treatment} against comparator {item.comparator}",
            )
        )
    for row in statistics:
        if row.window != "full_period" or row.basis is not CostBasis.NET_PESSIMISTIC:
            continue
        out.append(
            Estimate(
                name=f"{row.portfolio_id} full-period net geometric return",
                value=row.geometric_annual_percent,
                units="percentage points per year",
                cost_basis=CostBasis.NET_PESSIMISTIC,
                n_obs=row.observations,
                uncertainty_unavailable_reason=(
                    "a descriptive realised statistic of one path; the uncertainty "
                    "that decides this experiment is on the paired marginal "
                    "difference, which carries its own interval above"
                ),
                notes=(
                    f"max drawdown {row.max_drawdown_percent:.1f}%, annualised "
                    f"volatility {row.annualised_volatility_percent:.1f}%"
                ),
            )
        )
    return tuple(out)


def _caveats(inputs: PanelInputs, attribution: Attribution) -> tuple[str, ...]:
    del inputs
    return (
        "THIS IS A VENDOR-SERIES EVALUATION, NOT AN INDEPENDENT REPLICATION. The "
        "series is authored and maintained by a firm that sells the strategy, and "
        "the workbook states that AQR reconstructs the full history each time the "
        "returns are updated. An independent reimplementation would require "
        "contract-level futures histories, roll conventions, collateral returns, "
        "execution assumptions and point-in-time market availability, none of which "
        "are inputs here.",
        "The vendor's fee and transaction-cost basis is UNESTABLISHED. The archived "
        "workbook states no fee, cost, slippage or financing assumption anywhere; "
        "its Definitions, Data Sources and Disclosures sheets ship their content as "
        "embedded pictures, and the text recovered from those pictures describes the "
        "volatility model, the 40% per-position volatility target and the instrument "
        "universe while saying nothing about costs. The investor-level fee columns "
        "here are this repository's assumptions, not the vendor's disclosure.",
        "Survivorship and backfill on comparable CTA data move measured returns by "
        "7.7 percentage points a year, Sharpe 0.73 to 0.09, which is larger than the "
        "strategy's entire gross premium. No correction of that size has been applied "
        "because none can be estimated from a single vendor series, so every figure "
        "here is an upper bound of unknown tightness.",
        "The Kim, Tse and Wald (2016) test that collapses the published pooled t from "
        "4.34 to 1.68 by removing the volatility scaling CANNOT be run on this "
        "series. The published aggregate cannot be unwound to per-instrument "
        "positions. That is the single most informative test of this strategy and it "
        "is unavailable.",
        "The vendor's own Data Sources text states that MSCI country index returns "
        "and JP Morgan country bond index returns stand in for futures returns "
        "before futures were available. Part of the early history is therefore not a "
        "futures strategy at all, which is why the reconstructed era is reported "
        "separately and never pooled.",
        "The passive benchmark is 60% US equity / 40% cash, not 60/40 equity/bond. "
        "Decision record 0002 establishes that no free price source is research-grade "
        "and no investable bond total-return history is available. The equity/bond "
        "form appears only as a declared robustness arm built from a MODELLED GS10 "
        "duration approximation, flagged research_grade false, and no conclusion "
        "rests on it.",
        "The volatility estimator is the vendor's own exponentially weighted form at "
        "the vendor's own 60-day centre of mass, applied at MONTHLY frequency because "
        "the public series is monthly. It approximates the vendor's daily estimator "
        "and is not that estimator.",
        f"The attribution can only see the US equity market, while the sleeve trades "
        f"58 instruments across four asset classes. Its R-squared of "
        f"{100.0 * attribution.r_squared:.1f}% is therefore a LOWER bound on how much "
        "of the sleeve simple exposures could explain, and a low value does not "
        "vindicate the forecasting mechanism.",
        "Crisis windows hold 53 months in total. At a 12-month mean block that is "
        "about 4.4 independent observations, so every crisis-conditional interval is "
        "nearly uninformative by construction and is reported as such rather than "
        "narrowed by changing the estimator.",
    )


def _frames(
    statistics: Sequence[PathStatistics],
    marginals: Sequence[MarginalResult],
    crisis_rows: JsonValue,
) -> dict[str, pd.DataFrame]:
    del crisis_rows
    return {
        "portfolio_statistics": pd.DataFrame([item.to_json() for item in statistics]),
        "marginal_results": pd.DataFrame(
            [
                {
                    "comparison": item.label,
                    "window": item.window,
                    "cost_basis": item.basis.value,
                    "observations": item.observations,
                    "marginal_pp_per_year": item.marginal_percent,
                    "lower_95": item.lower_95,
                    "upper_95": item.upper_95,
                    "one_sided_p": item.one_sided_p_value,
                }
                for item in marginals
            ]
        ),
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
    return _workspace_root() / "experiments" / "exp_004_trend_marginal_value.yaml"


def _manifest_hashes(specification: Specification) -> tuple[str, ...]:
    parameters = specification.parameters
    if not isinstance(parameters, Mapping):
        return ()
    pin = parameters.get("source_pin")
    if not isinstance(pin, Mapping):
        return ()
    hashes: list[str] = []
    for entry in pin.values():
        if not isinstance(entry, Mapping):
            continue
        location = entry.get("committed_manifest")
        if isinstance(location, str):
            path = _workspace_root() / location
            if path.is_file():
                hashes.append(read_manifest(path).sha256_manifest())
    return tuple(hashes)


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    lines = [result.summary, ""]
    rows = result.diagnostics.get("portfolio_statistics")
    lines.append(
        f"{'portfolio':<26}{'basis':<18}{'n':>5}{'CE%':>8}{'geo%':>8}{'vol%':>8}"
        f"{'SR':>7}{'MDD%':>8}{'corr':>7}"
    )
    if isinstance(rows, Sequence) and not isinstance(rows, str):
        for item in rows:
            if not isinstance(item, Mapping) or item.get("window") != "full_period":
                continue
            certainty = item.get("certainty_equivalent_percent_per_year")
            correlation = item.get("correlation_to_passive")
            lines.append(
                f"{item.get('portfolio')!s:<26}{item.get('cost_basis')!s:<18}"
                f"{int(str(item.get('observations'))):>5}"
                f"{float(str(certainty)) if certainty is not None else float('nan'):>8.2f}"
                f"{float(str(item.get('geometric_annual_percent'))):>8.2f}"
                f"{float(str(item.get('annualised_volatility_percent'))):>8.2f}"
                f"{float(str(item.get('sharpe_annualised'))):>7.2f}"
                f"{float(str(item.get('max_drawdown_percent'))):>8.1f}"
                f"{float(str(correlation)) if correlation is not None else float('nan'):>7.2f}"
            )
    lines.append("")
    marginal = result.diagnostics.get("marginal_results")
    if isinstance(marginal, Sequence) and not isinstance(marginal, str):
        header = (
            f"{'marginal comparison':<62}{'pp/yr':>9}"
            f"{'95% low':>10}{'95% high':>10}{'p':>8}"
        )
        lines.append(header)
        for item in marginal:
            if not isinstance(item, Mapping):
                continue
            interval = item.get("two_sided_95")
            low = high = float("nan")
            if isinstance(interval, Sequence) and not isinstance(interval, str):
                low, high = float(str(interval[0])), float(str(interval[1]))
            lines.append(
                f"{str(item.get('comparison'))[:60]:<62}"
                f"{float(str(item.get('marginal_percentage_points_per_year'))):>9.3f}"
                f"{low:>10.3f}{high:>10.3f}"
                f"{float(str(item.get('one_sided_p_value_marginal_is_positive'))):>8.3f}"
            )
    lines.append("")
    verdict = result.diagnostics.get("verdict")
    if isinstance(verdict, Mapping):
        lines.append(f"status: {verdict.get('status')}")
        lines.append(f"  {verdict.get('reasoning')}")
    lines.append("")
    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 004 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_004_trend_marginal_value",
        description=(
            "Evaluate AQR's published time-series-momentum series as a marginal "
            "crisis diversifier inside a passive portfolio, writing a ledger entry "
            "for the attempt. This is a vendor-series evaluation, not a replication."
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
                "exp_004_trend_marginal_value"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
