"""Timing rules applied to the investor's own equity, kept separate from the data.

Why this module is not :mod:`portfolio_edge.studies.time_series_momentum`
-------------------------------------------------------------------------
That module builds a **long/short, volatility-targeted, multi-instrument** trend book —
the diversifying sleeve of [Experiment 004](../../../../docs/research/trend-marginal-value.md)
and [Experiment 011](../../../../docs/research/capital-efficiency-and-breadth.md). This
one builds something different and much narrower: a **long/flat switch on a single equity
index the investor already owns**. Faber's 10-month simple moving average, and the
12-month absolute-momentum rule it is a near-substitute for.

The two constructions share a signal and share nothing else. A long/short book funded as
notional earns from both signs and never sells the base portfolio; a long/flat switch on
the base portfolio **realises the base portfolio's gains every time it fires**, which in a
taxable account is a cost no long/short overlay pays. Keeping them in one module would
invite exactly the conflation this repository has already had to correct once.

Three conventions, stated because they decide the answer
--------------------------------------------------------
**Alignment.** ``levels[t]`` is the index at the *end* of month ``t``; ``returns[t]`` is
what was earned *during* month ``t``. A signal read at the end of month ``d`` governs the
position held during month ``d + 1 + execution_lag``. Nothing in :func:`in_market` can see
the return the position earns. ``execution_lag = 0`` is the literature's convention —
signal at the close, trade at that close — and is optimistic by exactly the amount an
investor cannot trade instantaneously; ``execution_lag = 1`` is the conservative bound at
monthly resolution.

**Excess returns throughout.** ``risky_excess`` is the index return less the bill. A
constant-weight portfolio holding ``w`` in the index and ``1 - w`` in bills therefore has
excess return ``w * risky_excess`` exactly, with no rebalancing term. That identity is why
:func:`matched_exposure_active_returns` is the honest control and costs nothing to
compute: a timing rule that is out of the market a quarter of the time has a quarter less
beta, and comparing it with a fully invested portfolio credits it for the beta it dropped.

**Costs are inside the rule, not beside it.** :func:`rule_excess_returns` charges
``one_way_cost`` on every change of position, so a whipsaw pays twice. There is no cost on
the initial entry, because the buy-and-hold control has to enter too.

What this module does not contain
---------------------------------
No market data, no cache access and no randomness;
:mod:`portfolio_edge.studies._timing_rules_tables` is the one file that reads the cache.
No parameter search: :func:`rule_grid` enumerates a declared family so that the
*selection* can be deflated, which is the opposite of tuning.
And no claim that a backtested Sharpe ratio means anything before
:mod:`portfolio_edge.inference.deflated_sharpe` has been applied to it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np

from portfolio_edge.core._types import FloatArray, FloatVector
from portfolio_edge.core.drawdown import drawdown_summary

__all__ = [
    "MONTHS_PER_YEAR",
    "Episode",
    "EpisodeLedger",
    "RelativeDrawdown",
    "RuleKind",
    "SeriesSummary",
    "TimingRuleSpec",
    "episode_ledger",
    "in_market",
    "levels_from_returns",
    "matched_exposure_active_returns",
    "out_of_market_episodes",
    "relative_drawdown",
    "rule_excess_returns",
    "rule_grid",
    "summarise",
    "switch_count",
    "time_in_market",
]

MONTHS_PER_YEAR = 12


class RuleKind(Enum):
    """The two signals this module implements, and why only two.

    They are near-substitutes — the difference between them is a smoothing choice, not a
    different idea — and the repository's interest is in whether *that family* survives
    deflation, not in which member of it won a backtest.
    """

    SMA = "sma"
    """In the market when the index closes above its own ``lookback``-month average of
    month-end closes, inclusive of the current close. Faber (2007) at monthly resolution;
    a 200-day average is the same rule sampled daily."""

    ABSOLUTE_MOMENTUM = "absolute_momentum"
    """In the market when the index's total return over the previous ``lookback`` months
    exceeds the benchmark's over the same months. With no benchmark supplied the
    comparison is against zero, which is price momentum; with the bill index supplied it
    is Antonacci's absolute momentum and Moskowitz-Ooi-Pedersen's time-series signal."""


@dataclass(frozen=True)
class TimingRuleSpec:
    """One rule. Frozen so a caller cannot tune it silently between calls."""

    kind: RuleKind
    lookback: int
    execution_lag: int = 0

    def __post_init__(self) -> None:
        minimum = 2 if self.kind is RuleKind.SMA else 1
        if self.lookback < minimum:
            raise ValueError(
                f"{self.kind.value} needs a lookback of at least {minimum}, got "
                f"{self.lookback}; a one-period moving average is the price itself and "
                "the rule degenerates"
            )
        if self.execution_lag < 0:
            raise ValueError(f"execution_lag cannot be negative, got {self.execution_lag}")

    @property
    def burn_in(self) -> int:
        """First month index at which a position can be held without look-ahead.

        The two signals need different amounts of history for the same ``lookback``. A
        ``k``-month moving average needs ``k`` month-end closes ending at the decision
        month, so the decision is formable at index ``k - 1`` and the position at ``k``. A
        ``k``-month return needs the close ``k`` months *before* the decision as well, so
        it costs one extra month. Getting this wrong reads ``levels[-1]`` through NumPy's
        negative indexing and silently scores the first month against the last one.
        """
        offset = 0 if self.kind is RuleKind.SMA else 1
        return self.lookback + self.execution_lag + offset

    @property
    def label(self) -> str:
        suffix = "" if self.execution_lag == 0 else f"+{self.execution_lag}m"
        return f"{self.kind.value}-{self.lookback}{suffix}"


def levels_from_returns(returns: FloatVector, *, initial: float = 1.0) -> FloatArray:
    """Month-end index levels implied by ``returns``, aligned to the same months.

    ``levels[t]`` is the level at the end of month ``t``, so ``levels`` has the same
    length as ``returns`` and the level *before* the sample is never materialised. A rule
    that needs ``lookback`` month-end closes therefore first has a signal at index
    ``lookback - 1`` and first holds a position at index ``lookback``.
    """
    series = np.asarray(returns, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"returns must be one-dimensional, got shape {series.shape}")
    if series.size == 0:
        raise ValueError("returns must not be empty")
    if not np.all(np.isfinite(series)):
        raise ValueError("returns contains non-finite values")
    if initial <= 0.0:
        raise ValueError(f"initial must be positive, got {initial}")
    levels = initial * np.cumprod(1.0 + series)
    if np.any(levels <= 0.0):
        raise ValueError("the implied index level reached zero; this is not a total-return series")
    return levels


def in_market(
    levels: FloatVector,
    *,
    spec: TimingRuleSpec,
    benchmark_levels: FloatVector | None = None,
) -> FloatArray:
    """Position held **during** each month: 1.0 in the index, 0.0 in bills, ``nan`` unformed.

    ``levels`` are month-end index levels. The signal governing month ``t`` is read at the
    end of month ``d = t - 1 - execution_lag``; a position is ``nan`` for every ``t``
    below :attr:`TimingRuleSpec.burn_in`.

    ``benchmark_levels`` is accepted only for :attr:`RuleKind.ABSOLUTE_MOMENTUM`. A moving
    average has no benchmark form, so supplying one for an SMA raises rather than being
    ignored.
    """
    series = np.asarray(levels, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"levels must be one-dimensional, got shape {series.shape}")
    if not np.all(np.isfinite(series)) or np.any(series <= 0.0):
        raise ValueError("levels must be finite and strictly positive")
    if benchmark_levels is not None and spec.kind is not RuleKind.ABSOLUTE_MOMENTUM:
        raise ValueError(
            f"{spec.kind.value} has no benchmark form; a moving average is compared with "
            "itself, not with cash"
        )

    bench: FloatArray | None = None
    if benchmark_levels is not None:
        bench = np.asarray(benchmark_levels, dtype=np.float64)
        if bench.shape != series.shape:
            raise ValueError(
                f"benchmark_levels has shape {bench.shape} but levels has {series.shape}; "
                "they must be the same months"
            )
        if not np.all(np.isfinite(bench)) or np.any(bench <= 0.0):
            raise ValueError("benchmark_levels must be finite and strictly positive")

    out = np.full(series.size, np.nan, dtype=np.float64)
    for index in range(spec.burn_in, series.size):
        decision = index - 1 - spec.execution_lag
        if decision - spec.lookback + 1 < 0 or (
            spec.kind is RuleKind.ABSOLUTE_MOMENTUM and decision - spec.lookback < 0
        ):  # pragma: no cover - burn_in already excludes it; a guard against a regression
            raise AssertionError(f"burn-in is wrong for {spec.label} at index {index}")
        if spec.kind is RuleKind.SMA:
            window = series[decision - spec.lookback + 1 : decision + 1]
            long_signal = float(series[decision]) > float(np.mean(window))
        else:
            growth = float(series[decision]) / float(series[decision - spec.lookback])
            hurdle = (
                1.0
                if bench is None
                else float(bench[decision]) / float(bench[decision - spec.lookback])
            )
            long_signal = growth > hurdle
        out[index] = 1.0 if long_signal else 0.0
    return out


def _live_slice(position: FloatArray) -> tuple[int, int]:
    """First and last index of the contiguous non-``nan`` run of ``position``."""
    live = np.flatnonzero(np.isfinite(position))
    if live.size == 0:
        raise ValueError("position has no formed months")
    first, last = int(live[0]), int(live[-1])
    if not np.all(np.isfinite(position[first : last + 1])):
        raise ValueError("position has a gap inside its live window; bridge it deliberately")
    return first, last


def rule_excess_returns(
    risky_excess: FloatVector,
    *,
    position: FloatVector,
    one_way_cost: float,
) -> FloatArray:
    """The rule's excess return over bills, with its own trading cost charged inside it.

    ``r[t] = position[t] * risky_excess[t] - one_way_cost * |position[t] - position[t-1]|``.
    The position before the first formed month is taken to be the first formed position,
    so the initial entry is free — the buy-and-hold control also has to buy. Months before
    the first formed position are ``nan``.

    ``one_way_cost`` is a fraction of position value paid on each *change* of position, so
    a complete round trip costs twice it and a whipsaw pays for both legs.
    """
    excess = np.asarray(risky_excess, dtype=np.float64)
    weights = np.asarray(position, dtype=np.float64)
    if excess.ndim != 1 or weights.shape != excess.shape:
        raise ValueError(
            f"risky_excess {excess.shape} and position {weights.shape} must be the same 1-D shape"
        )
    if not np.all(np.isfinite(excess)):
        raise ValueError("risky_excess contains non-finite values")
    if one_way_cost < 0.0:
        raise ValueError(f"one_way_cost cannot be negative, got {one_way_cost}")
    first, last = _live_slice(weights)

    out = np.full(excess.size, np.nan, dtype=np.float64)
    previous = float(weights[first])
    for index in range(first, last + 1):
        weight = float(weights[index])
        out[index] = weight * float(excess[index]) - one_way_cost * abs(weight - previous)
        previous = weight
    return out


def matched_exposure_active_returns(
    risky_excess: FloatVector,
    *,
    position: FloatVector,
    one_way_cost: float,
) -> FloatArray:
    """The rule less a constant-weight control at the rule's own average exposure.

    The control holds ``w = mean(position)`` in the index and ``1 - w`` in bills, so its
    excess return is ``w * risky_excess`` identically and the cash leg cancels. The active
    return is therefore ``(position[t] - w) * risky_excess[t]`` less the rule's trading
    cost, and its mean is exactly the beta-matched gap a reader should quote.

    This is the comparison an unmatched backtest gets wrong. A rule out of the market a
    quarter of the time carries three-quarters of the beta; scored against a fully
    invested portfolio it is credited for the risk it declined to take.
    """
    excess = np.asarray(risky_excess, dtype=np.float64)
    weights = np.asarray(position, dtype=np.float64)
    first, last = _live_slice(weights)
    average = float(np.mean(weights[first : last + 1]))
    rule = rule_excess_returns(excess, position=weights, one_way_cost=one_way_cost)
    out = np.full(excess.size, np.nan, dtype=np.float64)
    out[first : last + 1] = rule[first : last + 1] - average * excess[first : last + 1]
    return out


def time_in_market(position: FloatVector) -> float:
    """Average exposure over the formed months."""
    weights = np.asarray(position, dtype=np.float64)
    first, last = _live_slice(weights)
    return float(np.mean(weights[first : last + 1]))


def switch_count(position: FloatVector) -> int:
    """Number of changes of position over the formed months. A round trip counts two."""
    weights = np.asarray(position, dtype=np.float64)
    first, last = _live_slice(weights)
    window = weights[first : last + 1]
    return int(np.count_nonzero(np.diff(window) != 0.0))


@dataclass(frozen=True)
class SeriesSummary:
    """Everything a reader needs to compare two return series on the same axis."""

    label: str
    months: int
    geometric_excess: float
    """Annualised geometric excess return over bills."""
    geometric_total: float
    """Annualised geometric total return, bills added back."""
    volatility: float
    sharpe: float
    max_drawdown: float
    """Signed and non-positive, measured on the **total** wealth curve."""
    max_time_under_water: int
    worst_twelve_months: float
    """Worst compounded total return over any twelve consecutive months."""
    skewness: float
    kurtosis: float
    """Non-excess fourth standardised moment; a normal sample reads 3.0."""


def summarise(
    excess: FloatVector, *, cash: FloatVector, label: str, periods_per_year: int = MONTHS_PER_YEAR
) -> SeriesSummary:
    """Summarise an excess-return series against the bill series it is excess of."""
    series = np.asarray(excess, dtype=np.float64)
    bills = np.asarray(cash, dtype=np.float64)
    if series.shape != bills.shape:
        raise ValueError(f"excess {series.shape} and cash {bills.shape} must be the same shape")
    live = np.isfinite(series)
    if not np.any(live):
        raise ValueError("excess has no finite months")
    if not np.all(np.isfinite(bills[live])):
        raise ValueError("cash is missing where excess is present")

    e = series[live]
    total = e + bills[live]
    months = int(e.size)
    years = months / periods_per_year
    curve = np.cumprod(1.0 + total)
    summary = drawdown_summary(curve)
    volatility = float(np.std(e, ddof=1)) * math.sqrt(periods_per_year)
    mean = float(np.mean(e))
    centred = e - mean
    variance = float(np.mean(centred**2))
    worst_12 = float("nan")
    if months >= periods_per_year:
        gross = 1.0 + total
        rolling = np.array(
            [float(np.prod(gross[i : i + periods_per_year])) - 1.0 for i in range(months - 11)],
            dtype=np.float64,
        )
        worst_12 = float(np.min(rolling))
    return SeriesSummary(
        label=label,
        months=months,
        geometric_excess=float(np.prod(1.0 + e) ** (1.0 / years) - 1.0),
        geometric_total=float(curve[-1] ** (1.0 / years) - 1.0),
        volatility=volatility,
        sharpe=mean / float(np.std(e, ddof=1)) * math.sqrt(periods_per_year),
        max_drawdown=summary.max_drawdown,
        max_time_under_water=summary.max_time_under_water,
        worst_twelve_months=worst_12,
        skewness=float(np.mean(centred**3) / variance**1.5) if variance > 0.0 else 0.0,
        kurtosis=float(np.mean(centred**4) / variance**2) if variance > 0.0 else 3.0,
    )


@dataclass(frozen=True)
class Episode:
    """One uninterrupted spell out of the market, and what declining to hold was worth."""

    start: int
    """First month index held in bills."""
    end: int
    """Last month index held in bills, inclusive."""
    months: int
    avoided: float
    """Compounded index excess return the rule did **not** earn, sign-flipped: positive
    means the exit helped. Net of the round trip's ``2 * one_way_cost``."""

    @property
    def helped(self) -> bool:
        return self.avoided > 0.0


