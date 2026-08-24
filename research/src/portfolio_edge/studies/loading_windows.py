"""Windows on loadings: what a factor loading may be compared with, and what it may not.

Why this module exists
----------------------
Two errors, both cheap to make and both expensive to publish.

**The first is comparing loadings estimated on different months.** Every factor loading
in ``src/content/shelf.ts`` was fitted on the intersection of a frozen common period with
the fund's own filed history, so a fund that listed in 2019 carries 72 months and one that
listed in 2022 carries 36. Those are not two measurements of the same thing on a common
scale; they are two measurements taken through instruments of different length, in a
period when the value spread itself moved a lot. Ranking them produces an ordering of
launch dates as much as an ordering of funds. :class:`LoadingEstimate` therefore carries
its :class:`Window`, and :func:`rank` **raises** on a mixed-window set rather than sorting
it, in the tradition of ``studies.outperformance_horizon.aggregate()`` refusing to add
results measured against different benchmarks.

**The second is believing a wrapper's delivered exposure cannot be measured.** It can. A
fund's own monthly total return is filed in Item B.5 of Form N-PORT, net of the fund's own
ongoing fees and with distributions reinvested, and
:mod:`portfolio_edge.data.nport` has read it since Experiment 008. Anything with filings
can therefore be regressed on a trend benchmark, a stacked wrapper included. That needs no
price feed and no licence, so decision 0002 does not reach it: 0002 is about scraped
*price* series with no documented total-return contract, and Item B.5 is not one.

What this module is, and what it is not
---------------------------------------
It is arithmetic and inference over arrays that a caller supplies. It touches no cache and
downloads nothing, so it is testable against generated fixtures.
:mod:`portfolio_edge.studies._loading_windows_tables` is the half that reads filings.

Everything computed here is `exploratory`. The windows involved run from 30 to 78 months.
A 31-month window is roughly one market regime; it can show that an exposure is present,
and it cannot show that an exposure is stable, so no ordering produced here is durable.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from portfolio_edge.inference.hac import hac_ols

__all__ = [
    "MDE_MULTIPLIER",
    "IncomparableWindowsError",
    "LoadingEstimate",
    "Window",
    "common_window",
    "estimate_loadings",
    "minimum_detectable_loading",
    "month_index",
    "period_from_index",
    "rank",
    "require_contiguous",
    "rolling_windows",
    "window_ending",
]

FloatArray = NDArray[np.float64]

#: ``z_{0.975} + z_{0.80} = 2.802``. The smallest true loading a two-sided 5% test of this
#: precision would find 80% of the time is this multiple of the standard error. Reported
#: beside every estimate here because the windows are short and an interval that spans the
#: decision threshold is usually a statement about the window, not about the fund.
MDE_MULTIPLIER: Final = float(norm.ppf(0.975) + norm.ppf(0.80))

#: The two-sided 95% normal critical value used for every interval printed here.
_Z95: Final = float(norm.ppf(0.975))


def month_index(period: str) -> int:
    """``YYYY-MM`` to a count of months, so windows can be sliced with arithmetic."""
    if len(period) != 7 or period[4] != "-":
        raise ValueError(f"expected a YYYY-MM period, got {period!r}")
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def period_from_index(index: int) -> str:
    """Inverse of :func:`month_index`."""
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


@dataclass(frozen=True, slots=True, order=True)
class Window:
    """A closed range of calendar months, ``first`` and ``last`` inclusive.

    A window is part of a loading's identity, not metadata about it. Two loadings with
    different windows are answers to different questions.
    """

    first: str
    last: str

    def __post_init__(self) -> None:
        if month_index(self.last) < month_index(self.first):
            raise ValueError(f"window {self.first}..{self.last} ends before it begins")

    @property
    def months(self) -> int:
        """Length in months, inclusive of both endpoints."""
        return month_index(self.last) - month_index(self.first) + 1

    @property
    def label(self) -> str:
        return f"{self.first}..{self.last}"

    def periods(self) -> tuple[str, ...]:
        """Every month in the window, in order."""
        start = month_index(self.first)
        return tuple(period_from_index(start + offset) for offset in range(self.months))

    def overlap(self, other: Window) -> Window | None:
        """The months both windows contain, or ``None`` when they are disjoint."""
        first = max(month_index(self.first), month_index(other.first))
        last = min(month_index(self.last), month_index(other.last))
        if last < first:
            return None
        return Window(period_from_index(first), period_from_index(last))


def window_ending(last: str, months: int) -> Window:
    """The ``months``-long window ending on ``last``.

    This is the rule that recovers a published window from a published month count, and it
    is a *derivation*, not a record. It holds for this repository's three product audits
    because each freezes a common period ending 2025-12 and estimates each fund on the
    longest contiguous run of its own filed months inside that period, so a fund with
    ``n`` months has the trailing ``n``. ``_loading_windows_tables`` checks the derivation
    by reproducing seventeen published loadings from it exactly; it is not assumed.
    """
    if months < 1:
        raise ValueError(f"a window needs at least one month, got {months}")
    return Window(period_from_index(month_index(last) - months + 1), last)


def require_contiguous(periods: Sequence[str]) -> None:
    """Raise unless ``periods`` is a sorted, gapless run of months.

    Every estimator here assumes adjacency. A Newey-West covariance laid across a hole
    treats two months a year apart as neighbours, and a rolling window laid across one
    reports a period nobody measured.
    """
    indices = [month_index(period) for period in periods]
    gaps = [
        f"{period_from_index(earlier)}->{period_from_index(later)}"
        for earlier, later in pairwise(indices)
        if later - earlier != 1
    ]
    if gaps:
        raise ValueError(
            "these months are not a contiguous sorted run, so no window over them is "
            "the period it claims to be: " + ", ".join(gaps[:6])
        )


def rolling_windows(periods: Sequence[str], length: int) -> tuple[Window, ...]:
    """Every contiguous ``length``-month window inside ``periods``.

    ``periods`` must be contiguous and sorted; a gap would put a window across months that
    do not exist, which is how a rolling chart acquires numbers nobody measured.
    """
    if length < 1:
        raise ValueError(f"window length must be positive, got {length}")
    require_contiguous(periods)
    if len(periods) < length:
        return ()
    return tuple(
        Window(periods[start], periods[start + length - 1])
        for start in range(len(periods) - length + 1)
    )


class IncomparableWindowsError(ValueError):
    """Two loadings estimated on different months were about to be ranked."""


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadingEstimate:
    """One regression coefficient, inseparable from the months that produced it."""

    ticker: str
    factor: str
    """The regressor's name, e.g. ``HML`` or ``TSMOM``."""
    benchmark: str
    """Which panel or index the regressor came from. Two panels are two questions."""
    value: float
    standard_error: float
    window: Window

    def __post_init__(self) -> None:
        if self.standard_error < 0.0:
            raise ValueError(f"{self.ticker}: a standard error cannot be negative")

    @property
    def months(self) -> int:
        return self.window.months

    @property
    def t_statistic(self) -> float:
        return self.value / self.standard_error if self.standard_error > 0.0 else float("inf")

    @property
    def interval95(self) -> tuple[float, float]:
        half = _Z95 * self.standard_error
        return self.value - half, self.value + half

    @property
    def minimum_detectable_loading(self) -> float:
        """The smallest true loading this window could have found at 80% power."""
        return minimum_detectable_loading(self.standard_error)

    def excludes(self, bar: float) -> bool:
        """Whether the 95% interval lies wholly above or wholly below ``bar``."""
        low, high = self.interval95
        return low > bar or high < bar

    def format(self) -> str:
        low, high = self.interval95
        return (
            f"{self.value:+.3f} [{low:+.3f}, {high:+.3f}] "
            f"t={self.t_statistic:+.2f} n={self.months} {self.window.label} "
            f"mde={self.minimum_detectable_loading:.3f}"
        )


