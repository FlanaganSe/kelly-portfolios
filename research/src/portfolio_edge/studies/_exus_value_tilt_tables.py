"""Regenerates the ex-US tables in ``docs/research/portfolio-recommendation.md`` §5.2 and
``docs/research/factor-products.md``. Run it with::

    uv run python -m portfolio_edge.studies._exus_value_tilt_tables

Kept separate from :mod:`portfolio_edge.studies.exus_value_tilt` and
:mod:`portfolio_edge.studies.value_tilt` so both stay pure and testable and only this
file touches the cache, in the same split :mod:`portfolio_edge.studies._value_tilt_tables`
uses for the US shelf.

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen. The premia are computed here from the same French files Experiments 005 and
006 pin, and reproduce that experiment's published regional cells. The fees are
Experiment 009's committed product facts; the portfolio turnover rates are read from the
same filings and had never been read before. Nothing here promotes any product: decision
0002 caps every product result at `exploratory`.

Four things are computed
------------------------
*The size premium, ex-US.* SMB on each region's own panel over the eras Experiment 005
froze, with intervals and MDE₈₀. **This is measured, not transferred.** The US size
premium is not signable; whether the ex-US one is decides whether a developed-ex-US
small-value fund buys an unpriced exposure or a priced one.

*The decomposition.* Every ex-US product that reached `exploratory` in Experiment 009,
split into **HML and SMB together** on **its own region's** panel, with joint
block-bootstrap intervals. Experiment 009 published only the *intended* loading, so a
small-value fund's size leg has never been reported beside its value leg.

*The price of the exposure.* Realised tracking error against the **incumbent the investor
actually sells** — VEA, the developed-ex-US holding ``portfolio-recommendation.md`` §1.2
names, with SPDW beside it — and the tracking error per unit of delivered HML loading.

*The corners.* :func:`portfolio_edge.studies.value_tilt.tilt_verdict` at an 8% weight on
three premia, with the alpha charge applied where the alpha is measurable.

The window trap this module exists to avoid
-------------------------------------------
These funds have wildly unequal filed histories: AVDV 75 months from 2019-10, DFIV and
AVIV 51 from 2021-10, DISV 45 from 2022-04. A second moment measured over a window that
contains 2020 is not comparable with one that does not, and **AVDV's volatility falls
from 20.1%/yr on its own window to 17.1% on the common one** — enough to move a variance
drag by more than the effect being measured. Every cross-fund ranking is therefore
computed on the **common window all five share** as well as on each fund's own, and both
are printed.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from portfolio_edge.core.costs import K_FLOOR, K_PESSIMISTIC
from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_001_factor_decay import minimum_detectable_effect
from portfolio_edge.experiments.exp_002_fund_exposure import fetch_fund_series
from portfolio_edge.experiments.exp_002_universe import resolve_ticker, workspace_root
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.inference.hac import hac_mean, hac_ols
from portfolio_edge.studies.exus_value_tilt import (
    PremiumEvidence,
    alpha_charged_edge,
    growth_per_unit_tracking_error,
    tracking_error_per_unit_exposure,
)
from portfolio_edge.studies.outperformance_horizon import probability_of_outperformance
from portfolio_edge.studies.value_tilt import TiltInputs, tilt_verdict, turnover_cost_percent

MONTHS_PER_YEAR: Final = 12
HAC_LAGS: Final = 6
"""Experiment 009's lag count, kept so a loading here is comparable to one there."""

BLOCK_LENGTH: Final = 6.0
RESAMPLES: Final = 4000
CONFIDENCE: Final = 0.95
"""Experiment 009's loading-interval parameters, so the HML intervals here reproduce its
published ones — which they do, to about 0.01 on an independent seed.
"""

PREMIUM_BLOCK_LENGTH: Final = 12.0
PREMIUM_RESAMPLES: Final = 10_000
"""Experiments 001, 005 and 006's frozen premium-interval parameters."""

SEED: Final = 20260812
"""Experiment 009's seed. The draws are not its draws; the procedure is."""

EXP_009_RUN_ID: Final = "f6ce1701324546b28c03598c935b7819"
"""The Experiment 009 run whose published exposures, windows and verdicts this reads."""

SAMPLE_END: Final = "2025-12"
"""Experiment 005's sample policy. The cached French files now run to 2026-06."""

POST_PUBLICATION_START: Final = "1994-01"
"""HML's frozen post-publication boundary, copied from Experiment 001 through 005."""

PUBLICATION_BOUNDARIES: Final[Mapping[str, str]] = {
    "HML": "1994-01",
    "UMD": "1994-01",
    "RMW": "2014-01",
    "CMA": "2014-01",
    "SMB": "1982-01",
}
"""Each factor's own boundary: the first January strictly after its journal issue date.

Experiment 001 froze four of these and 005 and 006 copy them verbatim. **SMB's is new
here** and follows the same rule from
[Banz (1981)](https://doi.org/10.1016/0304-405X(81)90018-0), *Journal of Financial
Economics* 9(1), March 1981 — so 1982-01, twelve years earlier than HML's.

Applying HML's 1994-01 boundary to RMW and CMA would be an error of eight years and
would move RMW's developed-ex-US premium from +1.68 to +3.21. Applying it to SMB is not
an error but a **comparability choice**, so both are reported: SMB on its own boundary,
and SMB on HML's, which is the window every figure in this module's tilt tables uses.
It changes nothing outside the United States, because **the international files begin in
1989-07 and 1990-07 and are entirely post-Banz**: ex-US SMB has no pre-publication era at
all, and no decay across a size boundary can be measured there.
"""

