"""Regenerates the measured tables behind :mod:`portfolio_edge.studies.stacking`.

Kept separate from the study so the study stays pure and testable and only this file
touches the cache, exactly as :mod:`portfolio_edge.studies._factor_breadth_tables` is.
Run it with

    uv run python -m portfolio_edge.studies._stacking_tables

**This is a scoping script, not a frozen experiment.** No specification was frozen before
its numbers were seen, so nothing it prints may promote a sleeve or settle a decision. It
exists to answer one question the repository had never asked — *how many independent bets
is the candidate portfolio actually making* — and to say whether an experiment is worth
commissioning.

How each sleeve's excess-return series is built
-----------------------------------------------
A candidate fund's excess over the fund it displaces is modelled as its **measured
delivered loading vector** applied to its own region's factor returns:

    excess_t  =  sum_k (h_fund,k - h_incumbent,k) * f_k,t

with the loadings taken from the typed shelf in ``src/content/shelf.ts`` and
``src/content/tilts.ts``, which are Experiments 009 and 013's published outputs. This is
the same three-term chain :mod:`portfolio_edge.studies.value_tilt` prices, evaluated
month by month instead of on the mean, and it therefore inherits that module's rule: **a
loading is never multiplied by a long-only capture fraction.**

Three consequences, all of them limitations:

* The synthetic carries **no residual**. A real fund's tracking error against its
  incumbent is larger, and the gap is measured below and added back as an uncorrelated
  diagonal term, because idiosyncratic tracking error is real risk with no expected
  return attached.
* It carries **no market-beta difference**. Both funds are long-only equity in the same
  region; the residual term absorbs whatever beta difference exists.
* It carries **no alpha**. DFIV's own alpha is -4.11 pp/yr against a 3.52 pp/yr floor
  and charging it flips that tilt's sign; that sensitivity belongs to the recommendation
  and is reported here as a scenario rather than built in.

Everything except the covariance is an **input**. This module estimates no premium: the
premia are the repository's own measured post-publication figures, carried in
:data:`PREMIUM_SCENARIOS` with their source, and every headline is reported across all of
them rather than at one.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import aqr, french
from portfolio_edge.data.cache import RawCache, default_cache_root
from portfolio_edge.inference.hac import hac_mean
from portfolio_edge.studies.factor_breadth import (
    MONTHS_PER_YEAR,
    common_window,
    correlation_matrix,
    minimum_detectable_effect,
)
from portfolio_edge.studies.stacking import (
    MDE_TO_STANDARD_ERROR,
    Sleeve,
    confidence_ceiling,
    effective_bets,
    equicorrelated_probability,
    marginal_contribution,
    portfolio_edge_ceiling,
    probability_with_parameter_uncertainty,
    stack,
    stacking_ceiling_probability,
)
from portfolio_edge.studies.value_tilt import TiltInputs

#: The last month read. Six further months exist in every French file and are left
#: genuinely post-specification, which is the convention
#: ``docs/research/long-only-capture.md`` set and this module keeps.
LAST_MONTH: Final = "2025-12"

#: Percent, because the French and AQR parsers hand back decimals and every figure in
#: ``studies`` is in percentage points a year.
PERCENT: Final = 100.0

#: The candidate portfolio, as the reader proposed it. Capital weights, summing to 100.
CANDIDATE_WEIGHTS: Final[Mapping[str, float]] = {
    "RSST": 0.30,
    "VTI": 0.20,
    "AVLV": 0.15,
    "DFIV": 0.10,
    "VEA": 0.10,
    "IDMO": 0.05,
    "IEMG": 0.05,
    "AVES": 0.05,
}


#: AVES's incremental cost over IEMG, pp/yr. The fee half is **measured** as of
#: 2026-08-22: AVES charges 36 bp gross-equal-to-net with no waiver and no expense cap,
#: against IEMG's 9 bp contractually capped to 2030-12-31, so the fee delta is 27 bp and
#: it is the more durable of the two commitments in AVES's disfavour.
#:
#: The turnover half is **assumed**. Neither fund's portfolio turnover rate has been read
#: here, so this charges AVES with the 7%/yr its US sibling AVLV files, at ``k = 1.7``,
#: against an implicit zero for IEMG. That is deliberately unfavourable to AVES: an
#: emerging-market value sort almost certainly rotates more than 7%, and IEMG's own
#: turnover is not zero. The fee-only floor is 0.27 and the difference moves no verdict.
AVES_INCREMENTAL_COST: Final = (0.36 - 0.09) + 1.7 * 7 * 0.01


@dataclass(frozen=True)
class SleeveSpec:
    """One candidate sleeve: which region's factors, which delivered loadings, what weight.

    ``loadings`` are already **incremental over the incumbent**. ``measured_tracking_error``
    is the fund-against-incumbent tracking error where this repository measured one and
    ``None`` where it did not; the ``None`` cases are filled from the measured cases'
    factor-explained share and that substitution is reported as an assumption.
    """

    ticker: str
    incumbent: str
    region: str
    weight: float
    loadings: Mapping[str, float]
    measured_tracking_error: float | None
    incremental_cost: float
    note: str


#: Delivered loadings, `h_fund - h_incumbent`, from the typed shelf. AVLV's and DFIV's
#: come from ``src/content/tilts.ts`` at full precision because the client reproduces the
#: published edge from them; IDMO's and AVES's from ``src/content/shelf.ts``.
#:
#: AVES's incumbent IEMG has no measured loading of any kind, so its delivered HML is its
#: own +0.237 with an implicit zero for the incumbent. That is the most optimistic
#: reading available and is stated as such.
CANDIDATE_SLEEVES: Final[tuple[SleeveSpec, ...]] = (
    SleeveSpec(
        ticker="AVLV",
        incumbent="VTI",
        region="us",
        weight=0.15,
        loadings={"HML": 0.322028508346998 - 0.0246971965235378, "SMB": 0.12},
        measured_tracking_error=None,  # filled from tilts.ts inputs below
        incremental_cost=0.0,  # filled below
        note="US large value, funded out of VTI",
    ),
    SleeveSpec(
        ticker="DFIV",
        incumbent="VEA",
        region="exus",
        weight=0.10,
        loadings={
            "HML": 0.6976037808578383 - -0.025186177492858675,
            "SMB": -0.114,
            "RMW": -0.001,
            "CMA": -0.122,
            "UMD": 0.016 - 0.006,
        },
        measured_tracking_error=None,
        incremental_cost=0.0,
        note="developed ex-US large value, funded out of VEA",
    ),
    SleeveSpec(
        ticker="IDMO",
        incumbent="VEA",
        region="exus",
        weight=0.05,
        loadings={
            "UMD": 0.540 - 0.006,
            "HML": 0.218 - 0.015,
            "SMB": -0.164,
            "RMW": 0.040,
            "CMA": -0.394,
        },
        measured_tracking_error=None,
        incremental_cost=0.22 + 1.7 * (105 - 4) * 0.01,
        note="developed ex-US momentum, funded out of VEA",
    ),
    SleeveSpec(
        ticker="AVES",
        incumbent="IEMG",
        region="em",
        weight=0.05,
        loadings={"HML": 0.237},
        measured_tracking_error=None,
        incremental_cost=AVES_INCREMENTAL_COST,
        note="emerging value, funded out of IEMG; fee measured, turnover assumed",
    ),
)

#: The two tilts this repository priced, at full precision, so the tracking errors below
#: reproduce the published 135 bp and 47.6 bp rather than approximating them.
PRICED_TILT_INPUTS: Final[Mapping[str, TiltInputs]] = {
    "AVLV": TiltInputs(
        weight=0.20,
        fund_hml_loading=0.322028508346998,
        benchmark_hml_loading=0.0246971965235378,
        hml_premium=4.740625,
        fund_fee=0.15,
        benchmark_fee=0.03,
        fund_turnover_percent=7.0,
        benchmark_turnover_percent=3.0,
        turnover_coefficient=1.7,
        fund_volatility=17.181423095590738,
        benchmark_volatility=16.23770348459306,
        correlation=0.9194103780959881,
    ),
    "DFIV": TiltInputs(
        weight=0.08,
        fund_hml_loading=0.6976037808578383,
        benchmark_hml_loading=-0.025186177492858675,
        hml_premium=5.07125,
        fund_fee=0.27,
        benchmark_fee=0.03,
        fund_turnover_percent=6.0,
        benchmark_turnover_percent=4.0,
        turnover_coefficient=1.7,
        fund_volatility=15.781965234617221,
        benchmark_volatility=16.598108003208974,
        correlation=0.9337858710123662,
    ),
}

#: Post-publication factor premia, pp/yr, as this repository measured them. Nothing here
#: is estimated by this module.
#:
#: ``own-panel`` is each region's own figure from Experiments 005 and 006 and the size
#: study; ``pooled`` applies the three-region pooled figure everywhere, which is the
#: reading ``docs/research/portfolio-recommendation.md`` uses for the US line because the
#: US-only premium is not signable; ``half`` halves the own-panel figures as a
#: continued-decay scenario; ``null`` sets every premium to zero.
PREMIUM_SCENARIOS: Final[Mapping[str, Mapping[str, Mapping[str, float]]]] = {
    "own-panel": {
        "us": {"HML": 1.57, "SMB": 0.33, "RMW": 0.0, "CMA": 0.0, "UMD": 4.19},
        "exus": {"HML": 5.07125, "SMB": 0.49, "RMW": 1.681, "CMA": 0.533, "UMD": 8.351},
        "em": {"HML": 7.584, "SMB": -0.05, "RMW": 0.0, "CMA": 0.0, "UMD": 9.44},
    },
    "pooled": {
        region: {"HML": 4.740625, "SMB": 0.33, "RMW": 2.53, "CMA": 0.20, "UMD": 7.33}
        for region in ("us", "exus", "em")
    },
    "half": {
        "us": {"HML": 0.785, "SMB": 0.165, "RMW": 0.0, "CMA": 0.0, "UMD": 2.095},
        "exus": {
            "HML": 2.535625,
            "SMB": 0.245,
            "RMW": 0.8405,
            "CMA": 0.2665,
            "UMD": 4.1755,
        },
        "em": {"HML": 3.792, "SMB": -0.025, "RMW": 0.0, "CMA": 0.0, "UMD": 4.72},
    },
    "null": {
        region: {"HML": 0.0, "SMB": 0.0, "RMW": 0.0, "CMA": 0.0, "UMD": 0.0}
        for region in ("us", "exus", "em")
    },
}

#: Published MDE80 for each premium, pp/yr, from the pages that measured it. Dividing by
#: :data:`portfolio_edge.studies.stacking.MDE_TO_STANDARD_ERROR` recovers the standard
#: error, which is how the premium's own uncertainty reaches the probability calculation.
#:
#: RMW's and CMA's entries use the pooled 2.62 pp/yr best-of-twelve-cells floor from
#: ``docs/research/evidence-base.md`` §1 because no per-region figure is published for
#: them; both carry tiny loadings here and neither moves a headline.
PREMIUM_MDE80: Final[Mapping[str, Mapping[str, float]]] = {
    "us": {"HML": 5.03, "SMB": 2.47, "RMW": 2.62, "CMA": 2.62, "UMD": 7.27},
    "exus": {"HML": 3.67, "SMB": 2.83, "RMW": 2.62, "CMA": 2.62, "UMD": 5.21},
    "em": {"HML": 3.00, "SMB": 3.07, "RMW": 2.62, "CMA": 2.62, "UMD": 4.37},
}

#: The standard error on trend's post-publication marginal growth contribution, pp/yr,
#: backed out of the 95% interval ``[-0.175, +2.165]`` around ``+0.883`` in
#: ``docs/research/trend-marginal-value.md``. It is the tightest of the five and it is
#: still wide enough to contain zero.
TREND_EDGE_STANDARD_ERROR: Final = (2.165 - 0.883) / 1.959963984540054

#: Each fund's own fitted alpha **net of its panel's pedestal**, pp/yr, with the detection
#: floor beside it, from ``src/content/shelf.ts``. A pedestal is what a cap-weighted index
#: fund itself earns against the research portfolio it is supposed to be — -0.55 in the US,
#: -0.31 developed ex-US, +1.50 emerging — so an alpha is a distance from that and not from
#: zero.
#:
#: Charging these is a **scenario, not a correction**: three of the four sit inside their
#: own detection floor, and the repository's own reading is that fund alpha on this panel
#: should normally stay ``unresolved``. DFIV's does not sit inside its floor, and that is
#: the single largest unmodelled risk in the candidate.
ALPHA_NET_OF_PEDESTAL: Final[Mapping[str, tuple[float, float]]] = {
    "AVLV": (-0.92 - -0.55, 5.28),
    "DFIV": (-4.11 - -0.31, 3.52),
    "IDMO": (0.11 - -0.31, 5.34),
    "AVES": (-0.16 - 1.50, 4.48),
}

#: Trend's net excess return over cash after the wrapper's cost stack, pp/yr. Every one
#: is an assumption and the range is the point: the post-publication vendor interval
#: contains zero, and ``docs/research/trend-marginal-value.md`` measures the sleeve's
#: post-publication marginal growth at +0.883 with a 95% interval of [-0.175, +2.165].
TREND_NET_EXCESS_SCENARIOS: Final[tuple[float, ...]] = (0.0, 1.0, 2.0, 4.0)

_REGION_FILES: Final[Mapping[str, tuple[str, str, str]]] = {
    "us": ("french_us_ff5", "french_us_momentum", "Mom"),
    "exus": (
        "french_developed_ex_us_ff5",
        "french_developed_ex_us_momentum",
        "WML",
    ),
    "em": ("french_emerging_ff5", "french_emerging_momentum", "WML"),
}


def _monthly(table_periods: Sequence[str], values: Sequence[float | None]) -> dict[str, float]:
    return {
        period: PERCENT * float(value)
        for period, value in zip(table_periods, values, strict=True)
        if value is not None and period <= LAST_MONTH
    }


def load_factors(cache: RawCache) -> dict[str, dict[str, dict[str, float]]]:
    """``region -> factor -> period -> percent``, for the three French regional panels."""
    factors: dict[str, dict[str, dict[str, float]]] = {}
    for region, (five_factor, momentum, column) in _REGION_FILES.items():
        dataset = french.get_dataset(five_factor)
        _, parsed, _ = french.load(cache, dataset)
        table = parsed.table("monthly")
        panel = {
            name: _monthly(table.periods, table.column(name))
            for name in ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
        }
        momentum_dataset = french.get_dataset(momentum)
        _, momentum_parsed, _ = french.load(cache, momentum_dataset)
        momentum_table = momentum_parsed.table("monthly")
        panel["UMD"] = _monthly(momentum_table.periods, momentum_table.column(column))
        factors[region] = panel
    return factors


def load_trend(cache: RawCache) -> dict[str, float]:
    """AQR's diversified time-series-momentum factor, percent a month.

    A **vendor reconstruction** by a firm that sells the strategy, rebuilt on every
    update, with no vintage archive and no stated cost basis — the same three flags
    ``docs/research/trend-marginal-value.md`` raises before any number. It stands in for
    RSST's trend leg. RSST's own loading on that index has since been measured from its
    filings -- +0.681 [+0.406, +0.955] over 31 months to 2026-04,
    ``docs/research/loading-comparability-and-wrapper-exposure.md`` -- so the substitution
    is now an approximation with a known error rather than an unexamined assumption. It
    runs the trend leg about 47% hot: this file gives RSST one dollar of index per dollar
    of notional where 31 months of filings say roughly seven tenths of one arrived.
    """
    dataset = aqr.get_dataset("aqr_tsmom_factors")
    _, parsed, _ = aqr.load(cache, dataset)
    return _monthly(parsed.table.periods, parsed.table.column("TSMOM"))


def synthetic_excess(
    factors: Mapping[str, Mapping[str, float]], loadings: Mapping[str, float]
) -> tuple[tuple[str, ...], FloatArray]:
    """``sum_k h_k f_k,t``: one sleeve's modelled monthly excess over its incumbent."""
    window = common_window([tuple(sorted(factors[name])) for name in loadings])
    values = np.asarray(
        [
            sum(weight * factors[name][period] for name, weight in loadings.items())
            for period in window
        ],
        dtype=np.float64,
    )
    return window, values


