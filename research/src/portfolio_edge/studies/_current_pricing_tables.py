"""Regenerates the measured tables in ``docs/research/current-regime-and-pricing.md``.

Kept separate from :mod:`portfolio_edge.studies.current_pricing` so that the study
itself stays pure and testable and only this file touches the cache. Run it with

    uv run python -m portfolio_edge.studies._current_pricing_tables

Six data notes that decide how far the output may be trusted.

**The FRED series are refetched on every run and are not point-in-time.** FRED serves one
vintage. A percentile taken here uses today's estimate of 1974, not what anyone saw in
1974. For yields that is nearly harmless; for the CPI leg of the real cash rate it is not,
because seasonal factors are re-estimated annually and rewrite history.

**The ICE BofA option-adjusted spreads are truncated to three years at source.** Measured
2026-08-23: ``BAMLC0A0CM`` and ``BAMLH0A0HYM2`` return 786 and 787 daily rows beginning
2023-08-22, the same three-year cap the total-return siblings carry. **No percentile of a
current OAS against its own history can be computed from FRED**, and this module does not
pretend otherwise: it reports the level, the three-year rank, and then uses the Moody's
Baa/Aaa series, which begin in 1919, as the long-history credit proxy.

**Moody's Baa and Aaa are long-maturity corporate yields.** ``Baa - 10y`` therefore mixes
a term premium into a credit spread, which is exactly the confound
``docs/research/alternative-sleeves-audit.md`` documents for the unhedged corporate leg.
``Baa - Aaa`` is a *within-credit* quality spread and is much closer to a clean credit
signal. The two disagree today and the disagreement is the finding, not an error.

**The Goyal-Welch workbook ends 2025-12** and is an annual academic release. Its ``AAA``,
``BAA``, ``lty`` and ``tbl`` columns were verified against FRED ``AAA``, ``BAA``, ``GS10``
and ``TB3MS`` on the overlapping months of 2025 and match to the published precision, so
the level series are spliced forward from FRED to 2026-07. **The return columns are not
spliced**: every regression below stops where Goyal-Welch stops.

**Ken French's ``BE/ME`` is fixed at formation.** The file is built from the 202606 CRSP
database and its last row is 2026-06, but the June-2026 row belongs to the **June-2025**
formation, whose market equity is dated **December 2024**. The break is visible between
June and July of every year. So the raw value spread is twenty months stale on prices and
:func:`~portfolio_edge.studies.current_pricing.mark_to_market_log_spread` exists to move
it, using the portfolios' own cumulative returns.

**Nothing here is registered as an experiment and no specification was frozen.** Every
number is ``exploratory``.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import french, goyal_welch, lbma
from portfolio_edge.data.cache import CacheEntry, RawCache, default_cache_root
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.studies.current_pricing import (
    PredictiveEvidence,
    classify_evidence,
    log_value_spread,
    mark_to_market_log_spread,
    minimum_detectable_slope,
    percentile_rank,
)
from portfolio_edge.studies.valuation_conditioning import hodrick_1b_covariance

FRED_CSV: Final = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"

#: Daily and monthly FRED series this study reads, with the window each percentile is
#: taken over. The window is the series' own record; where that record is short the
#: table says so rather than borrowing a longer one.
FRED_SERIES: Final = (
    "DGS10", "DGS30", "DGS2", "DGS3MO", "DTB3", "DFF",
    "DFII10", "DFII30", "T10YIE",
    "GS10", "GS30", "GS2", "TB3MS", "FII10", "FII30",
    "AAA", "BAA", "BAA10Y", "CPIAUCSL",
    "BAMLC0A0CM", "BAMLH0A0HYM2",
)

#: The 6 value-weighted book-to-market portfolios, and which column is which side.
_VALUE_COLUMNS: Final = (("BIG HiBM", "BIG LoBM"), ("SMALL HiBM", "SMALL LoBM"))

MONTHS_PER_YEAR: Final = 12


# --------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FredPanel:
    """Every FRED series this study uses, with the cache entry that produced it."""

    series: Mapping[str, pd.Series[float]]
    entries: Mapping[str, CacheEntry]

    def __getitem__(self, key: str) -> pd.Series[float]:
        return self.series[key]


def load_fred(cache: RawCache, *, force: bool = True) -> FredPanel:
    """Refetch every registered series and return it indexed by its own date label."""
    series: dict[str, pd.Series[float]] = {}
    entries: dict[str, CacheEntry] = {}
    for series_id in FRED_SERIES:
        entry = cache.fetch(FRED_CSV.format(series_id), force=force, timeout=60.0)
        rows = list(csv.reader(io.StringIO(cache.read(entry).decode())))[1:]
        series[series_id] = pd.Series(
            {row[0]: float(row[1]) for row in rows if row[1] not in (".", "")},
            dtype=float,
        )
        entries[series_id] = entry
    return FredPanel(series=series, entries=entries)


def _to_month(series: pd.Series[float]) -> pd.Series[float]:
    """Relabel a FRED monthly series from ``YYYY-MM-01`` to ``YYYY-MM``."""
    out = series.copy()
    out.index = pd.Index(str(label)[:7] for label in series.index)
    return out


def load_goyal_welch(cache: RawCache) -> tuple[pd.DataFrame, CacheEntry]:
    """The monthly predictor sheet from 1926-07, and its cache entry."""
    dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    entry = cache.entry_for(dataset.url)
    if entry is None:  # pragma: no cover - the cache is committed with this artifact
        entry = goyal_welch.download(cache, dataset)
    table = goyal_welch.parse(cache, entry, dataset=dataset).table("monthly")
    frame = pd.DataFrame(
        list(table.values), index=list(table.periods), columns=list(table.columns)
    ).astype(float)
    frame = frame[pd.Index(frame.index) >= "1926-07"]
    return frame, entry


def load_french_tables(
    cache: RawCache, dataset_id: str
) -> tuple[french.FrenchFile, CacheEntry]:
    dataset = french.get_dataset(dataset_id)
    entry = cache.entry_for(dataset.url)
    if entry is None:  # pragma: no cover
        entry = french.download(cache, dataset)
    return french.parse(cache, entry, dataset=dataset), entry


def _frame(file: french.FrenchFile, table_id: str) -> pd.DataFrame:
    table = file.table(table_id)
    return pd.DataFrame(
        list(table.values), index=list(table.periods), columns=list(table.columns)
    ).astype(float)


# --------------------------------------------------------------------------------------
# 1. Where every priced input sits
# --------------------------------------------------------------------------------------


def _months_from(frame: pd.DataFrame, first_month: str) -> pd.DataFrame:
    """Rows of a month-labelled frame at or after ``first_month``.

    A plain ``.loc[first:last]`` slice on a string index would do the same thing and is
    what a reader expects; it is avoided because the index here is ``object`` and a
    label slice on an unsorted object index silently returns nothing rather than
    raising. A boolean mask cannot fail that way.
    """
    selected: pd.DataFrame = frame[pd.Index(frame.index) >= first_month]
    return selected


def _level_row(
    name: str, series: pd.Series[float], source: str, *, units: str = "%/yr"
) -> dict[str, object]:
    clean = series.dropna()
    value = float(clean.iloc[-1])
    return {
        "measure": name,
        "value": value,
        "units": units,
        "as_of": str(clean.index[-1]),
        "percentile": percentile_rank(clean.to_numpy(), value),
        "window": f"{clean.index[0]}..{clean.index[-1]}",
        "n": int(clean.size),
        "median": float(clean.median()),
        "source": source,
    }


def rates_table(panel: FredPanel) -> pd.DataFrame:
    """Real rates, nominal levels and curve slopes, each against its own record."""
    def slope(long_id: str, short_id: str) -> pd.Series[float]:
        long_leg, short_leg = panel[long_id], panel[short_id]
        shared = long_leg.index.intersection(short_leg.index)
        return long_leg[shared] - short_leg[shared]

    rows = [
        _level_row("10y TIPS real yield", panel["DFII10"], "FRED DFII10, daily"),
        _level_row("30y TIPS real yield", panel["DFII30"], "FRED DFII30, daily"),
        _level_row("10y nominal", panel["DGS10"], "FRED DGS10, daily"),
        _level_row("30y nominal", panel["DGS30"], "FRED DGS30, daily"),
        _level_row("2y nominal", panel["DGS2"], "FRED DGS2, daily"),
        _level_row("3m bill (secondary market)", panel["DTB3"], "FRED DTB3, daily"),
        _level_row("fed funds effective", panel["DFF"], "FRED DFF, daily"),
        _level_row("10y breakeven inflation", panel["T10YIE"], "FRED T10YIE, daily"),
        _level_row(
            "slope: 10y - 3m", slope("DGS10", "DGS3MO"), "FRED DGS10-DGS3MO", units="pp"
        ),
        _level_row("slope: 10y - 2y", slope("DGS10", "DGS2"), "FRED DGS10-DGS2", units="pp"),
        _level_row("slope: 30y - 10y", slope("DGS30", "DGS10"), "FRED DGS30-DGS10", units="pp"),
        _level_row(
            "real slope: 30y - 10y",
            slope("DFII30", "DFII10"),
            "FRED DFII30-DFII10",
            units="pp",
        ),
    ]
    return pd.DataFrame(rows)


def credit_table(panel: FredPanel, spliced: Mapping[str, pd.Series[float]]) -> pd.DataFrame:
    """Credit spreads on every window the sources allow, which is the whole story."""
    quality = spliced["quality"].dropna()
    default = spliced["default"].dropna()
    rows = [
        _level_row(
            "IG corporate OAS",
            panel["BAMLC0A0CM"],
            "FRED BAMLC0A0CM, TRUNCATED to 3y",
            units="pp",
        ),
        _level_row(
            "high-yield OAS",
            panel["BAMLH0A0HYM2"],
            "FRED BAMLH0A0HYM2, TRUNCATED to 3y",
            units="pp",
        ),
        _level_row(
            "Moody's Baa - Aaa (quality)", quality, "FRED AAA/BAA + Goyal-Welch", units="pp"
        ),
        _level_row(
            "Moody's Baa - 10y (default)", default, "FRED BAA/GS10 + Goyal-Welch", units="pp"
        ),
        _level_row(
            "Moody's Baa - 10y, daily", panel["BAA10Y"], "FRED BAA10Y, from 1986", units="pp"
        ),
    ]
    frame = pd.DataFrame(rows)
    measures = (
        panel["BAMLC0A0CM"],
        panel["BAMLH0A0HYM2"],
        quality,
        default,
        panel["BAA10Y"],
    )
    for label, since in (("pct_since_1990", "1990-01"), ("pct_since_2010", "2010-01")):
        column: list[float] = []
        for series in measures:
            clean = series.dropna()
            window = clean[clean.index >= since]
            column.append(
                percentile_rank(window.to_numpy(), float(clean.iloc[-1]))
                if window.size
                else float("nan")
            )
        frame[label] = column
    return frame


def splice_levels(
    goyal: pd.DataFrame, panel: FredPanel
) -> dict[str, pd.Series[float]]:
    """Goyal-Welch level columns extended to 2026 with their own FRED sources.

    ``lty`` is Goyal-Welch's long-term government yield and it **is** ``GS10``: on
    2025-11 the workbook reads 4.09 and FRED ``GS10`` reads 4.09. ``tbl`` is ``TB3MS``
    (3.78 on the same month) and ``AAA``/``BAA`` are the Moody's series. The splice is
    therefore a continuation of the same series, not a join of two measurements.
    """
    extended: dict[str, pd.Series[float]] = {}
    for column, series_id in (("AAA", "AAA"), ("BAA", "BAA"), ("lty", "GS10"), ("tbl", "TB3MS")):
        base = goyal[column].dropna()
        tail = _to_month(panel[series_id]) / 100.0
        extended[column] = pd.concat([base, tail[tail.index > base.index[-1]]])
    cpi = _to_month(panel["CPIAUCSL"])
    fred_inflation = (cpi / cpi.shift(12) - 1.0).dropna()
    workbook_inflation = (
        (1.0 + goyal["infl"]).rolling(12).apply(np.prod, raw=True) - 1.0
    ).dropna()
    inflation = pd.concat(
        [
            workbook_inflation,
            fred_inflation[fred_inflation.index > workbook_inflation.index[-1]],
        ]
    )
    return {
        "quality": (extended["BAA"] - extended["AAA"]) * 100.0,
        "default": (extended["BAA"] - extended["lty"]) * 100.0,
        "term": (extended["lty"] - extended["tbl"]) * 100.0,
        "real_bill": (extended["tbl"] - inflation) * 100.0,
        "inflation": inflation * 100.0,
        "tbl": extended["tbl"] * 100.0,
    }


def cash_table(
    panel: FredPanel, spliced: Mapping[str, pd.Series[float]]
) -> pd.DataFrame:
    """The cash rate in real terms, ex-post and ex-ante, which disagree by 1.2 pp."""
    bill, breakeven = panel["DTB3"], panel["T10YIE"]
    shared = bill.index.intersection(breakeven.index)
    ex_ante = bill[shared] - breakeven[shared]
    real_bill = spliced["real_bill"].dropna()
    rows = [
        _level_row("nominal 3m bill (monthly avg)", spliced["tbl"], "FRED TB3MS"),
        _level_row(
            "trailing 12m CPI inflation",
            spliced["inflation"],
            "FRED CPIAUCSL + Goyal-Welch",
        ),
        _level_row(
            "real bill, ex-post (bill - trailing CPI)", real_bill, "derived", units="pp"
        ),
        _level_row(
            "real bill, ex-ante (bill - 10y breakeven)",
            ex_ante,
            "FRED DTB3 - T10YIE",
            units="pp",
        ),
    ]
    frame = pd.DataFrame(rows)
    post_2009 = real_bill[real_bill.index >= "2009-01"]
    frame.attrs["real_bill_pct_since_2009"] = percentile_rank(
        post_2009.to_numpy(), float(real_bill.iloc[-1])
    )
    frame.attrs["real_bill_mean_since_2009"] = float(post_2009.mean())
    frame.attrs["real_bill_positive_months_since_2009"] = int((post_2009 > 0.0).sum())
    frame.attrs["real_bill_months_since_2009"] = int(post_2009.size)
    return frame


# --------------------------------------------------------------------------------------
# 2. The value spread
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ValueSpread:
    """The US value spread by formation year, raw and marked to market."""

    by_formation_year: pd.Series[float]
    big: pd.Series[float]
    small: pd.Series[float]
    marked_to_market: float
    formation_year: int
    market_equity_date: str
    entry: CacheEntry


def value_spread(cache: RawCache) -> ValueSpread:
    """Ken French's own ``BE/ME`` averages, turned into a spread and priced forward."""
    file, entry = load_french_tables(cache, "french_us_6_portfolios_2x3")
    book_to_market = _frame(
        file,
        "for_portfolios_formed_in_june_of_year_t_value_weight_average_of_be_me_calculated_monthly",
    )
    returns = _frame(file, "average_value_weighted_returns_monthly")

    # The July row of year t is the first month of the June-t formation. Using June
    # would silently take the *previous* formation, whose ME is a further year old.
    july = book_to_market[[str(label).endswith("-07") for label in book_to_market.index]]
    july.index = pd.Index(int(str(label)[:4]) for label in july.index)
    big = pd.Series(
        {
            year: log_value_spread(row["BIG HiBM"], row["BIG LoBM"])
            for year, row in july.iterrows()
        }
    )
    small = pd.Series(
        {
            year: log_value_spread(row["SMALL HiBM"], row["SMALL LoBM"])
            for year, row in july.iterrows()
        }
    )
    combined = 0.5 * (big + small)

    formation_year = int(combined.index[-1])
    since_market_equity_date = _months_from(returns, f"{formation_year}-01")
    latest = {
        str(column): float(np.asarray(value, dtype=np.float64))
        for column, value in july.loc[formation_year].items()
    }
    adjustments = [
        mark_to_market_log_spread(
            log_value_spread(latest[high], latest[low]),
            growth_cumulative_return=float(
                np.prod(1.0 + since_market_equity_date[low].to_numpy())
            ),
            value_cumulative_return=float(
                np.prod(1.0 + since_market_equity_date[high].to_numpy())
            ),
        )
        for high, low in _VALUE_COLUMNS
    ]
    return ValueSpread(
        by_formation_year=combined,
        big=big,
        small=small,
        marked_to_market=float(np.mean(adjustments)),
        formation_year=formation_year,
        market_equity_date=f"{formation_year - 1}-12",
        entry=entry,
    )


