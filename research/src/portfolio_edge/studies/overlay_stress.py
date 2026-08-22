"""Stressing the financed-overlay recommendation to destruction.

``docs/research/capital-efficiency-and-breadth.md`` §5a stresses the overlay one
parameter at a time, and a red team pointed out the obvious defect: **the adverse moves
are correlated in exactly the states that matter.** The one modestly-joint cell §5a
contains — trend excess -2% *and* correlation +0.30 — is already -1.26 pp/yr against the
leverage-matched control, which is twice the central case's *positive* +0.62. A table
that moves one axis at a time cannot see that, and reporting the worst univariate cell as
the worst case understates the risk by construction.

This module builds the joint object instead, and then attacks the empirical result the
whole recommendation rests on. Its four parts, in the order they matter:

**1. The joint stress surface** (:func:`stress_surface`). Four axes vary together — the
diversifier's gross excess return, its correlation with the base, its volatility and the
financing spread — under a stated copula. The headline is not the mean gap; it is the
**fraction of prior mass in the region where the overlay loses to the leverage-matched
control**, reported beside the same fraction under an independence copula so a reader can
see exactly what the univariate table costs. Prior-free companions
(:func:`break_even_net_excess_return`, :func:`tolerable_financing_spread`) give the
boundary of that region in closed form, so nothing here depends on the prior being right.

**2. The flat-drawdown attack** (:func:`drawdown_ladder`, :func:`paired_drawdown_bootstrap`,
:func:`window_drawdowns`, :func:`stress_crisis_correlation`). §7 reports maximum drawdown
as **flat in the overlay weight** — -50.3% at 1.0x gross against -49.4% at 2.0x — and that
single fact is what licenses holding gross notional of 1.30x at all. It was measured on
**one path**. Maximum drawdown is a single order statistic of that path: it has no
standard error printed beside it anywhere in the synthesis, and it is the least stable
statistic in the whole exercise. The functions here resample it, cut it by crisis window,
and break the assumption it silently rests on — that trend's negative correlation to
equity survives into equity's worst months.

**3. The failure modes the plan names and this programme has not**
(:func:`forced_deleveraging`, :func:`joint_loss_frequency`, :func:`closure_hazard`,
:func:`drought_probability`, :func:`abandonment_cost`). A return-stacked fund that must cut
notional after a loss, both stacked legs losing at once, the fund closing or changing
methodology mid-hold, and five years of manager underperformance meeting an investor who
has said out loud that they will reassess at five years.

**4. What cannot be estimated, said so.** Methodology change inside a live fund has no
observable base rate in anything this repository holds, and :func:`closure_hazard` prices
closure only. Nothing here converts that into a number.

Conventions, all inherited rather than re-decided
-------------------------------------------------
* **Growth decides and the certainty equivalent reports beside it** (decision 0008). Every
  gap in this module is a growth gap in pp/yr.
* **Benchmarks never aggregate.** :class:`GapPair` carries the unlevered gap and the
  leverage-matched gap as two fields on one object precisely so that a caller can print
  both and can never add them. They answer different questions: the unlevered control asks
  what an investor who will not borrow gives up, and the leverage-matched control asks
  whether the gain is alpha or beta.
* **The minimum detectable effect is reported beside anything measured**, using Experiment
  011's definition rather than a second copy of the same formula.

What this module is not
-----------------------
It is not an optimiser: nothing here searches a weight space, and every weight, threshold
and grid is an argument with a declared default. It reads no market data — the caller
supplies return arrays — so the same construction runs on any panel with a documented
provenance, exactly as :mod:`time_series_momentum` does.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.drawdown import drawdown_summary

# Experiment 011 owns the minimum-detectable-effect definition this repository quotes.
# Importing it inverts the usual studies-below-experiments layering, and that is the
# deliberate choice: a second copy of the formula would be a second definition, and the
# repository's rule is one canonical place per fact. The import reads no market data.
from portfolio_edge.experiments.exp_011_overlay_stack import minimum_detectable_effect
from portfolio_edge.studies.overlay_growth import OverlayInputs, matched_volatility_verdict

__all__ = [
    "MONTHS_PER_YEAR",
    "AbandonmentCost",
    "ClosureHazard",
    "CrisisStress",
    "DeleveragingOutcome",
    "DrawdownRung",
    "DroughtEstimate",
    "GapPair",
    "JointLoss",
    "JointPrior",
    "LeaveOutGap",
    "PairedDrawdownInterval",
    "Scaling",
    "StressSurface",
    "WindowDrawdown",
    "abandonment_cost",
    "break_even_net_excess_return",
    "closure_hazard",
    "drawdown_ladder",
    "drought_probability",
    "forced_deleveraging",
    "gap_pair",
    "joint_loss_frequency",
    "leave_out_gaps",
    "matched_volatility_gap",
    "overlay_total_returns",
    "paired_drawdown_bootstrap",
    "sample_joint_prior",
    "stress_crisis_correlation",
    "stress_surface",
    "tolerable_financing_spread",
    "window_drawdowns",
]

MONTHS_PER_YEAR: Final = 12

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.intp]


# --------------------------------------------------------------------------------
# 1. The two gaps, never added
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GapPair:
    """The overlay's growth gain against **both** controls, carried as one object.

    ``versus_unlevered`` is the growth added over the base held at 1.0x;
    ``versus_leverage_matched`` is the growth added over the *same base levered to the
    overlay portfolio's own volatility*. They are different counterfactuals and summing
    them double-counts, which is the error ``aggregate()`` in
    :mod:`portfolio_edge.studies.outperformance_horizon` raises on. They live on one
    dataclass with two names so a caller must choose which one it is quoting.
    """

    weight: float
    versus_unlevered: float
    versus_leverage_matched: float
    portfolio_volatility: float
    portfolio_sharpe: float
    base_sharpe: float


def gap_pair(inputs: OverlayInputs, *, weight: float) -> GapPair:
    """Both controls for one set of forecasts, from :mod:`overlay_growth`'s own algebra."""
    sizing = matched_volatility_verdict(inputs, weight=weight)
    return GapPair(
        weight=weight,
        versus_unlevered=sizing.growth_gain,
        versus_leverage_matched=sizing.leverage_matched_growth_gain,
        portfolio_volatility=sizing.portfolio_volatility,
        portfolio_sharpe=sizing.portfolio_sharpe,
        base_sharpe=sizing.base_sharpe,
    )


