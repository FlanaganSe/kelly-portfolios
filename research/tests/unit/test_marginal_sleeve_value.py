"""Independent closed-form fixtures for the marginal growth value of a candidate sleeve.

This module is a **second derivation**, written so that an implementation of the
marginal-sleeve-value calculation can be pointed at it without either side having seen
the other. Nothing here imports the calculation under test. Every expected value is a
literal constant carrying its derivation in a comment, and every literal is checked by at
least two further routes: exact rational arithmetic, a dense brute-force grid over the
sleeve weight, and — for the cases where the model's growth rate is the claim rather than
the algebra — a seeded Monte Carlo of the rebalanced mix.

--------------------------------------------------------------------------------------
1. The derivation
--------------------------------------------------------------------------------------

An existing portfolio ``P`` has instantaneous arithmetic drift ``mu_p`` and volatility
``sigma_p``. A candidate sleeve ``i`` has ``mu_i``, ``sigma_i`` and covariance
``sigma_ip = rho sigma_i sigma_p`` with the portfolio. The sleeve is funded **pro rata
out of the existing portfolio**, so the combined holding is ``(1 - w)`` in ``P`` and ``w``
in ``i`` and the weights always sum to one. That funding convention is a choice, not a
fact; section 5 shows what changes if the sleeve is financed from cash instead.

Arithmetic moments of the mix are exact:

    mu(w)       = mu_p + w (mu_i - mu_p)
    sigma^2(w)  = (1-w)^2 sigma_p^2 + 2 w (1-w) sigma_ip + w^2 sigma_i^2
                = sigma_p^2 - 2 w (sigma_p^2 - sigma_ip) + w^2 tau^2

with

    tau^2 = sigma_i^2 - 2 sigma_ip + sigma_p^2 = Var(r_i - r_p) >= 0.

In the diffusion model the growth rate is ``g = mu - sigma^2 / 2`` (Ito), so substituting
gives a form that is **exactly quadratic in w, with no approximation**:

    g(w) = g(0) + w D - (1/2) w^2 tau^2,                                            (1)
    g(0) = mu_p - sigma_p^2 / 2,
    D    = (mu_i - mu_p) + (sigma_p^2 - sigma_ip)
         = (mu_i - mu_p) + sigma_p^2 (1 - beta_ip),      beta_ip = sigma_ip / sigma_p^2.

``D = dg/dw |_{w=0}`` is the first-order marginal growth rate. Its two terms are the
**standalone term** ``mu_i - mu_p`` and the **diversification credit**
``sigma_p^2 (1 - beta_ip)``. Note what the credit is not: it is not a correlation effect
in its own right, it is a *beta* effect, and beta mixes correlation with the sleeve's own
volatility. A sleeve with ``rho = 0.25`` earns a credit of ``0.5 sigma_p^2`` at
``sigma_i = 2 sigma_p`` and a credit of ``0.75 sigma_p^2`` at ``sigma_i = sigma_p``.

--------------------------------------------------------------------------------------
2. Curvature, the interior optimum, and where the constraint binds
--------------------------------------------------------------------------------------

``g''(w) = -tau^2`` everywhere, so (1) is a downward parabola and the honest object is
the whole curve, not its slope at the origin. The interior optimum and the certainty-
equivalent gain at it are closed form:

    w*        = D / tau^2                                                           (2)
    g(w*)-g(0)= D^2 / (2 tau^2) = (1/2) tau^2 (w*)^2                                (3)
    g(w)-g(0) = w D - (1/2) w^2 tau^2  for any w.                                   (4)

``w* > 0`` iff ``D > 0``, i.e. iff ``mu_i - mu_p > sigma_ip - sigma_p^2``. Under a
long-only constraint the optimum is ``max(w*, 0)``; under an additional cap ``c`` it is
``min(max(w*, 0), c)``, and (4) values it. Both constraints bind often in practice: a
sleeve with a credit but no alpha lands at a small interior ``w*``, while a sleeve with
real alpha usually wants far more than any mandate allows.

``tau^2 = 0`` exactly when the sleeve is a pathwise clone of the portfolio. Then ``D = 0``
too, (1) is flat, and (2) is ``0/0``. That is a genuine degeneracy and the right response
is to refuse, not to return a number.

**A ceiling worth knowing.** For a zero-alpha sleeve (``mu_i = mu_p``), maximising (3)
over ``rho`` at fixed ``sigma_i`` gives

    g(w*) - g(0) <= sigma_p^2 / 2,   with equality iff |rho| = 1.                   (5)

Proof: with ``x = rho sigma_i``, (3) is ``sigma_p^2 (sigma_p - x)^2 / (2 (sigma_i^2 +
sigma_p^2 - 2 x sigma_p))`` and the denominator minus ``(sigma_p - x)^2`` is
``sigma_i^2 - x^2 = sigma_i^2 (1 - rho^2) >= 0``. So **the entire growth benefit any
zero-alpha diversifier can ever deliver is the portfolio's own variance drag**, which is
50 bp/yr at ``sigma_p = 10%`` and only reached by a perfect hedge. At a realistic
``rho = 0.25`` the fixtures below show 3.1 bp/yr.

--------------------------------------------------------------------------------------
3. Discrete returns: where the continuous form stops being exact
--------------------------------------------------------------------------------------

For discrete simple returns the objective is ``g(w) = E[log(1 + R_p + w (R_i - R_p))]``
and differentiating under the expectation gives an identity that holds for **any** joint
distribution with ``1 + R_p > 0``:

    dg/dw |_{w=0} = E[ (R_i - R_p) / (1 + R_p) ].                                   (6)

Expanding ``1/(1+R_p) = 1 - R_p + ...`` recovers the continuous form and shows what it
drops:

    E[(R_i - R_p)/(1+R_p)] = (mu_i - mu_p)(1 - mu_p) + (sigma_p^2 - sigma_ip)
                             + third-moment terms.

So the continuous ``D`` is a second-moment truncation. Two consequences the fixtures pin:
it ignores co-skewness entirely, which is exactly the property a tail-hedging sleeve is
bought for; and under a lognormal moment match with ``dm = 0`` the credit becomes
``(sigma_p^2 - sigma_ip) / ((1 + mu_p)^2 + sigma_p^2)``, i.e. the continuous form
**overstates the credit by about 12% at mu_p = 6%, sigma_p = 10%** and by 16% at
``mu_p = 8%, sigma_p = 15%``. Every fixture below is stated in the continuous convention
and the discrete ones are marked as such; mixing them is a units error of the same family
the repository has been bitten by before.

--------------------------------------------------------------------------------------
4. Annualisation
--------------------------------------------------------------------------------------

Under iid periods, ``mu``, all variances and covariances, and therefore ``D``, ``tau^2``
and the CE gain scale **linearly in the period length**. Consequences:

* the credit and the CE gain annualise by ``x 12`` from monthly, never by ``x sqrt(12)``;
* ``beta_ip`` and ``w* = D / tau^2`` are **scale-invariant** — identical monthly and
  annually — which is the cheapest available check that a pipeline's units are consistent.

--------------------------------------------------------------------------------------
5. Where this framing misleads
--------------------------------------------------------------------------------------

Recorded here because it is worth more than the fixtures, and each item is a test below.

1. **The answer depends on what funds the sleeve.** Pro rata out of the portfolio gives
   ``D``; financing from cash at rate ``r`` gives ``(mu_i - r) - sigma_ip`` instead. The
   two differ by ``sigma_p^2 - (mu_p - r)`` and agree **iff the base portfolio is itself
   at full Kelly**. Nothing in a reported marginal value says which convention produced
   it.
2. **The first-order term is not the value.** At the 5-20% weights actually under
   discussion, (4) is 25% to 400% below the linear extrapolation, and because the parabola
   is symmetric about ``w*`` a 5% and a 20% allocation of the same sleeve can be worth
   *exactly the same*, while the linear term says the larger is four times better.
3. **The first-order term always rewards low beta, without limit.** ``D`` is unbounded as
   ``beta -> -inf``, which makes it a poor screen on its own. (5) is the bound that makes
   it honest.
4. **The standalone term is not estimable and the credit is.** At 20 years of monthly
   data the fixtures pin ``SE(mu_i - mu_p) = 447 bp/yr`` against a total ``D`` of 50 bp
   (``t = 0.11``, and the *sign* of the estimated ``D`` is a 45/55 coin flip), while
   ``SE(credit) = 12.5 bp`` on the same 50 bp (``t = 4.0``). A positive marginal value
   driven by the standalone term is not evidence of anything; one driven by the credit is
   at least measurable.
5. **Selection across candidates inflates the credit.** With ``SE(credit) = 12.5 bp``,
   ranking 20 candidate sleeves and reporting the winner's measured credit adds about
   31 bp of pure noise to a true 50 bp — a 61% overstatement before any alpha is claimed.
6. **A correlation error moves the claim far more than the allocation.** One standard
   error of ``rho`` at 20 years of monthly data (0.061) moves ``w*`` by about 18% but the
   *reported* CE gain by about 43%, and the growth actually forgone by holding the wrong
   weight is only 6% of an already tiny number. The estimate is dangerous in what it
   licenses saying, not in what it licenses holding.
7. **The credit is gross.** Costs enter by reducing ``mu_i`` and re-solving (2), not as a
   haircut on (3). Break-even all-in cost is exactly ``D``, and the gain falls
   *quadratically* in the cost: half the break-even cost leaves a quarter of the gain.
8. **A single unconditional covariance is the whole model.** (1) prices no regime shift,
   no conditional correlation, and no co-skewness; a sleeve whose ``rho`` rises in
   drawdowns has a smaller true credit than its full-sample estimate, and (1) cannot see
   the difference.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pytest
from numpy.typing import NDArray

from portfolio_edge.core.kelly import kelly_leverage
from portfolio_edge.core.portfolio import portfolio_variance

FloatArray = NDArray[np.float64]

# --------------------------------------------------------------------------------------
# The base portfolio every fixture is measured against
# --------------------------------------------------------------------------------------

BASE_DRIFT = 0.06
"""``mu_p``: arithmetic drift of the existing portfolio, per year."""

BASE_VOLATILITY = 0.10
"""``sigma_p``: instantaneous volatility of the existing portfolio, per year."""

BASE_VARIANCE = 0.01
"""``sigma_p^2 = 0.10**2``, written as a literal so the fixtures never depend on a square."""

BASE_GROWTH = 0.055
"""``g(0) = mu_p - sigma_p^2 / 2 = 0.06 - 0.005``."""

WEIGHT_CAP = 0.20
"""A 20% mandate cap, used to pin the constrained optimum where it binds."""


@dataclass(frozen=True)
class SleeveCase:
    """One candidate sleeve and every quantity the marginal-value calculation must produce.

    Inputs are ``drift``, ``volatility`` and ``correlation``. Everything else is an
    expected value, stated as a literal and derived in :data:`MARGINAL_VALUE_FIXTURES`.
    All rates are per year and in the continuous (Ito) convention of section 1.
    """

    name: str
    drift: float
    volatility: float
    correlation: float
    covariance: float
    beta: float
    standalone: float
    credit: float
    marginal_growth: float
    relative_variance: float
    optimal_weight: float | None
    optimal_gain: float | None
    capped_weight: float | None
    capped_gain: float | None


# Every literal below is the exact rational value of the stated algebra with
# mu_p = 0.06, sigma_p^2 = 0.01. Read each row as:
#   covariance = rho sigma_i sigma_p
#   beta       = covariance / 0.01
#   standalone = mu_i - 0.06
#   credit     = 0.01 - covariance = 0.01 (1 - beta)
#   marginal   = standalone + credit                       [D, equation (1)]
#   rel. var   = sigma_i^2 - 2 covariance + 0.01           [tau^2]
#   w*         = marginal / rel. var                       [equation (2)]
#   gain       = marginal^2 / (2 rel. var)                 [equation (3)]
#   capped     = min(max(w*, 0), 0.20) and equation (4) at that weight
MARGINAL_VALUE_FIXTURES: tuple[SleeveCase, ...] = (
    SleeveCase(
        # Zero alpha, beta 0.5. The reference case.
        #   cov = 0.25 * 0.20 * 0.10 = 0.005;  beta = 0.5;  credit = 0.01 * 0.5 = 0.005
        #   D = 0 + 0.005 = 0.005;  tau^2 = 0.04 - 0.01 + 0.01 = 0.04
        #   w* = 0.005 / 0.04 = 1/8;  gain = 0.005^2 / 0.08 = 1/3200 = 3.125 bp
        name="zero_alpha_low_beta",
        drift=0.06,
        volatility=0.20,
        correlation=0.25,
        covariance=0.005,
        beta=0.5,
        standalone=0.0,
        credit=0.005,
        marginal_growth=0.005,
        relative_variance=0.04,
        optimal_weight=0.125,
        optimal_gain=0.0003125,
        capped_weight=0.125,
        capped_gain=0.0003125,
    ),
    SleeveCase(
        # beta exactly 1 at sigma_i = 20%: rho = sigma_p / sigma_i = 0.5.
        #   cov = 0.5 * 0.20 * 0.10 = 0.01 = sigma_p^2, so the credit is exactly zero.
        #   D = 0;  w* = 0;  gain = 0.  tau^2 = 0.04 - 0.02 + 0.01 = 0.03.
        name="beta_one_moderate_volatility",
        drift=0.06,
        volatility=0.20,
        correlation=0.5,
        covariance=0.01,
        beta=1.0,
        standalone=0.0,
        credit=0.0,
        marginal_growth=0.0,
        relative_variance=0.03,
        optimal_weight=0.0,
        optimal_gain=0.0,
        capped_weight=0.0,
        capped_gain=0.0,
    ),
    SleeveCase(
        # beta exactly 1 again, at double the volatility and a quarter of the correlation.
        #   cov = 0.25 * 0.40 * 0.10 = 0.01.  The credit is zero for the *same* reason and
        #   is independent of sigma_i: only beta matters.  tau^2 = 0.16 - 0.02 + 0.01.
        name="beta_one_high_volatility",
        drift=0.06,
        volatility=0.40,
        correlation=0.25,
        covariance=0.01,
        beta=1.0,
        standalone=0.0,
        credit=0.0,
        marginal_growth=0.0,
        relative_variance=0.15,
        optimal_weight=0.0,
        optimal_gain=0.0,
        capped_weight=0.0,
        capped_gain=0.0,
    ),
    SleeveCase(
        # beta 1 with 200 bp of standalone alpha: the whole marginal value is the alpha.
        #   D = 0.02;  tau^2 = 0.03;  w* = 2/3;  gain = 0.0004 / 0.06 = 1/150
        #   capped at 20%: 0.20 * 0.02 - 0.5 * 0.03 * 0.04 = 0.004 - 0.0006 = 0.0034
        name="beta_one_with_alpha",
        drift=0.08,
        volatility=0.20,
        correlation=0.5,
        covariance=0.01,
        beta=1.0,
        standalone=0.02,
        credit=0.0,
        marginal_growth=0.02,
        relative_variance=0.03,
        optimal_weight=2.0 / 3.0,
        optimal_gain=1.0 / 150.0,
        capped_weight=0.20,
        capped_gain=0.0034,
    ),
    SleeveCase(
        # beta 2.125: the small-value-like case. Positive alpha, NEGATIVE marginal value.
        #   cov = 0.85 * 0.25 * 0.10 = 0.02125;  credit = 0.01 - 0.02125 = -0.01125
        #   D = +0.01 - 0.01125 = -0.00125 < 0 despite 100 bp of standalone alpha.
        #   tau^2 = 0.0625 - 0.0425 + 0.01 = 0.03;  w* = -1/24;  gain = 1/38400
        #   Long-only binds: capped weight 0, capped gain exactly 0.
        name="high_beta_positive_alpha",
        drift=0.07,
        volatility=0.25,
        correlation=0.85,
        covariance=0.02125,
        beta=2.125,
        standalone=0.01,
        credit=-0.01125,
        marginal_growth=-0.00125,
        relative_variance=0.03,
        optimal_weight=-1.0 / 24.0,
        optimal_gain=1.0 / 38400.0,
        capped_weight=0.0,
        capped_gain=0.0,
    ),
    SleeveCase(
        # The mirror image: NEGATIVE alpha, positive marginal value.
        #   cov = -0.20 * 0.12 * 0.10 = -0.0024;  beta = -0.24;  credit = 0.0124
        #   D = -0.005 + 0.0124 = +0.0074;  tau^2 = 0.0144 + 0.0048 + 0.01 = 0.0292
        #   w* = 0.0074 / 0.0292 = 37/146;  gain = 1369/1460000
        #   capped at 20%: 0.20 * 0.0074 - 0.5 * 0.0292 * 0.04 = 0.00148 - 0.000584
        name="negative_alpha_positive_total",
        drift=0.055,
        volatility=0.12,
        correlation=-0.20,
        covariance=-0.0024,
        beta=-0.24,
        standalone=-0.005,
        credit=0.0124,
        marginal_growth=0.0074,
        relative_variance=0.0292,
        optimal_weight=37.0 / 146.0,
        optimal_gain=1369.0 / 1460000.0,
        capped_weight=0.20,
        capped_gain=0.000896,
    ),
    SleeveCase(
        # Degenerate: the sleeve IS the portfolio. tau^2 = 0 and D = 0 exactly, so the
        # objective is flat in w and w* is 0/0. The marginal value must be exactly zero
        # and the optimum must be refused rather than reported.
        name="identical_clone",
        drift=0.06,
        volatility=0.10,
        correlation=1.0,
        covariance=0.01,
        beta=1.0,
        standalone=0.0,
        credit=0.0,
        marginal_growth=0.0,
        relative_variance=0.0,
        optimal_weight=None,
        optimal_gain=None,
        capped_weight=None,
        capped_gain=None,
    ),
    SleeveCase(
        # Perfectly correlated but twice the volatility: a levered clone.
        #   cov = 0.02;  beta = 2;  credit = -0.01;  D = -0.01
        #   tau^2 = (sigma_i - sigma_p)^2 = 0.01;  w* = -1
        #   The growth-optimal move is to SHORT the redundant volatility and hold 200% of
        #   the portfolio, and the gain is sigma_p^2 / 2 = the bound (5), attained at |rho|=1.
        name="perfectly_correlated_levered_clone",
        drift=0.06,
        volatility=0.20,
        correlation=1.0,
        covariance=0.02,
        beta=2.0,
        standalone=0.0,
        credit=-0.01,
        marginal_growth=-0.01,
        relative_variance=0.01,
        optimal_weight=-1.0,
        optimal_gain=0.005,
        capped_weight=0.0,
        capped_gain=0.0,
    ),
    SleeveCase(
        # Zero-variance sleeve: cash at 2%. This is the Kelly leverage problem in disguise.
        #   cov = 0;  beta = 0;  credit = sigma_p^2 = 0.01;  D = -0.04 + 0.01 = -0.03
        #   tau^2 = 0.01;  w* = -3, i.e. 1 - w* = 4x exposure to the portfolio, which must
        #   equal L* = (mu_p - r) / sigma_p^2 = 0.04 / 0.01 = 4 exactly.
        #   gain = 0.0009 / 0.02 = 0.045 = g(L*) - g(1) = 0.10 - 0.055.
        name="cash_sleeve",
        drift=0.02,
        volatility=0.0,
        correlation=0.0,
        covariance=0.0,
        beta=0.0,
        standalone=-0.04,
        credit=0.01,
        marginal_growth=-0.03,
        relative_variance=0.01,
        optimal_weight=-3.0,
        optimal_gain=0.045,
        capped_weight=0.0,
        capped_gain=0.0,
    ),
    SleeveCase(
        # Perfect hedge: rho = -1 at twice the volatility, no alpha.
        #   cov = -0.02;  beta = -2;  credit = 0.03;  D = 0.03
        #   tau^2 = (sigma_i + sigma_p)^2 = 0.09;  w* = 1/3, at which sigma(w*) = 0 exactly
        #   gain = 0.0009 / 0.18 = 0.005 = sigma_p^2 / 2, the ceiling (5).
        #   capped at 20%: 0.20 * 0.03 - 0.5 * 0.09 * 0.04 = 0.006 - 0.0018 = 0.0042
        name="perfect_hedge",
        drift=0.06,
        volatility=0.20,
        correlation=-1.0,
        covariance=-0.02,
        beta=-2.0,
        standalone=0.0,
        credit=0.03,
        marginal_growth=0.03,
        relative_variance=0.09,
        optimal_weight=1.0 / 3.0,
        optimal_gain=0.005,
        capped_weight=0.20,
        capped_gain=0.0042,
    ),
)

FIXTURES_BY_NAME: dict[str, SleeveCase] = {case.name: case for case in MARGINAL_VALUE_FIXTURES}

RATE_TOLERANCE = 1e-15
"""Absolute tolerance on a per-year rate. Every fixture is an exact rational in binary."""


# --------------------------------------------------------------------------------------
# A local re-derivation. Deliberately written from equations (1)-(4) rather than imported.
# --------------------------------------------------------------------------------------


def _case_covariance(case: SleeveCase) -> FloatArray:
    """The 2x2 covariance matrix of ``(r_p, r_i)``."""
    return np.array(
        [
            [BASE_VARIANCE, case.covariance],
            [case.covariance, case.volatility**2],
        ],
        dtype=np.float64,
    )


def mix_growth_rate(weight: float, case: SleeveCase) -> float:
    """``g(w) = mu(w) - sigma^2(w) / 2`` built from the raw moments, not from (1).

    This is the definition the fixtures are checked against, and it shares no algebra with
    equations (1)-(4): it forms the 2x2 covariance matrix and calls the audited
    :func:`portfolio_edge.core.portfolio.portfolio_variance`.
    """
    weights = np.array([1.0 - weight, weight], dtype=np.float64)
    drift = float(weights @ np.array([BASE_DRIFT, case.drift], dtype=np.float64))
    return drift - 0.5 * portfolio_variance(weights, _case_covariance(case))


def mix_growth_rates(weights: FloatArray, case: SleeveCase) -> FloatArray:
    """Vectorised :func:`mix_growth_rate`, checked against it in the tests below.

    Written as the same quadratic form evaluated with ``einsum`` so that a dense grid is
    affordable; it is the definition, not equation (1).
    """
    matrix = np.stack([1.0 - weights, weights], axis=1)
    variance = np.einsum("ij,jk,ik->i", matrix, _case_covariance(case), matrix)
    drift = matrix @ np.array([BASE_DRIFT, case.drift], dtype=np.float64)
    return np.asarray(drift - 0.5 * variance, dtype=np.float64)


def _grid_optimum(
    case: SleeveCase, *, points: int = 400_001, span: float = 1.0
) -> tuple[float, float]:
    """Brute-force ``argmax`` and gain of :func:`mix_growth_rates` on a dense grid."""
    assert case.optimal_weight is not None
    grid = np.linspace(case.optimal_weight - span, case.optimal_weight + span, points)
    values = mix_growth_rates(grid, case)
    index = int(np.argmax(values))
    return float(grid[index]), float(values[index] - mix_growth_rate(0.0, case))


# --------------------------------------------------------------------------------------
# 1. The literals are the algebra
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda c: c.name)
def test_fixture_literals_are_internally_consistent(case: SleeveCase) -> None:
    """Each literal must be reproduced by exact rational arithmetic on the inputs.

    Fractions rather than floats, so this is a proof about the numbers rather than a
    tolerance. If a literal above were mistyped this is the test that catches it.
    """
    sigma_p = Fraction(1, 10)
    var_p = sigma_p**2
    mu_p = Fraction(6, 100)
    sigma_i = Fraction(case.volatility).limit_denominator(10_000)
    rho = Fraction(case.correlation).limit_denominator(10_000)
    mu_i = Fraction(case.drift).limit_denominator(100_000)

    covariance = rho * sigma_i * sigma_p
    credit = var_p - covariance
    standalone = mu_i - mu_p
    marginal = standalone + credit
    relative_variance = sigma_i**2 - 2 * covariance + var_p

    assert float(covariance) == pytest.approx(case.covariance, rel=0.0, abs=RATE_TOLERANCE)
    assert float(covariance / var_p) == pytest.approx(case.beta, rel=0.0, abs=1e-14)
    assert float(credit) == pytest.approx(case.credit, rel=0.0, abs=RATE_TOLERANCE)
    assert float(standalone) == pytest.approx(case.standalone, rel=0.0, abs=RATE_TOLERANCE)
    assert float(marginal) == pytest.approx(case.marginal_growth, rel=0.0, abs=RATE_TOLERANCE)
    assert float(relative_variance) == pytest.approx(
        case.relative_variance, rel=0.0, abs=RATE_TOLERANCE
    )

    if relative_variance == 0:
        assert case.optimal_weight is None
        assert case.optimal_gain is None
        return

    assert case.optimal_weight is not None
    assert case.optimal_gain is not None
    assert case.capped_weight is not None
    assert case.capped_gain is not None
    assert float(marginal / relative_variance) == pytest.approx(
        case.optimal_weight, rel=0.0, abs=1e-14
    )
    assert float(marginal * marginal / (2 * relative_variance)) == pytest.approx(
        case.optimal_gain, rel=0.0, abs=RATE_TOLERANCE
    )
    capped = min(max(marginal / relative_variance, Fraction(0)), Fraction(1, 5))
    assert float(capped) == pytest.approx(case.capped_weight, rel=0.0, abs=1e-14)
    assert float(capped * marginal - capped * capped * relative_variance / 2) == pytest.approx(
        case.capped_gain, rel=0.0, abs=RATE_TOLERANCE
    )


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda c: c.name)
def test_the_vectorised_growth_rate_agrees_with_the_audited_scalar_one(case: SleeveCase) -> None:
    """The ``einsum`` grid helper must equal the route through ``core.portfolio``, exactly."""
    weights = np.array([-2.0, -0.3, 0.0, 0.0625, 0.125, 0.5, 1.0, 3.0], dtype=np.float64)
    vectorised = mix_growth_rates(weights, case)
    for weight, value in zip(weights, vectorised, strict=True):
        assert float(value) == pytest.approx(
            mix_growth_rate(float(weight), case), rel=0.0, abs=1e-15
        )


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda c: c.name)
def test_marginal_growth_is_the_derivative_of_the_growth_rate_at_zero(case: SleeveCase) -> None:
    """``D`` must equal a central finite difference of ``g(w)`` at ``w = 0``.

    ``g`` is exactly quadratic, so a central difference is exact up to rounding for any
    step: the second-order term cancels. Using two steps that differ by a factor of 1000
    and demanding the same answer is what makes this a check rather than a restatement.
    """
    for step in (1e-3, 1e-6):
        derivative = (mix_growth_rate(step, case) - mix_growth_rate(-step, case)) / (2.0 * step)
        assert derivative == pytest.approx(case.marginal_growth, rel=0.0, abs=1e-11)


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda c: c.name)
def test_curvature_is_minus_the_variance_of_the_return_difference(case: SleeveCase) -> None:
    """``g''(w) = -tau^2 = -Var(r_i - r_p)``, constant in ``w``."""
    for centre in (-0.5, 0.0, 0.3, 1.7):
        step = 1e-3
        second = (
            mix_growth_rate(centre + step, case)
            - 2.0 * mix_growth_rate(centre, case)
            + mix_growth_rate(centre - step, case)
        ) / step**2
        assert second == pytest.approx(-case.relative_variance, rel=0.0, abs=1e-8)


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda c: c.name)
def test_growth_rate_is_exactly_quadratic_in_the_sleeve_weight(case: SleeveCase) -> None:
    """Equation (1) must reproduce ``g(w)`` at arbitrary weights, not only near zero."""
    for weight in (-1.5, -0.25, 0.0, 0.05, 0.2, 0.75, 2.0):
        expected = (
            BASE_GROWTH
            + weight * case.marginal_growth
            - 0.5 * weight**2 * case.relative_variance
        )
        assert mix_growth_rate(weight, case) == pytest.approx(expected, rel=0.0, abs=1e-15)


@pytest.mark.parametrize(
    "case",
    [c for c in MARGINAL_VALUE_FIXTURES if c.optimal_weight is not None],
    ids=lambda c: c.name,
)
def test_closed_form_optimum_agrees_with_a_brute_force_grid(case: SleeveCase) -> None:
    """A 400,001-point grid must find the same ``w*`` and the same CE gain.

    The tolerances are the grid's own resolution, not tuned numbers: the argmax can be off
    by at most half a grid step ``h``, and because the curvature is ``-tau^2`` the value at
    that point is below the true optimum by at most ``tau^2 h^2 / 8``.
    """
    assert case.optimal_weight is not None
    assert case.optimal_gain is not None
    step = 2.0 / 400_000.0
    weight, gain = _grid_optimum(case)
    assert weight == pytest.approx(case.optimal_weight, rel=0.0, abs=step)
    assert -1e-15 <= case.optimal_gain - gain <= case.relative_variance * step**2 / 8.0 + 1e-15


@pytest.mark.parametrize(
    "case",
    [c for c in MARGINAL_VALUE_FIXTURES if c.capped_gain is not None],
    ids=lambda c: c.name,
)
def test_constrained_optimum_is_the_projection_of_the_interior_one(case: SleeveCase) -> None:
    """Long-only and a 20% cap both bind by clipping ``w*``; equation (4) values the clip."""
    assert case.capped_weight is not None
    assert case.capped_gain is not None
    assert case.optimal_weight is not None
    assert case.optimal_gain is not None
    assert case.capped_weight == pytest.approx(
        min(max(case.optimal_weight, 0.0), WEIGHT_CAP), rel=0.0, abs=1e-14
    )
    realised = mix_growth_rate(case.capped_weight, case) - mix_growth_rate(0.0, case)
    assert realised == pytest.approx(case.capped_gain, rel=0.0, abs=RATE_TOLERANCE)
    # A constrained optimum is never better than the interior one, and no feasible weight
    # beats it.
    assert case.capped_gain <= case.optimal_gain + 1e-18
    feasible = np.linspace(0.0, WEIGHT_CAP, 2001)
    gains = mix_growth_rates(feasible, case) - mix_growth_rate(0.0, case)
    assert float(np.max(gains)) <= case.capped_gain + 1e-15


# --------------------------------------------------------------------------------------
# 2. The structural claims about the credit
# --------------------------------------------------------------------------------------


def test_zero_alpha_credit_is_exactly_sigma_p_squared_times_one_minus_beta() -> None:
    """With no standalone alpha the whole marginal value is ``sigma_p^2 (1 - beta)``."""
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    assert case.standalone == 0.0
    assert case.marginal_growth == pytest.approx(
        BASE_VARIANCE * (1.0 - case.beta), rel=0.0, abs=RATE_TOLERANCE
    )
    # 50 bp/yr of marginal rate. At the optimal 12.5% weight that is 3.125 bp of growth.
    assert case.credit == 0.005
    assert case.optimal_gain == 0.0003125


@pytest.mark.parametrize(
    "name", ["beta_one_moderate_volatility", "beta_one_high_volatility", "identical_clone"]
)
def test_beta_exactly_one_gives_exactly_zero_credit_at_any_volatility(name: str) -> None:
    """A unit-beta sleeve earns no diversification credit however volatile it is.

    Three sleeves with volatilities of 10%, 20% and 40% and correlations of 1.0, 0.5 and
    0.25 all have ``sigma_ip = sigma_p^2`` and therefore a credit of exactly zero. This is
    the fixture that separates a beta-based credit from a correlation-based one; an
    implementation that used ``1 - rho`` anywhere would give three different answers.
    """
    case = FIXTURES_BY_NAME[name]
    assert case.beta == 1.0
    assert case.credit == 0.0
    assert case.marginal_growth == case.standalone


def test_beta_above_one_makes_the_credit_strictly_negative() -> None:
    """The case most likely to be got wrong: a high-beta sleeve destroys growth.

    beta = 2.125 gives a credit of -112.5 bp, so 100 bp of standalone alpha still leaves a
    marginal value of -12.5 bp and a long-only allocation of exactly zero. An
    implementation that clipped the credit at zero, or that used ``|1 - beta|``, would
    report a positive marginal value here.
    """
    case = FIXTURES_BY_NAME["high_beta_positive_alpha"]
    assert case.beta > 1.0
    assert case.credit == -0.01125
    assert case.credit < 0.0
    assert case.standalone > 0.0
    assert case.marginal_growth < 0.0
    assert case.capped_weight == 0.0
    assert case.capped_gain == 0.0


def test_negative_standalone_alpha_can_still_be_worth_holding() -> None:
    """-50 bp of standalone drift plus a 124 bp credit is +74 bp of marginal value.

    The mirror of the high-beta case, and the reason neither term may be screened on
    alone. The sleeve is a 12%-volatility asset at rho = -0.2 that expects to *lose* 50 bp
    a year against the portfolio and is still worth a quarter of it.
    """
    case = FIXTURES_BY_NAME["negative_alpha_positive_total"]
    assert case.standalone < 0.0 < case.marginal_growth
    assert case.marginal_growth == pytest.approx(0.0074, rel=0.0, abs=RATE_TOLERANCE)
    assert case.optimal_weight == pytest.approx(0.2534246575342466, rel=0.0, abs=1e-14)


def test_a_clone_of_the_portfolio_has_exactly_zero_marginal_value() -> None:
    """``tau^2 = 0`` and ``D = 0``: the growth rate is flat in ``w`` and ``w*`` is 0/0.

    The right behaviour is to refuse, not to divide. A grid confirms flatness to machine
    precision so this is a statement about the objective, not about the formula.
    """
    case = FIXTURES_BY_NAME["identical_clone"]
    assert case.relative_variance == 0.0
    assert case.marginal_growth == 0.0
    assert case.optimal_weight is None
    for weight in (-3.0, -0.4, 0.0, 0.15, 1.0, 4.0):
        assert mix_growth_rate(weight, case) == pytest.approx(
            BASE_GROWTH, rel=0.0, abs=RATE_TOLERANCE
        )


@pytest.mark.parametrize("volatility", [0.05, 0.10, 0.20, 0.35, 0.60])
def test_a_zero_alpha_sleeve_can_never_add_more_than_half_the_base_variance(
    volatility: float,
) -> None:
    """Bound (5): ``gain <= sigma_p^2 / 2 = 50 bp/yr``, with equality only at ``|rho| = 1``.

    The bound is what stops the first-order term being a screen: ``D`` grows without limit
    as beta falls, but the achievable growth benefit does not. Checked here on a 2,001-point
    correlation grid at five sleeve volatilities.
    """
    ceiling = BASE_VARIANCE / 2.0
    best = -math.inf
    for rho in np.linspace(-1.0, 1.0, 2001):
        covariance = float(rho) * volatility * BASE_VOLATILITY
        marginal = BASE_VARIANCE - covariance
        relative_variance = volatility**2 - 2.0 * covariance + BASE_VARIANCE
        if relative_variance <= 0.0:
            continue
        best = max(best, marginal**2 / (2.0 * relative_variance))
        assert marginal**2 / (2.0 * relative_variance) <= ceiling + 1e-15
    assert best == pytest.approx(ceiling, rel=0.0, abs=1e-6)


def test_the_ceiling_is_attained_by_the_perfect_hedge_and_the_levered_clone() -> None:
    """Both ``rho = -1`` cases and ``rho = +1`` cases reach ``sigma_p^2 / 2`` exactly.

    At ``|rho| = 1`` the sleeve and the portfolio span a riskless position, so the optimum
    removes the entire variance drag. Only the ``rho = -1`` case does it at a positive
    weight; the ``rho = +1`` case needs a 100% short, which is why a long-only mandate
    cannot reach the bound with a high-beta clone.
    """
    hedge = FIXTURES_BY_NAME["perfect_hedge"]
    clone = FIXTURES_BY_NAME["perfectly_correlated_levered_clone"]
    assert hedge.optimal_gain == BASE_VARIANCE / 2.0
    assert clone.optimal_gain == BASE_VARIANCE / 2.0
    assert hedge.optimal_weight == pytest.approx(1.0 / 3.0, rel=0.0, abs=1e-15)
    assert clone.optimal_weight == -1.0
    # At w* the perfect hedge has literally zero variance, so g(w*) = mu(w*) = mu_p.
    assert mix_growth_rate(1.0 / 3.0, hedge) == pytest.approx(BASE_DRIFT, rel=0.0, abs=1e-15)


def test_the_cash_sleeve_reproduces_the_kelly_leverage_formula_exactly() -> None:
    """A zero-variance sleeve at rate ``r`` must give ``1 - w* = (mu_p - r) / sigma_p^2``.

    Algebraically ``w* = 1 - (mu_p - r) / sigma_p^2``, so the two-asset sleeve algebra and
    the one-risky-asset Kelly algebra are the same statement. This is the fixture that
    binds the new calculation to the audited :mod:`portfolio_edge.core.kelly`, and it is
    checked at three cash rates, not only the one in the fixture table.
    """
    case = FIXTURES_BY_NAME["cash_sleeve"]
    assert case.optimal_weight is not None
    assert 1.0 - case.optimal_weight == pytest.approx(
        kelly_leverage(excess_return=BASE_DRIFT - 0.02, volatility=BASE_VOLATILITY),
        rel=0.0,
        abs=1e-12,
    )
    for rate in (0.0, 0.01, 0.03, 0.05):
        marginal = (rate - BASE_DRIFT) + BASE_VARIANCE
        weight = marginal / BASE_VARIANCE
        assert 1.0 - weight == pytest.approx(
            kelly_leverage(excess_return=BASE_DRIFT - rate, volatility=BASE_VOLATILITY),
            rel=0.0,
            abs=1e-12,
        )
    # And the CE gain equals the peak-versus-unlevered growth gap: 0.10 - 0.055.
    assert case.optimal_gain == pytest.approx(0.045, rel=0.0, abs=1e-15)


# --------------------------------------------------------------------------------------
# 3. Discrete returns: the exact identity, in exact arithmetic
# --------------------------------------------------------------------------------------

TWO_SCENARIO_PORTFOLIO: tuple[Fraction, ...] = (Fraction(1, 4), Fraction(-1, 5))
TWO_SCENARIO_SLEEVE: tuple[Fraction, ...] = (Fraction(1, 20), Fraction(1, 20))

FOUR_SCENARIO_PORTFOLIO: tuple[Fraction, ...] = (
    Fraction(1, 5),
    Fraction(1, 10),
    Fraction(-1, 20),
    Fraction(-3, 20),
)
FOUR_SCENARIO_SLEEVE: tuple[Fraction, ...] = (
    Fraction(1, 10),
    Fraction(-1, 10),
    Fraction(1, 5),
    Fraction(0),
)


def _exact_discrete_marginal(
    portfolio: tuple[Fraction, ...], sleeve: tuple[Fraction, ...]
) -> Fraction:
    """Equation (6), ``E[(R_i - R_p) / (1 + R_p)]``, over equiprobable scenarios."""
    n = len(portfolio)
    return sum(
        ((b - a) / (1 + a) for a, b in zip(portfolio, sleeve, strict=True)), Fraction(0)
    ) / n


def _population_moments(
    portfolio: tuple[Fraction, ...], sleeve: tuple[Fraction, ...]
) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction]:
    """Population (divide by ``N``) moments. Using ``N - 1`` here is a units error."""
    n = len(portfolio)
    mu_p = sum(portfolio, Fraction(0)) / n
    mu_i = sum(sleeve, Fraction(0)) / n
    var_p = sum((x * x for x in portfolio), Fraction(0)) / n - mu_p * mu_p
    var_i = sum((x * x for x in sleeve), Fraction(0)) / n - mu_i * mu_i
    covariance = (
        sum((a * b for a, b in zip(portfolio, sleeve, strict=True)), Fraction(0)) / n
        - mu_p * mu_i
    )
    return mu_p, mu_i, var_p, var_i, covariance


def test_exact_discrete_marginal_value_two_scenarios() -> None:
    """Two equiprobable scenarios, constant sleeve. Exact rational answer, no tolerance.

    R_p in {+25%, -20%}, R_i = +5% always.
      E[(R_i - R_p)/(1 + R_p)] = (1/2)[(-0.20/1.25) + (0.25/0.80)]
                               = (1/2)(-4/25 + 5/16) = 61/800 = 0.07625 exactly.
    The continuous second-moment form gives (mu_i - mu_p) + sigma_p^2 - sigma_ip
      = 0.025 + 0.050625 = 121/1600 = 0.075625,
    which is 6.25 bp lower. The two are different quantities and neither is the other's
    approximation error at these volatilities: sigma_p here is 22.5%.
    """
    exact = _exact_discrete_marginal(TWO_SCENARIO_PORTFOLIO, TWO_SCENARIO_SLEEVE)
    assert exact == Fraction(61, 800)

    mu_p, mu_i, var_p, _var_i, covariance = _population_moments(
        TWO_SCENARIO_PORTFOLIO, TWO_SCENARIO_SLEEVE
    )
    assert (mu_p, mu_i, var_p, covariance) == (
        Fraction(1, 40),
        Fraction(1, 20),
        Fraction(81, 1600),
        Fraction(0),
    )
    continuous = (mu_i - mu_p) + var_p - covariance
    assert continuous == Fraction(121, 1600)
    assert float(exact - continuous) == pytest.approx(0.000625, rel=0.0, abs=1e-18)


def test_exact_discrete_optimum_differs_from_the_continuous_one() -> None:
    """The discrete optimum is ``w* = 1.525``; the continuous approximation says 1.4938.

    Solving ``d/dw [ (1/2) log(1.25 - 0.20 w) + (1/2) log(0.80 + 0.25 w) ] = 0``
    gives ``0.25 (1.25 - 0.20 w) = 0.20 (0.80 + 0.25 w)``, hence ``w* = 0.1525 / 0.10``.
    The continuous form gives ``D / tau^2 = 0.075625 / 0.050625``. A 2% difference in the
    optimal weight at a weight nobody would hold, but it is the same discrepancy that at
    realistic volatilities shows up as a systematic overstatement of the credit.
    """
    assert Fraction(1525, 1000) == Fraction(61, 40)
    grid = np.linspace(1.0, 2.0, 1_000_001)
    values = 0.5 * np.log(1.25 - 0.20 * grid) + 0.5 * np.log(0.80 + 0.25 * grid)
    assert float(grid[int(np.argmax(values))]) == pytest.approx(1.525, rel=0.0, abs=1e-6)
    continuous = float(Fraction(121, 1600) / Fraction(81, 1600))
    assert continuous == pytest.approx(1.4938271604938271, rel=0.0, abs=1e-14)


def test_exact_discrete_marginal_value_four_scenarios() -> None:
    """A sleeve with its own dispersion and a negative covariance, still exact.

    R_p = (+20%, +10%, -5%, -15%), R_i = (+10%, -10%, +20%, 0%), equiprobable.
      E[(R_i - R_p)/(1 + R_p)] = (1/4)(-1/12 - 2/11 + 5/19 + 3/17) = 7439/170544.
    Population moments: mu_p = 2.5%, mu_i = 5%, sigma_p^2 = 0.018125, sigma_ip = -0.00125,
    so the continuous form gives 0.044375. The gap is -7.56 bp, and it is not noise: it is
    the third-moment term that equation (6) keeps and the continuous form discards.
    """
    exact = _exact_discrete_marginal(FOUR_SCENARIO_PORTFOLIO, FOUR_SCENARIO_SLEEVE)
    assert exact == Fraction(7439, 170544)

    mu_p, mu_i, var_p, _var_i, covariance = _population_moments(
        FOUR_SCENARIO_PORTFOLIO, FOUR_SCENARIO_SLEEVE
    )
    assert (mu_p, mu_i, var_p, covariance) == (
        Fraction(1, 40),
        Fraction(1, 20),
        Fraction(29, 1600),
        Fraction(-1, 800),
    )
    continuous = (mu_i - mu_p) + var_p - covariance
    assert continuous == Fraction(71, 1600)
    assert float(exact) == pytest.approx(0.04361924195515527, rel=0.0, abs=1e-15)
    assert float(exact - continuous) * 1e4 == pytest.approx(-7.5575804, rel=0.0, abs=1e-6)


def test_the_continuous_form_overstates_the_credit_under_a_lognormal_match() -> None:
    """``mu - sigma^2/2`` is not the geometric mean, and the gap reaches the credit itself.

    Matching a lognormal to arithmetic mean ``mu`` and variance ``v`` gives
    ``g = log(1+mu) - (1/2) log(1 + v/(1+mu)^2)``. Differentiating at ``w = 0`` with zero
    standalone alpha gives a credit of ``(sigma_p^2 - sigma_ip) / ((1+mu_p)^2 + sigma_p^2)``,
    so at ``mu_p = 6%, sigma_p = 10%`` the continuous credit of 50.0 bp becomes 44.1 bp —
    the continuous convention overstates it by 13.4%. Reporting a marginal value without
    naming the convention is therefore worth roughly a tenth of the number itself.
    """
    scale = (1.0 + BASE_DRIFT) ** 2 + BASE_VARIANCE
    assert scale == pytest.approx(1.1336, rel=0.0, abs=1e-12)
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    lognormal_credit = case.credit / scale
    assert lognormal_credit == pytest.approx(0.0044107268877911, rel=0.0, abs=1e-14)
    assert case.credit / lognormal_credit == pytest.approx(1.1336, rel=0.0, abs=1e-12)

    # And the level gap, which is the same error one order up.
    def lognormal_growth(mu: float, variance: float) -> float:
        return math.log1p(mu) - 0.5 * math.log1p(variance / (1.0 + mu) ** 2)

    assert (BASE_DRIFT - BASE_VARIANCE / 2.0) - lognormal_growth(
        BASE_DRIFT, BASE_VARIANCE
    ) == pytest.approx(0.00116139, rel=0.0, abs=1e-8)
    assert (0.08 - 0.15**2 / 2.0) - lognormal_growth(0.08, 0.15**2) == pytest.approx(
        0.00134217, rel=0.0, abs=1e-8
    )


# --------------------------------------------------------------------------------------
# 4. Annualisation
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", MARGINAL_VALUE_FIXTURES, ids=lambda c: c.name)
def test_monthly_and_annual_parameters_give_consistent_answers(case: SleeveCase) -> None:
    """Rates and variances scale by 1/12; ``beta`` and ``w*`` do not scale at all.

    This is the units fixture. Under iid periods the credit and the CE gain are per-period
    *variances* and annualise by multiplying by 12, while ``w*`` is a ratio of two things
    that both scale and is therefore identical at both frequencies.
    """
    months = 12.0
    monthly_variance = BASE_VARIANCE / months
    monthly_covariance = case.covariance / months
    monthly_standalone = case.standalone / months
    monthly_credit = monthly_variance - monthly_covariance
    monthly_marginal = monthly_standalone + monthly_credit
    monthly_relative_variance = case.volatility**2 / months - 2.0 * monthly_covariance + (
        monthly_variance
    )

    assert monthly_covariance / monthly_variance == pytest.approx(case.beta, rel=0.0, abs=1e-14)
    assert monthly_credit * months == pytest.approx(case.credit, rel=0.0, abs=RATE_TOLERANCE)
    assert monthly_marginal * months == pytest.approx(
        case.marginal_growth, rel=0.0, abs=RATE_TOLERANCE
    )
    if case.optimal_weight is None:
        assert monthly_relative_variance == pytest.approx(0.0, rel=0.0, abs=1e-18)
        return
    assert case.optimal_gain is not None
    assert monthly_marginal / monthly_relative_variance == pytest.approx(
        case.optimal_weight, rel=0.0, abs=1e-13
    )
    assert (
        monthly_marginal**2 / (2.0 * monthly_relative_variance) * months
    ) == pytest.approx(case.optimal_gain, rel=0.0, abs=1e-15)


def test_the_square_root_of_twelve_annualisation_is_caught() -> None:
    """Annualising a credit by ``sqrt(12)`` gives 144 bp where the answer is 50 bp.

    The credit is a variance, not a volatility. The wrong convention is off by
    ``sqrt(12) = 3.46x`` and looks entirely plausible on a report, which is why it is
    pinned as a literal here rather than left as a warning.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    monthly_credit = (BASE_VARIANCE - case.covariance) / 12.0
    assert monthly_credit * 12.0 == pytest.approx(0.005, rel=0.0, abs=RATE_TOLERANCE)
    wrong = monthly_credit * math.sqrt(12.0)
    assert wrong == pytest.approx(0.00144337567297, rel=0.0, abs=1e-12)
    assert wrong / 0.005 == pytest.approx(0.28867513459, rel=0.0, abs=1e-10)


