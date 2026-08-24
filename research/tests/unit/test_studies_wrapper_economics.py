"""Every expectation here is built from a brute-force growth function or from hand
arithmetic, never from the module's own output.

``_growth_through_wrapper`` constructs the portfolio explicitly — ``1 - x`` of the base
held directly, ``x`` of the wrapper delivering ``b`` and ``d`` — and writes ``A - V/2``
out longhand. Equation (7) is then checked against numerical differentiation of that
function, and its two boundary cases against
:mod:`portfolio_edge.studies.overlay_growth`'s independently derived rules.
"""

from __future__ import annotations

import math

import pytest

from portfolio_edge.studies.overlay_growth import (
    FundingRule,
    OverlayInputs,
    funding_rule_gap,
    marginal_growth,
)
from portfolio_edge.studies.wrapper_economics import (
    Wrapper,
    base_substitution_note,
    capital_share_required,
    cost_per_unit_notional,
    displacement,
    funding_capture,
    funding_rule_penalty,
    marginal_growth_through_wrapper,
    required_net_excess_return_through_wrapper,
    wrapper_funding_class,
)

# Ordinary forecasts. a_p = 5% at sigma_p = 16% gives L_p* = 1.95, so the funding-rule
# gap is a substantial +2.44 pp/yr and the wrapper's structure has something to bite on.
INPUTS = OverlayInputs(
    base_excess_return=0.050,
    base_volatility=0.16,
    diversifier_excess_return=0.040,
    diversifier_volatility=0.126,
    correlation=-0.08,
    financing_spread=0.0059,
    fee=0.0086,
)


def _growth_through_wrapper(
    *, b: float, d: float, weight: float, inputs: OverlayInputs
) -> float:
    """``A - V/2`` written out longhand, sharing no algebra with the module."""
    x = weight / d
    base_exposure = (1.0 - x) + x * b
    arithmetic = base_exposure * inputs.base_excess_return + weight * (
        inputs.diversifier_excess_return - inputs.financing_spread - inputs.fee
    )
    variance = (
        base_exposure**2 * inputs.base_volatility**2
        + 2.0
        * base_exposure
        * weight
        * inputs.correlation
        * inputs.base_volatility
        * inputs.diversifier_volatility
        + weight**2 * inputs.diversifier_volatility**2
    )
    return arithmetic - variance / 2.0


def _numerical_marginal(*, b: float, d: float, inputs: OverlayInputs) -> float:
    h = 1e-6
    up = _growth_through_wrapper(b=b, d=d, weight=h, inputs=inputs)
    down = _growth_through_wrapper(b=b, d=d, weight=-h, inputs=inputs)
    return (up - down) / (2.0 * h)


# --------------------------------------------------------------------------------
# Equation (7) against numerical differentiation of an independent growth function
# --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("b", "d"),
    [
        (1.00, 1.00),  # RSST-shaped: pure overlay
        (0.90, 0.60),  # NTSX-shaped: partial overlay
        (0.00, 1.00),  # DBMF-shaped: pure pro rata
        (0.50, 0.50),  # a 50/50 blend, also pure pro rata
        (0.40, 0.30),  # dilutes faster than it stacks
        (1.20, 0.80),  # levers the base as well
    ],
)
def test_marginal_growth_matches_numerical_derivative(b: float, d: float) -> None:
    wrapper = Wrapper(name="test", base_notional=b, diversifier_notional=d)
    assert marginal_growth_through_wrapper(wrapper, INPUTS) == pytest.approx(
        _numerical_marginal(b=b, d=d, inputs=INPUTS), abs=1e-9
    )


# --------------------------------------------------------------------------------
# The two boundaries, against overlay_growth's separately derived rules
# --------------------------------------------------------------------------------


def test_pure_overlay_reduces_to_overlay_rule() -> None:
    wrapper = Wrapper(name="stacked", base_notional=1.0, diversifier_notional=1.0)
    assert displacement(wrapper) == pytest.approx(0.0)
    assert marginal_growth_through_wrapper(wrapper, INPUTS) == pytest.approx(
        marginal_growth(INPUTS, rule=FundingRule.OVERLAY), abs=1e-12
    )


@pytest.mark.parametrize(("b", "d"), [(0.0, 1.0), (0.5, 0.5), (0.25, 0.75)])
def test_delta_one_reduces_to_pro_rata_rule(b: float, d: float) -> None:
    """Three structurally different funds, all at ``delta = 1``, all identical."""
    wrapper = Wrapper(name="blend", base_notional=b, diversifier_notional=d)
    assert displacement(wrapper) == pytest.approx(1.0)
    assert marginal_growth_through_wrapper(wrapper, INPUTS) == pytest.approx(
        marginal_growth(INPUTS, rule=FundingRule.PRO_RATA), abs=1e-12
    )