def value_spread_table(spread: ValueSpread) -> pd.DataFrame:
    """The spread's level and percentile, raw and marked to market."""
    history = spread.by_formation_year.to_numpy()
    raw = float(spread.by_formation_year.iloc[-1])
    rows = [
        {
            "measure": "value spread, big caps",
            "log_spread": float(spread.big.iloc[-1]),
            "ratio": float(np.exp(spread.big.iloc[-1])),
            "percentile": percentile_rank(
                spread.big.to_numpy(), float(spread.big.iloc[-1])
            ),
        },
        {
            "measure": "value spread, small caps",
            "log_spread": float(spread.small.iloc[-1]),
            "ratio": float(np.exp(spread.small.iloc[-1])),
            "percentile": percentile_rank(
                spread.small.to_numpy(), float(spread.small.iloc[-1])
            ),
        },
        {
            "measure": f"combined, at formation (ME dated {spread.market_equity_date})",
            "log_spread": raw,
            "ratio": float(np.exp(raw)),
            "percentile": percentile_rank(history, raw),
        },
        {
            "measure": "combined, marked to market",
            "log_spread": spread.marked_to_market,
            "ratio": float(np.exp(spread.marked_to_market)),
            "percentile": percentile_rank(history, spread.marked_to_market),
        },
    ]
    frame = pd.DataFrame(rows)
    frame.attrs["n_years"] = int(spread.by_formation_year.size)
    frame.attrs["median_ratio"] = float(np.exp(spread.by_formation_year.median()))
    frame.attrs["formation_year"] = spread.formation_year
    return frame