# --------------------------------------------------------------------------------------
# 5. Where the framing misleads
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("weight", "linear", "exact", "ratio"),
    [
        # linear = w D = 0.005 w;  exact = 0.005 w - 0.02 w^2  (tau^2 / 2 = 0.02)
        (0.05, 0.00025, 0.00020, 1.25),
        (0.10, 0.00050, 0.00030, 5.0 / 3.0),
        (0.125, 0.000625, 0.0003125, 2.0),
        (0.15, 0.00075, 0.00030, 2.5),
        (0.20, 0.00100, 0.00020, 5.0),
    ],
)
def test_the_first_order_term_overstates_the_gain_at_the_weights_under_discussion(
    weight: float, linear: float, exact: float, ratio: float
) -> None:
    """At 5% the linear term is 25% high; at 20% it is 400% high.

    The overstatement is ``1 / (1 - w / (2 w*))``, so it is exactly 2x at ``w*`` itself and
    infinite at ``2 w* = 25%``, where the sleeve adds nothing at all. Quoting ``D`` as
    "the sleeve is worth 50 bp" is therefore only defensible per infinitesimal unit of
    weight; at any weight anyone would actually hold it is wrong by a factor between two
    and five.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    assert weight * case.marginal_growth == pytest.approx(linear, rel=0.0, abs=1e-15)
    realised = mix_growth_rate(weight, case) - mix_growth_rate(0.0, case)
    assert realised == pytest.approx(exact, rel=0.0, abs=1e-15)
    assert linear / exact == pytest.approx(ratio, rel=0.0, abs=1e-12)


def test_a_five_percent_and_a_twenty_percent_allocation_are_worth_exactly_the_same() -> None:
    """The parabola is symmetric about ``w* = 12.5%``, so ``g(5%) = g(20%)`` exactly.

    Both deliver 2.00 bp/yr. The first-order term says the 20% sleeve is worth four times
    the 5% sleeve. There is no weight at which the linear reading and the actual objective
    agree except zero, and the discrepancy is not small at the weights a sleeve discussion
    is actually about.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    assert mix_growth_rate(0.05, case) == pytest.approx(
        mix_growth_rate(0.20, case), rel=0.0, abs=1e-17
    )
    assert mix_growth_rate(0.05, case) - BASE_GROWTH == pytest.approx(
        0.0002, rel=0.0, abs=1e-15
    )
    # And 25% — twice w* — is worth exactly nothing.
    assert mix_growth_rate(0.25, case) == pytest.approx(BASE_GROWTH, rel=0.0, abs=1e-17)


