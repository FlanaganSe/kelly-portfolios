"""What is arithmetic about the equity/bond split, and what is not.

The repository's declared objective is net geometric growth subject to a drawdown
constraint, recorded as a preference justified by Breiman rather than as a proof
(``docs/research/expected-edge-decomposition.md`` §1.3). That objective has no risk
aversion parameter in it. Taken literally it does not produce a 60/40 portfolio, and
this module exists to show exactly where the bond allocation has to come from
instead.

Five separable pieces, in the order the companion page uses them.

**1. The growth parabola, written about its vertex.** From
:func:`portfolio_edge.core.kelly.growth_rate_vertex`,
``g(L) = r + 0.5 sigma**2 [(L*)**2 - (L - L*)**2]``. Divide the excess of ``g`` over
``r`` by its peak and every parameter cancels:

    growth retained at ``L = f L*``  =  ``1 - (1 - f)**2``   of the peak excess.

That single expression is the whole cost-of-being-wrong result, it holds for any
``mu``, ``sigma`` and ``r``, and it is why the question is more forgiving than it
looks. Half the growth-optimal exposure keeps 75% of the excess growth; twice it
keeps none. The parabola is symmetric in ``L``, so the asymmetry is *multiplicative*:
``f = 1/2`` and ``f = 2`` are both a factor of two away from the optimum and cost
0.25 and 1.00 of the peak respectively.

**2. The fully invested two-asset optimum.** With no leverage and no shorting, the
weight maximising the growth rate of a continuously rebalanced equity/bond mix is

    ``w* = (mu_e - mu_b + sigma_b**2 - rho sigma_e sigma_b)
           / (sigma_e**2 + sigma_b**2 - 2 rho sigma_e sigma_b)``,

clipped to ``[0, 1]``. Both the numerator's first term and every second moment are
forecasts. :func:`break_even_excess_return` inverts it, which is the more honest
direction to read it in: rather than assert a premium and derive a weight, state the
premium your chosen weight is implicitly asserting.

**3. What estimating the inputs costs.** Take ``sigma`` known and
``muhat ~ N(mu, sigma**2 / T)`` over ``T`` years. Then
``Lhat* = (muhat - r) / sigma**2`` is *unbiased* for ``L*`` with
``SE(Lhat*) = 1 / (sigma sqrt(T))``, and because ``g`` is quadratic,

    ``E[g(Lhat*)] = g(L*) - 0.5 sigma**2 Var(Lhat*) = g(L*) - 1 / (2 T)``.

The cost of not knowing the mean is ``1 / (2 T)`` per year, free of ``mu``, ``sigma``
and ``r``. Shrinking the plug-in by ``f`` and minimising the same expected shortfall
gives the shrinkage that trades bias against variance exactly:

    ``f* = S**2 T / (S**2 T + 1)``,  ``S`` the Sharpe ratio.

This is the estimation-error case for fractional Kelly, stated as arithmetic. Note
what it does *not* say: the plug-in is not biased upward by the mean's sampling
error. Estimating ``sigma`` as well does bias it upward, by
``(n - 1) / (n - 3)`` (:func:`inverse_variance_bias_factor`), which is 0.27% on 750
monthly observations — a rounding error next to the variance term. Anyone arguing for
half Kelly from bias is arguing from the small term.

**4. Sequence risk is a cash-flow interaction.** Without external flows terminal
wealth is ``W0 prod(1 + r_t)``, which is invariant to permutation. With flows it is
not, and an accumulator and a decumulator face the same dependence with opposite
sign. :func:`permuted_terminal_wealth` measures both on a supplied return record.

**5. The drawdown ladder.** :func:`constant_mix_ladder` is the operational form of the
answer: the depth and duration a reader would have had to sit through at each equity
share on a supplied history. Nothing in it is a forecast; everything in it is one
sample.

Sections 1 to 3 are arithmetic and hold exactly. Sections 4 and 5 are measurements on
whatever record the caller supplies, and inherit that record's limitations. The module
loads no data; the ``__main__`` block does, and only to regenerate the published
tables.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from portfolio_edge.core._types import FloatArray, FloatVector, as_float_array
from portfolio_edge.core.drawdown import drawdown_summary
from portfolio_edge.core.wealth import equity_curve

__all__ = [
    "ConstantMixSummary",
    "LeverageWipeoutError",
    "LeveredRung",
    "PermutedWealth",
    "break_even_excess_return",
    "constant_mix_ladder",
    "constant_mix_returns",
    "fully_invested_growth_optimal_weight",
    "growth_retained_fraction",
    "growth_shortfall",
    "implied_effective_years",
    "inverse_variance_bias_factor",
    "kelly_estimator_standard_error",
    "levered_ladder",
    "levered_mix_returns",
    "optimal_kelly_shrinkage",
    "permuted_terminal_wealth",
    "plug_in_growth_cost",
    "terminal_wealth_with_level_flow",
]

MONTHS_PER_YEAR = 12


# --------------------------------------------------------------------------------
# 1. The cost of being at the wrong fraction of the growth-optimal exposure
# --------------------------------------------------------------------------------


def growth_retained_fraction(kelly_fraction: float) -> float:
    """``1 - (1 - f)**2``: share of the peak *excess* growth rate kept at ``f L*``.

    Parameter-free. ``f = 1`` returns 1, ``f = 0`` returns 0, ``f = 2`` returns 0
    (growth falls back to the risk-free rate), and ``f > 2`` returns a negative
    number, meaning the position earns less than cash in growth terms. This is the
    ratio form of :func:`portfolio_edge.core.kelly.growth_rate_vertex`, so it is the
    same statement as that module's ``g(0) = g(2 L*) = r``.
    """
    return 1.0 - (1.0 - kelly_fraction) ** 2


def growth_shortfall(
    kelly_fraction: float, *, excess_return: float, volatility: float
) -> float:
    """Growth rate given up per year at ``f L*``, in the same units as the inputs.

    ``0.5 sigma**2 (L*)**2 (1 - f)**2``, i.e.
    :func:`growth_retained_fraction`'s complement times the peak excess growth
    ``(mu - r)**2 / (2 sigma**2)``.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    peak_excess = excess_return**2 / (2.0 * volatility**2)
    return peak_excess * (1.0 - kelly_fraction) ** 2