def out_of_market_episodes(
    risky_excess: FloatVector, *, position: FloatVector, one_way_cost: float
) -> tuple[Episode, ...]:
    """Every spell out of the market, in order.

    Only the exits are scored, because being *in* the market is not a decision the rule
    makes — it is the default the investor already had. A closing spell still open at the
    last observation is included and flagged by its ``end``.
    """
    excess = np.asarray(risky_excess, dtype=np.float64)
    weights = np.asarray(position, dtype=np.float64)
    first, last = _live_slice(weights)
    if one_way_cost < 0.0:
        raise ValueError(f"one_way_cost cannot be negative, got {one_way_cost}")

    episodes: list[Episode] = []
    index = first
    while index <= last:
        if weights[index] != 0.0:
            index += 1
            continue
        start = index
        while index <= last and weights[index] == 0.0:
            index += 1
        end = index - 1
        forgone = float(np.prod(1.0 + excess[start : end + 1]) - 1.0)
        episodes.append(
            Episode(
                start=start,
                end=end,
                months=end - start + 1,
                avoided=-forgone - 2.0 * one_way_cost,
            )
        )
    return tuple(episodes)


@dataclass(frozen=True)
class EpisodeLedger:
    """The whipsaw record: what the investor would actually have had to sit through."""

    episodes: int
    helped: int
    hurt: int
    total_avoided: float
    """Sum of episode gains. Not a return — episodes are not contiguous — but it is the
    right accounting for "how much of the benefit came from how few decisions".

    It is measured against **staying fully invested**, not against the beta-matched
    control, because that is the comparison the investor experiences: the exit either
    dodged a fall or missed a rise. A negative total with a positive beta-matched gap is
    not a contradiction; it means the rule's measured gap comes from carrying less beta
    rather than from the timing of its exits."""
    best_three_total: float
    """Sum of the three best episodes."""
    remainder_total: float
    """``total_avoided`` less :attr:`best_three_total` — what every other exit was worth
    between them."""
    worst_losing_run: int
    """Longest run of consecutive exits that lost money."""
    worst_losing_run_cost: float
    """Summed loss over that run."""
    worst_losing_run_span: tuple[int, int]
    """First and last month index of that run."""
    median_episode_months: float