@pytest.mark.parametrize(
    ("rate", "cash_funded"),
    [
        # cash-funded marginal value = (mu_i - r) - sigma_ip, with mu_i = 6%, sigma_ip = 0.005
        (0.01, 0.045),
        (0.02, 0.035),
        (0.05, 0.005),
    ],
)
def test_the_funding_convention_changes_the_answer_by_an_order_of_magnitude(
    rate: float, cash_funded: float
) -> None:
    """Pro rata gives 50 bp; cash-financed at 1% gives 450 bp for the same sleeve.

    The difference is ``sigma_p^2 - (mu_p - r)``, so the two conventions agree **iff the
    base portfolio is at full Kelly** (``mu_p - r = sigma_p^2``, here ``r = 5%``). Neither
    is wrong; a number reported without its convention is.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    computed = (case.drift - rate) - case.covariance
    assert computed == pytest.approx(cash_funded, rel=0.0, abs=RATE_TOLERANCE)
    assert case.marginal_growth - computed == pytest.approx(
        BASE_VARIANCE - (BASE_DRIFT - rate), rel=0.0, abs=RATE_TOLERANCE
    )
    agree = math.isclose(case.marginal_growth, computed, abs_tol=1e-15)
    at_full_kelly = math.isclose(
        kelly_leverage(excess_return=BASE_DRIFT - rate, volatility=BASE_VOLATILITY),
        1.0,
        abs_tol=1e-12,
    )
    assert agree == at_full_kelly


@pytest.mark.parametrize(
    ("estimated_correlation", "weight", "believed_gain", "realised_gain"),
    [
        # D(rho) = 0.01 - 0.02 rho;  tau^2(rho) = 0.05 - 0.02 rho;  w* = D / tau^2
        # believed = D^2 / (2 tau^2);  realised = w D_true - w^2 tau^2_true / 2 at rho = 0.25
        (0.15, 0.15909090909090909, 0.00055681818181818, 0.00028925619834710),
        (0.20, 0.14285714285714285, 0.00042857142857142, 0.00030612244897959),
        (0.25, 0.125, 0.0003125, 0.0003125),
        (0.30, 0.10526315789473684, 0.00021052631578947, 0.00030470914127424),
        (0.35, 0.08333333333333333, 0.000125, 0.00027777777777777),
    ],
)
def test_a_correlation_error_distorts_the_claim_far_more_than_the_allocation(
    estimated_correlation: float,
    weight: float,
    believed_gain: float,
    realised_gain: float,
) -> None:
    """rho off by 0.10 moves ``w*`` by 27% but the reported CE gain by 78%.

    The true sleeve is ``rho = 0.25``, ``w* = 12.5%``, gain 3.125 bp. Believing
    ``rho = 0.15`` gives ``w* = 15.9%`` and a *claimed* 5.57 bp, while the growth actually
    delivered at that wrong weight is 2.89 bp — only 0.23 bp, or 7.4%, below the best
    available. The objective is flat near its optimum, so covariance error is cheap in
    allocation and expensive in narrative.
    """
    marginal = BASE_VARIANCE - estimated_correlation * 0.20 * BASE_VOLATILITY
    relative_variance = 0.04 - 2.0 * estimated_correlation * 0.02 + BASE_VARIANCE
    assert marginal / relative_variance == pytest.approx(weight, rel=0.0, abs=1e-14)
    assert marginal**2 / (2.0 * relative_variance) == pytest.approx(
        believed_gain, rel=0.0, abs=1e-15
    )
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    realised = mix_growth_rate(weight, case) - mix_growth_rate(0.0, case)
    assert realised == pytest.approx(realised_gain, rel=0.0, abs=1e-15)
    assert case.optimal_gain is not None
    assert realised <= case.optimal_gain + 1e-18


def test_analytic_correlation_sensitivities() -> None:
    """``dw*/drho = sigma_i sigma_p (2 w* - 1) / tau^2`` and ``dG/drho = sigma_i sigma_p w*(w*-1)``.

    Derived by differentiating (2) and (3) in ``rho`` through ``sigma_ip`` and ``tau^2``:
    ``dD/drho = -sigma_i sigma_p`` and ``dtau^2/drho = -2 sigma_i sigma_p``. At the
    reference sleeve these are -0.375 weight units and -0.0021875 growth units per unit of
    correlation, i.e. **each 0.01 of correlation error moves the reported CE gain by
    0.219 bp, which is 7.0% of the entire 3.125 bp the sleeve is worth**. Confirmed
    against a central finite difference of the closed forms.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    assert case.optimal_weight is not None
    assert case.optimal_gain is not None
    product = case.volatility * BASE_VOLATILITY
    weight_sensitivity = product * (2.0 * case.optimal_weight - 1.0) / case.relative_variance
    gain_sensitivity = product * case.optimal_weight * (case.optimal_weight - 1.0)
    assert weight_sensitivity == pytest.approx(-0.375, rel=0.0, abs=1e-15)
    assert gain_sensitivity == pytest.approx(-0.0021875, rel=0.0, abs=1e-15)
    assert abs(gain_sensitivity) * 0.01 / case.optimal_gain == pytest.approx(
        0.07, rel=0.0, abs=1e-12
    )

    def optimum(rho: float) -> tuple[float, float]:
        marginal = BASE_VARIANCE - rho * product
        relative_variance = case.volatility**2 - 2.0 * rho * product + BASE_VARIANCE
        return marginal / relative_variance, marginal**2 / (2.0 * relative_variance)

    step = 1e-6
    high, low = optimum(0.25 + step), optimum(0.25 - step)
    assert (high[0] - low[0]) / (2.0 * step) == pytest.approx(
        weight_sensitivity, rel=0.0, abs=1e-8
    )
    assert (high[1] - low[1]) / (2.0 * step) == pytest.approx(
        gain_sensitivity, rel=0.0, abs=1e-10
    )