def annualised_volatility(values: FloatArray) -> float:
    return float(np.std(values, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)


def _align(
    series: Mapping[str, tuple[tuple[str, ...], FloatArray]], keys: Sequence[str]
) -> tuple[tuple[str, ...], list[FloatArray]]:
    window = common_window([series[key][0] for key in keys])
    aligned = []
    for key in keys:
        lookup = dict(zip(series[key][0], series[key][1], strict=True))
        aligned.append(np.asarray([lookup[period] for period in window], dtype=np.float64))
    return window, aligned


def sleeve_edge_from_premia(
    loadings: Mapping[str, float], premia: Mapping[str, float], cost: float
) -> float:
    """``sum_k h_k * premium_k - cost``, per dollar of sleeve.

    Three terms per factor and no fourth. A factor whose premium this repository cannot
    sign still enters, at whatever the scenario says it is — carrying an exposure to an
    unsignable premium is variance without a priced expectation, and zeroing it silently
    would hide that.
    """
    return sum(loadings.get(name, 0.0) * value for name, value in premia.items()) - cost


def _print_matrix(labels: Sequence[str], matrix: Sequence[Sequence[float]]) -> None:
    print("             " + "".join(f"{label[:10]:>12s}" for label in labels))
    for label, row in zip(labels, matrix, strict=True):
        print(f"{label[:12]:>12s} " + "".join(f"{value:12.3f}" for value in row))




#: The share of a sleeve's tracking variance the delivered exposure explains, for the two
#: sleeves whose tracking error this repository has **not** measured. The measured pair
#: disagree — AVLV 0.24, DFIV 0.82 — so the headline uses their mean and the low and high
#: readings are carried as a sensitivity rather than as a footnote.
RESIDUAL_SHARE_SETTINGS: Final[tuple[str, ...]] = ("low", "mean", "high")

#: The alternative constructions scored beside the candidate, each one change from it.
#: Their weights are capital weights; anything not listed keeps the candidate's weight
#: and anything set to zero is sold into the region's cheap core fund, which carries no
#: active position and therefore does not appear in the stack at all.
ALTERNATIVES: Final[Mapping[str, Mapping[str, float]]] = {
    "candidate": {"AVLV": 0.15, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.30},
    "AVLV 15 -> DFIV": {
        "AVLV": 0.0, "DFIV": 0.25, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.30,
    },
    "AVLV 15 -> AVES": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.20, "RSST-trend": 0.30,
    },
    "AVLV 15 -> IDMO": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.20, "AVES": 0.05, "RSST-trend": 0.30,
    },
    "AVLV 15 -> IDMO 10, core 5": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.15, "AVES": 0.05, "RSST-trend": 0.30,
    },
    "AVLV 15 split IDMO/AVES": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.125, "AVES": 0.125, "RSST-trend": 0.30,
    },
    "trend 30 -> 22, AVLV 15 -> IDMO 10": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.15, "AVES": 0.05, "RSST-trend": 0.22,
    },
    "AVLV 15 split DFIV/AVES": {
        "AVLV": 0.0, "DFIV": 0.175, "IDMO": 0.05, "AVES": 0.125, "RSST-trend": 0.30,
    },
    "AVLV 15 -> cheap core (VTI)": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.30,
    },
    "drop DFIV, hold VEA": {
        "AVLV": 0.15, "DFIV": 0.0, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.30,
    },
    "drop IDMO": {"AVLV": 0.15, "DFIV": 0.10, "IDMO": 0.0, "AVES": 0.05, "RSST-trend": 0.30},
    "drop AVES": {"AVLV": 0.15, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.0, "RSST-trend": 0.30},
    "trend 30 -> 22 (variance minimum)": {
        "AVLV": 0.15, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.22,
    },
    "trend 30 -> 22 and AVLV 15 -> core": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.22,
    },
    "drop the trend overlay": {
        "AVLV": 0.15, "DFIV": 0.10, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.0,
    },
    "priced weights (AVLV 20, DFIV 8)": {
        "AVLV": 0.20, "DFIV": 0.08, "IDMO": 0.05, "AVES": 0.05, "RSST-trend": 0.30,
    },
    "tilts only, DFIV 20 AVLV 10 AVES 10": {
        "AVLV": 0.10, "DFIV": 0.20, "IDMO": 0.0, "AVES": 0.10, "RSST-trend": 0.0,
    },
    "DFIV alone at 10, nothing else": {
        "AVLV": 0.0, "DFIV": 0.10, "IDMO": 0.0, "AVES": 0.0, "RSST-trend": 0.0,
    },
}

