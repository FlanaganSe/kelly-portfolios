"""Regenerates the value-tilt tables in ``docs/research/portfolio-recommendation.md`` §5
and the double-counting section of ``docs/research/long-only-capture.md``.

Kept separate from :mod:`portfolio_edge.studies.value_tilt` so the study stays pure and
testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.value_tilt

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen. The loadings are Experiment 013's, read from its committed artifact rather
than re-estimated; the premia are Experiments 001 and 005's; the fees and the portfolio
turnover rates are read from each fund's own SEC filing; and the identity check below is
computed here from Ken French's six portfolios.

Three things are computed and only the first is a proof
--------------------------------------------------------
*The identity.* ``capture = h + residue`` on Experiment 007's own primary definition,
from its own file, on its own months. It holds to floating point, which settles whether
``loading x capture`` double counts.

*The panel.* Each of the nine systematic value and small-value products Experiment 013
admitted, with its measured HML loading, its filed fee and portfolio turnover, and its
realised tracking error against VTI over **its own** estimation window.

*The corners.* The tilt's edge, growth contribution, certainty equivalent and terminal
wealth multiple at three weights and three premia. The premia disagree by a factor of
three and one of them is not reliably signed; the table reports all of them rather than
choosing.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from portfolio_edge.core.costs import K_FLOOR, K_PESSIMISTIC
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_001_factor_decay import minimum_detectable_effect
from portfolio_edge.experiments.exp_002_fund_exposure import fetch_fund_series
from portfolio_edge.experiments.exp_002_universe import resolve_ticker, workspace_root
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.studies.outperformance_horizon import (
    horizon_for_confidence,
    probability_of_outperformance,
)
from portfolio_edge.studies.value_tilt import (
    TiltInputs,
    capture_from_regression,
    tilt_verdict,
)

MONTHS_PER_YEAR: Final = 12
HAC_LAGS: Final = 6
"""Experiment 013's lag count, kept so the loadings here are comparable to its."""

WINDOW_START: Final = "2020-01"
WINDOW_END: Final = "2025-12"
"""Experiment 013's frozen sample policy. Months after it are held out there and here."""

CAPTURE_START: Final = "1963-07"
CAPTURE_END: Final = "2025-12"
"""Experiment 007's primary era for the size-neutral capture fraction."""

EXP_013_RUN_ID: Final = "2b8cc7f73aef4d8abee68b7abcde9c1c"
"""The Experiment 013 run whose published exposures this module reads."""

SIX_PORTFOLIOS: Final = (
    "SMALL LoBM",
    "ME1 BM2",
    "SMALL HiBM",
    "BIG LoBM",
    "ME2 BM2",
    "BIG HiBM",
)

FACTORS: Final = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom")

# --------------------------------------------------------------------------------
# Product facts read from SEC filings. Every one carries its form and the date read.
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FiledFacts:
    """What a fund's own summary prospectus says, with the filing that says it."""

    net_expense_ratio_percent: float
    portfolio_turnover_percent: float
    filing: str


FILED: Final[Mapping[str, FiledFacts]] = {
    "VTI": FiledFacts(0.03, 3.0, "485BPOS 2025-12-31, accession 0000036405-26-000181"),
    "VBR": FiledFacts(0.05, 25.0, "485BPOS 2025-12-31, accession 0000036405-26-000181"),
    "AVUV": FiledFacts(0.25, 6.0, "497K 2025-12-31, accession 0001710607-25-000416"),
    "AVSC": FiledFacts(0.25, 5.0, "497K 2025-12-31, accession 0001710607-25-000415"),
    "AVLV": FiledFacts(0.15, 7.0, "497K 2025-12-31, accession 0001710607-25-000411"),
    "DFAS": FiledFacts(0.26, 6.0, "497K 2026-02-27, accession 0001816125-26-000081"),
    "DFAT": FiledFacts(0.28, 9.0, "497K 2026-02-27, accession 0001816125-26-000084"),
    "DFSV": FiledFacts(0.30, 9.0, "497K 2026-02-27, accession 0001816125-26-000071"),
    "DFUV": FiledFacts(0.21, 5.0, "497K 2026-02-27, accession 0001816125-26-000077"),
    "DFLV": FiledFacts(0.21, 5.0, "497K 2026-02-27, accession 0001816125-26-000061"),
    "RPV": FiledFacts(0.35, 42.0, "497K 2025-08-28, accession 0001193125-25-190419"),
}
"""Net expense ratio and the Item 3 portfolio turnover rate, `as of 2026-08-17`.

The turnover rate is the fund's most recent fiscal year and is the SEC definition,
``min(purchases, sales) / average net assets``, which excludes an ETF's in-kind
creations and redemptions. Experiment 007 **assumed** 20-40%/yr for an annual
book-to-market reconstitution; eight of the nine systematic products file 5-9%.
"""

