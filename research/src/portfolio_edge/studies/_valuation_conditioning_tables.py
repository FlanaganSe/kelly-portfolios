"""Regenerates the measured tables in ``docs/research/valuation-and-the-allocation.md``.

Kept separate from :mod:`portfolio_edge.studies.valuation_conditioning` so that the study
itself stays pure and testable and only this file touches the cache. Run it with

    uv run python -m portfolio_edge.studies.valuation_conditioning

Four data notes that decide how far the output may be trusted.

**The US series is Shiller's ``ie_data`` workbook**, cached at
``sha256:71c3636d…`` with ``Last-Modified: Tue, 04 Aug 2026 15:29:32 GMT``. Its final row
is dated 2026-08 and the workbook's own footnote says *"Aug price is Aug 1st close … Aug
GS10 is Jul 31st value"*. So the published CAPE of 41.18 is an **August 1st** reading, not
a reading for the day this study is run, and :func:`~portfolio_edge.studies.
valuation_conditioning.rescale_cape_for_price` exists to move it. The workbook is also not
point-in-time: the whole file is rebuilt on each release, so every "expanding window"
below uses a *revised* history that the historical investor did not have. That biases the
conditional rules **in their own favour** and the rules still lose.

**The bond leg is Shiller's own real total bond return**, a modelled ten-year series
carried in the same workbook. It is not a fund, it holds no bid/ask and no tax, and it is
the same modelling class as the bond leg in ``docs/research/setting-the-equity-share.md``.

**The international panel is Jorda-Schularick-Taylor R6**, whose valuation variable is a
**dividend yield**, not a CAPE, and whose returns are **local-currency real**. Two
consequences and both matter. A US investor in non-US equity bears currency, which this
panel does not measure. And the dividend yield became a structurally different quantity in
the US when buybacks became the majority of payout, which is exactly the era in which the
cross-sectional relation stops being detectable here. The panel also ends in **2020**, so
it can measure the historical relation and cannot supply the current spread.

**The real yield is FRED ``DFII10``**, the ten-year TIPS constant-maturity yield, refetched
on each run. It begins in **2003**, so the TIPS-based excess CAPE yield has a 23-year
history and not a 145-year one, and any percentile taken on it says so.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import french, macrohistory, shiller
from portfolio_edge.data.cache import CacheEntry, RawCache, default_cache_root
from portfolio_edge.inference.hac import hac_ols
from portfolio_edge.studies.outperformance_horizon import (
    detectable_edge_bp,
    horizon_for_confidence,
    probability_of_outperformance,
    terminal_wealth_ratio,
)
from portfolio_edge.studies.valuation_conditioning import (
    MONTHS_PER_YEAR,
    ConditionalWeightRule,
    TiltCost,
    break_even_tax_rate,
    conditional_weight,
    derisking_regret_bp,
    excess_cape_yield,
    hodrick_1b_covariance,
    out_of_sample_r2,
    overlap_adjusted_observations,
    stambaugh_bias,
    tilt_net_edge_bp,
)

#: Months of history required before an expanding-window percentile is used at all.
BURN_IN_MONTHS: Final = 40 * MONTHS_PER_YEAR

#: Horizons reported, in years.
HORIZONS: Final = (1, 5, 10, 15)

#: The equity share the conditional rules tilt around. Chosen to sit inside the range
#: ``docs/research/setting-the-equity-share.md`` discusses; this study takes no position
#: on the level and only asks whether *conditioning* it helps.
BASE_EQUITY_WEIGHT: Final = 0.80

TIPS_URL: Final = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10"
NOMINAL_URL: Final = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"


# --------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class UsPanel:
    """The Shiller series this study uses, aligned and non-null."""

    period: pd.Index
    cape: FloatArray
    total_return_cape: FloatArray
    shiller_excess_cape_yield: FloatArray
    equity_log_real: FloatArray
    bond_log_real: FloatArray
    log_real_wealth: FloatArray
    price: FloatArray
    cpi: FloatArray
    entry: CacheEntry


def _column(frame: pd.DataFrame, name: str, keep: pd.Series[bool]) -> FloatArray:
    """One workbook column as a float64 array, restricted to the aligned months."""
    return np.asarray(frame[name].astype(float)[keep].to_numpy(), dtype=np.float64)


def load_us(cache: RawCache) -> UsPanel:
    """Shiller's workbook, restricted to months where every column used exists."""
    dataset = shiller.get_dataset("shiller_ie_data")
    entry = cache.require(dataset.url)
    frame = shiller.parse(cache, entry, dataset=dataset).table.to_frame()
    cape = frame["CAPE"].astype(float)
    equity = frame["Real_Total_Return_Price"].astype(float)
    bond = frame["Real_Total_Bond_Returns"].astype(float)
    keep = cape.notna() & equity.notna() & bond.notna()
    log_equity = np.log(equity[keep].to_numpy(dtype=float))
    log_bond = np.log(bond[keep].to_numpy(dtype=float))
    return UsPanel(
        period=pd.Index(cape.index[keep]),
        cape=_column(frame, "CAPE", keep),
        total_return_cape=_column(frame, "TR_CAPE", keep),
        shiller_excess_cape_yield=100.0 * _column(frame, "Excess_CAPE_Yield", keep),
        equity_log_real=np.diff(log_equity),
        bond_log_real=np.diff(log_bond),
        log_real_wealth=log_equity,
        price=_column(frame, "P", keep),
        cpi=_column(frame, "CPI", keep),
        entry=entry,
    )


def load_real_yield(
    cache: RawCache, url: str = TIPS_URL, *, force: bool = True
) -> pd.Series[float]:
    """A FRED daily constant-maturity yield as a ``Series`` indexed by ``YYYY-MM-DD``."""
    entry = cache.fetch(url, force=force, timeout=60.0)
    rows = list(csv.reader(io.StringIO(cache.read(entry).decode())))[1:]
    return pd.Series(
        {row[0]: float(row[1]) for row in rows if row[1] not in (".", "")}, dtype=float
    )


