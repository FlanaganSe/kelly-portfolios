"""Every expectation here is built from a brute-force growth function, not from the
closed forms under test.

``_growth_excess`` writes ``A - V/2`` out longhand for an explicitly constructed
portfolio, with no algebra shared with :mod:`portfolio_edge.studies.overlay_growth`.
The closed forms are then checked against numerical differentiation and grid search
of that function. A test that asserted the module's own output would pin a typo.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.equity_share import plug_in_growth_cost
from portfolio_edge.studies.overlay_growth import (
    FundingRule,
    MultiOverlay,
    OverlayInputs,
    effective_breadth,
    funding_rule_gap,
    growth_optimal_overlay_vector,
    growth_optimal_overlay_weight,
    marginal_growth,
    matched_volatility_verdict,
    multi_overlay_growth_gain,
    overlay_growth_gain,
    required_net_excess_return,
    sharpe_admission_threshold,
    shrunk_overlay_weight,
)

# A deliberately ordinary set of forecasts. Equity at a 5.5% arithmetic excess and
# 16% volatility has L_e* = 2.148, so the zero-leverage constraint binds hard, which
# is the case the module exists to price.
BASE = OverlayInputs(
    base_excess_return=0.055,
    base_volatility=0.16,
    diversifier_excess_return=0.040,
    diversifier_volatility=0.10,
    correlation=-0.17,
    financing_spread=0.0059,
    fee=0.0085,
)


def _growth_excess(
    inputs: OverlayInputs, weight: float, *, rule: str
) -> float:
    """``A - V/2`` for a portfolio built longhand from its two legs.

    Deliberately verbose and deliberately not factored: this is the reference
    implementation the closed forms are measured against.
    """
    net = (
        inputs.diversifier_excess_return - inputs.financing_spread - inputs.fee
    )
    if rule == FundingRule.OVERLAY:
        equity_weight = 1.0
    elif rule == FundingRule.PRO_RATA:
        equity_weight = 1.0 - weight
    else:  # pragma: no cover - guarded by the module under test
        raise ValueError(rule)

    arithmetic = equity_weight * inputs.base_excess_return + weight * net
    variance = (
        equity_weight**2 * inputs.base_volatility**2
        + 2.0
        * equity_weight
        * weight
        * inputs.correlation
        * inputs.base_volatility
        * inputs.diversifier_volatility
        + weight**2 * inputs.diversifier_volatility**2
    )
    return arithmetic - 0.5 * variance


def _numerical_slope(inputs: OverlayInputs, *, rule: str, step: float = 1e-7) -> float:
    forward = _growth_excess(inputs, step, rule=rule)
    backward = _growth_excess(inputs, -step, rule=rule)
    return (forward - backward) / (2.0 * step)


# --------------------------------------------------------------------------------
# 1. The two bars agree with numerical differentiation of the longhand portfolio
# --------------------------------------------------------------------------------


@pytest.mark.parametrize("rule", [FundingRule.OVERLAY, FundingRule.PRO_RATA])
def test_marginal_growth_matches_numerical_derivative(rule: str) -> None:
    assert marginal_growth(BASE, rule=rule) == pytest.approx(
        _numerical_slope(BASE, rule=rule), abs=1e-9
    )


@pytest.mark.parametrize("rule", [FundingRule.OVERLAY, FundingRule.PRO_RATA])
def test_required_net_excess_return_is_the_break_even(rule: str) -> None:
    """At the required ``a_net`` the first sleeve dollar must be worth exactly zero."""
    required = required_net_excess_return(BASE, rule=rule)
    # Rebuild the inputs so that a_net lands exactly on the bar.
    at_bar = OverlayInputs(
        base_excess_return=BASE.base_excess_return,
        base_volatility=BASE.base_volatility,
        diversifier_excess_return=required + BASE.financing_spread + BASE.fee,
        diversifier_volatility=BASE.diversifier_volatility,
        correlation=BASE.correlation,
        financing_spread=BASE.financing_spread,
        fee=BASE.fee,
    )
    assert _numerical_slope(at_bar, rule=rule) == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------------
# 2. Equation (3): the gap involves nothing about the diversifier
# --------------------------------------------------------------------------------


def test_funding_rule_gap_equals_the_difference_of_the_two_bars() -> None:
    gap = required_net_excess_return(
        BASE, rule=FundingRule.PRO_RATA
    ) - required_net_excess_return(BASE, rule=FundingRule.OVERLAY)
    assert gap == pytest.approx(
        funding_rule_gap(
            base_excess_return=BASE.base_excess_return,
            base_volatility=BASE.base_volatility,
        )
    )
    # Independently: a_e - sigma_e**2 = 5.5% - 2.56% = 2.94 pp/yr.
    assert gap == pytest.approx(0.055 - 0.16**2)
    assert gap == pytest.approx(0.0294)


@pytest.mark.parametrize("diversifier_volatility", [0.04, 0.10, 0.25, 0.60])
@pytest.mark.parametrize("correlation", [-0.6, -0.17, 0.0, 0.35, 0.9])
@pytest.mark.parametrize("diversifier_excess_return", [-0.02, 0.0, 0.04, 0.12])
def test_gap_is_invariant_to_every_diversifier_property(
    diversifier_volatility: float,
    correlation: float,
    diversifier_excess_return: float,
) -> None:
    """The finding, stated as a property test over the whole diversifier space."""
    inputs = OverlayInputs(
        base_excess_return=BASE.base_excess_return,
        base_volatility=BASE.base_volatility,
        diversifier_excess_return=diversifier_excess_return,
        diversifier_volatility=diversifier_volatility,
        correlation=correlation,
        financing_spread=BASE.financing_spread,
        fee=BASE.fee,
    )
    gap = required_net_excess_return(
        inputs, rule=FundingRule.PRO_RATA
    ) - required_net_excess_return(inputs, rule=FundingRule.OVERLAY)
    assert gap == pytest.approx(0.055 - 0.16**2)


def test_the_two_rules_coincide_exactly_when_leverage_does_not_bind() -> None:
    """``L_e* = 1`` is the whole content of equation (3)."""
    unbinding = OverlayInputs(
        base_excess_return=0.16**2,  # a_e = sigma_e**2, so L_e* = 1
        base_volatility=0.16,
        diversifier_excess_return=BASE.diversifier_excess_return,
        diversifier_volatility=BASE.diversifier_volatility,
        correlation=BASE.correlation,
    )
    assert unbinding.base_kelly_leverage == pytest.approx(1.0)
    assert marginal_growth(unbinding, rule=FundingRule.OVERLAY) == pytest.approx(
        marginal_growth(unbinding, rule=FundingRule.PRO_RATA)
    )


def test_gap_reverses_sign_for_an_over_levered_equity_position() -> None:
    over_levered = funding_rule_gap(base_excess_return=0.01, base_volatility=0.30)
    assert over_levered < 0.0


# --------------------------------------------------------------------------------
# 3. Equation (4) and the tangency condition are the same statement
# --------------------------------------------------------------------------------


def test_admission_threshold_at_equity_kelly_is_rho_times_base_sharpe() -> None:
    threshold = sharpe_admission_threshold(
        BASE, base_exposure=BASE.base_kelly_leverage
    )
    assert threshold == pytest.approx(BASE.correlation * BASE.base_sharpe)


def test_admission_threshold_signs_the_first_dollar() -> None:
    """Above the threshold the sleeve helps; below it, it hurts. Checked longhand."""
    threshold = sharpe_admission_threshold(BASE)
    assert BASE.diversifier_sharpe > threshold
    assert _numerical_slope(BASE, rule=FundingRule.OVERLAY) > 0.0

    # A sleeve whose net Sharpe sits below the threshold, holding rho and sigma_d.
    below = OverlayInputs(
        base_excess_return=BASE.base_excess_return,
        base_volatility=BASE.base_volatility,
        diversifier_excess_return=(threshold - 0.01) * BASE.diversifier_volatility,
        diversifier_volatility=BASE.diversifier_volatility,
        correlation=BASE.correlation,
    )
    assert below.diversifier_sharpe < threshold
    assert _numerical_slope(below, rule=FundingRule.OVERLAY) < 0.0


def test_negative_correlation_admits_a_negative_expected_return_sleeve() -> None:
    """Uncomfortable but exact: at rho < 0 the bar is below zero."""
    assert required_net_excess_return(BASE, rule=FundingRule.OVERLAY) < 0.0
    losing = OverlayInputs(
        base_excess_return=BASE.base_excess_return,
        base_volatility=BASE.base_volatility,
        diversifier_excess_return=-0.001,
        diversifier_volatility=BASE.diversifier_volatility,
        correlation=BASE.correlation,
    )
    assert losing.net_excess_return < 0.0
    assert _numerical_slope(losing, rule=FundingRule.OVERLAY) > 0.0


# --------------------------------------------------------------------------------
# 4. Sizing: grid search the longhand growth function
# --------------------------------------------------------------------------------


def test_optimal_weight_is_found_by_grid_search_of_the_longhand_growth() -> None:
    grid = np.linspace(-1.0, 3.0, 400_001)
    values = np.array(
        [_growth_excess(BASE, float(w), rule=FundingRule.OVERLAY) for w in grid]
    )
    argmax = float(grid[int(np.argmax(values))])
    assert growth_optimal_overlay_weight(BASE) == pytest.approx(argmax, abs=1e-4)


def test_growth_gain_matches_the_longhand_difference_at_every_weight() -> None:
    baseline = _growth_excess(BASE, 0.0, rule=FundingRule.OVERLAY)
    for weight in (0.0, 0.05, 0.25, 0.5, 1.0, 2.0):
        longhand = _growth_excess(BASE, weight, rule=FundingRule.OVERLAY) - baseline
        assert overlay_growth_gain(BASE, weight=weight) == pytest.approx(longhand)


def test_the_gain_returns_to_zero_at_twice_the_optimal_weight() -> None:
    optimum = growth_optimal_overlay_weight(BASE)
    assert overlay_growth_gain(BASE, weight=2.0 * optimum) == pytest.approx(0.0, abs=1e-15)
    peak = overlay_growth_gain(BASE, weight=optimum)
    edge = BASE.net_excess_return - BASE.covariance
    assert peak == pytest.approx(edge**2 / (2.0 * BASE.diversifier_volatility**2))


# --------------------------------------------------------------------------------
# 5. The matched-volatility control, which is the one that decides
# --------------------------------------------------------------------------------


def test_matched_volatility_gain_is_the_sharpe_difference_times_volatility() -> None:
    verdict = matched_volatility_verdict(BASE, weight=0.30)
    assert verdict.leverage_matched_growth_gain == pytest.approx(
        verdict.portfolio_volatility * (verdict.portfolio_sharpe - verdict.base_sharpe)
    )


def test_levered_base_at_the_matched_volatility_grows_by_the_stated_amount() -> None:
    """Rebuild the levered-base control longhand and difference it."""
    weight = 0.30
    verdict = matched_volatility_verdict(BASE, weight=weight)
    leverage = verdict.portfolio_volatility / BASE.base_volatility
    levered_growth = (
        leverage * BASE.base_excess_return
        - 0.5 * leverage**2 * BASE.base_volatility**2
    )
    overlay_growth = _growth_excess(BASE, weight, rule=FundingRule.OVERLAY)
    assert verdict.leverage_matched_growth_gain == pytest.approx(
        overlay_growth - levered_growth
    )


def test_an_overlay_can_raise_growth_and_still_lose_to_levered_base() -> None:
    """The trap the plan requires be labelled: growth bought with beta, not breadth.

    Growth improves iff ``a_net > beta sigma_e**2`` and Sharpe improves iff
    ``a_net > beta a_e``. Both bars exist only when ``a_e > sigma_e**2``, so this
    window is another face of equation (3). Here ``beta = 0.48 * 0.10 / 0.16 = 0.30``,
    giving ``0.30 * 2.56% = 0.768%`` and ``0.30 * 5.5% = 1.65%``; ``a_net = 1.2%``
    sits between them.
    """
    inputs = OverlayInputs(
        base_excess_return=0.055,
        base_volatility=0.16,
        diversifier_excess_return=0.012,
        diversifier_volatility=0.10,
        correlation=0.48,
    )
    assert inputs.beta == pytest.approx(0.30)
    assert 0.30 * 0.16**2 < inputs.net_excess_return < 0.30 * 0.055

    verdict = matched_volatility_verdict(inputs, weight=0.20)
    assert verdict.growth_gain > 0.0
    assert verdict.beats_leverage_matched_base is False
    assert verdict.leverage_matched_growth_gain < 0.0


# --------------------------------------------------------------------------------
# 6. Estimation error
# --------------------------------------------------------------------------------


def test_shrinkage_uses_the_marginal_sharpe_not_the_standalone_one() -> None:
    """At negative correlation the marginal Sharpe exceeds the standalone one."""
    marginal_sharpe = (
        BASE.net_excess_return - BASE.covariance
    ) / BASE.diversifier_volatility
    assert marginal_sharpe > BASE.diversifier_sharpe

    years = 35.0
    information = marginal_sharpe**2 * years
    expected = (information / (information + 1.0)) * growth_optimal_overlay_weight(BASE)
    assert shrunk_overlay_weight(BASE, years=years) == pytest.approx(expected)


def test_shrinkage_tends_to_the_plug_in_optimum_with_unlimited_data() -> None:
    assert shrunk_overlay_weight(BASE, years=1e9) == pytest.approx(
        growth_optimal_overlay_weight(BASE), rel=1e-6
    )


def test_plug_in_cost_is_one_over_two_t_for_the_overlay_too() -> None:
    """``sigma_d`` cancels, exactly as it does for equity in :mod:`equity_share`.

    Simulated: draw the sleeve's mean from its sampling distribution, size the
    overlay on the estimate, and score it on the truth. The mean growth shortfall
    must be ``1 / (2T)`` whatever the sleeve's volatility.
    """
    rng = np.random.default_rng(20260816)
    years = 40.0
    draws = 400_000
    truth = BASE

    for volatility in (0.06, 0.10, 0.30):
        inputs = OverlayInputs(
            base_excess_return=truth.base_excess_return,
            base_volatility=truth.base_volatility,
            diversifier_excess_return=truth.diversifier_excess_return,
            diversifier_volatility=volatility,
            correlation=0.0,
        )
        optimum = growth_optimal_overlay_weight(inputs)
        standard_error = volatility / math.sqrt(years)
        estimated_net = inputs.net_excess_return + rng.normal(
            0.0, standard_error, size=draws
        )
        estimated_weight = estimated_net / volatility**2
        shortfall = 0.5 * volatility**2 * (estimated_weight - optimum) ** 2
        assert float(shortfall.mean()) == pytest.approx(
            plug_in_growth_cost(years), rel=0.02
        )


# --------------------------------------------------------------------------------
# 7. Input validation
# --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("base_volatility", 0.0),
        ("base_volatility", -0.1),
        ("diversifier_volatility", 0.0),
        ("correlation", 1.5),
        ("correlation", -1.5),
    ],
)
def test_inputs_reject_impossible_parameters(field: str, value: float) -> None:
    kwargs = {
        "base_excess_return": 0.055,
        "base_volatility": 0.16,
        "diversifier_excess_return": 0.04,
        "diversifier_volatility": 0.10,
        "correlation": -0.17,
    }
    kwargs[field] = value
    with pytest.raises(ValueError):
        OverlayInputs(**kwargs)


def test_unknown_funding_rule_raises() -> None:
    with pytest.raises(ValueError, match="unknown funding rule"):
        marginal_growth(BASE, rule="margin_account")
    with pytest.raises(ValueError, match="unknown funding rule"):
        required_net_excess_return(BASE, rule="margin_account")


# --------------------------------------------------------------------------------
# 8. Many overlays: breadth checked against brute force, not against the formula
# --------------------------------------------------------------------------------


def _equicorrelated(
    *, count: int, edge: float, volatility: float, mutual_correlation: float
) -> MultiOverlay:
    covariance = tuple(
        tuple(
            volatility**2 * (1.0 if i == j else mutual_correlation)
            for j in range(count)
        )
        for i in range(count)
    )
    # covariance_with_base is folded into the edge here, so the marginal edge is the
    # edge itself and the breadth arithmetic is isolated from the base entirely.
    return MultiOverlay(
        net_excess_returns=tuple([edge] * count),
        covariance_with_base=tuple([0.0] * count),
        covariance=covariance,
    )


def test_single_overlay_case_agrees_with_the_scalar_formula() -> None:
    edge = BASE.net_excess_return - BASE.covariance
    single = MultiOverlay(
        net_excess_returns=(BASE.net_excess_return,),
        covariance_with_base=(BASE.covariance,),
        covariance=((BASE.diversifier_volatility**2,),),
    )
    assert single.marginal_edges[0] == pytest.approx(edge)
    assert growth_optimal_overlay_vector(single)[0] == pytest.approx(
        growth_optimal_overlay_weight(BASE)
    )
    for weight in (0.0, 0.25, 0.8):
        assert multi_overlay_growth_gain(single, weights=(weight,)) == pytest.approx(
            overlay_growth_gain(BASE, weight=weight)
        )


def test_optimal_vector_is_the_argmax_of_the_quadratic_by_random_search() -> None:
    """No matrix algebra in the check: perturb the claimed optimum and lose."""
    overlays = MultiOverlay(
        net_excess_returns=(0.030, 0.018, 0.006),
        covariance_with_base=(0.0, -0.0016, 0.0008),
        covariance=(
            (0.0100, 0.0012, -0.0005),
            (0.0012, 0.0225, 0.0009),
            (-0.0005, 0.0009, 0.0064),
        ),
    )
    optimum = growth_optimal_overlay_vector(overlays)
    best = multi_overlay_growth_gain(overlays, weights=optimum)
    rng = np.random.default_rng(20260816)
    for _ in range(5_000):
        perturbed = tuple(
            float(w + d) for w, d in zip(optimum, rng.normal(0.0, 0.05, size=3), strict=True)
        )
        assert multi_overlay_growth_gain(overlays, weights=perturbed) <= best + 1e-12


def test_peak_gain_scales_with_effective_breadth_not_with_count() -> None:
    """The claim in the docstring, checked by solving each case from scratch."""
    edge, volatility = 0.02, 0.10
    single = _equicorrelated(
        count=1, edge=edge, volatility=volatility, mutual_correlation=0.0
    )
    single_peak = multi_overlay_growth_gain(
        single, weights=growth_optimal_overlay_vector(single)
    )
    assert single_peak == pytest.approx(edge**2 / (2.0 * volatility**2))

    for count in (2, 5, 10):
        for correlation in (0.0, 0.3, 0.6, 1.0 - 1e-9):
            overlays = _equicorrelated(
                count=count,
                edge=edge,
                volatility=volatility,
                mutual_correlation=correlation,
            )
            peak = multi_overlay_growth_gain(
                overlays, weights=growth_optimal_overlay_vector(overlays)
            )
            breadth = effective_breadth(
                count=count, mutual_correlation=correlation
            )
            assert peak == pytest.approx(single_peak * breadth, rel=1e-6)


def test_uncorrelated_sleeves_multiply_the_gain_and_identical_ones_do_not() -> None:
    assert effective_breadth(count=10, mutual_correlation=0.0) == pytest.approx(10.0)
    assert effective_breadth(count=10, mutual_correlation=1.0) == pytest.approx(1.0)
    # The number the docstring quotes, computed here rather than copied.
    assert effective_breadth(count=10, mutual_correlation=0.3) == pytest.approx(
        10.0 / 3.7, rel=1e-9
    )


def test_effective_breadth_refuses_an_indefinite_correlation_matrix() -> None:
    with pytest.raises(ValueError, match="positive semi-definite"):
        effective_breadth(count=3, mutual_correlation=-0.5)
    with pytest.raises(ValueError, match="at least 1"):
        effective_breadth(count=0, mutual_correlation=0.0)
    with pytest.raises(ValueError, match=r"\[-1, 1\]"):
        effective_breadth(count=3, mutual_correlation=1.5)


def test_multi_overlay_rejects_malformed_inputs() -> None:
    with pytest.raises(ValueError, match="at least one overlay"):
        MultiOverlay(
            net_excess_returns=(), covariance_with_base=(), covariance=()
        )
    with pytest.raises(ValueError, match="must match"):
        MultiOverlay(
            net_excess_returns=(0.01, 0.02),
            covariance_with_base=(0.0,),
            covariance=((0.01, 0.0), (0.0, 0.01)),
        )
    with pytest.raises(ValueError, match="symmetric"):
        MultiOverlay(
            net_excess_returns=(0.01, 0.02),
            covariance_with_base=(0.0, 0.0),
            covariance=((0.01, 0.002), (0.003, 0.01)),
        )
    with pytest.raises(ValueError, match="singular"):
        growth_optimal_overlay_vector(
            MultiOverlay(
                net_excess_returns=(0.01, 0.01),
                covariance_with_base=(0.0, 0.0),
                covariance=((0.01, 0.01), (0.01, 0.01)),
            )
        )
