"""Seeded simulation that checks the closed forms in :mod:`volatility_harvesting`.

This module exists to *falsify* algebra, not to produce results of its own. Every
number it reports has a closed form elsewhere in this package, and the tests assert
agreement within a stated Monte Carlo tolerance. Where no closed form exists — the
``n``-asset buy-and-hold expectation, and any policy rebalanced at a finite interval
with more than two assets — the simulation is the estimate, and its standard error is
reported alongside it rather than left implicit.

The generative model is exact rather than discretised: log returns are drawn directly
from the multivariate normal implied by geometric Brownian motion over one step, so
there is no Euler discretisation error to confuse with a rebalancing effect.

A note on sample size. The paired difference ``log V_reb - log V_hold`` has a standard
deviation of roughly ``tau sqrt(T) / 2`` in log wealth, which at ``tau = 28%`` and
``T = 30`` is about 0.77 — so 5,000 paths give a standard error near 1.4 bp/yr on the
annualised difference, and a reported figure can sit two or three standard errors from
the true value without anything being wrong. Prefer the closed form; use this to check
that the closed form is the right closed form.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.portfolio import check_weights_sum_to_one
from portfolio_edge.core.rebalance import BuyAndHold, CalendarRebalance, simulate

FloatArray = NDArray[np.float64]

DEFAULT_SEED = 20260812
"""Committed default seed. Changing it changes every simulated number in the study."""


@dataclass(frozen=True)
class GrowthComparison:
    """Annualised growth rates of one rebalanced policy against buy-and-hold.

    All fields are per-year log growth rates, averaged over paths, except the
    ``*_standard_error`` fields (of those averages) and ``probability_rebalanced_wins``.
    """

    paths: int
    horizon_years: float
    steps_per_year: int
    rebalance_interval_steps: int
    rebalanced_growth: float
    buy_and_hold_growth: float
    component_growth: FloatArray
    advantage_mean: float
    advantage_median: float
    advantage_standard_error: float
    probability_rebalanced_wins: float

    @property
    def probability_standard_error(self) -> float:
        """Binomial standard error of :attr:`probability_rebalanced_wins`."""
        p = self.probability_rebalanced_wins
        return math.sqrt(p * (1.0 - p) / self.paths)


def simulate_growth_comparison(
    *,
    growth_rates: FloatArray | list[float],
    volatilities: FloatArray | list[float],
    correlation_matrix: FloatArray | list[list[float]],
    weights: FloatArray | list[float],
    horizon_years: float = 30.0,
    steps_per_year: int = 12,
    rebalance_interval_steps: int = 1,
    paths: int = 20_000,
    seed: int = DEFAULT_SEED,
    chunk_size: int = 2_000,
) -> GrowthComparison:
    """Compare a calendar-rebalanced portfolio with buy-and-hold under seeded GBM.

    ``growth_rates`` are annual **log** drifts ``g_i``, not arithmetic means: passing a
    CAGR where an Ito drift is expected is the single most common way this calculation
    goes wrong, so the units are named rather than inferred.

    The rebalanced path is computed blockwise — within a block of
    ``rebalance_interval_steps`` steps the portfolio drifts, and at each block boundary
    the target weights are restored — which is exactly the definition, evaluated in
    closed form per block rather than stepped. :func:`_agrees_with_core_simulator` in
    the tests checks this against
    :func:`portfolio_edge.core.rebalance.simulate` path by path.
    """
    g = np.asarray(growth_rates, dtype=np.float64)
    sigma = np.asarray(volatilities, dtype=np.float64)
    corr = np.asarray(correlation_matrix, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    n_assets = g.size
    if not (sigma.size == n_assets and w.size == n_assets):
        raise ValueError("growth_rates, volatilities and weights must have equal length")
    if corr.shape != (n_assets, n_assets):
        raise ValueError(f"correlation_matrix must be {n_assets}x{n_assets}, got {corr.shape}")
    if np.any(sigma < 0.0):
        raise ValueError("volatilities cannot be negative")
    check_weights_sum_to_one(w)
    if horizon_years <= 0.0 or steps_per_year < 1 or paths < 2 or chunk_size < 1:
        raise ValueError("horizon, step count, path count and chunk size must be positive")
    if rebalance_interval_steps < 1:
        raise ValueError("rebalance_interval_steps must be at least 1")

    total_steps = round(horizon_years * steps_per_year)
    if total_steps % rebalance_interval_steps != 0:
        raise ValueError(
            f"{total_steps} steps do not divide evenly into blocks of "
            f"{rebalance_interval_steps}; the final block would be shorter and the "
            "policy would not be the one named"
        )
    blocks = total_steps // rebalance_interval_steps
    dt = 1.0 / steps_per_year

    covariance = corr * np.outer(sigma, sigma)
    factor = np.linalg.cholesky(covariance + np.eye(n_assets) * 1e-15)
    step_mean = g * dt
    step_scale = math.sqrt(dt)

    rng = np.random.default_rng(seed)
    rebalanced = np.empty(paths, dtype=np.float64)
    held = np.empty(paths, dtype=np.float64)
    components = np.empty((paths, n_assets), dtype=np.float64)

    done = 0
    while done < paths:
        size = min(chunk_size, paths - done)
        shocks = rng.standard_normal((size, total_steps, n_assets)) @ factor.T
        log_returns = step_mean + step_scale * shocks

        block_logs = log_returns.reshape(size, blocks, rebalance_interval_steps, n_assets).sum(
            axis=2
        )
        block_multipliers = np.exp(block_logs) @ w
        rebalanced[done : done + size] = np.log(block_multipliers).sum(axis=1)

        total_logs = block_logs.sum(axis=1)
        held[done : done + size] = np.log(np.exp(total_logs) @ w)
        components[done : done + size] = total_logs
        done += size

    advantage = (rebalanced - held) / horizon_years
    return GrowthComparison(
        paths=paths,
        horizon_years=horizon_years,
        steps_per_year=steps_per_year,
        rebalance_interval_steps=rebalance_interval_steps,
        rebalanced_growth=float(np.mean(rebalanced) / horizon_years),
        buy_and_hold_growth=float(np.mean(held) / horizon_years),
        component_growth=np.asarray(np.mean(components, axis=0) / horizon_years, dtype=np.float64),
        advantage_mean=float(np.mean(advantage)),
        advantage_median=float(np.median(advantage)),
        advantage_standard_error=float(np.std(advantage, ddof=1) / math.sqrt(paths)),
        probability_rebalanced_wins=float(np.mean(rebalanced > held)),
    )


def core_simulator_growth_rates(
    *,
    asset_log_returns: FloatArray,
    weights: FloatArray | list[float],
    rebalance_interval_steps: int,
    horizon_years: float,
) -> tuple[float, float]:
    """Rebalanced and buy-and-hold annual log growth for one path, via the core engine.

    Delegates to :func:`portfolio_edge.core.rebalance.simulate` so that the blockwise
    vectorisation in :func:`simulate_growth_comparison` is checked against the audited
    implementation rather than trusted. ``asset_log_returns`` is ``(steps, n_assets)``.
    """
    simple = np.expm1(np.asarray(asset_log_returns, dtype=np.float64))
    w = np.asarray(weights, dtype=np.float64)
    rebalanced = simulate(simple, w, CalendarRebalance(interval=rebalance_interval_steps))
    held = simulate(simple, w, BuyAndHold())
    return (
        math.log(rebalanced.terminal_wealth) / horizon_years,
        math.log(held.terminal_wealth) / horizon_years,
    )