# --------------------------------------------------------------------------------------
# 1. Where valuations are
# --------------------------------------------------------------------------------------


def expanding_percentile(values: FloatArray, burn_in: int) -> FloatArray:
    """Percentile of each observation within the history ending at it.

    Strictly backward-looking, which is the whole point: a percentile taken against the
    full sample hands the 1955 investor a distribution containing 2026.
    """
    out = np.full(values.size, np.nan)
    for index in range(burn_in, values.size):
        window = values[: index + 1]
        out[index] = float(np.mean(window < values[index]))
    return out


def level_table(
    us: UsPanel, tips: pd.Series[float], nominal: pd.Series[float]
) -> pd.DataFrame:
    """Current levels beside their own history, and the two excess-yield measures."""
    cape = us.cape
    current = float(cape[-1])
    tips_last_date, tips_last = str(tips.index[-1]), float(tips.iloc[-1])
    nominal_last = float(nominal.iloc[-1])
    tr_cape = us.total_return_cape[~np.isnan(us.total_return_cape)]
    shiller_ecy = us.shiller_excess_cape_yield
    rows = [
        {
            "measure": "CAPE (Shiller, 2026-08 row)",
            "value": current,
            "full_sample_percentile": float(np.mean(cape < current)),
            "note": f"months at or above it: {int(np.sum(cape >= current))} of {cape.size}",
        },
        {
            "measure": "total-return CAPE",
            "value": float(tr_cape[-1]),
            "full_sample_percentile": float(np.mean(tr_cape < tr_cape[-1])),
            "note": f"max {tr_cape.max():.2f}",
        },
        {
            "measure": "CAPE earnings yield, %/yr",
            "value": 100.0 / current,
            "full_sample_percentile": float(np.mean(100.0 / cape < 100.0 / current)),
            "note": "not an expected return: it assumes flat real earnings per share",
        },
        {
            "measure": "Shiller excess CAPE yield, pp",
            "value": float(shiller_ecy[-1]),
            "full_sample_percentile": float(np.mean(shiller_ecy < shiller_ecy[-1])),
            "note": "against a trailing-inflation-adjusted nominal 10y",
        },
        {
            "measure": "TIPS excess CAPE yield, pp",
            "value": excess_cape_yield(cape=current, real_yield_percent=tips_last),
            "full_sample_percentile": float("nan"),
            "note": f"against DFII10 {tips_last:.2f}% on {tips_last_date}; TIPS begin 2003",
        },
        {
            "measure": "10y nominal (DGS10), %",
            "value": nominal_last,
            "full_sample_percentile": float("nan"),
            "note": f"as of {nominal.index[-1]}",
        },
        {
            "measure": "10y TIPS real (DFII10), %",
            "value": tips_last,
            "full_sample_percentile": float("nan"),
            "note": f"as of {tips_last_date}",
        },
    ]
    return pd.DataFrame(rows)


def tips_excess_yield_history(us: UsPanel, tips: pd.Series[float]) -> pd.DataFrame:
    """Month-end TIPS-based excess CAPE yield, 2003 to now, with its own percentile."""
    monthly = tips.groupby([d[:7] for d in tips.index]).mean()
    cape = pd.Series(us.cape, index=[str(p) for p in us.period])
    joined = pd.DataFrame({"cape": cape}).join(monthly.rename("tips"), how="inner")
    joined["tips_excess_cape_yield"] = 100.0 / joined["cape"] - joined["tips"]
    series = joined["tips_excess_cape_yield"]
    joined["percentile_since_2003"] = [
        float(np.mean(series[: i + 1] < v)) for i, v in enumerate(series)
    ]
    return joined


# --------------------------------------------------------------------------------------
# 2. What valuation predicts
# --------------------------------------------------------------------------------------


def _predictive_rows(log_wealth: FloatArray, predictor: FloatArray) -> list[dict[str, float]]:
    """One row per horizon: the same regression under three inference methods.

    ``log_wealth`` has one more element than the return series it came from, so a slice
    of length ``n - h`` lines up with the predictor observed at the forecast origin.
    """
    one_month = np.diff(log_wealth)
    rows: list[dict[str, float]] = []
    for horizon in HORIZONS:
        months = horizon * MONTHS_PER_YEAR
        response = (log_wealth[months:] - log_wealth[:-months]) / horizon
        regressor = predictor[:-months]
        demeaned = np.append((one_month - one_month.mean()) / horizon, 0.0)[: predictor.size]
        newey = hac_ols(response, regressor, n_lags=months)
        hodrick = hodrick_1b_covariance(
            response,
            regressor,
            horizon_periods=months,
            one_period_residuals=demeaned[:-months],
        )
        non_overlapping = hac_ols(response[::months], regressor[::months], n_lags=0)
        rows.append(
            {
                "horizon_years": float(horizon),
                "n_overlapping": float(response.size),
                "n_independent": overlap_adjusted_observations(response.size, months),
                "slope": float(newey.coefficients[1]),
                "t_newey_west": float(newey.t_statistics[1]),
                "t_hodrick_1b": float(hodrick.t_statistics[1]),
                "t_non_overlapping": float(non_overlapping.t_statistics[1]),
                "r2_in_sample": 1.0 - float(np.var(newey.residuals)) / float(np.var(response)),
            }
        )
    return rows


def predictive_table(us: UsPanel) -> pd.DataFrame:
    """CAPE yield against subsequent annualised real log return, three inference methods.

    The point estimate is one number. The standard error is three, and they disagree by
    a factor of two at the horizons that matter. That disagreement is the result.
    """
    return pd.DataFrame(_predictive_rows(us.log_real_wealth, np.log(1.0 / us.cape)))


