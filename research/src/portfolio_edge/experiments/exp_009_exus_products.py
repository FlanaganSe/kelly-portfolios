"""Experiment 009: what an ex-US factor product actually delivers, and at what cost.

The hole this fills
-------------------
Experiment 002 audited the factor-product shelf fund by fund and audited **zero**
ex-US products: its exclusion pattern removes every series whose name carries
``international``, ``intl``, ``global``, ``world``, ``emerging``, ``developed``,
``eafe``, ``acwi`` or ``ex-US``. Experiments 005 and 007 then located essentially
all of the value premium's measurable weight *outside* the United States. So the
repository audited products in the region where the premium is weakest and
audited none where it is strongest.

This module is the complement, not a replacement. Experiment 002's screen, its
frozen specification, its committed universe and its published numbers are
untouched, and
:func:`~portfolio_edge.experiments.exp_009_universe.exp_002_screen_is_unmodified`
asserts its two regexes byte-for-byte before this experiment runs. Every
statistic here is computed by the *same* functions Experiment 002 used --
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.fit_exposure`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.shrink_alpha`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.minimum_detectable_alpha`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.replicating_weights`,
:func:`~portfolio_edge.experiments.exp_002_fund_exposure.fetch_fund_series` -- so
an ex-US number here is comparable to a US number there fund for fund rather than
approximately.

Three things are genuinely different, and each is a finding
-----------------------------------------------------------
**The factor panel is regional.** An EAFE value fund regressed on the US factors
is priced against the wrong market, the wrong size spread and the wrong value
spread. Each fund is estimated on its own region's French file, and then
deliberately re-estimated on the *wrong* region's file and on the US file, so
that the reader can see how much of the loading the panel choice is doing.

**The windows are short and unequal.** Public N-PORT begins in 2019 and the
products that matter launched in 2021. A fund is evaluated on the intersection of
the frozen window with its own filed coverage, and its sample length and minimum
detectable effect are printed beside every estimate. A short window makes a fund
``unresolved``; it never makes it ``rejected``.

**Foreign withholding is inside every return and cannot be taken out.** A
US-domiciled fund's net asset value is struck after foreign dividend tax is
withheld, so its return is net of a cost the US audit never had to think about.
That cost cannot be measured against another fund -- every comparator here pays
it too -- but it can be bounded by comparing the model-misfit pedestal of a cheap
ex-US market fund against a French ex-US research portfolio with the pedestal of
a cheap US market fund against the US research portfolio, over the same months.
The difference is reported as an UPPER BOUND, because it also contains every
difference between an investable FTSE index and a French research portfolio.

Run it::

    uv run python -m portfolio_edge.experiments.exp_009_exus_products --build-universe
    uv run python -m portfolio_edge.experiments.exp_009_exus_products --view-results
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import yaml
from numpy.typing import NDArray

from portfolio_edge.data import french, nport
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
    minimum_detectable_alpha,
    replicating_weights,
    secondary_monthly_returns,
)
from portfolio_edge.experiments.exp_002_universe import ProductFacts, resolve_ticker, workspace_root
from portfolio_edge.experiments.exp_009_universe import (
    GRADED_REGIONS,
    ExtraFacts,
    ScreenedExUsFund,
    ScreeningPatterns,
    attrition,
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
    plain_json,
)
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.inference.multiple_testing import benjamini_hochberg, holm_bonferroni

__all__ = [
    "ENTRY_POINT",
    "PANEL_DATASETS",
    "ExUsProductError",
    "FundWindow",
    "RegionalFits",
    "ReplicationResult",
    "build_registry",
    "contiguous_window",
    "default_specification_path",
    "load_regional_panel",
    "main",
    "minimum_detectable_loading",
    "run",
    "screening_patterns_from_specification",
    "shelf_depth",
]

ENTRY_POINT: Final = "exp_009_exus_factor_products"

FloatArray = NDArray[np.float64]

#: Which French files price which region. The momentum column is ``WML`` in both
#: international files and ``Mom`` in the US file; both are the same 30/70
#: prior-return spread, and both are mapped to ``UMD`` so that the three model
#: specifications are byte-identical to Experiment 002's.
PANEL_DATASETS: Final[dict[str, tuple[str, str, str]]] = {
    "developed_ex_us": (
        "french_developed_ex_us_ff5",
        "french_developed_ex_us_momentum",
        "WML",
    ),
    "emerging": ("french_emerging_ff5", "french_emerging_momentum", "WML"),
    "us": ("french_us_ff5", "french_us_momentum", "Mom"),
}

#: The other graded region, for the wrong-panel hostile test.
_OPPOSITE_REGION: Final[dict[str, str]] = {
    "developed_ex_us": "emerging",
    "emerging": "developed_ex_us",
}


class ExUsProductError(RuntimeError):
    """The audit could not be attempted against the declared inputs."""


# --------------------------------------------------------------------------- #
# Typed access to the frozen specification
# --------------------------------------------------------------------------- #


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ExUsProductError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _sequence(value: JsonValue, *, where: str) -> Sequence[JsonValue]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ExUsProductError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _at(data: Mapping[str, JsonValue], key: str, *, where: str) -> JsonValue:
    if key not in data:
        raise ExUsProductError(f"missing {where}.{key} in the frozen specification")
    return data[key]


def _text(data: Mapping[str, JsonValue], key: str, *, where: str) -> str:
    value = _at(data, key, where=where)
    if not isinstance(value, str) or not value.strip():
        raise ExUsProductError(f"{where}.{key} must be a non-empty string, got {value!r}")
    return value.strip()


def _number(data: Mapping[str, JsonValue], key: str, *, where: str) -> float:
    value = _at(data, key, where=where)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ExUsProductError(f"{where}.{key} must be a number, got {value!r}")
    return float(value)


def _strings(data: Mapping[str, JsonValue], key: str, *, where: str) -> tuple[str, ...]:
    return tuple(str(item) for item in _sequence(_at(data, key, where=where), where=where))


def screening_patterns_from_specification(specification: Specification) -> ScreeningPatterns:
    """Rebuild the frozen screen from the specification, never from defaults."""
    parameters = _mapping(specification.parameters, where="parameters")
    block = _mapping(
        _at(parameters, "screening_patterns", where="parameters"), where="screening_patterns"
    )
    pairs: list[tuple[str, str]] = []
    for item in _sequence(_at(block, "mandate_patterns", where="screening_patterns"), where="p"):
        entry = _sequence(item, where="mandate_patterns entry")
        if len(entry) != 2:
            raise ExUsProductError(f"a mandate pattern must be a [name, regex] pair, got {entry!r}")
        pairs.append((str(entry[0]), str(entry[1])))
    return ScreeningPatterns(
        region_regex=_text(block, "region_regex", where="screening_patterns"),
        factor_regex=_text(block, "factor_regex", where="screening_patterns"),
        exclusion_regex=_text(block, "exclusion_regex", where="screening_patterns"),
        us_token_regex=_text(block, "us_token_regex", where="screening_patterns"),
        global_token_regex=_text(block, "global_token_regex", where="screening_patterns"),
        ex_us_token_regex=_text(block, "ex_us_token_regex", where="screening_patterns"),
        emerging_regex=_text(block, "emerging_regex", where="screening_patterns"),
        world_ex_us_regex=_text(block, "world_ex_us_regex", where="screening_patterns"),
        mandate_patterns=tuple(pairs),
    )


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
# Statistics this experiment adds
# --------------------------------------------------------------------------- #


def minimum_detectable_loading(
    standard_error: float, *, power: float = 0.80, significance: float = 0.05
) -> float:
    """The smallest true loading a two-sided test of this precision would find.

    Identical algebra to
    :func:`~portfolio_edge.experiments.exp_002_fund_exposure.minimum_detectable_alpha`
    -- ``(z_{1-a/2} + z_power) * SE`` -- kept as its own name because a loading is
    dimensionless and an alpha is percentage points per year, and a reader who
    sees one function used for both will eventually read one as the other.
    """
    return minimum_detectable_alpha(standard_error, power=power, significance=significance)


def contiguous_window(periods: Sequence[str]) -> tuple[str, ...]:
    """The longest run of consecutive months in ``periods``, latest run winning ties.

    A regression with Newey-West standard errors treats its rows as a time
    series. A fund with a hole in its filed history has two time series, not one,
    and stitching them would put a lag structure across a gap that does not
    exist. Ties go to the LATER run because a fund's recent history is the one
    that describes the product as it exists now.
    """
    if not periods:
        return ()
    ordered = sorted(set(periods))
    runs: list[list[str]] = [[ordered[0]]]
    for previous, current in pairwise(ordered):
        if month_index(current) == month_index(previous) + 1:
            runs[-1].append(current)
        else:
            runs.append([current])
    best = runs[0]
    for run in runs[1:]:
        if len(run) >= len(best):
            best = run
    return tuple(best)


def shelf_depth(
    funds: Sequence[ScreenedExUsFund],
) -> dict[str, JsonValue]:
    """How many distinct products deliver each exposure in each region.

    An exposure available from exactly one product at any price is a
    concentration risk and not a choice: the shareholder is exposed to that
    sponsor's index licence, its fee decisions and its continued existence, with
    no substitute. MTUM is the whole US momentum shelf in Experiment 002; this
    function is what makes the same statement checkable ex-US.
    """
    counts: dict[str, dict[str, list[str]]] = {}
    for fund in funds:
        if not fund.passed or fund.derived_region is None or fund.derived_mandate is None:
            continue
        counts.setdefault(fund.derived_region, {}).setdefault(fund.derived_mandate, []).append(
            fund.ticker
        )
    out: dict[str, JsonValue] = {}
    for region in sorted(counts):
        block: dict[str, JsonValue] = {}
        for mandate in sorted(counts[region]):
            tickers = sorted(counts[region][mandate])
            block[mandate] = {"products": len(tickers), "tickers": tickers}
        out[region] = block
    return out


# --------------------------------------------------------------------------- #
# Regional factor panels
# --------------------------------------------------------------------------- #


def load_regional_panel(
    cache: RawCache, *, region: str, start: str, end: str
) -> FactorPanel:
    """FF5 plus momentum for one region, joined on MONTH LABELS.

    The two files are joined on labels and never on row position. The
    developed-ex-US five-factor file begins 1990-07 and its momentum file
    1990-11; a positional join would shift momentum by four months against every
    other factor and leave every resulting number looking entirely plausible.

    Unlike Experiment 002's US loader this does NOT require the window to be
    covered completely, because it is called for regions whose files may end a
    month or two before the window does. The months actually available are
    returned and every consumer intersects against them, so a missing tail
    shortens a sample visibly instead of aborting the run.
    """
    if region not in PANEL_DATASETS:
        raise ExUsProductError(f"no factor panel is registered for region {region!r}")
    ff5_id, momentum_id, momentum_column = PANEL_DATASETS[region]
    root = workspace_root()

    frames: dict[str, pd.DataFrame] = {}
    provenance: dict[str, JsonValue] = {}
    for dataset_id in (ff5_id, momentum_id):
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

    ff5 = frames[ff5_id]
    momentum = frames[momentum_id]
    momentum_labels = {str(label) for label in momentum.index}
    shared = [
        str(label)
        for label in ff5.index
        if str(label) in momentum_labels
        and month_index(start) <= month_index(str(label)) <= month_index(end)
    ]
    if not shared:
        raise ExUsProductError(
            f"the {region} French files jointly cover none of {start}..{end}"
        )

    factors: dict[str, FloatArray] = {
        name: np.asarray(ff5.loc[shared, name].to_numpy(), dtype=np.float64)
        for name in ("Mkt-RF", "SMB", "HML", "RMW", "CMA")
    }
    factors["UMD"] = np.asarray(
        momentum.loc[shared, momentum_column].to_numpy(), dtype=np.float64
    )
    bill = np.asarray(ff5.loc[shared, "RF"].to_numpy(), dtype=np.float64)
    for name, series in (*factors.items(), ("RF", bill)):
        if not np.all(np.isfinite(series)):
            raise ExUsProductError(f"{region} {name} has a missing value inside {start}..{end}")
        # The international files carry a -99.99 sentinel for months a factor
        # could not be built. Read as a return it is a 9,999% monthly loss, so it
        # is refused rather than silently regressed on.
        if float(np.min(series)) < -0.9:
            raise ExUsProductError(
                f"{region} {name} contains a value below -90% inside {start}..{end}, which "
                "is the -99.99 missing-data sentinel rather than a return"
            )

    return FactorPanel(
        periods=tuple(shared),
        factors=factors,
        risk_free=bill,
        provenance=provenance,
    )


# --------------------------------------------------------------------------- #
# Per-fund inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class FundWindow:
    """The months of one fund that this experiment may actually use."""

    ticker: str
    region: str
    periods: tuple[str, ...]
    filed_periods: tuple[str, ...]
    dropped_before_gap: tuple[str, ...]
    filings: int
    amendments: int
    filings_held_out: int
    warnings: tuple[str, ...]

    @property
    def months(self) -> int:
        return len(self.periods)

    @property
    def first(self) -> str:
        return self.periods[0] if self.periods else ""

    @property
    def last(self) -> str:
        return self.periods[-1] if self.periods else ""

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "region": self.region,
            "months_usable": self.months,
            "first_month": self.first,
            "last_month": self.last,
            "months_filed_in_window": len(self.filed_periods),
            "months_dropped_before_an_internal_gap": list(self.dropped_before_gap),
            "filings": self.filings,
            "amendments": self.amendments,
            "filings_held_out_after_window": self.filings_held_out,
            "filing_warnings": list(self.warnings),
        }


def _first_whole_month(inception: str) -> str:
    """The first CALENDAR month the fund was open for all of.

    A fund that commenced operations on the 24th files an Item B.5 return for
    that month covering four trading days. Regressed against a whole month of
    factor returns it is not a small observation, it is a differently-scaled one:
    its beta is attenuated by roughly the fraction of the month the fund did not
    exist. Every ex-US product that matters here launched mid-month -- AVDV on
    the 24th, AVIV and AVES on the 28th, DISV and DFIS on the 23rd -- so dropping
    the stub is worth one observation each and removes a bias that all of them
    share in the same direction.
    """
    if inception[8:10] == "01":
        return inception[:7]
    return period_from_index(month_index(inception[:7]) + 1)


def _window_for(
    series: FundSeries,
    panel: FactorPanel,
    *,
    region: str,
    start: str,
    end: str,
    inception: str | None = None,
) -> FundWindow:
    """The months of one fund this experiment may use, after three cuts.

    The frozen window, the region's factor panel, and -- the one that matters
    here -- the fund's OWN inception. An SEC fund series survives a conversion
    from a mutual fund into an ETF, so DFIV's series carries filings from the
    Tax-Managed DFA International Value Portfolio for years before the ETF
    existed. Those months are a different product at a different fee, and using
    them would audit a fund nobody could have bought. The cut is applied to every
    fund, not only the converted ones, so no month can precede its product.
    """
    floor = start if inception is None else max(start, _first_whole_month(inception))
    available = {
        period
        for period in series.periods
        if month_index(floor) <= month_index(period) <= month_index(end)
    }
    usable = sorted(available & set(panel.periods))
    contiguous = contiguous_window(usable)
    dropped = tuple(period for period in usable if period not in set(contiguous))
    return FundWindow(
        ticker=series.ticker,
        region=region,
        periods=contiguous,
        filed_periods=tuple(sorted(available)),
        dropped_before_gap=dropped,
        filings=series.filing_count,
        amendments=series.amendment_count,
        filings_held_out=series.filings_held_out,
        warnings=series.warnings,
    )


def _rows_for(panel: FactorPanel, periods: Sequence[str]) -> NDArray[np.intp]:
    index = {period: position for position, period in enumerate(panel.periods)}
    return np.asarray([index[period] for period in periods], dtype=np.intp)


def _total(series: FundSeries, periods: Sequence[str]) -> FloatArray:
    available = dict(zip(series.periods, series.returns, strict=True))
    return np.asarray([available[period] for period in periods], dtype=np.float64)


def _excess(series: FundSeries, panel: FactorPanel, periods: Sequence[str]) -> FloatArray:
    rows = _rows_for(panel, periods)
    return _total(series, periods) - panel.risk_free[rows]


def _covered(series: FundSeries, periods: Sequence[str]) -> bool:
    return bool(periods) and set(periods) <= set(series.periods)


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplicationResult:
    """What a long-only combination of cheap broad ex-US funds does to a product."""

    ticker: str
    basis: tuple[str, ...]
    weights: tuple[float, ...]
    months: int
    tracking_difference_vs_combination: float
    tracking_error_vs_combination: float
    tracking_difference_vs_regional_market: float
    tracking_error_vs_regional_market: float
    tracking_difference_vs_french_market: float
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
            "tracking_difference_vs_regional_market_pp": (
                self.tracking_difference_vs_regional_market
            ),
            "tracking_error_vs_regional_market_pp": self.tracking_error_vs_regional_market,
            "tracking_difference_vs_french_market_pp": self.tracking_difference_vs_french_market,
            "fee_premium_over_basis_pp": self.fee_premium_over_basis,
            "implementation_shortfall_pp": self.implementation_shortfall,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionalFits:
    """One fund's exposure fits: own panel, wrong panel, and the US panel."""

    own_panel: dict[str, ExposureFit]
    """Keyed by model specification name."""
    wrong_panel: ExposureFit | None
    us_panel: ExposureFit | None


