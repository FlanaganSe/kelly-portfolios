"""The gold-sleeve arithmetic, against fixtures computed independently of it.

Four of the expectations below are hand-computed rather than recorded from a run:
:func:`test_total_returns_are_the_hand_computed_identity`,
:func:`test_geometric_growth_matches_the_closed_form`,
:func:`test_a_zero_beta_sleeve_earns_exactly_the_variance_ceiling` and
:func:`test_conditional_correlation_against_a_hand_built_mask`. A fixture that disagrees
with the implementation is a finding, not a tolerance to loosen.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.gold_sleeve import (
    GoldCarry,
    admission,
    conditional_correlation,
    drawdown_mask,
    geometric_growth,
    pro_rata_marginal_value,
    sleeve_moments,
    total_returns_from_levels,
)
from portfolio_edge.studies.overlay_growth import (
    FundingRule,
    OverlayInputs,
    funding_rule_gap,
    marginal_growth,
)

#: A carry tier whose annual cost divides exactly by 12, so the expectations below are
#: exact decimals rather than floating-point artefacts.
TWELVE_BP = GoldCarry(
    annual_cost=0.012, label="test tier", source="chosen so 0.012/12 = 0.001 exactly"
)


# --------------------------------------------------------------------------------
# Independently computed fixtures
# --------------------------------------------------------------------------------


def test_total_returns_are_the_hand_computed_identity() -> None:
    """``r_t = P_t/P_{t-1} - 1 - c/12``, worked out by hand.

    Levels 100 -> 110 -> 99 at a 1.2%/yr carry, so the monthly charge is exactly 0.001.
    The price returns are +0.10 and -0.10 by construction, so the total returns must be
    +0.099 and -0.101. Neither number came from running the function.
    """
    result = total_returns_from_levels([100.0, 110.0, 99.0], carry=TWELVE_BP)

    assert result.size == 2
    assert result[0] == pytest.approx(0.099, abs=1e-12)
    assert result[1] == pytest.approx(-0.101, abs=1e-12)


def test_geometric_growth_matches_the_closed_form() -> None:
    """Twelve months of exactly +1% compound to ``1.01**12 - 1`` over one year."""
    expected = 1.01**12 - 1.0
    assert geometric_growth([0.01] * 12) == pytest.approx(expected, rel=1e-14)

    # Twenty-four months of the same monthly return annualise to the same rate: the
    # exponent 12/n is what makes that true, and it is the step most easily got wrong.
    assert geometric_growth([0.01] * 24) == pytest.approx(expected, rel=1e-14)


def test_a_zero_beta_sleeve_earns_exactly_the_variance_ceiling() -> None:
    """At ``beta = 0`` the credit per unit weight is exactly ``sigma_p**2``.

    Experiment 010's ceiling, asserted against a base whose annualised variance is
    computed here from its own definition rather than read back out of the result.
    """
    rng = np.random.default_rng(11)
    base = rng.normal(0.008, 0.04, 600)
    cash = np.full(600, 0.002)
    # A sleeve exactly orthogonal to the base: project the noise off it, so the sample
    # correlation is zero to machine precision rather than merely small.
    noise = rng.normal(0.004, 0.03, 600)
    centred_base = base - base.mean()
    sleeve = (
        noise
        - centred_base * float(np.dot(noise - noise.mean(), centred_base))
        / float(np.dot(centred_base, centred_base))
    )

    value = pro_rata_marginal_value(base, sleeve, cash, weight=0.10)

    base_variance = float(np.var(base - cash, ddof=1)) * 12.0
    assert value.beta == pytest.approx(0.0, abs=1e-12)
    assert value.credit_per_unit_weight == pytest.approx(base_variance, rel=1e-12)
    assert value.credit_at_weight == pytest.approx(0.10 * base_variance, rel=1e-12)
    assert value.credit_at_weight == pytest.approx(value.credit_ceiling_at_weight)


def test_conditional_correlation_against_a_hand_built_mask() -> None:
    """The mask, the counts and one correlation, all computed away from the function.

    The base path is +10%, -20%, +5%, -10%, +40%, +5%. Its wealth curve is 1.10, 0.88,
    0.924, 0.8316, 1.16424, 1.222452 and its running peak 1.10, 1.10, 1.10, 1.10,
    1.16424, 1.222452, so the months at least 10% below the peak are exactly months 2, 3
    and 4 — 0.88/1.10 = 0.80, 0.924/1.10 = 0.84, 0.8316/1.10 = 0.756. Months 1, 5 and 6
    are each at a new high.
    """
    base = [0.10, -0.20, 0.05, -0.10, 0.40, 0.05]
    sleeve = [0.01, 0.02, -0.03, 0.04, -0.05, 0.06]

    mask = drawdown_mask(base, threshold=0.10)
    assert list(mask) == [False, True, True, True, False, False]

    result = conditional_correlation(base, sleeve, threshold=0.10)
    assert result.months_in == 3
    assert result.months_out == 3
    assert result.correlation_in == pytest.approx(
        float(np.corrcoef([-0.20, 0.05, -0.10], [0.02, -0.03, 0.04])[0, 1])
    )
    assert result.sleeve_mean_in == pytest.approx((0.02 - 0.03 + 0.04) / 3.0)
    assert result.base_mean_in == pytest.approx((-0.20 + 0.05 - 0.10) / 3.0)


# --------------------------------------------------------------------------------
# Moments and admission
# --------------------------------------------------------------------------------


def test_a_sleeve_that_is_the_base_doubled_has_beta_two_and_the_same_sharpe() -> None:
    rng = np.random.default_rng(3)
    base = rng.normal(0.006, 0.04, 400)
    moments = sleeve_moments(2.0 * base, base)

    assert moments.correlation == pytest.approx(1.0)
    assert moments.beta == pytest.approx(2.0)
    assert moments.volatility == pytest.approx(2.0 * moments.base_volatility)
    assert moments.sharpe == pytest.approx(moments.base_sharpe)


def test_moments_annualise_means_by_twelve_and_volatilities_by_root_twelve() -> None:
    sleeve = [0.01, -0.01, 0.02, -0.02, 0.03, -0.03]
    base = [0.02, -0.01, 0.01, -0.03, 0.02, -0.01]
    moments = sleeve_moments(sleeve, base)

    assert moments.arithmetic_excess == pytest.approx(float(np.mean(sleeve)) * 12.0)
    assert moments.volatility == pytest.approx(
        float(np.std(sleeve, ddof=1)) * math.sqrt(12.0)
    )
    assert moments.months == 6


def test_admission_is_equation_four_and_flags_its_own_validity_range() -> None:
    rng = np.random.default_rng(5)
    base = rng.normal(0.007, 0.045, 500)
    sleeve = rng.normal(0.004, 0.05, 500)
    moments = sleeve_moments(sleeve, base)

    for exposure in (1.0, 1.5, 2.0):
        verdict = admission(moments, base_exposure=exposure)
        assert verdict.threshold == pytest.approx(
            exposure * moments.correlation * moments.base_volatility
        )
        assert verdict.margin == pytest.approx(moments.sharpe - verdict.threshold)
        assert verdict.admitted is (moments.sharpe > verdict.threshold)

    # The misuse guard, which is the reason this is a field rather than a docstring note.
    assert admission(moments).within_equation_4_range is True
    assert admission(sleeve_moments(base, base)).within_equation_4_range is False


def test_at_negative_correlation_the_threshold_is_negative() -> None:
    """A diversifier with a small negative excess return can still clear the bar.

    :mod:`overlay_growth` documents this and calls it a reason to be suspicious of the
    inputs. It is pinned so a later change cannot quietly remove the property.
    """
    rng = np.random.default_rng(7)
    base = rng.normal(0.006, 0.04, 400)
    sleeve = -0.5 * base + rng.normal(0.0, 0.01, 400)
    moments = sleeve_moments(sleeve, base)

    assert moments.correlation < 0.0
    assert admission(moments).threshold < 0.0


# --------------------------------------------------------------------------------
# Marginal value
# --------------------------------------------------------------------------------


def test_the_marginal_value_at_zero_weight_is_zero_by_construction() -> None:
    rng = np.random.default_rng(13)
    base = rng.normal(0.008, 0.04, 300)
    sleeve = rng.normal(0.003, 0.045, 300)
    cash = np.full(300, 0.002)

    value = pro_rata_marginal_value(base, sleeve, cash, weight=0.0)
    assert value.realised_marginal_growth == pytest.approx(0.0, abs=1e-15)
    assert value.blended_growth == pytest.approx(value.base_growth)


def test_a_sleeve_with_beta_above_one_carries_a_negative_credit() -> None:
    """Experiment 010's central algebraic claim, on a constructed high-beta sleeve."""
    rng = np.random.default_rng(17)
    base = rng.normal(0.008, 0.04, 500)
    cash = np.full(500, 0.002)
    sleeve = cash + 1.5 * (base - cash) + rng.normal(0.0, 0.005, 500)

    value = pro_rata_marginal_value(base, sleeve, cash, weight=0.10)
    assert value.beta > 1.0
    assert value.credit_per_unit_weight < 0.0
    assert value.credit_at_weight < 0.0


