"""Purged and embargoed chronological cross-validation.

When labels are built from overlapping windows — a forward return, a triple-barrier exit,
a realised volatility over the next quarter — an observation in the training set can share
outcome periods with an observation in the test set. Ordinary k-fold cross-validation then
leaks the answer into the training data and reports a skill that does not exist.

Two mechanics prevent that:

* **Purging.** Drop from the training set every observation whose *label interval*
  intersects any test label interval.
* **Embargo.** Drop a further span of training observations immediately after the test
  label window, to stop serial correlation leaking backwards into observations that
  purging alone would keep.

**Never shuffle.** Every split produced here is chronological and contiguous, and the
functions refuse inputs that are not ordered.

Verification status
-------------------
**UNVERIFIED.** The primary text for these mechanics (Lopez de Prado, *Advances in
Financial Machine Learning*, ch. 7) was not retrievable in session, so the exact
definitions below — in particular whether the embargo is measured on the label-start axis
or the observation axis, and whether it is applied to both sides of the test window or only
after it — have not been checked against it. This is open question 3 in
``docs/research/portfolio-engine-specification.md``. The implementation is internally
consistent and tested against hand-computed interval examples; that is a weaker claim than
agreement with the source.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "LabelIntervals",
    "WalkForwardSplit",
    "embargo_mask",
    "purge_mask",
    "purged_walk_forward_splits",
]

FloatArray = NDArray[np.float64]
IndexArray = NDArray[np.intp]
BoolArray = NDArray[np.bool_]


@dataclass(frozen=True)
class LabelIntervals:
    """Closed label intervals ``[start_i, end_i]`` for each observation, in time order.

    ``start`` and ``end`` live on any monotone numeric axis — bar indices, day counts,
    ``datetime64`` values converted to floats. Only differences and comparisons are used,
    so the unit is the caller's choice, and the embargo span must be expressed in that same
    unit.
    """

    start: FloatArray
    end: FloatArray

    def __post_init__(self) -> None:
        start = np.asarray(self.start, dtype=np.float64)
        end = np.asarray(self.end, dtype=np.float64)
        if start.ndim != 1 or end.ndim != 1:
            raise ValueError("label starts and ends must be one-dimensional")
        if start.size != end.size:
            raise ValueError(
                f"label starts ({start.size}) and ends ({end.size}) must have equal length"
            )
        if start.size == 0:
            raise ValueError("label intervals must not be empty")
        if not (np.all(np.isfinite(start)) and np.all(np.isfinite(end))):
            raise ValueError("label intervals contain non-finite values")
        if np.any(end < start):
            raise ValueError("every label interval must satisfy end >= start")
        if np.any(np.diff(start) < 0.0):
            raise ValueError(
                "label starts must be non-decreasing; observations must stay in "
                "chronological order and must never be shuffled"
            )
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def __len__(self) -> int:
        return int(self.start.size)


def _as_indices(indices: Sequence[int] | NDArray[np.integer], n: int) -> IndexArray:
    values = np.asarray(indices, dtype=np.intp)
    if values.ndim != 1:
        raise ValueError("indices must be one-dimensional")
    if values.size == 0:
        raise ValueError("indices must not be empty")
    if np.any(values < 0) or np.any(values >= n):
        raise ValueError(f"indices must lie in [0, {n - 1}]")
    return values


def purge_mask(
    labels: LabelIntervals, test_indices: Sequence[int] | NDArray[np.integer]
) -> BoolArray:
    """Boolean mask, ``True`` where an observation must be purged from training.

    An observation is purged when its label interval ``[start_i, end_i]`` intersects the
    label interval of any test observation. Because the test set is a contiguous block, the
    union of test label intervals is bounded by ``[min start, max end]`` over the test set,
    and the closed-interval intersection test is ``start_i <= test_end and end_i >= test_start``.

    Test observations themselves are marked purged, so the mask can be applied directly to
    the full index.
    """
    test = _as_indices(test_indices, len(labels))
    test_start = float(labels.start[test].min())
    test_end = float(labels.end[test].max())
    return (labels.start <= test_end) & (labels.end >= test_start)


def embargo_mask(
    labels: LabelIntervals,
    test_indices: Sequence[int] | NDArray[np.integer],
    embargo: float,
) -> BoolArray:
    """Boolean mask, ``True`` where an observation falls inside the embargo.

    The embargo covers label starts in ``(test_end, test_end + embargo]``, where
    ``test_end`` is the latest label end in the test set. ``embargo`` is measured in the
    same units as the label axis. An embargo of 0 masks nothing.

    Only the forward side is embargoed: the backward side is already handled by purging,
    since any earlier observation whose label reaches into the test window intersects it by
    construction.
    """
    if embargo < 0.0:
        raise ValueError("embargo must be non-negative")
    test = _as_indices(test_indices, len(labels))
    test_end = float(labels.end[test].max())
    if embargo == 0.0:
        return np.zeros(len(labels), dtype=bool)
    return (labels.start > test_end) & (labels.start <= test_end + embargo)


@dataclass(frozen=True)
class WalkForwardSplit:
    """One chronological fold."""

    train: IndexArray
    test: IndexArray
    purged: IndexArray
    """Training candidates removed because their labels overlap the test window."""
    embargoed: IndexArray
    """Training candidates removed by the embargo."""
    fold: int


def purged_walk_forward_splits(
    labels: LabelIntervals,
    *,
    n_splits: int,
    embargo: float = 0.0,
    expanding: bool = True,
    min_train_size: int = 1,
) -> Iterator[WalkForwardSplit]:
    """Chronological walk-forward folds with purging and an embargo.

    The observations after the first training block are cut into ``n_splits`` contiguous
    test folds in time order. For each fold:

    * ``expanding=True`` (default) trains on everything before the test fold — an expanding
      window, which is what a live research process actually has available.
    * ``expanding=False`` also admits observations *after* the test fold, which is only
      appropriate for a pure model-selection study and never for a performance estimate,
      because it uses the future.

    Training candidates are then purged and embargoed. Folds whose surviving training set
    is smaller than ``min_train_size`` are skipped rather than silently returned, so a
    caller cannot accidentally fit on three observations.

    Nothing is shuffled at any point.
    """
    n = len(labels)
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if n_splits >= n:
        raise ValueError(f"n_splits ({n_splits}) must be smaller than the sample ({n})")
    if min_train_size < 1:
        raise ValueError("min_train_size must be positive")

    boundaries = np.linspace(0, n, n_splits + 1).astype(int)
    for fold in range(1, n_splits + 1):
        start, stop = int(boundaries[fold - 1]), int(boundaries[fold])
        if stop <= start:
            continue
        test = np.arange(start, stop, dtype=np.intp)
        candidates = (
            np.arange(0, start, dtype=np.intp)
            if expanding
            else np.concatenate([np.arange(0, start), np.arange(stop, n)]).astype(np.intp)
        )
        if candidates.size == 0:
            continue
        purged = purge_mask(labels, test)
        embargoed = embargo_mask(labels, test, embargo)
        keep = ~(purged | embargoed)
        train = candidates[keep[candidates]]
        if train.size < min_train_size:
            continue
        yield WalkForwardSplit(
            train=train,
            test=test,
            purged=candidates[purged[candidates]],
            embargoed=candidates[embargoed[candidates] & ~purged[candidates]],
            fold=fold,
        )