# --------------------------------------------------------------------------------------
# 3. What each conditioning variable has predicted
# --------------------------------------------------------------------------------------


def _forward_log_returns(returns: FloatArray, horizon: int, periods_per_year: int) -> FloatArray:
    log_returns = np.log1p(returns)
    scale = periods_per_year / horizon
    return np.array(
        [
            log_returns[i + 1 : i + 1 + horizon].sum() * scale
            for i in range(log_returns.size - horizon)
        ]
    )


def _evidence(
    *,
    predictor_name: str,
    response_name: str,
    predictor: FloatArray,
    returns: FloatArray,
    horizon: int,
    periods_per_year: int,
    out_of_sample: float,
) -> PredictiveEvidence:
    forward = _forward_log_returns(returns, horizon, periods_per_year)
    usable = predictor[: forward.size]
    log_returns = np.log1p(returns)[: forward.size]
    one_period = (log_returns - log_returns.mean()) * (periods_per_year / horizon)
    ols = hac_ols(forward, usable.reshape(-1, 1), n_lags=horizon)
    hodrick = hodrick_1b_covariance(
        forward, usable, horizon_periods=horizon, one_period_residuals=one_period
    )
    slope = float(hodrick.coefficients[1])
    standard_error = float(hodrick.standard_errors[1])
    spread = float(np.std(usable))
    fitted = hodrick.coefficients[0] + slope * usable
    slope_per_sd = 100.0 * slope * spread
    detectable = 100.0 * minimum_detectable_slope(standard_error) * spread
    return PredictiveEvidence(
        predictor=predictor_name,
        response=response_name,
        horizon_years=horizon / periods_per_year,
        n_observations=int(forward.size),
        independent_observations=float(hodrick.independent_observations),
        slope_per_sd=slope_per_sd,
        minimum_detectable_per_sd=detectable,
        t_newey_west=float(ols.t_statistics[1]),
        t_hodrick_1b=slope / standard_error,
        r_squared=float(1.0 - np.var(forward - fitted) / np.var(forward)),
        r_squared_out_of_sample=out_of_sample,
        verdict=classify_evidence(
            t_hodrick_1b=slope / standard_error,
            r_squared_out_of_sample=out_of_sample,
            slope_per_sd=slope_per_sd,
            minimum_detectable_per_sd=detectable,
        ),
    )