@pytest.mark.parametrize(
    ("years", "correlation_error", "beta_error", "credit_error", "drift_error"),
    [
        # SE(rho)  = (1 - rho^2) / sqrt(n - 3)     [Fisher z, rho = 0.25]
        # SE(beta) = (sigma_i sqrt(1 - rho^2) / sigma_p) / sqrt(n)  = 1.93649 / sqrt(n)
        # SE(credit) = sigma_p^2 SE(beta)
        # SE(mu_i - mu_p) = tau / sqrt(years) = 0.20 / sqrt(years)
        (10, 0.0866719, 0.1767767, 0.00176777, 0.0632456),
        (20, 0.0608972, 0.1250000, 0.00125000, 0.0447214),
        (50, 0.0383693, 0.0790569, 0.00079057, 0.0282843),
    ],
)
def test_sampling_standard_errors_of_the_two_terms(
    years: int,
    correlation_error: float,
    beta_error: float,
    credit_error: float,
    drift_error: float,
) -> None:
    """The credit is measurable and the standalone term is not, at every realistic sample.

    At 20 years of monthly data the diversification credit of the reference sleeve is
    50.0 +/- 12.5 bp (``t = 4.0``) while its standalone term carries a standard error of
    **447 bp/yr** against a total marginal value of 50 bp (``t = 0.11``). Fifty years only
    takes that to ``t = 0.18``. Any claim that a sleeve's marginal value is positive
    because of its expected return is therefore untestable at any sample this repository
    can obtain, and the honest object is the credit alone.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    n = years * 12
    residual = case.volatility * math.sqrt(1.0 - case.correlation**2)
    assert (1.0 - case.correlation**2) / math.sqrt(n - 3) == pytest.approx(
        correlation_error, rel=0.0, abs=1e-7
    )
    assert (residual / BASE_VOLATILITY) / math.sqrt(n) == pytest.approx(
        beta_error, rel=0.0, abs=1e-7
    )
    assert BASE_VARIANCE * (residual / BASE_VOLATILITY) / math.sqrt(n) == pytest.approx(
        credit_error, rel=0.0, abs=1e-8
    )
    assert math.sqrt(case.relative_variance / years) == pytest.approx(
        drift_error, rel=0.0, abs=1e-7
    )
    if years == 20:
        assert case.credit / credit_error == pytest.approx(4.0, rel=0.0, abs=1e-4)
        assert case.marginal_growth / drift_error == pytest.approx(0.1118, rel=0.0, abs=1e-4)


def test_the_sign_of_the_estimated_marginal_value_is_a_coin_flip() -> None:
    """With ``mu`` estimated from 20 years of monthly data, ``P(estimated D < 0) = 45%``.

    ``D_hat = (mu_i - mu_p)_hat + credit`` has standard deviation 447 bp around a true
    value of 50 bp, so the probability that a 20-year sample reports a *negative* marginal
    value for a sleeve that genuinely has a positive one is
    ``Phi(-0.05 / 0.4472) = 0.4555``. Reporting the point estimate without this is the
    single most misleading thing this calculation can do.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    standard_error = math.sqrt(case.relative_variance / 20.0)
    assert standard_error == pytest.approx(0.0447213595, rel=0.0, abs=1e-9)
    probability = 0.5 * math.erfc(case.marginal_growth / (standard_error * math.sqrt(2.0)))
    assert probability == pytest.approx(0.45549, rel=0.0, abs=1e-5)


