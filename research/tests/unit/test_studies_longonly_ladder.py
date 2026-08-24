"""Closed-form tests for :mod:`portfolio_edge.studies.longonly_ladder`.

No market data. The fixtures are of three kinds and the distinction matters:

* **Identities checkable by hand.** The two-candidate maximum information ratio has a
  closed form derived below from the 2x2 inverse, so it is computed independently of the
  ``numpy`` linear solve the module uses.
* **Cross-checks between two paths that share no arithmetic.** The equicorrelated equal-
  weight closed form ``mean(e)/sigma * sqrt(k/(1+(k-1)rho))`` is checked against the full
  matrix path, and the exact support enumeration is checked against a dense random search
  over the non-negative simplex, which cannot exceed it.
* **Constraint and edge behaviour.** Ranking, singularity, positive-definiteness, shelf
  size, degenerate edges, units and annualisation.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

from portfolio_edge.core._types import FloatArray
from portfolio_edge.studies.longonly_ladder import (
    MAXIMUM_CANDIDATES,
    correlation_sweep,
    equal_weight_information_ratio,
    equicorrelated_matrix,
    ladder,
    long_only_maximum,
    transfer_coefficient,
    unconstrained_maximum_information_ratio,
    unconstrained_weights,
)
from portfolio_edge.studies.stacking import correlation_to_covariance

#: The ladder published in ``docs/research/stacking-and-effective-breadth.md`` §5 and
#: frozen in ``research/experiments/exp_017_longonly_ladder.yaml``. Gross edges in
#: percentage points a year, ranked best to worst.
LADDER_EDGES = (3.0, 2.4, 1.9, 1.5, 1.2, 0.9, 0.7, 0.5, 0.35, 0.2, 0.1, 0.0)
LADDER_COST = 0.40
LADDER_TRACKING_ERROR = 6.0
LADDER_CORRELATION = 0.435


def _equicorrelated_covariance(
    count: int, correlation: float, tracking_error: float
) -> FloatArray:
    matrix = equicorrelated_matrix(count, correlation)
    return correlation_to_covariance(
        [tuple(float(x) for x in row) for row in matrix], [tracking_error] * count
    )


# ------------------------------------------------------- an independently computed fixture


def test_two_candidate_maximum_matches_the_hand_derived_closed_form() -> None:
    """``e' Sigma^-1 e`` for two candidates, derived from the 2x2 inverse rather than solved.

    With ``Sigma = [[s1^2, rho s1 s2], [rho s1 s2, s2^2]]`` the inverse is
    ``1/(s1^2 s2^2 (1 - rho^2)) [[s2^2, -rho s1 s2], [-rho s1 s2, s1^2]]``, so writing
    ``IR_i = e_i / s_i``,

        e' Sigma^-1 e = (IR_1^2 - 2 rho IR_1 IR_2 + IR_2^2) / (1 - rho^2)

    which shares no arithmetic with the module's ``numpy.linalg.solve`` path. The numbers
    below are deliberately asymmetric so that a transposition or a swapped index would
    change the answer.
    """
    edge_one, edge_two = 3.0, 1.25
    error_one, error_two = 5.0, 8.0
    rho = 0.3
    covariance = (
        (error_one**2, rho * error_one * error_two),
        (rho * error_one * error_two, error_two**2),
    )

    ratio_one = edge_one / error_one
    ratio_two = edge_two / error_two
    expected = math.sqrt(
        (ratio_one**2 - 2.0 * rho * ratio_one * ratio_two + ratio_two**2) / (1.0 - rho**2)
    )
    # Worked by hand: IR_1 = 0.6 and IR_2 = 0.15625, so the numerator is
    # 0.36 - 2 x 0.3 x 0.6 x 0.15625 + 0.0244140625 = 0.3281640625, and dividing by
    # 1 - 0.09 = 0.91 gives 0.3606198489010989. The literal below is that quotient.
    assert expected == pytest.approx(math.sqrt(0.3606198489010989), rel=1e-15)

    assert unconstrained_maximum_information_ratio(
        (edge_one, edge_two), covariance
    ) == pytest.approx(expected, rel=1e-12)


def test_two_candidate_long_only_drops_the_candidate_the_optimiser_would_short() -> None:
    """When ``IR_2 < rho IR_1`` the unconstrained weight on the second is negative.

    ``Sigma^-1 e`` is proportional to ``(IR_1 - rho IR_2, IR_2 - rho IR_1)`` after scaling
    by ``1/s_i``, so the second weight turns negative exactly at ``IR_2 = rho IR_1``. The
    long-only optimum must then be the first candidate alone, at its own standalone
    information ratio, and the transfer coefficient must be strictly below one.
    """
    edge_one, error_one = 3.0, 5.0  # IR = 0.60
    edge_two, error_two = 1.0, 10.0  # IR = 0.10
    rho = 0.5  # rho * IR_1 = 0.30 > 0.10
    covariance = (
        (error_one**2, rho * error_one * error_two),
        (rho * error_one * error_two, error_two**2),
    )

    optimum = long_only_maximum((edge_one, edge_two), covariance)
    assert optimum.support == (0,)
    assert optimum.sleeves_held == 1
    assert optimum.weights == pytest.approx((1.0, 0.0))
    assert optimum.information_ratio == pytest.approx(edge_one / error_one, rel=1e-12)
    assert optimum.supports_examined == 3  # 2^2 - 1

    maximum = unconstrained_maximum_information_ratio((edge_one, edge_two), covariance)
    assert maximum > optimum.information_ratio
    assert transfer_coefficient(optimum.information_ratio, maximum) < 1.0
    assert unconstrained_weights((edge_one, edge_two), covariance)[1] < 0.0


# ----------------------------------------------------- two paths that share no arithmetic


@pytest.mark.parametrize("count", [1, 2, 3, 5, 8, 12])
def test_equal_weight_matches_the_equicorrelated_closed_form(count: int) -> None:
    """``mean(e)/sigma * sqrt(k/(1+(k-1)rho))`` against the full covariance path."""
    edges = tuple(LADDER_EDGES[:count])
    rho = LADDER_CORRELATION
    sigma = LADDER_TRACKING_ERROR
    closed_form = (
        sum(edges)
        / count
        / sigma
        * math.sqrt(count / (1.0 + (count - 1) * rho))
    )
    covariance = _equicorrelated_covariance(count, rho, sigma)
    assert equal_weight_information_ratio(edges, covariance) == pytest.approx(
        closed_form, rel=1e-12
    )


def test_support_enumeration_is_not_beaten_by_a_dense_simplex_search() -> None:
    """A brute-force search over the non-negative simplex cannot exceed the exact optimum.

    The random search is not a fixture and is not allowed to *set* the answer; it can only
    falsify it, which is the correct direction for a check on a maximiser.
    """
    edges = LADDER_EDGES[:8]
    net = tuple(one - LADDER_COST for one in edges)
    covariance = _equicorrelated_covariance(8, LADDER_CORRELATION, LADDER_TRACKING_ERROR)
    optimum = long_only_maximum(net, covariance)

    rng = np.random.default_rng(20260823)
    vector = np.asarray(net, dtype=np.float64)
    matrix = np.asarray(covariance, dtype=np.float64)
    draws = rng.dirichlet(np.ones(8), size=40_000)
    numerator = draws @ vector
    denominator = np.sqrt(np.einsum("ij,jk,ik->i", draws, matrix, draws))
    best_random = float(np.max(numerator / denominator))

    assert best_random <= optimum.information_ratio + 1e-12
    # and the search should get reasonably close, or the optimum is in a corner the
    # enumeration found and the simplex draw cannot see, which would be worth knowing.
    assert best_random > 0.9 * optimum.information_ratio


def test_every_feasible_support_is_dominated_by_the_reported_one() -> None:
    """Re-derive the optimum by an independent enumeration written in the test."""
    net = tuple(one - LADDER_COST for one in LADDER_EDGES[:6])
    covariance = np.asarray(
        _equicorrelated_covariance(6, LADDER_CORRELATION, LADDER_TRACKING_ERROR)
    )
    vector = np.asarray(net)
    best = -math.inf
    for width in range(1, 7):
        for support in itertools.combinations(range(6), width):
            columns = list(support)
            weights = np.linalg.solve(
                covariance[np.ix_(columns, columns)], vector[columns]
            )
            if np.any(weights < 0.0):
                continue
            scaled = np.zeros(6)
            scaled[columns] = weights
            best = max(
                best,
                float(scaled @ vector) / math.sqrt(float(scaled @ covariance @ scaled)),
            )
    assert long_only_maximum(net, covariance).information_ratio == pytest.approx(
        best, rel=1e-12
    )


# ------------------------------------------------------------------- the published result


def test_the_published_ladder_reproduces_its_headline_numbers() -> None:
    """The three numbers ``/stacking`` quotes, and the shape behind them."""
    rungs = {
        rung.count: rung
        for rung in ladder(
            LADDER_EDGES,
            cost=LADDER_COST,
            tracking_error=LADDER_TRACKING_ERROR,
            correlation=LADDER_CORRELATION,
        )
    }

    # The equal-weighted optimum is two, and holding all twelve is far worse than one.
    equal = {count: rung.equal_weight_information_ratio for count, rung in rungs.items()}
    assert max(equal, key=lambda count: equal[count]) == 2
    assert equal[12] < equal[1] / 2.0

    # The long-only optimum holds three and never improves past three.
    assert rungs[3].sleeves_held == 3
    for count in (3, 5, 8, 12):
        assert rungs[count].sleeves_held == 3
        assert rungs[count].long_only_information_ratio == pytest.approx(
            rungs[3].long_only_information_ratio, rel=1e-12
        )

    # The unconstrained optimum keeps rising, and the gap is the transfer coefficient.
    assert rungs[12].unconstrained_information_ratio > rungs[3].unconstrained_information_ratio
    assert rungs[12].long_only_transfer_coefficient < rungs[3].long_only_transfer_coefficient
    assert rungs[3].long_only_transfer_coefficient == pytest.approx(1.0, abs=1e-12)

    # Everything the unconstrained optimiser gains past three, it gains by shorting.
    net = tuple(one - LADDER_COST for one in LADDER_EDGES)
    covariance = _equicorrelated_covariance(12, LADDER_CORRELATION, LADDER_TRACKING_ERROR)
    weights = unconstrained_weights(net, covariance)
    assert int(np.sum(weights < 0.0)) == 7
    assert abs(float(weights.sum())) < 0.10  # net long is under a tenth of gross


def test_the_optimum_is_two_with_every_cost_set_to_zero() -> None:
    """Dilution alone produces the shape; costs only sharpen it."""
    rungs = ladder(
        LADDER_EDGES,
        cost=0.0,
        tracking_error=LADDER_TRACKING_ERROR,
        correlation=LADDER_CORRELATION,
    )
    equal = {rung.count: rung.equal_weight_information_ratio for rung in rungs}
    assert max(equal, key=lambda count: equal[count]) == 2


def test_identical_edges_make_equal_weighting_optimal() -> None:
    """The scope limit that must travel with the count: dispersion is what collapses it."""
    flat = (2.0,) * 8
    rung = ladder(
        flat,
        cost=LADDER_COST,
        tracking_error=LADDER_TRACKING_ERROR,
        correlation=LADDER_CORRELATION,
        counts=(8,),
    )[0]
    assert rung.sleeves_held == 8
    assert rung.long_only_transfer_coefficient == pytest.approx(1.0, abs=1e-12)
    assert rung.equal_weight_transfer_coefficient == pytest.approx(1.0, abs=1e-12)
    assert rung.long_only_weights == pytest.approx((1.0 / 8,) * 8)


def test_the_two_columns_of_the_correlation_sweep_move_in_opposite_directions() -> None:
    sweep = correlation_sweep(
        LADDER_EDGES,
        cost=LADDER_COST,
        tracking_error=LADDER_TRACKING_ERROR,
        correlations=(0.10, 0.20, 0.30, 0.435, 0.50, 0.70),
    )
    unconstrained = [rung.unconstrained_information_ratio for _, rung in sweep]
    constrained = [rung.long_only_information_ratio for _, rung in sweep]
    held = [rung.sleeves_held for _, rung in sweep]

    assert unconstrained == sorted(unconstrained)
    assert constrained == sorted(constrained, reverse=True)
    assert held == sorted(held, reverse=True)
    assert held[0] == 5 and held[-1] == 2


# ------------------------------------------------------------- units and annualisation


def test_scaling_edges_and_tracking_errors_together_leaves_every_ratio_alone() -> None:
    """The information ratio is scale-free, so the unit of the inputs cannot change a count.

    Reported in percentage points a year throughout; restating the same shelf in basis
    points must move no ratio, no transfer coefficient and no count.
    """
    base = ladder(
        LADDER_EDGES,
        cost=LADDER_COST,
        tracking_error=LADDER_TRACKING_ERROR,
        correlation=LADDER_CORRELATION,
        counts=(12,),
    )[0]
    in_basis_points = ladder(
        tuple(one * 100.0 for one in LADDER_EDGES),
        cost=LADDER_COST * 100.0,
        tracking_error=LADDER_TRACKING_ERROR * 100.0,
        correlation=LADDER_CORRELATION,
        counts=(12,),
    )[0]

    assert in_basis_points.equal_weight_information_ratio == pytest.approx(
        base.equal_weight_information_ratio, rel=1e-12
    )
    assert in_basis_points.long_only_information_ratio == pytest.approx(
        base.long_only_information_ratio, rel=1e-12
    )
    assert in_basis_points.sleeves_held == base.sleeves_held
    assert in_basis_points.mean_net_edge == pytest.approx(base.mean_net_edge * 100.0)


def test_probability_annualises_through_the_shared_identity() -> None:
    """``Phi(IR sqrt(T))`` at the equal-weight ratio, and the horizon enters only there."""
    rung = ladder(
        LADDER_EDGES,
        cost=LADDER_COST,
        tracking_error=LADDER_TRACKING_ERROR,
        correlation=LADDER_CORRELATION,
        counts=(2,),
    )[0]
    ratio = rung.equal_weight_information_ratio
    for horizon in (1.0, 10.0, 30.0):
        expected = 0.5 * math.erfc(-ratio * math.sqrt(horizon) / math.sqrt(2.0))
        assert rung.probability(horizon) == pytest.approx(expected, abs=1e-12)
    assert rung.probability(30.0) > rung.probability(1.0)


def test_available_bets_is_the_shared_effective_breadth_definition() -> None:
    for rung in ladder(
        LADDER_EDGES,
        cost=LADDER_COST,
        tracking_error=LADDER_TRACKING_ERROR,
        correlation=LADDER_CORRELATION,
    ):
        expected = rung.count / (1.0 + (rung.count - 1) * LADDER_CORRELATION)
        assert rung.available_bets == pytest.approx(expected, rel=1e-12)
        assert rung.sharpe_multiple == pytest.approx(math.sqrt(expected), rel=1e-12)
    ceiling = 1.0 / LADDER_CORRELATION
    assert all(
        rung.available_bets < ceiling
        for rung in ladder(
            LADDER_EDGES,
            cost=LADDER_COST,
            tracking_error=LADDER_TRACKING_ERROR,
            correlation=LADDER_CORRELATION,
        )
    )


# ------------------------------------------------------------ constraints and edge cases


def test_a_single_candidate_is_its_own_optimum_everywhere() -> None:
    rung = ladder(
        (3.0,), cost=0.4, tracking_error=6.0, correlation=0.435, counts=(1,)
    )[0]
    assert rung.sleeves_held == 1
    assert rung.equal_weight_information_ratio == pytest.approx(2.6 / 6.0, rel=1e-12)
    assert rung.long_only_information_ratio == pytest.approx(2.6 / 6.0, rel=1e-12)
    assert rung.unconstrained_information_ratio == pytest.approx(2.6 / 6.0, rel=1e-12)
    assert rung.long_only_transfer_coefficient == pytest.approx(1.0, abs=1e-12)
    assert rung.available_bets == pytest.approx(1.0)


def test_unranked_edges_are_refused() -> None:
    with pytest.raises(ValueError, match="ranked best to worst"):
        ladder((1.0, 3.0, 2.0), cost=0.4, tracking_error=6.0, correlation=0.4)


def test_a_shelf_with_no_positive_net_edge_is_refused_rather_than_maximised() -> None:
    covariance = _equicorrelated_covariance(3, 0.4, 6.0)
    with pytest.raises(ValueError, match="no candidate has a positive edge"):
        long_only_maximum((-0.1, -0.2, -0.3), covariance)


def test_a_singular_covariance_is_refused() -> None:
    perfect = ((1.0, 1.0), (1.0, 1.0))
    covariance = correlation_to_covariance(perfect, [6.0, 6.0])
    with pytest.raises(ValueError, match="singular to working precision"):
        unconstrained_maximum_information_ratio((2.0, 1.0), covariance)
    with pytest.raises(ValueError, match="singular to working precision"):
        long_only_maximum((2.0, 1.0), covariance)


def test_an_indefinite_equicorrelated_matrix_is_refused() -> None:
    equicorrelated_matrix(3, -0.49)  # just inside the -1/(k-1) floor
    with pytest.raises(ValueError, match="not positive definite"):
        equicorrelated_matrix(3, -0.5)
    with pytest.raises(ValueError, match="strictly in"):
        equicorrelated_matrix(3, 1.0)


def test_an_oversized_shelf_is_refused_rather_than_approximated() -> None:
    size = MAXIMUM_CANDIDATES + 1
    edges = tuple(float(size - i) for i in range(size))
    covariance = _equicorrelated_covariance(size, 0.4, 6.0)
    with pytest.raises(ValueError, match="exceeds the"):
        long_only_maximum(edges, covariance)


def test_a_transfer_coefficient_needs_a_positive_denominator() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        transfer_coefficient(0.0, 0.0)


def test_a_rung_outside_the_shelf_is_refused() -> None:
    with pytest.raises(ValueError, match="outside the shelf"):
        ladder((3.0, 2.0), cost=0.4, tracking_error=6.0, correlation=0.4, counts=(3,))


def test_a_non_positive_tracking_error_is_refused() -> None:
    with pytest.raises(ValueError, match="tracking_error must be positive"):
        ladder((3.0, 2.0), cost=0.4, tracking_error=0.0, correlation=0.4)