# --------------------------------------------------------------------------------
# 2. The fully invested, long-only, two-asset optimum
# --------------------------------------------------------------------------------


def _mix_variance_denominator(
    equity_volatility: float, bond_volatility: float, correlation: float
) -> float:
    denominator = (
        equity_volatility**2
        + bond_volatility**2
        - 2.0 * correlation * equity_volatility * bond_volatility
    )
    if denominator <= 0.0:
        raise ValueError(
            "the two assets are perfectly co-moving in these inputs "
            f"(tracking variance {denominator!r}); no interior optimum exists"
        )
    return denominator


def fully_invested_growth_optimal_weight(
    *,
    excess_return_over_bond: float,
    equity_volatility: float,
    bond_volatility: float,
    correlation: float,
    clip: bool = True,
) -> float:
    """Equity weight maximising the growth rate of a fully invested two-asset mix.

    ``excess_return_over_bond`` is the *arithmetic* drift of equity less that of the
    bond asset. With ``clip`` the result is confined to ``[0, 1]``, which is the
    constraint ``docs/decisions/0004-no-sleeve-promoted.md``
    imposes: leverage is zero and shorting is not permitted. Pass ``clip=False`` to
    see the unconstrained number, which is the one that says whether the constraint
    binds.
    """
    if equity_volatility <= 0.0 or bond_volatility <= 0.0:
        raise ValueError("both volatilities must be positive")
    if not -1.0 <= correlation <= 1.0:
        raise ValueError(f"correlation must lie in [-1, 1], got {correlation}")
    denominator = _mix_variance_denominator(
        equity_volatility, bond_volatility, correlation
    )
    numerator = (
        excess_return_over_bond
        + bond_volatility**2
        - correlation * equity_volatility * bond_volatility
    )
    weight = numerator / denominator
    return min(max(weight, 0.0), 1.0) if clip else weight