PANEL: Final = ("AVUV", "AVSC", "AVLV", "DFAS", "DFAT", "DFSV", "DFUV", "DFLV", "RPV", "VBR")

BENCHMARK: Final = "VTI"


@dataclass(frozen=True, slots=True)
class Premium:
    """One HML premium, with the window and the interval that decide how to read it."""

    label: str
    point: float
    low: float
    high: float
    window: str
    source: str
    reliably_signed: bool


PREMIA: Final[tuple[Premium, ...]] = (
    Premium(
        "pooled post-publication, three regions",
        4.74,
        1.46,
        8.10,
        "1994-01..2025-12, 384 months",
        "Experiment 005, joint cross-region block bootstrap",
        True,
    ),
    Premium(
        "US full sample",
        3.45,
        float("nan"),
        float("nan"),
        "1963-07..2025-12, 750 months",
        "computed here from the same French file Experiment 007 pins",
        True,
    ),
    Premium(
        "US post-publication",
        1.57,
        -2.28,
        5.54,
        "1994-01..2025-12, 384 months",
        "Experiment 001, MDE80 5.03, BH p 0.402",
        False,
    ),
)


# --------------------------------------------------------------------------------
# 1. The identity, from French's own six portfolios
# --------------------------------------------------------------------------------


def _number(value: object) -> float:
    """One cell of a frame as a float.

    ``pandas`` cannot promise a scalar from ``frame.loc[row, column]`` at type-check
    time, so the narrowing happens once here instead of at every call site.
    """
    return float(value)  # type: ignore[arg-type]


