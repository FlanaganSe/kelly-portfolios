"""Experiment 013: the US factor shelf audited on a frame that can see it.

The defect this experiment corrects
-----------------------------------
Experiment 002 audited the US factor shelf against the **2019Q4 N-PORT census
alone**. Experiment 009 then audited the ex-US shelf against the **union** of the
2019Q4 and 2025Q4 censuses, and said why in its own specification: "AVDV launched
2019-09; AVIV, AVES and DISV in 2021-09; DFIV in 2021-11; DFEV in 2022. A
2019Q4-only frame would have excluded exactly the products the question is
about."

**That correction was never applied to the US shelf, and the same launch wave hit
it.** AVUV listed 2019-09; AVLV and AVSC in 2021; Dimensional converted DFAT,
DFAS, DFAC and DFUS into ETFs in 2021 and launched DFSV, DFLV and DUHP in 2022.
A long tail of Schwab, Vanguard and Fidelity products is missing from the 2019Q4
file for a duller reason: N-PORT filings are made on each registrant's own fiscal
calendar, so a trust whose quarter did not close inside the filing window that
quarter is simply not in that census, whatever its age. Either way, Experiment
002 could not see them, and the omission is not random: it removes the newest,
cheapest and highest-loading systematic products, which is the direction that
makes "the exposure is delivered, the value is not" easier to conclude.

What this experiment is, and what it is not
-------------------------------------------
It is Experiment 002 re-run on the corrected frame. It is **not** an edit to
Experiment 002, whose specification hash, committed universe and published
numbers are untouched and whose two screening regexes are asserted byte-for-byte
before this run, exactly as Experiment 009 does. Every statistic is computed by
the *same* functions Experiment 002 used --
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.fit_exposure`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.shrink_alpha`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.minimum_detectable_alpha`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.replicating_weights`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.fetch_fund_series` --
against the same US FF5+UMD panel over the same frozen 2020-01..2025-12 window,
so a fund common to both audits is estimated on exactly the same 72 months and
reproduces its Experiment 002 numbers by construction rather than by luck.

Two criteria move and no others
-------------------------------
1. The frame becomes the union of the two censuses, with the asset floor applied
   to the maximum of a series' two observed net-asset figures.
2. The inception cutoff of 2016-12-31 is deleted, and a **sample-length**
   requirement replaces it: at least 36 filed monthly returns, as in Experiment
   009. A young fund is `unresolved` on a short window, never absent.

The window trap, stated before the results
------------------------------------------
A post-2019 launch has fewer than 72 months, so its standard errors are larger,
its minimum detectable effect is larger, and more of its verdicts will be
`unresolved`. **That is the correct outcome and not a problem to engineer
around.** Every estimate carries its own month count and its own MDE at 80%
power, and the falsifier can only ever move a short-window fund to `unresolved`,
never to `rejected` for shortness.

Run it::

    uv run python -m portfolio_edge.experiments.exp_013_us_products_union_frame \\
        --build-universe
    uv run python -m portfolio_edge.experiments.exp_013_us_products_union_frame \\
        --view-results
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import yaml
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.manifest import read_manifest
from portfolio_edge.experiments.exp_002_fund_exposure import (
    FACTOR_SPECIFICATIONS,
    MONTHS_PER_YEAR,
    PRIMARY_SPECIFICATION,
    ExposureFit,
    FactorPanel,
    FundSeries,
    fetch_fund_series,
    fit_exposure,
    inflated_family,
    load_factor_panel,
    replicating_weights,
    secondary_monthly_returns,
)
from portfolio_edge.experiments.exp_002_universe import (
    ProductFacts,
    resolve_ticker,
    workspace_root,
)
from portfolio_edge.experiments.exp_002_universe import (
    load_universe as load_exp_002_universe,
)
from portfolio_edge.experiments.exp_009_exus_products import (
    FundWindow,
    _first_whole_month,
    contiguous_window,
    minimum_detectable_loading,
)
from portfolio_edge.experiments.exp_013_universe import (
    ScreenedUsFund,
    UnionUniverse,
    build_universe,
    exp_002_screen_is_unmodified,
    load_extra_facts,
    load_product_facts,
    load_universe,
    universe_manifests,
    universe_path,
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
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "UnionFrameError",
    "UsWindowPolicy",
    "build_registry",
    "default_specification_path",
    "main",
    "run",
    "window_for",
]

ENTRY_POINT: Final = "exp_013_us_products_union_frame"

FloatArray = NDArray[np.float64]


class UnionFrameError(RuntimeError):
    """The audit could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to the frozen specification
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise UnionFrameError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise UnionFrameError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise UnionFrameError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise UnionFrameError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise UnionFrameError(f"{where}.{key} must be a number, got {value!r}")
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
# The window a young fund may actually be estimated on
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class UsWindowPolicy:
    """The three cuts that decide which months of a fund this experiment may use.

    Frozen in the specification and applied to every fund identically, so no
    month can be added or removed after a return has been seen.
    """

    start: str
    end: str
    drop_first_filed_month_when_history_starts_late: bool = True
    """Drop the first filed month of a fund whose history does not reach ``start``.

    A fund that launched or converted inside the window files an Item B.5 return
    for its launch month covering part of a month. Regressed against a whole
    month of factor returns that is not a small observation, it is a
    differently-scaled one, and its beta is attenuated by roughly the fraction of
    the month the product did not exist. This rule needs no external fact: if the
    filed history does not reach the window start, the first month it does reach
    is a stub. It costs one observation for a fund that happened to list on the
    first of a month, and that is the conservative direction.
    """


def window_for(
    series: FundSeries,
    panel: FactorPanel,
    *,
    policy: UsWindowPolicy,
    inception: str | None,
) -> FundWindow:
    """The months of one fund this experiment may use, after three cuts.

    The frozen window, the fund's own filed and panel-covered coverage, and the
    launch cut. ``inception`` is the date the **exchange-traded product** began,
    which for a converted fund is not the date its SEC series began: DFAT's
    series carries filings from the predecessor Tax-Managed portfolio, and using
    them would audit a fund nobody could have bought at that fee.
    """
    floor = policy.start
    if inception is not None:
        floor = max(floor, _first_whole_month(inception))
    inside = sorted(
        period
        for period in series.periods
        if month_index(policy.start) <= month_index(period) <= month_index(policy.end)
    )
    if (
        policy.drop_first_filed_month_when_history_starts_late
        and inside
        and month_index(inside[0]) > month_index(policy.start)
    ):
        floor = max(floor, period_from_index(month_index(inside[0]) + 1))

    available = {
        period for period in inside if month_index(period) >= month_index(floor)
    }
    usable = sorted(available & set(panel.periods))
    contiguous = contiguous_window(usable)
    dropped = tuple(period for period in usable if period not in set(contiguous))
    return FundWindow(
        ticker=series.ticker,
        region="us",
        periods=contiguous,
        filed_periods=tuple(inside),
        dropped_before_gap=dropped,
        filings=series.filing_count,
        amendments=series.amendment_count,
        filings_held_out=series.filings_held_out,
        warnings=series.warnings,
    )


# --------------------------------------------------------------------------- #
# Small helpers over the panel and one fund's returns
# --------------------------------------------------------------------------- #


def _window_key(window: FundWindow) -> str:
    """Label for a distinct estimation window.

    The month COUNT is part of the key, not decoration: two funds can share a
    first and a last month and still be estimated on different months if one has
    an internal gap, and giving them the same pedestal would compare a fund's
    alpha against a control fitted on months it did not have.
    """
    return f"{window.first}..{window.last} ({window.months}m)"


def _rows_for(panel: FactorPanel, periods: Sequence[str]) -> NDArray[np.intp]:
    index = {period: position for position, period in enumerate(panel.periods)}
    return np.asarray([index[period] for period in periods], dtype=np.intp)


def _total(series: FundSeries, periods: Sequence[str]) -> FloatArray:
    available = dict(zip(series.periods, series.returns, strict=True))
    return np.asarray([available[period] for period in periods], dtype=np.float64)


def _excess(series: FundSeries, panel: FactorPanel, periods: Sequence[str]) -> FloatArray:
    return _total(series, periods) - panel.risk_free[_rows_for(panel, periods)]