def _finite(value: float) -> float | None:
    """``None`` for a quantity that does not exist, never ``NaN``.

    Unequal windows are the normal case here, so a fund can genuinely have no
    first-half loading and no wrong-panel loading. JSON has no NaN, and writing
    one would either abort the artifact or -- worse, had it been allowed through
    as ``NaN`` -- put a token in a results file that most readers parse as a
    number. A missing quantity is written as null and reads as missing.
    """
    return value if math.isfinite(value) else None


@dataclass(slots=True, kw_only=True)
class ExUsOutcome:
    """The per-fund verdict, with every falsifier clause that fired."""

    ticker: str
    series_name: str
    region: str
    mandate: str
    intended_factor: str
    intended_sign: int
    months: int
    first_month: str
    last_month: str
    status: str
    clauses_fired: list[str] = field(default_factory=list)
    intended_loading: float = float("nan")
    intended_loading_se: float = float("nan")
    intended_loading_mde: float = float("nan")
    intended_loading_interval: tuple[float, float] = (float("nan"), float("nan"))
    intended_loading_first_half: float = float("nan")
    intended_loading_second_half: float = float("nan")
    intended_loading_wrong_panel: float = float("nan")
    intended_loading_us_panel: float = float("nan")
    alpha_annual_percent: float = float("nan")
    shrunk_alpha_annual_percent: float = float("nan")
    alpha_mde_percent: float = float("nan")
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "ticker": self.ticker,
            "series_name": self.series_name,
            "region": self.region,
            "mandate": self.mandate,
            "intended_factor": self.intended_factor,
            "intended_sign": self.intended_sign,
            "months": self.months,
            "first_month": self.first_month,
            "last_month": self.last_month,
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
            "intended_loading_wrong_regional_panel": _finite(self.intended_loading_wrong_panel),
            "intended_loading_us_panel": _finite(self.intended_loading_us_panel),
            "alpha_annual_percent": _finite(self.alpha_annual_percent),
            "shrunk_alpha_annual_percent": _finite(self.shrunk_alpha_annual_percent),
            "alpha_mde_80pc_power_percent": _finite(self.alpha_mde_percent),
            "notes": list(self.notes),
        }


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_009_exus_factor_products.yaml"


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
    """Download Item B.5 histories for the funds that PASSED the screen, and the
    comparators. A fund that failed the screen is never fetched, so no screen
    decision can be revised after seeing performance."""
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