def _out_of_sample_r2(
    predictor: FloatArray,
    returns: FloatArray,
    horizon: int,
    periods_per_year: int,
    *,
    minimum_training: int,
) -> float:
    """Expanding-window forecasts against an expanding-window mean.

    Only outcomes already *observed* at the forecast origin enter the training set, so
    the origin at ``i`` may use rows up to ``i - horizon`` and no further.
    """
    forward = _forward_log_returns(returns, horizon, periods_per_year)
    predicted: list[float] = []
    actual: list[float] = []
    benchmark: list[float] = []
    for index in range(forward.size):
        train = index - horizon
        if train < minimum_training:
            continue
        design = np.column_stack([np.ones(train), predictor[:train]])
        response = forward[:train]
        coefficients = np.linalg.lstsq(design, response, rcond=None)[0]
        predicted.append(float(coefficients[0] + coefficients[1] * predictor[index]))
        actual.append(float(forward[index]))
        benchmark.append(float(response.mean()))
    if not actual:  # pragma: no cover - guarded by minimum_training in every caller
        return float("nan")
    errors = np.asarray(actual) - np.asarray(predicted)
    base = np.asarray(actual) - np.asarray(benchmark)
    return float(1.0 - np.sum(errors**2) / np.sum(base**2))


def macro_evidence_table(
    goyal: pd.DataFrame, *, horizons_years: Sequence[int] = (1, 5)
) -> pd.DataFrame:
    """Every macro conditioner against every response, on the Goyal-Welch window."""
    inflation = (1.0 + goyal["infl"]).rolling(12).apply(np.prod, raw=True) - 1.0
    predictors = {
        "quality spread (Baa - Aaa)": goyal["BAA"] - goyal["AAA"],
        "default spread (Baa - 10y)": goyal["BAA"] - goyal["lty"],
        "term spread (10y - 3m bill)": goyal["lty"] - goyal["tbl"],
        "real bill (3m - trailing CPI)": goyal["tbl"] - inflation,
    }
    responses = {
        "equity excess": goyal["CRSP_SPvw"] - goyal["Rfree"],
        "long govt excess": goyal["ltr"] - goyal["Rfree"],
        "credit excess (corp - govt)": goyal["corpr"] - goyal["ltr"],
    }
    rows: list[PredictiveEvidence] = []
    for predictor_name, predictor_series in predictors.items():
        for response_name, response_series in responses.items():
            shared = predictor_series.dropna().index.intersection(
                response_series.dropna().index
            )
            predictor = predictor_series[shared].to_numpy(dtype=float)
            returns = response_series[shared].to_numpy(dtype=float)
            for years in horizons_years:
                horizon = years * MONTHS_PER_YEAR
                rows.append(
                    _evidence(
                        predictor_name=predictor_name,
                        response_name=response_name,
                        predictor=predictor,
                        returns=returns,
                        horizon=horizon,
                        periods_per_year=MONTHS_PER_YEAR,
                        out_of_sample=_out_of_sample_r2(
                            predictor, returns, horizon, MONTHS_PER_YEAR, minimum_training=120
                        ),
                    )
                )
    return pd.DataFrame([row.__dict__ for row in rows])