def _covered(series: FundSeries, periods: Sequence[str]) -> bool:
    return bool(periods) and set(periods) <= set(series.periods)


def _net_expense(facts: ProductFacts | None) -> float:
    if facts is None or facts.net_expense_ratio_percent is None:
        return 0.0
    return facts.net_expense_ratio_percent


def _finite(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``.

    Unequal windows are the normal case here, so a fund can genuinely have no
    first-half loading. JSON has no NaN and writing one would put a token in a
    results file that most readers parse as a number.
    """
    return value if math.isfinite(value) else None


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplicationResult:
    """What a long-only combination of cheap broad US funds does to a product."""

    ticker: str
    basis: tuple[str, ...]
    weights: tuple[float, ...]
    months: int
    tracking_difference_vs_combination: float
    tracking_error_vs_combination: float
    tracking_difference_vs_market: float
    tracking_error_vs_market: float
    fee_premium_over_basis: float
    implementation_shortfall: float

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "basis": list(self.basis),
            "weights": list(self.weights),
            "months": self.months,
            "tracking_difference_vs_combination_pp": self.tracking_difference_vs_combination,
            "tracking_error_vs_combination_pp": self.tracking_error_vs_combination,
            "tracking_difference_vs_market_pp": self.tracking_difference_vs_market,
            "tracking_error_vs_market_pp": self.tracking_error_vs_market,
            "fee_premium_over_basis_pp": self.fee_premium_over_basis,
            "implementation_shortfall_pp": self.implementation_shortfall,
        }


@dataclass(slots=True, kw_only=True)
class UnionOutcome:
    """The per-fund verdict, with every falsifier clause that fired."""

    ticker: str
    series_name: str
    mandate: str
    intended_factor: str
    intended_sign: int
    months: int
    first_month: str
    last_month: str
    visible_to_exp_002_frame: bool
    in_exp_002_audit: bool
    status: str
    clauses_fired: list[str] = field(default_factory=list)
    intended_loading: float = float("nan")
    intended_loading_se: float = float("nan")
    intended_loading_mde: float = float("nan")
    intended_loading_interval: tuple[float, float] = (float("nan"), float("nan"))
    intended_loading_first_half: float = float("nan")
    intended_loading_second_half: float = float("nan")
    alpha_annual_percent: float = float("nan")
    shrunk_alpha_annual_percent: float = float("nan")
    alpha_mde_percent: float = float("nan")
    pedestal_on_this_window: float = float("nan")
    max_drawdown_percent: float = float("nan")
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "series_name": self.series_name,
            "mandate": self.mandate,
            "intended_factor": self.intended_factor,
            "intended_sign": self.intended_sign,
            "months": self.months,
            "first_month": self.first_month,
            "last_month": self.last_month,
            "visible_to_exp_002_frame": self.visible_to_exp_002_frame,
            "audited_by_exp_002": self.in_exp_002_audit,
            "status": self.status,
            "falsifier_clauses_fired": list(self.clauses_fired),
            "intended_loading": _finite(self.intended_loading),
            "intended_loading_se": _finite(self.intended_loading_se),
            "intended_loading_mde_80pc_power": _finite(self.intended_loading_mde),
            "intended_loading_interval": [
                _finite(value) for value in self.intended_loading_interval
            ],
            "intended_loading_first_half": _finite(self.intended_loading_first_half),
            "intended_loading_second_half": _finite(self.intended_loading_second_half),
            "alpha_annual_percent": _finite(self.alpha_annual_percent),
            "shrunk_alpha_annual_percent": _finite(self.shrunk_alpha_annual_percent),
            "alpha_mde_80pc_power_percent": _finite(self.alpha_mde_percent),
            "pedestal_on_this_window_pp": _finite(self.pedestal_on_this_window),
            "max_drawdown_percent": _finite(self.max_drawdown_percent),
            "notes": list(self.notes),
        }


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_013_us_products_union_frame.yaml"


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


# --------------------------------------------------------------------------- #
# The audit
# --------------------------------------------------------------------------- #


def _fetch_all(
    cache: RawCache,
    *,
    tickers: Mapping[str, tuple[str, str]],
    start: str,
    end: str,
) -> tuple[dict[str, FundSeries], list[dict[str, JsonValue]]]:
    """Download Item B.5 histories for the funds that PASSED the screen.

    A fund that failed the screen is never fetched. That is the whole point of
    committing the universe first: a screen decision cannot be revised after
    seeing performance if the performance was never obtained.
    """
    series: dict[str, FundSeries] = {}
    failures: list[dict[str, JsonValue]] = []
    for ticker, (series_id, class_id) in sorted(tickers.items()):
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
                    "consequence": "unresolved; this fund contributes no estimate",
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
    """Experiment 002's gate, unchanged, on the same comparator and months.

    Item B.5 orders its three returns earliest-first, so the month ending on the
    reporting date is the THIRD. A reversed reading would shift every history by
    two months and leave every number looking plausible, so the alignment is
    tested rather than trusted: a cheap total-market fund must reproduce the
    market factor and must show its worst month in 2020-03.
    """
    if comparator not in series:
        raise UnionFrameError(
            f"the comparator {comparator} has no usable history, so nothing in this "
            "experiment can be benchmarked and no gate can be checked"
        )
    rows = _rows_for(panel, periods)
    fund = _total(series[comparator], periods)
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
        raise UnionFrameError(
            "the data path failed its validation gates before any fund result was "
            "computed: " + "; ".join(findings)
        )
    return {
        "comparator": comparator,
        "months": len(periods),
        "correlation_with_market_total_return": correlation,
        "market_beta": beta,
        "r_squared": r_squared,
        "worst_month": worst_month,
        "worst_month_return_percent": float(np.min(fund)) * 100.0,
        "interpretation": (
            "The alignment of Item B.5's three returns to calendar months is "
            "confirmed against an independent series, not assumed. Identical to "
            "Experiment 002's gate, on the same comparator and the same months."
        ),
    }


def _era_windows(specification: Specification) -> dict[str, tuple[str, str]]:
    return {era.name: (era.start, era.end) for era in specification.sample_policy.eras}


def _slice_era(periods: Sequence[str], era: tuple[str, str]) -> tuple[str, ...]:
    first, last = month_index(era[0]), month_index(era[1])
    return tuple(period for period in periods if first <= month_index(period) <= last)


def _fit_all_specifications(
    *,
    ticker: str,
    era: str,
    series: FundSeries,
    panel: FactorPanel,
    periods: Sequence[str],
    hac_lags: int,
    dispersion: float,
    power: float,
) -> dict[str, ExposureFit]:
    excess = _excess(series, panel, periods)
    rows = _rows_for(panel, periods)
    return {
        name: fit_exposure(
            ticker=ticker,
            specification=name,
            era=era,
            excess_returns=excess,
            design=panel.design(factors, rows),
            factor_names=factors,
            n_lags=min(hac_lags, max(1, len(periods) // 6)),
            dispersion_annual_percent=dispersion,
            power=power,
        )
        for name, factors in FACTOR_SPECIFICATIONS.items()
    }


def _fit_one(
    series: FundSeries,
    panel: FactorPanel,
    periods: Sequence[str],
    *,
    ticker: str,
    era: str,
    hac_lags: int,
    dispersion: float,
    power: float,
) -> ExposureFit | None:
    """Fit the primary specification on ``periods``, or ``None`` if it cannot be."""
    usable = tuple(period for period in periods if period in set(panel.periods))
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    if len(usable) <= len(factors) + 2 or not _covered(series, usable):
        return None
    return fit_exposure(
        ticker=ticker,
        specification=PRIMARY_SPECIFICATION,
        era=era,
        excess_returns=_excess(series, panel, usable),
        design=panel.design(factors, _rows_for(panel, usable)),
        factor_names=factors,
        n_lags=min(hac_lags, max(1, len(usable) // 6)),
        dispersion_annual_percent=dispersion,
        power=power,
    )


def _bootstrap_interval(
    *,
    series: FundSeries,
    panel: FactorPanel,
    periods: Sequence[str],
    factor: str,
    rng: np.random.Generator,
    resamples: int,
    confidence: float,
    block_lengths: Sequence[float] = (3.0, 6.0, 12.0),
) -> dict[str, list[float]]:
    """Stationary block-bootstrap intervals for one loading.

    Rows are resampled JOINTLY across the fund return and the whole factor
    design, so the regressor-error dependence HAC exists for survives inside each
    resample. Resampling residuals alone would assume the very independence the
    block length is there to avoid assuming.
    """
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    rows = _rows_for(panel, periods)
    design = np.column_stack([np.ones(len(periods)), panel.design(factors, rows)])
    y = _excess(series, panel, periods)
    column = factors.index(factor) + 1
    lower_q = 100.0 * (1.0 - confidence) / 2.0
    upper_q = 100.0 - lower_q

    out: dict[str, list[float]] = {}
    for block_length in block_lengths:
        indices = stationary_bootstrap_indices(len(periods), block_length, resamples, rng)
        y_batch = y[indices]
        x_batch = design[indices]
        xtx = np.einsum("btk,btl->bkl", x_batch, x_batch)
        xty = np.einsum("btk,bt->bk", x_batch, y_batch)
        ridge = 1e-12 * np.eye(design.shape[1])
        solved = np.linalg.solve(xtx + ridge, xty[:, :, None])
        draws = np.asarray(solved[:, column, 0], dtype=np.float64)
        out[f"block_{int(block_length)}"] = [
            float(np.percentile(draws, lower_q)),
            float(np.percentile(draws, upper_q)),
        ]
    return out


def _replicate(
    *,
    fund: ScreenedUsFund,
    window: FundWindow,
    series: Mapping[str, FundSeries],
    comparator: str,
    basis: Sequence[str],
    facts: Mapping[str, ProductFacts],
) -> ReplicationResult | None:
    """Fit the cheap long-only combination that best tracks this product.

    Experiment 002's comparator, unchanged: VTI, VUG, VTV and VB with
    non-negative weights summing to one, fitted by constrained least squares on
    the SAME months as the exposure regression. An investor could not have known
    those weights in advance, so this is a BEST CASE for the replication and
    therefore a HARD test for the product, and it is never described as an
    achievable alternative. A fund is never part of the basis that replicates it:
    three of the four building blocks are themselves audited products and leaving
    one in would hand it a weight of one and a tracking difference of zero.
    """
    usable_basis = [
        ticker
        for ticker in basis
        if ticker != fund.ticker
        and ticker in series
        and _covered(series[ticker], window.periods)
    ]
    if not usable_basis or comparator not in series:
        return None
    if not _covered(series[comparator], window.periods):
        return None

    target = _total(series[fund.ticker], window.periods)
    matrix = np.column_stack([_total(series[ticker], window.periods) for ticker in usable_basis])
    weights = replicating_weights(target, matrix)
    combination = matrix @ weights
    market = _total(series[comparator], window.periods)

    difference = target - combination
    against_market = target - market
    basis_fee = sum(
        float(weights[i]) * _net_expense(facts.get(ticker))
        for i, ticker in enumerate(usable_basis)
    )
    fund_fee = _net_expense(facts.get(fund.ticker, fund.facts))
    tracking_difference = float(np.mean(difference)) * MONTHS_PER_YEAR * 100.0
    return ReplicationResult(
        ticker=fund.ticker,
        basis=tuple(usable_basis),
        weights=tuple(float(value) for value in weights),
        months=len(window.periods),
        tracking_difference_vs_combination=tracking_difference,
        tracking_error_vs_combination=float(np.std(difference, ddof=1))
        * math.sqrt(MONTHS_PER_YEAR)
        * 100.0,
        tracking_difference_vs_market=float(np.mean(against_market)) * MONTHS_PER_YEAR * 100.0,
        tracking_error_vs_market=float(np.std(against_market, ddof=1))
        * math.sqrt(MONTHS_PER_YEAR)
        * 100.0,
        fee_premium_over_basis=fund_fee - basis_fee,
        # POSITIVE means the product lost MORE to its cheap replication than its
        # extra fee explains: implementation cost paid on top of the fee.
        implementation_shortfall=-tracking_difference - (fund_fee - basis_fee),
    )


def _pedestal(
    *,
    comparator: str,
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
    hac_lags: int,
    dispersion: float,
    power: float,
    facts: Mapping[str, ProductFacts],
) -> dict[str, JsonValue]:
    """The alpha the factor model gives a fund that is, by construction, the market.

    A cap-weighted total-market fund holds the market portfolio, so under a
    correctly specified model its alpha must be about minus its three-basis-point
    fee. Anything further from zero is the model failing to span this window, not
    the fund doing something, and EVERY fund's alpha carries it. A fund's alpha is
    meaningful only as a distance from this pedestal, never from zero.
    """
    record = series.get(comparator)
    usable = tuple(
        period for period in periods if record is not None and period in record.periods
    )
    if record is None or len(usable) < 24:
        return {"available": False, "comparator": comparator}
    fits = _fit_all_specifications(
        ticker=comparator,
        era="pedestal",
        series=record,
        panel=panel,
        periods=usable,
        hac_lags=hac_lags,
        dispersion=dispersion,
        power=power,
    )
    primary = fits[PRIMARY_SPECIFICATION]
    return {
        "available": True,
        "comparator": comparator,
        "months": len(usable),
        "first_month": usable[0],
        "last_month": usable[-1],
        "net_expense_ratio_percent": _net_expense(facts.get(comparator)),
        "by_specification": {
            name: {
                "alpha_annual_percent": fit.alpha_annual_percent,
                "alpha_se_annual_percent": fit.alpha_se_annual_percent,
                "alpha_t": fit.alpha_t,
                "market_beta": fit.loadings["Mkt-RF"],
                "r_squared": fit.r_squared,
            }
            for name, fit in fits.items()
        },
        "pedestal_annual_percent": primary.alpha_annual_percent,
        "interpretation": (
            "A cap-weighted total-market fund IS the market portfolio, so its alpha "
            "under a correctly specified model should be about minus its expense "
            "ratio. The distance of this number from that is model misfit shared by "
            "every fund in the audit. Read each fund's alpha as a distance from this "
            "pedestal, not from zero."
        ),
    }


def _verdict(
    *,
    fund: ScreenedUsFund,
    window: FundWindow,
    audited_by_exp_002: bool,
    fits: Mapping[str, ExposureFit],
    halves: Mapping[str, ExposureFit],
    interval: Mapping[str, list[float]],
    replication: ReplicationResult | None,
    series: Mapping[str, FundSeries],
    pedestal: float,
    minimum_loading: float,
    materiality: float,
) -> UnionOutcome:
    """Apply Experiment 002's frozen falsifier clause by clause, verbatim."""
    factor = fund.intended_factor or ""
    sign = fund.intended_sign or 1
    outcome = UnionOutcome(
        ticker=fund.ticker,
        series_name=fund.series_name,
        mandate="" if fund.facts is None else fund.facts.stated_mandate,
        intended_factor=factor,
        intended_sign=sign,
        months=window.months,
        first_month=window.first,
        last_month=window.last,
        visible_to_exp_002_frame=fund.in_exp_002_frame,
        in_exp_002_audit=audited_by_exp_002,
        status="unresolved",
        pedestal_on_this_window=pedestal,
    )
    primary = fits.get(PRIMARY_SPECIFICATION)
    if primary is None or not factor:
        outcome.notes.append("no primary fit; nothing to decide")
        return outcome

    outcome.intended_loading = primary.loadings[factor] * sign
    outcome.intended_loading_se = primary.standard_errors[factor]
    outcome.intended_loading_mde = minimum_detectable_loading(primary.standard_errors[factor])
    outcome.alpha_annual_percent = primary.alpha_annual_percent
    outcome.shrunk_alpha_annual_percent = primary.shrunk_alpha_annual_percent
    outcome.alpha_mde_percent = primary.minimum_detectable_alpha_percent

    equity = np.cumprod(1.0 + _total(series[fund.ticker], window.periods))
    outcome.max_drawdown_percent = drawdown_summary(equity).max_drawdown * 100.0

    bounds = interval.get("block_6")
    if bounds is not None and len(bounds) == 2:
        low, high = bounds[0] * sign, bounds[1] * sign
        outcome.intended_loading_interval = (min(low, high), max(low, high))

    first = halves.get("first_half")
    second = halves.get("second_half")
    if first is not None:
        outcome.intended_loading_first_half = first.loadings[factor] * sign
    if second is not None:
        outcome.intended_loading_second_half = second.loadings[factor] * sign

    # (a) the intended exposure is not there
    if outcome.intended_loading < minimum_loading:
        outcome.clauses_fired.append(
            f"(a) intended {factor} loading {outcome.intended_loading:+.3f} is below "
            f"{minimum_loading:.2f}"
        )
    # (b) the exposure changes sign across the fixed split, where both are covered
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
    elif not (
        math.isfinite(outcome.intended_loading_first_half)
        and math.isfinite(outcome.intended_loading_second_half)
    ):
        outcome.notes.append(
            "clause (b) could not be evaluated: the fund's filed history does not "
            "cover both fixed halves, which is a statement about its age"
        )
    if replication is not None:
        # (c) the cheap combination beat it by more than its fee premium plus 0.50
        if replication.implementation_shortfall > 0.50:
            outcome.clauses_fired.append(
                f"(c) lost {-replication.tracking_difference_vs_combination:+.2f} pp/yr "
                f"to its cheap replication against a fee premium of only "
                f"{replication.fee_premium_over_basis:+.2f} pp/yr"
            )
        # (d) total cost above the comparator without a corresponding exposure
        total_cost = _net_expense(fund.facts) + max(
            0.0, -replication.tracking_difference_vs_combination
        )
        if total_cost > materiality and outcome.intended_loading < minimum_loading:
            outcome.clauses_fired.append(
                f"(d) total cost of ownership {total_cost:.2f} pp/yr exceeds "
                f"{materiality:.2f} with no corresponding exposure"
            )
    else:
        outcome.notes.append(
            "clauses (c) and (d) could not be evaluated: no basis fund covers this "
            "fund's whole window, so no replication was fitted"
        )

    low, high = outcome.intended_loading_interval
    if outcome.clauses_fired:
        outcome.status = "rejected"
    elif math.isfinite(low) and low <= minimum_loading <= high:
        outcome.status = "unresolved"
        outcome.notes.append(
            f"the 95% interval [{low:+.3f}, {high:+.3f}] contains the "
            f"{minimum_loading:.2f} threshold over {window.months} months; the "
            f"smallest loading this window could have detected at 80% power is "
            f"{outcome.intended_loading_mde:.3f}"
        )
    else:
        outcome.status = "exploratory"
    return outcome


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Audit every screened US product on the corrected frame."""
    parameters = _mapping(specification.parameters, where="parameters")
    exp_002_screen_is_unmodified(_exp_002_parameters())

    universe_block = _mapping(specification.universe, where="universe")
    comparators = _mapping(_at(universe_block, "comparators", where="universe"), where="universe")
    comparator = _text(
        _mapping(_at(comparators, "broad_market", where="comparators"), where="broad_market"),
        "ticker",
        where="comparators.broad_market",
    )
    basis = _strings(
        _mapping(
            _at(comparators, "synthetic_combination", where="comparators"), where="combination"
        ),
        "basis",
        where="comparators.synthetic_combination",
    )

    shrinkage = _mapping(
        _at(parameters, "alpha_shrinkage", where="parameters"), where="alpha_shrinkage"
    )
    dispersion = _number(shrinkage, "sigma_true_annual_percent", where="alpha_shrinkage")
    minimum_loading = _number(parameters, "minimum_intended_loading", where="parameters")
    materiality = _number(parameters, "materiality_threshold_annual_percent", where="parameters")
    hac_lags = int(_number(parameters, "hac_lags", where="parameters"))
    minimum_months = int(_number(parameters, "minimum_monthly_observations", where="parameters"))
    power = _number(parameters, "power_target", where="parameters")
    rolling_window = int(_number(parameters, "rolling_window_months", where="parameters"))

    universe = load_universe()
    facts = load_product_facts()
    extras = load_extra_facts()
    panel = load_factor_panel(specification)
    cache = RawCache()

    eras = _era_windows(specification)
    window_start, window_end = eras["common_period"]
    policy = UsWindowPolicy(start=window_start, end=window_end)
    full_periods = tuple(
        period_from_index(index)
        for index in range(month_index(window_start), month_index(window_end) + 1)
    )

    wanted: dict[str, tuple[str, str]] = {
        fund.ticker: (fund.series_id, fund.class_id) for fund in universe.passing
    }
    for ticker in (comparator, *basis):
        if ticker not in wanted:
            series_id, class_id, _name = resolve_ticker(cache, ticker)
            wanted[ticker] = (series_id, class_id)
    series, fetch_failures = _fetch_all(
        cache, tickers=wanted, start=window_start, end=window_end
    )

    gates = _validate_data_path(
        comparator=comparator, series=series, panel=panel, periods=full_periods
    )

    exp_002_audited = _exp_002_audited_tickers()

    # --- per-fund windows and coverage
    windows: dict[str, FundWindow] = {}
    coverage: list[dict[str, JsonValue]] = []
    usable: list[ScreenedUsFund] = []
    for fund in universe.passing:
        record = series.get(fund.ticker)
        if record is None:
            coverage.append(
                {"ticker": fund.ticker, "usable": False, "reason": "no filings retrieved"}
            )
            continue
        extra = extras.get(fund.ticker)
        inception = None
        if extra is not None and extra.etf_inception_date is not None:
            inception = extra.etf_inception_date
        elif fund.facts is not None:
            inception = fund.facts.inception_date
        window = window_for(record, panel, policy=policy, inception=inception)
        windows[fund.ticker] = window
        filed_first = min(record.periods) if record.periods else ""
        coverage.append(
            {
                "ticker": fund.ticker,
                "usable": window.months >= minimum_months,
                "months_usable": window.months,
                "first_month": window.first,
                "last_month": window.last,
                "months_filed_in_window": len(window.filed_periods),
                "first_month_filed_in_window": filed_first,
                "inception_used": inception,
                "converted_from_mutual_fund": (
                    None if extra is None else extra.converted_from_mutual_fund
                ),
                "months_dropped_before_an_internal_gap": list(window.dropped_before_gap),
                "filings": window.filings,
                "amendments": window.amendments,
                "filings_held_out_after_window": window.filings_held_out,
                "visible_to_exp_002_frame": fund.in_exp_002_frame,
                "audited_by_exp_002": fund.ticker in exp_002_audited,
                "reason": (
                    ""
                    if window.months >= minimum_months
                    else f"{window.months} usable months is below the {minimum_months} "
                    "minimum, which is a statement about the fund's age and not "
                    "about the fund"
                ),
            }
        )
        if window.months >= minimum_months:
            usable.append(fund)

    # --- exposure fits on each fund's own window
    all_fits: dict[str, dict[str, ExposureFit]] = {}
    half_fits: dict[tuple[str, str], ExposureFit] = {}
    flat_fits: list[ExposureFit] = []
    for fund in usable:
        window = windows[fund.ticker]
        record = series[fund.ticker]
        own = _fit_all_specifications(
            ticker=fund.ticker,
            era="common_period",
            series=record,
            panel=panel,
            periods=window.periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        all_fits[fund.ticker] = own
        flat_fits.extend(own.values())
        for era_name in ("first_half", "second_half", "covid_drawdown", "value_reversal"):
            era_start, era_end = eras[era_name]
            era_periods = _slice_era(window.periods, (era_start, era_end))
            # Clause (b) is a SIGN test on two point estimates, so a half the fund
            # only partly covers can flip it on noise alone -- and the frozen
            # falsifier says in terms that a fund is never rejected for the
            # shortness of a window it did not choose. So the two halves that
            # decide clause (b) are fitted only where the fund covers the WHOLE
            # half, which is the situation Experiment 002 was always in because
            # every fund it audited had all 72 months. A fund that does not is
            # recorded as "clause (b) not evaluable", never as passing it.
            if era_name in ("first_half", "second_half") and len(era_periods) != month_count(
                era_start, era_end
            ):
                continue
            fit = _fit_one(
                record,
                panel,
                era_periods,
                ticker=fund.ticker,
                era=era_name,
                hac_lags=hac_lags,
                dispersion=dispersion,
                power=power,
            )
            if fit is not None:
                half_fits[(fund.ticker, era_name)] = fit

    # --- bootstrap intervals on the intended loading
    intervals: dict[str, dict[str, list[float]]] = {}
    for fund in usable:
        if fund.intended_factor is None:
            continue
        intervals[fund.ticker] = _bootstrap_interval(
            series=series[fund.ticker],
            panel=panel,
            periods=windows[fund.ticker].periods,
            factor=fund.intended_factor,
            rng=context.rng,
            resamples=specification.inference.resamples,
            confidence=specification.inference.confidence_level,
        )

    replications: dict[str, ReplicationResult] = {}
    for fund in usable:
        result = _replicate(
            fund=fund,
            window=windows[fund.ticker],
            series=series,
            comparator=comparator,
            basis=basis,
            facts=facts,
        )
        if result is not None:
            replications[fund.ticker] = result

    # --- the pedestal, on the full window and on every distinct fund window
    pedestal_full = _pedestal(
        comparator=comparator,
        series=series,
        panel=panel,
        periods=full_periods,
        hac_lags=hac_lags,
        dispersion=dispersion,
        power=power,
        facts=facts,
    )
    pedestal_by_window: dict[str, float] = {}
    for fund in usable:
        key = _window_key(windows[fund.ticker])
        if key in pedestal_by_window:
            continue
        block = _pedestal(
            comparator=comparator,
            series=series,
            panel=panel,
            periods=windows[fund.ticker].periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            facts=facts,
        )
        if block.get("available"):
            pedestal_by_window[key] = float(str(block["pedestal_annual_percent"]))

    outcomes = [
        _verdict(
            fund=fund,
            window=windows[fund.ticker],
            audited_by_exp_002=fund.ticker in exp_002_audited,
            fits=all_fits[fund.ticker],
            halves={
                era: fit for (ticker, era), fit in half_fits.items() if ticker == fund.ticker
            },
            interval=intervals.get(fund.ticker, {}),
            replication=replications.get(fund.ticker),
            series=series,
            pedestal=pedestal_by_window.get(_window_key(windows[fund.ticker]), float("nan")),
            minimum_loading=minimum_loading,
            materiality=materiality,
        )
        for fund in usable
    ]

    # --- multiple testing over the whole family
    alpha_p = np.asarray([fit.alpha_p for fit in flat_fits], dtype=np.float64)
    bh = benjamini_hochberg(alpha_p, alpha=0.10) if alpha_p.size else None
    holm = holm_bonferroni(alpha_p, alpha=0.10) if alpha_p.size else None

    primary = {
        fit.ticker: fit for fit in flat_fits if fit.specification == PRIMARY_SPECIFICATION
    }
    loading_p = np.asarray(
        [
            _intended_p_value(primary[fund.ticker], fund)
            for fund in usable
            if fund.ticker in primary
        ],
        dtype=np.float64,
    )
    loading_bh = benjamini_hochberg(loading_p, alpha=0.10) if loading_p.size else None

    rolling = _rolling_loadings(
        usable=usable,
        windows=windows,
        series=series,
        panel=panel,
        window_months=rolling_window,
    )
    cross_source = _cross_check(cache, [fund.ticker for fund in usable], series, windows)

    lengths = [window.months for window in windows.values()]
    added = _frame_correction(universe, usable, outcomes, exp_002_audited)

    summary = (
        f"Screened {universe.mandate_matches} mandate-matching fund series from the "
        f"UNION of the {universe.frame_quarter} and {universe.follow_up_quarter} "
        f"N-PORT censuses; {len(universe.passing)} passed the predeclared screen and "
        f"{len(usable)} had at least {minimum_months} filed monthly returns. "
        f"Experiment 002's 2019Q4-only frame with its 2016 inception cutoff audited "
        f"{added['funds_audited_by_exp_002']} of them, so the corrected frame adds "
        f"{added['funds_added']} products. "
        f"{sum(1 for item in outcomes if item.status == 'exploratory')} reached "
        f"`exploratory`, {sum(1 for item in outcomes if item.status == 'rejected')} were "
        f"`rejected` on the frozen falsifier and "
        f"{sum(1 for item in outcomes if item.status == 'unresolved')} are `unresolved`. "
        f"Median usable history is {int(np.median(lengths)) if lengths else 0} months "
        f"against Experiment 002's uniform 72. The binding constraint is the data "
        f"contract and the length of the available windows, not the evidence."
    )

    diagnostics: dict[str, JsonValue] = {
        "relationship_to_experiment_002": {
            "what_changed": (
                "The FRAME and the INCEPTION CUTOFF, and nothing else. Experiment "
                "002's screen was not modified: its two regexes were asserted "
                "byte-for-byte before this run and its committed universe file was "
                "not written to. Every statistic here is computed by the same "
                "functions over the same frozen window, so a fund common to both "
                "audits reproduces its Experiment 002 numbers by construction."
            ),
            "criteria_changed": [
                "frame: 2019Q4 census only -> union of 2019Q4 and 2025Q4, with the "
                "asset floor on the MAXIMUM of the two observed net-asset figures",
                "inception_cutoff 2016-12-31: DELETED, replaced by a "
                "minimum_monthly_observations requirement at estimation time",
            ],
            "criteria_unchanged": [
                "mandate_regex",
                "exclusion_regex",
                "exchange_traded",
                "minimum_net_assets_usd = 1e9",
                "maximum_net_expense_ratio_percent = 0.60",
                "intended_factor_map and its signs",
                "falsifier clauses (a) 0.15, (b) sign flip, (c) 0.50 pp/yr, (d) 1.0 pp/yr",
                "comparator VTI and basis VTI/VUG/VTV/VB, fitted in sample",
                "window 2020-01..2025-12, HAC 6 lags, block 6 months, 10,000 resamples",
            ],
            "changed_exp_002_results": "none",
            "frame_correction": added,
        },
        "universe": {
            "committed_file": str(universe_path().relative_to(workspace_root())),
            "sha256": _sha256_file(universe_path()),
            "frame_quarters": [universe.frame_quarter, universe.follow_up_quarter],
            "union_series_count": universe.union_series_count,
            "mandate_matches": universe.mandate_matches,
            "screened": len(universe.funds),
            "passed_screen": len(universe.passing),
            "usable_returns": len(usable),
            "attrition": plain_json(universe.attrition.to_json()),
        },
        "screen": plain_json([fund.to_json() for fund in universe.funds]),
        "coverage": coverage,
        "fetch_failures": fetch_failures,
        "validation_gates": gates,
        "factor_provenance": dict(panel.provenance),
        "window_policy": {
            "start": policy.start,
            "end": policy.end,
            "minimum_monthly_observations": minimum_months,
            "launch_stub_rule": (
                "The first filed month of a fund whose history inside the window "
                "does not reach the window start is dropped, because for a fund "
                "that launched or converted inside the window that month covers "
                "part of a month and its beta is attenuated by the fraction of the "
                "month the product did not exist. Where an ETF inception or "
                "conversion date is committed, the floor is the first WHOLE "
                "calendar month after it and the later of the two cuts wins."
            ),
            "median_months": int(np.median(lengths)) if lengths else 0,
            "shortest_months": min(lengths) if lengths else 0,
            "longest_months": max(lengths) if lengths else 0,
        },
        "exposures": [fit.to_json() for fit in flat_fits],
        "subperiod_exposures": [fit.to_json() for fit in half_fits.values()],
        "bootstrap_intervals": {
            ticker: {name: list(bounds) for name, bounds in blocks.items()}
            for ticker, blocks in intervals.items()
        },
        "rolling_loadings": rolling,
        "replication": [item.to_json() for item in replications.values()],
        "cross_source_check": cross_source,
        "model_misfit_pedestal": pedestal_full,
        "model_misfit_pedestal_by_window": pedestal_by_window,
        "multiple_testing": {
            "family_definition": (
                "every fund with usable returns times every model specification "
                "estimated, not only the funds and specification reported"
            ),
            "family_size": int(alpha_p.size),
            "funds": len(usable),
            "specifications": list(FACTOR_SPECIFICATIONS),
            "alpha": _correction_json(flat_fits, bh, holm),
            "denominator_hostile_test": {
                "why": (
                    "A fund that failed the screen was never regressed and so has "
                    "no p-value, but the search still passed over it. Padding the "
                    "family to its full width with p = 1.0 cannot create a "
                    "rejection and strictly tightens both corrections."
                ),
                "tests_run": inflated_family(
                    [fit.alpha_p for fit in flat_fits], family_size=len(flat_fits)
                ),
                "all_funds_that_passed_the_screen": inflated_family(
                    [fit.alpha_p for fit in flat_fits],
                    family_size=max(
                        len(flat_fits), len(universe.passing) * len(FACTOR_SPECIFICATIONS)
                    ),
                ),
                "every_mandate_matching_series_screened": inflated_family(
                    [fit.alpha_p for fit in flat_fits],
                    family_size=max(
                        len(flat_fits), len(universe.funds) * len(FACTOR_SPECIFICATIONS)
                    ),
                ),
            },
            "intended_loading": {
                "family_size": int(loading_p.size),
                "rejected_uncorrected": int(np.sum(loading_p <= 0.05)) if loading_p.size else 0,
                "rejected_benjamini_hochberg": (
                    int(np.sum(loading_bh.rejected)) if loading_bh is not None else 0
                ),
            },
        },
        "outcomes": [item.to_json() for item in outcomes],
        "unobservable": {
            "realised_taxable_distributions": (
                "NOT AVAILABLE. Form N-PORT reports a single total return and no "
                "distribution split; the income and capital-gain history is in the "
                "annual report on Form N-CSR as unstructured HTML. Recorded as a "
                "gap rather than estimated, so clause (d) is evaluated without the "
                "distribution term the falsifier names."
            ),
            "portfolio_turnover": (
                "NOT AVAILABLE from Form N-PORT. The fund's internal trading cost "
                "is inside the tracking difference and is reported there rather "
                "than modelled."
            ),
            "stated_index_returns": (
                "NOT AVAILABLE. Index levels are licensed, so every tracking "
                "difference here is against a CONSTRUCTED benchmark and never "
                "against the fund's own stated index."
            ),
        },
    }

    caveats = _caveats(usable, windows, flat_fits, outcomes, minimum_months, added)
    estimates = _estimates(outcomes, all_fits, replications)

    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=summary,
        estimates=tuple(estimates),
        diagnostics=diagnostics,
        caveats=tuple(caveats),
        frames=_frames(universe, flat_fits, replications, outcomes, coverage),
    )


# --------------------------------------------------------------------------- #
# Helpers the audit calls
# --------------------------------------------------------------------------- #


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exp_002_parameters() -> Mapping[str, object]:
    """Experiment 002's frozen parameters, read from its own committed YAML."""
    path = workspace_root() / "experiments" / "exp_002_fund_exposure.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    parameters = payload.get("parameters") if isinstance(payload, dict) else None
    if not isinstance(parameters, dict):
        raise UnionFrameError("exp_002_fund_exposure.yaml has no parameters block")
    return parameters


def _exp_002_audited_tickers() -> frozenset[str]:
    """The tickers Experiment 002's screen passed, from its committed universe.

    Read rather than retyped, so "the corrected frame adds N products" is a
    difference of two committed files rather than a claim.
    """
    return frozenset(fund.ticker for fund in load_exp_002_universe().passing)


def _frame_correction(
    universe: UnionUniverse,
    usable: Sequence[ScreenedUsFund],
    outcomes: Sequence[UnionOutcome],
    exp_002_audited: frozenset[str],
) -> dict[str, JsonValue]:
    """What the frame correction admitted, and what it did to the verdicts."""
    added = [fund for fund in usable if fund.ticker not in exp_002_audited]
    added_outcomes = [item for item in outcomes if item.ticker not in exp_002_audited]
    invisible = [fund for fund in universe.passing if not fund.in_exp_002_frame]
    return {
        "funds_passing_the_screen": len(universe.passing),
        "funds_with_usable_returns": len(usable),
        "funds_audited_by_exp_002": len([f for f in usable if f.ticker in exp_002_audited]),
        "funds_added": len(added),
        "added_tickers": sorted(fund.ticker for fund in added),
        "added_absent_from_the_2019q4_census": sorted(
            fund.ticker for fund in added if not fund.in_exp_002_frame
        ),
        "added_present_in_2019q4_but_excluded_by_another_criterion": sorted(
            fund.ticker for fund in added if fund.in_exp_002_frame
        ),
        "passing_series_invisible_to_the_2019q4_frame": len(invisible),
        "added_status_counts": {
            status: sum(1 for item in added_outcomes if item.status == status)
            for status in ("exploratory", "rejected", "unresolved")
        },
        "interpretation": (
            "A fund can be added for two different reasons and they are counted "
            "separately. Absent from the 2019Q4 census means Experiment 002's frame "
            "could not see the series at all -- either it did not exist, or its "
            "registrant's fiscal calendar put no filing in that quarter. Present but "
            "excluded means the series was in the frame and failed a criterion that "
            "has since moved, which here is the inception cutoff or the asset floor "
            "measured at the 2019 date alone."
        ),
    }


def _intended_p_value(fit: ExposureFit, fund: ScreenedUsFund) -> float:
    """One-sided p-value that the intended loading exceeds nothing, in its own sign."""
    from scipy.stats import norm

    factor = fund.intended_factor
    if factor is None or factor not in fit.loadings:
        return 1.0
    signed_t = fit.t_statistics[factor] * (fund.intended_sign or 1)
    return float(norm.sf(signed_t))


def _rolling_loadings(
    *,
    usable: Sequence[ScreenedUsFund],
    windows: Mapping[str, FundWindow],
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    window_months: int,
) -> list[dict[str, JsonValue]]:
    """Rolling intended-factor loading, to test stability instead of assuming it."""
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    out: list[dict[str, JsonValue]] = []
    for fund in usable:
        if fund.intended_factor is None:
            continue
        window = windows[fund.ticker]
        if window.months < window_months + 6:
            out.append(
                {
                    "ticker": fund.ticker,
                    "factor": fund.intended_factor,
                    "windows": 0,
                    "reason": (
                        f"{window.months} months cannot support a {window_months}-month "
                        "rolling estimate with any room to roll"
                    ),
                }
            )
            continue
        rows = _rows_for(panel, window.periods)
        design = np.column_stack([np.ones(window.months), panel.design(factors, rows)])
        y = _excess(series[fund.ticker], panel, window.periods)
        column = factors.index(fund.intended_factor) + 1
        values: list[float] = []
        labels: list[str] = []
        for end in range(window_months, window.months + 1):
            block = slice(end - window_months, end)
            beta, *_ = np.linalg.lstsq(design[block], y[block], rcond=None)
            values.append(float(beta[column]) * (fund.intended_sign or 1))
            labels.append(window.periods[end - 1])
        out.append(
            {
                "ticker": fund.ticker,
                "factor": fund.intended_factor,
                "window_months": window_months,
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


def _cross_check(
    cache: RawCache,
    tickers: Sequence[str],
    series: Mapping[str, FundSeries],
    windows: Mapping[str, FundWindow],
) -> dict[str, JsonValue]:
    """Compare the filed return against the secondary source, month by month.

    Two independent measurements of the same quantity are the only cheap way to
    see a silent adjustment error. Agreement is evidence about the data and about
    nothing else; it does not make either source research-grade, and no result
    here depends on it.
    """
    rows: list[dict[str, JsonValue]] = []
    unavailable: list[str] = []
    for ticker in tickers:
        record = series.get(ticker)
        window = windows.get(ticker)
        if record is None or window is None:
            continue
        try:
            secondary, digest = secondary_monthly_returns(cache, ticker)
        except Exception as exc:
            unavailable.append(f"{ticker}: {type(exc).__name__}")
            continue
        filed = dict(zip(record.periods, record.returns, strict=True))
        shared = [
            period for period in window.periods if period in filed and period in secondary
        ]
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


def _correction_json(
    fits: Sequence[ExposureFit], bh: object, holm: object
) -> dict[str, JsonValue]:
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
            "NOT independent: the same six factors, overlapping windows and three "
            "nested specifications per fund, and several pairs of funds track one "
            "index under two sponsors. So the Benjamini-Hochberg count is an "
            "OPTIMISTIC bound and Holm is the defensible one."
        )
    return payload


def _estimates(
    outcomes: Sequence[UnionOutcome],
    fits: Mapping[str, Mapping[str, ExposureFit]],
    replications: Mapping[str, ReplicationResult],
) -> list[Estimate]:
    out: list[Estimate] = []
    for outcome in outcomes:
        fit = fits[outcome.ticker].get(PRIMARY_SPECIFICATION)
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
                    f"of the return and the whole design, on the fund's own "
                    f"{outcome.months}-month window"
                )
                if math.isfinite(low)
                else "",
                uncertainty_unavailable_reason=(
                    "" if math.isfinite(low) else "no bootstrap interval was computed"
                ),
                cost_basis=CostBasis.NET_OPTIMISTIC,
                n_obs=fit.n_observations,
                notes=(
                    f"sign-adjusted for the mandate; smallest loading this window "
                    f"could detect at 80% power {outcome.intended_loading_mde:.3f}; "
                    f"status {outcome.status}"
                ),
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
                    f"shrinkage factor {fit.shrinkage_factor:.3f}, a minimum "
                    f"detectable alpha at 80% power of "
                    f"{fit.minimum_detectable_alpha_percent:.2f} pp/yr over "
                    f"{outcome.months} months, and a model-misfit pedestal on the "
                    f"same window of {outcome.pedestal_on_this_window:+.2f} pp/yr."
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
                    value=replication.implementation_shortfall,
                    units="percentage points per year",
                    interval=None,
                    uncertainty_unavailable_reason=(
                        "The replicating weights are fitted IN SAMPLE, so this is a "
                        "best case for the replication and a hard test for the "
                        "product. A sampling interval around a look-ahead quantity "
                        "would imply a precision the construction does not have."
                    ),
                    cost_basis=CostBasis.NET_OPTIMISTIC,
                    notes=f"basis {list(replication.basis)} over {replication.months} months",
                )
            )
    return out