def test_gross_notional_does_not_decide_the_funding_rule() -> None:
    """The claim the module exists to make, as an assertion.

    A 50/50 fund at 1.0x gross and a 90/60 fund at 1.5x gross differ by a factor of
    1.5 on the number a fact sheet reports, and by a factor of six on the number that
    decides.
    """
    blend = Wrapper(name="50/50", base_notional=0.5, diversifier_notional=0.5)
    efficient = Wrapper(name="90/60", base_notional=0.9, diversifier_notional=0.6)
    assert blend.gross_notional == pytest.approx(1.0)
    assert efficient.gross_notional == pytest.approx(1.5)
    assert displacement(blend) == pytest.approx(1.0)
    assert displacement(efficient) == pytest.approx(1.0 / 6.0)


# --------------------------------------------------------------------------------
# Hand arithmetic
# --------------------------------------------------------------------------------


def test_displacement_and_capture_by_hand() -> None:
    wrapper = Wrapper(name="90/60", base_notional=0.90, diversifier_notional=0.60)
    # (1 - 0.90) / 0.60 = 0.10 / 0.60
    assert displacement(wrapper) == pytest.approx(0.16666666666666666)
    assert funding_capture(wrapper) == pytest.approx(0.8333333333333334)


def test_funding_rule_penalty_is_delta_times_the_gap() -> None:
    wrapper = Wrapper(name="90/60", base_notional=0.90, diversifier_notional=0.60)
    gap = funding_rule_gap(base_excess_return=0.050, base_volatility=0.16)
    assert gap == pytest.approx(0.05 - 0.0256)
    penalty = funding_rule_penalty(
        wrapper, base_excess_return=0.050, base_volatility=0.16
    )
    assert penalty == pytest.approx(gap / 6.0)
    # In the units the documentation quotes: 2.44 pp/yr becomes 0.41 pp/yr.
    assert penalty * 100.0 == pytest.approx(0.40666666666666, abs=1e-9)


def test_pro_rata_penalty_equals_the_whole_gap() -> None:
    wrapper = Wrapper(name="standalone", base_notional=0.0, diversifier_notional=1.0)
    assert funding_rule_penalty(
        wrapper, base_excess_return=0.050, base_volatility=0.16
    ) == pytest.approx(funding_rule_gap(base_excess_return=0.050, base_volatility=0.16))


def test_penalty_changes_sign_with_the_forecast() -> None:
    """The module inherits overlay_growth's sign warning and must not hide it."""
    wrapper = Wrapper(name="standalone", base_notional=0.0, diversifier_notional=1.0)
    # a_p below sigma_p**2 = 2.56% makes pro rata the better structure.
    assert (
        funding_rule_penalty(wrapper, base_excess_return=0.020, base_volatility=0.16)
        < 0.0
    )
    assert (
        funding_rule_penalty(wrapper, base_excess_return=0.0256, base_volatility=0.16)
        == pytest.approx(0.0)
    )


def test_cost_per_unit_notional_rescales_only_the_fee() -> None:
    wrapper = Wrapper(
        name="90/60",
        base_notional=0.90,
        diversifier_notional=0.60,
        fee=0.0020,
        financing_spread=0.0015,
    )
    # 0.20% on capital buying 0.60 of notional is 0.3333% of notional, plus 15 bp.
    assert cost_per_unit_notional(wrapper) == pytest.approx(0.0033333333333 + 0.0015)


def test_a_cheaper_expense_ratio_can_be_the_dearer_wrapper() -> None:
    """20 bp on 0.10 of notional beats 100 bp on 1.00 of notional on the fact sheet
    and loses by a factor of two in the units that decide."""
    thin = Wrapper(name="thin", base_notional=1.0, diversifier_notional=0.10, fee=0.0020)
    thick = Wrapper(name="thick", base_notional=1.0, diversifier_notional=1.00, fee=0.0100)
    assert thin.fee < thick.fee
    assert cost_per_unit_notional(thin) == pytest.approx(0.02)
    assert cost_per_unit_notional(thin) > cost_per_unit_notional(thick)


def test_capital_share_required_is_shelter_consumed() -> None:
    stacked = Wrapper(name="100/100", base_notional=1.0, diversifier_notional=1.0)
    half = Wrapper(name="50/50", base_notional=0.5, diversifier_notional=0.5)
    assert capital_share_required(stacked, diversifier_weight=0.30) == pytest.approx(0.30)
    assert capital_share_required(half, diversifier_weight=0.30) == pytest.approx(0.60)


