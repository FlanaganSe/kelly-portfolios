"""Settling whether expected log wealth is "an arbitrary nonlinear transformation".

Chambers and Zdanowicz (2014), "The Limitations of Diversification Return", show that
a long-rebalanced / short-buy-and-hold position has exactly zero expected profit under
their assumptions, and dismiss the fact that the rebalanced portfolio has higher
expected *log* wealth as "an arbitrary nonlinear transformation of wealth". Open
question 2 of ``docs/research/portfolio-edge-research-framework.md`` asks this
repository to settle that. This module is the arithmetic half of the answer.

Three results are computed here, and the third is the one that decides it.

**1. Their theorem generalises, and is correct.** For assets whose simple returns are
independent across time with identical means ``mu``, expected terminal wealth is
``(1 + mu)**T`` for *both* the constant-weight rebalanced portfolio and buy-and-hold:

    E[W_reb] = prod_t E[1 + w'R_t] = (1 + w'mu)**T
    E[W_hold] = sum_i w_i prod_t E[1 + r_{i,t}] = sum_i w_i (1 + mu_i)**T

These coincide exactly when all ``mu_i`` are equal, and by the strict convexity of
``x -> (1 + x)**T`` for ``T > 1`` the buy-and-hold portfolio is strictly *ahead* on
expected terminal wealth whenever the means differ. So the zero-expected-profit result
is not a knife-edge artefact of their binomial lattice; it is the equal-mean case of a
general identity, and off that case the sign favours buy-and-hold. Their conclusion —
that a positive variance decomposition is not evidence of profit — stands.

**2. The log advantage is real, exact, and the same size as the excess growth rate.**
It equals ``gamma_star`` per period in the continuous limit, and is computed here by
exhaustive path enumeration in the discrete case, with no simulation and no
approximation.

**3. What a log-utility investor actually gains is a variance reduction at an
unchanged mean.** In the continuous-time version of the same setup, with two assets of
equal arithmetic drift ``mu``, volatility ``sigma`` and correlation ``rho``:

    E[V_T]      = e**(mu T)                                for both portfolios
    E[V_reb**2] = e**(2 mu T) * e**(sigma**2 (1 + rho) T / 2)
    E[V_hold**2] = e**(2 mu T) * (e**(sigma**2 T) + e**(rho sigma**2 T)) / 2

and by the arithmetic-geometric mean inequality the second is never larger than the
third, strictly smaller unless ``rho = 1``. **Rebalancing is a mean-preserving
contraction of the terminal-wealth distribution.** That is the whole of the effect,
and it disposes of the dismissal in both directions:

* The dismissal is wrong as stated. The advantage is not an artefact of applying a
  utility function. ``(1/T) log W_T`` is the realised growth rate of the actual wealth
  path, a pathwise property with no preferences in it, and it converges almost surely
  to the growth rate that the log expectation computes. Breiman (1961) and
  Algoet and Cover (1988) then give the log-optimal portfolio asymptotic almost-sure
  dominance over every competing strategy. No other utility function has that property.
* The dismissal is right that expected terminal wealth is a legitimate alternative
  objective, and an investor who genuinely maximises ``E[W_T]`` gains nothing from
  rebalancing. It is also right that log is *a* utility function: Samuelson (1971,
  1979) showed geometric-mean maximisation is not a universal finite-horizon criterion,
  and nothing here contradicts him.

So the dispute is not about arithmetic; both sides compute correctly. It is about
whether the objective is the mean or the median of a right-skewed distribution whose
mean is set by paths of vanishing probability. This repository is named for Kelly, so
it takes the growth rate — but it must state that as a declared objective, not as a
proof that the other side is wrong.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class BinomialComparison:
    """Exact moments of both policies over an enumerated binomial return lattice."""

    periods: int
    paths: int
    expected_terminal_wealth_rebalanced: float
    expected_terminal_wealth_held: float
    expected_log_wealth_rebalanced: float
    expected_log_wealth_held: float
    variance_terminal_wealth_rebalanced: float
    variance_terminal_wealth_held: float

    @property
    def expected_profit_of_long_rebalanced_short_held(self) -> float:
        """The trade Chambers and Zdanowicz price. Zero under their assumptions."""
        return self.expected_terminal_wealth_rebalanced - self.expected_terminal_wealth_held

    @property
    def log_growth_rate_rebalanced(self) -> float:
        """``E[log W_T] / T`` per period."""
        return self.expected_log_wealth_rebalanced / self.periods

    @property
    def log_growth_rate_held(self) -> float:
        return self.expected_log_wealth_held / self.periods

    @property
    def log_growth_advantage(self) -> float:
        """Per-period expected-log advantage of rebalancing. The disputed quantity."""
        return self.log_growth_rate_rebalanced - self.log_growth_rate_held


def enumerate_binomial_comparison(
    *,
    up_return: float,
    down_return: float,
    up_probability: float = 0.5,
    periods: int = 2,
    weights: FloatArray | list[float] | None = None,
) -> BinomialComparison:
    """Exhaustively enumerate a two-asset binomial lattice and compare both policies.

    Each asset independently returns ``up_return`` with probability ``up_probability``
    and ``down_return`` otherwise, in every period, independently of the other asset.
    With ``n_assets = 2`` and ``periods = T`` there are ``4**T`` paths, all enumerated;
    nothing is sampled, so every figure is exact to floating point.

    The framework's committed fixture is ``up_return = 0.25``, ``down_return = -0.20``,
    ``up_probability = 0.5``, ``periods = 2``, equal weights: 16 paths and
    ``E[W_T] = 1.050625`` for both policies. Note that this asset has a geometric mean
    of exactly ``sqrt(1.25 * 0.80) - 1 = 0``, so the *entire* growth of the rebalanced
    portfolio is excess growth and the comparison isolates it cleanly.
    """
    if up_probability <= 0.0 or up_probability >= 1.0:
        raise ValueError(f"up_probability must lie in (0, 1), got {up_probability}")
    if periods < 1:
        raise ValueError(f"periods must be at least 1, got {periods}")
    if 1.0 + down_return <= 0.0 or 1.0 + up_return <= 0.0:
        raise ValueError("returns must leave a strictly positive wealth relative")
    w = np.array([0.5, 0.5], dtype=np.float64) if weights is None else np.asarray(
        weights, dtype=np.float64
    )
    if w.size != 2:
        raise ValueError("this enumeration is written for exactly two assets")
    if abs(float(np.sum(w)) - 1.0) > 1e-12:
        raise ValueError("weights must sum to one")
    if periods > 8:
        raise ValueError(
            f"enumerating {4 ** periods} paths is refused above 8 periods; use the "
            "closed-form moments instead"
        )

    outcomes = np.array([up_return, down_return], dtype=np.float64)
    probabilities = np.array([up_probability, 1.0 - up_probability], dtype=np.float64)

    rebalanced_wealth: list[float] = []
    held_wealth: list[float] = []
    path_probability: list[float] = []

    for choices in itertools.product(range(2), repeat=2 * periods):
        returns = outcomes[np.asarray(choices, dtype=np.int64)].reshape(periods, 2)
        probability = float(np.prod(probabilities[np.asarray(choices, dtype=np.int64)]))

        rebalanced = float(np.prod(1.0 + returns @ w))
        held = float(np.dot(w, np.prod(1.0 + returns, axis=0)))

        rebalanced_wealth.append(rebalanced)
        held_wealth.append(held)
        path_probability.append(probability)

    p = np.asarray(path_probability, dtype=np.float64)
    reb = np.asarray(rebalanced_wealth, dtype=np.float64)
    hold = np.asarray(held_wealth, dtype=np.float64)

    return BinomialComparison(
        periods=periods,
        paths=int(p.size),
        expected_terminal_wealth_rebalanced=float(np.dot(p, reb)),
        expected_terminal_wealth_held=float(np.dot(p, hold)),
        expected_log_wealth_rebalanced=float(np.dot(p, np.log(reb))),
        expected_log_wealth_held=float(np.dot(p, np.log(hold))),
        variance_terminal_wealth_rebalanced=float(np.dot(p, reb**2) - np.dot(p, reb) ** 2),
        variance_terminal_wealth_held=float(np.dot(p, hold**2) - np.dot(p, hold) ** 2),
    )


def expected_terminal_wealth_rebalanced(
    *,
    weights: FloatArray | list[float],
    mean_simple_returns: FloatArray | list[float],
    periods: int,
) -> float:
    """``(1 + w'mu)**T`` — exact for returns independent across time, any distribution."""
    w = np.asarray(weights, dtype=np.float64)
    mu = np.asarray(mean_simple_returns, dtype=np.float64)
    if w.shape != mu.shape:
        raise ValueError("weights and mean_simple_returns must have the same length")
    if periods < 1:
        raise ValueError("periods must be at least 1")
    return float((1.0 + float(w @ mu)) ** periods)


def expected_terminal_wealth_held(
    *,
    weights: FloatArray | list[float],
    mean_simple_returns: FloatArray | list[float],
    periods: int,
) -> float:
    """``sum_i w_i (1 + mu_i)**T`` — exact for returns independent across time.

    Equals :func:`expected_terminal_wealth_rebalanced` when all ``mu_i`` coincide, and
    strictly exceeds it otherwise by the convexity of ``x -> (1 + x)**T``. Buy-and-hold
    is therefore *ahead* on expected terminal wealth whenever the assets' arithmetic
    means differ at all — which sharpens rather than weakens Chambers and Zdanowicz.
    """
    w = np.asarray(weights, dtype=np.float64)
    mu = np.asarray(mean_simple_returns, dtype=np.float64)
    if w.shape != mu.shape:
        raise ValueError("weights and mean_simple_returns must have the same length")
    if periods < 1:
        raise ValueError("periods must be at least 1")
    return float(np.dot(w, (1.0 + mu) ** periods))


@dataclass(frozen=True)
class ContinuousMoments:
    """Terminal-wealth moments of both policies in the symmetric diffusion model."""

    horizon_years: float
    expected_terminal_wealth: float
    variance_rebalanced: float
    variance_held: float
    median_rebalanced: float
    median_held: float

    @property
    def variance_reduction(self) -> float:
        """``Var(hold) - Var(reb) >= 0``. The entire economic content of rebalancing."""
        return self.variance_held - self.variance_rebalanced


def continuous_terminal_wealth_moments(
    *,
    arithmetic_drift: float,
    volatility: float,
    correlation: float,
    horizon_years: float,
) -> ContinuousMoments:
    """Exact first two moments and medians for two symmetric GBM assets at 50/50.

    ``E[V_T] = e**(mu T)`` for both, so the Chambers-Zdanowicz equality is not an
    artefact of a two-period binomial lattice — it holds exactly in continuous time.
    The variances differ by the arithmetic-geometric mean inequality applied to
    ``e**(sigma**2 T)`` and ``e**(rho sigma**2 T)``, and the medians differ by exactly
    the excess growth rate times the horizon in log terms.

    The buy-and-hold median uses ``log V_hold = (X_a + X_b)/2 + log cosh(D/2)`` and the
    fact that the two terms are independent Gaussian-and-symmetric, so the median of the
    sum is not in general the sum of the medians; it is computed here as the median of
    the sum by inversion, not assumed. See :mod:`volatility_harvesting`.
    """
    if volatility < 0.0:
        raise ValueError("volatility cannot be negative")
    if not -1.0 <= correlation <= 1.0:
        raise ValueError("correlation must lie in [-1, 1]")
    if horizon_years <= 0.0:
        raise ValueError("horizon_years must be positive")

    t = horizon_years
    mean = math.exp(arithmetic_drift * t)
    second_rebalanced = math.exp(2.0 * arithmetic_drift * t) * math.exp(
        volatility**2 * (1.0 + correlation) * t / 2.0
    )
    second_held = (
        math.exp(2.0 * arithmetic_drift * t)
        * (math.exp(volatility**2 * t) + math.exp(correlation * volatility**2 * t))
        / 2.0
    )

    growth = arithmetic_drift - volatility**2 / 2.0
    excess = volatility**2 * (1.0 - correlation) / 4.0
    # Median of log V_reb: Gaussian with mean (g + gamma*) T.
    median_rebalanced = math.exp((growth + excess) * t)
    # Median of log V_hold: computed by numerically inverting its distribution function.
    median_held = math.exp(_median_log_buy_and_hold(growth=growth, volatility=volatility,
                                                    correlation=correlation, horizon_years=t))

    return ContinuousMoments(
        horizon_years=t,
        expected_terminal_wealth=mean,
        variance_rebalanced=second_rebalanced - mean**2,
        variance_held=second_held - mean**2,
        median_rebalanced=median_rebalanced,
        median_held=median_held,
    )


@dataclass(frozen=True)
class ExhibitFiveRow:
    """One horizon of Chambers and Zdanowicz's Exhibit 5, recomputed exactly.

    ``mean_annualised_rate`` is *their* metric: ``E[W_T**(1/T)] - 1``, the expectation
    of the realised annualised compound rate. It is **not** ``E[log W_T] / T``, and the
    distinction matters — the research framework currently describes their 1.874% and
    1.867% figures as expected log wealth, which they are not. Both metrics rank the
    two policies the same way, but only the log metric is horizon-invariant for the
    rebalanced portfolio.
    """

    periods: int
    rebalanced_mean_annualised_rate: float
    held_mean_annualised_rate: float
    expected_value: float
    rebalanced_log_growth: float
    held_log_growth: float

    @property
    def rate_gap(self) -> float:
        return self.rebalanced_mean_annualised_rate - self.held_mean_annualised_rate


def exhibit_five(
    *,
    up_return: float = 0.25,
    down_return: float = -0.20,
    up_probability: float = 0.5,
    periods: int,
) -> ExhibitFiveRow:
    """Reproduce one row of Exhibit 5 exactly, at any horizon, in ``O(T**2)`` work.

    Chambers and Zdanowicz stop at 12 periods, stating in a footnote that "The time
    horizon was not extended beyond 12 years because a four path tree with
    non-recombining nodes" becomes unmanageable. It does not have to be enumerated.
    Both policies have recombining structure:

    * the rebalanced portfolio's per-period multiplier takes three values with
      trinomial probabilities, so ``W_T`` is a trinomial mixture;
    * each asset's ``T``-period wealth relative is binomial in the number of up moves,
      so the held portfolio is a product of two independent binomials.

    Extending their own exhibit is what settles the dispute. The rebalanced portfolio's
    expected log growth is **constant at every horizon** — log wealth is additive, so
    the per-period expectation cannot depend on ``T`` — while the held portfolio's falls
    monotonically towards ``max_i g_i``, which in their parameterisation is exactly
    zero because ``sqrt(1.25 * 0.80) = 1``. Their reported 12-period gap of 12 bp is
    therefore not the size of the effect; it is the size of the effect at the horizon
    they chose to stop at, and it grows without bound towards 124 bp/yr.
    """
    if periods < 1:
        raise ValueError(f"periods must be at least 1, got {periods}")
    if periods > 3_000:
        raise ValueError(
            f"the held policy needs an O(T**2) table; {periods} periods is refused. "
            "Use asymptotic_rebalanced_rate for the limit instead"
        )
    if not 0.0 < up_probability < 1.0:
        raise ValueError("up_probability must lie in (0, 1)")
    up, down = 1.0 + up_return, 1.0 + down_return
    if up <= 0.0 or down <= 0.0:
        raise ValueError("returns must leave a strictly positive wealth relative")
    p, q = up_probability, 1.0 - up_probability

    counts = np.arange(periods + 1, dtype=np.float64)
    log_factorial = _log_factorial(periods)

    # Rebalanced: the 50/50 portfolio's per-period multiplier is trinomial.
    middle = 0.5 * (up + down)
    rebalanced_rate = 0.0
    rebalanced_log = 0.0
    for n_up in range(periods + 1):
        n_mid = np.arange(periods - n_up + 1, dtype=np.float64)
        n_down = periods - n_up - n_mid
        log_probability = (
            log_factorial[periods]
            - log_factorial[n_up]
            - _log_factorial_at(log_factorial, n_mid)
            - _log_factorial_at(log_factorial, n_down)
            + n_up * math.log(p * p)
            + n_mid * math.log(2.0 * p * q)
            + n_down * math.log(q * q)
        )
        probability = np.exp(log_probability)
        log_wealth = n_up * math.log(up) + n_mid * math.log(middle) + n_down * math.log(down)
        rebalanced_rate += float(np.sum(probability * np.expm1(log_wealth / periods)))
        rebalanced_log += float(np.sum(probability * log_wealth))

    # Held: two independent binomial wealth relatives, mixed 50/50.
    log_binomial = (
        log_factorial[periods]
        - _log_factorial_at(log_factorial, counts)
        - _log_factorial_at(log_factorial, periods - counts)
        + counts * math.log(p)
        + (periods - counts) * math.log(q)
    )
    binomial = np.exp(log_binomial)
    log_relatives = counts * math.log(up) + (periods - counts) * math.log(down)
    # log(0.5 e**a + 0.5 e**b) = logaddexp(a, b) - log 2, which never under- or overflows.
    log_mixture = np.logaddexp(log_relatives[:, None], log_relatives[None, :]) - math.log(2.0)
    joint = binomial[:, None] * binomial[None, :]
    held_rate = float(np.sum(joint * np.expm1(log_mixture / periods)))
    held_log = float(np.sum(joint * log_mixture))

    mean_simple = p * up_return + q * down_return
    return ExhibitFiveRow(
        periods=periods,
        rebalanced_mean_annualised_rate=rebalanced_rate,
        held_mean_annualised_rate=held_rate,
        expected_value=(1.0 + mean_simple) ** periods,
        rebalanced_log_growth=rebalanced_log / periods,
        held_log_growth=held_log / periods,
    )


def _log_factorial(n: int) -> FloatArray:
    """``log(k!)`` for ``k = 0 .. n``, by cumulative sum of ``log k``."""
    values = np.zeros(n + 1, dtype=np.float64)
    if n >= 1:
        values[1:] = np.cumsum(np.log(np.arange(1, n + 1, dtype=np.float64)))
    return values


def _log_factorial_at(table: FloatArray, index: FloatArray) -> FloatArray:
    return np.asarray(table[index.astype(np.int64)], dtype=np.float64)


def asymptotic_rebalanced_rate(
    *, up_return: float = 0.25, down_return: float = -0.20, up_probability: float = 0.5
) -> float:
    """The limit their Exhibit 5 is converging to: ``e**g_p - 1``.

    ``g_p = E[log(1 + w'R)]`` per period, and by the strong law
    ``W_T**(1/T) -> e**g_p`` almost surely, so the expected annualised rate converges
    there too. For their parameters this is 1.2423% per period against a buy-and-hold
    limit of exactly 0%.
    """
    up, down = 1.0 + up_return, 1.0 + down_return
    p, q = up_probability, 1.0 - up_probability
    middle = 0.5 * (up + down)
    log_growth = (
        p**2 * math.log(up) + 2.0 * p * q * math.log(middle) + q**2 * math.log(down)
    )
    return math.exp(log_growth) - 1.0


@dataclass(frozen=True)
class CertaintyEquivalentComparison:
    """Chambers and Zdanowicz's own deciding example, priced under both objectives."""

    certain_terminal_wealth: float
    risky_expected_terminal_wealth: float
    certain_expected_log_wealth: float
    risky_expected_log_wealth: float
    risky_log_certainty_equivalent: float

    @property
    def expected_wealth_prefers_the_gamble(self) -> bool:
        return self.risky_expected_terminal_wealth > self.certain_terminal_wealth

    @property
    def log_utility_prefers_the_certain_deposit(self) -> bool:
        return self.certain_expected_log_wealth > self.risky_expected_log_wealth


def certificate_of_deposit_example(
    *,
    principal: float = 10_000.0,
    years: int = 18,
    certain_yield: float = 0.04,
    low_yield: float = 0.00,
    high_yield: float = 0.08,
    high_probability: float = 0.5,
) -> CertaintyEquivalentComparison:
    """The example Chambers and Zdanowicz say "merely requires returning to".

    They pose an 18-year deposit paying a guaranteed 4%, against a coin flip between 0%
    and 8%. Both have the same expected annualised rate; the gamble has a far higher
    expected terminal value. They take this as deciding the question in favour of the
    value-based view.

    It does not decide it, and computing it out shows why. The gamble is worth about
    $24,980 in expectation against the certain $20,258 — 23% more — yet its
    certainty equivalent under log utility is about $19,979, so a log investor pays
    roughly $280 per $10,000 to *avoid* it. That is not an error on either side. It is
    the whole disagreement, stated as a price, and it is a preference, not a theorem.
    Their example establishes that expected wealth and expected log wealth rank this
    gamble differently; it does not establish that either ranking is arbitrary.
    """
    if years < 1 or principal <= 0.0:
        raise ValueError("principal and years must be positive")
    if not 0.0 < high_probability < 1.0:
        raise ValueError("high_probability must lie in (0, 1)")
    certain = principal * (1.0 + certain_yield) ** years
    low = principal * (1.0 + low_yield) ** years
    high = principal * (1.0 + high_yield) ** years
    p = high_probability
    expected = p * high + (1.0 - p) * low
    expected_log = p * math.log(high) + (1.0 - p) * math.log(low)
    return CertaintyEquivalentComparison(
        certain_terminal_wealth=certain,
        risky_expected_terminal_wealth=expected,
        certain_expected_log_wealth=math.log(certain),
        risky_expected_log_wealth=expected_log,
        risky_log_certainty_equivalent=math.exp(expected_log),
    )


def _median_log_buy_and_hold(
    *, growth: float, volatility: float, correlation: float, horizon_years: float
) -> float:
    """Median of ``log V_hold(T) = (X_a + X_b)/2 + log cosh(D/2)`` by root finding.

    ``(X_a + X_b)/2`` is ``N(g T, sigma**2 (1 + rho) T / 2)`` and ``D`` is
    ``N(0, 2 sigma**2 (1 - rho) T)``; the two are independent because their covariance
    ``sigma_a**2 - sigma_b**2`` vanishes when the volatilities are equal. The median of
    the sum is therefore a one-dimensional convolution, solved by bisection on the
    distribution function evaluated with Gauss-Hermite quadrature.
    """
    from scipy.optimize import brentq
    from scipy.stats import norm

    from .volatility_harvesting import log_cosh

    common_sd = volatility * math.sqrt((1.0 + correlation) * horizon_years / 2.0)
    relative_sd = volatility * math.sqrt(2.0 * (1.0 - correlation) * horizon_years)
    if relative_sd == 0.0:
        return growth * horizon_years

    nodes, weights = np.polynomial.hermite_e.hermegauss(120)
    weights = weights / float(np.sum(weights))
    straddle = np.asarray([log_cosh(relative_sd * node / 2.0) for node in nodes], dtype=np.float64)

    def cdf(x: float) -> float:
        if common_sd == 0.0:
            return float(np.dot(weights, (growth * horizon_years + straddle <= x).astype(float)))
        z = (x - growth * horizon_years - straddle) / common_sd
        return float(np.dot(weights, norm.cdf(z)))

    low = growth * horizon_years - 10.0 * (common_sd + relative_sd) - 1.0
    high = growth * horizon_years + 10.0 * (common_sd + relative_sd) + 1.0
    return float(brentq(lambda x: cdf(x) - 0.5, low, high, xtol=1e-12, rtol=1e-14))