def value_spread_evidence_table(
    cache: RawCache, spread: ValueSpread, *, horizons_years: Sequence[int] = (1, 5, 10)
) -> pd.DataFrame:
    """Does a wide value spread predict a better subsequent value premium?"""
    file, _ = load_french_tables(cache, "french_us_ff3")
    monthly = next(table for table in file.tables if table.frequency == "monthly")
    factors = pd.DataFrame(
        list(monthly.values), index=list(monthly.periods), columns=list(monthly.columns)
    ).astype(float)
    hml = factors["HML"]

    # Alignment is the whole trick. The spread at formation year ``y`` is known at the
    # end of June ``y``; the return it is asked to predict runs July ``y`` to June
    # ``y + 1``. ``_forward_log_returns`` reads element ``i`` as the return realised
    # *during* period ``i``, so the return stored against ``y`` must be the one already
    # in the past at that point: July ``y - 1`` to June ``y``. Storing the forward
    # return here instead shifts every observation a year and destroys the relation.
    aligned: list[tuple[float, float]] = []
    months = pd.Index(hml.index)
    for year in (int(label) for label in spread.by_formation_year.index):
        window = hml[(months >= f"{year - 1}-07") & (months <= f"{year}-06")]
        if window.size != MONTHS_PER_YEAR:
            continue
        aligned.append(
            (
                float(spread.by_formation_year.loc[year]),
                float(np.expm1(np.log1p(window.to_numpy()).sum())),
            )
        )
    predictor = np.array([value for value, _ in aligned])
    returns = np.array([value for _, value in aligned])

    rows = [
        _evidence(
            predictor_name="US value spread",
            response_name="HML",
            predictor=predictor,
            returns=returns,
            horizon=years_ahead,
            periods_per_year=1,
            out_of_sample=_out_of_sample_r2(
                predictor, returns, years_ahead, 1, minimum_training=20
            ),
        )
        for years_ahead in horizons_years
    ]
    return pd.DataFrame([row.__dict__ for row in rows])