def _portfolio_volatility(
    *, base_volatility: float, diversifier_volatility: float, correlation: float, weight: float
) -> float:
    variance = (
        base_volatility**2
        + 2.0 * weight * correlation * base_volatility * diversifier_volatility
        + weight**2 * diversifier_volatility**2
    )
    if variance <= 0.0:
        raise ValueError("portfolio variance is non-positive; the inputs are inconsistent")
    return math.sqrt(variance)


def break_even_net_excess_return(
    *,
    base_excess_return: float,
    base_volatility: float,
    diversifier_volatility: float,
    correlation: float,
    weight: float,
) -> float:
    """The smallest ``a_net`` at which the overlay ties the **leverage-matched** control.

    The leverage-matched gap is ``a_p + w a_net - sigma_total a_p / sigma_p``, and
    ``sigma_total`` does not depend on ``a_net``, so the break-even is closed form:

        a_net*  =  a_p (sigma_total / sigma_p - 1) / w.

    **This is the bar that decides, and it is strictly harder than the one §5a leads
    with.** The overlay bar of :func:`~portfolio_edge.studies.overlay_growth.
    required_net_excess_return` — ``rho sigma_p sigma_d``, negative at negative
    correlation — is the bar against *doing nothing*. This one is the bar against
    levering the base to the same risk, and it is positive at every correlation, because
    a portfolio at higher volatility must earn more merely to keep the base's Sharpe
    ratio. At zero correlation and a 30% overlay of a 12.6%-volatility sleeve on a
    15.5%-volatility base it is about 0.16%/yr rather than 0.00%.
    """
    if weight <= 0.0:
        raise ValueError(f"weight must be positive, got {weight}")
    total = _portfolio_volatility(
        base_volatility=base_volatility,
        diversifier_volatility=diversifier_volatility,
        correlation=correlation,
        weight=weight,
    )
    return base_excess_return * (total / base_volatility - 1.0) / weight


def tolerable_financing_spread(
    *,
    base_excess_return: float,
    base_volatility: float,
    diversifier_excess_return: float,
    diversifier_volatility: float,
    correlation: float,
    fee: float,
    weight: float,
) -> float:
    """How far financing may rise before the overlay loses to the leverage-matched control.

    ``a_d - phi - a_net*``. Negative means the overlay is already behind at a zero
    financing spread, so no financing market could rescue it. This is the prior-free
    statement of where the negative region is: a caller can tabulate it over a grid of
    ``a_d`` and ``rho`` and read the boundary directly, without believing any prior.
    """
    return (
        diversifier_excess_return
        - fee
        - break_even_net_excess_return(
            base_excess_return=base_excess_return,
            base_volatility=base_volatility,
            diversifier_volatility=diversifier_volatility,
            correlation=correlation,
            weight=weight,
        )
    )


# --------------------------------------------------------------------------------
# 2. The joint prior, and the surface it induces
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class JointPrior:
    """Four axes of the overlay's forecast, varying **together**.

    The marginals are deliberately plain, because the finding is about the dependence
    rather than about the tails of any one axis:

    ==========================  =====================================================
    ``a_d``                     ``Normal(excess_centre, excess_scale)``
    ``rho``                     ``Normal(correlation_centre, correlation_scale)``,
                                clipped to ``[-0.95, 0.95]``
    ``sigma_d``                 ``volatility_centre * exp(volatility_log_scale * z)``
    ``s``                       ``spread_centre * exp(spread_log_scale * z)``
    ==========================  =====================================================

    The lognormal axes are median-preserving rather than mean-preserving: the centre is
    the median, which is the number a reader would state, and the mean sits slightly
    above it. Both scale axes are one-sided in the direction that hurts and unbounded
    above, which is the correct shape for a volatility and for a borrowing cost.

    **The dependence is the whole point.** ``copula`` is the correlation matrix of the
    four standard normals behind those marginals, in the order
    ``(a_d, rho, sigma_d, s)``. The committed default :data:`ADVERSE_COPULA` encodes the
    states the red team named: a return drought arrives with a correlation that has risen
    and financing that has widened, and both arrive when volatility is high. Passing the
    identity recovers the independence case, which is what a univariate stress table
    implicitly assumes, and the difference between the two is this module's first result.
    """

    excess_centre: float
    excess_scale: float
    correlation_centre: float
    correlation_scale: float
    volatility_centre: float
    volatility_log_scale: float
    spread_centre: float
    spread_log_scale: float
    copula: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if self.excess_scale < 0.0 or self.correlation_scale < 0.0:
            raise ValueError("prior scales must be non-negative")
        if self.volatility_centre <= 0.0:
            raise ValueError(f"volatility centre must be positive, got {self.volatility_centre}")
        if self.spread_centre < 0.0:
            raise ValueError(f"spread centre must be non-negative, got {self.spread_centre}")
        matrix = np.asarray(self.copula, dtype=np.float64)
        if matrix.shape != (4, 4):
            raise ValueError(f"the copula must be 4 by 4, got shape {matrix.shape}")
        if not np.allclose(matrix, matrix.T):
            raise ValueError("the copula must be symmetric")
        if not np.allclose(np.diag(matrix), 1.0):
            raise ValueError("the copula must have unit diagonal")
        if float(np.min(np.linalg.eigvalsh(matrix))) <= 0.0:
            raise ValueError(
                "the copula is not positive definite; a dependence structure that cannot "
                "be sampled is a specification error, not a draw to discard"
            )


#: Adverse dependence, in the order ``(a_d, rho, sigma_d, s)``.
#:
#: Read the first row: the diversifier's return is **negatively** correlated with its
#: correlation to equity (a crowded unwind is a bad year *and* a co-moving one), with its
#: volatility, and with the financing spread. Rows two to four say the three bad things
#: arrive together. The magnitudes are round numbers chosen to be defensible rather than
#: measured, which is why every result computed from this matrix is reported beside the
#: same result computed from the identity.
ADVERSE_COPULA: Final[tuple[tuple[float, ...], ...]] = (
    (1.00, -0.50, -0.30, -0.40),
    (-0.50, 1.00, 0.40, 0.35),
    (-0.30, 0.40, 1.00, 0.30),
    (-0.40, 0.35, 0.30, 1.00),
)

