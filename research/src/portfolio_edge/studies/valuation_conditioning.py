"""Whether a valuation level should change an allocation, and what would show it.

Why this module exists
----------------------
An investor's stated concern is that a US CAPE above 40 is a fact about the future that
an allocation must respond to. That sentence bundles three different claims, and they
have different evidence:

1. **A return forecast.** "High CAPE means low subsequent returns, so shift out of
   equity now."
2. **A risk and regret statement.** "High CAPE means a wider left tail and a longer
   time spent underwater, so a given equity share is harder to hold."
3. **A relative statement.** "US equity is expensive *relative to* non-US equity, so the
   regional split should move." This is a cross-sectional estimand and is not the same
   object as (1).

This module holds the arithmetic and the estimators that decide between them. It reads
no market data; :mod:`portfolio_edge.studies._valuation_conditioning_tables` is the
companion that touches the cache and regenerates every measured figure in
``docs/research/valuation-and-the-allocation.md``.

The one methodological point that decides the answer
----------------------------------------------------
Long-horizon predictive regressions are run on **overlapping** windows. A 145-year
monthly sample yields 1,628 observations of the ten-year-ahead return and about
**13.6 independent** ones. Newey-West standard errors with a lag equal to the horizon
are known to be badly undersized in exactly this design, and here they say so out loud:
on the same regression they report a ``t`` near 4.8 where :func:`hodrick_1b_covariance`
reports 2.5. Neither number is a typo. The gap *is* the finding, and any page quoting the
Newey-West figure alone is quoting an artifact of the estimator.

:func:`overlap_adjusted_observations` exists so that a caller cannot report an ``R**2``
without also reporting how many independent observations produced it.

The second point that decides the answer
-----------------------------------------
The predictor is a valuation ratio, so its innovation is almost exactly the negative of
the return innovation: the price is in the numerator of one and the denominator of the
other. On this repository's own Shiller series the correlation between the one-month
return residual and the CAPE-yield residual is **-0.9975** and the predictor's monthly
autoregressive root is **0.9966**. Those are the two ingredients of the Stambaugh (1999)
bias, and at those values :func:`stambaugh_bias` returns a bias worth about
three-quarters of the fitted slope. A predictive slope from this family of regressors
that is quoted without a bias correction is quoted at roughly four times its corrected
size.

What this module is not
-----------------------
It is arithmetic and inference over supplied inputs. It forecasts no market, and none of
its functions accepts a "current CAPE" and returns a recommended weight. The decision
argument lives in the synthesis; what lives here is the machinery that keeps the
argument honest about its own resolution.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core._types import FloatArray

__all__ = [
    "MONTHS_PER_YEAR",
    "ConditionalWeightRule",
    "HodrickResult",
    "OutOfSampleScore",
    "TiltCost",
    "break_even_tax_rate",
    "conditional_weight",
    "derisking_regret_bp",
    "excess_cape_yield",
    "hodrick_1b_covariance",
    "out_of_sample_r2",
    "overlap_adjusted_observations",
    "rescale_cape_for_price",
    "stambaugh_bias",
    "tilt_net_edge_bp",
]

MONTHS_PER_YEAR: Final = 12


# --------------------------------------------------------------------------------------
# Resolution: how many observations are actually there
# --------------------------------------------------------------------------------------


def overlap_adjusted_observations(n_observations: int, horizon_periods: int) -> float:
    """Independent observations behind an overlapping long-horizon regression.

    ``n / h``. Crude, and deliberately so: it is the count of non-overlapping windows the
    sample contains, which is the quantity a reader needs beside an ``R**2`` computed on
    overlapping data. A 145-year monthly sample has 1,628 ten-year observations and about
    13.6 independent ones, and no estimator recovers information the sample does not hold.
    """
    if n_observations <= 0:
        raise ValueError(f"n_observations must be positive, got {n_observations}")
    if horizon_periods <= 0:
        raise ValueError(f"horizon_periods must be positive, got {horizon_periods}")
    return n_observations / horizon_periods


@dataclass(frozen=True)
class HodrickResult:
    """A long-horizon slope with Hodrick (1992) 1B standard errors.

    Attributes:
        coefficients: ``[intercept, slope]`` from ordinary least squares. Hodrick 1B
            changes the covariance, never the point estimate.
        standard_errors: The 1B standard errors, in the same order.
        t_statistics: ``coefficients / standard_errors``.
        n_observations: Rows in the regression, overlapping.
        independent_observations: :func:`overlap_adjusted_observations`.
        horizon_periods: The overlap length, in the sampling period of the data.
    """

    coefficients: FloatArray
    standard_errors: FloatArray
    t_statistics: FloatArray
    n_observations: int
    independent_observations: float
    horizon_periods: int


def hodrick_1b_covariance(
    y: NDArray[np.floating] | Sequence[float],
    x: NDArray[np.floating] | Sequence[float],
    *,
    horizon_periods: int,
    one_period_residuals: NDArray[np.floating] | Sequence[float],
) -> HodrickResult:
    """Hodrick (1992) 1B inference for an overlapping long-horizon regression.

    Newey-West sums the *residuals* forward over the overlap, which is where its
    small-sample failure comes from: at a 120-month overlap the estimator is asked for
    120 autocovariances from about 13 independent windows. Hodrick's 1B sums the
    **regressors backward** instead and takes the one-period residual, so the number of
    quantities estimated does not grow with the horizon.

    Under the null of no predictability the one-period residual is just the demeaned
    one-period return, and that is what ``one_period_residuals`` should carry: element
    ``k`` is the one-period return from ``k`` to ``k+1``, demeaned, and scaled the same
    way ``y`` is (so if ``y`` is annualised, divide by the horizon in years). The
    resulting statistic is a test of that null, which is the question being asked.

    The covariance is ``(1/T) (Z'Z/T)^-1 S (Z'Z/T)^-1`` with
    ``S = (1/T') sum_t W_t W_t' e_{t+1}**2`` and
    ``W_t = sum_{j=0}^{h-1} z_{t-j}``, where ``z_t = [1, x_t]'``.

    At ``horizon_periods = 1`` this is White's heteroskedasticity-robust covariance, which
    is the check that the implementation is not doing something horizon-specific.

    Args:
        y: The long-horizon response, one row per forecast origin, chronological.
        x: The single predictor at the forecast origin. Chronological, same length.
        horizon_periods: Overlap length ``h``, in periods of the data.
        one_period_residuals: One-period residuals under the null, same length as ``y``.

    Raises:
        ValueError: On a length mismatch, a non-positive horizon, a horizon that does not
            fit the sample, or a non-finite input.
    """
    response = np.asarray(y, dtype=np.float64)
    predictor = np.asarray(x, dtype=np.float64)
    residuals = np.asarray(one_period_residuals, dtype=np.float64)
    if response.ndim != 1 or predictor.ndim != 1 or residuals.ndim != 1:
        raise ValueError("y, x and one_period_residuals must each be one-dimensional")
    if not (response.size == predictor.size == residuals.size):
        raise ValueError(
            f"length mismatch: y={response.size}, x={predictor.size}, "
            f"one_period_residuals={residuals.size}"
        )
    if horizon_periods <= 0:
        raise ValueError(f"horizon_periods must be positive, got {horizon_periods}")
    if horizon_periods > response.size:
        raise ValueError(
            f"horizon_periods {horizon_periods} exceeds the sample of {response.size}"
        )
    for name, array in (("y", response), ("x", predictor), ("one_period_residuals", residuals)):
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} contains non-finite values")

    n = response.size
    design = np.column_stack([np.ones(n), predictor])
    moment = design.T @ design / n
    moment_inv = np.linalg.inv(moment)
    beta = moment_inv @ (design.T @ response / n)

    # W_t = sum of the last `horizon_periods` regressor rows, ending at t.
    cumulative = np.cumsum(design, axis=0)
    summed = np.empty_like(design)
    summed[horizon_periods - 1 :] = cumulative[horizon_periods - 1 :] - np.vstack(
        [np.zeros((1, design.shape[1])), cumulative[:-horizon_periods]]
    )
    usable = summed[horizon_periods - 1 :] * residuals[horizon_periods - 1 :, None]
    spectral = usable.T @ usable / usable.shape[0]

    covariance = moment_inv @ spectral @ moment_inv / n
    covariance = 0.5 * (covariance + covariance.T)
    errors = np.sqrt(np.clip(np.diag(covariance), 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_stats = np.where(errors > 0.0, beta / errors, np.nan)
    return HodrickResult(
        coefficients=beta,
        standard_errors=errors,
        t_statistics=t_stats,
        n_observations=n,
        independent_observations=overlap_adjusted_observations(n, horizon_periods),
        horizon_periods=horizon_periods,
    )


def stambaugh_bias(
    *,
    innovation_covariance: float,
    predictor_innovation_variance: float,
    autoregressive_root: float,
    n_observations: int,
) -> float:
    """Stambaugh (1999) small-sample bias of a predictive slope.

    ``E[b_hat - b] = -(sigma_uv / sigma_v**2) * (1 + 3 phi) / T``.

    The bias comes from two facts holding at once: the predictor is persistent, so its own
    autoregressive coefficient is estimated downward; and the predictor's innovation is
    correlated with the return innovation, so that downward bias transmits to the
    predictive slope. For a valuation ratio both conditions hold as strongly as they can.
    Price is in the denominator of the ratio and in the return, so ``sigma_uv`` is large
    and negative, and the ratio's root is close to one. The bias is therefore large and
    **positive**: the uncorrected slope overstates predictability.

    Sign convention: subtract the returned value from the fitted slope to correct it.

    Raises:
        ValueError: On a non-positive innovation variance or sample size, or a root at or
            beyond the unit circle, where the expansion does not apply.
    """
    if predictor_innovation_variance <= 0.0:
        raise ValueError("predictor_innovation_variance must be positive")
    if n_observations <= 0:
        raise ValueError("n_observations must be positive")
    if abs(autoregressive_root) >= 1.0:
        raise ValueError(
            "the Stambaugh expansion assumes a stationary predictor; "
            f"got an autoregressive root of {autoregressive_root}"
        )
    ratio = innovation_covariance / predictor_innovation_variance
    return -ratio * (1.0 + 3.0 * autoregressive_root) / n_observations


# --------------------------------------------------------------------------------------
# Out-of-sample scoring
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class OutOfSampleScore:
    """A forecast's record against a rolling-mean benchmark.

    Attributes:
        r2_out_of_sample: ``1 - SSE_model / SSE_benchmark``. Negative means the
            expanding historical mean forecast the outcome better than the model did.
        n_forecasts: Forecasts scored, overlapping if the horizon exceeds the step.
        independent_forecasts: :func:`overlap_adjusted_observations` on those.
        mean_model_error: Mean signed error of the model, in the units of the response.
            A large positive value says the model was systematically too pessimistic.
        mean_benchmark_error: The same for the benchmark.
    """

    r2_out_of_sample: float
    n_forecasts: int
    independent_forecasts: float
    mean_model_error: float
    mean_benchmark_error: float


def out_of_sample_r2(
    realised: NDArray[np.floating] | Sequence[float],
    model_forecast: NDArray[np.floating] | Sequence[float],
    benchmark_forecast: NDArray[np.floating] | Sequence[float],
    *,
    horizon_periods: int = 1,
) -> OutOfSampleScore:
    """Campbell-Thompson out-of-sample ``R**2`` against a rolling-mean benchmark.

    Goyal and Welch's point is that an in-sample ``R**2`` is not evidence a forecast is
    usable: the coefficient is fitted on the same data the fit is scored on, and the
    predictor's own drift is fitted along with it. The benchmark must therefore be the
    expanding or rolling historical mean, computed only from data available at the
    forecast origin, and the model coefficients must be too.

    Sign matters more than magnitude here. A negative value is a complete answer: a
    reader following the model would have done worse than a reader who knew only the
    average.

    Raises:
        ValueError: On a length mismatch, an empty input, or a degenerate benchmark.
    """
    actual = np.asarray(realised, dtype=np.float64)
    model = np.asarray(model_forecast, dtype=np.float64)
    bench = np.asarray(benchmark_forecast, dtype=np.float64)
    if not (actual.size == model.size == bench.size):
        raise ValueError(
            f"length mismatch: realised={actual.size}, model={model.size}, "
            f"benchmark={bench.size}"
        )
    if actual.size == 0:
        raise ValueError("need at least one forecast to score")
    model_error = actual - model
    bench_error = actual - bench
    denominator = float(np.sum(bench_error**2))
    if denominator <= 0.0:
        raise ValueError("the benchmark forecast is exact; out-of-sample R2 is undefined")
    return OutOfSampleScore(
        r2_out_of_sample=1.0 - float(np.sum(model_error**2)) / denominator,
        n_forecasts=actual.size,
        independent_forecasts=overlap_adjusted_observations(actual.size, horizon_periods),
        mean_model_error=float(np.mean(model_error)),
        mean_benchmark_error=float(np.mean(bench_error)),
    )


# --------------------------------------------------------------------------------------
# The rule, and what acting on it costs
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ConditionalWeightRule:
    """A valuation-conditional equity weight, stated as a rule rather than a judgement.

    Attributes:
        base_weight: The weight held when the signal is at its median.
        sensitivity: Weight change per unit of signal percentile away from the median.
            ``0.4`` moves the weight by at most +/- 0.20 across the full percentile range.
        floor: Lowest admissible weight.
        cap: Highest admissible weight.
    """

    base_weight: float
    sensitivity: float
    floor: float = 0.0
    cap: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.floor <= self.cap <= 1.0:
            raise ValueError(
                f"need 0 <= floor <= cap <= 1, got floor={self.floor}, cap={self.cap}"
            )
        if not self.floor <= self.base_weight <= self.cap:
            raise ValueError(
                f"base_weight {self.base_weight} lies outside [{self.floor}, {self.cap}]"
            )
        if self.sensitivity < 0.0:
            raise ValueError(
                "sensitivity is the magnitude of the response; give the signal the sign "
                f"that makes cheap mean 'buy more'. Got {self.sensitivity}"
            )


def conditional_weight(rule: ConditionalWeightRule, signal_percentile: float) -> float:
    """The weight the rule holds at a given signal percentile.

    ``clip(base + sensitivity * (percentile - 0.5), floor, cap)``.

    ``signal_percentile`` must be oriented so that a **high** percentile means **cheap**.
    For an excess CAPE yield that is the raw percentile; for a CAPE level it is one minus
    the raw percentile. Getting this backwards is the single easiest way to report a
    valuation rule with its sign inverted, so the orientation is the caller's explicit
    responsibility and the sensitivity is constrained to be non-negative to make the
    mistake visible rather than absorbable.

    The percentile must itself be computed from an expanding window that ends at the
    decision date. A percentile taken against the full sample is a look-ahead: it tells
    the 1955 investor where 1955 sits in a distribution that includes 2026.
    """
    if not 0.0 <= signal_percentile <= 1.0:
        raise ValueError(f"signal_percentile must lie in [0, 1], got {signal_percentile}")
    raw = rule.base_weight + rule.sensitivity * (signal_percentile - 0.5)
    return float(min(max(raw, rule.floor), rule.cap))


@dataclass(frozen=True)
class TiltCost:
    """What a dynamic rule pays for the privilege of moving.

    Attributes:
        annual_turnover: One-way turnover a year, as a fraction of the portfolio. A rule
            that moves the equity weight by 0.10 and back pays 0.20 of turnover.
        spread_and_commission_bp: Round-trip execution cost on the traded fraction.
        effective_capital_gains_rate: The tax actually paid on the equity **sold**,
            which is the statutory rate times the embedded unrealised gain fraction, not
            the statutory rate. A newly funded position pays nothing; a position held
            thirty years pays close to the full rate.
    """

    annual_turnover: float
    spread_and_commission_bp: float
    effective_capital_gains_rate: float

    def __post_init__(self) -> None:
        if self.annual_turnover < 0.0:
            raise ValueError("annual_turnover cannot be negative")
        if self.spread_and_commission_bp < 0.0:
            raise ValueError("spread_and_commission_bp cannot be negative")
        if not 0.0 <= self.effective_capital_gains_rate < 1.0:
            raise ValueError(
                "effective_capital_gains_rate must lie in [0, 1); it is the statutory "
                "rate times the embedded gain fraction, not the statutory rate"
            )


def tilt_net_edge_bp(*, gross_edge_bp: float, cost: TiltCost) -> float:
    """Gross edge less execution and realised-gain tax, in basis points a year.

    Half the turnover is a sale, and only the sale realises a gain, so the tax term
    carries ``annual_turnover / 2``. Execution is charged on all of it.

    This is the arithmetic that decides the question. A valuation rule's gross edge is
    measured in tens of basis points; its turnover is measured in tens of percent. At any
    embedded gain a long-term holder plausibly carries, the second number wins.
    """
    execution = cost.annual_turnover * cost.spread_and_commission_bp
    tax = 0.5 * cost.annual_turnover * cost.effective_capital_gains_rate * 1e4
    return gross_edge_bp - execution - tax


def break_even_tax_rate(*, gross_edge_bp: float, cost: TiltCost) -> float:
    """The effective capital-gains rate at which :func:`tilt_net_edge_bp` reaches zero.

    Returns ``0.0`` when execution alone already consumes the edge, and is capped below
    ``1.0``. Read it as: *how tax-sheltered must this account be before the rule is worth
    running?*
    """
    after_execution = gross_edge_bp - cost.annual_turnover * cost.spread_and_commission_bp
    if after_execution <= 0.0:
        return 0.0
    if cost.annual_turnover <= 0.0:
        return 1.0
    rate = after_execution / (0.5 * cost.annual_turnover * 1e4)
    return float(min(rate, 1.0))


def derisking_regret_bp(*, weight_reduction: float, realised_excess_return: float) -> float:
    """Growth given up a year by cutting the risky weight, if the premium is realised.

    ``weight_reduction * realised_excess_return``, in basis points a year, where
    ``realised_excess_return`` is the risky asset's realised excess log return over what
    the proceeds are moved into, in percent a year.

    This is the number a valuation-driven cut must be weighed against, and it is
    deliberately parameter-light: it needs no forecast, only the statement "if the
    premium turns out to be ``p``, the cut cost ``w * p``." The point of writing it this
    way is that the investor can supply the ``p`` they fear rather than be handed one.

    A negative return means the cut helped, so a negative result is not an error.
    """
    if not 0.0 <= weight_reduction <= 1.0:
        raise ValueError(f"weight_reduction must lie in [0, 1], got {weight_reduction}")
    return weight_reduction * realised_excess_return * 100.0


# --------------------------------------------------------------------------------------
# Level arithmetic
# --------------------------------------------------------------------------------------


def excess_cape_yield(*, cape: float, real_yield_percent: float) -> float:
    """``100/CAPE - r``: the cyclically adjusted earnings yield over a real yield.

    Shiller's own excess CAPE yield subtracts a **trailing-inflation-adjusted** nominal
    ten-year yield. Subtracting a **market-priced** real yield instead — the ten-year TIPS
    yield — is a different and, for a forward-looking decision, a better-posed quantity,
    because the investor's actual alternative is a TIPS, not a nominal bond deflated by
    the last decade's inflation. The two disagree by more than a percentage point when
    trailing inflation and expected inflation diverge, and they do so at the moment this
    decision is being taken.

    Both are proxies for an equity risk premium and neither is one. In particular the
    earnings yield is not an expected return: it equals one only if real earnings per
    share are expected to be flat forever.

    Raises:
        ValueError: On a non-positive CAPE.
    """
    if cape <= 0.0:
        raise ValueError(f"cape must be positive, got {cape}")
    return 100.0 / cape - real_yield_percent


def rescale_cape_for_price(*, cape: float, index_at_cape: float, index_now: float) -> float:
    """Move a published CAPE to a later index level, holding its denominator fixed.

    Shiller's workbook publishes a monthly figure whose final row is a single day's
    close, so a CAPE read from it is days-to-weeks stale by the time it is used. Because
    the smoothed real earnings denominator moves on a quarterly reporting schedule and
    the index moves daily, scaling by the price ratio is a good approximation over a few
    weeks and a bad one over a few quarters.

    It is an approximation in one direction only: it ignores earnings growth, so over a
    rising-earnings period it **overstates** the current CAPE.

    Raises:
        ValueError: On a non-positive input.
    """
    for name, value in (
        ("cape", cape),
        ("index_at_cape", index_at_cape),
        ("index_now", index_now),
    ):
        if value <= 0.0:
            raise ValueError(f"{name} must be positive, got {value}")
    return cape * index_now / index_at_cape


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._valuation_conditioning_tables import main

    main()