def french_robustness_table(cache: RawCache, us: UsPanel) -> pd.DataFrame:
    """The same regression with a **month-end** response instead of a monthly-averaged one.

    Shiller's ``P`` is the average of the month's daily closes, and averaging induces
    positive autocorrelation that a serial-correlation-dependent rule reads as signal —
    the source-fitness finding recorded in ``docs/research/evidence-base.md``. An
    overlapping long-horizon regression is a different construction from a moving-average
    rule, but it is in the same family of tests, so the check is owed rather than assumed.

    The response here is Ken French's ``Mkt-RF + RF``, a value-weighted CRSP total return
    dated to month-end, deflated by the same CPI. **Two things change at once**: the
    dating *and* the universe, since French covers all of CRSP where Shiller covers the
    S&P composite. The ``ar1_*`` columns isolate the dating, which is the part at issue;
    the slope comparison cannot separate them and the page says so.
    """
    dataset = french.get_dataset("french_us_ff3")
    parsed = french.parse(cache, cache.require(dataset.url), dataset=dataset)
    monthly = next(t for t in parsed.tables if t.table_id == "monthly").to_frame()
    nominal = pd.Series(
        (monthly["Mkt-RF"].astype(float) + monthly["RF"].astype(float)).to_numpy(dtype=float),
        index=[str(p) for p in monthly.index],
    )
    shiller_months = [str(p) for p in us.period]
    cpi_index = pd.Series(us.cpi, index=shiller_months)
    inflation = (cpi_index / cpi_index.shift(1) - 1.0).reindex(nominal.index)
    french_real = pd.Series(
        np.log((1.0 + nominal) / (1.0 + inflation)), index=nominal.index
    ).dropna()

    shiller_real = pd.Series(np.diff(us.log_real_wealth), index=shiller_months[1:])
    common = french_real.index.intersection(shiller_real.index)
    predictor_by_month = pd.Series(np.log(1.0 / us.cape), index=shiller_months)

    rows = []
    for label, series in (
        ("French month-end", french_real[common]),
        ("Shiller monthly-average", shiller_real[common]),
    ):
        values = series.to_numpy(dtype=np.float64)
        # ``wealth[t]`` is the cumulative log real return through the **end** of month t,
        # and ``predictor[t]`` is the CAPE for month t, so the response never overlaps
        # the window its own predictor was measured over. Same alignment as
        # :func:`predictive_table`.
        wealth = np.asarray(np.cumsum(values), dtype=np.float64)
        predictor = np.asarray(
            predictor_by_month.reindex(list(series.index)).to_numpy(), dtype=np.float64
        )
        ar1 = float(np.corrcoef(values[1:], values[:-1])[0, 1])
        for row in _predictive_rows(wealth, predictor):
            rows.append(
                {
                    "series": label,
                    "ar1_monthly": ar1,
                    "annualised_sd_pc": 100.0 * float(np.std(values)) * np.sqrt(MONTHS_PER_YEAR),
                    **row,
                }
            )
    return pd.DataFrame(rows)


def stambaugh_table(us: UsPanel) -> pd.DataFrame:
    """The one-month predictive slope, and how much of it is small-sample bias."""
    predictor = np.log(1.0 / us.cape)
    one_month = np.diff(log_wealth := us.log_real_wealth)
    del log_wealth
    predictive = hac_ols(one_month, predictor[:-1], n_lags=0)
    autoregression = hac_ols(predictor[1:], predictor[:-1], n_lags=0)
    root = float(autoregression.coefficients[1])
    innovations = autoregression.residuals
    bias = stambaugh_bias(
        innovation_covariance=float(np.cov(predictive.residuals, innovations, ddof=0)[0, 1]),
        predictor_innovation_variance=float(np.var(innovations, ddof=0)),
        autoregressive_root=root,
        n_observations=one_month.size,
    )
    fitted = float(predictive.coefficients[1])
    return pd.DataFrame(
        [
            {
                "autoregressive_root_monthly": root,
                "innovation_correlation": float(
                    np.corrcoef(predictive.residuals, innovations)[0, 1]
                ),
                "slope_monthly": fitted,
                "bias": bias,
                "bias_share_of_slope": bias / fitted,
                "slope_corrected_annualised": MONTHS_PER_YEAR * (fitted - bias),
                "slope_uncorrected_annualised": MONTHS_PER_YEAR * fitted,
            }
        ]
    )


