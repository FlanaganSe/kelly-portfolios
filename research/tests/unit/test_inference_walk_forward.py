"""Tests for purged and embargoed chronological cross-validation.

The mechanics under test are flagged **UNVERIFIED** against their primary text (open
question 3 in ``docs/research/portfolio-engine-specification.md``). These tests therefore
check internal consistency against hand-constructed interval examples that a reader can
verify by inspection — they do not establish agreement with the source.
"""

from __future__ import annotations

import numpy as np
import pytest

from portfolio_edge.inference.walk_forward import (
    LabelIntervals,
    embargo_mask,
    purge_mask,
    purged_walk_forward_splits,
)


def overlapping_labels(n: int, horizon: int) -> LabelIntervals:
    """Observation i is labelled by the outcome over ``[i, i + horizon]``."""
    start = np.arange(n, dtype=float)
    return LabelIntervals(start=start, end=start + horizon)


# The worked example used throughout, verifiable by inspection.
#
#   n = 10, label interval of observation i is [i, i + 2]:
#     0: [0, 2]   1: [1, 3]   2: [2, 4]   3: [3, 5]   4: [4, 6]
#     5: [5, 7]   6: [6, 8]   7: [7, 9]   8: [8, 10]  9: [9, 11]
#
#   test = {4, 5}, so the test label span is [4, 7].
#
#   Purged (interval intersects [4, 7], i.e. start <= 7 and end >= 4):
#     0 [0,2] no    1 [1,3] no    2 [2,4] YES (touches 4)   3 [3,5] YES
#     4 [4,6] YES   5 [5,7] YES   6 [6,8] YES               7 [7,9] YES
#     8 [8,10] no (starts at 8 > 7)                         9 [9,11] no
#
#   Embargo of 1 on the label-start axis covers starts in (7, 8]: observation 8.
#
#   Surviving training set: {0, 1, 9}.
WORKED_TEST_INDICES = [4, 5]
WORKED_PURGED = [2, 3, 4, 5, 6, 7]
WORKED_EMBARGOED = [8]
WORKED_TRAIN = [0, 1, 9]


def test_purge_mask_matches_the_hand_computed_example() -> None:
    labels = overlapping_labels(10, 2)
    mask = purge_mask(labels, WORKED_TEST_INDICES)
    assert np.flatnonzero(mask).tolist() == WORKED_PURGED


def test_embargo_mask_matches_the_hand_computed_example() -> None:
    labels = overlapping_labels(10, 2)
    mask = embargo_mask(labels, WORKED_TEST_INDICES, embargo=1.0)
    assert np.flatnonzero(mask).tolist() == WORKED_EMBARGOED


def test_purge_and_embargo_together_leave_the_hand_computed_training_set() -> None:
    labels = overlapping_labels(10, 2)
    removed = purge_mask(labels, WORKED_TEST_INDICES) | embargo_mask(
        labels, WORKED_TEST_INDICES, embargo=1.0
    )
    assert np.flatnonzero(~removed).tolist() == WORKED_TRAIN


def test_a_zero_embargo_removes_nothing_extra() -> None:
    labels = overlapping_labels(10, 2)
    assert not embargo_mask(labels, WORKED_TEST_INDICES, embargo=0.0).any()


def test_a_longer_embargo_removes_strictly_more() -> None:
    """Embargo 3 covers starts in (7, 10]: observations 8 and 9, leaving only {0, 1}."""
    labels = overlapping_labels(10, 2)
    mask = embargo_mask(labels, WORKED_TEST_INDICES, embargo=3.0)
    assert np.flatnonzero(mask).tolist() == [8, 9]


def test_non_overlapping_labels_purge_nothing_outside_the_test_block() -> None:
    """With point labels ([i, i]) the only purged observations are the test ones."""
    start = np.arange(12, dtype=float)
    labels = LabelIntervals(start=start, end=start.copy())
    mask = purge_mask(labels, [5, 6, 7])
    assert np.flatnonzero(mask).tolist() == [5, 6, 7]