def episode_ledger(episodes: Sequence[Episode]) -> EpisodeLedger:
    """Aggregate :func:`out_of_market_episodes` into the behavioural statistics."""
    if not episodes:
        raise ValueError("no out-of-market episodes; the rule never left the index")
    gains = np.array([episode.avoided for episode in episodes], dtype=np.float64)
    total = float(np.sum(gains))
    best_three = float(np.sum(np.sort(gains)[-3:]))

    worst_length = 0
    worst_cost = 0.0
    worst_span = (episodes[0].start, episodes[0].end)
    run_length = 0
    run_cost = 0.0
    run_start = 0
    for index, episode in enumerate(episodes):
        if episode.avoided <= 0.0:
            if run_length == 0:
                run_start = index
            run_length += 1
            run_cost += episode.avoided
            if run_length > worst_length or (
                run_length == worst_length and run_cost < worst_cost
            ):
                worst_length = run_length
                worst_cost = run_cost
                worst_span = (episodes[run_start].start, episode.end)
        else:
            run_length = 0
            run_cost = 0.0
    return EpisodeLedger(
        episodes=len(episodes),
        helped=int(np.count_nonzero(gains > 0.0)),
        hurt=int(np.count_nonzero(gains <= 0.0)),
        total_avoided=total,
        best_three_total=best_three,
        remainder_total=total - best_three,
        worst_losing_run=worst_length,
        worst_losing_run_cost=worst_cost,
        worst_losing_run_span=worst_span,
        median_episode_months=float(np.median([episode.months for episode in episodes])),
    )