RECENT_START: Final = "2016-01"

COMMON_START: Final = "2022-04"
"""The first month every one of the five developed-ex-US value candidates has filed."""

BENCHMARK: Final = "VEA"
ALTERNATIVE_BENCHMARK: Final = "SPDW"
"""The incumbent, and its alternative. A tilt is a substitution, so the incumbent is the
fund the investor sells — never a fitted cheap replication, which is what Experiment 009
reports and what a tracking error borrowed from it would mean.
"""

FACTORS: Final = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD")

FF5_FILES: Final[Mapping[str, str]] = {
    "us": "french_us_ff5",
    "developed_ex_us": "french_developed_ex_us_ff5",
    "emerging": "french_emerging_ff5",
}

MOMENTUM_FILES: Final[Mapping[str, str]] = {
    "us": "french_us_momentum",
    "developed_ex_us": "french_developed_ex_us_momentum",
    "emerging": "french_emerging_momentum",
}
"""Each region's own panel. Experiment 009 conclusion 5: grading an ex-US fund on the US
panel would put 16 of 25 below the bar rather than 5, moving loadings by up to 0.480.
The momentum column is ``Mom`` in the US file and ``WML`` in both international ones;
both are the same 30/70 prior-return spread.
"""

SURVIVORS: Final = ("DFIV", "IVLU", "AVIV", "AVDV", "DISV", "SCZ", "IDMO")
"""Experiment 015's surviving set: the seven of Experiment 009's twelve `exploratory`
ex-US products that keep their status under every basis tested, placebos included.
"""

SET_ASIDE: Final = ("IMTM", "FNDC", "SCHC", "DFIS")
"""`rejected` by Experiment 015 under its expressive basis. Decomposed and printed so the
exclusion is visible rather than assumed, then excluded from every ranking.
"""

ALSO_DECOMPOSED: Final = ("EFV",)
"""Survives every basis but the degenerate one, which hands the fit a second EAFE value
fund and so measures the basis rather than the product. Printed, not ranked.
"""

VALUE_CANDIDATES: Final = ("DFIV", "IVLU", "AVIV", "AVDV", "DISV")
"""The five developed-ex-US funds a value tilt could be bought through. SCZ is a plain
small-cap fund and IDMO a momentum fund; neither is a value tilt and neither is ranked
as one.
"""


@dataclass(frozen=True, slots=True)
class FiledFacts:
    """What a fund's own SEC filing says, with the filing that says it."""

    net_expense_ratio_percent: float
    portfolio_turnover_percent: float
    filing: str


FILED: Final[Mapping[str, FiledFacts]] = {
    "AVDV": FiledFacts(0.36, 4.0, "497K 2025-12-31, accession 0001710607-25-000402"),
    "AVIV": FiledFacts(0.25, 11.0, "497K 2025-12-31, accession 0001710607-25-000400"),
    "DFIV": FiledFacts(0.27, 6.0, "497K 2026-02-27, accession 0001816125-26-000082"),
    "DISV": FiledFacts(0.42, 8.0, "497K 2026-02-27, accession 0001816125-26-000069"),
    "IVLU": FiledFacts(0.31, 16.0, "497K 2025-11-28, accession 0001193125-25-302146"),
    "SCZ": FiledFacts(0.40, 18.0, "497K 2025-11-28, accession 0001193125-25-302167"),
    "EFV": FiledFacts(0.31, 23.0, "497K 2025-11-28, accession 0001193125-25-302176"),
    "IDMO": FiledFacts(0.25, 105.0, "497K 2026-02-27, accession 0001193125-26-079059"),
    "VEA": FiledFacts(0.03, 4.0, "497K 2026-04-28, accession 0000923202-26-000061"),
    "SPDW": FiledFacts(0.03, 3.0, "497K 2026-01-31, accession 0001193125-26-031210"),
}
"""Net expense ratio and the Item 3 portfolio turnover rate, `as of 2026-08-18`.

The fees are Experiment 009's committed ``product_facts.json`` unchanged, except SPDW's,
which that file does not carry and which is read here from the same form. **The turnover
rates are new**: no ex-US product's filed turnover had been read before, and the range is
far wider than the US shelf's. AVDV files **4%**, the lowest rotation of any fund in
either audit; IDMO files **105%**, which at ``k = 1.7`` is 1.79 pp/yr of trading cost and
swamps every other term in its row.

The SEC definition is ``min(purchases, sales) / average net assets`` and **excludes an
ETF's in-kind creations and redemptions**, so it is the one-sided measure
``core/costs.py`` wants.
"""


# --------------------------------------------------------------------------------
# Small typed helpers
# --------------------------------------------------------------------------------