#: The identity, i.e. what a one-parameter-at-a-time stress table assumes without saying so.
INDEPENDENT_COPULA: Final[tuple[tuple[float, ...], ...]] = tuple(
    tuple(1.0 if i == j else 0.0 for j in range(4)) for i in range(4)
)


def sample_joint_prior(
    prior: JointPrior, *, draws: int, rng: np.random.Generator
) -> dict[str, FloatArray]:
    """Draw ``(a_d, rho, sigma_d, s)`` jointly. Seeded by the caller, never internally."""
    if draws < 1:
        raise ValueError(f"draws must be at least 1, got {draws}")
    cholesky = np.linalg.cholesky(np.asarray(prior.copula, dtype=np.float64))
    latent = rng.standard_normal((draws, 4)) @ cholesky.T
    return {
        "diversifier_excess_return": prior.excess_centre + prior.excess_scale * latent[:, 0],
        "correlation": np.clip(
            prior.correlation_centre + prior.correlation_scale * latent[:, 1], -0.95, 0.95
        ),
        "diversifier_volatility": prior.volatility_centre
        * np.exp(prior.volatility_log_scale * latent[:, 2]),
        "financing_spread": prior.spread_centre * np.exp(prior.spread_log_scale * latent[:, 3]),
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class StressSurface:
    """The joint stress result. Two failure fractions, never one.

    ``probability_negative_leverage_matched`` is the headline: the share of prior mass in
    which the overlay loses to the base levered to the same volatility.
    ``probability_negative_unlevered`` answers the other question and is always the
    smaller of the two at a negatively correlated sleeve. They are not combined and there
    is no field here that averages them.
    """

    weight: float
    draws: int
    probability_negative_leverage_matched: float
    probability_negative_unlevered: float
    quantiles_leverage_matched: Mapping[str, float]
    quantiles_unlevered: Mapping[str, float]
    mean_leverage_matched: float
    conditional_shortfall: float
    """Mean leverage-matched gap over the draws where it is negative, in pp/yr terms."""
    probability_worse_than_univariate_worst: float
    """Share of mass below the worst single cell a one-at-a-time table would report."""
    univariate_worst: float
    driver_shares: Mapping[str, float]
    """Among the failing draws, the share in which each axis sits beyond its own median."""


def _quantiles(values: FloatArray, levels: Sequence[float]) -> dict[str, float]:
    computed = np.quantile(values, levels)
    return {
        f"p{level * 100:g}": float(value)
        for level, value in zip(levels, computed, strict=True)
    }


def stress_surface(
    prior: JointPrior,
    *,
    base_excess_return: float,
    base_volatility: float,
    fee: float,
    weight: float,
    draws: int,
    rng: np.random.Generator,
    quantile_levels: Sequence[float] = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.95),
) -> StressSurface:
    """The region of parameter space where the overlay is negative, and its prior mass.

    Every draw is evaluated with :func:`gap_pair`, which is
    :mod:`overlay_growth`'s own algebra rather than a second implementation of it, so the
    surface cannot disagree with §5a's arithmetic — only with its *shape*.

    ``univariate_worst`` is the worst leverage-matched gap obtainable by moving **one**
    axis to its 1st percentile while the other three sit at the prior's centre. It is the
    number a one-at-a-time table would report as its worst case, and
    ``probability_worse_than_univariate_worst`` is how much prior mass sits below it. If
    that fraction is not small, the univariate table is not conservative.
    """
    drawn = sample_joint_prior(prior, draws=draws, rng=rng)
    levered = np.empty(draws, dtype=np.float64)
    unlevered = np.empty(draws, dtype=np.float64)
    for index in range(draws):
        pair = gap_pair(
            OverlayInputs(
                base_excess_return=base_excess_return,
                base_volatility=base_volatility,
                diversifier_excess_return=float(drawn["diversifier_excess_return"][index]),
                diversifier_volatility=float(drawn["diversifier_volatility"][index]),
                correlation=float(drawn["correlation"][index]),
                financing_spread=float(drawn["financing_spread"][index]),
                fee=fee,
            ),
            weight=weight,
        )
        levered[index] = pair.versus_leverage_matched
        unlevered[index] = pair.versus_unlevered

    worst = _univariate_worst(
        prior,
        base_excess_return=base_excess_return,
        base_volatility=base_volatility,
        fee=fee,
        weight=weight,
    )
    failing = levered < 0.0
    shares: dict[str, float] = {}
    if int(failing.sum()) > 0:
        for name, values, adverse_is_high in (
            ("diversifier_excess_return", drawn["diversifier_excess_return"], False),
            ("correlation", drawn["correlation"], True),
            ("diversifier_volatility", drawn["diversifier_volatility"], True),
            ("financing_spread", drawn["financing_spread"], True),
        ):
            median = float(np.median(values))
            beyond = values > median if adverse_is_high else values < median
            shares[name] = float(np.mean(beyond[failing]))

    return StressSurface(
        weight=weight,
        draws=draws,
        probability_negative_leverage_matched=float(np.mean(failing)),
        probability_negative_unlevered=float(np.mean(unlevered < 0.0)),
        quantiles_leverage_matched=_quantiles(levered, quantile_levels),
        quantiles_unlevered=_quantiles(unlevered, quantile_levels),
        mean_leverage_matched=float(np.mean(levered)),
        conditional_shortfall=float(np.mean(levered[failing])) if failing.any() else 0.0,
        probability_worse_than_univariate_worst=float(np.mean(levered < worst)),
        univariate_worst=worst,
        driver_shares=shares,
    )


