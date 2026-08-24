"""Currency hedging arithmetic: what a USD investor is actually holding in VEA.

Why this module exists
----------------------
The reference portfolio holds 35% international — VEA, DFIV, IDMO, IEMG, AVES — every
one of them unhedged. That is a second position nobody chose: a long position in a
basket of foreign currencies, funded in dollars, sized at 35% of the equity book. This
module is the arithmetic that separates it from the equity it rides on.

The identity everything rests on
--------------------------------
Write ``r_L`` for a foreign asset's return in its own currency and ``s`` for the
appreciation of that currency against the dollar over the same period. A USD investor
holding the asset unhedged earns

    U = (1 + r_L)(1 + s) - 1                                    :func:`usd_return`

which is where the cross term ``r_L * s`` comes from: a US person who buys foreign
equity is long the currency on the *whole* position, including the part the equity
gains. Ken French publishes ``U``; nobody publishes ``r_L`` for free, so this module is
written to work from ``U`` and ``s`` and to solve for ``r_L``
(:func:`implied_local_return`) rather than the other way round.

Now suppose the investor sells the currency forward at the start of the period, on the
*beginning* notional, which is what every currency-hedged fund does and rolls monthly.
Under covered interest parity the forward rate is ``F = S (1 + i_d) / (1 + i_f)`` for
domestic rate ``i_d`` and foreign rate ``i_f``, and the hedged return works out to

    H = U - [(1 + i_f)(1 + s) - (1 + i_d)] / (1 + i_f)          :func:`forward_hedged_return`

The bracket is the excess return on *foreign cash funded in dollars* — spot move plus
the interest you earned abroad, less the interest you gave up at home. This module
calls it the **currency excess return** (:func:`currency_excess_return`), and the
identity above is the one fact that organises the whole question:

    **unhedged minus hedged is the currency excess return, and nothing else.**

:func:`hedge_give_up` returns the bracket divided by ``(1 + i_f)``, which is the
per-notional form that subtracts cleanly from a dollar return, and it is what
:class:`CurrencyPanel` carries. The two differ by a factor of ``(1 + i_f)``; the
difference is second order and always the same sign, which is precisely why it gets a
named function rather than an inline division.

So "should I hedge?" is exactly "do I want to be long the developed-currency carry
trade?", and it decomposes into a mean (is the carry trade compensated?) and a variance
and a crisis dependence (what does it do to the portfolio I already own?). Those three
have very different resolution and this module reports them separately.

Three things this arithmetic does *not* say
--------------------------------------------
*Covered interest parity is an assumption, not a measurement.* Since 2008 a persistent
cross-currency basis has separated the traded forward from the CIP forward. **Its sign
favours the dollar-based investor**, and the direction is the thing most often stated
backwards: the basis is quoted on the non-dollar leg and is negative because dollars
are scarce, so whoever *supplies* dollars to the swap market is paid for it — and a US
investor hedging foreign assets is supplying dollars. A hedged return computed here is
therefore a mild understatement, by roughly the basis. The magnitude is small and this
module cannot see it; a page quoting a hedged number states it from the published
source instead.

*A hedge on the beginning notional is not a hedge.* The residual — the currency
exposure of the period's own equity gain — is left deliberately in
:func:`forward_hedged_return`, because it is left in the real product. It is what makes
a "100% hedged" fund's tracking against a local-currency index imperfect.

*Nothing here nets a fee, a spread or a tax.* A hedged share class costs more than its
unhedged twin, and forward contracts have their own tax character. Those are costs the
caller applies; this module would otherwise hide the most decision-relevant number in
the problem inside an arithmetic identity.

What this module does not hold
-------------------------------
No market data and no cache access, in the tradition of
:mod:`portfolio_edge.studies.stress_dependence`;
:mod:`portfolio_edge.studies._currency_hedging_tables` is the one file that reads the
cache. Crisis conditioning reuses :func:`~portfolio_edge.studies.stress_dependence.tail_dependence`
and :func:`~portfolio_edge.studies.stress_dependence.episode_returns` rather than
growing a second copy of them here.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.inference.hac import hac_mean, long_run_variance, newey_west_lag_count
from portfolio_edge.studies.factor_breadth import minimum_detectable_effect

__all__ = [
    "HEDGE_RATIO_GRID",
    "CurrencyPanel",
    "HedgeComparison",
    "HedgeRatioPoint",
    "basket_return",
    "currency_excess_return",
    "effective_sample_size",
    "forward_hedged_return",
    "hedge_comparison",
    "hedge_give_up",
    "hedge_ratio_grid",
    "implied_local_return",
    "minimum_regret_ratio",
    "usd_return",
    "variance_minimising_hedge_ratio",
    "weighted_basket",
]

#: The hedge ratios reported on every frontier. 0.0 and 1.0 are the corners the products
#: actually sell; 0.5 is the minimum-regret default; the rest exist so that a reader can
#: see how flat the curve is between them, which is the substance of the 50% argument.
HEDGE_RATIO_GRID: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 1.0)

#: Percentage points per unit of decimal return. Named so no table multiplies by a bare
#: 100 and no reader has to guess whether a column is decimal or percent.
PERCENT: Final = 100.0


def _series(values: Sequence[float] | FloatArray, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(array)):
        raise ValueError(
            f"{name} contains a non-finite value. A missing exchange rate or bill rate "
            "must be dropped by the caller, with the window it kept stated, rather than "
            "filled with a zero here — a filled zero is a claim that the currency did "
            "not move."
        )
    return array


def _aligned(
    a: Sequence[float] | FloatArray, b: Sequence[float] | FloatArray, *, names: tuple[str, str]
) -> tuple[FloatArray, FloatArray]:
    x = _series(a, name=names[0])
    y = _series(b, name=names[1])
    if x.shape != y.shape:
        raise ValueError(
            f"{names[0]} and {names[1]} must be aligned, got {x.size} and {y.size} "
            "observations. Intersect the periods first; a silent truncation would "
            "compare different windows."
        )
    return x, y


def usd_return(
    local_return: Sequence[float] | FloatArray, currency_return: Sequence[float] | FloatArray
) -> FloatArray:
    """``(1 + r_L)(1 + s) - 1``: a foreign asset translated into dollars.

    The multiplication is not a convenience. Adding ``r_L + s`` drops the cross term,
    which is the currency exposure of the equity's own gain, and that term is the entire
    reason a "fully hedged" fund is not fully hedged.
    """
    local, currency = _aligned(
        local_return, currency_return, names=("local_return", "currency_return")
    )
    return np.asarray((1.0 + local) * (1.0 + currency) - 1.0, dtype=np.float64)


def implied_local_return(
    usd_returns: Sequence[float] | FloatArray, currency_return: Sequence[float] | FloatArray
) -> FloatArray:
    """Invert :func:`usd_return`: ``(1 + U) / (1 + s) - 1``.

    This is the direction the free data force. Ken French publishes developed-ex-US
    equity **in dollars only**; a local-currency series is not free anywhere this
    repository can reach. So the local leg here is a *residual* — whatever is left of
    the dollar return after a currency basket is divided out — and it inherits every
    error in the basket's weights. It is not a measurement of a local-currency index and
    must not be quoted as one.
    """
    dollars, currency = _aligned(
        usd_returns, currency_return, names=("usd_returns", "currency_return")
    )
    if np.any(currency <= -1.0):
        raise ValueError(
            "a currency return of -100% or worse cannot be divided out; the exchange "
            "rate series has a bad observation or a redenomination in it"
        )
    return np.asarray((1.0 + dollars) / (1.0 + currency) - 1.0, dtype=np.float64)


def currency_excess_return(
    currency_return: Sequence[float] | FloatArray,
    foreign_rate: Sequence[float] | FloatArray,
    domestic_rate: Sequence[float] | FloatArray,
) -> FloatArray:
    """``(1 + i_f)(1 + s) - (1 + i_d)``: foreign cash, funded in dollars.

    This is the object the whole question reduces to. It is the return to the long leg
    of a developed-currency carry trade, it is what a hedged fund gives up, and its mean
    is the empirical content of "is currency exposure compensated?".

    All three arguments are **per-period returns**, not annual rates: a monthly panel
    passes one twelfth of an annual rate, or better, a rate the source already states
    per period. Passing an annualised rate to a monthly panel overstates the carry by a
    factor of twelve and is invisible in the output, so the caller converts and says so.
    """
    spot, foreign = _aligned(
        currency_return, foreign_rate, names=("currency_return", "foreign_rate")
    )
    _, domestic = _aligned(
        currency_return, domestic_rate, names=("currency_return", "domestic_rate")
    )
    return np.asarray((1.0 + foreign) * (1.0 + spot) - (1.0 + domestic), dtype=np.float64)


def hedge_give_up(
    currency_return: Sequence[float] | FloatArray,
    foreign_rate: Sequence[float] | FloatArray,
    domestic_rate: Sequence[float] | FloatArray,
) -> FloatArray:
    """``[(1 + i_f)(1 + s) - (1 + i_d)] / (1 + i_f)``: what a full hedge gives up.

    The currency excess return **per unit of hedged notional**, which is the quantity
    that subtracts cleanly from a dollar return. It is not the same number as
    :func:`currency_excess_return`: that one is the excess return on a foreign *cash*
    position of one unit, and this one is the give-up on a hedge struck on the beginning
    notional. They differ by ``(1 + i_f)`` and the difference is second order in the
    rate, which is exactly why it is easy to get wrong and worth a named function.

    Equivalently ``(1 + s) - (1 + i_d) / (1 + i_f)`` — spot move less the forward
    premium — which is how a trading desk would write it. The two forms agree to machine
    precision and the test suite pins that.
    """
    _, foreign = _aligned(
        currency_return, foreign_rate, names=("currency_return", "foreign_rate")
    )
    if np.any(foreign <= -1.0):
        raise ValueError("a foreign gross rate of zero or less is not a rate; check the units")
    excess = currency_excess_return(currency_return, foreign_rate, domestic_rate)
    return np.asarray(excess / (1.0 + foreign), dtype=np.float64)


def forward_hedged_return(
    usd_returns: Sequence[float] | FloatArray,
    currency_return: Sequence[float] | FloatArray,
    foreign_rate: Sequence[float] | FloatArray,
    domestic_rate: Sequence[float] | FloatArray,
    *,
    hedge_ratio: float = 1.0,
) -> FloatArray:
    """The unhedged dollar return less ``hedge_ratio`` of the currency excess return.

    Derived in the module docstring: selling the beginning notional forward at the CIP
    forward rate removes ``[(1 + i_f)(1 + s) - (1 + i_d)] / (1 + i_f)`` from the dollar
    return. The ``/(1 + i_f)`` is not decoration — the forward is struck on the notional,
    and dividing by the foreign gross rate is what makes the identity exact rather than
    first-order.

    ``hedge_ratio`` is the fraction of notional sold forward. It is not restricted to
    ``[0, 1]``: a caller exploring an over-hedge should be able to, and the value is
    reported beside every result.
    """
    dollars, spot = _aligned(
        usd_returns, currency_return, names=("usd_returns", "currency_return")
    )
    _, foreign = _aligned(usd_returns, foreign_rate, names=("usd_returns", "foreign_rate"))
    _, domestic = _aligned(usd_returns, domestic_rate, names=("usd_returns", "domestic_rate"))
    return np.asarray(
        dollars - hedge_ratio * hedge_give_up(spot, foreign, domestic), dtype=np.float64
    )


def weighted_basket(
    weights: Mapping[str, float], series: Mapping[str, Sequence[float] | FloatArray]
) -> FloatArray:
    """Weighted arithmetic mean of per-currency returns, weights renormalised to one.

    Arithmetic, not geometric: a currency basket is a *portfolio* of currency positions
    rebalanced each period, and a portfolio's return is the weighted mean of its
    constituents' returns. Compounding first and averaging second would price a
    buy-and-hold basket nobody holds.

    Every key in ``weights`` must be present in ``series`` and vice versa. A silently
    dropped currency is a silently reweighted basket.
    """
    if not weights:
        raise ValueError("weights is empty")
    if set(weights) != set(series):
        missing = sorted(set(weights) - set(series))
        extra = sorted(set(series) - set(weights))
        raise ValueError(
            f"weights and series must name the same currencies; missing series for "
            f"{missing}, unweighted series {extra}. Renormalise deliberately rather "
            "than letting a key mismatch do it."
        )
    if any(w < 0.0 for w in weights.values()):
        raise ValueError(f"a currency weight cannot be negative: {dict(weights)}")
    total = float(sum(weights.values()))
    if total <= 0.0:
        raise ValueError(f"currency weights sum to {total}, which cannot be renormalised")
    keys = sorted(weights)
    stack = np.vstack([_series(series[k], name=f"series[{k!r}]") for k in keys])
    w = np.array([weights[k] / total for k in keys], dtype=np.float64)
    return np.asarray(w @ stack, dtype=np.float64)


def basket_return(
    weights: Mapping[str, float], series: Mapping[str, Sequence[float] | FloatArray]
) -> FloatArray:
    """Alias of :func:`weighted_basket`, kept because call sites read better either way."""
    return weighted_basket(weights, series)


def effective_sample_size(values: Sequence[float] | FloatArray) -> float:
    """``T * Var / S``, the number of independent observations the series is worth.

    ``S`` is the Newey-West long-run variance. For a serially uncorrelated series this
    returns ``T``; for a positively autocorrelated one it returns less, and for a
    mean-reverting one more. Reported beside every mean in this module because currency
    returns are close to a random walk with very large variance, and the honest answer
    to "is the mean positive?" usually depends on how many independent draws the window
    really contains rather than on how many rows it has.
    """
    series = _series(values, name="values")
    if series.size < 2:
        raise ValueError(f"need at least two observations, got {series.size}")
    if float(np.ptp(series)) == 0.0:
        raise ValueError(
            "a constant series has no effective sample size. The range is tested "
            "rather than the variance because a repeated inexact float has a tiny "
            "non-zero sample variance and would divide instead of raising."
        )
    variance = float(np.var(series, ddof=0))
    centred = series - series.mean()
    lrv = long_run_variance(centred, n_lags=newey_west_lag_count(series.size))
    if lrv <= 0.0:
        return float("nan")
    return float(series.size) * variance / lrv


@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyPanel:
    """One aligned window of the two series every result here is computed from.

    ``periods`` are ``YYYY`` or ``YYYY-MM`` labels; ``periods_per_year`` says which, and
    is the only place an annualisation factor is written down.

    ``currency_excess`` is the **hedge give-up per unit of notional** from
    :func:`hedge_give_up`, not the raw :func:`currency_excess_return`. That is the
    quantity for which ``hedged = unhedged - currency_excess`` holds exactly, and using
    the other one here would misprice the hedge by a factor of ``(1 + i_f)`` — small,
    always in the same direction, and invisible in the output.
    """

    label: str
    periods: tuple[str, ...]
    periods_per_year: int
    unhedged: FloatArray
    currency_excess: FloatArray

    def __post_init__(self) -> None:
        if self.periods_per_year not in (1, 4, 12):
            raise ValueError(
                f"periods_per_year must be 1, 4 or 12, got {self.periods_per_year}; an "
                "unusual frequency needs its annualisation justified at the call site"
            )
        if len(self.periods) != self.unhedged.size:
            raise ValueError(
                f"{len(self.periods)} period labels for {self.unhedged.size} returns"
            )
        if self.unhedged.shape != self.currency_excess.shape:
            raise ValueError("unhedged and currency_excess must be aligned")

    @property
    def hedged(self) -> FloatArray:
        """The fully-hedged counterpart. ``unhedged - currency_excess`` by the identity."""
        return np.asarray(self.unhedged - self.currency_excess, dtype=np.float64)


@dataclass(frozen=True, slots=True, kw_only=True)
class HedgeComparison:
    """Hedged against unhedged over one window, with the resolution of each claim.

    The three blocks answer three different questions and have wildly different power,
    which is the single most important thing this dataclass exists to make visible:

    * ``mean_difference`` and its interval answer "is currency compensated?". This is a
      mean of a near-random-walk and is normally **unresolved**: ``mean_resolved`` says
      so explicitly rather than letting a small point estimate read as a small effect.
    * ``volatility_unhedged`` against ``volatility_hedged`` answers "what does it cost in
      risk?". A variance ratio over the same window is estimated an order of magnitude
      more precisely than a mean and is normally decisive.
    * ``variance_minimising_ratio`` answers "how much of it would I remove if risk were
      the only objective?".

    All returns are decimals per year. ``mde_80`` is the smallest annual mean difference
    this window could reject a zero at one-sided 5% size with 80% power.
    """

    label: str
    periods_per_year: int
    n_periods: int
    first_period: str
    last_period: str
    effective_n: float
    mean_unhedged: float
    mean_hedged: float
    mean_difference: float
    mean_difference_se: float
    mean_difference_t: float
    mde_80: float
    mean_resolved: bool
    volatility_unhedged: float
    volatility_hedged: float
    volatility_currency: float
    variance_ratio: float
    correlation_currency_unhedged: float
    variance_minimising_ratio: float

    @property
    def volatility_reduction(self) -> float:
        """Fraction of unhedged volatility a full hedge removes, in ``[0, 1)`` normally."""
        if self.volatility_unhedged == 0.0:
            return float("nan")
        return 1.0 - self.volatility_hedged / self.volatility_unhedged


def _annualised_mean(values: FloatArray, periods_per_year: int) -> float:
    """Arithmetic mean times the frequency.

    Arithmetic and not geometric throughout this module. The question is whether a mean
    is distinguishable from zero, and a geometric mean of a high-variance series is a
    different estimand that is *lower* by roughly half the variance — quoting it in a
    row headed "is it compensated?" would answer a question nobody asked.
    """
    return float(np.mean(values)) * periods_per_year


def _annualised_volatility(values: FloatArray, periods_per_year: int) -> float:
    return float(np.std(values, ddof=1)) * math.sqrt(periods_per_year)


def _correlation(x: FloatArray, y: FloatArray) -> float:
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def variance_minimising_hedge_ratio(
    unhedged: Sequence[float] | FloatArray, currency_excess: Sequence[float] | FloatArray
) -> float:
    """``cov(U, cx) / var(cx)``: the ratio that minimises realised variance in sample.

    This is a regression coefficient, and it is **in sample by construction**. It is
    reported as a diagnostic of where the variance-minimising point sits, never as an
    allocation: an in-sample optimum on 300 correlated observations is an overfit, and
    the flatness of the curve around it — which :func:`hedge_ratio_grid` shows — is the
    decision-relevant fact.

    A full hedge is ratio 1.0. Above 1.0 the currency leg was *hedging* the local equity
    leg, so removing more than the notional reduced variance further; below 1.0 the two
    legs partly offset and some currency exposure was worth keeping on risk grounds
    alone.
    """
    u, cx = _aligned(unhedged, currency_excess, names=("unhedged", "currency_excess"))
    variance = float(np.var(cx, ddof=1))
    if variance == 0.0:
        raise ValueError("the currency excess return is constant; there is nothing to hedge")
    return float(np.cov(u, cx, ddof=1)[0, 1]) / variance


def minimum_regret_ratio() -> float:
    """0.5, and the reason it is a function rather than a literal.

    The 50% hedge is not an estimate of anything. It is the ratio that minimises the
    maximum regret against the two corners a decision-maker could be wrong about — fully
    hedged when currency was compensated, fully unhedged when it was not — under a
    symmetric loss. It therefore requires **no forecast of the currency mean**, which is
    exactly the quantity every window in this repository fails to resolve. Any page
    quoting 0.5 should cite that argument and not an optimisation.
    """
    return 0.5


def hedge_comparison(panel: CurrencyPanel) -> HedgeComparison:
    """Fully hedged against fully unhedged over ``panel``'s window."""
    unhedged = _series(panel.unhedged, name="unhedged")
    cx = _series(panel.currency_excess, name="currency_excess")
    hedged = unhedged - cx
    inference = hac_mean(cx)
    annual_se = inference.standard_error * panel.periods_per_year
    mde = minimum_detectable_effect(annual_se)
    difference = _annualised_mean(cx, panel.periods_per_year)
    return HedgeComparison(
        label=panel.label,
        periods_per_year=panel.periods_per_year,
        n_periods=unhedged.size,
        first_period=panel.periods[0],
        last_period=panel.periods[-1],
        effective_n=effective_sample_size(cx),
        mean_unhedged=_annualised_mean(unhedged, panel.periods_per_year),
        mean_hedged=_annualised_mean(hedged, panel.periods_per_year),
        mean_difference=difference,
        mean_difference_se=annual_se,
        mean_difference_t=inference.t_statistic,
        mde_80=mde,
        mean_resolved=abs(difference) >= mde,
        volatility_unhedged=_annualised_volatility(unhedged, panel.periods_per_year),
        volatility_hedged=_annualised_volatility(hedged, panel.periods_per_year),
        volatility_currency=_annualised_volatility(cx, panel.periods_per_year),
        variance_ratio=(
            float(np.var(hedged, ddof=1) / np.var(unhedged, ddof=1))
            if float(np.var(unhedged, ddof=1)) > 0.0
            else float("nan")
        ),
        correlation_currency_unhedged=_correlation(cx, unhedged),
        variance_minimising_ratio=variance_minimising_hedge_ratio(unhedged, cx),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class HedgeRatioPoint:
    """One point on the hedge-ratio frontier, in decimals per year."""

    hedge_ratio: float
    mean: float
    volatility: float
    worst_period: float
    max_drawdown: float


def hedge_ratio_grid(
    panel: CurrencyPanel, *, ratios: Sequence[float] = HEDGE_RATIO_GRID
) -> tuple[HedgeRatioPoint, ...]:
    """The mean, volatility and drawdown of ``U - h * cx`` for each ``h``.

    The drawdown is of the compounded path of the series as supplied. When ``panel``
    carries total returns that is a total-return drawdown; when it carries excess
    returns it is a drawdown relative to cash. The caller chose which by choosing what
    it put in the panel, and the distinction is not recoverable here.
    """
    unhedged = _series(panel.unhedged, name="unhedged")
    cx = _series(panel.currency_excess, name="currency_excess")
    points = []
    for ratio in ratios:
        blended = unhedged - ratio * cx
        curve = np.cumprod(1.0 + blended)
        peak = np.maximum.accumulate(curve)
        points.append(
            HedgeRatioPoint(
                hedge_ratio=float(ratio),
                mean=_annualised_mean(blended, panel.periods_per_year),
                volatility=_annualised_volatility(blended, panel.periods_per_year),
                worst_period=float(np.min(blended)),
                max_drawdown=float(np.min(curve / peak - 1.0)),
            )
        )
    return tuple(points)