def minimum_detectable_loading(
    standard_error: float, *, power: float = 0.80, significance: float = 0.05
) -> float:
    """``(z_{1-a/2} + z_{power}) * SE``: the resolution of the instrument, not of the fund."""
    if standard_error < 0.0:
        raise ValueError("standard_error cannot be negative")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must lie in (0, 1), got {power}")
    if not 0.0 < significance < 1.0:
        raise ValueError(f"significance must lie in (0, 1), got {significance}")
    multiplier = float(norm.ppf(1.0 - significance / 2.0) + norm.ppf(power))
    return multiplier * standard_error


def common_window(windows: Iterable[Window]) -> Window:
    """The months every window contains.

    Raises when the windows do not all overlap, because an empty intersection means the
    funds were never observed together and no comparison between them exists.
    """
    listed = list(windows)
    if not listed:
        raise ValueError("no windows supplied")
    running: Window | None = listed[0]
    for window in listed[1:]:
        if running is None:  # pragma: no cover - unreachable; the loop returns first
            break
        running = running.overlap(window)
        if running is None:
            raise IncomparableWindowsError(
                "these estimation windows do not all overlap, so no month exists on which "
                "every fund was observed and there is no comparison to make"
            )
    assert running is not None
    return running


def rank(estimates: Sequence[LoadingEstimate]) -> tuple[LoadingEstimate, ...]:
    """``estimates`` sorted by loading, largest first — but only if they are comparable.

    Raises :class:`IncomparableWindowsError` when the estimates were not all fitted on the
    same months. This is the guardrail, not a convenience: sorting a mixed-window set
    produces an ordering that partly reflects when each fund happened to launch, and the
    published US value shelf is exactly such a set.
    """
    if not estimates:
        return ()
    windows = {estimate.window for estimate in estimates}
    if len(windows) > 1:
        detail = ", ".join(
            f"{estimate.ticker} {estimate.window.label} ({estimate.months}m)"
            for estimate in estimates
        )
        raise IncomparableWindowsError(
            "refusing to rank loadings fitted on different months: "
            + detail
            + ". Refit them on the common window first; a ranking across unequal windows "
            "orders launch dates as well as funds."
        )
    factors = {estimate.factor for estimate in estimates}
    benchmarks = {estimate.benchmark for estimate in estimates}
    if len(factors) > 1 or len(benchmarks) > 1:
        raise IncomparableWindowsError(
            f"refusing to rank across factors {sorted(factors)} on benchmarks "
            f"{sorted(benchmarks)}: those are different quantities"
        )
    return tuple(sorted(estimates, key=lambda estimate: estimate.value, reverse=True))