def break_even_excess_return(
    *,
    weight: float,
    equity_volatility: float,
    bond_volatility: float,
    correlation: float,
) -> float:
    """The equity-over-bond arithmetic premium at which ``weight`` is growth-optimal.

    The inverse of :func:`fully_invested_growth_optimal_weight`. Read a chosen equity
    share through this and it becomes a forecast the reader is making, whether or not
    they meant to make one.
    """
    denominator = _mix_variance_denominator(
        equity_volatility, bond_volatility, correlation
    )
    return (
        weight * denominator
        - bond_volatility**2
        + correlation * equity_volatility * bond_volatility
    )


# --------------------------------------------------------------------------------
# 3. What estimating the inputs costs, and the shrinkage that answers it
# --------------------------------------------------------------------------------


def kelly_estimator_standard_error(*, volatility: float, years: float) -> float:
    """``SE(Lhat*) = 1 / (sigma sqrt(T))`` with ``sigma`` known.

    Reproduces the figure in :mod:`portfolio_edge.core.kelly`'s docstring: at
    ``sigma = 18%`` over 20 years this is 1.24 exposure units.
    """
    if volatility <= 0.0:
        raise ValueError(f"volatility must be positive, got {volatility}")
    if years <= 0.0:
        raise ValueError(f"years must be positive, got {years}")
    return 1.0 / (volatility * math.sqrt(years))


def plug_in_growth_cost(years: float) -> float:
    """``1 / (2 T)``: expected annual growth given up by using the plug-in optimum.

    Exact for a known ``sigma`` and a Gaussian mean estimated over ``T`` years, and
    free of ``mu``, ``sigma`` and ``r``, because the growth loss is quadratic in the
    exposure error and the exposure error's variance is ``1 / (T sigma**2)``.
    """
    if years <= 0.0:
        raise ValueError(f"years must be positive, got {years}")
    return 1.0 / (2.0 * years)


def optimal_kelly_shrinkage(*, sharpe_ratio: float, years: float) -> float:
    """``f* = S**2 T / (S**2 T + 1)``, the growth-maximising shrinkage of the plug-in.

    Minimises ``E[g(f Lhat*)]``'s shortfall by trading the squared bias ``(1 - f)**2
    L*^2`` against the variance ``f**2 Var(Lhat*)``. It depends on the data only
    through ``S**2 T``, the squared Sharpe ratio times the sample length in years —
    which is the sample's information content about the mean, and nothing else.

    The caller must supply the ``T`` they believe, not the ``T`` on the calendar. The
    two differ by however much non-stationarity they think the record contains, and
    that difference, not sampling noise, is what a half-Kelly rule is really asserting
    (see :func:`implied_effective_years`).
    """
    if years <= 0.0:
        raise ValueError(f"years must be positive, got {years}")
    information = sharpe_ratio**2 * years
    return information / (information + 1.0)


def implied_effective_years(*, sharpe_ratio: float, shrinkage: float) -> float:
    """Years of stationary data a chosen ``shrinkage`` is implicitly claiming to have.

    The inverse of :func:`optimal_kelly_shrinkage`: ``T = f / ((1 - f) S**2)``. At
    ``f = 0.5`` it is ``1 / S**2``. Half Kelly on an asset with a 0.40 Sharpe ratio is
    the statement that the whole record is worth 6.25 years.
    """
    if sharpe_ratio == 0.0:
        raise ValueError("sharpe_ratio must be non-zero")
    if not 0.0 <= shrinkage < 1.0:
        raise ValueError(f"shrinkage must lie in [0, 1), got {shrinkage}")
    return shrinkage / ((1.0 - shrinkage) * sharpe_ratio**2)


def inverse_variance_bias_factor(observations: int) -> float:
    """``E[1 / sigmahat**2] / (1 / sigma**2) = (n - 1) / (n - 3)`` for Gaussian data.

    The *only* upward bias in a plug-in Kelly fraction, and it is tiny in any sample
    long enough to be worth using. Quoted so that the argument for fractional Kelly
    is made from the variance term, which is large, rather than from the bias term,
    which is not.
    """
    if observations <= 3:
        raise ValueError(f"need more than 3 observations, got {observations}")
    return (observations - 1.0) / (observations - 3.0)


