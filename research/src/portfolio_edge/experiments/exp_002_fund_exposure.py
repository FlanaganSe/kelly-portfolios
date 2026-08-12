"""Experiment 002: what a retail factor product actually delivers, and at what cost.

This is an EXPOSURE AND IMPLEMENTATION AUDIT, not a fund-selection strategy. The
question is not "which of these funds has alpha". It is "does this product carry
the exposure it advertises, is that exposure stable, and can the same exposure be
had more cheaply from broad funds an investor already owns". A fund with zero
alpha passes if it delivers a wanted exposure cheaply; a fund with a positive
alpha estimate fails if its exposure is absent, unstable, or replicable.

Three things make this experiment awkward on purpose
----------------------------------------------------
**The universe is committed before any return is downloaded.** The screen lives
in :mod:`portfolio_edge.experiments.exp_002_universe` and writes
``data-manifests/exp_002/product_universe.json``. This module *reads* that file
and refuses to run without it. A fund that failed the screen never has its
returns fetched, so no screen decision can be revised after seeing performance.

**Every alpha is shrunk before it means anything, and the annualisation is the
trap.** An annual alpha is TWELVE times a monthly intercept, so its standard
error annualises by ``x12`` and never by ``sqrt(12)``. Using ``sqrt(12)`` would
understate the standard error by 3.46 and shrink far too little. With true
cross-sectional dispersion of about 1.25%/yr and a typical single-fund standard
error of about 3.36%/yr, the shrinkage factor is
``1.25**2 / (1.25**2 + 3.36**2) = 0.121``, so an observed 5%/yr alpha implies a
posterior near 0.6%/yr. Each fund is shrunk by its OWN factor computed from its
OWN standard error, because reusing 0.121 would be wrong for every fund.

**A wide interval is not evidence of absence.** The minimum detectable alpha at
80% power is reported beside every alpha. Over 72 months it is large enough that
most funds are `unresolved` on alpha and decidable only on exposure, and saying
so is the finding rather than a disclaimer.

The data contract is the binding constraint
-------------------------------------------
Returns come from Form N-PORT Item B.5 — the fund's own filed monthly total
return. That is a far stronger contract than any price feed tested in
``docs/decisions/0002-no-research-grade-free-price-source.md``, but public N-PORT
filings begin in 2019, the figures are unaudited, and General Instruction G lets
each filer use its own internal methodology. So this run is EXPLORATORY, it may
not promote a sleeve, and its conclusion is limited by the data contract and the
length of the window rather than by the evidence.

Run it::

    uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --build-universe
    uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --view-results
"""

from __future__ import annotations

import argparse
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
from scipy.optimize import minimize
from scipy.stats import norm

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data import french, nport
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.prices import YahooChartAdapter
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.experiments.exp_002_universe import (
    ProductFacts,
    ScreenedFund,
    Universe,
    build_universe,
    frame_manifest,
    load_product_facts,
    load_universe,
    resolve_ticker,
    universe_path,
    workspace_root,
    write_universe,
)
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import month_count, month_index, period_from_index
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
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "FACTOR_SPECIFICATIONS",
    "MONTHS_PER_YEAR",
    "ExposureFit",
    "FactorPanel",
    "FundExposureError",
    "FundOutcome",
    "FundSeries",
    "ReplicationFit",
    "build_registry",
    "default_specification_path",
    "fit_exposure",
    "inflated_family",
    "load_factor_panel",
    "main",
    "minimum_detectable_alpha",
    "replicating_weights",
    "run",
    "shrink_alpha",
]

ENTRY_POINT: Final = "exp_002_fund_exposure"

MONTHS_PER_YEAR: Final = 12

#: The three nested models every fund is estimated under. A loading that appears
#: in only one of them is a specification artefact, not an exposure -- and the
#: multiple-testing family is every fund times every one of these.
FACTOR_SPECIFICATIONS: Final[dict[str, tuple[str, ...]]] = {
    "CAPM": ("Mkt-RF",),
    "FF3": ("Mkt-RF", "SMB", "HML"),
    "FF5+UMD": ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"),
}

#: The specification the primary metric and the falsifier read.
PRIMARY_SPECIFICATION: Final = "FF5+UMD"

#: Months after the sample end beyond which a filing cannot contain an in-window
#: month. Form N-PORT reports the three months ending on a fiscal quarter end and
#: is filed within 60 days of it, so five months would do; eight is the margin.
_HELD_OUT_FILING_MONTHS: Final = 8

FloatArray = NDArray[np.float64]


class FundExposureError(RuntimeError):
    """The audit could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise FundExposureError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise FundExposureError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise FundExposureError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise FundExposureError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise FundExposureError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    return tuple(str(item) for item in _sequence(_at(data, key, where=where), where=where))


def intended_factor_map(specification: Specification) -> dict[str, tuple[str, int]]:
    """The predeclared mandate-to-factor mapping, including its signs."""
    universe = _mapping(specification.universe, where="universe")
    block = _mapping(_at(universe, "intended_factor_map", where="universe"), where="universe")
    mapping = _mapping(_at(block, "mapping", where="intended_factor_map"), where="mapping")
    out: dict[str, tuple[str, int]] = {}
    for mandate, entry in mapping.items():
        record = _mapping(entry, where=f"mapping.{mandate}")
        out[str(mandate)] = (
            _text(record, "factor", where=f"mapping.{mandate}"),
            int(_number(record, "sign", where=f"mapping.{mandate}")),
        )
    return out


# --------------------------------------------------------------------------- #
# Statistics this experiment adds, each with its own unit test
# --------------------------------------------------------------------------- #


def shrink_alpha(
    observed_annual_percent: float,
    standard_error_annual_percent: float,
    *,
    dispersion_annual_percent: float,
) -> tuple[float, float]:
    """Posterior mean of a fund's alpha, and the shrinkage factor that produced it.

    Under a normal prior with mean zero and standard deviation ``sigma_true``, and
    a normal likelihood with standard error ``SE``, the posterior mean is
    ``k * observed`` with ``k = sigma_true**2 / (sigma_true**2 + SE**2)``.

    Both inputs must already be ANNUAL. An annual alpha is twelve times a monthly
    intercept, so a monthly standard error becomes annual by ``x12``, never by
    ``sqrt(12)``: the intercept is a repeated constant, not a sum of independent
    shocks, and its scaling carries no square root. Getting that wrong understates
    the standard error by ``sqrt(12) = 3.46`` and shrinks far too little, which is
    the direction that manufactures skill.
    """
    if dispersion_annual_percent <= 0.0:
        raise ValueError("dispersion_annual_percent must be positive")
    if standard_error_annual_percent < 0.0:
        raise ValueError("standard_error_annual_percent cannot be negative")
    prior_variance = dispersion_annual_percent**2
    factor = prior_variance / (prior_variance + standard_error_annual_percent**2)
    return factor * observed_annual_percent, factor


def minimum_detectable_alpha(
    standard_error_annual_percent: float,
    *,
    power: float = 0.80,
    significance: float = 0.05,
) -> float:
    """The smallest true alpha a two-sided test of this precision would find.

    ``MDE = (z_{1 - significance/2} + z_{power}) * SE``. At 80% power and 5%
    significance the multiplier is 2.802. Reported beside every alpha because a
    confidence interval containing zero over a 72-month window usually means the
    window could not have detected the effect, not that the effect is absent.
    """
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must lie in (0, 1), got {power}")
    if not 0.0 < significance < 1.0:
        raise ValueError(f"significance must lie in (0, 1), got {significance}")
    multiplier = float(norm.ppf(1.0 - significance / 2.0) + norm.ppf(power))
    return multiplier * standard_error_annual_percent


def replicating_weights(target: FloatArray, basis: FloatArray) -> FloatArray:
    """Long-only weights summing to one that best track ``target``.

    Minimises the sum of squared tracking error subject to ``w >= 0`` and
    ``sum(w) = 1``, which is the portfolio an investor could actually hold: no
    shorting, fully invested.

    This is an IN-SAMPLE fit. The weights are chosen knowing the whole window, so
    the replication is a BEST CASE and the comparison against it is a HARD test
    for the product. That look-ahead is stated wherever the number is reported and
    is never described as an achievable alternative.
    """
    y = np.asarray(target, dtype=np.float64)
    x = np.asarray(basis, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] != y.size:
        raise ValueError(f"basis shape {x.shape} does not match target of length {y.size}")
    n_assets = x.shape[1]

    def objective(weights: FloatArray) -> float:
        residual = y - x @ weights
        return float(residual @ residual)

    def gradient(weights: FloatArray) -> FloatArray:
        residual = y - x @ weights
        return np.asarray(-2.0 * (x.T @ residual), dtype=np.float64)

    start = np.full(n_assets, 1.0 / n_assets, dtype=np.float64)
    result = minimize(
        objective,
        start,
        jac=gradient,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_assets,
        constraints=[{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}],
        options={"maxiter": 500, "ftol": 1e-14},
    )
    weights = np.clip(np.asarray(result.x, dtype=np.float64), 0.0, None)
    total = float(weights.sum())
    return weights / total if total > 0.0 else start


def _bootstrap_coefficients(
    y: FloatArray, design: FloatArray, indices: NDArray[np.intp]
) -> FloatArray:
    """Refit OLS on every resample at once, via batched normal equations.

    ``indices`` has shape ``(resamples, observations)``. Rows are resampled
    jointly across ``y`` and ``design`` so the regressor-error dependence that
    HAC exists for is preserved inside each resample.
    """
    y_batch = y[indices]
    x_batch = design[indices]
    xtx = np.einsum("btk,btl->bkl", x_batch, x_batch)
    xty = np.einsum("btk,bt->bk", x_batch, y_batch)
    ridge = 1e-12 * np.eye(design.shape[1])
    # ``xty`` is a stack of vectors, so it needs a trailing axis for the batched
    # solve and is squeezed straight back out.
    solved = np.linalg.solve(xtx + ridge, xty[:, :, None])
    return np.asarray(solved[:, :, 0], dtype=np.float64)


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorPanel:
    """FF5 plus momentum and the one-month bill, aligned on month labels."""

    periods: tuple[str, ...]
    factors: Mapping[str, FloatArray]
    risk_free: FloatArray
    provenance: Mapping[str, JsonValue]

    def window(self, start: str, end: str) -> tuple[NDArray[np.intp], tuple[str, ...]]:
        first, last = month_index(start), month_index(end)
        keep = [
            index
            for index, period in enumerate(self.periods)
            if first <= month_index(period) <= last
        ]
        return np.asarray(keep, dtype=np.intp), tuple(self.periods[i] for i in keep)

    def design(self, names: Sequence[str], rows: NDArray[np.intp]) -> FloatArray:
        return np.column_stack([self.factors[name][rows] for name in names])


def load_factor_panel(specification: Specification) -> FactorPanel:
    """Load FF5 and momentum from the same pinned French vintage as exp_001.

    The two files are joined on their MONTH LABELS, never on row position. The
    momentum file begins in 1927-01 and the five-factor file in 1963-07, so a
    positional join would shift momentum by 438 months against every other factor
    and leave every resulting number looking entirely plausible.
    """
    cache = RawCache()
    root = workspace_root()
    start = specification.sample_policy.start
    end = specification.sample_policy.end

    frames: dict[str, pd.DataFrame] = {}
    provenance: dict[str, JsonValue] = {}
    for dataset_id in ("french_us_ff5", "french_us_momentum"):
        dataset = french.get_dataset(dataset_id)
        entry = french.download(cache, dataset)
        parsed = french.parse(cache, entry, dataset=dataset)
        table = parsed.table("monthly")
        frames[dataset_id] = table.to_frame()
        manifest_path = root / "data-manifests" / f"{dataset_id}_monthly.json"
        provenance[dataset_id] = {
            "source_url": entry.url,
            "sha256_raw": entry.sha256,
            "sha256_normalized": table.sha256_normalized(),
            "retrieved_utc": entry.retrieved_utc,
            "source_last_modified": entry.last_modified,
            "parser_version": french.PARSER_VERSION,
            "committed_manifest_sha256": (
                read_manifest(manifest_path).sha256_manifest()
                if manifest_path.is_file()
                else None
            ),
            "rows_in_file": table.rows,
            "first_observation": table.first_observation,
            "last_observation": table.last_observation,
            "units": table.units,
            "unit_transform": table.unit_transform,
        }

    ff5 = frames["french_us_ff5"]
    momentum = frames["french_us_momentum"]
    momentum_labels = {str(label) for label in momentum.index}
    shared = [
        str(label)
        for label in ff5.index
        if str(label) in momentum_labels
        and month_index(start) <= month_index(str(label)) <= month_index(end)
    ]
    expected = month_count(start, end)
    if len(shared) != expected:
        raise FundExposureError(
            f"the French files jointly cover {len(shared)} of the {expected} months "
            f"in {start}..{end}; the frozen sample policy cannot be honoured and "
            "silently shortening it would change the experiment"
        )

    factors: dict[str, FloatArray] = {
        name: np.asarray(ff5.loc[shared, name].to_numpy(), dtype=np.float64)
        for name in ("Mkt-RF", "SMB", "HML", "RMW", "CMA")
    }
    factors["UMD"] = np.asarray(momentum.loc[shared, "Mom"].to_numpy(), dtype=np.float64)
    bill = np.asarray(ff5.loc[shared, "RF"].to_numpy(), dtype=np.float64)
    for name, series in (*factors.items(), ("RF", bill)):
        if not np.all(np.isfinite(series)):
            raise FundExposureError(f"{name} has a missing value inside {start}..{end}")

    return FactorPanel(
        periods=tuple(shared),
        factors=factors,
        risk_free=bill,
        provenance=provenance,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class FundSeries:
    """One share class' filed monthly total returns over the frozen window."""

    ticker: str
    series_id: str
    class_id: str
    periods: tuple[str, ...]
    returns: FloatArray
    missing_months: tuple[str, ...]
    filing_count: int
    amendment_count: int
    filings_held_out: int
    """Filings never downloaded because they can only cover held-out months."""
    warnings: tuple[str, ...]
    table: ParsedTable
    first_filing_sha256: str

    @property
    def complete(self) -> bool:
        return not self.missing_months