def estimate_loadings(
    *,
    ticker: str,
    benchmark: str,
    periods: Sequence[str],
    excess_returns: Sequence[float] | FloatArray,
    design: Mapping[str, Sequence[float]],
    n_lags: int,
) -> dict[str, LoadingEstimate]:
    """OLS of ``excess_returns`` on ``design``, with Newey-West standard errors.

    ``design`` maps a regressor name to its values on ``periods``; the intercept is added
    here and is not returned, because this module is about exposure and the alpha over
    these windows is not resolvable (see the module docstring).

    ``periods`` must be a contiguous run of months: a Newey-West covariance laid across a
    gap treats two months that are a year apart as adjacent.
    """
    if not design:
        raise ValueError(f"{ticker}: no regressors supplied")
    months = tuple(periods)
    require_contiguous(months)
    response = np.asarray(excess_returns, dtype=np.float64)
    if response.size != len(months):
        raise ValueError(
            f"{ticker}: {response.size} returns for {len(months)} months; they must align"
        )
    names = tuple(design)
    matrix = np.column_stack([np.asarray(design[name], dtype=np.float64) for name in names])
    if matrix.shape[0] != response.size:
        raise ValueError(f"{ticker}: a regressor has the wrong length for {len(months)} months")
    fit = hac_ols(response, matrix, n_lags=n_lags, add_constant=True)
    window = Window(months[0], months[-1])
    return {
        name: LoadingEstimate(
            ticker=ticker,
            factor=name,
            benchmark=benchmark,
            value=float(fit.coefficients[position + 1]),
            standard_error=float(fit.standard_errors[position + 1]),
            window=window,
        )
        for position, name in enumerate(names)
    }


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._loading_windows_tables import main

    main()