def _caveats(
    usable: Sequence[ScreenedUsFund],
    windows: Mapping[str, FundWindow],
    fits: Sequence[ExposureFit],
    outcomes: Sequence[UnionOutcome],
    minimum_months: int,
    added: Mapping[str, JsonValue],
) -> list[str]:
    median_mde = (
        float(np.median([fit.minimum_detectable_alpha_percent for fit in fits]))
        if fits
        else float("nan")
    )
    lengths = [window.months for window in windows.values()]
    return [
        "EXPLORATORY. Decision 0002 stands: this may not promote a sleeve and may "
        "not appear in the app as a finding.",
        "This experiment corrects a FRAME, not a method. Experiment 002's screen, "
        "specification hash and committed universe are untouched, and its two "
        "regexes are asserted byte-for-byte before this run.",
        f"Windows run from {min(lengths) if lengths else 0} to "
        f"{max(lengths) if lengths else 0} months and are UNEQUAL across funds, so a "
        "cross-fund comparison of alphas is a comparison of differently powered "
        "estimates. The median minimum detectable alpha at 80% power is "
        f"{median_mde:.2f} pp/yr, larger than any plausible true alpha. The newly "
        "admitted funds are the short-window ones by construction, so they are the "
        "least measurable part of the shelf and the frame correction cannot fix that.",
        f"A fund with fewer than {minimum_months} usable months is reported and "
        "excluded from estimation rather than estimated badly. Its absence is a "
        "statement about its age, not about the product.",
        "The replicating combination is fitted IN SAMPLE from VTI, VUG, VTV and VB. "
        "An investor could not have known those weights in advance, so it is a best "
        "case for the replication and the comparison against it is deliberately hard "
        "on the product. Three of the four building blocks are themselves audited "
        "products and a fund is never in its own basis, so for VUG, VTV and VB the "
        "replication degenerates and their shortfall is the realised style return of "
        "the window rather than an implementation cost.",
        "Every alpha is shrunk by its own factor from its own standard error, and is "
        "a distance from the model-misfit pedestal rather than from zero. The raw "
        "alpha, its HAC standard error and its MDE are printed beside it and it must "
        "never be quoted alone.",
        "Item B.5 returns are fund-reported and unaudited, and General Instruction G "
        "lets each filer use its own methodology.",
        "The union frame is LESS survivorship-selecting than a 2019Q4-only frame but "
        "is not survivorship-free: public N-PORT filings begin in 2019, so a fund "
        "that closed before then is invisible to both censuses.",
        f"{added['funds_added']} products enter this audit that Experiment 002 could "
        f"not see. {len(usable)} funds cleared every screen and had usable returns; "
        f"{sum(1 for item in outcomes if item.status == 'rejected')} were rejected on "
        "the frozen falsifier, which is a statement about delivered exposure and "
        "cost, not about whether the underlying factor exists.",
        "Every figure is PRETAX. Bid-ask spreads, brokerage, realised distributions "
        "and portfolio turnover are absent entirely.",
    ]