def fetch_fund_series(
    cache: RawCache,
    *,
    ticker: str,
    series_id: str,
    class_id: str,
    start: str,
    end: str,
) -> FundSeries:
    """Assemble one fund's Item B.5 history across every quarterly filing."""
    refs = nport.filing_index(cache, series_id)
    # The sample policy ends at ``end`` and months after it are HELD OUT. A filing
    # reports the three months ending on its own quarter end and reaches EDGAR
    # within 60 days of that, so nothing filed more than eight months after the
    # window closes can contain a month inside it. Those filings are not even
    # downloaded, which makes the holdout a property of the code rather than a
    # promise about what was ignored downstream.
    holdout_cutoff = period_from_index(month_index(end) + _HELD_OUT_FILING_MONTHS)
    filings: list[nport.NportFiling] = []
    skipped_after_window = 0
    for ref in refs:
        if not ref.form_type.startswith("NPORT-P"):
            continue
        if ref.filing_date[:7] > holdout_cutoff:
            skipped_after_window += 1
            continue
        filings.append(nport.fetch_filing(cache, ref))
        nport.throttle()
    if not filings:
        raise FundExposureError(f"{ticker}: EDGAR lists no NPORT-P filing for {series_id}")

    table = nport.build_return_table(
        filings, class_id=class_id, table_id=f"nport_{ticker.lower()}_monthly"
    )
    wanted = tuple(
        period_from_index(index)
        for index in range(month_index(start), month_index(end) + 1)
    )
    available = dict(zip(table.periods, (row[0] for row in table.values), strict=True))
    missing = tuple(period for period in wanted if available.get(period) is None)
    present = tuple(period for period in wanted if available.get(period) is not None)
    values = np.asarray(
        [available[period] for period in present], dtype=np.float64
    )
    return FundSeries(
        ticker=ticker,
        series_id=series_id,
        class_id=class_id,
        periods=present,
        returns=values,
        missing_months=missing,
        filing_count=len(filings),
        amendment_count=sum(1 for item in filings if item.form_type.endswith("/A")),
        filings_held_out=skipped_after_window,
        warnings=table.warnings,
        table=table,
        first_filing_sha256=filings[0].entry.sha256,
    )


def secondary_monthly_returns(cache: RawCache, ticker: str) -> tuple[dict[str, float], str]:
    """``{period: return}`` from the Yahoo chart endpoint, for cross-checking only.

    Raises on any failure. Callers catch and record "unavailable", because the
    secondary source is not research-grade and no result may depend on it: its
    only job is to make a silent adjustment error in the primary source visible.
    Returns are month-over-month changes in the adjusted close, which is Yahoo's
    own total-return construction and carries all of its documented problems.
    """
    adapter = YahooChartAdapter(
        range_="max", interval="1mo", transport="curl", attempts=1
    )
    series = adapter.fetch(cache, ticker)
    frame = series.table.to_frame()
    if "adjclose" not in frame.columns:
        raise FundExposureError(f"{ticker}: the chart response carried no adjusted close")
    values: dict[str, float] = {}
    previous: float | None = None
    for label, value in zip(frame.index, frame["adjclose"].to_numpy(), strict=True):
        current = float(value)
        if not math.isfinite(current) or current <= 0.0:
            previous = None
            continue
        if previous is not None:
            values[str(label)[:7]] = current / previous - 1.0
        previous = current
    return values, series.entry.sha256


# --------------------------------------------------------------------------- #
# The exposure regression
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class ExposureFit:
    """One fund, one specification, one era: loadings, alpha, and their honesty."""

    ticker: str
    specification: str
    era: str
    factor_names: tuple[str, ...]
    loadings: Mapping[str, float]
    standard_errors: Mapping[str, float]
    t_statistics: Mapping[str, float]
    p_values: Mapping[str, float]
    alpha_annual_percent: float
    alpha_se_annual_percent: float
    alpha_t: float
    alpha_p: float
    shrunk_alpha_annual_percent: float
    shrinkage_factor: float
    minimum_detectable_alpha_percent: float
    r_squared: float
    residual_volatility_annual_percent: float
    n_observations: int
    n_lags: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "specification": self.specification,
            "era": self.era,
            "loadings": dict(self.loadings),
            "standard_errors": dict(self.standard_errors),
            "t_statistics": dict(self.t_statistics),
            "p_values": dict(self.p_values),
            "alpha_annual_percent": self.alpha_annual_percent,
            "alpha_se_annual_percent": self.alpha_se_annual_percent,
            "alpha_t": self.alpha_t,
            "alpha_p": self.alpha_p,
            "shrunk_alpha_annual_percent": self.shrunk_alpha_annual_percent,
            "shrinkage_factor": self.shrinkage_factor,
            "minimum_detectable_alpha_percent": self.minimum_detectable_alpha_percent,
            "r_squared": self.r_squared,
            "residual_volatility_annual_percent": self.residual_volatility_annual_percent,
            "n_observations": self.n_observations,
            "hac_lags": self.n_lags,
        }