def test_required_net_excess_return_is_the_break_even() -> None:
    """Set ``a_d`` to the returned break-even and the marginal growth must vanish."""
    wrapper = Wrapper(name="90/60", base_notional=0.90, diversifier_notional=0.60)
    required = required_net_excess_return_through_wrapper(wrapper, INPUTS)
    solved = OverlayInputs(
        base_excess_return=INPUTS.base_excess_return,
        base_volatility=INPUTS.base_volatility,
        diversifier_excess_return=required
        + INPUTS.financing_spread
        + INPUTS.fee,
        diversifier_volatility=INPUTS.diversifier_volatility,
        correlation=INPUTS.correlation,
        financing_spread=INPUTS.financing_spread,
        fee=INPUTS.fee,
    )
    assert marginal_growth_through_wrapper(wrapper, solved) == pytest.approx(
        0.0, abs=1e-12
    )


# --------------------------------------------------------------------------------
# Classification and refusals
# --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("b", "d", "expected"),
    [
        (1.00, 1.00, "overlay"),
        (0.90, 0.60, "partial-overlay"),
        (0.00, 1.00, "pro-rata"),
        (0.50, 0.50, "pro-rata"),
        (0.40, 0.30, "worse-than-pro-rata"),
        (1.20, 0.80, "levered-base"),
    ],
)
def test_wrapper_funding_class(b: float, d: float, expected: str) -> None:
    wrapper = Wrapper(name="test", base_notional=b, diversifier_notional=d)
    assert wrapper_funding_class(wrapper) == expected


def test_zero_diversifier_notional_is_refused() -> None:
    with pytest.raises(ValueError, match="diversifier notional must be positive"):
        Wrapper(name="index fund", base_notional=1.0, diversifier_notional=0.0)


def test_negative_base_notional_is_refused() -> None:
    with pytest.raises(ValueError, match="base notional may not be negative"):
        Wrapper(name="short", base_notional=-0.1, diversifier_notional=1.0)


def test_negative_fee_is_refused() -> None:
    with pytest.raises(ValueError, match="fee may not be negative"):
        Wrapper(name="paid to hold", base_notional=1.0, diversifier_notional=1.0, fee=-0.01)


def test_negative_diversifier_weight_is_refused() -> None:
    wrapper = Wrapper(name="test", base_notional=1.0, diversifier_notional=1.0)
    with pytest.raises(ValueError, match="diversifier weight may not be negative"):
        capital_share_required(wrapper, diversifier_weight=-0.1)


def test_base_substitution_note_refuses_rather_than_scoring() -> None:
    wrapper = Wrapper(name="RSSB-shaped", base_notional=1.0, diversifier_notional=1.0)
    note = base_substitution_note(wrapper, base_is_substitutable=False)
    assert "does not apply" in note
    assert "no single delta" in note
    ok = base_substitution_note(wrapper, base_is_substitutable=True)
    assert "delta = 0.0000" in ok


# --------------------------------------------------------------------------------
# The property the whole audit turns on
# --------------------------------------------------------------------------------


def test_penalty_is_monotone_in_displacement_and_independent_of_the_sleeve() -> None:
    """The penalty must not move when the sleeve does — that is equation (3)."""
    wrapper = Wrapper(name="90/60", base_notional=0.90, diversifier_notional=0.60)
    penalty = funding_rule_penalty(
        wrapper, base_excess_return=0.050, base_volatility=0.16
    )
    for a_d in (0.0, 0.02, 0.08):
        for rho in (-0.3, 0.0, 0.4):
            for sigma_d in (0.05, 0.126, 0.30):
                probe = OverlayInputs(
                    base_excess_return=0.050,
                    base_volatility=0.16,
                    diversifier_excess_return=a_d,
                    diversifier_volatility=sigma_d,
                    correlation=rho,
                )
                gap = marginal_growth(
                    probe, rule=FundingRule.OVERLAY
                ) - marginal_growth_through_wrapper(wrapper, probe)
                assert gap == pytest.approx(penalty, abs=1e-12)


def test_grid_search_optimum_agrees_with_the_sign_of_the_marginal() -> None:
    """If the first dollar raises growth, the brute-force optimum is above zero."""
    for b, d in ((1.0, 1.0), (0.9, 0.6), (0.0, 1.0), (0.4, 0.3)):
        wrapper = Wrapper(name="test", base_notional=b, diversifier_notional=d)
        weights = [i / 2000.0 for i in range(0, 1001)]
        best = max(
            weights, key=lambda w: _growth_through_wrapper(b=b, d=d, weight=w, inputs=INPUTS)
        )
        marginal = marginal_growth_through_wrapper(wrapper, INPUTS)
        if marginal > 1e-6:
            assert best > 0.0
        elif marginal < -1e-6:
            assert math.isclose(best, 0.0, abs_tol=1e-12)