#: Which fitted alphas to charge. The **primary** setting is ``resolved``, and the rule is
#: stated before the numbers: charge an alpha when its own point estimate exceeds its own
#: detection floor, and leave it at zero otherwise. On this shelf exactly one qualifies —
#: DFIV's -3.80 pp/yr net of pedestal against a 3.52 floor.
#:
#: The rule has a bias and it must be named: **it penalises precisely the funds whose
#: instrument is good enough to measure them.** A fund with a short history and a wide
#: floor gets a free pass. ``all`` is therefore reported beside it, charging every point
#: estimate however unresolved, and ``none`` beside that. A change that improves the
#: candidate under all three is robust; one that improves it under one is a scenario.
ALPHA_SETTINGS: Final[tuple[str, ...]] = ("none", "resolved", "all")

_TILTS: Final[tuple[str, ...]] = ("AVLV", "DFIV", "IDMO", "AVES")
_ALL: Final[tuple[str, ...]] = (*_TILTS, "RSST-trend")


def _residual_correlation(
    labels: Sequence[str],
    model_correlation: Sequence[Sequence[float]],
    model_errors: Mapping[str, float],
    total_errors: Mapping[str, float],
) -> tuple[tuple[float, ...], ...]:
    """Rescale a factor-only correlation matrix for an uncorrelated fund residual.

    The residual is idiosyncratic by construction, so covariance is unchanged and only
    the diagonal grows: ``rho_ij_total = rho_ij_model * s_i_model * s_j_model /
    (s_i_total * s_j_total)``. Adding residual therefore always *lowers* every
    off-diagonal correlation, which raises ``1' R^-1 1`` — and that rise is not breadth,
    because the residual carries no edge. It is the clearest single reason effective
    breadth must be read beside a realised information ratio and never alone.
    """
    size = len(labels)
    out: list[tuple[float, ...]] = []
    for i in range(size):
        row = []
        for j in range(size):
            if i == j:
                row.append(1.0)
                continue
            covariance = (
                model_correlation[i][j] * model_errors[labels[i]] * model_errors[labels[j]]
            )
            row.append(covariance / (total_errors[labels[i]] * total_errors[labels[j]]))
        out.append(tuple(row))
    return tuple(out)