def fit_exposure(
    *,
    ticker: str,
    specification: str,
    era: str,
    excess_returns: FloatArray,
    design: FloatArray,
    factor_names: Sequence[str],
    n_lags: int,
    dispersion_annual_percent: float,
    power: float,
) -> ExposureFit:
    """OLS with Newey-West standard errors, annualised and shrunk correctly."""
    fit = hac_ols(excess_returns, design, n_lags=n_lags, add_constant=True)
    names = tuple(factor_names)

    # The intercept is a MONTHLY mean return in decimal. An annual alpha is twelve
    # of them, so both the point estimate and its standard error scale by 12.
    alpha_annual = float(fit.coefficients[0]) * MONTHS_PER_YEAR * 100.0
    alpha_se_annual = float(fit.standard_errors[0]) * MONTHS_PER_YEAR * 100.0
    shrunk, factor = shrink_alpha(
        alpha_annual, alpha_se_annual, dispersion_annual_percent=dispersion_annual_percent
    )

    total = float(np.sum((excess_returns - excess_returns.mean()) ** 2))
    residual_ss = float(np.sum(fit.residuals**2))
    r_squared = 1.0 - residual_ss / total if total > 0.0 else float("nan")

    return ExposureFit(
        ticker=ticker,
        specification=specification,
        era=era,
        factor_names=names,
        loadings={name: float(fit.coefficients[i + 1]) for i, name in enumerate(names)},
        standard_errors={
            name: float(fit.standard_errors[i + 1]) for i, name in enumerate(names)
        },
        t_statistics={name: float(fit.t_statistics[i + 1]) for i, name in enumerate(names)},
        p_values={name: float(fit.p_values[i + 1]) for i, name in enumerate(names)},
        alpha_annual_percent=alpha_annual,
        alpha_se_annual_percent=alpha_se_annual,
        alpha_t=float(fit.t_statistics[0]),
        alpha_p=float(fit.p_values[0]),
        shrunk_alpha_annual_percent=shrunk,
        shrinkage_factor=factor,
        minimum_detectable_alpha_percent=minimum_detectable_alpha(
            alpha_se_annual, power=power
        ),
        r_squared=r_squared,
        residual_volatility_annual_percent=float(
            np.std(fit.residuals, ddof=len(names) + 1)
            * math.sqrt(MONTHS_PER_YEAR)
            * 100.0
        ),
        n_observations=int(fit.n_observations),
        n_lags=int(fit.n_lags),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplicationFit:
    """What a long-only combination of cheap broad funds does to the product."""

    ticker: str
    basis: tuple[str, ...]
    weights: tuple[float, ...]
    tracking_difference_annual_percent: float
    tracking_error_annual_percent: float
    fee_premium_over_basis_percent: float
    """The product's net expense ratio less the weighted fee of its replication.

    Positive means the product costs more than the cheap combination that tracks
    it, which is what it should be: the whole question is whether the extra fee
    buys an exposure the combination cannot supply.
    """
    implementation_shortfall_percent: float
    tracking_difference_vs_market_percent: float
    tracking_error_vs_market_percent: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "basis": list(self.basis),
            "weights": list(self.weights),
            "tracking_difference_vs_combination_pp": (
                self.tracking_difference_annual_percent
            ),
            "tracking_error_vs_combination_pp": self.tracking_error_annual_percent,
            "fee_premium_over_basis_pp": self.fee_premium_over_basis_percent,
            "implementation_shortfall_pp": self.implementation_shortfall_percent,
            "tracking_difference_vs_market_pp": self.tracking_difference_vs_market_percent,
            "tracking_error_vs_market_pp": self.tracking_error_vs_market_percent,
        }


@dataclass(slots=True, kw_only=True)
class FundOutcome:
    """The per-fund verdict, with every falsifier clause that fired."""

    ticker: str
    series_name: str
    intended_factor: str
    intended_sign: int
    status: str
    clauses_fired: list[str] = field(default_factory=list)
    intended_loading: float = float("nan")
    intended_loading_se: float = float("nan")
    intended_loading_interval: tuple[float, float] = (float("nan"), float("nan"))
    intended_loading_first_half: float = float("nan")
    intended_loading_second_half: float = float("nan")
    max_drawdown_percent: float = float("nan")
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "series_name": self.series_name,
            "intended_factor": self.intended_factor,
            "intended_sign": self.intended_sign,
            "status": self.status,
            "falsifier_clauses_fired": list(self.clauses_fired),
            "intended_loading": self.intended_loading,
            "intended_loading_se": self.intended_loading_se,
            "intended_loading_interval": list(self.intended_loading_interval),
            "intended_loading_first_half": self.intended_loading_first_half,
            "intended_loading_second_half": self.intended_loading_second_half,
            "max_drawdown_percent": self.max_drawdown_percent,
            "notes": list(self.notes),
        }


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_002_fund_exposure.yaml"


def build_registry() -> ExperimentRegistry:
    """A registry holding exactly this experiment."""
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


# --------------------------------------------------------------------------- #
# The audit
# --------------------------------------------------------------------------- #


