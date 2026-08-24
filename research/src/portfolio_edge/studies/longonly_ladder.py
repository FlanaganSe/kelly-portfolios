"""How many strategies a long-only optimiser holds when the candidates are correlated.

:mod:`portfolio_edge.studies.stacking` prices a stack whose weights the caller supplies.
This module asks the question that comes next and is the one people actually quote: given
a shelf of candidate strategies ranked best to worst, **how many of them does an optimiser
hold, and how much of the theoretical benefit does a long-only investor forfeit?**

The three quantities, and they are three different things.

**1. Equal weights.** ``IR = w'e / sqrt(w' Sigma w)`` at ``w_i = 1/k``. Under equal edges,
equal tracking errors and mutual correlation ``rho`` this collapses to
``mean(e) / sigma * sqrt(k / (1 + (k-1) rho))``, which is the closed form
:func:`portfolio_edge.studies.stacking.equicorrelated_probability` already uses. The
second factor grows as a square root and asymptotes at ``1/sqrt(rho)``; the first is a
plain average and every below-average candidate drags it down **linearly**. A sublinear
bounded benefit against a linear unbounded cost has an interior optimum, and the optimum
is small. Costs sharpen it; dilution alone produces it.

**2. Unconstrained weights.** ``w* proportional to Sigma^-1 e``, giving
``IR_max = sqrt(e' Sigma^-1 e)``. This is the quantity
:func:`portfolio_edge.studies.stacking.stack` already reports as
``maximum_information_ratio``, and it is monotone in the candidate set: adding a candidate
with a non-zero appraisal ratio can never lower it. On this reading "stack a ton" is
correct, which is why the disagreement is never about the theorem.

**3. Long-only weights.** ``max IR`` over ``w >= 0``. Solved here **exactly**, by
enumerating supports rather than by an iterative solver, so the answer carries no
convergence tolerance and no starting point. The optimum's own support ``S`` is interior
in the reduced problem, so ``w_S`` is proportional to ``Sigma_S^-1 e_S``; enumerating
every subset, keeping the ones whose solution is non-negative, and taking the largest
information ratio therefore returns the exact optimum. Cost is ``2^k - 1`` linear solves,
which is why :data:`MAXIMUM_CANDIDATES` refuses a shelf large enough to matter.

The ratio of (3) to (2) is the **transfer coefficient** of Clarke, de Silva and Thorley
(2002), ``IR = TC x IC x sqrt(BR)``: the fraction of the achievable information ratio a
constrained investor reaches. It is reported here as a ratio of information ratios, which
is what that identity makes it, and not as a correlation estimated from a simulation.

Two limits on anything computed here, and they are the reason this module takes edges as
arguments rather than measuring them.

* **Every edge is an input.** This module estimates no premium, prices no fund and reads
  no market data. A ladder of candidate edges is an assumption set; a conclusion drawn
  from one is a property of that assumption set, and the sensitivity of the answer to it
  is the thing worth reporting. :func:`correlation_sweep` exists for that reason.
* **The answer depends on edge dispersion, not only on correlation.** Give every candidate
  the *same* edge and equal weighting is optimal, the transfer coefficient is 1.0, and the
  optimiser holds all of them. The count collapses because real shelves have dispersed
  edges and the optimiser can tell them apart. Both facts should travel together;
  :func:`ladder` reports the held count so neither can be quoted alone.

Units follow :mod:`portfolio_edge.studies.stacking`: edges and costs are percentage points
a year, tracking errors are percentage points a year, weights are fractions. Probability
is delegated to :mod:`portfolio_edge.studies.outperformance_horizon` through
:func:`portfolio_edge.studies.stacking.probability_from_information_ratio`, so the horizon
convention and the "edge treated as known" warning are inherited rather than restated.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, TypeAlias

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.studies.overlay_growth import effective_breadth
from portfolio_edge.studies.stacking import (
    correlation_to_covariance,
    probability_from_information_ratio,
)

#: Accepted input shapes. Spelled out because every function here is called both with
#: literal tuples from a test and with ``numpy`` arrays from an experiment, and silently
#: accepting only one of them would push a conversion into every call site.
EdgeInput: TypeAlias = "Sequence[float] | FloatArray"  # noqa: UP040 - matches specification.py
MatrixInput: TypeAlias = "Sequence[Sequence[float]] | FloatArray"  # noqa: UP040

__all__ = [
    "MAXIMUM_CANDIDATES",
    "EdgeInput",
    "LadderRung",
    "LongOnlyOptimum",
    "MatrixInput",
    "correlation_sweep",
    "equal_weight_information_ratio",
    "equicorrelated_matrix",
    "ladder",
    "long_only_maximum",
    "transfer_coefficient",
    "unconstrained_maximum_information_ratio",
    "unconstrained_weights",
]

#: Support enumeration is exact and costs ``2^k - 1`` linear solves. Twenty candidates is
#: already a million of them, and a shelf that large is not a retail decision. Refusing is
#: better than silently substituting an iterative solver whose answer would carry a
#: tolerance the caller never sees.
MAXIMUM_CANDIDATES: Final = 18

#: Weights below this are read as zero when counting how many candidates are held. An exact
#: support-enumeration optimum produces exact zeros off its own support, so this only
#: absorbs the rounding of the linear solve on the support itself.
_HELD_TOLERANCE: Final = 1e-9


@dataclass(frozen=True)
class LadderRung:
    """One rung of the ladder: what holding the best ``count`` candidates is worth.

    ``mean_net_edge`` is the plain average of the held candidates' edges net of cost — the
    factor that falls linearly. ``available_bets`` is ``k / (1 + (k-1) rho)``, the factor
    that grows as a square root and stops. ``sharpe_multiple`` is its square root, the
    most a caller could buy with breadth alone at this rung.

    The three information ratios are the same portfolio scored under three weighting rules
    and are not alternatives to one another: ``equal_weight`` is what an investor typically
    does, ``long_only`` is the best they are permitted to do, and ``unconstrained`` is what
    the theorem promises. ``sleeves_held`` counts the non-zero weights at the long-only
    optimum and is the number this module exists to report.
    """

    count: int
    mean_net_edge: float
    available_bets: float
    sharpe_multiple: float
    equal_weight_information_ratio: float
    unconstrained_information_ratio: float
    long_only_information_ratio: float
    equal_weight_transfer_coefficient: float
    long_only_transfer_coefficient: float
    sleeves_held: int
    long_only_weights: tuple[float, ...]

    def probability(self, horizon_years: float) -> float:
        """``Phi(IR sqrt(T))`` at the **equal-weight** information ratio.

        Equal weight rather than optimal because the ladder's point is what an investor
        who adds candidates without re-optimising actually gets. Read it as an upper bound
        even so: it treats the edge as known, which
        :func:`portfolio_edge.studies.stacking.confidence_ceiling` shows is the assumption
        that flatters the answer most.
        """
        return probability_from_information_ratio(
            self.equal_weight_information_ratio, horizon_years=horizon_years
        )


@dataclass(frozen=True)
class LongOnlyOptimum:
    """The exact solution of ``max w'e / sqrt(w' Sigma w)`` subject to ``w >= 0``.

    ``weights`` are normalised to sum to one, which is scale-free: the objective is
    invariant to scaling ``w``, so the budget constraint fixes the size of the position
    without changing the information ratio or the identity of the support.

    ``supports_examined`` is reported so a reader can confirm the search was exhaustive
    rather than heuristic.
    """

    information_ratio: float
    weights: tuple[float, ...]
    support: tuple[int, ...]
    supports_examined: int

    @property
    def sleeves_held(self) -> int:
        return len(self.support)


def equicorrelated_matrix(count: int, correlation: float) -> FloatArray:
    """``R`` with a unit diagonal and ``rho`` everywhere else.

    Rejects a correlation that would make ``R`` indefinite. For ``k`` assets the smallest
    eigenvalue is ``1 - rho``, with multiplicity ``k - 1``, and the largest is
    ``1 + (k-1) rho``; so ``rho`` must lie in ``[-1/(k-1), 1]`` and the boundary is
    singular. A caller who wants the boundary wants a different model.
    """
    if count < 1:
        raise ValueError(f"need at least one candidate, got {count}")
    if not -1.0 < correlation < 1.0:
        raise ValueError(f"correlation must lie strictly in (-1, 1), got {correlation}")
    lower = -1.0 / (count - 1) if count > 1 else -1.0
    if correlation <= lower:
        raise ValueError(
            f"an equicorrelated matrix of {count} assets is not positive definite at "
            f"rho = {correlation}; the floor is {lower:.6f}"
        )
    matrix = np.full((count, count), float(correlation), dtype=np.float64)
    np.fill_diagonal(matrix, 1.0)
    return matrix


def equal_weight_information_ratio(
    edges: EdgeInput, covariance: MatrixInput
) -> float:
    """``mean(e) / sqrt(w' Sigma w)`` at ``w_i = 1/k``.

    Computed from the covariance matrix rather than from the equicorrelated closed form,
    so that a test can check the two against each other.
    """
    vector = _as_edges(edges)
    matrix = _as_covariance(covariance, vector.size)
    weights = np.full(vector.size, 1.0 / vector.size, dtype=np.float64)
    variance = float(weights @ matrix @ weights)
    if variance <= 0.0:
        raise ValueError(
            f"the equal-weight tracking variance is {variance:.3e}; the covariance matrix "
            "is not positive definite"
        )
    return float(weights @ vector) / math.sqrt(variance)


def unconstrained_weights(
    edges: EdgeInput, covariance: MatrixInput
) -> FloatArray:
    """``Sigma^-1 e``, normalised so the absolute weights sum to one.

    Normalised on **gross** rather than net exposure because the interesting property of
    this solution is how much of it is short: at a positive mutual correlation the
    unconstrained optimum finances the good candidates by shorting the poor ones, and a
    net-normalised vector hides that by dividing by a small number.
    """
    vector = _as_edges(edges)
    matrix = _as_covariance(covariance, vector.size)
    raw = np.linalg.solve(matrix, vector)
    gross = float(np.abs(raw).sum())
    if gross <= 0.0:
        raise ValueError("every unconstrained weight is zero; the edges are all zero")
    return np.asarray(raw / gross, dtype=np.float64)


def unconstrained_maximum_information_ratio(
    edges: EdgeInput, covariance: MatrixInput
) -> float:
    """``sqrt(e' Sigma^-1 e)``: the most any weighting of these candidates can achieve."""
    vector = _as_edges(edges)
    matrix = _as_covariance(covariance, vector.size)
    quadratic = float(vector @ np.linalg.solve(matrix, vector))
    if quadratic < 0.0:
        raise ValueError(
            f"e' Sigma^-1 e is negative ({quadratic:.3e}); the covariance matrix is not "
            "positive definite"
        )
    return math.sqrt(quadratic)


def long_only_maximum(
    edges: EdgeInput, covariance: MatrixInput
) -> LongOnlyOptimum:
    """Exact ``max IR`` subject to ``w >= 0``, by enumerating every support.

    The objective is scale-invariant, so the sum-to-one budget does not bind on the
    information ratio: it fixes the size of the answer and nothing else. The optimum's
    support ``S`` is interior in the problem restricted to ``S``, so on that support the
    solution satisfies ``Sigma_S w_S proportional to e_S``. Every candidate is therefore
    ``Sigma_S^-1 e_S`` for some ``S``, and the exhaustive search over subsets is exact
    rather than approximate.

    Raises when every candidate edge is non-positive: the constrained problem then has no
    interior optimum and the honest answer is that nothing on the shelf is worth holding,
    which a returned information ratio of zero would disguise.
    """
    vector = _as_edges(edges)
    matrix = _as_covariance(covariance, vector.size)
    size = vector.size
    if size > MAXIMUM_CANDIDATES:
        raise ValueError(
            f"support enumeration is exact but costs 2^k solves; {size} candidates "
            f"exceeds the {MAXIMUM_CANDIDATES} this module will attempt. A larger shelf "
            "needs a different algorithm, and the answer would then carry a tolerance."
        )
    if not np.any(vector > 0.0):
        raise ValueError(
            "no candidate has a positive edge, so no long-only position has a positive "
            "information ratio. That is the result; it is not a maximisation."
        )

    best_ratio = -math.inf
    best_support: tuple[int, ...] = ()
    best_weights = np.zeros(size, dtype=np.float64)
    examined = 0
    indices = range(size)
    for width in range(1, size + 1):
        for support in itertools.combinations(indices, width):
            examined += 1
            columns = list(support)
            sub_edges = vector[columns]
            sub_covariance = matrix[np.ix_(columns, columns)]
            try:
                raw = np.linalg.solve(sub_covariance, sub_edges)
            except np.linalg.LinAlgError:  # pragma: no cover - guarded by _as_covariance
                continue
            if np.any(raw < -_HELD_TOLERANCE):
                continue
            total = float(raw.sum())
            if total <= 0.0:
                continue
            ratio = float(sub_edges @ raw) / math.sqrt(float(raw @ sub_covariance @ raw))
            if ratio > best_ratio + 1e-15:
                best_ratio = ratio
                best_support = support
                best_weights = np.zeros(size, dtype=np.float64)
                best_weights[columns] = raw / total

    if not best_support:  # pragma: no cover - unreachable while some edge is positive
        raise ValueError("no feasible long-only support was found")
    return LongOnlyOptimum(
        information_ratio=best_ratio,
        weights=tuple(float(one) for one in best_weights),
        support=best_support,
        supports_examined=examined,
    )


def transfer_coefficient(achieved: float, unconstrained: float) -> float:
    """``IR_achieved / IR_max``, the Clarke-de Silva-Thorley transfer coefficient.

    Raises on a non-positive denominator rather than returning a ratio: a shelf with no
    achievable information ratio has no transfer coefficient, and returning zero or
    infinity would put a number where there is none.
    """
    if not unconstrained > 0.0:
        raise ValueError(
            f"the unconstrained information ratio must be positive to form a transfer "
            f"coefficient, got {unconstrained}"
        )
    return achieved / unconstrained


def ladder(
    edges: EdgeInput,
    *,
    cost: float,
    tracking_error: float,
    correlation: float,
    counts: Sequence[int] | None = None,
) -> tuple[LadderRung, ...]:
    """Score the best ``k`` candidates of a ranked shelf, for each ``k`` in ``counts``.

    ``edges`` are **gross** and must be supplied already ranked best to worst — the whole
    mechanism is that an investor buys their best idea first, so a caller who sorts inside
    this function would be assuming the conclusion. ``cost`` is charged identically to
    every candidate and covers fee, turnover, spread and tax together; a per-candidate
    cost belongs in ``edges``.

    ``tracking_error`` and ``correlation`` are common to every candidate. That is a strong
    assumption and it is deliberate: it isolates the count from every other difference
    between candidates, so a result stated in counts cannot be an artefact of one
    candidate having been given a smaller tracking error than another.
    """
    gross = _as_edges(edges)
    if gross.size < 1:
        raise ValueError("need at least one candidate edge")
    if not np.all(np.diff(gross) <= 1e-12):
        raise ValueError(
            "edges must be supplied ranked best to worst; the ladder's mechanism is that "
            f"the best idea is bought first, so sorting here would beg the question. Got "
            f"{[float(one) for one in gross]}"
        )
    if tracking_error <= 0.0:
        raise ValueError(f"tracking_error must be positive, got {tracking_error}")
    rungs = tuple(counts) if counts is not None else tuple(range(1, gross.size + 1))
    for count in rungs:
        if not 1 <= count <= gross.size:
            raise ValueError(
                f"rung {count} is outside the shelf of {gross.size} candidates"
            )

    net = gross - float(cost)
    results: list[LadderRung] = []
    for count in rungs:
        held = net[:count]
        correlation_matrix = equicorrelated_matrix(count, correlation)
        covariance = correlation_to_covariance(
            [tuple(float(x) for x in row) for row in correlation_matrix],
            [tracking_error] * count,
        )
        equal = equal_weight_information_ratio(held, covariance)
        maximum = unconstrained_maximum_information_ratio(held, covariance)
        constrained = long_only_maximum(held, covariance)
        available = effective_breadth(count=count, mutual_correlation=correlation)
        results.append(
            LadderRung(
                count=count,
                mean_net_edge=float(np.mean(held)),
                available_bets=available,
                sharpe_multiple=math.sqrt(available),
                equal_weight_information_ratio=equal,
                unconstrained_information_ratio=maximum,
                long_only_information_ratio=constrained.information_ratio,
                equal_weight_transfer_coefficient=transfer_coefficient(equal, maximum),
                long_only_transfer_coefficient=transfer_coefficient(
                    constrained.information_ratio, maximum
                ),
                sleeves_held=constrained.sleeves_held,
                long_only_weights=constrained.weights,
            )
        )
    return tuple(results)


def correlation_sweep(
    edges: EdgeInput,
    *,
    cost: float,
    tracking_error: float,
    correlations: Sequence[float],
) -> tuple[tuple[float, LadderRung], ...]:
    """The full shelf scored at each correlation, so the count is never quoted at one.

    The two columns move in opposite directions and that is the finding: the unconstrained
    information ratio **rises** with correlation, because shorting correlated candidates
    against each other is more valuable rather than less, while the long-only one falls.
    Reporting either alone inverts the conclusion.
    """
    results: list[tuple[float, LadderRung]] = []
    for correlation in correlations:
        rung = ladder(
            edges,
            cost=cost,
            tracking_error=tracking_error,
            correlation=correlation,
            counts=(len(edges),),
        )[0]
        results.append((float(correlation), rung))
    return tuple(results)


def _as_edges(edges: EdgeInput) -> FloatArray:
    vector = np.asarray(edges, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"edges must be a non-empty one-dimensional sequence, got {edges!r}")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"every edge must be finite, got {edges!r}")
    return vector


def _as_covariance(covariance: MatrixInput, size: int) -> FloatArray:
    matrix = np.asarray(covariance, dtype=np.float64)
    if matrix.shape != (size, size):
        raise ValueError(
            f"covariance must be {size} by {size} to match {size} edges, got "
            f"shape {matrix.shape}"
        )
    if not np.allclose(matrix, matrix.T, atol=1e-12):
        raise ValueError("covariance matrix must be symmetric")
    smallest = float(np.min(np.linalg.eigvalsh(matrix)))
    if smallest <= 1e-12:
        raise ValueError(
            f"the covariance matrix is singular to working precision (smallest eigenvalue "
            f"{smallest:.3e}), so the maximum information ratio is not defined. Two of "
            "these candidates are the same candidate."
        )
    return matrix
