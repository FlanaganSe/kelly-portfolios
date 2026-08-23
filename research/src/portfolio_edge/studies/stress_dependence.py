"""Stress-state dependence: how a candidate engine behaves when equity is falling.

Why this module exists
----------------------
``docs/charter.md`` says that low average correlation is only an admission signal, and
``docs/research/search-coverage.md`` §2 asks for crisis-conditional dependence on every
candidate rather than on trend alone. The investor's stated requirement — *assets that
perform better in black swan events without excessive long-term drawdowns* — is a
statement about two moments of the **conditional** distribution, and a full-sample
correlation answers neither.

Three measurements, and each answers a different question:

* :func:`episode_returns` — what an engine actually did inside a **named** historical
  episode. A window the panel does not cover is reported as uncovered rather than
  truncated, because "this instrument cannot see 1929" is the most important thing a
  stress table can say. The window list itself is an analytical choice made by eye and
  the caller supplies it; this module never invents one.
* :func:`tail_dependence` — the engine's mean, hit rate and correlation inside the worst
  ``q`` of base months, against the best ``q``. This is the black-swan question stated
  as an estimand: an asset that "performs better in black swan events" must have a
  positive mean in the lower tail, and an asset "without excessive long-term drawdowns"
  must not pay for it out of the rest of the distribution.
* :func:`engine_summary` — the unconditional counterweight: annualised mean, volatility,
  Sharpe, maximum drawdown and full-sample correlation, so a conditional result is never
  read without the price of holding the thing.

What this module does not do
-----------------------------
It holds **no market data and no cache access**, in the tradition of
:mod:`portfolio_edge.studies.gold_sleeve`;
:mod:`portfolio_edge.studies._stress_dependence_tables` is the one file that reads the
cache. It does not size a sleeve, it does not net a fee (the caller nets fees before
calling), and it does not test a hypothesis — every function here is a descriptive
statistic on a supplied series, and a descriptive statistic on a window chosen after
seeing history is **exploratory** by construction.

Two traps that are the reason for the shape of the code
--------------------------------------------------------
*A conditional mean is not a rate.* Means are reported per month, never annualised,
because the conditioning set is not a calendar. Annualising the mean of the worst 10% of
months would state a return nobody could earn.

*A tail count is small and the code says how small.* :class:`TailDependence` carries the
number of months in the tail, and :func:`tail_dependence` refuses a tail with fewer than
five observations rather than returning a correlation computed from three points.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

__all__ = [
    "MONTHS_PER_YEAR",
    "Convexity",
    "EngineSummary",
    "EpisodeReturn",
    "TailDependence",
    "convexity",
    "engine_summary",
    "episode_returns",
    "tail_dependence",
]

FloatArray = np.typing.NDArray[np.float64]

#: Monthly data throughout. Named so an annualisation is never a bare ``12``.
MONTHS_PER_YEAR: int = 12

#: The smallest tail this module will describe. Below it a correlation is noise dressed
#: as a number, and the caller should widen the quantile or say the panel cannot answer.
MINIMUM_TAIL_MONTHS: int = 5


def _series(values: Sequence[float] | FloatArray, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains a non-finite value; drop or repair it upstream")
    return array


@dataclass(frozen=True, slots=True, kw_only=True)
class EpisodeReturn:
    """One engine's realised path inside one named window.

    ``covered`` is false when the panel and the window do not overlap at all, and
    ``months`` is then zero. ``partial`` is true when the panel covers the window only
    in part, which is the case that silently misleads if it is not reported: a 2008
    result computed from four of sixteen months is not a 2008 result.
    """

    window: str
    start: str
    end: str
    covered: bool
    partial: bool
    months: int
    cumulative_return: float
    worst_month: float
    peak_to_trough: float


def episode_returns(
    periods: Sequence[str],
    series: Sequence[float] | FloatArray,
    *,
    windows: Mapping[str, tuple[str, str]],
) -> tuple[EpisodeReturn, ...]:
    """Cumulative return, worst month and peak-to-trough inside each named window.

    ``periods`` are ``YYYY-MM`` labels aligned with ``series``; the comparison is
    lexicographic, which is correct for zero-padded ISO months and for nothing else.

    A window with no overlap yields ``covered=False`` and zeroed statistics rather than
    being omitted, so a caller cannot lose an episode by forgetting to check the length
    of the result. Partial coverage is flagged by comparing the number of panel months
    inside the window against the number of calendar months the window spans.
    """
    labels = list(periods)
    values = _series(series, name="series")
    if len(labels) != values.size:
        raise ValueError(
            f"periods and series must be aligned; got {len(labels)} and {values.size}"
        )
    rows: list[EpisodeReturn] = []
    for window, (start, end) in windows.items():
        if start > end:
            raise ValueError(f"window {window!r} runs backwards: {start} to {end}")
        keep = [i for i, period in enumerate(labels) if start <= period <= end]
        span = _calendar_months(start, end)
        if not keep:
            rows.append(
                EpisodeReturn(
                    window=window,
                    start=start,
                    end=end,
                    covered=False,
                    partial=False,
                    months=0,
                    cumulative_return=float("nan"),
                    worst_month=float("nan"),
                    peak_to_trough=float("nan"),
                )
            )
            continue
        take = values[np.asarray(keep, dtype=np.intp)]
        curve = np.cumprod(1.0 + take)
        peak = np.maximum.accumulate(curve)
        rows.append(
            EpisodeReturn(
                window=window,
                start=start,
                end=end,
                covered=True,
                partial=len(keep) < span,
                months=len(keep),
                cumulative_return=float(curve[-1]) - 1.0,
                worst_month=float(np.min(take)),
                peak_to_trough=float(np.min(curve / peak - 1.0)),
            )
        )
    return tuple(rows)


def _calendar_months(start: str, end: str) -> int:
    a = int(start[:4]) * 12 + int(start[5:7])
    b = int(end[:4]) * 12 + int(end[5:7])
    return b - a + 1


@dataclass(frozen=True, slots=True, kw_only=True)
class TailDependence:
    """An engine's behaviour in the worst and best ``quantile`` of base months.

    All means are **per month**. ``hit_rate_low`` is the fraction of lower-tail months in
    which the engine's return was positive: a hedge that pays on average because of one
    enormous month is a different object from one that pays reliably, and the two are
    distinguished here rather than in prose.

    ``correlation_low`` is the correlation *within* the lower tail. It is not comparable
    with a full-sample correlation — conditioning on the base's own magnitude truncates
    its variance and biases the conditional correlation downward in absolute value even
    under joint normality. Read it against ``correlation_high`` from the same design,
    never against ``correlation_full``.
    """

    quantile: float
    months_low: int
    months_high: int
    base_mean_low: float
    base_mean_high: float
    mean_low: float
    mean_high: float
    hit_rate_low: float
    worst_low: float
    correlation_low: float
    correlation_high: float
    correlation_full: float


def tail_dependence(
    base: Sequence[float] | FloatArray,
    engine: Sequence[float] | FloatArray,
    *,
    quantile: float = 0.10,
) -> TailDependence:
    """Split months by the base's own return and describe the engine in each tail.

    ``quantile`` is the fraction of months in each tail; 0.10 takes the worst and best
    deciles of base months. The split is on the base series alone, so the same months are
    selected for every engine measured against it and the rows of a table are comparable.
    """
    b = _series(base, name="base")
    e = _series(engine, name="engine")
    if b.shape != e.shape:
        raise ValueError("base and engine must be aligned")
    if not 0.0 < quantile < 0.5:
        raise ValueError(f"quantile must lie in (0, 0.5), got {quantile}")
    count = math.floor(quantile * b.size)
    if count < MINIMUM_TAIL_MONTHS:
        raise ValueError(
            f"a {quantile:.0%} tail of {b.size} months is {count} observations, below the "
            f"{MINIMUM_TAIL_MONTHS}-month floor; widen the quantile or report the panel "
            f"as unable to answer"
        )
    order = np.argsort(b, kind="stable")
    low = order[:count]
    high = order[-count:]
    return TailDependence(
        quantile=quantile,
        months_low=count,
        months_high=count,
        base_mean_low=float(np.mean(b[low])),
        base_mean_high=float(np.mean(b[high])),
        mean_low=float(np.mean(e[low])),
        mean_high=float(np.mean(e[high])),
        hit_rate_low=float(np.mean(e[low] > 0.0)),
        worst_low=float(np.min(e[low])),
        correlation_low=_correlation(b[low], e[low]),
        correlation_high=_correlation(b[high], e[high]),
        correlation_full=_correlation(b, e),
    )


def _correlation(x: FloatArray, y: FloatArray) -> float:
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineSummary:
    """The unconditional price of holding an engine, beside its conditional promise.

    ``geometric_return`` is the realised compound rate of the supplied series. When the
    series is an **excess** return it is the compound rate of the excess, which is not a
    total return and must not be quoted as one.
    """

    months: int
    arithmetic_return: float
    geometric_return: float
    volatility: float
    sharpe: float
    max_drawdown: float
    months_under_water: int
    correlation_to_base: float


def engine_summary(
    engine: Sequence[float] | FloatArray,
    *,
    base: Sequence[float] | FloatArray | None = None,
) -> EngineSummary:
    """Annualised moments, drawdown of the compounded excess path, and correlation.

    The drawdown is computed on the compounded path of the series as supplied. For an
    excess-return series that is the drawdown *relative to cash*, which is deeper than
    the total-return drawdown in a high-rate era and shallower in a low-rate one. The
    caller decides which it wants by choosing what it passes in.
    """
    e = _series(engine, name="engine")
    volatility = float(np.std(e, ddof=1)) * math.sqrt(MONTHS_PER_YEAR)
    curve = np.cumprod(1.0 + e)
    peak = np.maximum.accumulate(curve)
    underwater = curve < peak
    correlation = float("nan")
    if base is not None:
        b = _series(base, name="base")
        if b.shape != e.shape:
            raise ValueError("base and engine must be aligned")
        correlation = _correlation(b, e)
    return EngineSummary(
        months=int(e.size),
        arithmetic_return=float(np.mean(e)) * MONTHS_PER_YEAR,
        geometric_return=float(curve[-1]) ** (MONTHS_PER_YEAR / e.size) - 1.0,
        volatility=volatility,
        sharpe=(
            float("nan")
            if volatility == 0.0
            else float(np.mean(e)) * MONTHS_PER_YEAR / volatility
        ),
        max_drawdown=float(np.min(curve / peak - 1.0)),
        months_under_water=int(np.sum(underwater)),
        correlation_to_base=correlation,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Convexity:
    """A piecewise-linear fit that separates an engine's up-beta from its down-beta.

    The regression is

    ``engine_t = alpha + beta * base_t + kappa * min(base_t, 0) + u_t``

    so ``beta`` is the up-market slope, ``beta + kappa`` is the down-market slope, and
    **``kappa`` is the convexity itself**: negative ``kappa`` means the engine's slope
    against the base is *lower* when the base falls, which is what "performs better in a
    crash than a linear exposure would" means as an estimand. Standard errors are
    Newey-West, because monthly return series are not independent and a naive ``t`` on
    this coefficient is optimistic.

    ``alpha`` is a **per-month intercept in the units supplied**, not an annualised
    premium, and it is the *price of the shape*: an engine may buy negative ``kappa`` by
    paying a negative ``alpha`` every month. Reading ``kappa`` without ``alpha`` is how a
    tail hedge gets sold.

    This is a description of a realised sample, not a test of a promoted claim. Both a
    genuinely convex payoff and a series that happened to rise in three bad months
    produce a negative ``kappa``; ``kappa_t`` and the sample length are reported so the
    difference is visible.
    """

    months: int
    alpha: float
    alpha_t: float
    up_beta: float
    down_beta: float
    kappa: float
    kappa_t: float


def convexity(
    base: Sequence[float] | FloatArray,
    engine: Sequence[float] | FloatArray,
) -> Convexity:
    """Fit the up/down slope split with Newey-West standard errors.

    Requires at least 36 observations. Below that the down-slope is estimated from a
    handful of negative months and the coefficient is not worth printing.
    """
    from portfolio_edge.inference.hac import hac_ols

    b = _series(base, name="base")
    e = _series(engine, name="engine")
    if b.shape != e.shape:
        raise ValueError("base and engine must be aligned")
    if b.size < 36:
        raise ValueError(f"convexity needs at least 36 months; got {b.size}")
    design = np.column_stack([b, np.minimum(b, 0.0)])
    fit = hac_ols(e, design)
    alpha, beta, kappa = (float(c) for c in fit.coefficients)
    alpha_t, _, kappa_t = (float(t) for t in fit.t_statistics)
    return Convexity(
        months=int(b.size),
        alpha=alpha,
        alpha_t=alpha_t,
        up_beta=beta,
        down_beta=beta + kappa,
        kappa=kappa,
        kappa_t=kappa_t,
    )
