"""Deflated and probabilistic Sharpe ratios (Bailey and Lopez de Prado 2014).

A Sharpe ratio selected as the best of many trials is an order statistic, not a
measurement. This module supplies the expected maximum of ``N`` independent zero-skill
trials, the probabilistic Sharpe ratio with its non-normality correction, and the deflated
Sharpe ratio built from the two.

The load-bearing distinction
----------------------------
The threshold under the null is ``SR* = sqrt(V[{SR_n}]) * E[max Z]``, where ``V[{SR_n}]``
is the variance of Sharpe ratios **across trials** — the dispersion of the search — and
**not** the sampling variance of a single Sharpe ratio. Substituting the latter is the
most common implementation error in this formula, so
:func:`deflated_sharpe_ratio` takes ``trial_dispersion`` as a required keyword-only
argument with no default. There is deliberately no way to call it without stating what the
dispersion across trials was.

Reference: Bailey, D. and M. Lopez de Prado (2014), "The Deflated Sharpe Ratio: Correcting
for Selection Bias, Backtest Overfitting and Non-Normality", *Journal of Portfolio
Management* 40(5). https://ssrn.com/abstract=2460551
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

__all__ = [
    "EULER_MASCHERONI",
    "DeflatedSharpeResult",
    "LinearDependenceWarning",
    "TrialCorrelationError",
    "deflated_sharpe_ratio",
    "effective_number_of_trials",
    "expected_max_sharpe",
    "mean_off_diagonal_correlation",
    "probabilistic_sharpe_ratio",
    "trial_dispersion_from_sharpes",
]

FloatArray = NDArray[np.float64]

#: Euler-Mascheroni constant, as stated in the source paper.
EULER_MASCHERONI: Final[float] = 0.5772156649


class TrialCorrelationError(ValueError):
    """Raised when a trial correlation matrix cannot support the requested estimate."""


class LinearDependenceWarning(UserWarning):
    """Warns that a correlation summary captures linear dependence only."""


def expected_max_sharpe(n_trials: float) -> float:
    """Expected maximum of ``N`` independent standard-normal (zero-skill) trials.

    ``E[max Z] = (1 - gamma) Phi^-1(1 - 1/N) + gamma Phi^-1(1 - 1/(N e))`` with
    ``gamma`` the Euler-Mascheroni constant.

    This is the Gumbel approximation to the expected maximum, not the exact value. At
    ``N = 100`` it returns 2.530603 against an exact 2.5076, so it is slightly
    conservative — it demands marginally more of a candidate strategy than the exact order
    statistic would.

    ``N`` may be non-integral, which is what the effective-trial-count estimate produces.
    """
    if not math.isfinite(n_trials) or n_trials < 1.0:
        raise ValueError(f"n_trials must be a finite number >= 1, got {n_trials!r}")
    if n_trials == 1.0:
        # Phi^-1(0) is -inf; the expected maximum of one draw is its mean, zero, but the
        # Gumbel form is not defined there. Report the limit the formula is used for.
        return 0.0
    first = float(norm.ppf(1.0 - 1.0 / n_trials))
    second = float(norm.ppf(1.0 - 1.0 / (n_trials * math.e)))
    return (1.0 - EULER_MASCHERONI) * first + EULER_MASCHERONI * second


def probabilistic_sharpe_ratio(
    observed_sharpe: float,
    *,
    benchmark_sharpe: float,
    n_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """Probability that the true Sharpe ratio exceeds ``benchmark_sharpe``.

    ``PSR = Phi[ (SR - SR*) sqrt(T - 1) / sqrt(1 - g3 SR + (g4 - 1)/4 SR^2) ]``

    ``kurtosis`` is the **non-excess** fourth standardised moment, so a normal sample is
    3.0 and the correction term ``(g4 - 1)/4`` is 0.5. Passing excess kurtosis here
    silently overstates significance; the argument is named ``kurtosis`` rather than
    ``excess_kurtosis`` for exactly that reason.

    ``observed_sharpe`` and ``benchmark_sharpe`` must be expressed per observation period,
    at the same frequency as ``n_observations``. Annualising one but not the other is the
    second-most-common error here.
    """
    if n_observations < 2:
        raise ValueError("n_observations must be at least 2")
    if kurtosis < 1.0:
        raise ValueError(f"kurtosis is the non-excess moment and must be >= 1, got {kurtosis}")
    variance_term = 1.0 - skewness * observed_sharpe + 0.25 * (kurtosis - 1.0) * observed_sharpe**2
    if variance_term <= 0.0:
        raise ValueError(
            "non-normality correction is non-positive; the skew/kurtosis/Sharpe "
            f"combination ({skewness}, {kurtosis}, {observed_sharpe}) is inadmissible"
        )
    statistic = (observed_sharpe - benchmark_sharpe) * math.sqrt(n_observations - 1)
    return float(norm.cdf(statistic / math.sqrt(variance_term)))


def trial_dispersion_from_sharpes(sharpes: NDArray[np.floating] | list[float]) -> float:
    """Standard deviation of Sharpe ratios **across trials**.

    This is ``sqrt(V[{SR_n}])`` — the input :func:`deflated_sharpe_ratio` needs. It is a
    property of the *search*, not of any one backtest, and it must be computed over every
    trial actually run, including the abandoned ones. Uses the unbiased ``ddof=1``
    divisor.
    """
    values = np.asarray(sharpes, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"expected a one-dimensional array of trial Sharpes, got {values.shape}")
    if values.size < 2:
        raise ValueError("need at least two trials to measure dispersion across trials")
    if not np.all(np.isfinite(values)):
        raise ValueError("trial Sharpe ratios contain non-finite values")
    return float(np.std(values, ddof=1))


@dataclass(frozen=True)
class DeflatedSharpeResult:
    """Deflated Sharpe ratio and every assumption that produced it."""

    deflated_significance: float
    """``P[SR_true > SR*]``, the deflated significance."""
    sharpe_threshold: float
    """``SR* = trial_dispersion * E[max Z]``, the null threshold actually applied."""
    expected_max_z: float
    """``E[max Z]`` at the effective trial count."""
    n_trials_used: float
    """The ``N`` actually used. Always report it: the DSR is a monotone function of an
    assumption about the number of independent trials, not a measurement."""
    trial_dispersion: float
    observed_sharpe: float
    n_observations: int
    skewness: float
    kurtosis: float


def deflated_sharpe_ratio(
    observed_sharpe: float,
    *,
    trial_dispersion: float,
    n_trials: float,
    n_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> DeflatedSharpeResult:
    """Deflated Sharpe ratio.

    Parameters
    ----------
    observed_sharpe:
        The selected trial's Sharpe ratio, per observation period.
    trial_dispersion:
        ``sqrt(V[{SR_n}])`` — the standard deviation of Sharpe ratios **across trials**.
        Required, keyword-only, no default. It is *not* the standard error of a single
        Sharpe ratio; see :func:`trial_dispersion_from_sharpes`.
    n_trials:
        Number of *independent* trials. Pass the output of
        :func:`effective_number_of_trials` when the trials are correlated. May be
        non-integral.
    n_observations:
        Sample length at the same frequency as ``observed_sharpe``.
    skewness, kurtosis:
        Sample skewness and **non-excess** kurtosis of the returns (normal: 0.0 and 3.0).
    """
    if not math.isfinite(trial_dispersion) or trial_dispersion < 0.0:
        raise ValueError(
            f"trial_dispersion must be finite and non-negative, got {trial_dispersion}"
        )
    expected_max = expected_max_sharpe(n_trials)
    threshold = trial_dispersion * expected_max
    significance = probabilistic_sharpe_ratio(
        observed_sharpe,
        benchmark_sharpe=threshold,
        n_observations=n_observations,
        skewness=skewness,
        kurtosis=kurtosis,
    )
    return DeflatedSharpeResult(
        deflated_significance=significance,
        sharpe_threshold=threshold,
        expected_max_z=expected_max,
        n_trials_used=float(n_trials),
        trial_dispersion=float(trial_dispersion),
        observed_sharpe=float(observed_sharpe),
        n_observations=int(n_observations),
        skewness=float(skewness),
        kurtosis=float(kurtosis),
    )


def mean_off_diagonal_correlation(
    trial_returns: NDArray[np.floating],
    *,
    allow_rank_deficient: bool = False,
) -> float:
    """Average off-diagonal correlation ``rho_bar`` of a ``T x M`` matrix of trial returns.

    Guardrails, enforced rather than documented:

    * **Singularity.** The trial correlation matrix is singular whenever ``T < M``, so an
      average correlation computed from it is itself overfit. This raises
      :class:`TrialCorrelationError` in that case. Reduce the dimension first (cluster the
      trials, or project onto principal components retained on a training window) and pass
      the reduced matrix. ``allow_rank_deficient=True`` overrides the refusal and exists
      only for tests of the arithmetic itself.
    * **Linear dependence only.** Correlation is blind to non-linear and tail dependence,
      so ``rho_bar`` understates how much two trials share whenever they are the same idea
      expressed two ways. A :class:`LinearDependenceWarning` is emitted on every call.
    * **Lower bound.** Positive semi-definiteness bounds ``rho_bar >= -1/(M-1)``. A result
      below that bound indicates a malformed input and raises.
    """
    matrix = np.asarray(trial_returns, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError(f"trial_returns must be T x M, got shape {matrix.shape}")
    n_obs, n_trials = int(matrix.shape[0]), int(matrix.shape[1])
    if n_trials < 2:
        raise ValueError("need at least two trials to average off-diagonal correlations")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("trial_returns contains non-finite values")
    if n_obs < n_trials and not allow_rank_deficient:
        raise TrialCorrelationError(
            f"the trial correlation matrix is singular for T={n_obs} < M={n_trials}; "
            "reduce the dimension (clustering or a retained-component projection) before "
            "averaging off-diagonal correlations"
        )
    if np.any(matrix.std(axis=0) == 0.0):
        raise TrialCorrelationError("a trial has zero variance; its correlations are undefined")

    warnings.warn(
        "rho_bar summarises linear dependence only; trials that share a mechanism "
        "non-linearly will look more independent than they are",
        LinearDependenceWarning,
        stacklevel=2,
    )

    correlation = np.corrcoef(matrix, rowvar=False)
    off_diagonal = (float(correlation.sum()) - float(np.trace(correlation))) / (
        n_trials * (n_trials - 1)
    )
    lower_bound = -1.0 / (n_trials - 1)
    if off_diagonal < lower_bound - 1e-9:
        raise TrialCorrelationError(
            f"rho_bar={off_diagonal:.6f} is below the positive-semi-definite lower bound "
            f"{lower_bound:.6f} for M={n_trials}; the input is not a valid correlation structure"
        )
    return off_diagonal


def effective_number_of_trials(n_trials: int, mean_correlation: float) -> float:
    """Effective independent trial count from ``M`` trials of average correlation ``rho_bar``.

    **UNVERIFIED.** The exact interpolation in Bailey and Lopez de Prado sits in a glyph our
    source extraction dropped, and it has not been confirmed against the typeset paper. What
    is implemented here is the *linear reading*

    ``N_hat = M (1 - rho_bar) + rho_bar``

    which reproduces both stated endpoints — ``N_hat = M`` at ``rho_bar -> 0`` and
    ``N_hat = 1`` at ``rho_bar -> 1`` — and nothing more. Whether the intended estimator is
    this linear form, a clustering-based count, or something else is open question 1 in
    ``docs/research/portfolio-engine-specification.md``. Do not treat the returned number as
    a measurement; report it alongside every deflated Sharpe ratio it produced.

    ``rho_bar`` is bounded below by ``-1/(M-1)`` by positive semi-definiteness and above by
    1; values outside that range raise.
    """
    if n_trials < 1:
        raise ValueError("n_trials must be at least 1")
    if n_trials == 1:
        return 1.0
    lower_bound = -1.0 / (n_trials - 1)
    if not math.isfinite(mean_correlation):
        raise ValueError("mean_correlation must be finite")
    if mean_correlation > 1.0:
        raise TrialCorrelationError(f"rho_bar={mean_correlation} exceeds 1")
    if mean_correlation < lower_bound - 1e-9:
        raise TrialCorrelationError(
            f"rho_bar={mean_correlation:.6f} is below the positive-semi-definite lower bound "
            f"{lower_bound:.6f} for M={n_trials}"
        )
    estimate = n_trials * (1.0 - mean_correlation) + mean_correlation
    return float(max(estimate, 1.0))