@dataclass(frozen=True)
class RelativeDrawdown:
    """How far behind its control a rule fell, and for how long.

    This is the holdability statistic. An investor does not abandon a rule because its
    Sharpe ratio fell; they abandon it because it spent nine years behind the portfolio
    they would otherwise have owned.
    """

    max_shortfall: float
    """Signed and non-positive: the worst peak-to-trough fall of the ratio of the rule's
    wealth to the control's."""
    max_months_behind: int
    """Longest run below a previous high of that ratio."""
    peak_index: int
    """Index, in the common window, of the high the ratio fell furthest from. When it sits
    early in a long sample, the rule's entire lifetime advantage was earned before it."""
    trough_index: int
    final_months_behind: int
    open_at_end: bool


def relative_drawdown(
    rule_excess: FloatVector, *, control_excess: FloatVector, cash: FloatVector
) -> RelativeDrawdown:
    """Drawdown of ``rule / control`` measured on total wealth, over the common months."""
    rule = np.asarray(rule_excess, dtype=np.float64)
    control = np.asarray(control_excess, dtype=np.float64)
    bills = np.asarray(cash, dtype=np.float64)
    if rule.shape != control.shape or rule.shape != bills.shape:
        raise ValueError("rule, control and cash must be the same shape")
    live = np.isfinite(rule) & np.isfinite(control) & np.isfinite(bills)
    if not np.any(live):
        raise ValueError("no common months")
    ratio = np.cumprod((1.0 + rule[live] + bills[live]) / (1.0 + control[live] + bills[live]))
    summary = drawdown_summary(ratio)
    return RelativeDrawdown(
        max_shortfall=summary.max_drawdown,
        max_months_behind=summary.max_time_under_water,
        peak_index=summary.peak_index,
        trough_index=summary.trough_index,
        final_months_behind=summary.final_time_under_water,
        open_at_end=summary.open_at_end,
    )


