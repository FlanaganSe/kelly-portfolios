"""Closed-form tests for :mod:`portfolio_edge.studies.stacking`.

No market data. Every fixture is either an identity checkable by hand, a standard-normal
value quoted to machine precision, or a quantity computed independently of the code under
test — in particular the equicorrelated closed form is checked against a full covariance
matrix passed through :func:`portfolio_edge.studies.stacking.stack`, which shares none of
its arithmetic, and the marginal appraisal ratio is checked against the unconstrained
maximum information ratio the same function computes by a matrix solve.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from portfolio_edge.studies.stacking import (
    MDE_TO_STANDARD_ERROR,
    Sleeve,
    _inverse_normal_cdf,
    _normal_cdf,
    confidence_ceiling,
    correlation_to_covariance,
    effective_bets,
    equicorrelated_probability,
    marginal_contribution,
    portfolio_edge_ceiling,
    probability_from_information_ratio,
    probability_with_parameter_uncertainty,
    stack,
    stacking_ceiling_probability,
)

#: ``Phi(1)`` to machine precision. Quoted, not computed, so the assertion depends on no
#: function in the module under test.
PHI_OF_ONE = 0.8413447460685429


def _equicorrelated(count: int, correlation: float) -> list[tuple[float, ...]]:
    return [
        tuple(1.0 if i == j else correlation for j in range(count)) for i in range(count)
    ]


# ---------------------------------------------------------------- the probability core


def test_probability_is_phi_of_ir_times_root_time() -> None:
    """An information ratio of 0.5 over four years is ``Phi(1)``, an independent value."""
    assert probability_from_information_ratio(0.5, horizon_years=4.0) == pytest.approx(
        PHI_OF_ONE, abs=1e-12
    )
    assert probability_from_information_ratio(0.0, horizon_years=30.0) == 0.5
    assert probability_from_information_ratio(-0.5, horizon_years=4.0) == pytest.approx(
        1.0 - PHI_OF_ONE, abs=1e-12
    )
    with pytest.raises(ValueError, match="horizon_years"):
        probability_from_information_ratio(0.5, horizon_years=0.0)


def test_the_sleeve_information_ratio_is_scale_free() -> None:
    """Halving edge and tracking error together leaves the probability untouched.

    This is the reason dilution does not change the odds: a tilt held at 5% of capital
    and the same tilt held at 20% have the same information ratio and the same
    probability of being ahead. Only the size of the prize moves.
    """
    small = Sleeve(label="a", weight=0.05, edge=0.5, tracking_error=5.0)
    large = Sleeve(label="a", weight=0.20, edge=0.5, tracking_error=5.0)
    assert small.information_ratio == pytest.approx(large.information_ratio)
    one = stack([small], [(1.0,)])
    other = stack([large], [(1.0,)])
    assert one.probability(30) == pytest.approx(other.probability(30))
    assert other.edge == pytest.approx(4.0 * one.edge)


def test_a_zero_tracking_error_sleeve_is_a_contractual_edge() -> None:
    certain = Sleeve(label="fee saving", weight=1.0, edge=0.5, tracking_error=0.0)
    assert certain.information_ratio == math.inf
    assert probability_from_information_ratio(math.inf, horizon_years=1.0) == 1.0
    losing = Sleeve(label="fee increase", weight=1.0, edge=-0.5, tracking_error=0.0)
    assert probability_from_information_ratio(losing.information_ratio, horizon_years=1.0) == 0.0
    flat = Sleeve(label="nothing", weight=1.0, edge=0.0, tracking_error=0.0)
    assert flat.information_ratio == 0.0


def test_a_negative_tracking_error_is_rejected() -> None:
    with pytest.raises(ValueError, match="tracking error cannot be negative"):
        Sleeve(label="bad", weight=0.1, edge=1.0, tracking_error=-1e-9)


# --------------------------------------------------------------- the equicorrelated law


@pytest.mark.parametrize("count", [1, 2, 3, 5, 10, 40])
@pytest.mark.parametrize("correlation", [0.0, 0.1, 0.35, 0.6, 0.9])
def test_the_closed_form_matches_a_full_covariance_solve(
    count: int, correlation: float
) -> None:
    """``Phi(z_1 sqrt(k/(1+(k-1)rho)))`` against equal sleeves passed through ``stack``.

    The closed form never builds a matrix and ``stack`` never uses the closed form, so
    agreement is evidence about both.
    """
    single = 0.55
    horizon = 30.0
    edge, tracking = 1.0, 4.0
    sleeves = [
        Sleeve(label=f"s{i}", weight=1.0 / count, edge=edge, tracking_error=tracking)
        for i in range(count)
    ]
    verdict = stack(sleeves, _equicorrelated(count, correlation))
    single_ratio = edge / tracking
    scaled = verdict.information_ratio / single_ratio
    from_closed_form = math.sqrt(
        count / (1.0 + (count - 1) * correlation)
    )
    assert scaled == pytest.approx(from_closed_form)

    # and the same relation stated as probabilities
    from_probability = equicorrelated_probability(
        single_probability=_normal_cdf(single_ratio * math.sqrt(horizon)),
        count=count,
        correlation=correlation,
    )
    assert from_probability == pytest.approx(verdict.probability(horizon))
    assert equicorrelated_probability(
        single_probability=single, count=1, correlation=correlation
    ) == pytest.approx(single)


def test_perfectly_correlated_sleeves_are_one_sleeve() -> None:
    for count in (2, 5, 50):
        assert equicorrelated_probability(
            single_probability=0.55, count=count, correlation=1.0
        ) == pytest.approx(0.55)


def test_the_ceiling_is_the_limit_of_the_stack() -> None:
    """``Phi(z_1/sqrt(rho))`` is approached from below and never crossed."""
    for correlation in (0.1, 0.3, 0.5, 0.8):
        ceiling = stacking_ceiling_probability(
            single_probability=0.55, correlation=correlation
        )
        previous = 0.0
        for count in (1, 10, 1_000, 1_000_000):
            value = equicorrelated_probability(
                single_probability=0.55, count=count, correlation=correlation
            )
            assert value <= ceiling + 1e-12
            assert value >= previous
            previous = value
        assert previous == pytest.approx(ceiling, abs=1e-6)


def test_the_ceiling_at_the_measured_value_correlation() -> None:
    """The number the synthesis quotes, computed here rather than transcribed.

    ``rho = 0.435`` is the mean off-diagonal correlation of the three value tilts'
    modelled excess returns over 1990-11..2025-12. An unlimited number of 55% value
    sleeves at that correlation reaches 0.5756, not 1.
    """
    ceiling = stacking_ceiling_probability(single_probability=0.55, correlation=0.435)
    assert ceiling == pytest.approx(0.5756, abs=5e-4)
    assert (
        equicorrelated_probability(single_probability=0.55, count=100, correlation=0.435)
        == pytest.approx(ceiling, abs=1e-3)
    )


def test_the_ceiling_refuses_a_non_positive_correlation() -> None:
    with pytest.raises(ValueError, match="positive mutual correlation"):
        stacking_ceiling_probability(single_probability=0.55, correlation=0.0)
    with pytest.raises(ValueError, match="positive mutual correlation"):
        stacking_ceiling_probability(single_probability=0.55, correlation=-0.1)
    with pytest.raises(ValueError, match=r"\(0, 1\]"):
        stacking_ceiling_probability(single_probability=0.55, correlation=1.5)
    with pytest.raises(ValueError, match="single_probability"):
        stacking_ceiling_probability(single_probability=0.0, correlation=0.3)


# ------------------------------------------------------------------------- the matrices


def test_correlation_to_covariance_validates_what_a_caller_forgets() -> None:
    covariance = correlation_to_covariance([(1.0, 0.5), (0.5, 1.0)], [2.0, 4.0])
    assert covariance[0][0] == pytest.approx(4.0)
    assert covariance[1][1] == pytest.approx(16.0)
    assert covariance[0][1] == pytest.approx(4.0)
    with pytest.raises(ValueError, match="symmetric"):
        correlation_to_covariance([(1.0, 0.5), (0.4, 1.0)], [1.0, 1.0])
    with pytest.raises(ValueError, match="unit diagonal"):
        correlation_to_covariance([(0.9, 0.5), (0.5, 1.0)], [1.0, 1.0])
    with pytest.raises(ValueError, match="to match"):
        correlation_to_covariance([(1.0, 0.5), (0.5, 1.0)], [1.0, 1.0, 1.0])
    with pytest.raises(ValueError, match="cannot be negative"):
        correlation_to_covariance([(1.0, 0.5), (0.5, 1.0)], [1.0, -1.0])


def test_effective_bets_recovers_the_equicorrelated_form() -> None:
    for count in (2, 4, 9):
        for correlation in (0.0, 0.25, 0.7):
            assert effective_bets(_equicorrelated(count, correlation)) == pytest.approx(
                count / (1.0 + (count - 1) * correlation)
            )


def test_negatively_correlated_sleeves_exceed_their_own_count() -> None:
    """Value against momentum: ``1' R^-1 1`` above ``N`` is a real property, not an error.

    At the measured -0.232 between the modelled AVLV and IDMO excess returns, two
    sleeves are worth 2.6 bets rather than 2. Effective breadth is not capped at the
    number of sleeves and a page that assumes it is will misread this table.
    """
    assert effective_bets([(1.0, -0.232), (-0.232, 1.0)]) == pytest.approx(
        2.0 / (1.0 - 0.232)
    )
    assert effective_bets([(1.0, -0.232), (-0.232, 1.0)]) > 2.0


def test_two_identical_sleeves_are_refused_rather_than_reported() -> None:
    sleeves = [
        Sleeve(label="a", weight=0.5, edge=1.0, tracking_error=4.0),
        Sleeve(label="b", weight=0.5, edge=1.0, tracking_error=4.0),
    ]
    with pytest.raises(ValueError, match="singular"):
        stack(sleeves, [(1.0, 1.0), (1.0, 1.0)])
    with pytest.raises(ValueError, match="cannot score an empty stack"):
        stack([], [])


# ------------------------------------------------------------------- the funding rules


def test_substitution_averages_and_an_overlay_adds() -> None:
    edges = [0.3, 1.2, 0.8]
    assert portfolio_edge_ceiling(edges, rule="substitution") == pytest.approx(1.2)
    assert portfolio_edge_ceiling(edges, rule="overlay") == pytest.approx(2.3)
    assert portfolio_edge_ceiling(
        edges, rule="substitution", total_weight=0.35
    ) == pytest.approx(0.42)
    with pytest.raises(ValueError, match="rule must be one of"):
        portfolio_edge_ceiling(edges, rule="financed")
    with pytest.raises(ValueError, match="at least one sleeve edge"):
        portfolio_edge_ceiling([], rule="overlay")


def test_a_substitution_stack_can_never_beat_its_best_sleeve() -> None:
    """The dilution result, checked exhaustively on a simplex grid rather than argued."""
    edges = [0.3, 1.2, 0.8]
    best = portfolio_edge_ceiling(edges, rule="substitution")
    rng = np.random.default_rng(20260822)
    draws = rng.dirichlet(np.ones(3), size=2_000)
    assert float(np.max(draws @ np.asarray(edges))) <= best + 1e-12


# --------------------------------------------------------------- the marginal criterion


def test_a_redundant_sleeve_adds_nothing_however_good_it_looks_alone() -> None:
    """``alpha = 0`` leaves the information ratio exactly where it was.

    Constructed so the candidate's standalone edge is precisely ``beta`` times the held
    position's: a positive edge, a positive information ratio, and no contribution.
    """
    held_edge, held_tracking = 1.0, 5.0
    correlation = 0.9
    candidate_tracking = 5.0
    beta = correlation * candidate_tracking / held_tracking
    candidate = Sleeve(
        label="redundant",
        weight=0.1,
        edge=beta * held_edge,
        tracking_error=candidate_tracking,
    )
    assert candidate.information_ratio > 0
    verdict = marginal_contribution(
        label="redundant",
        candidate=candidate,
        held_edge=held_edge,
        held_tracking_error=held_tracking,
        correlation_to_held=correlation,
    )
    assert verdict.alpha == pytest.approx(0.0, abs=1e-12)
    assert verdict.appraisal_ratio == pytest.approx(0.0, abs=1e-12)
    assert verdict.information_ratio_after == pytest.approx(
        verdict.information_ratio_before
    )
    assert not verdict.earns_its_place


def test_a_losing_sleeve_earns_its_place_when_its_beta_is_negative_enough() -> None:
    """The investor's own objection, made exact."""
    candidate = Sleeve(label="crisis hedge", weight=0.1, edge=-0.4, tracking_error=12.0)
    assert candidate.information_ratio < 0
    verdict = marginal_contribution(
        label="crisis hedge",
        candidate=candidate,
        held_edge=1.0,
        held_tracking_error=5.0,
        correlation_to_held=-0.35,
    )
    assert verdict.beta < 0
    assert verdict.alpha > 0
    assert verdict.earns_its_place
    assert verdict.information_ratio_after > verdict.information_ratio_before


