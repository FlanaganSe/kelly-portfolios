"""Constant-weight versus buy-and-hold growth: exact algebra, not simulation.

The whole study rests on one decomposition, derived here rather than quoted. Let two
assets follow correlated geometric Brownian motions with log-drifts ``g_a``, ``g_b``,
instantaneous volatilities ``sigma_a``, ``sigma_b`` and correlation ``rho``. Write
``X_i(T) = g_i T + sigma_i W_i(T)`` for the log price relative of asset ``i``, and
``D(T) = X_a(T) - X_b(T)``, which is Gaussian with variance ``tau**2 T`` where
``tau**2 = sigma_a**2 + sigma_b**2 - 2 rho sigma_a sigma_b``.

**Continuously rebalanced 50/50.** ``d V / V = 0.5 (dS_a/S_a + dS_b/S_b)``, so by
Ito ``log V_reb(T) = (X_a + X_b) / 2 + gamma_star T`` with the excess growth rate

    gamma_star = 0.5 * (sum_i w_i sigma_i**2 - sigma_p**2).

**Buy-and-hold 50/50.** ``V_hold(T) = 0.5 e^{X_a} + 0.5 e^{X_b}``, and the algebraic
identity ``0.5 (e^u + e^v) = e^{(u+v)/2} cosh((u-v)/2)`` gives, with no approximation,

    log V_hold(T) = (X_a + X_b) / 2 + log cosh(D(T) / 2).

Subtracting, the common factor cancels **pathwise**:

    log V_reb(T) - log V_hold(T) = gamma_star * T - log cosh(D(T) / 2).          (*)

Three consequences, all exact, and all of which this module computes:

1. ``log cosh(d/2) -> |d|/2 - log 2`` for large ``|d|``, so (*) is the payoff of a
   **short straddle on relative log performance**, struck at zero, with premium
   ``gamma_star * T``. That derives the qualitative Rattray et al. (2020) result — a
   rebalance is short relative-performance continuation — in continuous time, and it
   is why the loss is unbounded below while the gain is capped at ``gamma_star * T``.
2. ``|D(T)|`` grows like ``sqrt(T)`` while the premium grows like ``T``, so (*) tends
   to ``+infinity`` almost surely: constant-weight rebalancing does asymptotically
   beat buy-and-hold whenever ``gamma_star > 0``. See
   :func:`asymptotic_buy_and_hold_growth` for the general statement and its proof
   sketch, which is the condition ``g_p > max_i g_i``.
3. Because the drift cancels in (*), the probability that rebalancing wins depends on
   the horizon and volatilities **only through the single number ``c = gamma_star T``**.
   It never falls below ``2 Phi(1) - 1 = 68.27%`` and rises towards one absurdly
   slowly. See :func:`probability_rebalanced_beats_buy_and_hold`.

Nothing here is a claim about market data. Every function is a statement about a
stated model, and the model's assumptions — continuous trading, no costs, no taxes,
constant parameters, lognormal prices — are all false in the direction that reduces
the measured advantage.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

FloatArray = NDArray[np.float64]

MINIMUM_PROBABILITY = 2.0 * float(norm.cdf(1.0)) - 1.0
"""``2 Phi(1) - 1 = 0.6827``: the infimum of P(rebalanced beats buy-and-hold).