def rule_grid(
    *, lookbacks: Sequence[int] | None = None, execution_lag: int = 0
) -> tuple[TimingRuleSpec, ...]:
    """The declared family of rules, enumerated so the selection can be deflated.

    Both signals at every lookback from 2 to 24 months. The point is **not** to find the
    best member. It is that the 10-month SMA and the 12-month momentum rule were selected
    from at least this family by the literature, so a Sharpe ratio quoted for either is an
    order statistic over at least this many trials and must be deflated as one. The true
    search is far larger than this grid — daily windows, dual and fractional weights, other
    indices — so any trial count derived from it is a **lower bound** and the deflated
    significance it produces is an upper bound on the evidence.
    """
    windows = tuple(lookbacks) if lookbacks is not None else tuple(range(2, 25))
    if not windows:
        raise ValueError("lookbacks must not be empty")
    return tuple(
        TimingRuleSpec(kind=kind, lookback=lookback, execution_lag=execution_lag)
        for kind in (RuleKind.SMA, RuleKind.ABSOLUTE_MOMENTUM)
        for lookback in windows
    )


# --------------------------------------------------------------------------------------
# After tax, on the realised path rather than on an average growth rate
# --------------------------------------------------------------------------------------
#
# :func:`portfolio_edge.studies.tax_structure.after_tax_path` compounds one dollar at a
# *constant* growth rate under a stated realisation fraction. That is the right instrument
# for a fund's turnover and the wrong one here: a timing rule's realisations are not a
# fraction of standing gain each year, they are the whole position on the months the
# signal fires, and whether the gain is short- or long-term depends on how long the rule
# happened to stay in. The tax outcome is a property of the *path*, so it is simulated on
# the path.