def test_the_appraisal_ratio_recovers_the_unconstrained_maximum() -> None:
    """``IR_max**2 = IR_held**2 + appraisal**2``, against ``stack``'s matrix solve.

    ``stack`` computes ``sqrt(e' Sigma^-1 e)`` by a linear solve and
    ``marginal_contribution`` computes ``alpha/omega`` from two scalars. They agree, and
    that agreement is the reason the marginal criterion is the right one: the appraisal
    ratio is exactly what the optimiser would have found.
    """
    held = Sleeve(label="held", weight=1.0, edge=1.0, tracking_error=5.0)
    candidate = Sleeve(label="new", weight=0.0, edge=0.6, tracking_error=8.0)
    correlation = 0.25
    verdict = marginal_contribution(
        label="new",
        candidate=candidate,
        held_edge=held.edge,
        held_tracking_error=held.tracking_error,
        correlation_to_held=correlation,
    )
    both = stack(
        [held, Sleeve(label="new", weight=0.0, edge=0.6, tracking_error=8.0)],
        [(1.0, correlation), (correlation, 1.0)],
    )
    assert both.maximum_information_ratio**2 == pytest.approx(
        verdict.information_ratio_before**2 + verdict.appraisal_ratio**2
    )
    assert both.maximum_information_ratio == pytest.approx(
        abs(verdict.information_ratio_after)
    )