def test_the_credit_never_exceeds_its_ceiling() -> None:
    rng = np.random.default_rng(19)
    base = rng.normal(0.008, 0.04, 400)
    cash = np.full(400, 0.002)
    for scale in (-1.0, -0.5, 0.0, 0.5, 1.0, 2.0):
        sleeve = cash + scale * (base - cash) + rng.normal(0.001, 0.02, 400)
        value = pro_rata_marginal_value(base, sleeve, cash, weight=0.10)
        if value.beta >= 0.0:
            assert value.credit_at_weight <= value.credit_ceiling_at_weight + 1e-15


# --------------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------------


def test_a_carry_tier_must_state_its_provenance() -> None:
    with pytest.raises(ValueError, match="label and a source"):
        GoldCarry(annual_cost=0.001, label="", source="somewhere")
    with pytest.raises(ValueError, match="non-negative"):
        GoldCarry(annual_cost=-0.001, label="x", source="y")


def test_a_non_positive_price_raises_rather_than_producing_a_return() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        total_returns_from_levels([100.0, 0.0, 90.0], carry=TWELVE_BP)


def test_a_path_that_wipes_out_has_no_growth_rate() -> None:
    with pytest.raises(ValueError, match="non-positive wealth"):
        geometric_growth([0.05, -1.0, 0.05])