def _univariate_worst(
    prior: JointPrior,
    *,
    base_excess_return: float,
    base_volatility: float,
    fee: float,
    weight: float,
    tail: float = 0.01,
) -> float:
    """Worst leverage-matched gap from moving one axis to its own ``tail`` quantile."""
    from scipy.stats import norm  # local: the module is otherwise scipy-free

    z = float(norm.ppf(tail))
    centre = {
        "diversifier_excess_return": prior.excess_centre,
        "correlation": prior.correlation_centre,
        "diversifier_volatility": prior.volatility_centre,
        "financing_spread": prior.spread_centre,
    }
    tails = {
        "diversifier_excess_return": prior.excess_centre + prior.excess_scale * z,
        "correlation": min(0.95, prior.correlation_centre - prior.correlation_scale * z),
        "diversifier_volatility": prior.volatility_centre
        * math.exp(-prior.volatility_log_scale * z),
        "financing_spread": prior.spread_centre * math.exp(-prior.spread_log_scale * z),
    }
    worst = math.inf
    for axis, value in tails.items():
        arguments = dict(centre)
        arguments[axis] = value
        gap = gap_pair(
            OverlayInputs(
                base_excess_return=base_excess_return,
                base_volatility=base_volatility,
                fee=fee,
                **arguments,
            ),
            weight=weight,
        ).versus_leverage_matched
        worst = min(worst, gap)
    return worst


# --------------------------------------------------------------------------------
# 3. The flat-drawdown attack
# --------------------------------------------------------------------------------