@pytest.mark.parametrize(
    ("candidates", "inflation"),
    # E[max of k iid N(0, s)] ~ s sqrt(2 log k) with s = SE(credit) = 12.5 bp at 20y monthly
    [(5, 0.00224265), (10, 0.00268246), (20, 0.00305968), (50, 0.00349644)],
)
def test_selecting_the_best_of_k_sleeves_inflates_the_measured_credit(
    candidates: int, inflation: float
) -> None:
    """Ranking 20 candidates adds ~31 bp of pure noise to a true 50 bp credit.

    ``SE(credit) = 12.5 bp`` at 20 years of monthly data, so the expected maximum of ``k``
    independent zero-mean estimation errors is ``12.5 sqrt(2 log k)`` bp. At ``k = 20``
    that is 30.6 bp, a 61% overstatement, before a single return has been forecast. The
    credit is the *measurable* half of this decomposition and it is still not safe to
    report a selected maximum of it.
    """
    residual_ratio = 0.20 * math.sqrt(1.0 - 0.25**2) / BASE_VOLATILITY
    standard_error = BASE_VARIANCE * residual_ratio / math.sqrt(240)
    assert standard_error == pytest.approx(0.00125, rel=0.0, abs=1e-9)
    assert standard_error * math.sqrt(2.0 * math.log(candidates)) == pytest.approx(
        inflation, rel=0.0, abs=1e-8
    )
    if candidates == 20:
        assert inflation / 0.005 == pytest.approx(0.611937, rel=0.0, abs=1e-5)