def _fetch_all_series(
    cache: RawCache,
    *,
    universe: Universe,
    comparator: str,
    basis: Sequence[str],
    start: str,
    end: str,
) -> tuple[dict[str, FundSeries], list[dict[str, JsonValue]]]:
    """Download Item B.5 histories for every fund that PASSED the screen.

    A fund that failed the screen is never fetched. That is the whole point of
    committing the universe first: a screen decision cannot be revised after
    seeing performance if the performance was never obtained.
    """
    wanted: dict[str, tuple[str, str, str]] = {}
    for fund in universe.passing:
        wanted[fund.ticker] = (fund.series_id, fund.class_id, fund.series_name)
    for ticker in (comparator, *basis):
        if ticker not in wanted:
            series_id, class_id, name = resolve_ticker(cache, ticker)
            wanted[ticker] = (series_id, class_id, name)

    series: dict[str, FundSeries] = {}
    failures: list[dict[str, JsonValue]] = []
    for ticker, (series_id, class_id, _name) in sorted(wanted.items()):
        try:
            series[ticker] = fetch_fund_series(
                cache,
                ticker=ticker,
                series_id=series_id,
                class_id=class_id,
                start=start,
                end=end,
            )
        except Exception as exc:
            failures.append(
                {
                    "ticker": ticker,
                    "series_id": series_id,
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )
    return series, failures


def _validate_data_path(
    *,
    comparator: str,
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
) -> dict[str, JsonValue]:
    """Gates that must pass before any fund result is believable.

    Item B.5 orders its three returns earliest-first, so the month ending on the
    reporting date is the THIRD. A reversed reading would shift every history by
    two months and leave every number looking plausible, so the alignment is
    tested rather than trusted: a cheap total-market fund must reproduce the
    market factor.
    """
    if comparator not in series:
        raise FundExposureError(
            f"the comparator {comparator} has no usable history, so nothing in this "
            "experiment can be benchmarked and no gate can be checked"
        )
    index = {period: position for position, period in enumerate(panel.periods)}
    rows = np.asarray([index[period] for period in periods], dtype=np.intp)
    available = dict(zip(series[comparator].periods, series[comparator].returns, strict=True))
    fund = np.asarray([available[period] for period in periods], dtype=np.float64)
    market_total = panel.factors["Mkt-RF"][rows] + panel.risk_free[rows]
    excess = fund - panel.risk_free[rows]

    correlation = float(np.corrcoef(fund, market_total)[0, 1])
    fit = hac_ols(excess, panel.factors["Mkt-RF"][rows][:, None], n_lags=6)
    beta = float(fit.coefficients[1])
    residual_ss = float(np.sum(fit.residuals**2))
    total_ss = float(np.sum((excess - excess.mean()) ** 2))
    r_squared = 1.0 - residual_ss / total_ss
    worst_month = periods[int(np.argmin(fund))]

    findings: list[str] = []
    if correlation < 0.99:
        findings.append(
            f"{comparator} correlates {correlation:.4f} with the market factor, below "
            "0.99. The month alignment or the share class is wrong."
        )
    if abs(beta - 1.0) > 0.05:
        findings.append(f"{comparator} has market beta {beta:.4f}, more than 0.05 from 1.00")
    if r_squared < 0.98:
        findings.append(f"{comparator} regression R-squared {r_squared:.4f} is below 0.98")
    if worst_month != "2020-03":
        findings.append(
            f"{comparator}'s worst month in the window is {worst_month}, not 2020-03. "
            "The COVID drawdown is the sharpest month in this window for any US "
            "equity fund, so this points at a month-offset error."
        )
    if findings:
        raise FundExposureError(
            "the data path failed its validation gates before any fund result was "
            "computed: " + "; ".join(findings)
        )
    return {
        "comparator": comparator,
        "correlation_with_market_total_return": correlation,
        "market_beta": beta,
        "r_squared": r_squared,
        "worst_month": worst_month,
        "worst_month_return_percent": float(np.min(fund)) * 100.0,
        "interpretation": (
            "The alignment of Item B.5's three returns to calendar months is "
            "confirmed against an independent series, not assumed."
        ),
    }


def _era_windows(specification: Specification) -> dict[str, tuple[str, str]]:
    return {era.name: (era.start, era.end) for era in specification.sample_policy.eras}


def _rows_for(panel: FactorPanel, periods: Sequence[str]) -> NDArray[np.intp]:
    index = {period: position for position, period in enumerate(panel.periods)}
    return np.asarray([index[period] for period in periods], dtype=np.intp)


def _excess(series: FundSeries, panel: FactorPanel, periods: Sequence[str]) -> FloatArray:
    available = dict(zip(series.periods, series.returns, strict=True))
    rows = _rows_for(panel, periods)
    values = np.asarray([available[period] for period in periods], dtype=np.float64)
    return values - panel.risk_free[rows]


def _total(series: FundSeries, periods: Sequence[str]) -> FloatArray:
    available = dict(zip(series.periods, series.returns, strict=True))
    return np.asarray([available[period] for period in periods], dtype=np.float64)


def _covered(series: FundSeries, periods: Sequence[str]) -> bool:
    return set(periods) <= set(series.periods)


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Audit every screened product's exposure, cost and replicability."""
    parameters = _mapping(specification.parameters, where="parameters")
    universe_block = _mapping(specification.universe, where="universe")
    comparators = _mapping(_at(universe_block, "comparators", where="universe"), where="universe")
    comparator = _text(
        _mapping(_at(comparators, "broad_market", where="comparators"), where="broad_market"),
        "ticker",
        where="comparators.broad_market",
    )
    combination = _mapping(
        _at(comparators, "synthetic_combination", where="comparators"),
        where="synthetic_combination",
    )
    basis = _strings(combination, "basis", where="comparators.synthetic_combination")

    shrinkage = _mapping(
        _at(parameters, "alpha_shrinkage", where="parameters"), where="parameters.alpha_shrinkage"
    )
    dispersion = _number(shrinkage, "sigma_true_annual_percent", where="alpha_shrinkage")
    minimum_loading = _number(parameters, "minimum_intended_loading", where="parameters")
    materiality = _number(parameters, "materiality_threshold_annual_percent", where="parameters")
    hac_lags = int(_number(parameters, "hac_lags", where="parameters"))
    minimum_months = int(_number(parameters, "minimum_monthly_observations", where="parameters"))
    power = _number(parameters, "power_target", where="parameters")
    rolling_window = int(_number(parameters, "rolling_window_months", where="parameters"))

    universe = load_universe()
    universe_digest = _sha256_file(universe_path())
    panel = load_factor_panel(specification)
    cache = RawCache()

    eras = _era_windows(specification)
    common_start, common_end = eras["common_period"]
    common_periods = tuple(
        period_from_index(index)
        for index in range(month_index(common_start), month_index(common_end) + 1)
    )

    series, fetch_failures = _fetch_all_series(
        cache,
        universe=universe,
        comparator=comparator,
        basis=basis,
        start=common_start,
        end=common_end,
    )
    gates = _validate_data_path(
        comparator=comparator, series=series, panel=panel, periods=common_periods
    )

    usable: list[ScreenedFund] = []
    coverage: list[dict[str, JsonValue]] = []
    for fund in universe.passing:
        record = series.get(fund.ticker)
        if record is None:
            coverage.append(
                {"ticker": fund.ticker, "usable": False, "reason": "no filings retrieved"}
            )
            continue
        complete = _covered(record, common_periods)
        coverage.append(
            {
                "ticker": fund.ticker,
                "usable": complete and len(record.periods) >= minimum_months,
                "months_available": len(record.periods),
                "missing_months": list(record.missing_months),
                "filings": record.filing_count,
                "amendments": record.amendment_count,
                "filings_held_out_after_window": record.filings_held_out,
                "reason": (
                    ""
                    if complete
                    else f"{len(record.missing_months)} month(s) have no filed return"
                ),
            }
        )
        if complete and len(record.periods) >= minimum_months:
            usable.append(fund)

    fits: list[ExposureFit] = []
    for fund in usable:
        excess = _excess(series[fund.ticker], panel, common_periods)
        rows = _rows_for(panel, common_periods)
        for name, factors in FACTOR_SPECIFICATIONS.items():
            fits.append(
                fit_exposure(
                    ticker=fund.ticker,
                    specification=name,
                    era="common_period",
                    excess_returns=excess,
                    design=panel.design(factors, rows),
                    factor_names=factors,
                    n_lags=hac_lags,
                    dispersion_annual_percent=dispersion,
                    power=power,
                )
            )

    half_fits: dict[tuple[str, str], ExposureFit] = {}
    for era_name in ("first_half", "second_half", "covid_drawdown", "value_reversal"):
        era_start, era_end = eras[era_name]
        era_periods = tuple(
            period_from_index(index)
            for index in range(month_index(era_start), month_index(era_end) + 1)
        )
        factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
        rows = _rows_for(panel, era_periods)
        for fund in usable:
            if not _covered(series[fund.ticker], era_periods):
                continue
            if len(era_periods) <= len(factors) + 2:
                continue
            half_fits[(fund.ticker, era_name)] = fit_exposure(
                ticker=fund.ticker,
                specification=PRIMARY_SPECIFICATION,
                era=era_name,
                excess_returns=_excess(series[fund.ticker], panel, era_periods),
                design=panel.design(factors, rows),
                factor_names=factors,
                n_lags=min(hac_lags, max(1, len(era_periods) // 6)),
                dispersion_annual_percent=dispersion,
                power=power,
            )

    # --- multiple testing over the WHOLE family: every fund x every specification
    alpha_p = np.asarray([fit.alpha_p for fit in fits], dtype=np.float64)
    bh = benjamini_hochberg(alpha_p, alpha=0.10) if alpha_p.size else None
    holm = holm_bonferroni(alpha_p, alpha=0.10) if alpha_p.size else None

    primary = {fit.ticker: fit for fit in fits if fit.specification == PRIMARY_SPECIFICATION}
    loading_p = np.asarray(
        [
            _intended_p_value(primary[fund.ticker], fund)
            for fund in usable
            if fund.ticker in primary
        ],
        dtype=np.float64,
    )
    loading_bh = benjamini_hochberg(loading_p, alpha=0.10) if loading_p.size else None

    # --- bootstrap intervals on the intended loading
    rng = context.rng
    intervals = _bootstrap_intervals(
        usable=usable,
        primary=primary,
        series=series,
        panel=panel,
        periods=common_periods,
        specification=specification,
        rng=rng,
    )

    replications = _replicate(
        usable=usable,
        series=series,
        panel=panel,
        periods=common_periods,
        comparator=comparator,
        basis=basis,
        universe=universe,
    )

    cross_source = _cross_check(cache, [fund.ticker for fund in usable], series, common_periods)

    outcomes = _verdicts(
        usable=usable,
        primary=primary,
        half_fits=half_fits,
        intervals=intervals,
        replications=replications,
        series=series,
        periods=common_periods,
        minimum_loading=minimum_loading,
        materiality=materiality,
    )

    rolling = _rolling_loadings(
        usable=usable,
        series=series,
        panel=panel,
        periods=common_periods,
        window=rolling_window,
    )

    cash_sensitivity = _cash_rate_sensitivity(panel, common_periods)

    pedestal = _model_misfit_pedestal(
        comparator=comparator,
        series=series,
        panel=panel,
        periods=common_periods,
        n_lags=hac_lags,
        dispersion_annual_percent=dispersion,
        power=power,
    )

    promoted = [item.ticker for item in outcomes if item.status == "exploratory"]
    summary = _summary_sentence(
        universe=universe,
        usable=usable,
        outcomes=outcomes,
        fits=fits,
        promoted=promoted,
        bh=bh,
    )

    estimates = _estimates(outcomes, primary, replications, intervals)

    diagnostics: dict[str, JsonValue] = {
        "universe": {
            "committed_file": str(universe_path().relative_to(workspace_root())),
            "sha256": universe_digest,
            "frame_quarter": universe.frame_quarter,
            "frame_series_count": universe.frame_series_count,
            "mandate_matches": universe.mandate_matches,
            "screened": len(universe.funds),
            "passed_screen": len(universe.passing),
            "usable_returns": len(usable),
            "attrition": plain_json(dict(universe.attrition)),
        },
        "screen": plain_json([fund.to_json() for fund in universe.funds]),
        "coverage": coverage,
        "fetch_failures": fetch_failures,
        "validation_gates": gates,
        "factor_provenance": dict(panel.provenance),
        "exposures": [fit.to_json() for fit in fits],
        "subperiod_exposures": [fit.to_json() for fit in half_fits.values()],
        "rolling_loadings": rolling,
        "replication": [item.to_json() for item in replications.values()],
        "cross_source_check": cross_source,
        "cash_rate_sensitivity": cash_sensitivity,
        "model_misfit_pedestal": pedestal,
        "multiple_testing": {
            "family_definition": (
                "every fund with usable returns times every model specification "
                "estimated, not only the funds and specification reported"
            ),
            "family_size": int(alpha_p.size),
            "funds": len(usable),
            "specifications": list(FACTOR_SPECIFICATIONS),
            "alpha": _correction_json(fits, bh, holm),
            "denominator_hostile_test": {
                "why": (
                    "A fund that failed the screen was never regressed and so has "
                    "no p-value, but the search still passed over it. Padding the "
                    "family to its full width with p = 1.0 cannot create a "
                    "rejection and strictly tightens both corrections, so this is "
                    "the most pessimistic honest accounting of how much looking "
                    "was done."
                ),
                "tests_run": inflated_family(
                    [fit.alpha_p for fit in fits], family_size=len(fits)
                ),
                "all_funds_that_passed_the_screen": inflated_family(
                    [fit.alpha_p for fit in fits],
                    family_size=max(len(fits), len(universe.passing) * len(FACTOR_SPECIFICATIONS)),
                ),
                "every_mandate_matching_series_screened": inflated_family(
                    [fit.alpha_p for fit in fits],
                    family_size=max(len(fits), len(universe.funds) * len(FACTOR_SPECIFICATIONS)),
                ),
            },
            "intended_loading": {
                "family_size": int(loading_p.size),
                "rejected_uncorrected": (
                    int(np.sum(loading_p <= 0.05)) if loading_p.size else 0
                ),
                "rejected_benjamini_hochberg": (
                    int(np.sum(loading_bh.rejected)) if loading_bh is not None else 0
                ),
            },
        },
        "outcomes": [item.to_json() for item in outcomes],
        "promoted": promoted,
        "unobservable": {
            "realised_taxable_distributions": (
                "NOT AVAILABLE. Form N-PORT reports a single total return and no "
                "distribution split; the income/capital-gain history is in the "
                "annual report on Form N-CSR as unstructured HTML. Recorded as a "
                "gap rather than estimated."
            ),
            "portfolio_turnover": (
                "NOT AVAILABLE from Form N-PORT for the same reason. The fund's "
                "internal trading cost is therefore inside the tracking difference "
                "and is reported there rather than modelled."
            ),
            "securities_lending_split": (
                "Disclosed by sponsor policy rather than per fund per year in this "
                "source. Whatever the fund kept is already inside net asset value "
                "and therefore inside every return here."
            ),
        },
    }

    caveats = _caveats(universe, usable, fits, outcomes)

    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=summary,
        estimates=tuple(estimates),
        diagnostics=diagnostics,
        caveats=tuple(caveats),
        frames=_frames(universe, fits, replications, outcomes, coverage),
    )


# --------------------------------------------------------------------------- #
# Helpers the audit calls
# --------------------------------------------------------------------------- #


def _sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _intended_p_value(fit: ExposureFit, fund: ScreenedFund) -> float:
    """One-sided p-value that the intended loading exceeds nothing, in its own sign."""
    factor = fund.intended_factor
    if factor is None or factor not in fit.loadings:
        return 1.0
    signed_t = fit.t_statistics[factor] * (fund.intended_sign or 1)
    return float(norm.sf(signed_t))


def _bootstrap_intervals(
    *,
    usable: Sequence[ScreenedFund],
    primary: Mapping[str, ExposureFit],
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
    specification: Specification,
    rng: np.random.Generator,
) -> dict[str, dict[str, JsonValue]]:
    """Stationary block-bootstrap intervals for the intended loading.

    Rows are resampled JOINTLY across the fund return and the whole factor
    design, so the dependence between regressors and errors that HAC exists to
    handle survives inside each resample. Resampling residuals alone would assume
    the very independence the block length is there to avoid assuming.
    """
    from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices

    resamples = specification.inference.resamples
    confidence = specification.inference.confidence_level
    lower_q = 100.0 * (1.0 - confidence) / 2.0
    upper_q = 100.0 - lower_q
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    rows = _rows_for(panel, periods)
    design = np.column_stack([np.ones(len(periods)), panel.design(factors, rows)])

    out: dict[str, dict[str, JsonValue]] = {}
    for block_length in (3.0, 6.0, 12.0):
        indices = stationary_bootstrap_indices(len(periods), block_length, resamples, rng)
        for fund in usable:
            fit = primary.get(fund.ticker)
            if fit is None or fund.intended_factor is None:
                continue
            column = factors.index(fund.intended_factor) + 1
            draws = _bootstrap_coefficients(
                _excess(series[fund.ticker], panel, periods), design, indices
            )[:, column]
            record = out.setdefault(fund.ticker, {})
            record[f"block_{int(block_length)}"] = [
                float(np.percentile(draws, lower_q)),
                float(np.percentile(draws, upper_q)),
            ]
    return out


def _replicate(
    *,
    usable: Sequence[ScreenedFund],
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
    comparator: str,
    basis: Sequence[str],
    universe: Universe,
) -> dict[str, ReplicationFit]:
    """Fit the cheap long-only combination that best tracks each product."""
    all_basis = [ticker for ticker in basis if ticker in series]
    if comparator not in series or not all_basis:
        return {}
    facts = load_product_facts()
    market = _total(series[comparator], periods)
    del universe

    out: dict[str, ReplicationFit] = {}
    for fund in usable:
        if fund.ticker == comparator:
            continue
        # A fund is never part of the basis that replicates it. Three of the four
        # building blocks are themselves audited products, and leaving one in
        # would hand it a weight of one and a tracking difference of exactly zero.
        available_basis = [ticker for ticker in all_basis if ticker != fund.ticker]
        if not available_basis:
            continue
        basis_matrix = np.column_stack(
            [_total(series[ticker], periods) for ticker in available_basis]
        )
        target = _total(series[fund.ticker], periods)
        weights = replicating_weights(target, basis_matrix)
        combination = basis_matrix @ weights
        difference = target - combination
        against_market = target - market
        # Positive: what the product costs above the combination that replicates it.
        basis_fee = sum(
            float(weights[i]) * _net_expense(facts.get(ticker))
            for i, ticker in enumerate(available_basis)
        )
        fund_fee = _net_expense(facts.get(fund.ticker, fund.facts))
        tracking_difference = float(np.mean(difference)) * MONTHS_PER_YEAR * 100.0
        fee_premium = fund_fee - basis_fee
        out[fund.ticker] = ReplicationFit(
            ticker=fund.ticker,
            basis=tuple(available_basis),
            weights=tuple(float(value) for value in weights),
            tracking_difference_annual_percent=tracking_difference,
            tracking_error_annual_percent=float(np.std(difference, ddof=1))
            * math.sqrt(MONTHS_PER_YEAR)
            * 100.0,
            fee_premium_over_basis_percent=fee_premium,
            # POSITIVE means the product lost MORE to its cheap replication than
            # its extra fee explains: implementation cost the shareholder paid on
            # top of the published expense ratio.
            implementation_shortfall_percent=-tracking_difference - fee_premium,
            tracking_difference_vs_market_percent=float(np.mean(against_market))
            * MONTHS_PER_YEAR
            * 100.0,
            tracking_error_vs_market_percent=float(np.std(against_market, ddof=1))
            * math.sqrt(MONTHS_PER_YEAR)
            * 100.0,
        )
    return out


def _net_expense(facts: ProductFacts | None) -> float:
    if facts is None or facts.net_expense_ratio_percent is None:
        return 0.0
    return facts.net_expense_ratio_percent


def _cross_check(
    cache: RawCache,
    tickers: Sequence[str],
    series: Mapping[str, FundSeries],
    periods: Sequence[str],
) -> dict[str, JsonValue]:
    """Compare the filed return against the secondary source, month by month.

    Two independent measurements of the same quantity are the only cheap way to
    see a silent adjustment error. Agreement is evidence about the data and about
    nothing else; it does not make either source research-grade.
    """
    rows: list[dict[str, JsonValue]] = []
    unavailable: list[str] = []
    for ticker in tickers:
        record = series.get(ticker)
        if record is None:
            continue
        try:
            secondary, digest = secondary_monthly_returns(cache, ticker)
        except Exception as exc:
            unavailable.append(f"{ticker}: {type(exc).__name__}")
            continue
        filed = dict(zip(record.periods, record.returns, strict=True))
        shared = [period for period in periods if period in filed and period in secondary]
        if len(shared) < 12:
            unavailable.append(f"{ticker}: only {len(shared)} overlapping months")
            continue
        differences = np.asarray(
            [filed[period] - secondary[period] for period in shared], dtype=np.float64
        )
        rows.append(
            {
                "ticker": ticker,
                "overlapping_months": len(shared),
                "median_absolute_difference_bp": float(np.median(np.abs(differences))) * 10000.0,
                "max_absolute_difference_bp": float(np.max(np.abs(differences))) * 10000.0,
                "mean_difference_bp": float(np.mean(differences)) * 10000.0,
                "secondary_sha256": digest,
            }
        )
    return {
        "source": "Yahoo chart endpoint, monthly adjusted close, via curl",
        "status": (
            "EXPLORATORY and not research-grade (decision 0002). Used only to "
            "cross-check the filed returns; no result depends on it."
        ),
        "compared": rows,
        "unavailable": unavailable,
    }


def _verdicts(
    *,
    usable: Sequence[ScreenedFund],
    primary: Mapping[str, ExposureFit],
    half_fits: Mapping[tuple[str, str], ExposureFit],
    intervals: Mapping[str, Mapping[str, JsonValue]],
    replications: Mapping[str, ReplicationFit],
    series: Mapping[str, FundSeries],
    periods: Sequence[str],
    minimum_loading: float,
    materiality: float,
) -> list[FundOutcome]:
    """Apply the frozen falsifier, clause by clause, and record which ones fired."""
    outcomes: list[FundOutcome] = []
    for fund in usable:
        fit = primary.get(fund.ticker)
        outcome = FundOutcome(
            ticker=fund.ticker,
            series_name=fund.series_name,
            intended_factor=fund.intended_factor or "",
            intended_sign=fund.intended_sign,
            status="unresolved",
        )
        if fit is None or fund.intended_factor is None:
            outcome.notes.append("no primary fit; nothing to decide")
            outcomes.append(outcome)
            continue

        sign = fund.intended_sign or 1
        signed = fit.loadings[fund.intended_factor] * sign
        outcome.intended_loading = signed
        outcome.intended_loading_se = fit.standard_errors[fund.intended_factor]

        interval = intervals.get(fund.ticker, {}).get("block_6")
        if isinstance(interval, list) and len(interval) == 2:
            low, high = float(interval[0]) * sign, float(interval[1]) * sign
            outcome.intended_loading_interval = (min(low, high), max(low, high))

        first = half_fits.get((fund.ticker, "first_half"))
        second = half_fits.get((fund.ticker, "second_half"))
        if first is not None:
            outcome.intended_loading_first_half = first.loadings[fund.intended_factor] * sign
        if second is not None:
            outcome.intended_loading_second_half = second.loadings[fund.intended_factor] * sign

        equity = np.cumprod(1.0 + _total(series[fund.ticker], periods))
        outcome.max_drawdown_percent = drawdown_summary(equity).max_drawdown * 100.0

        # (a) the intended exposure is not there
        if signed < minimum_loading:
            outcome.clauses_fired.append(
                f"(a) intended {fund.intended_factor} loading {signed:+.3f} is below "
                f"{minimum_loading:.2f}"
            )
        # (b) the exposure changes sign across the fixed split
        if (
            math.isfinite(outcome.intended_loading_first_half)
            and math.isfinite(outcome.intended_loading_second_half)
            and outcome.intended_loading_first_half * outcome.intended_loading_second_half < 0.0
        ):
            outcome.clauses_fired.append(
                f"(b) intended loading flips sign between halves: "
                f"{outcome.intended_loading_first_half:+.3f} then "
                f"{outcome.intended_loading_second_half:+.3f}"
            )
        replication = replications.get(fund.ticker)
        if replication is not None:
            # (c) the cheap combination beat it by more than its fee premium plus 0.50
            if replication.implementation_shortfall_percent > 0.50:
                outcome.clauses_fired.append(
                    f"(c) lost {-replication.tracking_difference_annual_percent:+.2f} pp/yr "
                    f"to its cheap replication against a fee premium of only "
                    f"{replication.fee_premium_over_basis_percent:+.2f} pp/yr"
                )
            # (d) total cost above the comparator without a corresponding exposure
            total_cost = _net_expense(fund.facts) + max(
                0.0, -replication.tracking_difference_annual_percent
            )
            if total_cost > materiality and signed < minimum_loading:
                outcome.clauses_fired.append(
                    f"(d) total cost of ownership {total_cost:.2f} pp/yr exceeds "
                    f"{materiality:.2f} with no corresponding exposure"
                )

        low, high = outcome.intended_loading_interval
        if outcome.clauses_fired:
            outcome.status = "rejected"
        elif math.isfinite(low) and low <= minimum_loading <= high:
            outcome.status = "unresolved"
            outcome.notes.append(
                f"the 95% interval [{low:+.3f}, {high:+.3f}] contains the "
                f"{minimum_loading:.2f} threshold, which is what a 72-month window "
                "usually produces"
            )
        else:
            outcome.status = "exploratory"
        outcomes.append(outcome)
    return outcomes


def _rolling_loadings(
    *,
    usable: Sequence[ScreenedFund],
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
    window: int,
) -> list[dict[str, JsonValue]]:
    """Rolling intended-factor loading, to test stability instead of assuming it."""
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    rows = _rows_for(panel, periods)
    design = np.column_stack([np.ones(len(periods)), panel.design(factors, rows)])
    out: list[dict[str, JsonValue]] = []
    for fund in usable:
        if fund.intended_factor is None:
            continue
        column = factors.index(fund.intended_factor) + 1
        y = _excess(series[fund.ticker], panel, periods)
        values: list[float] = []
        labels: list[str] = []
        for end in range(window, len(periods) + 1):
            block = slice(end - window, end)
            beta, *_ = np.linalg.lstsq(design[block], y[block], rcond=None)
            values.append(float(beta[column]) * (fund.intended_sign or 1))
            labels.append(periods[end - 1])
        if not values:
            continue
        out.append(
            {
                "ticker": fund.ticker,
                "factor": fund.intended_factor,
                "window_months": window,
                "windows": len(values),
                "first_window_end": labels[0],
                "last_window_end": labels[-1],
                "minimum": min(values),
                "maximum": max(values),
                "range": max(values) - min(values),
                "sign_changes": sum(
                    1 for i in range(1, len(values)) if values[i] * values[i - 1] < 0.0
                ),
                "values": values,
            }
        )
    return out


def _cash_rate_sensitivity(panel: FactorPanel, periods: Sequence[str]) -> dict[str, JsonValue]:
    """What substituting each alternative cash series would do to every alpha.

    A different cash rate shifts every excess return by the same amount in every
    month, so it moves an alpha by exactly the mean rate difference and moves no
    loading at all. That makes the size of the effect computable exactly rather
    than needing a re-run per series, and it makes clear that the choice of cash
    series cannot have produced any exposure result.
    """
    from portfolio_edge.data import fred

    cache = RawCache()
    rows = _rows_for(panel, periods)
    # French's RF is a decimal rate per month; twelve of them, in percent, is the
    # annual figure that a FRED annualised rate can be compared against.
    french_mean_annual = float(np.mean(panel.risk_free[rows])) * MONTHS_PER_YEAR * 100.0
    out: dict[str, JsonValue] = {
        "primary": "French one-month Treasury bill, from the same file as the factors",
        "primary_mean_annual_percent": french_mean_annual,
        "why_it_matters": (
            "Mkt-RF is the market return less the one-month bill, so an excess "
            "return taken over any other rate pushes the spread between the two "
            "straight into the intercept. Loadings are unaffected: a constant "
            "shift in the dependent variable moves only the intercept."
        ),
        "alternatives": [],
    }
    alternatives: list[dict[str, JsonValue]] = []
    for series_id in ("TB3MS", "DGS3MO", "DFF"):
        try:
            entry = fred.download(cache, series_id)
            table = fred.parse(cache, entry, series_id)
        except Exception as exc:
            alternatives.append({"series": series_id, "error": f"{type(exc).__name__}: {exc}"})
            continue
        # UNITS. FRED parses these to ``decimal_per_year`` -- 0.0366 means 3.66%
        # a year -- while French's RF is a decimal rate PER MONTH. Comparing the
        # two without converting is a factor-of-100 error that would have printed
        # a +2.6 pp/yr alpha shift where the truth is a few basis points, so the
        # units are asserted rather than assumed.
        if table.units != "decimal_per_year":
            alternatives.append(
                {
                    "series": series_id,
                    "error": (
                        f"expected decimal_per_year, got {table.units!r}; refusing to "
                        "convert a series whose units have changed"
                    ),
                }
            )
            continue
        monthly: dict[str, list[float]] = {}
        for label, row in zip(table.periods, table.values, strict=True):
            value = row[0]
            if value is None:
                continue
            monthly.setdefault(str(label)[:7], []).append(float(value))
        wanted = [period for period in periods if period in monthly]
        if not wanted:
            alternatives.append({"series": series_id, "error": "no overlap with the window"})
            continue
        # Daily series are averaged within a month first, so a month with more
        # observations does not get more weight than one with fewer.
        annual = 100.0 * float(np.mean([float(np.mean(monthly[period])) for period in wanted]))
        alternatives.append(
            {
                "series": series_id,
                "months_matched": len(wanted),
                "mean_annual_percent": annual,
                "alpha_shift_pp_per_year": french_mean_annual - annual,
                "loading_shift": 0.0,
            }
        )
    out["alternatives"] = alternatives
    return out




def _model_misfit_pedestal(
    *,
    comparator: str,
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
    n_lags: int,
    dispersion_annual_percent: float,
    power: float,
) -> dict[str, JsonValue]:
    """The alpha the factor model gives a fund that is, by construction, the market.

    The single most important calibration on this page. A cap-weighted total-market
    fund holds the market portfolio, so under a correctly specified model its alpha
    must be approximately minus its expense ratio -- three basis points. Anything
    further from zero is the model failing to span this window, not the fund doing
    something.

    Whatever that number is, EVERY fund's alpha carries it, because every fund is
    priced by the same six factors over the same 72 months. So it is measured and
    reported beside the fund alphas rather than left for a reader to infer, and a
    fund's alpha is meaningful only as a distance from this pedestal, never as a
    distance from zero.
    """
    if comparator not in series:
        return {"available": False, "reason": f"{comparator} has no usable history"}
    rows = _rows_for(panel, periods)
    excess = _excess(series[comparator], panel, periods)
    by_specification: dict[str, JsonValue] = {}
    for name, factors in FACTOR_SPECIFICATIONS.items():
        fit = fit_exposure(
            ticker=comparator,
            specification=name,
            era="common_period",
            excess_returns=excess,
            design=panel.design(factors, rows),
            factor_names=factors,
            n_lags=n_lags,
            dispersion_annual_percent=dispersion_annual_percent,
            power=power,
        )
        by_specification[name] = {
            "alpha_annual_percent": fit.alpha_annual_percent,
            "alpha_se_annual_percent": fit.alpha_se_annual_percent,
            "alpha_t": fit.alpha_t,
            "market_beta": fit.loadings["Mkt-RF"],
            "r_squared": fit.r_squared,
        }
    primary = by_specification[PRIMARY_SPECIFICATION]
    assert isinstance(primary, Mapping)
    return {
        "available": True,
        "comparator": comparator,
        "by_specification": by_specification,
        "pedestal_annual_percent": primary["alpha_annual_percent"],
        "interpretation": (
            "A cap-weighted total-market fund IS the market portfolio, so its alpha "
            "under a correctly specified model should be about minus its expense "
            "ratio. The distance of this number from that is model misfit shared by "
            "every fund in the audit. Read each fund's alpha as a distance from this "
            "pedestal, not from zero."
        ),
    }


def _correction_json(
    fits: Sequence[ExposureFit], bh: object, holm: object
) -> dict[str, JsonValue]:
    """What the multiple-testing correction did to the alpha family."""
    from portfolio_edge.inference.multiple_testing import MultipleTestingResult

    raw = [fit.alpha_p for fit in fits]
    payload: dict[str, JsonValue] = {
        "tests": len(raw),
        "rejected_uncorrected_at_0_05": sum(1 for value in raw if value <= 0.05),
        "rejected_uncorrected_at_0_10": sum(1 for value in raw if value <= 0.10),
    }
    if isinstance(bh, MultipleTestingResult):
        payload["benjamini_hochberg_alpha"] = bh.alpha
        payload["rejected_benjamini_hochberg"] = int(np.sum(bh.rejected))
        payload["survivors_benjamini_hochberg"] = [
            {
                "ticker": fits[i].ticker,
                "specification": fits[i].specification,
                "alpha_annual_percent": fits[i].alpha_annual_percent,
                "shrunk_alpha_annual_percent": fits[i].shrunk_alpha_annual_percent,
                "raw_p": fits[i].alpha_p,
                "adjusted_p": float(bh.adjusted_p_values[i]),
            }
            for i in range(len(fits))
            if bool(bh.rejected[i])
        ]
    if isinstance(holm, MultipleTestingResult):
        payload["rejected_holm_bonferroni"] = int(np.sum(holm.rejected))
        payload["holm_note"] = (
            "Holm-Bonferroni is valid under arbitrary dependence. These tests are "
            "NOT independent: the same six factors, the same window, and three "
            "nested specifications per fund, so the Benjamini-Hochberg count is an "
            "OPTIMISTIC bound and Holm is the defensible one."
        )
    return payload


def inflated_family(
    p_values: Sequence[float], *, family_size: int, alpha: float = 0.10
) -> dict[str, JsonValue]:
    """Re-run the correction with the denominator widened to ``family_size``.

    The hostile test the specification demands: a fund that failed the screen was
    never regressed, so it contributes no p-value -- but the *search* still passed
    over it, and a denominator counting only the tests that happened understates
    how much looking was done. Padding the family to its full width with
    ``p = 1.0`` is the conservative device: it cannot create a rejection and it
    strictly tightens both corrections, so whatever survives here survives the
    most pessimistic accounting of the search.
    """
    observed = list(p_values)
    if family_size < len(observed):
        raise ValueError(
            f"family_size {family_size} is smaller than the {len(observed)} tests run"
        )
    padded = np.asarray(observed + [1.0] * (family_size - len(observed)), dtype=np.float64)
    bh = benjamini_hochberg(padded, alpha=alpha)
    holm = holm_bonferroni(padded, alpha=alpha)
    return {
        "family_size": family_size,
        "tests_actually_run": len(observed),
        "padded_with_p_equal_one": family_size - len(observed),
        "rejected_benjamini_hochberg": int(np.sum(bh.rejected[: len(observed)])),
        "rejected_holm_bonferroni": int(np.sum(holm.rejected[: len(observed)])),
    }


def _summary_sentence(
    *,
    universe: Universe,
    usable: Sequence[ScreenedFund],
    outcomes: Sequence[FundOutcome],
    fits: Sequence[ExposureFit],
    promoted: Sequence[str],
    bh: object,
) -> str:
    from portfolio_edge.inference.multiple_testing import MultipleTestingResult

    survivors = int(np.sum(bh.rejected)) if isinstance(bh, MultipleTestingResult) else 0
    rejected = sum(1 for item in outcomes if item.status == "rejected")
    unresolved = sum(1 for item in outcomes if item.status == "unresolved")
    return (
        f"Screened {universe.mandate_matches} mandate-matching fund series from the "
        f"{universe.frame_quarter} N-PORT census; {len(universe.passing)} passed the "
        f"predeclared screen and {len(usable)} had complete filed monthly returns over "
        f"the frozen window. {len(promoted)} product(s) reached `exploratory`, "
        f"{rejected} were `rejected` on the frozen falsifier and {unresolved} are "
        f"`unresolved`. Across the full multiple-testing family of {len(fits)} "
        f"fund-by-specification alpha tests, {survivors} survive Benjamini-Hochberg at "
        "0.10. The binding constraint is the data contract and a 72-month window, "
        "not the evidence."
    )


def _estimates(
    outcomes: Sequence[FundOutcome],
    primary: Mapping[str, ExposureFit],
    replications: Mapping[str, ReplicationFit],
    intervals: Mapping[str, Mapping[str, JsonValue]],
) -> list[Estimate]:
    """One estimate per fund for the primary metric, plus its alpha, both shrunk."""
    out: list[Estimate] = []
    for outcome in outcomes:
        fit = primary.get(outcome.ticker)
        if fit is None:
            continue
        low, high = outcome.intended_loading_interval
        out.append(
            Estimate(
                name=f"{outcome.ticker} intended {outcome.intended_factor} loading",
                value=outcome.intended_loading,
                units="loading (dimensionless)",
                interval=(low, high) if math.isfinite(low) else None,
                interval_method=(
                    "stationary block bootstrap, 95%, mean block 6m, joint resampling "
                    "of the return and the whole design"
                )
                if math.isfinite(low)
                else "",
                uncertainty_unavailable_reason=(
                    "" if math.isfinite(low) else "no bootstrap interval was computed"
                ),
                cost_basis=CostBasis.NET_OPTIMISTIC,
                n_obs=fit.n_observations,
                notes=f"sign-adjusted for the mandate; status {outcome.status}",
            )
        )
        out.append(
            Estimate(
                name=f"{outcome.ticker} shrunk alpha",
                value=fit.shrunk_alpha_annual_percent,
                units="percentage points per year",
                interval=None,
                uncertainty_unavailable_reason=(
                    "A posterior mean under a fixed prior has no sampling interval of "
                    f"its own. The raw alpha is {fit.alpha_annual_percent:+.2f} pp/yr "
                    f"with HAC standard error {fit.alpha_se_annual_percent:.2f}, "
                    f"shrinkage factor {fit.shrinkage_factor:.3f}, and a minimum "
                    f"detectable alpha at 80% power of "
                    f"{fit.minimum_detectable_alpha_percent:.2f} pp/yr."
                ),
                cost_basis=CostBasis.NET_OPTIMISTIC,
                n_obs=fit.n_observations,
                notes=(
                    "NOT a promotion criterion in either direction. A positive alpha "
                    "over a short history is not evidence of future manager skill."
                ),
            )
        )
        replication = replications.get(outcome.ticker)
        if replication is not None:
            out.append(
                Estimate(
                    name=f"{outcome.ticker} implementation shortfall vs cheap replication",
                    value=replication.implementation_shortfall_percent,
                    units="percentage points per year",
                    interval=None,
                    uncertainty_unavailable_reason=(
                        "The replicating weights are fitted IN SAMPLE, so this is a "
                        "best case for the replication and a hard test for the "
                        "product. A sampling interval around a look-ahead quantity "
                        "would imply a precision the construction does not have."
                    ),
                    cost_basis=CostBasis.NET_OPTIMISTIC,
                    notes=f"basis {list(replication.basis)}",
                )
            )
    del intervals
    return out


def _caveats(
    universe: Universe,
    usable: Sequence[ScreenedFund],
    fits: Sequence[ExposureFit],
    outcomes: Sequence[FundOutcome],
) -> list[str]:
    median_mde = (
        float(np.median([fit.minimum_detectable_alpha_percent for fit in fits]))
        if fits
        else float("nan")
    )
    attrition = universe.attrition.get("series_present_in_frame_and_absent_at_follow_up", "?")
    born = universe.attrition.get("series_absent_from_frame_and_present_at_follow_up", "?")
    return [
        "EXPLORATORY. Decision 0002 stands: this may not promote a sleeve and may "
        "not appear in the app as a finding.",
        "The window is 72 months. The median minimum detectable alpha at 80% power "
        f"is {median_mde:.2f} pp/yr, which is larger than any plausible true alpha, "
        "so a confidence interval containing zero here is a statement about the "
        "window and not about the fund.",
        "Every alpha is shrunk by its own factor from its own standard error. The "
        "raw alpha is reported beside it and must never be quoted alone.",
        "Item B.5 returns are fund-reported and unaudited. Form N-PORT General "
        "Instruction G lets each filer use its own internal methodology, so returns "
        "are not guaranteed to be computed identically across funds.",
        "Public N-PORT filings begin in 2019, so the universe cannot see any fund "
        f"that closed before then. Within the window {attrition} mandate-matching "
        f"series disappeared and {born} launched; a universe assembled today would "
        "contain the second group and none of the first. The measured attrition is "
        "a LOWER BOUND on survivorship contamination.",
        "The replicating combination is fitted in sample. An investor could not have "
        "known those weights in advance, so it is a best case for the replication "
        "and the comparison against it is deliberately hard on the product.",
        "Realised taxable distributions and portfolio turnover are NOT in Form "
        "N-PORT and are recorded as gaps. No tax haircut is applied to any return.",
        "The HML/RMW volatility band inherited from the Phase 1 gate is carried by "
        "anything that divides by those volatilities. Nothing here does: every "
        "figure is a loading, a mean or a difference of means.",
        f"{len(usable)} funds cleared every screen and had complete returns; "
        f"{sum(1 for item in outcomes if item.status == 'rejected')} were rejected on "
        "the frozen falsifier, which is a statement about delivered exposure and "
        "cost, not about whether the underlying factor exists.",
    ]


def _frames(
    universe: Universe,
    fits: Sequence[ExposureFit],
    replications: Mapping[str, ReplicationFit],
    outcomes: Sequence[FundOutcome],
    coverage: Sequence[Mapping[str, JsonValue]],
) -> dict[str, pd.DataFrame]:
    screen_rows = [
        {
            "ticker": fund.ticker,
            "series_name": fund.series_name,
            "passed": fund.passed,
            "failed_criterion": fund.failed_criterion or "",
            "failure_detail": fund.failure_detail,
            "net_assets_frame_usd": fund.net_assets_frame,
            "net_assets_follow_up_usd": fund.net_assets_follow_up,
            "still_filing": fund.still_filing_at_follow_up,
            "net_expense_ratio_percent": _net_expense(fund.facts),
            "intended_factor": fund.intended_factor or "",
            "intended_sign": fund.intended_sign,
        }
        for fund in universe.funds
    ]
    exposure_rows = []
    for fit in fits:
        row: dict[str, object] = {
            "ticker": fit.ticker,
            "specification": fit.specification,
            "era": fit.era,
            "alpha_annual_percent": fit.alpha_annual_percent,
            "alpha_se_annual_percent": fit.alpha_se_annual_percent,
            "alpha_t": fit.alpha_t,
            "shrunk_alpha_annual_percent": fit.shrunk_alpha_annual_percent,
            "shrinkage_factor": fit.shrinkage_factor,
            "mde_alpha_annual_percent": fit.minimum_detectable_alpha_percent,
            "r_squared": fit.r_squared,
            "residual_vol_annual_percent": fit.residual_volatility_annual_percent,
            "n_observations": fit.n_observations,
        }
        row.update({f"beta_{name}": value for name, value in fit.loadings.items()})
        row.update({f"se_{name}": value for name, value in fit.standard_errors.items()})
        exposure_rows.append(row)
    return {
        "screen": pd.DataFrame(screen_rows),
        "exposures": pd.DataFrame(exposure_rows),
        "replication": pd.DataFrame([item.to_json() for item in replications.values()]),
        "outcomes": pd.DataFrame([item.to_json() for item in outcomes]),
        "coverage": pd.DataFrame(list(coverage)),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _build_universe_command(specification: Specification) -> int:
    """Screen the census and write the committed universe, before any return."""
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
        intended_factor_map=intended_factor_map(specification),
    )
    path = write_universe(universe)
    manifests = workspace_root() / "data-manifests"
    for quarter in (universe.frame_quarter, universe.follow_up_quarter):
        frame_manifest(cache, quarter).write(manifests)

    print(f"universe written to {path}")
    print(f"  frame {universe.frame_quarter}: {universe.frame_series_count} NPORT-P series")
    print(f"  mandate matches: {universe.mandate_matches}")
    print(f"  screened and recorded: {len(universe.funds)}")
    print(f"  passed: {len(universe.passing)}")
    counts: dict[str, int] = {}
    for fund in universe.funds:
        if fund.failed_criterion:
            counts[fund.failed_criterion] = counts.get(fund.failed_criterion, 0) + 1
    for criterion, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"    failed {criterion}: {count}")
    print(f"  attrition: {json.dumps(dict(universe.attrition), indent=2)[:400]}")
    for fund in universe.passing:
        print(
            f"    {fund.ticker:<6} {(fund.net_assets_frame or 0) / 1e9:8.2f}bn  "
            f"{fund.intended_factor or '?':<5} {fund.series_name[:56]}"
        )
    return 0


def _as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    diagnostics = result.diagnostics
    lines = [result.summary, ""]

    universe = diagnostics.get("universe")
    if isinstance(universe, Mapping):
        attrition = universe.get("attrition")
        lines.append(
            f"Universe: frame {universe['frame_quarter']} with "
            f"{universe['frame_series_count']} NPORT-P series, "
            f"{universe['mandate_matches']} mandate matches, "
            f"{universe['passed_screen']} passed, {universe['usable_returns']} usable."
        )
        if isinstance(attrition, Mapping):
            lines.append(
                "  attrition (LOWER BOUND): "
                f"{attrition['series_present_in_frame_and_absent_at_follow_up']} of "
                f"{attrition['mandate_qualifying_series_in_frame']} mandate-qualifying "
                f"series gone by the follow-up quarter "
                f"({float(str(attrition['attrition_rate'])) * 100:.1f}%); "
                f"{attrition['series_absent_from_frame_and_present_at_follow_up']} "
                "launched inside the window."
            )
        lines.append("")

    gates = diagnostics.get("validation_gates")
    if isinstance(gates, Mapping):
        lines.append(
            f"Data-path gates PASSED on {gates['comparator']}: correlation with the "
            f"market factor {float(str(gates['correlation_with_market_total_return'])):.4f}, "
            f"beta {float(str(gates['market_beta'])):.4f}, "
            f"R2 {float(str(gates['r_squared'])):.4f}, worst month "
            f"{gates['worst_month']} at "
            f"{float(str(gates['worst_month_return_percent'])):.2f}%."
        )
        lines.append("")

    exposures = diagnostics.get("exposures")
    outcomes = diagnostics.get("outcomes")
    if isinstance(exposures, Sequence) and isinstance(outcomes, Sequence):
        primary = {
            str(item["ticker"]): item
            for item in exposures
            if isinstance(item, Mapping) and item["specification"] == PRIMARY_SPECIFICATION
        }
        header = (
            f"{'ticker':<7}{'factor':<7}{'load':>7}{'HACse':>7}"
            f"{'  95% bootstrap':<20}{'H1':>7}{'H2':>7}"
            f"{'alphaR':>8}{'alphaS':>8}{'MDE80':>8}{'R2':>6}  status"
        )
        lines.extend([f"Exposure audit, {PRIMARY_SPECIFICATION}, common period", header,
                      "-" * len(header)])
        for item in outcomes:
            if not isinstance(item, Mapping):
                continue
            ticker = str(item["ticker"])
            fit = primary.get(ticker)
            if fit is None:
                continue
            interval = item["intended_loading_interval"]
            assert isinstance(interval, Sequence)
            lines.append(
                f"{ticker:<7}{item['intended_factor']!s:<7}"
                f"{float(str(item['intended_loading'])):>+7.3f}"
                f"{float(str(item['intended_loading_se'])):>7.3f}"
                f"  [{float(str(interval[0])):+.3f},{float(str(interval[1])):+.3f}]"
                f"{float(str(item['intended_loading_first_half'])):>+7.2f}"
                f"{float(str(item['intended_loading_second_half'])):>+7.2f}"
                f"{float(str(fit['alpha_annual_percent'])):>+8.2f}"
                f"{float(str(fit['shrunk_alpha_annual_percent'])):>+8.2f}"
                f"{float(str(fit['minimum_detectable_alpha_percent'])):>8.2f}"
                f"{float(str(fit['r_squared'])):>6.3f}  {item['status']}"
            )
            for clause in item["falsifier_clauses_fired"]:  # type: ignore[union-attr]
                lines.append(f"         {clause}")
        lines.append("")
        lines.append(
            "alphaR is the raw annual alpha, alphaS the posterior after shrinking by "
            "this fund's own factor, MDE80 the smallest alpha this window could have "
            "detected at 80% power. Read them together or not at all."
        )
        lines.append("")

    replication = diagnostics.get("replication")
    if isinstance(replication, Sequence):
        header = (
            f"{'ticker':<7}{'TD vs mkt':>11}{'TD vs combo':>13}"
            f"{'TE combo':>10}{'fee prem':>9}{'shortfall':>11}  weights"
        )
        lines.extend(["Can cheap broad funds already do this? (pp/yr)", header, "-" * len(header)])
        for item in replication:
            if not isinstance(item, Mapping):
                continue
            weights = item["weights"]
            basis = item["basis"]
            assert isinstance(weights, Sequence) and isinstance(basis, Sequence)
            rendered = " ".join(
                f"{basis[i]}={float(str(weights[i])) * 100:.0f}%"
                for i in range(len(basis))
                if float(str(weights[i])) > 0.005
            )
            lines.append(
                f"{item['ticker']!s:<7}"
                f"{float(str(item['tracking_difference_vs_market_pp'])):>+11.2f}"
                f"{float(str(item['tracking_difference_vs_combination_pp'])):>+13.2f}"
                f"{float(str(item['tracking_error_vs_combination_pp'])):>10.2f}"
                f"{float(str(item['fee_premium_over_basis_pp'])):>+9.2f}"
                f"{float(str(item['implementation_shortfall_pp'])):>+11.2f}  {rendered}"
            )
        lines.append("")

    correction = diagnostics.get("multiple_testing")
    if isinstance(correction, Mapping):
        alpha_block = correction["alpha"]
        assert isinstance(alpha_block, Mapping)
        lines.append(
            f"Multiple testing over the whole family ({correction['family_size']} tests = "
            f"{correction['funds']} funds x {len(FACTOR_SPECIFICATIONS)} specifications):"
        )
        lines.append(
            f"  uncorrected p<=0.05: {alpha_block['rejected_uncorrected_at_0_05']}; "
            f"Benjamini-Hochberg at 0.10: {alpha_block.get('rejected_benjamini_hochberg')}; "
            f"Holm-Bonferroni at 0.10: {alpha_block.get('rejected_holm_bonferroni')}"
        )
        inflated = correction.get("denominator_hostile_test")
        if isinstance(inflated, Mapping):
            for label in (
                "all_funds_that_passed_the_screen",
                "every_mandate_matching_series_screened",
            ):
                block = inflated[label]
                assert isinstance(block, Mapping)
                lines.append(
                    f"  denominator widened to {block['family_size']} "
                    f"({label.replace('_', ' ')}): BH "
                    f"{block['rejected_benjamini_hochberg']}, Holm "
                    f"{block['rejected_holm_bonferroni']}"
                )
        survivors = alpha_block.get("survivors_benjamini_hochberg")
        if isinstance(survivors, Sequence):
            for item in survivors:
                if isinstance(item, Mapping):
                    lines.append(
                        f"    {item['ticker']} {item['specification']}: raw "
                        f"{float(str(item['alpha_annual_percent'])):+.2f} pp/yr, shrunk "
                        f"{float(str(item['shrunk_alpha_annual_percent'])):+.2f}, "
                        f"adjusted p={float(str(item['adjusted_p'])):.4f}"
                    )
        lines.append("")

    cross = diagnostics.get("cross_source_check")
    if isinstance(cross, Mapping):
        compared = cross["compared"]
        unavailable = cross["unavailable"]
        assert isinstance(compared, Sequence) and isinstance(unavailable, Sequence)
        if compared:
            medians = [float(str(item["median_absolute_difference_bp"])) for item in compared
                       if isinstance(item, Mapping)]
            lines.append(
                f"Cross-source check against the secondary feed: {len(compared)} funds "
                f"compared, median absolute monthly disagreement "
                f"{float(np.median(medians)):.1f} bp, worst fund median "
                f"{max(medians):.1f} bp. {len(unavailable)} funds unavailable."
            )
        else:
            lines.append(
                f"Cross-source check: NOT AVAILABLE for any fund ({len(unavailable)} "
                "refusals). The secondary source is not research-grade and nothing "
                "depends on it, but the check could not be run."
            )
        lines.append("")

    rolling = diagnostics.get("rolling_loadings")
    if isinstance(rolling, Sequence) and rolling:
        lines.append("Rolling 36-month intended loading: range and sign changes")
        for item in rolling:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"  {item['ticker']!s:<7}{item['factor']!s:<5} "
                f"min {float(str(item['minimum'])):+.3f}  max {float(str(item['maximum'])):+.3f}"
                f"  range {float(str(item['range'])):.3f}"
                f"  sign changes {item['sign_changes']}"
            )
        lines.append("")

    pedestal = diagnostics.get("model_misfit_pedestal")
    if isinstance(pedestal, Mapping) and pedestal.get("available"):
        specs = pedestal["by_specification"]
        assert isinstance(specs, Mapping)
        rendered = ", ".join(
            f"{name} {float(str(_as_mapping(block)['alpha_annual_percent'])):+.2f}"
            for name, block in specs.items()
        )
        lines.append(
            f"MODEL-MISFIT PEDESTAL. {pedestal['comparator']} is the market "
            f"portfolio, so its alpha should be about minus its 0.03% fee. It is: "
            f"{rendered} pp/yr. Every fund alpha above carries this; read them as "
            "distances from the pedestal, not from zero."
        )
        lines.append("")

    cash = diagnostics.get("cash_rate_sensitivity")
    if isinstance(cash, Mapping):
        alternatives = cash["alternatives"]
        assert isinstance(alternatives, Sequence)
        rendered = ", ".join(
            f"{item['series']} would move every alpha by "
            f"{float(str(item['alpha_shift_pp_per_year'])):+.3f} pp/yr"
            for item in alternatives
            if isinstance(item, Mapping) and "alpha_shift_pp_per_year" in item
        )
        lines.append(f"Cash-rate substitution: {rendered or 'unavailable'}; no loading moves.")
        lines.append("")

    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Build the universe, or run Experiment 002 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_002_fund_exposure",
        description=(
            "Audit the exposure and implementation cost of screened factor products, "
            "writing a ledger entry for the attempt."
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
            "screen the N-PORT census and write the committed product universe. "
            "MUST be run before the audit: the universe is fixed before any return "
            "is downloaded, and the audit refuses to rebuild it."
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
                "exp_002_fund_exposure"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