def _validate_regional_path(
    *,
    ticker: str,
    region: str,
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    minimum_correlation: float,
    beta_tolerance: float,
    minimum_r_squared: float,
) -> dict[str, JsonValue]:
    """Gates that must pass before any fund result in this region is believable.

    The thresholds are LOOSER than Experiment 002's, and the reason is stated in
    the specification rather than buried: no investable ex-US fund is the French
    research portfolio. FTSE, MSCI and Ken French classify Korea, Poland and
    Canada differently, the investable indices exclude the smallest deciles, and
    the fund's return is net of withholding while the research portfolio's
    treatment of it is undocumented. A gate tight enough for a US total-market
    fund would fail here for reasons about index definitions, not about the
    data path.
    """
    record = series.get(ticker)
    if record is None:
        raise ExUsProductError(
            f"the {region} comparator {ticker} has no usable history, so nothing in "
            "that region can be benchmarked and no gate can be checked"
        )
    periods = tuple(period for period in record.periods if period in set(panel.periods))
    if len(periods) < 24:
        raise ExUsProductError(
            f"{ticker} has only {len(periods)} months overlapping the {region} panel"
        )
    rows = _rows_for(panel, periods)
    fund = _total(record, periods)
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
    if correlation < minimum_correlation:
        findings.append(
            f"{ticker} correlates {correlation:.4f} with the {region} market factor, "
            f"below {minimum_correlation:.2f}"
        )
    if abs(beta - 1.0) > beta_tolerance:
        findings.append(
            f"{ticker} has market beta {beta:.4f}, more than {beta_tolerance:.2f} from 1.00"
        )
    if r_squared < minimum_r_squared:
        findings.append(
            f"{ticker} regression R-squared {r_squared:.4f} is below {minimum_r_squared:.2f}"
        )
    if worst_month != "2020-03":
        findings.append(
            f"{ticker}'s worst month is {worst_month}, not 2020-03; the COVID drawdown "
            "is the sharpest month in this window for any equity fund, so this points "
            "at a month-offset error"
        )
    if findings:
        raise ExUsProductError(
            "the data path failed its validation gates before any fund result was "
            "computed: " + "; ".join(findings)
        )
    return {
        "comparator": ticker,
        "region": region,
        "months": len(periods),
        "correlation_with_market_total_return": correlation,
        "market_beta": beta,
        "r_squared": r_squared,
        "worst_month": worst_month,
        "worst_month_return_percent": float(np.min(fund)) * 100.0,
        "thresholds": {
            "minimum_correlation": minimum_correlation,
            "beta_tolerance": beta_tolerance,
            "minimum_r_squared": minimum_r_squared,
        },
    }


def _era_windows(specification: Specification) -> dict[str, tuple[str, str]]:
    return {era.name: (era.start, era.end) for era in specification.sample_policy.eras}


def _slice_era(periods: Sequence[str], era: tuple[str, str]) -> tuple[str, ...]:
    first, last = month_index(era[0]), month_index(era[1])
    return tuple(period for period in periods if first <= month_index(period) <= last)