class Disposal(Enum):
    """What happens to the unrealised gain at the horizon. Mirrors
    :class:`portfolio_edge.studies.tax_structure.Disposal`, restated here so this
    simulation does not import a constant it would then have to keep in step."""

    LIQUIDATE = "liquidate"
    STEP_UP = "step_up"


@dataclass(frozen=True)
class TaxableAssumptions:
    """Every rate and yield the taxable simulation uses. All of them are arguments.

    ``dividend_yield`` is annual and applied to market value at ``1/12`` a month. It is a
    stated assumption, not a measured series, because the decision-relevant yield is the
    one the investor faces now and not the 5% of the 1930s; the tables run a sensitivity
    over it.
    """

    ordinary_rate: float
    long_term_rate: float
    dividend_yield: float
    qualified_fraction: float = 1.0
    long_term_months: int = 12
    """26 U.S.C. §1222: a holding period of **more than** one year. A position held
    exactly twelve months is short-term."""

    def __post_init__(self) -> None:
        for name in ("ordinary_rate", "long_term_rate", "dividend_yield", "qualified_fraction"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1], got {value}")
        if self.long_term_rate > self.ordinary_rate:
            raise ValueError("a long-term rate above the ordinary rate inverts the answer")
        if self.long_term_months < 0:
            raise ValueError("long_term_months cannot be negative")