# --------------------------------------------------------------------------------
# 4. Sequence risk: permutation invariance, and what breaks it
# --------------------------------------------------------------------------------


def terminal_wealth_with_level_flow(
    returns: FloatVector,
    *,
    initial_wealth: float,
    flow_per_period: float,
) -> float:
    """Terminal wealth under a level per-period flow applied before each return.

    ``flow_per_period`` is signed: positive contributes, negative withdraws. Ruin
    returns ``0.0`` rather than raising, which is the difference between this and
    :func:`portfolio_edge.core.wealth.equity_curve_with_cash_flows` — there, running
    out of money is an input error; here it is the measurement.
    """
    array = as_float_array(returns, name="returns")
    if initial_wealth <= 0.0:
        raise ValueError(f"initial_wealth must be positive, got {initial_wealth}")
    wealth = initial_wealth
    for period_return in array:
        wealth += flow_per_period
        if wealth <= 0.0:
            return 0.0
        wealth *= 1.0 + float(period_return)
        if wealth <= 0.0:
            return 0.0
    return wealth


@dataclass(frozen=True)
class PermutedWealth:
    """Terminal wealth across random permutations of one return record."""

    draws: int
    periods: int
    minimum: float
    percentile_5: float
    median: float
    percentile_95: float
    maximum: float
    ruin_probability: float
    early_return_correlation: float
    """Correlation between the compounded return of the first ``early_periods`` and
    terminal wealth. Zero without flows, negative while contributing, positive while
    withdrawing."""

    @property
    def spread_ratio(self) -> float:
        """95th percentile over 5th. ``1.0`` means ordering did not matter."""
        if self.percentile_5 <= 0.0:
            return math.inf
        return self.percentile_95 / self.percentile_5


def permuted_terminal_wealth(
    returns: FloatVector,
    *,
    initial_wealth: float,
    flow_per_period: float,
    periods: int,
    draws: int,
    seed: int,
    early_periods: int,
) -> PermutedWealth:
    """Terminal wealth over ``draws`` random permutations of ``returns``.

    Permuting is the right null for this question and the wrong model of markets: it
    holds the multiset of returns fixed, so any dispersion in the result is caused by
    ordering *alone*, but it also destroys serial dependence, so it neither confirms
    nor denies mean reversion. Each draw takes the first ``periods`` entries of a
    fresh permutation, so ``periods`` may be shorter than the record.
    """
    array = as_float_array(returns, name="returns")
    if periods <= 0 or periods > array.size:
        raise ValueError(
            f"periods must lie in [1, {array.size}], got {periods}"
        )
    if draws <= 0:
        raise ValueError(f"draws must be positive, got {draws}")
    if not 0 < early_periods <= periods:
        raise ValueError(f"early_periods must lie in [1, {periods}], got {early_periods}")

    generator = np.random.default_rng(seed)
    terminal = np.empty(draws, dtype=np.float64)
    early = np.empty(draws, dtype=np.float64)
    for index in range(draws):
        path = generator.permutation(array)[:periods]
        terminal[index] = terminal_wealth_with_level_flow(
            path, initial_wealth=initial_wealth, flow_per_period=flow_per_period
        )
        early[index] = float(np.prod(1.0 + path[:early_periods]))
    # Without flows the terminal wealth is the same number in every draw, up to the
    # order in which floating-point multiplications happen. Correlating that residue
    # against anything measures the rounding, so it is reported as the zero it is.
    scale = float(np.mean(np.abs(terminal)))
    dispersion = float(np.std(terminal)) / scale if scale > 0.0 else 0.0
    correlation = (
        0.0 if dispersion < 1e-12 else float(np.corrcoef(early, terminal)[0, 1])
    )
    return PermutedWealth(
        draws=draws,
        periods=periods,
        minimum=float(terminal.min()),
        percentile_5=float(np.percentile(terminal, 5)),
        median=float(np.median(terminal)),
        percentile_95=float(np.percentile(terminal, 95)),
        maximum=float(terminal.max()),
        ruin_probability=float((terminal <= 0.0).mean()),
        early_return_correlation=correlation,
    )