def test_a_perfectly_correlated_candidate_has_no_marginal_verdict() -> None:
    candidate = Sleeve(label="clone", weight=0.1, edge=1.0, tracking_error=5.0)
    with pytest.raises(ValueError, match="no residual"):
        marginal_contribution(
            label="clone",
            candidate=candidate,
            held_edge=1.0,
            held_tracking_error=5.0,
            correlation_to_held=1.0,
        )
    with pytest.raises(ValueError, match="correlation must lie"):
        marginal_contribution(
            label="clone",
            candidate=candidate,
            held_edge=1.0,
            held_tracking_error=5.0,
            correlation_to_held=1.5,
        )
    with pytest.raises(ValueError, match="must be positive"):
        marginal_contribution(
            label="clone",
            candidate=candidate,
            held_edge=1.0,
            held_tracking_error=0.0,
            correlation_to_held=0.5,
        )


# ------------------------------------------------------------- the estimated-edge limit


def test_a_known_edge_is_the_zero_uncertainty_case() -> None:
    known = probability_from_information_ratio(0.25, horizon_years=30.0)
    estimated = probability_with_parameter_uncertainty(
        edge=1.0, edge_standard_error=0.0, tracking_error=4.0, horizon_years=30.0
    )
    assert estimated == pytest.approx(known)