@dataclass(frozen=True)
class AfterTaxOutcome:
    """Terminal state of one dollar run through the realised path."""

    label: str
    months: int
    terminal_wealth: float
    """After every tax charged along the way, before any terminal disposal."""
    terminal_after_disposal: float
    cumulative_tax: float
    realised_short_term_gain: float
    realised_long_term_gain: float
    unused_loss_carryforward: float
    """Capital losses never absorbed. They expire worthless in this model, which
    understates the rule's after-tax result by the value of the omitted $3,000-a-year
    ordinary-income offset (26 U.S.C. §1211(b)) and of any gain realised elsewhere."""
    turnover_cost_paid: float
    annualised_after_tax_growth: float
    """``log(terminal_after_disposal) / years``. Log growth, because it is the only
    difference measure that adds across years."""


def taxable_path(
    *,
    label: str,
    position: FloatVector,
    risky_total: FloatVector,
    cash: FloatVector,
    assumptions: TaxableAssumptions,
    one_way_cost: float,
    disposal: Disposal = Disposal.LIQUIDATE,
    rebalance_band: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> AfterTaxOutcome:
    """Compound one dollar through ``position`` in a US taxable account.

    ``risky_total`` is the index's **total** return and ``cash`` the bill return, both
    simple and monthly. ``position`` is a weight in ``[0, 1]``; the rest sits in bills.

    The bookkeeping, stated because tax arithmetic goes wrong when each lever invents its
    own convention:

    * **Tax is paid out of the account.** Paying it from an external wallet is a disguised
      contribution and flatters every deferral figure.
    * **Dividends are reinvested and raise basis**, and the tax on them is met by selling
      the shares whose basis was just stepped up, so the standing unrealised gain is
      unchanged by a distribution.
    * **Basis is average cost** across the position, and the holding period is the
      value-weighted average acquisition month. For a long/flat rule, which sells the
      entire position or none of it, both are exact; for a partial sale they are an
      approximation whose direction is not signed.
    * **Losses carry forward against later capital gains only**, at the rate of the gain
      they offset. The §1211(b) ordinary offset and cross-character netting under §1222
      are omitted; both would improve the timing rule's figure, so this is the
      conservative direction for buy-and-hold.
    * **Transaction cost is charged on the traded notional** and reduces proceeds before
      the gain is computed, which is what a spread actually does.
    * ``rebalance_band`` is the absolute weight deviation tolerated before a trade. The
      first month always trades, to establish the position. ``0.0`` tracks ``position``
      exactly and is what a long/flat rule needs; ``1.0`` never trades again and is how a
      *never-rebalanced* static blend is expressed, which matters because a monthly
      rebalanced blend realises gains a buy-and-hold blend does not.
    """
    weights = np.asarray(position, dtype=np.float64)
    total = np.asarray(risky_total, dtype=np.float64)
    bills = np.asarray(cash, dtype=np.float64)
    if weights.shape != total.shape or weights.shape != bills.shape:
        raise ValueError("position, risky_total and cash must be the same shape")
    if one_way_cost < 0.0:
        raise ValueError(f"one_way_cost cannot be negative, got {one_way_cost}")
    if not 0.0 <= rebalance_band <= 1.0:
        raise ValueError(f"rebalance_band must lie in [0, 1], got {rebalance_band}")
    first, last = _live_slice(weights)
    if np.any(weights[first : last + 1] < 0.0) or np.any(weights[first : last + 1] > 1.0):
        raise ValueError(
            "position must lie in [0, 1]; this simulation has no short and no leverage"
        )
    if not np.all(np.isfinite(total[first : last + 1])) or not np.all(
        np.isfinite(bills[first : last + 1])
    ):
        raise ValueError("risky_total or cash is missing inside the live window")

    monthly_dividend = assumptions.dividend_yield / periods_per_year
    qualified_rate = assumptions.long_term_rate
    ordinary_rate = assumptions.ordinary_rate

    equity = 0.0
    equity_basis = 0.0
    acquired = float(first)
    cash_value = 1.0
    tax_paid = 0.0
    cost_paid = 0.0
    carryforward = 0.0
    short_gain = 0.0
    long_gain = 0.0

    def realise(gain: float, held_months: float) -> float:
        nonlocal carryforward, short_gain, long_gain
        if gain < 0.0:
            carryforward += -gain
            return 0.0
        usable = min(gain, carryforward)
        carryforward -= usable
        taxable = gain - usable
        if held_months > assumptions.long_term_months:
            long_gain += gain
            return assumptions.long_term_rate * taxable
        short_gain += gain
        return ordinary_rate * taxable

    for index in range(first, last + 1):
        target = float(weights[index])
        wealth = equity + cash_value
        current = equity / wealth if wealth > 0.0 else 0.0
        if index != first and abs(current - target) <= rebalance_band:
            target = current
        desired = target * wealth
        delta = desired - equity
        if delta > 0.0:
            cost = one_way_cost * delta
            cost_paid += cost
            cash_value -= delta
            added = delta - cost
            new_basis = equity_basis + added
            acquired = (
                (acquired * equity_basis + float(index) * added) / new_basis
                if new_basis > 0.0
                else float(index)
            )
            equity += added
            equity_basis = new_basis
        elif delta < 0.0 and equity > 0.0:
            sold = min(-delta, equity)
            fraction = sold / equity
            proceeds = sold * (1.0 - one_way_cost)
            cost_paid += sold * one_way_cost
            basis_released = equity_basis * fraction
            tax = realise(proceeds - basis_released, float(index) - acquired)
            tax_paid += tax
            equity -= sold
            equity_basis -= basis_released
            cash_value += proceeds - tax

        if equity > 0.0:
            opening = equity
            equity *= 1.0 + float(total[index])
            dividend = opening * monthly_dividend
            qualified = assumptions.qualified_fraction * dividend
            dividend_tax = qualified_rate * qualified + ordinary_rate * (dividend - qualified)
            equity -= dividend_tax
            equity_basis += dividend - dividend_tax
            tax_paid += dividend_tax
            if equity <= 0.0:
                raise ValueError("the equity leg reached zero; check the return series")
        if cash_value > 0.0:
            interest = cash_value * float(bills[index])
            interest_tax = ordinary_rate * max(interest, 0.0)
            cash_value += interest - interest_tax
            tax_paid += interest_tax

    terminal = equity + cash_value
    after_disposal = terminal
    if disposal is Disposal.LIQUIDATE and equity > 0.0:
        held = float(last) - acquired
        tax = realise(equity - equity_basis, held)
        tax_paid += tax
        after_disposal = terminal - tax

    months = last - first + 1
    years = months / periods_per_year
    return AfterTaxOutcome(
        label=label,
        months=months,
        terminal_wealth=terminal,
        terminal_after_disposal=after_disposal,
        cumulative_tax=tax_paid,
        realised_short_term_gain=short_gain,
        realised_long_term_gain=long_gain,
        unused_loss_carryforward=carryforward,
        turnover_cost_paid=cost_paid,
        annualised_after_tax_growth=math.log(after_disposal) / years,
    )


def sheltered_path(
    *,
    label: str,
    position: FloatVector,
    risky_total: FloatVector,
    cash: FloatVector,
    one_way_cost: float,
    rebalance_band: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> AfterTaxOutcome:
    """The same path inside a Roth or traditional account: no internal tax at all.

    Traditional and Roth differ by a constant multiplier that cancels out of every
    comparison made here — see
    :func:`portfolio_edge.studies.tax_structure.traditional_and_roth_are_equivalent` — so
    one simulation serves both. The only surviving frictions are the spread and the
    forgone equity risk premium.
    """
    zero = TaxableAssumptions(
        ordinary_rate=0.0, long_term_rate=0.0, dividend_yield=0.0, qualified_fraction=1.0
    )
    return taxable_path(
        label=label,
        position=position,
        risky_total=risky_total,
        cash=cash,
        assumptions=zero,
        one_way_cost=one_way_cost,
        disposal=Disposal.STEP_UP,
        rebalance_band=rebalance_band,
        periods_per_year=periods_per_year,
    )


if __name__ == "__main__":  # pragma: no cover - regenerates the published timing tables
    from portfolio_edge.studies._timing_rules_tables import main

    main()