def out_of_sample_table(
    us: UsPanel, first_origins: tuple[str, ...] = ("", "1965-01", "1990-01")
) -> pd.DataFrame:
    """The expanding-window forecast record against an expanding historical mean.

    Every coefficient and every benchmark mean is fitted only on outcomes already
    *observed* at the forecast origin, which for a horizon of ``h`` years means the last
    usable training origin is ``h`` years before the forecast. Skipping that step is the
    commonest way a valuation backtest is accidentally given the answer.
    """
    log_wealth = us.log_real_wealth
    predictor = np.log(1.0 / us.cape)
    rows = []
    for horizon in HORIZONS:
        months = horizon * MONTHS_PER_YEAR
        response = (log_wealth[months:] - log_wealth[:-months]) / horizon
        regressor = predictor[: response.size]
        origins = us.period[: response.size]
        for first in first_origins:
            realised, model, benchmark = [], [], []
            for index in range(30 * MONTHS_PER_YEAR, response.size):
                if first and str(origins[index]) < first:
                    continue
                trainable = index - months
                if trainable < 24:
                    continue
                design = np.column_stack([np.ones(trainable + 1), regressor[: trainable + 1]])
                coefficients = np.linalg.lstsq(design, response[: trainable + 1], rcond=None)[0]
                realised.append(response[index])
                model.append(coefficients[0] + coefficients[1] * regressor[index])
                benchmark.append(float(np.mean(response[: trainable + 1])))
            if not realised:
                continue
            score = out_of_sample_r2(realised, model, benchmark, horizon_periods=months)
            rows.append(
                {
                    "horizon_years": horizon,
                    "origins_from": first or str(origins[30 * MONTHS_PER_YEAR]),
                    "n_forecasts": score.n_forecasts,
                    "n_independent": score.independent_forecasts,
                    "r2_out_of_sample": score.r2_out_of_sample,
                    "model_mean_error_pp": 100.0 * score.mean_model_error,
                    "benchmark_mean_error_pp": 100.0 * score.mean_benchmark_error,
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# 3. Does conditioning the weight help
# --------------------------------------------------------------------------------------


def _walk(
    weights: FloatArray,
    equity: FloatArray,
    bond: FloatArray,
    *,
    spread_bp: float,
    capital_gains_rate: float,
) -> tuple[FloatArray, float]:
    """Monthly log returns of a portfolio driven to ``weights``, and its annual turnover.

    Trading cost is charged on the traded fraction and capital-gains tax only on the
    equity **sold**, because only a sale realises a gain. Drift between decisions is free,
    which is why the constant-mix control still turns over: a constant weight is itself a
    rebalancing rule.
    """
    held = float(weights[0])
    out = np.empty(weights.size)
    traded = 0.0
    for index in range(weights.size):
        target = float(weights[index])
        change = abs(target - held)
        traded += change
        drag = change * spread_bp / 1e4 + max(0.0, held - target) * capital_gains_rate
        gross = target * equity[index] + (1.0 - target) * bond[index]
        out[index] = gross + (float(np.log1p(-drag)) if drag > 0.0 else 0.0)
        grown_equity = target * np.exp(equity[index])
        grown_bond = (1.0 - target) * np.exp(bond[index])
        held = float(grown_equity / (grown_equity + grown_bond))
    return out, traded / (weights.size / MONTHS_PER_YEAR)


def rule_weights(us: UsPanel) -> tuple[dict[str, FloatArray], FloatArray, FloatArray, pd.Index]:
    """The rules compared, all on expanding-window percentiles with no look-ahead."""
    n_returns = us.equity_log_real.size
    cape_percentile = expanding_percentile(us.cape, BURN_IN_MONTHS)[:n_returns]
    ecy_percentile = expanding_percentile(us.shiller_excess_cape_yield, BURN_IN_MONTHS)[:n_returns]
    start = BURN_IN_MONTHS
    cheap_by_cape = 1.0 - cape_percentile[start:]
    cheap_by_ecy = ecy_percentile[start:]
    rules: dict[str, FloatArray] = {"constant": np.full(cheap_by_cape.size, BASE_EQUITY_WEIGHT)}
    for sensitivity in (0.4, 0.8):
        for label, signal in (("CAPE level", cheap_by_cape), ("excess CAPE yield", cheap_by_ecy)):
            rule = ConditionalWeightRule(BASE_EQUITY_WEIGHT, sensitivity)
            rules[f"{label} tilt k={sensitivity}"] = np.array(
                [conditional_weight(rule, float(p)) for p in signal]
            )
    # The control that decides what the excess-yield signal is made of. Its regressor is
    # the real yield Shiller's own column implies, `100/CAPE - ECY`, with no valuation
    # term at all. If this reproduced the excess-yield rule's edge, that rule would be a
    # bond-cheapness bet wearing a valuation label. It does not.
    implied_real_yield = 100.0 / us.cape - us.shiller_excess_cape_yield
    cheap_by_yield = expanding_percentile(implied_real_yield, BURN_IN_MONTHS)[:n_returns][
        start:
    ]
    rules["real yield only, k=0.4"] = np.array(
        [
            conditional_weight(ConditionalWeightRule(BASE_EQUITY_WEIGHT, 0.4), float(p))
            for p in cheap_by_yield
        ]
    )
    rules["halve above the CAPE median"] = np.where(cheap_by_cape < 0.5, 0.40, 1.00)
    return (
        rules,
        us.equity_log_real[start:],
        us.bond_log_real[start:],
        us.period[start:n_returns],
    )


def conditioning_table(us: UsPanel) -> pd.DataFrame:
    """Does conditioning the equity share on valuation beat not conditioning it?

    Three columns decide it. ``gross_vs_constant`` asks whether the rule beat a constant
    80/20 at all. ``timing_vs_matched`` asks the fairer question — whether it beat a
    constant mix held at the rule's *own average weight*, which strips out the part of
    any answer that is really just "held less equity". ``net_vs_constant`` charges 10 bp
    of execution and a 15% effective rate on realised gains.
    """
    rules, equity, bond, _ = rule_weights(us)
    base_gross, _ = _walk(rules["constant"], equity, bond, spread_bp=0.0, capital_gains_rate=0.0)
    base_net, _ = _walk(rules["constant"], equity, bond, spread_bp=10.0, capital_gains_rate=0.15)
    rows = []
    for label, weights in rules.items():
        gross, turnover = _walk(weights, equity, bond, spread_bp=0.0, capital_gains_rate=0.0)
        net, _ = _walk(weights, equity, bond, spread_bp=10.0, capital_gains_rate=0.15)
        matched, _ = _walk(
            np.full(weights.size, float(weights.mean())),
            equity,
            bond,
            spread_bp=0.0,
            capital_gains_rate=0.0,
        )
        difference = gross - base_gross
        edge_bp = 1e4 * MONTHS_PER_YEAR * float(difference.mean())
        tracking_bp = 1e4 * float(difference.std()) * np.sqrt(MONTHS_PER_YEAR)
        rows.append(
            {
                "rule": label,
                "mean_weight": float(weights.mean()),
                "annual_turnover": turnover,
                "gross_vs_constant_bp": edge_bp,
                "timing_vs_matched_bp": 1e4 * MONTHS_PER_YEAR * float((gross - matched).mean()),
                "net_vs_constant_bp": 1e4 * MONTHS_PER_YEAR * float((net - base_net).mean()),
                "tracking_error_bp": tracking_bp,
                "mde_30y_bp": detectable_edge_bp(
                    tracking_error_bp=tracking_bp, horizon_years=30.0, confidence=0.90
                )
                if tracking_bp > 0.0
                else 0.0,
                "years_to_90pc_confidence": horizon_for_confidence(
                    edge_bp=edge_bp, tracking_error_bp=tracking_bp, confidence=0.90
                )
                if edge_bp > 0.0
                else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def rolling_window_table(us: UsPanel, window_years: int = 30) -> pd.DataFrame:
    """The distribution of the rule-minus-constant outcome, not its point estimate.

    An investor gets one draw. The right question is not "what was the mean" but "over how
    many of the 30-year lives this sample contains would the rule have helped", and the
    honest caveat is that these windows overlap almost completely: 908 of them come from
    about 3.5 independent 30-year blocks.
    """
    rules, equity, bond, _ = rule_weights(us)
    months = window_years * MONTHS_PER_YEAR
    base_gross, _ = _walk(rules["constant"], equity, bond, spread_bp=0.0, capital_gains_rate=0.0)
    base_net, _ = _walk(rules["constant"], equity, bond, spread_bp=10.0, capital_gains_rate=0.15)
    rows = []
    for label, weights in rules.items():
        if label == "constant":
            continue
        gross, _ = _walk(weights, equity, bond, spread_bp=0.0, capital_gains_rate=0.0)
        net, _ = _walk(weights, equity, bond, spread_bp=10.0, capital_gains_rate=0.15)
        starts = range(gross.size - months + 1)
        gross_diff = np.array(
            [
                1e4 * MONTHS_PER_YEAR * (gross[s : s + months] - base_gross[s : s + months]).mean()
                for s in starts
            ]
        )
        net_diff = np.array(
            [
                1e4 * MONTHS_PER_YEAR * (net[s : s + months] - base_net[s : s + months]).mean()
                for s in starts
            ]
        )
        rows.append(
            {
                "rule": label,
                "n_windows": gross_diff.size,
                "n_independent": gross_diff.size / months,
                "gross_p10_bp": float(np.percentile(gross_diff, 10)),
                "gross_median_bp": float(np.median(gross_diff)),
                "gross_p90_bp": float(np.percentile(gross_diff, 90)),
                "gross_share_ahead": float(np.mean(gross_diff > 0.0)),
                "net_p10_bp": float(np.percentile(net_diff, 10)),
                "net_median_bp": float(np.median(net_diff)),
                "net_p90_bp": float(np.percentile(net_diff, 90)),
                "net_share_ahead": float(np.mean(net_diff > 0.0)),
            }
        )
    return pd.DataFrame(rows)


def conditioning_era_table(us: UsPanel) -> pd.DataFrame:
    """The gross edge of each rule, split by era.

    A rule with a positive full-sample edge and one era of the wrong sign is a different
    object from a rule with a positive edge everywhere, and the difference does not show
    up in a full-sample mean. Gross only: the point is the signal's stability, not its
    net value, which §3's cost table settles separately.
    """
    rules, equity, bond, periods = rule_weights(us)
    base, _ = _walk(rules["constant"], equity, bond, spread_bp=0.0, capital_gains_rate=0.0)
    labels = np.array([str(p) for p in periods])
    eras = (
        ("1921-1950", "1900-00", "1950-01"),
        ("1950-1980", "1950-01", "1980-01"),
        ("1980-2000", "1980-01", "2000-01"),
        ("2000-", "2000-01", "9999-99"),
    )
    rows = []
    for label, weights in rules.items():
        if label == "constant":
            continue
        gross, _ = _walk(weights, equity, bond, spread_bp=0.0, capital_gains_rate=0.0)
        record: dict[str, object] = {"rule": label}
        for era, low, high in eras:
            window = (labels >= low) & (labels < high)
            record[era] = 1e4 * MONTHS_PER_YEAR * float((gross[window] - base[window]).mean())
        rows.append(record)
    return pd.DataFrame(rows)


def cost_sensitivity_table(us: UsPanel) -> pd.DataFrame:
    """At what effective capital-gains rate does the best rule stop paying?

    The gross edge and the turnover both come from the measured backtest; only the tax
    rate varies. The break-even is the decision-relevant number because it is a statement
    about the *account*, not about the market: below it the rule belongs in a sheltered
    account, above it the rule belongs nowhere.

    The turnover charged is the rule's turnover **less the constant-mix control's**,
    because the control is not a buy-and-hold portfolio: holding a fixed 80/20 through
    1921-2026 itself turns over 6.1% a year and pays tax on it. Charging the rule its
    gross turnover would compare a taxed rule with an untaxed benchmark, which is the
    same error as comparing results measured against different benchmarks. With the
    incremental figure this closed form reproduces the path simulation in
    :func:`conditioning_table` to within a basis point, which is the check that the two
    are costing the same thing.
    """
    table = conditioning_table(us)
    baseline = float(table.loc[table.rule == "constant", "annual_turnover"].iloc[0])
    rows = []
    for row in table.to_dict(orient="records"):
        if row["rule"] == "constant":
            continue
        incremental = max(0.0, float(row["annual_turnover"]) - baseline)
        gross = float(row["gross_vs_constant_bp"])

        def cost_at(rate: float, turnover: float = incremental) -> TiltCost:
            return TiltCost(
                annual_turnover=turnover,
                spread_and_commission_bp=10.0,
                effective_capital_gains_rate=rate,
            )

        rows.append(
            {
                "rule": row["rule"],
                "gross_edge_bp": gross,
                "turnover_over_control": incremental,
                "break_even_effective_cgt": break_even_tax_rate(
                    gross_edge_bp=gross, cost=cost_at(0.0)
                ),
                **{
                    f"net_bp_at_cgt_{int(100 * rate):02d}": tilt_net_edge_bp(
                        gross_edge_bp=gross, cost=cost_at(rate)
                    )
                    for rate in (0.0, 0.05, 0.10, 0.15, 0.20)
                },
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# 4. Valuation as a risk statement rather than a forecast
# --------------------------------------------------------------------------------------


def conditional_distribution_table(us: UsPanel) -> pd.DataFrame:
    """The distribution of subsequent real returns given the entry CAPE.

    Reported instead of a point forecast because the decision the investor faces is about
    the left tail and about holdability, not about the mean. The ``n_independent`` column
    is the reason the table cannot be read as a probability: the whole ``CAPE > 30``
    bucket is drawn from two episodes.
    """
    log_wealth = us.log_real_wealth
    rows = []
    for horizon in (10, 15, 20):
        months = horizon * MONTHS_PER_YEAR
        realised = 100.0 * (np.exp((log_wealth[months:] - log_wealth[:-months]) / horizon) - 1.0)
        entry = us.cape[:-months]
        origins = us.period[:-months]
        buckets = (
            ("CAPE > 30", entry > 30.0),
            ("CAPE 25-30", (entry >= 25.0) & (entry <= 30.0)),
            ("CAPE < 25", entry < 25.0),
            ("all", np.ones(entry.size, dtype=bool)),
        )
        for label, mask in buckets:
            if int(mask.sum()) < 12:
                continue
            values = realised[mask]
            rows.append(
                {
                    "horizon_years": horizon,
                    "bucket": label,
                    "n_months": int(mask.sum()),
                    "n_independent": overlap_adjusted_observations(int(mask.sum()), months),
                    "distinct_years": len({str(p)[:4] for p in origins[mask]}),
                    "min": float(values.min()),
                    "p10": float(np.percentile(values, 10)),
                    "median": float(np.median(values)),
                    "mean": float(values.mean()),
                    "p90": float(np.percentile(values, 90)),
                    "share_negative": float(np.mean(values < 0.0)),
                }
            )
    return pd.DataFrame(rows)


def drought_table(us: UsPanel, horizon: int = 15) -> pd.DataFrame:
    """How long a buyer at a given valuation spent below their own real entry price.

    This is the holdability statistic, and it is the one place where the entry valuation
    says something a return forecast does not. A portfolio that ends well but spends most
    of fifteen years underwater in real terms is a portfolio the investor may not still be
    holding at the end.
    """
    log_wealth = us.log_real_wealth
    months = horizon * MONTHS_PER_YEAR
    entry = us.cape[:-months]
    rows = []
    for label, mask in (("CAPE > 30", entry > 30.0), ("CAPE < 20", entry < 20.0)):
        drawdowns, underwater = [], []
        for index in np.flatnonzero(mask):
            path = log_wealth[index : index + months + 1] - log_wealth[index]
            drawdowns.append(
                100.0 * float(np.min(np.exp(path - np.maximum.accumulate(path)) - 1.0))
            )
            underwater.append(100.0 * float(np.mean(path < 0.0)))
        rows.append(
            {
                "bucket": label,
                "n_months": int(mask.sum()),
                "n_independent": overlap_adjusted_observations(int(mask.sum()), months),
                "median_worst_real_drawdown": float(np.median(drawdowns)),
                "worst_real_drawdown": float(np.min(drawdowns)),
                "median_share_below_entry": float(np.median(underwater)),
                "p90_share_below_entry": float(np.percentile(underwater, 90)),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# 5. The cross-sectional estimand
# --------------------------------------------------------------------------------------


def _jst_panel(cache: RawCache) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    dataset = macrohistory.get_dataset("jst_macrohistory_r6")
    parsed = macrohistory.parse(cache, cache.require(dataset.url), dataset=dataset)
    tables = {table.table_id: table.to_frame() for table in parsed.tables}
    yields = tables["equity_dividend_yield"].astype(float)
    # A yield below 15 bp or above 25% is a reporting artifact in this panel, not a
    # valuation. Portugal 2020 prints 0.04%, which would dominate any log spread.
    yields = yields.where((yields > 0.0015) & (yields < 0.25))
    total = tables["equity_total_return"].astype(float)
    prices = tables["consumer_prices"].astype(float)
    real = pd.DataFrame(
        np.log((1.0 + total) / (1.0 + prices.pct_change())),
        index=total.index,
        columns=total.columns,
    ).replace([np.inf, -np.inf], np.nan)
    peers = [c for c in yields.columns if c != "USA" and int(yields[c].notna().sum()) > 80]
    return yields, real, peers


def _log_spread(yields: pd.DataFrame, peers: list[str]) -> pd.Series[float]:
    """``log(dp_US) - median_i log(dp_i)``: the US's valuation against the panel's middle.

    A median rather than a mean, because the panel carries reporting artifacts at both
    ends and a single mis-scaled country would otherwise set the spread on its own.
    """
    us = pd.Series(np.log(yields["USA"].to_numpy(dtype=float)), index=yields.index)
    panel = pd.DataFrame(
        np.log(yields[peers].to_numpy(dtype=float)), index=yields.index, columns=peers
    )
    return us - panel.median(axis=1)


def cross_section_table(cache: RawCache) -> pd.DataFrame:
    """US minus the developed-panel median: relative yield against relative real return.

    This is the estimand behind the regional split, and it is a different object from the
    US time series above. Its identification is cross-sectional, so it does not depend on
    the level of any market drifting, which is the defect that sinks the time-series call.

    Local-currency real returns. A US investor bears the currency and this panel does not
    price it.
    """
    yields, real, peers = _jst_panel(cache)
    rows = []
    for horizon in HORIZONS:
        forward = real.rolling(horizon).sum().shift(-horizon) / horizon
        response = forward["USA"] - forward[peers].median(axis=1)
        spread = _log_spread(yields, peers)
        mask = response.notna() & spread.notna() & np.isfinite(response) & np.isfinite(spread)
        fit = hac_ols(
            response[mask].to_numpy(dtype=float),
            spread[mask].to_numpy(dtype=float),
            n_lags=max(1, int(1.5 * horizon)),
        )
        rows.append(
            {
                "horizon_years": horizon,
                "n_years": int(mask.sum()),
                "n_independent": overlap_adjusted_observations(int(mask.sum()), horizon),
                "intercept": float(fit.coefficients[0]),
                "slope": float(fit.coefficients[1]),
                "t_statistic": float(fit.t_statistics[1]),
                "r2": 1.0
                - float(np.var(fit.residuals))
                / float(np.var(response[mask].to_numpy(dtype=float))),
                "residual_sd_pp": 100.0 * float(np.std(fit.residuals)),
            }
        )
    return pd.DataFrame(rows)


def cross_section_era_table(cache: RawCache, horizon: int = 10) -> pd.DataFrame:
    """The same relation split by era, which is where it stops being detectable."""
    yields, real, peers = _jst_panel(cache)
    forward = real.rolling(horizon).sum().shift(-horizon) / horizon
    response = forward["USA"] - forward[peers].median(axis=1)
    spread = _log_spread(yields, peers)
    mask = response.notna() & spread.notna() & np.isfinite(response) & np.isfinite(spread)
    years = response[mask].index.astype(int)
    rows = []
    for label, low, high in (
        ("1870-1945", 0, 1945),
        ("1945-1990", 1945, 1990),
        ("1990-2010", 1990, 2011),
    ):
        window = (years >= low) & (years < high)
        if int(window.sum()) < 12:
            continue
        fit = hac_ols(
            response[mask].to_numpy(dtype=float)[window],
            spread[mask].to_numpy(dtype=float)[window],
            n_lags=15,
        )
        rows.append(
            {
                "era": label,
                "n_years": int(window.sum()),
                "n_independent": overlap_adjusted_observations(int(window.sum()), horizon),
                "intercept": float(fit.coefficients[0]),
                "slope": float(fit.coefficients[1]),
                "t_statistic": float(fit.t_statistics[1]),
                "mde_slope_at_80pc_power": 2.486 * float(fit.standard_errors[1]),
            }
        )
    return pd.DataFrame(rows)


def spread_history(cache: RawCache) -> pd.Series[float]:
    """The US-minus-panel-median log dividend-yield spread, 1870-2020."""
    yields, _, peers = _jst_panel(cache)
    return _log_spread(yields, peers).dropna()


def panel_fixed_effects_table(cache: RawCache) -> pd.DataFrame:
    """The same relation with year fixed effects, so identification is purely within-year.

    Demeaning both variables inside each year removes every global shock — wars, the
    common component of the world business cycle, and any drift in the world price of
    equity — so what is left is only "was the cheaper country's *subsequent* return
    higher than the dearer country's". That is the estimand behind a regional split.

    Standard errors are Driscoll-Kraay: the scores are averaged within a year, which
    handles arbitrary cross-country correlation, then a Bartlett HAC is applied over the
    year series, which handles the overlap. The row count is country-years and the
    ``n_years`` column is the number of independent blocks the HAC actually sees.
    """
    from portfolio_edge.inference.hac import long_run_variance

    yields, real, peers = _jst_panel(cache)
    countries = ["USA", *peers]
    rows = []
    for horizon in (1, 5, 10):
        forward = real.rolling(horizon).sum().shift(-horizon) / horizon
        log_yield = pd.DataFrame(
            np.log(yields[countries].to_numpy(dtype=float)),
            index=yields.index,
            columns=countries,
        )
        frames = []
        for period in yields.index:
            response = forward.loc[period, countries]
            predictor = log_yield.loc[period]
            keep = (
                response.notna()
                & predictor.notna()
                & np.isfinite(response)
                & np.isfinite(predictor)
            )
            if int(keep.sum()) < 5:
                continue
            frames.append(
                pd.DataFrame(
                    {
                        "year": int(period),
                        "y": response[keep] - response[keep].mean(),
                        "x": predictor[keep] - predictor[keep].mean(),
                    }
                )
            )
        panel = pd.concat(frames)
        x = panel["x"].to_numpy(dtype=float)
        y = panel["y"].to_numpy(dtype=float)
        slope = float(np.sum(x * y) / np.sum(x * x))
        residuals = y - slope * x
        scores = pd.Series(x * residuals).groupby(panel["year"].to_numpy()).mean()
        variance = long_run_variance(
            scores.to_numpy(dtype=float), n_lags=max(1, int(1.5 * horizon))
        )
        error = float(np.sqrt(variance / scores.size) / np.mean(x * x))
        rows.append(
            {
                "horizon_years": horizon,
                "country_years": int(panel.shape[0]),
                "n_years": int(scores.size),
                "slope": slope,
                "standard_error_dk": error,
                "t_statistic": slope / error,
                "r2_within": 1.0 - float(np.var(residuals)) / float(np.var(y)),
            }
        )
    return pd.DataFrame(rows)


def split_sizing_table(
    cache: RawCache,
    *,
    us_cape: float = 35.82,
    ex_us_cape: float = 21.02,
    relative_volatility_percent: tuple[float, ...] = (8.0, 14.4),
) -> pd.DataFrame:
    """What a shift out of US equity into non-US equity is worth at the current spread.

    Defaults are Siblis Research's ``as of 2026-06-30`` CAPE levels. The point estimate
    plugs a **CAPE** ratio into a fit estimated on **dividend-yield** spreads, which is an
    assumption and not a measurement: the two ratios differ by the payout ratio, and the
    US payout ratio has fallen by half since 1980. The residual band is reported beside
    the point estimate because it is four times wider.
    """
    fit = cross_section_table(cache)
    ten = fit[fit.horizon_years == 10].iloc[0]
    spread = -float(np.log(us_cape / ex_us_cape))
    implied_pp = 100.0 * (float(ten.intercept) + float(ten.slope) * spread)
    residual = float(ten.residual_sd_pp)
    rows = []
    for shift in (0.05, 0.10, 0.15, 0.35):
        for volatility in relative_volatility_percent:
            edge_bp = shift * abs(implied_pp) * 100.0
            tracking_bp = shift * volatility * 100.0
            rows.append(
                {
                    "shift_pp": 100.0 * shift,
                    "relative_volatility_pc": volatility,
                    "implied_us_minus_exus_pp": implied_pp,
                    "band_low_pp": implied_pp - 1.96 * residual,
                    "band_high_pp": implied_pp + 1.96 * residual,
                    "edge_bp": edge_bp,
                    "tracking_error_bp": tracking_bp,
                    "p_ahead_30y": probability_of_outperformance(
                        edge_bp=edge_bp, tracking_error_bp=tracking_bp, horizon_years=30.0
                    ),
                    "years_to_90pc": horizon_for_confidence(
                        edge_bp=edge_bp, tracking_error_bp=tracking_bp, confidence=0.90
                    ),
                }
            )
    return pd.DataFrame(rows)


def regret_table(us: UsPanel, *, weight_reduction: float = 0.15) -> pd.DataFrame:
    """What cutting the equity share costs, as a function of the premium the reader fears.

    Deliberately parameter-light. It contains no forecast: the reader supplies the
    realised premium they believe in and reads off what the cut cost. The realised figure
    on this repository's own Shiller sample is printed beside it for scale, as an
    illustration and not as a forecast.
    """
    rows = []
    for premium in (5.0, 4.0, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0):
        cost_bp = derisking_regret_bp(
            weight_reduction=weight_reduction, realised_excess_return=premium
        )
        rows.append(
            {
                "realised_premium_pc": premium,
                "cost_bp_per_year": cost_bp,
                "terminal_wealth_10y_pc": 100.0
                * (terminal_wealth_ratio(edge_bp=-cost_bp, horizon_years=10.0) - 1.0),
                "terminal_wealth_30y_pc": 100.0
                * (terminal_wealth_ratio(edge_bp=-cost_bp, horizon_years=30.0) - 1.0),
            }
        )
    frame = pd.DataFrame(rows)
    frame.attrs["realised_equity_real_pc"] = MONTHS_PER_YEAR * 100.0 * float(
        us.equity_log_real.mean()
    )
    frame.attrs["realised_bond_real_pc"] = MONTHS_PER_YEAR * 100.0 * float(
        us.bond_log_real.mean()
    )
    return frame


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def main() -> None:
    """Print every table the synthesis quotes."""
    cache = RawCache(default_cache_root())
    us = load_us(cache)
    tips = load_real_yield(cache, TIPS_URL)
    nominal = load_real_yield(cache, NOMINAL_URL)

    def show(frame: pd.DataFrame) -> None:
        print(frame.to_string(index=False, float_format=lambda v: f"{v:10.4f}"))

    print(f"\nShiller workbook: {us.period[0]}..{us.period[-1]}, sha256 {us.entry.sha256[:12]}")
    print("\n=== 1. levels ===")
    show(level_table(us, tips, nominal))
    print("\n--- TIPS excess CAPE yield, last 12 months ---")
    show(tips_excess_yield_history(us, tips).tail(12).reset_index(names="period"))

    print("\n=== 2a. predictive regressions, three inference methods ===")
    show(predictive_table(us))
    print("\n=== 2a2. same, month-end French response vs monthly-averaged Shiller ===")
    show(french_robustness_table(cache, us))
    print("\n=== 2b. Stambaugh bias ===")
    show(stambaugh_table(us))
    print("\n=== 2c. out-of-sample record ===")
    show(out_of_sample_table(us))

    print("\n=== 3a. does conditioning the weight help ===")
    show(conditioning_table(us))
    print("\n=== 3b. distribution over rolling 30-year windows ===")
    show(rolling_window_table(us))
    print("\n=== 3b2. gross edge by era ===")
    show(conditioning_era_table(us))
    print("\n=== 3c. cost sensitivity ===")
    show(cost_sensitivity_table(us))

    print("\n=== 4a. conditional distribution of subsequent real returns ===")
    show(conditional_distribution_table(us))
    print("\n=== 4b. drought and drawdown by entry valuation ===")
    show(drought_table(us))

    print("\n=== 5a. cross-section: US minus developed median ===")
    show(cross_section_table(cache))
    print("\n=== 5b. the same by era ===")
    show(cross_section_era_table(cache))
    print("\n=== 5c. year fixed effects, Driscoll-Kraay ===")
    show(panel_fixed_effects_table(cache))
    print("\n=== 5d. what a US-to-international shift is worth ===")
    show(split_sizing_table(cache))
    print("\n=== 6. the regret of cutting the equity share by 15 pp ===")
    regret = regret_table(us)
    show(regret)
    print(
        f"  for scale, realised on this sample: equity "
        f"{regret.attrs['realised_equity_real_pc']:.2f}%/yr real, bond "
        f"{regret.attrs['realised_bond_real_pc']:.2f}%/yr real, premium "
        f"{regret.attrs['realised_equity_real_pc'] - regret.attrs['realised_bond_real_pc']:.2f} pp"
    )
    spread = spread_history(cache)
    print(
        f"\nUS-minus-panel log dividend-yield spread: mean {spread.mean():+.3f}, "
        f"sd {spread.std():.3f}, last {spread.iloc[-1]:+.3f} in {spread.index[-1]}, "
        f"percentile {float(np.mean(spread < spread.iloc[-1])):.3f}"
    )
    print("\nDecade means of that spread:")
    print(spread.groupby((spread.index.astype(int) // 10) * 10).mean().round(3).to_string())


if __name__ == "__main__":
    main()