def test_parameter_uncertainty_only_ever_pulls_the_probability_towards_a_half() -> None:
    previous = probability_with_parameter_uncertainty(
        edge=1.0, edge_standard_error=0.0, tracking_error=4.0, horizon_years=30.0
    )
    for tau in (0.1, 0.25, 0.5, 1.0, 4.0):
        value = probability_with_parameter_uncertainty(
            edge=1.0, edge_standard_error=tau, tracking_error=4.0, horizon_years=30.0
        )
        assert value < previous
        assert value > 0.5
        previous = value


def test_waiting_longer_stops_helping_at_the_confidence_ceiling() -> None:
    """``Phi(e/tau)`` bounds the probability at every horizon, and is reached in the limit."""
    ceiling = confidence_ceiling(edge=1.0, edge_standard_error=0.5)
    assert ceiling == pytest.approx(_normal_cdf(2.0))
    previous = 0.0
    for horizon in (10.0, 30.0, 1_000.0, 1e8):
        value = probability_with_parameter_uncertainty(
            edge=1.0, edge_standard_error=0.5, tracking_error=4.0, horizon_years=horizon
        )
        assert value <= ceiling + 1e-12
        assert value >= previous
        previous = value
    assert previous == pytest.approx(ceiling, abs=1e-6)
    with pytest.raises(ValueError, match="estimated edge"):
        confidence_ceiling(edge=1.0, edge_standard_error=0.0)