def test_misaligned_series_raise_rather_than_being_truncated() -> None:
    with pytest.raises(ValueError, match="aligned"):
        sleeve_moments([0.01, 0.02, 0.03], [0.01, 0.02])
    with pytest.raises(ValueError, match="aligned"):
        pro_rata_marginal_value(
            [0.01, 0.02, 0.03], [0.01, 0.02, 0.03], [0.0, 0.0], weight=0.1
        )


def test_a_conditioning_set_too_small_to_correlate_raises() -> None:
    # A monotonically rising base is never in drawdown, so one side of the split is
    # empty and no conditional correlation exists.
    with pytest.raises(ValueError, match="at least three months on each side"):
        conditional_correlation([0.01] * 10, [0.02] * 10, threshold=0.10)


def test_a_negative_drawdown_threshold_raises_because_it_is_a_depth() -> None:
    with pytest.raises(ValueError, match="depth"):
        drawdown_mask([0.01, -0.02, 0.03], threshold=-0.10)


# --------------------------------------------------------------------------------
# The funding rule, which is what decides the gold verdict
# --------------------------------------------------------------------------------


def test_the_wrapper_bar_interpolates_between_the_two_funding_rules() -> None:
    """``overlay - delta * (a_p - sigma_p**2)`` is pro rata at ``delta = 1``.

    ``_gold_sleeve_tables`` composes the wrapper bar from two committed functions rather
    than importing a third module, so the composition is pinned here. The identity is
    equation (3) of :mod:`overlay_growth` rearranged and is derived independently of both
    functions: subtracting (1) from (2) leaves ``a_p - sigma_p**2``, so adding it back to
    (1) must reproduce (2) exactly.
    """
    inputs = OverlayInputs(
        base_excess_return=0.0911,
        base_volatility=0.1556,
        diversifier_excess_return=0.0314,
        diversifier_volatility=0.1615,
        correlation=-0.024,
        financing_spread=0.0040,
        fee=0.0024,
    )
    gap = funding_rule_gap(
        base_excess_return=inputs.base_excess_return,
        base_volatility=inputs.base_volatility,
    )
    overlay = marginal_growth(inputs, rule=FundingRule.OVERLAY)
    pro_rata = marginal_growth(inputs, rule=FundingRule.PRO_RATA)

    # Independently: (2) - (1) = a_p - sigma_p**2, with no term from the diversifier.
    assert pro_rata - overlay == pytest.approx(-gap, rel=1e-12)
    assert overlay - 0.0 * gap == pytest.approx(overlay)
    assert overlay - 1.0 * gap == pytest.approx(pro_rata, rel=1e-12)


def test_gdes_measured_delta_forfeits_the_share_its_legs_imply() -> None:
    """``delta = (1 - b) / d`` on the legs measured from GDE's own Form N-PORT."""
    base_leg, overlay_leg = 0.8480, 0.8363
    # By hand: 0.1520 / 0.8363 = 0.18175...
    assert (1.0 - base_leg) / overlay_leg == pytest.approx(0.181753, abs=1e-6)
    # A wrapper holding a full base leg forfeits nothing; one holding none forfeits all.
    assert (1.0 - 1.0) / overlay_leg == pytest.approx(0.0)
    assert pytest.approx(1.0) == (1.0 - 0.0) / 1.0