# --------------------------------------------------------------------------------
# 5. The drawdown ladder
# --------------------------------------------------------------------------------


def constant_mix_returns(
    equity_returns: FloatVector, safe_returns: FloatVector, weight: float
) -> FloatArray:
    """``w * equity + (1 - w) * safe``, period by period.

    This is a constant mix rebalanced every period, which is what makes it the right
    object here: the weight is the policy, so the portfolio must actually hold it.
    Buy-and-hold answers a different question and
    ``docs/research/rebalancing-policy.md`` already priced the
    difference at under 1.2 bp/yr in cost and nothing in return.
    """
    equity = as_float_array(equity_returns, name="equity_returns")
    safe = as_float_array(safe_returns, name="safe_returns")
    if equity.shape != safe.shape:
        raise ValueError(
            f"equity_returns and safe_returns must be the same length; "
            f"got {equity.size} and {safe.size}"
        )
    if not 0.0 <= weight <= 1.0:
        raise ValueError(f"weight must lie in [0, 1], got {weight}")
    return np.asarray(weight * equity + (1.0 - weight) * safe, dtype=np.float64)


@dataclass(frozen=True)
class ConstantMixSummary:
    """One rung of the ladder: what the reader would have lived through."""

    weight: float
    observations: int
    geometric_return: float
    volatility: float
    max_drawdown: float
    max_time_under_water: int