# --------------------------------------------------------------------------------------
# 4. Gold, which has no valuation ratio at all
# --------------------------------------------------------------------------------------


def real_gold_table(cache: RawCache, panel: FredPanel) -> pd.DataFrame:
    """The real gold price against its own record. Not a valuation; a level."""
    dataset = lbma.get_dataset("lbma_gold_pm")
    entry = cache.entry_for(dataset.url)
    if entry is None:  # pragma: no cover
        entry = lbma.download(cache, dataset)
    table = lbma.parse(cache, entry, dataset=dataset)
    month_end = dict(lbma.month_end_usd(table.table if hasattr(table, "table") else table))
    cpi = _to_month(panel["CPIAUCSL"]).dropna()
    latest_cpi = float(cpi.iloc[-1])
    real = pd.Series(
        {
            month: float(price) / float(cpi[month]) * latest_cpi
            for month, price in month_end.items()
            if month in cpi.index and month >= "1975-01"
        }
    )
    row = _level_row(
        "real gold price",
        real,
        "LBMA PM fix deflated by CPIAUCSL",
        units=f"USD/oz in {cpi.index[-1]} money",
    )
    frame = pd.DataFrame([row])
    frame.attrs["january_1980"] = float(real.get("1980-01", np.nan))
    frame.attrs["august_2011"] = float(real.get("2011-08", np.nan))
    frame.attrs["cache_sha256"] = entry.sha256
    return frame


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def show(frame: pd.DataFrame, *, digits: int = 3) -> None:
    with pd.option_context("display.width", 220, "display.max_columns", 40):
        print(frame.round(digits).to_string(index=False))


