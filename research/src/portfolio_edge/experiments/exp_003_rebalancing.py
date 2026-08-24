"""Experiment 003: unlevered rebalancing policy comparison on regional equity sleeves.

The repository's first CONFIRMATORY experiment. It takes the closed-form model in
``docs/research/expected-edge-decomposition.md`` -- rebalancing is a short straddle
on relative log performance with premium ``gamma_star * T`` -- and asks whether real
regional equity returns behave the way it predicts.

Five policies from identical starting weights and identical cash flows:
buy-and-hold, annual calendar, monthly calendar, one frozen 25% relative threshold,
and cash-flow-directed. Every one of them is run through
:func:`portfolio_edge.core.rebalance.simulate`; nothing here reimplements a policy.

Four questions, in the order the specification asks them
--------------------------------------------------------
1. **Does realised ``gamma_star`` match ``0.5 (sum w_i sigma_i^2 - sigma_p^2)``?**
   Reported per 50/50 regional pair and for the three-sleeve portfolio, against
   both the continuous-time closed form and the discrete monthly form
   ``B(tau^2 h)/h`` from :mod:`portfolio_edge.studies.volatility_harvesting`.
2. **Is ``kappa_t`` serially dependent?** The framework says this, not the
   diversification-return statistic, is the diagnostic that decides whether
   rebalancing can add value. Tested with autocorrelations at fourteen lags with
   block-bootstrap intervals, an i.i.d. null, Ljung-Box, and the
   heteroskedasticity-robust Lo-MacKinlay variance ratio.
3. **Does realised rebalanced-minus-held fall inside the closed form's band?**
   The published band assumes equal drifts. Real regions do not have equal drifts,
   so :func:`expected_log_cosh_half` extends the closed form to a non-zero drift
   gap and the two predictions are reported side by side. The difference between
   them is the answer to "diagnose the gap".
4. **Where does the data contradict the theory?** Skewness, excess kurtosis,
   Ljung-Box on ``kappa`` and on ``kappa**2``, and the realised win frequency over
   rolling windows against the closed-form probability.

What is deliberately awkward here
---------------------------------
* **The source bytes are pinned and a mismatch aborts.** Ken French rebuilds each
  region's whole history from a new Bloomberg or CRSP vintage; a different file is
  a different specification, not a hash to update.
* **Each sleeve's total return is ``Mkt-RF + RF``, an identity rather than an
  approximation.** French subtracts the *US* one-month bill from every region and
  quotes every region in US dollars, so adding it back recovers that region's USD
  total return exactly. The reconstruction error is the source's two-decimal
  printing, and it is measured rather than assumed negligible.
* **Drawdown, volatility and geometric return are computed on the time-weighted
  wealth index**, not on the equity curve, because contributions inflate the
  equity curve and would hide a drawdown. Terminal wealth is reported from the
  equity curve, which is the one figure that should include the contributions.
* **PRETAX everywhere, with no tax haircut of any kind.** The simulation holds no
  tax lots, so it cannot know a basis, so it may not price a realisation.

Run it::

    uv run python -m portfolio_edge.experiments.exp_003_rebalancing --view-results
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import chi2, norm

from portfolio_edge.core.costs import ProportionalCostModel
from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.rebalance import (
    BuyAndHold,
    CalendarRebalance,
    CashFlowDirected,
    RebalancePolicy,
    RelativeThreshold,
    kappa_autocorrelation,
    kappa_series,
    simulate,
    two_period_rebalance_advantage,
)
from portfolio_edge.core.wealth import CashFlowTiming
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.data.validation import validate_table
from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.periods import PeriodError, month_count, month_index
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
from portfolio_edge.inference.bootstrap import (
    optimal_block_length,
    stationary_bootstrap_indices,
)
from portfolio_edge.inference.multiple_testing import holm_bonferroni
from portfolio_edge.studies.volatility_harvesting import (
    discrete_rebalancing_growth_bonus,
    excess_growth_two_asset,
    log_cosh,
    probability_rebalanced_beats_buy_and_hold,
    rebalancing_advantage,
    relative_log_volatility,
)

__all__ = [
    "ENTRY_POINT",
    "MONTHS_PER_YEAR",
    "PolicySummary",
    "RebalancingError",
    "VarianceRatio",
    "build_registry",
    "calendar_year_gross_returns",
    "compare_policies",
    "crra_certainty_equivalent",
    "default_specification_path",
    "expected_log_cosh_half",
    "ljung_box",
    "main",
    "probability_beats_with_drift",
    "run",
    "serial_dependence",
    "summarise_policy",
    "variance_ratio",
]

ENTRY_POINT: Final = "exp_003_rebalancing"

MONTHS_PER_YEAR: Final = 12

#: Two-sided normal quantile for the 95% intervals attached to reported means.
_Z_95: Final = 1.959963984540054

#: Half-width of the source's printed precision: French prints percent to two
#: decimals, so every cell carries a uniform ``+/- 0.005`` percentage points.
_PRINT_HALF_WIDTH_DECIMAL: Final = 0.00005

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.intp]


class RebalancingError(RuntimeError):
    """The experiment could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to frozen specification data
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise RebalancingError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise RebalancingError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise RebalancingError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise RebalancingError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise RebalancingError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _integers(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[int, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    out: list[int] = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, int):
            raise RebalancingError(f"{where}.{key} must hold integers, got {item!r}")
        out.append(item)
    return tuple(out)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    items = _sequence(_at(data, key, where=where), where=f"{where}.{key}")
    return tuple(str(item) for item in items)


# --------------------------------------------------------------------------- #
# Statistics that this experiment adds, each with its own unit test
# --------------------------------------------------------------------------- #


def crra_certainty_equivalent(gross_returns: FloatArray, *, gamma: float) -> float:
    """The constant return whose CRRA utility equals the mean utility of the sample.

    ``u(x) = x**(1 - gamma) / (1 - gamma)`` for ``gamma != 1`` and ``log x`` at
    ``gamma = 1``. Inverting the mean utility gives, for ``gamma != 1``,
    ``CE = (mean_y G_y**(1 - gamma))**(1 / (1 - gamma)) - 1``; at ``gamma = 1`` it
    is the geometric mean minus one.

    ``gross_returns`` are wealth relatives (``1 + r``), not returns, and must be
    strictly positive: CRRA utility is undefined at zero wealth for ``gamma >= 1``
    and a portfolio that reaches it is insolvent, not merely unlucky.
    """
    values = np.asarray(gross_returns, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("gross_returns must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(values)):
        raise ValueError("gross_returns contains non-finite values")
    if np.any(values <= 0.0):
        raise ValueError(
            "CRRA utility is undefined at non-positive wealth; a gross return of "
            f"{float(np.min(values))!r} is insolvency, not a low return"
        )
    if math.isclose(gamma, 1.0):
        return float(np.exp(np.mean(np.log(values)))) - 1.0
    power = 1.0 - gamma
    return float(np.mean(values**power) ** (1.0 / power)) - 1.0


def calendar_year_gross_returns(monthly_returns: FloatArray) -> FloatArray:
    """Compound monthly returns into non-overlapping 12-month gross returns.

    Requires a whole number of years. The sample policy is frozen at 420 months
    precisely so that this cannot silently drop a partial year.
    """
    values = np.asarray(monthly_returns, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("monthly_returns must be one-dimensional")
    if values.size == 0 or values.size % MONTHS_PER_YEAR != 0:
        raise ValueError(
            f"need a whole number of 12-month blocks, got {values.size} months"
        )
    blocks = values.reshape(-1, MONTHS_PER_YEAR)
    return np.asarray(np.prod(1.0 + blocks, axis=1), dtype=np.float64)


def expected_log_cosh_half(*, mean: float, standard_deviation: float) -> float:
    """``E[log cosh(D / 2)]`` for ``D ~ N(mean, standard_deviation**2)``.

    This is the general form of
    :func:`portfolio_edge.studies.volatility_harvesting.buy_and_hold_log_bonus`,
    which is the ``mean = 0`` case. It matters because that zero-mean assumption
    is exactly what real regional equity returns violate: two markets with
    different realised log drifts have a ``D(T)`` whose mean grows like ``T``, and
    the resulting shortfall grows like ``T`` too, so it does not average away.

    Computed by Gauss-Hermite quadrature, which is exact for polynomials and
    converges quickly here because ``log cosh`` is smooth and asymptotically
    linear.
    """
    if standard_deviation < 0.0:
        raise ValueError("standard_deviation cannot be negative")
    if standard_deviation == 0.0:
        return log_cosh(mean / 2.0)
    nodes, weights = np.polynomial.hermite_e.hermegauss(201)
    points = mean + standard_deviation * nodes
    values = np.asarray([log_cosh(float(x) / 2.0) for x in points], dtype=np.float64)
    return float(np.dot(weights, values) / math.sqrt(2.0 * math.pi))


def probability_beats_with_drift(
    *, excess_growth: float, horizon_years: float, drift_gap: float, relative_volatility: float
) -> float:
    """``P(constant-weight beats buy-and-hold)`` when the two drifts differ.

    From the pathwise identity ``log V_reb - log V_hold = gamma_star T - log cosh(D/2)``,
    the winning event is ``|D(T)| < 2 arccosh(e**c)`` with ``c = gamma_star T``.
    The identity holds whatever the drifts are; only the law of ``D(T)`` changes,
    to ``N(drift_gap * T, tau**2 T)``. Hence

        P = Phi((b - mu) / s) - Phi((-b - mu) / s),   b = 2 arccosh(e**c).

    At ``drift_gap = 0`` this reduces to the symmetric closed form
    :func:`~portfolio_edge.studies.volatility_harvesting.probability_rebalanced_beats_buy_and_hold`.
    """
    if excess_growth < 0.0:
        raise ValueError("excess_growth cannot be negative")
    if horizon_years <= 0.0:
        raise ValueError(f"horizon_years must be positive, got {horizon_years}")
    if relative_volatility <= 0.0:
        raise ValueError("relative_volatility must be positive")
    c = excess_growth * horizon_years
    if c <= 0.0:
        return 0.0
    bound = 2.0 * (c + math.log1p(math.sqrt(-math.expm1(-2.0 * c))))
    mu = drift_gap * horizon_years
    s = relative_volatility * math.sqrt(horizon_years)
    return float(norm.cdf((bound - mu) / s) - norm.cdf((-bound - mu) / s))


@dataclass(frozen=True, slots=True, kw_only=True)
class VarianceRatio:
    """Lo-MacKinlay variance ratio with the heteroskedasticity-robust statistic."""

    horizon: int
    ratio: float
    z_homoskedastic: float
    z_heteroskedastic: float
    p_value_heteroskedastic: float
    observations: int

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "horizon_months": self.horizon,
            "variance_ratio": self.ratio,
            "z_homoskedastic": self.z_homoskedastic,
            "z_heteroskedastic": self.z_heteroskedastic,
            "p_value_heteroskedastic": self.p_value_heteroskedastic,
            "observations": self.observations,
        }


def variance_ratio(series: FloatArray, *, horizon: int) -> VarianceRatio:
    """Lo and MacKinlay (1988) overlapping variance ratio, ``VR(q)``.

    ``VR(q) = sigma_c**2(q) / sigma_a**2`` with the unbiased overlapping estimators

        sigma_a**2 = sum_t (x_t - mu)**2 / (T - 1),
        sigma_c**2 = sum_{t=q}^{T} (x_t + ... + x_{t-q+1} - q mu)**2 / m,
        m = q (T - q + 1) (1 - q / T).

    ``VR = 1`` under a random walk, ``> 1`` under positive serial dependence
    (trending), ``< 1`` under reversal. Both test statistics are reported: ``z1``
    assumes homoskedasticity and ``z2`` is the heteroskedasticity-consistent
    statistic that survives volatility clustering, which monthly equity returns
    plainly have. Only ``z2`` should be read here.

    ``series`` must be a series whose null is a random walk in *levels*, i.e. a
    series of log differences. Feeding it simple returns is close but not exact,
    and this experiment feeds it log relative performance.
    """
    values = np.asarray(series, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("series must be one-dimensional")
    if horizon < 1:
        raise ValueError(f"horizon must be at least 1, got {horizon}")
    n = int(values.size)
    if n <= horizon + 1:
        raise ValueError(f"need more than {horizon + 1} observations for VR({horizon})")
    mu = float(np.mean(values))
    centred = values - mu
    variance_1 = float(np.dot(centred, centred)) / (n - 1)
    if variance_1 <= 0.0:
        raise ValueError("series has zero variance; the variance ratio is undefined")

    if horizon == 1:
        return VarianceRatio(
            horizon=1,
            ratio=1.0,
            z_homoskedastic=0.0,
            z_heteroskedastic=0.0,
            p_value_heteroskedastic=1.0,
            observations=n,
        )

    cumulative = np.concatenate(([0.0], np.cumsum(values)))
    aggregated = cumulative[horizon:] - cumulative[:-horizon] - horizon * mu
    m = horizon * (n - horizon + 1) * (1.0 - horizon / n)
    variance_q = float(np.dot(aggregated, aggregated)) / m
    ratio = variance_q / variance_1

    # Homoskedastic asymptotic variance: 2 (2q - 1)(q - 1) / (3 q n).
    homoskedastic_variance = (
        2.0 * (2.0 * horizon - 1.0) * (horizon - 1.0) / (3.0 * horizon * n)
    )

    # Heteroskedasticity-consistent variance: sum_j [2(q - j)/q]**2 delta_j.
    squared = centred**2
    denominator = float(np.sum(squared)) ** 2
    theta = 0.0
    for j in range(1, horizon):
        delta = float(np.dot(squared[j:], squared[:-j])) / denominator
        theta += (2.0 * (horizon - j) / horizon) ** 2 * delta

    z1 = (ratio - 1.0) / math.sqrt(homoskedastic_variance)
    z2 = (ratio - 1.0) / math.sqrt(theta) if theta > 0.0 else math.nan
    p2 = (
        float(2.0 * (1.0 - norm.cdf(abs(z2))))
        if math.isfinite(z2)
        else math.nan
    )
    return VarianceRatio(
        horizon=horizon,
        ratio=ratio,
        z_homoskedastic=z1,
        z_heteroskedastic=z2,
        p_value_heteroskedastic=p2,
        observations=n,
    )


def ljung_box(series: FloatArray, *, lags: int) -> tuple[float, float]:
    """Ljung-Box ``Q`` and its chi-squared p-value over ``lags`` lags.

    ``Q = T (T + 2) sum_{k=1}^{L} rho_k**2 / (T - k)``, distributed ``chi2(L)``
    under the null of no serial correlation.
    """
    values = np.asarray(series, dtype=np.float64)
    n = int(values.size)
    if lags < 1 or lags >= n:
        raise ValueError(f"lags must lie in [1, {n - 1}], got {lags}")
    centred = values - float(np.mean(values))
    denominator = float(np.dot(centred, centred))
    if denominator <= 0.0:
        raise ValueError("series has zero variance; Ljung-Box is undefined")
    statistic = 0.0
    for k in range(1, lags + 1):
        rho = float(np.dot(centred[k:], centred[:-k])) / denominator
        statistic += rho * rho / (n - k)
    q = n * (n + 2) * statistic
    return q, float(chi2.sf(q, lags))


def _autocorrelations_of_rows(matrix: FloatArray, lags: Sequence[int]) -> FloatArray:
    """Autocorrelation at each lag for every row of ``matrix``, shape ``(rows, lags)``."""
    centred = matrix - matrix.mean(axis=1, keepdims=True)
    denominator = np.sum(centred * centred, axis=1)
    out = np.empty((matrix.shape[0], len(lags)), dtype=np.float64)
    for index, lag in enumerate(lags):
        numerator = np.sum(centred[:, lag:] * centred[:, :-lag], axis=1)
        out[:, index] = numerator / denominator
    return out


# --------------------------------------------------------------------------- #
# Panel construction
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class Panel:
    """A rectangular monthly panel of sleeve total returns, with its provenance."""

    periods: tuple[str, ...]
    sleeves: tuple[str, ...]
    returns: FloatArray
    """Shape ``(T, N)``, simple monthly total returns in decimal."""
    provenance: tuple[Mapping[str, JsonValue], ...]
    findings: tuple[str, ...]

    @property
    def months(self) -> int:
        return len(self.periods)

    @property
    def years(self) -> float:
        return self.months / MONTHS_PER_YEAR

    def index_of(self, sleeve: str) -> int:
        return self.sleeves.index(sleeve)

    def window(self, *, start: str, end: str) -> Panel:
        first, last = month_index(start), month_index(end)
        keep = [
            i for i, period in enumerate(self.periods) if first <= month_index(period) <= last
        ]
        return Panel(
            periods=tuple(self.periods[i] for i in keep),
            sleeves=self.sleeves,
            returns=self.returns[keep, :],
            provenance=self.provenance,
            findings=self.findings,
        )

    def pair(self, first: str, second: str) -> FloatArray:
        return np.column_stack(
            (self.returns[:, self.index_of(first)], self.returns[:, self.index_of(second)])
        )


def _workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def _load_pinned_table(
    pin: Mapping[str, JsonValue], *, expected_columns: Sequence[str]
) -> tuple[ParsedTable, dict[str, JsonValue], list[str]]:
    """Fetch, hash-pin, parse and validate one sleeve's source table."""
    where = "parameters.source_pin.tables[]"
    dataset = french.get_dataset(_text(pin, "dataset_id", where=where))
    cache = RawCache()
    entry = french.download(cache, dataset)

    expected_raw = _text(pin, "expected_sha256_raw", where=where)
    if entry.sha256 != expected_raw:
        raise RebalancingError(
            f"the file at {dataset.url} now hashes to {entry.sha256}, but this "
            f"specification is frozen against {expected_raw}. Ken French rebuilds "
            "each region's whole history from every new source vintage, so this is "
            "a new vintage, not a corrupted download. Freeze a new specification "
            "against it rather than reporting numbers from an unrecognised file."
        )

    parsed = french.parse(cache, entry, dataset=dataset)
    table = parsed.table(_text(pin, "table_id", where=where))

    report = validate_table(
        table,
        dataset_id=_text(pin, "manifest_dataset_id", where=where),
        expected_columns=tuple(expected_columns),
        expected_frequency="monthly",
    )
    findings = list(report.summary())
    if not report.ok:
        raise RebalancingError(
            "a source table failed validation before any statistic was computed: "
            + "; ".join(findings)
        )

    expected_normalized = _text(pin, "expected_sha256_normalized", where=where)
    if table.sha256_normalized() != expected_normalized:
        raise RebalancingError(
            f"the derived table hashes to {table.sha256_normalized()}, but the "
            f"specification pins {expected_normalized}. The raw bytes matched, so "
            "the parser changed behaviour. That is a finding, not a hash to update."
        )

    manifest_hash: str | None = None
    manifest_path = _workspace_root() / _text(pin, "committed_manifest", where=where)
    if manifest_path.is_file():
        manifest = read_manifest(manifest_path)
        manifest_hash = manifest.sha256_manifest()
        if manifest.sha256_raw != expected_raw:
            raise RebalancingError(
                f"{manifest_path} records sha256_raw {manifest.sha256_raw}, which "
                f"is not the pinned {expected_raw}"
            )

    provenance: dict[str, JsonValue] = {
        "sleeve": _text(pin, "sleeve", where=where),
        "dataset_id": dataset.dataset_id,
        "dataset_description": dataset.description,
        "source_url": entry.url,
        "sha256_raw": entry.sha256,
        "sha256_normalized": table.sha256_normalized(),
        "retrieved_utc": entry.retrieved_utc,
        "source_last_modified": entry.last_modified,
        "parser_version": french.PARSER_VERSION,
        "committed_manifest_sha256": manifest_hash,
        "rows_in_file": table.rows,
        "first_observation": table.first_observation,
        "last_observation": table.last_observation,
        "source_units": table.source_units,
        "units": table.units,
        "unit_transform": table.unit_transform,
        "preamble": parsed.preamble.strip(),
        "validation_findings": findings,
        "construction": "Mkt-RF + RF, an identity: French quotes every region in "
        "USD and subtracts the US one-month bill from every region.",
    }
    return table, provenance, findings


def load_panel(specification: Specification) -> Panel:
    """Build the frozen three-sleeve panel from the pinned source files."""
    parameters = _mapping(specification.parameters, where="parameters")
    pin_block = _mapping(
        _at(parameters, "source_pin", where="parameters"), where="parameters.source_pin"
    )
    expected_columns = _strings(pin_block, "expected_columns", where="source_pin")
    tables = _sequence(_at(pin_block, "tables", where="source_pin"), where="source_pin.tables")

    start = specification.sample_policy.start
    end = specification.sample_policy.end
    first, last = month_index(start), month_index(end)

    per_sleeve: dict[str, dict[str, float]] = {}
    provenance: list[Mapping[str, JsonValue]] = []
    findings: list[str] = []
    risk_free: dict[str, dict[str, float]] = {}

    for item in tables:
        pin = _mapping(item, where="source_pin.tables[]")
        table, record, table_findings = _load_pinned_table(pin, expected_columns=expected_columns)
        sleeve = str(record["sleeve"])
        market = table.column("Mkt-RF")
        cash = table.column("RF")
        values: dict[str, float] = {}
        cash_values: dict[str, float] = {}
        missing: list[str] = []
        for index, period in enumerate(table.periods):
            try:
                if not first <= month_index(period) <= last:
                    continue
            except PeriodError as exc:  # pragma: no cover - defensive
                raise RebalancingError(str(exc)) from exc
            excess, rate = market[index], cash[index]
            if excess is None or rate is None:
                missing.append(period)
                continue
            values[period] = excess + rate
            cash_values[period] = rate
        if missing:
            raise RebalancingError(
                f"sleeve {sleeve!r} has missing Mkt-RF or RF in {len(missing)} months "
                f"inside the frozen window: {missing[:5]}. Missing months are a "
                "finding, never imputed."
            )
        per_sleeve[sleeve] = values
        risk_free[sleeve] = cash_values
        provenance.append(record)
        findings.extend(f"{sleeve}: {text}" for text in table_findings)

    sleeves = tuple(str(record["sleeve"]) for record in provenance)
    common = sorted(set.intersection(*(set(per_sleeve[name]) for name in sleeves)), key=month_index)
    expected_months = month_count(start, end)
    if len(common) != expected_months:
        raise RebalancingError(
            f"the frozen window {start}..{end} spans {expected_months} months but "
            f"only {len(common)} are present in every sleeve. The sample policy and "
            "the data disagree; that is a finding, not a window to shrink."
        )
    if common[0] != start or common[-1] != end:
        raise RebalancingError(
            f"the panel runs {common[0]}..{common[-1]}, not the frozen {start}..{end}"
        )

    # The RF column must be the identical series in every file, because French
    # subtracts the US bill from every region. Difference beyond printing
    # precision would mean the identity used to rebuild total returns is wrong.
    base = sleeves[0]
    worst = 0.0
    for name in sleeves[1:]:
        worst = max(
            worst, max(abs(risk_free[name][p] - risk_free[base][p]) for p in common)
        )
    if worst > 2.0 * _PRINT_HALF_WIDTH_DECIMAL + 1e-12:
        raise RebalancingError(
            f"the RF columns of the three files differ by up to {worst!r} in decimal "
            "units, which is more than their printing precision. The Mkt-RF + RF "
            "reconstruction assumes one common risk-free rate; that assumption has "
            "failed and the sleeves must not be combined."
        )
    findings.append(
        f"the three files' RF columns agree to {worst * 100:.4f} percentage points, "
        "which is their printed precision; one common US one-month bill confirmed"
    )

    matrix = np.asarray(
        [[per_sleeve[name][period] for name in sleeves] for period in common],
        dtype=np.float64,
    )
    return Panel(
        periods=tuple(common),
        sleeves=sleeves,
        returns=matrix,
        provenance=tuple(provenance),
        findings=tuple(findings),
    )


# --------------------------------------------------------------------------- #
# Policy evaluation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicySummary:
    """Everything reported for one policy on one cost basis over one window."""

    policy_id: str
    cost_basis: str
    months: int
    terminal_wealth: float
    contributions: float
    certainty_equivalent_percent: float
    geometric_return_percent: float
    arithmetic_return_percent: float
    volatility_percent: float
    max_drawdown_percent: float
    time_under_water_months: int
    annual_turnover_percent: float
    annual_cost_percent: float
    rebalance_count: int
    mean_absolute_deviation_pp: float
    max_deviation_pp: float
    monthly_returns: FloatArray

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "policy": self.policy_id,
            "cost_basis": self.cost_basis,
            "months": self.months,
            "terminal_wealth": self.terminal_wealth,
            "contributions": self.contributions,
            "certainty_equivalent_percent_per_year": self.certainty_equivalent_percent,
            "geometric_return_percent_per_year": self.geometric_return_percent,
            "arithmetic_return_percent_per_year": self.arithmetic_return_percent,
            "volatility_percent_per_year": self.volatility_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "time_under_water_months": self.time_under_water_months,
            "annual_one_sided_turnover_percent": self.annual_turnover_percent,
            "annual_transaction_cost_percent": self.annual_cost_percent,
            "rebalance_count": self.rebalance_count,
            "mean_absolute_weight_deviation_pp": self.mean_absolute_deviation_pp,
            "max_weight_deviation_pp": self.max_deviation_pp,
        }


def _policies(threshold: float, annual_interval: int) -> dict[str, RebalancePolicy]:
    """The five frozen policies, in the order the specification lists them."""
    return {
        "buy_and_hold": BuyAndHold(),
        "annual_calendar": CalendarRebalance(annual_interval),
        "monthly_calendar": CalendarRebalance(1),
        "relative_threshold_25pct": RelativeThreshold(threshold),
        "cash_flow_directed": CashFlowDirected(),
    }


def summarise_policy(
    returns: FloatArray,
    target: FloatArray,
    policy: RebalancePolicy,
    *,
    policy_id: str,
    cost_basis: str,
    cost_bp: float,
    cash_flows: FloatArray,
    gamma: float,
    initial_wealth: float = 1.0,
) -> PolicySummary:
    """Run one policy through :func:`simulate` and reduce it to reported statistics.

    The monthly return series used for every risk statistic is the *time-weighted*
    return ``W_{t+1} / (W_t + f_t) - 1``, which removes the contribution and leaves
    the return the portfolio actually earned net of the costs it actually paid.
    Terminal wealth is taken from the equity curve instead, because that is the one
    figure that should include the money the investor put in.
    """
    result = simulate(
        returns,
        target,
        policy,
        initial_wealth=initial_wealth,
        cash_flows=cash_flows,
        cost_model=ProportionalCostModel(cost_bp),
        cash_flow_timing=CashFlowTiming.BEGINNING,
    )
    equity = result.equity_curve
    invested = equity[:-1] + cash_flows
    monthly = equity[1:] / invested - 1.0
    index = np.concatenate(([1.0], np.cumprod(1.0 + monthly)))

    months = int(returns.shape[0])
    years = months / MONTHS_PER_YEAR
    drawdown = drawdown_summary(index)
    deviations = np.abs(result.weights - target) * 100.0

    return PolicySummary(
        policy_id=policy_id,
        cost_basis=cost_basis,
        months=months,
        terminal_wealth=float(equity[-1]),
        contributions=float(np.sum(cash_flows)),
        certainty_equivalent_percent=100.0
        * crra_certainty_equivalent(calendar_year_gross_returns(monthly), gamma=gamma),
        geometric_return_percent=100.0 * (float(index[-1]) ** (1.0 / years) - 1.0),
        arithmetic_return_percent=100.0 * float(np.mean(monthly)) * MONTHS_PER_YEAR,
        volatility_percent=100.0
        * float(np.std(monthly, ddof=1))
        * math.sqrt(MONTHS_PER_YEAR),
        max_drawdown_percent=100.0 * drawdown.max_drawdown,
        time_under_water_months=drawdown.max_time_under_water,
        annual_turnover_percent=100.0 * result.total_turnover / years,
        annual_cost_percent=100.0 * float(np.sum(result.costs / invested)) / years,
        rebalance_count=int(np.count_nonzero(result.turnover)),
        mean_absolute_deviation_pp=float(np.mean(np.sum(deviations, axis=1))) / 2.0,
        max_deviation_pp=float(np.max(deviations)),
        monthly_returns=monthly,
    )


def compare_policies(
    panel: Panel,
    target: FloatArray,
    *,
    cost_bases: Mapping[str, float],
    cash_flows: FloatArray,
    gamma: float,
    threshold: float,
    annual_interval: int,
) -> dict[tuple[str, str], PolicySummary]:
    """Every policy on every cost basis, from identical weights and cash flows."""
    out: dict[tuple[str, str], PolicySummary] = {}
    for basis, cost_bp in cost_bases.items():
        for policy_id, policy in _policies(threshold, annual_interval).items():
            out[(policy_id, basis)] = summarise_policy(
                panel.returns,
                target,
                policy,
                policy_id=policy_id,
                cost_basis=basis,
                cost_bp=cost_bp,
                cash_flows=cash_flows,
                gamma=gamma,
            )
    return out


# --------------------------------------------------------------------------- #
# Question 1 and 3: excess growth, predicted against realised
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PairTheory:
    """The closed form versus the data, for one 50/50 pair of sleeves."""

    name: str
    first: str
    second: str
    months: int
    horizon_years: float
    volatility_a: float
    volatility_b: float
    correlation: float
    relative_volatility: float
    growth_a: float
    growth_b: float
    drift_gap: float
    gamma_star_continuous: float
    gamma_star_discrete_monthly: float
    gamma_star_realised: float
    realised_advantage: float
    predicted_advantage_equal_drift: float
    predicted_advantage_with_drift: float
    predicted_median_equal_drift: float
    predicted_q05_equal_drift: float
    predicted_q95_equal_drift: float
    probability_equal_drift: float
    probability_with_drift: float
    inside_equal_drift_band: bool

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "pair": self.name,
            "months": self.months,
            "horizon_years": self.horizon_years,
            "log_volatility_a_percent": 100.0 * self.volatility_a,
            "log_volatility_b_percent": 100.0 * self.volatility_b,
            "log_correlation": self.correlation,
            "relative_log_volatility_percent": 100.0 * self.relative_volatility,
            "log_growth_a_percent": 100.0 * self.growth_a,
            "log_growth_b_percent": 100.0 * self.growth_b,
            "drift_gap_percent_per_year": 100.0 * self.drift_gap,
            "gamma_star_continuous_bp": 1e4 * self.gamma_star_continuous,
            "gamma_star_discrete_monthly_bp": 1e4 * self.gamma_star_discrete_monthly,
            "gamma_star_realised_bp": 1e4 * self.gamma_star_realised,
            "realised_rebalanced_minus_held_bp": 1e4 * self.realised_advantage,
            "predicted_mean_equal_drift_bp": 1e4 * self.predicted_advantage_equal_drift,
            "predicted_mean_with_drift_bp": 1e4 * self.predicted_advantage_with_drift,
            "predicted_median_equal_drift_bp": 1e4 * self.predicted_median_equal_drift,
            "predicted_q05_equal_drift_bp": 1e4 * self.predicted_q05_equal_drift,
            "predicted_q95_equal_drift_bp": 1e4 * self.predicted_q95_equal_drift,
            "probability_equal_drift": self.probability_equal_drift,
            "probability_with_drift": self.probability_with_drift,
            "realised_inside_equal_drift_5_95_band": self.inside_equal_drift_band,
        }


def _log_moments(returns: FloatArray) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Annualised log growth, log volatility and log correlation of a return panel."""
    logs = np.log1p(returns)
    growth = np.mean(logs, axis=0) * MONTHS_PER_YEAR
    covariance = np.cov(logs, rowvar=False, ddof=1) * MONTHS_PER_YEAR
    covariance = np.atleast_2d(covariance)
    volatility = np.sqrt(np.diag(covariance))
    return growth, volatility, covariance


def analyse_pair(panel: Panel, first: str, second: str) -> PairTheory:
    """Predicted versus realised excess growth for one 50/50 pair, gross of costs."""
    returns = panel.pair(first, second)
    growth, volatility, covariance = _log_moments(returns)
    correlation = float(covariance[0, 1] / (volatility[0] * volatility[1]))
    tau = relative_log_volatility(
        volatility_a=float(volatility[0]),
        volatility_b=float(volatility[1]),
        correlation=correlation,
    )
    gamma_continuous = excess_growth_two_asset(
        volatility_a=float(volatility[0]),
        volatility_b=float(volatility[1]),
        correlation=correlation,
        weight_a=0.5,
    )
    gamma_discrete = discrete_rebalancing_growth_bonus(
        relative_log_variance=tau**2, interval_years=1.0 / MONTHS_PER_YEAR
    )

    years = panel.years
    weights = np.array([0.5, 0.5], dtype=np.float64)
    rebalanced = np.sum(np.log1p(returns @ weights)) / years
    held_terminal = float(np.dot(weights, np.prod(1.0 + returns, axis=0)))
    held = math.log(held_terminal) / years
    gamma_realised = rebalanced - float(np.dot(weights, growth))
    realised_advantage = rebalanced - held

    drift_gap = float(growth[0] - growth[1])
    equal_drift = rebalancing_advantage(
        excess_growth=gamma_continuous, horizon_years=years
    )
    with_drift = gamma_continuous - expected_log_cosh_half(
        mean=drift_gap * years, standard_deviation=tau * math.sqrt(years)
    ) / years

    return PairTheory(
        name=f"{first}|{second}",
        first=first,
        second=second,
        months=panel.months,
        horizon_years=years,
        volatility_a=float(volatility[0]),
        volatility_b=float(volatility[1]),
        correlation=correlation,
        relative_volatility=tau,
        growth_a=float(growth[0]),
        growth_b=float(growth[1]),
        drift_gap=drift_gap,
        gamma_star_continuous=gamma_continuous,
        gamma_star_discrete_monthly=gamma_discrete,
        gamma_star_realised=gamma_realised,
        realised_advantage=realised_advantage,
        predicted_advantage_equal_drift=equal_drift.mean,
        predicted_advantage_with_drift=with_drift,
        predicted_median_equal_drift=equal_drift.median,
        predicted_q05_equal_drift=equal_drift.quantile_05,
        predicted_q95_equal_drift=equal_drift.quantile_95,
        probability_equal_drift=probability_rebalanced_beats_buy_and_hold(
            excess_growth=gamma_continuous, horizon_years=years
        ),
        probability_with_drift=probability_beats_with_drift(
            excess_growth=gamma_continuous,
            horizon_years=years,
            drift_gap=drift_gap,
            relative_volatility=tau,
        ),
        inside_equal_drift_band=bool(
            equal_drift.quantile_05 <= realised_advantage <= equal_drift.quantile_95
        ),
    )


def portfolio_excess_growth(panel: Panel, weights: FloatArray) -> dict[str, JsonValue]:
    """Predicted and realised ``gamma_star`` for the whole three-sleeve portfolio."""
    growth, volatility, covariance = _log_moments(panel.returns)
    weighted_variance = float(np.dot(weights, volatility**2))
    portfolio_variance = float(weights @ covariance @ weights)
    predicted = 0.5 * (weighted_variance - portfolio_variance)

    years = panel.years
    rebalanced = float(np.sum(np.log1p(panel.returns @ weights))) / years
    held = math.log(float(np.dot(weights, np.prod(1.0 + panel.returns, axis=0)))) / years
    realised = rebalanced - float(np.dot(weights, growth))
    return {
        "weights": [float(value) for value in weights],
        "gamma_star_predicted_continuous_bp": 1e4 * predicted,
        "gamma_star_realised_bp": 1e4 * realised,
        "gap_bp": 1e4 * (realised - predicted),
        "constant_weight_log_growth_percent": 100.0 * rebalanced,
        "buy_and_hold_log_growth_percent": 100.0 * held,
        "rebalanced_minus_held_bp": 1e4 * (rebalanced - held),
        "component_log_growth_percent": [100.0 * float(value) for value in growth],
        "weighted_component_log_growth_percent": 100.0 * float(np.dot(weights, growth)),
        "note": (
            "The weighted component log growth is the diversification-return "
            "benchmark and is NOT investable (Willenbrock 2011). It appears here "
            "only because gamma_star is defined against it. The investable "
            "comparison is rebalanced_minus_held."
        ),
    }


# --------------------------------------------------------------------------- #
# Question 2: is kappa serially dependent?
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class SerialDependence:
    """The kappa diagnostic for one pair: the crux of the whole experiment."""

    pair: str
    observations: int
    lags: tuple[int, ...]
    autocorrelation: tuple[float, ...]
    block_lower: tuple[float, ...]
    block_upper: tuple[float, ...]
    iid_null_lower: tuple[float, ...]
    iid_null_upper: tuple[float, ...]
    significant_lags: tuple[int, ...]
    variance_ratios: tuple[VarianceRatio, ...]
    ljung_box_q: float
    ljung_box_p: float
    ljung_box_squared_q: float
    ljung_box_squared_p: float
    skewness: float
    excess_kurtosis: float
    politis_white_block: float
    block_length_used: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "pair": self.pair,
            "observations": self.observations,
            "lags": list(self.lags),
            "autocorrelation": list(self.autocorrelation),
            "block_bootstrap_95_lower": list(self.block_lower),
            "block_bootstrap_95_upper": list(self.block_upper),
            "iid_null_95_lower": list(self.iid_null_lower),
            "iid_null_95_upper": list(self.iid_null_upper),
            "lags_outside_the_iid_null": list(self.significant_lags),
            "variance_ratios": [item.to_json() for item in self.variance_ratios],
            "ljung_box_q": self.ljung_box_q,
            "ljung_box_p": self.ljung_box_p,
            "ljung_box_squared_q": self.ljung_box_squared_q,
            "ljung_box_squared_p": self.ljung_box_squared_p,
            "skewness": self.skewness,
            "excess_kurtosis": self.excess_kurtosis,
            "politis_white_block_months": self.politis_white_block,
            "block_length_used_months": self.block_length_used,
        }


def serial_dependence(
    panel: Panel,
    first: str,
    second: str,
    *,
    lags: Sequence[int],
    variance_ratio_horizons: Sequence[int],
    rng: np.random.Generator,
    block_length: float,
    n_resamples: int,
    confidence_level: float,
) -> SerialDependence:
    """Autocorrelation of ``kappa`` with intervals, variance ratios and tail moments.

    Two intervals are reported and they answer different questions. The
    **block-bootstrap** interval is uncertainty about the true autocorrelation and
    is attenuated at lags approaching the block length, because a resample breaks
    dependence at every block join. The **i.i.d. null** band is the distribution of
    the same statistic when the ordering carries no information at all; an
    autocorrelation outside it is evidence that ``kappa`` is not serially
    independent.
    """
    kappa = kappa_series(panel.pair(first, second))
    lag_list = list(lags)
    point = np.asarray(
        [kappa_autocorrelation(kappa, lag=lag) for lag in lag_list], dtype=np.float64
    )

    alpha = 1.0 - confidence_level
    block_indices = stationary_bootstrap_indices(kappa.size, block_length, n_resamples, rng)
    block_replicates = _autocorrelations_of_rows(kappa[block_indices], lag_list)
    block_bounds = np.quantile(block_replicates, [alpha / 2.0, 1.0 - alpha / 2.0], axis=0)

    permuted = np.empty((n_resamples, kappa.size), dtype=np.float64)
    for row in range(n_resamples):
        permuted[row] = rng.permutation(kappa)
    null_replicates = _autocorrelations_of_rows(permuted, lag_list)
    null_bounds = np.quantile(null_replicates, [alpha / 2.0, 1.0 - alpha / 2.0], axis=0)

    significant = tuple(
        lag
        for index, lag in enumerate(lag_list)
        if point[index] < null_bounds[0, index] or point[index] > null_bounds[1, index]
    )

    # Variance ratios are a statement about a random walk in levels, so they are
    # computed on the log relative performance, not on the simple difference.
    log_relative = np.log1p(panel.returns[:, panel.index_of(first)]) - np.log1p(
        panel.returns[:, panel.index_of(second)]
    )
    ratios = tuple(
        variance_ratio(log_relative, horizon=q)
        for q in variance_ratio_horizons
        if q < kappa.size - 1
    )

    centred = kappa - float(np.mean(kappa))
    variance = float(np.mean(centred**2))
    q_kappa, p_kappa = ljung_box(kappa, lags=MONTHS_PER_YEAR)
    q_squared, p_squared = ljung_box(centred**2, lags=MONTHS_PER_YEAR)

    return SerialDependence(
        pair=f"{first}|{second}",
        observations=int(kappa.size),
        lags=tuple(lag_list),
        autocorrelation=tuple(float(value) for value in point),
        block_lower=tuple(float(value) for value in block_bounds[0]),
        block_upper=tuple(float(value) for value in block_bounds[1]),
        iid_null_lower=tuple(float(value) for value in null_bounds[0]),
        iid_null_upper=tuple(float(value) for value in null_bounds[1]),
        significant_lags=significant,
        variance_ratios=ratios,
        ljung_box_q=q_kappa,
        ljung_box_p=p_kappa,
        ljung_box_squared_q=q_squared,
        ljung_box_squared_p=p_squared,
        skewness=float(np.mean(centred**3) / variance**1.5),
        excess_kurtosis=float(np.mean(centred**4) / variance**2 - 3.0),
        politis_white_block=optimal_block_length(kappa).stationary,
        block_length_used=block_length,
    )


# --------------------------------------------------------------------------- #
# Inference on the paired differences
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class PairedDifference:
    """One policy's certainty-equivalent advantage over buy-and-hold, with its interval."""

    policy_id: str
    cost_basis: str
    difference_percent: float
    lower: float
    upper: float
    p_value: float
    excludes_zero: bool
    clears_materiality: bool
    drawdown_gap_pp: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "policy": self.policy_id,
            "cost_basis": self.cost_basis,
            "certainty_equivalent_difference_pp_per_year": self.difference_percent,
            "interval_lower": self.lower,
            "interval_upper": self.upper,
            "bootstrap_p_value": self.p_value,
            "interval_excludes_zero": self.excludes_zero,
            "clears_materiality_threshold": self.clears_materiality,
            "max_drawdown_worse_than_buy_and_hold_pp": self.drawdown_gap_pp,
        }


def _bootstrap_differences(
    panel: Panel,
    target: FloatArray,
    *,
    cost_bases: Mapping[str, float],
    cash_flows: FloatArray,
    gamma: float,
    threshold: float,
    annual_interval: int,
    indices: IntArray,
) -> dict[tuple[str, str], FloatArray]:
    """Re-simulate every policy on every resample and return the paired differences.

    The panel is resampled jointly -- the same time index for every sleeve -- so
    cross-sectional dependence, which is the entire mechanism, survives. Every
    policy is re-run rather than the return series being resampled, because
    turnover, costs and the threshold trigger are all path-dependent.
    """
    policies = _policies(threshold, annual_interval)
    out: dict[tuple[str, str], list[float]] = {
        (policy_id, basis): []
        for basis in cost_bases
        for policy_id in policies
        if policy_id != "buy_and_hold"
    }
    for row in indices:
        resampled = panel.returns[row, :]
        for basis, cost_bp in cost_bases.items():
            baseline = summarise_policy(
                resampled,
                target,
                policies["buy_and_hold"],
                policy_id="buy_and_hold",
                cost_basis=basis,
                cost_bp=cost_bp,
                cash_flows=cash_flows,
                gamma=gamma,
            ).certainty_equivalent_percent
            for policy_id, policy in policies.items():
                if policy_id == "buy_and_hold":
                    continue
                value = summarise_policy(
                    resampled,
                    target,
                    policy,
                    policy_id=policy_id,
                    cost_basis=basis,
                    cost_bp=cost_bp,
                    cash_flows=cash_flows,
                    gamma=gamma,
                ).certainty_equivalent_percent
                out[(policy_id, basis)].append(value - baseline)
    return {key: np.asarray(values, dtype=np.float64) for key, values in out.items()}


def _paired_differences(
    summaries: Mapping[tuple[str, str], PolicySummary],
    replicates: Mapping[tuple[str, str], FloatArray],
    *,
    confidence_level: float,
    materiality: float,
) -> dict[tuple[str, str], PairedDifference]:
    alpha = 1.0 - confidence_level
    out: dict[tuple[str, str], PairedDifference] = {}
    for key, sample in replicates.items():
        policy_id, basis = key
        point = (
            summaries[key].certainty_equivalent_percent
            - summaries[("buy_and_hold", basis)].certainty_equivalent_percent
        )
        bounds = np.quantile(sample, [alpha / 2.0, 1.0 - alpha / 2.0])
        lower, upper = float(bounds[0]), float(bounds[1])
        centred = sample - float(np.mean(sample))
        p_value = float(np.mean(np.abs(centred) >= abs(point)))
        out[key] = PairedDifference(
            policy_id=policy_id,
            cost_basis=basis,
            difference_percent=point,
            lower=lower,
            upper=upper,
            p_value=p_value,
            excludes_zero=bool(lower > 0.0 or upper < 0.0),
            clears_materiality=bool(point >= materiality),
            drawdown_gap_pp=(
                summaries[("buy_and_hold", basis)].max_drawdown_percent
                - summaries[key].max_drawdown_percent
            ),
        )
    return out


# --------------------------------------------------------------------------- #
# Hostile tests
# --------------------------------------------------------------------------- #


def _policy_table(
    panel: Panel,
    target: FloatArray,
    *,
    cost_bp: float,
    cash_flows: FloatArray,
    gamma: float,
    threshold: float,
    annual_interval: int,
) -> dict[str, float]:
    """Certainty-equivalent advantage over buy-and-hold for each policy, one basis."""
    policies = _policies(threshold, annual_interval)
    values = {
        policy_id: summarise_policy(
            panel.returns,
            target,
            policy,
            policy_id=policy_id,
            cost_basis="net-pessimistic",
            cost_bp=cost_bp,
            cash_flows=cash_flows,
            gamma=gamma,
        ).certainty_equivalent_percent
        for policy_id, policy in policies.items()
    }
    baseline = values["buy_and_hold"]
    return {key: value - baseline for key, value in values.items() if key != "buy_and_hold"}


def _drop_window(panel: Panel, start: str, end: str) -> Panel:
    first, last = month_index(start), month_index(end)
    keep = [
        index
        for index, period in enumerate(panel.periods)
        if not first <= month_index(period) <= last
    ]
    return Panel(
        periods=tuple(panel.periods[i] for i in keep),
        sleeves=panel.sleeves,
        returns=panel.returns[keep, :],
        provenance=panel.provenance,
        findings=panel.findings,
    )


def _hostile_tests(
    panel: Panel,
    target: FloatArray,
    *,
    cost_bp: float,
    contribution: float,
    gamma: float,
    threshold: float,
    annual_interval: int,
) -> dict[str, JsonValue]:
    """Every hostile test the specification declares, plus the reason for any unrun."""
    months = panel.months
    flows = np.full(months, contribution, dtype=np.float64)

    def advantage(
        target_panel: Panel,
        *,
        weights: FloatArray | None = None,
        cost: float = cost_bp,
        band: float = threshold,
        interval: int = annual_interval,
        flow_amount: float | None = None,
    ) -> dict[str, float]:
        n = target_panel.months
        schedule = np.full(
            n, contribution if flow_amount is None else flow_amount, dtype=np.float64
        )
        return _policy_table(
            target_panel,
            target if weights is None else weights,
            cost_bp=cost,
            cash_flows=schedule,
            gamma=gamma,
            threshold=band,
            annual_interval=interval,
        )

    baseline = advantage(panel)
    tests: dict[str, JsonValue] = {
        "baseline_net_pessimistic": dict(baseline),
        "double_every_cost": dict(advantage(panel, cost=2.0 * cost_bp)),
        "quadruple_every_cost": dict(advantage(panel, cost=4.0 * cost_bp)),
        "threshold_20pct": dict(advantage(panel, band=0.20)),
        "threshold_30pct": dict(advantage(panel, band=0.30)),
        "zero_cash_flow": dict(advantage(panel, flow_amount=0.0)),
        "remove_2008_2009": dict(advantage(_drop_window(panel, "2008-01", "2009-12"))),
        "remove_2020_and_2022": dict(
            advantage(_drop_window(_drop_window(panel, "2020-01", "2020-12"), "2022-01", "2022-12"))
        ),
    }

    # Weight variation: plus and minus 10 percentage points of US equity, taken
    # from and given to the two non-US sleeves in proportion to their weights.
    us = panel.index_of("us_equity")
    for label, shift in (("us_plus_10pp", 0.10), ("us_minus_10pp", -0.10)):
        weights = target.copy()
        rest = np.array([i for i in range(target.size) if i != us])
        weights[us] += shift
        weights[rest] -= shift * target[rest] / float(np.sum(target[rest]))
        tests[f"starting_weights_{label}"] = dict(advantage(panel, weights=weights))

    # An annual policy whose advantage depends on the calendar month is an
    # artefact. The anchor is period zero, so dropping k leading months moves it.
    # The same number of trailing months is dropped as is needed to keep a whole
    # number of years, because the certainty equivalent is defined on complete
    # 12-month blocks and a partial year would silently change the statistic.
    for label, offset in (("june", 5), ("march", 2)):
        trailing = MONTHS_PER_YEAR - offset
        shifted = Panel(
            periods=panel.periods[offset : months - trailing],
            sleeves=panel.sleeves,
            returns=panel.returns[offset : months - trailing, :],
            provenance=panel.provenance,
            findings=panel.findings,
        )
        tests[f"annual_anchor_{label}"] = {
            "start": shifted.periods[0],
            "end": shifted.periods[-1],
            "months": shifted.months,
            "advantage_pp": dict(advantage(shifted)),
            "note": (
                "the annual rebalance is anchored at this window's first month. "
                "Leading and trailing months are dropped together so the sample "
                "stays a whole number of years. What matters is whether the annual "
                "policy's advantage moves between the two anchors: if it does, the "
                "calendar policy is a month artefact."
            ),
        }

    # A contribution held at a constant fraction of CURRENT wealth keeps the
    # cash-flow-directed policy powerful late in the sample. simulate takes a
    # fixed schedule, so this is approximated by scaling the schedule along the
    # buy-and-hold wealth path, which is identical for every policy and therefore
    # keeps the comparison fair.
    baseline_path = simulate(
        panel.returns,
        target,
        BuyAndHold(),
        cash_flows=flows,
        cost_model=ProportionalCostModel(cost_bp),
    ).equity_curve[:-1]
    scaled = np.asarray(contribution * baseline_path / baseline_path[0], dtype=np.float64)
    tests["contribution_tracking_current_wealth"] = dict(
        _policy_table(
            panel,
            target,
            cost_bp=cost_bp,
            cash_flows=scaled,
            gamma=gamma,
            threshold=threshold,
            annual_interval=annual_interval,
        )
    )

    # Remove the leading policy's best year and re-report. A result that lives in
    # one twelve-month block is an episode, not a policy. Whole years are removed
    # rather than single months because the certainty equivalent is defined on
    # complete 12-month blocks; the leading policy is whichever has the largest
    # baseline advantage, so this is not aimed at a policy chosen after the fact.
    leader = max(baseline, key=lambda policy: baseline[policy])
    leader_summary = summarise_policy(
        panel.returns,
        target,
        _policies(threshold, annual_interval)[leader],
        policy_id=leader,
        cost_basis="net-pessimistic",
        cost_bp=cost_bp,
        cash_flows=flows,
        gamma=gamma,
    )
    benchmark_summary = summarise_policy(
        panel.returns,
        target,
        BuyAndHold(),
        policy_id="buy_and_hold",
        cost_basis="net-pessimistic",
        cost_bp=cost_bp,
        cash_flows=flows,
        gamma=gamma,
    )
    excess = (leader_summary.monthly_returns - benchmark_summary.monthly_returns).reshape(
        -1, MONTHS_PER_YEAR
    )
    best_block = int(np.argmax(np.sum(excess, axis=1)))
    best_start = panel.periods[best_block * MONTHS_PER_YEAR]
    best_end = panel.periods[(best_block + 1) * MONTHS_PER_YEAR - 1]
    tests["remove_the_leading_policys_best_year"] = {
        "leading_policy": leader,
        "removed_window": f"{best_start}..{best_end}",
        "excess_return_removed_pp": 100.0 * float(np.sum(excess[best_block])),
        "advantage_pp": dict(advantage(_drop_window(panel, best_start, best_end))),
    }

    # The two-period identity, as a correctness check on the accounting.
    tests["two_period_identity"] = _two_period_identity_check()

    tests["not_run"] = {
        "delay_execution_by_a_further_month": (
            "NOT RUN. core.rebalance.simulate already executes a decision on the "
            "next period's return, which is the one-period lag this specification "
            "declares. Adding a second lag for the threshold policy would require "
            "a new RebalancePolicy member in core/, which this experiment is not "
            "permitted to add for a diagnostic. The annual_anchor_june and "
            "annual_anchor_march tests are execution shifts and are run; the "
            "threshold policy's sensitivity to a further delay is unmeasured and "
            "is recorded here as an open item rather than quietly omitted."
        ),
        "remove_the_single_best_month": (
            "NOT RUN as a single month. The certainty equivalent is defined on "
            "complete 12-month blocks, so removing one month would silently change "
            "the statistic rather than stress it. "
            "remove_the_leading_policys_best_year removes a whole block instead, "
            "which is a strictly harsher test on the same idea."
        ),
    }
    return tests


def _two_period_identity_check() -> dict[str, JsonValue]:
    """``R_rebal - R_hold = -w1 w2 k1 k2`` on a two-asset, two-period fixture.

    Computed two ways: from the closed identity, and by compounding the two
    portfolios by hand. They must agree to floating-point precision, which is what
    makes this a check on the accounting rather than a restatement of it.
    """
    weight = 0.6
    returns = np.array([[0.10, -0.05], [-0.04, 0.08]], dtype=np.float64)
    kappa = returns[:, 0] - returns[:, 1]
    identity = two_period_rebalance_advantage(weight, float(kappa[0]), float(kappa[1]))

    weights = np.array([weight, 1.0 - weight], dtype=np.float64)
    rebalanced = float(np.prod(1.0 + returns @ weights)) - 1.0
    held = float(np.dot(weights, np.prod(1.0 + returns, axis=0))) - 1.0
    return {
        "identity_value": identity,
        "simulated_difference": rebalanced - held,
        "absolute_error": abs(identity - (rebalanced - held)),
        "agrees": bool(abs(identity - (rebalanced - held)) < 1e-15),
    }


def _rolling_win_frequency(
    panel: Panel, first: str, second: str, *, horizons_years: Sequence[int]
) -> dict[str, JsonValue]:
    """Realised frequency with which 50/50 monthly rebalancing beat holding.

    Overlapping windows, which are **not** independent observations: a 30-year
    window inside a 35-year sample has six distinct start months. The figure is
    reported so that the closed-form probability has something to be compared
    with, not as a test.
    """
    returns = panel.pair(first, second)
    weights = np.array([0.5, 0.5], dtype=np.float64)
    monthly = np.log1p(returns @ weights)
    logs = np.log1p(returns)
    out: dict[str, JsonValue] = {}
    for years in horizons_years:
        width = years * MONTHS_PER_YEAR
        if width >= returns.shape[0]:
            continue
        wins = 0
        total = 0
        for start in range(returns.shape[0] - width + 1):
            rebalanced = float(np.sum(monthly[start : start + width]))
            components = np.sum(logs[start : start + width], axis=0)
            held = math.log(float(np.dot(weights, np.exp(components))))
            wins += int(rebalanced > held)
            total += 1
        out[f"{years}_year"] = {
            "windows": total,
            "overlapping": True,
            "realised_win_frequency": wins / total,
        }
    return out


# --------------------------------------------------------------------------- #
# The experiment
# --------------------------------------------------------------------------- #


def _investability_drag(
    cost_model: Mapping[str, JsonValue], weights: FloatArray, sleeves: Sequence[str]
) -> dict[str, JsonValue]:
    """The index-to-fund drag, reported in its own column and never applied."""
    block = _mapping(
        _at(cost_model, "index_to_fund_drag", where="cost_model"),
        where="cost_model.index_to_fund_drag",
    )
    expenses = _mapping(_at(block, "expense_ratio_bp_per_year", where="drag"), where="drag")
    withholding = _mapping(
        _at(block, "non_recoverable_withholding_bp_per_year", where="drag"), where="drag"
    )
    per_sleeve: dict[str, JsonValue] = {}
    total = 0.0
    for index, sleeve in enumerate(sleeves):
        fee = _number(expenses, sleeve, where="drag.expense_ratio_bp_per_year")
        tax = _number(withholding, sleeve, where="drag.non_recoverable_withholding_bp_per_year")
        weighted = float(weights[index]) * (fee + tax)
        total += weighted
        per_sleeve[sleeve] = {
            "weight": float(weights[index]),
            "expense_ratio_bp": fee,
            "non_recoverable_withholding_bp": tax,
            "weighted_contribution_bp": weighted,
        }
    return {
        "per_sleeve": per_sleeve,
        "portfolio_total_bp_per_year": total,
        "applied_to_any_reported_return": False,
        "expense_ratio_source": _text(block, "expense_ratio_source", where="drag"),
        "withholding_basis": _text(block, "withholding_basis", where="drag"),
        "spread_note": _text(block, "spread_note", where="drag"),
        "why_it_cannot_change_the_ranking": _text(
            block, "why_it_cannot_change_the_ranking", where="drag"
        ),
    }


def _reconstruction_error(panel: Panel) -> dict[str, JsonValue]:
    """How much of each sleeve's mean is the source's two-decimal printing.

    Each of ``Mkt-RF`` and ``RF`` is printed to two decimals in percent, so each
    carries an independent uniform rounding error of half-width 0.005 pp. Their
    sum has standard deviation ``sqrt(2 / 12) * 0.01`` pp per month, and the
    annualised mean over ``T`` months has standard deviation ``12 / sqrt(T)``
    times that. It is reported because it is the same order of magnitude as the
    effect under test, which is the only reason a rounding error ever matters.
    """
    width = 2.0 * _PRINT_HALF_WIDTH_DECIMAL
    per_cell_sd = width / math.sqrt(12.0)
    monthly_sd = per_cell_sd * math.sqrt(2.0)
    annual_mean_sd = monthly_sd * MONTHS_PER_YEAR / math.sqrt(panel.months)
    return {
        "printed_precision_percentage_points": 0.005,
        "monthly_reconstruction_sd_bp": 1e4 * monthly_sd,
        "annualised_mean_sd_bp": 1e4 * annual_mean_sd,
        "affects_kappa": False,
        "note": (
            "kappa is a difference of two sleeves and the RF term is the identical "
            "column in both files, so RF rounding cancels exactly. Only the level "
            "of each sleeve's mean carries it."
        ),
    }


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Execute Experiment 003 against the pinned regional equity vintages."""
    parameters = _mapping(specification.parameters, where="parameters")
    cost_model = _mapping(specification.cost_model, where="cost_model")
    universe = _mapping(specification.universe, where="universe")

    gamma = _number(parameters, "crra_gamma", where="parameters")
    threshold = _number(parameters, "relative_threshold", where="parameters")
    materiality = _number(parameters, "materiality_threshold_annual_percent", where="parameters")
    drawdown_tolerance = _number(
        parameters, "drawdown_tolerance_percentage_points", where="parameters"
    )
    annual_interval = MONTHS_PER_YEAR
    lags = _integers(parameters, "kappa_lags", where="parameters")
    vr_horizons = _integers(parameters, "variance_ratio_horizons_months", where="parameters")
    initial_wealth = _number(parameters, "initial_wealth", where="parameters")

    weights_block = _mapping(
        _at(universe, "starting_weights", where="universe"), where="universe.starting_weights"
    )
    panel = load_panel(specification)
    target = np.asarray(
        [
            _number(weights_block, sleeve, where="universe.starting_weights")
            for sleeve in panel.sleeves
        ],
        dtype=np.float64,
    )

    spread = _mapping(
        _at(cost_model, "spread_and_commission", where="cost_model"),
        where="cost_model.spread_and_commission",
    )
    cost_bases: dict[str, float] = {
        CostBasis.GROSS.value: 0.0,
        CostBasis.NET_OPTIMISTIC.value: _number(
            _mapping(_at(spread, "net_optimistic", where="spread"), where="spread"),
            "one_way_bps",
            where="spread.net_optimistic",
        ),
        CostBasis.NET_PESSIMISTIC.value: _number(
            _mapping(_at(spread, "net_pessimistic", where="spread"), where="spread"),
            "one_way_bps",
            where="spread.net_pessimistic",
        ),
    }
    decision_basis = _text(cost_model, "default_reported_column", where="cost_model")

    rebalance_rule = _mapping(specification.rebalance_rule, where="rebalance_rule")
    flows_block = _mapping(
        _at(rebalance_rule, "cash_flows", where="rebalance_rule"),
        where="rebalance_rule.cash_flows",
    )
    annual_fraction = _number(
        flows_block, "annual_amount_fraction_of_initial_wealth", where="cash_flows"
    )
    # The simulation is exactly scale-invariant when the contribution scales with
    # initial wealth, which it does here, so it is run at unit wealth and terminal
    # wealth is reported in multiples of the initial amount.
    if initial_wealth <= 0.0:
        raise RebalancingError(f"parameters.initial_wealth must be positive, got {initial_wealth}")
    contribution = annual_fraction / MONTHS_PER_YEAR
    cash_flows = np.full(panel.months, contribution, dtype=np.float64)

    # -- the policy comparison ------------------------------------------------ #
    summaries = compare_policies(
        panel,
        target,
        cost_bases=cost_bases,
        cash_flows=cash_flows,
        gamma=gamma,
        threshold=threshold,
        annual_interval=annual_interval,
    )

    block_length = 24.0
    resamples = specification.inference.resamples
    indices = stationary_bootstrap_indices(panel.months, block_length, resamples, context.rng)
    replicates = _bootstrap_differences(
        panel,
        target,
        cost_bases=cost_bases,
        cash_flows=cash_flows,
        gamma=gamma,
        threshold=threshold,
        annual_interval=annual_interval,
        indices=indices,
    )
    differences = _paired_differences(
        summaries,
        replicates,
        confidence_level=specification.inference.confidence_level,
        materiality=materiality,
    )

    ordered_policies = [
        policy for policy in _policies(threshold, annual_interval) if policy != "buy_and_hold"
    ]
    holm = holm_bonferroni(
        [differences[(policy, decision_basis)].p_value for policy in ordered_policies],
        alpha=1.0 - specification.inference.confidence_level,
    )

    # -- eras, as diagnostics only ------------------------------------------- #
    eras: dict[str, JsonValue] = {}
    for era in specification.sample_policy.eras:
        window = panel.window(start=era.start, end=era.end)
        era_flows = np.full(window.months, contribution, dtype=np.float64)
        era_advantage = _policy_table(
            window,
            target,
            cost_bp=cost_bases[decision_basis],
            cash_flows=era_flows,
            gamma=gamma,
            threshold=threshold,
            annual_interval=annual_interval,
        )
        eras[era.name] = {
            "start": era.start,
            "end": era.end,
            "months": window.months,
            "IS_A_DIAGNOSTIC_NOT_AN_INDEPENDENT_OBSERVATION": True,
            "certainty_equivalent_advantage_over_buy_and_hold_pp": era_advantage,
        }

    # -- the theory, tested -------------------------------------------------- #
    pairs = tuple(
        analyse_pair(panel, str(pair[0]), str(pair[1]))
        for pair in (
            _sequence(item, where="parameters.regional_pairs[]")
            for item in _sequence(
                _at(parameters, "regional_pairs", where="parameters"),
                where="parameters.regional_pairs",
            )
        )
    )
    dependence = tuple(
        serial_dependence(
            panel,
            pair.first,
            pair.second,
            lags=lags,
            variance_ratio_horizons=vr_horizons,
            rng=context.rng,
            block_length=block_length,
            n_resamples=min(resamples, 20_000),
            confidence_level=specification.inference.confidence_level,
        )
        for pair in pairs
    )
    rolling = {
        pair.name: _rolling_win_frequency(
            panel, pair.first, pair.second, horizons_years=(5, 10, 20, 30)
        )
        for pair in pairs
    }

    hostile = _hostile_tests(
        panel,
        target,
        cost_bp=cost_bases[decision_basis],
        contribution=contribution,
        gamma=gamma,
        threshold=threshold,
        annual_interval=annual_interval,
    )

    # -- the predeclared decision -------------------------------------------- #
    survivors = [
        policy
        for policy in ordered_policies
        if differences[(policy, decision_basis)].clears_materiality
        and differences[(policy, decision_basis)].excludes_zero
    ]
    era_names = [era.name for era in specification.sample_policy.eras if era.name != "full_sample"]

    def eras_supporting(policy: str) -> int:
        count = 0
        for name in era_names:
            payload = eras[name]
            assert isinstance(payload, Mapping)
            table = payload["certainty_equivalent_advantage_over_buy_and_hold_pp"]
            assert isinstance(table, Mapping)
            value = table[policy]
            assert isinstance(value, float | int)
            count += int(float(value) >= materiality)
        return count

    acceptable = [
        policy
        for policy in survivors
        if differences[(policy, decision_basis)].drawdown_gap_pp > -drawdown_tolerance
        and eras_supporting(policy) >= 2
        and bool(holm.rejected[ordered_policies.index(policy)])
    ]
    near_misses = [
        policy
        for policy in ordered_policies
        if differences[(policy, decision_basis)].clears_materiality
        and not differences[(policy, decision_basis)].excludes_zero
    ]

    if acceptable:
        status = ResultStatus.WALK_FORWARD_TESTED
        verdict = "NOT REJECTED"
    elif near_misses:
        status = ResultStatus.UNRESOLVED
        verdict = "UNRESOLVED"
    else:
        status = ResultStatus.REJECTED
        verdict = "REJECTED"

    best = max(
        ordered_policies,
        key=lambda policy: differences[(policy, decision_basis)].difference_percent,
    )
    best_difference = differences[(best, decision_basis)]
    summary = (
        f"{verdict}: PRETAX. Over {panel.months} months ({panel.periods[0]}..{panel.periods[-1]}) "
        f"on {', '.join(panel.sleeves)}, the best policy against buy-and-hold on the "
        f"{decision_basis} basis is {best} at {best_difference.difference_percent:+.3f} pp/yr "
        f"certainty-equivalent [{best_difference.lower:+.3f}, {best_difference.upper:+.3f}], "
        f"against a frozen materiality threshold of {materiality:.2f} pp/yr. "
        f"gamma_star on the three-sleeve portfolio and every regional pair is reported "
        f"predicted against realised, and the kappa serial-dependence diagnostic decides "
        f"whether the mechanism that could make rebalancing profitable is present."
    )

    diagnostics: dict[str, JsonValue] = {
        "verdict": verdict,
        "pretax": True,
        "decision_cost_basis": decision_basis,
        "sample": {
            "start": panel.periods[0],
            "end": panel.periods[-1],
            "months": panel.months,
            "years": panel.years,
            "sleeves": list(panel.sleeves),
            "target_weights": [float(value) for value in target],
            "monthly_contribution": contribution,
            "total_contributions": float(np.sum(cash_flows)),
        },
        "source": [dict(record) for record in panel.provenance],
        "data_findings": list(panel.findings),
        "reconstruction_error": _reconstruction_error(panel),
        "risk_free_treatment": _text(universe, "risk_free_treatment", where="universe"),
        "data_integrity_finding": _text(universe, "data_integrity_finding", where="universe"),
        "policies": [summary.to_json() for summary in summaries.values()],
        "paired_differences": [item.to_json() for item in differences.values()],
        "multiple_testing": {
            "method": holm.method,
            "family": ordered_policies,
            "raw_p_values": [float(value) for value in holm.p_values],
            "adjusted_p_values": [float(value) for value in holm.adjusted_p_values],
            "rejected": [bool(value) for value in holm.rejected],
            "alpha": holm.alpha,
        },
        "eras": eras,
        "portfolio_excess_growth": portfolio_excess_growth(panel, target),
        "pair_theory": [pair.to_json() for pair in pairs],
        "kappa_serial_dependence": [item.to_json() for item in dependence],
        "rolling_win_frequency": rolling,
        "investability_drag": _investability_drag(cost_model, target, panel.sleeves),
        "hostile_tests": hostile,
        "bootstrap": {
            "method": "stationary block bootstrap on the joint sleeve panel",
            "block_length_months": block_length,
            "block_length_is_frozen_not_tuned": True,
            "politis_white_diagnostic_only": [
                item.politis_white_block for item in dependence
            ],
            "resamples": resamples,
            "confidence_level": specification.inference.confidence_level,
        },
        "diversification_return_statement": (
            "The diversification-return identity g_p - sum w_i g_i was NOT used as "
            "evidence anywhere in this experiment. It appears once, in "
            "portfolio_excess_growth, because gamma_star is defined against it, and "
            "it is labelled there as a benchmark nobody can hold."
        ),
    }

    estimates = _estimates(summaries, differences, pairs, dependence, decision_basis)
    caveats = (
        "PRETAX. No tax of any kind is modelled and no constant tax haircut is "
        "applied. The simulation holds no tax lots, so it cannot know a basis and "
        "therefore may not price a realisation. In a taxable account the ranking "
        "would move against the higher-turnover policies, because a rebalance "
        "realises gain that buy-and-hold defers; the size of that move is not "
        "estimated here and must not be guessed.",
        "These are index-like regional total returns, not investable funds. They "
        "carry no expense ratio, no bid-ask spread, no tracking difference and no "
        "withholding tax. Those are reported in the investability_drag column and "
        "never applied to a return. Any claim about what an investor would have "
        "received is capped at exploratory by decision 0002.",
        "The decades are DIAGNOSTICS. Three overlapping regimes inside one "
        "35-year sample are not three independent observations, and no statement "
        "about any policy is made from a single era.",
        "Ken French rebuilds each region's whole history from every new source "
        "vintage and publishes no vintage archive. The sha256 pins identify which "
        "files were used; they do not establish what was available at any earlier "
        "date, so nothing here is point-in-time.",
        "The source is monthly, so intramonth threshold breaches are invisible and "
        "no intramonth execution is modelled. A daily threshold policy would trade "
        "more often than the one measured here.",
        "Deploying a contribution is charged no transaction cost, for every policy "
        "identically. The total notional deployed is the contribution itself and is "
        "the same under every policy, so at a flat basis-point rate this omission "
        "cancels in every paired difference; it understates every policy's absolute "
        "cost by the same amount.",
        "The stationary bootstrap preserves short-range dependence at the frozen "
        "24-month mean block length and attenuates it beyond that. Autocorrelations "
        "at lags approaching or exceeding the block length have conservatively wide "
        "intervals for that reason.",
        "Rolling-window win frequencies use overlapping windows, which are not "
        "independent observations. A 30-year window inside a 35-year sample has six "
        "distinct start months.",
    )

    return ExperimentResult(
        status=status,
        summary=summary,
        estimates=estimates,
        diagnostics=diagnostics,
        caveats=caveats,
        frames=_frames(summaries, differences, pairs, dependence, eras),
    )


def _estimates(
    summaries: Mapping[tuple[str, str], PolicySummary],
    differences: Mapping[tuple[str, str], PairedDifference],
    pairs: Sequence[PairTheory],
    dependence: Sequence[SerialDependence],
    decision_basis: str,
) -> tuple[Estimate, ...]:
    """The decision-relevant numbers, each with its units and its uncertainty."""
    method = (
        "stationary block bootstrap on the joint sleeve panel, mean block 24 months "
        "frozen not tuned, percentile interval on the paired difference"
    )
    out: list[Estimate] = []
    for basis in (CostBasis.GROSS, CostBasis.NET_OPTIMISTIC, CostBasis.NET_PESSIMISTIC):
        baseline = summaries[("buy_and_hold", basis.value)]
        out.append(
            Estimate(
                name="buy_and_hold certainty-equivalent return",
                value=baseline.certainty_equivalent_percent,
                units="percentage points per year",
                cost_basis=basis,
                n_obs=baseline.months,
                uncertainty_unavailable_reason=(
                    "the decision is taken on the paired difference, so the level's "
                    "interval would invite a comparison the specification forbids; "
                    "the paired intervals below are the reportable uncertainty"
                ),
                notes="PRETAX, CRRA gamma = 3 on 35 non-overlapping calendar years",
            )
        )
        for policy in sorted({key[0] for key in differences if key[1] == basis.value}):
            item = differences[(policy, basis.value)]
            out.append(
                Estimate(
                    name=f"{policy} minus buy-and-hold certainty-equivalent return",
                    value=item.difference_percent,
                    units="percentage points per year",
                    interval=(item.lower, item.upper),
                    interval_method=method,
                    cost_basis=basis,
                    n_obs=summaries[(policy, basis.value)].months,
                    notes=(
                        f"PRETAX. bootstrap p = {item.p_value:.4f}; max drawdown "
                        f"{item.drawdown_gap_pp:+.2f} pp versus buy-and-hold"
                        + (" (decision basis)" if basis.value == decision_basis else "")
                    ),
                )
            )
    for pair in pairs:
        out.append(
            Estimate(
                name=f"{pair.name} gamma_star, realised minus predicted",
                value=1e4 * (pair.gamma_star_realised - pair.gamma_star_continuous),
                units="basis points per year",
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=pair.months,
                uncertainty_unavailable_reason=(
                    "both terms are computed from the same single realised path, so "
                    "their difference has no sampling distribution that is not the "
                    "path's own; the discrete-monthly prediction beside it is the "
                    "size of the model's own approximation"
                ),
                notes=(
                    f"predicted continuous {1e4 * pair.gamma_star_continuous:.1f} bp, "
                    f"predicted discrete-monthly {1e4 * pair.gamma_star_discrete_monthly:.1f} bp, "
                    f"realised {1e4 * pair.gamma_star_realised:.1f} bp"
                ),
            )
        )
        out.append(
            Estimate(
                name=f"{pair.name} realised rebalanced minus buy-and-hold log growth",
                value=1e4 * pair.realised_advantage,
                units="basis points per year",
                interval=(
                    1e4 * pair.predicted_q05_equal_drift,
                    1e4 * pair.predicted_q95_equal_drift,
                ),
                interval_method=(
                    "closed-form 5th and 95th percentiles of the equal-drift model, "
                    "not a sampling interval: it is the model's own predicted band "
                    "and the realised value is asked whether it falls inside it"
                ),
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=pair.months,
                notes=(
                    f"equal-drift mean {1e4 * pair.predicted_advantage_equal_drift:.1f} bp; "
                    f"with the realised {100.0 * pair.drift_gap:.2f} pp/yr drift gap the "
                    f"predicted mean is {1e4 * pair.predicted_advantage_with_drift:.1f} bp"
                ),
            )
        )
    for diagnostic in dependence:
        index = diagnostic.lags.index(1)
        out.append(
            Estimate(
                name=f"{diagnostic.pair} kappa lag-1 autocorrelation",
                value=diagnostic.autocorrelation[index],
                units="correlation",
                interval=(diagnostic.block_lower[index], diagnostic.block_upper[index]),
                interval_method=(
                    "stationary block bootstrap percentile interval, mean block 24 "
                    "months, frozen not tuned"
                ),
                cost_basis=CostBasis.NOT_APPLICABLE,
                n_obs=diagnostic.observations,
                notes=(
                    "positive means relative performance trends and rebalancing is "
                    "predicted to lose; negative means it reverses and rebalancing "
                    "is predicted to gain. i.i.d. null band ["
                    f"{diagnostic.iid_null_lower[index]:.4f}, "
                    f"{diagnostic.iid_null_upper[index]:.4f}]"
                ),
            )
        )
    return tuple(out)


def _frames(
    summaries: Mapping[tuple[str, str], PolicySummary],
    differences: Mapping[tuple[str, str], PairedDifference],
    pairs: Sequence[PairTheory],
    dependence: Sequence[SerialDependence],
    eras: Mapping[str, JsonValue],
) -> dict[str, pd.DataFrame]:
    kappa_rows: list[dict[str, float | str | int]] = []
    for item in dependence:
        for index, lag in enumerate(item.lags):
            kappa_rows.append(
                {
                    "pair": item.pair,
                    "lag": lag,
                    "autocorrelation": item.autocorrelation[index],
                    "block_lower": item.block_lower[index],
                    "block_upper": item.block_upper[index],
                    "iid_null_lower": item.iid_null_lower[index],
                    "iid_null_upper": item.iid_null_upper[index],
                }
            )
    era_rows: list[dict[str, float | str | int]] = []
    for name, payload in eras.items():
        assert isinstance(payload, Mapping)
        table = payload["certainty_equivalent_advantage_over_buy_and_hold_pp"]
        assert isinstance(table, Mapping)
        for policy, value in table.items():
            assert isinstance(value, float | int)
            era_rows.append({"era": name, "policy": policy, "advantage_pp": float(value)})
    return {
        "policy_comparison": pd.DataFrame([item.to_json() for item in summaries.values()]),
        "paired_differences": pd.DataFrame([item.to_json() for item in differences.values()]),
        "pair_theory": pd.DataFrame([item.to_json() for item in pairs]),
        "kappa_autocorrelation": pd.DataFrame(kappa_rows),
        "era_diagnostics": pd.DataFrame(era_rows),
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
    return _workspace_root() / "experiments" / "exp_003_rebalancing.yaml"


def _render_console_report(outcome: RunOutcome) -> str:
    """The numbers, for a human. Calling this is what ``results_viewed`` records."""
    result = outcome.result
    if result is None:  # pragma: no cover - run_experiment raises before this
        return "no result"
    diagnostics = result.diagnostics
    lines = [result.summary, ""]

    policies = diagnostics.get("policies")
    if isinstance(policies, Sequence) and not isinstance(policies, str):
        header = (
            f"{'policy':<26}{'basis':<17}{'CE%':>8}{'geo%':>8}{'vol%':>8}"
            f"{'MDD%':>8}{'TUW':>6}{'turn%':>8}{'cost%':>8}{'trades':>8}{'devpp':>8}{'termW':>9}"
        )
        lines.extend(["PRETAX policy comparison", header, "-" * len(header)])
        for item in policies:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"{item['policy']!s:<26}{item['cost_basis']!s:<17}"
                f"{float(str(item['certainty_equivalent_percent_per_year'])):>8.3f}"
                f"{float(str(item['geometric_return_percent_per_year'])):>8.3f}"
                f"{float(str(item['volatility_percent_per_year'])):>8.2f}"
                f"{float(str(item['max_drawdown_percent'])):>8.1f}"
                f"{int(str(item['time_under_water_months'])):>6d}"
                f"{float(str(item['annual_one_sided_turnover_percent'])):>8.2f}"
                f"{float(str(item['annual_transaction_cost_percent'])):>8.4f}"
                f"{int(str(item['rebalance_count'])):>8d}"
                f"{float(str(item['mean_absolute_weight_deviation_pp'])):>8.2f}"
                f"{float(str(item['terminal_wealth'])):>9.3f}"
            )
        lines.append("")

    paired = diagnostics.get("paired_differences")
    if isinstance(paired, Sequence) and not isinstance(paired, str):
        lines.append("Paired certainty-equivalent difference from buy-and-hold, pp/yr")
        for item in paired:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"  {item['policy']!s:<26}{item['cost_basis']!s:<17}"
                f"{float(str(item['certainty_equivalent_difference_pp_per_year'])):>+8.3f} "
                f"[{float(str(item['interval_lower'])):+.3f}, "
                f"{float(str(item['interval_upper'])):+.3f}] "
                f"p={float(str(item['bootstrap_p_value'])):.4f}"
            )
        lines.append("")

    theory = diagnostics.get("pair_theory")
    if isinstance(theory, Sequence) and not isinstance(theory, str):
        lines.append("gamma_star and the closed form, per 50/50 regional pair (bp/yr)")
        for item in theory:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"  {item['pair']!s:<42} predicted "
                f"{float(str(item['gamma_star_continuous_bp'])):>7.1f}"
                f"  discrete {float(str(item['gamma_star_discrete_monthly_bp'])):>7.1f}"
                f"  realised {float(str(item['gamma_star_realised_bp'])):>7.1f}"
            )
            lines.append(
                f"  {'':<42} rebal-hold realised "
                f"{float(str(item['realised_rebalanced_minus_held_bp'])):>+8.1f}"
                f"  predicted(equal drift) "
                f"{float(str(item['predicted_mean_equal_drift_bp'])):>+8.1f}"
                f"  predicted(with drift) "
                f"{float(str(item['predicted_mean_with_drift_bp'])):>+9.1f}"
            )
            lines.append(
                f"  {'':<42} drift gap "
                f"{float(str(item['drift_gap_percent_per_year'])):>+6.2f} pp/yr"
                f"  P(win) equal {float(str(item['probability_equal_drift'])):.4f}"
                f"  with drift {float(str(item['probability_with_drift'])):.4f}"
                f"  inside 5-95 band: {item['realised_inside_equal_drift_5_95_band']}"
            )
        lines.append("")

    kappa = diagnostics.get("kappa_serial_dependence")
    if isinstance(kappa, Sequence) and not isinstance(kappa, str):
        lines.append("kappa serial dependence: the diagnostic that decides the mechanism")
        for item in kappa:
            if not isinstance(item, Mapping):
                continue
            autocorrelations = item["autocorrelation"]
            lag_labels = item["lags"]
            assert isinstance(autocorrelations, Sequence) and isinstance(lag_labels, Sequence)
            lines.append(f"  {item['pair']}")
            rendered = "  ".join(
                f"L{lag_labels[i]}={float(str(autocorrelations[i])):+.3f}"
                for i in range(min(6, len(lag_labels)))
            )
            lines.append(f"    {rendered}")
            lines.append(
                f"    lags outside the i.i.d. null: {item['lags_outside_the_iid_null']}; "
                f"Ljung-Box(12) p={float(str(item['ljung_box_p'])):.4f}; "
                f"on kappa^2 p={float(str(item['ljung_box_squared_p'])):.4g}; "
                f"skew={float(str(item['skewness'])):+.2f}; "
                f"excess kurtosis={float(str(item['excess_kurtosis'])):.2f}"
            )
            ratios = item["variance_ratios"]
            assert isinstance(ratios, Sequence)
            rendered_vr = "  ".join(
                f"VR({r['horizon_months']})={float(str(r['variance_ratio'])):.3f}"
                f"(z2={float(str(r['z_heteroskedastic'])):+.2f})"
                for r in ratios
                if isinstance(r, Mapping)
            )
            lines.append(f"    {rendered_vr}")
        lines.append("")

    eras = diagnostics.get("eras")
    if isinstance(eras, Mapping):
        lines.append("Era diagnostics (NOT independent observations), pp/yr vs buy-and-hold")
        for name, payload in eras.items():
            if not isinstance(payload, Mapping):
                continue
            table = payload["certainty_equivalent_advantage_over_buy_and_hold_pp"]
            assert isinstance(table, Mapping)
            rendered = "  ".join(f"{k}={float(str(v)):+.3f}" for k, v in table.items())
            lines.append(f"  {name!s:<20}{payload['start']}..{payload['end']}  {rendered}")
        lines.append("")

    drag = diagnostics.get("investability_drag")
    if isinstance(drag, Mapping):
        lines.append(
            f"Index-to-fund drag, reported separately and applied to nothing: "
            f"{float(str(drag['portfolio_total_bp_per_year'])):.1f} bp/yr"
        )
        lines.append("")

    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 003 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_003_rebalancing",
        description=(
            "Compare five unlevered rebalancing policies on regional equity total "
            "returns, writing a ledger entry for the attempt."
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
                "exp_003_rebalancing"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
