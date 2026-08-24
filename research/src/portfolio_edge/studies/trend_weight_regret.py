"""How much trend notional to hold when the forward premium is not identified.

Three instruments in this repository return three different trend weights and they
disagree because they answer different questions, not because any of them is wrong: a
variance argument returns 21.6% ``[10.3%, 32.8%]``, a holdability-constrained growth
argument returns 15-25%, and the construction tournament's growth measure runs
monotonically to whatever corner the grid stops at. The tournament's own reading is that
*the prior is the entire disagreement*, and no amount of resampling one window speaks to
it, because every resample inherits that window's mean.

This module builds the decision surface instead of another point estimate. Four ideas
carry it, and each is a separate section below.

**1. One uncertain parameter, in net units.** Every gap here depends on the forward
premium ``p`` and the retail cost ``c`` only through their difference. So the axis is
``m = p - c``: the **net-of-all-cost arithmetic excess over cash that one unit of trend
notional delivers**, at the panel's own trend volatility. Sweeping cost is then a
translation of the premium axis rather than a second dimension, which is stated once here
and never re-derived.

**2. Two benchmarks, never added.** The charter forbids adding results measured against
different comparators, and :mod:`portfolio_edge.studies.overlay_growth` already carries
the algebra for both. ``cheap_index`` is the investor's own unlevered portfolio;
``leverage_matched`` is that portfolio levered to the overlay's gross notional and charged
the same financing, which
``docs/decisions/0009-blocks-lifted-and-closures-rescoped.md`` clause 3 makes mandatory for
any funding-rule result. **They give different answers and the difference is not
empirical.**

**3. Minimax regret does not escape the prior, and the identity in
:func:`minimax_regret_weight` shows exactly how.** Regret is convex in ``m`` for fixed
``w``, so its maximum over an interval sits at an endpoint; equating the two endpoints and
applying the envelope theorem gives

    ``w_minimax = [G*(m_hi) - G*(m_lo)] / (m_hi - m_lo) = mean of w*(m) over the support``

— the minimax-regret weight is the **average of the weights that would have been optimal**,
under a uniform prior on the stated range. When the value function is bang-bang, as it is
against a leverage-matched control, this collapses further to *the grid ceiling times the
fraction of the range in which trend beats the control*. **A minimax rule therefore
replaces a forecast of the premium's mean with a forecast of its endpoints. That is a
real improvement in what has to be defended, and it is not an escape.**

**4. The decision is made by the asymmetry, not by the growth arithmetic.** Growth regret
is symmetric in the sense that it prices only terminal wealth. The two errors are not:
holding trend through a decade in which the premium is zero costs fee, tracking error and
a relative drawdown long enough to end the position, while holding none through a
flat-to-negative equity decade costs the diversification in exactly the episode the sleeve
exists for. :func:`abandonment_adjusted_gap` prices the first arm by making the investor's
own capitulation part of the path, and :func:`conditional_decade_gaps` prices the second by
conditioning on the equity decade rather than averaging over it.

Nothing here is an experiment: no specification is frozen, no hypothesis is adjudicated
and no ledger entry is written. It is a decision surface over quantities other pages
measured, and every input it takes is named with its source in
``docs/research/trend-weight-under-uncertainty.md``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary

__all__ = [
    "AbandonmentOutcome",
    "DecadeGap",
    "OverlayGrowthModel",
    "PremiumPrior",
    "PremiumScenario",
    "RegretSurface",
    "abandonment_adjusted_gap",
    "conditional_decade_gaps",
    "minimax_regret_weight",
    "regret_from_gaps",
    "regret_surface",
    "restate_annual_mean",
    "robust_range",
    "years_to_resolve",
]

FloatArray = NDArray[np.float64]

MONTHS_PER_YEAR: Final = 12

#: The two comparators. They are a ``Literal`` rather than a string so that mypy refuses a
#: caller who invents a third one, and so that a result object always records which of the
#: charter's three questions it answered.
Benchmark = Literal["cheap_index", "leverage_matched"]


# --------------------------------------------------------------------------------
# 1. The growth model: two closed forms, one uncertain parameter
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class OverlayGrowthModel:
    """After-cost log-growth gaps for a financed trend overlay, in closed form.

    All rates are annual arithmetic excesses over cash. The overlay adds ``w`` units of
    trend notional to a base held at 1.0 and sells nothing, which is what a return-stacked
    fund does and what the candidate portfolio actually holds.

    ``equity_excess_return`` is a **forecast**, not a measurement, wherever the
    ``leverage_matched`` benchmark is used: that comparator's break-even is dominated by
    it. Holding the equity leg at its realised mean while haircutting the trend leg to a
    forward one is not a consistent comparison, and this class makes the equity input
    explicit so that the inconsistency cannot be hidden inside a default.
    """

    equity_excess_return: float
    equity_volatility: float
    trend_volatility: float
    correlation: float
    equity_financing_spread: float = 0.0

    def __post_init__(self) -> None:
        if self.equity_volatility <= 0.0:
            raise ValueError(
                f"equity volatility must be positive, got {self.equity_volatility}"
            )
        if self.trend_volatility <= 0.0:
            raise ValueError(f"trend volatility must be positive, got {self.trend_volatility}")
        if not -1.0 <= self.correlation <= 1.0:
            raise ValueError(f"correlation must lie in [-1, 1], got {self.correlation}")

    @property
    def covariance(self) -> float:
        """``rho sigma_e sigma_d``: the overlay hurdle, negative iff the correlation is."""
        return self.correlation * self.equity_volatility * self.trend_volatility

    def growth_gap(self, *, weight: float, net_premium: float, benchmark: Benchmark) -> float:
        """Annual after-cost log-growth gap of the overlay against ``benchmark``.

        ``cheap_index`` is ``w (m - rho sigma_e sigma_d) - w**2 sigma_d**2 / 2``, which is
        :func:`portfolio_edge.studies.overlay_growth.overlay_growth_gain` with the cost
        already folded into ``m``. ``leverage_matched`` subtracts what the same gross
        notional would have earned as levered equity, financed at
        ``equity_financing_spread``:

            ``gap_matched = gap_index - w (a_e - f - sigma_e**2) + w**2 sigma_e**2 / 2``

        The two differ by a term containing **no property of the trend leg except its
        weight**, which is the whole reason the funding rule can decide the sign.
        """
        indexed = (
            weight * (net_premium - self.covariance)
            - 0.5 * weight**2 * self.trend_volatility**2
        )
        if benchmark == "cheap_index":
            return indexed
        if benchmark == "leverage_matched":
            equity_leg = self.equity_excess_return - self.equity_financing_spread
            return (
                indexed
                - weight * (equity_leg - self.equity_volatility**2)
                + 0.5 * weight**2 * self.equity_volatility**2
            )
        raise ValueError(f"unknown benchmark {benchmark!r}")

    def break_even_net_premium(self, *, weight: float, benchmark: Benchmark) -> float:
        """The ``m`` at which ``growth_gap`` is exactly zero at this ``weight``.

        At ``weight = 0`` this is the marginal bar on the first unit of notional; it rises
        with weight against a cheap index and falls against a leverage-matched control,
        because the control's own variance drag grows faster than the overlay's whenever
        equity is the more volatile leg.
        """
        if weight == 0.0:
            raise ValueError("break-even at zero weight is degenerate; ask for a marginal bar")
        base = self.covariance + 0.5 * weight * self.trend_volatility**2
        if benchmark == "cheap_index":
            return base
        if benchmark == "leverage_matched":
            equity_leg = self.equity_excess_return - self.equity_financing_spread
            return (
                base
                + equity_leg
                - self.equity_volatility**2
                - 0.5 * weight * self.equity_volatility**2
            )
        raise ValueError(f"unknown benchmark {benchmark!r}")

    def best_weight(
        self, *, net_premium: float, benchmark: Benchmark, weights: Sequence[float]
    ) -> tuple[float, float]:
        """``argmax`` and ``max`` of the gap over the *offered* weight grid.

        Regret is measured against the best weight the investor could actually have
        chosen, so the grid is part of the decision problem rather than a discretisation of
        it. Against a cheap index the unconstrained optimum is far outside any grid an
        investor would consider, and reporting a corner as if it were an optimum is the
        error ``docs/research/construction-tournament.md`` finding 6 names.
        """
        if not weights:
            raise ValueError("weights must not be empty")
        gaps = [
            self.growth_gap(weight=w, net_premium=net_premium, benchmark=benchmark)
            for w in weights
        ]
        index = int(np.argmax(gaps))
        return float(weights[index]), float(gaps[index])


# --------------------------------------------------------------------------------
# 2. The prior, kept visibly separate from every measurement
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class PremiumScenario:
    """One forward view of the trend premium, with the provenance that licenses it.

    ``gross_premium`` is an arithmetic excess over cash per unit of trend notional at the
    panel's trend volatility, **before** any retail cost. ``vendor_authored`` is a required
    field rather than a note: three of the estimates in this repository come from a series
    published by a firm that sells the strategy and reconstructed on every update, and a
    prior that does not label them is hiding its weakest input.
    """

    label: str
    gross_premium: float
    prior_weight: float
    provenance: str
    vendor_authored: bool

    def __post_init__(self) -> None:
        if self.prior_weight < 0.0:
            raise ValueError(f"prior weight must be non-negative, got {self.prior_weight}")


@dataclass(frozen=True, slots=True, kw_only=True)
class PremiumPrior:
    """A weighted set of scenarios plus the cost that converts them to net units.

    The weights are a **judgement**, and the only defensible thing to do with a judgement
    is to write it down, name what it rests on, and show the answer's sensitivity to it.
    The class therefore exposes the mean, the median and the support separately, because
    the three drive different decision rules and they do not agree here.
    """

    scenarios: tuple[PremiumScenario, ...]
    cost_per_unit_notional: float

    def __post_init__(self) -> None:
        if not self.scenarios:
            raise ValueError("a prior needs at least one scenario")
        total = sum(s.prior_weight for s in self.scenarios)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"prior weights must sum to 1, got {total}")

    @property
    def net_premia(self) -> tuple[float, ...]:
        return tuple(s.gross_premium - self.cost_per_unit_notional for s in self.scenarios)

    @property
    def weights(self) -> tuple[float, ...]:
        return tuple(s.prior_weight for s in self.scenarios)

    @property
    def support(self) -> tuple[float, float]:
        """``(m_lo, m_hi)``: the endpoints minimax regret is entirely determined by.

        **Scenarios carrying zero weight are outside the support.** Setting a scenario's
        weight to zero is the operation that says "I do not believe this is possible", and
        it has to move the minimax answer or the sensitivity arm would be measuring
        nothing: minimax regret reads only the endpoints, so a reweighting that left them
        alone would leave the minimax weight alone too.
        """
        live = [
            m
            for m, w in zip(self.net_premia, self.weights, strict=True)
            if w > 0.0
        ]
        if not live:
            raise ValueError("every scenario carries zero weight; the support is empty")
        return min(live), max(live)

    @property
    def mean(self) -> float:
        return float(np.dot(self.net_premia, self.weights))

    @property
    def median(self) -> float:
        """The 50th percentile of the discrete prior, taken as the lowest ``m`` whose
        cumulative weight reaches one half."""
        order = sorted(zip(self.net_premia, self.weights, strict=True))
        cumulative = 0.0
        for value, weight in order:
            cumulative += weight
            if cumulative >= 0.5 - 1e-12:
                return value
        return order[-1][0]  # pragma: no cover - unreachable once weights sum to one

    def probability_below(self, threshold: float) -> float:
        """Prior mass strictly below ``threshold`` in net units."""
        return float(
            sum(w for m, w in zip(self.net_premia, self.weights, strict=True) if m < threshold)
        )

    def reweighted(self, weights: Sequence[float]) -> PremiumPrior:
        """The same scenarios under a different judgement, for the sensitivity arm."""
        if len(weights) != len(self.scenarios):
            raise ValueError("need one weight per scenario")
        return PremiumPrior(
            scenarios=tuple(
                PremiumScenario(
                    label=s.label,
                    gross_premium=s.gross_premium,
                    prior_weight=float(w),
                    provenance=s.provenance,
                    vendor_authored=s.vendor_authored,
                )
                for s, w in zip(self.scenarios, weights, strict=True)
            ),
            cost_per_unit_notional=self.cost_per_unit_notional,
        )


# --------------------------------------------------------------------------------
# 3. The regret surface, and what minimax regret is actually doing
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class RegretSurface:
    """Everything one benchmark decides, so that half of it cannot be quoted alone."""

    benchmark: Benchmark
    weights: tuple[float, ...]
    net_premia: tuple[float, ...]
    growth: tuple[tuple[float, ...], ...]
    regret: tuple[tuple[float, ...], ...]
    max_regret: tuple[float, ...]
    minimax_weight: float
    minimax_regret: float
    expected_growth: tuple[float, ...]
    expected_regret: tuple[float, ...]
    bayes_weight: float
    bayes_expected_regret: float
    support: tuple[float, float]

    def regret_at(self, weight: float, net_premium: float) -> float:
        """Regret at one cell, by exact lookup rather than interpolation."""
        i = self.weights.index(weight)
        j = self.net_premia.index(net_premium)
        return self.regret[i][j]


def regret_from_gaps(
    growth: Sequence[Sequence[float]],
    *,
    weights: Sequence[float],
    prior: PremiumPrior,
    benchmark: Benchmark,
) -> RegretSurface:
    """Assemble a surface from an arbitrary ``weight x scenario`` matrix of gaps.

    The closed-form surface and the simulated, capitulation-adjusted one go through this
    one function so that "minimax" and "Bayes" mean exactly the same operation in both, and
    a difference between the two sections can only be a difference in the growth model.
    The matrix must be indexed by the **prior's own scenarios in order**, since that is
    where the weights come from.
    """
    action = tuple(float(w) for w in weights)
    grid = prior.net_premia
    if len(growth) != len(action):
        raise ValueError("need one row of gaps per weight")
    if any(len(row) != len(grid) for row in growth):
        raise ValueError("need one column of gaps per prior scenario")

    matrix = tuple(tuple(float(value) for value in row) for row in growth)
    best = tuple(max(matrix[i][j] for i in range(len(action))) for j in range(len(grid)))
    regret = tuple(tuple(best[j] - row[j] for j in range(len(grid))) for row in matrix)

    lo, hi = prior.support
    endpoints = tuple(j for j, m in enumerate(grid) if m in (lo, hi))
    max_regret = tuple(max(row[j] for j in endpoints) for row in regret)
    minimax_index = int(np.argmin(max_regret))

    expected_regret = tuple(float(np.dot(row, prior.weights)) for row in regret)
    expected_growth = tuple(float(np.dot(row, prior.weights)) for row in matrix)
    bayes_index = int(np.argmin(expected_regret))

    return RegretSurface(
        benchmark=benchmark,
        weights=action,
        net_premia=grid,
        growth=matrix,
        regret=regret,
        max_regret=max_regret,
        minimax_weight=action[minimax_index],
        minimax_regret=max_regret[minimax_index],
        expected_growth=expected_growth,
        expected_regret=expected_regret,
        bayes_weight=action[bayes_index],
        bayes_expected_regret=expected_regret[bayes_index],
        support=(lo, hi),
    )


def regret_surface(
    model: OverlayGrowthModel,
    *,
    weights: Sequence[float],
    prior: PremiumPrior,
    benchmark: Benchmark,
) -> RegretSurface:
    """Growth, regret, the minimax weight and the Bayes weight on one benchmark.

    Max regret is evaluated at the prior's support because regret is convex in ``m`` at
    fixed ``w`` — a maximum of linear functions less a linear function — so its maximum
    over the interval is attained at an endpoint and a denser grid cannot find a larger
    value. Expected regret is evaluated at the prior's own scenarios and weights, because
    that is where the judgement lives.
    """
    if not weights:
        raise ValueError("weights must not be empty")
    growth = [
        [model.growth_gap(weight=w, net_premium=m, benchmark=benchmark) for m in prior.net_premia]
        for w in weights
    ]
    return regret_from_gaps(growth, weights=weights, prior=prior, benchmark=benchmark)


def robust_range(surface: RegretSurface, *, tolerance: float) -> tuple[float, float]:
    """The weights whose max regret is within ``tolerance`` of the minimax weight's.

    The decision-useful output is not the argmin — a surface this flat does not support
    one — but the interval over which the choice barely matters. Read it against the size
    of the whole prize: when the best available weight is worth tens of basis points a
    year, a tolerance of ten is most of the decision.
    """
    if tolerance < 0.0:
        raise ValueError(f"tolerance must be non-negative, got {tolerance}")
    ceiling = surface.minimax_regret + tolerance
    inside = [w for w, r in zip(surface.weights, surface.max_regret, strict=True) if r <= ceiling]
    return min(inside), max(inside)


def minimax_regret_weight(
    model: OverlayGrowthModel,
    *,
    weights: Sequence[float],
    support: tuple[float, float],
    benchmark: Benchmark,
) -> float:
    """The minimax-regret weight in closed form: the slope of the value function.

    Let ``G*(m) = max_w G(w, m)``. Regret is convex in ``m``, so max regret sits at an
    endpoint of ``[m_lo, m_hi]``; equating the two endpoints gives

        ``w = [G*(m_hi) - G*(m_lo)] / (m_hi - m_lo)``

    and the envelope theorem makes ``dG*/dm = w*(m)``, so that ratio is the **mean of the
    optimal weight over the support**. Two consequences the surface itself hides:

    * the interior shape of the prior does not enter at all — minimax regret imposes a
      uniform prior on the stated range and inherits every error in the endpoints;
    * when the value function is bang-bang, as it is against a leverage-matched control
      whose gap is convex in ``w``, this equals the grid ceiling times the fraction of the
      range in which the overlay wins. **The rule is then a probability statement wearing a
      decision-theory costume.**

    The returned value is continuous and is *not* snapped to the grid; the grid-restricted
    answer is :attr:`RegretSurface.minimax_weight`, and the two agree to the grid spacing.
    """
    lo, hi = support
    if hi <= lo:
        raise ValueError(f"support must be non-degenerate, got {support}")
    top = model.best_weight(net_premium=hi, benchmark=benchmark, weights=weights)[1]
    bottom = model.best_weight(net_premium=lo, benchmark=benchmark, weights=weights)[1]
    return (top - bottom) / (hi - lo)


# --------------------------------------------------------------------------------
# 4. The asymmetry, arm one: the investor's own capitulation, priced inside the path
# --------------------------------------------------------------------------------


def restate_annual_mean(
    series: FloatArray, *, annual_mean: float, periods_per_year: int = MONTHS_PER_YEAR
) -> FloatArray:
    """Shift a series to a stated annual mean, leaving every other moment untouched.

    The same operation ``_notional_budget_tables`` uses, duplicated here only because a
    private helper in a reporting module is not an interface. A level shift changes the one
    moment that is a forecast and none of the moments the sample can estimate, which is
    what makes "what if the premium is lower" answerable at all.
    """
    values = np.asarray(series, dtype=np.float64)
    return np.asarray(
        values - float(np.mean(values)) + annual_mean / periods_per_year, dtype=np.float64
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class AbandonmentOutcome:
    """What a stated capitulation rule costs at one weight and one premium."""

    weight: float
    net_premium: float
    relative_drawdown_trigger: float
    horizon_years: float
    resamples: int
    probability_abandoned: float
    median_months_to_abandonment: float
    gap_if_held: float
    gap_with_abandonment: float
    probability_underperform_if_held: float
    probability_underperform_with_abandonment: float

    @property
    def capitulation_cost(self) -> float:
        """``gap_if_held - gap_with_abandonment``, in annual log-growth points."""
        return self.gap_if_held - self.gap_with_abandonment


def abandonment_adjusted_gap(
    candidate_total: FloatArray,
    control_total: FloatArray,
    *,
    weight: float,
    net_premium: float,
    trigger: float,
    horizon_years: float,
    resamples: int,
    block_length: int,
    rng: np.random.Generator,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> AbandonmentOutcome:
    """Growth against a control when the investor sells the sleeve after a bad stretch.

    Both arms are resampled **jointly** — one set of block indices applied to both — so a
    draw is one investor's two portfolios on one history. On each path the relative wealth
    ``W_candidate / W_control`` is tracked against its own running peak; the first month
    that ratio sits ``trigger`` below its peak, the investor switches to the control and
    stays there, which freezes relative wealth at its trough for the rest of the horizon.

    **The trigger is an input, not an estimate**, and it should be read against the sibling
    page's measured worst relative run rather than tuned. Nothing in this repository
    estimates a real investor's capitulation threshold, and inventing one inside an
    optimiser would be the failure this design exists to expose.
    """
    if trigger >= 0.0:
        raise ValueError(f"trigger must be a negative relative drawdown, got {trigger}")
    candidate = np.asarray(candidate_total, dtype=np.float64)
    control = np.asarray(control_total, dtype=np.float64)
    if candidate.shape != control.shape or candidate.ndim != 1:
        raise ValueError("candidate and control must be one-dimensional and the same length")
    if block_length < 1 or resamples < 1:
        raise ValueError("block_length and resamples must both be at least one")

    horizon = round(horizon_years * periods_per_year)
    if horizon < 1:
        raise ValueError(f"horizon_years must cover a month, got {horizon_years}")

    n = candidate.size
    blocks = math.ceil(horizon / block_length)
    starts = rng.integers(0, n, size=(resamples, blocks))
    offsets = np.arange(block_length, dtype=np.intp)
    drawn = (starts[:, :, None] + offsets[None, None, :]) % n
    indices = drawn.reshape(resamples, -1)[:, :horizon]

    relative_step = (1.0 + candidate[indices]) / (1.0 + control[indices])
    relative = np.cumprod(relative_step, axis=1)
    peak = np.maximum.accumulate(relative, axis=1)
    breached = relative / peak - 1.0 <= trigger

    any_breach = breached.any(axis=1)
    first = np.where(any_breach, breached.argmax(axis=1), horizon - 1)
    frozen = relative[np.arange(resamples), first]
    held = relative[:, -1]
    with_abandonment = np.where(any_breach, frozen, held)

    years = horizon / periods_per_year
    return AbandonmentOutcome(
        weight=weight,
        net_premium=net_premium,
        relative_drawdown_trigger=trigger,
        horizon_years=years,
        resamples=resamples,
        probability_abandoned=float(np.mean(any_breach)),
        median_months_to_abandonment=(
            float(np.median(first[any_breach]) + 1) if any_breach.any() else float("nan")
        ),
        gap_if_held=float(np.mean(np.log(held))) / years,
        gap_with_abandonment=float(np.mean(np.log(with_abandonment))) / years,
        probability_underperform_if_held=float(np.mean(held < 1.0)),
        probability_underperform_with_abandonment=float(np.mean(with_abandonment < 1.0)),
    )


# --------------------------------------------------------------------------------
# 5. The asymmetry, arm two: the episode the sleeve exists for
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class DecadeGap:
    """The overlay's contribution conditioned on the equity decade, not averaged over it."""

    net_premium: float
    weight: float
    windows: int
    horizon_months: int
    worst_window: tuple[str, str]
    worst_equity_growth: float
    worst_candidate_growth: float
    decile_threshold: float
    mean_gap_in_worst_decile: float
    mean_gap_elsewhere: float
    worst_candidate_drawdown: float
    worst_control_drawdown: float