def _frames(
    universe: UnionUniverse,
    fits: Sequence[ExposureFit],
    replications: Mapping[str, ReplicationResult],
    outcomes: Sequence[UnionOutcome],
    coverage: Sequence[Mapping[str, JsonValue]],
) -> dict[str, pd.DataFrame]:
    screen_rows = [
        {
            "ticker": fund.ticker,
            "series_name": fund.series_name,
            "renamed": fund.renamed,
            "passed": fund.passed,
            "failed_criterion": fund.failed_criterion or "",
            "failure_detail": fund.failure_detail,
            "net_assets_max_usd": fund.net_assets_max,
            "net_assets_2019_usd": fund.net_assets_frame,
            "net_assets_2025_usd": fund.net_assets_follow_up,
            "in_frame_census": fund.in_frame_census,
            "in_follow_up_census": fund.in_follow_up_census,
            "net_expense_ratio_percent": _net_expense(fund.facts),
            "stated_mandate": "" if fund.facts is None else fund.facts.stated_mandate,
            "intended_factor": fund.intended_factor or "",
            "intended_sign": fund.intended_sign,
        }
        for fund in universe.funds
    ]
    exposure_rows: list[dict[str, object]] = []
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
    """Screen the union census and write the committed universe, before any return."""
    parameters = _mapping(specification.parameters, where="parameters")
    exp_002_screen_is_unmodified(_exp_002_parameters())
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
        intended_factor_map=intended_factor_map(specification),
    )
    path = write_universe(universe)
    manifests = workspace_root() / "data-manifests"
    for manifest in universe_manifests(cache):
        manifest.write(manifests)

    audited = _exp_002_audited_tickers()
    print(f"universe written to {path}")
    print(
        f"  union frame {universe.frame_quarter} + {universe.follow_up_quarter}: "
        f"{universe.union_series_count} series"
    )
    print(f"  mandate matches: {universe.mandate_matches}")
    print(f"  screened and recorded: {len(universe.funds)}")
    print(f"  passed: {len(universe.passing)}")
    counts: dict[str, int] = {}
    for fund in universe.funds:
        if fund.failed_criterion:
            counts[fund.failed_criterion] = counts.get(fund.failed_criterion, 0) + 1
    for criterion, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"    failed {criterion}: {count}")
    added = [fund for fund in universe.passing if fund.ticker not in audited]
    print(f"  passed and NOT audited by Experiment 002: {len(added)}")
    for fund in universe.passing:
        flag = " " if fund.ticker in audited else "+"
        print(
            f"   {flag}{fund.ticker:<6} {fund.net_assets_max / 1e9:8.2f}bn  "
            f"{(fund.facts.stated_mandate if fund.facts else '?'):<17}"
            f"{fund.intended_factor or '?':<5} {_net_expense(fund.facts):.2f}%  "
            f"{fund.series_name[:44]}"
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

    relationship = diagnostics.get("relationship_to_experiment_002")
    if isinstance(relationship, Mapping):
        block = relationship.get("frame_correction")
        if isinstance(block, Mapping):
            lines.append(
                f"FRAME CORRECTION: {block['funds_with_usable_returns']} funds audited, of "
                f"which {block['funds_audited_by_exp_002']} were in Experiment 002 and "
                f"{block['funds_added']} are new."
            )
            lines.append(
                f"  new because the 2019Q4 census did not carry the series: "
                f"{block['added_absent_from_the_2019q4_census']}"
            )
            lines.append(
                f"  new because a moved criterion had excluded them: "
                f"{block['added_present_in_2019q4_but_excluded_by_another_criterion']}"
            )
            lines.append(f"  their statuses: {block['added_status_counts']}")
            lines.append("")

    universe = diagnostics.get("universe")
    if isinstance(universe, Mapping):
        lines.append(
            f"Universe: union frame {universe['frame_quarters']}, "
            f"{universe['union_series_count']} series, "
            f"{universe['mandate_matches']} mandate matches, "
            f"{universe['passed_screen']} passed, {universe['usable_returns']} usable."
        )
        lines.append("")

    gates = diagnostics.get("validation_gates")
    if isinstance(gates, Mapping):
        lines.append(
            f"Data-path gates PASSED on {gates['comparator']}: correlation "
            f"{float(str(gates['correlation_with_market_total_return'])):.5f}, beta "
            f"{float(str(gates['market_beta'])):.4f}, R2 "
            f"{float(str(gates['r_squared'])):.5f}, worst month {gates['worst_month']} at "
            f"{float(str(gates['worst_month_return_percent'])):.2f}%."
        )
        lines.append("")

    outcomes = diagnostics.get("outcomes")
    if isinstance(outcomes, Sequence):
        replication = diagnostics.get("replication")
        shortfalls: dict[str, float] = {}
        if isinstance(replication, Sequence):
            for item in replication:
                if isinstance(item, Mapping):
                    shortfalls[str(item["ticker"])] = float(
                        str(item["implementation_shortfall_pp"])
                    )
        header = (
            f"{'tkr':<6}{'new':>4}{'mo':>4}{'factor':>7}{'load':>8}"
            f"{'  95% bootstrap':<21}{'MDEld':>7}{'alphaR':>8}{'alphaS':>8}"
            f"{'MDE80':>7}{'short':>7}  status"
        )
        lines.extend([f"Exposure audit, {PRIMARY_SPECIFICATION}, own window", header,
                      "-" * len(header)])
        for item in outcomes:
            if not isinstance(item, Mapping):
                continue
            interval = item["intended_loading_interval"]
            assert isinstance(interval, Sequence)
            ticker = str(item["ticker"])
            lines.append(
                f"{ticker:<6}"
                f"{('' if item['audited_by_exp_002'] else '+'):>4}"
                f"{int(str(item['months'])):>4}"
                f"{item['intended_factor']!s:>7}"
                f"{_show(item['intended_loading'], 8, 3, signed=True)}"
                f"  [{_show(interval[0], 6, 3, signed=True)},"
                f"{_show(interval[1], 6, 3, signed=True)}]"
                f"{_show(item['intended_loading_mde_80pc_power'], 7, 3)}"
                f"{_show(item['alpha_annual_percent'], 8, 2, signed=True)}"
                f"{_show(item['shrunk_alpha_annual_percent'], 8, 2, signed=True)}"
                f"{_show(item['alpha_mde_80pc_power_percent'], 7, 2)}"
                f"{shortfalls.get(ticker, float('nan')):>+7.2f}"
                f"  {item['status']}"
            )
            for clause in item["falsifier_clauses_fired"]:  # type: ignore[union-attr]
                lines.append(f"        {clause}")
        lines.append("")
        lines.append(
            "'+' marks a fund Experiment 002's frame could not audit. MDEld is the "
            "smallest LOADING this window could detect at 80% power, MDE80 the "
            "smallest ALPHA. 'short' is the implementation shortfall against the "
            "in-sample cheap replication, positive meaning the product lost to it."
        )
        lines.append("")

    correction = diagnostics.get("multiple_testing")
    if isinstance(correction, Mapping):
        alpha_block = _as_mapping(correction["alpha"])
        lines.append(
            f"Multiple testing over the whole family ({correction['family_size']} tests = "
            f"{correction['funds']} funds x {len(FACTOR_SPECIFICATIONS)} specifications):"
        )
        lines.append(
            f"  uncorrected p<=0.05: {alpha_block['rejected_uncorrected_at_0_05']}; "
            f"Benjamini-Hochberg at 0.10: {alpha_block.get('rejected_benjamini_hochberg')} "
            f"(OPTIMISTIC); Holm-Bonferroni at 0.10: "
            f"{alpha_block.get('rejected_holm_bonferroni')} (defensible)"
        )
        inflated = correction.get("denominator_hostile_test")
        if isinstance(inflated, Mapping):
            for label in (
                "all_funds_that_passed_the_screen",
                "every_mandate_matching_series_screened",
            ):
                block = _as_mapping(inflated[label])
                lines.append(
                    f"  denominator widened to {block['family_size']} "
                    f"({label.replace('_', ' ')}): BH "
                    f"{block['rejected_benjamini_hochberg']}, Holm "
                    f"{block['rejected_holm_bonferroni']}"
                )
        loading = correction.get("intended_loading")
        if isinstance(loading, Mapping):
            lines.append(
                f"  intended-loading family of {loading['family_size']}: "
                f"{loading['rejected_uncorrected']} uncorrected, "
                f"{loading['rejected_benjamini_hochberg']} under BH"
            )
        lines.append("")

    pedestal = diagnostics.get("model_misfit_pedestal")
    if isinstance(pedestal, Mapping) and pedestal.get("available"):
        specs = _as_mapping(pedestal["by_specification"])
        rendered = ", ".join(
            f"{name} {float(str(_as_mapping(block)['alpha_annual_percent'])):+.2f}"
            for name, block in specs.items()
        )
        lines.append(
            f"MODEL-MISFIT PEDESTAL over the full {pedestal['months']} months. "
            f"{pedestal['comparator']} IS the market portfolio, so its alpha should be "
            f"about minus its {pedestal['net_expense_ratio_percent']}% fee. It is: "
            f"{rendered} pp/yr. Every fund alpha above carries this; read them as "
            "distances from the pedestal, not from zero."
        )
        by_window = diagnostics.get("model_misfit_pedestal_by_window")
        if isinstance(by_window, Mapping) and by_window:
            rendered = ", ".join(
                f"{key} {float(str(value)):+.2f}" for key, value in sorted(by_window.items())
            )
            lines.append(f"  pedestal on each distinct fund window: {rendered}")
        lines.append("")

    window_policy = diagnostics.get("window_policy")
    if isinstance(window_policy, Mapping):
        lines.append(
            f"Windows: {window_policy['shortest_months']} to "
            f"{window_policy['longest_months']} months, median "
            f"{window_policy['median_months']}, minimum accepted "
            f"{window_policy['minimum_monthly_observations']}."
        )
        lines.append("")

    cross = diagnostics.get("cross_source_check")
    if isinstance(cross, Mapping):
        compared = cross["compared"]
        unavailable = cross["unavailable"]
        assert isinstance(compared, Sequence) and isinstance(unavailable, Sequence)
        if compared:
            medians = [
                float(str(item["median_absolute_difference_bp"]))
                for item in compared
                if isinstance(item, Mapping)
            ]
            lines.append(
                f"Cross-source check: {len(compared)} funds compared, median absolute "
                f"monthly disagreement {float(np.median(medians)):.1f} bp; "
                f"{len(unavailable)} unavailable."
            )
        else:
            lines.append(
                f"Cross-source check: NOT AVAILABLE for any fund ({len(unavailable)} "
                "refusals). Form N-PORT Item B.5 is the sole measurement of every "
                "return here, with no independent corroboration of any kind."
            )
        lines.append("")

    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def _show(value: JsonValue, width: int, places: int, *, signed: bool = False) -> str:
    if value is None:
        return "-".rjust(width)
    number = float(str(value))
    if not math.isfinite(number):
        return "-".rjust(width)
    return f"{number:>{width}.{places}f}" if not signed else f"{number:>+{width}.{places}f}"


def main(argv: Sequence[str] | None = None) -> int:
    """Build the universe, or run Experiment 013 through the runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_013_us_products_union_frame",
        description=(
            "Re-audit the US factor shelf on the union of the 2019Q4 and 2025Q4 "
            "N-PORT censuses, writing a ledger entry for the attempt."
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
            "screen the union N-PORT census and write the committed product "
            "universe. MUST be run before the audit: the universe is fixed before "
            "any return is downloaded, and the audit refuses to rebuild it."
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
                "exp_013_us_products_union_frame"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