Reached as ``gamma_star * T -> 0``. A striking consequence of (*): however small the
excess growth rate and however short the horizon, continuous rebalancing of two
equal-volatility assets with equal drift wins about 68% of the time. That is the
*floor*, not evidence of an edge, and it is the reason a high win rate against
buy-and-hold is not by itself informative.
"""


def log_cosh(x: float) -> float:
    """``log cosh(x)``, computed without overflowing for large ``|x|``.

    ``log cosh(x) = |x| + log1p(exp(-2|x|)) - log 2``.
    """
    absolute = abs(x)
    return absolute + math.log1p(math.exp(-2.0 * absolute)) - math.log(2.0)


def relative_log_volatility(
    *, volatility_a: float, volatility_b: float, correlation: float
) -> float:
    """``tau = sqrt(sigma_a**2 + sigma_b**2 - 2 rho sigma_a sigma_b)``.

    The volatility of the *relative* log performance ``D = X_a - X_b``. It is the only
    volatility input that the rebalanced-versus-held comparison depends on.
    """
    if volatility_a < 0.0 or volatility_b < 0.0:
        raise ValueError("volatilities cannot be negative")
    if not -1.0 <= correlation <= 1.0:
        raise ValueError(f"correlation must lie in [-1, 1], got {correlation}")
    variance = (
        volatility_a**2
        + volatility_b**2
        - 2.0 * correlation * volatility_a * volatility_b
    )
    return math.sqrt(max(variance, 0.0))


def excess_growth_two_asset(
    *,
    volatility_a: float,
    volatility_b: float,
    correlation: float,
    weight_a: float = 0.5,
) -> float:
    """``gamma_star = 0.5 (sum_i w_i sigma_i**2 - sigma_p**2)`` for two assets.

    At ``w = 1/2`` and equal volatilities this reduces to
    ``gamma_star = sigma**2 (1 - rho) / 4 = tau**2 / 8``, which is the closed form the
    two-asset results in this module use. The general ``n``-asset version is
    :func:`portfolio_edge.core.portfolio.excess_growth_rate`; this function exists so
    the two-asset case can be written from scalars without building a matrix.
    """
    if not 0.0 <= weight_a <= 1.0:
        raise ValueError(f"weight_a must lie in [0, 1], got {weight_a}")
    weight_b = 1.0 - weight_a
    weighted_variance = weight_a * volatility_a**2 + weight_b * volatility_b**2
    portfolio_variance = (
        weight_a**2 * volatility_a**2
        + weight_b**2 * volatility_b**2
        + 2.0 * weight_a * weight_b * correlation * volatility_a * volatility_b
    )
    return 0.5 * (weighted_variance - portfolio_variance)


def rebalanced_growth_rate(
    *,
    growth_a: float,
    growth_b: float,
    volatility_a: float,
    volatility_b: float,
    correlation: float,
    weight_a: float = 0.5,
) -> float:
    """``g_p = sum_i w_i g_i + gamma_star``: growth of the continuously rebalanced mix.

    Exact in the diffusion model, and equal to both the almost-sure long-run growth
    rate and ``E[log V_T] / T`` at every horizon, because ``log V_reb(T)`` is Gaussian
    with mean ``g_p T``.
    """
    weight_b = 1.0 - weight_a
    return weight_a * growth_a + weight_b * growth_b + excess_growth_two_asset(
        volatility_a=volatility_a,
        volatility_b=volatility_b,
        correlation=correlation,
        weight_a=weight_a,
    )


def asymptotic_buy_and_hold_growth(component_growth_rates: FloatArray | list[float]) -> float:
    """``lim (1/T) log V_hold(T) = max_i g_i`` almost surely, for any fixed weights.

    Proof, for ``n`` assets with strictly positive initial weights ``w`` and
    ``X_i(T) = g_i T + (a local martingale with (1/T)-limit zero)``. Write
    ``M(T) = max_i X_i(T)``. Then

        M(T) + log(min_i w_i) <= log sum_i w_i e^{X_i(T)} <= M(T) + log(1),

    because the sum is at least ``w_j e^{M}`` for the maximising ``j`` and at most
    ``e^{M}`` since the weights sum to one. Both bounds are ``M(T) + O(1)``, so
    ``(1/T) log V_hold(T) - M(T)/T -> 0``. The strong law for Brownian motion gives
    ``X_i(T)/T -> g_i`` almost surely, hence ``M(T)/T -> max_i g_i``.

    **This is the exact statement the repository needed.** A constant-weight portfolio
    asymptotically beats buy-and-hold if and only if ``g_p > max_i g_i``, that is

        sum_i w_i g_i + gamma_star_w > max_i g_i.

    Two corollaries. When all ``g_i`` are equal the condition is just
    ``gamma_star_w > 0``, which holds for any long-only weights on assets that are not
    perfectly co-moving in log space — so with equal drifts, rebalancing *always* wins
    eventually. And the buy-and-hold portfolio asymptotically throws away the whole of
    ``gamma_star``: the drifting portfolio converges on the single best asset, which is
    the opposite of diversification.

    The word doing the work is *asymptotically*. The finite-horizon shortfall is
    :func:`buy_and_hold_log_bonus`, and it decays only like ``1 / sqrt(T)``.
    """
    rates = np.asarray(component_growth_rates, dtype=np.float64)
    if rates.size == 0:
        raise ValueError("component_growth_rates must contain at least one asset")
    if not np.all(np.isfinite(rates)):
        raise ValueError("component_growth_rates contains non-finite entries")
    return float(np.max(rates))


def rebalancing_beats_buy_and_hold_asymptotically(
    *, portfolio_growth_rate: float, component_growth_rates: FloatArray | list[float]
) -> bool:
    """The proved condition ``g_p > max_i g_i``, evaluated.

    See :func:`asymptotic_buy_and_hold_growth` for the proof. Ties return ``False``:
    at ``g_p = max_i g_i`` the difference is ``O(sqrt(T))`` noise with no drift and the
    sign does not settle.
    """
    return portfolio_growth_rate > asymptotic_buy_and_hold_growth(component_growth_rates)


def buy_and_hold_log_bonus(*, relative_variance: float) -> float:
    """``E[log cosh(Z / 2)]`` for ``Z ~ N(0, relative_variance)``.

    This is the amount of ``gamma_star * T`` that a 50/50 buy-and-hold portfolio of two
    equal-drift assets captures *for free*, purely because two assets held without
    trading still diversify. It is the reason a 30-year backtest attributes most of the
    diversification bonus to holding rather than to rebalancing.

    Its shape is the whole finding. For small ``v`` it is ``v/8 + O(v**2)``, matching
    ``gamma_star * T`` exactly; for large ``v`` it is
    ``sqrt(v / (2 pi)) - log 2 + o(1)``, so as a *rate* it decays like
    ``1 / sqrt(T)`` and the rebalancing residual ``gamma_star - E[.]/T`` approaches
    ``gamma_star`` only over centuries.

    Computed by adaptive quadrature on the half line using the symmetry of the
    integrand, which is smooth for ``z > 0``; the ``|z|`` kink at the origin is
    excluded by construction rather than integrated across.
    """
    if relative_variance < 0.0:
        raise ValueError("relative_variance cannot be negative")
    if relative_variance == 0.0:
        return 0.0
    scale = math.sqrt(relative_variance)

    def integrand(z: float) -> float:
        return 2.0 * log_cosh(scale * z / 2.0) * math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)

    value, _ = quad(integrand, 0.0, np.inf, limit=400)
    return float(value)


def buy_and_hold_growth_rate(
    *,
    growth_a: float,
    growth_b: float,
    volatility_a: float,
    volatility_b: float,
    correlation: float,
    horizon_years: float,
    weight_a: float = 0.5,
) -> float:
    """``E[log V_hold(T)] / T`` for two assets held untouched for ``horizon_years``.

    General form, valid for unequal weights and unequal drifts:
    ``E[log V_hold] = g_a T + E[log(w_a + w_b e**Y)]`` with
    ``Y ~ N((g_b - g_a) T, tau**2 T)``. At ``w_a = 1/2`` and ``g_a = g_b`` this reduces
    to ``g T + E[log cosh(D/2)]``, which :func:`buy_and_hold_log_bonus` computes
    directly; the tests assert the two agree.

    Note what this is *not*: the almost-sure growth rate, which is ``max_i g_i`` by
    :func:`asymptotic_buy_and_hold_growth`. The expected log is strictly above it at
    every finite horizon, and the gap is the whole of the finite-horizon story.
    """
    if horizon_years <= 0.0:
        raise ValueError(f"horizon_years must be positive, got {horizon_years}")
    if not 0.0 < weight_a < 1.0:
        raise ValueError(f"weight_a must lie strictly inside (0, 1), got {weight_a}")
    weight_b = 1.0 - weight_a
    tau = relative_log_volatility(
        volatility_a=volatility_a, volatility_b=volatility_b, correlation=correlation
    )
    mean = (growth_b - growth_a) * horizon_years
    scale = tau * math.sqrt(horizon_years)
    if scale == 0.0:
        expectation = math.log(weight_a + weight_b * math.exp(mean))
    else:

        def integrand(z: float) -> float:
            y = mean + scale * z
            # log(w_a + w_b e**y), written stably for large |y|.
            if y > 0.0:
                shifted = math.log(weight_a * math.exp(-y) + weight_b) + y
            else:
                shifted = math.log(weight_a + weight_b * math.exp(y))
            return shifted * math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)

        value, _ = quad(integrand, -np.inf, np.inf, limit=400)
        expectation = float(value)
    return growth_a + expectation / horizon_years


def probability_rebalanced_beats_buy_and_hold(
    *, excess_growth: float, horizon_years: float
) -> float:
    """``P(log V_reb(T) > log V_hold(T))`` for the symmetric two-asset case, exactly.

    From (*), the event is ``log cosh(D/2) < gamma_star T``, i.e.
    ``|D| < 2 arccosh(e**c)`` with ``c = gamma_star T``, and ``D ~ N(0, 8 c)`` because
    ``tau**2 T = 8 gamma_star T``. Hence

        P = 2 Phi( 2 arccosh(e**c) / sqrt(8 c) ) - 1.

    The probability therefore depends on volatility, correlation and horizon **only
    through the product ``c``**. It equals :data:`MINIMUM_PROBABILITY` in the limit
    ``c -> 0`` and increases monotonically, but only like ``2 Phi(sqrt(c/2)) - 1``, so
    reaching 90% needs ``c`` near 3.9 — four centuries at ``gamma_star = 1%/yr``.

    Requires equal drifts and equal volatilities at 50/50. For a drift gap use
    :func:`probability_rebalanced_beats_single_asset`, whose comparator is investable.
    """
    if excess_growth < 0.0:
        raise ValueError("excess_growth cannot be negative")
    if horizon_years <= 0.0:
        raise ValueError(f"horizon_years must be positive, got {horizon_years}")
    c = excess_growth * horizon_years
    if c == 0.0:
        return MINIMUM_PROBABILITY
    return 2.0 * float(norm.cdf(_arccosh_exp(c) * 2.0 / math.sqrt(8.0 * c))) - 1.0


def horizon_for_rebalancing_confidence(
    *, excess_growth: float, probability: float
) -> float:
    """Years until ``P(rebalanced beats buy-and-hold)`` reaches ``probability``.

    Undefined below :data:`MINIMUM_PROBABILITY`, which is attained at zero horizon, so
    anything at or under that floor raises rather than returning zero.
    """
    if excess_growth <= 0.0:
        raise ValueError("excess_growth must be positive")
    if not MINIMUM_PROBABILITY < probability < 1.0:
        raise ValueError(
            f"probability must lie strictly between {MINIMUM_PROBABILITY!r} and 1, "
            f"got {probability!r}"
        )

    def objective(c: float) -> float:
        return 2.0 * float(norm.cdf(_arccosh_exp(c) * 2.0 / math.sqrt(8.0 * c))) - 1.0 - probability

    c = float(brentq(objective, 1e-12, 1e7, xtol=1e-12, rtol=1e-14))
    return c / excess_growth


def probability_rebalanced_beats_single_asset(
    *, excess_growth: float, drift_gap: float, horizon_years: float
) -> float:
    """``P(rebalanced 50/50 beats the ex-ante higher-drift asset held alone)``.

    Let asset A have log-drift ``g + delta`` and asset B ``g - delta`` with
    ``delta = drift_gap >= 0``, equal volatilities and 50/50 weights. Then
    ``log V_reb - X_a = (gamma_star - delta) T - D_0 / 2`` with
    ``D_0 ~ N(0, tau**2 T)``, so

        P = Phi( (gamma_star - delta) sqrt(T / (2 gamma_star)) ).

    Two exact readings. The break-even is ``delta = gamma_star``: a drift gap equal to
    the excess growth rate makes the comparison a **coin flip at every horizon**, and
    any larger gap makes rebalancing lose with probability approaching one. And the
    comparator is the asset chosen *in advance*, not the ex-post winner, which is the
    only comparison an investor can actually make.

    This is the estimation cliff. A 1%/yr difference in true expected log return
    between two broad equity markets is far inside the standard error of anything that
    can be estimated from data, and it exactly cancels a ``gamma_star`` of 1%/yr.
    """
    if excess_growth <= 0.0:
        raise ValueError("excess_growth must be positive")
    if drift_gap < 0.0:
        raise ValueError("drift_gap cannot be negative; label the better asset A")
    if horizon_years <= 0.0:
        raise ValueError(f"horizon_years must be positive, got {horizon_years}")
    z = (excess_growth - drift_gap) * math.sqrt(horizon_years / (2.0 * excess_growth))
    return float(norm.cdf(z))


def breakeven_drift_gap(*, excess_growth: float) -> float:
    """The drift gap at which rebalancing becomes a coin flip: ``delta = gamma_star``.

    Horizon-independent, which is the point. No amount of time rescues a constant-weight
    portfolio whose components' true growth rates differ by more than its excess growth
    rate; see :func:`probability_rebalanced_beats_single_asset`.
    """
    if excess_growth <= 0.0:
        raise ValueError("excess_growth must be positive")
    return excess_growth


@dataclass(frozen=True)
class RebalancingAdvantage:
    """The distribution of the annualised rebalancing advantage over buy-and-hold."""

    excess_growth: float
    horizon_years: float
    mean: float
    median: float
    quantile_05: float
    quantile_95: float
    probability_positive: float


def rebalancing_advantage_quantile(
    *, excess_growth: float, horizon_years: float, quantile: float
) -> float:
    """Quantile of ``(log V_reb - log V_hold) / T``, annualised, in the symmetric case.

    From (*) the advantage is ``gamma_star - log cosh(D/2) / T``, a strictly decreasing
    function of ``|D|``, so its ``q``-quantile uses the ``(1 - q)``-quantile of ``|D|``,
    which is ``tau sqrt(T) Phi^{-1}(1 - q/2)``.

    The asymmetry this exposes matters more than the mean. The upside is capped at
    ``gamma_star``; the downside is unbounded. That is the short straddle, priced.
    """
    if excess_growth <= 0.0:
        raise ValueError("excess_growth must be positive")
    if horizon_years <= 0.0:
        raise ValueError(f"horizon_years must be positive, got {horizon_years}")
    if not 0.0 < quantile < 1.0:
        raise ValueError(f"quantile must lie strictly inside (0, 1), got {quantile}")
    scale = math.sqrt(8.0 * excess_growth * horizon_years)
    absolute_d = scale * float(norm.ppf(1.0 - quantile / 2.0))
    return excess_growth - log_cosh(absolute_d / 2.0) / horizon_years


def rebalancing_advantage(
    *, excess_growth: float, horizon_years: float
) -> RebalancingAdvantage:
    """Mean, median and tails of the annualised rebalancing advantage, all closed form.

    The mean and the median differ sharply and both are correct. The mean is
    ``gamma_star - E[log cosh(D/2)] / T``; the median replaces the expectation with the
    value at the median of ``|D|``. Because ``log cosh`` is convex in ``|D|`` and
    ``|D|`` is right-skewed, the mean advantage is materially *smaller* than the median
    advantage: expected-log arithmetic is dragged down by the minority of paths on which
    the untouched portfolio's winner runs away. Reporting only the mean understates what
    a typical path sees; reporting only the median hides the left tail.
    """
    mean = excess_growth - buy_and_hold_log_bonus(
        relative_variance=8.0 * excess_growth * horizon_years
    ) / horizon_years
    return RebalancingAdvantage(
        excess_growth=excess_growth,
        horizon_years=horizon_years,
        mean=mean,
        median=rebalancing_advantage_quantile(
            excess_growth=excess_growth, horizon_years=horizon_years, quantile=0.5
        ),
        quantile_05=rebalancing_advantage_quantile(
            excess_growth=excess_growth, horizon_years=horizon_years, quantile=0.05
        ),
        quantile_95=rebalancing_advantage_quantile(
            excess_growth=excess_growth, horizon_years=horizon_years, quantile=0.95
        ),
        probability_positive=probability_rebalanced_beats_buy_and_hold(
            excess_growth=excess_growth, horizon_years=horizon_years
        ),
    )


def discrete_rebalancing_growth_bonus(
    *, relative_log_variance: float, interval_years: float
) -> float:
    """Annual excess growth actually captured by rebalancing every ``interval_years``.

    A portfolio rebalanced at interval ``h`` is a chain of buy-and-hold portfolios of
    length ``h``, so its annual expected log growth above ``sum_i w_i g_i`` is
    ``E[log cosh(D_h / 2)] / h`` with ``D_h ~ N(0, tau**2 h)``. One function therefore
    governs the whole spectrum: continuous rebalancing is the ``h -> 0`` limit
    ``tau**2 / 8 = gamma_star``, buy-and-hold for ``T`` years is ``h = T``, and every
    calendar policy sits in between. Rebalancing more often is monotonically better in
    this model — which is exactly why the model, having no costs or taxes in it, cannot
    be used to choose a rebalancing frequency.
    """
    if interval_years <= 0.0:
        raise ValueError(f"interval_years must be positive, got {interval_years}")
    return (
        buy_and_hold_log_bonus(relative_variance=relative_log_variance * interval_years)
        / interval_years
    )


def _arccosh_exp(c: float) -> float:
    """``arccosh(e**c)`` without overflowing ``e**c``.

    ``arccosh(x) = log(x + sqrt(x**2 - 1))``, so with ``x = e**c`` and ``c > 0``,
    ``arccosh(e**c) = c + log1p(sqrt(1 - e**(-2c)))``.
    """
    if c <= 0.0:
        raise ValueError("c must be positive")
    return c + math.log1p(math.sqrt(-math.expm1(-2.0 * c)))
