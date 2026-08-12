"""Regenerates the measured tables in ``docs/research/setting-the-equity-share.md``.

Kept separate from :mod:`portfolio_edge.studies.equity_share` so that the study
itself stays pure and testable and only this file touches the cache. Run it with

    uv run python -m portfolio_edge.studies.equity_share

Two data notes that decide how far the output may be trusted.

**Equity is Ken French's US market total return**, ``Mkt-RF + RF`` from
``F-F_Research_Data_5_Factors_2x3``, over 1963-07…2025-12. That is the same series
and window that produced the ``10.80% / 15.40% / -50.3% / 72 months`` line in
``docs/research/long-only-capture.md``, and this module
reproduces all four to the printed precision, which is the check that the pipeline is
the same one.

**The bond series is modelled, not measured.** No total-return bond series exists in
this repository — ``fred.SERIES`` carries yields and policy rates only — so a
ten-year par-bond total return is constructed from ``GS10``: buy a par bond at last
month's constant-maturity yield, accrue one month of coupon, and reprice the
remaining 9 years 11 months at this month's yield. It is a standard approximation and
it is still an approximation: it holds no on-the-run premium, no bid/ask, no tax and
no roll into an actual index's maturity band. Every figure that uses it is a modelled
figure and the page says so beside each one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import fred, french
from portfolio_edge.data.cache import RawCache, default_cache_root
from portfolio_edge.studies.equity_share import (
    break_even_excess_return,
    constant_mix_ladder,
    constant_mix_returns,
    fully_invested_growth_optimal_weight,
    growth_retained_fraction,
    implied_effective_years,
    inverse_variance_bias_factor,
    kelly_estimator_standard_error,
    optimal_kelly_shrinkage,
    permuted_terminal_wealth,
    plug_in_growth_cost,
)

WINDOW_START = "1963-07"
WINDOW_END = "2025-12"
BOND_MATURITY_YEARS = 10.0
LADDER = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SEED = 20260812
DRAWS = 20_000

#: Sub-period boundaries as the authors of the bond-stock comovement paper state them
#: in their own February 2026 summary, translated from quarters to months so this
#: repository's monthly series can be read against them.
CAMPBELL_ERAS = (
    ("1964-01", "1967-09"),
    ("1967-10", "1971-09"),
    ("1971-10", "1974-06"),
    ("1974-07", "1999-12"),
    ("2000-01", "2022-09"),
    ("2022-10", "2024-06"),
    ("2024-07", "2025-12"),
)


def par_bond_price(*, coupon: float, yield_to_maturity: float, years: float) -> float:
    """Price per unit of face of a semiannual-coupon bond, exact given its inputs."""
    periods = 2.0 * years
    rate = yield_to_maturity / 2.0
    coupon_payment = coupon / 2.0
    if abs(rate) < 1e-12:
        return coupon_payment * periods + 1.0
    discount = (1.0 + rate) ** (-periods)
    return float(coupon_payment * (1.0 - discount) / rate + discount)


def ten_year_par_bond_returns(yields: pd.Series) -> pd.Series:
    """Monthly total return of a rolled ten-year par bond, from constant-maturity yields."""
    values = yields.to_numpy(dtype=np.float64)
    monthly = np.empty(values.size - 1, dtype=np.float64)
    for index in range(1, values.size):
        opening, closing = float(values[index - 1]), float(values[index])
        price = par_bond_price(
            coupon=opening,
            yield_to_maturity=closing,
            years=BOND_MATURITY_YEARS - 1.0 / 12.0,
        )
        monthly[index - 1] = opening / 12.0 + (price - 1.0)
    return pd.Series(monthly, index=yields.index[1:])


def _on_window(series: pd.Series) -> pd.Series:
    index = pd.PeriodIndex(series.index)
    keep = (index >= pd.Period(WINDOW_START, "M")) & (index <= pd.Period(WINDOW_END, "M"))
    return series[keep]


def load_series() -> tuple[pd.Series, pd.Series, pd.Series]:
    """Equity total return, cash, and the modelled ten-year bond, on the window."""
    cache = RawCache(default_cache_root())
    _, parsed, _ = french.load(cache, french.get_dataset("french_us_ff5"))
    frame = parsed.table("monthly").to_frame()
    frame.index = pd.PeriodIndex(frame.index, freq="M")
    equity = _on_window(frame["Mkt-RF"] + frame["RF"])
    cash = _on_window(frame["RF"])

    entry = fred.download(cache, "GS10")
    yields = fred.parse(cache, entry, "GS10").to_frame()["GS10"]
    yields.index = pd.PeriodIndex(pd.to_datetime(yields.index), freq="M")
    bond = _on_window(ten_year_par_bond_returns(yields))
    return equity, cash, bond


def main() -> None:
    equity, cash, bond = load_series()
    common = equity.index.intersection(bond.index)
    equity, cash, bond = equity.loc[common], cash.loc[common], bond.loc[common]
    months = len(common)
    print(f"window {common[0]}..{common[-1]}  {months} months\n")

    print("== the drawdown ladder ==")
    print("  w   | equity/cash: geo%  vol%   MDD%  TUW | equity/10y: geo%  vol%   MDD%  TUW")
    cash_rungs = constant_mix_ladder(equity.to_numpy(), cash.to_numpy(), LADDER)
    bond_rungs = constant_mix_ladder(equity.to_numpy(), bond.to_numpy(), LADDER)
    for left, right in zip(cash_rungs, bond_rungs, strict=True):
        print(
            f" {left.weight:4.1f} | "
            f"{left.geometric_return * 100:17.2f} {left.volatility * 100:5.2f} "
            f"{left.max_drawdown * 100:6.1f} {left.max_time_under_water:4d} | "
            f"{right.geometric_return * 100:16.2f} {right.volatility * 100:5.2f} "
            f"{right.max_drawdown * 100:6.1f} {right.max_time_under_water:4d}"
        )

    print("\n== growth retained at a fraction of the growth-optimal exposure ==")
    for fraction in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        print(f"  f={fraction:4.2f}  retained {growth_retained_fraction(fraction):+7.3f}")

    print("\n== the premium each equity share is implicitly forecasting ==")
    equity_volatility = float(np.std(equity, ddof=1)) * np.sqrt(12.0)
    bond_volatility = float(np.std(bond, ddof=1)) * np.sqrt(12.0)
    sample_correlation = float(np.corrcoef(equity, bond)[0, 1])
    print(
        f"  sample sigma_e {equity_volatility * 100:.2f}%  sigma_b "
        f"{bond_volatility * 100:.2f}%  rho {sample_correlation:+.3f}"
    )
    for correlation in (-0.30, 0.0, sample_correlation, 0.30):
        cells = []
        for weight in (0.4, 0.6, 0.8, 1.0):
            premium = break_even_excess_return(
                weight=weight,
                equity_volatility=equity_volatility,
                bond_volatility=bond_volatility,
                correlation=correlation,
            )
            cells.append(f"w={weight:.1f}: {premium * 100:5.2f}%")
        print(f"  rho={correlation:+.3f}  " + "  ".join(cells))

    sample_premium = float((equity - bond).mean()) * 12.0
    unconstrained = fully_invested_growth_optimal_weight(
        excess_return_over_bond=sample_premium,
        equity_volatility=equity_volatility,
        bond_volatility=bond_volatility,
        correlation=sample_correlation,
        clip=False,
    )
    print(
        f"  at the sample premium {sample_premium * 100:.2f}%/yr the unconstrained "
        f"w* is {unconstrained:.2f}"
    )

    print("\n== estimation error ==")
    sharpe = float((equity - cash).mean()) * 12.0 / equity_volatility
    print(f"  sample Sharpe of equity over cash {sharpe:.4f}")
    print("  years |  SE(L*) | cost %/yr | f* at this Sharpe")
    for years in (10.0, 20.0, 30.0, months / 12.0):
        print(
            f"  {years:5.1f} | "
            f"{kelly_estimator_standard_error(volatility=equity_volatility, years=years):7.2f} | "
            f"{plug_in_growth_cost(years) * 100:9.2f} | "
            f"{optimal_kelly_shrinkage(sharpe_ratio=sharpe, years=years):.3f}"
        )
    print(
        f"  half Kelly implies {implied_effective_years(sharpe_ratio=sharpe, shrinkage=0.5):.2f}"
        f" effective years; sigma-estimation bias factor at n={months} is "
        f"{inverse_variance_bias_factor(months):.5f}"
    )

    print("\n== sequence risk: one fixed multiset of returns, reordered ==")
    horizon = 360
    record = equity.to_numpy()[-horizon:]
    print(f"  the last {horizon} months, {common[-horizon]}..{common[-1]}, 100% equity")
    for label, initial, flow in (
        ("lump sum, no flows", 1.0, 0.0),
        ("contributing 1/month", 1e-9, 1.0),
        ("withdrawing 4%/yr of initial", 1.0, -0.04 / 12.0),
    ):
        result = permuted_terminal_wealth(
            record,
            initial_wealth=initial,
            flow_per_period=flow,
            periods=horizon,
            draws=DRAWS,
            seed=SEED,
            early_periods=120,
        )
        print(
            f"  {label:30s} p5 {result.percentile_5:12.4f}  median "
            f"{result.median:12.4f}  p95 {result.percentile_95:12.4f}  "
            f"spread {result.spread_ratio:7.4f}  corr(first decade) "
            f"{result.early_return_correlation:+.3f}"
        )

    print("\n== ruin, in real terms, by equity share ==")
    real_equity, real_bond, real_months = real_series(equity, bond)
    print(
        f"  {real_months} months of CPI-deflated returns; real equity "
        f"{annualised(real_equity) * 100:.2f}%/yr, real bond "
        f"{annualised(real_bond) * 100:.2f}%/yr"
    )
    print("  wd%  | " + "  ".join(f"w={w:.1f}" for w in LADDER[1:]))
    for withdrawal in (0.03, 0.04, 0.05, 0.06):
        cells = []
        for weight in LADDER[1:]:
            mixed = constant_mix_returns(real_equity, real_bond, weight)
            result = permuted_terminal_wealth(
                mixed,
                initial_wealth=1.0,
                flow_per_period=-withdrawal / 12.0,
                periods=horizon,
                draws=DRAWS,
                seed=SEED,
                early_periods=120,
            )
            cells.append(f"{result.ruin_probability * 100:5.2f}")
        print(f"  {withdrawal * 100:4.1f} | " + "  ".join(cells))

    print("\n== how much a step up the ladder is worth, and how long it takes to show ==")
    print("  pair              edge bp/yr   TE bp/yr   P(30 yr)   90% at")
    for high, low in ((0.7, 0.6), (0.8, 0.6), (0.9, 0.6), (1.0, 0.6), (1.0, 0.4)):
        upper = constant_mix_returns(equity.to_numpy(), bond.to_numpy(), high)
        lower = constant_mix_returns(equity.to_numpy(), bond.to_numpy(), low)
        edge = annualised(upper) - annualised(lower)
        tracking = float(
            np.std(np.log1p(upper) - np.log1p(lower), ddof=1)
        ) * np.sqrt(12.0)
        print(
            f"  {high:.0%}/{1 - high:.0%} vs {low:.0%}/{1 - low:.0%}  "
            f"{edge * 1e4:10.1f} {tracking * 1e4:10.1f} "
            f"{norm.cdf(edge * np.sqrt(30.0) / tracking):10.3f} "
            f"{(norm.ppf(0.90) * tracking / edge) ** 2:7.0f} yr"
        )

    print("\n== bond-stock comovement by era, modelled bond ==")
    joint = pd.concat([equity.rename("eq"), bond.rename("bd")], axis=1).dropna()
    index = pd.PeriodIndex(joint.index)
    for start, end in CAMPBELL_ERAS:
        window = joint[
            (index >= pd.Period(start, "M")) & (index <= pd.Period(end, "M"))
        ]
        slope = float(np.polyfit(window["eq"], window["bd"], 1)[0])
        print(
            f"  {start}..{end}  n={len(window):4d}  corr "
            f"{float(window['eq'].corr(window['bd'])):+.3f}  beta {slope:+.3f}"
        )


def annualised(returns: FloatArray) -> float:
    return float(float(np.prod(1.0 + returns)) ** (12.0 / returns.size) - 1.0)


def real_series(equity: pd.Series, bond: pd.Series) -> tuple[FloatArray, FloatArray, int]:
    """CPI-deflated equity and bond returns on whatever window CPI also covers."""
    cache = RawCache(default_cache_root())
    entry = fred.download(cache, "CPIAUCSL")
    level = fred.parse(cache, entry, "CPIAUCSL").to_frame()["CPIAUCSL"]
    level.index = pd.PeriodIndex(pd.to_datetime(level.index), freq="M")
    inflation = (level / level.shift(1) - 1.0).dropna()
    window = equity.index.intersection(inflation.index)
    factor = 1.0 + inflation.loc[window].to_numpy()
    real_equity = (1.0 + equity.loc[window].to_numpy()) / factor - 1.0
    real_bond = (1.0 + bond.loc[window].to_numpy()) / factor - 1.0
    return real_equity, real_bond, len(window)