def overlay_total_returns(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    cash: FloatArray,
    *,
    weight: float,
    fee: float = 0.0,
    borrow_spread: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> FloatArray:
    """One financed overlay path: ``r_base + w r_div - charges + cash``, per period.

    The base weight is **not** reduced to fund the sleeve — that is the overlay funding
    rule and the whole point. The fee is charged on the sleeve's notional and the borrow
    spread on gross notional above 1.0, both inside the path rather than as a haircut
    afterwards, so drawdown and time under water carry them.
    """
    base = np.asarray(base_excess, dtype=np.float64)
    sleeve = np.asarray(diversifier_excess, dtype=np.float64)
    funding = np.asarray(cash, dtype=np.float64)
    if base.shape != sleeve.shape or base.shape != funding.shape:
        raise ValueError("base, diversifier and cash must have the same shape")
    if base.ndim != 1:
        raise ValueError(f"returns must be one-dimensional, got shape {base.shape}")
    charge = fee * abs(weight) + borrow_spread * max(0.0, abs(weight) + 1.0 - 1.0)
    return np.asarray(
        base + weight * sleeve - charge / periods_per_year + funding, dtype=np.float64
    )


@dataclass(frozen=True, slots=True)
class DrawdownRung:
    """One overlay weight, simulated over one path."""

    weight: float
    gross_notional: float
    geometric_return: float
    volatility: float
    sharpe: float
    max_drawdown: float
    months_under_water: int


def drawdown_ladder(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    cash: FloatArray,
    *,
    weights: Sequence[float],
    fee: float = 0.0,
    borrow_spread: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> tuple[DrawdownRung, ...]:
    """§7's table, recomputed here so the attack and the claim share one implementation."""
    rungs: list[DrawdownRung] = []
    for weight in weights:
        total = overlay_total_returns(
            base_excess,
            diversifier_excess,
            cash,
            weight=weight,
            fee=fee,
            borrow_spread=borrow_spread,
            periods_per_year=periods_per_year,
        )
        excess = total - np.asarray(cash, dtype=np.float64)
        curve = np.cumprod(1.0 + total)
        summary = drawdown_summary(curve)
        volatility = float(np.std(excess, ddof=1)) * math.sqrt(periods_per_year)
        rungs.append(
            DrawdownRung(
                weight=float(weight),
                gross_notional=1.0 + abs(float(weight)),
                geometric_return=float(curve[-1]) ** (periods_per_year / total.size) - 1.0,
                volatility=volatility,
                sharpe=float(np.mean(excess)) * periods_per_year / volatility,
                max_drawdown=summary.max_drawdown,
                months_under_water=summary.max_time_under_water,
            )
        )
    return tuple(rungs)


@dataclass(frozen=True, slots=True, kw_only=True)
class PairedDrawdownInterval:
    """The resampled distribution of ``mdd(w) - mdd(0)`` on **paired** resamples.

    Maximum drawdown is one order statistic of one path, so the point estimate in §7 has
    no error bar anywhere in the synthesis. The rows are drawn jointly, so the difference
    is the same investor's two portfolios on the same resampled history rather than two
    independent histories.

    ``probability_deeper`` is the share of resamples in which the overlay's drawdown is
    **worse** than the unlevered base's. A flat-drawdown claim needs this to be small;
    at one half the observed flatness is a coin flip that happened to land the right way.
    """

    weight: float
    resamples: int
    block_length: float
    observed_difference: float
    mean_difference: float
    interval: tuple[float, float]
    probability_deeper: float
    quantiles: Mapping[str, float]


def _circular_blocks(
    n_observations: int, block_length: int, n_resamples: int, rng: np.random.Generator
) -> IntArray:
    """Fixed-length circular blocks. Local rather than imported because the drawdown
    resample needs whole contiguous blocks of a *path*, and the stationary bootstrap's
    geometric lengths add resampling variance to an order statistic that already has too
    much of it."""
    if block_length < 1:
        raise ValueError(f"block_length must be at least 1, got {block_length}")
    blocks = math.ceil(n_observations / block_length)
    starts = rng.integers(0, n_observations, size=(n_resamples, blocks))
    offsets = np.arange(block_length, dtype=np.intp)
    drawn = (starts[:, :, None] + offsets[None, None, :]) % n_observations
    return np.asarray(drawn.reshape(n_resamples, -1)[:, :n_observations], dtype=np.intp)


def paired_drawdown_bootstrap(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    cash: FloatArray,
    *,
    weight: float,
    resamples: int,
    block_length: int,
    rng: np.random.Generator,
    fee: float = 0.0,
    borrow_spread: float = 0.0,
    confidence_level: float = 0.95,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> PairedDrawdownInterval:
    """Block-bootstrap ``mdd(w) - mdd(0)``, resampling the two arms together."""
    base = np.asarray(base_excess, dtype=np.float64)
    overlay = overlay_total_returns(
        base_excess,
        diversifier_excess,
        cash,
        weight=weight,
        fee=fee,
        borrow_spread=borrow_spread,
        periods_per_year=periods_per_year,
    )
    control = overlay_total_returns(
        base_excess,
        diversifier_excess,
        cash,
        weight=0.0,
        periods_per_year=periods_per_year,
    )
    observed = (
        drawdown_summary(np.cumprod(1.0 + overlay)).max_drawdown
        - drawdown_summary(np.cumprod(1.0 + control)).max_drawdown
    )

    indices = _circular_blocks(base.size, block_length, resamples, rng)
    differences = np.empty(resamples, dtype=np.float64)
    for row in range(resamples):
        take = indices[row]
        a = drawdown_summary(np.cumprod(1.0 + overlay[take])).max_drawdown
        b = drawdown_summary(np.cumprod(1.0 + control[take])).max_drawdown
        differences[row] = a - b
    tail = (1.0 - confidence_level) / 2.0
    low, high = np.quantile(differences, [tail, 1.0 - tail])
    return PairedDrawdownInterval(
        weight=weight,
        resamples=resamples,
        block_length=float(block_length),
        observed_difference=observed,
        mean_difference=float(np.mean(differences)),
        interval=(float(low), float(high)),
        probability_deeper=float(np.mean(differences < 0.0)),
        quantiles=_quantiles(differences, (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99)),
    )


@dataclass(frozen=True, slots=True)
class WindowDrawdown:
    """One named crisis window, one overlay weight."""

    window: str
    months: int
    weight: float
    peak_to_trough: float
    total_return: float


def window_drawdowns(
    periods: Sequence[str],
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    cash: FloatArray,
    *,
    windows: Mapping[str, tuple[str, str]],
    weights: Sequence[float],
    fee: float = 0.0,
    borrow_spread: float = 0.0,
) -> tuple[WindowDrawdown, ...]:
    """Peak-to-trough inside each named window, per weight.

    A window that lies wholly outside ``periods`` is **skipped rather than truncated**,
    and the caller is expected to say which ones were skipped: a crisis the panel does
    not cover is the most important thing a stress test can report, and silently
    returning the drawdown of a shorter window would hide it.
    """
    labels = list(periods)
    rows: list[WindowDrawdown] = []
    for name, (start, end) in windows.items():
        keep = [i for i, period in enumerate(labels) if start <= period <= end]
        if not keep:
            continue
        take = np.asarray(keep, dtype=np.intp)
        for weight in weights:
            total = overlay_total_returns(
                np.asarray(base_excess)[take],
                np.asarray(diversifier_excess)[take],
                np.asarray(cash)[take],
                weight=weight,
                fee=fee,
                borrow_spread=borrow_spread,
            )
            curve = np.cumprod(1.0 + total)
            rows.append(
                WindowDrawdown(
                    window=name,
                    months=len(keep),
                    weight=float(weight),
                    peak_to_trough=drawdown_summary(curve).max_drawdown,
                    total_return=float(curve[-1]) - 1.0,
                )
            )
    return tuple(rows)


@dataclass(frozen=True, slots=True, kw_only=True)
class CrisisStress:
    """A diversifier whose correlation is forced positive **in equity drawdowns only**."""

    target_correlation: float
    crisis_months: int
    crisis_correlation_before: float
    crisis_correlation_after: float
    full_sample_correlation_after: float
    crisis_mean_before: float
    crisis_mean_after: float
    stressed: FloatArray


def stress_crisis_correlation(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    *,
    target_correlation: float,
    drawdown_threshold: float = 0.0,
    crisis_mean: float | None = None,
) -> CrisisStress:
    """Rotate the diversifier toward the base **inside equity drawdowns**, nothing else.

    Crisis months are those in which the base's own wealth path sits at least
    ``drawdown_threshold`` below its running peak. Inside them the diversifier is replaced
    by a rotation that sets the correlation to **exactly** ``target_correlation`` while
    preserving the crisis-window mean and standard deviation of the diversifier:

        u = (d_hat - c e_hat) / sqrt(1 - c**2),   d' = mu_d + sigma_d (a e_hat + sqrt(1 - a**2) u)

    with ``e_hat`` and ``d_hat`` the standardised crisis-window series, ``c`` their sample
    correlation and ``a`` the target. Outside crisis months nothing changes.

    **This is the assumption §5a never varies.** §5a raises the correlation everywhere and
    finds the overlay survives. Raising it only where equity is losing is a different and
    much more hostile stress, because that is where the drawdown is set — and the drawdown
    is what §7's recommendation rests on. ``crisis_mean``, if given, additionally forces
    the diversifier's crisis-window mean, which is how the plan's "simultaneous loss in
    both sides of a return stack" is expressed: set it to zero or below and the sleeve
    stops paying exactly when it is needed.
    """
    base = np.asarray(base_excess, dtype=np.float64)
    sleeve = np.asarray(diversifier_excess, dtype=np.float64)
    if base.shape != sleeve.shape or base.ndim != 1:
        raise ValueError("base and diversifier must be one-dimensional and the same length")
    if not -1.0 <= target_correlation <= 1.0:
        raise ValueError(f"target correlation must lie in [-1, 1], got {target_correlation}")
    if drawdown_threshold < 0.0:
        raise ValueError("drawdown_threshold is a depth and must be non-negative")

    curve = np.cumprod(1.0 + base)
    peak = np.maximum.accumulate(curve)
    in_crisis = curve / peak - 1.0 <= -drawdown_threshold
    count = int(in_crisis.sum())
    if count < 3:
        raise ValueError(
            f"only {count} crisis months at a {drawdown_threshold:.0%} threshold; a "
            "conditional correlation cannot be set on fewer than three observations"
        )

    e = base[in_crisis]
    d = sleeve[in_crisis]
    e_mean, e_sd = float(np.mean(e)), float(np.std(e, ddof=1))
    d_mean, d_sd = float(np.mean(d)), float(np.std(d, ddof=1))
    if e_sd <= 0.0 or d_sd <= 0.0:
        raise ValueError("a crisis window with zero variance cannot be rotated")
    e_hat = (e - e_mean) / e_sd
    d_hat = (d - d_mean) / d_sd
    before = float(np.corrcoef(e_hat, d_hat)[0, 1])
    residual = d_hat - before * e_hat
    residual_sd = float(np.std(residual, ddof=1))
    if residual_sd <= 0.0:
        raise ValueError("the diversifier is collinear with the base inside the crisis window")
    u = residual / residual_sd
    a = target_correlation
    rotated = a * e_hat + math.sqrt(max(0.0, 1.0 - a * a)) * u

    target_mean = d_mean if crisis_mean is None else crisis_mean
    out = sleeve.copy()
    out[in_crisis] = target_mean + d_sd * rotated
    return CrisisStress(
        target_correlation=a,
        crisis_months=count,
        crisis_correlation_before=before,
        crisis_correlation_after=float(np.corrcoef(e, out[in_crisis])[0, 1]),
        full_sample_correlation_after=float(np.corrcoef(base, out)[0, 1]),
        crisis_mean_before=d_mean,
        crisis_mean_after=float(np.mean(out[in_crisis])),
        stressed=out,
    )


# --------------------------------------------------------------------------------
# 4. The failure modes the plan names
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleveragingOutcome:
    """A return-stacked fund that must cut notional after a loss, and cannot re-add early."""

    weight: float
    trigger: float
    reduced_weight: float
    restore_fraction: float
    months_deleveraged: int
    geometric_return: float
    max_drawdown: float
    months_under_water: int
    geometric_cost_versus_unconstrained: float
    drawdown_change_versus_unconstrained: float


def forced_deleveraging(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    cash: FloatArray,
    *,
    weight: float,
    trigger: float,
    reduced_weight: float = 0.0,
    restore_fraction: float = 1.0,
    fee: float = 0.0,
    borrow_spread: float = 0.0,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> DeleveragingOutcome:
    """Cut the overlay when the fund's own NAV falls ``trigger`` below its peak.

    The mechanism this prices is not a margin call on the investor — a return-stacked ETF
    cannot margin-call its holders — but the fund's own risk control, which is the same
    arithmetic seen from inside: notional is cut *after* the loss and restored only once
    wealth has recovered to ``restore_fraction`` of the prior peak, so the sleeve is
    absent for exactly the part of the path where it would have paid. The state variable
    is the **stacked fund's** drawdown, so the constraint is endogenous: cutting the
    overlay changes the path that decides when it is cut back.

    ``restore_fraction = 1.0`` means the overlay comes back only at a new high water mark.
    That is deliberately harsh and it is what a drawdown-control mandate actually says.
    """
    base = np.asarray(base_excess, dtype=np.float64)
    sleeve = np.asarray(diversifier_excess, dtype=np.float64)
    funding = np.asarray(cash, dtype=np.float64)
    if not 0.0 < trigger < 1.0:
        raise ValueError(f"trigger must lie strictly inside (0, 1), got {trigger}")
    if restore_fraction <= 0.0:
        raise ValueError(f"restore_fraction must be positive, got {restore_fraction}")

    full_charge = fee * abs(weight) + borrow_spread * abs(weight)
    cut_charge = fee * abs(reduced_weight) + borrow_spread * abs(reduced_weight)

    wealth = 1.0
    peak = 1.0
    deleveraged = False
    months = 0
    path = np.empty(base.size, dtype=np.float64)
    for t in range(base.size):
        if deleveraged and wealth >= restore_fraction * peak:
            deleveraged = False
        if not deleveraged and wealth / peak - 1.0 <= -trigger:
            deleveraged = True
        active, charge = (
            (reduced_weight, cut_charge) if deleveraged else (weight, full_charge)
        )
        months += int(deleveraged)
        step = base[t] + active * sleeve[t] - charge / periods_per_year + funding[t]
        path[t] = step
        wealth *= 1.0 + step
        peak = max(peak, wealth)

    curve = np.cumprod(1.0 + path)
    summary = drawdown_summary(curve)
    unconstrained = overlay_total_returns(
        base,
        sleeve,
        funding,
        weight=weight,
        fee=fee,
        borrow_spread=borrow_spread,
        periods_per_year=periods_per_year,
    )
    free_curve = np.cumprod(1.0 + unconstrained)
    free_growth = float(free_curve[-1]) ** (periods_per_year / path.size) - 1.0
    free_drawdown = drawdown_summary(free_curve).max_drawdown
    growth = float(curve[-1]) ** (periods_per_year / path.size) - 1.0
    return DeleveragingOutcome(
        weight=weight,
        trigger=trigger,
        reduced_weight=reduced_weight,
        restore_fraction=restore_fraction,
        months_deleveraged=months,
        geometric_return=growth,
        max_drawdown=summary.max_drawdown,
        months_under_water=summary.max_time_under_water,
        geometric_cost_versus_unconstrained=growth - free_growth,
        drawdown_change_versus_unconstrained=summary.max_drawdown - free_drawdown,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class JointLoss:
    """How often both stacked legs lose in the same month, against two null models."""

    months: int
    probability_base_loses: float
    probability_diversifier_loses: float
    probability_both_lose: float
    independence_benchmark: float
    gaussian_benchmark: float
    lift_over_independence: float
    worst_joint_month: float
    """The most negative sum of the two legs' returns in any single month."""
    probability_both_lose_given_base_tail: float
    base_tail_quantile: float


def joint_loss_frequency(
    base_excess: FloatArray,
    diversifier_excess: FloatArray,
    *,
    base_tail_quantile: float = 0.10,
) -> JointLoss:
    """Measured joint-loss frequency, beside independence and beside a Gaussian copula.

    The Gaussian benchmark uses the two series' sample correlation and asks what a joint
    normal with that correlation would predict; the gap between it and the measured figure
    is tail dependence the correlation does not carry. **A correlation of -0.07 does not
    mean the legs never lose together**, and the number a reader needs before holding
    1.30x gross notional is the joint frequency rather than the correlation.
    """
    # Imported locally: the module is otherwise scipy-free and this is its only user.
    from scipy.stats import multivariate_normal, norm

    base = np.asarray(base_excess, dtype=np.float64)
    sleeve = np.asarray(diversifier_excess, dtype=np.float64)
    if base.shape != sleeve.shape or base.ndim != 1:
        raise ValueError("base and diversifier must be one-dimensional and the same length")
    p_base = float(np.mean(base < 0.0))
    p_sleeve = float(np.mean(sleeve < 0.0))
    both = float(np.mean((base < 0.0) & (sleeve < 0.0)))
    correlation = float(np.corrcoef(base, sleeve)[0, 1])
    thresholds = [
        float(norm.ppf(p_base)) if 0.0 < p_base < 1.0 else 0.0,
        float(norm.ppf(p_sleeve)) if 0.0 < p_sleeve < 1.0 else 0.0,
    ]
    gaussian = float(
        multivariate_normal(mean=[0.0, 0.0], cov=[[1.0, correlation], [correlation, 1.0]]).cdf(
            thresholds
        )
    )
    cut = float(np.quantile(base, base_tail_quantile))
    tail = base <= cut
    conditional = float(np.mean(sleeve[tail] < 0.0)) if tail.any() else float("nan")
    return JointLoss(
        months=int(base.size),
        probability_base_loses=p_base,
        probability_diversifier_loses=p_sleeve,
        probability_both_lose=both,
        independence_benchmark=p_base * p_sleeve,
        gaussian_benchmark=gaussian,
        lift_over_independence=(
            both / (p_base * p_sleeve) if p_base * p_sleeve > 0.0 else float("nan")
        ),
        worst_joint_month=float(np.min(base + sleeve)),
        probability_both_lose_given_base_tail=conditional,
        base_tail_quantile=base_tail_quantile,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ClosureHazard:
    """A per-year closure hazard estimated from an observed cohort, with its interval."""

    cohort: int
    deaths: int
    years_observed: float
    annual_hazard: float
    annual_hazard_interval: tuple[float, float]
    probability_of_closure_within_hold: float
    probability_interval_within_hold: tuple[float, float]
    hold_years: float


def _clopper_pearson(deaths: int, cohort: int, confidence_level: float) -> tuple[float, float]:
    from scipy.stats import beta  # local: the module is otherwise scipy-free

    tail = (1.0 - confidence_level) / 2.0
    low = 0.0 if deaths == 0 else float(beta.ppf(tail, deaths, cohort - deaths + 1))
    high = 1.0 if deaths == cohort else float(beta.ppf(1.0 - tail, deaths + 1, cohort - deaths))
    return low, high


def closure_hazard(
    *,
    cohort: int,
    deaths: int,
    years_observed: float,
    hold_years: float,
    confidence_level: float = 0.95,
) -> ClosureHazard:
    """Constant-hazard closure risk from ``deaths`` of a ``cohort`` over ``years_observed``.

    ``h = 1 - (1 - deaths/cohort)**(1/years)``, with a Clopper-Pearson interval on the
    cohort proportion carried through the same transform. The constant-hazard assumption
    is the weak part and it is stated rather than hidden: fund mortality is
    front-loaded — a young fund that has not gathered assets dies faster than an
    established one — so a constant rate **understates** the risk in the first years of a
    holding and overstates it later.

    This prices **closure only**. A fund that stays open and changes its methodology,
    its leverage target or its sub-adviser produces no observable event in any census
    this repository holds, so no hazard for that is estimated here and none should be
    inferred from this number.
    """
    if cohort < 1 or not 0 <= deaths <= cohort:
        raise ValueError(f"need 0 <= deaths <= cohort and cohort >= 1, got {deaths}/{cohort}")
    if years_observed <= 0.0 or hold_years <= 0.0:
        raise ValueError("years_observed and hold_years must be positive")
    proportion = deaths / cohort
    low, high = _clopper_pearson(deaths, cohort, confidence_level)

    def hazard(p: float) -> float:
        return float(1.0 - (1.0 - p) ** (1.0 / years_observed))

    def survival(p: float) -> float:
        return float(1.0 - (1.0 - hazard(p)) ** hold_years)

    return ClosureHazard(
        cohort=cohort,
        deaths=deaths,
        years_observed=years_observed,
        annual_hazard=hazard(proportion),
        annual_hazard_interval=(hazard(low), hazard(high)),
        probability_of_closure_within_hold=survival(proportion),
        probability_interval_within_hold=(survival(low), survival(high)),
        hold_years=hold_years,
    )


Scaling = Literal["leverage_matched", "unlevered"]


def _paired_difference(
    portfolio: FloatArray, benchmark: FloatArray, *, scaling: Scaling
) -> FloatArray:
    """The monthly series whose annualised mean is the gap against ``scaling``'s control.

    ``leverage_matched`` scales the benchmark to the portfolio's own volatility first, so
    the mean is ``sigma_p (S_p - S_b)`` exactly. ``unlevered`` subtracts the benchmark as
    held. **The two are different claims and this function will not average them**; the
    scaling is a required keyword so no caller can get one by accident while quoting the
    other.

    A consequence worth stating because it caught this module out: the leverage-matched
    difference is *invariant to any constant rescaling of the benchmark*, so passing the
    unlevered equity series and passing that series levered 1.35x give the identical
    number. They are one observation, not two.
    """
    sigma_b = float(np.std(benchmark, ddof=1))
    if sigma_b <= 0.0:
        raise ValueError("the benchmark has zero volatility; no scaling exists")
    if scaling == "leverage_matched":
        ratio = float(np.std(portfolio, ddof=1)) / sigma_b
        return np.asarray(portfolio - ratio * benchmark, dtype=np.float64)
    return np.asarray(portfolio - benchmark, dtype=np.float64)


def matched_volatility_gap(
    portfolio_excess: FloatArray,
    benchmark_excess: FloatArray,
    *,
    scaling: Scaling,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> tuple[float, float]:
    """``(gap, minimum detectable effect)`` in the same units, both annualised.

    Returned as a pair because the repository's rule is that the resolution floor is
    reported beside the estimate, and a function that returns only the estimate makes
    forgetting the floor the path of least resistance.
    """
    difference = _paired_difference(
        np.asarray(portfolio_excess, dtype=np.float64),
        np.asarray(benchmark_excess, dtype=np.float64),
        scaling=scaling,
    )
    return float(np.mean(difference)) * periods_per_year, minimum_detectable_effect(difference)


@dataclass(frozen=True, slots=True, kw_only=True)
class LeaveOutGap:
    """The gap with one named slice of history removed."""

    removed: str
    months_removed: int
    gap: float
    change_from_full_sample: float
    scaling: str


def leave_out_gaps(
    portfolio_excess: FloatArray,
    benchmark_excess: FloatArray,
    *,
    scaling: Scaling,
    groups: Mapping[str, Sequence[int]],
    periods_per_year: int = MONTHS_PER_YEAR,
) -> tuple[LeaveOutGap, ...]:
    """The charter's "test removing" clause, on the gap that decides.

    Each group is a set of row indices dropped before the gap is recomputed. Dropping the
    strongest crisis is the one that matters: a diversifier whose entire case is two good
    months is a diversifier whose case is two good months, and only this test says so.
    """
    portfolio = np.asarray(portfolio_excess, dtype=np.float64)
    control = np.asarray(benchmark_excess, dtype=np.float64)
    full = float(np.mean(_paired_difference(portfolio, control, scaling=scaling)))
    full *= periods_per_year
    rows: list[LeaveOutGap] = []
    for name, indices in groups.items():
        keep = np.ones(portfolio.size, dtype=bool)
        keep[np.asarray(list(indices), dtype=np.intp)] = False
        if int(keep.sum()) < 24:
            continue
        gap = (
            float(
                np.mean(_paired_difference(portfolio[keep], control[keep], scaling=scaling))
            )
            * periods_per_year
        )
        rows.append(
            LeaveOutGap(
                removed=name,
                months_removed=int(portfolio.size - keep.sum()),
                gap=gap,
                change_from_full_sample=gap - full,
                scaling=scaling,
            )
        )
    return tuple(rows)


@dataclass(frozen=True, slots=True, kw_only=True)
class DroughtEstimate:
    """How often a five-year window leaves the investor behind the control they chose."""

    horizon_months: int
    windows: int
    probability_negative_gap: float
    median_gap: float
    worst_gap: float
    scaling: str
    minimum_detectable_effect: float
    resamples: int
    block_length: float


def drought_probability(
    portfolio_excess: FloatArray,
    benchmark_excess: FloatArray,
    *,
    scaling: Scaling,
    horizon_months: int,
    resamples: int,
    block_length: int,
    rng: np.random.Generator,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> DroughtEstimate:
    """Probability that the realised gap over ``horizon_months`` is negative.

    Each resample draws ``horizon_months`` of **paired** history in circular blocks and
    computes the gap on that window under the requested ``scaling``. The result answers
    the question an investor with a five-year review actually asks: not "is the edge real"
    but "how often does five years of it look like a mistake".

    ``scaling`` is carried onto the result because a gap against the unlevered control and
    a gap against the leverage-matched control are different claims and this repository
    has already added two such numbers together once.
    """
    portfolio = np.asarray(portfolio_excess, dtype=np.float64)
    control = np.asarray(benchmark_excess, dtype=np.float64)
    if portfolio.shape != control.shape or portfolio.ndim != 1:
        raise ValueError("portfolio and benchmark must be one-dimensional and the same length")
    if horizon_months < 2 or horizon_months > portfolio.size:
        raise ValueError(f"horizon_months must lie in [2, {portfolio.size}], got {horizon_months}")

    indices = _circular_blocks(portfolio.size, block_length, resamples, rng)[:, :horizon_months]
    drawn_p = portfolio[indices]
    drawn_b = control[indices]
    if scaling == "leverage_matched":
        ratio = np.std(drawn_p, ddof=1, axis=1) / np.std(drawn_b, ddof=1, axis=1)
        differences = drawn_p - ratio[:, None] * drawn_b
    else:
        differences = drawn_p - drawn_b
    gaps = np.mean(differences, axis=1) * periods_per_year

    difference = _paired_difference(portfolio, control, scaling=scaling)
    return DroughtEstimate(
        horizon_months=horizon_months,
        windows=resamples,
        probability_negative_gap=float(np.mean(gaps < 0.0)),
        median_gap=float(np.median(gaps)),
        worst_gap=float(np.min(gaps)),
        scaling=scaling,
        minimum_detectable_effect=minimum_detectable_effect(difference[:horizon_months]),
        resamples=resamples,
        block_length=float(block_length),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class AbandonmentCost:
    """What quitting at the review date costs, given that the review date is arbitrary."""

    review_years: int
    windows: int
    probability_review_shows_a_loss: float
    mean_subsequent_gap_after_a_bad_review: float
    mean_subsequent_gap_after_a_good_review: float
    subsequent_years: int
    minimum_detectable_effect: float
    scaling: str


def abandonment_cost(
    portfolio_excess: FloatArray,
    benchmark_excess: FloatArray,
    *,
    scaling: Scaling,
    review_years: int,
    subsequent_years: int,
    periods_per_year: int = MONTHS_PER_YEAR,
) -> AbandonmentCost:
    """Does a bad five-year review predict a bad next five years, on this record?

    Every overlapping ``review_years`` window is scored by its matched-volatility gap, and
    the *following* ``subsequent_years`` are scored the same way. If the two are
    unrelated, a five-year review is a coin flip dressed as a decision and the investor's
    stated intent to reassess at five years is a plan to sell after bad luck.

    The windows overlap heavily, so the two conditional means are **not** independent
    observations and no interval is offered for their difference. What the function
    supports is a sign and a magnitude, and the minimum detectable effect on the full
    monthly paired difference is reported beside them as the resolution floor.
    """
    portfolio = np.asarray(portfolio_excess, dtype=np.float64)
    control = np.asarray(benchmark_excess, dtype=np.float64)
    review = review_years * periods_per_year
    ahead = subsequent_years * periods_per_year
    if portfolio.size < review + ahead:
        raise ValueError(
            f"need at least {review + ahead} observations, got {portfolio.size}"
        )

    def gap(start: int, length: int) -> float:
        window = slice(start, start + length)
        return (
            float(
                np.mean(
                    _paired_difference(portfolio[window], control[window], scaling=scaling)
                )
            )
            * periods_per_year
        )

    starts = range(portfolio.size - review - ahead + 1)
    scored = [(gap(s, review), gap(s + review, ahead)) for s in starts]
    bad = [after for before, after in scored if before < 0.0]
    good = [after for before, after in scored if before >= 0.0]
    difference = _paired_difference(portfolio, control, scaling=scaling)
    return AbandonmentCost(
        review_years=review_years,
        windows=len(scored),
        probability_review_shows_a_loss=len(bad) / len(scored),
        mean_subsequent_gap_after_a_bad_review=float(np.mean(bad)) if bad else float("nan"),
        mean_subsequent_gap_after_a_good_review=float(np.mean(good)) if good else float("nan"),
        subsequent_years=subsequent_years,
        minimum_detectable_effect=minimum_detectable_effect(difference),
        scaling=scaling,
    )


if __name__ == "__main__":  # pragma: no cover - regenerates the published stress tables
    from portfolio_edge.studies._overlay_stress_tables import main

    main()