@pytest.mark.parametrize(
    ("cost", "weight", "gain"),
    [
        # Costs reduce mu_i, hence D, and w* and the gain are re-solved: not haircut.
        # D_net = 0.005 - c;  w* = D_net / 0.04;  gain = D_net^2 / 0.08
        (0.0000, 0.125, 0.0003125),
        (0.0010, 0.100, 0.0002000),
        (0.0025, 0.0625, 0.0000781250),
        (0.0050, 0.0, 0.0),
        (0.0060, 0.0, 0.0),
    ],
)
def test_costs_enter_through_the_optimum_and_the_gain_falls_quadratically(
    cost: float, weight: float, gain: float
) -> None:
    """Break-even all-in cost is exactly ``D``; half of it leaves a quarter of the gain.

    A 25 bp sleeve fee against a 50 bp marginal rate removes 75% of the growth benefit,
    leaving 0.78 bp/yr, and 50 bp removes all of it. Since 25 bp is a cheap systematic
    sleeve and 50 bp is an ordinary one, the reference sleeve — zero alpha, beta 0.5,
    twice the portfolio's volatility — is not investable at any realistic fee.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    net = case.marginal_growth - cost
    optimal = max(net, 0.0) / case.relative_variance
    assert optimal == pytest.approx(weight, rel=0.0, abs=1e-14)
    assert max(net, 0.0) ** 2 / (2.0 * case.relative_variance) == pytest.approx(
        gain, rel=0.0, abs=1e-15
    )


# --------------------------------------------------------------------------------------
# 6. Monte Carlo: the model's growth rate is a claim, not algebra
# --------------------------------------------------------------------------------------

MONTE_CARLO_SEED = 20260812
"""Same committed seed as :mod:`portfolio_edge.studies.rebalancing_monte_carlo`."""


def _simulate_growth_gains(
    case: SleeveCase,
    weights: tuple[float, ...],
    *,
    years: float = 30.0,
    steps_per_year: int = 52,
    paths: int = 40_000,
) -> tuple[FloatArray, FloatArray]:
    """Paired-path annual log growth gain over ``w = 0`` for each weight, and its SE.

    Continuously rebalanced is approximated by weekly rebalancing, which by the study in
    :mod:`portfolio_edge.studies.volatility_harvesting` captures essentially all of the
    excess growth term at these volatilities. Paths are shared across weights, so the
    differences are paired and the level's Monte Carlo error cancels.
    """
    rng = np.random.default_rng(MONTE_CARLO_SEED)
    steps = round(years * steps_per_year)
    dt = 1.0 / steps_per_year
    covariance = np.array(
        [
            [BASE_VARIANCE, case.covariance],
            [case.covariance, case.volatility**2],
        ],
        dtype=np.float64,
    )
    factor = np.linalg.cholesky(covariance + np.eye(2) * 1e-18)
    log_drift = (
        np.array([BASE_DRIFT, case.drift], dtype=np.float64)
        - 0.5 * np.diag(covariance)
    ) * dt

    totals = np.zeros((len(weights), paths), dtype=np.float64)
    done = 0
    while done < paths:
        size = min(2_000, paths - done)
        shocks = rng.standard_normal((size, steps, 2)) @ factor.T
        relatives = np.exp(log_drift + math.sqrt(dt) * shocks)
        for index, weight in enumerate(weights):
            mix = relatives @ np.array([1.0 - weight, weight], dtype=np.float64)
            totals[index, done : done + size] = np.log(mix).sum(axis=1) / years
        done += size

    gains = totals[1:] - totals[0]
    return (
        np.asarray(gains.mean(axis=1), dtype=np.float64),
        np.asarray(gains.std(axis=1, ddof=1) / math.sqrt(paths), dtype=np.float64),
    )


@pytest.mark.parametrize(
    ("name", "weights"),
    [
        ("zero_alpha_low_beta", (0.0, 0.05, 0.125, 0.20)),
        ("high_beta_positive_alpha", (0.0, 0.05, 0.20)),
        ("negative_alpha_positive_total", (0.0, 0.2534246575342466)),
        ("perfect_hedge", (0.0, 1.0 / 3.0)),
    ],
)
def test_monte_carlo_reproduces_the_closed_form_gain(name: str, weights: tuple[float, ...]) -> None:
    """Seeded 40,000-path simulation of the rebalanced mix, within four standard errors.

    The simulation never evaluates ``mu(w)`` or ``sigma^2(w)``: it draws correlated GBM
    price relatives and compounds ``log(1 + (1-w) r_p + w r_i)`` step by step. Agreement
    therefore tests that ``mu - sigma^2/2`` is the growth rate of the object the algebra
    claims, which is the part of the derivation that is a modelling claim rather than a
    manipulation. The tolerance is the simulation's own standard error, not a tuned number.
    """
    case = FIXTURES_BY_NAME[name]
    means, errors = _simulate_growth_gains(case, weights)
    for weight, mean, error in zip(weights[1:], means, errors, strict=True):
        expected = mix_growth_rate(weight, case) - mix_growth_rate(0.0, case)
        assert abs(mean - expected) < 4.0 * error


def test_monte_carlo_confirms_the_five_and_twenty_percent_weights_are_equivalent() -> None:
    """The symmetry ``g(5%) = g(20%)`` survives simulation: a falsifiable prediction.

    A first-order marginal-value reading predicts the 20% sleeve is worth four times the
    5% sleeve. The simulation, which knows nothing of either formula, finds no difference
    within its standard error.
    """
    case = FIXTURES_BY_NAME["zero_alpha_low_beta"]
    means, errors = _simulate_growth_gains(case, (0.0, 0.05, 0.20))
    difference = float(means[1] - means[0])
    # The two gains share paths, so their difference has roughly the larger standard error.
    assert abs(difference) < 4.0 * float(max(errors))
    assert float(means[0]) > 0.0