def _number(value: object) -> float:
    """One cell of a frame as a float; ``pandas`` cannot promise a scalar statically."""
    return float(value)  # type: ignore[arg-type]


def _text(value: object) -> str:
    return str(value)


def _months(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Rows whose month label lies in ``[start, end]``, by comparison rather than slice."""
    labels = frame.index.astype(str)
    return frame.loc[(labels >= start) & (labels <= end)]


def _window(series: pd.Series, start: str, end: str) -> pd.Series:
    labels = series.index.astype(str)
    return series.loc[(labels >= start) & (labels <= end)]


def _table(cache: RawCache, dataset_id: str, table_id: str) -> pd.DataFrame:
    dataset = french.get_dataset(dataset_id)
    entry = cache.require(dataset.url)
    frame = french.parse(cache, entry, dataset=dataset).table(table_id).to_frame()
    frame.index = pd.Index([str(label) for label in frame.index])
    return frame


def factor_files(cache: RawCache) -> dict[str, pd.DataFrame]:
    """Each region's FF5 file **alone**, which is what a premium is measured on.

    Joining the momentum file first would silently shorten two of the three samples:
    ``Developed_ex_US_Mom_Factor`` begins 1990-11 against the five-factor file's 1990-07,
    and the emerging pair differ by six months. Experiment 005 measures HML, RMW and CMA
    on the five-factor file, so this does too.
    """
    return {region: _table(cache, name, "monthly") for region, name in FF5_FILES.items()}


def regression_panels(cache: RawCache) -> dict[str, pd.DataFrame]:
    """Each region's FF5 file joined to its own momentum file, for the FF5+UMD fits."""
    panels: dict[str, pd.DataFrame] = {}
    for region, ff5_id in FF5_FILES.items():
        ff5 = _table(cache, ff5_id, "monthly")
        momentum = _table(cache, MOMENTUM_FILES[region], "monthly")
        momentum = momentum.rename(columns={momentum.columns[0]: "UMD"})
        panels[region] = ff5.join(momentum, how="inner")
    return panels


# --------------------------------------------------------------------------------
# 1. The size premium, ex-US: measured rather than transferred
# --------------------------------------------------------------------------------


def premium_cell(
    values: NDArray[np.float64] | Sequence[float],
    *,
    label: str,
    panel: str,
    window: str,
) -> tuple[PremiumEvidence, dict[str, float]]:
    """One factor premium, with the interval and the detection floor that read it.

    ``values`` are monthly decimal returns. The interval is a stationary block bootstrap
    at the frozen 12-month mean block and 10,000 resamples; the MDE₈₀ uses the
    **conventional** standard error, which is what Experiments 001, 005 and 006 publish.
    The HAC floor is returned beside it rather than substituted for it, because swapping
    the two silently would move every published figure this reproduces.
    """
    series = np.asarray(values, dtype=np.float64)
    count = series.size
    point = float(series.mean()) * MONTHS_PER_YEAR * 100.0
    hac = hac_mean(series * 100.0)
    conventional_se = float(series.std(ddof=1)) * 100.0 / math.sqrt(count)
    rng = np.random.default_rng(SEED)
    indices = stationary_bootstrap_indices(
        count, PREMIUM_BLOCK_LENGTH, PREMIUM_RESAMPLES, rng
    )
    replicates = series[indices].mean(axis=1) * MONTHS_PER_YEAR * 100.0
    low, high = (float(value) for value in np.quantile(replicates, [0.05, 0.95]))
    evidence = PremiumEvidence(
        label=label,
        panel=panel,
        window=window,
        months=count,
        point=point,
        low=low,
        high=high,
        mde80=MONTHS_PER_YEAR * minimum_detectable_effect(standard_error=conventional_se),
    )
    diagnostics = {
        "volatility": float(series.std(ddof=1)) * math.sqrt(MONTHS_PER_YEAR) * 100.0,
        "hac_t": point / (hac.standard_error * MONTHS_PER_YEAR),
        "hac_lags": float(hac.n_lags),
        "mde80_hac": MONTHS_PER_YEAR
        * minimum_detectable_effect(standard_error=hac.standard_error),
    }
    return evidence, diagnostics


def regional_premia(
    files: Mapping[str, pd.DataFrame], *, factors: Sequence[str] = ("SMB", "HML")
) -> pd.DataFrame:
    """Every factor on every region's own panel, over three eras.

    The eras are Experiment 005's two — each factor's own post-publication era and the
    recent decade from 2016-01 — plus each region's **full** available sample, which for
    the developed-ex-US file begins 1990-07 and for the emerging one 1989-07. A factor
    whose boundary is not HML's gets a fourth row on HML's window, so the two are
    comparable without pretending they are the same era.

    **Full sample and post-publication are not independent readings outside the United
    States.** They share 384 of 426 and 384 of 438 months, so the international files
    cannot say anything about decay across HML's publication boundary and are not asked
    to. In the US they share 384 of 750 and the comparison is meaningful.
    """
    rows: list[dict[str, object]] = []
    for region, panel in files.items():
        for factor in factors:
            eras: list[tuple[str, str]] = [
                ("full sample", str(panel.index.min())),
                ("post-publication", PUBLICATION_BOUNDARIES[factor]),
                ("recent decade", RECENT_START),
            ]
            if PUBLICATION_BOUNDARIES[factor] != POST_PUBLICATION_START:
                eras.append(("on HML's window", POST_PUBLICATION_START))
            for era, start in eras:
                window = _months(panel, start, SAMPLE_END)
                if window.empty:
                    continue
                evidence, diagnostics = premium_cell(
                    window[factor].to_numpy(),
                    label=f"{factor} {era}",
                    panel=region,
                    window=f"{window.index.min()}..{window.index.max()}",
                )
                verdict = evidence.verdict
                rows.append(
                    {
                        "panel": region,
                        "factor": factor,
                        "era": era,
                        "window": evidence.window,
                        "months": evidence.months,
                        "premium": evidence.point,
                        "low": evidence.low,
                        "high": evidence.high,
                        "mde80": evidence.mde80,
                        "hac_t": diagnostics["hac_t"],
                        "volatility": diagnostics["volatility"],
                        "signable": verdict.signable,
                        "material": verdict.material,
                        "reason": verdict.reason,
                    }
                )
    return pd.DataFrame(rows)


def pooled_premium(
    files: Mapping[str, pd.DataFrame], *, factor: str, start: str
) -> tuple[PremiumEvidence, dict[str, float]]:
    """Experiment 005's equal-weighted three-region composite, jointly resampled.

    One vote per region, because the object is to count independent looks rather than to
    build a portfolio. Resampling the composite with one index set is algebraically
    identical to resampling the panel jointly and then compositing, which is the identity
    ``exp_005_regional_replication.cross_region_bootstrap`` relies on and the reason a
    per-region independent resample is invalid here.
    """
    columns = [_months(panel, start, SAMPLE_END)[factor] for panel in files.values()]
    joined = pd.concat(columns, axis=1, join="inner")
    return premium_cell(
        joined.mean(axis=1).to_numpy(),
        label=f"{factor} pooled",
        panel=" + ".join(files),
        window=f"{joined.index.min()}..{joined.index.max()}",
    )


# --------------------------------------------------------------------------------
# 2. The decomposition: HML and SMB together, on each fund's own panel
# --------------------------------------------------------------------------------


def artifact_frame(name: str) -> Path:
    return workspace_root() / "artifacts" / EXP_009_RUN_ID / "frames" / f"{name}.parquet"


def published_outcomes() -> pd.DataFrame:
    """Experiment 009's per-fund verdicts, windows and panels, read rather than redone."""
    return pd.read_parquet(artifact_frame("outcomes")).set_index("ticker")


def published_loadings() -> pd.DataFrame:
    """Experiment 009's FF5+UMD exposures, read rather than re-estimated.

    Re-estimating them would produce a second set of numbers that could disagree with the
    published table for reasons nobody would track down.
    """
    frame = pd.read_parquet(artifact_frame("exposures"))
    return frame[frame["specification"] == "FF5+UMD"].set_index("ticker")


def fund_returns(
    cache: RawCache, tickers: Sequence[str], *, start: str, end: str
) -> dict[str, pd.Series]:
    """Item B.5 monthly total returns from each fund's own N-PORT filings.

    Fetched **once** per ticker for the widest window any caller needs and sliced
    thereafter, because :func:`fetch_fund_series` re-reads every quarterly filing and
    throttles between them.
    """
    series: dict[str, pd.Series] = {}
    for ticker in tickers:
        series_id, class_id, _ = resolve_ticker(cache, ticker)
        record = fetch_fund_series(
            cache, ticker=ticker, series_id=series_id, class_id=class_id, start=start, end=end
        )
        series[ticker] = pd.Series(record.returns, index=list(record.periods))
    return series


def loadings_with_intervals(
    returns: pd.Series, panel: pd.DataFrame
) -> dict[str, tuple[float, float, float]]:
    """Every FF5+UMD coefficient with a joint block-bootstrap interval, plus alpha.

    Rows are resampled **jointly** across the fund return and the whole factor design,
    which is what ``exp_009_exus_products._bootstrap_interval`` does. Resampling
    residuals alone would assume the independence the block length exists to avoid
    assuming. Alpha is returned annualised in percent; every loading is a pure number.
    """
    window = panel.loc[list(returns.index)]
    excess = returns.to_numpy() - window["RF"].to_numpy()
    regressors = window[list(FACTORS)].to_numpy()
    design = np.column_stack([np.ones(len(returns)), regressors])
    fit = hac_ols(excess, regressors, n_lags=HAC_LAGS)

    rng = np.random.default_rng(SEED)
    indices = stationary_bootstrap_indices(len(returns), BLOCK_LENGTH, RESAMPLES, rng)
    batch_y = excess[indices]
    batch_x = design[indices]
    gram = np.einsum("btk,btl->bkl", batch_x, batch_x)
    moment = np.einsum("btk,bt->bk", batch_x, batch_y)
    draws = np.linalg.solve(gram + 1e-12 * np.eye(design.shape[1]), moment[:, :, None])[:, :, 0]

    tail = 100.0 * (1.0 - CONFIDENCE) / 2.0
    out: dict[str, tuple[float, float, float]] = {}
    for position, name in enumerate(("alpha", *FACTORS)):
        scale = 100.0 * MONTHS_PER_YEAR if name == "alpha" else 1.0
        low, high = np.percentile(draws[:, position], [tail, 100.0 - tail])
        out[name] = (
            float(fit.coefficients[position]) * scale,
            float(low) * scale,
            float(high) * scale,
        )
    return out


def decomposition(
    returns: Mapping[str, pd.Series],
    panels: Mapping[str, pd.DataFrame],
    outcomes: pd.DataFrame,
    tickers: Sequence[str],
) -> pd.DataFrame:
    """Every named fund's full loading vector on **its own region's** panel.

    Each fund is estimated over Experiment 009's own window for it, so the HML column
    reproduces that experiment's published intended loading exactly rather than
    approximately, and the SMB column beside it is measured on the same months.
    """
    rows: list[dict[str, object]] = []
    for ticker in tickers:
        region = _text(outcomes.loc[ticker, "region"])
        first = _text(outcomes.loc[ticker, "first_month"])
        last = _text(outcomes.loc[ticker, "last_month"])
        fund = _window(returns[ticker], first, last)
        loadings = loadings_with_intervals(fund, panels[region])
        row: dict[str, object] = {
            "ticker": ticker,
            "panel": region,
            "mandate": _text(outcomes.loc[ticker, "mandate"]),
            "months": len(fund),
            "window": f"{first}..{last}",
            "status": _text(outcomes.loc[ticker, "status"]),
        }
        for name in ("HML", "SMB", "UMD", "RMW", "CMA"):
            point, low, high = loadings[name]
            row[name] = point
            row[f"{name}_low"] = low
            row[f"{name}_high"] = high
        row["alpha"] = loadings["alpha"][0]
        row["alpha_mde80"] = _number(outcomes.loc[ticker, "alpha_mde_80pc_power_percent"])
        rows.append(row)
    return pd.DataFrame(rows).set_index("ticker")


# --------------------------------------------------------------------------------
# 3. The price of the exposure, against the fund the investor actually sells
# --------------------------------------------------------------------------------


def moments_against(fund: pd.Series, benchmark: pd.Series) -> dict[str, float]:
    """Annualised volatilities, correlation and realised tracking error, in percent."""
    matched = benchmark.loc[list(fund.index)]
    scale = math.sqrt(MONTHS_PER_YEAR) * 100.0
    return {
        "fund_volatility": float(fund.std(ddof=1)) * scale,
        "benchmark_volatility": float(matched.std(ddof=1)) * scale,
        "correlation": float(np.corrcoef(fund.to_numpy(), matched.to_numpy())[0, 1]),
        "tracking_error": float((fund - matched).std(ddof=1)) * scale,
    }


def tilt_inputs(
    *,
    weight: float,
    ticker: str,
    benchmark: str,
    fund_hml_loading: float,
    benchmark_hml_loading: float,
    premium: float,
    moments: Mapping[str, float],
    turnover_coefficient: float,
) -> TiltInputs:
    """One swap, with every cost charged incrementally over the incumbent."""
    return TiltInputs(
        weight=weight,
        fund_hml_loading=fund_hml_loading,
        benchmark_hml_loading=benchmark_hml_loading,
        hml_premium=premium,
        fund_fee=FILED[ticker].net_expense_ratio_percent,
        benchmark_fee=FILED[benchmark].net_expense_ratio_percent,
        fund_turnover_percent=FILED[ticker].portfolio_turnover_percent,
        benchmark_turnover_percent=FILED[benchmark].portfolio_turnover_percent,
        turnover_coefficient=turnover_coefficient,
        fund_volatility=moments["fund_volatility"],
        benchmark_volatility=moments["benchmark_volatility"],
        correlation=moments["correlation"],
    )


@dataclass(frozen=True, slots=True)
class FundEstimate:
    """One fund's HML loading, alpha and second moments, all on the same months."""

    ticker: str
    months: int
    window: str
    hml_loading: float
    smb_loading: float
    alpha: float
    alpha_mde80: float
    moments: Mapping[str, float]


def estimate_funds(
    returns: Mapping[str, pd.Series],
    panel: pd.DataFrame,
    windows: Mapping[str, tuple[str, str]],
    tickers: Sequence[str],
    *,
    alpha_floors: Mapping[str, float],
    benchmark: str = BENCHMARK,
) -> dict[str, FundEstimate]:
    """Loadings and second moments for each fund over the window it is given.

    ``alpha_floors`` comes from Experiment 009 and is a property of each fund's **own
    published window**, so it is deliberately not rescaled when a shorter common window
    is used. A shorter window has a higher floor, so keeping the published one makes the
    alpha charge more willing to fire, not less — the conservative direction for a charge
    that only ever reduces an edge.

    The incumbent is estimated by the same function with a floor of ``nan``, which never
    fires a charge; that is correct, because the incumbent's alpha is the *pedestal* the
    charge is measured against and cannot be charged against itself.
    """
    out: dict[str, FundEstimate] = {}
    for ticker in tickers:
        start, end = windows[ticker]
        fund = _window(returns[ticker], start, end)
        fitted = loadings_with_intervals(fund, panel)
        out[ticker] = FundEstimate(
            ticker=ticker,
            months=len(fund),
            window=f"{fund.index[0]}..{fund.index[-1]}",
            hml_loading=fitted["HML"][0],
            smb_loading=fitted["SMB"][0],
            alpha=fitted["alpha"][0],
            alpha_mde80=alpha_floors.get(ticker, float("nan")),
            moments=moments_against(fund, returns[benchmark]),
        )
    return out


def corners(
    estimates: Mapping[str, FundEstimate],
    *,
    benchmark_estimate: FundEstimate,
    premia: Sequence[PremiumEvidence],
    tickers: Sequence[str] = VALUE_CANDIDATES,
    benchmark: str = BENCHMARK,
    weights: Sequence[float] = (0.08,),
    turnover_coefficient: float = K_PESSIMISTIC,
    horizon_years: float = 30.0,
) -> pd.DataFrame:
    """One row per (fund, premium, weight), with growth beside demonstrability."""
    rows: list[dict[str, object]] = []
    for ticker in tickers:
        estimate = estimates[ticker]
        for premium in premia:
            for weight in weights:
                inputs = tilt_inputs(
                    weight=weight,
                    ticker=ticker,
                    benchmark=benchmark,
                    fund_hml_loading=estimate.hml_loading,
                    benchmark_hml_loading=benchmark_estimate.hml_loading,
                    premium=premium.point,
                    moments=estimate.moments,
                    turnover_coefficient=turnover_coefficient,
                )
                verdict = tilt_verdict(inputs)
                tracking_error = verdict.portfolio_tracking_error_basis_points
                rows.append(
                    {
                        "ticker": ticker,
                        "premium": premium.label,
                        "panel": premium.panel,
                        "signable": premium.verdict.signable,
                        "weight": weight,
                        "months": estimate.months,
                        "hml": estimate.hml_loading,
                        "smb": estimate.smb_loading,
                        "delivered": inputs.delivered_loading,
                        "cost": inputs.incremental_cost,
                        "edge_bp": verdict.portfolio_edge_basis_points,
                        "te_bp": tracking_error,
                        "sleeve_te": inputs.sleeve_tracking_error,
                        "te_per_unit": tracking_error_per_unit_exposure(inputs),
                        "growth_bp": verdict.growth_contribution_percent * 100.0,
                        "ce_bp": verdict.certainty_equivalent_percent * 100.0,
                        "growth_per_te": growth_per_unit_tracking_error(verdict),
                        "wealth_30y": verdict.terminal_wealth_multiple_30y,
                        "p_30y": probability_of_outperformance(
                            edge_bp=verdict.portfolio_edge_basis_points,
                            tracking_error_bp=tracking_error,
                            horizon_years=horizon_years,
                        ),
                        "mde80_30y_bp": minimum_detectable_effect(
                            standard_error=tracking_error / math.sqrt(horizon_years)
                        ),
                        "alpha": estimate.alpha,
                        "alpha_mde80": estimate.alpha_mde80,
                        "alpha_charged_bp": alpha_charged_edge(
                            weight=weight,
                            portfolio_edge_basis_points=verdict.portfolio_edge_basis_points,
                            fund_alpha=estimate.alpha,
                            benchmark_alpha=benchmark_estimate.alpha,
                            alpha_mde80=estimate.alpha_mde80,
                        ),
                    }
                )
    return pd.DataFrame(rows)


def momentum_leg(
    *,
    delivered_umd_loading: float,
    premium: PremiumEvidence,
    ticker: str = "IDMO",
    benchmark: str = BENCHMARK,
    turnover_coefficient: float = K_PESSIMISTIC,
) -> dict[str, float]:
    """IDMO's momentum leg, priced in components rather than through the value chain.

    ``value_tilt.TiltInputs`` names every field for HML, and feeding a UMD loading into a
    field called ``hml_premium`` would be exactly the mislabelling
    ``outperformance_horizon.aggregate`` raises over. So the two measured components are
    returned separately — the gross ``delivered loading x premium`` and the incremental
    cost, the latter through the same tested :func:`turnover_cost_percent` — and the
    caller does the one multiplication in the open.

    The cost is the finding here. **IDMO files 105%/yr of portfolio turnover against
    VEA's 4%**, which is 26 times the incumbent's and 4.5 times the dearest value product
    on this shelf.
    """
    trading = turnover_cost_percent(
        one_sided_turnover_percent=FILED[ticker].portfolio_turnover_percent,
        coefficient=turnover_coefficient,
    ) - turnover_cost_percent(
        one_sided_turnover_percent=FILED[benchmark].portfolio_turnover_percent,
        coefficient=turnover_coefficient,
    )
    fee = FILED[ticker].net_expense_ratio_percent - FILED[benchmark].net_expense_ratio_percent
    gross = delivered_umd_loading * premium.point
    return {
        "delivered_umd_loading": delivered_umd_loading,
        "premium": premium.point,
        "gross_percent": gross,
        "fee_percent": fee,
        "trading_percent": trading,
        "incremental_cost_percent": fee + trading,
        "net_percent": gross - fee - trading,
        "cost_share_of_gross": (fee + trading) / gross if gross != 0.0 else float("nan"),
    }


def hml_premium_evidence(premia: pd.DataFrame, pooled: PremiumEvidence) -> list[PremiumEvidence]:
    """The three HML premia a developed-ex-US tilt may be priced on, and no others.

    The recent decade is deliberately absent: at 120 months its detection floor is 7.52
    against a 5.17 premium, so it can neither confirm nor deny and would only add a
    fourth column that means nothing.
    """
    out: list[PremiumEvidence] = []
    rows = premia[(premia["panel"] == "developed_ex_us") & (premia["factor"] == "HML")]
    for _, row in rows.iterrows():
        if _text(row["era"]) == "recent decade":
            continue
        out.append(
            PremiumEvidence(
                label=f"developed ex-US HML, {row['era']}",
                panel="developed_ex_us",
                window=_text(row["window"]),
                months=int(_number(row["months"])),
                point=_number(row["premium"]),
                low=_number(row["low"]),
                high=_number(row["high"]),
                mde80=_number(row["mde80"]),
            )
        )
    out.append(pooled)
    return out


# --------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------


def _show(frame: pd.DataFrame, *, digits: int = 3) -> None:  # pragma: no cover
    print(frame.round(digits).to_string())


def main() -> None:  # pragma: no cover - a reporting entry point
    cache = RawCache()
    files = factor_files(cache)
    panels = regression_panels(cache)
    outcomes = published_outcomes()
    developed = panels["developed_ex_us"]

    print("=" * 78)
    print("1. Is the ex-US size premium signable? Measured, not transferred")
    print("=" * 78)
    premia = regional_premia(files)
    _show(
        premia.set_index(["panel", "factor", "era"])[
            ["window", "months", "premium", "low", "high", "mde80", "hac_t", "signable"]
        ]
    )
    print()
    for factor in ("SMB", "HML"):
        for era, start in (
            ("post-publication", POST_PUBLICATION_START),
            ("recent decade", RECENT_START),
        ):
            evidence, diagnostics = pooled_premium(files, factor=factor, start=start)
            print(
                f"  pooled {factor} {era:17s} {evidence.point:+6.2f} "
                f"[{evidence.low:+6.2f}, {evidence.high:+6.2f}] "
                f"MDE80 {evidence.mde80:5.2f} HAC t {diagnostics['hac_t']:+5.2f}"
            )
            print(f"    {evidence.verdict.reason}")

    universe = (*SURVIVORS, *ALSO_DECOMPOSED, *SET_ASIDE)
    returns = fund_returns(
        cache,
        (*universe, BENCHMARK, ALTERNATIVE_BENCHMARK),
        start="2019-07",
        end=SAMPLE_END,
    )

    print()
    print("=" * 78)
    print("2. HML and SMB together, on each fund's OWN region's panel")
    print("=" * 78)
    table = decomposition(returns, panels, outcomes, universe)
    _show(
        table[
            [
                "panel", "mandate", "months", "window",
                "HML", "HML_low", "HML_high",
                "SMB", "SMB_low", "SMB_high",
                "alpha", "alpha_mde80",
            ]
        ]
    )
    print()
    print("  the other three legs, which is where a momentum fund's side loads live:")
    _show(
        table[
            [
                "UMD", "UMD_low", "UMD_high",
                "RMW", "RMW_low", "RMW_high",
                "CMA", "CMA_low", "CMA_high",
            ]
        ]
    )

    print()
    print("=" * 78)
    print(f"3. The price of the exposure, against {BENCHMARK} and {ALTERNATIVE_BENCHMARK}")
    print("=" * 78)
    own_windows = {
        ticker: (
            _text(outcomes.loc[ticker, "first_month"]),
            _text(outcomes.loc[ticker, "last_month"]),
        )
        for ticker in universe
    }
    rows: list[dict[str, object]] = []
    for ticker in (*VALUE_CANDIDATES, *ALSO_DECOMPOSED, "SCZ", "IDMO"):
        start, end = own_windows[ticker]
        fund = _window(returns[ticker], start, end)
        for incumbent in (BENCHMARK, ALTERNATIVE_BENCHMARK):
            rows.append(
                {
                    "ticker": ticker,
                    "incumbent": incumbent,
                    "months": len(fund),
                    **moments_against(fund, returns[incumbent]),
                }
            )
    _show(pd.DataFrame(rows).set_index(["ticker", "incumbent"]))
    print()
    print("  the two incumbents against each other, which bounds every figure above:")
    _show(
        pd.DataFrame(
            [
                {
                    "pair": f"{BENCHMARK}/{ALTERNATIVE_BENCHMARK}",
                    **moments_against(returns[BENCHMARK], returns[ALTERNATIVE_BENCHMARK]),
                }
            ]
        ).set_index("pair")
    )

    print()
    print("=" * 78)
    print("4. The corners, at 8% of portfolio")
    print("=" * 78)
    pooled, _ = pooled_premium(files, factor="HML", start=POST_PUBLICATION_START)
    evidence_set = hml_premium_evidence(
        premia,
        PremiumEvidence(
            label="pooled three regions, post-publication",
            panel=pooled.panel,
            window=pooled.window,
            months=pooled.months,
            point=pooled.point,
            low=pooled.low,
            high=pooled.high,
            mde80=pooled.mde80,
        ),
    )
    common_windows = {ticker: (COMMON_START, SAMPLE_END) for ticker in universe}
    alpha_floors = {
        ticker: _number(outcomes.loc[ticker, "alpha_mde_80pc_power_percent"])
        for ticker in universe
    }
    for label, windows in (
        ("each fund's own Experiment 009 window", own_windows),
        (f"the common window all five share, {COMMON_START}..{SAMPLE_END}", common_windows),
    ):
        estimates = estimate_funds(
            returns, developed, windows, VALUE_CANDIDATES, alpha_floors=alpha_floors
        )
        earliest = min(windows[ticker][0] for ticker in VALUE_CANDIDATES)
        benchmark_estimate = estimate_funds(
            returns,
            developed,
            {BENCHMARK: (earliest, SAMPLE_END)},
            (BENCHMARK,),
            alpha_floors={},
        )[BENCHMARK]
        print()
        print(f"  --- {label}")
        print(
            f"      {BENCHMARK} on the developed-ex-US panel over "
            f"{benchmark_estimate.window}: HML {benchmark_estimate.hml_loading:+.4f}, "
            f"SMB {benchmark_estimate.smb_loading:+.4f}, "
            f"alpha {benchmark_estimate.alpha:+.4f} pp/yr"
        )
        table = corners(estimates, benchmark_estimate=benchmark_estimate, premia=evidence_set)
        for premium in evidence_set:
            block = table[table["premium"] == premium.label]
            print(f"\n      {premium.label}: {premium.point:+.2f} pp/yr, {premium.window}")
            _show(
                block.set_index("ticker")[
                    [
                        "months", "hml", "smb", "delivered", "cost",
                        "edge_bp", "te_bp", "te_per_unit",
                        "growth_bp", "ce_bp", "growth_per_te",
                        "wealth_30y", "p_30y", "mde80_30y_bp",
                        "alpha", "alpha_mde80", "alpha_charged_bp",
                    ]
                ]
            )

    print()
    print("  the common window at k = 1.0 rather than 1.7, on the post-publication premium:")
    estimates = estimate_funds(
        returns, developed, common_windows, VALUE_CANDIDATES, alpha_floors=alpha_floors
    )
    benchmark_estimate = estimate_funds(
        returns,
        developed,
        {BENCHMARK: (COMMON_START, SAMPLE_END)},
        (BENCHMARK,),
        alpha_floors={},
    )[BENCHMARK]
    table = corners(
        estimates,
        benchmark_estimate=benchmark_estimate,
        premia=evidence_set[1:2],
        turnover_coefficient=K_FLOOR,
    )
    _show(table.set_index("ticker")[["cost", "edge_bp", "growth_bp", "growth_per_te"]])

    print()
    print("=" * 78)
    print("5. IDMO's momentum leg, and the load nobody had decomposed")
    print("=" * 78)
    umd_premia = regional_premia(
        {"developed_ex_us": developed}, factors=("UMD", "RMW", "CMA")
    )
    _show(
        umd_premia.set_index(["factor", "era"])[
            ["window", "months", "premium", "low", "high", "mde80", "hac_t", "signable"]
        ]
    )
    developed_umd = umd_premia[
        (umd_premia["factor"] == "UMD") & (umd_premia["era"] == "post-publication")
    ].iloc[0]
    umd_evidence = PremiumEvidence(
        label="developed ex-US UMD, post-publication",
        panel="developed_ex_us",
        window=_text(developed_umd["window"]),
        months=int(_number(developed_umd["months"])),
        point=_number(developed_umd["premium"]),
        low=_number(developed_umd["low"]),
        high=_number(developed_umd["high"]),
        mde80=_number(developed_umd["mde80"]),
    )
    idmo_fit = loadings_with_intervals(
        _window(returns["IDMO"], *own_windows["IDMO"]), developed
    )
    vea_fit = loadings_with_intervals(_window(returns[BENCHMARK], "2019-08", SAMPLE_END), developed)
    for coefficient, label in ((K_PESSIMISTIC, "k = 1.7"), (K_FLOOR, "k = 1.0")):
        leg = momentum_leg(
            delivered_umd_loading=idmo_fit["UMD"][0] - vea_fit["UMD"][0],
            premium=umd_evidence,
            turnover_coefficient=coefficient,
        )
        print(f"\n  {label}: " + ", ".join(f"{k} {v:+.3f}" for k, v in leg.items()))

    print()
    print("  the same five at 4% and 12%, post-publication premium, k = 1.7:")
    table = corners(
        estimates,
        benchmark_estimate=benchmark_estimate,
        premia=evidence_set[1:2],
        weights=(0.04, 0.08, 0.12),
    )
    _show(
        table.set_index(["ticker", "weight"])[
            ["edge_bp", "te_bp", "growth_bp", "ce_bp", "growth_per_te"]
        ]
    )


if __name__ == "__main__":  # pragma: no cover - a reporting entry point
    main()