def test_the_mde_conversion_is_the_two_quantile_sum() -> None:
    """The same constant :mod:`factor_breadth` builds an MDE from, used in reverse."""
    assert pytest.approx(2.4864748605243866) == MDE_TO_STANDARD_ERROR
    # A published MDE80 of 3.67 pp/yr on the developed ex-US HML premium implies a
    # standard error of 1.476 pp/yr, which is the number the synthesis quotes.
    standard_error = 3.67 / MDE_TO_STANDARD_ERROR
    assert standard_error == pytest.approx(1.4760, abs=5e-4)


def test_a_bad_horizon_or_a_negative_input_is_refused() -> None:
    with pytest.raises(ValueError, match="horizon_years"):
        probability_with_parameter_uncertainty(
            edge=1.0, edge_standard_error=0.5, tracking_error=4.0, horizon_years=0.0
        )
    with pytest.raises(ValueError, match="edge_standard_error"):
        probability_with_parameter_uncertainty(
            edge=1.0, edge_standard_error=-1e-9, tracking_error=4.0, horizon_years=1.0
        )
    with pytest.raises(ValueError, match="tracking_error"):
        probability_with_parameter_uncertainty(
            edge=1.0, edge_standard_error=0.5, tracking_error=-1e-9, horizon_years=1.0
        )


# ------------------------------------------------------------------------- the normals


@pytest.mark.parametrize(
    "probability",
    [1e-10, 1e-4, 0.01, 0.02, 0.1, 0.4, 0.5, 0.55, 0.6, 0.9, 0.99, 1 - 1e-10],
)
def test_the_inverse_normal_round_trips_to_machine_precision(probability: float) -> None:
    assert _normal_cdf(_inverse_normal_cdf(probability)) == pytest.approx(
        probability, rel=1e-12, abs=1e-15
    )


def test_the_normal_cdf_matches_quoted_values() -> None:
    assert _normal_cdf(0.0) == pytest.approx(0.5)
    assert _normal_cdf(1.0) == pytest.approx(PHI_OF_ONE, abs=1e-15)
    assert _inverse_normal_cdf(0.975) == pytest.approx(1.959963984540054, abs=1e-10)
    with pytest.raises(ValueError, match="p must lie"):
        _inverse_normal_cdf(1.0)