def _net_expense(facts: ProductFacts | None) -> float:
    if facts is None or facts.net_expense_ratio_percent is None:
        return 0.0
    return facts.net_expense_ratio_percent


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
    fund: ScreenedExUsFund,
    window: FundWindow,
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    basis: Sequence[str],
    comparator: str,
    facts: Mapping[str, ProductFacts],
) -> ReplicationResult | None:
    """Fit the cheap long-only ex-US combination that best tracks this product.

    Every basis member must cover the fund's whole window, otherwise the weights
    would be fitted on a different sample from the one they are scored on. A fund
    is never part of the basis that replicates it: leaving it in would hand it a
    weight of one and a tracking difference of exactly zero.
    """
    usable_basis = [
        ticker
        for ticker in basis
        if ticker != fund.ticker and ticker in series and _covered(series[ticker], window.periods)
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
    rows = _rows_for(panel, window.periods)
    french_market = panel.factors["Mkt-RF"][rows] + panel.risk_free[rows]

    difference = target - combination
    against_market = target - market
    against_french = target - french_market
    basis_fee = sum(
        float(weights[i]) * _net_expense(facts.get(ticker))
        for i, ticker in enumerate(usable_basis)
    )
    fund_fee = _net_expense(facts.get(fund.ticker, fund.facts))
    tracking_difference = float(np.mean(difference)) * MONTHS_PER_YEAR * 100.0
    fee_premium = fund_fee - basis_fee
    return ReplicationResult(
        ticker=fund.ticker,
        basis=tuple(usable_basis),
        weights=tuple(float(value) for value in weights),
        months=len(window.periods),
        tracking_difference_vs_combination=tracking_difference,
        tracking_error_vs_combination=float(np.std(difference, ddof=1))
        * math.sqrt(MONTHS_PER_YEAR)
        * 100.0,
        tracking_difference_vs_regional_market=float(np.mean(against_market))
        * MONTHS_PER_YEAR
        * 100.0,
        tracking_error_vs_regional_market=float(np.std(against_market, ddof=1))
        * math.sqrt(MONTHS_PER_YEAR)
        * 100.0,
        tracking_difference_vs_french_market=float(np.mean(against_french))
        * MONTHS_PER_YEAR
        * 100.0,
        fee_premium_over_basis=fee_premium,
        # POSITIVE means the product lost MORE to its cheap replication than its
        # extra fee explains: implementation cost paid on top of the fee.
        implementation_shortfall=-tracking_difference - fee_premium,
    )


def _pedestal(
    *,
    ticker: str,
    region: str,
    series: Mapping[str, FundSeries],
    panel: FactorPanel,
    periods: Sequence[str],
    hac_lags: int,
    dispersion: float,
    power: float,
    facts: Mapping[str, ProductFacts],
) -> dict[str, JsonValue]:
    """The alpha the model gives a fund that is, by construction, its own market.

    A cap-weighted market fund holds the market portfolio, so under a correctly
    specified model its alpha should be about minus its expense ratio. Whatever
    it is instead is model misfit carried by EVERY fund priced by the same
    factors over the same months, and each fund's alpha is meaningful only as a
    distance from it.
    """
    record = series.get(ticker)
    usable = tuple(period for period in periods if record is not None and period in record.periods)
    if record is None or len(usable) < 24:
        return {"available": False, "ticker": ticker, "region": region}
    fits = _fit_all_specifications(
        ticker=ticker,
        era="pedestal",
        series=record,
        panel=panel,
        periods=usable,
        hac_lags=hac_lags,
        dispersion=dispersion,
        power=power,
    )
    primary = fits[PRIMARY_SPECIFICATION]
    rows = _rows_for(panel, usable)
    french_market = panel.factors["Mkt-RF"][rows] + panel.risk_free[rows]
    gap = float(np.mean(_total(record, usable) - french_market)) * MONTHS_PER_YEAR * 100.0
    return {
        "available": True,
        "ticker": ticker,
        "region": region,
        "months": len(usable),
        "first_month": usable[0],
        "last_month": usable[-1],
        "net_expense_ratio_percent": _net_expense(facts.get(ticker)),
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
        "simple_gap_vs_french_market_pp": gap,
        "interpretation": (
            "A cap-weighted market fund IS its region's market portfolio, so its "
            "alpha under a correctly specified model should be about minus its "
            "expense ratio. The distance from that is model misfit shared by every "
            "fund in this region. Read each fund's alpha as a distance from this "
            "pedestal, never from zero."
        ),
    }


def _structural_drag(
    ex_us: Mapping[str, JsonValue], us: Mapping[str, JsonValue]
) -> dict[str, JsonValue]:
    """The ex-US cost the US audit could not see, bounded rather than measured.

    A US-domiciled fund holding foreign shares has foreign dividend tax withheld
    before its net asset value is struck, so its filed total return is net of a
    charge no US-equity fund pays. That charge cannot be separated from the
    return, and Form N-PORT does not carry foreign tax paid. What CAN be done is
    to compare like with like: the gap between a cheap market fund and its own
    region's research portfolio, ex-US against US, over the same months. The
    difference is an UPPER BOUND on the withholding drag, because it also
    contains every difference between an investable index and a research
    portfolio -- country classification, the excluded small deciles, and the
    undocumented dividend treatment of the French international files.
    """
    if not (ex_us.get("available") and us.get("available")):
        return {"available": False, "reason": "a pedestal was unavailable"}
    ex_us_gap = float(str(ex_us["simple_gap_vs_french_market_pp"]))
    us_gap = float(str(us["simple_gap_vs_french_market_pp"]))
    ex_us_fee = float(str(ex_us["net_expense_ratio_percent"]))
    us_fee = float(str(us["net_expense_ratio_percent"]))
    difference = (ex_us_gap + ex_us_fee) - (us_gap + us_fee)
    return {
        "available": True,
        "ex_us_comparator": ex_us["ticker"],
        "us_comparator": us["ticker"],
        "months": min(int(str(ex_us["months"])), int(str(us["months"]))),
        "ex_us_gap_vs_own_french_market_pp": ex_us_gap,
        "us_gap_vs_own_french_market_pp": us_gap,
        "ex_us_fee_percent": ex_us_fee,
        "us_fee_percent": us_fee,
        "ex_us_gap_beyond_fee_pp": ex_us_gap + ex_us_fee,
        "us_gap_beyond_fee_pp": us_gap + us_fee,
        "difference_of_gaps_beyond_fee_pp": difference,
        "sign_convention": (
            "POSITIVE means the fund BEAT its own region's French market portfolio. "
            "A fund that tracked perfectly would show a gap of about minus its fee, "
            "so the 'beyond fee' figures are what is left after the fee is put back."
        ),
        "what_this_can_and_cannot_conclude": (
            "A NEGATIVE difference would be an upper bound on the ex-US structural "
            "drag -- foreign dividend withholding plus every difference between an "
            "investable index and a French research portfolio. A POSITIVE "
            "difference, which is what this window shows, means the "
            "index-construction differences swamp whatever withholding costs and "
            "the method cannot bound the tax at all. It must not be reported as "
            "evidence that withholding is small: withholding is certainly being "
            "paid, is inside every ex-US return in this experiment, and is simply "
            "not separable from the benchmark mismatch by this construction."
        ),
        "why_no_other_method_is_available_here": (
            "Form N-PORT carries no foreign-tax-paid figure. It is reported to "
            "shareholders on Form 1099-DIV box 7 and in the annual report on Form "
            "N-CSR as unstructured HTML. A US taxable shareholder may recover part "
            "of the withholding through the foreign tax credit and a "
            "retirement-account shareholder may not; neither case is modelled."
        ),
    }


def _verdict(
    *,
    fund: ScreenedExUsFund,
    window: FundWindow,
    fits: RegionalFits,
    halves: Mapping[str, ExposureFit],
    interval: Mapping[str, list[float]],
    replication: ReplicationResult | None,
    minimum_loading: float,
    materiality: float,
) -> ExUsOutcome:
    """Apply the frozen falsifier clause by clause and record which ones fired."""
    factor = fund.intended_factor or ""
    sign = fund.intended_sign or 1
    outcome = ExUsOutcome(
        ticker=fund.ticker,
        series_name=fund.series_name_follow_up or fund.series_name_frame,
        region=fund.derived_region or "",
        mandate=fund.derived_mandate or "",
        intended_factor=factor,
        intended_sign=sign,
        months=window.months,
        first_month=window.first,
        last_month=window.last,
        status="unresolved",
    )
    primary = fits.own_panel.get(PRIMARY_SPECIFICATION)
    if primary is None or not factor:
        outcome.notes.append("no primary fit; nothing to decide")
        return outcome

    outcome.intended_loading = primary.loadings[factor] * sign
    outcome.intended_loading_se = primary.standard_errors[factor]
    outcome.intended_loading_mde = minimum_detectable_loading(primary.standard_errors[factor])
    outcome.alpha_annual_percent = primary.alpha_annual_percent
    outcome.shrunk_alpha_annual_percent = primary.shrunk_alpha_annual_percent
    outcome.alpha_mde_percent = primary.minimum_detectable_alpha_percent
    if fits.wrong_panel is not None:
        outcome.intended_loading_wrong_panel = fits.wrong_panel.loadings[factor] * sign
    if fits.us_panel is not None:
        outcome.intended_loading_us_panel = fits.us_panel.loadings[factor] * sign

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
                f"(c) lost {-replication.tracking_difference_vs_combination:+.2f} pp/yr to "
                f"its cheap ex-US replication against a fee premium of only "
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
    """Audit every screened ex-US product's exposure, cost and replicability."""
    parameters = _mapping(specification.parameters, where="parameters")
    exp_002_screen_is_unmodified(_exp_002_parameters())

    universe_block = _mapping(specification.universe, where="universe")
    comparators = _mapping(_at(universe_block, "comparators", where="universe"), where="universe")
    developed_comparator = _text(
        _mapping(
            _at(comparators, "developed_ex_us_market", where="comparators"), where="comparator"
        ),
        "ticker",
        where="comparators.developed_ex_us_market",
    )
    emerging_comparator = _text(
        _mapping(_at(comparators, "emerging_market", where="comparators"), where="comparator"),
        "ticker",
        where="comparators.emerging_market",
    )
    us_comparator = _text(
        _mapping(_at(comparators, "us_pedestal", where="comparators"), where="comparator"),
        "ticker",
        where="comparators.us_pedestal",
    )
    basis = _strings(
        _mapping(
            _at(comparators, "synthetic_combination", where="comparators"), where="combination"
        ),
        "basis",
        where="comparators.synthetic_combination",
    )
    region_comparator = {
        "developed_ex_us": developed_comparator,
        "emerging": emerging_comparator,
    }

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
    cache = RawCache()

    eras = _era_windows(specification)
    window_start, window_end = eras["common_period"]

    panels = {
        region: load_regional_panel(cache, region=region, start=window_start, end=window_end)
        for region in (*GRADED_REGIONS, "us")
    }

    wanted: dict[str, tuple[str, str]] = {
        fund.ticker: (fund.series_id, fund.class_id) for fund in universe.passing
    }
    for ticker in (developed_comparator, emerging_comparator, us_comparator, *basis):
        if ticker not in wanted:
            series_id, class_id, _name = resolve_ticker(cache, ticker)
            wanted[ticker] = (series_id, class_id)
    series, fetch_failures = _fetch_all(
        cache, tickers=wanted, start=window_start, end=window_end
    )

    gates = [
        _validate_regional_path(
            ticker=developed_comparator,
            region="developed_ex_us",
            series=series,
            panel=panels["developed_ex_us"],
            minimum_correlation=0.97,
            beta_tolerance=0.10,
            minimum_r_squared=0.93,
        ),
        _validate_regional_path(
            ticker=emerging_comparator,
            region="emerging",
            series=series,
            panel=panels["emerging"],
            minimum_correlation=0.95,
            beta_tolerance=0.10,
            minimum_r_squared=0.93,
        ),
        _validate_regional_path(
            ticker=us_comparator,
            region="us",
            series=series,
            panel=panels["us"],
            minimum_correlation=0.99,
            beta_tolerance=0.05,
            minimum_r_squared=0.98,
        ),
    ]

    # --- per-fund windows and coverage
    windows: dict[str, FundWindow] = {}
    coverage: list[dict[str, JsonValue]] = []
    usable: list[ScreenedExUsFund] = []
    for fund in universe.passing:
        record = series.get(fund.ticker)
        region = fund.derived_region or ""
        if record is None or region not in panels:
            coverage.append(
                {
                    "ticker": fund.ticker,
                    "usable": False,
                    "reason": "no filings retrieved" if record is None else "no panel",
                }
            )
            continue
        inception = None if fund.facts is None else fund.facts.inception_date
        window = _window_for(
            record,
            panels[region],
            region=region,
            start=window_start,
            end=window_end,
            inception=inception,
        )
        windows[fund.ticker] = window
        # A fund whose N-PORT history begins materially before its ETF inception
        # was a MUTUAL FUND first: the SEC series survived the conversion and its
        # early months are a different product with a different fee. Those months
        # are cut by ``_window_for``; this records that the cut happened and how
        # much it removed, because a silent truncation is indistinguishable from a
        # fund that simply had no history.
        filed_first = min(record.periods) if record.periods else ""
        pre_history = (
            inception is not None
            and filed_first != ""
            and month_index(filed_first) < month_index(inception[:7]) - 1
        )
        record_row: dict[str, JsonValue] = {
            "ticker": fund.ticker,
            "region": region,
            "usable": window.months >= minimum_months,
            "months_usable": window.months,
            "first_month": window.first,
            "last_month": window.last,
            "inception_date": inception,
            "first_month_filed_in_window": filed_first,
            "nport_history_predates_inception": pre_history,
            "months_cut_as_pre_inception": (
                month_index(inception[:7]) - month_index(filed_first)
                if pre_history and inception is not None
                else 0
            ),
            "converted_from_mutual_fund": (
                extras[fund.ticker].converted_from_mutual_fund
                if fund.ticker in extras
                else None
            ),
            "months_dropped_before_an_internal_gap": list(window.dropped_before_gap),
            "filings": window.filings,
            "amendments": window.amendments,
            "reason": (
                ""
                if window.months >= minimum_months
                else f"{window.months} usable months is below the {minimum_months} minimum, "
                "which is a statement about the fund's age and not about the fund"
            ),
        }
        coverage.append(record_row)
        if window.months >= minimum_months:
            usable.append(fund)

    # --- exposure fits: own panel, wrong panel, US panel
    all_fits: dict[str, RegionalFits] = {}
    half_fits: dict[tuple[str, str], ExposureFit] = {}
    flat_fits: list[ExposureFit] = []
    for fund in usable:
        region = fund.derived_region or ""
        window = windows[fund.ticker]
        record = series[fund.ticker]
        own = _fit_all_specifications(
            ticker=fund.ticker,
            era="common_period",
            series=record,
            panel=panels[region],
            periods=window.periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        flat_fits.extend(own.values())

        wrong_region = _OPPOSITE_REGION[region]
        wrong = _fit_on(
            record,
            panels[wrong_region],
            window.periods,
            ticker=fund.ticker,
            era=f"wrong_panel_{wrong_region}",
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        on_us = _fit_on(
            record,
            panels["us"],
            window.periods,
            ticker=fund.ticker,
            era="us_panel",
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
        )
        all_fits[fund.ticker] = RegionalFits(own_panel=own, wrong_panel=wrong, us_panel=on_us)

        for era_name in ("first_half", "second_half", "value_reversal", "us_comparable_period"):
            era_periods = _slice_era(window.periods, eras[era_name])
            if len(era_periods) <= len(FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]) + 6:
                continue
            fit = _fit_on(
                record,
                panels[region],
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
            panel=panels[fund.derived_region or ""],
            periods=windows[fund.ticker].periods,
            factor=fund.intended_factor,
            rng=context.rng,
            resamples=specification.inference.resamples,
            confidence=specification.inference.confidence_level,
        )

    # --- replication against cheap broad ex-US funds
    replications: dict[str, ReplicationResult] = {}
    for fund in usable:
        region = fund.derived_region or ""
        result = _replicate(
            fund=fund,
            window=windows[fund.ticker],
            series=series,
            panel=panels[region],
            basis=basis,
            comparator=region_comparator[region],
            facts=facts,
        )
        if result is not None:
            replications[fund.ticker] = result

    outcomes = [
        _verdict(
            fund=fund,
            window=windows[fund.ticker],
            fits=all_fits[fund.ticker],
            halves={
                era: fit
                for (ticker, era), fit in half_fits.items()
                if ticker == fund.ticker
            },
            interval=intervals.get(fund.ticker, {}),
            replication=replications.get(fund.ticker),
            minimum_loading=minimum_loading,
            materiality=materiality,
        )
        for fund in usable
    ]

    # --- multiple testing over the whole family
    alpha_p = np.asarray([fit.alpha_p for fit in flat_fits], dtype=np.float64)
    bh = benjamini_hochberg(alpha_p, alpha=0.10) if alpha_p.size else None
    holm = holm_bonferroni(alpha_p, alpha=0.10) if alpha_p.size else None

    pedestals = {
        "developed_ex_us": _pedestal(
            ticker=developed_comparator,
            region="developed_ex_us",
            series=series,
            panel=panels["developed_ex_us"],
            periods=panels["developed_ex_us"].periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            facts=facts,
        ),
        "emerging": _pedestal(
            ticker=emerging_comparator,
            region="emerging",
            series=series,
            panel=panels["emerging"],
            periods=panels["emerging"].periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            facts=facts,
        ),
        "us": _pedestal(
            ticker=us_comparator,
            region="us",
            series=series,
            panel=panels["us"],
            periods=panels["us"].periods,
            hac_lags=hac_lags,
            dispersion=dispersion,
            power=power,
            facts=facts,
        ),
    }

    rolling = _rolling_loadings(
        usable=usable,
        windows=windows,
        series=series,
        panels=panels,
        window_months=rolling_window,
    )

    cross_source = _cross_check(
        cache, [fund.ticker for fund in usable], series, windows
    )

    exp_002_attrition = _exp_002_attrition_recomputed(cache)

    summary = (
        f"Screened {universe.mandate_matches} region-and-factor matching series from the "
        f"union of the {universe.frame_quarter} and {universe.follow_up_quarter} N-PORT "
        f"censuses; {len(universe.passing)} passed the predeclared ex-US screen and "
        f"{len(usable)} had at least {minimum_months} filed monthly returns. "
        f"{sum(1 for item in outcomes if item.status == 'exploratory')} product(s) reached "
        f"`exploratory`, {sum(1 for item in outcomes if item.status == 'rejected')} were "
        f"`rejected` on the frozen falsifier and "
        f"{sum(1 for item in outcomes if item.status == 'unresolved')} are `unresolved`. "
        f"Median usable history is "
        f"{int(np.median([w.months for w in windows.values()])) if windows else 0} months "
        f"against Experiment 002's uniform 72. The binding constraint is the data "
        f"contract and the length of the available windows, not the evidence."
    )

    diagnostics: dict[str, JsonValue] = {
        "relationship_to_experiment_002": {
            "what_changed": (
                "Experiment 002's screen was COMPLEMENTED, not modified. Its two "
                "regexes were asserted byte-for-byte before this run and its "
                "committed universe file was not written to. Every statistic here "
                "is computed by the same functions, so an ex-US number is "
                "comparable to a US number fund for fund."
            ),
            "changed_us_results": "none",
            "one_correction_to_a_published_diagnostic": exp_002_attrition,
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
        "shelf_depth": shelf_depth(universe.funds),
        "coverage": coverage,
        "fetch_failures": fetch_failures,
        "validation_gates": gates,
        "factor_provenance": {
            region: dict(panel.provenance) for region, panel in panels.items()
        },
        "exposures": [fit.to_json() for fit in flat_fits],
        "subperiod_exposures": [fit.to_json() for fit in half_fits.values()],
        "wrong_panel_exposures": [
            fits.wrong_panel.to_json()
            for fits in all_fits.values()
            if fits.wrong_panel is not None
        ],
        "us_panel_exposures": [
            fits.us_panel.to_json() for fits in all_fits.values() if fits.us_panel is not None
        ],
        "bootstrap_intervals": {
            ticker: {name: list(bounds) for name, bounds in blocks.items()}
            for ticker, blocks in intervals.items()
        },
        "rolling_loadings": rolling,
        "replication": [item.to_json() for item in replications.values()],
        "cross_source_check": cross_source,
        "model_misfit_pedestals": pedestals,
        "ex_us_structural_drag": _structural_drag(
            _mapping_or_empty(pedestals["developed_ex_us"]), _mapping_or_empty(pedestals["us"])
        ),
        "mandate_and_region_verification": _verify_facts(universe.passing, extras),
        "multiple_testing": {
            "family_definition": (
                "every fund with usable returns times every model specification "
                "estimated on its OWN regional panel, not only the funds and the "
                "specification reported"
            ),
            "family_size": int(alpha_p.size),
            "funds": len(usable),
            "specifications": list(FACTOR_SPECIFICATIONS),
            "alpha": _correction_json(flat_fits, bh, holm),
            "denominator_hostile_test": {
                "why": (
                    "A fund that failed the screen was never regressed and so has no "
                    "p-value, but the search still passed over it. Padding the family "
                    "to its full width with p = 1.0 cannot create a rejection and "
                    "strictly tightens both corrections."
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
                "every_matching_series_screened": inflated_family(
                    [fit.alpha_p for fit in flat_fits],
                    family_size=max(
                        len(flat_fits), len(universe.funds) * len(FACTOR_SPECIFICATIONS)
                    ),
                ),
            },
        },
        "outcomes": [item.to_json() for item in outcomes],
        "unobservable": {
            "foreign_tax_paid_and_credit": (
                "NOT AVAILABLE. Form N-PORT carries no foreign-tax-paid figure. It is "
                "reported to shareholders on Form 1099-DIV box 7 and in the annual "
                "report on Form N-CSR. Recorded as a gap; the structural-drag block "
                "bounds it rather than measuring it."
            ),
            "realised_taxable_distributions": (
                "NOT AVAILABLE. Item B.5 reports a single total return with no "
                "distribution split."
            ),
            "portfolio_turnover": (
                "NOT AVAILABLE from Form N-PORT. The fund's internal trading cost is "
                "inside the tracking difference and is reported there rather than "
                "modelled -- which matters more ex-US than in the US audit, because "
                "ex-US execution is dearer."
            ),
            "stated_index_returns": (
                "NOT AVAILABLE. Index levels are licensed products and no free source "
                "with a documented contract carries them, so the tracking difference "
                "here is against a CONSTRUCTED benchmark -- the regional comparator "
                "fund and the fitted cheap combination -- and never against the fund's "
                "own stated index."
            ),
        },
    }

    caveats = _caveats(universe, usable, windows, flat_fits, outcomes, minimum_months)
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


def _mapping_or_empty(value: JsonValue) -> Mapping[str, JsonValue]:
    return value if isinstance(value, Mapping) else {}


def _fit_on(
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
    """Fit the primary specification on one panel, or ``None`` if it cannot be."""
    usable = tuple(period for period in periods if period in set(panel.periods))
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    if len(usable) <= len(factors) + 6 or not _covered(series, usable):
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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exp_002_parameters() -> Mapping[str, object]:
    """Experiment 002's frozen parameters, read from its own committed YAML."""
    path = workspace_root() / "experiments" / "exp_002_fund_exposure.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    parameters = payload.get("parameters") if isinstance(payload, dict) else None
    if not isinstance(parameters, dict):
        raise ExUsProductError("exp_002_fund_exposure.yaml has no parameters block")
    return parameters


def _exp_002_attrition_recomputed(cache: RawCache) -> dict[str, JsonValue]:
    """Experiment 002's own attrition, with renames separated from deaths.

    Experiment 002 reports 358 of 1513 mandate-qualifying series gone by the
    follow-up quarter. That number differences two NAME-QUALIFIED sets of series
    identifiers, so a fund still filing under a name that no longer matches the
    pattern is counted as a death. Recomputing it here changes no loading and no
    verdict in that experiment; it corrects the reading of one diagnostic.
    """
    from portfolio_edge.experiments.exp_009_universe import (
        EXP_002_EXCLUSION_REGEX,
        EXP_002_MANDATE_REGEX,
    )

    frame, _ = nport.load_frame(cache, "2019q4")
    follow_up, _ = nport.load_frame(cache, "2025q4")
    # exp_002's screen tests the mandate pattern and the exclusion pattern; there
    # is no separate region pattern, so the region regex is set to "match
    # everything" to reproduce its qualifying set exactly.
    patterns = ScreeningPatterns(
        region_regex="",
        factor_regex=EXP_002_MANDATE_REGEX,
        exclusion_regex=EXP_002_EXCLUSION_REGEX,
        us_token_regex="",
        global_token_regex="",
        ex_us_token_regex="",
        emerging_regex="",
        world_ex_us_regex="",
        mandate_patterns=(),
    )
    report = attrition(frame, follow_up, patterns)
    payload: dict[str, JsonValue] = plain_json(report.to_json())  # type: ignore[assignment]
    payload["what_this_corrects"] = (
        "Experiment 002's published attrition counts a fund that renamed out of "
        "its mandate pattern as a fund that died. Of the "
        f"{report.qualifying_in_frame} qualifying series in 2019Q4, "
        f"{report.absent_from_follow_up_census} had left the census by 2025Q4 and "
        f"{report.renamed_out_of_the_pattern} were still filing under a name the "
        "pattern no longer matches. The published rate is "
        f"{report.naive_rate * 100:.1f}%; the death rate is "
        f"{report.death_rate * 100:.1f}%."
    )
    return payload


def _verify_facts(
    funds: Sequence[ScreenedExUsFund], extras: Mapping[str, ExtraFacts]
) -> list[dict[str, JsonValue]]:
    """Where the name-derived mandate and region disagree with the prospectus.

    The screen is mechanical on purpose, and a mechanical rule applied to names
    written by marketing departments will sometimes be wrong. Reporting the
    disagreements is the point: an unreported reconciliation would be a
    discretionary edit to a predeclared screen.
    """
    rows: list[dict[str, JsonValue]] = []
    for fund in funds:
        extra = extras.get(fund.ticker)
        stated_mandate = "" if fund.facts is None else fund.facts.stated_mandate
        stated_region = None if extra is None else extra.stated_region
        mandate_agrees = stated_mandate == (fund.derived_mandate or "")
        region_agrees = stated_region is None or stated_region == fund.derived_region
        if mandate_agrees and region_agrees:
            continue
        rows.append(
            {
                "ticker": fund.ticker,
                "derived_mandate": fund.derived_mandate,
                "stated_mandate": stated_mandate,
                "derived_region": fund.derived_region,
                "stated_region": stated_region,
                "index_region_words": "" if extra is None else extra.index_region_words,
                "resolution": (
                    "The DERIVED value decides the screen and the grading, because it "
                    "was fixed before any return was read. The disagreement is "
                    "reported, never silently reconciled."
                ),
            }
        )
    return rows


def _rolling_loadings(
    *,
    usable: Sequence[ScreenedExUsFund],
    windows: Mapping[str, FundWindow],
    series: Mapping[str, FundSeries],
    panels: Mapping[str, FactorPanel],
    window_months: int,
) -> list[dict[str, JsonValue]]:
    """Rolling intended-factor loading, to test stability instead of assuming it."""
    factors = FACTOR_SPECIFICATIONS[PRIMARY_SPECIFICATION]
    out: list[dict[str, JsonValue]] = []
    for fund in usable:
        if fund.intended_factor is None:
            continue
        window = windows[fund.ticker]
        panel = panels[fund.derived_region or ""]
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
            "Holm-Bonferroni is valid under arbitrary dependence. These tests are NOT "
            "independent: the same six factors, overlapping windows and three nested "
            "specifications per fund, so the Benjamini-Hochberg count is an OPTIMISTIC "
            "bound and Holm is the defensible one."
        )
    return payload


def _estimates(
    outcomes: Sequence[ExUsOutcome],
    fits: Mapping[str, RegionalFits],
    replications: Mapping[str, ReplicationResult],
) -> list[Estimate]:
    out: list[Estimate] = []
    for outcome in outcomes:
        fit = fits[outcome.ticker].own_panel.get(PRIMARY_SPECIFICATION)
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
                    "stationary block bootstrap, 95%, mean block 6m, joint resampling of "
                    "the return and the whole design, on the fund's own "
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
                    f"{outcome.region}; sign-adjusted for the mandate; smallest loading "
                    f"this window could detect at 80% power "
                    f"{outcome.intended_loading_mde:.3f}; status {outcome.status}"
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
                    "A posterior mean under a fixed prior has no sampling interval of its "
                    f"own. The raw alpha is {fit.alpha_annual_percent:+.2f} pp/yr with HAC "
                    f"standard error {fit.alpha_se_annual_percent:.2f}, shrinkage factor "
                    f"{fit.shrinkage_factor:.3f}, and a minimum detectable alpha at 80% "
                    f"power of {fit.minimum_detectable_alpha_percent:.2f} pp/yr over "
                    f"{outcome.months} months."
                ),
                cost_basis=CostBasis.NET_OPTIMISTIC,
                n_obs=fit.n_observations,
                notes=(
                    "NOT a promotion criterion in either direction. A positive alpha over "
                    "a short history is not evidence of future manager skill."
                ),
            )
        )
        replication = replications.get(outcome.ticker)
        if replication is not None:
            out.append(
                Estimate(
                    name=f"{outcome.ticker} implementation shortfall vs cheap ex-US replication",
                    value=replication.implementation_shortfall,
                    units="percentage points per year",
                    interval=None,
                    uncertainty_unavailable_reason=(
                        "The replicating weights are fitted IN SAMPLE, so this is a best "
                        "case for the replication and a hard test for the product. A "
                        "sampling interval around a look-ahead quantity would imply a "
                        "precision the construction does not have."
                    ),
                    cost_basis=CostBasis.NET_OPTIMISTIC,
                    notes=f"basis {list(replication.basis)} over {replication.months} months",
                )
            )
    return out


def _caveats(
    universe: object,
    usable: Sequence[ScreenedExUsFund],
    windows: Mapping[str, FundWindow],
    fits: Sequence[ExposureFit],
    outcomes: Sequence[ExUsOutcome],
    minimum_months: int,
) -> list[str]:
    del universe
    median_mde = (
        float(np.median([fit.minimum_detectable_alpha_percent for fit in fits]))
        if fits
        else float("nan")
    )
    lengths = [window.months for window in windows.values()]
    return [
        "EXPLORATORY. Decision 0002 stands: this may not promote a sleeve and may not "
        "appear in the app as a finding.",
        f"Windows run from {min(lengths) if lengths else 0} to "
        f"{max(lengths) if lengths else 0} months and are UNEQUAL across funds, so a "
        "cross-fund comparison of alphas is a comparison of differently powered "
        "estimates. The median minimum detectable alpha at 80% power is "
        f"{median_mde:.2f} pp/yr, larger than any plausible true alpha.",
        f"A fund with fewer than {minimum_months} usable months is reported and "
        "excluded from estimation rather than estimated badly. Its absence is a "
        "statement about its age, not about the product.",
        "Every return here is NET OF FOREIGN DIVIDEND WITHHOLDING, which is deducted "
        "before net asset value is struck and is not recoverable inside the fund. Form "
        "N-PORT carries no foreign-tax-paid figure, so the charge is bounded by the "
        "pedestal comparison and never measured. A taxable US shareholder may recover "
        "part of it through the foreign tax credit; a retirement-account shareholder "
        "may not. Neither case is modelled.",
        "The tracking difference is against a CONSTRUCTED benchmark -- the regional "
        "comparator fund and an in-sample fitted combination of cheap ex-US funds -- "
        "and never against the fund's own stated index, because index levels are "
        "licensed and no free source with a documented contract carries them.",
        "The replicating combination is fitted in sample. An investor could not have "
        "known those weights in advance, so it is a best case for the replication and "
        "the comparison against it is deliberately hard on the product.",
        "The French international files are built from a different vintage than the US "
        "file, their second moments were never gated against any printed table, and "
        "their dividend-tax treatment is undocumented. Every ex-US loading inherits "
        "that, and it is why the regional validation gates are looser than the US ones.",
        "Item B.5 returns are fund-reported and unaudited, and General Instruction G "
        "lets each filer use its own methodology.",
        "Public N-PORT filings begin in 2019, so no census here can see a fund that "
        "closed before then. The measured attrition is a LOWER BOUND on survivorship "
        "contamination even after renames are separated from deaths.",
        f"{len(usable)} funds cleared every screen and had usable returns; "
        f"{sum(1 for item in outcomes if item.status == 'rejected')} were rejected on "
        "the frozen falsifier, which is a statement about delivered exposure and cost, "
        "not about whether the underlying factor exists.",
    ]


def _frames(
    universe: object,
    fits: Sequence[ExposureFit],
    replications: Mapping[str, ReplicationResult],
    outcomes: Sequence[ExUsOutcome],
    coverage: Sequence[Mapping[str, JsonValue]],
) -> dict[str, pd.DataFrame]:
    from portfolio_edge.experiments.exp_009_universe import ExUsUniverse

    assert isinstance(universe, ExUsUniverse)
    screen_rows = [
        {
            "ticker": fund.ticker,
            "series_name": fund.series_name_follow_up or fund.series_name_frame,
            "renamed": fund.renamed,
            "passed": fund.passed,
            "failed_criterion": fund.failed_criterion or "",
            "failure_detail": fund.failure_detail,
            "net_assets_max_usd": fund.net_assets_max,
            "net_assets_2019_usd": fund.net_assets_frame,
            "net_assets_2025_usd": fund.net_assets_follow_up,
            "in_follow_up_census": fund.in_follow_up_census,
            "net_expense_ratio_percent": _net_expense(fund.facts),
            "derived_mandate": fund.derived_mandate or "",
            "derived_region": fund.derived_region or "",
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
            "shrunk_alpha_annual_percent": fit.shrunk_alpha_annual_percent,
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
    cache = RawCache()
    universe = build_universe(
        cache=cache,
        patterns=screening_patterns_from_specification(specification),
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

    print(f"universe written to {path}")
    print(
        f"  union frame {universe.frame_quarter} + {universe.follow_up_quarter}: "
        f"{universe.union_series_count} series"
    )
    print(f"  region-and-factor matches: {universe.mandate_matches}")
    print(f"  passed: {len(universe.passing)}")
    counts: dict[str, int] = {}
    for fund in universe.funds:
        if fund.failed_criterion:
            counts[fund.failed_criterion] = counts.get(fund.failed_criterion, 0) + 1
    for criterion, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"    failed {criterion}: {count}")
    report = universe.attrition
    print(
        f"  attrition: {report.absent_from_follow_up_census} of "
        f"{report.qualifying_in_frame} qualifying series left the census "
        f"({report.death_rate * 100:.1f}%); {report.renamed_out_of_the_pattern} renamed "
        f"out of the pattern while still filing (a naive difference would have called "
        f"the rate {report.naive_rate * 100:.1f}%); "
        f"{report.launched_inside_the_window} launched inside the window"
    )
    for fund in universe.passing:
        print(
            f"    {fund.ticker:<6} {fund.net_assets_max / 1e9:8.2f}bn  "
            f"{fund.derived_region or '?':<16}{fund.derived_mandate or '?':<17}"
            f"{fund.intended_factor or '?':<5} {_net_expense(fund.facts):.2f}%  "
            f"{(fund.series_name_follow_up or fund.series_name_frame)[:48]}"
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
            f"Universe: union frame {universe['frame_quarters']}, "
            f"{universe['union_series_count']} series, "
            f"{universe['mandate_matches']} region-and-factor matches, "
            f"{universe['passed_screen']} passed, {universe['usable_returns']} usable."
        )
        attrition_block = universe.get("attrition")
        if isinstance(attrition_block, Mapping):
            naive = attrition_block["naive_rate_counting_renames_as_deaths"]
            lines.append(
                "  attrition (LOWER BOUND): "
                f"{attrition_block['absent_from_follow_up_census']} of "
                f"{attrition_block['qualifying_in_frame']} qualifying series LEFT the "
                f"census ({float(str(attrition_block['death_rate'])) * 100:.1f}%); "
                f"{attrition_block['renamed_out_of_the_pattern']} merely RENAMED out of "
                "the pattern while still filing. Differencing name-qualified sets "
                "would have reported "
                f"{float(str(naive)) * 100:.1f}%."
            )
        lines.append("")

    depth = diagnostics.get("shelf_depth")
    if isinstance(depth, Mapping):
        lines.append("Shelf depth: how many products deliver each exposure in each region")
        for region, block in depth.items():
            if not isinstance(block, Mapping):
                continue
            rendered = ", ".join(
                f"{mandate} {_as_mapping(entry)['products']} "
                f"({' '.join(str(t) for t in _as_sequence(_as_mapping(entry)['tickers']))})"
                for mandate, entry in block.items()
            )
            lines.append(f"  {region}: {rendered}")
        lines.append("")

    gates = diagnostics.get("validation_gates")
    if isinstance(gates, Sequence):
        for gate in gates:
            if not isinstance(gate, Mapping):
                continue
            lines.append(
                f"Gate PASSED {gate['region']:<16} {gate['comparator']}: correlation "
                f"{float(str(gate['correlation_with_market_total_return'])):.4f}, beta "
                f"{float(str(gate['market_beta'])):.4f}, R2 "
                f"{float(str(gate['r_squared'])):.4f}, worst month {gate['worst_month']}"
            )
        lines.append("")

    outcomes = diagnostics.get("outcomes")
    if isinstance(outcomes, Sequence):
        header = (
            f"{'ticker':<7}{'region':<9}{'fac':<5}{'n':>4}{'from':>9}"
            f"{'load':>8}{'se':>7}{'MDE':>7}"
            f"{'  95% bootstrap':<20}{'wrong':>7}{'US':>7}"
            f"{'alphaR':>8}{'alphaS':>8}{'aMDE':>7}  status"
        )
        lines.extend(
            ["Exposure audit on each fund's OWN regional panel, FF5+UMD", header, "-" * len(header)]
        )
        for item in sorted(
            (row for row in outcomes if isinstance(row, Mapping)),
            key=lambda row: (str(row["region"]), -float(str(row["intended_loading"]))),
        ):
            interval = item["intended_loading_interval"]
            assert isinstance(interval, Sequence)
            region = str(item["region"]).replace("developed_ex_us", "dev-exUS")
            lines.append(
                f"{item['ticker']!s:<7}{region:<9}{item['intended_factor']!s:<5}"
                f"{int(str(item['months'])):>4}{item['first_month']!s:>9}"
                f"{_show(item['intended_loading'], 8, 3, signed=True)}"
                f"{_show(item['intended_loading_se'], 7, 3)}"
                f"{_show(item['intended_loading_mde_80pc_power'], 7, 3)}"
                f"  [{_show(interval[0], 6, 3, signed=True)},"
                f"{_show(interval[1], 6, 3, signed=True)}]"
                f"{_show(item['intended_loading_wrong_regional_panel'], 7, 2, signed=True)}"
                f"{_show(item['intended_loading_us_panel'], 7, 2, signed=True)}"
                f"{_show(item['alpha_annual_percent'], 8, 2, signed=True)}"
                f"{_show(item['shrunk_alpha_annual_percent'], 8, 2, signed=True)}"
                f"{_show(item['alpha_mde_80pc_power_percent'], 7, 2)}  {item['status']}"
            )
            for clause in _as_sequence(item["falsifier_clauses_fired"]):
                lines.append(f"         {clause}")
        lines.append("")
        lines.append(
            "n is the fund's own usable months. MDE is the smallest loading that window "
            "could detect at 80% power; aMDE the same for the annual alpha. 'wrong' is "
            "the same loading on the OTHER ex-US region's panel and 'US' on the US "
            "panel, both hostile tests of whether the regional panel is doing any work."
        )
        lines.append("")

    replication = diagnostics.get("replication")
    if isinstance(replication, Sequence):
        header = (
            f"{'ticker':<7}{'n':>4}{'TD vs mkt':>11}{'TD vs combo':>13}{'TE combo':>10}"
            f"{'TD vs French':>14}{'fee prem':>9}{'shortfall':>11}  weights"
        )
        lines.extend(
            ["Can cheap broad ex-US funds already do this? (pp/yr)", header, "-" * len(header)]
        )
        for item in sorted(
            (row for row in replication if isinstance(row, Mapping)),
            key=lambda row: -float(str(row["implementation_shortfall_pp"])),
        ):
            weights = _as_sequence(item["weights"])
            basis = _as_sequence(item["basis"])
            rendered = " ".join(
                f"{basis[i]}={float(str(weights[i])) * 100:.0f}%"
                for i in range(len(basis))
                if float(str(weights[i])) > 0.005
            )
            lines.append(
                f"{item['ticker']!s:<7}{int(str(item['months'])):>4}"
                f"{float(str(item['tracking_difference_vs_regional_market_pp'])):>+11.2f}"
                f"{float(str(item['tracking_difference_vs_combination_pp'])):>+13.2f}"
                f"{float(str(item['tracking_error_vs_combination_pp'])):>10.2f}"
                f"{float(str(item['tracking_difference_vs_french_market_pp'])):>+14.2f}"
                f"{float(str(item['fee_premium_over_basis_pp'])):>+9.2f}"
                f"{float(str(item['implementation_shortfall_pp'])):>+11.2f}  {rendered}"
            )
        lines.append("")
        lines.append(
            "TD vs French is against the region's Ken French market portfolio and is the "
            "ONLY column containing the foreign-withholding wedge; it cannot separate it "
            "from index-construction differences and is never a measurement of tax."
        )
        lines.append("")

    pedestals = diagnostics.get("model_misfit_pedestals")
    if isinstance(pedestals, Mapping):
        lines.append("MODEL-MISFIT PEDESTALS. A market fund IS its market, so its alpha")
        lines.append("should be about minus its fee. Read every fund alpha as a distance")
        lines.append("from its own region's pedestal, never from zero.")
        for region, block in pedestals.items():
            if not isinstance(block, Mapping) or not block.get("available"):
                continue
            specs = _as_mapping(block["by_specification"])
            rendered = ", ".join(
                f"{name} {float(str(_as_mapping(entry)['alpha_annual_percent'])):+.2f}"
                for name, entry in specs.items()
            )
            lines.append(
                f"  {region:<16}{block['ticker']!s:<5} fee "
                f"{float(str(block['net_expense_ratio_percent'])):.2f}%  {rendered} pp/yr; "
                f"simple gap vs the French market "
                f"{float(str(block['simple_gap_vs_french_market_pp'])):+.2f} pp/yr over "
                f"{block['months']} months"
            )
        lines.append("")

    drag = diagnostics.get("ex_us_structural_drag")
    if isinstance(drag, Mapping) and drag.get("available"):
        difference = float(str(drag["difference_of_gaps_beyond_fee_pp"]))
        lines.append(
            f"EX-US STRUCTURAL DRAG. {drag['ex_us_comparator']} differs from its own "
            f"French market by "
            f"{float(str(drag['ex_us_gap_vs_own_french_market_pp'])):+.2f} pp/yr against a "
            f"{float(str(drag['ex_us_fee_percent'])):.2f}% fee, so "
            f"{float(str(drag['ex_us_gap_beyond_fee_pp'])):+.2f} pp/yr once the fee is put "
            f"back. {drag['us_comparator']} differs from its own by "
            f"{float(str(drag['us_gap_vs_own_french_market_pp'])):+.2f} pp/yr against "
            f"{float(str(drag['us_fee_percent'])):.2f}%, so "
            f"{float(str(drag['us_gap_beyond_fee_pp'])):+.2f} pp/yr. Difference "
            f"{difference:+.2f} pp/yr (positive = the ex-US fund did BETTER against its "
            "own benchmark)."
        )
        lines.append(
            "  " + str(drag["what_this_can_and_cannot_conclude"])
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
            f"Benjamini-Hochberg at 0.10: {alpha_block.get('rejected_benjamini_hochberg')}; "
            f"Holm-Bonferroni at 0.10: {alpha_block.get('rejected_holm_bonferroni')}"
        )
        lines.append("")

    relationship = diagnostics.get("relationship_to_experiment_002")
    if isinstance(relationship, Mapping):
        lines.append(
            f"Previously published US results changed: {relationship['changed_us_results']}"
        )
        correction_block = relationship.get("one_correction_to_a_published_diagnostic")
        if isinstance(correction_block, Mapping):
            lines.append(f"  {correction_block['what_this_corrects']}")
        lines.append("")

    verification = diagnostics.get("mandate_and_region_verification")
    if isinstance(verification, Sequence) and verification:
        lines.append(
            "Name-derived mandate or region disagrees with the prospectus for "
            f"{len(verification)} fund(s); the derived value decided the screen:"
        )
        for row in verification:
            if isinstance(row, Mapping):
                lines.append(
                    f"  {row['ticker']}: derived {row['derived_mandate']}/"
                    f"{row['derived_region']} vs stated {row['stated_mandate']}/"
                    f"{row['stated_region']} ({row['index_region_words']})"
                )
        lines.append("")

    cross = diagnostics.get("cross_source_check")
    if isinstance(cross, Mapping):
        compared = _as_sequence(cross["compared"])
        unavailable = _as_sequence(cross["unavailable"])
        if compared:
            medians = [
                float(str(_as_mapping(item)["median_absolute_difference_bp"]))
                for item in compared
            ]
            lines.append(
                f"Cross-source check: {len(compared)} funds compared, median absolute "
                f"monthly disagreement {float(np.median(medians)):.1f} bp, worst fund "
                f"median {max(medians):.1f} bp. {len(unavailable)} unavailable."
            )
        else:
            lines.append(
                f"Cross-source check: NOT AVAILABLE for any fund ({len(unavailable)} "
                "refusals). Nothing depends on it, but the check could not be run."
            )
        lines.append("")

    lines.append("Caveats:")
    lines.extend(f"  - {caveat}" for caveat in result.caveats)
    return "\n".join(lines)


def _show(value: JsonValue, width: int, places: int, *, signed: bool = False) -> str:
    """Right-aligned number, or a dash for a quantity that does not exist.

    Unequal windows mean some quantities genuinely have no value -- a fund with 40
    months has no first-half loading. Printing 0.000 or nan there would both read
    as measurements.
    """
    if value is None or not isinstance(value, int | float):
        return "-".rjust(width)
    sign = "+" if signed else ""
    return f"{float(value):>{sign}{width}.{places}f}"


def _as_mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    assert isinstance(value, Mapping)
    return value


def _as_sequence(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    """Build the universe, or run Experiment 009 through the real runner and ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_009_exus_products",
        description=(
            "Audit the exposure and implementation cost of screened ex-US factor "
            "products, writing a ledger entry for the attempt."
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
            "screen the union of the two N-PORT censuses and write the committed "
            "product universe. MUST be run before the audit: the universe is fixed "
            "before any return is downloaded, and the audit refuses to rebuild it."
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
                "exp_009_exus_products"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