def constant_mix_ladder(
    equity_returns: FloatVector,
    safe_returns: FloatVector,
    weights: FloatVector,
    *,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> tuple[ConstantMixSummary, ...]:
    """Geometric return, volatility, maximum drawdown and time under water by weight.

    Maximum drawdown deepens mechanically with sample length, so every rung must be
    computed on the same window — which it is, by construction, since all rungs share
    one pair of series. Comparing a rung here against a drawdown from a different
    window is the error :mod:`portfolio_edge.core.drawdown` warns about.
    """
    equity = as_float_array(equity_returns, name="equity_returns")
    grid = as_float_array(weights, name="weights")
    if periods_per_year <= 0:
        raise ValueError(f"periods_per_year must be positive, got {periods_per_year}")
    rungs = []
    for weight in grid:
        mixed = constant_mix_returns(equity, safe_returns, float(weight))
        summary = drawdown_summary(equity_curve(mixed))
        growth = float(np.prod(1.0 + mixed)) ** (periods_per_year / mixed.size) - 1.0
        rungs.append(
            ConstantMixSummary(
                weight=float(weight),
                observations=int(mixed.size),
                geometric_return=growth,
                volatility=float(np.std(mixed, ddof=1)) * math.sqrt(periods_per_year),
                max_drawdown=summary.max_drawdown,
                max_time_under_water=summary.max_time_under_water,
            )
        )
    return tuple(rungs)


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._equity_share_tables import main

    main()


# --------------------------------------------------------------------------------
# 8. The ladder continued past 1.0, which the zero-leverage rule stops it reaching
# --------------------------------------------------------------------------------
#
# `constant_mix_ladder` clips its weight to [0, 1] by construction, so it cannot see
# the exposure the growth objective actually points at. Section 1 records that under
# the zero-leverage rule the objective returns a corner solution at 100% equity, and
# `docs/decisions/0004-no-sleeve-promoted.md` records that the rule itself is what
# makes the corner. These two functions continue the same ladder past the corner on
# realised returns, so the question can be answered with a measurement rather than
# with the lognormal model that produced `L*`.
#
# Nothing here recommends leverage. The model's `L*` is computed from a Gaussian with
# constant parameters; realised equity has fat tails, volatility clustering and a
# financing rate that rises exactly when it hurts, all of which move the realised
# optimum down and none of which the closed form contains. Measuring how far down is
# the point.


class LeverageWipeoutError(ValueError):
    """A period return at or below -100%: the levered position was wiped out.

    Raised rather than clamped. A wealth path that touches zero has no geometric
    return, and silently flooring it at zero would report a number for a portfolio
    that stopped existing. The message carries the period index so the caller can
    name the month.
    """


def levered_mix_returns(
    equity_returns: FloatVector,
    financing_returns: FloatVector,
    leverage: float,
    *,
    borrow_spread_per_period: float = 0.0,
) -> FloatArray:
    """``L r_e - (L - 1)(r_f + s)``: constant leverage, rebalanced every period.

    The exposure is the policy, so the portfolio must actually hold it, exactly as in
    :func:`constant_mix_returns`. Below ``L = 1`` the borrowed portion is negative and
    the spread is not charged — lending and borrowing are not the same rate, and
    :func:`portfolio_edge.core.kelly.kinked_growth_rate` is the model form of the same
    kink.

    Raises :class:`LeverageWipeoutError` if any period return reaches -100%.
    """
    equity = as_float_array(equity_returns, name="equity_returns")
    financing = as_float_array(financing_returns, name="financing_returns")
    if equity.shape != financing.shape:
        raise ValueError(
            "equity_returns and financing_returns must be the same length; "
            f"got {equity.size} and {financing.size}"
        )
    if leverage < 0.0:
        raise ValueError(f"leverage cannot be negative, got {leverage}")
    if borrow_spread_per_period < 0.0:
        raise ValueError(
            f"borrow_spread_per_period cannot be negative, got {borrow_spread_per_period}"
        )
    borrowed = max(leverage - 1.0, 0.0)
    returns = (
        leverage * equity
        - (leverage - 1.0) * financing
        - borrowed * borrow_spread_per_period
    )
    wiped = np.flatnonzero(returns <= -1.0)
    if wiped.size:
        raise LeverageWipeoutError(
            f"leverage {leverage} is wiped out at period index {int(wiped[0])}, "
            f"where the position return is {float(returns[wiped[0]]):.4f}"
        )
    return np.asarray(returns, dtype=np.float64)


@dataclass(frozen=True)
class LeveredRung:
    """One rung of the levered ladder, or the leverage at which it stopped existing."""

    leverage: float
    observations: int
    geometric_return: float
    volatility: float
    max_drawdown: float
    max_time_under_water: int
    wiped_out: bool


def levered_ladder(
    equity_returns: FloatVector,
    financing_returns: FloatVector,
    leverages: FloatVector,
    *,
    borrow_spread_per_period: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> tuple[LeveredRung, ...]:
    """:func:`constant_mix_ladder`'s shape, for exposures that may exceed 1.

    A wiped-out rung is returned with ``wiped_out=True`` and every statistic at
    ``nan`` rather than omitted, because the leverage at which a real series destroys
    a monthly-rebalanced investor is the most decision-relevant number on the ladder
    and dropping the row would hide it.
    """
    equity = as_float_array(equity_returns, name="equity_returns")
    grid = as_float_array(leverages, name="leverages")
    if periods_per_year <= 0:
        raise ValueError(f"periods_per_year must be positive, got {periods_per_year}")
    rungs = []
    for leverage in grid:
        try:
            levered = levered_mix_returns(
                equity,
                financing_returns,
                float(leverage),
                borrow_spread_per_period=borrow_spread_per_period,
            )
        except LeverageWipeoutError:
            rungs.append(
                LeveredRung(
                    leverage=float(leverage),
                    observations=int(equity.size),
                    geometric_return=math.nan,
                    volatility=math.nan,
                    max_drawdown=math.nan,
                    max_time_under_water=-1,
                    wiped_out=True,
                )
            )
            continue
        summary = drawdown_summary(equity_curve(levered))
        growth = float(np.prod(1.0 + levered)) ** (
            periods_per_year / levered.size
        ) - 1.0
        rungs.append(
            LeveredRung(
                leverage=float(leverage),
                observations=int(levered.size),
                geometric_return=growth,
                volatility=float(np.std(levered, ddof=1))
                * math.sqrt(periods_per_year),
                max_drawdown=summary.max_drawdown,
                max_time_under_water=summary.max_time_under_water,
                wiped_out=False,
            )
        )
    return tuple(rungs)