def main() -> None:
    """Print every table the synthesis quotes."""
    cache = RawCache(default_cache_root())
    panel = load_fred(cache)
    goyal, goyal_entry = load_goyal_welch(cache)
    spliced = splice_levels(goyal, panel)

    print("=== cache provenance ===")
    for series_id in FRED_SERIES:
        entry = panel.entries[series_id]
        print(
            f"  FRED {series_id:16s} sha256:{entry.sha256[:12]} "
            f"retrieved {entry.retrieved_utc}"
        )
    print(
        f"  Goyal-Welch          sha256:{goyal_entry.sha256[:12]} "
        f"retrieved {goyal_entry.retrieved_utc}"
    )

    print("\n=== 1. real rates, nominal levels and the curve ===")
    show(rates_table(panel))
    print("\n=== 2. credit ===")
    show(credit_table(panel, spliced))
    print("\n=== 3. cash in real terms ===")
    cash = cash_table(panel, spliced)
    show(cash)
    print(
        f"  real bill percentile since 2009: {cash.attrs['real_bill_pct_since_2009']:.3f}; "
        f"mean {cash.attrs['real_bill_mean_since_2009']:+.2f} pp; positive in "
        f"{cash.attrs['real_bill_positive_months_since_2009']} of "
        f"{cash.attrs['real_bill_months_since_2009']} months"
    )
    print("\n=== 4. the value spread ===")
    spread = value_spread(cache)
    table = value_spread_table(spread)
    show(table)
    print(
        f"  formation year {table.attrs['formation_year']}, {table.attrs['n_years']} years of "
        f"history, median ratio {table.attrs['median_ratio']:.2f}x"
    )
    print("\n=== 5. what each macro conditioner has predicted ===")
    show(macro_evidence_table(goyal))
    print("\n=== 6. what the value spread has predicted ===")
    show(value_spread_evidence_table(cache, spread))
    print("\n=== 7. gold, deflated ===")
    gold = real_gold_table(cache, panel)
    show(gold)
    print(
        f"  prior real peaks: 1980-01 {gold.attrs['january_1980']:,.0f}, "
        f"2011-08 {gold.attrs['august_2011']:,.0f}"
    )


if __name__ == "__main__":
    main()
