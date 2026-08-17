"""The retail-shelf arithmetic, against fixtures computed independently of it.

Every expectation here is either hand-computed or derived from a construction whose
answer is known before the function runs. Nothing is recorded from a run. A fixture
that disagrees with the implementation is a finding, not a tolerance to loosen.

The three that carry the most weight:

* :func:`test_buffer_payoff_is_the_hand_computed_piecewise` pins the payoff at all
  four regions and at both kinks, because an off-by-one at a kink would flatter the
  structure exactly where the marketing does.
* :func:`test_matched_volatility_gap_equals_sigma_times_the_sharpe_difference` proves
  the identity the module claims licenses a HAC standard error on the gap.
* :func:`test_piecewise_beta_recovers_a_planted_asymmetry` plants known up- and
  down-market betas in noiseless data and requires them back.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.factor_breadth import FIRST_ORDER_CORRELATION_LIMIT
from portfolio_edge.studies.retail_shelf import (
    BufferTerms,
    buffer_cost_decomposition,
    buffer_payoff,
    choose_instrument,
    factor_regression,
    matched_volatility,
    piecewise_beta,
    sharpe_ratio,
)

#: A 15% buffer and a 12% cap: PJUL's contracted buffer and roughly the mean of the
#: nine starting caps it has actually published. The dividend and fee are the numbers
#: the study uses, kept here so the fixture is the real product rather than a stylised
#: one.
PJUL_LIKE = BufferTerms(buffer=0.15, cap=0.12, forgone_dividend_yield=0.02, fee=0.0079)


# --------------------------------------------------------------------------------
# The buffer payoff
# --------------------------------------------------------------------------------


def test_buffer_payoff_is_the_hand_computed_piecewise() -> None:
    """Both kinks and all four regions, worked out by hand from the definition."""
    # Above the cap: capped.
    assert buffer_payoff(0.30, PJUL_LIKE) == pytest.approx(0.12)
    # Exactly at the cap: the cap, and not one basis point more.
    assert buffer_payoff(0.12, PJUL_LIKE) == pytest.approx(0.12)
    # Below the cap and positive: uncapped.
    assert buffer_payoff(0.05, PJUL_LIKE) == pytest.approx(0.05)
    # Zero is zero under both branches, which is what makes the kink well defined.
    assert buffer_payoff(0.0, PJUL_LIKE) == pytest.approx(0.0)
    # Inside the buffer: flat at zero, however far in.
    assert buffer_payoff(-0.01, PJUL_LIKE) == pytest.approx(0.0)
    assert buffer_payoff(-0.15, PJUL_LIKE) == pytest.approx(0.0)
    # Through the buffer: loss less the buffer, one for one.
    assert buffer_payoff(-0.20, PJUL_LIKE) == pytest.approx(-0.05)
    assert buffer_payoff(-0.50, PJUL_LIKE) == pytest.approx(-0.35)


def test_buffer_payoff_is_price_plus_put_spread_minus_short_call() -> None:
    """The decomposition the module documents, checked at forty points.

    ``payoff = r + max(0, min(buffer, -r)) - max(0, r - cap)``. If this identity ever
    fails, :func:`buffer_cost_decomposition`'s "protection received" and "upside sold"
    columns stop adding up to what the fund did, and the whole pricing section becomes
    two unrelated numbers printed side by side.
    """
    for value in np.linspace(-0.60, 0.60, 41):
        expected = (
            value
            + max(0.0, min(PJUL_LIKE.buffer, -value))
            - max(0.0, value - PJUL_LIKE.cap)
        )
        assert buffer_payoff(float(value), PJUL_LIKE) == pytest.approx(expected)


def test_buffer_cost_decomposition_on_four_hand_computed_returns() -> None:
    """Four price returns chosen so every column is a decimal done on paper.

    Returns +0.30, +0.05, -0.10 and -0.20 against a 15% buffer and a 12% cap.

    * protection received: 0, 0, 0.10, 0.15 -> mean 0.0625
    * upside sold: 0.18, 0, 0, 0 -> mean 0.045
    * net option value: 0.0625 - 0.045 = 0.0175
    * payoffs: 0.12, 0.05, 0, -0.05 -> mean 0.03
    * capped in 1 of 4, negative in 2 of 4, through the buffer in 1 of 4
    * total shortfall: 0.0175 - 0.02 - 0.0079 = -0.0104
    """
    result = buffer_cost_decomposition(
        [0.30, 0.05, -0.10, -0.20], PJUL_LIKE, label="hand"
    )

    assert result.periods == 4
    assert result.mean_protection_received == pytest.approx(0.0625)
    assert result.mean_upside_sold == pytest.approx(0.045)
    assert result.net_option_value == pytest.approx(0.0175)
    assert result.mean_buffer_payoff == pytest.approx(0.03)
    assert result.capped_fraction == pytest.approx(0.25)
    assert result.buffer_used_fraction == pytest.approx(0.50)
    assert result.buffer_exceeded_fraction == pytest.approx(0.25)
    assert result.total_shortfall == pytest.approx(-0.0104)


def test_buffer_terms_require_a_stated_forgone_dividend() -> None:
    """The dividend the wrapper gives up has no default, and must not acquire one.

    A buffer fund holds options on the reference asset's price, so its holders receive
    none of its dividends. That is a certain recurring cost invisible in the cap and
    the buffer, and defaulting it to zero would hide the single largest term in the
    whole comparison.
    """
    with pytest.raises(TypeError):
        BufferTerms(buffer=0.15, cap=0.12)  # type: ignore[call-arg]


def test_buffer_terms_reject_impossible_parameters() -> None:
    with pytest.raises(ValueError, match="buffer must lie"):
        BufferTerms(buffer=1.0, cap=0.12, forgone_dividend_yield=0.02)
    with pytest.raises(ValueError, match="cap must be positive"):
        BufferTerms(buffer=0.15, cap=0.0, forgone_dividend_yield=0.02)
    with pytest.raises(ValueError, match="forgone dividend"):
        BufferTerms(buffer=0.15, cap=0.12, forgone_dividend_yield=-0.01)


# --------------------------------------------------------------------------------
# Which instrument, and why
# --------------------------------------------------------------------------------


def test_choose_instrument_switches_exactly_at_the_documented_limit() -> None:
    """At and inside the limit, equation (4); outside it, equation (5), both signs."""
    inside = choose_instrument(label="x", correlation=FIRST_ORDER_CORRELATION_LIMIT)
    assert inside.instrument == "admission_equation_4"
    assert inside.first_order_admission_is_usable

    outside = choose_instrument(
        label="x", correlation=FIRST_ORDER_CORRELATION_LIMIT + 1e-9
    )
    assert outside.instrument == "matched_volatility_equation_5"
    assert not outside.first_order_admission_is_usable

    negative = choose_instrument(label="x", correlation=-0.9)
    assert negative.instrument == "matched_volatility_equation_5"


def test_choose_instrument_puts_a_dividend_fund_on_equation_five() -> None:
    """The measured correlations, so the classification cannot silently drift.

    SCHD's correlation to VTI over the N-PORT window is +0.82 and bitcoin's to the
    market factor is +0.34. If a future change moved either across the boundary, the
    audit page's claim about which instrument scored which family would be wrong, and
    that claim is the point of the page.
    """
    assert choose_instrument(label="SCHD", correlation=0.820).instrument == (
        "matched_volatility_equation_5"
    )
    assert choose_instrument(label="BTC", correlation=0.342).instrument == (
        "admission_equation_4"
    )


def test_choose_instrument_rejects_an_impossible_correlation() -> None:
    with pytest.raises(ValueError, match="must lie in"):
        choose_instrument(label="x", correlation=1.5)


# --------------------------------------------------------------------------------
# Equation (5)
# --------------------------------------------------------------------------------


def _deterministic_pair(seed: int) -> tuple[np.ndarray, np.ndarray]:
    generator = np.random.default_rng(seed)
    base = 0.008 + 0.04 * generator.standard_normal(240)
    sleeve = 0.004 + 0.7 * base + 0.02 * generator.standard_normal(240)
    return sleeve, base


def test_matched_volatility_gap_equals_sigma_times_the_sharpe_difference() -> None:
    """``gap = sigma_target (S_d - S_p)``, computed from the moments rather than read.

    This is the identity the module's docstring claims, and it is what makes a HAC
    standard error on the paired series a standard error on a growth difference. It is
    verified here against Sharpe ratios computed by a separate function.
    """
    sleeve, base = _deterministic_pair(seed=20260817)
    verdict = matched_volatility(sleeve, base, label="pair")

    expected = verdict.target_volatility * (
        sharpe_ratio(sleeve) - sharpe_ratio(base)
    )
    assert verdict.growth_gap == pytest.approx(expected, rel=1e-12)
    assert verdict.target_volatility == pytest.approx(verdict.base_volatility)


def test_matched_volatility_is_exactly_zero_against_itself() -> None:
    """A control with a known answer: the base against the base gains nothing.

    The repository found a de-risking artefact worth +0.809 pp/yr with a control of
    this shape, and controls-with-known-answers are the pattern that found it.
    """
    _, base = _deterministic_pair(seed=7)
    verdict = matched_volatility(base, base, label="self")

    assert verdict.growth_gap == pytest.approx(0.0, abs=1e-12)
    assert verdict.sharpe_gap == pytest.approx(0.0, abs=1e-12)
    assert not verdict.wins


def test_matched_volatility_is_invariant_to_the_target_volatility_sign_and_test() -> None:
    """Rescaling the target scales the gap and leaves the t statistic alone."""
    sleeve, base = _deterministic_pair(seed=11)
    one = matched_volatility(sleeve, base, label="a")
    two = matched_volatility(sleeve, base, label="b", target_volatility=2.0 * one.base_volatility)

    assert two.growth_gap == pytest.approx(2.0 * one.growth_gap, rel=1e-12)
    assert two.t_statistic == pytest.approx(one.t_statistic, rel=1e-12)


def test_matched_volatility_refuses_ragged_windows() -> None:
    sleeve, base = _deterministic_pair(seed=3)
    with pytest.raises(ValueError, match="align them on a common window"):
        matched_volatility(sleeve[:-5], base, label="ragged")


def test_a_gap_below_its_own_detection_floor_is_flagged_unresolved() -> None:
    """``resolved`` reads the floor, not the sign.

    Constructed so the two series have nearly identical Sharpe ratios: the gap is tiny,
    the standard error is not, and the verdict must say so rather than report a
    direction.
    """
    generator = np.random.default_rng(99)
    base = 0.008 + 0.04 * generator.standard_normal(96)
    sleeve = base + 1e-5 * generator.standard_normal(96)
    verdict = matched_volatility(sleeve, base, label="twin")

    assert abs(verdict.growth_gap) < verdict.mde_80
    assert not verdict.resolved


# --------------------------------------------------------------------------------
# Regressions
# --------------------------------------------------------------------------------


def test_factor_regression_recovers_planted_coefficients_without_noise() -> None:
    """Noiseless data with a known intercept and two known loadings.

    The intercept is 0.001 a month, so the annualised alpha must be 0.012 exactly.
    """
    generator = np.random.default_rng(20260817)
    first = generator.standard_normal(200) * 0.04
    second = generator.standard_normal(200) * 0.02
    response = 0.001 + 0.8 * first - 0.3 * second

    regression = factor_regression(
        response, [first, second], label="planted", factor_names=("one", "two")
    )

    assert regression.alpha == pytest.approx(0.012, abs=1e-12)
    assert regression.loading("one") == pytest.approx(0.8, abs=1e-12)
    assert regression.loading("two") == pytest.approx(-0.3, abs=1e-12)
    assert regression.r_squared == pytest.approx(1.0, abs=1e-12)


def test_factor_regression_refuses_a_name_count_mismatch() -> None:
    generator = np.random.default_rng(1)
    column = generator.standard_normal(50)
    with pytest.raises(ValueError, match="factor series but"):
        factor_regression(column, [column], label="x", factor_names=("a", "b"))


def test_piecewise_beta_recovers_a_planted_asymmetry() -> None:
    """Up beta 0.45 and down beta 0.86, the shape the audit measured for put-writing.

    Built noiselessly from the market series itself, so the two betas and their
    difference are known before the regression runs. The put-writing ordering is the
    one a buffer structure has to invert, and a sign error here would report that
    inversion where it does not exist.
    """
    generator = np.random.default_rng(5)
    market = generator.standard_normal(300) * 0.04
    sleeve = np.where(market < 0.0, 0.86 * market, 0.45 * market)

    result = piecewise_beta(sleeve, market, label="planted")

    assert result.up_beta == pytest.approx(0.45, abs=1e-12)
    assert result.down_beta == pytest.approx(0.86, abs=1e-12)
    assert result.asymmetry == pytest.approx(0.41, abs=1e-12)
    assert not result.protects


def test_piecewise_beta_calls_a_genuine_protector_a_protector() -> None:
    generator = np.random.default_rng(6)
    market = generator.standard_normal(300) * 0.04
    sleeve = np.where(market < 0.0, 0.40 * market, 0.60 * market)

    result = piecewise_beta(sleeve, market, label="protector")

    assert result.protects
    assert result.asymmetry == pytest.approx(-0.20, abs=1e-12)


def test_piecewise_beta_refuses_a_window_with_no_down_months() -> None:
    market = np.linspace(0.01, 0.05, 60)
    with pytest.raises(ValueError, match="at least two up months and two down months"):
        piecewise_beta(market, market, label="all up")


# --------------------------------------------------------------------------------
# Sharpe
# --------------------------------------------------------------------------------


def test_sharpe_ratio_is_the_hand_computed_annualisation() -> None:
    """Mean 0.01, sample standard deviation 0.02, so the answer is 0.5 * sqrt(12)."""
    values = np.array([0.03, -0.01, 0.03, -0.01, 0.03, -0.01, 0.03, -0.01])
    assert float(np.mean(values)) == pytest.approx(0.01)

    expected = 0.01 / float(np.std(values, ddof=1)) * math.sqrt(12.0)
    assert sharpe_ratio(values) == pytest.approx(expected, rel=1e-12)


def test_sharpe_ratio_refuses_a_constant_series() -> None:
    with pytest.raises(ValueError, match="zero volatility"):
        sharpe_ratio([0.01] * 24)


def test_non_finite_input_is_refused_rather_than_dropped() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        sharpe_ratio([0.01, float("nan"), 0.02])