def _months(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Rows whose month label lies in ``[start, end]``, by comparison rather than slice.

    A label slice would type as an integer slice and would silently include a month the
    caller did not ask for if the index were ever unsorted.
    """
    labels = frame.index.astype(str)
    return frame.loc[(labels >= start) & (labels <= end)]


def _table(cache: RawCache, dataset_id: str, table_id: str) -> pd.DataFrame:
    dataset = french.get_dataset(dataset_id)
    entry = cache.require(dataset.url)
    frame = french.parse(cache, entry, dataset=dataset).table(table_id).to_frame()
    frame.index = pd.Index([str(label) for label in frame.index])
    return frame


def french_panel(cache: RawCache) -> pd.DataFrame:
    """The six 2x3 portfolios joined to FF5 and momentum on their month labels."""
    six = _table(cache, "french_us_6_portfolios_2x3", "average_value_weighted_returns_monthly")
    ff5 = _table(cache, "french_us_ff5", "monthly")
    momentum = _table(cache, "french_us_momentum", "monthly")
    return six.join(ff5, how="inner").join(momentum, how="inner")


def capture_identity(panel: pd.DataFrame) -> dict[str, object]:
    """Experiment 007's primary capture fraction, and the regression that explains it.

    ``L = 0.5 (SH + BH)`` and the benchmark is the equal-weighted six, which is
    Experiment 007's ``value_halves_vs_size_neutral`` definition verbatim.
    """
    window = _months(panel, CAPTURE_START, CAPTURE_END)
    small_low, _, small_high, big_low, _, big_high = (window[name] for name in SIX_PORTFOLIOS)
    reconstructed = 0.5 * (small_high + big_high) - 0.5 * (small_low + big_low)
    residual = float((reconstructed - window["HML"]).abs().max()) * 100.0

    long_leg = 0.5 * (small_high + big_high)
    benchmark = window[list(SIX_PORTFOLIOS)].mean(axis=1)
    spread = long_leg - benchmark

    design = window[list(FACTORS)].to_numpy()
    fit = hac_ols(spread.to_numpy(), design, n_lags=HAC_LAGS)
    names = ("alpha", *FACTORS)
    coefficients = dict(zip(names, fit.coefficients.tolist(), strict=True))
    standard_errors = dict(zip(names, fit.standard_errors.tolist(), strict=True))

    means = {name: float(window[name].mean()) * 100.0 * MONTHS_PER_YEAR for name in FACTORS}
    decomposition = capture_from_regression(
        hml_loading=coefficients["HML"],
        alpha=coefficients["alpha"] * 100.0 * MONTHS_PER_YEAR,
        other_loadings={name: coefficients[name] for name in FACTORS if name != "HML"},
        factor_means=means,
        hml_premium=means["HML"],
    )
    direct = float(spread.mean()) / float(window["HML"].mean())
    return {
        "months": len(window),
        "reconstruction_max_abs_residual_pp_per_month": residual,
        "capture_direct_ratio": direct,
        "capture_from_identity": decomposition.capture,
        "identity_error": decomposition.capture - direct,
        "hml_loading": decomposition.hml_loading,
        "hml_loading_se": standard_errors["HML"],
        "hml_loading_t": coefficients["HML"] / standard_errors["HML"],
        "residue": decomposition.residue,
        "alpha_contribution": decomposition.alpha_contribution,
        "other_factor_contribution": decomposition.other_factor_contribution,
        "long_only_excess_pp_per_year": decomposition.long_only_excess,
        "share_that_is_exposure": decomposition.share_that_is_exposure(),
        "factor_means_pp_per_year": means,
        "loadings": coefficients,
        "market_relative": _market_relative(window),
    }


def _market_relative(window: pd.DataFrame) -> dict[str, float]:
    """The same long leg against the market: where the 0.958 capture goes.

    The ratio books the whole difference as value. The regression splits it into an HML
    loading and an SMB loading, and the SMB loading is the size premium Experiment 007
    identified in prose.
    """
    small_low, _, small_high, big_low, _, big_high = (window[name] for name in SIX_PORTFOLIOS)
    del small_low, big_low
    long_leg = 0.5 * (small_high + big_high)
    market = window["Mkt-RF"] + window["RF"]
    spread = long_leg - market
    fit = hac_ols(spread.to_numpy(), window[list(FACTORS)].to_numpy(), n_lags=HAC_LAGS)
    names = ("alpha", *FACTORS)
    coefficients = dict(zip(names, fit.coefficients.tolist(), strict=True))
    return {
        "capture_ratio": float(spread.mean()) / float(window["HML"].mean()),
        "hml_loading": coefficients["HML"],
        "smb_loading": coefficients["SMB"],
    }


# --------------------------------------------------------------------------------
# 2. The product panel
# --------------------------------------------------------------------------------


def exposures_path() -> Path:
    return (
        workspace_root()
        / "artifacts"
        / EXP_013_RUN_ID
        / "frames"
        / "exposures.parquet"
    )


def published_loadings() -> pd.DataFrame:
    """Experiment 013's FF5+UMD exposures, read rather than re-estimated.

    Re-estimating them here would produce a second set of numbers that could disagree
    with the published table for reasons nobody would track down. The one loading this
    module does estimate is the comparator's, because Experiment 013 records only the
    comparator's alpha and market beta.
    """
    frame = pd.read_parquet(exposures_path())
    return frame[frame["specification"] == "FF5+UMD"].set_index("ticker")


def fund_returns(cache: RawCache, tickers: Sequence[str]) -> dict[str, pd.Series]:
    """Item B.5 monthly total returns over Experiment 013's frozen window."""
    series: dict[str, pd.Series] = {}
    for ticker in tickers:
        series_id, class_id, _ = resolve_ticker(cache, ticker)
        record = fetch_fund_series(
            cache,
            ticker=ticker,
            series_id=series_id,
            class_id=class_id,
            start=WINDOW_START,
            end=WINDOW_END,
        )
        series[ticker] = pd.Series(record.returns, index=list(record.periods))
    return series


def benchmark_loadings(
    panel: pd.DataFrame, returns: pd.Series
) -> dict[str, float]:
    """VTI's own FF5+UMD loadings, which decide how much exposure the swap really buys.

    Its alpha reproduces Experiment 013's published pedestal of -0.547 pp/yr, which is
    what licenses reading the HML coefficient beside that experiment's fund loadings.
    """
    window = panel.loc[list(returns.index)]
    excess = returns.to_numpy() - window["RF"].to_numpy()
    fit = hac_ols(excess, window[list(FACTORS)].to_numpy(), n_lags=HAC_LAGS)
    names = ("alpha", *FACTORS)
    coefficients = dict(zip(names, fit.coefficients.tolist(), strict=True))
    coefficients["alpha"] = coefficients["alpha"] * 100.0 * MONTHS_PER_YEAR
    return coefficients


def product_panel(
    loadings: pd.DataFrame, returns: Mapping[str, pd.Series]
) -> pd.DataFrame:
    """Each product's loading, filed cost, and realised moments against the comparator."""
    benchmark = returns[BENCHMARK]
    rows: list[dict[str, object]] = []
    for ticker in PANEL:
        months = int(_number(loadings.loc[ticker, "n_observations"]))
        fund = returns[ticker].iloc[-months:]
        matched = benchmark.loc[list(fund.index)]
        difference = fund - matched
        rows.append(
            {
                "ticker": ticker,
                "months": months,
                "hml_loading": _number(loadings.loc[ticker, "beta_HML"]),
                "hml_se": _number(loadings.loc[ticker, "se_HML"]),
                "smb_loading": _number(loadings.loc[ticker, "beta_SMB"]),
                "alpha": _number(loadings.loc[ticker, "alpha_annual_percent"]),
                "alpha_mde80": _number(loadings.loc[ticker, "mde_alpha_annual_percent"]),
                "fee": FILED[ticker].net_expense_ratio_percent,
                "turnover": FILED[ticker].portfolio_turnover_percent,
                "volatility": float(fund.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
                "benchmark_volatility": (
                    float(matched.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0
                ),
                "correlation": float(np.corrcoef(fund.to_numpy(), matched.to_numpy())[0, 1]),
                "tracking_error": (
                    float(difference.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0
                ),
            }
        )
    return pd.DataFrame(rows).set_index("ticker")


def research_portfolio_moments(panel: pd.DataFrame) -> dict[str, float]:
    """The same swap priced on 62 years of research portfolios instead of six of a fund.

    2020-2025 is one window, and a distinctive one for value. Ken French's small-value
    2x3 portfolio against the market over 1963-07..2025-12 says whether the volatility,
    correlation and tracking error a fund shows over that window are a window artefact.
    Nothing here is investable and the point is only the second moments.
    """
    window = _months(panel, CAPTURE_START, CAPTURE_END)
    _, _, small_high, _, _, _ = (window[name] for name in SIX_PORTFOLIOS)
    market = window["Mkt-RF"] + window["RF"]
    scale = math.sqrt(MONTHS_PER_YEAR) * 100.0
    return {
        "fund_volatility": float(small_high.std(ddof=1)) * scale,
        "benchmark_volatility": float(market.std(ddof=1)) * scale,
        "correlation": float(np.corrcoef(small_high.to_numpy(), market.to_numpy())[0, 1]),
        "tracking_error": float((small_high - market).std(ddof=1)) * scale,
    }


def long_run_tracking_error(panel: pd.DataFrame) -> dict[str, float]:
    """What a long-only value portfolio's tracking error to the market has been.

    2020-2025 is one window and a distinctive one. The research portfolios say whether
    a fund's measured tracking error over it is a window artefact.
    """
    window = _months(panel, CAPTURE_START, CAPTURE_END)
    _, _, small_high, _, _, big_high = (window[name] for name in SIX_PORTFOLIOS)
    market = window["Mkt-RF"] + window["RF"]
    scale = math.sqrt(MONTHS_PER_YEAR) * 100.0
    halves = 0.5 * (small_high + big_high)
    return {
        "small_value_full_sample": float((small_high - market).std(ddof=1)) * scale,
        "small_value_post_publication": (
            float(_months((small_high - market).to_frame("d"), "1994-01", CAPTURE_END)["d"]
                  .std(ddof=1))
            * scale
        ),
        "small_value_2020_2025": (
            float(_months((small_high - market).to_frame("d"), WINDOW_START, WINDOW_END)["d"]
                  .std(ddof=1))
            * scale
        ),
        "value_halves_full_sample": float((halves - market).std(ddof=1)) * scale,
    }


# --------------------------------------------------------------------------------
# 3. The corners
# --------------------------------------------------------------------------------


def corners(
    products: pd.DataFrame,
    *,
    benchmark_hml_loading: float,
    tickers: Sequence[str] = ("AVUV",),
    weights: Sequence[float] = (0.10, 0.20, 0.30),
    premia: Sequence[Premium] = PREMIA,
    turnover_coefficient: float = K_PESSIMISTIC,
    horizon_years: float = 30.0,
) -> pd.DataFrame:
    """One row per (product, premium, weight), with growth beside demonstrability."""
    rows: list[dict[str, object]] = []
    for ticker in tickers:
        record = products.loc[ticker]
        for premium in premia:
            for weight in weights:
                inputs = TiltInputs(
                    weight=weight,
                    fund_hml_loading=_number(record["hml_loading"]),
                    benchmark_hml_loading=benchmark_hml_loading,
                    hml_premium=premium.point,
                    fund_fee=_number(record["fee"]),
                    benchmark_fee=FILED[BENCHMARK].net_expense_ratio_percent,
                    fund_turnover_percent=_number(record["turnover"]),
                    benchmark_turnover_percent=FILED[BENCHMARK].portfolio_turnover_percent,
                    turnover_coefficient=turnover_coefficient,
                    fund_volatility=_number(record["volatility"]),
                    benchmark_volatility=_number(record["benchmark_volatility"]),
                    correlation=_number(record["correlation"]),
                )
                verdict = tilt_verdict(inputs, years=horizon_years)
                tracking_error = verdict.portfolio_tracking_error_basis_points
                rows.append(
                    {
                        "ticker": ticker,
                        "premium": premium.label,
                        "premium_pp": premium.point,
                        "reliably_signed": premium.reliably_signed,
                        "weight": weight,
                        "edge_bp": verdict.portfolio_edge_basis_points,
                        "te_bp": tracking_error,
                        "p_30y": probability_of_outperformance(
                            edge_bp=verdict.portfolio_edge_basis_points,
                            tracking_error_bp=tracking_error,
                            horizon_years=horizon_years,
                        ),
                        "years_to_90": (
                            horizon_for_confidence(
                                edge_bp=verdict.portfolio_edge_basis_points,
                                tracking_error_bp=tracking_error,
                                confidence=0.90,
                            )
                            if verdict.portfolio_edge_basis_points > 0.0
                            else float("inf")
                        ),
                        "mde80_30y_bp": minimum_detectable_effect(
                            standard_error=tracking_error / math.sqrt(horizon_years)
                        ),
                        "alpha_pp": _number(record.get("alpha", float("nan"))),
                        "alpha_mde80_pp": _number(record.get("alpha_mde80", float("nan"))),
                        "growth_pp": verdict.growth_contribution_percent,
                        "ce_gamma3_pp": verdict.certainty_equivalent_percent,
                        "wealth_multiple_30y": verdict.terminal_wealth_multiple_30y,
                    }
                )
    return pd.DataFrame(rows)


def edge_interval(
    products: pd.DataFrame,
    *,
    ticker: str,
    weight: float,
    benchmark_hml_loading: float,
    premium: Premium,
    turnover_coefficient: float = K_PESSIMISTIC,
) -> tuple[float, float]:
    """The net edge at the two ends of a premium's interval, in basis points."""
    record = products.loc[ticker]
    out: list[float] = []
    for point in (premium.low, premium.high):
        inputs = TiltInputs(
            weight=weight,
            fund_hml_loading=_number(record["hml_loading"]),
            benchmark_hml_loading=benchmark_hml_loading,
            hml_premium=point,
            fund_fee=_number(record["fee"]),
            benchmark_fee=FILED[BENCHMARK].net_expense_ratio_percent,
            fund_turnover_percent=_number(record["turnover"]),
            benchmark_turnover_percent=FILED[BENCHMARK].portfolio_turnover_percent,
            turnover_coefficient=turnover_coefficient,
            fund_volatility=_number(record["volatility"]),
            benchmark_volatility=_number(record["benchmark_volatility"]),
            correlation=_number(record["correlation"]),
        )
        out.append(tilt_verdict(inputs).portfolio_edge_basis_points)
    return (out[0], out[1])


# --------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------


def main() -> None:  # pragma: no cover - a reporting entry point
    cache = RawCache()
    panel = french_panel(cache)
    identity = capture_identity(panel)

    print("=" * 78)
    print("1. Is the capture fraction a loading? Identity (C) on French's six portfolios")
    print("=" * 78)
    print(f"  months                          {identity['months']}")
    print(
        "  HML reconstruction residual     "
        f"{identity['reconstruction_max_abs_residual_pp_per_month']:.4f} pp/month"
    )
    print(f"  capture, direct ratio           {identity['capture_direct_ratio']:.6f}")
    print(f"  capture, rebuilt from (C)       {identity['capture_from_identity']:.6f}")
    print(f"  identity error                  {identity['identity_error']:.2e}")
    print(
        f"  HML loading of the same spread  {identity['hml_loading']:.4f} "
        f"(HAC t {identity['hml_loading_t']:.1f})"
    )
    print(f"  residue                         {identity['residue']:.4f}")
    print(f"    of which alpha                {identity['alpha_contribution']:.4f}")
    print(f"    of which other factors        {identity['other_factor_contribution']:.4f}")
    print(f"  share of the ratio that is exposure  {identity['share_that_is_exposure']:.3f}")
    market = identity["market_relative"]
    assert isinstance(market, dict)
    print(
        f"  against the market: ratio {market['capture_ratio']:.3f} splits into "
        f"HML {market['hml_loading']:.3f} and SMB {market['smb_loading']:.3f}"
    )

    loadings = published_loadings()
    returns = fund_returns(cache, (BENCHMARK, *PANEL))
    comparator = benchmark_loadings(panel, returns[BENCHMARK])
    products = product_panel(loadings, returns)

    print()
    print("=" * 78)
    print(f"2. The comparator, {BENCHMARK}, over {WINDOW_START}..{WINDOW_END}")
    print("=" * 78)
    print(f"  alpha {comparator['alpha']:.4f} pp/yr (Experiment 013 publishes -0.5470)")
    for name in FACTORS:
        print(f"  {name:8s} {comparator[name]: .4f}")

    print()
    print("=" * 78)
    print("3. The nine systematic products, plus VBR")
    print("=" * 78)
    print(products.round(4).to_string())

    print()
    print("  long-run tracking error of long-only value vs the market, pp/yr:")
    for key, value in long_run_tracking_error(panel).items():
        print(f"    {key:34s} {value:6.2f}")

    print()
    print("  the same swap on 1963-2025 research portfolios rather than 2020-2025 funds:")
    moments = research_portfolio_moments(panel)
    for key, value in moments.items():
        print(f"    {key:34s} {value:6.3f}")
    long_run = products.copy()
    for key, column in (
        ("fund_volatility", "volatility"),
        ("benchmark_volatility", "benchmark_volatility"),
        ("correlation", "correlation"),
    ):
        long_run.loc["AVUV", column] = moments[key]
    print(
        corners(long_run, benchmark_hml_loading=comparator["HML"])
        .round(4)
        .to_string(index=False)
    )

    print()
    print("=" * 78)
    print("4. The corners")
    print("=" * 78)
    for coefficient, label in ((K_FLOOR, "k = 1.0"), (K_PESSIMISTIC, "k = 1.7")):
        table = corners(
            products,
            benchmark_hml_loading=comparator["HML"],
            turnover_coefficient=coefficient,
        )
        print(f"\n  AVUV, {label}")
        print(table.round(4).to_string(index=False))

    print()
    print("  every product at 20%, pooled premium, k = 1.7:")
    table = corners(
        products,
        benchmark_hml_loading=comparator["HML"],
        tickers=PANEL,
        weights=(0.20,),
        premia=(PREMIA[0],),
    )
    print(table.round(4).to_string(index=False))

    print()
    print("  AVUV at 20% across the pooled premium's interval, bp/yr:")
    low, high = edge_interval(
        products,
        ticker="AVUV",
        weight=0.20,
        benchmark_hml_loading=comparator["HML"],
        premium=PREMIA[0],
    )
    print(f"    {low:.1f} .. {high:.1f}")
    print("  AVUV at 20% across the US post-publication interval, bp/yr:")
    low, high = edge_interval(
        products,
        ticker="AVUV",
        weight=0.20,
        benchmark_hml_loading=comparator["HML"],
        premium=PREMIA[2],
    )
    print(f"    {low:.1f} .. {high:.1f}")

    print()
    print(json.dumps({"exp_013_run_id": EXP_013_RUN_ID, "hac_lags": HAC_LAGS}))


if __name__ == "__main__":  # pragma: no cover - a reporting entry point
    main()