def conditional_decade_gaps(
    periods: Sequence[str],
    candidate_total: FloatArray,
    control_total: FloatArray,
    *,
    weight: float,
    net_premium: float,
    horizon_months: int = 120,
) -> DecadeGap:
    """Every overlapping decade, split on how the *equity* decade went.

    An unconditional mean answers "what did the overlay add", which is not the question a
    diversifier is bought to answer. This conditions on the control's own outcome and
    reports the two conditional means separately. The windows overlap heavily, so these are
    **not** independent observations, no interval is offered for their difference, and the
    number of genuinely distinct decades in the panel is roughly ``len(periods) / 120``.
    """
    candidate = np.asarray(candidate_total, dtype=np.float64)
    control = np.asarray(control_total, dtype=np.float64)
    if candidate.shape != control.shape or candidate.ndim != 1:
        raise ValueError("candidate and control must be one-dimensional and the same length")
    if len(periods) != candidate.size:
        raise ValueError("periods must line up with the return series")
    if candidate.size < horizon_months:
        raise ValueError(f"need at least {horizon_months} months, got {candidate.size}")

    years = horizon_months / MONTHS_PER_YEAR
    starts = range(candidate.size - horizon_months + 1)
    control_growth = np.array(
        [float(np.sum(np.log1p(control[s : s + horizon_months]))) / years for s in starts]
    )
    candidate_growth = np.array(
        [float(np.sum(np.log1p(candidate[s : s + horizon_months]))) / years for s in starts]
    )
    gaps = candidate_growth - control_growth

    worst = int(np.argmin(control_growth))
    threshold = float(np.quantile(control_growth, 0.10))
    bad = control_growth <= threshold

    return DecadeGap(
        net_premium=net_premium,
        weight=weight,
        windows=len(control_growth),
        horizon_months=horizon_months,
        worst_window=(periods[worst], periods[worst + horizon_months - 1]),
        worst_equity_growth=float(control_growth[worst]),
        worst_candidate_growth=float(candidate_growth[worst]),
        decile_threshold=threshold,
        mean_gap_in_worst_decile=float(np.mean(gaps[bad])),
        mean_gap_elsewhere=float(np.mean(gaps[~bad])),
        worst_candidate_drawdown=drawdown_summary(
            np.cumprod(1.0 + candidate[worst : worst + horizon_months])
        ).max_drawdown,
        worst_control_drawdown=drawdown_summary(
            np.cumprod(1.0 + control[worst : worst + horizon_months])
        ).max_drawdown,
    )


# --------------------------------------------------------------------------------
# 6. Resolution: a verdict may not outrun its instrument
# --------------------------------------------------------------------------------


def years_to_resolve(*, gap: float, minimum_detectable_effect: float, window_years: float) -> float:
    """How long the arm must be held before the detection floor falls to ``gap``.

    The floor shrinks as ``1/sqrt(T)``, so the required span is
    ``window_years * (mde / gap)**2``. Returns infinity for a gap of zero, which is the
    honest answer and the one ``docs/decisions/0010-bars-carry-a-reopening-condition.md``
    asks for: a design that cannot see the effect returns ``unresolved``, not ``absent``.
    """
    if window_years <= 0.0:
        raise ValueError(f"window_years must be positive, got {window_years}")
    if minimum_detectable_effect < 0.0:
        raise ValueError("minimum detectable effect must be non-negative")
    if gap == 0.0:
        return math.inf
    return window_years * (minimum_detectable_effect / abs(gap)) ** 2


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._trend_weight_regret_tables import main

    main()