def test_purging_is_symmetric_around_the_test_window() -> None:
    """Labels reaching forward into the window and labels the window reaches into both go."""
    labels = overlapping_labels(20, 4)
    mask = purge_mask(labels, [10])
    # Test label span is [10, 14]. Purged: start <= 14 and end >= 10, i.e. i in [6, 14].
    assert np.flatnonzero(mask).tolist() == list(range(6, 15))


def test_embargo_rejects_a_negative_span() -> None:
    labels = overlapping_labels(10, 2)
    with pytest.raises(ValueError, match="embargo"):
        embargo_mask(labels, [4], embargo=-1.0)


# --------------------------------------------------------------------------------------
# Splits
# --------------------------------------------------------------------------------------


def test_splits_are_chronological_contiguous_and_never_shuffled() -> None:
    labels = overlapping_labels(120, 3)
    splits = list(purged_walk_forward_splits(labels, n_splits=4, embargo=2.0))
    assert [s.fold for s in splits] == sorted(s.fold for s in splits)
    previous_end = -1
    for split in splits:
        assert np.array_equal(split.test, np.arange(split.test[0], split.test[-1] + 1))
        assert int(split.test[0]) > previous_end
        previous_end = int(split.test[-1])
        # Expanding window: every training index precedes the test block.
        assert int(split.train.max()) < int(split.test.min())
        assert np.array_equal(split.train, np.sort(split.train))


def test_training_sets_never_intersect_the_test_label_window() -> None:
    labels = overlapping_labels(200, 5)
    for split in purged_walk_forward_splits(labels, n_splits=5, embargo=3.0):
        test_start = float(labels.start[split.test].min())
        test_end = float(labels.end[split.test].max())
        train_start = labels.start[split.train]
        train_end = labels.end[split.train]
        overlaps = (train_start <= test_end) & (train_end >= test_start)
        assert not overlaps.any()
        # And nothing survives inside the embargo band.
        assert not ((train_start > test_end) & (train_start <= test_end + 3.0)).any()


def test_purged_and_embargoed_observations_are_reported_separately() -> None:
    """Fold accounting must balance: candidates = train + purged + embargoed."""
    labels = overlapping_labels(100, 4)
    for split in purged_walk_forward_splits(labels, n_splits=5, embargo=2.0):
        candidates = int(split.test.min())
        assert split.train.size + split.purged.size + split.embargoed.size == candidates
        assert set(split.purged.tolist()).isdisjoint(split.embargoed.tolist())


def test_non_expanding_splits_admit_future_observations() -> None:
    """Only appropriate for model selection — it uses the future, and says so."""
    labels = overlapping_labels(100, 2)
    splits = list(purged_walk_forward_splits(labels, n_splits=4, expanding=False, embargo=1.0))
    middle = splits[1]
    assert int(middle.train.max()) > int(middle.test.max())


def test_first_fold_is_skipped_because_it_has_no_training_history() -> None:
    labels = overlapping_labels(50, 2)
    folds = [s.fold for s in purged_walk_forward_splits(labels, n_splits=5)]
    assert 1 not in folds
    assert folds == [2, 3, 4, 5]


def test_folds_with_too_little_surviving_training_data_are_skipped() -> None:
    """A long label horizon purges nearly everything; the caller must not silently fit on it."""
    labels = overlapping_labels(60, 25)
    folds = list(purged_walk_forward_splits(labels, n_splits=5, min_train_size=10))
    for split in folds:
        assert split.train.size >= 10


def test_label_intervals_reject_shuffled_or_malformed_input() -> None:
    with pytest.raises(ValueError, match="chronological order"):
        LabelIntervals(start=np.array([3.0, 1.0, 2.0]), end=np.array([4.0, 2.0, 3.0]))
    with pytest.raises(ValueError, match="end >= start"):
        LabelIntervals(start=np.array([1.0, 2.0]), end=np.array([0.0, 3.0]))
    with pytest.raises(ValueError, match="equal length"):
        LabelIntervals(start=np.array([1.0, 2.0]), end=np.array([3.0]))


def test_split_arguments_are_validated() -> None:
    labels = overlapping_labels(20, 2)
    with pytest.raises(ValueError, match="n_splits"):
        list(purged_walk_forward_splits(labels, n_splits=1))
    with pytest.raises(ValueError, match="smaller than the sample"):
        list(purged_walk_forward_splits(labels, n_splits=20))