def _build_stack(
    weights: Mapping[str, float],
    edges: Mapping[str, float],
    errors: Mapping[str, float],
    correlation: Sequence[Sequence[float]],
    labels: Sequence[str],
) -> tuple[list[Sleeve], tuple[tuple[float, ...], ...]]:
    kept = [label for label in labels if weights.get(label, 0.0) > 0.0]
    index = {label: position for position, label in enumerate(labels)}
    sleeves = [
        Sleeve(label=label, weight=weights[label], edge=edges[label], tracking_error=errors[label])
        for label in kept
    ]
    sub = tuple(tuple(correlation[index[a]][index[b]] for b in kept) for a in kept)
    return sleeves, sub


def main() -> None:
    cache = RawCache(default_cache_root())
    factors = load_factors(cache)
    trend = load_trend(cache)
    specs = {spec.ticker: spec for spec in CANDIDATE_SLEEVES}

    series: dict[str, tuple[tuple[str, ...], FloatArray]] = {
        spec.ticker: synthetic_excess(factors[spec.region], spec.loadings)
        for spec in CANDIDATE_SLEEVES
    }
    series["RSST-trend"] = (
        tuple(sorted(trend)),
        np.asarray([trend[period] for period in sorted(trend)], dtype=np.float64),
    )

    print("=" * 100)
    print("STACKING AND EFFECTIVE BREADTH — a study, exploratory throughout, no ledger entry")
    print("=" * 100)
    print(f"\nLast month read {LAST_MONTH}. Sleeve excess = delivered loading vector x regional")
    print("factor returns. No residual, no market-beta difference and no alpha are modelled.")

    window, aligned = _align(series, _ALL)
    common = {label: values for label, values in zip(_ALL, aligned, strict=True)}
    print(f"\nCommon window: {len(window)} months, {window[0]}..{window[-1]}.")
    print("Every correlation and every model tracking error below is on that one window.")

    # ------------------------------------------------- 1. sleeves and tracking error
    measured = {
        ticker: PRICED_TILT_INPUTS[ticker].sleeve_tracking_error for ticker in ("AVLV", "DFIV")
    }
    model_errors = {label: annualised_volatility(common[label]) for label in _ALL}
    shares = {ticker: (model_errors[ticker] / measured[ticker]) ** 2 for ticker in measured}

    print("\n1. Tracking error per dollar of sleeve, pp/yr")
    print(f"{'sleeve':<13}{'model TE':>10}{'measured TE':>13}{'factor share':>14}  measured over")
    for ticker in _ALL:
        share = shares.get(ticker)
        print(
            f"{ticker:<13}{model_errors[ticker]:>10.3f}"
            f"{(f'{measured[ticker]:.3f}' if ticker in measured else '—'):>13}"
            f"{(f'{share:.3f}' if share else '—'):>14}"
            f"  {'51 fund months, 2020-2025' if ticker in measured else 'not measured here'}"
        )
    print(
        "\n   The two measured shares disagree by a factor of three. AVLV's delivered\n"
        "   exposure explains under a third of its tracking variance against VTI and\n"
        "   DFIV's explains four fifths, so the two unmeasured sleeves are carried at\n"
        "   the low, mean and high reading and all three are reported."
    )

    settings = {
        "low": min(shares.values()),
        "mean": float(np.mean(list(shares.values()))),
        "high": max(shares.values()),
    }

    # -------------------------------------------------------- 2. correlation matrices
    model_correlation = correlation_matrix([common[label] for label in _ALL])
    print(f"\n2. Correlation of the modelled excess returns, n={len(window)}")
    _print_matrix(_ALL, model_correlation)
    off = [
        model_correlation[i][j] for i in range(len(_ALL)) for j in range(i + 1, len(_ALL))
    ]
    print(f"   mean off-diagonal rho {np.mean(off):+.3f}; "
          f"SE on one correlation near zero {1 / math.sqrt(len(window)):.3f}")

    value_only = correlation_matrix([common[label] for label in ("AVLV", "DFIV", "AVES")])
    tilt_only = correlation_matrix([common[label] for label in _TILTS])
    print(f"\n   1'R^-1 1, three value tilts       {effective_bets(value_only):>6.2f} of 3")
    print(f"   1'R^-1 1, four long-only tilts    {effective_bets(tilt_only):>6.2f} of 4")
    print(f"   1'R^-1 1, four tilts plus trend   {effective_bets(model_correlation):>6.2f} of 5")

    # ------------------------------------------- 3. the wider question: sixteen engines
    wide: dict[str, tuple[tuple[str, ...], FloatArray]] = {}
    for region in ("us", "exus", "em"):
        for factor in ("HML", "SMB", "RMW", "CMA", "UMD"):
            keys = tuple(sorted(factors[region][factor]))
            wide[f"{region}:{factor}"] = (
                keys,
                np.asarray([factors[region][factor][k] for k in keys], dtype=np.float64),
            )
    wide["trend"] = series["RSST-trend"]
    wide_labels = tuple(wide)
    wide_window, wide_aligned = _align(wide, wide_labels)
    wide_correlation = correlation_matrix(wide_aligned)
    wide_off = [
        wide_correlation[i][j]
        for i in range(len(wide_labels))
        for j in range(i + 1, len(wide_labels))
    ]
    print(
        f"\n3. Stack everything the library holds: five French factors in three regions\n"
        f"   plus trend, long-short and gross, n={len(wide_window)} "
        f"{wide_window[0]}..{wide_window[-1]}"
    )
    print(f"   mean off-diagonal rho {np.mean(wide_off):+.3f}")
    print(
        f"   1'R^-1 1 = {effective_bets(wide_correlation):.2f} of {len(wide_labels)}. "
        "Sixteen paper strategies are worth about ten."
    )
    for name, keys in (
        ("HML, three regions", ("us:HML", "exus:HML", "em:HML")),
        ("UMD, three regions", ("us:UMD", "exus:UMD", "em:UMD")),
        (
            "one region, five factors (US)",
            tuple(f"us:{name}" for name in ("HML", "SMB", "RMW", "CMA", "UMD")),
        ),
    ):
        _, arrays = _align(wide, keys)
        sub = correlation_matrix(arrays)
        print(f"   1'R^-1 1, {name:<30} {effective_bets(sub):>6.2f} of {len(keys)}")

    # ------------------------------------------------------- 4. the candidate, priced
    costs = {
        "AVLV": PRICED_TILT_INPUTS["AVLV"].incremental_cost,
        "DFIV": PRICED_TILT_INPUTS["DFIV"].incremental_cost,
        "IDMO": specs["IDMO"].incremental_cost,
        "AVES": specs["AVES"].incremental_cost,
    }
    print("\n4. Incremental cost, pp/yr per dollar of sleeve: " + ", ".join(
        f"{k} {v:.3f}" for k, v in costs.items()
    ))
    print("\n   Sleeve edge by premium scenario, pp/yr per dollar of sleeve")
    print(f"{'sleeve':<13}" + "".join(f"{name:>12}" for name in PREMIUM_SCENARIOS))
    edges_by_scenario: dict[str, dict[str, float]] = {}
    for scenario, premia in PREMIUM_SCENARIOS.items():
        edges_by_scenario[scenario] = {
            ticker: sleeve_edge_from_premia(
                specs[ticker].loadings, premia[specs[ticker].region], costs[ticker]
            )
            for ticker in _TILTS
        }
    for ticker in _TILTS:
        print(
            f"{ticker:<13}"
            + "".join(f"{edges_by_scenario[s][ticker]:>12.3f}" for s in PREMIUM_SCENARIOS)
        )

    print("\n5. The candidate stack. Benchmark: the same regional split held in the cheap")
    print("   core funds, unlevered. Trend enters as financed notional, so its whole")
    print("   volatility is tracking error against that benchmark.")
    for setting in RESIDUAL_SHARE_SETTINGS:
        share = settings[setting]
        total_errors = {
            ticker: measured.get(ticker, model_errors[ticker] / math.sqrt(share))
            for ticker in _TILTS
        }
        total_errors["RSST-trend"] = model_errors["RSST-trend"]
        correlation = _residual_correlation(_ALL, model_correlation, model_errors, total_errors)
        print(
            f"\n   residual setting {setting!r}: unmeasured factor share {share:.3f}; "
            f"IDMO TE {total_errors['IDMO']:.2f}, AVES TE {total_errors['AVES']:.2f} pp/yr; "
            f"1'R^-1 1 = {effective_bets(correlation):.2f} of 5"
        )
        if setting != "mean":
            continue
        _print_matrix(_ALL, correlation)
        for scenario in PREMIUM_SCENARIOS:
            edges = dict(edges_by_scenario[scenario])
            for trend_excess in TREND_NET_EXCESS_SCENARIOS:
                edges["RSST-trend"] = trend_excess
                sleeves, sub = _build_stack(
                    ALTERNATIVES["candidate"], edges, total_errors, correlation, _ALL
                )
                verdict = stack(sleeves, sub)
                print(
                    f"   {scenario:<10} trend {trend_excess:>4.1f}  "
                    f"edge {100 * verdict.edge:>6.1f} bp"
                    f"  TE {100 * verdict.tracking_error:>5.0f} bp"
                    f"  IR {verdict.information_ratio:>6.3f}"
                    f"  P10 {verdict.probability(10):.3f}"
                    f"  P20 {verdict.probability(20):.3f}"
                    f"  P30 {verdict.probability(30):.3f}"
                )

    share = settings["mean"]
    total_errors = {
        ticker: measured.get(ticker, model_errors[ticker] / math.sqrt(share))
        for ticker in _TILTS
    }
    total_errors["RSST-trend"] = model_errors["RSST-trend"]
    correlation = _residual_correlation(_ALL, model_correlation, model_errors, total_errors)

    # ------------------------------------------------------------ 6. marginal verdicts
    print("\n6. What each sleeve adds to the rest of the stack, own-panel premia, trend +1.0")
    edges = dict(edges_by_scenario["own-panel"])
    edges["RSST-trend"] = 1.0
    index = {label: position for position, label in enumerate(_ALL)}
    print(
        f"{'sleeve':<13}{'weight':>8}{'edge':>8}{'IR alone':>10}{'beta':>8}"
        f"{'alpha':>8}{'resid TE':>10}{'appraisal':>11}{'conditioning':>14}"
        f"{'IR before':>11}{'IR after':>10}"
    )
    for ticker in _ALL:
        others = {k: v for k, v in ALTERNATIVES["candidate"].items() if k != ticker}
        kept = [label for label in _ALL if others.get(label, 0.0) > 0.0]
        held_sleeves, held_sub = _build_stack(others, edges, total_errors, correlation, _ALL)
        held = stack(held_sleeves, held_sub)
        weights = np.asarray([others[label] for label in kept])
        cross = np.asarray(
            [
                correlation[index[ticker]][index[label]]
                * total_errors[ticker]
                * total_errors[label]
                for label in kept
            ]
        )
        held_correlation = float(weights @ cross) / (
            total_errors[ticker] * held.tracking_error
        )
        candidate = Sleeve(
            label=ticker,
            weight=ALTERNATIVES["candidate"][ticker],
            edge=edges[ticker],
            tracking_error=total_errors[ticker],
        )
        marginal = marginal_contribution(
            label=ticker,
            candidate=candidate,
            held_edge=held.edge,
            held_tracking_error=held.tracking_error,
            correlation_to_held=held_correlation,
        )
        print(
            f"{ticker:<13}{candidate.weight:>8.2f}{candidate.edge:>8.3f}"
            f"{candidate.information_ratio:>10.3f}{marginal.beta:>8.3f}{marginal.alpha:>8.3f}"
            f"{marginal.residual_tracking_error:>10.3f}{marginal.appraisal_ratio:>11.3f}"
            f"{marginal.appraisal_ratio - candidate.information_ratio:>14.3f}"
            f"{marginal.information_ratio_before:>11.3f}"
            f"{marginal.information_ratio_after:>10.3f}"
        )
    print(
        "\n   A negative-edge sleeve earns its place when beta is negative enough that\n"
        "   alpha stays positive; a positive-edge sleeve earns nothing when alpha is zero.\n"
        "\n   READ THE 'conditioning' COLUMN. It is appraisal minus standalone IR, which is\n"
        "   EXACTLY zero when a sleeve is uncorrelated with everything else held. In this\n"
        "   portfolio it is small and mostly NEGATIVE, so the marginal verdict and the\n"
        "   standalone verdict nearly coincide and no sleeve here is rescued or condemned\n"
        "   by the company it keeps. The 'works alone, fails in a portfolio' effect is real\n"
        "   arithmetic and it is NOT what is happening in this construction."
    )

    # ------------------------------------------- 7. the edge is estimated, not known
    print("\n7. The same stack with the premia treated as ESTIMATED rather than known")
    print("   tau_i = sum_k |h_ik| * SE(premium_k); the portfolio tau is bracketed by")
    print("   independent premium errors (quadrature) and perfectly correlated ones (sum).")
    sleeve_tau = {}
    for ticker in _TILTS:
        region = specs[ticker].region
        sleeve_tau[ticker] = sum(
            abs(loading) * PREMIUM_MDE80[region][name] / MDE_TO_STANDARD_ERROR
            for name, loading in specs[ticker].loadings.items()
        )
    sleeve_tau["RSST-trend"] = TREND_EDGE_STANDARD_ERROR
    signable = {
        ticker: confidence_ceiling(
            edge=edges[ticker], edge_standard_error=sleeve_tau[ticker]
        )
        for ticker in _ALL
    }
    print(f"{'sleeve':<13}{'edge':>8}{'tau':>8}{'P(edge>0)':>12}")
    for ticker in _ALL:
        print(
            f"{ticker:<13}{edges[ticker]:>8.3f}{sleeve_tau[ticker]:>8.3f}"
            f"{signable[ticker]:>12.3f}"
        )
    weights_map = ALTERNATIVES["candidate"]
    contributions = {t: weights_map[t] * sleeve_tau[t] for t in _ALL}
    tau_low = math.sqrt(sum(value**2 for value in contributions.values()))
    tau_high = sum(contributions.values())
    sleeves, sub = _build_stack(weights_map, edges, total_errors, correlation, _ALL)
    verdict = stack(sleeves, sub)
    print(
        f"\n   portfolio edge {100 * verdict.edge:.1f} bp,"
        f" TE {100 * verdict.tracking_error:.0f} bp,"
        f" tau between {100 * tau_low:.0f} and {100 * tau_high:.0f} bp"
    )
    print(f"{'premium error':<20}{'P10':>8}{'P20':>8}{'P30':>8}{'P(edge>0)':>12}")
    print(
        f"{'known (the flaw)':<20}"
        + "".join(f"{verdict.probability(t):>8.3f}" for t in (10, 20, 30))
        + f"{'1.000':>12}"
    )
    for name, tau in (("independent", tau_low), ("perfectly correlated", tau_high)):
        row = "".join(
            f"{probability_with_parameter_uncertainty(
                edge=verdict.edge,
                edge_standard_error=tau,
                tracking_error=verdict.tracking_error,
                horizon_years=horizon,
            ):>8.3f}"
            for horizon in (10, 20, 30)
        )
        print(
            f"{name:<20}{row}"
            f"{confidence_ceiling(edge=verdict.edge, edge_standard_error=tau):>12.3f}"
        )

    # ------------------------------------ 7b. does the overlay's variance term rescue it?
    blend = {"us": 0.65, "exus": 0.25, "em": 0.10}
    market_window = common_window(
        [tuple(sorted(factors[region]["Mkt-RF"])) for region in blend]
        + [tuple(sorted(factors[region]["RF"])) for region in blend]
        + [series["RSST-trend"][0]]
    )
    equity = np.asarray(
        [
            sum(
                share * (factors[region]["Mkt-RF"][period] + factors[region]["RF"][period])
                for region, share in blend.items()
            )
            for period in market_window
        ],
        dtype=np.float64,
    )
    trend_lookup = dict(zip(series["RSST-trend"][0], series["RSST-trend"][1], strict=True))
    trend_aligned = np.asarray([trend_lookup[period] for period in market_window])
    equity_volatility = annualised_volatility(equity)
    trend_correlation = float(np.corrcoef(equity, trend_aligned)[0][1])
    covariance = trend_correlation * equity_volatility * annualised_volatility(trend_aligned)
    print(
        f"\n7b. The geometric term the probability calculation leaves out, for a FINANCED\n"
        f"    overlay — nothing is sold, so the base's variance stays. n={len(market_window)} "
        f"{market_window[0]}..{market_window[-1]}"
    )
    print(
        f"   65/25/10 equity blend volatility {equity_volatility:.2f} pp/yr; "
        f"correlation to trend {trend_correlation:+.3f}"
    )
    for notional in (0.10, 0.20, 0.30, 0.50):
        variance_change = (
            2 * notional * covariance + notional**2 * annualised_volatility(trend_aligned) ** 2
        )
        print(
            f"   trend notional {notional:.0%}: portfolio variance change "
            f"{variance_change:>+7.2f} pp^2/yr, growth effect "
            f"{-variance_change / (2 * PERCENT):>+6.3f} pp/yr"
        )
    trend_volatility = annualised_volatility(trend_aligned)
    minimising = -covariance / trend_volatility**2
    print(
        f"\n   *** VARIANCE IS MINIMISED AT {minimising:.1%} OF NOTIONAL AND THE CANDIDATE\n"
        f"   *** HOLDS 30%. This result needs no benchmark, no premium and no forecast:\n"
        f"   *** w* = -rho * sigma_equity / sigma_trend, three measured numbers."
    )
    standard_error = 1.0 / math.sqrt(len(market_window))
    print(
        f"\n   Sensitivity. SE on rho is 1/sqrt(n) = {standard_error:.3f}, so the 95%\n"
        f"   interval on rho is [{trend_correlation - 1.96 * standard_error:+.3f}, "
        f"{trend_correlation + 1.96 * standard_error:+.3f}] and w* moves with it:"
    )
    print(f"{'rho':>10}{'w* notional':>14}  note")
    for label, rho_value in (
        ("-1.96 SE", trend_correlation - 1.96 * standard_error),
        ("point", trend_correlation),
        ("+1.96 SE", trend_correlation + 1.96 * standard_error),
        ("Exp 004", -0.17),
        ("crisis", -0.59),
        ("zero", 0.0),
    ):
        star = -rho_value * equity_volatility / trend_volatility
        note = {
            "-1.96 SE": "the candidate's 30% sits INSIDE this bound",
            "Exp 004": "the vendor series against a 60/40 base, 432 months",
            "crisis": "conditional on equity drawdowns; 53 months, ~4.4 effective",
            "zero": "no covariance benefit at all: any notional adds variance",
        }.get(label, "")
        print(f"{label:>10}{star:>13.1%}  rho={rho_value:+.3f} {note}")
    print(
        "\n   Read that honestly: the POINT estimate says 22% and the upper end of rho's own\n"
        "   95% interval says 33%, so 30% is not outside what this instrument can support.\n"
        "   What the instrument does say is that 30% is past the centre of the admissible\n"
        "   range rather than inside it, and that the marginal unit of trend at 30% is\n"
        "   adding variance rather than removing it under the central estimate."
    )
    print(
        "\n   Note how much smaller the whole credit is than the pro-rata credit of\n"
        "   w * sigma_p^2 * (1 - beta): a substitution sells the base and removes its\n"
        "   variance, an overlay keeps both the variance and the return. That difference\n"
        "   IS the funding-rule gap, seen from the variance side."
    )

    # --------------------------------------------- 7c. the alpha nobody can explain
    print("\n7c. Fitted alpha, net of each panel's pedestal, with the charging rule")
    print("   RULE, stated before the numbers: charge an alpha when its own point estimate")
    print("   exceeds its own detection floor. Exactly one on this shelf qualifies.")
    print(f"{'fund':<8}{'alpha':>9}{'floor':>8}{'charged under resolved':>25}")
    for ticker in _TILTS:
        alpha, floor = ALPHA_NET_OF_PEDESTAL[ticker]
        verdict_word = "yes" if abs(alpha) > floor else "no"
        print(f"{ticker:<8}{alpha:>9.2f}{floor:>8.2f}{verdict_word:>25}")
    print(
        "\n   The rule's bias, named: it charges the fund we can measure and forgives the\n"
        "   ones we cannot. That is why 'all' is reported beside it everywhere below."
    )

    # -------------------------------------------------------- 8. funding, and dilution
    print("\n8. The funding ceiling, own-panel premia, pp/yr of portfolio")
    tilt_edges = [edges_by_scenario["own-panel"][t] for t in _TILTS]
    best_single = portfolio_edge_ceiling(
        tilt_edges, rule="substitution", total_weight=0.35
    )
    print(
        f"   substitution, all 35% of tilted capital in the best tilt  "
        f"{100 * best_single:>7.1f} bp"
    )
    print(
        f"   overlay, 35% of notional in EACH of the four              "
        f"{100 * portfolio_edge_ceiling(tilt_edges, rule='overlay', total_weight=0.35):>7.1f} bp"
    )
    held_edge = sum(
        ALTERNATIVES["candidate"][t] * edges_by_scenario["own-panel"][t] for t in _TILTS
    )
    print(
        f"   the candidate's four tilts as actually weighted           "
        f"{100 * held_edge:>7.1f} bp"
    )

    # ------------------------------------------------------- 8. alternative constructions
    print("\n9. One change at a time, own-panel premia, trend net excess +1.0 pp/yr.")
    print("   PRIMARY reading is 'resolved': DFIV's -3.80 alpha charged, the other three")
    print("   left at zero because none clears its own floor. A change is ROBUST only if it")
    print("   beats the candidate's 30-year probability under all three alpha settings.")

    def edges_under(setting: str) -> dict[str, float]:
        out = dict(edges)
        for ticker in _TILTS:
            alpha, floor = ALPHA_NET_OF_PEDESTAL[ticker]
            if setting == "all" or (setting == "resolved" and abs(alpha) > floor):
                out[ticker] = edges[ticker] + alpha
        return out

    edge_sets = {setting: edges_under(setting) for setting in ALPHA_SETTINGS}
    print("\n   sleeve edge, pp/yr per dollar of sleeve, by alpha setting")
    print(f"{'sleeve':<13}" + "".join(f"{setting:>12}" for setting in ALPHA_SETTINGS))
    for ticker in _ALL:
        print(
            f"{ticker:<13}"
            + "".join(f"{edge_sets[setting][ticker]:>12.3f}" for setting in ALPHA_SETTINGS)
        )

    scored: dict[str, dict[str, tuple[float, float, float, float]]] = {}
    for setting in ALPHA_SETTINGS:
        scored[setting] = {}
        for name, weights_of in ALTERNATIVES.items():
            sleeves, sub = _build_stack(
                weights_of, edge_sets[setting], total_errors, correlation, _ALL
            )
            verdict = stack(sleeves, sub)
            tau = sum(weights_of.get(t, 0.0) * sleeve_tau[t] for t in _ALL)
            estimated = probability_with_parameter_uncertainty(
                edge=verdict.edge,
                edge_standard_error=tau,
                tracking_error=verdict.tracking_error,
                horizon_years=30,
            )
            scored[setting][name] = (
                verdict.edge,
                verdict.tracking_error,
                verdict.information_ratio,
                estimated,
            )

    header = "".join(f"{setting + ' P30':>13}" for setting in ALPHA_SETTINGS)
    print(
        f"\n{'construction':<36}{'edge bp':>9}{'TE bp':>7}{'IR':>7}{'bets':>7}"
        + header
        + f"{'robust':>8}"
    )
    for name, weights_of in ALTERNATIVES.items():
        primary = scored["resolved"][name]
        sleeves, sub = _build_stack(
            weights_of, edge_sets["resolved"], total_errors, correlation, _ALL
        )
        bets = stack(sleeves, sub).effective_bets
        beats = all(
            scored[setting][name][3] >= scored[setting]["candidate"][3] - 1e-12
            for setting in ALPHA_SETTINGS
        )
        flag = "-" if name == "candidate" else ("yes" if beats else "no")
        print(
            f"{name:<36}{100 * primary[0]:>9.1f}{100 * primary[1]:>7.0f}"
            f"{primary[2]:>7.3f}{bets:>7.2f}"
            + "".join(f"{scored[setting][name][3]:>13.3f}" for setting in ALPHA_SETTINGS)
            + f"{flag:>8}"
        )
    print(
        "\n   'AVLV 15 -> DFIV' is the change this study first proposed. Read its row:\n"
        "   it wins only under 'none'. Concentrating capital into the one fund whose\n"
        "   negative alpha is statistically resolved is the opposite of robust, and the\n"
        "   recommendation is WITHDRAWN. Under the primary reading 'DFIV alone at 10' is a\n"
        "   LOSING bet: -4.5 bp of edge and a 30-year probability of 0.398."
    )
    print(
        "\n   'drop the trend overlay' must not be read off this table. Against an EQUITY\n"
        "   benchmark a 12.4 pp/yr financed sleeve is nearly all tracking error, which is\n"
        "   what that row shows. Against the comparator trend is actually held for, the\n"
        "   repository's own frozen results are: Experiment 004, a 15% sleeve in a 60/40\n"
        "   base against a RISK-MATCHED cash comparator, +1.312 pp/yr of geometric growth\n"
        "   95% [+0.759, +1.916], falling to +0.883 [-0.175, +2.165] post-publication; and\n"
        "   Experiment 010b, a 10% sleeve in a global equity core, +0.258 pp/yr of growth\n"
        "   against a 0.30 threshold with a +1.172 certainty equivalent beside it. Neither\n"
        "   is a figure at 30% of notional and this study does not supply one."
    )

    # -------------------------------------- 9c. what the recommendation costs in tax
    print("\n9c. The charge this study does NOT make, and it points the other way")
    print("   Deferral of unrealised gain plus the section 1014 step-up is worth a")
    print("   horizon-free 1.62 pp/yr in a taxable account (expected-edge decomposition")
    print("   section 1). It is a HURDLE any turnover-bearing sleeve must clear, and none")
    print("   of it is charged above. IDMO files 105%/yr of turnover against VEA's 4%.")
    print(f"{'IDMO weight':>13}{'upper-bound tax hurdle on that weight':>40}")
    for weight in (0.05, 0.10, 0.15, 0.20):
        print(f"{weight:>13.0%}{100 * weight * 1.62:>34.1f} bp")
    print(
        "\n   That is an UPPER bound: it assumes the sleeve forfeits the whole deferral\n"
        "   benefit, which a fund with in-kind creation and redemption does not. But at a\n"
        "   15% or 20% weight it is the same order as the edge the swap buys, it lands\n"
        "   only in a taxable account, and it is the reason this study recommends the\n"
        "   partial move rather than the whole one."
    )

    # -------------------------------------- 9b. reconciling the two readings of AVLV
    print("\n9b. Why AVLV reads +24.4 bp in the recommendation and 0.053 of appraisal here")
    published = Sleeve(
        label="AVLV at 20% on the pooled premium, HML leg only",
        weight=0.20,
        edge=(
            PRICED_TILT_INPUTS["AVLV"].fund_hml_loading
            - PRICED_TILT_INPUTS["AVLV"].benchmark_hml_loading
        )
        * PREMIUM_SCENARIOS["pooled"]["us"]["HML"]
        - PRICED_TILT_INPUTS["AVLV"].incremental_cost,
        tracking_error=PRICED_TILT_INPUTS["AVLV"].sleeve_tracking_error,
    )
    print(
        f"   reproduced published line: {100 * published.weight * published.edge:>5.1f} bp "
        f"of portfolio edge against "
        f"{100 * published.weight * published.tracking_error:>5.0f} bp of tracking error, "
        f"standalone IR {published.information_ratio:.3f}"
    )
    print("\n   The same fund, two channels, separated:")
    for scenario in ("pooled", "own-panel"):
        scenario_edges = dict(edges_by_scenario[scenario])
        scenario_edges["RSST-trend"] = 1.0
        others = {k: v for k, v in ALTERNATIVES["candidate"].items() if k != "AVLV"}
        kept = [label for label in _ALL if others.get(label, 0.0) > 0.0]
        held_sleeves, held_sub = _build_stack(
            others, scenario_edges, total_errors, correlation, _ALL
        )
        held = stack(held_sleeves, held_sub)
        weights = np.asarray([others[label] for label in kept])
        cross = np.asarray(
            [
                correlation[index["AVLV"]][index[label]]
                * total_errors["AVLV"]
                * total_errors[label]
                for label in kept
            ]
        )
        rho_held = float(weights @ cross) / (total_errors["AVLV"] * held.tracking_error)
        avlv = Sleeve(
            label="AVLV",
            weight=0.15,
            edge=scenario_edges["AVLV"],
            tracking_error=total_errors["AVLV"],
        )
        marginal = marginal_contribution(
            label="AVLV",
            candidate=avlv,
            held_edge=held.edge,
            held_tracking_error=held.tracking_error,
            correlation_to_held=rho_held,
        )
        print(
            f"   {scenario:<10} standalone edge {avlv.edge:>6.3f} pp/yr, standalone IR "
            f"{avlv.information_ratio:>6.3f}, appraisal inside the candidate "
            f"{marginal.appraisal_ratio:>6.3f}"
        )
    pooled_ir = edges_by_scenario["pooled"]["AVLV"] / total_errors["AVLV"]
    own_ir = edges_by_scenario["own-panel"]["AVLV"] / total_errors["AVLV"]
    print(
        f"\n   premium channel: standalone IR {pooled_ir:.3f} -> {own_ir:.3f}, a factor of "
        f"{pooled_ir / own_ir:.1f}\n"
        "   conditioning channel: appraisal minus standalone IR, +0.006 on either premium\n"
        "   The two readings differ almost entirely because of WHICH PREMIUM IS BELIEVED,\n"
        "   not because of the portfolio around the fund."
    )

    # ---------------------------------------------------------- 9. the thesis, priced
    print("\n10. The thesis: P(stack ahead) when each sleeve alone is 55% likely")
    counts = (1, 2, 3, 5, 10, 25, 100)
    print(f"{'rho':>6}" + "".join(f"{k:>9}" for k in counts) + f"{'k -> inf':>10}")
    for rho in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        row = "".join(
            f"{equicorrelated_probability(single_probability=0.55, count=k, correlation=rho):>9.3f}"
            for k in counts
        )
        limit = (
            f"{stacking_ceiling_probability(single_probability=0.55, correlation=rho):>10.3f}"
            if rho > 0
            else f"{'1.000':>10}"
        )
        print(f"{rho:>6.1f}{row}{limit}")

    # ---------------------------------------------------------------- 10. resolution
    print("\n11. Resolution of the instrument, on the common window")
    for label in _ALL:
        estimate = hac_mean(common[label])
        annual_error = MONTHS_PER_YEAR * estimate.standard_error
        print(
            f"   {label:<12} in-sample mean {MONTHS_PER_YEAR * estimate.mean:>7.3f} pp/yr,"
            f"  MDE80 {minimum_detectable_effect(annual_error):>6.3f} pp/yr"
        )
    print(
        "\n   Every in-sample mean above describes this window and forecasts nothing.\n"
        "   The edges in sections 4 to 9 come from PREMIUM_SCENARIOS, never from here."
    )


if __name__ == "__main__":
    main()
